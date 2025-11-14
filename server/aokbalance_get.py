#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import configparser
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os
import traceback

# 读取配置文件
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'aokbalance_get.ini'))

# 服务器配置
SERVER_PORT = int(config.get('server', 'port'))

# Aoksend配置
API_ADDRESS = config.get('aok', 'api_address')
APP_KEY = config.get('aok', 'app_key')

def get_balance():
    """获取余额信息"""
    try:
        # 准备请求数据
        data = {
            'app_key': APP_KEY
        }
        
        # 发送POST请求
        response = requests.post(API_ADDRESS, data=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"[ERROR] 获取余额时出错: {str(e)}")
        return {"code": 500, "error_text": f"获取余额时出错: {str(e)}"}

# HTTP请求处理器
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"[INFO] 收到GET请求: {self.path}")
        
        try:
            # 解析URL路径
            parsed_path = urlparse(self.path)
            
            # 根据路径处理请求
            if parsed_path.path == '/':
                # 获取余额信息
                balance_data = get_balance()
                
                # 发送响应
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(balance_data, ensure_ascii=False).encode('utf-8'))
            else:
                # 404 Not Found
                response_data = {"code": 404, "error_text": "路径未找到"}
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                
        except Exception as e:
            print(f"[ERROR] 处理请求时出错: {str(e)}")
            traceback.print_exc()
            response_data = {"code": 500, "error_text": "服务器内部错误"}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        # 处理CORS预检请求
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    server = HTTPServer(('', SERVER_PORT), RequestHandler)
    print(f"[INFO] Aoksend余额查询服务器启动，监听端口 {SERVER_PORT}")
    print(f"[INFO] API地址: {API_ADDRESS}")
    print(f"[INFO] 服务器就绪，等待请求...")
    server.serve_forever()

if __name__ == '__main__':
    main()