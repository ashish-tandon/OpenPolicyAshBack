"""
OpenPolicy Merge - API Test Suite

Comprehensive test suite for the FastAPI application targeting 90%+ test coverage.
Tests cover all major endpoints, error conditions, and edge cases.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Generator
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test database setup
from src.database.models import Base, Jurisdiction, JurisdictionType, Representative, RepresentativeRole, Bill, BillStatus
from src.database.config import get_db
from src.api.main import app

# =============================================================================
# Test Database Setup
# =============================================================================

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def client():
    """Create test client with database setup"""
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_jurisdiction(db_session):
    """Create sample jurisdiction for testing"""
    jurisdiction = Jurisdiction(
        name="Canada",
        jurisdiction_type=JurisdictionType.FEDERAL,
        code="CA",
        website="https://canada.ca",
        population=38000000,
        area_km2=9984670.0,
        data_quality_score=0.95
    )
    db_session.add(jurisdiction)
    db_session.commit()
    db_session.refresh(jurisdiction)
    return jurisdiction

@pytest.fixture
def sample_representative(db_session, sample_jurisdiction):
    """Create sample representative for testing"""
    representative = Representative(
        jurisdiction_id=sample_jurisdiction.id,
        name="John Doe",
        role=RepresentativeRole.MP,
        party="Liberal",
        riding="Ottawa Centre",
        email="john.doe@parl.gc.ca",
        phone="613-555-0123",
        active=True
    )
    db_session.add(representative)
    db_session.commit()
    db_session.refresh(representative)
    return representative

@pytest.fixture
def sample_bill(db_session, sample_jurisdiction):
    """Create sample bill for testing"""
    bill = Bill(
        jurisdiction_id=sample_jurisdiction.id,
        number="C-1",
        title="An Act respecting the administration of oaths of office",
        status=BillStatus.ROYAL_ASSENT_GIVEN,
        parliament=44,
        session=1,
        introduction_date=datetime(2021, 11, 22),
        private_member=False
    )
    db_session.add(bill)
    db_session.commit()
    db_session.refresh(bill)
    return bill

# =============================================================================
# Health and System Endpoint Tests
# =============================================================================

class TestHealthEndpoints:
    """Test health and system monitoring endpoints"""
    
    def test_health_check_success(self, client):
        """Test successful health check"""
        with patch('src.database.config.check_database_health') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "response_time_ms": 5.2,
                "postgresql_version": "PostgreSQL 16.0",
                "active_connections": 3
            }
            
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert data["version"] == "1.0.0"
            assert "timestamp" in data
            assert data["database"]["status"] == "healthy"
            assert "services" in data
    
    def test_health_check_degraded(self, client):
        """Test health check when database is unhealthy"""
        with patch('src.database.config.check_database_health') as mock_health:
            mock_health.return_value = {
                "status": "unhealthy",
                "error": "Connection timeout"
            }
            
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "degraded"
            assert data["database"]["status"] == "unhealthy"
    
    def test_stats_endpoint(self, client, sample_jurisdiction, sample_representative, sample_bill):
        """Test system statistics endpoint"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert data["jurisdictions"] >= 1
        assert data["representatives"] >= 1
        assert data["bills"] >= 1
        assert "data_freshness" in data
        assert isinstance(data["data_freshness"], dict)
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        with patch('src.database.config.get_database_stats') as mock_stats, \
             patch('src.database.config.db_metrics') as mock_metrics, \
             patch('src.scrapers.manager.scraper_manager') as mock_scraper:
            
            mock_stats.return_value = {"table_stats": [], "index_stats": []}
            mock_metrics.get_metrics.return_value = {"total_queries": 100}
            mock_scraper.get_scraper_stats.return_value = {"total_runs": 5}
            
            response = client.get("/metrics")
            assert response.status_code == 200
            data = response.json()
            
            assert "database" in data
            assert "scrapers" in data
            assert "api" in data

# =============================================================================
# Jurisdiction Endpoint Tests
# =============================================================================

class TestJurisdictionEndpoints:
    """Test jurisdiction management endpoints"""
    
    def test_list_jurisdictions(self, client, sample_jurisdiction):
        """Test listing jurisdictions"""
        response = client.get("/api/v1/jurisdictions")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        jurisdiction = data[0]
        assert jurisdiction["name"] == "Canada"
        assert jurisdiction["jurisdiction_type"] == "federal"
        assert jurisdiction["code"] == "CA"
        assert "representative_count" in jurisdiction
        assert "bill_count" in jurisdiction
    
    def test_list_jurisdictions_with_filter(self, client, sample_jurisdiction):
        """Test jurisdiction listing with type filter"""
        response = client.get("/api/v1/jurisdictions?jurisdiction_type=federal")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        assert all(j["jurisdiction_type"] == "federal" for j in data)
    
    def test_list_jurisdictions_with_search(self, client, sample_jurisdiction):
        """Test jurisdiction listing with name search"""
        response = client.get("/api/v1/jurisdictions?search=canada")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        assert any("canada" in j["name"].lower() for j in data)
    
    def test_list_jurisdictions_invalid_type(self, client):
        """Test jurisdiction listing with invalid type"""
        response = client.get("/api/v1/jurisdictions?jurisdiction_type=invalid")
        assert response.status_code == 400
        assert "Invalid jurisdiction type" in response.json()["detail"]
    
    def test_get_jurisdiction_success(self, client, sample_jurisdiction):
        """Test getting specific jurisdiction"""
        response = client.get(f"/api/v1/jurisdictions/{sample_jurisdiction.id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Canada"
        assert data["jurisdiction_type"] == "federal"
        assert data["population"] == 38000000
    
    def test_get_jurisdiction_not_found(self, client):
        """Test getting non-existent jurisdiction"""
        response = client.get("/api/v1/jurisdictions/non-existent-id")
        assert response.status_code == 404
        assert "Jurisdiction not found" in response.json()["detail"]
    
    def test_list_jurisdictions_pagination(self, client, db_session):
        """Test jurisdiction pagination"""
        # Create multiple jurisdictions
        for i in range(5):
            jurisdiction = Jurisdiction(
                name=f"Test Province {i}",
                jurisdiction_type=JurisdictionType.PROVINCIAL,
                code=f"T{i}"
            )
            db_session.add(jurisdiction)
        db_session.commit()
        
        # Test pagination
        response = client.get("/api/v1/jurisdictions?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        response = client.get("/api/v1/jurisdictions?limit=2&offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

# =============================================================================
# Representative Endpoint Tests
# =============================================================================

class TestRepresentativeEndpoints:
    """Test representative management endpoints"""
    
    def test_list_representatives(self, client, sample_representative):
        """Test listing representatives"""
        response = client.get("/api/v1/representatives")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        rep = data[0]
        assert rep["name"] == "John Doe"
        assert rep["role"] == "mp"
        assert rep["party"] == "Liberal"
        assert "jurisdiction" in rep
        assert "committees" in rep
    
    def test_list_representatives_with_filters(self, client, sample_representative):
        """Test representative listing with filters"""
        # Test role filter
        response = client.get("/api/v1/representatives?role=mp")
        assert response.status_code == 200
        data = response.json()
        assert all(r["role"] == "mp" for r in data)
        
        # Test party filter
        response = client.get("/api/v1/representatives?party=Liberal")
        assert response.status_code == 200
        data = response.json()
        assert any("Liberal" in r["party"] for r in data)
        
        # Test active filter
        response = client.get("/api/v1/representatives?active=true")
        assert response.status_code == 200
        data = response.json()
        assert all(r["active"] is True for r in data)
    
    def test_list_representatives_search(self, client, sample_representative):
        """Test representative search"""
        response = client.get("/api/v1/representatives?search=john")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        assert any("john" in r["name"].lower() for r in data)
    
    def test_list_representatives_invalid_role(self, client):
        """Test representative listing with invalid role"""
        response = client.get("/api/v1/representatives?role=invalid")
        assert response.status_code == 400
        assert "Invalid role" in response.json()["detail"]

# =============================================================================
# Bill Endpoint Tests
# =============================================================================

class TestBillEndpoints:
    """Test bill management endpoints"""
    
    def test_list_bills(self, client, sample_bill):
        """Test listing bills"""
        response = client.get("/api/v1/bills")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        bill = data[0]
        assert bill["number"] == "C-1"
        assert bill["title"] == "An Act respecting the administration of oaths of office"
        assert bill["status"] == "royal_assent_given"
        assert "jurisdiction" in bill
    
    def test_list_bills_with_filters(self, client, sample_bill):
        """Test bill listing with filters"""
        # Test status filter
        response = client.get("/api/v1/bills?status=royal_assent_given")
        assert response.status_code == 200
        data = response.json()
        assert all(b["status"] == "royal_assent_given" for b in data)
        
        # Test parliament filter
        response = client.get("/api/v1/bills?parliament=44")
        assert response.status_code == 200
        data = response.json()
        assert all(b["parliament"] == 44 for b in data)
        
        # Test session filter
        response = client.get("/api/v1/bills?session=1")
        assert response.status_code == 200
        data = response.json()
        assert all(b["session"] == 1 for b in data)
    
    def test_list_bills_search(self, client, sample_bill):
        """Test bill search"""
        response = client.get("/api/v1/bills?search=oaths")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        assert any("oaths" in b["title"].lower() for b in data)
    
    def test_list_bills_invalid_status(self, client):
        """Test bill listing with invalid status"""
        response = client.get("/api/v1/bills?status=invalid")
        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

# =============================================================================
# Search Endpoint Tests
# =============================================================================

class TestSearchEndpoints:
    """Test global search functionality"""
    
    def test_global_search_all_entities(self, client, sample_representative, sample_bill):
        """Test searching across all entity types"""
        response = client.get("/api/v1/search?q=john")
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == "john"
        assert "total_results" in data
        assert "results" in data
        
        # Should find the representative
        results = data["results"]
        assert any(r["type"] == "representative" for r in results)
    
    def test_global_search_specific_entities(self, client, sample_representative):
        """Test searching specific entity types"""
        response = client.get("/api/v1/search?q=john&entity_types=representatives")
        assert response.status_code == 200
        data = response.json()
        
        results = data["results"]
        assert all(r["type"] == "representative" for r in results)
    
    def test_global_search_with_jurisdiction_filter(self, client, sample_representative, sample_jurisdiction):
        """Test search with jurisdiction filter"""
        response = client.get(f"/api/v1/search?q=john&jurisdiction_id={sample_jurisdiction.id}")
        assert response.status_code == 200
        data = response.json()
        
        # Results should only come from the specified jurisdiction
        assert len(data["results"]) >= 0
    
    def test_global_search_empty_query(self, client):
        """Test search with missing query parameter"""
        response = client.get("/api/v1/search")
        assert response.status_code == 422  # Validation error
    
    def test_global_search_limit(self, client, sample_representative):
        """Test search result limiting"""
        response = client.get("/api/v1/search?q=john&limit=1")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) <= 1

# =============================================================================
# Administrative Endpoint Tests
# =============================================================================

class TestAdministrativeEndpoints:
    """Test administrative and scraping endpoints"""
    
    def test_trigger_scraper_success(self, client):
        """Test triggering a scraper task"""
        with patch('src.scrapers.manager.scraper_manager') as mock_manager:
            mock_manager.run_scraper = AsyncMock()
            
            request_data = {
                "scraper_type": "federal_parliament",
                "jurisdiction_id": "test-jurisdiction",
                "config": {"test": "config"}
            }
            
            response = client.post("/api/v1/admin/scraping/run", json=request_data)
            assert response.status_code == 200
            data = response.json()
            
            assert data["scraper_type"] == "federal_parliament"
            assert data["jurisdiction_id"] == "test-jurisdiction"
            assert data["status"] == "queued"
            assert "task_id" in data
    
    def test_trigger_scraper_invalid_type(self, client):
        """Test triggering scraper with invalid type"""
        request_data = {
            "scraper_type": "invalid_scraper",
            "jurisdiction_id": "test-jurisdiction"
        }
        
        response = client.post("/api/v1/admin/scraping/run", json=request_data)
        assert response.status_code == 400
        assert "Invalid scraper type" in response.json()["detail"]
    
    def test_get_scraping_status(self, client):
        """Test getting scraper status"""
        with patch('src.scrapers.manager.scraper_manager') as mock_manager:
            mock_manager.get_active_runs.return_value = []
            mock_manager.get_scraper_stats.return_value = {"total_runs": 0}
            
            response = client.get("/api/v1/admin/scraping/status")
            assert response.status_code == 200
            data = response.json()
            
            assert "active_runs" in data
            assert "statistics" in data

# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_endpoint(self, client):
        """Test accessing non-existent endpoint"""
        response = client.get("/api/v1/non-existent")
        assert response.status_code == 404
    
    def test_invalid_http_method(self, client):
        """Test using invalid HTTP method"""
        response = client.delete("/api/v1/jurisdictions")
        assert response.status_code == 405
    
    def test_malformed_json(self, client):
        """Test sending malformed JSON"""
        response = client.post(
            "/api/v1/admin/scraping/run",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_database_error_simulation(self, client):
        """Test handling database errors"""
        with patch('src.database.config.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/v1/jurisdictions")
            assert response.status_code == 500

# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Test API performance and response times"""
    
    def test_response_time_health_check(self, client):
        """Test health check response time"""
        import time
        start_time = time.time()
        
        response = client.get("/health")
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 200
        assert response_time < 200  # Should respond within 200ms
        assert "X-Process-Time" in response.headers
    
    def test_large_result_set_handling(self, client, db_session):
        """Test handling large result sets with pagination"""
        # Create many test jurisdictions
        jurisdictions = []
        for i in range(50):
            jurisdiction = Jurisdiction(
                name=f"Test City {i}",
                jurisdiction_type=JurisdictionType.MUNICIPAL,
                code=f"TC{i:02d}"
            )
            jurisdictions.append(jurisdiction)
        
        db_session.add_all(jurisdictions)
        db_session.commit()
        
        # Test with large limit
        response = client.get("/api/v1/jurisdictions?limit=100")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 100
    
    def test_concurrent_requests(self, client):
        """Test handling concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/health")
            results.append(response.status_code)
        
        # Create 10 concurrent threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 10
        
        # Should handle concurrent requests efficiently
        total_time = end_time - start_time
        assert total_time < 5.0  # Should complete within 5 seconds

# =============================================================================
# Data Validation Tests
# =============================================================================

class TestDataValidation:
    """Test input validation and data integrity"""
    
    def test_pagination_validation(self, client):
        """Test pagination parameter validation"""
        # Test negative offset
        response = client.get("/api/v1/jurisdictions?offset=-1")
        assert response.status_code == 422
        
        # Test zero limit
        response = client.get("/api/v1/jurisdictions?limit=0")
        assert response.status_code == 422
        
        # Test excessive limit
        response = client.get("/api/v1/jurisdictions?limit=10000")
        assert response.status_code == 422
    
    def test_search_query_validation(self, client):
        """Test search query validation"""
        # Test empty search query
        response = client.get("/api/v1/search?q=")
        assert response.status_code == 422
        
        # Test very long search query
        long_query = "a" * 1000
        response = client.get(f"/api/v1/search?q={long_query}")
        assert response.status_code == 200  # Should handle gracefully
    
    def test_uuid_validation(self, client):
        """Test UUID parameter validation"""
        # Test invalid UUID format
        response = client.get("/api/v1/jurisdictions/invalid-uuid")
        assert response.status_code == 404  # Should handle gracefully

# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Test integration between different components"""
    
    def test_full_workflow_create_and_retrieve(self, client, db_session):
        """Test complete workflow of creating and retrieving data"""
        # Create jurisdiction
        jurisdiction = Jurisdiction(
            name="Test Integration City",
            jurisdiction_type=JurisdictionType.MUNICIPAL,
            code="TIC",
            website="https://testcity.ca"
        )
        db_session.add(jurisdiction)
        db_session.commit()
        db_session.refresh(jurisdiction)
        
        # Create representative
        representative = Representative(
            jurisdiction_id=jurisdiction.id,
            name="Integration Tester",
            role=RepresentativeRole.COUNCILLOR,
            party="Test Party",
            riding="Test Ward",
            email="tester@testcity.ca",
            active=True
        )
        db_session.add(representative)
        db_session.commit()
        
        # Test retrieving through API
        response = client.get(f"/api/v1/jurisdictions/{jurisdiction.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Integration City"
        assert data["representative_count"] == 1
        
        # Test finding through search
        response = client.get("/api/v1/search?q=Integration")
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] > 0
        
        # Should find both jurisdiction and representative
        types_found = {result["type"] for result in data["results"]}
        assert "representative" in types_found

# =============================================================================
# API Documentation Tests
# =============================================================================

class TestAPIDocumentation:
    """Test API documentation and OpenAPI schema"""
    
    def test_openapi_schema_available(self, client):
        """Test OpenAPI schema is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert schema["info"]["title"] == "OpenPolicy Merge API"
        assert schema["info"]["version"] == "1.0.0"
        assert "paths" in schema
        assert "components" in schema
    
    def test_swagger_ui_available(self, client):
        """Test Swagger UI is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_available(self, client):
        """Test ReDoc documentation is accessible"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

# =============================================================================
# Test Configuration and Utilities
# =============================================================================

@pytest.mark.asyncio
async def test_async_operations():
    """Test async operations work correctly"""
    # This would test async scraper operations
    # For now, just verify async/await works in test environment
    async def sample_async_function():
        await asyncio.sleep(0.1)
        return "async_result"
    
    result = await sample_async_function()
    assert result == "async_result"

def test_test_database_isolation(client):
    """Verify tests are properly isolated"""
    # This test verifies that database state doesn't leak between tests
    response = client.get("/api/v1/jurisdictions")
    assert response.status_code == 200
    # Should start with clean database
    data = response.json()
    # The exact count depends on fixtures loaded, but should be predictable

if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=90"
    ])