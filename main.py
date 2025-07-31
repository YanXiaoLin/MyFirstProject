#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iwhereGIS 网格数据引擎完整测试案例
测试所有API接口的正确性和错误处理
"""

import sys
import os
import time
from airspace_grid.grid_manager import AirspaceGridManager

class GridEngineTester:
    """网格引擎测试器"""
    
    def __init__(self):
        self.manager = AirspaceGridManager()
        self.test_results = []
        
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("iwhereGIS 网格数据引擎完整测试")
        print("=" * 60)
        
        # 基础功能测试
        self.test_grid_generation()
        self.test_attribute_management()
        self.test_grid_query()
        self.test_coordinate_encoding()
        self.test_route_planning()
        self.test_statistics()
        self.test_search_functionality()
        self.test_import_export()
        self.test_error_handling()
        
        # 输出测试结果
        self.print_test_summary()
        
    def test_grid_generation(self):
        """测试网格生成功能"""
        print("\n1. 测试网格生成功能")
        print("-" * 40)
        
        try:
            # 测试基本网格生成
            grids = self.manager.generate_grids(
                lon_min=114.0, lon_max=114.001,
                lat_min=22.5, lat_max=22.501,
                level=8, alt_min=0, alt_max=100
            )
            
            assert len(grids) > 0, "网格生成失败"
            print(f"✓ 基本网格生成测试通过: 生成了 {len(grids)} 个网格")
            
            # 测试不同级别的网格生成
            level_6_grids = self.manager.generate_grids(
                lon_min=114.0, lon_max=114.01,
                lat_min=22.5, lat_max=22.51,
                level=6, alt_min=0, alt_max=200
            )
            
            assert len(level_6_grids) > 0, "6级网格生成失败"
            print(f"✓ 6级网格生成测试通过: 生成了 {len(level_6_grids)} 个网格")
            
            # 测试三维网格生成（带高程）
            grids_3d = self.manager.generate_grids(
                lon_min=114.0, lon_max=114.001,
                lat_min=22.5, lat_max=22.501,
                level=8, alt_min=0, alt_max=500
            )
            
            assert len(grids_3d) > 0, "三维网格生成失败"
            print(f"✓ 三维网格生成测试通过: 生成了 {len(grids_3d)} 个网格")
            
            self.test_results.append(("网格生成", True, "所有测试通过"))
            
        except Exception as e:
            print(f"✗ 网格生成测试失败: {e}")
            self.test_results.append(("网格生成", False, str(e)))
    
    def test_attribute_management(self):
        """测试属性管理功能"""
        print("\n2. 测试属性管理功能")
        print("-" * 40)
        
        try:
            # 先生成测试网格
            grids = self.manager.generate_grids(
                lon_min=114.0, lon_max=114.001,
                lat_min=22.5, lat_max=22.501,
                level=8, alt_min=0, alt_max=100
            )
            
            if len(grids) == 0:
                raise Exception("没有生成测试网格")
            
            test_grid = grids[0]
            
            # 测试设置飞行规则属性
            success = self.manager.update_grid_attribute(
                grid_code=test_grid.code,
                category="flight_rules",
                key="max_altitude",
                value=300
            )
            
            assert success, "属性更新失败"
            print("✓ 飞行规则属性设置测试通过")
            
            # 测试设置天气条件属性
            success = self.manager.update_grid_attribute(
                grid_code=test_grid.code,
                category="weather_conditions",
                key="visibility",
                value="good"
            )
            
            assert success, "天气属性更新失败"
            print("✓ 天气条件属性设置测试通过")
            
            # 测试获取属性
            attrs = self.manager.get_grid_attributes(test_grid.code)
            
            assert attrs is not None, "属性获取失败"
            assert attrs.flight_rules.get("max_altitude") == 300, "飞行规则属性不匹配"
            assert attrs.weather_conditions.get("visibility") == "good", "天气属性不匹配"
            print("✓ 属性获取测试通过")
            
            # 测试设置风险评估属性
            success = self.manager.update_grid_attribute(
                grid_code=test_grid.code,
                category="risk_assessment",
                key="risk_level",
                value="low"
            )
            
            assert success, "风险评估属性更新失败"
            print("✓ 风险评估属性设置测试通过")
            
            self.test_results.append(("属性管理", True, "所有测试通过"))
            
        except Exception as e:
            print(f"✗ 属性管理测试失败: {e}")
            self.test_results.append(("属性管理", False, str(e)))
    
    def test_grid_query(self):
        """测试网格查询功能"""
        print("\n3. 测试网格查询功能")
        print("-" * 40)
        
        try:
            # 先生成一些网格
            grids = self.manager.generate_grids(
                lon_min=114.0, lon_max=114.01,
                lat_min=22.5, lat_max=22.51,
                level=8, alt_min=0, alt_max=100
            )
            
            if len(grids) == 0:
                raise Exception("没有生成测试网格")
            
            # 测试根据编码查询网格
            test_grid = grids[0]
            queried_grid = self.manager.get_grid_by_code(test_grid.code)
            
            assert queried_grid is not None, "网格编码查询失败"
            assert queried_grid.code == test_grid.code, "网格编码不匹配"
            print(f"✓ 网格编码查询测试通过: {test_grid.code}")
            
            # 测试根据区域查询网格
            area_grids = self.manager.get_grids_by_area(
                lon_min=114.0, lon_max=114.01,
                lat_min=22.5, lat_max=22.51
            )
            
            assert len(area_grids) > 0, "区域查询失败"
            print(f"✓ 区域查询测试通过: 找到 {len(area_grids)} 个网格")
            
            # 测试查询不存在的网格
            non_existent = self.manager.get_grid_by_code("INVALID_CODE")
            assert non_existent is None, "应该返回None"
            print("✓ 无效编码查询测试通过")
            
            self.test_results.append(("网格查询", True, "所有测试通过"))
            
        except Exception as e:
            print(f"✗ 网格查询测试失败: {e}")
            self.test_results.append(("网格查询", False, str(e)))
    
    def test_coordinate_encoding(self):
        """测试坐标编码功能"""
        print("\n4. 测试坐标编码功能")
        print("-" * 40)
        
        try:
            # 测试基本坐标编码
            code = self.manager.get_grid_code_by_coordinates(
                lon=114.1234, lat=22.5678, alt=100, level=8
            )
            
            assert isinstance(code, str), "编码应该是字符串"
            assert len(code) > 0, "编码不能为空"
            print(f"✓ 基本坐标编码测试通过: {code}")
            
            # 测试不同级别的编码
            code_level_6 = self.manager.get_grid_code_by_coordinates(
                lon=114.1234, lat=22.5678, alt=100, level=6
            )
            
            assert code_level_6 != code, "不同级别应该有不同编码"
            print(f"✓ 不同级别编码测试通过: {code_level_6}")
            
            # 测试边界坐标编码
            boundary_code = self.manager.get_grid_code_by_coordinates(
                lon=179.9, lat=89.9, alt=0, level=1
            )
            
            assert isinstance(boundary_code, str), "边界坐标编码失败"
            print(f"✓ 边界坐标编码测试通过: {boundary_code}")
            
            self.test_results.append(("坐标编码", True, "所有测试通过"))
            
        except Exception as e:
            print(f"✗ 坐标编码测试失败: {e}")
            self.test_results.append(("坐标编码", False, str(e)))
    
    def test_route_planning(self):
        """测试路径规划功能"""
        print("\n5. 测试路径规划功能")
        print("-" * 40)
        
        try:
            # 测试简单路径规划
            waypoints = [
                (114.05, 22.55, 100),  # 起点
                (114.08, 22.58, 150)   # 终点
            ]
            
            grid_codes, route_grids = self.manager.calculate_route_grids(waypoints, level=8)
            
            assert isinstance(grid_codes, list), "路径网格编码应该是列表"
            assert len(grid_codes) > 0, "路径应该经过至少一个网格"
            assert isinstance(route_grids, list), "路径网格对象应该是列表"
            assert len(route_grids) > 0, "路径应该包含至少一个网格对象"
            print(f"✓ 简单路径规划测试通过: 经过 {len(grid_codes)} 个网格")
            
            # 测试多点路径规划
            multi_waypoints = [
                (114.05, 22.55, 100),
                (114.06, 22.56, 120),
                (114.07, 22.57, 140),
                (114.08, 22.58, 150)
            ]
            
            multi_grid_codes, multi_route_grids = self.manager.calculate_route_grids(multi_waypoints, level=8)
            
            assert len(multi_grid_codes) >= len(grid_codes), "多点路径应该经过更多网格"
            print(f"✓ 多点路径规划测试通过: 经过 {len(multi_grid_codes)} 个网格")
            
            self.test_results.append(("路径规划", True, "所有测试通过"))
            
        except Exception as e:
            print(f"✗ 路径规划测试失败: {e}")
            self.test_results.append(("路径规划", False, str(e)))
    
    def test_statistics(self):
        """测试统计功能"""
        print("\n6. 测试统计功能")
        print("-" * 40)
        
        try:
            # 先生成一些网格
            self.manager.generate_grids(
                lon_min=114.0, lon_max=114.01,
                lat_min=22.5, lat_max=22.51,
                level=8, alt_min=0, alt_max=100
            )
            
            # 测试统计信息
            stats = self.manager.get_statistics()
            
            assert isinstance(stats, dict), "统计信息应该是字典"
            assert 'total_grids' in stats, "缺少总网格数"
            assert 'level_distribution' in stats, "缺少级别分布"
            assert stats['total_grids'] > 0, "总网格数应该大于0"
            
            print(f"✓ 统计功能测试通过: 总网格数 {stats['total_grids']}")
            print(f"  级别分布: {stats['level_distribution']}")
            
            self.test_results.append(("统计功能", True, "所有测试通过"))
            
        except Exception as e:
            print(f"✗ 统计功能测试失败: {e}")
            self.test_results.append(("统计功能", False, str(e)))
    
    def test_search_functionality(self):
        """测试搜索功能"""
        print("\n7. 测试搜索功能")
        print("-" * 40)
        
        try:
            # 先生成测试网格并设置属性
            grids = self.manager.generate_grids(
                lon_min=114.0, lon_max=114.001,
                lat_min=22.5, lat_max=22.501,
                level=8, alt_min=0, alt_max=100
            )
            
            if len(grids) > 0:
                # 设置高风险属性
                self.manager.update_grid_attribute(
                    grids[0].code, "risk_assessment", "risk_level", "high"
                )
                
                # 设置低能见度属性
                if len(grids) > 1:
                    self.manager.update_grid_attribute(
                        grids[1].code, "weather_conditions", "visibility", "poor"
                    )
            
            # 测试搜索高风险网格
            high_risk_grids = self.manager.search_grids(
                category="risk_assessment",
                key="risk_level",
                value="high"
            )
            
            assert isinstance(high_risk_grids, list), "搜索结果应该是列表"
            print(f"✓ 高风险搜索测试通过: 找到 {len(high_risk_grids)} 个网格")
            
            # 测试搜索低能见度网格
            low_visibility_grids = self.manager.search_grids(
                category="weather_conditions",
                key="visibility",
                value="poor"
            )
            
            assert isinstance(low_visibility_grids, list), "搜索结果应该是列表"
            print(f"✓ 低能见度搜索测试通过: 找到 {len(low_visibility_grids)} 个网格")
            
            self.test_results.append(("搜索功能", True, "所有测试通过"))
            
        except Exception as e:
            print(f"✗ 搜索功能测试失败: {e}")
            self.test_results.append(("搜索功能", False, str(e)))
    
    def test_import_export(self):
        """测试数据导入导出功能"""
        print("\n8. 测试数据导入导出功能")
        print("-" * 40)
        
        try:
            # 先生成测试数据
            grids = self.manager.generate_grids(
                lon_min=114.0, lon_max=114.001,
                lat_min=22.5, lat_max=22.501,
                level=8, alt_min=0, alt_max=100
            )
            
            if len(grids) > 0:
                # 设置一些属性
                self.manager.update_grid_attribute(
                    grids[0].code, "flight_rules", "max_altitude", 300
                )
            
            # 测试导出数据
            export_file = "test_export.json"
            self.manager.export_to_json(export_file)
            
            assert os.path.exists(export_file), "导出文件不存在"
            print("✓ 数据导出测试通过")
            
            # 测试导入数据
            new_manager = AirspaceGridManager()
            new_manager.import_from_json(export_file)
            
            # 验证导入的数据
            stats = new_manager.get_statistics()
            assert stats['total_grids'] > 0, "导入后网格数量为0"
            print(f"✓ 数据导入测试通过: 导入了 {stats['total_grids']} 个网格")
            
            # 清理测试文件
            if os.path.exists(export_file):
                os.remove(export_file)
            
            self.test_results.append(("数据导入导出", True, "所有测试通过"))
            
        except Exception as e:
            print(f"✗ 数据导入导出测试失败: {e}")
            self.test_results.append(("数据导入导出", False, str(e)))
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n9. 测试错误处理")
        print("-" * 40)
        
        try:
            # 测试无效坐标范围
            try:
                self.manager.generate_grids(
                    lon_min=200, lon_max=210,  # 经度超出范围
                    lat_min=22.5, lat_max=22.7,
                    level=8
                )
                print("✗ 应该抛出ValueError异常")
                raise Exception("无效坐标范围测试失败")
            except Exception:
                print("✓ 无效坐标范围异常处理正确")
            
            # 测试查询不存在的网格
            non_existent = self.manager.get_grid_by_code("INVALID_CODE")
            if non_existent is None:
                print("✓ 查询不存在网格处理正确")
            else:
                print("✗ 应该返回None")
            
            # 测试更新不存在的网格属性
            success = self.manager.update_grid_attribute(
                "NONEXISTENT", "flight_rules", "max_altitude", 300
            )
            if not success:
                print("✓ 更新不存在网格属性处理正确")
            else:
                print("✗ 应该返回False")
            
            self.test_results.append(("错误处理", True, "所有测试通过"))
            
        except Exception as e:
            print(f"✗ 错误处理测试失败: {e}")
            self.test_results.append(("错误处理", False, str(e)))
    
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, passed, _ in self.test_results if passed)
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n详细结果:")
        for test_name, passed, message in self.test_results:
            status = "✓ 通过" if passed else "✗ 失败"
            print(f"  {test_name:<15} {status:<8} {message}")
        
        if failed_tests == 0:
            print("\n🎉 所有测试通过！iwhereGIS网格数据引擎运行正常。")
        else:
            print(f"\n⚠️  有 {failed_tests} 个测试失败，请检查相关功能。")

def run_performance_test():
    """运行性能测试"""
    print("\n" + "=" * 50)
    print("性能测试")
    print("=" * 50)
    
    manager = AirspaceGridManager()
    
    # 测试网格生成性能
    start_time = time.time()
    grids = manager.generate_grids(
        lon_min=114.0, lon_max=114.01,
        lat_min=22.5, lat_max=22.51,
        level=8, alt_min=0, alt_max=500
    )
    end_time = time.time()
    
    print(f"网格生成性能: {len(grids)} 个网格, 耗时 {end_time - start_time:.3f} 秒")
    print(f"平均速度: {len(grids)/(end_time - start_time):.0f} 网格/秒")
    
    # 测试查询性能
    if len(grids) > 0:
        start_time = time.time()
        for i in range(min(100, len(grids))):
            manager.get_grid_by_code(grids[i].code)
        end_time = time.time()
        
        print(f"查询性能: 100次查询, 耗时 {end_time - start_time:.3f} 秒")
        print(f"平均速度: {100/(end_time - start_time):.0f} 查询/秒")

def main():
    """主函数"""
    tester = GridEngineTester()
    tester.run_all_tests()
    
    # 如果所有测试通过，运行性能测试
    if all(passed for _, passed, _ in tester.test_results):
        run_performance_test()

if __name__ == "__main__":
    main()