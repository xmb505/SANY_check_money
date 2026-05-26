#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server/libs/db_pool.py

MySQL 数据库连接池封装。提供连接池初始化和上下文管理器两种用法。

用法（显式参数）:
    from server.libs.db_pool import init_pool, get_conn, close_pool

    init_pool(host, port, user, password, database, pool_size=30)

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM device LIMIT 1")
        result = cur.fetchall()
    release_conn(conn)

用法（配置文件）:
    from server.libs.db_pool import init_pool_from_ini

    init_pool_from_ini('/path/to/service.ini', pool_size=30)
"""

import atexit
import threading
from queue import Queue
from contextlib import contextmanager

import pymysql

# 全局状态
_pool: Queue = Queue()
_lock = threading.Lock()
_initialized = False
_db_config = {}


def init_pool(host: str, port: int, user: str, password: str,
              database: str, pool_size: int = 30):
    """
    用显式参数初始化连接池（只应调用一次）。

    Args:
        host, port, user, password, database: MySQL 连接参数
        pool_size: 连接池大小，默认 30
    """
    global _initialized, _db_config
    if _initialized:
        print("[WARN] 连接池已初始化，跳过")
        return

    _db_config = dict(host=host, port=port, user=user,
                      password=password, database=database)

    print(f"[INFO] 初始化数据库连接池，大小: {pool_size}")

    for _ in range(pool_size):
        try:
            conn = _create_conn()
            _pool.put(conn)
        except Exception as e:
            print(f"[ERROR] 创建连接失败: {e}")

    atexit.register(_close_all)
    _initialized = True
    print(f"[INFO] 连接池初始化完成，{_pool.qsize()} 个可用连接")


def init_pool_from_ini(ini_path: str, pool_size: int = 30):
    """
    从 INI 配置文件初始化连接池。

    Args:
        ini_path: 配置文件路径（需含 [mysql] 节）
        pool_size: 连接池大小，默认 30
    """
    import configparser
    cfg = configparser.ConfigParser()
    cfg.read(ini_path)

    init_pool(
        host=cfg.get('mysql', 'mysql_server'),
        port=cfg.getint('mysql', 'mysql_port'),
        user=cfg.get('mysql', 'login_user'),
        password=cfg.get('mysql', 'login_passwd'),
        database=cfg.get('mysql', 'db_schema'),
        pool_size=pool_size
    )


def _create_conn():
    """创建新连接"""
    return pymysql.connect(
        host=_db_config['host'],
        port=_db_config['port'],
        user=_db_config['user'],
        password=_db_config['password'],
        database=_db_config['database'],
        charset='utf8mb4',
        connect_timeout=5,
        read_timeout=5,
        write_timeout=5,
        autocommit=True,
        init_command='SET SESSION sql_mode = "STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"'
    )


def _close_all():
    """关闭所有连接"""
    global _initialized
    print("[INFO] 关闭所有数据库连接")
    _initialized = False
    with _lock:
        while not _pool.empty():
            try:
                _pool.get_nowait().close()
            except Exception:
                pass


@contextmanager
def get_connection():
    """
    获取数据库连接的上下文管理器。

    用法:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    """
    if not _initialized:
        raise RuntimeError("连接池未初始化，请先调用 init_pool() 或 init_pool_from_ini()")

    conn = None
    try:
        conn = _pool.get(timeout=5)
        conn.ping(reconnect=True)
    except Exception:
        # 获取超时或连接失效，直接创建新连接
        try:
            conn = _create_conn()
        except Exception as e:
            raise RuntimeError(f"无法获取数据库连接: {e}")

    try:
        yield conn
    finally:
        _release(conn)


def _release(conn):
    """归还连接，若连接无效则关闭"""
    try:
        conn.ping(reconnect=True)
        if not _pool.full():
            _pool.put_nowait(conn)
        else:
            conn.close()
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def get_pool_size() -> int:
    """返回连接池当前可用连接数"""
    return _pool.qsize()


def is_initialized() -> bool:
    """返回连接池是否已初始化"""
    return _initialized