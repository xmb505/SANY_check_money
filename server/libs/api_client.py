#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server/libs/api_client.py

学校 API 调用封装。提供登录、账户查询、设备列表查询等接口。

用法：
    from server.libs.api_client import login, get_account_list, get_device_list

所有函数返回格式均为 API 原始 JSON 响应（dict），网络异常时返回 {"code": -1, "msg": ...}
"""

import requests

from .signer import generate_sign, get_timestamp, md5_encrypt, BASE_URL, DEFAULT_HEADERS, CHANNEL_ID


# ─────────────────────────────────────────────
# API 端点
# ─────────────────────────────────────────────

_LOGIN_URL = f"{BASE_URL}/appUser/login"
_ACCOUNT_LIST_URL = f"{BASE_URL}/appUserAcct/list"
_DEVICE_LIST_URL = f"{BASE_URL}/equipment/list"


# ─────────────────────────────────────────────
# API 函数
# ─────────────────────────────────────────────

def login(phone_num: str, password: str) -> dict:
    """
    用户登录。

    Args:
        phone_num: 手机号
        password: 密码（明文，内部做 MD5 加密）

    Returns:
        API 响应 dict，典型字段：appUserId, roleId, token 等
    """
    params = {
        "phoneNum": phone_num,
        "password": md5_encrypt(password),
        "channelid": CHANNEL_ID,
        "timestamp": get_timestamp()
    }
    signed = generate_sign(params)
    try:
        resp = requests.post(_LOGIN_URL, json=signed, headers=DEFAULT_HEADERS)
        return resp.json()
    except Exception as e:
        return {"code": -1, "msg": f"请求失败: {str(e)}"}


def get_account_list(app_user_id: str, role_id: str) -> dict:
    """
    查询水电费账户列表（每个设备的余额信息）。

    Args:
        app_user_id: 登录返回的 appUserId
        role_id: 登录返回的 roleId

    Returns:
        API 响应 dict，rows 字段含设备余额列表
    """
    params = {
        "appUserId": app_user_id,
        "channelid": CHANNEL_ID,
        "roleId": role_id,
        "timestamp": get_timestamp()
    }
    signed = generate_sign(params)
    try:
        resp = requests.get(_ACCOUNT_LIST_URL, params=signed, headers=DEFAULT_HEADERS)
        return resp.json()
    except Exception as e:
        return {"code": -1, "msg": f"请求失败: {str(e)}"}


def get_device_list(app_user_id: str, role_key: str,
                    page_num: int = 1, page_size: int = 15) -> dict:
    """
    查询设备分页列表（设备完整信息，含电表/水表类型）。

    Args:
        app_user_id: 登录返回的 appUserId
        role_key: 登录返回的 roleId（字段名 roleKey）
        page_num: 页码，默认 1
        page_size: 每页条数，默认 15

    Returns:
        API 响应 dict，含 rows 设备列表
    """
    params = {
        "appUserId": app_user_id,
        "channelid": CHANNEL_ID,
        "pageNum": page_num,
        "pageSize": page_size,
        "roleKey": role_key,
        "timestamp": get_timestamp()
    }
    signed = generate_sign(params)
    try:
        resp = requests.get(_DEVICE_LIST_URL, params=signed, headers=DEFAULT_HEADERS)
        return resp.json()
    except Exception as e:
        return {"code": -1, "msg": f"请求失败: {str(e)}"}