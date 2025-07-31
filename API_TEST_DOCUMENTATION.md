# iwhereGIS 网格数据引擎 HTTP API 测试文档

## 概述

本文档提供了 iwhereGIS 网格数据引擎 HTTP API 的完整测试指南，包括所有接口的测试用例、请求示例和预期响应。

## 基础信息

- **服务器地址**: `http://localhost:5000`
- **API版本**: 1.0.0
- **内容类型**: `application/json`

## 1. 健康检查接口

### 接口信息
- **URL**: `/api/health`
- **方法**: `GET`
- **描述**: 检查API服务器状态

### 测试用例

#### 1.1 正常健康检查
```bash
curl -X GET http://localhost:5000/api/health
```

**预期响应**:
```json
{
  "status": "healthy",
  "service": "iwhereGIS Grid Engine API",
  "version": "1.0.0"
}
```

## 2. 网格生成接口

### 接口信息
- **URL**: `/api/grids/generate`
- **方法**: `POST`
- **描述**: 生成指定区域的网格

### 测试用例

#### 2.1 基本网格生成
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

**预期响应**:
```json
{
  "success": true,
  "message": "成功生成 X 个网格",
  "data": {
    "grids": [
      {
        "code": "网格编码",
        "level": 8,
        "bbox": [114.0, 22.5, 114.001, 22.501],
        "center": [114.0005, 22.5005],
        "size": {"lon": 0.12369, "lat": 0.12369, "unit": "km"},
        "alt_range": [0.0, 100.0]
      }
    ],
    "count": 1
  }
}
```

#### 2.2 大区域网格生成
```bash
curl -X POST http://localhost:5000/api/grids/generate \
  -H "Content-Type: application/json" \
  -d '{
    "lon_min": 114.0,
    "lon_max": 114.01,
    "lat_min": 22.5,
    "lat_max": 22.51,
    "level": 6,
    "alt_min": 0,
    "alt_max": 500
  }'
```

#### 2.3 参数错误测试
```bash
curl -X POST http://localhost:5000/api/grids/generate \
  -H "Content-Type: application/json" \
  -d '{
    "lon_min": 114.0,
    "lat_min": 22.5,
    "level": 8
  }'
```

**预期响应**:
```json
{
  "error": "缺少必需参数: lon_max"
}
```

## 3. 网格查询接口

### 接口信息
- **URL**: `/api/grids/{grid_code}`
- **方法**: `GET`
- **描述**: 根据网格编码获取网格信息

### 测试用例

#### 3.1 查询存在的网格
```bash
# 先生成网格获取编码
curl -X POST http://localhost:5000/api/grids/generate \
  -H "Content-Type: application/json" \
  -d '{
    "lon_min": 114.0,
    "lon_max": 114.001,
    "lat_min": 22.5,
    "lat_max": 22.501,
    "level": 8
  }'

# 使用返回的编码查询
curl -X GET http://localhost:5000/api/grids/GRID_CODE_HERE
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "code": "网格编码",
    "level": 8,
    "bbox": [114.0, 22.5, 114.001, 22.501],
    "center": [114.0005, 22.5005],
    "size": {"lon": 0.12369, "lat": 0.12369, "unit": "km"},
    "alt_range": [0.0, 1000.0]
  }
}
```

#### 3.2 查询不存在的网格
```bash
curl -X GET http://localhost:5000/api/grids/INVALID_CODE
```

**预期响应**:
```json
{
  "error": "未找到网格: INVALID_CODE"
}
```

## 4. 坐标编码接口

### 接口信息
- **URL**: `/api/grids/encode`
- **方法**: `POST`
- **描述**: 根据坐标获取网格编码

### 测试用例

#### 4.1 基本坐标编码
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

**预期响应**:
```json
{
  "success": true,
  "data": {
    "grid_code": "编码结果"
  }
}
```

#### 4.2 不同级别的编码
```bash
curl -X POST http://localhost:5000/api/grids/encode \
  -H "Content-Type: application/json" \
  -d '{
    "lon": 114.1234,
    "lat": 22.5678,
    "alt": 100,
    "level": 6
  }'
```

## 5. 网格属性管理接口

### 接口信息
- **URL**: `/api/grids/{grid_code}/attributes`
- **方法**: `GET` / `PUT`
- **描述**: 获取和更新网格属性

### 测试用例

#### 5.1 获取网格属性
```bash
curl -X GET http://localhost:5000/api/grids/GRID_CODE_HERE/attributes
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "grid_code": "网格编码",
    "flight_rules": {},
    "airspace_status": {},
    "weather_conditions": {},
    "risk_assessment": {}
  }
}
```

#### 5.2 更新飞行规则属性
```bash
curl -X PUT http://localhost:5000/api/grids/GRID_CODE_HERE/attributes \
  -H "Content-Type: application/json" \
  -d '{
    "category": "flight_rules",
    "key": "max_altitude",
    "value": 300
  }'
```

**预期响应**:
```json
{
  "success": true,
  "message": "属性更新成功"
}
```

#### 5.3 更新天气条件属性
```bash
curl -X PUT http://localhost:5000/api/grids/GRID_CODE_HERE/attributes \
  -H "Content-Type: application/json" \
  -d '{
    "category": "weather_conditions",
    "key": "visibility",
    "value": "good"
  }'
```

#### 5.4 更新风险评估属性
```bash
curl -X PUT http://localhost:5000/api/grids/GRID_CODE_HERE/attributes \
  -H "Content-Type: application/json" \
  -d '{
    "category": "risk_assessment",
    "key": "risk_level",
    "value": "low"
  }'
```

## 6. 网格搜索接口

### 接口信息
- **URL**: `/api/grids/search`
- **方法**: `POST`
- **描述**: 根据属性搜索网格

### 测试用例

#### 6.1 搜索高风险网格
```bash
curl -X POST http://localhost:5000/api/grids/search \
  -H "Content-Type: application/json" \
  -d '{
    "category": "risk_assessment",
    "key": "risk_level",
    "value": "high"
  }'
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "grids": [
      {
        "code": "网格编码",
        "level": 8,
        "bbox": [114.0, 22.5, 114.001, 22.501],
        "center": [114.0005, 22.5005]
      }
    ],
    "count": 1
  }
}
```

#### 6.2 搜索低能见度网格
```bash
curl -X POST http://localhost:5000/api/grids/search \
  -H "Content-Type: application/json" \
  -d '{
    "category": "weather_conditions",
    "key": "visibility",
    "value": "poor"
  }'
```

## 7. 航线规划接口

### 接口信息
- **URL**: `/api/grids/route`
- **方法**: `POST`
- **描述**: 计算航线经过的网格

### 测试用例

#### 7.1 简单航线规划
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

**预期响应**:
```json
{
  "success": true,
  "data": {
    "grid_codes": ["编码1", "编码2", "编码3"],
    "count": 3,
    "waypoints": [
      [114.05, 22.55, 100],
      [114.08, 22.58, 150]
    ],
    "level": 8
  }
}
```

#### 7.2 多点航线规划
```bash
curl -X POST http://localhost:5000/api/grids/route \
  -H "Content-Type: application/json" \
  -d '{
    "waypoints": [
      [114.05, 22.55, 100],
      [114.06, 22.56, 120],
      [114.07, 22.57, 140],
      [114.08, 22.58, 150]
    ],
    "level": 8
  }'
```

## 8. 统计信息接口

### 接口信息
- **URL**: `/api/statistics`
- **方法**: `GET`
- **描述**: 获取网格统计信息

### 测试用例

#### 8.1 获取统计信息
```bash
curl -X GET http://localhost:5000/api/statistics
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "total_grids": 100,
    "level_distribution": {
      "6": 50,
      "8": 50
    }
  }
}
```

## 9. 完整测试流程

### 9.1 端到端测试流程

```bash
#!/bin/bash

echo "开始 iwhereGIS API 端到端测试..."

# 1. 健康检查
echo "1. 健康检查..."
curl -s http://localhost:5000/api/health | jq .

# 2. 生成网格
echo "2. 生成网格..."
GRID_RESPONSE=$(curl -s -X POST http://localhost:5000/api/grids/generate \
  -H "Content-Type: application/json" \
  -d '{
    "lon_min": 114.0,
    "lon_max": 114.001,
    "lat_min": 22.5,
    "lat_max": 22.501,
    "level": 8
  }')

echo $GRID_RESPONSE | jq .

# 3. 获取网格编码
GRID_CODE=$(echo $GRID_RESPONSE | jq -r '.data.grids[0].code')
echo "网格编码: $GRID_CODE"

# 4. 查询网格
echo "3. 查询网格..."
curl -s http://localhost:5000/api/grids/$GRID_CODE | jq .

# 5. 更新属性
echo "4. 更新属性..."
curl -s -X PUT http://localhost:5000/api/grids/$GRID_CODE/attributes \
  -H "Content-Type: application/json" \
  -d '{
    "category": "flight_rules",
    "key": "max_altitude",
    "value": 300
  }' | jq .

# 6. 获取属性
echo "5. 获取属性..."
curl -s http://localhost:5000/api/grids/$GRID_CODE/attributes | jq .

# 7. 搜索网格
echo "6. 搜索网格..."
curl -s -X POST http://localhost:5000/api/grids/search \
  -H "Content-Type: application/json" \
  -d '{
    "category": "flight_rules",
    "key": "max_altitude",
    "value": 300
  }' | jq .

# 8. 航线规划
echo "7. 航线规划..."
curl -s -X POST http://localhost:5000/api/grids/route \
  -H "Content-Type: application/json" \
  -d '{
    "waypoints": [
      [114.05, 22.55, 100],
      [114.08, 22.58, 150]
    ],
    "level": 8
  }' | jq .

# 9. 获取统计
echo "8. 获取统计..."
curl -s http://localhost:5000/api/statistics | jq .

echo "端到端测试完成！"
```

## 10. 性能测试

### 10.1 批量网格生成测试
```bash
# 测试大区域网格生成性能
time curl -X POST http://localhost:5000/api/grids/generate \
  -H "Content-Type: application/json" \
  -d '{
    "lon_min": 114.0,
    "lon_max": 114.1,
    "lat_min": 22.5,
    "lat_max": 22.6,
    "level": 8
  }'
```

### 10.2 并发查询测试
```bash
# 使用 ab 工具进行并发测试
ab -n 100 -c 10 http://localhost:5000/api/health
```

## 11. 错误处理测试

### 11.1 参数验证测试
```bash
# 测试缺少必需参数
curl -X POST http://localhost:5000/api/grids/generate \
  -H "Content-Type: application/json" \
  -d '{}'

# 测试无效参数类型
curl -X POST http://localhost:5000/api/grids/generate \
  -H "Content-Type: application/json" \
  -d '{
    "lon_min": "invalid",
    "lon_max": 114.001,
    "lat_min": 22.5,
    "lat_max": 22.501,
    "level": 8
  }'
```

### 11.2 边界值测试
```bash
# 测试超出范围的坐标
curl -X POST http://localhost:5000/api/grids/generate \
  -H "Content-Type: application/json" \
  -d '{
    "lon_min": 200,
    "lon_max": 210,
    "lat_min": 22.5,
    "lat_max": 22.501,
    "level": 8
  }'
```

## 12. 测试工具推荐

### 12.1 命令行工具
- **curl**: 基础HTTP请求测试
- **jq**: JSON响应格式化
- **ab**: Apache Bench 性能测试

### 12.2 GUI工具
- **Postman**: 完整的API测试工具
- **Insomnia**: 轻量级API客户端
- **Swagger UI**: API文档和测试界面

### 12.3 自动化测试
- **Python requests**: 自动化测试脚本
- **pytest**: 单元测试框架
- **JMeter**: 性能测试工具

## 13. 常见问题

### 13.1 连接问题
- 确保API服务器已启动
- 检查端口5000是否被占用
- 验证防火墙设置

### 13.2 参数问题
- 确保所有必需参数都已提供
- 检查参数类型是否正确
- 验证坐标范围是否有效

### 13.3 性能问题
- 大区域网格生成可能需要较长时间
- 考虑使用较低级别的网格进行测试
- 监控服务器资源使用情况

## 14. 测试报告模板

```markdown
# API测试报告

## 测试环境
- 服务器: localhost:5000
- 测试时间: YYYY-MM-DD HH:MM:SS
- 测试工具: curl/jq

## 测试结果
| 接口 | 状态 | 响应时间 | 备注 |
|------|------|----------|------|
| /api/health | ✅ | 50ms | 正常 |
| /api/grids/generate | ✅ | 200ms | 正常 |
| /api/grids/{code} | ✅ | 30ms | 正常 |
| ... | ... | ... | ... |

## 性能指标
- 平均响应时间: XXXms
- 最大响应时间: XXXms
- 成功率: XX%

## 问题记录
1. 问题描述
2. 解决方案
3. 状态

## 建议
1. 优化建议
2. 功能建议
3. 文档建议
```

---

**注意**: 在实际测试前，请确保：
1. API服务器已启动 (`python api_server.py`)
2. 所有依赖已安装 (`pip install flask flask-cors`)
3. 网络连接正常
4. 测试环境配置正确 