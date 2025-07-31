#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iwhereGIS 网格数据引擎 HTTP API 服务器
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from airspace_grid.grid_manager import AirspaceGridManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

grid_manager = AirspaceGridManager()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "iwhereGIS Grid Engine API",
        "version": "1.0.0"
    })

@app.route('/api/grids/generate', methods=['POST'])
def generate_grids():
    try:
        data = request.get_json()
        required_fields = ['lon_min', 'lon_max', 'lat_min', 'lat_max', 'level']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"缺少必需参数: {field}"}), 400
        
        grids = grid_manager.generate_grids(
            lon_min=float(data['lon_min']), lon_max=float(data['lon_max']),
            lat_min=float(data['lat_min']), lat_max=float(data['lat_max']),
            level=int(data['level']), 
            alt_min=float(data.get('alt_min', 0.0)),
            alt_max=float(data.get('alt_max', 1000.0))
        )
        
        grid_list = [{
            "code": grid.code,
            "level": grid.level,
            "bbox": grid.bbox,
            "center": grid.center,
            "size": grid.size,
            "alt_range": grid.alt_range
        } for grid in grids]
        
        return jsonify({
            "success": True,
            "message": f"成功生成 {len(grids)} 个网格",
            "data": {"grids": grid_list, "count": len(grids)}
        })
        
    except Exception as e:
        logger.error(f"生成网格失败: {str(e)}")
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

@app.route('/api/grids/<grid_code>', methods=['GET'])
def get_grid_by_code(grid_code: str):
    try:
        grid = grid_manager.get_grid_by_code(grid_code)
        if grid is None:
            return jsonify({"error": f"未找到网格: {grid_code}"}), 404
        
        return jsonify({
            "success": True,
            "data": {
                "code": grid.code,
                "level": grid.level,
                "bbox": grid.bbox,
                "center": grid.center,
                "size": grid.size,
                "alt_range": grid.alt_range
            }
        })
    except Exception as e:
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

@app.route('/api/grids/encode', methods=['POST'])
def encode_coordinates():
    try:
        data = request.get_json()
        required_fields = ['lon', 'lat', 'alt', 'level']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"缺少必需参数: {field}"}), 400
        
        grid_code = grid_manager.get_grid_code_by_coordinates(
            lon=float(data['lon']), lat=float(data['lat']),
            alt=float(data['alt']), level=int(data['level'])
        )
        
        return jsonify({
            "success": True,
            "data": {"grid_code": grid_code}
        })
    except Exception as e:
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

@app.route('/api/grids/<grid_code>/attributes', methods=['GET'])
def get_grid_attributes(grid_code: str):
    try:
        attrs = grid_manager.get_grid_attributes(grid_code)
        if attrs is None:
            return jsonify({"error": f"未找到网格属性: {grid_code}"}), 404
        
        return jsonify({
            "success": True,
            "data": {
                "grid_code": attrs.grid_code,
                "flight_rules": attrs.flight_rules,
                "airspace_status": attrs.airspace_status,
                "weather_conditions": attrs.weather_conditions,
                "risk_assessment": attrs.risk_assessment
            }
        })
    except Exception as e:
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

@app.route('/api/grids/<grid_code>/attributes', methods=['PUT'])
def update_grid_attribute(grid_code: str):
    try:
        data = request.get_json()
        required_fields = ['category', 'key', 'value']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"缺少必需参数: {field}"}), 400
        
        success = grid_manager.update_grid_attribute(
            grid_code=grid_code,
            category=data['category'],
            key=data['key'],
            value=data['value']
        )
        
        if not success:
            return jsonify({"error": f"更新属性失败: {grid_code}"}), 400
        
        return jsonify({
            "success": True,
            "message": "属性更新成功"
        })
    except Exception as e:
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

@app.route('/api/grids/search', methods=['POST'])
def search_grids():
    try:
        data = request.get_json()
        required_fields = ['category', 'key', 'value']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"缺少必需参数: {field}"}), 400
        
        grids = grid_manager.search_grids(
            category=data['category'],
            key=data['key'],
            value=data['value']
        )
        
        grid_list = [{
            "code": grid.code,
            "level": grid.level,
            "bbox": grid.bbox,
            "center": grid.center
        } for grid in grids]
        
        return jsonify({
            "success": True,
            "data": {"grids": grid_list, "count": len(grids)}
        })
    except Exception as e:
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

@app.route('/api/grids/route', methods=['POST'])
def calculate_route_grids():
    try:
        data = request.get_json()
        if 'waypoints' not in data:
            return jsonify({"error": "缺少必需参数: waypoints"}), 400
        
        waypoints = [(float(p[0]), float(p[1]), float(p[2])) for p in data['waypoints']]
        level = int(data.get('level', 8))
        
        grid_codes, sample_grid = grid_manager.calculate_route_grids(
            waypoints=waypoints, level=level
        )
        
        return jsonify({
            "success": True,
            "data": {
                "grid_codes": grid_codes,
                "count": len(grid_codes),
                "waypoints": data['waypoints'],
                "level": level
            }
        })
    except Exception as e:
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    try:
        stats = grid_manager.get_statistics()
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

if __name__ == '__main__':
    print("iwhereGIS 网格数据引擎 HTTP API 服务器启动中...")
    app.run(host='0.0.0.0', port=5000, debug=True) 