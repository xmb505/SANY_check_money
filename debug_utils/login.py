#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加 server/ 到模块搜索路径，使 libs.* 成为顶层包
_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_root, '..', 'server'))

import json
from libs.api_client import login as api_login


def main():
    if len(sys.argv) != 3:
        print(json.dumps({"code": -1, "msg": "用法: ./debug_utils/login.py <账号> <密码>"}, ensure_ascii=False))
        sys.exit(1)

    phone_num = sys.argv[1]
    password = sys.argv[2]
    result = api_login(phone_num, password)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()