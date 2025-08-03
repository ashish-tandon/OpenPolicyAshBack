"""
Database Configuration

This module handles database connection configuration and settings.
"""

import os
from typing import Optional
from dataclasses import dataclass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str = "localhost"
    port: int = 5432
    database: str = "opencivicdata"
    username: str = "openpolicy"
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
        username=os.getenv("DB_USER", "openpolicy"),
        password=os.getenv("DB_PASSWORD", "openpolicy123")
    )


def get_database_url() -> str:
    """Get the database URL from environment or config"""
    # Check for explicit DATABASE_URL first
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Fall back to PostgreSQL config
    config = get_database_config()
    return config.get_url()


# Create engine and session factory
engine = create_engine(get_database_url(), echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()