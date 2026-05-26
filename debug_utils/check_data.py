#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_root, '..', 'server'))

import json
from libs.api_client import get_device_list


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 5:
        print(json.dumps({"code": -1, "msg": "用法: ./debug_utils/check_data.py <appUserId> <roleId> [pageNum] [pageSize]"}, ensure_ascii=False))
        sys.exit(1)

    app_user_id = sys.argv[1]
    role_key = sys.argv[2]
    page_num = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    page_size = int(sys.argv[4]) if len(sys.argv) > 4 else 15
    result = get_device_list(app_user_id, role_key, page_num, page_size)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()