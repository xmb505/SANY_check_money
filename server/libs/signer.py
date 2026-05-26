#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server/libs/signer.py

学校 API 签名算法和工具函数。
所有调用学校接口的模块都应从此导入，以确保签名逻辑集中统一。

签名算法（来自学校前端 JS）：
  1. 按参数名字典序排序
  2. 拼接为 KEY=VALUE& 格式（KEY 和 VALUE 均大写）
  3. 末尾追加签名密钥 SIGN_KEY
  4. 整体 MD5 加密得到 sign 值
"""

import hashlib
import time

# 签名密钥（硬编码，不可泄漏）
SIGN_KEY = "DJKSBNW123"

# 学校 API 基础地址
BASE_URL = "http://sywap.funsine.com/prod-api/external"

# 固定请求头
DEFAULT_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0"
}

# 固定渠道 ID
CHANNEL_ID = "1003"


def generate_sign(params: dict) -> dict:
    """
    为参数字典生成签名（直接加到原字典返回）。

    Args:
        params: 请求参数字典

    Returns:
        包含 sign 字段的完整参数字典
    """
    params_copy = params.copy()
    sorted_params = sorted(params_copy.items())
    param_str = "&".join([f"{k.upper()}={str(v).upper()}" for k, v in sorted_params])
    sign_str = param_str + SIGN_KEY
    md5 = hashlib.md5()
    md5.update(sign_str.encode('utf-8'))
    params_copy['sign'] = md5.hexdigest()
    return params_copy


def get_timestamp() -> str:
    """返回当前时间戳字符串，格式 YYYYMMDDHHmmss"""
    return time.strftime("%Y%m%d%H%M%S")


def md5_encrypt(text: str) -> str:
    """对输入文本做 UTF-8 MD5 加密，返回十六进制字符串"""
    md5 = hashlib.md5()
    md5.update(text.encode('utf-8'))
    return md5.hexdigest()