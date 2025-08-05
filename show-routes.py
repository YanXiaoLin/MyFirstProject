import json
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from datetime import datetime
import uuid
# 导入网格系统
from airspace_grid.grid_manager import *
from airspace_grid.grid_core import *
from airspace_grid.grid_encode import *

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

# 设置插值距离阈值（米）
INTERPOLATION_THRESHOLD = 2.0

def calculate_distance(coord1, coord2):
    """
    计算两点间距离（使用经纬度距离公式）
    """
    lon1, lat1, alt1 = coord1
    lon2, lat2, alt2 = coord2
    
    # 经纬度距离计算（Haversine公式简化版）
    R = 6371000  # 地球半径（米）
    d_lat = np.radians(lat2 - lat1)
    d_lon = np.radians(lon2 - lon1)
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    
    a = np.sin(d_lat/2) * np.sin(d_lat/2) + \
        np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(d_lon/2) * np.sin(d_lon/2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    horizontal_distance = R * c
    
    # 加上垂直距离
    vertical_distance = abs(alt2 - alt1)
    total_distance = np.sqrt(horizontal_distance**2 + vertical_distance**2)
    
    return total_distance

def interpolate_point(start_point, end_point, t):
    """
    在两点间进行线性插值
    
    Args:
        start_point: 起点坐标 [lon, lat, alt]
        end_point: 终点坐标 [lon, lat, alt]
        t: 插值参数 (0-1)
    
    Returns:
        interpolated_point: 插值点坐标
    """
    lon = start_point[0] + (end_point[0] - start_point[0]) * t
    lat = start_point[1] + (end_point[1] - start_point[1]) * t
    alt = start_point[2] + (end_point[2] - start_point[2]) * t
    return [lon, lat, alt]

def sample_segment_by_distance(start_point, end_point, speed, threshold=INTERPOLATION_THRESHOLD, level=6, airspace_manager=None):
    """
    根据距离进行插值采样，每隔threshold米采样一个点，并去重重复网格
    
    Args:
        start_point: 起点坐标 [lon, lat, alt]
        end_point: 终点坐标 [lon, lat, alt]
        speed: 航段速度 (米/秒)
        threshold: 插值距离阈值（米）
        level: 网格级别
    
    Returns:
        sampled_points: 采样点列表
        time_intervals: 各段的时间间隔列表
        segment_time: 总飞行时间
        grid_codes: 网格编码列表
        grid_cells: 网格对象列表
    """
    # 计算直线距离
    distance = calculate_distance(start_point, end_point)
    
    # 计算飞行时间
    if speed > 0:
        segment_time = distance / speed  # 秒
    else:
        segment_time = 0
    
    # 生成采样点
    raw_sampled_points = []
    
    # 始终包含起点
    raw_sampled_points.append(start_point)
    
    # 如果距离大于阈值，则每隔threshold米采样一个点
    if distance > threshold:
        # 计算需要采样的中间点数量
        num_intervals = int(distance / threshold)
        
        # 生成中间采样点
        for i in range(1, num_intervals):
            # 计算插值参数
            t = (i * threshold) / distance
            point = interpolate_point(start_point, end_point, t)
            raw_sampled_points.append(point)
    
    # 始终包含终点
    raw_sampled_points.append(end_point)
    
    # 获取每个采样点的网格编码和网格对象
    raw_grid_codes = []
    raw_grid_cells = []
    
    for point in raw_sampled_points:
        obj_waypoints = [(point[0], point[1], point[2])]
        grid_codes, grid_cells = airspace_manager.calculate_route_grids(obj_waypoints, level)
        raw_grid_codes.append(grid_codes[0] if isinstance(grid_codes, list) else grid_codes)
        raw_grid_cells.append(grid_cells[0] if isinstance(grid_cells, list) and len(grid_cells) > 0 else grid_cells)
    
    # 去重重复网格编码（保留每个网格的第一个和最后一个点）
    unique_sampled_points = []
    unique_grid_codes = []
    unique_grid_cells = []
    
    if len(raw_sampled_points) > 0:
        # 添加第一个点
        unique_sampled_points.append(raw_sampled_points[0])
        unique_grid_codes.append(raw_grid_codes[0])
        unique_grid_cells.append(raw_grid_cells[0])
        
        # 遍历中间点，只保留网格编码发生变化的点
        for i in range(1, len(raw_sampled_points)):
            if raw_grid_codes[i] != raw_grid_codes[i-1]:
                # 网格编码发生变化，添加前一个点（网格的最后一个点）
                if len(unique_sampled_points) == 1 or unique_sampled_points[-1] != raw_sampled_points[i-1]:
                    unique_sampled_points.append(raw_sampled_points[i-1])
                    unique_grid_codes.append(raw_grid_codes[i-1])
                    unique_grid_cells.append(raw_grid_cells[i-1])
                
                # 添加当前点（新网格的第一个点）
                unique_sampled_points.append(raw_sampled_points[i])
                unique_grid_codes.append(raw_grid_codes[i])
                unique_grid_cells.append(raw_grid_cells[i])
        
        # 确保包含最后一个点
        if len(unique_sampled_points) == 0 or unique_sampled_points[-1] != raw_sampled_points[-1]:
            unique_sampled_points.append(raw_sampled_points[-1])
            unique_grid_codes.append(raw_grid_codes[-1])
            unique_grid_cells.append(raw_grid_cells[-1])
    
    # 计算时间间隔
    num_samples = len(unique_sampled_points) - 1
    time_per_sample = segment_time / num_samples if num_samples > 0 else 0
    time_intervals = [time_per_sample] * num_samples
    
    print(f"  原始采样点: {len(raw_sampled_points)}, 去重后: {len(unique_sampled_points)}")
    
    return unique_sampled_points, time_intervals, segment_time, unique_grid_codes, unique_grid_cells

def get_point_by_num(points, point_num):
    """
    根据点序号获取点坐标
    """
    for point in points:
        if point['num'] == point_num:
            return point['geometry']['coordinates']
    return None

def generate_complete_waypoints_with_grid_continuity(channel, base_time=0, level=6, airspace_manager=None, route_id=None):
    """
    根据航段生成完整的航点序列，根据距离进行插值并去重网格
    
    Args:
        channel: 航道数据
        base_time: 基准时间戳
        level: 网格级别
        airspace_manager: 空域管理器
        route_id: 航线ID
    
    Returns:
        waypoints: 完整的航点列表，包含时间信息
    """
    waypoints = []
    current_time = base_time
    points_data = channel['points']
    segments_data = channel['segments']
    
    print(f"开始生成航点序列，基准时间: {base_time}")
    
    # 按照segments顺序处理
    for segment_idx, segment in enumerate(segments_data):
        point_nums = segment['points']  # [起点序号, 终点序号]
        speed = segment.get('speed', 50)  # 默认速度50米/秒
        
        start_num, end_num = point_nums[0], point_nums[1]
        start_coord = get_point_by_num(points_data, start_num)
        end_coord = get_point_by_num(points_data, end_num)
        
        if start_coord is None or end_coord is None:
            print(f"警告: 找不到点 {start_num} 或 {end_num}")
            continue
        
        print(f"处理航段 {segment_idx+1}: 点{start_num} -> 点{end_num}, 速度: {speed}m/s")
        
        # 根据距离进行插值采样并去重网格
        sampled_points, time_intervals, segment_time, grid_codes, grid_cells = sample_segment_by_distance(
            start_coord, end_coord, speed, INTERPOLATION_THRESHOLD, level, airspace_manager
        )
        
        distance = calculate_distance(start_coord, end_coord)
        print(f"  航段距离: {distance:.2f}米, 采样点数: {len(sampled_points)}, 飞行时间: {segment_time:.2f}秒")
        
        # 添加采样点到航点列表
        for i, (point_coord, time_interval, grid_code, grid_cell) in enumerate(zip(sampled_points, time_intervals, grid_codes, grid_cells)):
            waypoint = {
                'waypoint_id': f"{route_id}_wp_{len(waypoints)+1:04d}",  # 航点ID
                'coordinates': point_coord,
                'time': current_time,
                'speed': speed,
                'grid_code': grid_code,
                'is_segment_start': (i == 0),
                'is_segment_end': (i == len(sampled_points) - 1),
                'segment_index': segment_idx,
                'grid_cell': grid_cell,
                'route_id': route_id  # 航线ID
            }
            
            waypoints.append(waypoint)
            current_time += time_interval
    
    print(f"总共生成 {len(waypoints)} 个航点")
    return waypoints

def save_waypoints_to_json(waypoints, route_info, filename="waypoints.json"):
    """
    将航点序列保存到JSON文件，包含航线ID信息
    
    Args:
        waypoints: 航点列表
        route_info: 航线信息
        filename: 保存的文件名
    """
    # 转换航点数据为可序列化的格式
    serializable_waypoints = []
    count_points=0
    for wp in waypoints:
        # 处理grid_cell对象，只保存基本信息
        count_points=count_points+1
        grid_cell_info = None
        if wp['grid_cell'] is not None:
            try:
                grid_cell_info = {
                    'level': getattr(wp['grid_cell'], 'level', None),
                    'bbox': getattr(wp['grid_cell'], 'bbox', None),
                    'center': getattr(wp['grid_cell'], 'center', None),
                    'alt_range': getattr(wp['grid_cell'], 'alt_range', None),
                    'code': getattr(wp['grid_cell'], 'code', ''),
                }
            except:
                grid_cell_info = str(wp['grid_cell'])  # 如果无法序列化，转换为字符串
        
        serializable_waypoint = {
            'waypoint_id': wp['waypoint_id'],
            'coordinates': wp['coordinates'],
            'time': wp['time'],
            'speed': wp['speed'],
            'num': count_points,
            'is_segment_start': wp['is_segment_start'],
            'is_segment_end': wp['is_segment_end'],
            'segment_index': wp['segment_index'],
            'route_id': wp['route_id'],
            'grid_cell': grid_cell_info
        }
        serializable_waypoints.append(serializable_waypoint)
    
    # 创建完整的数据结构
    data = {
        'metadata': {
            'route_id': route_info.get('route_id', ''),
            'route_name': route_info.get('route_name', ''),
            'total_waypoints': len(serializable_waypoints),
            'generated_time': datetime.now().isoformat(),
            'description': '无人机航点序列数据'
        },
        'route_info': route_info,
        'waypoints': serializable_waypoints
    }
    
    # 保存到JSON文件
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"航点序列已保存到 {filename}")
    except Exception as e:
        print(f"保存航点序列时出错: {e}")

def draw_grid_box(ax, grid_cell, color='yellow', alpha=0.2):
    """
    在3D图中绘制网格框
    """
    if grid_cell is None:
        return
    
    try:
        # 获取网格的边界
        lon_min, lon_max = grid_cell.bbox[0], grid_cell.bbox[2]
        lat_min, lat_max = grid_cell.bbox[1], grid_cell.bbox[3]
        alt_min, alt_max = grid_cell.alt_range[0], grid_cell.alt_range[1]
        
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
        
        # 绘制网格框
        for edge in edges:
            points = np.array([vertices[edge[0]], vertices[edge[1]]])
            ax.plot3D(points[:, 0], points[:, 1], points[:, 2], color=color, alpha=alpha, linewidth=0.5)
            
    except Exception as e:
        print(f"绘制网格框时出错: {e}")
        pass

def visualize_sampled_3d_with_grids(data, channel_name="航道1", level=6):
    """
    可视化采样后的3D航线（包含网格信息）
    """
    airspace_manager = AirspaceGridManager()
    
    fig = plt.figure(figsize=(15, 12))
    
    # 创建3D航线图
    ax1 = fig.add_subplot(1, 1, 1, projection='3d')
    
    # 获取指定航道的数据
    route = data['data']['route']
    target_channel = None
    for channel in route['channels']:
        if channel['name'] == channel_name:
            target_channel = channel
            break
    
    if not target_channel:
        print(f"未找到{channel_name}")
        return
    
    # 生成航线ID
    route_id = route.get('id', f"route_{uuid.uuid4().hex[:8]}")
    
    # 获取航线占用时间作为基准时间
    base_time = route['schedule']['occupied_times'][0]['start_time'] if route['schedule'].get('occupied_times') else 0
    
    # 准备航线信息
    route_info = {
        'route_id': route_id,
        'route_name': channel_name,
        'base_time': base_time,
        'grid_level': level,
        'sampling_threshold': INTERPOLATION_THRESHOLD
    }
    
    # 生成完整的航点序列
    waypoints = generate_complete_waypoints_with_grid_continuity(target_channel, base_time, level, airspace_manager, route_id)
  
    if not waypoints:
        print("未生成航点")
        return
    
    # 保存航点序列到JSON文件
    save_waypoints_to_json(waypoints, route_info, f"{channel_name}_waypoints.json")
    
    # 提取坐标和时间信息
    lons = [wp['coordinates'][0] for wp in waypoints]
    lats = [wp['coordinates'][1] for wp in waypoints]
    alts = [wp['coordinates'][2] for wp in waypoints]
    times = [wp['time'] for wp in waypoints]
    grid_codes = [wp['grid_code'] for wp in waypoints]
    
    # 3D航线图
    ax1.plot(lons, lats, alts, 'b-', linewidth=2, alpha=0.7, label='航线')
    scatter1 = ax1.scatter(lons, lats, alts, c=times, cmap='viridis', s=20)
    
    # 绘制每个航点的网格框
    for wp in waypoints:
        draw_grid_box(ax1, wp['grid_cell'], color='blue', alpha=0.1)
    
    # 标注关键点
    for i, wp in enumerate(waypoints):
        if wp['is_segment_start'] or wp['is_segment_end']:
            ax1.text(wp['coordinates'][0], wp['coordinates'][1], wp['coordinates'][2], 
                    f'{i+1}', fontsize=8, color='red')
    
    ax1.set_xlabel('经度')
    ax1.set_ylabel('纬度')
    ax1.set_zlabel('高度(米)')
    ax1.set_title(f'{channel_name} - 3D航线图\n航点数: {len(waypoints)}, 航线ID: {route_id}')
    ax1.legend()
    ax1.grid(True)
    
    # 添加颜色条
    cbar1 = plt.colorbar(scatter1, ax=ax1, shrink=0.5)
    cbar1.set_label('时间戳')
    
    plt.tight_layout()
    plt.show()
    
    # 打印航点信息和网格信息
    print(f"\n=== {channel_name} 航点信息 ===")
    print(f"航线ID: {route_id}")
    print(f"总航点数: {len(waypoints)}")
    print(f"基准时间: {base_time}")
    print(f"总时间跨度: {waypoints[-1]['time'] - waypoints[0]['time']:.2f} 秒")
    
    # 统计网格使用情况
    unique_grids = set(grid_codes)
    print(f"使用网格数: {len(unique_grids)}")
    
    print("\n航点详情:")
    prev_grid_code = None
    for i, wp in enumerate(waypoints):
        coord = wp['coordinates']
        grid_code = wp['grid_code']
        grid_change = " (网格变化)" if i > 0 and grid_code != prev_grid_code else ""
        prev_grid_code = grid_code
        
        distance_info = ""
        if i > 0:
            prev_coord = waypoints[i-1]['coordinates']
            dist = calculate_distance(prev_coord, coord)
            distance_info = f" (与前一点距离: {dist:.2f}m)"
            
        print(f"  {i+1}. ID:{wp['waypoint_id']}, 经度:{coord[0]:.6f}, 纬度:{coord[1]:.6f}, 高度:{coord[2]:.2f}m, "
              f"时间:{wp['time']:.2f}s, 网格:{grid_code}{grid_change}{distance_info}")

# 主函数
def main():
    # 读取JSON文件
    try:
        with open('./data/routes/route.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("未找到route.json文件，请确保文件路径正确")
        return
    except json.JSONDecodeError as e:
        print(f"JSON格式错误: {e}")
        return
    
    # 可视化采样后的3D航线（航道1）
    visualize_sampled_3d_with_grids(data, "航道1", level=11)

if __name__ == "__main__":
    main()
