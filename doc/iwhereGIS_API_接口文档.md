# iwhereGIS 网格数据引擎 API 接口文档

## 1. 概述

iwhereGIS网格数据引擎是一款专为无人机空域管理设计的三维网格数据引擎，提供16级网格编码、三维空间划分和空域属性管理功能。本文档详细说明了所有可用的API接口。

## 2. 核心类

### AirspaceGridManager
空域网格管理器，提供网格生成、查询、属性管理等核心功能。

```python
from airspace_grid.grid_manager import AirspaceGridManager

# 创建管理器实例
manager = AirspaceGridManager()
```

## 3. 网格生成接口

### generate_grids()
生成指定区域的网格单元。

**接口签名：**
```python
def generate_grids(self, lon_min: float, lon_max: float,
                  lat_min: float, lat_max: float,
                  level: int, alt_min: float = 0.0, 
                  alt_max: float = 1000) -> List[GridCell]
```

**参数说明：**
- `lon_min` (float): 最小经度 [-180, 180]
- `lon_max` (float): 最大经度 [-180, 180]
- `lat_min` (float): 最小纬度 [-90, 90]
- `lat_max` (float): 最大纬度 [-90, 90]
- `level` (int): 网格级别 [1-16]
- `alt_min` (float): 最小高程，默认0.0米
- `alt_max` (float): 最大高程，默认1000米

**返回值：**
- `List[GridCell]`: 生成的网格单元列表

**使用示例：**
```python
# 生成惠州空域8级网格
grids = manager.generate_grids(
    lon_min=113.7550, lon_max=114.6380,
    lat_min=22.4480, lat_max=22.8340,
    level=8, alt_min=0, alt_max=500
)
print(f"生成了 {len(grids)} 个网格单元")
```

**网格级别说明：**
| 级别 | 经度步长 | 纬度步长 | 物理尺寸(km) | 适用场景 |
|------|----------|----------|--------------|----------|
| 1 | 6° | 4° | 768×512 | 全球概览 |
| 2 | 3° | 2° | 384×256 | 区域规划 |
| 3 | 0.5° | 0.5° | 55.66×55.66 | 城市级 |
| 4 | 0.25° | 1/6° | 27.83×18.55 | 城区级 |
| 5 | 1/12° | 1/12° | 9.27×9.27 | 街区级 |
| 6 | 1/60° | 1/60° | 1.85×1.85 | 精确导航 |
| 7 | 1/300° | 1/300° | 0.371×0.371 | 高精度 |
| 8 | 1/900° | 1/900° | 0.124×0.124 | 超精度 |
| 9-16 | 递减 | 递减 | 更精细 | 特殊应用 |

## 4. 网格查询接口

### get_grid_by_code()
根据网格编码获取网格单元。

**接口签名：**
```python
def get_grid_by_code(self, code: str) -> Optional[GridCell]
```

**参数说明：**
- `code` (str): 网格编码字符串

**返回值：**
- `Optional[GridCell]`: 网格单元对象，不存在时返回None

**使用示例：**
```python
# 根据编码查询网格
grid = manager.get_grid_by_code("N01A001")
if grid:
    print(f"网格中心: {grid.center}")
    print(f"网格边界: {grid.bbox}")
    print(f"高程范围: {grid.alt_range}")
```

### get_grids_by_area()
根据地理区域获取网格单元。

**接口签名：**
```python
def get_grids_by_area(self, lon_min: float, lon_max: float,
                     lat_min: float, lat_max: float) -> List[GridCell]
```

**参数说明：**
- `lon_min` (float): 最小经度
- `lon_max` (float): 最大经度
- `lat_min` (float): 最小纬度
- `lat_max` (float): 最大纬度

**返回值：**
- `List[GridCell]`: 区域内的网格单元列表

**使用示例：**
```python
# 查询指定区域的网格
area_grids = manager.get_grids_by_area(
    lon_min=114.0, lon_max=114.2,
    lat_min=22.5, lat_max=22.7
)
print(f"区域内共有 {len(area_grids)} 个网格")
```

## 5. 坐标编码接口

### get_grid_code_by_coordinates()
根据经纬度、高程和级别获取网格编码。

**接口签名：**
```python
def get_grid_code_by_coordinates(self, lon: float, lat: float, 
                                alt: float, level: int) -> str
```

**参数说明：**
- `lon` (float): 经度 [-180, 180]
- `lat` (float): 纬度 [-90, 90]
- `alt` (float): 高程 (米)
- `level` (int): 网格级别 [1-16]

**返回值：**
- `str`: 网格编码字符串

**使用示例：**
```python
# 获取坐标对应的网格编码
code = manager.get_grid_code_by_coordinates(
    lon=114.1234, lat=22.5678, alt=100, level=8
)
print(f"网格编码: {code}")
```

**编码格式说明：**
- 格式：`[半球标识][网格编码][高程编码]`
- 示例：`N01A001H001` (北半球，01A001网格，高程100米)

## 6. 属性管理接口

### update_grid_attribute()
更新网格属性。

**接口签名：**
```python
def update_grid_attribute(self, grid_code: str, category: str, 
                         key: str, value: any) -> bool
```

**参数说明：**
- `grid_code` (str): 网格编码
- `category` (str): 属性类别
- `key` (str): 属性键名
- `value` (any): 属性值

**属性类别说明：**
- `flight_rules`: 飞行规则属性
- `airspace_status`: 空域状态属性
- `weather_conditions`: 气象环境属性
- `risk_assessment`: 风险评估属性
- `control_authority`: 管制权限属性
- `dynamic_updates`: 动态更新属性

**返回值：**
- `bool`: 更新成功返回True，失败返回False

**使用示例：**
```python
# 设置飞行限制
success = manager.update_grid_attribute(
    grid_code="N01A001",
    category="flight_rules",
    key="max_altitude",
    value=300
)

# 设置天气信息
success = manager.update_grid_attribute(
    grid_code="N01A001",
    category="weather_conditions",
    key="visibility",
    value="good"
)

# 设置风险评估
success = manager.update_grid_attribute(
    grid_code="N01A001",
    category="risk_assessment",
    key="risk_level",
    value="low"
)
```

### get_grid_attributes()
获取网格属性。

**接口签名：**
```python
def get_grid_attributes(self, grid_code: str) -> Optional[GridAttributes]
```

**参数说明：**
- `grid_code` (str): 网格编码

**返回值：**
- `Optional[GridAttributes]`: 网格属性对象

**使用示例：**
```python
# 获取网格属性
attrs = manager.get_grid_attributes("N01A001")
if attrs:
    print(f"飞行规则: {attrs.flight_rules}")
    print(f"天气条件: {attrs.weather_conditions}")
    print(f"风险评估: {attrs.risk_assessment}")
    print(f"最后更新: {attrs.last_updated}")
```

## 7. 路径规划接口

### calculate_route_grids()
计算航线经过的网格单元。

**接口签名：**
```python
def calculate_route_grids(self, waypoints: List[Tuple[float, float, float]], 
                         level: int = 8) -> Tuple[List[str], GridCell]
```

**参数说明：**
- `waypoints` (List[Tuple[float, float, float]]): 航点列表，每个航点为(经度, 纬度, 高程)
- `level` (int): 网格级别，默认8

**返回值：**
- `Tuple[List[str], GridCell]`: (网格编码列表, 示例网格单元)

**使用示例：**
```python
# 定义航点
waypoints = [
    (114.0, 22.5, 100),  # 起点
    (114.1, 22.6, 150),  # 中间点
    (114.2, 22.7, 200)   # 终点
]

# 计算路径网格
grid_codes, sample_grid = manager.calculate_route_grids(waypoints, level=8)
print(f"路径经过 {len(grid_codes)} 个网格")
for code in grid_codes:
    print(f"网格编码: {code}")
```

## 8. 数据导入导出接口

### export_to_json()
导出网格数据到JSON文件。

**接口签名：**
```python
def export_to_json(self, filename: str) -> None
```

**参数说明：**
- `filename` (str): 输出文件名

**使用示例：**
```python
# 导出网格数据
manager.export_to_json("airspace_grids.json")
print("网格数据已导出到 airspace_grids.json")
```

**导出格式：**
```json
{
  "grids": {
    "N01A001": {
      "level": 8,
      "bbox": [114.0, 22.5, 114.001, 22.501],
      "center": [114.0005, 22.5005],
      "size": {"lon": 0.124, "lat": 0.124, "unit": "km"},
      "code": "N01A001",
      "alt_range": [0, 100],
      "cellid": 1
    }
  },
  "attributes": {
    "N01A001": {
      "grid_code": "N01A001",
      "level": 8,
      "flight_rules": {"max_altitude": 300},
      "weather_conditions": {"visibility": "good"},
      "risk_assessment": {"risk_level": "low"}
    }
  }
}
```

### import_from_json()
从JSON文件导入网格数据。

**接口签名：**
```python
def import_from_json(self, filename: str) -> None
```

**参数说明：**
- `filename` (str): 输入文件名

**使用示例：**
```python
# 导入网格数据
manager.import_from_json("airspace_grids.json")
print("网格数据已从 airspace_grids.json 导入")
```

## 9. 辅助接口

### get_statistics()
获取网格统计信息。

**接口签名：**
```python
def get_statistics(self) -> Dict[str, any]
```

**返回值：**
- `Dict[str, any]`: 统计信息字典

**使用示例：**
```python
# 获取统计信息
stats = manager.get_statistics()
print(f"总网格数: {stats['total_grids']}")
print(f"级别分布: {stats['level_distribution']}")
```

### search_grids()
根据属性搜索网格。

**接口签名：**
```python
def search_grids(self, category: str, key: str, value: any) -> List[GridCell]
```

**参数说明：**
- `category` (str): 属性类别
- `key` (str): 属性键名
- `value` (any): 属性值

**返回值：**
- `List[GridCell]`: 匹配的网格单元列表

**使用示例：**
```python
# 搜索高风险区域
high_risk_grids = manager.search_grids(
    category="risk_assessment",
    key="risk_level",
    value="high"
)
print(f"找到 {len(high_risk_grids)} 个高风险网格")

# 搜索低能见度区域
low_visibility_grids = manager.search_grids(
    category="weather_conditions",
    key="visibility",
    value="poor"
)
print(f"找到 {len(low_visibility_grids)} 个低能见度网格")
```

## 10. 错误处理

### 常见错误码
- `ValueError`: 参数值无效（如坐标超出范围、级别不在1-16之间）
- `FileNotFoundError`: 文件不存在（导入导出时）
- `KeyError`: 网格编码不存在
- `TypeError`: 参数类型错误

### 错误处理示例
```python
try:
    grids = manager.generate_grids(
        lon_min=200, lon_max=210,  # 经度超出范围
        lat_min=22.5, lat_max=22.7,
        level=8
)
except ValueError as e:
    print(f"参数错误: {e}")

try:
    grid = manager.get_grid_by_code("INVALID_CODE")
    if grid is None:
        print("网格编码不存在")
except Exception as e:
    print(f"查询错误: {e}")
```

## 11. 性能优化建议

1. **批量操作**: 对于大量网格操作，建议使用批量接口
2. **缓存策略**: 频繁查询的网格可以缓存到内存中
3. **级别选择**: 根据应用场景选择合适的网格级别
4. **内存管理**: 大规模网格生成时注意内存使用

## 12. 完整使用示例

```python
from airspace_grid.grid_manager import AirspaceGridManager

# 创建管理器
manager = AirspaceGridManager()

# 1. 生成网格
grids = manager.generate_grids(
    lon_min=114.0, lon_max=114.1,
    lat_min=22.5, lat_max=22.6,
    level=8, alt_min=0, alt_max=500
)

# 2. 设置属性
for grid in grids[:5]:  # 为前5个网格设置属性
    manager.update_grid_attribute(
        grid.code, "flight_rules", "max_altitude", 300
    )
    manager.update_grid_attribute(
        grid.code, "weather_conditions", "visibility", "good"
    )

# 3. 查询网格
grid = manager.get_grid_by_code(grids[0].code)
print(f"网格中心: {grid.center}")

# 4. 路径规划
waypoints = [(114.05, 22.55, 100), (114.08, 22.58, 150)]
route_grids, _ = manager.calculate_route_grids(waypoints, level=8)

# 5. 导出数据
manager.export_to_json("my_airspace.json")

# 6. 获取统计
stats = manager.get_statistics()
print(f"总网格数: {stats['total_grids']}")
```

---

**版本**: V1.2.4  
**更新时间**: 2024年  
**技术支持**: iwhereGIS团队 