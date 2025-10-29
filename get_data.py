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
    生成签名，模拟JavaScript中的签名生成过程
    
    Args:
        params (dict): 请求参数字典
        
    Returns:
        dict: 包含签名的参数字典
    """
    # 创建新的参数字典
    n = {}
    t = ""
    
    # 按照参数名的字典序排序
    sorted_keys = sorted(params.keys())
    
    # 模拟JavaScript中的map函数
    for key in sorted_keys:
        # 将参数值转为字符串
        n[key] = str(params[key])
        # 拼接参数字符串
        t += "{}={}&".format(key.upper(), n[key].upper())
    
    # 添加密钥
    a = t + SIGN_KEY
    
    # MD5加密
    md5 = hashlib.md5()
    md5.update(a.encode('utf-8'))
    sign = md5.hexdigest()
    
    # 将签名添加到参数中
    n['sign'] = sign
    
    return n

def get_utility_data(app_user_id, role_id):
    """
    获取水电费数据
    
    Args:
        app_user_id (str): 用户ID
        role_id (str): 角色ID
        
    Returns:
        dict: 水电费数据
    """
    # 获取当前时间戳
    timestamp = time.strftime("%Y%m%d%H%M%S")
    
    # 准备查询参数
    query_params = {
        "appUserId": app_user_id,
        "channelid": "1003",  # 硬编码的渠道ID
        "roleId": role_id,
        "timestamp": timestamp
    }
    
    # 生成签名
    signed_params = generate_sign(query_params)
    
    # 设置请求头
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0"
    }
    
    # 发送查询请求
    url = "http://sywap.funsine.com/prod-api/external/appUserAcct/list"
    try:
        response = requests.get(url, params=signed_params, headers=headers)
        return response.json()
    except Exception as e:
        return {"code": -1, "msg": f"请求失败: {str(e)}"}

def main():
    # 检查命令行参数
    if len(sys.argv) != 3:
        print(json.dumps({"code": -1, "msg": "用法: ./get_data.py <appUserId> <roleId>"}, ensure_ascii=False))
        sys.exit(1)
    
    # 获取命令行参数
    app_user_id = sys.argv[1]
    role_id = sys.argv[2]
    
    # 执行查询
    result = get_utility_data(app_user_id, role_id)
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()