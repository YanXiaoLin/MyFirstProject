"""
Input validation utilities for iwhereGIS Grid Engine
"""
from typing import Tuple, Optional
from .exceptions import ValidationError


def validate_coordinates(lon: float, lat: float) -> Tuple[float, float]:
    """
    Validate longitude and latitude values
    
    Args:
        lon: Longitude value
        lat: Latitude value
    
    Returns:
        Validated (lon, lat) tuple
    
    Raises:
        ValidationError: If coordinates are invalid
    """
    if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
        raise ValidationError("Coordinates must be numeric values")
    
    if not -180 <= lon <= 180:
        raise ValidationError(f"Longitude must be between -180 and 180, got {lon}")
    
    if not -90 <= lat <= 90:
        raise ValidationError(f"Latitude must be between -90 and 90, got {lat}")
    
    return float(lon), float(lat)


def validate_grid_level(level: int) -> int:
    """
    Validate grid level
    
    Args:
        level: Grid level (1-16)
    
    Returns:
        Validated level
    
    Raises:
        ValidationError: If level is invalid
    """
    if not isinstance(level, int):
        try:
            level = int(level)
        except (ValueError, TypeError):
            raise ValidationError("Grid level must be an integer")
    
    if not 1 <= level <= 16:
        raise ValidationError(f"Grid level must be between 1 and 16, got {level}")
    
    return level


def validate_altitude(alt: float, min_alt: float = -1000, max_alt: float = 50000) -> float:
    """
    Validate altitude value
    
    Args:
        alt: Altitude value in meters
        min_alt: Minimum allowed altitude
        max_alt: Maximum allowed altitude
    
    Returns:
        Validated altitude
    
    Raises:
        ValidationError: If altitude is invalid
    """
    if not isinstance(alt, (int, float)):
        try:
            alt = float(alt)
        except (ValueError, TypeError):
            raise ValidationError("Altitude must be a numeric value")
    
    if not min_alt <= alt <= max_alt:
        raise ValidationError(f"Altitude must be between {min_alt} and {max_alt} meters, got {alt}")
    
    return float(alt)


def validate_bbox(lon_min: float, lon_max: float, lat_min: float, lat_max: float) -> Tuple[float, float, float, float]:
    """
    Validate bounding box coordinates
    
    Args:
        lon_min: Minimum longitude
        lon_max: Maximum longitude
        lat_min: Minimum latitude
        lat_max: Maximum latitude
    
    Returns:
        Validated (lon_min, lon_max, lat_min, lat_max) tuple
    
    Raises:
        ValidationError: If bounding box is invalid
    """
    # Validate individual coordinates
    lon_min, lat_min = validate_coordinates(lon_min, lat_min)
    lon_max, lat_max = validate_coordinates(lon_max, lat_max)
    
    # Check order
    if lon_min >= lon_max:
        raise ValidationError(f"lon_min ({lon_min}) must be less than lon_max ({lon_max})")
    
    if lat_min >= lat_max:
        raise ValidationError(f"lat_min ({lat_min}) must be less than lat_max ({lat_max})")
    
    # Check size (prevent too large areas)
    if lon_max - lon_min > 10:
        raise ValidationError("Bounding box longitude range cannot exceed 10 degrees")
    
    if lat_max - lat_min > 10:
        raise ValidationError("Bounding box latitude range cannot exceed 10 degrees")
    
    return lon_min, lon_max, lat_min, lat_max


def validate_waypoints(waypoints: list) -> list:
    """
    Validate waypoints for route planning
    
    Args:
        waypoints: List of waypoint coordinates [(lon, lat, alt), ...]
    
    Returns:
        Validated waypoints
    
    Raises:
        ValidationError: If waypoints are invalid
    """
    if not isinstance(waypoints, list):
        raise ValidationError("Waypoints must be a list")
    
    if len(waypoints) < 2:
        raise ValidationError("At least 2 waypoints are required")
    
    if len(waypoints) > 100:
        raise ValidationError("Maximum 100 waypoints allowed")
    
    validated = []
    for i, waypoint in enumerate(waypoints):
        if not isinstance(waypoint, (list, tuple)) or len(waypoint) < 2:
            raise ValidationError(f"Waypoint {i} must be a tuple/list with at least (lon, lat)")
        
        lon, lat = validate_coordinates(waypoint[0], waypoint[1])
        
        # Optional altitude
        alt = 0.0
        if len(waypoint) >= 3:
            alt = validate_altitude(waypoint[2])
        
        validated.append((lon, lat, alt))
    
    return validated


def validate_grid_code(code: str) -> str:
    """
    Validate grid code format
    
    Args:
        code: Grid code string
    
    Returns:
        Validated grid code
    
    Raises:
        ValidationError: If grid code is invalid
    """
    if not isinstance(code, str):
        raise ValidationError("Grid code must be a string")
    
    if not code:
        raise ValidationError("Grid code cannot be empty")
    
    if len(code) > 100:
        raise ValidationError("Grid code is too long")
    
    # Basic format check (can be enhanced based on actual encoding format)
    if not all(c.isalnum() or c in '-_:' for c in code):
        raise ValidationError("Grid code contains invalid characters")
    
    return code


def validate_attribute_category(category: str) -> str:
    """
    Validate attribute category
    
    Args:
        category: Attribute category name
    
    Returns:
        Validated category
    
    Raises:
        ValidationError: If category is invalid
    """
    valid_categories = [
        'flight_rules',
        'airspace_status',
        'weather_conditions',
        'risk_assessment',
        'custom'
    ]
    
    if not isinstance(category, str):
        raise ValidationError("Category must be a string")
    
    if category not in valid_categories:
        raise ValidationError(f"Invalid category. Must be one of: {', '.join(valid_categories)}")
    
    return category


def validate_request_data(data: dict, required_fields: list) -> dict:
    """
    Validate request data has required fields
    
    Args:
        data: Request data dictionary
        required_fields: List of required field names
    
    Returns:
        Validated data
    
    Raises:
        ValidationError: If required fields are missing
    """
    if not isinstance(data, dict):
        raise ValidationError("Request data must be a JSON object")
    
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return data