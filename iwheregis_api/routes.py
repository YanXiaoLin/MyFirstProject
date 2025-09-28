"""Flask routes (Blueprint) for the iwhereGIS Grid Engine API."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List

from flask import Blueprint, current_app, jsonify, request, send_from_directory


bp = Blueprint("api", __name__)


def _grid_manager():
    return current_app.config["GRID_MANAGER"]


@bp.route("/", methods=["GET"]) 
def index():
    return current_app.send_static_file("index.html")


@bp.route("/<path:filename>", methods=["GET"]) 
def static_files(filename: str):
    static_dir = current_app.static_folder or str(Path(current_app.config["PROJECT_ROOT"]) / "static")
    return send_from_directory(static_dir, filename)


@bp.route("/api/health", methods=["GET"]) 
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "iwhereGIS Grid Engine API",
        "version": "1.0.0"
    })


@bp.route("/api/grids/<grid_code>/risk", methods=["GET"]) 
def get_grid_risk(grid_code: str):
    try:
        from risk_assessment import risk_by_code  # lazy import to avoid heavy deps at startup
        risk = risk_by_code(grid_code)
        return jsonify({"success": True, "grid_code": grid_code, "risk_level": risk})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"服务器内部错误: {str(exc)}"}), 500


@bp.route("/api/grids/generate", methods=["POST"]) 
def generate_grids():
    try:
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        required_fields = ["lon_min", "lon_max", "lat_min", "lat_max", "level"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"缺少必需参数: {field}"}), 400

        grids = _grid_manager().generate_grids(
            lon_min=float(data["lon_min"]), lon_max=float(data["lon_max"]),
            lat_min=float(data["lat_min"]), lat_max=float(data["lat_max"]),
            level=int(data["level"]),
            alt_min=float(data.get("alt_min", 0.0)),
            alt_max=float(data.get("alt_max", 1000.0)),
        )

        grid_list = [{
            "code": grid.code,
            "level": grid.level,
            "bbox": grid.bbox,
            "center": grid.center,
            "size": grid.size,
            "alt_range": grid.alt_range,
        } for grid in grids]

        return jsonify({
            "success": True,
            "message": f"成功生成 {len(grids)} 个网格",
            "data": {"grids": grid_list, "count": len(grids)},
        })
    except Exception as exc:  # noqa: BLE001
        current_app.logger.exception("生成网格失败")
        return jsonify({"error": f"服务器内部错误: {str(exc)}"}), 500


@bp.route("/api/grids/<grid_code>", methods=["GET"]) 
def get_grid_by_code(grid_code: str):
    try:
        decoded = _grid_manager().get_grid_by_code(grid_code)
        if decoded is None:
            return jsonify({"error": f"未找到网格: {grid_code}"}), 404

        min_lon = decoded.bounds.get("min_lon", 0.0)
        max_lon = decoded.bounds.get("max_lon", 0.0)
        min_lat = decoded.bounds.get("min_lat", 0.0)
        max_lat = decoded.bounds.get("max_lat", 0.0)

        bbox = [min_lon, min_lat, max_lon, max_lat]
        center = decoded.center
        alt_range = decoded.alt_range

        # Approximate grid size in kilometers based on center latitude
        # 1 degree latitude ~ 111.32 km; 1 degree longitude ~ 111.32 * cos(lat)
        lat_km_per_deg = 111.32
        lon_km_per_deg = 111.32 * math.cos(math.radians(center[1])) if center else 111.32
        size = {
            "lon": round((max_lon - min_lon) * lon_km_per_deg, 5),
            "lat": round((max_lat - min_lat) * lat_km_per_deg, 5),
            "unit": "km",
        }

        return jsonify({
            "success": True,
            "data": {
                "code": grid_code,
                "level": decoded.level,
                "bbox": bbox,
                "center": center,
                "size": size,
                "alt_range": alt_range,
            },
        })
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"服务器内部错误: {str(exc)}"}), 500


@bp.route("/api/grids/encode", methods=["POST"]) 
def encode_coordinates():
    try:
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        required_fields = ["lon", "lat", "alt", "level"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"缺少必需参数: {field}"}), 400

        grid_code = _grid_manager().get_grid_code_by_coordinates(
            lon=float(data["lon"]), lat=float(data["lat"]),
            alt=float(data["alt"]), level=int(data["level"]),
        )

        return jsonify({"success": True, "data": {"grid_code": grid_code}})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"服务器内部错误: {str(exc)}"}), 500


@bp.route("/api/grids/<grid_code>/attributes", methods=["GET"]) 
def get_grid_attributes(grid_code: str):
    try:
        attrs = _grid_manager().get_grid_attributes(grid_code)
        if attrs is None:
            return jsonify({"error": f"未找到网格属性: {grid_code}"}), 404

        return jsonify({
            "success": True,
            "data": {
                "grid_code": attrs.grid_code,
                "flight_rules": attrs.flight_rules,
                "airspace_status": attrs.airspace_status,
                "weather_conditions": attrs.weather_conditions,
                "risk_assessment": attrs.risk_assessment,
            },
        })
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"服务器内部错误: {str(exc)}"}), 500


@bp.route("/api/grids/<grid_code>/attributes", methods=["PUT"]) 
def update_grid_attribute(grid_code: str):
    try:
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        required_fields = ["category", "key", "value"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"缺少必需参数: {field}"}), 400

        success = _grid_manager().update_grid_attribute(
            grid_code=grid_code,
            category=str(data["category"]),
            key=str(data["key"]),
            value=data["value"],
        )

        if not success:
            return jsonify({"error": f"更新属性失败: {grid_code}"}), 400

        return jsonify({"success": True, "message": "属性更新成功"})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"服务器内部错误: {str(exc)}"}), 500


@bp.route("/api/grids/search", methods=["POST"]) 
def search_grids():
    try:
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        required_fields = ["category", "key", "value"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"缺少必需参数: {field}"}), 400

        grids = _grid_manager().search_grids(
            category=str(data["category"]),
            key=str(data["key"]),
            value=data["value"],
        )

        grid_list = [{
            "code": grid.code,
            "level": grid.level,
            "bbox": grid.bbox,
            "center": grid.center,
        } for grid in grids]

        return jsonify({"success": True, "data": {"grids": grid_list, "count": len(grids)}})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"服务器内部错误: {str(exc)}"}), 500


@bp.route("/api/grids/route", methods=["POST"]) 
def calculate_route_grids():
    try:
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        if "waypoints" not in data:
            return jsonify({"error": "缺少必需参数: waypoints"}), 400

        waypoints = [(float(p[0]), float(p[1]), float(p[2])) for p in data["waypoints"]]
        level = int(data.get("level", 8))

        grid_codes, route_grids = _grid_manager().calculate_route_grids(
            waypoints=waypoints, level=level
        )

        route_grids_data: List[Dict[str, Any]] = []
        for grid in route_grids:
            route_grids_data.append({
                "code": grid.code,
                "level": grid.level,
                "bbox": grid.bbox,
                "center": grid.center,
                "alt_range": grid.alt_range,
                "size": grid.size,
            })

        return jsonify({
            "success": True,
            "data": {
                "grid_codes": grid_codes,
                "route_grids": route_grids_data,
                "count": len(grid_codes),
                "waypoints": data["waypoints"],
                "level": level,
            },
        })
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"服务器内部错误: {str(exc)}"}), 500


@bp.route("/api/routes", methods=["GET"]) 
def get_routes():
    try:
        data_dir = Path(current_app.config.get("DATA_DIR", Path(current_app.config["PROJECT_ROOT"]) / "data"))
        route_path = data_dir / "routes" / "route.json"
        with route_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        route = data.get("data", {}).get("route", {})
        channels = route.get("channels", [])
        result = []
        for ch in channels:
            points = [pt["geometry"]["coordinates"] for pt in ch.get("points", [])]
            name = ch.get("name", "")
            ch_id = ch.get("id", "")
            result.append({"id": ch_id, "name": name, "points": points})
        return jsonify({"success": True, "routes": result})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "error": str(exc)}), 500


@bp.route("/api/routes/<route_name>/grids_risk", methods=["GET"]) 
def get_route_grids_risk(route_name: str):
    try:
        from risk_assessment import risk_by_code  # lazy import to avoid heavy deps at startup
        data_dir = Path(current_app.config.get("DATA_DIR", Path(current_app.config["PROJECT_ROOT"]) / "data"))
        waypoints_path = data_dir / "routes" / f"{route_name}_waypoints.json"
        with waypoints_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        waypoints = data.get("waypoints", [])
        grid_risk_map: Dict[str, Any] = {}
        for wp in waypoints:
            grid_cell = wp.get("grid_cell", {})
            grid_code = grid_cell.get("code")
            if grid_code and grid_code not in grid_risk_map:
                try:
                    risk = risk_by_code(grid_code)
                except Exception:
                    risk = "未知"
                grid_risk_map[grid_code] = {
                    "code": grid_code,
                    "center": grid_cell.get("center"),
                    "bbox": grid_cell.get("bbox"),
                    "alt_range": grid_cell.get("alt_range"),
                    "risk_level": risk,
                }
        return jsonify({"success": True, "grids": list(grid_risk_map.values())})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "error": str(exc)}), 500


@bp.route("/api/statistics", methods=["GET"]) 
def get_statistics():
    try:
        stats = _grid_manager().get_statistics()
        return jsonify({"success": True, "data": stats})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"服务器内部错误: {str(exc)}"}), 500