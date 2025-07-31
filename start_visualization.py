#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iwhereGIS 网格数据引擎可视化启动脚本
"""

import subprocess
import sys
import time
import webbrowser
import os
import signal
import threading

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import flask
        import flask_cors
        print("✓ Flask 依赖检查通过")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def start_api_server():
    """启动API服务器"""
    print("正在启动 iwhereGIS 网格数据引擎 API 服务器...")
    
    # 检查静态文件是否存在
    if not os.path.exists('static/index.html'):
        print("✗ 错误: 找不到 static/index.html 文件")
        return False
    
    try:
        # 启动API服务器
        process = subprocess.Popen([
            sys.executable, 'api_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务器启动
        time.sleep(3)
        
        # 检查服务器是否正常启动
        if process.poll() is None:
            print("✓ API 服务器启动成功")
            print("✓ 服务器地址: http://localhost:5000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"✗ API 服务器启动失败:")
            print(f"错误信息: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"✗ 启动API服务器时出错: {e}")
        return False

def open_browser():
    """打开浏览器访问可视化界面"""
    time.sleep(2)  # 等待服务器完全启动
    try:
        webbrowser.open('http://localhost:5000')
        print("✓ 已打开浏览器访问可视化界面")
    except Exception as e:
        print(f"✗ 无法自动打开浏览器: {e}")
        print("请手动访问: http://localhost:5000")

def main():
    """主函数"""
    print("=" * 50)
    print("iwhereGIS 网格数据引擎可视化系统")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 启动API服务器
    server_process = start_api_server()
    if not server_process:
        return
    
    # 在新线程中打开浏览器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("\n" + "=" * 50)
    print("可视化系统已启动!")
    print("=" * 50)
    print("功能说明:")
    print("1. 在左侧控制面板设置网格参数")
    print("2. 点击'生成网格'按钮创建网格")
    print("3. 点击'航线规划'按钮规划航线")
    print("4. 在3D地图中查看网格和航线")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    try:
        # 保持服务器运行
        while True:
            time.sleep(1)
            if server_process.poll() is not None:
                print("✗ API 服务器意外停止")
                break
                
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        server_process.terminate()
        server_process.wait()
        print("✓ 服务器已停止")

if __name__ == '__main__':
    main() 