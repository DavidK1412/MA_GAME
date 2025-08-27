"""
Application settings and configuration.
"""

import os
from typing import Dict, Any
from pathlib import Path


class Settings:
    """Application settings class."""
    
    # Base directory
    BASE_DIR = Path(__file__).parent.parent.parent
    
    # Database settings
    DATABASE_HOST: str = os.getenv("PGHOST", "localhost")
    DATABASE_PORT: str = os.getenv("PGPORT", "5432")
    DATABASE_NAME: str = os.getenv("PGDATABASE", "frog_game")
    DATABASE_USER: str = os.getenv("PGUSER", "postgres")
    DATABASE_PASSWORD: str = os.getenv("PGPASSWORD", "")
    
    # API settings
    API_TITLE: str = "Frog Game API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Intelligent educational game system with adaptive AI"
    
    # Game settings
    DECISION_INTERVAL: int = 3  # Make decision every N moves
    MAX_GAME_ATTEMPTS: int = 10
    SESSION_TIMEOUT: int = 3600  # 1 hour in seconds
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "logs/frog_game.log"
    
    # Belief system settings
    BELIEF_EVALUATION_THRESHOLD: float = 0.5
    MIN_CONFIDENCE_SCORE: float = 0.3
    
    @classmethod
    def get_database_config(cls) -> Dict[str, str]:
        """Get database configuration as dictionary."""
        return {
            "host": cls.DATABASE_HOST,
            "port": cls.DATABASE_PORT,
            "dbname": cls.DATABASE_NAME,
            "user": cls.DATABASE_USER,
            "password": cls.DATABASE_PASSWORD,
        }
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate that all required configuration is present."""
        required_vars = [
            "DATABASE_NAME",
            "DATABASE_USER", 
            "DATABASE_PASSWORD"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required configuration variables: {missing_vars}")


# Global settings instance
settings = Settings()
