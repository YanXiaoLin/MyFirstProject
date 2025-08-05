import os
import numpy as np
import rasterio
from airspace_grid import grid_decode,grid_encode

# 数据路径
data_dir = os.path.join(os.path.dirname(__file__), 'data', 'all_tif_data_wgs84')
population_tif = os.path.join(data_dir, 'population.tif')
building_tif = os.path.join(data_dir, 'shenzhengbuilding.tif')
terrain_tif = os.path.join(data_dir, 'terrain.tif')

# 读取tif数据为numpy数组
def read_tif(tif_path):
    with rasterio.open(tif_path) as src:
        arr = src.read(1)
        transform = src.transform
    return arr, transform

# 计算某经纬度高程点的风险分数
def get_risk_score(lon, lat, alt):
    pop_arr, pop_trans = read_tif(population_tif)
    bld_arr, bld_trans = read_tif(building_tif)
    ter_arr, ter_trans = read_tif(terrain_tif)
    
    def sample(arr, trans):
        col, row = ~trans * (lon, lat)
        col, row = int(col), int(row)
        if 0 <= row < arr.shape[0] and 0 <= col < arr.shape[1]:
            return arr[row, col]
        return 0
    
    pop = sample(pop_arr, pop_trans)
    bld = sample(bld_arr, bld_trans)
    ter = sample(ter_arr, ter_trans)
    # 简单加权风险分数
    score = 0.5 * pop + 0.3 * bld + 0.2 * abs(alt - ter)
    return score

# 风险分级（1-5级）
def risk_level(score):
    if score < 20:
        return 1
    elif score < 50:
        return 2
    elif score < 100:
        return 3
    elif score < 200:
        return 4
    else:
        return 5

# 给定网格编码，返回风险等级
def risk_by_code(grid_code):
    result = grid_decode.decode_grid(grid_code)
    lon, lat = result.center
    alt = (result.alt_range[0] + result.alt_range[1]) / 2 if hasattr(result, 'alt_range') else 0
    score = get_risk_score(lon, lat, alt)
    return risk_level(score)

# 给定经纬度高程，返回网格编码和风险等级
def risk_by_coord(lon, lat, alt):
    code = grid_encode.encode_grid(lon, lat, alt, level=11)
    score = get_risk_score(lon, lat, alt)
    return code, risk_level(score)

# 给定多边形区域，返回区域内所有网格的风险等级（简化实现：采样区域内网格中心点）
def risk_by_polygon(polygon):
    # polygon: [(lon, lat, alt), ...] 闭合
    from shapely.geometry import Polygon, Point
    poly2d = Polygon([(p[0], p[1]) for p in polygon])
    min_lon, min_lat, max_lon, max_lat = poly2d.bounds
    step = 0.002  # 约等于11级网格分辨率
    results = []
    alt = polygon[0][2] if len(polygon[0]) > 2 else 0
    lon = min_lon
    while lon <= max_lon:
        lat = min_lat
        while lat <= max_lat:
            if poly2d.contains(Point(lon, lat)):
                code = grid_encode.encode_grid(lon, lat, alt, level=11)
                score = get_risk_score(lon, lat, alt)
                results.append({'code': code, 'risk': risk_level(score)})
            lat += step
        lon += step
    return results
