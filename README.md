# Siliconflow2cow 插件（用于 chatgpt-on-wechat）

## 概述

Siliconflow2cow 是一款强大的 chatgpt-on-wechat 插件，让用户能够通过简单的命令生成各种风格的图像。这个多功能插件支持多种模型，可进行文本到图像和图像到图像的转换，为用户提供丰富的图像生成选项。

## 主要特性

- 支持多种图像生成模型
- 文本到图像和图像到图像的转换功能
- 可自定义图像尺寸和宽高比
- AI 增强的提示词优化
- 直观的命令语法

## 安装步骤

1. 确保您已安装 chatgpt-on-wechat。
2. 将 `siliconflow2cow` 目录复制到 chatgpt-on-wechat 的 `plugins` 文件夹中。
3. 安装所需依赖：
   ```
   pip install -r siliconflow2cow/requirements.txt
   ```
4. 在 `config.json` 文件中配置您的 API 令牌和其他设置。

## 配置说明

在 `config.json` 文件中设置以下参数：

```json
{
  "auth_token": "您的认证令牌",
  "drawing_prefixes": ["绘", "draw"],
  "image_output_dir": "./plugins/siliconflow2cow/images"
}
```

- `auth_token`：您的 Siliconflow API 认证令牌
- `drawing_prefixes`：触发绘图命令的前缀
- `image_output_dir`：生成图像的保存目录

## 翻译模型选择

默认情况下，插件使用 DeepSeek 付费模型。您可以切换到免费模型，如：
```
Qwen/Qwen2-7B-Instruct (32K, 免费)
Qwen/Qwen2-1.5B-Instruct (32K, 免费)
Qwen/Qwen1.5-7B-Chat (32K, 免费)
THUDM/glm-4-9b-chat (32K, 免费)
THUDM/chatglm3-6b (32K, 免费)
01-ai/Yi-1.5-9B-Chat-16K (16K, 免费)
01-ai/Yi-1.5-6B-Chat (4K, 免费)
internlm/internlm2_5-7b-chat (32K, 免费)
国际领先模型部分：
google/gemma-2-9b-it (8K, 免费)
meta-llama/Meta-Llama-3-8B-Instruct (8K, 免费)
meta-llama/Meta-Llama-3.1-8B-Instruct (8K, 免费)
mistralai/Mistral-7B-Instruct-v0.2 (32K，免费) 
```

## 优化建议

为提高图像质量，特别是解决颜色过度饱和的问题，可以考虑调整以下参数：

1. **推理步数** (`num_inference_steps`)：
   - 标准模型：20-50 步
   - 快速模型（如 SDXL Turbo）：4-10 步

2. **引导尺度** (`guidance_scale`)：
   - 标准范围：5.0-8.0
   - 对于过度饱和的情况，尝试：3.0-5.0

3. **提示词优化**：
   - 使用具体、详细的描述
   - 包含艺术风格（例如，"油画风格"）
   - 使用括号增加权重："(蓝色眼睛:1.2)"

4. **模型特定配置**：
   根据您使用的模型（FLUX、SD、SDXL Turbo 等）调整参数

## 使用方法

使用以下格式生成图像：

```
[前缀] [提示词] -m [模型] ---[宽高比]
```

示例：
```
绘小女孩,情趣内衣,18岁,蜡烛,昏暗 -m flux ---16:9
```
<img width="1076" alt="image" src="https://github.com/user-attachments/assets/e31cc900-37e4-4737-ac6f-320a4558d6c5">

![图片](https://github.com/user-attachments/assets/5f30b4ea-41fd-496e-aae9-cb40b1d4f0ea)

### 支持的模型

- flux: FLUX.1-schnell
- sd3: Stable Diffusion 3 Medium
- sdxl: Stable Diffusion XL Base 1.0
- sd2: Stable Diffusion 2.1
- sdt: Stable Diffusion Turbo
- sdxlt: Stable Diffusion XL Turbo
- sdxll: SDXL-Lightning

### 可用宽高比

1:1, 1:2, 2:1, 3:2, 2:3, 4:3, 3:4, 16:9, 9:16

### 图像到图像转换

在提示词中包含图片 URL：

```
绘 将这张图片中的猫娘头上加上玫瑰 https://demo-cloudflare-imgbed.pages.dev/file/3a58a0d70ecf5439ec784.png -m sdxl ---9:16
```
<img width="1077" alt="image" src="https://github.com/user-attachments/assets/a8921a07-46ef-4aae-85a8-782c1d8fb497">

- 图生图有点奇葩，勉勉强强使用吧（第一张为原图，第二张为图生图）
![pintu-fulicat com-1724763611385](https://github.com/user-attachments/assets/46aa3223-36f9-4f36-bf06-ac48855851a5)


## 重要说明

1. 确保您有足够的 API 使用额度。
2. 生成的图像将保存在配置的输出目录中。
3. 插件会自动优化您的提示词以产生更好的结果。

## 故障排除

如果遇到问题：

1. 验证您的 API 令牌是否正确。
2. 确保您有稳定的网络连接。
3. 查看日志文件以获取详细的错误信息。

## 贡献

特别感谢 L 站的"逆向达人"提供的见解。
[Workers 部署链接](https://linux.do/t/topic/185085)

我们欢迎您提交问题和拉取请求，以改进这个插件！
