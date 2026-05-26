#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import subprocess
import configparser
import time
import requests
import os

def load_aoksend_config():
    """
    加载Aoksend邮件配置
    
    Returns:
        dict: Aoksend邮件配置参数
    """
    config = configparser.ConfigParser()
    config.read('config/aoksender.ini', encoding='utf-8')
    
    # 获取基本配置，只在必要时提供默认值
    api_url = config.get('aoksender', 'server', fallback='https://www.aoksend.com/index/api/send_email')
    if not api_url or api_url.strip() == '':
        api_url = 'https://www.aoksend.com/index/api/send_email'
    
    app_key = config.get('aoksender', 'app_key', fallback='')
    template_id = config.get('aoksender', 'template_id', fallback='')
    to = config.get('aoksender', 'to', fallback='')
    
    return {
        'api_url': api_url,
        'app_key': app_key,
        'template_id': template_id,
        'to': to,
        'reply_to': config.get('aoksender', 'reply_to', fallback=None),
        'alias': config.get('aoksender', 'alias', fallback='三一工学院水电费监控系统'),
        'data': config.get('aoksender', 'data', fallback=None),
        'attachment': config.get('aoksender', 'attachment', fallback=None),
        'monitor_timer': config.getint('monitor', 'monitor_timer', fallback=3600),
        'monitor_keyword': config.get('monitor', 'monitor_keyword', fallback='remainingBalance'),
        'monitor_start': config.getfloat('monitor', 'monitor_start', fallback=10.0)
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
        list: 达到阈值的设备列表
    """
    rows = data.get('rows', [])
    threshold_devices = []
    
    for row in rows:
        # 检查是否为监控关键词对应的值且低于阈值
        value = row.get(config['monitor_keyword'], float('inf'))
        if isinstance(value, (int, float)) and value <= config['monitor_start']:
            threshold_devices.append(row)
    
    return threshold_devices

def send_aoksend_mail(config, device_data):
    """
    使用Aoksend API发送邮件
    
    Args:
        config (dict): Aoksend配置
        device_data (dict): 触发条件的单个设备数据
    """
    # 检查必需参数
    if not config['app_key'] or not config['template_id'] or not config['to']:
        print("错误: 缺少必要的Aoksend配置参数 (app_key, template_id, to)")
        return False
    
    # 构建请求参数
    payload = {
        'app_key': config['app_key'],
        'template_id': config['template_id'],
        'to': config['to']
    }
    
    # 添加可选参数
    if config['reply_to']:
        payload['reply_to'] = config['reply_to']
    if config['alias']:
        payload['alias'] = config['alias']
    
    # 直接将单个设备的完整JSON数据作为模板数据发送
    template_data = device_data
    payload['data'] = json.dumps(template_data, ensure_ascii=False)
    
    try:
        # 如果有附件，使用multipart/form-data方式发送
        if config['attachment'] and os.path.exists(config['attachment']):
            with open(config['attachment'], 'rb') as f:
                files = {'attachment': f}
                response = requests.post(config['api_url'], data=payload, files=files)
        else:
            # 没有附件时使用普通的POST请求
            response = requests.post(config['api_url'], data=payload)
        
        # 解析响应
        result = response.json()
        print(f"Aoksend API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get("code") == 200:
            print("邮件发送成功")
            return True
        else:
            print(f"邮件发送失败: {result.get('message', '未知错误')}")
            return False
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return False

def main():
    # 检查命令行参数
    if len(sys.argv) != 3:
        print("用法: ./monitor_aoksender.py <账号> <密码>")
        sys.exit(1)
    
    # 获取命令行参数
    phone_num = sys.argv[1]
    password = sys.argv[2]
    
    # 加载Aoksend配置
    print("正在加载Aoksend配置...")
    try:
        aoksend_config = load_aoksend_config()
    except Exception as e:
        print(f"加载Aoksend配置失败: {e}")
        sys.exit(1)
    
    print(f"Aoksend配置加载成功，检查周期: {aoksend_config['monitor_timer']} 秒")
    
    while True:
        print("开始检查水电费数据...")
        
        # 调用登录脚本
        print("正在登录...")
        login_result = call_login_script(phone_num, password)
        
        if not login_result or login_result.get('code') != 200:
            print("登录失败")
            print(login_result)
            time.sleep(aoksend_config['monitor_timer'])
            continue
        
        # 提取用户信息
        user = login_result.get('user', {})
        app_user_id = user.get('appUserId')
        role_id = user.get('roleId')
        
        if not app_user_id or not role_id:
            print("无法获取用户ID或角色ID")
            time.sleep(aoksend_config['monitor_timer'])
            continue
        
        print(f"登录成功，用户ID: {app_user_id}，角色ID: {role_id}")
        
        # 调用数据获取脚本
        print("正在获取水电费数据...")
        data_result = call_get_data_script(app_user_id, role_id)
        
        if not data_result or data_result.get('code') != 200:
            print("数据获取失败")
            print(data_result)
            time.sleep(aoksend_config['monitor_timer'])
            continue
        
        print("数据获取成功")
        
        # 逐个检查设备是否达到阈值
        rows = data_result.get('rows', [])
        sent_count = 0
        
        for device in rows:
            # 检查当前设备是否达到阈值
            value = device.get(aoksend_config['monitor_keyword'], float('inf'))
            if isinstance(value, (int, float)) and value <= aoksend_config['monitor_start']:
                print(f"检测到设备 '{device.get('acctName', '未知设备')}' 余额低于阈值，准备发送邮件通知...")
                # 如果达到阈值，使用Aoksend API发送邮件
                if send_aoksend_mail(aoksend_config, device):
                    sent_count += 1
            else:
                print(f"设备 '{device.get('acctName', '未知设备')}' 余额正常，无需发送邮件")
        
        if sent_count > 0:
            print(f"本轮检查共发送 {sent_count} 封邮件")
        else:
            print("本轮检查未发现需要发送邮件的设备")
        
        # 等待下一个检查周期
        print(f"等待 {aoksend_config['monitor_timer']} 秒后进行下一次检查...")
        time.sleep(aoksend_config['monitor_timer'])

if __name__ == "__main__":
    main()