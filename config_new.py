"""
Configuration management for CommitHub
Supports multiple environments: development, testing, production
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    
    # Flask core settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Mail/SMTP Settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@commithub.local')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    
    # AWS Settings (if used)
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'ap-southeast-1')
    
    # Firebase Settings
    FIREBASE_CREDENTIALS_JSON = os.getenv('FIREBASE_CREDENTIALS')
    
    # File paths
    BASE_DIR = os.path.dirname(__file__)
    EXCEL_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'excels', 'UploadedIPCR')
    PROFILE_PICS_FOLDER = os.path.join(BASE_DIR, 'profile_pics')


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'LOCAL_DATABASE_URL',
        'sqlite:///commithub_dev.db'
    )
    CORS_ORIGINS = ['*']  # Allow all origins in development


class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        'sqlite:///:memory:'
    )
    WTF_CSRF_ENABLED = False
    # Use in-memory database for faster tests


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('PRODUCTION_DATABASE_URL')
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    
    # Stricter CORS in production
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://yourdomain.com').split(',')
    
    # Ensure all required keys are set
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError('PRODUCTION_DATABASE_URL environment variable not set')
    if not SECRET_KEY:
        raise ValueError('SECRET_KEY environment variable not set')


def get_config(config_name=None):
    """
    Get configuration object based on environment
    
    Args:
        config_name: 'development', 'testing', 'production' or None to use FLASK_ENV
    
    Returns:
        Config class instance
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development').lower()
    
    config_map = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
        'dev': DevelopmentConfig,
        'test': TestingConfig,
        'prod': ProductionConfig,
    }
    
    config_class = config_map.get(config_name, DevelopmentConfig)
    return config_class()
