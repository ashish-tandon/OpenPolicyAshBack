"""
OpenPolicy Merge - Database Configuration

This module provides database connection management and configuration
for the unified OpenPolicy Merge platform.
"""

import os
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base, init_database

logger = logging.getLogger(__name__)

# Database configuration
class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self):
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://openpolicy:secure_password@localhost:5432/openpolicy_merge"
        )
        
        # Extract components for different connections
        self.async_database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        # Connection pool settings
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "30"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        
        # Performance settings
        self.echo = os.getenv("DB_ECHO", "false").lower() == "true"
        self.echo_pool = os.getenv("DB_ECHO_POOL", "false").lower() == "true"
        
    def get_engine_kwargs(self):
        """Get engine configuration parameters"""
        return {
            "echo": self.echo,
            "echo_pool": self.echo_pool,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": True,
            "connect_args": {
                "options": "-c timezone=America/Toronto",
                "application_name": "OpenPolicy_Merge",
                "connect_timeout": 10,
            }
        }

# Global configuration instance
db_config = DatabaseConfig()

# Create the main database engine
engine = create_engine(
    db_config.database_url,
    **db_config.get_engine_kwargs()
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI endpoints.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    try:
        # Try to connect to the database
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        
        # Try to create the database
        try:
            # Extract database name from URL
            db_name = db_config.database_url.split('/')[-1]
            base_url = db_config.database_url.rsplit('/', 1)[0] + '/postgres'
            
            # Connect to postgres database to create our database
            temp_engine = create_engine(base_url)
            with temp_engine.connect() as conn:
                conn.execute(text("COMMIT"))  # End any existing transaction
                conn.execute(text(f"CREATE DATABASE {db_name}"))
            
            logger.info(f"Database {db_name} created successfully")
            temp_engine.dispose()
            return True
            
        except Exception as create_error:
            logger.error(f"Failed to create database: {create_error}")
            return False

def initialize_database():
    """Initialize database with all tables and indexes"""
    try:
        # Ensure database exists
        if not create_database_if_not_exists():
            raise Exception("Failed to create or connect to database")
        
        # Create all tables
        logger.info("Creating database tables...")
        init_database(engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.scalar()
            logger.info(f"Database initialized with {table_count} tables")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def check_database_health() -> dict:
    """Check database connectivity and performance"""
    try:
        start_time = time.time()
        
        with engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT version()"))
            pg_version = result.scalar()
            
            # Test performance
            result = conn.execute(text("SELECT COUNT(*) FROM pg_stat_activity"))
            active_connections = result.scalar()
            
            # Check database size
            result = conn.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """))
            db_size = result.scalar()
            
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "postgresql_version": pg_version,
            "active_connections": active_connections,
            "database_size": db_size,
            "pool_size": engine.pool.size(),
            "pool_checked_out": engine.pool.checkedout(),
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

def get_database_stats() -> dict:
    """Get detailed database statistics"""
    try:
        with engine.connect() as conn:
            # Table statistics
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
                LIMIT 10
            """))
            tables = [dict(row._mapping) for row in result]
            
            # Index usage
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE idx_tup_read > 0
                ORDER BY idx_tup_read DESC
                LIMIT 10
            """))
            indexes = [dict(row._mapping) for row in result]
            
            # Database activity
            result = conn.execute(text("""
                SELECT 
                    datname,
                    numbackends,
                    xact_commit,
                    xact_rollback,
                    blks_read,
                    blks_hit,
                    tup_returned,
                    tup_fetched,
                    tup_inserted,
                    tup_updated,
                    tup_deleted
                FROM pg_stat_database 
                WHERE datname = current_database()
            """))
            activity = dict(result.fetchone()._mapping)
            
        return {
            "table_stats": tables,
            "index_stats": indexes,
            "database_activity": activity
        }
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {"error": str(e)}

# Performance monitoring
class DatabaseMetrics:
    """Database performance metrics collection"""
    
    def __init__(self):
        self.query_count = 0
        self.total_query_time = 0.0
        self.slow_queries = []
        
    def record_query(self, query: str, execution_time: float):
        """Record query execution metrics"""
        self.query_count += 1
        self.total_query_time += execution_time
        
        # Track slow queries (> 1 second)
        if execution_time > 1.0:
            self.slow_queries.append({
                "query": query[:200],  # Truncate long queries
                "execution_time": execution_time,
                "timestamp": time.time()
            })
            
            # Keep only recent slow queries
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-50:]
    
    def get_metrics(self) -> dict:
        """Get current performance metrics"""
        avg_query_time = (
            self.total_query_time / self.query_count 
            if self.query_count > 0 else 0
        )
        
        return {
            "total_queries": self.query_count,
            "average_query_time": round(avg_query_time, 4),
            "total_query_time": round(self.total_query_time, 2),
            "slow_queries_count": len(self.slow_queries),
            "recent_slow_queries": self.slow_queries[-5:] if self.slow_queries else []
        }

# Global metrics instance
db_metrics = DatabaseMetrics()

# Custom event listeners for metrics
from sqlalchemy import event
import time

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time"""
    context._query_start_time = time.time()

@event.listens_for(engine, "after_cursor_execute")  
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query completion and metrics"""
    if hasattr(context, '_query_start_time'):
        execution_time = time.time() - context._query_start_time
        db_metrics.record_query(statement, execution_time)

if __name__ == "__main__":
    # Test database setup
    print("Testing database configuration...")
    
    # Initialize database
    if initialize_database():
        print("✅ Database initialized successfully")
        
        # Test health check
        health = check_database_health()
        print(f"✅ Database health: {health}")
        
        # Test stats
        stats = get_database_stats()
        print(f"✅ Database stats collected: {len(stats.get('table_stats', []))} tables")
        
    else:
        print("❌ Database initialization failed")