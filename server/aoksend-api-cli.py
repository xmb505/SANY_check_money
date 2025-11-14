#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import requests
import json
import os
import sys

# Aoksend API默认URL
DEFAULT_API_URL = "https://www.aoksend.com/index/api/send_email"

# 支持的附件文件类型
SUPPORTED_FILE_TYPES = {
    "zip", "rar", "pdf", "jpg", "png", "gif", "mp4", "txt", "doc", "xls", 
    "ppt", "docx", "xlsx", "pptx", "jpeg", "csv"
}

# 返回码对照
RESPONSE_CODES = {
    200: "请求成功",
    40001: "API密钥不能为空",
    40002: "认证失败API密钥错误",
    40003: "模板ID错误",
    40004: "收件人地址to不能为空",
    40005: "收件人地址to格式不正确",
    40006: "默认回复地址reply_to格式不正确",
    40007: "余额不足或账号被禁用",
    40008: "data格式错误",
    40009: "不支持的文件类型或附件大小不能超过1MB"
}

def validate_email(email):
    """简单的邮箱格式验证"""
    return "@" in email and "." in email

def validate_file(file_path):
    """验证文件是否存在且大小不超过1MB"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 检查文件大小 (1MB = 1024 * 1024 bytes)
    file_size = os.path.getsize(file_path)
    if file_size > 1024 * 1024:
        raise ValueError("附件大小不能超过1MB")
    
    # 检查文件类型
    file_extension = os.path.splitext(file_path)[1][1:].lower()
    if file_extension not in SUPPORTED_FILE_TYPES:
        raise ValueError(f"不支持的文件类型: {file_extension}")
    
    return True

def send_email(api_url, app_key, template_id, to, reply_to=None, alias=None, 
               is_random=None, data=None, attachment=None):
    """发送邮件"""
    # 构建请求参数
    payload = {
        'app_key': app_key,
        'template_id': template_id,
        'to': to
    }
    
    # 添加可选参数
    if reply_to:
        payload['reply_to'] = reply_to
    if alias:
        payload['alias'] = alias
    if is_random:
        payload['is_random'] = is_random
    if data:
        payload['data'] = data
    
    try:
        # 如果有附件，使用multipart/form-data方式发送
        if attachment:
            with open(attachment, 'rb') as f:
                files = {'attachment': f}
                response = requests.post(api_url, data=payload, files=files)
        else:
            # 没有附件时使用普通的POST请求
            response = requests.post(api_url, data=payload)
        
        # 解析响应
        result = response.json()
        return result
    except Exception as e:
        return {
            "code": 500,
            "message": f"请求失败: {str(e)}"
        }

def main():
    parser = argparse.ArgumentParser(description='Aoksend邮件发送CLI工具')
    parser.add_argument('--api-url', default=DEFAULT_API_URL, 
                        help='API地址 (默认: https://www.aoksend.com/index/api/send_email)')
    parser.add_argument('--app-key', required=True, help='API密钥')
    parser.add_argument('--template-id', required=True, help='模板ID')
    parser.add_argument('--to', required=True, help='收件人邮箱地址')
    parser.add_argument('--reply-to', help='默认回复地址')
    parser.add_argument('--alias', help='发件人名称')
    parser.add_argument('--is-random', type=int, choices=[0, 1], help='是否随机发送')
    parser.add_argument('--data', help='模板数据(JSON格式)')
    parser.add_argument('--attachment', help='附件文件路径')
    
    args = parser.parse_args()
    
    # 验证必填参数
    if not args.app_key:
        print("错误: API密钥不能为空")
        sys.exit(1)
    
    if not args.template_id:
        print("错误: 模板ID不能为空")
        sys.exit(1)
    
    if not args.to:
        print("错误: 收件人地址不能为空")
        sys.exit(1)
    
    if not validate_email(args.to):
        print("错误: 收件人地址格式不正确")
        sys.exit(1)
    
    if args.reply_to and not validate_email(args.reply_to):
        print("错误: 默认回复地址格式不正确")
        sys.exit(1)
    
    # 验证并处理data参数
    data_json = None
    if args.data:
        try:
            data_json = json.loads(args.data)
        except json.JSONDecodeError:
            print("错误: data参数必须是有效的JSON格式")
            sys.exit(1)
    
    # 验证附件
    if args.attachment:
        try:
            validate_file(args.attachment)
        except (FileNotFoundError, ValueError) as e:
            print(f"错误: {e}")
            sys.exit(1)
    
    # 发送邮件
    result = send_email(
        api_url=args.api_url,
        app_key=args.app_key,
        template_id=args.template_id,
        to=args.to,
        reply_to=args.reply_to,
        alias=args.alias,
        is_random=args.is_random,
        data=json.dumps(data_json) if data_json else None,
        attachment=args.attachment
    )
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 检查返回码
    if result.get("code") != 200:
        message = RESPONSE_CODES.get(result.get("code"), "未知错误")
        print(f"错误: {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()