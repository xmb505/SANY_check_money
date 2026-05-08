#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_cleaner/hourly_report.py

将 data 表的原始读数整点化，输出每设备每小时一个最优 total_reading。
支持标准24小时制和日式30小时制两种输出模式。

用法:
  python hourly_report.py                                   # 自动判断日期
  python hourly_report.py --date 2026-04-16                 # 单日
  python hourly_report.py --date-range 2026-04-01:2026-04-16  # 日期范围，每天一个文件
  python hourly_report.py --mode 24                         # 标准24小时制
  python hourly_report.py --mode 30                         # 日式30小时制
  python hourly_report.py --filter 室电表                   # 覆盖设备名过滤关键字
"""

import argparse
import configparser
import csv
import os
import sys
from datetime import datetime, date, timedelta, timezone

import pymysql

# UTC+8
TZ_UTC8 = timezone(timedelta(hours=8))

# 配置文件默认值（当 config.ini 缺少某项时使用）
_DEFAULTS = {
    'device_name_filter':      '室电表',
    'align_threshold_minutes': '29',
    'output_dir':              './output',
    'filename_template':       '{date}_{mode}.csv',
    'default_mode':            '24',
    'output_type':             'usage',
    'max_missing_count':       '10',
    'min_usage_24h':           '0.7',
    'min_usage_30h':           '1.0',
}


# ─────────────────────────────────────────────
# 配置加载
# ─────────────────────────────────────────────

def load_app_config() -> configparser.ConfigParser:
    """加载 config/config.ini，文件不存在时使用全部默认值并给出提示。"""
    cfg = configparser.ConfigParser(defaults=_DEFAULTS)
    ini_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.ini')
    if not os.path.exists(ini_path):
        example = ini_path.replace('config.ini', 'example_config.ini')
        print(f"[WARN] 配置文件不存在: {ini_path}")
        print(f"       请参考 {example} 创建配置文件，当前使用全部默认值")
        for sec in ('filter', 'align', 'output', 'filter_output'):
            cfg.add_section(sec)
    else:
        cfg.read(ini_path, encoding='utf-8')
        for sec in ('filter', 'align', 'output', 'filter_output'):
            if not cfg.has_section(sec):
                cfg.add_section(sec)
    return cfg


def load_mysql_config() -> configparser.ConfigParser:
    """加载 config/mysql.ini，不存在则报错退出。"""
    ini_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'mysql.ini')
    if not os.path.exists(ini_path):
        example = ini_path.replace('mysql.ini', 'example_mysql.ini')
        print(f"[ERROR] 数据库配置文件不存在: {ini_path}")
        print(f"        请参考 {example} 创建配置文件")
        sys.exit(1)
    cfg = configparser.ConfigParser()
    cfg.read(ini_path, encoding='utf-8')
    return cfg


# ─────────────────────────────────────────────
# 数据库连接
# ─────────────────────────────────────────────

def get_connection(cfg: configparser.ConfigParser):
    try:
        return pymysql.connect(
            host=cfg.get('mysql', 'mysql_server'),
            port=cfg.getint('mysql', 'mysql_port'),
            user=cfg.get('mysql', 'login_user'),
            password=cfg.get('mysql', 'login_passwd'),
            database=cfg.get('mysql', 'db_schema'),
            charset='utf8mb4',
            connect_timeout=10,
        )
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────
# 日期逻辑
# ─────────────────────────────────────────────

def resolve_target_date(user_date_str: str | None) -> date:
    """
    确定单日模式的目标日期。
    - 未指定：UTC+8 >= 10:00 → 昨天，否则 → 前天
    - 已指定：不能是未来或当天
    """
    now_utc8 = datetime.now(TZ_UTC8)
    today = now_utc8.date()

    if user_date_str is None:
        return today - timedelta(days=1) if now_utc8.hour >= 10 else today - timedelta(days=2)

    try:
        target = date.fromisoformat(user_date_str)
    except ValueError:
        print(f"[ERROR] 日期格式错误: '{user_date_str}'，请使用 YYYY-MM-DD 格式")
        sys.exit(1)

    if target >= today:
        print(f"[ERROR] 禁止计算未来或当天数据（目标: {target}，今天: {today}）")
        sys.exit(1)

    return target


def resolve_date_range(range_str: str) -> list[date]:
    """
    解析 --date-range 参数，格式 YYYY-MM-DD:YYYY-MM-DD。
    返回从 start 到 end（含）的日期列表，全部不能是未来或当天。
    """
    today = datetime.now(TZ_UTC8).date()

    parts = range_str.split(':')
    if len(parts) != 2:
        print(f"[ERROR] --date-range 格式错误: '{range_str}'，请使用 YYYY-MM-DD:YYYY-MM-DD")
        sys.exit(1)

    try:
        start = date.fromisoformat(parts[0].strip())
        end   = date.fromisoformat(parts[1].strip())
    except ValueError:
        print(f"[ERROR] --date-range 日期格式错误，请使用 YYYY-MM-DD:YYYY-MM-DD")
        sys.exit(1)

    if start > end:
        print(f"[ERROR] --date-range 起始日期 {start} 晚于结束日期 {end}")
        sys.exit(1)

    if end >= today:
        print(f"[ERROR] 禁止计算未来或当天数据（结束日期: {end}，今天: {today}）")
        sys.exit(1)

    dates = []
    cur = start
    while cur <= end:
        dates.append(cur)
        cur += timedelta(days=1)
    return dates


# ─────────────────────────────────────────────
# 数据查询
# ─────────────────────────────────────────────

def fetch_devices(conn, name_filters: list[str]) -> list[dict]:
    """查询所有符合条件的电表设备（name_filters 关键字满足任意一个即可）。"""
    conditions = " OR ".join(["equipmentName LIKE %s"] * len(name_filters))
    sql = f"""
        SELECT id, equipmentName, installationSite
        FROM device
        WHERE equipmentType = 0
          AND ({conditions})
        ORDER BY equipmentName
    """
    params = [f"%{kw}%" for kw in name_filters]
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    devices = [{"id": r[0], "name": r[1] or "", "site": r[2] or ""} for r in rows]
    print(f"[INFO] 查询到 {len(devices)} 个电表设备（过滤关键字: {name_filters}）")
    return devices


def fetch_raw_readings(conn, device_ids: list,
                       query_start: datetime, query_end: datetime) -> dict:
    """
    查询指定设备在时间范围内的原始读数。
    返回 {device_id: [(read_time, total_reading), ...]}，按 read_time 升序。
    """
    if not device_ids:
        return {}

    placeholders = ",".join(["%s"] * len(device_ids))
    sql = f"""
        SELECT device_id, read_time, total_reading
        FROM data
        WHERE device_id IN ({placeholders})
          AND read_time BETWEEN %s AND %s
          AND unStandard = 0
          AND total_reading IS NOT NULL
        ORDER BY device_id, read_time
    """
    params = list(device_ids) + [query_start, query_end]
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    readings: dict = {}
    for device_id, read_time, total_reading in rows:
        readings.setdefault(device_id, []).append((read_time, float(total_reading)))

    total = sum(len(v) for v in readings.values())
    print(f"[INFO] 查询到 {total} 条原始读数，覆盖 {len(readings)} 个设备")
    return readings


# ─────────────────────────────────────────────
# 整点取值算法
# ─────────────────────────────────────────────

def build_slot_max(readings: list, slot_starts: list[datetime]) -> list[tuple[float | None, str]]:
    """
    按小时段取最大 total_reading（即该小时段内最后上报的有效读数）。

    slot_starts: N 个整点，定义 N 个半开区间 [slot_starts[i], slot_starts[i+1])
                 最后一个 slot 的右边界为 slot_starts[-1] + 1小时。

    策略：
    - 该小时段内有数据 -> 取最大值（累计量单调递增，最大值即最新值）-> 'direct'
    - 该小时段内无数据 -> None, 'missing'

    返回长度与 slot_starts 相同的列表，每项为 (max_reading_or_None, source)。
    """
    n = len(slot_starts)
    slot_end = slot_starts[-1] + timedelta(hours=1)

    # 按时间分配每条读数到对应 slot，过滤异常的 0 值读数
    slots: list[list[float]] = [[] for _ in range(n)]
    for rt, val in readings:
        if rt < slot_starts[0] or rt >= slot_end:
            continue
        if val <= 0:
            # 累计量不应为 0 或负值，视为电表通信异常，跳过
            continue
        # 二分找 slot 索引
        lo, hi = 0, n - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if rt >= slot_starts[mid]:
                lo = mid
            else:
                hi = mid - 1
        slots[lo].append(val)

    result = []
    for s in slots:
        if s:
            result.append((max(s), 'direct'))
        else:
            result.append((None, 'missing'))
    return result


def fill_missing_slots(slot_vals: list[tuple[float | None, str]]) -> list[tuple[float | None, str]]:
    """
    对 missing 的 slot，用相邻有效 slot 的最大值线性插值。
    若左右都无有效值则保持 None。
    """
    result = list(slot_vals)
    n = len(result)
    for i in range(n):
        if result[i][0] is not None:
            continue
        # 找左侧最近有效值
        before_idx, before_val = None, None
        for j in range(i - 1, -1, -1):
            if result[j][0] is not None:
                before_idx, before_val = j, result[j][0]
                break
        # 找右侧最近有效值
        after_idx, after_val = None, None
        for j in range(i + 1, n):
            if result[j][0] is not None:
                after_idx, after_val = j, result[j][0]
                break

        if before_val is not None and after_val is not None:
            ratio = (i - before_idx) / (after_idx - before_idx)
            interp = round(before_val + (after_val - before_val) * ratio, 4)
            result[i] = (interp, 'interpolated')
        elif before_val is not None:
            result[i] = (before_val, 'interpolated')
        elif after_val is not None:
            result[i] = (after_val, 'interpolated')
    return result


def compute_usage_series(slot_vals: list[tuple[float | None, str]],
                         anchor: float | None) -> list[tuple[float | None, str]]:
    """
    将每个 slot 的 max total_reading 转换为用量（与上一 slot 的差值）。

    anchor: 第一个 slot 的前一小时的 max total_reading（即前一天23:00段的值）。
            为 None 时第一列留空。

    用量 = 当前 slot max - 上一 slot max，负值置 0。
    任一侧为 None 则该列留空。
    """
    result = []
    prev_val = anchor
    for val, src in slot_vals:
        if val is not None and prev_val is not None:
            usage = round(max(0.0, val - prev_val), 4)
            result.append((usage, src))
        else:
            result.append((None, src))
        prev_val = val
    return result


def smooth_zero_usage(usage_series: list[tuple[float | None, str]],
                      zero_threshold: float = 0.02
                      ) -> list[tuple[float | None, str]]:
    """
    平滑用量为 0（或接近 0）的异常时段。

    典型场景：电表某小时未上报读数，该小时用量为 0，而下一小时累积了
    多个小时的用量。例如 [0.5, 0, 1.0] → [0.5, 0.5, 0.5]。

    算法：
    1. 找到连续的近零用量段（< zero_threshold）
    2. 取近零段之前的正常用量作为参考值
    3. 若近零段右侧的用量接近"参考值 × 段长"（即累积了多段用量），
       则将近零段 + 右侧合并后平均分配，标记为 'smoothed'
    """
    result = list(usage_series)
    n = len(result)

    i = 0
    while i < n:
        val, src = result[i]
        if val is None or val >= zero_threshold:
            i += 1
            continue

        # ── 找连续近零段 [run_start, run_end) ──
        run_start = i
        while i < n and result[i][0] is not None and result[i][0] < zero_threshold:
            i += 1
        run_end = i  # 近零段结束位置（不含）

        # 取近零段之前的参考值（正常时段用量）
        if run_start == 0:
            continue  # 序列开头无参考，跳过
        ref = result[run_start - 1][0]
        if ref is None or ref <= zero_threshold:
            continue  # 参考值也是零，跳过

        # ── 检查右侧值是否为累积用量 ──
        if run_end >= n or result[run_end][0] is None:
            continue
        right_val = result[run_end][0]
        zero_count = run_end - run_start
        # 如果用量均匀，右侧值应 ≈ ref；实际它累积了 (zero_count+1) 段用量
        expected_accumulated = ref * (zero_count + 1)

        if right_val >= expected_accumulated * 0.5:
            # 右侧值达到预期累积量的一半以上，判定为累积，执行平滑
            total = sum(result[k][0] for k in range(run_start, run_end + 1))
            avg = round(total / (zero_count + 1), 4)
            for k in range(run_start, run_end + 1):
                result[k] = (avg, 'smoothed')
            i = run_end + 1
            continue

    return result


# ─────────────────────────────────────────────
# 时间序列生成
# ─────────────────────────────────────────────

def build_24h_hours(target_date: date) -> list[datetime]:
    """标准24小时制：target_date 00:00 ~ 23:00，共24个整点"""
    base = datetime(target_date.year, target_date.month, target_date.day, 0, 0)
    return [base + timedelta(hours=h) for h in range(24)]


def build_30h_hours(target_date: date) -> list[datetime]:
    """日式30小时制：target_date 00:00 ~ 次日 05:00，共30个整点"""
    base = datetime(target_date.year, target_date.month, target_date.day, 0, 0)
    return [base + timedelta(hours=h) for h in range(30)]


# ─────────────────────────────────────────────
# CSV 输出
# ─────────────────────────────────────────────

def get_anchor_max(raw: list, anchor_start: datetime, anchor_end: datetime) -> float | None:
    """
    从原始读数中取 [anchor_start, anchor_end) 区间内的最大 total_reading。
    用作 h00:00 用量计算的前值锚点（即前一天 23:00 段的最大值）。
    """
    vals = [val for rt, val in raw if anchor_start <= rt < anchor_end]
    return max(vals) if vals else None


def write_csv(filepath: str, devices: list[dict], readings_map: dict,
              hour_datetimes: list[datetime], hour_labels: list[str],
              threshold_sec: int, output_type: str,
              anchor_start: datetime | None = None,
              anchor_end: datetime | None = None,
              max_missing_count: int = 10,
              min_usage_threshold: float = 0.7):
    """
    输出 CSV，每行一个设备：
    device_id, equipment_name, installation_site, h00:00, ..., interpolated_count, missing_count

    output_type:
      'reading' -> 每列为该整点的累计总量
      'usage'   -> 每列为该整点与上一整点的差值（用量）
                   当 anchor_start/anchor_end 有值时，用前一天 23:00 段最大值作为 h00:00 的前值锚点，
                   使 h00:00 的用量 = h00:00段最大值 - 前一天23:00段最大值，不再留空。
    """
    header = (["device_id", "equipment_name", "installation_site"] +
              [f"h{lbl}" for lbl in hour_labels] +
              ["interpolated_count", "missing_count"])

    out_dir = os.path.dirname(filepath)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for dev in devices:
            did = dev["id"]
            raw = readings_map.get(did, [])

            # 按小时段取最大值，再对缺失段插值
            slot_vals = build_slot_max(raw, hour_datetimes)
            slot_vals = fill_missing_slots(slot_vals)

            if output_type == 'usage':
                # 取前一天 23:00 段最大值作为 h00:00 的前值锚点
                anchor_val = None
                if anchor_start is not None and anchor_end is not None:
                    anchor_val = get_anchor_max(raw, anchor_start, anchor_end)
                usage_vals = compute_usage_series(slot_vals, anchor_val)
                values = [(v if v is not None else "", src) for v, src in usage_vals]
            else:
                values = [(val if val is not None else "", src) for val, src in slot_vals]

            row = [did, dev["name"], dev["site"]]
            interp_count = 0
            missing_count = 0
            for val, src in values:
                row.append(val)
                if src == 'interpolated':
                    interp_count += 1
                elif src == 'missing':
                    missing_count += 1
            row += [interp_count, missing_count]

            # 过滤1：missing 过多（数据基本缺失）
            if missing_count > max_missing_count:
                continue

            # 过滤2：全天用量低于阈值
            numeric_vals = [v for v, _ in values if isinstance(v, (int, float))]
            if sum(numeric_vals) < min_usage_threshold:
                continue

            writer.writerow(row)

    print(f"[INFO] 已输出 {len(devices)} 行 -> {filepath}")


def resolve_output_path(output_dir: str, template: str,
                        date_str: str, mode_label: str) -> str:
    """根据模板生成输出文件路径，相对路径以程序所在目录为基准。"""
    filename = template.format(date=date_str, mode=mode_label)
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_dir)
    return os.path.join(output_dir, filename)


# ─────────────────────────────────────────────
# 单日处理
# ─────────────────────────────────────────────

def process_date(target_date: date, mode: str, devices: list[dict],
                 conn, threshold_sec: int,
                 output_dir: str, filename_template: str, output_type: str,
                 max_missing_count: int = 10, min_usage_24h: float = 0.7,
                 min_usage_30h: float = 1.0):
    """处理单个日期，查询数据并输出 CSV。"""
    device_ids = [d["id"] for d in devices]
    date_str   = target_date.strftime("%Y%m%d")

    # 查询时间范围：前一天 23:00 ~ 当天末尾（按模式决定）
    # 多查前一天 23:00 这一段，用于计算 h00:00 的用量锚点
    anchor_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0) - timedelta(hours=1)
    query_start  = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    hours_span   = 24 if mode == '24' else 30
    query_end    = query_start + timedelta(hours=hours_span) - timedelta(seconds=1)
    print(f"[INFO] [{target_date}] 查询时间范围: {anchor_start} ~ {query_end}")

    readings_map = fetch_raw_readings(conn, device_ids, anchor_start, query_end)

    if mode == '24':
        hours     = build_24h_hours(target_date)
        labels    = [f"{h:02d}:00" for h in range(24)]
        path      = resolve_output_path(output_dir, filename_template, date_str, '24h')
        min_usage = min_usage_24h
        write_csv(path, devices, readings_map, hours, labels, threshold_sec, output_type,
                  anchor_start=anchor_start, anchor_end=query_start,
                  max_missing_count=max_missing_count, min_usage_threshold=min_usage)

    elif mode == '30':
        hours     = build_30h_hours(target_date)
        labels    = [f"{h:02d}:00" for h in range(30)]
        path      = resolve_output_path(output_dir, filename_template, date_str, '30h')
        min_usage = min_usage_30h
        write_csv(path, devices, readings_map, hours, labels, threshold_sec, output_type,
                  anchor_start=anchor_start, anchor_end=query_start,
                  max_missing_count=max_missing_count, min_usage_threshold=min_usage)


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="电表读数整点化清洗报表工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python hourly_report.py                                      # 自动日期
  python hourly_report.py --date 2026-04-16                    # 单日
  python hourly_report.py --date-range 2026-04-01:2026-04-16   # 日期范围，每天一个文件
  python hourly_report.py --mode 30                            # 日式30小时制
  python hourly_report.py --filter 室电表                      # 覆盖设备名过滤关键字

30小时制说明（--date-range 模式）:
  4/15 的文件包含 00:00~29:00，其中 24:00~29:00 对应 4/16 的 00:00~05:00
  4/16 的文件包含 00:00~29:00，其中 00:00~05:00 与 4/15 的 24:00~29:00 重叠
  此重叠为设计行为，方便 AI 训练时保留跨日时间上下文。
        """
    )

    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument('--date',       type=str, default=None,
                            help='单日模式，目标日期 YYYY-MM-DD（默认自动判断）')
    date_group.add_argument('--date-range', type=str, default=None, dest='date_range',
                            help='多日模式，格式 YYYY-MM-DD:YYYY-MM-DD，每天输出一个文件')

    parser.add_argument('--mode',   type=str, default=None,
                        choices=['24', '30'],
                        help='输出模式：24（标准24小时制）/ 30（日式30小时制），覆盖配置文件 default_mode')
    parser.add_argument('--filter', type=str, default=None, dest='filter_kw',
                        help='设备名过滤关键字，覆盖 config.ini 中的设置（逗号分隔多个）')
    args = parser.parse_args()

    # ── 加载配置 ──
    app_cfg   = load_app_config()
    mysql_cfg = load_mysql_config()

    # 过滤关键字：CLI > config.ini > 默认值
    if args.filter_kw:
        name_filters = [kw.strip() for kw in args.filter_kw.split(',') if kw.strip()]
    else:
        raw = app_cfg.get('filter', 'device_name_filter', fallback=_DEFAULTS['device_name_filter'])
        name_filters = [kw.strip() for kw in raw.split(',') if kw.strip()]

    # 对齐阈值
    threshold_min = app_cfg.getint('align', 'align_threshold_minutes',
                                   fallback=int(_DEFAULTS['align_threshold_minutes']))
    threshold_sec = threshold_min * 60

    # 输出目录 & 文件名模板 & 数据类型
    output_dir        = app_cfg.get('output', 'output_dir',        fallback=_DEFAULTS['output_dir'])
    filename_template = app_cfg.get('output', 'filename_template', fallback=_DEFAULTS['filename_template'])
    output_type       = app_cfg.get('output', 'output_type',       fallback=_DEFAULTS['output_type'])
    if output_type not in ('reading', 'usage'):
        print(f"[ERROR] config.ini 中 output_type 值无效: '{output_type}'，可选值为 reading / usage")
        sys.exit(1)

    # 输出模式：CLI > config.ini > 默认值
    if args.mode:
        mode = args.mode
    else:
        mode = app_cfg.get('output', 'default_mode', fallback=_DEFAULTS['default_mode'])
        if mode not in ('24', '30'):
            print(f"[ERROR] config.ini 中 default_mode 值无效: '{mode}'，可选值为 24 / 30")
            sys.exit(1)

    # 输出过滤阈值
    max_missing_count = app_cfg.getint('filter_output', 'max_missing_count',
                                       fallback=int(_DEFAULTS['max_missing_count']))
    min_usage_24h     = app_cfg.getfloat('filter_output', 'min_usage_24h',
                                         fallback=float(_DEFAULTS['min_usage_24h']))
    min_usage_30h     = app_cfg.getfloat('filter_output', 'min_usage_30h',
                                         fallback=float(_DEFAULTS['min_usage_30h']))

    print(f"[INFO] 过滤关键字: {name_filters}")
    print(f"[INFO] 整点对齐阈值: ±{threshold_min} 分钟")
    print(f"[INFO] 输出模式: {mode}")
    print(f"[INFO] 数据类型: {output_type}")
    print(f"[INFO] 输出目录: {output_dir}")
    print(f"[INFO] 过滤: missing>{max_missing_count} 或总用量<{min_usage_24h if mode == '24' else min_usage_30h}kWh 的设备将被丢弃")

    # ── 确定日期列表 ──
    if args.date_range:
        target_dates = resolve_date_range(args.date_range)
        print(f"[INFO] 多日模式: {target_dates[0]} ~ {target_dates[-1]}，共 {len(target_dates)} 天")
    else:
        target_dates = [resolve_target_date(args.date)]
        print(f"[INFO] 单日模式: {target_dates[0]}")

    # ── 连接数据库 ──
    conn = get_connection(mysql_cfg)

    try:
        devices = fetch_devices(conn, name_filters)
        if not devices:
            print("[WARN] 没有符合条件的设备，退出")
            return

        for target_date in target_dates:
            process_date(target_date, mode, devices, conn,
                         threshold_sec, output_dir, filename_template, output_type,
                         max_missing_count=max_missing_count,
                         min_usage_24h=min_usage_24h, min_usage_30h=min_usage_30h)

        print(f"[INFO] 全部完成，共处理 {len(target_dates)} 天")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
