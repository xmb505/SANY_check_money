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
24. **邮件订阅庆祝功能**：新增在用户成功完成邮件订阅后发送庆祝邮件的功能
25. **前端验证按钮优化**：修复了验证按钮在前端界面中的对齐问题，确保按钮居中显示
26. **邮件订阅系统前端增强**：在订阅模态框中新增"直接输入订阅验证码"和"直接输入解绑验证码"按钮，方便用户在刷新页面后继续操作
27. **订阅提醒优化**：在订阅模态框中添加了红色显眼的提示信息，提醒用户检查垃圾邮件文件夹
28. **邮件检查服务**：新增`email_checker.py`服务，定期检查所有活跃订阅用户的设备余额，低于预警阈值时自动发送邮件
29. **高性能数据库连接**：为邮件检查服务添加了连接池和线程池优化，提高查询性能
30. **邮件发送频率限制**：在`email_api.py`中新增内存存储的邮件发送频率限制功能，防止邮件滥用，按日历日（过0点）计算发送次数

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
- **新增：订阅和解绑按钮增强**，在订阅按钮旁添加了"直接输入订阅验证码"和"直接输入解绑验证码"按钮
- **新增：订阅提醒优化**，在订阅模态框中添加了红色显眼的提示信息，提醒用户检查垃圾邮件文件夹
- **新增：验证按钮居中**，修复了验证按钮在前端界面中的对齐问题

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
    - **新增：验证码验证成功后发送庆祝邮件**
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
  - 防止成功状态被后续错误覆盖的机制
  - **新增：添加"直接输入订阅验证码"和"直接输入解绑验证码"按钮**

- **安全机制**：
  - 邮箱使用次数限制(默认25次)
  - 验证码冷却期检查(5分钟)
  - 解绑请求24小时限制
  - 设备类型匹配验证
  - 邮箱格式验证
  - **新增：邮件发送频率限制**，按日历日（过0点）计算，通过内存字典存储发送次数
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

### 16. 邮件订阅庆祝功能模块 (`server/email_api.py`)

- 在用户完成邮件订阅验证后发送庆祝邮件
- **实现方式**：
  - 从配置文件读取庆祝邮件模板ID和字段配置
  - 获取设备最新数据（余额、读数、状态等）
  - 构造庆祝邮件模板数据
  - 使用Aoksend API发送包含设备信息的庆祝邮件
- **配置项**：
  - `new_celebrate_template_id`：庆祝邮件模板ID
  - `new_celebrate_title`：标题字段名
  - `new_celebrate_device_name`：设备名称字段名
  - `new_celebrate_device_balance`：余额字段名
  - `new_celebrate_device_check_time`：查询时间字段名
  - `new_celebrate_device_statu`：设备状态字段名
  - `new_celebrate_device_latest_read`：最后读数字段名

### 17. 邮件检查服务模块 (`server/email_checker.py`)

- **功能**：定期检查所有活跃订阅用户的设备余额，低于预警阈值时自动发送邮件
- **实现方式**：
  - 从email表中获取所有活跃的订阅
  - 查询每个订阅设备的最新数据
  - 比较余额与用户设置的预警阈值
  - 当余额低于阈值时，通过Aoksend API发送预警邮件
- **性能优化**：
  - 实现了数据库连接池机制
  - 使用线程池并发处理多个用户
  - 支持批量处理，提高处理效率
- **配置文件**：`server/email_checker.ini`
- **命令行启动**：`./server/email_checker.py`

### 18. 邮件发送频率限制功能 (`server/email_api.py`)

- **功能**：防止邮件滥用，在内存中跟踪每个邮箱的每日发送次数
- **实现方式**：
  - 使用内存字典`daily_email_counts`格式为 `{email: {date: count}}` 存储发送次数
  - 通过`count_emails_sent_today()`函数统计用户当天发送的邮件数量
  - 通过`record_email_sent()`函数记录邮件发送
  - 通过`cleanup_old_dates()`函数定期清理超过3天的旧数据
  - 邮件发送前检查当日发送次数是否超过配置限制
- **配置项**：
  - `email_daily_limit`：每个邮箱每天最多发送邮件数量，超过此值拒绝发送邮件
- **时间计算**：按日历日计算（过0点），使用系统时间的日期部分

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
- `server/email_checker.ini`：邮件检查服务配置
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

#### 内存邮件频率限制机制
- 使用内存字典存储每日邮件发送次数
- 格式为 `{email: {date: count}}`
- 每日发送次数按日历日（过0点）计算
- 定期清理超过3天的旧数据以防止内存泄漏

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
- `server/email_api.py`：邮件订阅系统后端API（支持订阅、验证、解绑功能，新增邮件发送频率限制）
- `server/email_api.ini`：邮件API服务配置文件
- `server/aokbalance_get.py`：Aoksend余额查询服务
- `server/aokbalance_get.ini`：Aoksend余额查询服务配置文件
- `server/email_checker.py`：邮件检查服务（定期检查设备余额并发送预警邮件）
- `server/email_checker.ini`：邮件检查服务配置文件
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

### 邮件检查服务
```bash
./server/email_checker.py
```

该命令会启动邮件检查服务，按照 `server/email_checker.ini` 中配置的检查周期持续监控所有活跃订阅用户的设备余额，
当余额低于用户设定的阈值时自动通过Aoksend API发送预警邮件。

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
- 邮件每日发送限制
- 数据库连接信息
- Aoksend邮件服务配置
- **新增：注册庆祝邮件配置**

示例配置：
```ini
[server]
port = 8081

[email]
# 表记录中同一个邮件最多出现次数，超过此值拒绝服务
email_limit = 25
# 每个邮箱每天最多发送邮件数量，超过此值拒绝发送邮件
email_daily_limit = 100

[mysql]
mysql_server = your_mysql_host
mysql_port = 3306
login_user = your_username
login_passwd = your_password
db_schema = your_database_name

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
# 解绑模板ID
change_template_id = YOUR_CHANGE_TEMPLATE_ID_HERE
# 新注册庆祝模板ID，制定了发件用的模板
new_celebrate_template_id = YOUR_CHANGE_TEMPLATE_ID_HERE
# 新注册庆祝模板标题字段名，也就是邮件里面的大标题的变量，程序里面会写死："恭喜注册成功，现在是你邮箱绑定的设备情况"
new_celebrate_title = title
# 新注册庆祝模板设备字段名 直接拿着device_id去device表的id字段查，然后拿到equipmentName，发送邮件API的时候就是acctName:equipmentName
new_celebrate_device_name = acctName
# 新注册庆祝模板余额字段名，拿着device_id去data表的device_id字段查这个设备下read_time最新的设备的remainingBalance
new_celebrate_device_balance = remainingBalance
# 新注册庆祝模板上次查询时间字段名，拿着device_id去data表的device_id字段查这个设备下read_time最新的设备的read_time
new_celebrate_device_check_time = currentDealDate
# 新注册庆祝模板设备状态字段名，拿着device_id去data表的device_id字段查这个设备下read_time最新的设备的equipmentStatus
new_celebrate_device_statu = equipmentStatus
# 新注册庆祝模板最后读表示数字段名，拿着device_id去data表的device_id字段查这个设备下read_time最新的设备的total_reading
new_celebrate_device_latest_read = equipmentLatestLarge
```

### server/email_checker.ini
邮件检查服务配置文件，包含：
- 检查周期设置
- 数据库连接信息
- Aoksend邮件服务配置

示例配置：
```ini
[service]
# 重新查询时间，单位为秒
round_time = 3600

[mysql]
mysql_server = your_mysql_host
mysql_port = 3306
login_user = your_username
login_passwd = your_password
db_schema = sany_check

[aoksender]
# API地址(选填)
server = https://www.aoksend.com/index/api/send_email
# API密钥
app_key = YOUR_API_KEY_HERE
# 默认回复地址
reply_to = 
# 发件人名称
alias = 新毛云
# 邮件附件, 仅专业版可用；发送附件时, 必须使用 multipart/form-data 进行 post 提交 (表单提交)
attachment =

[email]
# 查询模板ID
checker_template_id = YOUR_TEMPLATE_ID_HERE
# 查询模板标题字段名
checker_title = title
# 查询模板设备字段名
checker_device_name = acctName
# 查询模板余额字段名
checker_device_balance = remainingBalance
# 查询模板上次查询时间字段名
checker_device_check_time = currentDealDate
# 查询模板设备状态字段名
checker_device_statu = equipmentStatus
# 查询模板最后读表示数字段名
checker_device_latest_read = equipmentLatestLarge
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
34. **邮件订阅庆祝功能**：在用户完成验证后发送庆祝邮件，提升用户体验
35. **邮件检查服务**：独立运行的服务，检查所有活跃用户的设备余额并发送预警邮件
36. **高性能处理**：为邮件检查服务添加连接池和线程池优化，提高批量处理效率
37. **前端功能增强**：增加直接输入验证码按钮，优化订阅提醒信息，改进按钮对齐
38. **邮件发送频率限制**：通过内存存储机制实现邮件发送频率限制，防止滥用，按日历日（过0点）计算发送次数
39. **可配置连接池**：支持通过配置文件调整数据库连接池大小，优化性能

## server.py RESTful API 接口文档

### API 概述

`server.py` 提供高性能的 RESTful API 服务，为 Web 前端提供设备数据查询功能。采用 HTTP 协议，返回 JSON 格式数据，支持跨域访问。

**服务器地址**：`http://localhost:8080`（可在配置文件中修改）

**请求方式**：GET

**响应格式**：JSON

**跨域支持**：支持 CORS，允许所有来源访问

### 接口列表

#### 1. 首屏数据接口

**接口路径**：`/`

**请求参数**：
- `mode=first_screen`：固定值，表示获取首屏数据

**请求示例**：
```
http://localhost:8080/?mode=first_screen
```

**功能说明**：
获取首页展示的随机设备列表，用于 Web 界面首次加载时展示。从数据库中随机选取配置数量的设备 ID。

**响应参数**：
- `code`：响应状态码（"200" 表示成功）
- `total_num`：返回的设备数量
- `device_ids`：设备 ID 列表（字符串数组）

**成功响应示例**：
```json
{
  "code": "200",
  "total_num": 6,
  "device_ids": [
    "24831",
    "24901",
    "25012",
    "25123",
    "25234",
    "25345"
  ]
}
```

**配置项**：
- 返回数量由配置文件中的 `first_screen_count` 参数控制（默认：6）
- 最大限制为 100 个设备

---

#### 2. 设备数据查询接口

**接口路径**：`/`

**请求参数**：
- `mode=check`：固定值，表示查询设备数据
- `device_id`：设备 ID（必需，字符串）
- `data_num`：返回的数据条数（可选，整数，默认：5，范围：1-1000）

**请求示例**：
```
http://localhost:8080/?mode=check&device_id=24831&data_num=10
```

**功能说明**：
查询指定设备的详细信息和历史数据记录。返回设备基本信息和最近的数据读数。

**响应参数**：
- `code`：响应状态码（200 表示成功，404 表示设备未找到）
- `equipmentName`：设备名称
- `device_id`：设备 ID
- `installationSite`：安装位置
- `equipmentType`：设备类型（0=电表，1=水表）
- `ratio`：互感器倍率
- `rate`：单价
- `acctId`：财务账户号
- `status`：设备状态（0=停用，1=启用）
- `updated_at`：档案更新时间
- `total`：返回的数据记录数
- `rows`：数据记录列表
  - `device_id`：设备 ID
  - `read_time`：读数时间
  - `total_reading`：累积读数
  - `remainingBalance`：剩余余额

**成功响应示例**：
```json
{
  "equipmentName": "7栋6楼楼道中间大厅饮水机",
  "device_id": "24831",
  "installationSite": "7栋6楼楼道中间大厅",
  "equipmentType": 0,
  "ratio": "40",
  "rate": "0.6190",
  "acctId": "20220805000452",
  "status": "0",
  "updated_at": "2025-11-12 10:05:46",
  "total": 10,
  "rows": [
    {
      "device_id": "24831",
      "read_time": "2025-11-12 10:05:46",
      "total_reading": "684.92",
      "remainingBalance": "-2619.789200"
    },
    {
      "device_id": "24831",
      "read_time": "2025-11-11 10:05:46",
      "total_reading": "684.12",
      "remainingBalance": "-2618.989200"
    }
  ],
  "code": 200
}
```

**错误响应示例**：
```json
{
  "code": "404",
  "error": "设备未找到"
}
```

**参数验证**：
- `device_id`：只允许字母、数字和下划线，长度不超过 50
- `data_num`：必须是 1-1000 之间的整数

---

#### 3. 设备搜索接口

**接口路径**：`/`

**请求参数**：
- `mode=search`：固定值，表示搜索设备
- `key_word`：搜索关键词（必需，字符串，最少 2 个字符）

**请求示例**：
```
http://localhost:8080/?mode=search&key_word=饮水机
```

**功能说明**：
根据关键词搜索设备，支持模糊匹配。在设备名称（equipmentName）和安装位置（installationSite）字段中进行搜索。

**响应参数**：
- `code`：响应状态码（200 表示成功，418 表示关键词长度不足）
- `search_status`：搜索状态（0=成功，1=关键词长度不足）
- `error_talk`：错误提示信息（仅在 search_status=1 时返回）
- `total`：匹配的设备数量
- `rows`：设备列表
  - `equipmentName`：设备名称
  - `installationSite`：安装位置
  - `device_id`：设备 ID
  - `equipmentType`：设备类型
  - `status`：设备状态

**成功响应示例**：
```json
{
  "search_status": 0,
  "total": 3,
  "rows": [
    {
      "equipmentName": "7栋6楼楼道中间大厅饮水机",
      "installationSite": "7栋6楼楼道中间大厅",
      "device_id": "24831",
      "equipmentType": "0",
      "status": "0"
    },
    {
      "equipmentName": "7栋5楼楼道饮水机",
      "installationSite": "7栋5楼楼道",
      "device_id": "24832",
      "equipmentType": "0",
      "status": "0"
    }
  ],
  "code": 200
}
```

**关键词长度不足响应示例**：
```json
{
  "search_status": 1,
  "error_talk": "请输入两个以上的字符。",
  "code": 418
}
```

**参数验证**：
- `key_word`：最少 2 个字符，最多 50 个字符
- 只允许字母、数字、中文和空格

---

### 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 参数错误（缺少必需参数或参数格式不正确） |
| 404 | 设备未找到 |
| 418 | 业务逻辑错误（如关键词长度不足） |
| 500 | 服务器内部错误（数据库查询错误等） |

### 性能优化特性

1. **连接池机制**：使用数据库连接池，减少连接建立开销
   - 连接池大小可配置（默认：30）
   - 连接健康检查和自动恢复

2. **线程池处理**：使用线程池并行处理多个请求
   - 线程池大小：10
   - 提高并发处理能力

3. **输入验证**：对所有输入参数进行验证
   - 防止 SQL 注入攻击
   - 参数格式和范围检查

4. **查询优化**：
   - 限制最大返回数据量（1000 条）
   - 合理使用数据库索引

### 配置参数

**server.ini 配置示例**：
```ini
[mysql]
mysql_server = your_mysql_host
mysql_port = 3306
login_user = your_username
login_passwd = your_password
db_schema = your_database_name
# 数据库连接池大小，建议设置为线程池的3倍
connection_pool_size = 30

[server]
port = 8080

[config]
first_screen_count = 6
```

**配置说明**：
- `connection_pool_size`：数据库连接池大小（默认：30）
- `first_screen_count`：首屏显示设备数量（默认：6）
- `port`：服务器监听端口（默认：8080）

### 使用示例

#### Python 调用示例
```python
import requests

# 获取首屏数据
response = requests.get('http://localhost:8080/?mode=first_screen')
data = response.json()
print(f"获取到 {data['total_num']} 个设备")

# 查询设备数据
response = requests.get('http://localhost:8080/?mode=check&device_id=24831&data_num=10')
device_data = response.json()
print(f"设备名称：{device_data['equipmentName']}")
print(f"余额：{device_data['rows'][0]['remainingBalance']}")

# 搜索设备
response = requests.get('http://localhost:8080/?mode=search&key_word=饮水机')
search_results = response.json()
print(f"找到 {search_results['total']} 个设备")
```

#### JavaScript 调用示例
```javascript
// 获取首屏数据
fetch('http://localhost:8080/?mode=first_screen')
  .then(response => response.json())
  .then(data => {
    console.log(`获取到 ${data.total_num} 个设备`);
    console.log('设备ID列表：', data.device_ids);
  });

// 查询设备数据
fetch('http://localhost:8080/?mode=check&device_id=24831&data_num=10')
  .then(response => response.json())
  .then(deviceData => {
    console.log('设备名称：', deviceData.equipmentName);
    console.log('最新余额：', deviceData.rows[0].remainingBalance);
  });

// 搜索设备
fetch('http://localhost:8080/?mode=search&key_word=饮水机')
  .then(response => response.json())
  .then(searchResults => {
    console.log(`找到 ${searchResults.total} 个设备`);
    searchResults.rows.forEach(device => {
      console.log(`${device.equipmentName} - ${device.installationSite}`);
    });
  });
```

### 日志输出

server.py 会输出详细的运行日志，包括：
- 请求来源 IP（支持反向代理）
- 请求路径和参数
- SQL 查询语句
- 响应状态码和数据长度
- 数据库连接池使用情况
- 错误信息和堆栈跟踪

**日志示例**：
```
[INFO] 收到GET请求 from 127.0.0.1: /?mode=check&device_id=24831&data_num=10
[INFO] 解析参数完成: {'mode': ['check'], 'device_id': ['24831'], 'data_num': ['10']}
[INFO] 请求模式: check
[INFO] 处理设备检查请求，设备ID: 24831, 数据量: 10
[INFO] 从连接池获取数据库连接
[INFO] 数据库连接建立成功
[INFO] 查询设备信息，SQL: SELECT equipmentName, installationSite, equipmentType, ratio, rate, acctId, status, updated_at, id FROM device WHERE id = %s, 参数: 24831
[INFO] 设备信息查询完成
[INFO] 查询设备读数数据，SQL: SELECT device_id, read_time, total_reading, remainingBalance FROM data WHERE device_id = %s ORDER BY read_time DESC LIMIT %s, 参数: (24831, 10)
[INFO] 读数数据查询完成，获取到 10 条记录
[INFO] 设备数据响应构建完成
[INFO] 请求处理完成，响应数据: 200
[INFO] 发送响应，响应长度: 1250
[INFO] 响应发送完成
[INFO] 数据库连接已返回连接池
```

### 安全特性

1. **SQL 注入防护**：
   - 所有数据库查询使用参数化查询
   - 输入参数严格验证格式和长度

2. **请求频率限制**：
   - 通过 Web 服务器或反向代理实现
   - 建议在生产环境部署 Nginx 等反向代理

3. **连接安全**：
   - 数据库连接使用超时设置
   - 连接池自动清理无效连接

4. **数据访问控制**：
   - 建议创建只读数据库用户
   - 限制单个请求的数据量（最大 1000 条）

### 部署建议

1. **生产环境配置**：
   - 使用 Nginx/Apache 作为反向代理
   - 配置 HTTPS 加密传输
   - 设置请求频率限制
   - 使用 systemd 管理服务

2. **性能调优**：
   - 根据服务器配置调整 `connection_pool_size`
   - 监控数据库连接使用情况
   - 定期清理日志文件

3. **监控告警**：
   - 监控服务器端口存活状态
   - 监控错误日志
   - 设置异常告警

### 常见问题

**Q: 为什么请求会超时？**
A: 可能原因：
- 数据库连接池耗尽，检查连接池配置
- 查询数据量过大，减少 `data_num` 参数
- 数据库性能问题，优化数据库索引

**Q: 如何调整连接池大小？**
A: 修改 `server.ini` 配置文件中的 `connection_pool_size` 参数，建议设置为线程池的 3 倍。

**Q: 支持 HTTPS 吗？**
A: server.py 本身只支持 HTTP，建议在生产环境使用 Nginx 等反向代理实现 HTTPS。

**Q: 如何查看详细日志？**
A: 直接查看终端输出，或重定向日志到文件：
```bash
python3 server.py > server.log 2>&1
```

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
20. **邮件检查服务优化**：进一步优化邮件检查服务的性能和稳定性
21. **邮件频率限制优化**：考虑使用更先进的滑动窗口算法或其他时间窗口策略

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

### 邮件订阅庆祝功能实现
- **难点**：需要在用户完成验证后发送包含设备信息的庆祝邮件
- **解决方案**：
  - 从配置文件读取庆祝邮件模板配置
  - 获取设备最新数据（余额、读数、状态等）
  - 使用Aoksend API发送个性化庆祝邮件
  - 处理Decimal类型数据的JSON序列化问题
  - 确保庆祝邮件在正确时机发送（注册验证成功后）

### 邮件检查服务实现
- **难点**：需要定期检查所有活跃用户的设备余额并发送预警邮件
- **解决方案**：
  - 实现数据库连接池和线程池优化性能
  - 并发处理多个用户的预警检查
  - 添加错误处理和资源管理机制
  - 优化SQL查询性能，使用适当的索引

### 邮件发送频率限制实现
- **难点**：需要防止邮件滥用，同时避免数据库操作的性能开销
- **解决方案**：
  - 使用内存字典存储每日邮件发送次数，格式为`{email: {date: count}}`
  - 实现`count_emails_sent_today()`和`record_email_sent()`函数
  - 添加`cleanup_old_dates()`函数定期清理过期数据（保留最近3天）
  - 按日历日（过0点）计算发送次数，而非24小时滚动窗口
  - 在配置文件中添加`email_daily_limit`配置项控制每日发送上限