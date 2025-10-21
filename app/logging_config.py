"""Structured logging configuration"""
import logging
import sys
from pythonjsonlogger import jsonlogger
from app.config import Config

def setup_logging():
    """Configure structured JSON logging"""
    log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
    json_formatter = jsonlogger.JsonFormatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(Config.LOG_LEVEL)
    root_logger.handlers = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(Config.LOG_LEVEL)
    console_handler.setFormatter(json_formatter)
    root_logger.addHandler(console_handler)

    try:
        file_handler = logging.FileHandler(Config.LOG_FILE)
        file_handler.setLevel(Config.LOG_LEVEL)
        file_handler.setFormatter(json_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        root_logger.warning(f"Could not create file handler: {e}")

    root_logger.info("Logging configured", extra={
        'log_level': Config.LOG_LEVEL,
        'log_file': Config.LOG_FILE
    })

    return root_logger
