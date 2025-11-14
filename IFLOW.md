# IFLOW.md - 三一工学院自动查询水电费脚本项目

## 项目概述

这是一个用于自动查询三一工学院水电费信息的Python脚本项目，项目名为`sany_check_money`。该项目通过模拟学校网站的登录和数据查询过程，实现了自动化的水电费信息获取功能，并支持邮件预警功能和Web可视化界面。

主要功能包括：

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
14. **Web可视化界面**：新增Web前端界面，提供数据可视化展示和交互式查询功能
15. **高性能RESTful API服务**：新增后端API服务，为Web界面提供数据支持，支持连接池、线程池和输入验证
16. **反向代理支持**：支持通过X-Real-IP和X-Forwarded-For头部获取真实客户端IP，适用于Nginx/Apache等反向代理环境
17. **动态配置加载**：Web前端支持动态加载配置文件，避免浏览器缓存问题
18. **响应式设计**：Web界面支持响应式布局，在不同设备上都能良好显示
19. **文本溢出处理**：优化了设备名称过长时的显示效果，使用省略号代替换行
20. **邮件订阅和解绑系统**：新增完整的邮件订阅和解绑功能，包含验证码验证机制和用户友好的前端界面
21. **返回首页按钮**：Web界面添加了返回首页按钮，方便用户从搜索结果返回首页
22. **Aoksend余额查询服务**：新增独立的Aoksend余额查询服务，可查询API账户余额
23. **邮件余额显示功能**：在Web界面页脚中实时显示剩余邮件数量，提升用户体验

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

### 11. Web可视化模块

- 提供基于Web的图形化界面，用于展示水电费数据
- 支持多种数据展示模式（用量模式、用钱模式、总量模式、余额模式）
- 支持数据点数量自定义（5、10、20、50、100或自定义）
- 支持设备搜索功能
- 提供数据图表展示功能
- 支持设备详细信息查看
- 支持响应式设计，在不同设备上都能良好显示
- 优化了设备名称过长时的显示效果，使用省略号代替换行
- **新增：添加了返回首页按钮**，点击可清空搜索框并返回首页数据
- **新增：邮件余额显示功能**，在页脚实时显示剩余邮件数量

### 12. 高性能RESTful API服务模块 (`server/server.py`)

- 提供后端API服务，为Web界面提供数据支持
- 支持设备数据查询接口
- 支持设备搜索接口
- 支持数据统计接口
- 使用MySQL数据库作为数据源
- 支持配置化部署
- **性能优化特性**：
  - 实现了数据库连接池机制，减少连接建立开销
  - 使用线程池并行处理多个请求
  - 对查询参数进行输入验证，防止SQL注入
  - 实现了高效的缓存机制
  - 支持只读用户访问，提高安全性
- **反向代理支持特性**：
  - 支持通过X-Real-IP和X-Forwarded-For头部获取真实客户端IP
  - 日志记录中显示真实客户端IP地址，便于分析请求来源
  - 适用于Nginx、Apache等反向代理环境

### 13. 邮件订阅和解绑系统模块 (`server/email_api.py`)

- 提供完整的邮件订阅和解绑功能
- **API功能模块**：
  - **注册模式 (reg)**：处理用户订阅请求
    - 验证邮箱格式、设备类型和设备存在性
    - 检查邮箱使用次数限制(默认25次)
    - 检查是否有未过期的验证记录或正常可用的记录
    - 插入新记录并发送验证邮件
    - 返回`{"code": 200, "set_client_mode": "wait_user_verifi"}`

  - **验证码验证模式 (enter_code)**：验证用户输入的注册验证码
    - 验证邮箱格式和必需参数
    - 查找验证活跃的条目(验证码未过期且未验证)
    - 验证验证码是否正确
    - 更新验证状态
    - 返回验证结果

  - **解绑请求模式 (change_code)**：处理解绑请求
    - 验证参数和邮箱格式
    - 检查24小时内是否已请求过解绑
    - 检查用户是否有正在使用的订阅
    - 更新记录的updated_time并发送解绑验证码邮件
    - 返回`{"code": 200, "set_client_mode": "wait_user_change"}`

  - **解绑验证码验证模式 (enter_change)**：验证用户输入的解绑验证码
    - 验证参数和邮箱格式
    - 查找对应的订阅记录
    - 验证解绑验证码是否正确
    - 更新记录，标记为已解绑
    - 返回验证结果

- **数据库设计**：
  - **email表**：存储邮箱订阅信息
    - `id`：自增主键
    - `email`：邮箱地址
    - `uuid`：唯一标识符
    - `device_id`：设备ID
    - `verifi_code`：验证验证码
    - `verifi_end_time`：验证验证码过期时间（自动计算为created_time + 300秒）
    - `life_end_time`：生命周期结束时间（自动计算为created_time + 1年）
    - `ip_address`：IP地址
    - `alarm_num`：预警阈值
    - `equipment_type`：设备类型（0=电表，1=水表）
    - `change_code`：解绑验证码
    - `verifi_statu`：验证状态（0=未验证，1=已验证）
    - `change_device_statu`：解绑状态（0=未解绑，1=已解绑）
    - `created_time`：创建时间
    - `updated_time`：更新时间

- **前端实现 (`web/index.html`, `web/main.js`)**：
  - 每个设备卡片添加邮件图标按钮
  - 点击后弹出订阅模态框，询问邮箱和预警阈值
  - 支持订阅和解绑双重功能
  - 解绑按钮为红色，位于订阅按钮右侧
  - 验证码验证界面
  - 成功/失败状态反馈
  - 防止成功状态被后续错误信息覆盖的机制

- **安全机制**：
  - 邮箱使用次数限制(默认25次)
  - 验证码冷却期检查(5分钟)
  - 解绑请求24小时限制
  - 设备类型匹配验证
  - 邮箱格式验证
  - 防止验证码被后续错误覆盖的安全机制

### 14. Aoksend余额查询服务模块 (`server/aokbalance_get.py`)

- 提供独立的Aoksend API余额查询服务
- 通过POST请求向Aoksend API发送app_key获取账户余额
- 支持配置文件`server/aokbalance_get.ini`管理API参数
- 通过GET请求返回Aoksend账户余额信息
- 以服务器身份挂载后台，浏览器访问对应端口即可获取余额信息
- 支持跨域访问（CORS）

### 15. 邮件余额显示功能模块

- 在Web界面页脚添加剩余邮件数量显示
- 通过API调用获取Aoksend账户余额信息
- 支持配置文件`web/config.js`中的`EMAIL_BALANCE_API_URL`配置项
- 显示格式为：`{"message": "请求成功", "code": 200, "account": 24968}`
- 在前端页脚中显示为"免费预警邮件数量: [数量]"
- 提供错误处理机制，当API调用失败时显示"获取失败"
- 使用JavaScript异步获取并显示数据
- 支持亮色和暗色模式下的样式显示

## 配置文件处理方式更新

为了保护用户隐私并便于项目部署，项目采用了新的配置文件处理方式：

1. **示例配置文件**：所有配置文件都提供了示例模板，文件名以`example_`开头
2. **敏感信息保护**：实际配置文件包含敏感信息，已被添加到`.gitignore`文件中，不会被上传到版本控制系统
3. **配置文件使用方法**：
   - 复制示例配置文件并重命名为实际使用的文件名
   - 根据实际环境修改配置文件中的参数
   - 项目会自动忽略实际配置文件，确保敏感信息不会被上传

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

#### email表（邮箱订阅表）
存储用户邮箱订阅信息，用于预警通知。

字段说明：
- `id`：自增主键
- `email`：邮箱地址
- `uuid`：唯一标识符
- `device_id`：设备ID
- `verifi_code`：验证验证码
- `verifi_end_time`：验证验证码过期时间
- `verifi_statu`：验证状态（0=未验证，1=已验证）
- `life_end_time`：生命周期结束时间
- `change_device_statu`：解绑状态（0=正常，1=已解绑）
- `created_time`：创建时间
- `updated_time`：更新时间
- `ip_address`：IP地址
- `alarm_num`：预警阈值
- `equipment_type`：设备类型（0=电表，1=水表）
- `change_code`：解绑验证码

### 高性能API实现

#### 数据库连接池机制
- 创建固定大小的连接池（默认10个连接）
- 复用数据库连接，减少连接建立和关闭的开销
- 支持连接自动恢复机制

#### 线程池并行处理
- 使用线程池处理多个并发请求
- 提高系统并发处理能力
- 合理控制线程数量，避免资源耗尽

#### 输入验证与安全
- 对所有输入参数进行验证和过滤
- 使用正则表达式验证参数格式
- 防止SQL注入攻击

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
- `server/server.py`：Web后端API服务（高性能版本，支持连接池和线程池）
- `server/server.ini`：API服务配置文件
- `server/email_api.py`：邮件订阅系统后端API（支持订阅、验证、解绑功能）
- `server/email_api.ini`：邮件API服务配置文件
- `server/aokbalance_get.py`：Aoksend余额查询服务
- `server/aokbalance_get.ini`：Aoksend余额查询服务配置文件
- `web/`：Web前端文件目录
  - `index.html`：Web界面主页面
  - `main.js`：Web界面主逻辑
  - `styles.css`：Web界面样式
  - `config.js`：Web界面配置文件
  - `chart.js`：图表库文件

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

### 启动Web服务
```bash
cd server
python3 server.py
```

该命令会启动Web后端API服务，默认监听8080端口。

### 启动邮件订阅API服务
```bash
cd server
python3 email_api.py
```

该命令会启动邮件订阅系统API服务，默认监听8081端口。

### 启动Aoksend余额查询服务
```bash
cd server
python3 aokbalance_get.py
```

该命令会启动Aoksend余额查询服务，默认监听8082端口。

### 访问Web界面
在浏览器中打开 `http://localhost:8080` 即可访问Web界面。

### 创建只读数据库用户
为提高安全性，可以创建只读用户：
```sql
-- 创建只读用户
CREATE USER 'sany_check_viewer'@'%' IDENTIFIED BY 'secure_password';
-- 授予只读权限
GRANT SELECT ON sany_check.* TO 'sany_check_viewer'@'%';
-- 刷新权限
FLUSH PRIVILEGES;
```

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
app_key = YOUR_API_KEY_HERE
# 模板ID
template_id = YOUR_TEMPLATE_ID_HERE
# 收件人地址
to = your_email@example.com
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

### server/email_api.ini
邮件订阅API服务配置文件，包含：
- 服务器端口
- 邮件限制次数
- 数据库连接信息
- Aoksend邮件服务配置

示例配置：
```ini
[server]
port = 8081

[email]
# 表记录中同一个邮件最多出现次数，超过此值拒绝服务
email_limit = 25

[mysql]
mysql_server = your_mysql_host
mysql_port = 3306
login_user = your_username
login_passwd = your_password
db_schema = sany_check

[aoksender]
# API地址(选填)
server = 
# API密钥
app_key = YOUR_API_KEY_HERE
# 模板ID
template_id = YOUR_TEMPLATE_ID_HERE
# 默认回复地址
reply_to = 
# 发件人名称
alias = 新毛云
# 邮件附件, 仅专业版可用；发送附件时, 必须使用 multipart/form-data 进行 post 提交 (表单提交)
attachment =
# 模板中验证码字段名
verifi_code = code
# 模板中用户注册操作的字段名
verifi_email_statu = email_mode
# 模板中解绑码字段名
change_code = code
# 模板中用户解绑操作的字段名
change_email_statu = email_mode
# 模板ID
change_template_id = YOUR_CHANGE_TEMPLATE_ID_HERE
```

### server/aokbalance_get.ini
Aoksend余额查询服务配置文件，包含：
- 服务器端口
- Aoksend API地址
- API密钥

示例配置：
```ini
[server]
port = 8082

[aok]
api_address = https://www.aoksend.com/index/api/check_account
app_key = YOUR_APP_KEY_HERE
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
login_passwd = 
db_schema = 
```

### server/server.ini
Web后端API服务配置文件，包含：
- 数据库连接信息
- 服务器端口
- 其他配置参数

示例配置：
```ini
[mysql]
mysql_server = your_mysql_host
mysql_port = 3306
login_user = your_username
login_passwd = your_password
db_schema = sany_check_money

[server]
port = 8080

[config]
first_screen_count = 6
```

### web/config.js
Web前端配置文件，包含：
- API服务器地址和端口
- 邮件API服务器地址和端口
- 请求超时时间
- 默认数据量和模式
- 界面显示配置
- **新增：邮件余额查询API地址配置**

示例配置：
```javascript
// 配置文件 - 为动态加载设计
window.DYNAMIC_CONFIG = {
    // API服务器地址和端口
    API_BASE_URL: 'https://check_api.your_mysql_host',
    
    // 邮件API服务器地址和端口
    EMAIL_API_BASE_URL: 'http://192.168.1.3:8081',  // 使用http协议，因为邮件API服务器使用http
    
    // 剩余邮件查询API地址
    EMAIL_BALANCE_API_URL: 'http://192.168.1.3:8082',  // Aoksend余额查询服务地址
    
    // 请求超时时间(毫秒)
    API_TIMEOUT: 5000,
    
    // 默认数据量
    DEFAULT_DATA_COUNT: 20,
    
    // 默认数据模式
    // usage: 用量模式 (新total_reading - 旧total_reading)
    // cost: 用钱模式 (新remainingBalance - 旧remainingBalance)
    // total: 总量模式 (直接用读表数据)
    // balance: 余额模式 (直接显示remainingBalance)
    DEFAULT_MODE: 'balance',
    
    // 背景图片配置
    BACKGROUND_IMAGE_URL: 'https://s3.bmp.ovh/imgs/2025/06/24/a08d3969ca418f84.png',  // 背景图片URL，留空则不显示背景图片
    BACKGROUND_IMAGE_OPACITY: 0.4,  // 背景图片透明度，范围0-1，0为完全透明，1为完全不透明
    BACKGROUND_BLUR_RADIUS: 20,  // 背景图片模糊半径，单位px，0为不模糊
    
    // 容器透明度配置
    CONTAINER_OPACITY: 0.8,  // 容器透明度，范围0-1，0为完全不透明，1为完全透明
    
    // 网站favicon配置
    FAVICON_URL: 'https://littleskin.cn/avatar/112989?size=128'  // favicon URL，留空则使用默认favicon
};
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
- `chart.js` 用于Web界面数据图表展示（通过CDN引入）
- `concurrent.futures` 用于线程池处理
- `atexit` 用于程序退出时清理资源
- `queue` 用于连接池管理

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
16. **Web可视化界面**：提供图形化界面，支持数据可视化展示
17. **多模式数据展示**：支持用量、用钱、总量、余额等多种数据展示模式
18. **交互式查询**：支持设备搜索和自定义数据点数量
19. **数据图表展示**：通过图表直观展示数据变化趋势
20. **高性能API服务**：采用连接池和线程池技术，显著提升查询性能
21. **安全防护**：支持只读用户访问，输入参数验证，防止SQL注入
22. **可扩展性**：模块化设计便于功能扩展和维护
23. **反向代理支持**：支持通过X-Real-IP和X-Forwarded-For头部获取真实客户端IP
24. **动态配置加载**：Web前端支持动态加载配置文件，避免浏览器缓存问题
25. **响应式设计**：Web界面支持响应式布局，在不同设备上都能良好显示
26. **文本溢出处理**：优化了设备名称过长时的显示效果，使用省略号代替换行
27. **完整的邮件订阅系统**：支持用户订阅、验证、解绑的完整生命周期管理
28. **安全机制完善**：包含邮箱使用次数限制、验证码冷却期、解绑时间限制等多种安全措施
29. **用户友好的前端界面**：包含订阅/解绑按钮、验证码输入界面、成功/失败反馈等
30. **错误处理机制**：防止成功状态被后续错误覆盖的安全机制
31. **返回首页功能**：在搜索后提供一键返回首页的按钮，提升用户体验
32. **Aoksend余额查询服务**：提供独立的API余额查询服务
33. **邮件余额显示功能**：在Web界面页脚实时显示剩余邮件数量，提升用户体验

## 后续扩展建议

1. **Web界面**：开发Web界面，提供更友好的查询和展示方式
2. **定时任务**：使用cron等工具设置定时任务，实现自动化查询和预警
3. **多用户支持**：扩展系统以支持多个用户的水电费监控
4. **移动端应用**：开发移动端应用，方便用户随时查看水电费情况
5. **数据可视化**：添加数据图表功能，展示历史使用趋势
6. **多邮件服务支持**：扩展支持更多的邮件服务提供商
7. **数据备份**：实现数据库定期备份功能，确保数据安全
8. **性能优化**：优化数据库查询性能，支持更大规模的数据存储和查询
9. **用户认证系统**：为Web界面添加用户认证功能
10. **多语言支持**：为Web界面添加多语言支持
11. **响应式设计**：优化Web界面在不同设备上的显示效果
12. **数据导出功能**：添加数据导出为Excel或CSV格式的功能
13. **API安全增强**：实现API访问频率限制和认证机制
14. **实时数据推送**：使用WebSocket实现实时数据推送功能
15. **用户管理功能**：实现用户注册、登录、权限管理等机制
16. **通知中心**：集成多种通知方式（短信、微信、推送等）
17. **数据分析功能**：增加使用趋势分析、预测等功能
18. **API文档**：提供完整的API文档和SDK
19. **邮件余额显示功能**：在前端页面实时显示剩余邮件数量，提升用户体验

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

### Web界面开发
- **难点**：需要实现响应式设计和数据可视化展示
- **解决方案**：使用HTML、CSS和JavaScript开发前端界面，通过Chart.js实现数据图表展示

### API服务开发
- **难点**：需要实现高效的数据查询和处理
- **解决方案**：使用Python的HTTPServer模块开发RESTful API，通过MySQL数据库提供数据支持

### 性能优化与安全
- **难点**：API服务需要处理大量并发请求，同时确保安全性
- **解决方案**：
  - 实现数据库连接池减少连接开销
  - 使用线程池处理并发请求
  - 对所有输入参数进行验证和过滤
  - 支持只读用户访问以提高安全性
  - 使用参数化查询防止SQL注入
  - 限制单次查询返回的数据量

### 动态配置加载
- **难点**：浏览器缓存导致配置文件更新不及时
- **解决方案**：通过JavaScript动态加载配置文件，并在URL中添加时间戳避免缓存

### 文本溢出处理
- **难点**：设备名称过长导致界面显示问题
- **解决方案**：使用CSS的`white-space: nowrap`、`overflow: hidden`和`text-overflow: ellipsis`属性处理文本溢出

### 邮件订阅系统实现
- **难点**：需要实现完整的订阅、验证、解绑流程，包含多种安全机制
- **解决方案**：
  - 设计完整的email表结构，包含验证码、过期时间等字段
  - 实现验证码生成、邮件发送、状态验证等功能
  - 添加邮箱使用次数限制、验证码冷却期等安全机制
  - 前端实现用户友好的界面和交互流程
  - 防止成功状态被后续错误覆盖的安全机制

### 前端用户体验优化
- **难点**：用户在搜索后没有明确的路径返回首页
- **解决方案**：在前端添加返回首页按钮，点击后清空搜索框并重新加载首页数据
- **优化**：确保按钮在亮色和暗色模式下都与现有界面风格保持一致

### 邮件余额显示功能实现
- **难点**：需要实时获取Aoksend API账户余额并在前端显示
- **解决方案**：
  - 创建`getEmailBalance()`函数，用于从API获取邮件余额
  - 在Web界面页脚添加`<span id="email-balance">`元素用于显示余额
  - 添加CSS样式确保余额在亮色和暗色模式下都能清晰显示
  - 在页面初始化完成后自动调用API获取余额
  - 添加错误处理，当API请求失败时显示"获取失败"
  - 支持配置文件中的`EMAIL_BALANCE_API_URL`配置项
  - API返回格式为`{"message": "请求成功", "code": 200, "account": 24968}`