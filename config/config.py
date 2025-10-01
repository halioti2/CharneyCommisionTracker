"""
Configuration management for the Commission Tracker application.

Loads configuration from environment variables with sensible defaults.
Uses python-dotenv to load from .env file in development.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


class Config:
    """Application configuration"""
    
    # Application Settings
    APP_NAME: str = os.getenv('APP_NAME', 'Charney Commission Tracker')
    APP_VERSION: str = os.getenv('APP_VERSION', '0.1.0')
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    
    # Flask Settings
    FLASK_HOST: str = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT: int = int(os.getenv('FLASK_PORT', '5000'))
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database Settings
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///commissions.db')
    DATABASE_ECHO: bool = os.getenv('DATABASE_ECHO', 'False').lower() == 'true'
    
    # OpenAI Settings
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4')
    OPENAI_TEMPERATURE: float = float(os.getenv('OPENAI_TEMPERATURE', '0.1'))
    
    # Email Settings (for IMAP processing)
    EMAIL_HOST: str = os.getenv('EMAIL_HOST', '')
    EMAIL_PORT: int = int(os.getenv('EMAIL_PORT', '993'))
    EMAIL_USERNAME: str = os.getenv('EMAIL_USERNAME', '')
    EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_USE_SSL: bool = os.getenv('EMAIL_USE_SSL', 'True').lower() == 'true'
    EMAIL_FOLDER: str = os.getenv('EMAIL_FOLDER', 'INBOX')
    EMAIL_SEARCH_CRITERIA: str = os.getenv('EMAIL_SEARCH_CRITERIA', 'UNSEEN SUBJECT "commission"')
    
    # CORS Settings
    CORS_ORIGINS: list = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: Optional[str] = os.getenv('LOG_FILE', 'logs/app.log')
    
    # API Settings
    API_PREFIX: str = os.getenv('API_PREFIX', '/api/v1')
    MAX_CONTENT_LENGTH: int = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
    
    # Validation Settings
    MIN_CONFIDENCE_SCORE: float = float(os.getenv('MIN_CONFIDENCE_SCORE', '0.5'))
    AUTO_APPROVE_THRESHOLD: float = float(os.getenv('AUTO_APPROVE_THRESHOLD', '0.9'))
    
    @classmethod
    def validate(cls) -> list:
        """
        Validate configuration and return list of errors.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        
        if cls.ENVIRONMENT == 'production' and cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("SECRET_KEY must be changed in production")
        
        if cls.MIN_CONFIDENCE_SCORE < 0 or cls.MIN_CONFIDENCE_SCORE > 1:
            errors.append("MIN_CONFIDENCE_SCORE must be between 0 and 1")
        
        if cls.AUTO_APPROVE_THRESHOLD < 0 or cls.AUTO_APPROVE_THRESHOLD > 1:
            errors.append("AUTO_APPROVE_THRESHOLD must be between 0 and 1")
        
        return errors
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get the database URL with proper formatting"""
        return cls.DATABASE_URL
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.ENVIRONMENT.lower() == 'production'
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.ENVIRONMENT.lower() == 'development'
    
    @classmethod
    def to_dict(cls) -> dict:
        """
        Convert configuration to dictionary (for logging/debugging).
        Excludes sensitive values.
        """
        return {
            'APP_NAME': cls.APP_NAME,
            'APP_VERSION': cls.APP_VERSION,
            'DEBUG': cls.DEBUG,
            'ENVIRONMENT': cls.ENVIRONMENT,
            'FLASK_HOST': cls.FLASK_HOST,
            'FLASK_PORT': cls.FLASK_PORT,
            'DATABASE_URL': cls.DATABASE_URL.split('://')[0] + '://***',  # Hide credentials
            'OPENAI_MODEL': cls.OPENAI_MODEL,
            'OPENAI_API_KEY': '***' if cls.OPENAI_API_KEY else 'NOT SET',
            'EMAIL_HOST': cls.EMAIL_HOST,
            'EMAIL_USERNAME': cls.EMAIL_USERNAME if cls.EMAIL_USERNAME else 'NOT SET',
            'LOG_LEVEL': cls.LOG_LEVEL,
            'API_PREFIX': cls.API_PREFIX,
            'MIN_CONFIDENCE_SCORE': cls.MIN_CONFIDENCE_SCORE,
            'AUTO_APPROVE_THRESHOLD': cls.AUTO_APPROVE_THRESHOLD
        }


# Create a singleton instance
config = Config()


def get_config() -> Config:
    """Get the configuration instance"""
    return config

