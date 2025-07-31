#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iwhereGIS 网格数据引擎可视化系统演示脚本
"""

import requests
import json
import time
import webbrowser
import subprocess
import sys
import os

def check_api_server():
    """检查API服务器是否运行"""
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def start_api_server():
    """启动API服务器"""
    print("正在启动API服务器...")
    try:
        process = subprocess.Popen([
            sys.executable, 'api_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务器启动
        for i in range(10):
            time.sleep(1)
            if check_api_server():
                print("✓ API服务器启动成功")
                return process
            print(f"等待服务器启动... ({i+1}/10)")
        
        print("✗ API服务器启动超时")
        return None
        
    except Exception as e:
        print(f"✗ 启动API服务器失败: {e}")
        return None

def demo_grid_generation():
    """演示网格生成功能"""
    print("\n=== 网格生成演示 ===")
    
    # 生成网格数据
    data = {
        "lon_min": 114.0,
        "lon_max": 114.01,
        "lat_min": 22.5,
        "lat_max": 22.51,
        "level": 8,
        "alt_min": 0,
        "alt_max": 1000
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/grids/generate',
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 成功生成 {result['data']['count']} 个网格")
            return result['data']['grids']
        else:
            print(f"✗ 网格生成失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"✗ 网格生成错误: {e}")
        return None

def demo_route_planning():
    """演示航线规划功能"""
    print("\n=== 航线规划演示 ===")
    
    # 航线数据
    data = {
        "waypoints": [
            [114.05, 22.55, 100],
            [114.08, 22.58, 150]
        ],
        "level": 8
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/grids/route',
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 航线规划成功，经过 {result['data']['count']} 个网格")
            return result['data']['grid_codes']
        else:
            print(f"✗ 航线规划失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"✗ 航线规划错误: {e}")
        return None

def demo_statistics():
    """演示统计信息功能"""
    print("\n=== 统计信息演示 ===")
    
    try:
        response = requests.get(
            'http://localhost:5000/api/statistics',
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            stats = result['data']
            print(f"✓ 统计信息获取成功")
            print(f"  总网格数: {stats.get('total_grids', 0)}")
            print(f"  已使用网格: {stats.get('used_grids', 0)}")
            print(f"  属性数量: {stats.get('attribute_count', 0)}")
            return True
        else:
            print(f"✗ 统计信息获取失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ 统计信息错误: {e}")
        return False

def open_visualization():
    """打开可视化界面"""
    print("\n=== 打开可视化界面 ===")
    try:
        webbrowser.open('http://localhost:5000')
        print("✓ 已打开浏览器访问可视化界面")
        print("请在浏览器中:")
        print("1. 设置网格参数")
        print("2. 点击'生成网格'按钮")
        print("3. 点击'航线规划'按钮")
        print("4. 在3D地图中查看结果")
        return True
    except Exception as e:
        print(f"✗ 无法打开浏览器: {e}")
        print("请手动访问: http://localhost:5000")
        return False

def main():
    """主演示函数"""
    print("=" * 60)
    print("iwhereGIS 网格数据引擎可视化系统演示")
    print("=" * 60)
    
    # 检查API服务器
    if not check_api_server():
        print("API服务器未运行，正在启动...")
        server_process = start_api_server()
        if not server_process:
            print("无法启动API服务器，演示终止")
            return
    else:
        print("✓ API服务器已运行")
        server_process = None
    
    # 演示功能
    print("\n开始功能演示...")
    
    # 1. 网格生成演示
    grids = demo_grid_generation()
    
    # 2. 航线规划演示
    route_grids = demo_route_planning()
    
    # 3. 统计信息演示
    demo_statistics()
    
    # 4. 打开可视化界面
    open_visualization()
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)
    print("可视化系统功能:")
    print("✓ 3D网格显示")
    print("✓ 实时网格生成")
    print("✓ 航线可视化")
    print("✓ 交互式操作")
    print("✓ 统计信息显示")
    print("\n请在浏览器中体验完整的可视化功能")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    try:
        # 保持服务器运行
        while True:
            time.sleep(1)
            if server_process and server_process.poll() is not None:
                print("API服务器意外停止")
                break
                
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        if server_process:
            server_process.terminate()
            server_process.wait()
        print("✓ 服务器已停止")

if __name__ == '__main__':
    main() 