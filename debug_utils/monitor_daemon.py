#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_root, '..', 'server'))

import json
import configparser
import smtplib
import time
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

from libs.api_client import login as api_login, get_account_list


def load_monitor_config():
    config = configparser.ConfigParser()
    config.read('config/monitor_config.ini', encoding='utf-8')
    return {
        'check_round': config.getint('data', 'check_round'),
        'ele_keyword': config.get('data', 'ele_keyword'),
        'ele_num': config.getfloat('data', 'ele_num'),
        'water_keyword': config.get('data', 'water_keyword'),
        'water_num': config.getfloat('data', 'water_num')
    }


def load_mail_config():
    config = configparser.ConfigParser()
    files_read = config.read('config/mail_setting.ini', encoding='utf-8')
    if not files_read:
        raise FileNotFoundError("无法读取 config/mail_setting.ini")
    if 'smtp' not in config:
        raise ValueError("配置文件中缺少 [smtp] 节点")
    receivers_raw = config.get('smtp', 'receivers')
    receivers = [r.strip() for r in receivers_raw.split(',') if r.strip()]
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


def load_mail_template():
    with open('config/mail_texter.txt', 'r', encoding='utf-8') as f:
        return f.read()


def check_threshold(data, config):
    rows = data.get('rows', [])
    for row in rows:
        acct_name = row.get('acctName', '')
        remaining_balance = row.get('remainingBalance', 0)
        if config['ele_keyword'] in acct_name and remaining_balance <= config['ele_num']:
            return True
        if config['water_keyword'] in acct_name and remaining_balance <= config['water_num']:
            return True
    return False


def format_mail_content(template, data):
    rows = data.get('rows', [])
    device_template = """设备名称：{acctName}
最后更新时间：{currentDealDate}
当前余额：{remainingBalance} 元
设备状态：{equipmentStatus}
"""
    data_content = ""
    for row in rows:
        item_content = device_template
        for key, value in row.items():
            if isinstance(value, (str, int, float)):
                item_content = item_content.replace(f'{{{key}}}', str(value))
        data_content += item_content + '\n'
    template_lines = [line for line in template.split('\n') if not line.strip().startswith('#')]
    clean_template = '\n'.join(template_lines)
    return clean_template.replace('{{DATA_SECTION}}', data_content.strip())


def send_mail(config, subject, content):
    try:
        message = MIMEText(content, 'plain', 'utf-8')
        sender_name = config.get('sender_name', '三一工学院水电费监控系统')
        message['From'] = formataddr((sender_name, config['sender']))
        message['To'] = ', '.join(config['receivers'])
        message['Subject'] = Header(subject, 'utf-8')
        if config.get('encryption', 'ssl').lower() == 'ssl':
            server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
        else:
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
    if len(sys.argv) != 3:
        print("用法: ./debug_utils/monitor_daemon.py <账号> <密码>")
        sys.exit(1)

    phone_num = sys.argv[1]
    password = sys.argv[2]

    print("正在加载监控配置...")
    try:
        monitor_config = load_monitor_config()
    except Exception as e:
        print(f"加载监控配置失败: {e}")
        sys.exit(1)

    print(f"监控配置加载成功，检查周期: {monitor_config['check_round']} 秒")

    while True:
        print("开始检查水电费数据...")

        login_result = api_login(phone_num, password)
        if not login_result or login_result.get('code') != 200:
            print("登录失败")
            print(login_result)
            time.sleep(monitor_config['check_round'])
            continue

        user = login_result.get('user', {})
        app_user_id = user.get('appUserId')
        role_id = user.get('roleId')

        if not app_user_id or not role_id:
            print("无法获取用户ID或角色ID")
            time.sleep(monitor_config['check_round'])
            continue

        print(f"登录成功，用户ID: {app_user_id}，角色ID: {role_id}")

        data_result = get_account_list(app_user_id, str(role_id))
        if not data_result or data_result.get('code') != 200:
            print("数据获取失败")
            print(data_result)
            time.sleep(monitor_config['check_round'])
            continue

        print("数据获取成功")

        if check_threshold(data_result, monitor_config):
            print("检测到余额低于阈值，准备发送邮件通知...")
            try:
                mail_config = load_mail_config()
                mail_template = load_mail_template()
                mail_content = format_mail_content(mail_template, data_result)
                send_mail(mail_config, "三一工学院宿舍水电费信息", mail_content)
            except Exception as e:
                print(f"发送邮件失败: {e}")
        else:
            print("余额正常，无需发送邮件")

        print(f"等待 {monitor_config['check_round']} 秒后进行下一次检查...")
        time.sleep(monitor_config['check_round'])


if __name__ == "__main__":
    main()