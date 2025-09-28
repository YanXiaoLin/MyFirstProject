"""
Configuration management for iwhereGIS Grid Engine
"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class AppConfig:
    """Application configuration"""
    name: str = os.getenv('APP_NAME', 'iwhereGIS Grid Engine')
    version: str = os.getenv('APP_VERSION', '2.0.0')
    env: str = os.getenv('APP_ENV', 'development')
    debug: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    @property
    def is_production(self) -> bool:
        return self.env == 'production'
    
    @property
    def is_development(self) -> bool:
        return self.env == 'development'


@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = os.getenv('HOST', '0.0.0.0')
    port: int = int(os.getenv('PORT', 5000))
    workers: int = int(os.getenv('WORKERS', 4))
    request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', 30))


@dataclass
class APIConfig:
    """API configuration"""
    prefix: str = os.getenv('API_PREFIX', '/api/v1')
    rate_limit: str = os.getenv('API_RATE_LIMIT', '100/hour')
    key_required: bool = os.getenv('API_KEY_REQUIRED', 'False').lower() == 'true'
    secret_key: Optional[str] = os.getenv('API_SECRET_KEY')


@dataclass
class LogConfig:
    """Logging configuration"""
    level: str = os.getenv('LOG_LEVEL', 'INFO')
    file: str = os.getenv('LOG_FILE', 'logs/app.log')
    format: str = os.getenv('LOG_FORMAT', 
                           '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    def ensure_log_dir(self):
        """Ensure log directory exists"""
        log_dir = Path(self.file).parent
        log_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class SecurityConfig:
    """Security configuration"""
    cors_enabled: bool = os.getenv('CORS_ENABLED', 'True').lower() == 'true'
    cors_origins: str = os.getenv('CORS_ORIGINS', '*')
    jwt_secret_key: str = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
    jwt_expiration_delta: int = int(os.getenv('JWT_EXPIRATION_DELTA', 3600))


@dataclass
class DataConfig:
    """Data paths configuration"""
    base_dir: str = Path(__file__).parent.absolute()
    data_dir: str = os.path.join(base_dir, os.getenv('DATA_DIR', 'data'))
    tif_data_dir: str = os.path.join(base_dir, os.getenv('TIF_DATA_DIR', 
                                                          'data/all_tif_data_wgs84'))
    routes_dir: str = os.path.join(base_dir, os.getenv('ROUTES_DIR', 'data/routes'))
    export_dir: str = os.path.join(base_dir, os.getenv('EXPORT_DIR', 'exports'))
    
    def ensure_dirs(self):
        """Ensure all data directories exist"""
        for dir_path in [self.data_dir, self.export_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


@dataclass
class PerformanceConfig:
    """Performance configuration"""
    cache_enabled: bool = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
    cache_ttl: int = int(os.getenv('CACHE_TTL', 300))
    max_grid_generation: int = int(os.getenv('MAX_GRID_GENERATION', 10000))


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    metrics_enabled: bool = os.getenv('METRICS_ENABLED', 'True').lower() == 'true'
    health_check_enabled: bool = os.getenv('HEALTH_CHECK_ENABLED', 'True').lower() == 'true'
    sentry_dsn: Optional[str] = os.getenv('SENTRY_DSN')


@dataclass
class FeatureFlags:
    """Feature flags configuration"""
    enable_visualization: bool = os.getenv('ENABLE_VISUALIZATION', 'True').lower() == 'true'
    enable_risk_assessment: bool = os.getenv('ENABLE_RISK_ASSESSMENT', 'True').lower() == 'true'
    enable_route_planning: bool = os.getenv('ENABLE_ROUTE_PLANNING', 'True').lower() == 'true'


@dataclass
class Config:
    """Main configuration class"""
    app: AppConfig = field(default_factory=AppConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    api: APIConfig = field(default_factory=APIConfig)
    log: LogConfig = field(default_factory=LogConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    data: DataConfig = field(default_factory=DataConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    
    def __post_init__(self):
        """Initialize configuration"""
        self.log.ensure_log_dir()
        self.data.ensure_dirs()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'app': {
                'name': self.app.name,
                'version': self.app.version,
                'env': self.app.env,
                'debug': self.app.debug
            },
            'server': {
                'host': self.server.host,
                'port': self.server.port,
                'workers': self.server.workers
            },
            'api': {
                'prefix': self.api.prefix,
                'rate_limit': self.api.rate_limit,
                'key_required': self.api.key_required
            },
            'features': {
                'visualization': self.features.enable_visualization,
                'risk_assessment': self.features.enable_risk_assessment,
                'route_planning': self.features.enable_route_planning
            }
        }


# Global configuration instance
config = Config()

def get_config() -> Config:
    """Get configuration instance"""
    return config

def reload_config():
    """Reload configuration from environment"""
    global config
    load_dotenv(override=True)
    config = Config()
    return config