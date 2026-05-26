#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_root, '../..', 'server'))

import json
import configparser
import time

from libs.api_client import login as api_login, get_account_list
from libs.aoksender import send_email as aoksend_send_email


def load_aoksend_config():
    config = configparser.ConfigParser()
    config.read('config/aoksender.ini', encoding='utf-8')
    api_url = config.get('aoksender', 'server', fallback='https://www.aoksend.com/index/api/send_email')
    if not api_url or api_url.strip() == '':
        api_url = 'https://www.aoksend.com/index/api/send_email'
    return {
        'api_url': api_url,
        'app_key': config.get('aoksender', 'app_key', fallback=''),
        'template_id': config.get('aoksender', 'template_id', fallback=''),
        'to': config.get('aoksender', 'to', fallback=''),
        'reply_to': config.get('aoksender', 'reply_to', fallback=None),
        'alias': config.get('aoksender', 'alias', fallback='三一工学院水电费监控系统'),
        'data': config.get('aoksender', 'data', fallback=None),
        'attachment': config.get('aoksender', 'attachment', fallback=None),
        'monitor_timer': config.getint('monitor', 'monitor_timer', fallback=3600),
        'monitor_keyword': config.get('monitor', 'monitor_keyword', fallback='remainingBalance'),
        'monitor_start': config.getfloat('monitor', 'monitor_start', fallback=10.0)
    }


def check_threshold(rows, config):
    """返回达到阈值的设备列表"""
    threshold_devices = []
    for row in rows:
        value = row.get(config['monitor_keyword'], float('inf'))
        if isinstance(value, (int, float)) and value <= config['monitor_start']:
            threshold_devices.append(row)
    return threshold_devices


def send_aoksend_mail(config, device_data):
    if not config['app_key'] or not config['template_id'] or not config['to']:
        print("错误: 缺少必要的Aoksend配置参数 (app_key, template_id, to)")
        return False
    result = aoksend_send_email(
        api_url=config['api_url'],
        app_key=config['app_key'],
        template_id=config['template_id'],
        to=config['to'],
        reply_to=config['reply_to'],
        alias=config['alias'],
        data=json.dumps(device_data, ensure_ascii=False),
        attachment=config['attachment'] if os.path.exists(config['attachment']) else None
    )
    print(f"Aoksend API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    if result.get("code") == 200:
        print("邮件发送成功")
        return True
    else:
        print(f"邮件发送失败: {result.get('message', '未知错误')}")
        return False


def main():
    if len(sys.argv) != 3:
        print("用法: ./debug_utils/monitor_aoksender/monitor_aoksender.py <账号> <密码>")
        sys.exit(1)

    phone_num = sys.argv[1]
    password = sys.argv[2]

    print("正在加载Aoksend配置...")
    try:
        aoksend_config = load_aoksend_config()
    except Exception as e:
        print(f"加载Aoksend配置失败: {e}")
        sys.exit(1)

    print(f"Aoksend配置加载成功，检查周期: {aoksend_config['monitor_timer']} 秒")

    while True:
        print("开始检查水电费数据...")

        login_result = api_login(phone_num, password)
        if not login_result or login_result.get('code') != 200:
            print("登录失败")
            print(login_result)
            time.sleep(aoksend_config['monitor_timer'])
            continue

        user = login_result.get('user', {})
        app_user_id = user.get('appUserId')
        role_id = user.get('roleId')

        if not app_user_id or not role_id:
            print("无法获取用户ID或角色ID")
            time.sleep(aoksend_config['monitor_timer'])
            continue

        print(f"登录成功，用户ID: {app_user_id}，角色ID: {role_id}")

        data_result = get_account_list(app_user_id, str(role_id))
        if not data_result or data_result.get('code') != 200:
            print("数据获取失败")
            print(data_result)
            time.sleep(aoksend_config['monitor_timer'])
            continue

        print("数据获取成功")

        rows = data_result.get('rows', [])
        threshold_devices = check_threshold(rows, aoksend_config)
        sent_count = 0

        for device in threshold_devices:
            print(f"检测到设备 '{device.get('acctName', '未知设备')}' 余额低于阈值，准备发送邮件通知...")
            if send_aoksend_mail(aoksend_config, device):
                sent_count += 1

        if sent_count > 0:
            print(f"本轮检查共发送 {sent_count} 封邮件")
        else:
            print("本轮检查未发现需要发送邮件的设备")

        print(f"等待 {aoksend_config['monitor_timer']} 秒后进行下一次检查...")
        time.sleep(aoksend_config['monitor_timer'])


if __name__ == "__main__":
    main()
