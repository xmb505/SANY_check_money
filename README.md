# your_database_name_money

三一工学院自动查询水电费脚本

## 项目简介

`your_database_name_money` 是一个用于自动查询三一工学院水电费信息的Python脚本项目。该项目通过模拟学校网站的登录和数据查询过程，实现了自动化的水电费信息获取功能，并支持邮件预警功能。

## 功能特性

- **自动登录**：通过 `login.py` 脚本实现用户自动登录
- **数据查询**：通过 `get_data.py` 脚本获取水电费使用情况
- **签名算法**：实现了与学校网站完全一致的请求签名算法
- **模块化设计**：支持命令行调用，返回标准JSON格式数据
- **邮件预警**：当水电费余额低于阈值时自动发送邮件提醒
- **后台监控**：通过 `monitor_daemon.py` 脚本实现周期性自动监控
- **Aoksend邮件服务**：支持通过Aoksend API发送邮件，提供更灵活的邮件发送选项
- **Aoksend后台监控**：通过 `monitor_aoksender.py` 脚本实现基于Aoksend API的周期性自动监控
- **灵活配置**：支持通过配置文件自定义邮件和监控参数
- **易于集成**：脚本设计便于集成到其他自动化系统

## 技术特点

- 模拟学校网站的登录和查询流程
- 实现了与网站完全一致的参数加密和签名算法
- 无需维护会话状态，通过URL参数维持用户验证
- 采用标准的HTTP请求和JSON数据格式
- 支持多种邮件发送方式（SMTP和Aoksend API）
- 支持灵活的邮件模板和配置

## 文件说明

- `login.py` - 用户登录脚本，接收账号密码作为参数，返回登录结果
- `get_data.py` - 水电费数据查询脚本，接收用户ID和角色ID作为参数，返回水电费信息
- `mail_sender.py` - 邮件发送脚本（基于SMTP协议），自动获取数据并发送邮件通知
- `monitor_daemon.py` - 监控守护进程脚本（基于SMTP协议），按配置周期检查数据并发送预警邮件
- `aoksend-api-cli.py` - Aoksend邮件API命令行工具（来自 https://github.com/xmb505/aoksend-api-cli ），用于测试和调试邮件发送功能
- `monitor_aoksender.py` - 监控守护进程脚本（基于Aoksend API），按配置周期检查数据并发送预警邮件
- `mail_setting.ini` - SMTP邮件发送配置文件
- `config/aoksender.ini` - Aoksend邮件API配置文件
- `config/monitor_config.ini` - 数据监控配置文件
- `config/mail_texter.txt` - 邮件模板文件
- `IFLOW.md` - 项目开发过程和技术细节说明
- `config/example.txt` - 使用示例文件

## 使用方法

### 登录
```bash
python3 login.py <phone_number> <password>
```

### 查询水电费
```bash
python3 get_data.py <appUserId> <roleId>
```

### 发送邮件通知（SMTP方式）
```bash
./mail_sender.py <账号> <密码>
```

该命令会自动执行登录、获取数据并发送邮件的完整流程。

### 发送邮件通知（Aoksend API方式）
```bash
python3 aoksend-api-cli.py --app-key YOUR_KEY --template-id TEMPLATE_ID --to recipient@example.com
```

该命令通过Aoksend邮件API发送邮件，支持更多高级功能。`aoksend-api-cli.py` 也是本项目作者开发的工具，开源在另一个仓库，详细用法请移步 https://github.com/xmb505/aoksend-api-cli

### 后台监控服务（SMTP方式）
```bash
./monitor_daemon.py <账号> <密码>
```

该命令会启动后台监控服务，按照 `config/monitor_config.ini` 中配置的检查周期持续监控水电费余额，
当余额低于设定阈值时自动发送邮件通知。

### 后台监控服务（Aoksend API方式）
```bash
./monitor_aoksender.py <账号> <密码>
```

该命令会启动后台监控服务，按照 `config/aoksender.ini` 中配置的检查周期持续监控水电费余额，
当余额低于设定阈值时自动通过Aoksend API发送邮件通知。

## 配置文件

### mail_setting.ini
邮件发送配置文件（SMTP方式），包含SMTP服务器设置、用户名、密码等信息。
- `server`: SMTP服务器地址
- `port`: SMTP服务器端口 (465用于SSL, 587用于TLS)
- `username`: 发送邮件的用户名
- `password`: 发送邮件的密码或应用专用密码
- `sender`: 发件人邮箱地址
- `sender_name`: 发件人显示名称
- `receivers`: 收件人邮箱地址 (多个邮箱请用逗号分隔)
- `encryption`: 邮件加密方式 (ssl/tls)

### config/aoksender.ini
邮件发送配置文件（Aoksend API方式），包含Aoksend邮件API设置、API密钥、模板ID等信息。
- `server`: API地址（选填）
- `app_key`: API密钥
- `template_id`: 模板ID
- `to`: 收件人地址
- `reply_to`: 默认回复地址
- `alias`: 发件人名称
- `attachment`: 邮件附件路径
- `monitor_timer`: 循环检测时间，单位为秒
- `monitor_keyword`: JSON检测关键词，对应的数据必须是数字
- `monitor_start`: 低于数值触发程序阈值

### config/monitor_config.ini
数据监控配置文件（SMTP方式），包含检查周期、预警阈值等参数。
- `check_round`: 检查周期，单位为秒
- `ele_keyword`: 电表关键字，用于识别电表数据
- `ele_num`: 电表余额警报阈值
- `water_keyword`: 水表关键字，用于识别水表数据
- `water_num`: 水表余额警报阈值

### config/mail_texter.txt
邮件模板文件，可自定义邮件内容格式。支持使用{{DATA_SECTION}}占位符来插入水电费数据。

## 依赖项

- Python 3.x
- `requests` 库用于HTTP请求
- `hashlib` 库用于MD5加密
- `smtplib` 和 `email` 库用于邮件发送
- `configparser` 库用于配置文件解析
- `subprocess` 库用于脚本间调用
- `json` 库用于数据处理
- `time` 库用于时间处理
- `sys` 库用于系统操作
- `argparse` 库用于命令行参数解析

## 注意事项

- 本项目仅供学习和研究目的使用
- 请遵守学校网站的使用条款和相关法律法规
- 不建议在生产环境中频繁使用本脚本，可能对学校服务器造成压力
- 项目维护者不对因使用本脚本导致的任何后果承担责任
- 使用邮件功能时，请确保配置文件中的SMTP设置正确

## 贡献

欢迎提交 Issue 和 Pull Request 来改进项目。

## 许可证

本项目仅供个人学习和研究使用。