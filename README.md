# iwhereGIS 网格数据引擎

## 项目概述

iwhereGIS 网格数据引擎是一个高性能的空域网格管理系统，支持网格生成、编码解码、属性管理、搜索查询和航线规划等功能。本项目为无人机低空飞行服务提供精确的空域管理解决方案。

## 功能特性

- **网格生成**: 支持多级别网格生成，从1级到16级精度
- **坐标编码**: 高效的经纬度坐标到网格编码转换
- **属性管理**: 灵活的网格属性管理，支持飞行规则、天气条件、风险评估等
- **搜索查询**: 基于属性的高级搜索功能
- **航线规划**: 智能航线网格计算
- **HTTP API**: 完整的RESTful API接口
- **数据导入导出**: 支持JSON格式数据交换

## 快速开始

### 1. 环境要求

- Python 3.7+
- 操作系统: Windows, Linux, macOS

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行测试

```bash
# 运行完整功能测试
python main.py

# 运行API测试
python test_api.py
```

### 4. 启动API服务器

```bash
# 方法1: 直接启动
python api_server.py

# 方法2: 使用启动脚本
python start_api.py

# 方法3: Windows用户双击
start_api.bat
```

## 项目结构

```
MyFirstProject/
├── airspace_grid/          # 核心网格引擎模块
│   ├── grid_core.py        # 网格核心功能
│   ├── grid_manager.py     # 网格管理器
│   ├── grid_encode.py      # 编码功能
│   ├── grid_decode.py      # 解码功能
│   ├── grid_attributes.py  # 属性管理
│   └── __init__.py
├── api_server.py           # HTTP API服务器
├── test_api.py             # API测试脚本
├── main.py                 # 主测试程序
├── requirements.txt        # Python依赖
├── README_API.md           # API使用文档
├── API_TEST.md             # API测试文档
├── start_api.py            # 启动脚本
├── start_api.bat           # Windows启动脚本
└── test_api.bat            # Windows测试脚本
```

## API接口

### 基础接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/statistics` | GET | 获取统计信息 |

### 网格管理接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/grids/generate` | POST | 生成网格 |
| `/api/grids/{code}` | GET | 查询网格 |
| `/api/grids/encode` | POST | 坐标编码 |
| `/api/grids/search` | POST | 搜索网格 |

### 属性管理接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/grids/{code}/attributes` | GET | 获取网格属性 |
| `/api/grids/{code}/attributes` | PUT | 更新网格属性 |

### 航线规划接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/grids/route` | POST | 计算航线网格 |

## 使用示例

### 1. 生成网格

```python
from airspace_grid.grid_manager import AirspaceGridManager

manager = AirspaceGridManager()
grids = manager.generate_grids(
    lon_min=114.0, lon_max=114.001,
    lat_min=22.5, lat_max=22.501,
    level=8, alt_min=0, alt_max=100
)
print(f"生成了 {len(grids)} 个网格")
```

### 2. 坐标编码

```python
grid_code = manager.get_grid_code_by_coordinates(
    lon=114.1234, lat=22.5678, alt=100, level=8
)
print(f"网格编码: {grid_code}")
```

### 3. 属性管理

```python
# 更新飞行规则
manager.update_grid_attribute(
    grid_code, "flight_rules", "max_altitude", 300
)

# 获取属性
attrs = manager.get_grid_attributes(grid_code)
print(f"最大高度: {attrs.flight_rules.get('max_altitude')}")
```

### 4. 航线规划

```python
waypoints = [
    (114.05, 22.55, 100),  # 起点
    (114.08, 22.58, 150)   # 终点
]
grid_codes, sample_grid = manager.calculate_route_grids(waypoints, level=8)
print(f"航线经过 {len(grid_codes)} 个网格")
```

## HTTP API使用

### 启动服务器

```bash
python api_server.py
```

### 测试API

```bash
# 健康检查
curl http://localhost:5000/api/health

# 生成网格
curl -X POST http://localhost:5000/api/grids/generate \
  -H "Content-Type: application/json" \
  -d '{
    "lon_min": 114.0,
    "lon_max": 114.001,
    "lat_min": 22.5,
    "lat_max": 22.501,
    "level": 8
  }'
```

详细API文档请参考 [README_API.md](README_API.md)

## 测试

### 功能测试

```bash
python main.py
```

### API测试

```bash
python test_api.py
```

### 自动化测试

```bash
# Windows
test_api.bat

# Linux/Mac
python start_api.py test
```

## 部署

### 开发环境

```bash
python api_server.py
```

### 生产环境

```bash
# 使用 gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app

# 使用 uwsgi
pip install uwsgi
uwsgi --http 0.0.0.0:5000 --module api_server:app --processes 4
```

### Docker部署

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "api_server.py"]
```

## 性能指标

- 网格生成速度: 1000+ 网格/秒
- 查询响应时间: < 10ms
- 编码解码速度: < 1ms
- 支持并发访问: 100+ 并发用户

## 开发指南

### 代码规范

- 使用Python 3.7+语法
- 遵循PEP 8代码风格
- 添加类型注解
- 编写单元测试

### 贡献流程

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 文档: [README_API.md](README_API.md)

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持基础网格功能
- 提供HTTP API接口
- 完整的测试套件 