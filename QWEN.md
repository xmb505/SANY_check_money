# QWEN.md

本项目指南，供 AI 编码助手在代码交互中使用。

## 项目概述

三一工学院宿舍水电费自动查询监控系统。通过模拟学校网站（sywap.funsine.com）的登录和数据查询流程（含参数签名算法），自动采集水电表读数存入 MySQL，提供 Web 可视化面板、邮件预警订阅、宿管模式等功能的单体 Python 项目。

### 核心技术栈

| 层级 | 技术 |
|------|------|
| 数据采集 | Python 3 + `requests` |
| 后端服务 | Python `http.server`（标准库，无 Web 框架） |
| 数据库 | MySQL + `pymysql`（带连接池） |
| 前端 | 原生 HTML/JS/CSS + Chart.js（无框架/无打包器） |
| 邮件通知 | SMTP 协议 或 Aoksend 第三方 API |
| 数据清洗 | 自定义管道：整点对齐 → 插值 → 用量计算 → 平滑异常 |

### 项目结构

```
/
├── debug_utils/             # 开发工具脚本
│   ├── login.py             # 学校网站登录（含 MD5 签名）
│   ├── get_data.py          # 单次查询水电费数据
│   ├── check_data.py        # 分页查询所有设备数据
│   ├── data2sql.py          # 将数据存入 MySQL（防止重复）
│   ├── mail_sender.py       # SMTP 邮件发送
│   ├── monitor_daemon.py    # SMTP 方式监控守护进程
│   ├── monitor_aoksender.py # Aoksend 方式监控守护进程
│   └── aoksend-api-cli.py   # Aoksend 邮件 API CLI 工具
├── daemon.sh                # Shell 守护进程（循环执行自定义命令）
├── config/                  # 根层配置（均为 gitignored，参考 example_* 文件）
│   ├── example_mysql.ini
│   ├── example_aoksender.ini
│   ├── example_daemon.ini
│   ├── example_mail_setting.ini
│   ├── example_monitor_config.ini
│   └── mail_texter.txt
├── data_cleaner/            # 数据清洗模块
│   ├── hourly_report.py     # 核心清洗算法
│   └── config/              # 清洗模块配置（example_config.ini, example_mysql.ini）
├── server/                  # 三个 HTTP 后端服务
│   ├── libs/                # 共享业务模块（所有服务和脚本的核心依赖）
│   │   ├── __init__.py      # 模块汇总，from server.libs import * 批量导入
│   │   ├── signer.py        # 签名算法和工具函数（MD5 + 字典序 + SHA）
│   │   ├── api_client.py    # 学校 API 调用封装（登录、账户查询、设备列表）
│   │   ├── aoksender.py     # Aoksend 邮件发送客户端（含余额查询）
│   │   └── db_pool.py       # MySQL 连接池（init_pool / get_connection）
│   ├── server.py            端口 8080 — 数据查询 API
│   ├── email_api.py         端口 8081 — 邮件订阅 API
│   ├── aokbalance_get.py    端口 8082 — Aoksend 余额查询
│   └── config_examples/     # 各服务配置文件模板
├── doc/                     # 文档
│   ├── API_DOC.md           # 完整 API 接口文档
│   ├── sql/                 # 数据库建表脚本
│   │   ├── import.sql       # 一键建表（device + data + email）
│   │   ├── device_table.sql
│   │   ├── data_table.sql
│   │   └── email_table.sql
│   ├── IFLOW.md
│   ├── IFLOW_debug.md
│   └── aoksend-api-cli.md
└── web/                     # 前端静态文件
    ├── index.html           # 主页面（三个标签页）
    ├── main.js              # 前端核心逻辑（2200+ 行）
    ├── styles.css           # 样式
    ├── example_config.js    # 前端配置模板（复制为 config.js 使用）
    └── config.js            # （gitignored）运行时配置
```

## 运行与开发

### 依赖安装

```bash
pip install requests pymysql
```

无虚拟环境要求，无构建工具，无包管理器配置。

### 启动服务

三个后端服务各自独立启动（均为 Python `http.server` 进程）：

```bash
python3 server/server.py              # 数据查询 API → 端口 8080
python3 server/email_api.py           # 邮件订阅 API → 端口 8081
python3 server/aokbalance_get.py      # Aoksend 余额查询 → 端口 8082
```

前端为 `web/` 目录下的静态文件，由 `server.py` 直接提供服务（或任意静态文件服务器）。访问 `http://localhost:8080`。

### 基础数据采集流程

```bash
python3 debug_utils/login.py <手机号> <密码>                # 获取 appUserId 和 roleId
python3 debug_utils/get_data.py <appUserId> <roleId>        # 查询设备电量数据
python3 debug_utils/check_data.py <appUserId> <roleId> [pageNum] [pageSize]  # 分页查询
python3 debug_utils/data2sql.py <appUserId> <roleId> [pageNum] [pageSize]    # 采集入库
```

### 邮件监控启动

```bash
# SMTP 方式（依赖 config/mail_setting.ini）
python3 debug_utils/monitor_daemon.py <账号> <密码>

# Aoksend API 方式（依赖 config/aoksender.ini）
python3 debug_utils/monitor_aoksender.py <账号> <密码>
```

### Shell 守护进程

```bash
bash daemon.sh   # 根据 config/daemon.ini 配置循环执行命令
```

### 语法检查

无测试框架、无 linter、无 type checker。

```bash
python3 -m py_compile <file.py>        # Python 语法检查
node --check <file.js>                 # JS 语法检查
```

## 架构

### 后端：Mode-Routed HTTP 服务

三个服务均使用 `http.server.BaseHTTPRequestHandler`，通过查询参数路由：

| 服务 | 端口 | 方法 | 路由方式 |
|------|------|------|----------|
| `server.py` | 8080 | GET | `mode` 查询参数 |
| `email_api.py` | 8081 | POST | `action` JSON 字段 |
| `aokbalance_get.py` | 8082 | GET | `action` 查询参数 |

所有接口返回 `Content-Type: application/json`，HTTP 200，业务状态在 `code` 字段。

### 数据库层

MySQL + `pymysql`，连接池大小为 30（3× 线程池大小）。`server/libs/db_pool.py` 提供统一的连接池管理，所有有数据库需求的服务均可复用。

核心表：

- **`device`** — 设备表（电表/水表），主键 `id`（varchar）
- **`data`** — 读数表，外键 `device_id` → `device.id`，联合索引 `(device_id, read_time)`，含 `unStandard` 异常标记
- **`email`** — 邮件订阅表，含验证码、有效期、预警阈值、解绑状态

### 共享业务模块 (`server/libs/`)

`server/libs/` 是项目的核心共享库，包含所有可复用的业务逻辑：

- **`signer.py`** — 签名算法（MD5 + 字典序排序 + `SIGN_KEY`），生成学校 API 请求签名
- **`api_client.py`** — 学校 API 封装：`login()`, `get_account_list()`, `get_device_list()`
- **`aoksender.py`** — Aoksend 邮件客户端：`send_email()`, `check_balance()`, `validate_email()`, `validate_file()`
- **`db_pool.py`** — MySQL 连接池：`init_pool()`, `init_pool_from_ini()`, `get_connection()`

所有后端服务和 debug_utils 脚本都通过导入此模块获取核心功能，不再使用 subprocess 进程调用。

### 数据清洗管道 (`data_cleaner/hourly_report.py`)

```
原始读数 → build_slot_max() → fill_missing_slots() → compute_usage_series() → smooth_zero_usage()
```

- `build_slot_max`: 按小时段取最大 `total_reading`，过滤≤0异常值 → `'direct'` / `'missing'`
- `fill_missing_slots`: 线性插值 → `'interpolated'`
- `compute_usage_series`: 用量 = 当前段 - 前一段，负值钳 0
- `smooth_zero_usage`: 检测"0 用量 + 累积邻居"模式（如 `[0.5, 0, 1.0]` → `[0.5, 0.5, 0.5]`）→ `'smoothed'`

清洗结果每条含 `(value, source)`，source ∈ `{'direct', 'missing', 'interpolated', 'smoothed'}`。

### 宿管模式

后端 `mode=check_hourly_building` 按楼栋返回逐小时用量，复用 `data_cleaner/hourly_report.py` 算法（通过 `sys.path.insert` 跨目录导入）。前端支持楼栋切换（1-10 跳 4）、状态过滤、用量阈值过滤、激增检测、日期范围（最长 7 天）。当日未来小时会被截断。

## 核心 API 端点

### server.py（端口 8080）

| mode 参数 | 说明 |
|-----------|------|
| `first_screen` | 随机返回设备 ID 列表（首页用） |
| `check` | 按 `device_id` + `data_num` 查最近 N 条读数 |
| `check_daily_range` | 按 `device_id` + 日期范围查每日最后读数 |
| `check_hourly_building` | 按 `building` + 日期范围查逐小时用量（宿管模式） |
| `search` | 按 `key_word` 搜索设备（需 ≥2 字符） |

### email_api.py（端口 8081）

| action | 说明 |
|--------|------|
| `reg` | 订阅注册，发送验证码邮件 |
| `enter_code` | 提交验证码完成验证 |
| `change_code` | 请求解绑，发送解绑验证码 |
| `enter_change` | 提交解绑验证码完成解绑 |

## 配置系统

每个服务读取同目录下的 `{name}.ini` 配置文件。示例模板以 `example_` 开头。实际配置文件均列在 `.gitignore` 中。

### 配置文件一览

| 服务/脚本 | 配置文件 | 关键配置节 |
|-----------|----------|-----------|
| `server.py` | `server/server.ini` | `[mysql]`, `[server]`, `[config]` |
| `email_api.py` | `server/email_api.ini` | `[server]`, `[email]`, `[mysql]`, `[aoksender]` |
| `aokbalance_get.py` | `server/aokbalance_get.ini` | `[aok]`, `[server]` |
| `monitor_aoksender.py` | `config/aoksender.ini` | `[aoksender]`, `[monitor]` |
| `monitor_daemon.py` | `config/monitor_config.ini` | `[data]` |
| `mail_sender.py` | `config/mail_setting.ini` | `[smtp]` |
| `daemon.sh` | `config/daemon.ini` | `rec_time`, `command` |
| `data_cleaner/hourly_report.py` | `data_cleaner/config/config.ini` | `[filter]`, `[align]`, `[output]`, `[filter_output]` |
| 前端 | `web/config.js` | API 地址、默认模式、UI 配置 |

### 配置初始化命令

```bash
cp server/config_examples/example_server.ini server/server.ini
cp config/example_mysql.ini config/mysql.ini
cp web/example_config.js web/config.js
# 然后编辑真实凭据
```

## 开发约定

### 编码风格

- 所有 Python 文件使用 `#!/usr/bin/env python3` + `# -*- coding: utf-8 -*-`
- 后端日志使用 `print(f"[INFO/WARN/ERROR] ...")` — 无 logging 框架
- 函数和类有中文文档字符串（Google 风格 `Args:` / `Returns:`）
- `data_cleaner/hourly_report.py` 有英文文档字符串（这是特例）

### 跨模块导入

**`server/libs/` 是共享核心库**，所有服务和 debug_utils 脚本都从此处导入：

```python
# debug_utils/*.py 中使用（通过 sys.path.insert 将 server/ 加入搜索路径）
from libs.api_client import login, get_account_list, get_device_list
from libs.aoksender import send_email, check_balance

# server/*.py 中直接 import（无需 sys.path.insert）
from libs.signer import generate_sign, get_timestamp
from libs.aoksender import send_email
```

**`data_cleaner/`** 是数据清洗专用模块，仅由 `server/server.py` 导入：

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data_cleaner'))
from hourly_report import (...)
```

新导入必须加在对应的 `sys.path.insert` 行下方。

### 数据库约定

- `device.id` 为 varchar(32)，从学校 API 返回
- `data.read_time` 精确到秒，`(device_id, read_time)` 联合唯一防重
- `data.unStandard=1` 表示 read_time 为空时用当前时间填充的异常记录
- 连接池 = `queue.Queue`，大小 = 3× 线程池大小（默认 30）
- 连接池使用 `DatabaseManager.get_connection()` 上下文管理器

### 前端约定

- Tab 切换：toggle `.tab.active` / `.tab-pane.active`
- 图表渲染：`prepareMiniChartData()` + `prepareChartData()` → Chart.js
- 四种展示模式：`usage` / `cost` / `total` / `balance`（宿管模式强制 `total`）
- 前端 `source` 字段：`direct`=真实数据，`interpolated`=插值填充，`smoothed`=平滑处理，`missing`=无数据
- 宿管模式使用客户端侧缓存 `dormDataCache`，切换楼栋不过滤时不再重新请求
- 配置通过全局 `window.DYNAMIC_CONFIG` 动态加载（`config.js`）

### 邮件速率限制

- 单邮箱最多绑定 25 条记录（`email_limit`）
- 单邮箱每日最多发送 100 封邮件（`email_daily_limit`）
- 订阅有效期：1 年（`life_end_time`）
- 解绑冷却期：24 小时
- 验证码有效期：5 分钟（`verifi_end_time`）

### 重要硬编码值

- 签名密钥：`SIGN_KEY = "DJKSBNW123"`
- 学校 API 基础地址：`http://sywap.funsine.com/prod-api/external/`
- 渠道 ID：`channelid = "1003"`
- 宿管模式楼栋白名单正则：`^(1|2|3|5|6|7|8|9|10)$`（楼栋 4 被排除）
- 前端搜索关键词至少 2 字符
- 设备类型：`0`=电表, `1`=水表
- `data_cleaner/hourly_report.py` 的 `--date-range` 模式每天输出一个独立 CSV 文件

### 安全与防护

- 所有真实配置被 `.gitignore` 忽略
- `server.py` 对 `device_id` 做正则白名单校验（`^[a-zA-Z0-9_]+$`，最长 50 字符）
- `server.py` 对 `data_num` 做范围限制（1-1000）
- 关键词搜索防注入：`LIKE %s` 参数化查询
- `email_api.py` 验证邮箱格式正则
- 支持 `X-Real-IP` / `X-Forwarded-For` 反向代理头
