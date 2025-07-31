#!/usr/bin/env python3
import requests
import json

def test_api():
    base_url = "http://localhost:5000"
    
    print("iwhereGIS API 测试开始...")
    
    # 1. 健康检查
    print("1. 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 2. 生成网格
    print("\n2. 测试网格生成...")
    try:
        data = {
            "lon_min": 114.0,
            "lon_max": 114.001,
            "lat_min": 22.5,
            "lat_max": 22.501,
            "level": 8
        }
        response = requests.post(f"{base_url}/api/grids/generate", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"生成网格数: {result.get('data', {}).get('count', 0)}")
        
        # 获取网格编码用于后续测试
        grid_code = result.get('data', {}).get('grids', [{}])[0].get('code')
        
    except Exception as e:
        print(f"错误: {e}")
        grid_code = None
    
    # 3. 查询网格
    if grid_code:
        print(f"\n3. 测试网格查询: {grid_code}")
        try:
            response = requests.get(f"{base_url}/api/grids/{grid_code}")
            print(f"状态码: {response.status_code}")
        except Exception as e:
            print(f"错误: {e}")
    
    # 4. 坐标编码
    print("\n4. 测试坐标编码...")
    try:
        data = {
            "lon": 114.1234,
            "lat": 22.5678,
            "alt": 100,
            "level": 8
        }
        response = requests.post(f"{base_url}/api/grids/encode", json=data)
        print(f"状态码: {response.status_code}")
        print(f"网格编码: {response.json().get('data', {}).get('grid_code')}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 5. 更新属性
    if grid_code:
        print(f"\n5. 测试属性更新: {grid_code}")
        try:
            data = {
                "category": "flight_rules",
                "key": "max_altitude",
                "value": 300
            }
            response = requests.put(f"{base_url}/api/grids/{grid_code}/attributes", json=data)
            print(f"状态码: {response.status_code}")
        except Exception as e:
            print(f"错误: {e}")
    
    # 6. 统计信息
    print("\n6. 测试统计信息...")
    try:
        response = requests.get(f"{base_url}/api/statistics")
        print(f"状态码: {response.status_code}")
        print(f"统计信息: {response.json()}")
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_api() 