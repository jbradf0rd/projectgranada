"""
Granada v2 Configuration
"""
import os
import sys


def get_base_dir():
    """
    Get the base directory for the application.
    Handles both development and PyInstaller bundled modes.
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return os.path.dirname(sys.executable)
    else:
        # Running in development
        return os.path.abspath(os.path.dirname(__file__))


def get_resource_dir():
    """
    Get the directory where bundled resources (templates, static) are located.
    For PyInstaller, this is sys._MEIPASS; for development, it's BASE_DIR.
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle - resources in _MEIPASS
        return sys._MEIPASS
    else:
        # Running in development
        return os.path.abspath(os.path.dirname(__file__))


BASE_DIR = get_base_dir()
RESOURCE_DIR = get_resource_dir()
DATA_DIR = os.path.join(BASE_DIR, 'data')


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'granada-dev-secret-key')

    # Database - stored in DATA_DIR (next to executable)
    DATABASE_PATH = os.path.join(DATA_DIR, 'granada.db')

    # Resource paths - use RESOURCE_DIR for bundled resources
    STATIC_FOLDER = os.path.join(RESOURCE_DIR, 'static')
    TEMPLATES_FOLDER = os.path.join(RESOURCE_DIR, 'templates')

    # AI Settings (stored in database, these are defaults)
    DEFAULT_CLAUDE_MODEL = 'claude-sonnet-4-5'
    DEFAULT_OLLAMA_URL = 'http://localhost:11434'

    # App settings
    HOST = '127.0.0.1'
    PORT = 5000


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
