# Siliconflow2cow Plugin for chatgpt-on-wechat

## 简介

Siliconflow2cow 是一个强大的 chatgpt-on-wechat 插件，允许用户通过简单的命令生成各种风格的图像。该插件支持多种模型，包括文本到图像和图像到图像的转换，为用户提供了丰富的图像生成选项。

## 特性

- 支持多种图像生成模型
- 文本到图像和图像到图像的转换
- 可自定义图像尺寸和比例
- AI 提示词增强功能
- 简单直观的命令语法

## 安装

1. 确保您已经安装了 chatgpt-on-wechat。
2. 将 `siliconflow2cow` 目录复制到 chatgpt-on-wechat 的 `plugins` 目录中。
3. 安装所需的依赖：
   ```
    pip install -r siliconflow2cow/requirements.txt
   ```
4. 在 `config.json` 文件中配置您的 API 令牌和其他设置。

## 配置

在 `config.json` 文件中设置以下参数：

```json
{
  "auth_token": "your_auth_token_here",
  "drawing_prefixes": ["绘", "draw"],
  "image_output_dir": "./plugins/siliconflow2cow/images"
}
```

- `auth_token`：您的 Siliconflow API 认证令牌
- `drawing_prefixes`：触发绘图命令的前缀
- `image_output_dir`：生成图像的保存目录

## 译文模型切换（默认使用deepseek付费模型）
<img width="692" alt="image" src="https://github.com/user-attachments/assets/318f14c6-1458-436c-90a9-8c98ff1a5784">

可更改为下面免费模型（部分展示）
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


## 调优建议

如果您发现生成的图片质量不佳，特别是出现色彩过度饱和的情况，可以尝试调整以下参数：

### 1. 调整推理步数 (num_inference_steps)

推理步数影响图像生成的精细程度。增加步数通常可以提高图像质量，但也会增加生成时间。

建议值：
- 标准模型：20-50 步
- 快速模型（如 SDXL Turbo）：4-10 步

### 2. 修改引导尺度 (guidance_scale)

引导尺度控制生成图像与提示词的匹配程度。较低的值可能导致图像不够清晰，而较高的值可能导致过度饱和。

建议值：
- 标准范围：5.0-8.0
- 对于色彩过度饱和的情况，尝试降低到 3.0-5.0

### 3. 优化提示词

- 添加特定的风格描述，如 "柔和的色彩"、"自然的光线"
- 使用负面提示词来避免不想要的效果，如 "过度饱和, 过度对比"

### 4. 模型特定配置

根据不同模型调整参数：

#### FLUX 模型
```python
json_body = {
    "num_inference_steps": 30,
    "guidance_scale": 6.0,
    "prompt": prompt,
    "width": width,
    "height": height
}
```

#### Stable Diffusion (SD) 模型
```python
json_body = {
    "num_inference_steps": 40,
    "guidance_scale": 5.5,
    "prompt": prompt,
    "width": width,
    "height": height
}
```

#### SDXL Turbo 和 SDXL Lightning
```python
json_body = {
    "num_inference_steps": 6,  # 可以尝试 4-8
    "guidance_scale": 1.5,     # 可以尝试 1.0-2.0
    "prompt": prompt,
    "width": width,
    "height": height
}
```

### 如何应用这些调整

1. 打开 `siliconflow2cow.py` 文件。
2. 找到 `generate_image_by_text` 和 `generate_image_by_img` 方法。
3. 根据您使用的模型，修改相应的 `json_body` 配置。

例如，对于 FLUX 模型：

```python
if model_key == "flux":
    json_body.update({
        "num_inference_steps": 30,
        "guidance_scale": 6.0
    })
```

4. 保存文件并重新加载插件。

通过调整这些参数，您应该能够显著改善生成图像的质量，减少色彩过度饱和的问题。如果问题仍然存在，可以逐步微调这些值，直到达到满意的结果。

## 高级用户提示

- 尝试不同的模型：有时切换到不同的模型可能会产生更好的结果。
- 实验性调整：对于经验丰富的用户，可以尝试在提示词中直接指定参数，例如：
  ```
  绘 自然风景 -m sdxl --steps 40 --guidance 5.5 ---16:9
  ```
  
## 使用方法

使用以下格式发送消息来生成图像：

```
[前缀] [提示词] -m [模型] ---[尺寸比例]
```

例如：
```
绘 一只可爱的小猫 -m flux ---16:9
```
<img width="1061" alt="image" src="https://github.com/user-attachments/assets/3285128e-1ad2-4f27-84ab-e426e11ccfb6">


### 可用模型

- flux
- sd3
- sdxl
- sd2
- sdt
- sdxlt
- sdxll

### 可用尺寸比例

- 1:1 (1024x1024)
- 1:2 (1024x2048)
- 2:1 (2048x1024)
- 3:2 (1536x1024)
- 2:3 (1024x1536)
- 4:3 (1536x1152)
- 3:4 (1152x1536)
- 16:9 (2048x1152)
- 9:16 (1152x2048)

### 图像到图像转换

要进行图像到图像的转换，只需在提示词中包含图片 URL：

```
绘 将这张图片转换成动漫风格 https://example.com/image.jpg -m sdxl ---1:1
```

<img width="1070" alt="image" src="https://github.com/user-attachments/assets/8799bb57-25ab-4182-ba9e-0459d584b8fa">

## 注意事项

1. 确保您有足够的 API 使用额度。
2. 生成的图像将保存在配置的输出目录中。
3. 插件会自动优化您的提示词以产生更好的结果。


## 贡献榜
感谢L站“逆向达人”提供思路
[Workers部署链接](https://linux.do/t/topic/185085)

## 故障排除

如果遇到问题：

1. 检查您的 API 令牌是否正确。
2. 确保您有稳定的网络连接。
3. 检查日志文件以获取详细的错误信息。


欢迎提交 issues 和 pull requests 来改进这个插件。


