"""
Logging utilities for iwhereGIS Grid Engine
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json

class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'process': record.process,
            'thread': record.thread
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = 'iwhereGIS',
    level: str = 'INFO',
    log_file: Optional[str] = None,
    json_format: bool = False,
    console_output: bool = True
) -> logging.Logger:
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Log file path
        json_format: Use JSON format for logs
        console_output: Enable console output
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers = []  # Clear existing handlers
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        
        if json_format:
            console_formatter = JSONFormatter()
        else:
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Ensure log directory exists
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        
        if json_format:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger instance
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f'iwhereGIS.{name}')


class RequestLogger:
    """HTTP request logger middleware"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(self, method: str, path: str, status: int, 
                   duration: float, **kwargs):
        """Log HTTP request"""
        extra_data = {
            'method': method,
            'path': path,
            'status': status,
            'duration_ms': round(duration * 1000, 2),
            **kwargs
        }
        
        if status >= 500:
            self.logger.error(f"Request failed: {method} {path}", 
                            extra={'extra_data': extra_data})
        elif status >= 400:
            self.logger.warning(f"Request error: {method} {path}", 
                              extra={'extra_data': extra_data})
        else:
            self.logger.info(f"Request completed: {method} {path}", 
                           extra={'extra_data': extra_data})


class PerformanceLogger:
    """Performance metrics logger"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_operation(self, operation: str, duration: float, 
                      count: Optional[int] = None, **kwargs):
        """Log operation performance"""
        extra_data = {
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            **kwargs
        }
        
        if count is not None:
            extra_data['count'] = count
            extra_data['rate'] = round(count / duration if duration > 0 else 0, 2)
        
        self.logger.info(f"Operation completed: {operation}", 
                        extra={'extra_data': extra_data})


# Global logger instance
logger = setup_logger()

def configure_logging(config):
    """Configure logging from config object"""
    global logger
    logger = setup_logger(
        name='iwhereGIS',
        level=config.log.level,
        log_file=config.log.file if config.app.is_production else None,
        json_format=config.app.is_production,
        console_output=True
    )
    return logger