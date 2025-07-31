#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iwhereGIS 网格数据引擎功能演示脚本
"""

from airspace_grid.grid_manager import AirspaceGridManager
import time

def demo_grid_generation():
    """演示网格生成功能"""
    print("=" * 50)
    print("1. 网格生成功能演示")
    print("=" * 50)
    
    manager = AirspaceGridManager()
    
    # 生成小区域网格
    print("生成小区域网格 (8级精度)...")
    start_time = time.time()
    grids = manager.generate_grids(
        lon_min=114.0, lon_max=114.001,
        lat_min=22.5, lat_max=22.501,
        level=8, alt_min=0, alt_max=100
    )
    end_time = time.time()
    
    print(f"✓ 生成了 {len(grids)} 个网格")
    print(f"✓ 耗时: {end_time - start_time:.3f} 秒")
    
    if grids:
        print(f"✓ 第一个网格编码: {grids[0].code}")
        print(f"✓ 网格边界: {grids[0].bbox}")
        print(f"✓ 网格中心: {grids[0].center}")
        print(f"✓ 高度范围: {grids[0].alt_range}")
    
    return grids

def demo_coordinate_encoding():
    """演示坐标编码功能"""
    print("\n" + "=" * 50)
    print("2. 坐标编码功能演示")
    print("=" * 50)
    
    manager = AirspaceGridManager()
    
    # 测试坐标编码
    test_coordinates = [
        (114.1234, 22.5678, 100, 8),
        (114.1234, 22.5678, 100, 6),
        (180.0, 90.0, 0, 1)
    ]
    
    for lon, lat, alt, level in test_coordinates:
        grid_code = manager.get_grid_code_by_coordinates(lon, lat, alt, level)
        print(f"✓ 坐标 ({lon}, {lat}, {alt}) 级别 {level} -> 编码: {grid_code}")

def demo_attribute_management(grids):
    """演示属性管理功能"""
    print("\n" + "=" * 50)
    print("3. 属性管理功能演示")
    print("=" * 50)
    
    if not grids:
        print("没有网格可用于演示")
        return
    
    manager = AirspaceGridManager()
    test_grid = grids[0]
    
    # 设置飞行规则属性
    print("设置飞行规则属性...")
    manager.update_grid_attribute(
        test_grid.code, "flight_rules", "max_altitude", 300
    )
    manager.update_grid_attribute(
        test_grid.code, "flight_rules", "max_speed", 120
    )
    manager.update_grid_attribute(
        test_grid.code, "flight_rules", "allowed_flight_types", ["VFR", "IFR"]
    )
    print("✓ 飞行规则属性设置完成")
    
    # 设置天气条件属性
    print("设置天气条件属性...")
    manager.update_grid_attribute(
        test_grid.code, "weather_conditions", "visibility", "good"
    )
    manager.update_grid_attribute(
        test_grid.code, "weather_conditions", "wind_speed", 5.5
    )
    print("✓ 天气条件属性设置完成")
    
    # 设置风险评估属性
    print("设置风险评估属性...")
    manager.update_grid_attribute(
        test_grid.code, "risk_assessment", "risk_level", "low"
    )
    manager.update_grid_attribute(
        test_grid.code, "risk_assessment", "hazard_count", 0
    )
    print("✓ 风险评估属性设置完成")
    
    # 获取并显示属性
    print("\n获取网格属性...")
    attrs = manager.get_grid_attributes(test_grid.code)
    if attrs:
        print(f"✓ 飞行规则: {attrs.flight_rules}")
        print(f"✓ 天气条件: {attrs.weather_conditions}")
        print(f"✓ 风险评估: {attrs.risk_assessment}")

def demo_search_functionality():
    """演示搜索功能"""
    print("\n" + "=" * 50)
    print("4. 搜索功能演示")
    print("=" * 50)
    
    manager = AirspaceGridManager()
    
    # 搜索高风险网格
    print("搜索高风险网格...")
    high_risk_grids = manager.search_grids(
        "risk_assessment", "risk_level", "high"
    )
    print(f"✓ 找到 {len(high_risk_grids)} 个高风险网格")
    
    # 搜索低能见度网格
    print("搜索低能见度网格...")
    low_visibility_grids = manager.search_grids(
        "weather_conditions", "visibility", "poor"
    )
    print(f"✓ 找到 {len(low_visibility_grids)} 个低能见度网格")

def demo_route_planning():
    """演示航线规划功能"""
    print("\n" + "=" * 50)
    print("5. 航线规划功能演示")
    print("=" * 50)
    
    manager = AirspaceGridManager()
    
    # 简单航线规划
    print("计算简单航线网格...")
    waypoints = [
        (114.05, 22.55, 100),  # 起点
        (114.08, 22.58, 150)   # 终点
    ]
    
    grid_codes, route_grids = manager.calculate_route_grids(waypoints, level=8)
    print(f"✓ 航线经过 {len(grid_codes)} 个网格")
    print(f"✓ 第一个网格编码: {grid_codes[0] if grid_codes else 'N/A'}")
    print(f"✓ 网格对象数量: {len(route_grids)}")
    
    # 多点航线规划
    print("\n计算多点航线网格...")
    multi_waypoints = [
        (114.05, 22.55, 100),
        (114.06, 22.56, 120),
        (114.07, 22.57, 140),
        (114.08, 22.58, 150)
    ]
    
    multi_grid_codes, multi_route_grids = manager.calculate_route_grids(multi_waypoints, level=8)
    print(f"✓ 多点航线经过 {len(multi_grid_codes)} 个网格")

def demo_statistics():
    """演示统计功能"""
    print("\n" + "=" * 50)
    print("6. 统计功能演示")
    print("=" * 50)
    
    manager = AirspaceGridManager()
    
    # 获取统计信息
    stats = manager.get_statistics()
    print("网格统计信息:")
    print(f"✓ 总网格数: {stats['total_grids']}")
    print(f"✓ 级别分布: {stats['level_distribution']}")

def demo_performance():
    """演示性能测试"""
    print("\n" + "=" * 50)
    print("7. 性能测试演示")
    print("=" * 50)
    
    manager = AirspaceGridManager()
    
    # 网格生成性能测试
    print("网格生成性能测试...")
    start_time = time.time()
    grids = manager.generate_grids(
        lon_min=114.0, lon_max=114.01,
        lat_min=22.5, lat_max=22.51,
        level=8, alt_min=0, alt_max=500
    )
    end_time = time.time()
    
    print(f"✓ 生成了 {len(grids)} 个网格")
    print(f"✓ 总耗时: {end_time - start_time:.3f} 秒")
    print(f"✓ 平均速度: {len(grids)/(end_time - start_time):.0f} 网格/秒")
    
    # 查询性能测试
    if grids:
        print("\n查询性能测试...")
        start_time = time.time()
        for i in range(min(100, len(grids))):
            manager.get_grid_by_code(grids[i].code)
        end_time = time.time()
        
        print(f"✓ 100次查询耗时: {end_time - start_time:.3f} 秒")
        print(f"✓ 平均速度: {100/(end_time - start_time):.0f} 查询/秒")

def main():
    """主演示函数"""
    print("iwhereGIS 网格数据引擎功能演示")
    print("=" * 60)
    
    try:
        # 1. 网格生成演示
        grids = demo_grid_generation()
        
        # 2. 坐标编码演示
        demo_coordinate_encoding()
        
        # 3. 属性管理演示
        demo_attribute_management(grids)
        
        # 4. 搜索功能演示
        demo_search_functionality()
        
        # 5. 航线规划演示
        demo_route_planning()
        
        # 6. 统计功能演示
        demo_statistics()
        
        # 7. 性能测试演示
        demo_performance()
        
        print("\n" + "=" * 60)
        print("🎉 所有功能演示完成！")
        print("=" * 60)
        print("\n下一步:")
        print("1. 运行 'python main.py' 进行完整测试")
        print("2. 运行 'python api_server.py' 启动HTTP API")
        print("3. 运行 'python test_api.py' 测试API接口")
        print("4. 查看 README_API.md 了解详细API文档")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        print("请检查依赖是否正确安装")

if __name__ == "__main__":
    main() 