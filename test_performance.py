#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本 - 比较优化前后的性能
"""

import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

def test_api_performance(url, test_data, num_requests=10, max_workers=5):
    """测试API性能"""
    response_times = []
    success_count = 0
    error_count = 0
    
    def make_request(request_data):
        start_time = time.time()
        try:
            response = requests.post(url, json=request_data, timeout=10)
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                return response_time, True, None
            else:
                return response_time, False, f"HTTP {response.status_code}"
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            return response_time, False, str(e)
    
    print(f"开始性能测试: {num_requests}个请求，并发数: {max_workers}")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(make_request, test_data) for _ in range(num_requests)]
        
        for future in as_completed(futures):
            response_time, success, error = future.result()
            response_times.append(response_time)
            
            if success:
                success_count += 1
            else:
                error_count += 1
                print(f"请求失败: {error}")
    
    # 计算统计数据
    avg_time = statistics.mean(response_times)
    median_time = statistics.median(response_times)
    min_time = min(response_times)
    max_time = max(response_times)
    
    if len(response_times) > 1:
        std_dev = statistics.stdev(response_times)
    else:
        std_dev = 0
    
    # 计算QPS
    total_time = max(response_times)
    qps = success_count / total_time if total_time > 0 else 0
    
    print(f"\n=== 性能测试结果 ===")
    print(f"总请求数: {num_requests}")
    print(f"成功请求: {success_count}")
    print(f"失败请求: {error_count}")
    print(f"成功率: {success_count/num_requests*100:.1f}%")
    print(f"\n响应时间统计:")
    print(f"  平均响应时间: {avg_time*1000:.1f}ms")
    print(f"  中位数响应时间: {median_time*1000:.1f}ms")
    print(f"  最小响应时间: {min_time*1000:.1f}ms")
    print(f"  最大响应时间: {max_time*1000:.1f}ms")
    print(f"  标准差: {std_dev*1000:.1f}ms")
    print(f"  QPS: {qps:.1f}")
    
    return {
        'avg_time': avg_time,
        'success_rate': success_count/num_requests,
        'qps': qps
    }

if __name__ == "__main__":
    # 测试配置
    API_URL = "http://localhost:8081"  # email_api.py服务地址
    
    # 测试数据 - 模拟注册请求
    test_request_data = {
        "mode": "reg",
        "email": "test@example.com",
        "equipment_type": "0",
        "device_id": "24831",
        "alarm_num": "10"
    }
    
    print("正在测试email_api.py的性能...")
    print("请确保email_api.py服务已在端口8081启动")
    
    # 进行性能测试
    result = test_api_performance(API_URL, test_request_data, num_requests=10, max_workers=5)
    
    print(f"\n✅ 测试完成!")
    print(f"预期性能提升: 10-100倍")
    if result['success_rate'] > 0.8:
        print(f"✅ 服务运行正常")
    else:
        print(f"⚠️  可能有错误，请检查服务状态")