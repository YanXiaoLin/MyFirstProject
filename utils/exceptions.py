"""
Custom exceptions for iwhereGIS Grid Engine
"""

class GridEngineError(Exception):
    """Base exception for grid engine errors"""
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or 'GRID_ENGINE_ERROR'
        self.details = details or {}


class ValidationError(GridEngineError):
    """Raised when input validation fails"""
    def __init__(self, message: str, field: str = None, value: any = None):
        super().__init__(
            message,
            code='VALIDATION_ERROR',
            details={'field': field, 'value': value} if field else {}
        )


class GridNotFoundError(GridEngineError):
    """Raised when a grid is not found"""
    def __init__(self, grid_code: str):
        super().__init__(
            f"Grid not found: {grid_code}",
            code='GRID_NOT_FOUND',
            details={'grid_code': grid_code}
        )


class GridGenerationError(GridEngineError):
    """Raised when grid generation fails"""
    def __init__(self, message: str, params: dict = None):
        super().__init__(
            message,
            code='GRID_GENERATION_ERROR',
            details={'params': params} if params else {}
        )


class AttributeError(GridEngineError):
    """Raised when attribute operations fail"""
    def __init__(self, message: str, grid_code: str = None, attribute: str = None):
        details = {}
        if grid_code:
            details['grid_code'] = grid_code
        if attribute:
            details['attribute'] = attribute
        
        super().__init__(
            message,
            code='ATTRIBUTE_ERROR',
            details=details
        )


class RouteCalculationError(GridEngineError):
    """Raised when route calculation fails"""
    def __init__(self, message: str, waypoints: list = None):
        super().__init__(
            message,
            code='ROUTE_CALCULATION_ERROR',
            details={'waypoints': waypoints} if waypoints else {}
        )


class RiskAssessmentError(GridEngineError):
    """Raised when risk assessment fails"""
    def __init__(self, message: str, location: tuple = None):
        super().__init__(
            message,
            code='RISK_ASSESSMENT_ERROR',
            details={'location': location} if location else {}
        )


class DataImportError(GridEngineError):
    """Raised when data import fails"""
    def __init__(self, message: str, file_path: str = None):
        super().__init__(
            message,
            code='DATA_IMPORT_ERROR',
            details={'file_path': file_path} if file_path else {}
        )


class DataExportError(GridEngineError):
    """Raised when data export fails"""
    def __init__(self, message: str, file_path: str = None):
        super().__init__(
            message,
            code='DATA_EXPORT_ERROR',
            details={'file_path': file_path} if file_path else {}
        )


class ConfigurationError(GridEngineError):
    """Raised when configuration is invalid"""
    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message,
            code='CONFIGURATION_ERROR',
            details={'config_key': config_key} if config_key else {}
        )


class AuthenticationError(GridEngineError):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message,
            code='AUTHENTICATION_ERROR'
        )


class AuthorizationError(GridEngineError):
    """Raised when authorization fails"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message,
            code='AUTHORIZATION_ERROR'
        )


class RateLimitError(GridEngineError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(
            message,
            code='RATE_LIMIT_ERROR',
            details={'retry_after': retry_after} if retry_after else {}
        )