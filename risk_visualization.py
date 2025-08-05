import requests
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

def visualize_risk_map(polygon, api_url='http://127.0.0.1:9010/risk/by_polygon'):
    # polygon: [(lon, lat, alt), ...]
    resp = requests.post(api_url, json={'polygon': polygon})
    data = resp.json()
    results = data['results']
    print(results)
    # 画图
    lons = []
    lats = []
    risks = []
    for item in results:
        code = item['code']
        risk = item['risk']
        # 解析网格中心点
        from airspace_grid import grid_decode
        result = grid_decode.decode_grid(code)
        lons.append(result.center[0])
        lats.append(result.center[1])
        risks.append(risk)
    plt.figure(figsize=(8, 6))
    scatter = plt.scatter(lons, lats, c=risks, cmap='RdYlGn_r', s=40, marker='s')
    plt.colorbar(scatter, label='Risk Level')
    plt.title('Risk Map (Level 11 Grid)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    # 图例
    legend_elements = [Patch(facecolor=plt.cm.RdYlGn_r(i/4), label=f'Level {i+1}') for i in range(5)]
    plt.legend(handles=legend_elements, title='Risk Level', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    # 深圳某区域示例
    polygon = [
        [114.05, 22.52, 10],
        [114.10, 22.52, 10],
        [114.10, 22.56, 10],
        [114.05, 22.56, 10],
        [114.05, 22.52, 10]
    ]
    visualize_risk_map(polygon)
