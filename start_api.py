#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iwhereGIS 网格数据引擎 HTTP API 启动脚本
"""

import os
import sys
import subprocess
import time

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import flask
        import flask_cors
        import requests
        print("✓ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def start_server():
    """启动API服务器"""
    print("=" * 60)
    print("iwhereGIS 网格数据引擎 HTTP API 服务器")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        return False
    
    print("正在启动API服务器...")
    print("服务器地址: http://localhost:5000")
    print("API文档: http://localhost:5000/api/health")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    try:
        # 启动服务器
        subprocess.run([sys.executable, "api_server.py"])
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        return False
    
    return True

def run_tests():
    """运行API测试"""
    print("运行API测试...")
    try:
        subprocess.run([sys.executable, "test_api.py"])
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_tests()
    else:
        start_server() 