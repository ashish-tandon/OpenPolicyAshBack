"""
OpenPolicy Testing Configuration
Pytest configuration and fixtures for comprehensive testing
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock
import tempfile
import shutil
from typing import Generator, AsyncGenerator

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test imports
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import redis
import requests

# Application imports
from database import (
    create_all_tables, get_session_factory, Base, 
    Jurisdiction, Representative, Bill, Committee
)
from api.main import app

# Test database configuration
TEST_DB_URL = "postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata_test"
TEST_REDIS_URL = "redis://localhost:6379/1"  # Use different DB for tests

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_database():
    """Create and cleanup test database"""
    # Create test database
    try:
        # Connect to postgres to create test database
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="postgres",
            user="openpolicy",
            password="openpolicy123"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Drop and recreate test database
        cursor.execute("DROP DATABASE IF EXISTS opencivicdata_test")
        cursor.execute("CREATE DATABASE opencivicdata_test")
        
        conn.close()
        
        # Create engine and tables
        engine = create_engine(TEST_DB_URL)
        create_all_tables(engine)
        
        yield engine
        
        # Cleanup
        engine.dispose()
        
        # Drop test database
        conn = psycopg2.connect(
            host="localhost",
            port="5432", 
            database="postgres",
            user="openpolicy",
            password="openpolicy123"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DROP DATABASE IF EXISTS opencivicdata_test")
        conn.close()
        
    except Exception as e:
        pytest.skip(f"Could not create test database: {e}")

@pytest.fixture
def db_session(test_database):
    """Create a database session for testing"""
    Session = get_session_factory(test_database)
    session = Session()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def test_redis():
    """Test Redis connection"""
    try:
        client = redis.from_url(TEST_REDIS_URL)
        client.ping()  # Test connection
        
        # Clear test database
        client.flushdb()
        
        yield client
        
        # Cleanup
        client.flushdb()
        client.close()
        
    except Exception as e:
        pytest.skip(f"Redis not available for testing: {e}")

@pytest.fixture
def api_client():
    """FastAPI test client"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def temp_directory():
    """Create temporary directory for file tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_jurisdiction(db_session):
    """Create sample jurisdiction for testing"""
    jurisdiction = Jurisdiction(
        name="Test Province",
        jurisdiction_type="provincial",
        division_id="ocd-division/country:ca/province:test"
    )
    db_session.add(jurisdiction)
    db_session.commit()
    db_session.refresh(jurisdiction)
    return jurisdiction

@pytest.fixture
def sample_representative(db_session, sample_jurisdiction):
    """Create sample representative for testing"""
    representative = Representative(
        name="John Test MP",
        role="Member of Parliament",
        party="Test Party",
        district="Test District",
        jurisdiction_id=sample_jurisdiction.id
    )
    db_session.add(representative)
    db_session.commit()
    db_session.refresh(representative)
    return representative

@pytest.fixture
def sample_bill(db_session, sample_jurisdiction):
    """Create sample bill for testing"""
    bill = Bill(
        identifier="C-TEST",
        title="Test Bill for Testing",
        summary="A bill to test the testing system",
        jurisdiction_id=sample_jurisdiction.id
    )
    db_session.add(bill)
    db_session.commit()
    db_session.refresh(bill)
    return bill

@pytest.fixture
def mock_scraper_data():
    """Mock scraper data for testing"""
    return {
        "federal": [
            {
                "name": "Test MP 1",
                "role": "Member of Parliament",
                "party": "Liberal",
                "district": "Test District 1",
                "email": "test1@parl.gc.ca"
            },
            {
                "name": "Test MP 2", 
                "role": "Member of Parliament",
                "party": "Conservative",
                "district": "Test District 2",
                "email": "test2@parl.gc.ca"
            }
        ],
        "provincial": [
            {
                "name": "Test MPP 1",
                "role": "Member of Provincial Parliament",
                "party": "NDP",
                "district": "Test Provincial District",
                "email": "test@province.ca"
            }
        ]
    }

@pytest.fixture
def services_running():
    """Check if required services are running"""
    services = {
        "database": False,
        "redis": False,
        "api": False
    }
    
    # Check database
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="opencivicdata",
            user="openpolicy",
            password="openpolicy123"
        )
        conn.close()
        services["database"] = True
    except:
        pass
    
    # Check Redis
    try:
        client = redis.Redis(host="localhost", port=6379, db=0)
        client.ping()
        services["redis"] = True
        client.close()
    except:
        pass
    
    # Check API
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            services["api"] = True
    except:
        pass
    
    return services

# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data(db_session):
    """Automatically cleanup test data after each test"""
    yield
    # Rollback any uncommitted changes
    db_session.rollback()

# Environment setup for tests
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ["TESTING"] = "1"
    os.environ["DB_URL"] = TEST_DB_URL
    os.environ["REDIS_URL"] = TEST_REDIS_URL
    yield
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]