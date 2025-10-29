#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import subprocess
import configparser
import time

def load_monitor_config():
    """
    加载监控配置
    
    Returns:
        dict: 监控配置参数
    """
    config = configparser.ConfigParser()
    config.read('monitor_config.ini', encoding='utf-8')
    
    return {
        'check_round': config.getint('data', 'check_round'),
        'ele_keyword': config.get('data', 'ele_keyword'),
        'ele_num': config.getfloat('data', 'ele_num'),
        'water_keyword': config.get('data', 'water_keyword'),
        'water_num': config.getfloat('data', 'water_num')
    }

def call_login_script(phone_num, password):
    """
    调用登录脚本获取用户信息
    
    Args:
        phone_num (str): 手机号码
        password (str): 密码
        
    Returns:
        dict: 登录结果
    """
    try:
        result = subprocess.run(
            [sys.executable, 'login.py', phone_num, password],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"登录脚本执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"解析登录结果失败: {e}")
        return None

def call_get_data_script(app_user_id, role_id):
    """
    调用数据获取脚本获取水电费信息
    
    Args:
        app_user_id (str): 用户ID
        role_id (str): 角色ID
        
    Returns:
        dict: 水电费数据
    """
    try:
        result = subprocess.run(
            [sys.executable, 'get_data.py', app_user_id, str(role_id)],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"数据获取脚本执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"解析数据结果失败: {e}")
        return None

def check_threshold(data, config):
    """
    检查数据是否达到阈值
    
    Args:
        data (dict): 水电费数据
        config (dict): 监控配置
        
    Returns:
        bool: 是否达到阈值
    """
    rows = data.get('rows', [])
    
    for row in rows:
        acct_name = row.get('acctName', '')
        remaining_balance = row.get('remainingBalance', 0)
        
        # 检查是否为电表且余额低于阈值
        if config['ele_keyword'] in acct_name and remaining_balance <= config['ele_num']:
            return True
            
        # 检查是否为水表且余额低于阈值
        if config['water_keyword'] in acct_name and remaining_balance <= config['water_num']:
            return True
    
    return False

def call_mail_sender(phone_num, password):
    """
    调用邮件发送脚本
    
    Args:
        phone_num (str): 手机号码
        password (str): 密码
    """
    try:
        result = subprocess.run(
            [sys.executable, 'mail_sender.py', phone_num, password],
            capture_output=True,
            text=True,
            check=True
        )
        print("邮件发送脚本执行成功")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"邮件发送脚本执行失败: {e}")
        print(f"返回码: {e.returncode}")
        if e.stdout:
            print(f"标准输出: {e.stdout}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        # 如果没有错误输出，尝试获取更多详细信息
        if not e.stderr and not e.stdout:
            print("没有捕获到详细的错误信息，尝试直接运行查看错误详情...")
            # 再次运行但不捕获输出，让错误直接显示到控制台
            try:
                subprocess.run([sys.executable, 'mail_sender.py', phone_num, password])
            except Exception as inner_e:
                print(f"再次尝试时发生错误: {inner_e}")

def main():
    # 检查命令行参数
    if len(sys.argv) != 3:
        print("用法: ./monitor_daemon.py <账号> <密码>")
        sys.exit(1)
    
    # 获取命令行参数
    phone_num = sys.argv[1]
    password = sys.argv[2]
    
    # 加载监控配置
    print("正在加载监控配置...")
    try:
        monitor_config = load_monitor_config()
    except Exception as e:
        print(f"加载监控配置失败: {e}")
        sys.exit(1)
    
    print(f"监控配置加载成功，检查周期: {monitor_config['check_round']} 秒")
    
    while True:
        print("开始检查水电费数据...")
        
        # 调用登录脚本
        print("正在登录...")
        login_result = call_login_script(phone_num, password)
        
        if not login_result or login_result.get('code') != 200:
            print("登录失败")
            print(login_result)
            time.sleep(monitor_config['check_round'])
            continue
        
        # 提取用户信息
        user = login_result.get('user', {})
        app_user_id = user.get('appUserId')
        role_id = user.get('roleId')
        
        if not app_user_id or not role_id:
            print("无法获取用户ID或角色ID")
            time.sleep(monitor_config['check_round'])
            continue
        
        print(f"登录成功，用户ID: {app_user_id}，角色ID: {role_id}")
        
        # 调用数据获取脚本
        print("正在获取水电费数据...")
        data_result = call_get_data_script(app_user_id, role_id)
        
        if not data_result or data_result.get('code') != 200:
            print("数据获取失败")
            print(data_result)
            time.sleep(monitor_config['check_round'])
            continue
        
        print("数据获取成功")
        
        # 检查是否达到阈值
        if check_threshold(data_result, monitor_config):
            print("检测到余额低于阈值，准备发送邮件通知...")
            # 如果达到阈值，调用邮件发送脚本
            call_mail_sender(phone_num, password)
        else:
            print("余额正常，无需发送邮件")
        
        # 等待下一个检查周期
        print(f"等待 {monitor_config['check_round']} 秒后进行下一次检查...")
        time.sleep(monitor_config['check_round'])

if __name__ == "__main__":
    main()