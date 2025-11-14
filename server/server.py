#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import configparser
import pymysql
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
import atexit
from queue import Queue
import re

# 读取配置文件
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'server.ini'))

# 数据库配置
DB_HOST = config.get('mysql', 'mysql_server')
DB_PORT = int(config.get('mysql', 'mysql_port'))
DB_USER = config.get('mysql', 'login_user')
DB_PASSWORD = config.get('mysql', 'login_passwd')
DB_NAME = config.get('mysql', 'db_schema')

# 服务器配置
SERVER_PORT = int(config.get('server', 'port'))

# 首页显示配置
FIRST_SCREEN_COUNT = int(config.get('config', 'first_screen_count'))

# 创建线程池
executor = ThreadPoolExecutor(max_workers=10)

# 连接池设置
CONNECTION_POOL_SIZE = 10
connection_pool = Queue(maxsize=CONNECTION_POOL_SIZE)
connection_lock = threading.Lock()

# 创建初始连接池
def create_connection_pool():
    print(f"[INFO] 初始化数据库连接池，大小: {CONNECTION_POOL_SIZE}")
    for _ in range(CONNECTION_POOL_SIZE):
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4',
                connect_timeout=5,
                read_timeout=5,
                write_timeout=5,
                autocommit=True
            )
            connection_pool.put(conn)
        except Exception as e:
            print(f"[ERROR] 创建连接池失败: {str(e)}")
            traceback.print_exc()

# 关闭所有连接
def close_all_connections():
    print("[INFO] 关闭所有数据库连接")
    with connection_lock:
        while not connection_pool.empty():
            try:
                conn = connection_pool.get_nowait()
                conn.close()
            except:
                pass

# 注册退出处理
atexit.register(close_all_connections)

# 初始化连接池
create_connection_pool()

# 数据库连接函数（使用连接池）
def get_db_connection():
    # 获取连接池中的连接
    try:
        conn = connection_pool.get(timeout=5)
        print("[INFO] 从连接池获取数据库连接")
        return conn
    except:
        print("[WARN] 连接池获取连接超时，创建新连接")
        # 如果无法从连接池获取连接，创建新连接
        return pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            connect_timeout=5,
            read_timeout=5,
            write_timeout=5,
            autocommit=True
        )

# 释放数据库连接
def release_db_connection(conn):
    try:
        # 检查连接是否有效
        conn.ping(reconnect=True)
        # 将连接放回连接池
        connection_pool.put(conn)
        print("[INFO] 数据库连接已返回连接池")
    except Exception as e:
        print(f"[WARN] 连接无效，创建新连接替换: {str(e)}")
        # 连接无效，创建新连接替换
        try:
            new_conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4',
                connect_timeout=5,
                read_timeout=5,
                write_timeout=5,
                autocommit=True
            )
            connection_pool.put(new_conn)
        except Exception as e:
            print(f"[ERROR] 创建替换连接失败: {str(e)}")
            traceback.print_exc()

# 首屏数据接口
def get_first_screen_data():
    print(f"[INFO] 开始获取首屏数据，请求数量: {FIRST_SCREEN_COUNT}")
    conn = None
    try:
        conn = get_db_connection()
        print("[INFO] 数据库连接建立成功")
        with conn.cursor() as cursor:
            # 验证FIRST_SCREEN_COUNT是否在安全范围内
            safe_limit = min(FIRST_SCREEN_COUNT, 100)  # 限制最大返回数量
            # 随机获取配置数量的设备ID
            sql = "SELECT id FROM device ORDER BY RAND() LIMIT %s"
            print(f"[INFO] 执行SQL查询: {sql}")
            cursor.execute(sql, (safe_limit,))
            results = cursor.fetchall()
            device_ids = [str(row[0]) for row in results]
            print(f"[INFO] 查询完成，获取到 {len(device_ids)} 个设备ID")
            
            response = {
                "code": "200",
                "total_num": len(device_ids),
                "device_ids": device_ids
            }
            print(f"[INFO] 首屏数据响应: {response}")
            return response
    except Exception as e:
        print(f"[ERROR] 获取首屏数据时出错: {str(e)}")
        traceback.print_exc()
        return {"code": "500", "error": f"数据库查询错误: {str(e)}"}
    finally:
        if conn:
            release_db_connection(conn)
            print("[INFO] 数据库连接已释放")

# 并行获取多个设备数据
def get_multiple_device_data(device_ids, data_num):
    def fetch_device_data(device_id):
        return device_id, get_device_data(device_id, data_num)
    
    # 使用线程池并行获取设备数据
    futures = [executor.submit(fetch_device_data, device_id) for device_id in device_ids]
    results = {}
    
    for future in futures:
        device_id, data = future.result()
        results[device_id] = data
    
    return results

# 检查设备数据接口
def get_device_data(device_id, data_num):
    print(f"[INFO] 开始获取设备数据，设备ID: {device_id}, 数据数量: {data_num}")
    conn = None
    try:
        conn = get_db_connection()
        print(f"[INFO] 数据库连接建立成功")
        with conn.cursor() as cursor:
            # 获取设备信息
            device_sql = """
                SELECT equipmentName, installationSite, equipmentType, ratio, rate, acctId, status, updated_at, id
                FROM device WHERE id = %s
            """
            print(f"[INFO] 查询设备信息，SQL: {device_sql.strip()}, 参数: {device_id}")
            cursor.execute(device_sql, (device_id,))
            device_info = cursor.fetchone()
            
            if not device_info:
                print(f"[WARN] 未找到设备ID为 {device_id} 的设备")
                return {"code": "404", "error": "设备未找到"}
            print(f"[INFO] 设备信息查询完成")
            
            # 获取设备读数数据
            data_sql = """
                SELECT device_id, read_time, total_reading, remainingBalance
                FROM data WHERE device_id = %s ORDER BY read_time DESC LIMIT %s
            """
            print(f"[INFO] 查询设备读数数据，SQL: {data_sql.strip()}, 参数: ({device_id}, {data_num})")
            cursor.execute(data_sql, (device_id, data_num))
            data_results = cursor.fetchall()
            print(f"[INFO] 读数数据查询完成，获取到 {len(data_results)} 条记录")
            
            # 构造返回数据
            rows = []
            for row in data_results:
                rows.append({
                    "device_id": str(row[0]),
                    "read_time": str(row[1]),
                    "total_reading": str(row[2]),
                    "remainingBalance": str(row[3])
                })
            
            response = {
                "equipmentName": device_info[0],
                "device_id": str(device_info[8]),
                "installationSite": device_info[1],
                "equipmentType": device_info[2],
                "ratio": str(device_info[3]),
                "rate": str(device_info[4]),
                "acctId": device_info[5],
                "status": str(device_info[6]),
                "updated_at": str(device_info[7]),
                "total": len(rows),
                "rows": rows,
                "code": 200
            }
            print(f"[INFO] 设备数据响应构建完成")
            return response
    except Exception as e:
        print(f"[ERROR] 获取设备数据时出错: {str(e)}")
        traceback.print_exc()
        return {"code": "500", "error": f"数据库查询错误: {str(e)}"}
    finally:
        if conn:
            release_db_connection(conn)
            print("[INFO] 数据库连接已释放")

# 搜索设备接口
def search_devices(keyword):
    print(f"[INFO] 开始搜索设备，关键词: {keyword}")
    # 检查关键词长度，2个字符以内包括两个字符不允许查询
    if len(keyword) < 2:
        print(f"[INFO] 关键词长度不足，返回错误提示")
        return {
            "search_status": 1,
            "error_talk": "请输入两个以上的字符。",
            "code": 418
        }
    
    conn = None
    try:
        conn = get_db_connection()
        print(f"[INFO] 数据库连接建立成功")
        with conn.cursor() as cursor:
            # 搜索设备
            sql = """
                SELECT equipmentName, installationSite, id, equipmentType, status
                FROM device WHERE equipmentName LIKE %s OR installationSite LIKE %s
            """
            search_term = f"%{keyword}%"
            print(f"[INFO] 执行搜索查询，SQL: {sql.strip()}, 参数: ({search_term}, {search_term})")
            cursor.execute(sql, (search_term, search_term))
            results = cursor.fetchall()
            print(f"[INFO] 搜索完成，找到 {len(results)} 条记录")
            
            # 构造返回数据
            rows = []
            for row in results:
                rows.append({
                    "equipmentName": row[0],
                    "installationSite": row[1],
                    "device_id": str(row[2]),
                    "equipmentType": str(row[3]),
                    "status": row[4]
                })
            
            response = {
                "search_status": 0,
                "total": len(rows),
                "rows": rows,
                "code": 200
            }
            print(f"[INFO] 搜索响应构建完成: total={len(rows)}")
            return response
    except Exception as e:
        print(f"[ERROR] 搜索设备时出错: {str(e)}")
        traceback.print_exc()
        return {"code": "500", "error": f"数据库查询错误: {str(e)}"}
    finally:
        if conn:
            release_db_connection(conn)
            print("[INFO] 数据库连接已释放")

# HTTP请求处理器
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 获取真实客户端IP
        real_ip = self.headers.get('X-Real-IP') or self.headers.get('X-Forwarded-For') or self.client_address[0]
        print(f"[INFO] 收到GET请求 from {real_ip}: {self.path}")
        response_data = {}
        try:
            # 解析URL和参数
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            print(f"[INFO] 解析参数完成: {params}")
            
            # 处理不同模式的请求
            mode = params.get('mode', [None])[0]
            print(f"[INFO] 请求模式: {mode}")
            
            if mode == 'first_screen':
                # 首屏数据
                print("[INFO] 处理首屏数据请求")
                response_data = get_first_screen_data()
            elif mode == 'check':
                # 检查设备数据
                device_id = params.get('device_id', [None])[0]
                data_num = params.get('data_num', [5])[0]  # 默认5条数据
                print(f"[INFO] 处理设备检查请求，设备ID: {device_id}, 数据量: {data_num}")
                if device_id:
                    # 验证device_id格式（允许字母、数字和下划线，限制长度）
                    if not re.match(r'^[a-zA-Z0-9_]+$', device_id) or len(device_id) > 50:
                        print(f"[WARN] 无效的device_id参数: {device_id}")
                        response_data = {"code": "400", "error": "无效的device_id参数"}
                    else:
                        # 验证data_num是否为有效数字
                        try:
                            num = int(data_num)
                            if num < 1 or num > 1000:  # 限制数据量范围
                                print(f"[WARN] data_num参数超出范围: {num}")
                                response_data = {"code": "400", "error": "data_num参数超出范围(1-1000)"}
                            else:
                                response_data = get_device_data(device_id, num)
                        except ValueError:
                            print(f"[WARN] 无效的data_num参数: {data_num}")
                            response_data = {"code": "400", "error": "无效的data_num参数"}
                else:
                    print("[WARN] 缺少device_id参数")
                    response_data = {"code": "400", "error": "缺少device_id参数"}
            elif mode == 'search':
                # 搜索设备
                keyword = params.get('key_word', [None])[0]
                print(f"[INFO] 处理搜索设备请求，关键词: {keyword}")
                if keyword:
                    # 验证keyword是否为有效格式，只允许字母、数字和中文
                    if not isinstance(keyword, str) or len(keyword) > 50 or not re.match(r'^[a-zA-Z0-9\u4e00-\u9fa5\s]+$', keyword):
                        print(f"[WARN] 搜索关键词包含非法字符: {keyword}")
                        response_data = {"code": "400", "error": "搜索关键词包含非法字符"}
                    else:
                        response_data = search_devices(keyword)
                else:
                    print("[WARN] 缺少key_word参数")
                    response_data = {"code": "400", "error": "缺少key_word参数"}
            else:
                print(f"[WARN] 无效的mode参数: {mode}")
                response_data = {"code": "400", "error": "无效的mode参数"}
            
            print(f"[INFO] 请求处理完成，响应数据: {response_data.get('code', 'N/A')}")
        except Exception as e:
            print(f"[ERROR] 处理请求时出错: {str(e)}")
            traceback.print_exc()
            response_data = {"code": "500", "error": f"服务器内部错误: {str(e)}"}
        finally:
            # 设置响应头
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # 允许跨域
            self.end_headers()
            
            # 发送响应
            print(f"[INFO] 发送响应，响应长度: {len(json.dumps(response_data, ensure_ascii=False))}")
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            
            # 确保数据发送完成并关闭连接
            self.wfile.flush()
            print("[INFO] 响应发送完成")

# 启动服务器
if __name__ == '__main__':
    server = HTTPServer(('', SERVER_PORT), RequestHandler)
    print(f"服务器启动，监听端口 {SERVER_PORT}")
    server.serve_forever()