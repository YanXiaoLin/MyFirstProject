# iwhereGIS 网格数据引擎 HTTP API 使用指南

## 概述

本项目为 iwhereGIS 网格数据引擎提供了完整的 HTTP API 接口，支持网格生成、查询、属性管理、搜索和航线规划等功能。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动API服务器

```bash
python api_server.py
```

服务器将在 `http://localhost:5000` 启动。

### 3. 测试API

```bash
python test_api.py
```

## API接口列表

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

## 详细使用示例

### 1. 生成网格

```bash
curl -X POST http://localhost:5000/api/grids/generate \
  -H "Content-Type: application/json" \
  -d '{
    "lon_min": 114.0,
    "lon_max": 114.001,
    "lat_min": 22.5,
    "lat_max": 22.501,
    "level": 8,
    "alt_min": 0,
    "alt_max": 100
  }'
```

### 2. 查询网格

```bash
curl http://localhost:5000/api/grids/GRID_CODE_HERE
```

### 3. 坐标编码

```bash
curl -X POST http://localhost:5000/api/grids/encode \
  -H "Content-Type: application/json" \
  -d '{
    "lon": 114.1234,
    "lat": 22.5678,
    "alt": 100,
    "level": 8
  }'
```

### 4. 更新网格属性

```bash
curl -X PUT http://localhost:5000/api/grids/GRID_CODE_HERE/attributes \
  -H "Content-Type: application/json" \
  -d '{
    "category": "flight_rules",
    "key": "max_altitude",
    "value": 300
  }'
```

### 5. 搜索网格

```bash
curl -X POST http://localhost:5000/api/grids/search \
  -H "Content-Type: application/json" \
  -d '{
    "category": "flight_rules",
    "key": "max_altitude",
    "value": 300
  }'
```

### 6. 航线规划

```bash
curl -X POST http://localhost:5000/api/grids/route \
  -H "Content-Type: application/json" \
  -d '{
    "waypoints": [
      [114.05, 22.55, 100],
      [114.08, 22.58, 150]
    ],
    "level": 8
  }'
```

## 响应格式

所有API接口都返回统一的JSON格式：

### 成功响应

```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    // 具体数据
  }
}
```

### 错误响应

```json
{
  "error": "错误描述"
}
```

## 参数说明

### 网格生成参数

- `lon_min`, `lon_max`: 经度范围 (-180 到 180)
- `lat_min`, `lat_max`: 纬度范围 (-90 到 90)
- `level`: 网格级别 (1-16)
- `alt_min`, `alt_max`: 高度范围 (可选)

### 坐标编码参数

- `lon`: 经度
- `lat`: 纬度
- `alt`: 高度
- `level`: 网格级别

### 属性更新参数

- `category`: 属性类别 (flight_rules, weather_conditions, risk_assessment 等)
- `key`: 属性键
- `value`: 属性值

### 航线规划参数

- `waypoints`: 航点列表，每个航点为 [lon, lat, alt]
- `level`: 网格级别

## 错误代码

- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

## 性能建议

1. 大区域网格生成时建议使用较低级别 (6-8)
2. 频繁查询时可以使用缓存
3. 批量操作时考虑使用会话保持

## 开发环境

- Python 3.7+
- Flask 2.3.3
- Flask-CORS 4.0.0

## 测试

运行完整测试套件：

```bash
python test_api.py
```

查看详细测试文档：

```bash
cat API_TEST.md
```

## 部署

### 生产环境部署

```bash
# 使用 gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app

# 使用 uwsgi
pip install uwsgi
uwsgi --http 0.0.0.0:5000 --module api_server:app --processes 4
```

### Docker 部署

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "api_server.py"]
```

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 许可证

本项目采用 MIT 许可证。 