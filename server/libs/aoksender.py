#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server/libs/aoksender.py

Aoksend 邮件发送客户端。提供纯函数式调用和 CLI 入口两种使用方式。

用法（函数调用）:
    from server.libs.aoksender import send_email, check_balance, validate_email

    result = send_email(
        api_url="https://...",
        app_key="xxx",
        template_id="xxx",
        to="user@example.com",
        data={"name": "张三"}
    )

用法（CLI）:
    python3 -m server.libs.aoksender --app-key KEY --template-id TID --to user@example.com
"""

import json
import os
import sys

import requests

# 默认 API 地址
DEFAULT_API_URL = "https://www.aoksend.com/index/api/send_email"

# 余额查询 API 地址
BALANCE_API_URL = "https://www.aoksend.com/index/api/check_account"

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


def validate_email(email: str) -> bool:
    """简单的邮箱格式验证"""
    return "@" in email and "." in email


def validate_file(file_path: str) -> bool:
    """
    验证文件是否存在、类型合法、大小不超过 1MB。

    Raises:
        FileNotFoundError / ValueError
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    if os.path.getsize(file_path) > 1024 * 1024:
        raise ValueError("附件大小不能超过1MB")
    ext = os.path.splitext(file_path)[1][1:].lower()
    if ext not in SUPPORTED_FILE_TYPES:
        raise ValueError(f"不支持的文件类型: {ext}")
    return True


def send_email(api_url: str, app_key: str, template_id: str, to: str,
               reply_to: str = None, alias: str = None,
               is_random: int = None, data: str = None,
               attachment: str = None) -> dict:
    """
    发送邮件。

    Args:
        api_url: Aoksend API 地址
        app_key: API 密钥
        template_id: 模板 ID
        to: 收件人邮箱
        reply_to: 默认回复地址（可选）
        alias: 发件人别名（可选）
        is_random: 是否随机发送 0/1（可选）
        data: 模板数据 JSON 字符串（可选）
        attachment: 附件文件路径（可选）

    Returns:
        API 响应 dict
    """
    payload = {'app_key': app_key, 'template_id': template_id, 'to': to}
    if reply_to:
        payload['reply_to'] = reply_to
    if alias:
        payload['alias'] = alias
    if is_random is not None:
        payload['is_random'] = is_random
    if data:
        payload['data'] = data

    try:
        if attachment:
            with open(attachment, 'rb') as f:
                files = {'attachment': f}
                resp = requests.post(api_url, data=payload, files=files)
        else:
            resp = requests.post(api_url, data=payload)
        return resp.json()
    except Exception as e:
        return {"code": 500, "message": f"请求失败: {str(e)}"}


def check_balance(app_key: str, api_url: str = BALANCE_API_URL) -> dict:
    """
    查询 Aoksend 账户剩余邮件额度。

    Args:
        app_key: API 密钥
        api_url: 查询 API 地址

    Returns:
        API 响应 dict，含 code/account 等字段
    """
    try:
        resp = requests.post(api_url, data={'app_key': app_key})
        return resp.json()
    except Exception as e:
        return {"code": 500, "message": f"请求失败: {str(e)}"}


# ─────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Aoksend邮件发送CLI工具')
    parser.add_argument('--api-url', default=DEFAULT_API_URL)
    parser.add_argument('--app-key', required=True)
    parser.add_argument('--template-id', required=True)
    parser.add_argument('--to', required=True)
    parser.add_argument('--reply-to')
    parser.add_argument('--alias')
    parser.add_argument('--is-random', type=int, choices=[0, 1])
    parser.add_argument('--data')
    parser.add_argument('--attachment')

    args = parser.parse_args()

    if not validate_email(args.to):
        print("错误: 收件人地址格式不正确")
        sys.exit(1)
    if args.reply_to and not validate_email(args.reply_to):
        print("错误: 默认回复地址格式不正确")
        sys.exit(1)

    data_json = None
    if args.data:
        try:
            data_json = json.loads(args.data)
        except json.JSONDecodeError:
            print("错误: data参数必须是有效的JSON格式")
            sys.exit(1)

    if args.attachment:
        try:
            validate_file(args.attachment)
        except (FileNotFoundError, ValueError) as e:
            print(f"错误: {e}")
            sys.exit(1)

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

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("code") != 200:
        msg = RESPONSE_CODES.get(result.get("code"), "未知错误")
        print(f"错误: {msg}")
        sys.exit(1)