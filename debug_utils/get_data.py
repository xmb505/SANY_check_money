#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_root, '..', 'server'))

import json
from libs.api_client import get_account_list


def main():
    if len(sys.argv) != 3:
        print(json.dumps({"code": -1, "msg": "用法: ./debug_utils/get_data.py <appUserId> <roleId>"}, ensure_ascii=False))
        sys.exit(1)

    app_user_id = sys.argv[1]
    role_id = sys.argv[2]
    result = get_account_list(app_user_id, role_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()