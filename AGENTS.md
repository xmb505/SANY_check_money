# AGENTS.md

This file provides guidance to Qoder (qoder.com) when working with code in this repository.

## Project Overview

三一工学院宿舍水电费自动查询监控系统。采集学校网站水电数据存入 MySQL，提供 Web 可视化、邮件预警、宿管模式等功能的单体 Python 项目。

## Running & Development

### Dependencies

```bash
pip install requests pymysql
```

No build system, no package manager, no virtual environment setup required.

### Start Services

Each service is an independent `http.server` process, started directly:

```bash
python3 server/server.py           # Data query API, port 8080
python3 server/email_api.py        # Email subscription API, port 8081
python3 server/aokbalance_get.py   # Aoksend balance checker, port 8082
```

Frontend is static files in `web/`, served by `server.py` or any static file server. Access at `http://localhost:8080`.

### Verification

No test framework. Verify Python syntax with:

```bash
python3 -m py_compile <file.py>
node --check <file.js>
```

There is no linter or type checker configured.

## Architecture

### Backend: Mode-Routed HTTP Services

All three services use `http.server.BaseHTTPRequestHandler` with a `mode` query parameter for routing (not a web framework). Example route dispatch pattern in `server.py`:

```python
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        mode = params.get('mode', [None])[0]
        if mode == 'first_screen': ...
        elif mode == 'check': ...
```

- `server.py` uses **GET** with `mode` param
- `email_api.py` uses **POST** with `action` param in JSON body
- `aokbalance_get.py` uses **GET** with `action` param

All services return `Content-Type: application/json`, HTTP 200 with business status in `code` field.

### Database Layer

MySQL via `pymysql`. Connection pooling implemented with `queue.Queue` in `DatabaseManager`:

- `DatabaseManager.initialize_connection_pool()` — pre-creates connections
- `DatabaseManager.get_connection()` — context manager yielding from pool
- Pool size = 3× thread pool size (default 30 connections for 10 threads)

Three tables: `device` (meters), `data` (readings with `total_reading`, `remainingBalance`, `equipmentStatus`), `email` (subscriptions). SQL schema in `doc/sql/`.

### Data Cleaning Pipeline (`data_cleaner/hourly_report.py`)

This is the core algorithm module, imported by `server.py` via `sys.path.insert`:

```
raw readings → build_slot_max() → fill_missing_slots() → compute_usage_series() → smooth_zero_usage()
```

- `build_slot_max`: Assigns raw readings to hourly slots, takes max per slot, filters `total_reading <= 0` as anomalous
- `fill_missing_slots`: Linear interpolation for `None` slots from neighbors (source=`'interpolated'`)
- `compute_usage_series`: Usage = current_slot_max - prev_slot_max, negatives clamped to 0
- `smooth_zero_usage`: Detects "0 usage + accumulated neighbor" patterns (e.g. `[0.5, 0, 1.0]` → `[0.5, 0.5, 0.5]`), marks source=`'smoothed'`

Each result tuple is `(value, source)` where source ∈ `{'direct', 'missing', 'interpolated', 'smoothed'}`.

### Frontend (`web/`)

Vanilla HTML/JS/CSS with Chart.js. No framework, no bundler.

- `config.js` — runtime config (API URLs, defaults), gitignored, copy from `example_config.js`
- Three tabs: 数据统计, 数据解析, 宿管模式
- Tab switching toggles `.tab.active` / `.tab-pane.active` CSS classes
- Chart rendering: `prepareMiniChartData()` / `prepareChartData()` transform `rows` → labels/values arrays for Chart.js line charts
- Four display modes: `usage`, `cost`, `total`, `balance` (in dorm mode, forced to `total`)
- Dorm mode uses client-side filtering from `dormDataCache` (no re-fetch on filter change)

### Dorm Manager Mode (宿管模式)

Backend route `check_hourly_building` reuses data_cleaner algorithms to return per-hour **usage** data per building. Frontend has building buttons (1-10 skip 4), status filter, usage threshold filter, and date range selector. Backend truncates future hours for today to prevent 0-value chart tails.

## Configuration System

INI files per service, each reads its own `{name}.ini` from its working directory:

| Service | Config File | Sections |
|---------|-------------|----------|
| `server.py` | `server/server.ini` | `[mysql]`, `[server]`, `[config]` |
| `email_api.py` | `server/email_api.ini` | `[server]`, `[email]`, `[mysql]`, `[aoksender]` |
| `aokbalance_get.py` | `server/aokbalance_get.ini` | `[aok]`, `[server]` |
| `email_checker.py` | `server/email_checker.ini` | `[service]`, `[mysql]`, `[aoksender]`, `[email]` |
| Root scripts | `config/*.ini` | Various |
| `data_cleaner` | `data_cleaner/config/*.ini` | `[mysql]`, `[filter]`, `[align]`, `[output]` |

**Convention**: Example templates are `example_{name}.ini`. Actual configs are gitignored. To set up, copy example and rename:

```bash
cp server/config_examples/example_server.ini server/server.ini
# then edit with real credentials
```

Frontend config: copy `web/example_config.js` → `web/config.js` and set API URLs.

## Cross-Module Imports

`server.py` imports from `data_cleaner/` (sibling directory) using:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data_cleaner'))
from hourly_report import (build_24h_hours, build_slot_max, ...)
```

Any new imports from `data_cleaner/hourly_report.py` must be added to this import line.

## Key API Endpoints (server.py, port 8080)

| `mode` param | Description |
|-------------|-------------|
| `first_screen` | Random device IDs for homepage |
| `check` | Device data by `device_id` + `count` |
| `check_daily_range` | Device daily data by `device_id` + date range |
| `check_hourly_building` | Building hourly usage by `building` + date range (dorm mode) |
| `search` | Search devices by keyword |

Full API docs: `doc/API_DOC.md`

## Important Conventions

- All backend logging uses `print(f"[INFO/WARN/ERROR] ...")` — no logging framework
- Building whitelist for dorm mode is regex `^(1|2|3|5|6|7|8|9|10)$` (building 4 excluded)
- Date range limit for dorm mode: max 7 days
- Email rate limiting: per-email limit (25 records) + daily limit (100/day)
- Frontend `source` field values: `'direct'` = real data, `'interpolated'` = filled gap, `'smoothed'` = averaged from neighbor, `'missing'` = no data. Frontend shows `missingdata` tag for non-direct sources in detail text view.
