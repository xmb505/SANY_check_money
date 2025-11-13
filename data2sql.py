#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import configparser
import subprocess
import pymysql
from datetime import datetime

def load_mysql_config():
    """加载MySQL配置"""
    config = configparser.ConfigParser()
    config.read('./config/mysql.ini', encoding='utf-8')
    
    return {
        'host': config.get('mysql', 'mysql_server'),
        'port': config.getint('mysql', 'mysql_port'),
        'user': config.get('mysql', 'login_user'),
        'password': config.get('mysql', 'login_passwd'),
        'database': config.get('mysql', 'db_schema')
    }

def get_device_data(app_user_id, role_id, page_num=1, page_size=100):
    """调用check_data.py获取设备数据"""
    try:
        # 调用check_data.py，使用指定的pageNum和pageSize
        result = subprocess.run(
            ['./check_data.py', app_user_id, role_id, str(page_num), str(page_size)],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"调用check_data.py失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"解析JSON数据失败: {e}")
        return None

def connect_database(config):
    """连接数据库"""
    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset='utf8mb4'
        )
        return connection
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def insert_device_data(connection, device_data):
    """插入设备数据到device表"""
    try:
        with connection.cursor() as cursor:
            # 插入或更新设备信息
            sql = """
            INSERT INTO device (id, addr, equipmentName, installationSite, equipmentType, 
                               ratio, rate, acctId, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
            addr=VALUES(addr), equipmentName=VALUES(equipmentName), installationSite=VALUES(installationSite),
            equipmentType=VALUES(equipmentType), ratio=VALUES(ratio), rate=VALUES(rate),
            acctId=VALUES(acctId), status=VALUES(status), updated_at=NOW()
            """
            
            # 批量处理设备数据
            device_values = []
            for item in device_data:
                # 直接从JSON数据中获取设备类型
                equipment_type = int(item.get('equipmentType')) if item.get('equipmentType') is not None else None
                
                # 处理设备状态
                status = None
                if item.get('equipmentStatus') == '开':
                    status = 1
                elif item.get('equipmentStatus') == '关':
                    status = 0
                
                device_values.append((
                    item.get('id'),
                    item.get('addr'),
                    item.get('equipmentName'),
                    item.get('installationSite'),
                    equipment_type,
                    float(item.get('ratio')) if item.get('ratio') else None,
                    float(item.get('rate')) if item.get('rate') else None,
                    item.get('acctId'),
                    status
                ))
            
            if device_values:
                cursor.executemany(sql, device_values)
                connection.commit()
                print(f"成功插入/更新 {len(device_values)} 条设备数据")
            
    except Exception as e:
        print(f"插入设备数据失败: {e}")
        connection.rollback()

def insert_reading_data(connection, device_data):
    """插入读数数据到data表，避免重复插入相同read_time的数据"""
    from datetime import datetime
    
    try:
        with connection.cursor() as cursor:
            # 统计需要插入的数据条数
            new_data_count = 0
            
            for item in device_data:
                device_id = item.get('id')
                read_time = item.get('currentDealDate')
                
                # 检查currentDealDate是否为null，如果是则标记为unStandard并设置为当前时间
                un_standard = 0
                if read_time is None or read_time == '':
                    un_standard = 1
                    read_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 检查是否已存在相同的device_id和read_time记录
                check_sql = "SELECT COUNT(*) FROM data WHERE device_id = %s AND read_time = %s"
                cursor.execute(check_sql, (device_id, read_time))
                count = cursor.fetchone()[0]
                
                # 如果不存在相同记录，则插入新数据
                if count == 0:
                    # 处理设备状态
                    status = None
                    if item.get('equipmentStatus') == '开':
                        status = 1
                    elif item.get('equipmentStatus') == '关':
                        status = 0
                    
                    # 插入读数数据
                    insert_sql = """
                    INSERT INTO data (device_id, read_time, total_reading, remainingBalance, 
                                     equipmentStatus, created_at, unStandard)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    """
                    
                    cursor.execute(insert_sql, (
                        device_id,
                        read_time,
                        float(item.get('equipmentCurrentLarge')) if item.get('equipmentCurrentLarge') else None,
                        float(item.get('remainingBalance')) if item.get('remainingBalance') else None,
                        status,
                        un_standard
                    ))
                    
                    new_data_count += 1
            
            if new_data_count > 0:
                connection.commit()
                print(f"成功插入 {new_data_count} 条新读数数据")
            else:
                print("没有新的读数数据需要插入")
            
    except Exception as e:
        print(f"插入读数数据失败: {e}")
        connection.rollback()

def main():
    # 检查命令行参数
    if len(sys.argv) < 3 or len(sys.argv) > 5:
        print("用法: ./data2sql.py <appUserId> <roleId> [pageNum] [pageSize]")
        sys.exit(1)
    
    # 获取命令行参数
    app_user_id = sys.argv[1]
    role_id = sys.argv[2]
    page_num = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    page_size = int(sys.argv[4]) if len(sys.argv) > 4 else 100  # 默认页面大小改为100
    
    print(f"开始处理数据: appUserId={app_user_id}, roleId={role_id}, pageNum={page_num}, pageSize={page_size}")
    
    # 加载MySQL配置
    try:
        mysql_config = load_mysql_config()
        print("MySQL配置加载成功")
    except Exception as e:
        print(f"加载MySQL配置失败: {e}")
        sys.exit(1)
    
    # 获取设备数据
    result = get_device_data(app_user_id, role_id, page_num, page_size)
    if not result:
        print("调用check_data.py失败，返回结果为空")
        sys.exit(1)
    
    if result.get('code') != 200:
        print(f"获取设备数据失败，错误代码: {result.get('code')}, 错误信息: {result.get('msg')}")
        sys.exit(1)
    
    device_data = result.get('rows', [])
    if not device_data:
        print("没有获取到设备数据")
        sys.exit(1)
    
    print(f"获取到 {len(device_data)} 条设备数据")
    
    # 连接数据库
    connection = connect_database(mysql_config)
    if not connection:
        print("数据库连接失败")
        sys.exit(1)
    
    try:
        # 插入设备数据
        insert_device_data(connection, device_data)
        
        # 插入读数数据
        insert_reading_data(connection, device_data)
        
        print("数据插入完成")
    finally:
        connection.close()

if __name__ == "__main__":
    main()