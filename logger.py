import logging
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
import os
import config

def setup_logging():
    """
    Setup logging configuration
    Creates log directory and configures loggers
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(config.DATA_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log filename with date
    log_filename = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Set levels for specific loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


class Logger:
    """Custom logger class with console and file output"""
    
    def __init__(self, name="URLShortener"):
        """
        Initialize logger
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if config.LOG_TO_CONSOLE:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler with rotation
        if config.LOG_TO_FILE:
            file_handler = RotatingFileHandler(
                config.LOG_FILE_PATH,
                maxBytes=config.MAX_LOG_SIZE_MB * 1024 * 1024,
                backupCount=config.LOG_BACKUP_COUNT
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message):
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message):
        """Log critical message"""
        self.logger.critical(message)
    
    def log_url_created(self, short_code, original_url, custom=False):
        """Log URL creation"""
        url_type = "custom" if custom else "auto-generated"
        self.info(f"URL created - Short code: {short_code} ({url_type}) -> {original_url}")
    
    def log_url_accessed(self, short_code, ip_address):
        """Log URL access"""
        self.info(f"URL accessed - Short code: {short_code} from IP: {ip_address}")
    
    def log_url_deleted(self, short_code):
        """Log URL deletion"""
        self.info(f"URL deleted - Short code: {short_code}")
    
    def log_url_updated(self, short_code, new_url):
        """Log URL update"""
        self.info(f"URL updated - Short code: {short_code} -> {new_url}")
    
    def log_error_with_context(self, error_type, message, **kwargs):
        """Log error with additional context"""
        context = " | ".join([f"{k}: {v}" for k, v in kwargs.items()])
        self.error(f"{error_type} - {message} | {context}")
    
    def log_performance(self, operation, duration_ms):
        """Log performance metrics"""
        self.debug(f"Performance - {operation}: {duration_ms:.2f}ms")


# Create global logger instance
logger = Logger()