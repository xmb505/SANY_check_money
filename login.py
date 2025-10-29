#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import hashlib
import requests
import time

# 签名密钥
SIGN_KEY = "DJKSBNW123"

def generate_sign(params):
    """
    生成签名
    
    Args:
        params (dict): 请求参数字典
        
    Returns:
        dict: 包含签名的参数字典
    """
    # 复制参数字典，避免修改原始数据
    params_copy = params.copy()
    
    # 按照参数名的字典序排序
    sorted_params = sorted(params_copy.items())
    
    # 拼接参数字符串，格式为 KEY=VALUE&
    param_str = "&".join([f"{k.upper()}={str(v).upper()}" for k, v in sorted_params])
    
    # 添加密钥
    sign_str = param_str + SIGN_KEY
    
    # MD5加密
    md5 = hashlib.md5()
    md5.update(sign_str.encode('utf-8'))
    sign = md5.hexdigest()
    
    # 将签名添加到参数中
    params_copy['sign'] = sign
    
    return params_copy

def get_timestamp():
    """
    获取当前时间戳，格式为YYYYMMDDHHmmss
    
    Returns:
        str: 时间戳字符串
    """
    return time.strftime("%Y%m%d%H%M%S")

def md5_encrypt(text):
    """
    MD5加密
    
    Args:
        text (str): 待加密文本
        
    Returns:
        str: 加密后的MD5值
    """
    md5 = hashlib.md5()
    md5.update(text.encode('utf-8'))
    return md5.hexdigest()

def login(phone_num, password):
    """
    用户登录
    
    Args:
        phone_num (str): 手机号码
        password (str): 密码（明文）
        
    Returns:
        dict: 登录结果
    """
    # 准备登录参数
    login_params = {
        "phoneNum": phone_num,
        "password": md5_encrypt(password),
        "channelid": "1003",
        "timestamp": get_timestamp()
    }
    
    # 生成签名
    signed_params = generate_sign(login_params)
    
    # 设置请求头
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0"
    }
    
    # 发送登录请求
    url = "http://sywap.funsine.com/prod-api/external/appUser/login"
    try:
        response = requests.post(url, json=signed_params, headers=headers)
        return response.json()
    except Exception as e:
        return {"code": -1, "msg": f"请求失败: {str(e)}"}

def main():
    # 检查命令行参数
    if len(sys.argv) != 3:
        print(json.dumps({"code": -1, "msg": "用法: ./login.py <账号> <密码>"}, ensure_ascii=False))
        sys.exit(1)
    
    # 获取命令行参数
    phone_num = sys.argv[1]
    password = sys.argv[2]
    
    # 执行登录
    result = login(phone_num, password)
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()