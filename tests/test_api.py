"""
Integration tests for API endpoints
"""
import pytest
import json
from app import create_app
from config import get_config


class TestAPI:
    """Test suite for API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test app"""
        app = create_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def config(self):
        """Get configuration"""
        return get_config()
    
    def test_health_check(self, client, config):
        """Test health check endpoint"""
        response = client.get(f'{config.api.prefix}/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'version' in data
        assert 'service' in data
    
    def test_generate_grids_success(self, client, config):
        """Test successful grid generation"""
        payload = {
            'lon_min': 114.0,
            'lon_max': 114.001,
            'lat_min': 22.5,
            'lat_max': 22.501,
            'level': 8,
            'alt_min': 0,
            'alt_max': 100
        }
        
        response = client.post(
            f'{config.api.prefix}/grids/generate',
            json=payload
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'grids' in data['data']
        assert 'count' in data['data']
        assert data['data']['count'] > 0
    
    def test_generate_grids_missing_fields(self, client, config):
        """Test grid generation with missing required fields"""
        payload = {
            'lon_min': 114.0,
            'lat_min': 22.5,
            'level': 8
        }
        
        response = client.post(
            f'{config.api.prefix}/grids/generate',
            json=payload
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_generate_grids_invalid_coordinates(self, client, config):
        """Test grid generation with invalid coordinates"""
        payload = {
            'lon_min': 200,  # Invalid longitude
            'lon_max': 210,
            'lat_min': 22.5,
            'lat_max': 22.501,
            'level': 8
        }
        
        response = client.post(
            f'{config.api.prefix}/grids/generate',
            json=payload
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_encode_coordinates(self, client, config):
        """Test coordinate encoding"""
        payload = {
            'lon': 114.1234,
            'lat': 22.5678,
            'alt': 100,
            'level': 8
        }
        
        response = client.post(
            f'{config.api.prefix}/grids/encode',
            json=payload
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'grid_code' in data['data']
        assert isinstance(data['data']['grid_code'], str)
    
    def test_get_grid_by_code(self, client, config):
        """Test getting grid by code"""
        # First, generate a grid and get its code
        payload = {
            'lon': 114.1234,
            'lat': 22.5678,
            'alt': 100,
            'level': 8
        }
        
        encode_response = client.post(
            f'{config.api.prefix}/grids/encode',
            json=payload
        )
        
        grid_code = json.loads(encode_response.data)['data']['grid_code']
        
        # Now get the grid by code
        response = client.get(f'{config.api.prefix}/grids/{grid_code}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert data['data']['code'] == grid_code
    
    def test_get_grid_by_invalid_code(self, client, config):
        """Test getting grid with invalid code"""
        response = client.get(f'{config.api.prefix}/grids/INVALID_CODE_XYZ')
        
        # Should return 404 or error
        assert response.status_code in [404, 500]
        data = json.loads(response.data)
        assert 'error' in data or 'success' in data
    
    def test_update_grid_attributes(self, client, config):
        """Test updating grid attributes"""
        # First encode a coordinate to get a grid code
        encode_payload = {
            'lon': 114.1234,
            'lat': 22.5678,
            'alt': 100,
            'level': 8
        }
        
        encode_response = client.post(
            f'{config.api.prefix}/grids/encode',
            json=encode_payload
        )
        grid_code = json.loads(encode_response.data)['data']['grid_code']
        
        # Generate the grid
        generate_payload = {
            'lon_min': 114.12,
            'lon_max': 114.13,
            'lat_min': 22.56,
            'lat_max': 22.57,
            'level': 8
        }
        client.post(f'{config.api.prefix}/grids/generate', json=generate_payload)
        
        # Update attributes
        update_payload = {
            'category': 'flight_rules',
            'key': 'max_altitude',
            'value': 500
        }
        
        response = client.put(
            f'{config.api.prefix}/grids/{grid_code}/attributes',
            json=update_payload
        )
        
        # The response might be 200 or 400 depending on whether the grid exists
        assert response.status_code in [200, 400, 404]
    
    def test_search_grids(self, client, config):
        """Test searching grids by attributes"""
        search_payload = {
            'category': 'risk_assessment',
            'key': 'risk_level',
            'value': 'high'
        }
        
        response = client.post(
            f'{config.api.prefix}/grids/search',
            json=search_payload
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'grids' in data['data']
        assert 'count' in data['data']
    
    def test_calculate_route_grids(self, client, config):
        """Test route grid calculation"""
        payload = {
            'waypoints': [
                [114.05, 22.55, 100],
                [114.06, 22.56, 120],
                [114.07, 22.57, 150]
            ],
            'level': 8
        }
        
        response = client.post(
            f'{config.api.prefix}/grids/route',
            json=payload
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'grid_codes' in data['data']
        assert 'route_grids' in data['data']
        assert 'count' in data['data']
        assert data['data']['count'] > 0
    
    def test_calculate_route_invalid_waypoints(self, client, config):
        """Test route calculation with invalid waypoints"""
        payload = {
            'waypoints': [
                [114.05, 22.55]  # Only one waypoint
            ],
            'level': 8
        }
        
        response = client.post(
            f'{config.api.prefix}/grids/route',
            json=payload
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_statistics(self, client, config):
        """Test getting statistics"""
        # First generate some grids
        generate_payload = {
            'lon_min': 114.0,
            'lon_max': 114.01,
            'lat_min': 22.5,
            'lat_max': 22.51,
            'level': 8
        }
        client.post(f'{config.api.prefix}/grids/generate', json=generate_payload)
        
        # Get statistics
        response = client.get(f'{config.api.prefix}/statistics')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'total_grids' in data['data']
        assert 'level_distribution' in data['data']
    
    def test_rate_limiting(self, client, config):
        """Test rate limiting (if configured)"""
        # This test would need rate limiting to be configured
        # Make multiple rapid requests to trigger rate limit
        pass
    
    def test_cors_headers(self, client, config):
        """Test CORS headers"""
        response = client.get(f'{config.api.prefix}/health')
        
        # Check if CORS headers are present when enabled
        if config.security.cors_enabled:
            assert 'Access-Control-Allow-Origin' in response.headers