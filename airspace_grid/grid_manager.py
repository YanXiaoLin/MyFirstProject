# airspace_grid/grid_manager.py
from typing import List, Dict, Optional, Tuple
from .grid_core import GridGenerator, GridCell
from .grid_encode import *
from .grid_attributes import GridAttributes, GridAttributeManager
import json
from . import grid_encode as ge
from .grid_decode import *

class AirspaceGridManager:
    """空域网格管理系统"""
    
    def __init__(self):
        self.grid_cells: Dict[str, GridCell] = {}
        self.attribute_manager = GridAttributeManager()
    
    def generate_grids(self, lon_min: float, lon_max: float,
                      lat_min: float, lat_max: float,
                      level: int, alt_min: float = 0.0, 
                      alt_max: float = 1000) -> List[GridCell]:
        """生成指定区域的网格"""
        grids = GridGenerator.get_grids(
            lon_min, lon_max, lat_min, lat_max, level, alt_min, alt_max
        )
        
        # 存储网格
        for grid in grids:
            self.grid_cells[grid.code] = grid
            
            # 创建对应的属性对象
            attrs = GridAttributes(
                grid_code=grid.code,
                level=grid.level,
                bbox=grid.bbox,
                center=grid.center,
                alt_range=list(grid.alt_range)
            )
            self.attribute_manager.add_grid_attributes(attrs)
            
        return grids
    
    def get_grid_by_code(self, code: str) -> Optional[GridCell]:
        """根据编码获取网格"""
        return decode_grid(code)   
    
    def get_grids_by_area(self, lon_min: float, lon_max: float,
                         lat_min: float, lat_max: float) -> List[GridCell]:
        """根据区域获取网格"""
        result = []
        for grid in self.grid_cells.values():
            # 检查网格是否与指定区域相交
            if (grid.bbox[2] >= lon_min and grid.bbox[0] <= lon_max and
                grid.bbox[3] >= lat_min and grid.bbox[1] <= lat_max):
                result.append(grid)
        return result
    def get_grid_code_by_coordinates(self, lon: float, lat: float, alt: float, level: int) -> str:        
        """根据经纬度、高程和level获取网格编码"""        
        return encode_grid(lon, lat, alt, level)    

    def get_attribute_manager(self) -> GridAttributeManager:
        """获取属性管理器"""
        return self.attribute_manager
    
    def update_grid_attribute(self, grid_code: str, category: str, 
                             key: str, value: any) -> bool:
        """更新网格属性"""
        return self.attribute_manager.update_grid_attributes(
            grid_code, category, key, value
        )
    
    def get_grid_attributes(self, grid_code: str) -> Optional[GridAttributes]:
        """获取网格属性"""
        return self.attribute_manager.get_grid_attributes(grid_code)
    
    def search_grids(self, category: str, key: str, value: any) -> List[GridCell]:
        """根据属性搜索网格"""
        attrs_list = self.attribute_manager.get_grids_by_category_value(
            category, key, value
        )
        return [self.grid_cells[attrs.grid_code] for attrs in attrs_list 
                if attrs.grid_code in self.grid_cells]
    
    def get_statistics(self) -> Dict[str, any]:
        """获取网格统计信息"""
        total_grids = len(self.grid_cells)
        level_counts = {}
        
        for grid in self.grid_cells.values():
            level = grid.level
            if level not in level_counts:
                level_counts[level] = 0
            level_counts[level] += 1
            
        return {
            "total_grids": total_grids,
            "level_distribution": level_counts
        }
    
    def export_to_json(self, filename: str) -> None:
        """导出网格数据到JSON文件"""
        data = {
            "grids": {code: {
                "level": grid.level,
                "bbox": grid.bbox,
                "center": grid.center,
                "size": grid.size,
                "code": grid.code,
                "alt_range": grid.alt_range,
                "cellid": grid.cellid
            } for code, grid in self.grid_cells.items()},
            "attributes": json.loads(self.attribute_manager.to_json())
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_from_json(self, filename: str) -> None:
        """从JSON文件导入网格数据"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 导入网格
        for code, grid_data in data["grids"].items():
            grid = GridCell(
                level=grid_data["level"],
                bbox=grid_data["bbox"],
                center=grid_data["center"],
                size=grid_data["size"],
                code=grid_data["code"],
                alt_range=tuple(grid_data["alt_range"]),
                cellid=grid_data["cellid"]
            )
            self.grid_cells[code] = grid
        
        # 导入属性
        self.attribute_manager.from_json(json.dumps(data["attributes"]))

    def calculate_route_grids(self, waypoints: List[Tuple[float, float, float]], level: int = 8) -> Tuple[List[str], GridCell]:
        """计算航线经过的网格"""
        point_cls = GridGenerator()
        visited_grids = set()
        result = []
        all_points = []
        all_points.append(waypoints[0])
        
     
        # 惠州空域边界
        lon_min = 113.7550
        lon_max = 114.6380  
        lat_min = 22.4480
        lat_max = 22.8340        

        max_level = level

        for level_info in [x for x in [
            {'level': 1, 'lon_deg': 6.0, 'lat_deg': 4.0, 'approx_lon': 768, 'approx_lat': 512, 'unit': 'km'},
            {'level': 2, 'lon_deg': 3.0, 'lat_deg': 2.0, 'approx_lon': 384, 'approx_lat': 256, 'unit': 'km'},
            {'level': 3, 'lon_deg': 0.5, 'lat_deg': 0.5, 'approx_lon': 55.66, 'approx_lat': 55.66, 'unit': 'km'},
            {'level': 4, 'lon_deg': 0.25, 'lat_deg': 1/6, 'approx_lon': 27.83, 'approx_lat': 18.55, 'unit': 'km'},
            {'level': 5, 'lon_deg': 1/12, 'lat_deg': 1/12, 'approx_lon': 9.27, 'approx_lat': 9.27, 'unit': 'km'},
            {'level': 6, 'lon_deg': 1/60, 'lat_deg': 1/60, 'approx_lon': 1.85, 'approx_lat': 1.85, 'unit': 'km'},
            {'level': 7, 'lon_deg': 1/300, 'lat_deg': 1/300, 'approx_lon': 0.37106, 'approx_lat': 0.37106, 'unit': 'km'},
            {'level': 8, 'lon_deg': 1/900, 'lat_deg': 1/900, 'approx_lon': 0.12369, 'approx_lat': 0.12369, 'unit': 'km'},
            {'level': 9, 'lon_deg': 1/1800, 'lat_deg': 1/1800, 'approx_lon': 0.06184, 'approx_lat': 0.06184, 'unit': 'km'},
            {'level': 10, 'lon_deg': 1/3600, 'lat_deg': 1/3600, 'approx_lon': 0.0309, 'approx_lat': 0.0309, 'unit': 'km'},
            {'level': 11, 'lon_deg': 1/7200, 'lat_deg': 1/7200, 'approx_lon': 0.01546, 'approx_lat': 0.01546, 'unit': 'km'},
            {'level': 12, 'lon_deg': 1/14400, 'lat_deg': 1/14400, 'approx_lon': 0.00773, 'approx_lat': 0.00773, 'unit': 'km'},
            {'level': 13, 'lon_deg': 1/28800, 'lat_deg': 1/28800, 'approx_lon': 0.00386, 'approx_lat': 0.00386, 'unit': 'km'},
            {'level': 14, 'lon_deg': 1/57600, 'lat_deg': 1/57600, 'approx_lon': 0.00193, 'approx_lat': 0.00193, 'unit': 'km'},
            {'level': 15, 'lon_deg': 1/115200, 'lat_deg': 1/115200, 'approx_lon': 0.00097, 'approx_lat': 0.00097, 'unit': 'km'},
            {'level': 16, 'lon_deg': 1/230400, 'lat_deg': 1/230400, 'approx_lon': 0.00048, 'approx_lat': 0.00048, 'unit': 'km'}
        ] if x['level'] == level]:
            lon_step = level_info['lon_deg']
            lat_step = level_info['lat_deg']     

        lon_starts = point_cls.generate_starts(lon_min, lon_max, lon_step)
        lat_starts = point_cls.generate_starts(lat_min, lat_max, lat_step)  
        
        for lon, lat, alt in all_points:
            # 计算经度索引
            relative_lon = lon - lon_starts[0]
            idx_lon = int(round(relative_lon / lon_step))  
            idx_lon = max(0, min(len(lon_starts)-1, idx_lon))
            closest_lon = lon_starts[idx_lon]
            max_lon = lon_starts[-1] + lon_step

            if lon < lon_starts[0]:
                closest_lon = lon_starts[0]
            elif lon >= max_lon:
                closest_lon = lon_starts[-1]
            elif lon < closest_lon:
                closest_lon = lon_starts[max(0, idx_lon-1)]
            elif lon >= (closest_lon + lon_step):
                closest_lon = lon_starts[min(len(lon_starts)-1, idx_lon+1)]
            
            # 计算纬度索引
            relative_lat = lat - lat_starts[0]
            idx_lat = int(round(relative_lat / lat_step))
            idx_lat = max(0, min(len(lat_starts)-1, idx_lat))
            closest_lat = lat_starts[idx_lat]
            max_lat = lat_starts[-1] + lat_step
            if lat < lat_starts[0]:
                closest_lat = lat_starts[0]
            elif lat >= max_lat:
                closest_lat = lat_starts[-1]
            elif lat < closest_lat:
                closest_lat = lat_starts[max(0, idx_lat-1)]
            elif lat >= (closest_lat + lat_step):
                closest_lat = lat_starts[min(len(lat_starts)-1, idx_lat+1)]
        
            # 计算高度索引
            alt_step = ge.MAX_ELEVATION / (2**ge.ELEVATION_BITS)
            alt_starts = point_cls.generate_starts(0, 1000, alt_step)

            relative_alt = alt - alt_starts[0]
            idx_alt = int(round(relative_alt/alt_step))
            idx_alt = max(0, min(len(alt_starts)-1, idx_alt))
            close_alt = alt_starts[idx_alt]
            max_alt = alt_starts[-1] + alt_step

            if alt < alt_starts[0]:
                close_alt = alt_starts[0]
            elif alt >= max_alt:
                close_alt = alt_starts[-1]
            elif alt < close_alt:
                close_alt = alt_starts[max(0, idx_alt-1)]
            elif alt >= (close_alt + alt_step):
                close_alt = alt_starts[min(len(alt_starts)-1, idx_alt+1)]
        
            # 创建网格单元
            point_grid = GridCell(
                level=max_level,
                bbox=[round(closest_lon,9), round(closest_lat,9),
                      round(closest_lon+lon_step,9), round(closest_lat+lat_step,9)],
                center=[round(closest_lon+lon_step/2,9), round(closest_lat+lat_step/2,9)],
                size={
                    'lon': level_info['approx_lon'],
                    'lat': level_info['approx_lat'],
                    'unit': level_info['unit']
                }
            )  

            point_grid.alt_range = (round(close_alt,2), round(close_alt+alt_step,2))
            
            center_lon = round(closest_lon+lon_step/2,9)
            center_lat = round(closest_lat+lat_step/2,9)
            center_alt = round(close_alt+alt_step/2,2)

            #grid_code = encode_grid(center_lon, center_lat, center_alt,max_level)
            point_grid.code = encode_grid(center_lon, center_lat, center_alt,max_level)
    
            #point_grid.code = grid_code

            if point_grid.code not in visited_grids:

                visited_grids.add(point_grid.code)
                result.append(point_grid.code)
        
        return result, point_grid



# 使用示例和测试代码
if __name__ == "__main__":
    # 创建网格管理器
    manager = AirspaceGridManager()
    
    # 生成网格 (以北京市为例)
    grids = manager.generate_grids(
        lon_min=116.0, lon_max=116.8,
        lat_min=39.5, lat_max=40.3,
        level=6, alt_min=0, alt_max=300
    )
    
    print(f"生成了 {len(grids)} 个网格")
    
    # 显示前几个网格的信息
    for i, grid in enumerate(grids[:3]):
        print(f"网格 {i+1}:")
        print(f"  编码: {grid.code}")
        print(f"  级别: {grid.level}")
        print(f"  边界: {grid.bbox}")
        print(f"  中心: {grid.center}")
        print(f"  高度范围: {grid.alt_range}")
        print()
    
    # 更新网格属性示例
    if grids:
        first_grid_code = grids[0].code
        
        # 更新飞行规则属性
        manager.update_grid_attribute(
            first_grid_code, "flight_rules", "max_speed", 120
        )
        manager.update_grid_attribute(
            first_grid_code, "flight_rules", "allowed_flight_types", ["VFR", "IFR"]
        )
        
        # 更新空域状态属性
        manager.update_grid_attribute(
            first_grid_code, "airspace_status", "status", "active"
        )
        manager.update_grid_attribute(
            first_grid_code, "airspace_status", "traffic_density", "medium"
        )
        
        # 更新气象环境属性
        manager.update_grid_attribute(
            first_grid_code, "weather_conditions", "wind_speed", 5.5
        )
        manager.update_grid_attribute(
            first_grid_code, "weather_conditions", "visibility", "good"
        )
        
        # 获取并显示属性
        attrs = manager.get_grid_attributes(first_grid_code)
        if attrs:
            print("第一个网格的属性:")
            print(f"  飞行规则: {attrs.flight_rules}")
            print(f"  空域状态: {attrs.airspace_status}")
            print(f"  气象条件: {attrs.weather_conditions}")
            print()
    
    # 搜索网格示例
    active_grids = manager.search_grids("airspace_status", "status", "active")
    print(f"找到 {len(active_grids)} 个活动状态的网格")
    
    # 显示统计信息
    stats = manager.get_statistics()
    print("网格统计信息:")
    print(f"  总网格数: {stats['total_grids']}")
    print(f"  级别分布: {stats['level_distribution']}")
    
    # 导出到JSON
    manager.export_to_json("airspace_grids.json")
    print("网格数据已导出到 airspace_grids.json")
