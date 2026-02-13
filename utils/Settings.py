"""
Settings utilities - Single source of truth for system settings
Provides caching and centralized access to all system configuration
"""
from functools import lru_cache
import os
from datetime import datetime


class SystemSettings:
    """Centralized system settings access"""
    
    # Cache for settings to avoid repeated database queries
    _settings_cache = {}
    _cache_timestamp = None
    _cache_ttl = 3600  # 1 hour cache TTL
    
    @classmethod
    def get_setting(cls, key, default=None):
        """
        Get a system setting value
        
        Args:
            key: Setting key name
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        # Check if we need to refresh cache
        now = datetime.now().timestamp()
        if cls._cache_timestamp is None or (now - cls._cache_timestamp) > cls._cache_ttl:
            cls._refresh_cache()
        
        return cls._settings_cache.get(key, default)
    
    @classmethod
    def set_setting(cls, key, value):
        """
        Set a system setting value
        
        Args:
            key: Setting key name
            value: Value to set
        """
        cls._settings_cache[key] = value
        cls._cache_timestamp = datetime.now().timestamp()
        # TODO: Persist to database
    
    @classmethod
    def _refresh_cache(cls):
        """Refresh settings cache from database"""
        try:
            from models.System_Settings import System_Settings
            
            settings = System_Settings.query.all()
            cls._settings_cache = {s.setting_key: s.setting_value for s in settings}
            cls._cache_timestamp = datetime.now().timestamp()
        except Exception as e:
            print(f"Warning: Could not refresh settings cache: {e}")
            cls._cache_timestamp = datetime.now().timestamp()
    
    @classmethod
    def clear_cache(cls):
        """Clear the settings cache"""
        cls._settings_cache = {}
        cls._cache_timestamp = None
    
    # Common settings accessors
    @classmethod
    def is_system_maintenance_mode(cls):
        """Check if system is in maintenance mode"""
        return cls.get_setting('maintenance_mode', False)
    
    @classmethod
    def get_email_settings(cls):
        """Get email configuration settings"""
        return {
            'smtp_server': cls.get_setting('smtp_server', 'smtp.gmail.com'),
            'smtp_port': cls.get_setting('smtp_port', 587),
            'from_email': cls.get_setting('from_email', 'noreply@commithub.local'),
        }
    
    @classmethod
    def get_file_upload_settings(cls):
        """Get file upload configuration"""
        return {
            'max_file_size': cls.get_setting('max_file_size', 50 * 1024 * 1024),
            'allowed_extensions': cls.get_setting('allowed_extensions', ['xlsx', 'xls', 'pdf', 'doc', 'docx']),
        }
    
    @classmethod
    def get_session_timeout(cls):
        """Get session timeout in minutes"""
        return int(cls.get_setting('session_timeout', 30))


class AppSettings:
    """Application-level settings from environment and config"""
    
    @classmethod
    @lru_cache(maxsize=1)
    def get_flask_env(cls):
        """Get Flask environment (development, testing, production)"""
        return os.getenv('FLASK_ENV', 'development')
    
    @classmethod
    @lru_cache(maxsize=1)
    def get_debug_mode(cls):
        """Check if debug mode is enabled"""
        return os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes')
    
    @classmethod
    @lru_cache(maxsize=1)
    def get_log_level(cls):
        """Get logging level"""
        return os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    @lru_cache(maxsize=1)
    def get_jwt_expiration_hours(cls):
        """Get JWT token expiration time in hours"""
        return int(os.getenv('JWT_EXPIRATION_HOURS', 24 * 30))  # 30 days default
    
    @classmethod
    @lru_cache(maxsize=1)
    def get_api_version(cls):
        """Get API version"""
        return os.getenv('API_VERSION', 'v1')
    
    @classmethod
    @lru_cache(maxsize=1)
    def get_app_name(cls):
        """Get application name"""
        return os.getenv('APP_NAME', 'CommitHub')
    
    @classmethod
    @lru_cache(maxsize=1)
    def is_production(cls):
        """Check if running in production"""
        return cls.get_flask_env() == 'production'
    
    @classmethod
    @lru_cache(maxsize=1)
    def is_testing(cls):
        """Check if running in test mode"""
        return cls.get_flask_env() == 'testing'
    
    @classmethod
    @lru_cache(maxsize=1)
    def is_development(cls):
        """Check if running in development"""
        return cls.get_flask_env() == 'development'
