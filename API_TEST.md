# iwhereGIS 网格数据引擎 HTTP API 测试文档

## 服务器启动
```bash
python api_server.py
```

## 1. 健康检查
```bash
curl http://localhost:5000/api/health
```

## 2. 生成网格
```bash
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

## 3. 查询网格
```bash
curl http://localhost:5000/api/grids/GRID_CODE_HERE
```

## 4. 坐标编码
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

## 5. 更新属性
```bash
curl -X PUT http://localhost:5000/api/grids/GRID_CODE_HERE/attributes \
  -H "Content-Type: application/json" \
  -d '{
    "category": "flight_rules",
    "key": "max_altitude",
    "value": 300
  }'
```

## 6. 搜索网格
```bash
curl -X POST http://localhost:5000/api/grids/search \
  -H "Content-Type: application/json" \
  -d '{
    "category": "flight_rules",
    "key": "max_altitude",
    "value": 300
  }'
```

## 7. 航线规划
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

## 8. 统计信息
```bash
curl http://localhost:5000/api/statistics
``` 