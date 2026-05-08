# SANY_check_money 后端 API 接口文档

本文档描述系统中三个后端 HTTP 服务的所有 API 接口。

---

## 服务概览

| 服务 | 文件 | 默认端口 | 协议 | 说明 |
|------|------|---------|------|------|
| 数据查询服务 | `server/server.py` | 8080 | HTTP GET | 设备数据查询、搜索 |
| 邮件订阅服务 | `server/email_api.py` | 8081 | HTTP POST | 邮件订阅、验证、解绑 |
| 邮件余额查询服务 | `server/aokbalance_get.py` | 8082 | HTTP GET | Aoksend 邮件余额查询 |

**通用说明:**
- 所有接口返回 `Content-Type: application/json`
- 所有接口支持 CORS（`Access-Control-Allow-Origin: *`）
- HTTP 状态码统一返回 `200`，业务状态通过响应体中的 `code` 字段区分

---

## 一、数据查询服务 (server.py - 端口 8080)

所有请求均为 **GET** 方法，通过 `mode` 查询参数区分接口。

### 1.1 获取首屏数据

随机返回一批设备 ID，用于首页展示。

**请求:**

```
GET /?mode=first_screen
```

**参数:** 无

**成功响应:**

```json
{
    "code": "200",
    "total_num": 6,
    "device_ids": ["device_001", "device_002", "device_003", "device_004", "device_005", "device_006"]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 状态码，`"200"` 表示成功 |
| `total_num` | int | 返回的设备数量 |
| `device_ids` | string[] | 设备 ID 列表 |

**错误响应:**

```json
{
    "code": "500",
    "error": "数据库查询错误: ..."
}
```

**备注:** 返回数量由 `server.ini` 中 `[config].first_screen_count` 配置，最大限制 100。

---

### 1.2 查询设备数据（数据点模式）

根据设备 ID 查询设备信息及最近 N 条读数记录。

**请求:**

```
GET /?mode=check&device_id={device_id}&data_num={data_num}
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `device_id` | string | 是 | 设备 ID，仅允许字母、数字、下划线，最长 50 字符 |
| `data_num` | int | 是 | 请求数据条数，范围 1-1000 |

**成功响应:**

```json
{
    "code": 200,
    "equipmentName": "A栋-101电表",
    "device_id": "device_001",
    "installationSite": "A栋101室",
    "equipmentType": "0",
    "ratio": "1.00",
    "rate": "0.5500",
    "acctId": "ACC001",
    "status": "1",
    "updated_at": "2025-06-20 12:00:00",
    "total": 5,
    "rows": [
        {
            "device_id": "device_001",
            "read_time": "2025-06-20 12:00:00",
            "total_reading": "1234.56",
            "remainingBalance": "88.123456"
        }
    ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 状态码，`200` 表示成功 |
| `equipmentName` | string | 设备名称 |
| `device_id` | string | 设备 ID |
| `installationSite` | string | 安装位置 |
| `equipmentType` | string | 设备类型：`"0"` = 电表，`"1"` = 水表 |
| `ratio` | string | 倍率 |
| `rate` | string | 单价 |
| `acctId` | string | 财务账户号 |
| `status` | string | 设备状态：`"1"` = 启用，`"0"` = 停用 |
| `updated_at` | string | 最后更新时间 |
| `total` | int | 返回的数据条数 |
| `rows` | object[] | 读数数据列表（按 `read_time` 降序排列） |
| `rows[].device_id` | string | 设备 ID |
| `rows[].read_time` | string | 读数时间 |
| `rows[].total_reading` | string | 总读数 |
| `rows[].remainingBalance` | string | 剩余余额 |

**错误响应:**

| code | 说明 |
|------|------|
| `"404"` | 设备未找到 |
| `"400"` | 参数缺失或格式无效 |
| `"500"` | 数据库查询错误 |

---

### 1.3 查询设备每日数据（日期模式）

根据日期范围查询设备每天最后一条读数记录。

**请求:**

```
GET /?mode=check_daily_range&device_id={device_id}&start_day={start_day}&end_day={end_day}
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `device_id` | string | 是 | 设备 ID，仅允许字母、数字、下划线，最长 50 字符 |
| `start_day` | string | 是 | 开始日期，格式 `YYYY-MM-DD` |
| `end_day` | string | 是 | 结束日期，格式 `YYYY-MM-DD`，不得早于 `start_day` |

**成功响应:**

响应结构与 **1.2 查询设备数据** 完全一致。

`rows` 中的每条记录代表该日最后一次读数数据，按日期降序排列。

**错误响应:**

| code | 说明 |
|------|------|
| `"404"` | 设备未找到 |
| `"400"` | 参数缺失、日期格式不正确、开始日期晚于结束日期 |
| `"500"` | 数据库查询错误 |

---

### 1.4 搜索设备

根据关键词搜索设备（匹配设备名称或安装位置）。

**请求:**

```
GET /?mode=search&key_word={keyword}
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `key_word` | string | 是 | 搜索关键词，仅允许字母、数字、中文和空格，最长 50 字符，至少 2 个字符 |

**成功响应:**

```json
{
    "code": 200,
    "search_status": 0,
    "total": 3,
    "rows": [
        {
            "equipmentName": "A栋-101电表",
            "installationSite": "A栋101室",
            "device_id": "device_001",
            "equipmentType": "0",
            "status": "1"
        }
    ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 状态码，`200` 表示成功 |
| `search_status` | int | 搜索状态：`0` = 成功，`1` = 失败 |
| `total` | int | 搜索结果总数 |
| `rows` | object[] | 搜索结果列表 |
| `rows[].equipmentName` | string | 设备名称 |
| `rows[].installationSite` | string | 安装位置 |
| `rows[].device_id` | string | 设备 ID |
| `rows[].equipmentType` | string | 设备类型：`"0"` = 电表，`"1"` = 水表 |
| `rows[].status` | string | 设备状态 |

**关键词过短响应 (< 2 字符):**

```json
{
    "code": 418,
    "search_status": 1,
    "error_talk": "请输入两个以上的字符。"
}
```

**错误响应:**

| code | 说明 |
|------|------|
| `"400"` | 关键词缺失或包含非法字符 |
| `"500"` | 数据库查询错误 |

---

## 二、邮件订阅服务 (email_api.py - 端口 8081)

所有请求均为 **POST** 方法，请求体为 JSON 格式，通过 `mode` 字段区分接口。

### 2.1 订阅注册

为指定邮箱绑定设备预警通知。成功后发送验证码邮件，需用户输入验证码完成验证。

**请求:**

```
POST /
Content-Type: application/json
```

```json
{
    "mode": "reg",
    "email": "user@example.com",
    "equipment_type": 0,
    "device_id": "device_001",
    "alarm_num": 10
}
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | string | 是 | 固定值 `"reg"` |
| `email` | string | 是 | 邮箱地址 |
| `equipment_type` | int | 是 | 设备类型：`0` = 电表，`1` = 水表 |
| `device_id` | string | 是 | 设备 ID |
| `alarm_num` | int | 否 | 预警阈值（元），默认 `20`，须 > 0 |

**成功响应（等待验证码）:**

```json
{
    "code": 200,
    "set_client_mode": "wait_user_verifi"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 状态码 |
| `set_client_mode` | string | 客户端下一步操作：`"wait_user_verifi"` = 等待用户输入验证码 |

**错误响应:**

| code | error_text | 说明 |
|------|-----------|------|
| `400` | 邮箱格式不正确 | 邮箱校验失败 |
| `400` | 设备类型不正确 | `equipment_type` 不是 0 或 1 |
| `400` | 预警值必须大于0 | `alarm_num` <= 0 |
| `403` | 设备不存在 | `device_id` 在数据库中不存在 |
| `403` | 绑定的设备和类型不一致 | 设备实际类型与传入的 `equipment_type` 不匹配 |
| `418` | 该账号使用次数超过限制，不予注册 | 邮箱记录数达到上限（默认 25） |
| `418` | 请等待验证码冷却期过期 | 验证码尚未过期（5 分钟内），请等待 |
| `418` | 请解绑当前设备 | 该邮箱+设备类型已有活跃订阅 |
| `500` | 服务器内部错误 / 插入记录失败 | 服务端异常 |

---

### 2.2 提交验证码

用户收到邮件后，输入验证码完成订阅验证。验证成功后自动发送庆祝邮件。

**请求:**

```
POST /
Content-Type: application/json
```

```json
{
    "mode": "enter_code",
    "email": "user@example.com",
    "code": "123456"
}
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | string | 是 | 固定值 `"enter_code"` |
| `email` | string | 是 | 邮箱地址 |
| `code` | string | 是 | 6 位验证码 |

**成功响应:**

```json
{
    "code": 200,
    "verifi_statu": 1
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 状态码 |
| `verifi_statu` | int | 验证状态：`1` = 验证成功 |

**错误响应:**

| code | error_text | 说明 |
|------|-----------|------|
| `400` | 缺少必需参数 | `email` 或 `code` 为空 |
| `400` | 邮箱格式不正确 | 邮箱校验失败 |
| `418` | 验证码过期，请重新生成 | 验证码已超过 5 分钟有效期 |
| `418` | 验证码错误，请重新输入 | 验证码不匹配 |
| `500` | 服务器内部错误 | 服务端异常 |

---

### 2.3 请求解绑

请求解除邮箱与设备的绑定关系。成功后发送解绑验证码邮件。

**请求:**

```
POST /
Content-Type: application/json
```

```json
{
    "mode": "change_code",
    "email": "user@example.com",
    "equipment_type": 0,
    "device_id": "device_001"
}
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | string | 是 | 固定值 `"change_code"` |
| `email` | string | 是 | 邮箱地址 |
| `equipment_type` | int | 是 | 设备类型：`0` = 电表，`1` = 水表 |
| `device_id` | string | 是 | 设备 ID |

**成功响应（等待解绑验证码）:**

```json
{
    "code": 200,
    "set_client_mode": "wait_user_change"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 状态码 |
| `set_client_mode` | string | 客户端下一步操作：`"wait_user_change"` = 等待用户输入解绑验证码 |

**错误响应:**

| code | error_text | 说明 |
|------|-----------|------|
| `400` | 缺少必需参数 | 必填参数为空或 `equipment_type` 不是 0/1 |
| `400` | 邮箱格式不正确 | 邮箱校验失败 |
| `418` | 未查询到正在订阅预警服务的邮箱账号或设备 | 没有匹配的活跃订阅 |
| `418` | 24小时内已请求过解绑或者刚绑定不到24小时，明天再试吧！ | 解绑冷却期未到 |

---

### 2.4 提交解绑验证码

用户收到解绑邮件后，输入验证码完成解绑。

**请求:**

```
POST /
Content-Type: application/json
```

```json
{
    "mode": "enter_change",
    "email": "user@example.com",
    "equipment_type": 0,
    "device_id": "device_001",
    "change_code": "654321"
}
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | string | 是 | 固定值 `"enter_change"` |
| `email` | string | 是 | 邮箱地址 |
| `equipment_type` | int | 是 | 设备类型：`0` = 电表，`1` = 水表 |
| `device_id` | string | 是 | 设备 ID |
| `change_code` | string | 是 | 6 位解绑验证码 |

**成功响应:**

```json
{
    "code": 200,
    "change_device_statu": 1
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 状态码 |
| `change_device_statu` | int | 解绑状态：`1` = 解绑成功 |

**错误响应:**

| code | error_text | 说明 |
|------|-----------|------|
| `400` | 缺少必需参数 | 必填参数为空 |
| `400` | 邮箱格式不正确 | 邮箱校验失败 |
| `418` | 未找到有效的订阅记录 | 没有匹配的可解绑记录 |
| `418` | 解绑验证码错误 | 验证码不匹配 |
| `500` | 服务器内部错误 | 服务端异常 |

---

## 三、邮件余额查询服务 (aokbalance_get.py - 端口 8082)

### 3.1 查询 Aoksend 邮件余额

查询 Aoksend 邮件发送服务的剩余额度。

**请求:**

```
GET /
```

**参数:** 无

**成功响应:**

```json
{
    "code": 200,
    "account": 9500
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 状态码，`200` 表示成功 |
| `account` | int | 剩余可发送邮件数量 |

**错误响应:**

```json
{
    "code": 500,
    "error_text": "获取余额时出错: ..."
}
```

**备注:** 此接口实际调用 Aoksend 第三方 API，响应字段取决于 Aoksend 返回结果，上述为典型结构。

---

## 四、数据库表结构参考

### device 表（设备表）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | varchar(32) | 设备 ID（主键） |
| `addr` | varchar(20) | 设备地址 |
| `equipmentName` | varchar(100) | 设备名称 |
| `installationSite` | varchar(100) | 安装位置 |
| `equipmentType` | tinyint(1) | 设备类型：`0` = 电表，`1` = 水表 |
| `ratio` | decimal(10,2) | 倍率 |
| `rate` | decimal(10,4) | 单价 |
| `acctId` | varchar(20) | 财务账户号 |
| `status` | tinyint(1) | 状态：`1` = 启用，`0` = 停用 |
| `properties` | longtext(json) | 扩展属性（JSON） |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间（自动更新） |

### data 表（读数表）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | bigint(20) | 自增主键 |
| `device_id` | varchar(32) | 设备 ID（外键 -> device.id） |
| `read_time` | datetime | 读数时间 |
| `total_reading` | decimal(15,2) | 总读数 |
| `diff_reading` | decimal(15,2) | 差值读数 |
| `remainingBalance` | decimal(15,6) | 剩余余额 |
| `equipmentStatus` | tinyint(1) | 设备状态 |
| `created_at` | datetime | 记录创建时间 |
| `remark` | varchar(255) | 备注 |
| `unStandard` | tinyint(1) | 是否异常数据：`0` = 正常，`1` = 异常 |

### email 表（邮箱订阅表）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | bigint(20) | 自增主键 |
| `email` | varchar(255) | 邮箱地址 |
| `uuid` | varchar(36) | UUID 标识 |
| `device_id` | varchar(32) | 绑定设备 ID |
| `verifi_code` | varchar(10) | 注册验证码 |
| `created_time` | datetime | 创建时间 |
| `verifi_end_time` | datetime | 验证码过期时间（创建后 5 分钟） |
| `verifi_statu` | tinyint(1) | 验证状态：`0` = 未验证，`1` = 已验证 |
| `life_end_time` | datetime | 订阅过期时间（创建后 1 年） |
| `change_device_statu` | tinyint(1) | 解绑状态：`0` = 正常，`1` = 已解绑 |
| `updated_time` | datetime | 更新时间（自动更新） |
| `ip_address` | varchar(45) | 客户端 IP |
| `alarm_num` | int(11) | 预警阈值（元） |
| `equipment_type` | tinyint(1) | 设备类型：`0` = 电表，`1` = 水表 |
| `change_code` | varchar(10) | 解绑验证码 |

**唯一约束:** `(email, device_id, equipment_type)` 联合唯一

---

## 五、前端调用流程参考

### 首页加载流程

```
1. GET /?mode=first_screen          → 获取设备 ID 列表
2. 对每个 device_id:
   - 数据点模式: GET /?mode=check&device_id=xxx&data_num=20
   - 日期模式:   GET /?mode=check_daily_range&device_id=xxx&start_day=2025-06-01&end_day=2025-06-20
3. GET /  (端口8082)                 → 获取邮件余额显示在页脚
```

### 搜索流程

```
1. GET /?mode=search&key_word=A栋    → 获取匹配的设备列表
2. 对每个搜索结果的 device_id，按首页加载流程的步骤 2 获取详细数据
```

### 邮件订阅流程

```
1. POST {mode:"reg", email, equipment_type, device_id, alarm_num}
   → 返回 set_client_mode: "wait_user_verifi"
2. 用户收到验证码邮件
3. POST {mode:"enter_code", email, code}
   → 返回 verifi_statu: 1 表示成功
```

### 邮件解绑流程

```
1. POST {mode:"change_code", email, equipment_type, device_id}
   → 返回 set_client_mode: "wait_user_change"
2. 用户收到解绑验证码邮件
3. POST {mode:"enter_change", email, equipment_type, device_id, change_code}
   → 返回 change_device_statu: 1 表示成功
```
