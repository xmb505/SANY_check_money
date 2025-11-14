#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import configparser
import pymysql
import random
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import sys
import os
import traceback
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import atexit
from queue import Queue
import threading

# 读取配置文件
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'email_api.ini'))

# 服务器配置
SERVER_PORT = int(config.get('server', 'port'))

# MySQL配置
DB_HOST = config.get('mysql', 'mysql_server')
DB_PORT = int(config.get('mysql', 'mysql_port'))
DB_USER = config.get('mysql', 'login_user')
DB_PASSWORD = config.get('mysql', 'login_passwd')
DB_NAME = config.get('mysql', 'db_schema')

# 邮件配置
EMAIL_LIMIT = int(config.get('email', 'email_limit', fallback=25))
EMAIL_DAILY_LIMIT = int(config.get('email', 'email_daily_limit', fallback=100))

# Aoksend新注册庆祝邮件配置
NEW_CELEBRATE_TEMPLATE_ID = config.get('aoksender', 'new_celebrate_template_id', fallback='')
NEW_CELEBRATE_TITLE_FIELD = config.get('aoksender', 'new_celebrate_title', fallback='title')
NEW_CELEBRATE_DEVICE_NAME_FIELD = config.get('aoksender', 'new_celebrate_device_name', fallback='acctName')
NEW_CELEBRATE_DEVICE_BALANCE_FIELD = config.get('aoksender', 'new_celebrate_device_balance', fallback='remainingBalance')
NEW_CELEBRATE_DEVICE_CHECK_TIME_FIELD = config.get('aoksender', 'new_celebrate_device_check_time', fallback='currentDealDate')
NEW_CELEBRATE_DEVICE_STATU_FIELD = config.get('aoksender', 'new_celebrate_device_statu', fallback='equipmentStatus')
NEW_CELEBRATE_DEVICE_LATEST_READ_FIELD = config.get('aoksender', 'new_celebrate_device_latest_read', fallback='equipmentLatestLarge')

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
                if conn:
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

# 保持向后兼容的别名
connect_db = get_db_connection

def validate_email_format(email):
    """验证邮箱格式"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_verification_code():
    """生成6位验证码"""
    return random.randint(100000, 999999)

def get_real_ip(request_handler):
    """获取真实IP地址"""
    real_ip = request_handler.headers.get('X-Real-IP') or \
              request_handler.headers.get('X-Forwarded-For') or \
              request_handler.client_address[0]
    return real_ip

def check_device_exists(device_id):
    """检查设备是否存在"""
    conn = get_db_connection()
    if not conn:
        return False, None
    
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, equipmentType FROM device WHERE id = %s"
            cursor.execute(sql, (str(device_id),))
            result = cursor.fetchone()
            if result:
                return True, result[1]
            else:
                return False, None
    except Exception as e:
        print(f"[ERROR] 检查设备存在性时出错: {str(e)}")
        traceback.print_exc()
        return False, None
    finally:
        release_db_connection(conn)

def check_device_type_match(device_id, expected_type):
    """检查设备类型是否匹配"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            sql = "SELECT equipmentType FROM device WHERE id = %s"
            cursor.execute(sql, (str(device_id),))
            result = cursor.fetchone()
            
            if result is None:
                return False  # 设备不存在
            
            actual_type = result[0]
            return actual_type == expected_type
    except Exception as e:
        print(f"[ERROR] 检查设备类型匹配时出错: {str(e)}")
        return False
    finally:
        release_db_connection(conn)

def count_email_records(email):
    """统计邮箱在表中的记录数"""
    conn = get_db_connection()
    if not conn:
        return -1
    
    try:
        with conn.cursor() as cursor:
            sql = "SELECT COUNT(*) FROM email WHERE email = %s"
            cursor.execute(sql, (email,))
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        print(f"[ERROR] 统计邮箱记录数时出错: {str(e)}")
        return -1
    finally:
        release_db_connection(conn)

def count_active_user_records(email, equipment_type):
    """统计用户特定设备类型的记录数"""
    conn = get_db_connection()
    if not conn:
        return -1
    
    try:
        with conn.cursor() as cursor:
            sql = "SELECT COUNT(*) FROM email WHERE email = %s AND equipment_type = %s"
            cursor.execute(sql, (email, equipment_type))
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        print(f"[ERROR] 统计用户特定设备类型记录数时出错: {str(e)}")
        return -1
    finally:
        release_db_connection(conn)

# 使用内存字典存储每日邮件发送次数，格式为 {email: {date: count}}
daily_email_counts = {}

def count_emails_sent_today(email):
    """统计用户今天发送的邮件数量"""
    today = datetime.now().date().isoformat()
    
    # 检查是否是今天的新日期，如果是则清理旧日期
    cleanup_old_dates()
    
    # 获取该邮箱今天的邮件发送次数
    if email not in daily_email_counts:
        daily_email_counts[email] = {}
    
    if today not in daily_email_counts[email]:
        daily_email_counts[email][today] = 0
    
    return daily_email_counts[email][today]

def cleanup_old_dates():
    """清理过期的日期数据（保留最近3天的数据）"""
    today = datetime.now().date()
    cutoff_date = (today - timedelta(days=3)).isoformat()
    
    # 遍历所有邮箱的记录
    for email in list(daily_email_counts.keys()):
        # 删除超过3天的日期记录
        for date_str in list(daily_email_counts[email].keys()):
            if date_str < cutoff_date:
                del daily_email_counts[email][date_str]
        
        # 如果邮箱没有有效记录，删除该邮箱
        if not daily_email_counts[email]:
            del daily_email_counts[email]

def record_email_sent(email):
    """记录邮件发送"""
    today = datetime.now().date().isoformat()
    
    # 清理旧日期数据
    cleanup_old_dates()
    
    # 增加该邮箱今天的邮件发送次数
    if email not in daily_email_counts:
        daily_email_counts[email] = {}
    
    if today not in daily_email_counts[email]:
        daily_email_counts[email][today] = 0
    
    daily_email_counts[email][today] += 1
    return True

def check_verification_records(email, equipment_type):
    """检查用户特定设备类型的验证记录状态"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cursor:
            sql = "SELECT verifi_end_time, verifi_statu, life_end_time, change_device_statu FROM email WHERE email = %s AND equipment_type = %s ORDER BY created_time DESC"
            cursor.execute(sql, (email, equipment_type))
            results = cursor.fetchall()
            return results
    except Exception as e:
        print(f"[ERROR] 检查验证记录状态时出错: {str(e)}")
        return None
    finally:
        release_db_connection(conn)

def check_active_subscription(email, device_id, equipment_type):
    """检查用户是否有正在使用的订阅"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            sql = """SELECT id FROM email 
                     WHERE email = %s 
                     AND device_id = %s 
                     AND equipment_type = %s 
                     AND verifi_statu = 1 
                     AND change_device_statu = 0 
                     AND life_end_time > NOW()"""
            cursor.execute(sql, (email, device_id, equipment_type))
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        print(f"[ERROR] 检查活跃订阅时出错: {str(e)}")
        return False
    finally:
        release_db_connection(conn)

def verify_change_code(email, device_id, equipment_type, change_code):
    """验证解绑验证码"""
    conn = get_db_connection()
    if not conn:
        return {"code": 500, "error_text": "服务器内部错误"}
    
    try:
        with conn.cursor() as cursor:
            # 查找对应的记录
            sql = """SELECT id, change_code 
                     FROM email 
                     WHERE email = %s 
                     AND device_id = %s 
                     AND equipment_type = %s 
                     AND verifi_statu = 1 
                     AND change_device_statu = 0"""
            cursor.execute(sql, (email, device_id, equipment_type))
            result = cursor.fetchone()
            
            if not result:
                return {"code": 418, "error_text": "未找到有效的订阅记录"}
            
            record_id, stored_change_code = result
            
            # 验证解绑验证码是否正确
            if str(stored_change_code) == str(change_code):
                # 更新记录，标记为已解绑
                update_sql = """UPDATE email 
                                SET change_device_statu = 1, updated_time = NOW() 
                                WHERE id = %s"""
                cursor.execute(update_sql, (record_id,))
                return {"code": 200, "change_device_statu": 1}
            else:
                return {"code": 418, "error_text": "解绑验证码错误"}
    except Exception as e:
        print(f"[ERROR] 验证解绑验证码时出错: {str(e)}")
        return {"code": 500, "error_text": "服务器内部错误"}
    finally:
        release_db_connection(conn)

def verify_code(email, code):
    """验证用户输入的验证码"""
    conn = get_db_connection()
    if not conn:
        return {"code": 500, "error_text": "服务器内部错误"}
    
    try:
        with conn.cursor() as cursor:
            # 查找用户所有验证活跃的条目（verifi_end_time在未来的条目）
            sql = """SELECT id, verifi_code, verifi_end_time, verifi_statu 
                     FROM email 
                     WHERE email = %s 
                     AND verifi_end_time > NOW() 
                     AND verifi_statu = 0
                     ORDER BY verifi_end_time DESC"""
            cursor.execute(sql, (email,))
            results = cursor.fetchall()
            
            # 没有验证活跃的条目
            if not results:
                return {"code": 418, "error_text": "验证码过期，请重新生成"}
            
            # 检查验证码是否正确
            for record in results:
                record_id, stored_code, verifi_end_time, verifi_statu = record
                
                # 验证码正确
                if str(stored_code) == str(code):
                    # 再次确认记录仍然在有效期内（防止并发问题）
                    check_sql = """SELECT id FROM email 
                                   WHERE id = %s 
                                   AND verifi_end_time > NOW() 
                                   AND verifi_statu = 0"""
                    cursor.execute(check_sql, (record_id,))
                    active_record = cursor.fetchone()
                    
                    if active_record:
                        # 更新验证状态
                        update_sql = """UPDATE email 
                                        SET verifi_statu = 1, updated_time = NOW() 
                                        WHERE id = %s"""
                        cursor.execute(update_sql, (record_id,))
                        return {"code": 200, "verifi_statu": 1}
                    else:
                        # 记录已过期或被处理
                        return {"code": 418, "error_text": "验证码过期，请重新生成"}
            
            # 所有活跃条目的验证码都不匹配
            return {"code": 418, "error_text": "验证码错误，请重新输入"}
    except Exception as e:
        print(f"[ERROR] 验证验证码时出错: {str(e)}")
        return {"code": 500, "error_text": "服务器内部错误"}
    finally:
        release_db_connection(conn)

def get_device_info(device_id):
    """获取设备信息"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cursor:
            sql = "SELECT equipmentName, installationSite FROM device WHERE id = %s"
            cursor.execute(sql, (str(device_id),))
            result = cursor.fetchone()
            if result:
                return {
                    'equipmentName': result[0],
                    'installationSite': result[1]
                }
            return None
    except Exception as e:
        print(f"[ERROR] 获取设备信息时出错: {str(e)}")
        return None
    finally:
        release_db_connection(conn)

def get_latest_device_data(device_id):
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
                    'total_reading': result[0],
                    'remainingBalance': result[1],
                    'equipmentStatus': result[2],
                    'read_time': result[3]
                }
            return None
    except Exception as e:
        print(f"[ERROR] 获取设备最新数据时出错: {str(e)}")
        return None
    finally:
        release_db_connection(conn)

def check_unsubscribe_request_limit(email, device_id, equipment_type):
    """检查解绑请求时间限制（24小时内不能重复请求）"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            sql = """SELECT id FROM email 
                     WHERE email = %s 
                     AND device_id = %s 
                     AND equipment_type = %s 
                     AND verifi_statu = 1 
                     AND change_device_statu = 0 
                     AND life_end_time > NOW()
                     AND updated_time > DATE_SUB(NOW(), INTERVAL 1 DAY)"""
            cursor.execute(sql, (email, device_id, equipment_type))
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        print(f"[ERROR] 检查解绑请求时间限制时出错: {str(e)}")
        return False
    finally:
        release_db_connection(conn)

def request_unsubscribe(email, device_id, equipment_type):
    """请求解绑，更新updated_time并发送解绑验证码邮件"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # 获取记录信息（包括change_code和设备信息）
            sql = """SELECT e.change_code, d.equipmentName, d.installationSite, d.equipmentType
                     FROM email e
                     LEFT JOIN device d ON e.device_id = d.id
                     WHERE e.email = %s 
                     AND e.device_id = %s 
                     AND e.equipment_type = %s 
                     AND e.verifi_statu = 1 
                     AND e.change_device_statu = 0 
                     AND e.life_end_time > NOW()"""
            cursor.execute(sql, (email, device_id, equipment_type))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            change_code, equipment_name, installation_site, equipment_type_db = result
            
            # 发送解绑验证码邮件
            device_info = {
                'equipmentName': equipment_name,
                'installationSite': installation_site,
                'equipmentType': equipment_type_db
            }
            
            email_sent = send_change_email(email, change_code, device_info)
            if not email_sent:
                print(f"[WARNING] 解绑验证码邮件发送失败，但记录已更新: {email}")
            
            # 更新记录的updated_time为当前时间
            sql = """UPDATE email 
                     SET updated_time = NOW() 
                     WHERE email = %s 
                     AND device_id = %s 
                     AND equipment_type = %s 
                     AND verifi_statu = 1 
                     AND change_device_statu = 0 
                     AND life_end_time > NOW()"""
            cursor.execute(sql, (email, device_id, equipment_type))
            return cursor.rowcount > 0
    except Exception as e:
        print(f"[ERROR] 请求解绑时出错: {str(e)}")
        return False
    finally:
        release_db_connection(conn)

def send_verification_email(email, verifi_code, device_info):
    """发送验证码邮件"""
    import subprocess
    import json
    
    # 检查邮件发送频率限制
    emails_sent_today = count_emails_sent_today(email)
    if emails_sent_today >= EMAIL_DAILY_LIMIT:
        print(f"[WARN] 邮件发送频率超限，邮箱 {email} 今日已发送 {emails_sent_today} 封邮件")
        return False
    
    def _send_email():
        try:
            # 从配置文件读取Aoksend配置
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.dirname(__file__), 'email_api.ini'))
            
            aoksend_config = {
                'api_url': config.get('aoksender', 'server', fallback='https://www.aoksend.com/index/api/send_email'),
                'app_key': config.get('aoksender', 'app_key'),
                'template_id': config.get('aoksender', 'template_id'),
                'reply_to': config.get('aoksender', 'reply_to', fallback=None),
                'alias': config.get('aoksender', 'alias', fallback='新毛云'),
                'attachment': config.get('aoksender', 'attachment', fallback=None),
                'verifi_code_field': config.get('aoksender', 'verifi_code', fallback='code'),
                'verifi_email_statu_field': config.get('aoksender', 'verifi_email_statu', fallback='email_mode')
            }
            
            if not aoksend_config['api_url'] or aoksend_config['api_url'].strip() == '':
                aoksend_config['api_url'] = 'https://www.aoksend.com/index/api/send_email'
            
            # 构造模板数据
            template_data = {
                'email': email,
                aoksend_config['verifi_code_field']: verifi_code,  # 使用配置的字段名
                aoksend_config['verifi_email_statu_field']: '注册',  # 使用配置的字段名发送操作类型
                'device_name': device_info.get('equipmentName', '未知设备') if device_info else '未知设备',
                'device_location': device_info.get('installationSite', '未知位置') if device_info else '未知位置',
                'equipment_type': '电表' if device_info and device_info.get('equipmentType') == 0 else '水表'
            }
            
            # 构建命令行参数
            cmd = [
                sys.executable, 'aoksend-api-cli.py',
                '--api-url', aoksend_config['api_url'],
                '--app-key', aoksend_config['app_key'],
                '--template-id', aoksend_config['template_id'],
                '--to', email
            ]
            
            if aoksend_config['reply_to']:
                cmd.extend(['--reply-to', aoksend_config['reply_to']])
            
            if aoksend_config['alias']:
                cmd.extend(['--alias', aoksend_config['alias']])
            
            cmd.extend(['--data', json.dumps(template_data, ensure_ascii=False)])
            
            if aoksend_config['attachment']:
                cmd.extend(['--attachment', aoksend_config['attachment']])
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                print(f"[INFO] 验证码邮件发送成功到 {email}")
                # 记录邮件发送
                record_email_sent(email)
                return True
            else:
                print(f"[ERROR] 邮件发送失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ERROR] 发送邮件时出错: {str(e)}")
            return False
    
    # 使用线程池并发处理邮件发送
    future = executor.submit(_send_email)
    return future.result()

def send_change_email(email, change_code, device_info):
    """发送解绑验证码邮件"""
    import subprocess
    import json
    
    # 检查邮件发送频率限制
    emails_sent_today = count_emails_sent_today(email)
    if emails_sent_today >= EMAIL_DAILY_LIMIT:
        print(f"[WARN] 邮件发送频率超限，邮箱 {email} 今日已发送 {emails_sent_today} 封邮件")
        return False
    
    def _send_change_email():
        try:
            # 从配置文件读取Aoksend配置
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.dirname(__file__), 'email_api.ini'))
            
            aoksend_config = {
                'api_url': config.get('aoksender', 'server', fallback='https://www.aoksend.com/index/api/send_email'),
                'app_key': config.get('aoksender', 'app_key'),
                'change_template_id': config.get('aoksender', 'change_template_id', fallback=config.get('aoksender', 'template_id')),
                'reply_to': config.get('aoksender', 'reply_to', fallback=None),
                'alias': config.get('aoksender', 'alias', fallback='新毛云'),
                'attachment': config.get('aoksender', 'attachment', fallback=None),
                'change_code_field': config.get('aoksender', 'change_code', fallback='code'),
                'change_email_statu_field': config.get('aoksender', 'change_email_statu', fallback='email_mode')
            }
            
            if not aoksend_config['api_url'] or aoksend_config['api_url'].strip() == '':
                aoksend_config['api_url'] = 'https://www.aoksend.com/index/api/send_email'
            
            # 构造模板数据
            template_data = {
                'email': email,
                aoksend_config['change_code_field']: change_code,  # 使用配置的字段名
                aoksend_config['change_email_statu_field']: '解绑',  # 使用配置的字段名发送操作类型
                'device_name': device_info.get('equipmentName', '未知设备') if device_info else '未知设备',
                'device_location': device_info.get('installationSite', '未知位置') if device_info else '未知位置',
                'equipment_type': '电表' if device_info and device_info.get('equipmentType') == 0 else '水表'
            }
            
            # 构建命令行参数
            cmd = [
                sys.executable, 'aoksend-api-cli.py',
                '--api-url', aoksend_config['api_url'],
                '--app-key', aoksend_config['app_key'],
                '--template-id', aoksend_config['change_template_id'],
                '--to', email
            ]
            
            if aoksend_config['reply_to']:
                cmd.extend(['--reply-to', aoksend_config['reply_to']])
            
            if aoksend_config['alias']:
                cmd.extend(['--alias', aoksend_config['alias']])
            
            cmd.extend(['--data', json.dumps(template_data, ensure_ascii=False)])
            
            if aoksend_config['attachment']:
                cmd.extend(['--attachment', aoksend_config['attachment']])
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                print(f"[INFO] 解绑验证码邮件发送成功到 {email}")
                # 记录邮件发送
                record_email_sent(email)
                return True
            else:
                print(f"[ERROR] 解绑邮件发送失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ERROR] 发送解绑邮件时出错: {str(e)}")
            return False
    
    # 使用线程池并发处理邮件发送
    future = executor.submit(_send_change_email)
    return future.result()


def send_celebration_email(email, device_id, device_info):
    """发送注册庆祝邮件"""
    import subprocess
    import json
    from decimal import Decimal
    
    # 检查邮件发送频率限制
    emails_sent_today = count_emails_sent_today(email)
    if emails_sent_today >= EMAIL_DAILY_LIMIT:
        print(f"[WARN] 邮件发送频率超限，邮箱 {email} 今日已发送 {emails_sent_today} 封邮件")
        return False
    
    def _send_celebration_email():
        try:
            # 获取设备最新数据
            latest_data = get_latest_device_data(device_id)
            if not latest_data:
                print(f"[WARNING] 无法获取设备 {device_id} 的最新数据")
                latest_data = {
                    'total_reading': 'N/A',
                    'remainingBalance': 'N/A',
                    'equipmentStatus': 'N/A',
                    'read_time': 'N/A'
                }
            
            # 从配置文件获取Aoksend配置
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.dirname(__file__), 'email_api.ini'))
            
            aoksend_config = {
                'api_url': config.get('aoksender', 'server', fallback='https://www.aoksend.com/index/api/send_email'),
                'app_key': config.get('aoksender', 'app_key'),
                'celebrate_template_id': config.get('aoksender', 'new_celebrate_template_id', fallback=config.get('aoksender', 'template_id')),
                'reply_to': config.get('aoksender', 'reply_to', fallback=None),
                'alias': config.get('aoksender', 'alias', fallback='新毛云'),
                'attachment': config.get('aoksender', 'attachment', fallback=None),
                'title_field': config.get('aoksender', 'new_celebrate_title', fallback='title'),
                'device_name_field': config.get('aoksender', 'new_celebrate_device_name', fallback='acctName'),
                'device_balance_field': config.get('aoksender', 'new_celebrate_device_balance', fallback='remainingBalance'),
                'device_check_time_field': config.get('aoksender', 'new_celebrate_device_check_time', fallback='currentDealDate'),
                'device_statu_field': config.get('aoksender', 'new_celebrate_device_statu', fallback='equipmentStatus'),
                'device_latest_read_field': config.get('aoksender', 'new_celebrate_device_latest_read', fallback='equipmentLatestLarge')
            }
            
            if not aoksend_config['api_url'] or aoksend_config['api_url'].strip() == '':
                aoksend_config['api_url'] = 'https://www.aoksend.com/index/api/send_email'
            
            # 构造模板数据，处理Decimal类型
            template_data = {
                aoksend_config['title_field']: '恭喜注册成功，现在是你邮箱绑定的设备情况',
                aoksend_config['device_name_field']: device_info.get('equipmentName', '未知设备') if device_info else '未知设备',
                aoksend_config['device_balance_field']: float(latest_data['remainingBalance']) if isinstance(latest_data['remainingBalance'], Decimal) else latest_data['remainingBalance'],
                aoksend_config['device_check_time_field']: str(latest_data['read_time']),
                aoksend_config['device_statu_field']: latest_data['equipmentStatus'],
                aoksend_config['device_latest_read_field']: float(latest_data['total_reading']) if isinstance(latest_data['total_reading'], Decimal) else latest_data['total_reading']
            }
            
            # 构建命令行参数
            cmd = [
                sys.executable, 'aoksend-api-cli.py',
                '--api-url', aoksend_config['api_url'],
                '--app-key', aoksend_config['app_key'],
                '--template-id', aoksend_config['celebrate_template_id'],
                '--to', email
            ]
            
            if aoksend_config['reply_to']:
                cmd.extend(['--reply-to', aoksend_config['reply_to']])
            
            if aoksend_config['alias']:
                cmd.extend(['--alias', aoksend_config['alias']])
            
            cmd.extend(['--data', json.dumps(template_data, ensure_ascii=False, default=str)])
            
            if aoksend_config['attachment']:
                cmd.extend(['--attachment', aoksend_config['attachment']])
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                print(f"[INFO] 注册庆祝邮件发送成功到 {email}")
                # 记录邮件发送
                record_email_sent(email)
                return True
            else:
                print(f"[ERROR] 注册庆祝邮件发送失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ERROR] 发送注册庆祝邮件时出错: {str(e)}")
            return False
    
    # 使用线程池并发处理邮件发送
    future = executor.submit(_send_celebration_email)
    return future.result()

def generate_change_code():
    """生成6位解绑验证码"""
    return random.randint(100000, 999999)

def insert_email_record(email, device_id, equipment_type, alarm_num, ip_address):
    """插入新的邮箱记录并发送验证邮件"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            uuid_value = str(uuid.uuid4())
            verifi_code = generate_verification_code()
            change_code = generate_change_code()
            
            # 计算时间字段
            current_time = datetime.now()
            verifi_end_time = current_time + timedelta(seconds=300)  # 验证码5分钟过期
            life_end_time = current_time + timedelta(days=365)       # 生命周期1年
            
            # 先插入记录，包含所有必要字段
            # 注意：verifi_end_time 和 life_end_time 是生成列，不由INSERT语句指定
            sql = """INSERT INTO email 
                    (email, uuid, device_id, verifi_code, ip_address, alarm_num, equipment_type, change_code) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (email, uuid_value, str(device_id), verifi_code, ip_address, alarm_num, equipment_type, change_code))
            
            # 获取设备信息
            device_info = get_device_info(device_id)
            
            # 发送验证邮件
            email_sent = send_verification_email(email, verifi_code, device_info)
            
            if not email_sent:
                print(f"[WARNING] 邮件发送失败，但记录已插入: {email}")
            
            return True
    except Exception as e:
        print(f"[ERROR] 插入邮箱记录时出错: {str(e)}")
        return False
    finally:
        release_db_connection(conn)

# HTTP请求处理器
class RequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # 处理CORS预检请求
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        # 获取真实客户端IP
        real_ip = get_real_ip(self)
        print(f"[INFO] 收到POST请求 from {real_ip}: {self.path}")
        
        try:
            # 读取请求体
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # 解析JSON数据
            try:
                data = json.loads(post_data)
            except json.JSONDecodeError:
                response_data = {"code": 400, "error_text": "请求数据格式错误"}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                return
            
            # 获取参数
            mode = data.get('mode')
            email = str(data.get('email', '')) if data.get('email') is not None else ''
            equipment_type = int(data.get('equipment_type', -1)) if data.get('equipment_type') is not None else -1
            device_id = str(data.get('device_id', '')) if data.get('device_id') is not None else ''
            
            # 处理alarm_num，确保它是一个大于0的整数
            try:
                alarm_num = int(data.get('alarm_num', 20)) if data.get('alarm_num') is not None else 20
                if alarm_num <= 0:
                    response_data = {"code": 400, "error_text": "预警值必须大于0"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
            except (ValueError, TypeError):
                response_data = {"code": 400, "error_text": "预警值必须是有效的整数"}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                return
            
            # 验证必需参数
            if not mode:
                response_data = {"code": 400, "error_text": "缺少必需参数mode"}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                return
            
            # 处理不同的模式
            if mode == 'reg':
                # 注册模式的处理逻辑
                # ... (现有的注册逻辑)
                
                # 验证邮箱格式
                if not validate_email_format(email):
                    response_data = {"code": 400, "error_text": "邮箱格式不正确"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 验证设备类型
                if equipment_type not in [0, 1]:  # 0为电表，1为水表
                    response_data = {"code": 400, "error_text": "设备类型不正确"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 验证设备是否存在
                device_exists, actual_type = check_device_exists(device_id)
                if not device_exists:
                    response_data = {"code": 403, "error_text": "设备不存在"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 验证设备类型是否匹配
                if actual_type != equipment_type:
                    response_data = {"code": 403, "error_text": "绑定的设备和类型不一致"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 统计邮箱记录数量
                email_count = count_email_records(email)
                if email_count >= EMAIL_LIMIT:
                    response_data = {"code": 418, "error_text": "该账号使用次数超过限制，不予注册"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 统计用户特定设备类型的记录数量
                user_equipment_count = count_active_user_records(email, equipment_type)
                if user_equipment_count < 0:
                    response_data = {"code": 500, "error_text": "服务器内部错误"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                if user_equipment_count == 0:
                    # 插入新记录
                    success = insert_email_record(email, device_id, equipment_type, alarm_num, real_ip)
                    if success:
                        response_data = {
                            "code": 200,
                            "set_client_mode": "wait_user_verifi"
                        }
                    else:
                        response_data = {"code": 500, "error_text": "插入记录失败"}
                else:
                    # 获取用户特定设备类型的验证记录状态
                    verification_records = check_verification_records(email, equipment_type)
                    if verification_records is None:
                        response_data = {"code": 500, "error_text": "服务器内部错误"}
                    else:
                        # 检查验证记录状态 - 按照优先级检查
                        verification_cooling = False  # 验证码冷却期
                        active_subscription = False   # 正常活跃订阅
                        
                        for record in verification_records:
                            verifi_end_time, verifi_statu, life_end_time, change_device_statu = record
                            
                            # 优先级1: 检查是否在验证码冷却期（优先级最高）
                            if verifi_end_time and datetime.now() < verifi_end_time and verifi_statu == 0:
                                verification_cooling = True
                                break  # 冷却期优先级最高，直接返回
                            
                            # 优先级2: 检查是否有正常可用的记录（已通过验证但未到期且未解绑）
                            if life_end_time and datetime.now() < life_end_time and change_device_statu == 0 and verifi_statu == 1:
                                active_subscription = True
                                # 不跳出，继续检查是否有冷却期记录（虽然概率很低）
                        
                        if verification_cooling:
                            response_data = {"code": 418, "error_text": "请等待验证码冷却期过期"}
                        elif active_subscription:
                            response_data = {"code": 418, "error_text": "请解绑当前设备"}
                        else:
                            # 既没有冷却期，也没有活跃订阅，可以插入新记录
                            success = insert_email_record(email, device_id, equipment_type, alarm_num, real_ip)
                            if success:
                                response_data = {
                                    "code": 200,
                                    "set_client_mode": "wait_user_verifi"
                                }
                            else:
                                response_data = {"code": 500, "error_text": "插入记录失败"}
            elif mode == 'enter_code':
                # 验证码输入模式
                email = str(data.get('email', '')) if data.get('email') is not None else ''
                code = str(data.get('code', '')) if data.get('code') is not None else ''
                
                # 验证必需参数
                if not email or not code:
                    response_data = {"code": 400, "error_text": "缺少必需参数"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 验证邮箱格式
                if not validate_email_format(email):
                    response_data = {"code": 400, "error_text": "邮箱格式不正确"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 处理验证码验证逻辑
                response_data = verify_code(email, code)
                
                # 如果验证码验证成功，发送庆祝邮件
                if response_data.get("code") == 200 and response_data.get("verifi_statu") == 1:
                    # 获取用户设备信息用于发送庆祝邮件
                    # 需要根据邮箱查找对应的设备信息
                    conn = get_db_connection()
                    if conn:
                        try:
                            with conn.cursor() as cursor:
                                # 查找用户的设备信息
                                sql = """SELECT e.device_id, d.equipmentName, d.installationSite, d.equipmentType 
                                         FROM email e 
                                         LEFT JOIN device d ON e.device_id = d.id 
                                         WHERE e.email = %s AND e.verifi_statu = 1 
                                         ORDER BY e.created_time DESC LIMIT 1"""
                                cursor.execute(sql, (email,))
                                result = cursor.fetchone()
                                if result:
                                    device_id = result[0]
                                    device_info = {
                                        'equipmentName': result[1],
                                        'installationSite': result[2],
                                        'equipmentType': result[3]
                                    }
                                    # 发送注册庆祝邮件
                                    send_celebration_email(email, device_id, device_info)
                        except Exception as e:
                            print(f"[ERROR] 获取设备信息发送庆祝邮件时出错: {str(e)}")
                        finally:
                            release_db_connection(conn)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                return
            elif mode == 'change_code':
                # 解绑请求模式
                email = str(data.get('email', '')) if data.get('email') is not None else ''
                device_id = str(data.get('device_id', '')) if data.get('device_id') is not None else ''
                try:
                    equipment_type = int(data.get('equipment_type', -1)) if data.get('equipment_type') is not None else -1
                except (ValueError, TypeError):
                    response_data = {"code": 400, "error_text": "设备类型必须是有效的整数"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 验证必需参数
                if not email or not device_id or equipment_type not in [0, 1]:
                    response_data = {"code": 400, "error_text": "缺少必需参数"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 验证邮箱格式
                if not validate_email_format(email):
                    response_data = {"code": 400, "error_text": "邮箱格式不正确"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 检查用户是否有正在使用的订阅
                is_active_sub = check_active_subscription(email, device_id, equipment_type)
                if not is_active_sub:
                    response_data = {"code": 418, "error_text": "未查询到正在订阅预警服务的邮箱账号或设备"}
                else:
                    # 检查是否在24小时内已经请求过解绑
                    if check_unsubscribe_request_limit(email, device_id, equipment_type):
                        response_data = {"code": 418, "error_text": "24小时内已请求过解绑或者刚绑定不到24小时，明天再试吧！"}
                    else:
                        # 请求解绑，更新updated_time
                        request_unsubscribe(email, device_id, equipment_type)
                        response_data = {"code": 200, "set_client_mode": "wait_user_change"}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                return
            elif mode == 'enter_change':
                # 输入解绑验证码模式
                email = str(data.get('email', '')) if data.get('email') is not None else ''
                device_id = str(data.get('device_id', '')) if data.get('device_id') is not None else ''
                try:
                    equipment_type = int(data.get('equipment_type', -1)) if data.get('equipment_type') is not None else -1
                except (ValueError, TypeError):
                    response_data = {"code": 400, "error_text": "设备类型必须是有效的整数"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                change_code = str(data.get('change_code', '')) if data.get('change_code') is not None else ''
                
                # 验证必需参数
                if not email or not device_id or equipment_type not in [0, 1] or not change_code:
                    response_data = {"code": 400, "error_text": "缺少必需参数"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 验证邮箱格式
                if not validate_email_format(email):
                    response_data = {"code": 400, "error_text": "邮箱格式不正确"}
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 验证解绑验证码
                response_data = verify_change_code(email, device_id, equipment_type, change_code)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                return
            else:
                response_data = {"code": 400, "error_text": "未知的模式"}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                return
            
            # 发送响应
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            print(f"[ERROR] 处理请求时出错: {str(e)}")
            traceback.print_exc()
            response_data = {"code": 500, "error_text": "服务器内部错误"}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

def main():
    server = HTTPServer(('', SERVER_PORT), RequestHandler)
    print(f"[INFO] 邮箱API服务器启动，监听端口 {SERVER_PORT}")
    print(f"[INFO] 邮箱限制: {EMAIL_LIMIT}")
    print(f"[INFO] 邮箱每日发送限制: {EMAIL_DAILY_LIMIT}")
    print(f"[INFO] 连接池大小: {CONNECTION_POOL_SIZE}")
    print(f"[INFO] 线程池大小: 10")
    print(f"[INFO] 数据库: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"[INFO] 服务器就绪，等待请求...")
    server.serve_forever()

if __name__ == '__main__':
    main()