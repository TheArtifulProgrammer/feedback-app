"""Application configuration"""
import os

class Config:
    """Application configuration"""

    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/feedback.db')
    SECRET_KEY = os.getenv('SECRET_KEY', '07b13c38b89f521dd1c6227e3645abe1')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8090))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
