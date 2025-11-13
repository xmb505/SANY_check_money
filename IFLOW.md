# IFLOW.md - 三一工学院自动查询水电费脚本项目

## 项目概述

这是一个用于自动查询三一工学院水电费信息的Python脚本项目，项目名为`your_database_name_money`。主要功能包括：

1. **登录功能**：通过`login.py`脚本实现用户登录，并获取用户ID和角色ID等信息
2. **数据查询**：通过`get_data.py`脚本查询用户的水电费使用情况和余额
3. **分页数据查询**：通过`check_data.py`脚本支持分页查询设备数据
4. **数据库存储功能**：通过`data2sql.py`脚本将查询到的数据存储到MySQL数据库
5. **守护进程功能**：通过`daemon.sh`脚本实现周期性自动执行数据存储任务
6. **签名验证**：实现了与目标网站（sywap.funsine.com）完全一致的签名算法，确保请求能够通过验证
7. **模块化设计**：脚本支持命令行调用，并返回JSON格式数据，便于其他模块集成和扩展
8. **数据去重功能**：自动检测并避免重复插入相同时间点的数据
9. **异常数据识别**：能够识别并标记异常数据（如`currentDealDate`为null的记录）
10. **数据库表结构导入**：通过`import.sql`文件快速创建项目所需的数据库表结构
11. **邮件预警功能**：当水电费余额低于阈值时，自动发送邮件提醒用户
12. **后台监控功能**：通过`monitor_daemon.py`脚本实现周期性自动监控水电费余额
13. **Aoksend邮件服务集成**：新增基于Aoksend邮件API的邮件发送功能，提供更灵活的邮件发送选项

## 核心功能模块

### 1. 登录模块 (`login.py`)

- 使用MD5加密用户密码
- 生成符合网站要求的签名参数
- 发送登录请求并返回用户信息
- 支持命令行调用：`python3 login.py <手机号> <密码>`
- 返回JSON格式的登录结果，包含用户ID(appUserId)和角色ID(roleId)等关键信息

### 2. 数据查询模块 (`get_data.py`)

- 使用用户ID和角色ID查询水电费数据
- 实现与网站完全一致的签名算法
- 支持命令行调用：`python3 get_data.py <appUserId> <roleId>`
- 返回JSON格式的水电费数据，包含房间信息、使用量、余额等详细信息

### 3. 分页数据查询模块 (`check_data.py`)

- 支持分页查询设备数据
- 使用`appUserId`和`roleKey`参数查询设备信息
- 支持`pageNum`和`pageSize`参数控制分页
- `pageNum`一般设为1，`pageSize`学校未设置限制，但请合理使用，避免请求过大数据量
- 返回JSON格式的设备数据，包含设备ID、名称、状态、余额等信息
- 支持命令行调用：`./check_data.py <appUserId> <roleKey> [pageNum] [pageSize]`

### 4. 数据库存储模块 (`data2sql.py`)

- 将查询到的设备数据存储到MySQL数据库
- 自动创建和维护两个数据表：`device`（设备信息表）和`data`（读数数据表）
- 支持数据去重，避免重复插入相同时间点的数据
- 能够识别并标记异常数据（如`currentDealDate`为null的记录）
- `pageNum`一般设为1，`pageSize`学校未设置限制，但请合理使用，避免请求过大数据量
- 支持命令行调用：`./data2sql.py <appUserId> <roleId> [pageNum] [pageSize]`

### 5. 守护进程模块 (`daemon.sh`)

- 读取配置文件并执行命令的守护进程脚本
- 支持配置文件`config/daemon.ini`设置执行间隔和命令
- 无限循环执行指定的命令
- 提供执行日志和错误处理
- 支持通过Ctrl+C停止脚本

### 6. 数据库表结构导入 (`import.sql`)

- 快速创建项目所需的数据库表结构
- 包含完整的`device`表和`data`表定义
- 包含必要的索引和外键约束
- 支持一键导入数据库表结构
- 使用方法：`mysql -h [服务器地址] -u [用户名] -p < import.sql`

### 7. 邮件预警模块

- 监控水电费余额，当低于预设阈值时自动发送邮件提醒
- 使用`mail_sender.py`脚本处理邮件发送逻辑（基于SMTP协议）
- 使用`mail_setting.ini`配置邮件发送参数
- 使用`mail_texter.txt`定义邮件模板格式
- 使用`monitor_config.ini`配置监控参数
- 支持多设备监控（电表和水表）

### 8. Aoksend邮件服务模块

- 基于Aoksend邮件API的邮件发送功能
- 提供命令行工具`aoksend-api-cli.py`用于测试和调试
- 支持配置文件`config/aoksender.ini`管理API参数
- 支持模板数据和附件发送
- 提供更灵活的邮件发送选项

### 9. 后台监控模块 (`monitor_daemon.py`)

- 按照配置周期持续监控水电费余额
- 使用`monitor_config.ini`配置检查周期和预警阈值
- 当检测到余额低于阈值时，自动调用`mail_sender.py`发送预警邮件
- 支持命令行调用：`./monitor_daemon.py <账号> <密码>`
- 实现无人值守的自动化监控功能

### 10. Aoksend后台监控模块 (`monitor_aoksender.py`)

- 按照配置周期持续监控水电费余额
- 使用`config/aoksender.ini`配置检查周期和预警阈值
- 当检测到余额低于阈值时，自动调用Aoksend API发送预警邮件
- 支持命令行调用：`./monitor_aoksender.py <账号> <密码>`
- 实现无人值守的自动化监控功能
- 逐个设备检查并发送邮件，确保每封邮件只包含单个设备的信息

## 核心技术实现

### 签名算法详解

签名算法是本项目的核心技术，完全模拟了目标网站的JavaScript实现：

- **签名密钥**：`DJKSBNW123`
- **算法流程**：
  1. 按参数名的字典序排序
  2. 将参数名和参数值都转换为大写
  3. 拼接成`KEY=VALUE&`格式
  4. 在末尾添加签名密钥
  5. 对拼接后的字符串进行MD5加密生成签名
- **时间戳格式**：`YYYYMMDDHHmmss`
- **渠道ID**：固定值`1003`

### 会话管理机制

本项目采用特殊的会话管理机制，不同于传统的Cookie方式：

- 通过URL参数维持会话状态
- 关键参数包括：`appUserId`、`roleId`、`channelid`、`timestamp`、`sign`
- 每次请求都需要重新生成签名，确保请求的有效性

### 数据库设计

#### device表（设备信息表）
存储设备的基本信息，包括设备ID、名称、类型、状态等。

字段说明：
- `id`：设备ID，主键
- `addr`：表地址编码
- `equipmentName`：设备名称/位置描述
- `installationSite`：物理安装点
- `equipmentType`：设备类型（0=电表，1=水表）
- `ratio`：互感器倍率
- `rate`：单价（元/度或元/吨）
- `acctId`：财务账户号
- `status`：设备状态（0=停用，1=启用）
- `properties`：扩展属性，JSON格式
- `created_at`：首次入库时间
- `updated_at`：档案变更时间

#### data表（读数数据表）
存储设备的读数数据，包括时间点、读数、余额等。

字段说明：
- `id`：自增主键
- `device_id`：设备ID，外键关联device表
- `read_time`：表底时间（currentDealDate）
- `total_reading`：表底累积量
- `diff_reading`：距上次用量（程序计算）
- `remainingBalance`：余额（可为负值）
- `equipmentStatus`：设备状态（1=开，0=关，NULL=未知）
- `created_at`：本行写入时间
- `remark`：异常备注
- `unStandard`：非标准标记（0=标准，1=非标准）

## 项目文件说明

- `login.py`：用户登录脚本，接收手机号和密码作为参数，返回登录结果（包含appUserId和roleId）
- `get_data.py`：水电费数据查询脚本，接收appUserId和roleId作为参数，返回水电费详细信息
- `check_data.py`：分页设备数据查询脚本，支持pageNum和pageSize参数
- `data2sql.py`：数据存储脚本，将查询到的数据存储到MySQL数据库
- `daemon.sh`：守护进程脚本，根据配置文件重复执行命令
- `import.sql`：数据库表结构导入文件，用于快速创建项目所需的数据库表结构
- `mail_sender.py`：邮件发送脚本（基于SMTP协议），接收账号和密码参数，自动获取数据并发送邮件
- `monitor_daemon.py`：后台监控脚本（基于SMTP协议），周期性检查水电费余额并在低于阈值时发送预警邮件
- `aoksend-api-cli.py`：Aoksend邮件API命令行工具，用于测试和调试邮件发送功能
- `monitor_aoksender.py`：后台监控脚本（基于Aoksend API），周期性检查水电费余额并在低于阈值时发送预警邮件
- `mail_setting.ini`：SMTP邮件发送配置文件
- `config/aoksender.ini`：Aoksend邮件API配置文件
- `config/daemon.ini`：守护进程配置文件
- `config/monitor_config.ini`：数据监控配置文件
- `config/mail_texter.txt`：邮件模板文件
- `config/example.txt`：使用示例文件
- `config/mysql.ini`：MySQL数据库连接配置文件
- `README.md`：项目介绍和使用说明文档
- `IFLOW.md`：项目开发过程和技术细节说明文档
- `aoksend-api-cli.md`：Aoksend API CLI工具使用说明文档

## 使用方法示例

### 登录获取用户信息
```bash
python3 login.py your_phone_number your_password
```

返回示例：
```json
{
  "msg": "操作成功",
  "code": 200,
  "user": {
    "appUserId": "12345",
    "phoneNum": "your_phone_number",
    "password": "想看密码吗？没门",
    "roleId": 201,
    "roleWxPayChannel": "1"
  }
}
```

### 查询水电费数据
```bash
python3 get_data.py 12345 201
```

返回示例：
```json
{
  "total": 2,
  "rows": [
    {
      "acctName": "学1栋101室电表",
      "currentDealDate": "2025-10-30 00:00:00",
      "remainingBalance": 50.00,
      "equipmentStatus": "开"
    },
    {
      "acctName": "学1栋101室水表",
      "currentDealDate": "2025-10-30 00:00:00",
      "remainingBalance": 30.00,
      "equipmentStatus": "开"
    }
  ],
  "code": 200,
  "msg": "查询成功"
}
```

### 分页查询设备数据
```bash
./check_data.py 20241231000020 201 1 50
```

返回示例：
```json
{
  "total": 4297,
  "rows": [
    {
      "id": "24831",
      "addr": "000000078445",
      "equipmentName": "7栋6楼楼道中间大厅饮水机",
      "installationSite": "7栋6楼楼道中间大厅",
      "equipmentType": "0",
      "ratio": "40",
      "rate": "0.6190",
      "remainingBalance": "-2619.789200",
      "acctId": "20220805000452",
      "equipmentStatus": "开",
      "equipmentLatestLarge": null,
      "equipmentCurrentLarge": "684.92",
      "currentDealDate": "2025-11-12 10:05:46",
      "status": "0",
      "properties": null,
      "deviceName": null
    }
  ],
  "code": 200,
  "msg": "查询成功"
}
```

### 导入数据库表结构
```bash
mysql -h [服务器地址] -u [用户名] -p < import.sql
```

该命令会创建项目所需的数据库和表结构，包括device表和data表。

### 存储数据到数据库
```bash
./data2sql.py 20241231000020 201 1 100
```

该命令会自动：
1. 调用`check_data.py`获取设备数据
2. 连接MySQL数据库
3. 将设备信息存储到`device`表
4. 将读数数据存储到`data`表
5. 自动去重，避免重复插入相同时间点的数据
6. 识别并标记异常数据（如`currentDealDate`为null的记录）

### 守护进程运行
```bash
./daemon.sh
```

该命令会：
1. 读取`config/daemon.ini`配置文件
2. 根据配置的`rec_time`参数设置重复执行间隔
3. 执行配置的`command`命令
4. 无限循环执行，每次执行后等待指定时间

### 发送邮件通知（SMTP方式）
```bash
./mail_sender.py <账号> <密码>
```

该命令会自动：
1. 调用`login.py`进行登录
2. 使用获取的用户信息调用`get_data.py`获取水电费数据
3. 使用`mail_texter.txt`模板生成邮件内容
4. 根据`mail_setting.ini`配置发送邮件

### 发送邮件通知（Aoksend API方式）
```bash
python3 aoksend-api-cli.py --app-key YOUR_KEY --template-id TEMPLATE_ID --to recipient@example.com
```

### 后台监控服务（SMTP方式）
```bash
./monitor_daemon.py <账号> <密码>
```

该命令会启动后台监控服务，按照 `monitor_config.ini` 中配置的检查周期持续监控水电费余额，
当余额低于设定阈值时自动发送邮件通知。

### 后台监控服务（Aoksend API方式）
```bash
./monitor_aoksender.py <账号> <密码>
```

该命令会启动后台监控服务，按照 `config/aoksender.ini` 中配置的检查周期持续监控水电费余额，
当余额低于设定阈值时自动通过Aoksend API发送邮件通知。

## 配置文件说明

### mail_setting.ini
邮件发送配置文件，包含：
- SMTP服务器地址
- 端口
- 用户名和密码
- 发件人和收件人信息
- 邮件加密方式

### config/aoksender.ini
Aoksend邮件API配置文件，包含：
- API地址
- API密钥
- 模板ID
- 收件人地址
- 默认回复地址
- 发件人名称
- 邮件附件
- 监控参数（检查周期、监控关键词、阈值）

示例配置：
```ini
# 邮件发送配置
[aoksender]
# API地址(选填)
server = 
# API密钥
app_key = 
# 模板ID
template_id = 
# 收件人地址
to = 
# 默认回复地址
reply_to = 
# 发件人名称
alias = 三一工学院水电费监控系统
# 邮件附件, 仅专业版可用；发送附件时, 必须使用 multipart/form-data 进行 post 提交 (表单提交)
attachment =

# 水电费监控限制（这里不再区分水电费，而是直接对于json表里所有的设备直接遍历，谁低于设定值就出发邮件）
[monitor]
# 循环检测时间，单位为秒
monitor_timer = 3600
# JSON检测关键词条，这里词条对应的数据必须是数字，非数字会导致程序出错
monitor_keyword = remainingBalance
# 低于数值触发程序阈值
monitor_start = 10
```

### config/daemon.ini
守护进程配置文件，包含：
- 执行间隔时间
- 需要执行的命令

示例配置：
```ini
[daemon]
# 重复时间，单位为秒
rec_time = 3600
command = './data2sql.py 20251112000004 201 1 5000'
```

### config/monitor_config.ini
数据监控配置文件，包含：
- 检查周期（秒）
- 电表和水表的关键字识别
- 预警阈值设置

示例配置：
```ini
# 数据监控配置
[data]
# 检查周期，单位为秒
check_round = 3600
# 电表关键字，用于识别电表数据
ele_keyword = 电表
# 电表余额警报阈值
ele_num = 10
# 水表关键字，用于识别水表数据
water_keyword = 水表
# 水表余额警报阈值
water_num = 10
```

### config/mysql.ini
MySQL数据库连接配置文件，包含：
- 数据库服务器地址
- 端口号
- 登录用户名
- 数据库名称

示例配置：
```ini
[mysql]
mysql_server = 
mysql_port = 3306
login_user = 
db_schema = 
```

## 依赖项和环境要求

- Python 3.x
- `requests` 库用于HTTP请求
- `hashlib` 库用于MD5加密
- `json` 库用于数据格式处理
- `time` 库用于生成时间戳
- `sys` 库用于命令行参数处理
- `smtplib` 和 `email` 库用于邮件发送（邮件预警功能）
- `configparser` 库用于配置文件解析
- `subprocess` 库用于脚本间调用
- `argparse` 库用于命令行参数解析
- `pymysql` 库用于MySQL数据库连接（需要安装pip）
- `pip` 用于安装Python包（连接MySQL数据库需要）

## 项目特点和优势

1. **完全模拟网站行为**：所有请求参数和签名算法都与目标网站完全一致
2. **模块化设计**：登录、查询、邮件发送和监控功能分离，便于独立使用和扩展
3. **命令行友好**：支持命令行直接调用，返回标准JSON格式数据
4. **易于集成**：返回的数据格式便于其他系统集成和处理
5. **无会话依赖**：通过参数签名机制，无需维护复杂的会话状态
6. **智能预警**：新增邮件预警功能，及时提醒用户充值
7. **灵活配置**：支持通过配置文件自定义邮件和监控参数
8. **多种邮件发送方式**：支持传统的SMTP邮件发送和现代化的Aoksend API邮件发送
9. **后台监控**：支持无人值守的自动化监控功能
10. **精细化监控**：`monitor_aoksender.py`支持逐个设备检查，每封邮件只包含单个设备的信息
11. **数据持久化**：支持将查询数据存储到MySQL数据库，便于历史数据分析
12. **数据去重**：自动检测并避免重复插入相同时间点的数据
13. **异常数据识别**：能够识别并标记异常数据，如`currentDealDate`为null的记录
14. **快速部署**：通过`import.sql`文件快速创建数据库表结构
15. **定时任务支持**：通过`daemon.sh`脚本实现周期性任务执行

## 后续扩展建议

1. **Web界面**：开发Web界面，提供更友好的查询和展示方式
2. **定时任务**：使用cron等工具设置定时任务，实现自动化查询和预警
3. **多用户支持**：扩展系统以支持多个用户的水电费监控
4. **移动端应用**：开发移动端应用，方便用户随时查看水电费情况
5. **数据可视化**：添加数据图表功能，展示历史使用趋势
6. **多邮件服务支持**：扩展支持更多的邮件服务提供商
7. **数据备份**：实现数据库定期备份功能，确保数据安全
8. **性能优化**：优化数据库查询性能，支持更大规模的数据存储和查询

## 技术难点和解决方案

### 签名算法逆向工程
- **难点**：网站的签名算法较为复杂，且与标准实现略有差异
- **解决方案**：通过仔细分析网站JavaScript代码，完全模拟其实现过程

### 参数处理
- **难点**：参数的大小写处理和拼接顺序有特殊要求
- **解决方案**：严格按照网站的处理方式，先转大写再拼接

### 时间戳一致性
- **难点**：签名生成和请求发送需要使用相同的时间戳
- **解决方案**：在函数内部获取时间戳，确保一致性

### 邮件模板设计
- **难点**：需要设计灵活的邮件模板以适应不同设备的监控需求
- **解决方案**：使用占位符和`{{DATA_SECTION}}`系统，动态生成邮件内容
- **优化**：使用`{{DATA_SECTION}}`占位符避免注释中标签冲突问题

### 模块化设计
- **难点**：需要将登录、数据获取、邮件发送和监控功能分离
- **解决方案**：创建独立的脚本模块，通过`subprocess`调用协调使用

### 后台监控实现
- **难点**：需要实现周期性检查并在满足条件时触发邮件发送
- **解决方案**：使用`while True`循环配合`time.sleep()`实现周期性检查，通过配置文件控制检查周期

### Aoksend API集成
- **难点**：需要实现与第三方邮件服务API的集成
- **解决方案**：创建独立的CLI工具和配置文件，通过API密钥和模板ID实现邮件发送功能

### 数据库集成
- **难点**：需要设计合理的数据库表结构并实现数据的高效存储和查询
- **解决方案**：创建两个表分别存储设备信息和读数数据，通过外键关联，实现数据的高效存储和查询
- **系统要求**：需要安装pip来连接MySQL数据库

### 数据去重
- **难点**：需要避免重复插入相同时间点的数据
- **解决方案**：在插入数据前检查是否已存在相同的`device_id`和`read_time`组合，如果存在则跳过插入

### 异常数据处理
- **难点**：部分设备数据可能存在异常，如`currentDealDate`为null
- **解决方案**：识别这些异常数据并标记为非标准，同时用当前时间替换null值以确保数据完整性

### 分页查询优化
- **难点**：避免请求过大的数据量影响系统性能
- **解决方案**：`pageNum`一般设为1，`pageSize`学校未设置限制，但建议合理使用，避免请求过大数据量

### 数据库表结构导入
- **难点**：为用户提供快速创建数据库表结构的方法
- **解决方案**：创建`import.sql`文件，包含完整的数据库表结构定义，支持一键导入

### 守护进程实现
- **难点**：实现周期性自动执行任务的功能
- **解决方案**：创建`daemon.sh`脚本，读取配置文件并无限循环执行指定命令