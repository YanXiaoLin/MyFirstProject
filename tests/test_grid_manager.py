"""
Unit tests for Grid Manager
"""
import pytest
from airspace_grid.grid_manager import AirspaceGridManager
from utils.exceptions import ValidationError, GridNotFoundError


class TestGridManager:
    """Test suite for AirspaceGridManager"""
    
    @pytest.fixture
    def manager(self):
        """Create a grid manager instance"""
        return AirspaceGridManager()
    
    def test_generate_grids_basic(self, manager):
        """Test basic grid generation"""
        grids = manager.generate_grids(
            lon_min=114.0,
            lon_max=114.001,
            lat_min=22.5,
            lat_max=22.501,
            level=8,
            alt_min=0,
            alt_max=100
        )
        
        assert len(grids) > 0
        assert all(hasattr(g, 'code') for g in grids)
        assert all(hasattr(g, 'level') for g in grids)
        assert all(g.level == 8 for g in grids)
    
    def test_generate_grids_different_levels(self, manager):
        """Test grid generation with different levels"""
        for level in [1, 4, 8, 12, 16]:
            grids = manager.generate_grids(
                lon_min=114.0,
                lon_max=114.01,
                lat_min=22.5,
                lat_max=22.51,
                level=level,
                alt_min=0,
                alt_max=100
            )
            assert len(grids) > 0
            assert all(g.level == level for g in grids)
    
    def test_get_grid_by_code(self, manager):
        """Test retrieving grid by code"""
        # First generate some grids
        grids = manager.generate_grids(
            lon_min=114.0,
            lon_max=114.001,
            lat_min=22.5,
            lat_max=22.501,
            level=8
        )
        
        if grids:
            test_code = grids[0].code
            retrieved = manager.get_grid_by_code(test_code)
            assert retrieved is not None
            assert retrieved.code == test_code
    
    def test_get_grid_by_invalid_code(self, manager):
        """Test retrieving grid with invalid code"""
        result = manager.get_grid_by_code("INVALID_CODE_12345")
        assert result is None
    
    def test_coordinate_encoding(self, manager):
        """Test coordinate to grid code encoding"""
        code = manager.get_grid_code_by_coordinates(
            lon=114.1234,
            lat=22.5678,
            alt=100,
            level=8
        )
        
        assert isinstance(code, str)
        assert len(code) > 0
    
    def test_coordinate_encoding_different_levels(self, manager):
        """Test coordinate encoding with different levels"""
        codes = []
        for level in [1, 4, 8, 12]:
            code = manager.get_grid_code_by_coordinates(
                lon=114.1234,
                lat=22.5678,
                alt=100,
                level=level
            )
            codes.append(code)
        
        # Different levels should produce different codes
        assert len(set(codes)) == len(codes)
    
    def test_update_grid_attribute(self, manager):
        """Test updating grid attributes"""
        # Generate a grid first
        grids = manager.generate_grids(
            lon_min=114.0,
            lon_max=114.001,
            lat_min=22.5,
            lat_max=22.501,
            level=8
        )
        
        if grids:
            grid_code = grids[0].code
            
            # Update attribute
            success = manager.update_grid_attribute(
                grid_code=grid_code,
                category="flight_rules",
                key="max_altitude",
                value=500
            )
            assert success is True
            
            # Retrieve and verify
            attrs = manager.get_grid_attributes(grid_code)
            assert attrs is not None
            assert attrs.flight_rules.get("max_altitude") == 500
    
    def test_search_grids_by_attribute(self, manager):
        """Test searching grids by attributes"""
        # Generate grids and set attributes
        grids = manager.generate_grids(
            lon_min=114.0,
            lon_max=114.001,
            lat_min=22.5,
            lat_max=22.501,
            level=8
        )
        
        if len(grids) >= 2:
            # Set different attributes
            manager.update_grid_attribute(
                grids[0].code,
                "risk_assessment",
                "risk_level",
                "high"
            )
            manager.update_grid_attribute(
                grids[1].code,
                "risk_assessment",
                "risk_level",
                "low"
            )
            
            # Search for high risk grids
            high_risk = manager.search_grids(
                category="risk_assessment",
                key="risk_level",
                value="high"
            )
            
            assert len(high_risk) >= 1
            assert grids[0].code in [g.code for g in high_risk]
    
    def test_calculate_route_grids(self, manager):
        """Test route grid calculation"""
        waypoints = [
            (114.05, 22.55, 100),
            (114.06, 22.56, 120),
            (114.07, 22.57, 150)
        ]
        
        grid_codes, route_grids = manager.calculate_route_grids(
            waypoints=waypoints,
            level=8
        )
        
        assert isinstance(grid_codes, list)
        assert isinstance(route_grids, list)
        assert len(grid_codes) > 0
        assert len(route_grids) > 0
        assert len(grid_codes) == len(route_grids)
    
    def test_get_statistics(self, manager):
        """Test getting statistics"""
        # Generate some grids
        manager.generate_grids(
            lon_min=114.0,
            lon_max=114.01,
            lat_min=22.5,
            lat_max=22.51,
            level=8
        )
        
        stats = manager.get_statistics()
        
        assert isinstance(stats, dict)
        assert 'total_grids' in stats
        assert 'level_distribution' in stats
        assert stats['total_grids'] > 0
    
    def test_export_import_json(self, manager, tmp_path):
        """Test JSON export and import"""
        # Generate grids
        original_grids = manager.generate_grids(
            lon_min=114.0,
            lon_max=114.001,
            lat_min=22.5,
            lat_max=22.501,
            level=8
        )
        
        # Set some attributes
        if original_grids:
            manager.update_grid_attribute(
                original_grids[0].code,
                "flight_rules",
                "max_altitude",
                300
            )
        
        # Export to JSON
        export_file = tmp_path / "test_export.json"
        manager.export_to_json(str(export_file))
        
        assert export_file.exists()
        
        # Create new manager and import
        new_manager = AirspaceGridManager()
        new_manager.import_from_json(str(export_file))
        
        # Verify imported data
        stats = new_manager.get_statistics()
        assert stats['total_grids'] == len(original_grids)
        
        if original_grids:
            attrs = new_manager.get_grid_attributes(original_grids[0].code)
            assert attrs is not None
            assert attrs.flight_rules.get("max_altitude") == 300
    
    def test_grids_by_area(self, manager):
        """Test getting grids by area"""
        # Generate grids in a larger area
        manager.generate_grids(
            lon_min=114.0,
            lon_max=114.02,
            lat_min=22.5,
            lat_max=22.52,
            level=6
        )
        
        # Query a subset area
        area_grids = manager.get_grids_by_area(
            lon_min=114.005,
            lon_max=114.015,
            lat_min=22.505,
            lat_max=22.515
        )
        
        assert isinstance(area_grids, list)
        # All returned grids should intersect with the query area
        for grid in area_grids:
            assert grid.bbox[2] >= 114.005  # max_lon >= query_min_lon
            assert grid.bbox[0] <= 114.015  # min_lon <= query_max_lon
            assert grid.bbox[3] >= 22.505   # max_lat >= query_min_lat
            assert grid.bbox[1] <= 22.515   # min_lat <= query_max_lat