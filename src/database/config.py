"""
Database Configuration

This module handles database connection configuration and settings.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str = "localhost"
    port: int = 5432
    database: str = "opencivicdata"
    username: str = "ubuntu"
    password: Optional[str] = None
    
    def get_url(self) -> str:
        """Get the database URL for SQLAlchemy"""
        if self.password:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"postgresql://{self.username}@{self.host}:{self.port}/{self.database}"


def get_database_config() -> DatabaseConfig:
    """Get database configuration from environment variables or defaults"""
    return DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "opencivicdata"),
        username=os.getenv("DB_USER", "ubuntu"),
        password=os.getenv("DB_PASSWORD")
    )