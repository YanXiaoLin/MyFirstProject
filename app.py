"""
iwhereGIS Grid Engine API Server - Production Version
"""
import os
import json
from datetime import datetime
from typing import Optional

from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from config import get_config
from utils import (
    configure_logging,
    get_logger,
    RequestLogger,
    handle_errors,
    measure_performance,
    validate_request,
    require_api_key
)
from utils.validators import (
    validate_coordinates,
    validate_grid_level,
    validate_bbox,
    validate_waypoints,
    validate_grid_code,
    validate_attribute_category
)
from utils.exceptions import GridNotFoundError, ValidationError

from airspace_grid.grid_manager import AirspaceGridManager
from risk_assessment import risk_by_code

# Initialize configuration
config = get_config()

# Configure logging
logger = configure_logging(config)
request_logger = RequestLogger(logger)

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = config.app.debug

# Add proxy fix for proper client IP detection
if config.app.is_production:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Configure CORS
if config.security.cors_enabled:
    CORS(app, origins=config.security.cors_origins.split(','))

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[config.api.rate_limit] if config.api.rate_limit else []
)

# Initialize grid manager
grid_manager = AirspaceGridManager()

# Middleware for request timing
@app.before_request
def before_request():
    g.start_time = datetime.utcnow()
    g.request_id = request.headers.get('X-Request-ID', os.urandom(16).hex())

@app.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        duration = (datetime.utcnow() - g.start_time).total_seconds()
        request_logger.log_request(
            method=request.method,
            path=request.path,
            status=response.status_code,
            duration=duration,
            request_id=g.request_id
        )
        response.headers['X-Request-ID'] = g.request_id
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
    return response

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'code': 'NOT_FOUND',
        'path': request.path
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method not allowed',
        'code': 'METHOD_NOT_ALLOWED',
        'method': request.method,
        'path': request.path
    }), 405

@app.errorhandler(500)
def internal_error(error):
    logger.exception("Internal server error")
    return jsonify({
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR',
        'request_id': g.get('request_id')
    }), 500

# Static files
@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory('static', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

# Health and monitoring endpoints
@app.route(f'{config.api.prefix}/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': config.app.name,
        'version': config.app.version,
        'environment': config.app.env,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route(f'{config.api.prefix}/status', methods=['GET'])
@require_api_key
def status():
    """Detailed status endpoint"""
    stats = grid_manager.get_statistics()
    return jsonify({
        'status': 'operational',
        'service': config.app.name,
        'version': config.app.version,
        'environment': config.app.env,
        'statistics': stats,
        'features': {
            'visualization': config.features.enable_visualization,
            'risk_assessment': config.features.enable_risk_assessment,
            'route_planning': config.features.enable_route_planning
        },
        'timestamp': datetime.utcnow().isoformat()
    })

# Grid generation endpoints
@app.route(f'{config.api.prefix}/grids/generate', methods=['POST'])
@handle_errors
@measure_performance('grid_generation')
@validate_request('lon_min', 'lon_max', 'lat_min', 'lat_max', 'level')
def generate_grids():
    """Generate grids for a specified area"""
    data = request.get_json()
    
    # Validate input
    lon_min, lon_max, lat_min, lat_max = validate_bbox(
        float(data['lon_min']),
        float(data['lon_max']),
        float(data['lat_min']),
        float(data['lat_max'])
    )
    level = validate_grid_level(data['level'])
    
    alt_min = float(data.get('alt_min', 0.0))
    alt_max = float(data.get('alt_max', 1000.0))
    
    # Check grid generation limit
    estimated_count = ((lon_max - lon_min) * (lat_max - lat_min)) * (2 ** (level * 2))
    if estimated_count > config.performance.max_grid_generation:
        raise ValidationError(
            f"Too many grids requested. Maximum allowed: {config.performance.max_grid_generation}"
        )
    
    # Generate grids
    grids = grid_manager.generate_grids(
        lon_min=lon_min,
        lon_max=lon_max,
        lat_min=lat_min,
        lat_max=lat_max,
        level=level,
        alt_min=alt_min,
        alt_max=alt_max
    )
    
    # Format response
    grid_list = [{
        'code': grid.code,
        'level': grid.level,
        'bbox': grid.bbox,
        'center': grid.center,
        'size': grid.size,
        'alt_range': grid.alt_range
    } for grid in grids]
    
    return jsonify({
        'success': True,
        'message': f'Successfully generated {len(grids)} grids',
        'data': {
            'grids': grid_list,
            'count': len(grids),
            'parameters': {
                'bbox': [lon_min, lat_min, lon_max, lat_max],
                'level': level,
                'alt_range': [alt_min, alt_max]
            }
        }
    })

@app.route(f'{config.api.prefix}/grids/<grid_code>', methods=['GET'])
@handle_errors
@measure_performance('grid_query')
def get_grid_by_code(grid_code: str):
    """Get grid information by code"""
    # Validate grid code
    grid_code = validate_grid_code(grid_code)
    
    # Get grid
    grid = grid_manager.get_grid_by_code(grid_code)
    if grid is None:
        raise GridNotFoundError(grid_code)
    
    return jsonify({
        'success': True,
        'data': {
            'code': grid.code,
            'level': grid.level,
            'bbox': grid.bbox,
            'center': grid.center,
            'size': grid.size,
            'alt_range': grid.alt_range
        }
    })

@app.route(f'{config.api.prefix}/grids/encode', methods=['POST'])
@handle_errors
@validate_request('lon', 'lat', 'level')
def encode_coordinates():
    """Encode coordinates to grid code"""
    data = request.get_json()
    
    # Validate input
    lon, lat = validate_coordinates(float(data['lon']), float(data['lat']))
    level = validate_grid_level(data['level'])
    alt = float(data.get('alt', 0))
    
    # Get grid code
    grid_code = grid_manager.get_grid_code_by_coordinates(
        lon=lon,
        lat=lat,
        alt=alt,
        level=level
    )
    
    return jsonify({
        'success': True,
        'data': {
            'grid_code': grid_code,
            'coordinates': {
                'lon': lon,
                'lat': lat,
                'alt': alt
            },
            'level': level
        }
    })

# Attribute management endpoints
@app.route(f'{config.api.prefix}/grids/<grid_code>/attributes', methods=['GET'])
@handle_errors
def get_grid_attributes(grid_code: str):
    """Get grid attributes"""
    grid_code = validate_grid_code(grid_code)
    
    attrs = grid_manager.get_grid_attributes(grid_code)
    if attrs is None:
        raise GridNotFoundError(grid_code)
    
    return jsonify({
        'success': True,
        'data': {
            'grid_code': attrs.grid_code,
            'flight_rules': attrs.flight_rules,
            'airspace_status': attrs.airspace_status,
            'weather_conditions': attrs.weather_conditions,
            'risk_assessment': attrs.risk_assessment
        }
    })

@app.route(f'{config.api.prefix}/grids/<grid_code>/attributes', methods=['PUT'])
@handle_errors
@validate_request('category', 'key', 'value')
def update_grid_attribute(grid_code: str):
    """Update grid attributes"""
    data = request.get_json()
    
    grid_code = validate_grid_code(grid_code)
    category = validate_attribute_category(data['category'])
    
    success = grid_manager.update_grid_attribute(
        grid_code=grid_code,
        category=category,
        key=data['key'],
        value=data['value']
    )
    
    if not success:
        raise GridNotFoundError(grid_code)
    
    return jsonify({
        'success': True,
        'message': 'Attribute updated successfully',
        'data': {
            'grid_code': grid_code,
            'category': category,
            'key': data['key'],
            'value': data['value']
        }
    })

# Search endpoints
@app.route(f'{config.api.prefix}/grids/search', methods=['POST'])
@handle_errors
@validate_request('category', 'key', 'value')
def search_grids():
    """Search grids by attributes"""
    data = request.get_json()
    
    category = validate_attribute_category(data['category'])
    
    grids = grid_manager.search_grids(
        category=category,
        key=data['key'],
        value=data['value']
    )
    
    grid_list = [{
        'code': grid.code,
        'level': grid.level,
        'bbox': grid.bbox,
        'center': grid.center
    } for grid in grids]
    
    return jsonify({
        'success': True,
        'data': {
            'grids': grid_list,
            'count': len(grids),
            'search_criteria': {
                'category': category,
                'key': data['key'],
                'value': data['value']
            }
        }
    })

# Route planning endpoints
@app.route(f'{config.api.prefix}/grids/route', methods=['POST'])
@handle_errors
@measure_performance('route_calculation')
@validate_request('waypoints')
def calculate_route_grids():
    """Calculate grids along a route"""
    if not config.features.enable_route_planning:
        return jsonify({
            'error': 'Route planning feature is disabled',
            'code': 'FEATURE_DISABLED'
        }), 403
    
    data = request.get_json()
    
    # Validate waypoints
    waypoints = validate_waypoints(data['waypoints'])
    level = validate_grid_level(data.get('level', 8))
    
    # Calculate route grids
    grid_codes, route_grids = grid_manager.calculate_route_grids(
        waypoints=waypoints,
        level=level
    )
    
    # Format response
    route_grids_data = [{
        'code': grid.code,
        'level': grid.level,
        'bbox': grid.bbox,
        'center': grid.center,
        'alt_range': grid.alt_range,
        'size': grid.size
    } for grid in route_grids]
    
    return jsonify({
        'success': True,
        'data': {
            'grid_codes': grid_codes,
            'route_grids': route_grids_data,
            'count': len(grid_codes),
            'waypoints': waypoints,
            'level': level
        }
    })

# Risk assessment endpoints
@app.route(f'{config.api.prefix}/grids/<grid_code>/risk', methods=['GET'])
@handle_errors
def get_grid_risk(grid_code: str):
    """Get risk assessment for a grid"""
    if not config.features.enable_risk_assessment:
        return jsonify({
            'error': 'Risk assessment feature is disabled',
            'code': 'FEATURE_DISABLED'
        }), 403
    
    grid_code = validate_grid_code(grid_code)
    
    try:
        risk_level = risk_by_code(grid_code)
        return jsonify({
            'success': True,
            'data': {
                'grid_code': grid_code,
                'risk_level': risk_level,
                'risk_category': _categorize_risk(risk_level)
            }
        })
    except Exception as e:
        logger.error(f"Risk assessment failed for {grid_code}: {e}")
        return jsonify({
            'error': 'Risk assessment failed',
            'code': 'RISK_ASSESSMENT_ERROR'
        }), 500

def _categorize_risk(risk_level: int) -> str:
    """Categorize risk level"""
    categories = {
        1: 'very_low',
        2: 'low',
        3: 'medium',
        4: 'high',
        5: 'very_high'
    }
    return categories.get(risk_level, 'unknown')

# Statistics endpoints
@app.route(f'{config.api.prefix}/statistics', methods=['GET'])
@handle_errors
def get_statistics():
    """Get system statistics"""
    stats = grid_manager.get_statistics()
    
    return jsonify({
        'success': True,
        'data': stats
    })

# Route data endpoints
@app.route(f'{config.api.prefix}/routes', methods=['GET'])
@handle_errors
def get_routes():
    """Get available routes"""
    try:
        route_path = os.path.join(config.data.routes_dir, 'route.json')
        with open(route_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        route = data.get('data', {}).get('route', {})
        channels = route.get('channels', [])
        
        result = []
        for ch in channels:
            points = [pt['geometry']['coordinates'] for pt in ch.get('points', [])]
            result.append({
                'id': ch.get('id', ''),
                'name': ch.get('name', ''),
                'points': points,
                'metadata': {
                    'created_at': ch.get('created_at'),
                    'updated_at': ch.get('updated_at')
                }
            })
        
        return jsonify({
            'success': True,
            'data': {
                'routes': result,
                'count': len(result)
            }
        })
    except Exception as e:
        logger.error(f"Failed to load routes: {e}")
        return jsonify({
            'error': 'Failed to load routes',
            'code': 'ROUTE_LOAD_ERROR'
        }), 500

def create_app():
    """Application factory"""
    return app

if __name__ == '__main__':
    logger.info(f"Starting {config.app.name} v{config.app.version}")
    logger.info(f"Environment: {config.app.env}")
    logger.info(f"API Prefix: {config.api.prefix}")
    logger.info(f"Server: http://{config.server.host}:{config.server.port}")
    
    if config.app.is_production:
        logger.warning("Running in production mode with development server is not recommended!")
        logger.info("Use gunicorn or uwsgi for production deployment")
    
    app.run(
        host=config.server.host,
        port=config.server.port,
        debug=config.app.debug
    )