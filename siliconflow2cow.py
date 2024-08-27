import os
import re
import json
import time
import requests
import base64
import schedule
from io import BytesIO
from typing import List, Tuple
from pathvalidate import sanitize_filename
from PIL import Image
from datetime import datetime, timedelta
import threading

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from plugins import *
from config import conf

CHAT_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
CHAT_MODEL = "deepseek-ai/DeepSeek-V2-Chat"
ENHANCER_PROMPT = """As a Stable Diffusion Prompt expert, you will create prompts from keywords, often from databases like Danbooru. Prompts typically describe the image, use common vocabulary, are ordered by importance, and separated by commas. Avoid using "-" or ".", but spaces and natural language are acceptable. Avoid word repetition. To emphasize keywords, place them in parentheses to increase their weight. For example, "(flowers)" increases 'flowers' weight by 1.1x, while "(((flowers)))" increases it by 1.331x. Use "(flowers:1.5)" to increase 'flowers' weight by 1.5x. Only increase weights for important tags. Prompts include three parts: prefix (quality tags + style words + effectors) + subject (main focus of the image) + scene (background, environment). The prefix affects image quality. Tags like "masterpiece", "best quality" increase image detail. Style words like "illustration", "lensflare" define the image style. Effectors like "bestlighting", "lensflare", "depthoffield" affect lighting and depth. The subject is the main focus, like characters or scenes. Detailed subject description ensures rich, detailed images. Increase subject weight for clarity. For characters, describe facial, hair, body, clothing, pose features. The scene describes the environment. Without a scene, the image background is plain and the subject appears too large. Some subjects inherently include scenes (e.g., buildings, landscapes). Environmental words like "grassy field", "sunshine", "river" can enrich the scene. Your task is to design image generation prompts. Please follow these steps: 1. I will send you an image scene. You need to generate a detailed image description. 2. The image description must be in English, output as a Positive Prompt."""

@plugins.register(
    name="Siliconflow2cow",
    desire_priority=90,
    hidden=False,
    desc="A plugin for generating images using various models.",
    version="2.5.5",
    author="Assistant",
)
class Siliconflow2cow(Plugin):
    def __init__(self):
        super().__init__()
        try:
            conf = super().load_config()
            if not conf:
                raise Exception("配置未找到。")

            self.auth_token = conf.get("auth_token")
            if not self.auth_token:
                raise Exception("在配置中未找到认证令牌。")

            self.drawing_prefixes = conf.get("drawing_prefixes", ["绘", "draw"])
            self.image_output_dir = conf.get("image_output_dir", "./plugins/siliconflow2cow/images")
            self.clean_interval = conf.get("clean_interval", 3)  # 默认3天清理一次

            if not os.path.exists(self.image_output_dir):
                os.makedirs(self.image_output_dir)

            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            
            # 启动定时清理任务
            self.schedule_thread = threading.Thread(target=self.run_schedule, daemon=True)
            self.schedule_thread.start()
            
            logger.info("[Siliconflow2cow] 初始化成功")
        except Exception as e:
            logger.error(f"[Siliconflow2cow] 初始化失败，错误：{e}")
            raise e

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type != ContextType.TEXT:
            return

        content = e_context["context"].content
        if not content.startswith(tuple(self.drawing_prefixes)):
            return

        logger.debug(f"[Siliconflow2cow] 收到消息: {content}")

        try:
            # 移除前缀
            for prefix in self.drawing_prefixes:
                if content.startswith(prefix):
                    content = content[len(prefix):].strip()
                    break

            if content.lower() == "clean_all":
                reply = self.clean_all_images()
            else:
                model_key, image_size, clean_prompt = self.parse_user_input(content)
                logger.debug(f"[Siliconflow2cow] 解析后的参数: 模型={model_key}, 尺寸={image_size}, 提示词={clean_prompt}")

                original_image_url = self.extract_image_url(clean_prompt)
                logger.debug(f"[Siliconflow2cow] 原始提示词中提取的图片URL: {original_image_url}")

                enhanced_prompt = self.enhance_prompt(clean_prompt)
                logger.debug(f"[Siliconflow2cow] 增强后的提示词: {enhanced_prompt}")

                image_url = self.generate_image(enhanced_prompt, original_image_url, model_key, image_size)
                logger.debug(f"[Siliconflow2cow] 生成的图片URL: {image_url}")

                if image_url:
                    image_path = self.download_and_save_image(image_url)
                    logger.debug(f"[Siliconflow2cow] 图片已保存到: {image_path}")

                    with open(image_path, 'rb') as f:
                        image_storage = BytesIO(f.read())
                    reply = Reply(ReplyType.IMAGE, image_storage)
                else:
                    logger.error("[Siliconflow2cow] 生成图片失败")
                    reply = Reply(ReplyType.ERROR, "生成图片失败。")

            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
        except Exception as e:
            logger.error(f"[Siliconflow2cow] 发生错误: {e}")
            reply = Reply(ReplyType.ERROR, f"发生错误: {str(e)}")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

    def parse_user_input(self, content: str) -> Tuple[str, str, str]:
        model_key = self.extract_model_key(content)
        image_size = self.extract_image_size(content)
        clean_prompt = self.clean_prompt_string(content, model_key)
        logger.debug(f"[Siliconflow2cow] 解析用户输入: 模型={model_key}, 尺寸={image_size}, 清理后的提示词={clean_prompt}")
        return model_key, image_size, clean_prompt

    def enhance_prompt(self, prompt: str) -> str:
        try:
            logger.debug(f"[Siliconflow2cow] 正在增强提示词: {prompt}")
            response = requests.post(
                CHAT_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.auth_token}"
                },
                json={
                    "model": CHAT_MODEL,
                    "messages": [
                        {"role": "system", "content": ENHANCER_PROMPT},
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            response.raise_for_status()
            enhanced_prompt = response.json()['choices'][0]['message']['content']
            logger.debug(f"[Siliconflow2cow] 增强后的提示词: {enhanced_prompt}")
            return enhanced_prompt
        except Exception as e:
            logger.error(f"[Siliconflow2cow] 增强提示词失败: {e}")
            return prompt

    def generate_image(self, prompt: str, original_image_url: str, model_key: str, image_size: str) -> str:
        if original_image_url:
            logger.debug(f"[Siliconflow2cow] 检测到图片URL，使用图生图模式")
            return self.generate_image_by_img(prompt, original_image_url, model_key, image_size)
        else:
            logger.debug(f"[Siliconflow2cow] 未检测到图片URL，使用文生图模式")
            return self.generate_image_by_text(prompt, model_key, image_size)

    def generate_image_by_text(self, prompt: str, model_key: str, image_size: str) -> str:
        url = self.get_url_for_model(model_key)
        logger.debug(f"[Siliconflow2cow] 使用模型URL: {url}")

        width, height = map(int, image_size.split('x'))

        json_body = {
            "prompt": prompt,
            "width": width,
            "height": height
        }

        headers = {
            'Authorization': f"Bearer {self.auth_token}",
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        if model_key == "flux":
            json_body.update({
                "num_inference_steps": 30,
                "guidance_scale": 7.0
            })
        elif model_key == "sd2":
            json_body.update({
                "num_inference_steps": 40,
                "guidance_scale": 6.0
            })
        elif model_key == "sd3":
            json_body.update({
                "num_inference_steps": 45,
                "guidance_scale": 6.0
            })
        elif model_key == "sdt":
            json_body.update({
                "num_inference_steps": 6,
                "guidance_scale": 1.0,
                "cfg_scale": 1.0
            })
        elif model_key == "sdxlt":
            json_body.update({
                "num_inference_steps": 4,
                "guidance_scale": 1.0
            })
        elif model_key == "sdxll":
            json_body.update({
                "num_inference_steps": 4,
                "guidance_scale": 1.0
            })
        else:
            json_body.update({
                "num_inference_steps": 50,
                "guidance_scale": 7.5
            })

        logger.debug(f"[Siliconflow2cow] 发送请求体: {json_body}")
        try:
            response = requests.post(url, headers=headers, json=json_body)
            response.raise_for_status()
            json_response = response.json()
            logger.debug(f"[Siliconflow2cow] API响应: {json_response}")
            return json_response['images'][0]['url']
        except requests.exceptions.RequestException as e:
            logger.error(f"[Siliconflow2cow] API请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 400:
                    error_message = e.response.json().get('error', {}).get('message', '未知错误')
                    logger.error(f"[Siliconflow2cow] API错误信息: {error_message}")
                logger.error(f"[Siliconflow2cow] API响应内容: {e.response.text}")
            raise Exception(f"API请求失败: {str(e)}")

    def generate_image_by_img(self, prompt: str, image_url: str, model_key: str, image_size: str) -> str:
        url = self.get_img_url_for_model(model_key)
        logger.debug(f"[Siliconflow2cow] 使用图生图模型URL: {url}")
        img_prompt = self.remove_image_urls(prompt)

        base64_image = self.convert_image_to_base64(image_url)

        width, height = map(int, image_size.split('x'))

        json_body = {
            "prompt": img_prompt,
            "image": base64_image,
            "width": width,
            "height": height,
            "batch_size": 1
        }

        if model_key == "sdxl":
            json_body.update({
                "num_inference_steps": 40,
                "guidance_scale": 7.5
            })
        elif model_key == "sd2":
            json_body.update({
                "num_inference_steps": 40,
                "guidance_scale": 8.5
            })
        elif model_key == "sdxll":
            json_body.update({
                "num_inference_steps": 4,
                "guidance_scale": 1.0
            })
        elif model_key == "pm":
            json_body.update({
                "style_name": "Photographic (Default)",
                "guidance_scale": 5,
                "style_strengh_radio": 20
            })
        else:
            json_body.update({
                "num_inference_steps": 50,
                "guidance_scale": 7.5
            })

        headers = {
            'Authorization': f"Bearer {self.auth_token}",
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        log_json_body = json_body.copy()
        log_json_body['image'] = '[BASE64_IMAGE_DATA]'
        logger.debug(f"[Siliconflow2cow] 发送图生图请求体: {log_json_body}")

        try:
            response = requests.post(url, headers=headers, json=json_body)
            response.raise_for_status()
            json_response = response.json()
            logger.debug(f"[Siliconflow2cow] API响应: {json_response}")
            return json_response['images'][0]['url']
        except requests.exceptions.RequestException as e:
            logger.error(f"[Siliconflow2cow] API请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 400:
                    error_message = e.response.json().get('error', {}).get('message', '未知错误')
                    logger.error(f"[Siliconflow2cow] API错误信息: {error_message}")
                logger.error(f"[Siliconflow2cow] API响应内容: {e.response.text}")
            raise Exception(f"API请求失败: {str(e)}")

    def extract_model_key(self, prompt: str) -> str:
        match = re.search(r'-m ?(\S+)', prompt)
        model_key = match.group(1).strip() if match else "flux"
        logger.debug(f"[Siliconflow2cow] 提取的模型键: {model_key}")
        return model_key

    def extract_image_size(self, prompt: str) -> str:
        match = re.search(r'---(\d+:\d+)', prompt)
        if match:
            ratio = match.group(1).strip()
            size = self.RATIO_MAP.get(ratio, "1024x1024")
        else:
            size = "1024x1024"
        logger.debug(f"[Siliconflow2cow] 提取的图片尺寸: {size}")
        return size

    def clean_prompt_string(self, prompt: str, model_key: str) -> str:
        clean_prompt = re.sub(r' -m ?\S+', '', re.sub(r'---\d+:\d+', '', prompt)).strip()
        logger.debug(f"[Siliconflow2cow] 清理后的提示词: {clean_prompt}")
        return clean_prompt

    def extract_image_url(self, text: str) -> str:
        match = re.search(r'(https?://[^\s]+?\.(?:png|jpe?g|gif|bmp|webp|svg|tiff|ico))(?:\s|$)', text, re.IGNORECASE)
        url = match.group(1) if match else None
        logger.debug(f"[Siliconflow2cow] 提取的图片URL: {url}")
        return url

    def convert_image_to_base64(self, image_url: str) -> str:
        logger.debug(f"[Siliconflow2cow] 正在下载图片: {image_url}")
        response = requests.get(image_url)
        if response.status_code != 200:
            logger.error(f"[Siliconflow2cow] 下载图片失败，状态码: {response.status_code}")
            raise Exception('下载图片失败')
        base64_image = f"data:image/webp;base64,{base64.b64encode(response.content).decode('utf-8')}"
        logger.debug("[Siliconflow2cow] 图片已成功转换为base64")
        return base64_image

    def remove_image_urls(self, text: str) -> str:
        cleaned_text = re.sub(r'https?://\S+\.(?:png|jpe?g|gif|bmp|webp|svg|tiff|ico)(?:\s|$)', '', text, flags=re.IGNORECASE)
        logger.debug(f"[Siliconflow2cow] 移除图片URL后的文本: {cleaned_text}")
        return cleaned_text

    def get_url_for_model(self, model_key: str) -> str:
        URL_MAP = {
            "flux": "https://api.siliconflow.cn/v1/black-forest-labs/FLUX.1-schnell/text-to-image",
            "sd3": "https://api.siliconflow.cn/v1/stabilityai/stable-diffusion-3-medium/text-to-image",
            "sdxl": "https://api.siliconflow.cn/v1/stabilityai/stable-diffusion-xl-base-1.0/text-to-image",
            "sd2": "https://api.siliconflow.cn/v1/stabilityai/stable-diffusion-2-1/text-to-image",
            "sdt": "https://api.siliconflow.cn/v1/stabilityai/sd-turbo/text-to-image",
            "sdxlt": "https://api.siliconflow.cn/v1/stabilityai/sdxl-turbo/text-to-image",
            "sdxll": "https://api.siliconflow.cn/v1/ByteDance/SDXL-Lightning/text-to-image"
        }
        url = URL_MAP.get(model_key, URL_MAP["flux"])
        logger.debug(f"[Siliconflow2cow] 选择的模型URL: {url}")
        return url

    def get_img_url_for_model(self, model_key: str) -> str:
        IMG_URL_MAP = {
            "sdxl": "https://api.siliconflow.cn/v1/stabilityai/stable-diffusion-xl-base-1.0/image-to-image",
            "sd2": "https://api.siliconflow.cn/v1/stabilityai/stable-diffusion-2-1/image-to-image",
            "sdxll": "https://api.siliconflow.cn/v1/ByteDance/SDXL-Lightning/image-to-image",
            "pm": "https://api.siliconflow.cn/v1/TencentARC/PhotoMaker/image-to-image"
        }
        url = IMG_URL_MAP.get(model_key, IMG_URL_MAP["sdxl"])
        logger.debug(f"[Siliconflow2cow] 选择的图生图模型URL: {url}")
        return url

    RATIO_MAP = {
        "1:1": "1024x1024",
        "1:2": "1024x2048",
        "2:1": "2048x1024",
        "3:2": "1536x1024",
        "2:3": "1024x1536",
        "4:3": "1536x1152",
        "3:4": "1152x1536",
        "16:9": "2048x1152",
        "9:16": "1152x2048"       
    }

    def download_and_save_image(self, image_url: str) -> str:
        logger.debug(f"[Siliconflow2cow] 正在下载并保存图片: {image_url}")
        response = requests.get(image_url)
        if response.status_code != 200:
            logger.error(f"[Siliconflow2cow] 下载图片失败，状态码: {response.status_code}")
            raise Exception('下载图片失败')

        image = Image.open(BytesIO(response.content))

        filename = f"{int(time.time())}.png"
        file_path = os.path.join(self.image_output_dir, filename)

        image.save(file_path, format='PNG')

        logger.info(f"[Siliconflow2cow] 图片已保存到 {file_path}")
        return file_path

    def clean_all_images(self):
        """清理所有图片"""
        logger.info("[Siliconflow2cow] 开始清理所有图片")
        initial_count = len([name for name in os.listdir(self.image_output_dir) if os.path.isfile(os.path.join(self.image_output_dir, name))])
        
        for filename in os.listdir(self.image_output_dir):
            file_path = os.path.join(self.image_output_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                logger.info(f"[Siliconflow2cow] 已删除图片: {file_path}")
        
        final_count = len([name for name in os.listdir(self.image_output_dir) if os.path.isfile(os.path.join(self.image_output_dir, name))])
        
        logger.info("[Siliconflow2cow] 清理所有图片完成")
        return Reply(ReplyType.TEXT, f"清理完成：已删除 {initial_count - final_count} 张图片，当前目录下还有 {final_count} 张图片。")

    def run_schedule(self):
        """运行定时任务"""
        schedule.every().day.at("00:00").do(self.clean_old_images)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def clean_old_images(self):
        """清理指定天数前的图片"""
        logger.info("[Siliconflow2cow] 开始清理旧图片")
        now = datetime.now()
        for filename in os.listdir(self.image_output_dir):
            file_path = os.path.join(self.image_output_dir, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if now - file_time > timedelta(days=self.clean_interval):
                    os.remove(file_path)
                    logger.info(f"[Siliconflow2cow] 已删除旧图片: {file_path}")
        logger.info("[Siliconflow2cow] 清理旧图片完成")

    def get_help_text(self, **kwargs):
        help_text = "插件使用指南：\n"
        help_text += f"1. 使用 {', '.join(self.drawing_prefixes)} 作为命令前缀\n"
        help_text += "2. 在提示词后面添加 '-m' 来选择模型，例如：-m sdxl\n"
        help_text += "3. 使用 '---' 后跟比例来指定图片尺寸，例如：---16:9\n"
        help_text += "4. 如果要进行图生图，直接在提示词中包含图片URL\n"
        help_text += f"5. 输入 '{self.drawing_prefixes[0]}clean_all' 来清理所有图片（警告：这将删除所有已生成的图片）\n"
        help_text += f"示例：{self.drawing_prefixes[0]} 一只可爱的小猫 -m flux ---16:9\n"
        help_text += "注意：您的提示词将会被AI自动优化以产生更好的结果。\n"
        help_text += "注意：各模型的参数已经过调整以提高图像质量。\n"
        help_text += f"可用的模型：flux, sd3, sdxl, sd2, sdt, sdxlt, sdxll\n"
        help_text += f"可用的尺寸比例：{', '.join(self.RATIO_MAP.keys())}\n"
        help_text += f"图片将每{self.clean_interval}天自动清理一次。\n"
        return help_text