# 风险评估API与可视化使用说明

1. 启动风险评估API服务：

```bash
python risk_api.py
```

2. 查询接口示例：

- 按网格编码：
  GET http://127.0.0.1:9010/risk/by_code?code=xxxx
- 按经纬度高程：
  GET http://127.0.0.1:9010/risk/by_coord?lon=114.05&lat=22.55&alt=10
- 按区域多边形：
  POST http://127.0.0.1:9010/risk/by_polygon
  Body: {"polygon": [[114.05,22.52,10],[114.10,22.52,10],[114.10,22.56,10],[114.05,22.56,10],[114.05,22.52,10]]}

3. 可视化风险地图：

```bash
python risk_visualization.py
```

可根据需要修改 `risk_visualization.py` 中的 polygon 区域。

---

如需集成到前端3D可视化，可将 `/risk/by_polygon` 的结果转为GeoJSON或直接渲染。
