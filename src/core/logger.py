"""
WiFi Tester Pro v6.0 - Centralized Logger
Unified logging system with file and console output
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List
from logging.handlers import RotatingFileHandler
from threading import Lock
from dataclasses import dataclass
from enum import Enum

from ..settings import (
    LOGS_PATH, LOG_CONFIG, APP_NAME
)


class LogLevel(Enum):
    """Log severity levels"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class LogEntry:
    """Single log entry"""
    timestamp: float
    level: str
    source: str
    message: str
    
    @property
    def formatted_time(self) -> str:
        return datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")
    
    def __str__(self) -> str:
        return f"[{self.formatted_time}] [{self.level}] {self.source}: {self.message}"


class LogBuffer:
    """Thread-safe log buffer for UI display"""
    
    def __init__(self, max_size: int = 1000):
        self._buffer: List[LogEntry] = []
        self._max_size = max_size
        self._lock = Lock()
        self._listeners: List[Callable[[LogEntry], None]] = []
    
    def add(self, entry: LogEntry):
        """Add log entry to buffer"""
        with self._lock:
            self._buffer.append(entry)
            if len(self._buffer) > self._max_size:
                self._buffer = self._buffer[-self._max_size:]
        
        # Notify listeners
        for listener in self._listeners:
            try:
                listener(entry)
            except:
                pass
    
    def get_all(self) -> List[LogEntry]:
        """Get all log entries"""
        with self._lock:
            return list(self._buffer)
    
    def get_recent(self, count: int = 100) -> List[LogEntry]:
        """Get recent log entries"""
        with self._lock:
            return list(self._buffer[-count:])
    
    def clear(self):
        """Clear buffer"""
        with self._lock:
            self._buffer.clear()
    
    def add_listener(self, callback: Callable[[LogEntry], None]):
        """Add listener for new log entries"""
        self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[LogEntry], None]):
        """Remove listener"""
        try:
            self._listeners.remove(callback)
        except ValueError:
            pass


class ColoredFormatter(logging.Formatter):
    """Colored output for console logging"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m',   # Red background
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


class BufferHandler(logging.Handler):
    """Logging handler that writes to LogBuffer"""
    
    def __init__(self, buffer: LogBuffer):
        super().__init__()
        self._buffer = buffer
    
    def emit(self, record: logging.LogRecord):
        try:
            entry = LogEntry(
                timestamp=record.created,
                level=record.levelname,
                source=record.name,
                message=self.format(record)
            )
            self._buffer.add(entry)
        except:
            pass


class Logger:
    """
    Centralized logging system (Singleton).
    Provides file logging, console output, and UI buffer.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._buffer = LogBuffer(max_size=LOG_CONFIG.get("max_lines", 1000))
        self._loggers: dict = {}
        self._root_logger = self._setup_root_logger()
        
        print(f"[Logger] Initialized - Logs: {LOGS_PATH}")
    
    def _setup_root_logger(self) -> logging.Logger:
        """Setup the root logger with all handlers"""
        logger = logging.getLogger(APP_NAME)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        
        # Create formatters
        detailed_format = LOG_CONFIG.get(
            "format",
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
        simple_format = "%(levelname)-8s | %(message)s"
        date_format = LOG_CONFIG.get("date_format", "%Y-%m-%d %H:%M:%S")
        
        # Console handler
        if LOG_CONFIG.get("console_enabled", True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(ColoredFormatter(simple_format))
            logger.addHandler(console_handler)
        
        # File handler
        if LOG_CONFIG.get("file_enabled", True):
            log_file = LOGS_PATH / f"{APP_NAME.lower().replace(' ', '_')}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=LOG_CONFIG.get("max_file_size", 10*1024*1024),
                backupCount=LOG_CONFIG.get("backup_count", 5),
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(detailed_format, date_format))
            logger.addHandler(file_handler)
        
        # Buffer handler (for UI)
        buffer_handler = BufferHandler(self._buffer)
        buffer_handler.setLevel(logging.DEBUG)
        buffer_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(buffer_handler)
        
        return logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a named logger (child of root)"""
        if name not in self._loggers:
            full_name = f"{APP_NAME}.{name}"
            self._loggers[name] = logging.getLogger(full_name)
        return self._loggers[name]
    
    # ==========================================================================
    # Convenience logging methods
    # ==========================================================================
    
    def debug(self, message: str, source: str = "App"):
        """Log debug message"""
        self.get_logger(source).debug(message)
    
    def info(self, message: str, source: str = "App"):
        """Log info message"""
        self.get_logger(source).info(message)
    
    def warning(self, message: str, source: str = "App"):
        """Log warning message"""
        self.get_logger(source).warning(message)
    
    def error(self, message: str, source: str = "App"):
        """Log error message"""
        self.get_logger(source).error(message)
    
    def critical(self, message: str, source: str = "App"):
        """Log critical message"""
        self.get_logger(source).critical(message)
    
    def exception(self, message: str, source: str = "App"):
        """Log exception with traceback"""
        self.get_logger(source).exception(message)
    
    # Aliases for compatibility
    def log(self, message: str, level: str = "INFO", source: str = "App"):
        """Generic log method"""
        level_map = {
            "DEBUG": self.debug,
            "INFO": self.info,
            "WARNING": self.warning,
            "WARN": self.warning,
            "ERROR": self.error,
            "CRITICAL": self.critical,
        }
        log_func = level_map.get(level.upper(), self.info)
        log_func(message, source)
    
    # ==========================================================================
    # Buffer access
    # ==========================================================================
    
    @property
    def buffer(self) -> LogBuffer:
        """Get log buffer for UI display"""
        return self._buffer
    
    def get_recent_logs(self, count: int = 100) -> List[LogEntry]:
        """Get recent log entries"""
        return self._buffer.get_recent(count)
    
    def add_log_listener(self, callback: Callable[[LogEntry], None]):
        """Add listener for new log entries (for UI updates)"""
        self._buffer.add_listener(callback)
    
    def remove_log_listener(self, callback: Callable[[LogEntry], None]):
        """Remove log listener"""
        self._buffer.remove_listener(callback)
    
    def clear_buffer(self):
        """Clear the log buffer"""
        self._buffer.clear()


# Global logger instance
log = Logger()


def get_logger(name: str = "App") -> logging.Logger:
    """Get a named logger"""
    return log.get_logger(name)


# Convenience functions
def debug(message: str, source: str = "App"):
    log.debug(message, source)

def info(message: str, source: str = "App"):
    log.info(message, source)

def warning(message: str, source: str = "App"):
    log.warning(message, source)

def error(message: str, source: str = "App"):
    log.error(message, source)

def critical(message: str, source: str = "App"):
    log.critical(message, source)


__all__ = [
    'Logger',
    'LogLevel',
    'LogEntry',
    'LogBuffer',
    'log',
    'get_logger',
    'debug', 'info', 'warning', 'error', 'critical',
]
