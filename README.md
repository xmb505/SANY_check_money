# sany_check_money

三一工学院自动查询水电费脚本

## 项目简介

`sany_check_money` 是一个功能强大的Python脚本项目，专为三一工学院学生设计，用于自动查询宿舍水电费信息。该项目通过模拟学校网站的登录和数据查询过程，实现了自动化的水电费信息获取，并提供邮件预警、数据库存储、Web可视化界面等丰富功能。

对于经常忘记查询水电费余额而导致停电停水的同学，这个项目可以帮助你实时监控余额并在低于设定阈值时自动发送邮件提醒，让你及时充值，避免影响正常生活。

## 核心功能

### 🔍 自动查询
- **用户登录**：通过 `login.py` 脚本自动完成用户登录，获取必要凭证
- **数据获取**：通过 `get_data.py` 脚本查询详细的水电费使用情况和当前余额
- **分页查询**：通过 `check_data.py` 脚本支持分页查询所有设备数据

### 📧 智能预警
- **邮件通知**：支持两种邮件发送方式：
  - 基于SMTP协议的传统邮件发送 (`mail_sender.py`)
  - 基于Aoksend API的现代化邮件服务 (`monitor_aoksender.py`)
- **后台监控**：通过守护进程脚本实现无人值守的周期性监控：
  - SMTP方式：`monitor_daemon.py`
  - Aoksend API方式：`monitor_aoksender.py`
- **个性化配置**：支持自定义预警阈值、邮件模板和发送参数

### 💾 数据持久化
- **数据库存储**：通过 `data2sql.py` 脚本将查询到的数据存储到MySQL数据库
- **数据去重**：自动检测并避免重复插入相同时间点的数据
- **异常处理**：能够识别并标记异常数据（如时间为空的记录）
- **一键建表**：通过 `import.sql` 文件快速创建所需的数据库表结构

### 🌐 Web可视化
- **数据展示**：提供基于Web的图形化界面，直观展示水电费数据
- **多种模式**：支持用量、用钱、总量、余额等多种数据展示模式
- **交互查询**：支持设备搜索和自定义数据点数量
- **图表可视化**：通过图表直观展示数据变化趋势
- **邮件订阅**：支持用户订阅和解绑邮件通知服务
- **邮件余额显示**：实时显示剩余邮件数量

### ⚙️ 自动化执行
- **守护进程**：通过 `daemon.sh` 脚本实现周期性自动执行任务
- **灵活配置**：支持通过配置文件自定义执行间隔和命令

## 技术亮点

- **完全模拟**：精确模拟学校网站的登录和查询流程，包括参数加密和签名算法
- **无会话依赖**：通过URL参数维持用户验证，无需维护复杂的会话状态
- **模块化设计**：各功能模块独立，支持命令行调用，返回标准JSON格式数据，便于集成
- **高性能API**：Web后端采用连接池和线程池技术，显著提升查询性能
- **安全防护**：支持只读用户访问，输入参数验证，防止SQL注入
- **反向代理支持**：支持Nginx、Apache等反向代理环境

## 项目结构

```
sany_check_money/
├── login.py                 # 用户登录脚本
├── get_data.py              # 水电费数据查询脚本
├── check_data.py            # 分页设备数据查询脚本
├── data2sql.py              # 数据库存储脚本
├── daemon.sh                # 守护进程脚本
├── mail_sender.py           # SMTP邮件发送脚本
├── monitor_daemon.py        # SMTP监控守护进程
├── aoksend-api-cli.py       # Aoksend邮件API命令行工具
├── monitor_aoksender.py     # Aoksend监控守护进程
├── import.sql               # 数据库表结构导入文件
├── IFLOW.md                 # 项目开发过程和技术细节说明
├── config/                  # 配置文件目录
│   ├── mail_setting.ini     # SMTP邮件配置
│   ├── aoksender.ini        # Aoksend API配置
│   ├── daemon.ini           # 守护进程配置
│   ├── monitor_config.ini   # 监控配置
│   ├── mail_texter.txt      # 邮件模板
│   └── mysql.ini            # MySQL数据库配置
├── server/                  # Web后端服务
│   ├── server.py            # RESTful API服务
│   ├── email_api.py         # 邮件订阅API
│   ├── aokbalance_get.py    # Aoksend余额查询服务
│   └── *.ini                # 服务配置文件
└── web/                     # Web前端界面
    ├── index.html           # 主页面
    ├── main.js              # 主逻辑
    ├── styles.css           # 样式文件
    └── config.js            # 前端配置
```

## 快速开始

### 1. 环境准备

确保已安装Python 3.x和必要的依赖库：

```bash
pip install requests pymysql
```

### 2. 数据库配置

创建MySQL数据库并导入表结构：

```bash
mysql -h [服务器地址] -u [用户名] -p < import.sql
```

配置数据库连接信息：

```ini
# config/mysql.ini
[mysql]
mysql_server = your_mysql_host
mysql_port = 3306
login_user = your_username
login_passwd = your_password
db_schema = sany_check_money
```

### 3. 基础查询

登录获取用户信息：

```bash
python3 login.py <手机号> <密码>
```

查询水电费数据：

```bash
python3 get_data.py <appUserId> <roleId>
```

### 4. 数据存储

将数据存储到数据库：

```bash
./data2sql.py <appUserId> <roleId> [pageNum] [pageSize]
```

### 5. 邮件预警

配置邮件发送参数后，启动监控服务：

```bash
# SMTP方式
./monitor_daemon.py <账号> <密码>

# Aoksend API方式
./monitor_aoksender.py <账号> <密码>
```

### 6. Web服务

启动Web后端API服务：

```bash
cd server
python3 server.py
```

在浏览器中访问 `http://localhost:8080` 查看Web界面。

## 配置说明

项目使用多个配置文件来管理不同功能的参数。为了保护隐私和便于部署，所有配置文件都提供了示例模板（以`example_`开头的文件）。

### 配置文件列表

- `config/mysql.ini`：数据库连接配置
- `config/mail_setting.ini`：SMTP邮件发送配置
- `config/aoksender.ini`：Aoksend API配置
- `config/daemon.ini`：守护进程配置
- `config/monitor_config.ini`：数据监控配置
- `config/mail_texter.txt`：邮件模板文件
- `server/server.ini`：Web后端API服务配置
- `server/email_api.ini`：邮件订阅API配置
- `server/aokbalance_get.ini`：Aoksend余额查询服务配置
- `web/config.js`：Web前端配置

### 配置文件使用方法

1. 复制示例配置文件并重命名为实际使用的文件名：
   ```bash
   cp config/example_mysql.ini config/mysql.ini
   cp config/example_aoksender.ini config/aoksender.ini
   cp server/example_server.ini server/server.ini
   cp server/example_email_api.ini server/email_api.ini
   cp web/example_config.js web/config.js
   ```

2. 根据实际环境修改配置文件中的参数

3. 项目会自动忽略实际配置文件，确保敏感信息不会被上传到版本控制系统

详细配置说明请参考各配置文件内的注释。

## 使用场景

1. **个人监控**：学生个人使用，定期检查宿舍水电费余额
2. **宿舍管理**：宿舍管理员批量监控多个房间的水电费情况
3. **数据分析**：通过数据库存储的历史数据进行用量趋势分析
4. **系统集成**：作为其他自动化系统的一部分，提供水电费数据接口

## 注意事项

- 本项目仅供学习和研究目的使用
- 请遵守学校网站的使用条款和相关法律法规
- 不建议在生产环境中频繁使用本脚本，可能对学校服务器造成压力
- 使用分页查询时请合理设置pageSize，避免请求过大数据量
- 项目维护者不对因使用本脚本导致的任何后果承担责任

## 贡献

欢迎提交 Issue 和 Pull Request 来改进项目。

## 许可证

本项目仅供个人学习和研究使用。