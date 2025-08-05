from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import matplotlib.pyplot as plt
import time
import taichi as ti
import sys
import logging
import io
import base64
import os
from datetime import datetime
from typing import List, Tuple
from typing import Tuple
from grid_core import GridGenerator, GridCell
import grid_encode as ge
from grid_encode import encode_grid


# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# 抑制matplotlib的调试日志
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('matplotlib.backends.backend_agg').setLevel(logging.WARNING)
logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)
logging.getLogger('matplotlib.pyplot').setLevel(logging.WARNING)
logging.getLogger('matplotlib.figure').setLevel(logging.WARNING)
logging.getLogger('matplotlib.axes').setLevel(logging.WARNING)

def calculate_point_grid(point: Tuple[float, float, float], level: int = 8) -> GridCell:
    """
    计算单个三维坐标点所在的网格
    
    Args:
        point: 三维坐标点 (经度, 纬度, 高度)
        level: 网格层级
        
    Returns:
        GridCell: 点所在的网格单元
    """
    lon, lat, alt = point
    point_cls = GridGenerator()  
    
    # 给定一定范围避免无意义计算
    lon_min = 114
    lon_max = 115 
    lat_min = 22
    lat_max = 23
   
    # 获取指定层级的网格参数
    level_info = None
    for info in [

        {'level': 1, 'lon_deg': 6.0, 'lat_deg': 4.0, 'approx_lon': 768, 'approx_lat': 256, 'unit': 'km'},
        {'level': 2, 'lon_deg': 3.0, 'lat_deg': 2.0, 'approx_lon': 384, 'approx_lat': 128, 'unit': 'km'},
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
        
    ]:
        if info['level'] == level:
            level_info = info
            break
    
    if level_info is None:
        raise ValueError(f"Unsupported level: {level}")
        
    lon_step = level_info['lon_deg']
    lat_step = level_info['lat_deg']
    
    lon_starts = point_cls.generate_starts(lon_min, lon_max, lon_step)
    lat_starts = point_cls.generate_starts(lat_min, lat_max, lat_step)
    
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
        level=level,
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
    
    point_grid.code = encode_grid(center_lon, center_lat, center_alt, level)
    
    return point_grid

# 文件日志函数
def file_debug_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("debug_output.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    # 同时尝试打印到stderr
    try:
        print(message, file=sys.stderr)
        sys.stderr.flush()
    except:
        pass

app = Flask(__name__)
CORS(app)  # 启用CORS，允许跨域请求

# 全局变量用于存储航线数据
existing_routes = []
new_routes = []

def load_channels_from_routes(existing_routes, new_routes):
    """
    从现有航线和新航线列表加载通道
    
    参数:
    - existing_routes: 现有航线列表，每个元素是航线字典
    - new_routes: 新增航线列表，每个元素是航线字典
    
    返回:
    - channels: 合并后的通道列表
    """
    channels = []
    
    # 处理现有航线
    for route in existing_routes:
        channels.append(route)
    
    # 处理新航线
    for route in new_routes:
        channels.append(route)
    
    return channels

def build_channel_field_and_mask(channels, max_time_steps=86400, num_dimensions=3):
    """构建通道字段和有效掩码"""
    num_channel = len(channels)
    file_debug_log(f"调试: 构建通道字段，航线数量: {num_channel}")
    
    # 处理空航线列表的情况
    if num_channel == 0:
        channel_np = np.zeros((0, max_time_steps, num_dimensions), dtype=np.float32)
        valid_mask = np.zeros((0, max_time_steps), dtype=bool)
        return channel_np, valid_mask
    
    channel_np = np.zeros((num_channel, max_time_steps, num_dimensions), dtype=np.float32)
    total_points = 0
    valid_points = 0
    
    for i, channel in enumerate(channels):
        filled_t = set()
        points = channel.get('points', [])
        total_points += len(points)
        file_debug_log(f"航线 {i+1} 包含 {len(points)} 个点")
        
        for point in points:
            # 检查expected_time_seconds键是否存在
            if 'expected_time_seconds' not in point:
                file_debug_log(f"  跳过点: 缺少 expected_time_seconds 字段")
                continue
            
            try:
                t = int(point['expected_time_seconds'])
                if t < 0 or t >= max_time_steps:
                    file_debug_log(f"  跳过点: 时间步 {t} 超出范围 [0, {max_time_steps})")
                    continue
                    
                if t in filled_t:
                    file_debug_log(f"  跳过点: 时间步 {t} 已存在")
                    continue
                    
                coords = point['geometry']['coordinates']
                if not isinstance(coords, (list, tuple)) or len(coords) < 3:
                    file_debug_log(f"  跳过点: 坐标数据无效 {coords}")
                    continue
                    
                channel_np[i, t, :] = coords[:3]
                filled_t.add(t)
                valid_points += 1
            except (ValueError, KeyError, TypeError) as e:
                file_debug_log(f"  跳过点: 数据转换错误 {str(e)}")
                continue
    
    file_debug_log(f"调试: 总共处理了 {total_points} 个航点，有效点数: {valid_points}")
    # 用 numpy 高效生成 valid_mask
    valid_mask = np.any(channel_np != 0, axis=2)  # shape: (num_channel, max_time_steps)
    file_debug_log(f"调试: 生成的字段形状: {channel_np.shape}，有效掩码形状: {valid_mask.shape}")
    
    # 统计有效时间步
    valid_timesteps = np.sum(np.any(valid_mask, axis=0))
    file_debug_log(f"调试: 有效时间步总数: {valid_timesteps}")
    
    return channel_np, valid_mask

@ti.kernel
def collect_conflicts_between_groups(channel_field: ti.template(), valid_mask: ti.template(),
                                   existing_count: int, epsilon: float, 
                                   result_triplets: ti.types.ndarray(), 
                                   result_count: ti.types.ndarray(), 
                                   conflict_flags: ti.types.ndarray()):
    """检测新航线与已有航线之间的冲突"""
    n = channel_field.shape[0]  # 总航线数
    tmax = channel_field.shape[1]
    epsilon_sq = epsilon * epsilon
    
    # 只检测新航线与已有航线之间的冲突
    for t in range(tmax):
        for i in range(existing_count, n):  # i: 新航线索引
            for j in range(0, existing_count):  # j: 已有航线索引
                if valid_mask[i, t] and valid_mask[j, t]:
                    p1 = channel_field[i, t]
                    p2 = channel_field[j, t]
                    dist_sq = (p1 - p2).norm_sqr()
                    if dist_sq < epsilon_sq:
                        ti.atomic_max(conflict_flags[t], 1)
                        idx = ti.atomic_add(result_count[0], 1)
                        if idx < result_triplets.shape[0]:
                            result_triplets[idx, 0] = t
                            result_triplets[idx, 1] = j  # 已有航线索引
                            result_triplets[idx, 2] = i  # 新航线索引

def detect_conflicts(existing_routes, new_routes, epsilon=0.001, max_time_steps=20000):
    """
    执行冲突检测的核心函数
    
    参数:
    - existing_routes: 已有航线列表
    - new_routes: 新航线列表
    - epsilon: 冲突距离阈值
    - max_time_steps: 最大时间步
    
    返回:
    - 包含冲突信息的字典
    """
    start_time = time.time()
    
    # 合并航线
    routes = existing_routes + new_routes
    existing_count = len(existing_routes)
    new_count = len(new_routes)
    
    # 检查是否有航线数据
    if not routes or existing_count == 0 or new_count == 0:
        file_debug_log("调试: 没有航线数据或缺少一方航线，跳过冲突检测")
        return {
            "status": "success",
            "num_existing_routes": existing_count,
            "num_new_routes": new_count,
            "max_time_steps": max_time_steps,
            "conflict_count": 0,
            "conflict_time_steps": 0,
            "conflict_times": [],
            "conflicts": [],
            "processing_time": 0,
            "detection_time": 0,
            "total_time": 0,
            "message": "没有航线数据或缺少一方航线，跳过冲突检测"
        }
    
    # 从输入列表加载通道
    channel_np, valid_mask = build_channel_field_and_mask(routes, max_time_steps=max_time_steps)
    
    num_channel, max_time_steps, num_dimensions = channel_np.shape
    file_debug_log(f"航线总数: {num_channel}, 已有航线数: {existing_count}, 新航线数: {new_count}")
    
    # 检查是否有有效航线数据
    if num_channel == 0:
        file_debug_log("调试: 没有有效航线数据，跳过冲突检测")
        return {
            "status": "success",
            "num_existing_routes": existing_count,
            "num_new_routes": new_count,
            "max_time_steps": max_time_steps,
            "conflict_count": 0,
            "conflict_time_steps": 0,
            "conflict_times": [],
            "conflicts": [],
            "processing_time": 0,
            "detection_time": 0,
            "total_time": time.time() - start_time,
            "message": "没有有效航线数据，跳过冲突检测"
        }
    
    processing_time = time.time() - start_time
    file_debug_log(f"数据预处理耗时: {processing_time:.3f} 秒")
    file_debug_log(f'加载了{num_channel}条航线, shape: {channel_np.shape}')
    
    # 统计有效数据点
    valid_points = np.sum(valid_mask)
    file_debug_log(f'有效数据点总数: {valid_points}')
    
    # 初始化 Taichi
    ti.init(arch=ti.cpu)
    
    # 创建 Taichi 字段
    valid_mask_field = ti.field(dtype=ti.i8, shape=(num_channel, max_time_steps))
    valid_mask_field.from_numpy(valid_mask.astype(np.int8))
    
    # 定义稀疏字段
    channel_field = ti.Vector.field(3, dtype=ti.f32)
    ti.root.dense(ti.i, num_channel).pointer(ti.j, max_time_steps).place(channel_field)
    
    # 填充稀疏字段
    @ti.kernel
    def fill_sparse_channel(channel_np: ti.types.ndarray()):
        for i in range(num_channel):
            for t in range(max_time_steps):
                if valid_mask_field[i, t] == 1:
                    channel_field[i, t] = ti.Vector([
                        channel_np[i, t, 0],
                        channel_np[i, t, 1],
                        channel_np[i, t, 2]
                    ])
    
    # 调用填充
    fill_sparse_channel(channel_np)
    
    # 准备结果存储
    conflict_flags = np.zeros(max_time_steps, dtype=np.int32)
    max_triplets = 1000000  # 预设最大冲突对数
    result_triplets = np.zeros((max_triplets, 3), dtype=np.int32)
    result_count = np.zeros(1, dtype=np.int32)
    
    # 执行冲突检测
    start_detect = time.time()
    file_debug_log("开始执行Taichi冲突检测...")
    collect_conflicts_between_groups(channel_field, valid_mask_field, existing_count, epsilon, 
                                  result_triplets, result_count, conflict_flags)
    detect_time = time.time() - start_detect
    file_debug_log(f"冲突检测耗时: {detect_time:.3f} 秒")
    
    # 提取结果
    conflict_times = np.where(conflict_flags == 1)[0].tolist()
    
    # 格式化冲突对
    conflicts = []
    if result_count[0] > 0:
        file_debug_log(f"检测到 {result_count[0]} 个冲突对")
        for k in range(min(result_count[0], 10000)):  # 限制处理数量以避免性能问题
            t, j, i = result_triplets[k]
            
            # 确保索引在有效范围内
            if j < existing_count and i < num_channel:
                # 获取航线信息
                existing_route = existing_routes[j]
                new_route = new_routes[i - existing_count]  # 新航线索引需要减去已有航线数量
                
                conflicts.append({
                    "time_step": int(t),
                    "existing_route_id": existing_route.get('id', f'route_{j}'),
                    "new_route_id": new_route.get('id', f'route_{i}'),
                    "existing_route_name": existing_route.get('name', f'Route {j}'),
                    "new_route_name": new_route.get('name', f'Route {i}'),
                    "debug_info": f"已有航线索引: {j}, 新航线索引: {i - existing_count}"
                })
    else:
        file_debug_log("未检测到冲突")
    
    # 准备返回结果
    result = {
        "status": "success",
        "num_existing_routes": existing_count,
        "num_new_routes": new_count,
        "max_time_steps": max_time_steps,
        "conflict_count": int(result_count[0]),
        "conflict_time_steps": len(conflict_times),
        "conflict_times": conflict_times,  # 限制返回数量，避免响应过大
        "conflicts": conflicts,  # 限制返回数量
        "processing_time": processing_time,
        "detection_time": detect_time,
        "total_time": time.time() - start_time,
        "valid_points": int(valid_points),
        "debug_message": f"检测到{result_count[0]}个新航线与已有航线之间的冲突"
    }
    
    file_debug_log(f"检测完成: {result['debug_message']}")
    return result

@app.route('/detect_conflicts', methods=['POST'])
def api_detect_conflicts():
    """冲突检测API端点"""
    try:
        file_debug_log("=== 开始处理冲突检测请求 ===")
        # 获取全局航线数据
        global existing_routes, new_routes
        
        # 添加航线数据结构调试信息
        routes = existing_routes + new_routes
        debug_routes_structure(routes)
        
        # 调试信息：准备航线数量和基本信息
        debug_info = {
            "existing_route_count": len(existing_routes),
            "new_route_count": len(new_routes),
            "routes_summary": []
        }
        
        file_debug_log(f"调试: 加载了 {len(existing_routes)} 条已有航线和 {len(new_routes)} 条新航线")
        
        # 记录已有航线信息
        for i, route in enumerate(existing_routes):
            route_info = {
                "type": "existing",
                "index": i,
                "id": route.get('id', 'N/A'),
                "name": route.get('name', 'N/A'),
                "point_count": len(route.get('points', []))
            }
            debug_info["routes_summary"].append(route_info)
            file_debug_log(f"已有航线 {i}: ID={route_info['id']}, 名称={route_info['name']}, 点数={route_info['point_count']}")
        
        # 记录新航线信息
        for i, route in enumerate(new_routes):
            route_info = {
                "type": "new",
                "index": i,
                "id": route.get('id', 'N/A'),
                "name": route.get('name', 'N/A'),
                "point_count": len(route.get('points', []))
            }
            debug_info["routes_summary"].append(route_info)
            file_debug_log(f"新航线 {i}: ID={route_info['id']}, 名称={route_info['name']}, 点数={route_info['point_count']}")
        
        # 执行冲突检测
        file_debug_log("开始执行冲突检测...")
        # 执行冲突检测
        result = detect_conflicts(existing_routes, new_routes, epsilon=0.001, max_time_steps=20000)
        file_debug_log("冲突检测执行完成")
        
        # 将调试信息添加到结果中
        result["debug_info"] = debug_info
        
        # 如果检测函数返回了消息，将其包含在响应中
        if "message" in result:
            file_debug_log(f"检测结果消息: {result['message']}")
            return jsonify(result)
        
        file_debug_log("=== 冲突检测请求处理完成 ===")
        return jsonify(result)
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        file_debug_log(f"错误: {error_trace}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": error_trace.split('\n')[-2]  # 返回最后一行错误信息
        }), 500

def parse_channel_data(data):
    """
    从新格式JSON数据中解析航线信息
    预期数据格式:
    {
      "channels": [
        {
          "id": 123,
          "code": "channel-001",
          "name": "航道1",
          "points": [
            {
              "num": 1,
              "geometry": {"coordinates": [lon, lat, alt]},
              "expected_time_seconds": 100,
              "grid_cell": {"code": "GRID_CODE"}
            },
            ...
          ]
        }
      ]
    }
    """
    if not isinstance(data, dict) or 'channels' not in data:
        raise ValueError("数据格式错误：必须包含'channels'字段的对象")
    
    channels = data['channels']
    if not isinstance(channels, list):
        raise ValueError("数据格式错误：'channels'必须是数组")
    
    parsed_routes = []
    
    for channel in channels:
        # 验证channel结构
        if not isinstance(channel, dict):
            continue
            
        # 提取航线基本信息
        route_id = str(channel.get('id', f"route_{int(time.time())}"))
        route_code = channel.get('code', f"route_code_{route_id}")
        route_name = channel.get('name', f"航道_{route_id}")
        
        # 提取航点数据
        points = channel.get('points', [])
        if not isinstance(points, list) or not points:
            continue
            
        # 按num排序航点
        sorted_points = sorted(points, key=lambda x: x.get('num', 0))
        
        # 验证航点数据完整性
        valid_points = []
        for point in sorted_points:
            if not isinstance(point, dict):
                continue
                
            # 检查必需字段
            if 'geometry' not in point or 'expected_time_seconds' not in point:
                continue
                
            geometry = point['geometry']
            if not isinstance(geometry, dict) or 'coordinates' not in geometry:
                continue
                
            coordinates = geometry['coordinates']
            if not isinstance(coordinates, list) or len(coordinates) < 3:
                continue
            
            valid_points.append(point)
        
        if len(valid_points) < 2:
            continue  # 至少需要2个航点才能形成航线
        
        # 生成航线颜色
        color = plt.cm.viridis(time.time() % 1)
        
        # 创建航线对象，保持原始数据格式
        route = {
            'id': route_id,
            'code': route_code,
            'name': route_name,
            "type": channel.get('type'),
            "radius": channel.get('radius'),
            "aircraft_model": channel.get('aircraft_model'),
            "level": channel.get('level'),
            'points': valid_points  # 直接使用原始格式的点数据
        }
        
        parsed_routes.append(route)
    
    return parsed_routes

@app.route('/upload_existing_routes', methods=['POST'])
def upload_existing_routes():
    """上传已存在航线"""
    try:
        # 获取JSON数据
        data = request.get_json()
        if data is None:
            return jsonify({
                'status': 'error',
                'message': '请求数据为空或格式错误'
            }), 400
        
        # 解析航线数据
        routes = parse_channel_data(data)
        
        if not routes:
            return jsonify({
                'status': 'error',
                'message': '没有找到有效的航线数据'
            }), 400
        
        # 存储航线
        global existing_routes
        existing_routes = routes
        
        return jsonify({
            'status': 'success',
            'message': f'成功上传 {len(routes)} 条已存在航线',
            'count': len(routes),
            'route_names': [route['name'] for route in routes]
        }), 200
        
    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/upload_new_routes', methods=['POST'])
def upload_new_routes():
    """上传新航线"""
    try:
        # 获取JSON数据
        data = request.get_json()
        if data is None:
            return jsonify({
                'status': 'error',
                'message': '请求数据为空或格式错误'
            }), 400
        
        # 解析航线数据
        routes = parse_channel_data(data)
        
        if not routes:
            return jsonify({
                'status': 'error',
                'message': '没有找到有效的航线数据'
            }), 400
        
        # 存储航线
        global new_routes
        new_routes = routes
        
        return jsonify({
            'status': 'success',
            'message': f'成功上传 {len(routes)} 条新航线',
            'count': len(routes),
            'route_names': [route['name'] for route in routes]
        }), 200
        
    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/get_routes', methods=['GET'])
def get_routes():
    """获取当前存储的航线信息"""
    return jsonify({
        'status': 'success',
        'existing_routes_count': len(existing_routes),
        'new_routes_count': len(new_routes),
        'existing_routes': [{
            'id': route['id'],
            'name': route['name'],
            'num_points': len(route['points'])
        } for route in existing_routes],
        'new_routes': [{
            'id': route['id'],
            'name': route['name'],
            'num_points': len(route['points'])
        } for route in new_routes]
    })

@app.route('/clear_routes', methods=['POST'])
def clear_routes():
    """清空航线数据"""
    data = request.get_json()
    clear_type = data.get('type', 'all') if data else 'all'
    
    global existing_routes, new_routes
    
    if clear_type == 'existing':
        existing_routes = []
        message = '已清空已存在航线数据'
    elif clear_type == 'new':
        new_routes = []
        message = '已清空新航线数据'
    else:
        existing_routes = []
        new_routes = []
        message = '已清空所有航线数据'
    
    return jsonify({
        'status': 'success',
        'message': message
    })

@app.route('/test_output', methods=['GET'])
def test_output():
    """测试输出功能"""
    print("这是一个测试输出消息")
    print(f"当前existing_routes数量: {len(existing_routes)}")
    print(f"当前new_routes数量: {len(new_routes)}")
    return jsonify({
        "status": "success",
        "message": "测试完成，请查看终端输出"
    })

def debug_routes_structure(routes, max_routes=5, max_points=10):
    """
    调试航线数据结构，输出详细信息以帮助诊断问题
    
    参数:
    - routes: 航线列表
    - max_routes: 最大显示航线数
    - max_points: 每条航线最大显示点数
    """
    file_debug_log("=== 航线数据结构调试信息 ===")
    file_debug_log(f"总航线数: {len(routes)}")
    
    for i, route in enumerate(routes[:max_routes]):
        file_debug_log(f"航线 {i+1}:")
        file_debug_log(f"  ID: {route.get('id', 'MISSING')}")
        file_debug_log(f"  名称: {route.get('name', 'MISSING')}")
        file_debug_log(f"  代码: {route.get('code', 'MISSING')}")
        
        # 检查航线中的所有键
        route_keys = list(route.keys())
        file_debug_log(f"  航线包含的键: {route_keys}")
        
        # 检查points字段
        if 'points' not in route:
            file_debug_log(f"  *** 错误: 航线缺少 'points' 字段 ***")
            continue
            
        points = route['points']
        file_debug_log(f"  点数: {len(points)}")
        
        if not isinstance(points, list):
            file_debug_log(f"  *** 错误: 'points' 不是列表，类型为 {type(points)} ***")
            continue
            
        # 检查前几个点的结构
        for j, point in enumerate(points[:max_points]):
            file_debug_log(f"    点 {j+1}:")
            if not isinstance(point, dict):
                file_debug_log(f"      *** 错误: 点不是字典，类型为 {type(point)} ***")
                file_debug_log(f"      点内容: {point}")
                continue
                
            point_keys = list(point.keys())
            file_debug_log(f"      点包含的键: {point_keys}")
            
            # 检查关键字段
            if 'expected_time_seconds' not in point:
                file_debug_log(f"      *** 缺少 'expected_time_seconds' 字段 ***")
            else:
                file_debug_log(f"      expected_time_seconds: {point['expected_time_seconds']} (类型: {type(point['expected_time_seconds'])})")
                
            if 'geometry' not in point:
                file_debug_log(f"      *** 缺少 'geometry' 字段 ***")
            else:
                geometry = point['geometry']
                file_debug_log(f"      geometry 类型: {type(geometry)}")
                if isinstance(geometry, dict) and 'coordinates' in geometry:
                    coords = geometry['coordinates']
                    file_debug_log(f"      coordinates: {coords} (类型: {type(coords)})")
                else:
                    file_debug_log(f"      *** geometry 格式错误 ***")
            
            # 显示点的完整内容（截断以避免过长）
            point_str = str(point)
            if len(point_str) > 200:
                point_str = point_str[:200] + "..."
            file_debug_log(f"      点完整内容: {point_str}")
            
        if len(points) > max_points:
            file_debug_log(f"    ... 还有 {len(points) - max_points} 个点未显示")
    
    if len(routes) > max_routes:
        file_debug_log(f"... 还有 {len(routes) - max_routes} 条航线未显示")
    file_debug_log("=== 航线数据结构调试信息结束 ===")

@app.route('/generate_routes_image', methods=['POST'])
def generate_routes_image():
    """
    生成航线图片
    
    参数:
    - existing_routes: 现有航线列表
    - new_routes: 新航线列表
    - params: 图片生成参数字典
    
    返回:
    - 包含生成结果的字典
    """

    
    try:
        # 加载航线数据
        routes = load_channels_from_routes(existing_routes, new_routes)
        conflict_result = detect_conflicts(existing_routes, new_routes, epsilon=0.0000000001, max_time_steps=20000)
        
        if not routes:
            return {
                'status': 'error',
                'message': '没有航线数据可供生成图片'
            }
        
        # 创建3D图形
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'FangSong', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 为每条航线生成不同的颜色，确保同一条航线使用同一种颜色
        # 使用tab10颜色映射为每条航线分配一个唯一颜色
        colors = plt.cm.tab10(np.linspace(0, 1, len(routes)))
        
        # 提取冲突点信息
        conflict_points = set()  # 存储冲突点的时间和航线信息
        if conflict_result.get("status") == "success":
            conflicts = conflict_result.get("conflicts", [])
            for conflict in conflicts:
                # 记录冲突的时间步和涉及的航线
                conflict_points.add((conflict["time_step"], conflict["existing_route_id"], conflict["new_route_id"]))
        
        # 绘制每条航线，确保整条航线使用同一种颜色
        for idx, route in enumerate(routes):
            route_id = route.get('id', f'route_{idx}')
            route_name = route.get('name', f'Route {idx+1}')
            
            # 提取航线点坐标
            lons, lats, alts = [], [], []
            times = []  # 时间信息用于颜色映射
            
            points = route.get('points', [])
            for point in points:
                coords = point['geometry']['coordinates']
                if len(coords) >= 3:
                    lons.append(coords[0])
                    lats.append(coords[1])
                    alts.append(coords[2])
                    times.append(point.get('expected_time_seconds', 0))
            
            if len(lons) > 0:
                # 绘制航线 - 整条航线使用同一种颜色colors[idx]
                ax.plot(lons, lats, alts, color=colors[idx], label=route_name, alpha=1,linewidth=2)
                               
                # 绘制每个航点对应的三维网格轮廓
                drawn_grids = set()  # 用于跟踪已经绘制的网格，避免重复绘制
                
                # 收集需要绘制的网格
                grid_boxes = []
                for point in points:
                    if 'grid_cell' in point and point['grid_cell']:
                        coords = point['geometry']['coordinates']
                        grid_cell = calculate_point_grid((coords[0],coords[1],coords[2]),level=11)
                        # 检查是否有bbox和alt_range
                        bbox = grid_cell.bbox
                        alt_range = grid_cell.alt_range
                        # 创建网格的唯一标识
                        grid_key = (str(bbox), str(alt_range))  # 转换为字符串以确保可哈希
                        if grid_key not in drawn_grids:
                            grid_boxes.append({
                                'bbox': bbox,
                                'alt_range': alt_range,
                                'color': colors[idx],  # 使用航线的颜色
                                'is_conflict': False  # 默认不是冲突网格
                            })
                            drawn_grids.add(grid_key)
                
                # 检查当前航线的点是否涉及冲突
                for point_idx, point in enumerate(points):
                    point_time = point.get('expected_time_seconds', -1)
                    # 检查该点的时间是否与任何冲突时间匹配
                    for conflict_time, existing_id, new_id in conflict_points:
                        if point_time == conflict_time and (route_id == existing_id or route_id == new_id):
                            # 标记该点所在的网格为冲突网格
                            coords = point['geometry']['coordinates']
                            if len(coords) >= 3:
                                grid_cell = calculate_point_grid((coords[0], coords[1], coords[2]), level=11)
                                bbox = grid_cell.bbox
                                alt_range = grid_cell.alt_range
                                grid_key = (str(bbox), str(alt_range))
                                # 查找并更新网格标记
                                for grid_box in grid_boxes:
                                    box_key = (str(grid_box['bbox']), str(grid_box['alt_range']))
                                    if box_key == grid_key:
                                        grid_box['is_conflict'] = True
                                        break
                
                # 绘制所有唯一的网格框
                for grid_box in grid_boxes:
                    bbox = grid_box['bbox']
                    alt_range = grid_box['alt_range']
                    color = grid_box['color']
                    is_conflict = grid_box.get('is_conflict', False)
                    
                    # 获取网格的边界并确保是数值类型
                    try:
                        # 处理不同的bbox格式
                        if isinstance(bbox, dict):
                            # 如果bbox是字典格式，例如 {'min_lon': ..., 'min_lat': ..., 'max_lon': ..., 'max_lat': ...}
                            lon_min = float(bbox.get('min_lon', bbox.get('lon_min', 0)))
                            lat_min = float(bbox.get('min_lat', bbox.get('lat_min', 0)))
                            lon_max = float(bbox.get('max_lon', bbox.get('lon_max', 0)))
                            lat_max = float(bbox.get('max_lat', bbox.get('lat_max', 0)))
                        else:
                            # 如果bbox是列表或元组格式
                            lon_min = float(bbox[0])
                            lat_min = float(bbox[1])
                            lon_max = float(bbox[2])
                            lat_max = float(bbox[3])
                        
                        # 处理不同的alt_range格式
                        if isinstance(alt_range, dict):
                            # 如果alt_range是字典格式
                            alt_min = float(alt_range.get('min_alt', alt_range.get('alt_min', 0)))
                            alt_max = float(alt_range.get('max_alt', alt_range.get('alt_max', 0)))
                        else:
                            # 如果alt_range是列表或元组格式
                            alt_min = float(alt_range[0])
                            alt_max = float(alt_range[1])
                    except (ValueError, TypeError, IndexError, KeyError) as e:
                        # 如果数据格式不正确，跳过这个网格
                        continue
                    
                    # 创建网格框的8个顶点
                    vertices = [
                        [lon_min, lat_min, alt_min],
                        [lon_max, lat_min, alt_min],
                        [lon_max, lat_max, alt_min],
                        [lon_min, lat_max, alt_min],
                        [lon_min, lat_min, alt_max],
                        [lon_max, lat_min, alt_max],
                        [lon_max, lat_max, alt_max],
                        [lon_min, lat_max, alt_max]
                    ]
                    
                    # 创建网格框的12条边
                    edges = [
                        [0, 1], [1, 2], [2, 3], [3, 0],  # 底面
                        [4, 5], [5, 6], [6, 7], [7, 4],  # 顶面
                        [0, 4], [1, 5], [2, 6], [3, 7]   # 垂直边
                    ]
                    
                    # 绘制网格框，冲突网格使用红色，其他网格使用黑色
                    line_color = 'red' if is_conflict else 'black'
                    line_alpha = 1.0 if is_conflict else 0.2
                    
                    # 绘制网格框
                    for edge in edges:
                        points = [vertices[edge[0]], vertices[edge[1]]]
                        xs = [points[0][0], points[1][0]]
                        ys = [points[0][1], points[1][1]]
                        zs = [points[0][2], points[1][2]]
                        ax.plot(xs, ys, zs, color=line_color, alpha=line_alpha, linewidth=0.5)
                    
                    # 如果是冲突网格，绘制半透明的红色表面以突出显示
                    if is_conflict:
                        # 绘制6个面的网格表面
                        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
                        
                        faces = [
                            [vertices[0], vertices[1], vertices[2], vertices[3]],  # 底面
                            [vertices[4], vertices[5], vertices[6], vertices[7]],  # 顶面
                            [vertices[0], vertices[1], vertices[5], vertices[4]],  # 前面
                            [vertices[2], vertices[3], vertices[7], vertices[6]],  # 后面
                            [vertices[1], vertices[2], vertices[6], vertices[5]],  # 右面
                            [vertices[0], vertices[3], vertices[7], vertices[4]]   # 左面
                        ]
                        
                        # 创建3D多边形集合并添加到图形中
                        poly3d = Poly3DCollection(faces, alpha=0.3, facecolor='red', edgecolor='red')
                        ax.add_collection3d(poly3d)
                
                # 添加标签
                if len(lons) > 0:
                    ax.text(lons[0], lats[0], alts[0], f'{route_name} Start', 
                           color=colors[idx], fontsize=8)
                    ax.text(lons[-1], lats[-1], alts[-1], f'{route_name} End', 
                           color=colors[idx], fontsize=8)
        
        ax.set_xlabel('经度')
        ax.set_ylabel('纬度')
        ax.set_zlabel('高度')
        ax.set_title('无人机航线可视化')
        
        ax.legend()
        
        # 优化视角
        ax.view_init(elev=20, azim=45)
        
        # 生成文件名
        filename = "channel_conflict.png"

        # 保存图片到文件系统
        plt.savefig(filename, format='png', dpi=300, bbox_inches='tight')

        plt.show()
        
        
        # 保存图片到内存以返回给客户端
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        
        # 将图片转换为base64编码
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # 关闭图形以释放内存
        plt.close(fig)
        
        # 检查文件是否成功保存
        file_saved = False
        file_path = None
        if os.path.exists(filename):
            file_saved = True
            file_path = os.path.abspath(filename)
        
        # 返回结果
        return {
            'status': 'success',
            'message': f'成功生成{len(routes)}条航线的图片',
            'routes_count': len(routes),
            'image_data': img_base64,
            'file_path': file_path if file_saved else None
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {
            'status': 'error',
            'message': f'生成图片时发生错误: {str(e)}',
            'traceback': error_trace
        }

if __name__ == '__main__':
    print("启动航线上传服务...")
    print("可用API端点:")
    print("  POST /upload_existing_routes - 上传已存在航线")
    print("  POST /upload_new_routes - 上传新航线")
    print("  POST /detect_conflicts - 检测冲突")
    print("  GET /get_routes - 获取航线信息")
    print("  POST /clear_routes - 清空航线数据")
    print("  POST /generate_routes_image - 生成航线图片")
    print("  GET /test_output - 测试输出功能")
    app.run(host='0.0.0.0', port=9005, debug=True)