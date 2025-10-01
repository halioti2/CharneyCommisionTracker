"""
Quick start script for Charney Commission Tracker.

This script provides a simple way to start the application.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.app import app
from config.config import config
from src.database.models import DatabaseManager
import logging

logger = logging.getLogger(__name__)


def initialize_database():
    """Initialize the database if it doesn't exist"""
    try:
        db_manager = DatabaseManager(config.get_database_url())
        db_manager.create_tables()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def validate_configuration():
    """Validate configuration before starting"""
    errors = config.validate()
    if errors:
        logger.error("Configuration errors found:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    return True


def main():
    """Main entry point"""
    print("=" * 70)
    print("Charney Commission Tracker")
    print("=" * 70)
    print()
    
    # Validate configuration
    print("Validating configuration...")
    if not validate_configuration():
        print("✗ Configuration validation failed. Please check your .env file.")
        sys.exit(1)
    print("✓ Configuration valid")
    print()
    
    # Initialize database
    print("Initializing database...")
    if not initialize_database():
        print("✗ Database initialization failed.")
        sys.exit(1)
    print("✓ Database initialized")
    print()
    
    # Display configuration
    print("Configuration:")
    print(f"  Environment: {config.ENVIRONMENT}")
    print(f"  Debug Mode: {config.DEBUG}")
    print(f"  API Endpoint: http://{config.FLASK_HOST}:{config.FLASK_PORT}{config.API_PREFIX}")
    print(f"  Database: {config.DATABASE_URL.split('://')[0]}://...")
    print(f"  OpenAI Model: {config.OPENAI_MODEL}")
    print()
    
    # Start server
    print("=" * 70)
    print("Starting Flask server...")
    print("=" * 70)
    print()
    print(f"API available at: http://{config.FLASK_HOST}:{config.FLASK_PORT}{config.API_PREFIX}")
    print(f"Health check: http://{config.FLASK_HOST}:{config.FLASK_PORT}{config.API_PREFIX}/health")
    print()
    print("Press CTRL+C to stop the server")
    print()
    
    try:
        app.run(
            host=config.FLASK_HOST,
            port=config.FLASK_PORT,
            debug=config.DEBUG
        )
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        print("Goodbye!")


if __name__ == "__main__":
    main()

