# airspace_grid/grid_core.py
import sys
import math
from typing import List, Dict, Tuple
from dataclasses import dataclass
from decimal import Decimal, getcontext
import re
from .grid_encode import *
# 设置足够精度处理小数
getcontext().prec = 24

@dataclass
class GridCell:
    """三维网格基本单元类"""
    level: int
    bbox: List[float]
    center: List[float]
    size: Dict[str, float]
    code: str = ""
    alt_range: Tuple[float, float] = (0, 1000)
    cellid: int = 0

    def copy(self):
        """创建网格的副本"""
        return GridCell(
            level=self.level,
            bbox=self.bbox.copy(),
            center=self.center.copy(),
            size=self.size.copy(),
            code=self.code,
            alt_range=self.alt_range,
            cellid=self.cellid
        )

class GridGenerator:
    """网格生成器"""
    
    @classmethod
    def generate_starts(cls, min_val: float, max_val: float, step: float) -> List[float]:
        """生成网格起点（优化版）"""
        starts = []
        if step <= 0:
            return []
        current = math.floor(min_val / step) * step
        current = round(current, 9)
        
        while True:
            end = round(current + step, 9)
            if end > min_val and current < max_val:
                starts.append(round(current, 9))
            current = round(current + step, 9)
            if current > max_val:
                break
        return starts

    @classmethod
    def get_grids(cls, lon_min: float, lon_max: float,
                 lat_min: float, lat_max: float,
                 level_max: int, 
                 alt_min: float = 0.0, alt_max: float = 1000) -> List[GridCell]:
        # 网格参数配置
        grid_levels = [
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
        ]
        
        all_grids = []
        for level_info in [x for x in grid_levels if x['level'] == level_max]:
            lon_step = level_info['lon_deg']
            lat_step = level_info['lat_deg']
            
            lon_starts = cls.generate_starts(lon_min, lon_max, lon_step)
            lat_starts = cls.generate_starts(lat_min, lat_max, lat_step)
            
            for lon in lon_starts:
                for lat in lat_starts:
                    base_grid = GridCell(
                        level=level_info['level'],
                        bbox=[round(lon,9), round(lat,9),
                              round(lon+lon_step,9), round(lat+lat_step,9)],
                        center=[round(lon+lon_step/2,9), round(lat+lat_step/2,9)],
                        size={
                            'lon': level_info['approx_lon'],
                            'lat': level_info['approx_lat'],
                            'unit': level_info['unit']
                        }
                    )
                    center_lon = round(lon+lon_step/2,9)
                    center_lat = round(lat+lat_step/2,9)
                    if level_info['level'] >= 6:
                        height_levels = level_info['level'] - 5
                        alt_step = 1000 / (2 ** height_levels)
                        alt_starts = cls.generate_starts(alt_min, alt_max, alt_step)
                        for alt in alt_starts:
                            new_grid = base_grid.copy()
                            new_grid.alt_range = (round(alt,2), round(alt+alt_step,2))
                            center_alt = round(alt+alt_step/2,2)
                            new_grid.code = encode_grid(center_lon,center_lat,height=center_alt)
                            all_grids.append(new_grid)
                    else:
                        base_grid.code = encode_grid(center_lon,center_lat,height=alt_min)
                        all_grids.append(base_grid)
        return all_grids
