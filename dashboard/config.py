#!/usr/bin/env python3
# dashboard/config.py

import os
from datetime import timedelta

# Base configuration class
class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # API configuration
    API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000/api/v1')
    HEALTH_URL = os.environ.get('HEALTH_URL', 'http://localhost:8000/health')
    
    # Dashboard configuration
    DASHBOARD_TITLE = 'Temperature Monitoring System'
    DASHBOARD_LOGO = 'static/img/logo.png'
    COMPANY_NAME = 'Your Company'
    SUPPORT_EMAIL = 'support@example.com'
    
    # Temperature units
    DEFAULT_TEMP_UNIT = 'C'
    TEMP_UNITS = ['C', 'F', 'K']
    
    # Size units
    DEFAULT_SIZE_UNIT = 'sqm'
    SIZE_UNITS = ['sqm', 'sqft', 'm2', 'ft2']
    
    # Pagination
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    
    # Date format
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Temperature threshold defaults
    DEFAULT_WARNING_THRESHOLD = 2
    DEFAULT_CRITICAL_THRESHOLD = 5
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = os.path.join(os.getcwd(), 'dashboard', 'sessions')

# Development configuration
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000/api/v1')
    HEALTH_URL = os.environ.get('HEALTH_URL', 'http://localhost:8000/health')

# Testing configuration
class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    
    # Testing-specific settings
    API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000/api/v1')
    HEALTH_URL = os.environ.get('HEALTH_URL', 'http://localhost:8000/health')
    
    # Use in-memory session for testing
    SESSION_TYPE = 'null'

# Production configuration
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    API_BASE_URL = os.environ.get('API_BASE_URL', 'https://api.example.com/api/v1')
    HEALTH_URL = os.environ.get('HEALTH_URL', 'https://api.example.com/health')
    
    # Secure cookie settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    
    # Set this to True when behind a reverse proxy
    PREFERRED_URL_SCHEME = 'https'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    
    # Default configuration
    'default': DevelopmentConfig
}

def get_config():
    """Get the current configuration based on environment variable"""
    config_name = os.environ.get('FLASK_CONFIG', 'default')
    return config.get(config_name, config['default'])