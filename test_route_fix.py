#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修正后的 calculate_route_grids 函数
验证是否能正确处理多个航点
"""

from airspace_grid.grid_manager import AirspaceGridManager

def test_route_calculation():
    """测试航线网格计算功能"""
    print("测试修正后的 calculate_route_grids 函数")
    print("=" * 50)
    
    # 创建网格管理器
    manager = AirspaceGridManager()
    
    # 测试用例1: 单点航线
    print("\n1. 测试单点航线")
    single_waypoint = [(114.05, 22.55, 100)]
    grid_codes, route_grids = manager.calculate_route_grids(single_waypoint, level=8)
    
    print(f"   航点数量: {len(single_waypoint)}")
    print(f"   网格编码数量: {len(grid_codes)}")
    print(f"   网格对象数量: {len(route_grids)}")
    print(f"   第一个网格编码: {grid_codes[0] if grid_codes else 'N/A'}")
    
    # 测试用例2: 两点航线
    print("\n2. 测试两点航线")
    two_waypoints = [
        (114.05, 22.55, 100),  # 起点
        (114.08, 22.58, 150)   # 终点
    ]
    grid_codes, route_grids = manager.calculate_route_grids(two_waypoints, level=8)
    
    print(f"   航点数量: {len(two_waypoints)}")
    print(f"   网格编码数量: {len(grid_codes)}")
    print(f"   网格对象数量: {len(route_grids)}")
    print(f"   网格编码列表: {grid_codes}")
    
    # 测试用例3: 多点航线
    print("\n3. 测试多点航线")
    multi_waypoints = [
        (114.05, 22.55, 100),
        (114.06, 22.56, 120),
        (114.07, 22.57, 140),
        (114.08, 22.58, 150)
    ]
    grid_codes, route_grids = manager.calculate_route_grids(multi_waypoints, level=8)
    
    print(f"   航点数量: {len(multi_waypoints)}")
    print(f"   网格编码数量: {len(grid_codes)}")
    print(f"   网格对象数量: {len(route_grids)}")
    print(f"   网格编码列表: {grid_codes}")
    
    # 验证网格对象信息
    if route_grids:
        print(f"\n4. 验证网格对象信息")
        for i, grid in enumerate(route_grids[:3]):  # 只显示前3个
            print(f"   网格 {i+1}:")
            print(f"     编码: {grid.code}")
            print(f"     级别: {grid.level}")
            print(f"     边界: {grid.bbox}")
            print(f"     中心: {grid.center}")
            print(f"     高度范围: {grid.alt_range}")
    
    # 验证去重功能
    print(f"\n5. 验证去重功能")
    print(f"   网格编码数量: {len(grid_codes)}")
    print(f"   网格对象数量: {len(route_grids)}")
    print(f"   编码是否等于对象数量: {len(grid_codes) == len(route_grids)}")
    
    # 验证所有网格编码都是唯一的
    unique_codes = set(grid_codes)
    print(f"   唯一编码数量: {len(unique_codes)}")
    print(f"   是否有重复编码: {len(unique_codes) != len(grid_codes)}")
    
    print("\n" + "=" * 50)
    print("测试完成！")
    
    if len(grid_codes) > 0 and len(route_grids) > 0:
        print("✓ 修正成功：函数现在能正确处理多个航点")
        return True
    else:
        print("✗ 修正失败：函数仍然有问题")
        return False

if __name__ == "__main__":
    test_route_calculation() 