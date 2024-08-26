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
   pip install requests pathvalidate Pillow
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

## 使用方法

使用以下格式发送消息来生成图像：

```
[前缀] [提示词] -m [模型] ---[尺寸比例]
```

例如：
```
绘 一只可爱的小猫 -m flux ---16:9
```

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

## 注意事项

1. 确保您有足够的 API 使用额度。
2. 生成的图像将保存在配置的输出目录中。
3. 插件会自动优化您的提示词以产生更好的结果。

## 故障排除

如果遇到问题：

1. 检查您的 API 令牌是否正确。
2. 确保您有稳定的网络连接。
3. 检查日志文件以获取详细的错误信息。

## 贡献

欢迎提交 issues 和 pull requests 来改进这个插件。

## 许可证

[在此处添加许可证信息]

