#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import configparser
import pymysql
import time
import subprocess
import sys
import os
import traceback
from datetime import datetime
from queue import Queue
import threading
from concurrent.futures import ThreadPoolExecutor
import atexit
from decimal import Decimal

# 读取配置文件
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'email_checker.ini'))

# 服务配置
ROUND_TIME = int(config.get('service', 'round_time'))

# MySQL配置
DB_HOST = config.get('mysql', 'mysql_server')
DB_PORT = int(config.get('mysql', 'mysql_port'))
DB_USER = config.get('mysql', 'login_user')
DB_PASSWORD = config.get('mysql', 'login_passwd')
DB_NAME = config.get('mysql', 'db_schema')

# Aoksend配置
AOKSEND_API_URL = config.get('aoksender', 'server', fallback='https://www.aoksend.com/index/api/send_email')
AOKSEND_APP_KEY = config.get('aoksender', 'app_key')
AOKSEND_REPLY_TO = config.get('aoksender', 'reply_to', fallback=None)
AOKSEND_ALIAS = config.get('aoksender', 'alias', fallback='新毛云')
AOKSEND_ATTACHMENT = config.get('aoksender', 'attachment', fallback=None)

# 邮件模板配置
CHECKER_TEMPLATE_ID = config.get('email', 'checker_template_id')
CHECKER_TITLE_FIELD = config.get('email', 'checker_title', fallback='title')
CHECKER_DEVICE_NAME_FIELD = config.get('email', 'checker_device_name', fallback='acctName')
CHECKER_DEVICE_BALANCE_FIELD = config.get('email', 'checker_device_balance', fallback='remainingBalance')
CHECKER_DEVICE_CHECK_TIME_FIELD = config.get('email', 'checker_device_check_time', fallback='currentDealDate')
CHECKER_DEVICE_STATU_FIELD = config.get('email', 'checker_device_statu', fallback='equipmentStatus')
CHECKER_DEVICE_LATEST_READ_FIELD = config.get('email', 'checker_device_latest_read', fallback='equipmentLatestLarge')

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
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30,
                autocommit=True,
                init_command='SET SESSION sql_mode = "STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"'
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
        conn = connection_pool.get(timeout=10)
        print("[INFO] 从连接池获取数据库连接")
        # 检查连接是否有效
        try:
            conn.ping(reconnect=True)
        except Exception as e:
            print(f"[WARN] 连接已失效，创建新连接: {str(e)}")
            # 连接失效，创建新连接
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4',
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30,
                autocommit=True,
                init_command='SET SESSION sql_mode = "STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"'
            )
        return conn
    except:
        print("[WARN] 连接池获取连接超时，创建新连接")
        # 如果无法从连接池获取连接，创建新连接
        try:
            return pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4',
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30,
                autocommit=True,
                init_command='SET SESSION sql_mode = "STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"'
            )
        except Exception as e:
            print(f"[ERROR] 创建新连接失败: {str(e)}")
            traceback.print_exc()
            return None

# 释放数据库连接
def release_db_connection(conn):
    try:
        # 检查连接是否有效
        conn.ping(reconnect=True)
        # 将连接放回连接池
        if not connection_pool.full():
            connection_pool.put(conn)
        else:
            # 如果连接池已满，关闭连接
            conn.close()
        print("[INFO] 数据库连接已返回连接池")
    except Exception as e:
        print(f"[WARN] 连接无效，连接已关闭: {str(e)}")
        try:
            conn.close()
        except:
            pass

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            connect_timeout=30,
            read_timeout=30,
            write_timeout=30,
            autocommit=True,
            init_command='SET SESSION sql_mode = "STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"'
        )
        return conn
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {str(e)}")
        return None

def get_active_subscriptions():
    """获取所有活跃的订阅用户"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            # 查询所有活跃的订阅用户（已验证且未解绑且未过期）
            sql = """
                SELECT e.email, e.device_id, e.alarm_num, e.equipment_type, d.equipmentName, d.installationSite
                FROM email e
                LEFT JOIN device d ON e.device_id = d.id
                WHERE e.verifi_statu = 1 
                AND e.change_device_statu = 0 
                AND e.life_end_time > NOW()
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            
            subscriptions = []
            for row in results:
                subscriptions.append({
                    'email': row[0],
                    'device_id': row[1],
                    'alarm_num': float(row[2]),
                    'equipment_type': row[3],
                    'equipment_name': row[4],
                    'installation_site': row[5]
                })
            
            return subscriptions
    except Exception as e:
        print(f"[ERROR] 获取活跃订阅用户时出错: {str(e)}")
        traceback.print_exc()
        return []
    finally:
        release_db_connection(conn)

def get_device_latest_data(device_id):
    """获取设备最新的数据记录"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cursor:
            # 获取设备最新的数据记录
            sql = """
                SELECT total_reading, remainingBalance, equipmentStatus, read_time
                FROM data 
                WHERE device_id = %s 
                ORDER BY read_time DESC 
                LIMIT 1
            """
            cursor.execute(sql, (str(device_id),))
            result = cursor.fetchone()
            if result:
                return {
                    'total_reading': float(result[0]) if result[0] is not None else None,
                    'remainingBalance': float(result[1]) if result[1] is not None else 0.0,
                    'equipmentStatus': result[2],
                    'read_time': str(result[3]) if result[3] is not None else None
                }
            return None
    except Exception as e:
        print(f"[ERROR] 获取设备最新数据时出错: {str(e)}")
        return None
    finally:
        release_db_connection(conn)

def send_alert_email(email, device_info, latest_data, alarm_num):
    """发送预警邮件"""
    try:
        # 构造模板数据，处理Decimal类型
        template_data = {
            CHECKER_TITLE_FIELD: '注意注意！设备数值低于预警阀值！',
            CHECKER_DEVICE_NAME_FIELD: device_info.get('equipment_name', '未知设备'),
            CHECKER_DEVICE_BALANCE_FIELD: float(latest_data['remainingBalance']) if isinstance(latest_data['remainingBalance'], Decimal) else latest_data['remainingBalance'],
            CHECKER_DEVICE_CHECK_TIME_FIELD: latest_data['read_time'],
            CHECKER_DEVICE_STATU_FIELD: latest_data['equipmentStatus'],
            CHECKER_DEVICE_LATEST_READ_FIELD: float(latest_data['total_reading']) if latest_data['total_reading'] is not None and isinstance(latest_data['total_reading'], Decimal) else latest_data['total_reading']
        }
        
        # 构建命令行参数
        cmd = [
            sys.executable, 'aoksend-api-cli.py',
            '--api-url', AOKSEND_API_URL,
            '--app-key', AOKSEND_APP_KEY,
            '--template-id', CHECKER_TEMPLATE_ID,
            '--to', email
        ]
        
        if AOKSEND_REPLY_TO:
            cmd.extend(['--reply-to', AOKSEND_REPLY_TO])
        
        if AOKSEND_ALIAS:
            cmd.extend(['--alias', AOKSEND_ALIAS])
        
        # 使用default=str来处理不能序列化的对象
        cmd.extend(['--data', json.dumps(template_data, ensure_ascii=False, default=str)])
        
        if AOKSEND_ATTACHMENT:
            cmd.extend(['--attachment', AOKSEND_ATTACHMENT])
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print(f"[INFO] 预警邮件发送成功到 {email}")
            return True
        else:
            print(f"[ERROR] 预警邮件发送失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] 发送预警邮件时出错: {str(e)}")
        return False

def check_and_alert():
    """检查并发送预警邮件"""
    print(f"[INFO] 开始检查预警阈值，当前时间: {datetime.now()}")
    
    # 获取所有活跃订阅
    subscriptions = get_active_subscriptions()
    print(f"[INFO] 找到 {len(subscriptions)} 个活跃订阅")
    
    # 使用线程池并发处理多个用户
    futures = []
    for subscription in subscriptions:
        future = executor.submit(process_subscription, subscription)
        futures.append(future)
    
    # 等待所有任务完成
    for future in futures:
        try:
            future.result()
        except Exception as e:
            print(f"[ERROR] 处理订阅时出错: {str(e)}")
            traceback.print_exc()

def process_subscription(subscription):
    """处理单个订阅用户"""
    email = subscription['email']
    device_id = subscription['device_id']
    alarm_num = subscription['alarm_num']
    equipment_name = subscription['equipment_name']
    
    print(f"[INFO] 检查设备 {device_id} ({equipment_name}) 的数据")
    
    # 获取设备最新数据
    latest_data = get_device_latest_data(device_id)
    if not latest_data:
        print(f"[WARNING] 无法获取设备 {device_id} 的最新数据")
        return
    
    # 检查余额是否低于预警阈值
    balance = latest_data['remainingBalance']
    if balance < alarm_num:
        print(f"[ALERT] 设备 {device_id} 余额 {balance} 低于预警阈值 {alarm_num}，发送预警邮件")
        # 发送预警邮件
        send_alert_email(email, subscription, latest_data, alarm_num)
    else:
        print(f"[INFO] 设备 {device_id} 余额 {balance} 高于预警阈值 {alarm_num}，无需预警")

def main():
    """主函数"""
    print(f"[INFO] 邮件检查服务启动")
    print(f"[INFO] 检查间隔: {ROUND_TIME} 秒")
    print(f"[INFO] 数据库: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"[INFO] Aoksend API: {AOKSEND_API_URL}")
    print(f"[INFO] Aoksend Template ID: {CHECKER_TEMPLATE_ID}")
    
    try:
        while True:
            try:
                check_and_alert()
                print(f"[INFO] 等待 {ROUND_TIME} 秒后进行下一次检查...")
                time.sleep(ROUND_TIME)
            except KeyboardInterrupt:
                print("[INFO] 收到中断信号，服务退出")
                break
            except Exception as e:
                print(f"[ERROR] 服务运行时出错: {str(e)}")
                traceback.print_exc()
                print(f"[INFO] 等待 {ROUND_TIME} 秒后重试...")
                time.sleep(ROUND_TIME)
    finally:
        # 程序退出时关闭所有连接
        close_all_connections()

if __name__ == '__main__':
    main()