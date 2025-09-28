"""
Decorator utilities for iwhereGIS Grid Engine
"""
import functools
import time
from typing import Callable, Any, Optional
from flask import request, jsonify, g
from .logger import get_logger
from .exceptions import ValidationError, AuthenticationError, GridEngineError
from .validators import validate_request_data

logger = get_logger('decorators')


def validate_request(*required_fields):
    """
    Decorator to validate request data
    
    Args:
        *required_fields: Required field names
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                validate_request_data(data, list(required_fields))
                return func(*args, **kwargs)
            except ValidationError as e:
                return jsonify({'error': str(e), 'code': e.code}), 400
        
        return wrapper
    return decorator


def handle_errors(func: Callable) -> Callable:
    """
    Decorator to handle exceptions and return appropriate error responses
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            return jsonify({
                'error': str(e),
                'code': e.code,
                'details': e.details
            }), 400
        except AuthenticationError as e:
            logger.warning(f"Authentication error in {func.__name__}: {e}")
            return jsonify({
                'error': str(e),
                'code': e.code
            }), 401
        except GridEngineError as e:
            logger.error(f"Grid engine error in {func.__name__}: {e}")
            return jsonify({
                'error': str(e),
                'code': e.code,
                'details': e.details
            }), 500
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            return jsonify({
                'error': 'Internal server error',
                'code': 'INTERNAL_ERROR'
            }), 500
    
    return wrapper


def measure_performance(operation_name: Optional[str] = None):
    """
    Decorator to measure function execution time
    
    Args:
        operation_name: Name of the operation for logging
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                name = operation_name or func.__name__
                logger.info(f"Operation {name} completed in {duration:.3f}s")
                
                # Store performance data in Flask's g object if available
                try:
                    if not hasattr(g, 'performance_metrics'):
                        g.performance_metrics = []
                    g.performance_metrics.append({
                        'operation': name,
                        'duration': duration
                    })
                except RuntimeError:
                    # Not in Flask context
                    pass
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                name = operation_name or func.__name__
                logger.error(f"Operation {name} failed after {duration:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator


# Simple in-memory cache (for production, use Redis)
_cache = {}
_cache_timestamps = {}

def cache_result(ttl: int = 300):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check if cached result exists and is not expired
            if cache_key in _cache:
                cached_time = _cache_timestamps.get(cache_key, 0)
                if time.time() - cached_time < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return _cache[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache[cache_key] = result
            _cache_timestamps[cache_key] = time.time()
            
            # Clean up old cache entries
            _cleanup_cache(ttl)
            
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result
        
        return wrapper
    return decorator


def _cleanup_cache(ttl: int):
    """Clean up expired cache entries"""
    current_time = time.time()
    expired_keys = [
        key for key, timestamp in _cache_timestamps.items()
        if current_time - timestamp > ttl * 2
    ]
    for key in expired_keys:
        _cache.pop(key, None)
        _cache_timestamps.pop(key, None)


def require_api_key(func: Callable) -> Callable:
    """
    Decorator to require API key authentication
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from config import get_config
        config = get_config()
        
        if not config.api.key_required:
            return func(*args, **kwargs)
        
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'code': 'API_KEY_REQUIRED'
            }), 401
        
        # Validate API key (in production, check against database)
        if api_key != config.api.secret_key:
            return jsonify({
                'error': 'Invalid API key',
                'code': 'INVALID_API_KEY'
            }), 401
        
        return func(*args, **kwargs)
    
    return wrapper


def async_task(func: Callable) -> Callable:
    """
    Decorator to run function as async task (placeholder for future implementation)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # In production, this would queue the task to Celery or similar
        logger.info(f"Running {func.__name__} as async task")
        return func(*args, **kwargs)
    
    return wrapper


def rate_limit(max_calls: int = 100, window: int = 3600):
    """
    Decorator to implement rate limiting
    
    Args:
        max_calls: Maximum number of calls allowed
        window: Time window in seconds
    """
    def decorator(func: Callable) -> Callable:
        call_times = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get client identifier (IP address or API key)
            client_id = request.remote_addr
            if hasattr(g, 'api_key'):
                client_id = g.api_key
            
            current_time = time.time()
            
            # Initialize or clean up old entries
            if client_id not in call_times:
                call_times[client_id] = []
            
            # Remove old entries outside the window
            call_times[client_id] = [
                t for t in call_times[client_id]
                if current_time - t < window
            ]
            
            # Check rate limit
            if len(call_times[client_id]) >= max_calls:
                retry_after = window - (current_time - call_times[client_id][0])
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'retry_after': int(retry_after)
                }), 429
            
            # Record this call
            call_times[client_id].append(current_time)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator