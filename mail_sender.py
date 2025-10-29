#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import subprocess
import configparser
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

def load_mail_config():
    """
    加载邮件配置
    
    Returns:
        dict: 邮件配置参数
    """
    try:
        config = configparser.ConfigParser()
        files_read = config.read('mail_setting.ini', encoding='utf-8')
        if not files_read:
            raise FileNotFoundError("无法读取 mail_setting.ini 配置文件，请检查文件是否存在且可访问")
        
        if 'smtp' not in config:
            raise ValueError("配置文件中缺少 [smtp] 节点")
        
        # 处理收件人列表，去除空格
        try:
            receivers_raw = config.get('smtp', 'receivers')
            receivers = [r.strip() for r in receivers_raw.split(',') if r.strip()]
        except configparser.NoOptionError:
            raise ValueError("配置文件中缺少 receivers 配置项")
        
        return {
            'smtp_server': config.get('smtp', 'server'),
            'smtp_port': config.getint('smtp', 'port'),
            'username': config.get('smtp', 'username'),
            'password': config.get('smtp', 'password'),
            'sender': config.get('smtp', 'sender'),
            'sender_name': config.get('smtp', 'sender_name', fallback='三一工学院水电费监控系统'),
            'receivers': receivers,
            'encryption': config.get('smtp', 'encryption', fallback='ssl')
        }
    except Exception as e:
        print(f"加载邮件配置时发生错误: {e}")
        raise

def load_mail_template():
    """
    加载邮件模板
    
    Returns:
        str: 邮件模板内容
    """
    try:
        with open('mail_texter.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError("无法找到邮件模板文件 mail_texter.txt，请检查文件是否存在")
    except Exception as e:
        print(f"加载邮件模板时发生错误: {e}")
        raise

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

def format_mail_content(template, data):
    """
    根据模板和数据生成邮件内容
    
    Args:
        template (str): 邮件模板
        data (dict): 水电费数据
        
    Returns:
        str: 格式化后的邮件内容
    """
    # 提取数据部分
    rows = data.get('rows', [])
    
    # 定义设备信息模板
    device_template = """设备名称：{acctName}
最后更新时间：{currentDealDate}
当前余额：{remainingBalance} 元
设备状态：{equipmentStatus}
"""
    
    # 生成数据部分
    data_content = ""
    for row in rows:
        item_content = device_template
        for key, value in row.items():
            if isinstance(value, (str, int, float)):
                item_content = item_content.replace(f'{{{key}}}', str(value))
        data_content += item_content + '\n'
    
    # 替换模板中的数据部分
    # 移除模板中的注释行
    template_lines = [line for line in template.split('\n') if not line.strip().startswith('#')]
    clean_template = '\n'.join(template_lines)
    
    # 替换数据部分
    final_content = clean_template.replace('{{DATA_SECTION}}', data_content.strip())
    
    return final_content

def send_mail(config, subject, content):
    """
    发送邮件
    
    Args:
        config (dict): 邮件配置
        subject (str): 邮件主题
        content (str): 邮件内容
    """
    try:
        # 创建邮件对象
        message = MIMEText(content, 'plain', 'utf-8')
        sender_name = config.get('sender_name', '三一工学院水电费监控系统')
        message['From'] = formataddr((sender_name, config['sender']))
        message['To'] = ', '.join(config['receivers'])
        message['Subject'] = Header(subject, 'utf-8')
        
        # 连接SMTP服务器并发送邮件
        if config.get('encryption', 'ssl').lower() == 'ssl':
            # SSL加密连接
            server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
        else:
            # TLS加密连接
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
        
        server.login(config['username'], config['password'])
        server.sendmail(config['sender'], config['receivers'], message.as_string())
        server.quit()
        
        print("邮件发送成功")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

def main():
    # 检查命令行参数
    if len(sys.argv) != 3:
        print("用法: ./mail_sender.py <账号> <密码>")
        sys.exit(1)
    
    # 获取命令行参数
    phone_num = sys.argv[1]
    password = sys.argv[2]
    
    # 调用登录脚本
    print("正在登录...")
    login_result = call_login_script(phone_num, password)
    
    if not login_result or login_result.get('code') != 200:
        print("登录失败")
        print(login_result)
        sys.exit(1)
    
    # 提取用户信息
    user = login_result.get('user', {})
    app_user_id = user.get('appUserId')
    role_id = user.get('roleId')
    
    if not app_user_id or not role_id:
        print("无法获取用户ID或角色ID")
        sys.exit(1)
    
    print(f"登录成功，用户ID: {app_user_id}，角色ID: {role_id}")
    
    # 调用数据获取脚本
    print("正在获取水电费数据...")
    data_result = call_get_data_script(app_user_id, role_id)
    
    if not data_result or data_result.get('code') != 200:
        print("数据获取失败")
        print(data_result)
        sys.exit(1)
    
    print("数据获取成功")
    
    # 加载邮件配置和模板
    print("正在加载邮件配置和模板...")
    try:
        mail_config = load_mail_config()
        mail_template = load_mail_template()
    except Exception as e:
        print(f"加载邮件配置或模板失败: {e}")
        sys.exit(1)
    
    # 格式化邮件内容
    print("正在格式化邮件内容...")
    mail_content = format_mail_content(mail_template, data_result)
    mail_subject = "三一工学院宿舍水电费信息"
    
    # 发送邮件
    print("正在发送邮件...")
    if send_mail(mail_config, mail_subject, mail_content):
        print("邮件已成功发送")
    else:
        print("邮件发送失败")
        sys.exit(1)

if __name__ == "__main__":
    main()