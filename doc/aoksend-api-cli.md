# Aoksend API CLI 工具

一个用于与 Aoksend 邮件服务 API 进行交互的命令行工具，帮助用户快速测试和调试邮件发送功能。

## 功能特点

- 通过命令行直接调用 Aoksend 邮件 API
- 支持所有必需和可选参数
- 文件附件上传（支持多种文件类型，最大 1MB）
- 完整的参数验证和错误处理
- 详细的返回信息和错误提示

## 安装要求

- Python 3.x
- requests 库

安装 requests 库：
```bash
pip install requests
```

## 使用方法

### 基本使用

```bash
python3 aoksend-api-cli.py --app-key YOUR_KEY --template-id TEMPLATE_ID --to recipient@example.com
```

### 带模板数据

```bash
python3 aoksend-api-cli.py --app-key YOUR_KEY --template-id TEMPLATE_ID --to recipient@example.com --data '{"name": "张三"}'
```

### 带附件

```bash
python3 aoksend-api-cli.py --app-key YOUR_KEY --template-id TEMPLATE_ID --to recipient@example.com --attachment file.pdf
```

### 完整参数示例

```bash
python3 aoksend-api-cli.py \
  --api-url https://www.aoksend.com/index/api/send_email \
  --app-key YOUR_API_KEY \
  --template-id YOUR_TEMPLATE_ID \
  --to recipient@example.com \
  --reply-to reply@example.com \
  --alias "发件人名称" \
  --is-random 1 \
  --data '{"name": "张三", "code": "123456"}' \
  --attachment attachment.pdf
```

## 参数说明

| 参数 | 必需 | 说明 |
|------|------|------|
| `--api-url` | 否 | API 地址（默认：https://www.aoksend.com/index/api/send_email） |
| `--app-key` | 是 | API 密钥 |
| `--template-id` | 是 | 模板 ID |
| `--to` | 是 | 收件人邮箱地址 |
| `--reply-to` | 否 | 默认回复地址 |
| `--alias` | 否 | 发件人名称 |
| `--is-random` | 否 | 是否随机发送（1 或 0） |
| `--data` | 否 | 模板数据（JSON 格式） |
| `--attachment` | 否 | 附件文件路径 |

## 支持的附件类型

支持以下文件类型，且文件大小不得超过 1MB：
- zip, rar, pdf, jpg, png, gif, mp4
- txt, doc, xls, ppt, docx, xlsx, pptx
- jpeg, csv

## 返回值说明

成功调用后会返回 JSON 格式的响应：

```json
{
  "code": 200,
  "message": "请求成功"
}
```

### 返回码对照

| 返回码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 40001 | API 密钥不能为空 |
| 40002 | 认证失败，API 密钥错误 |
| 40003 | 模板 ID 错误 |
| 40004 | 收件人地址 to 不能为空 |
| 40005 | 收件人地址 to 格式不正确 |
| 40006 | 默认回复地址 reply_to 格式不正确 |
| 40007 | 余额不足或账号被禁用 |
| 40008 | data 格式错误 |
| 40009 | 不支持的文件类型或附件大小不能超过 1MB |

## 开发规范

本项目遵循以下开发规范：
- PEP 8 Python 代码规范
- 函数式编程风格
- 参数验证与业务逻辑分离
- 统一的错误处理机制

## 许可证

MIT