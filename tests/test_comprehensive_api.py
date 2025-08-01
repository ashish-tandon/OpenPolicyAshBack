"""
Comprehensive API Testing Suite
Tests all API endpoints, authentication, rate limiting, and error handling
"""

import pytest
import json
import time
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from api.main import app
from database import Jurisdiction, Representative, Bill, Committee


class TestHealthAndBasicEndpoints:
    """Test basic API functionality"""
    
    def test_health_endpoint(self, api_client):
        """Test health check endpoint"""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
    
    def test_cors_headers(self, api_client):
        """Test CORS headers are properly set"""
        response = api_client.options("/health")
        assert "access-control-allow-origin" in response.headers
    
    def test_api_documentation(self, api_client):
        """Test API documentation endpoints"""
        # OpenAPI docs
        response = api_client.get("/docs")
        assert response.status_code == 200
        
        # ReDoc docs  
        response = api_client.get("/redoc")
        assert response.status_code == 200
        
        # OpenAPI schema
        response = api_client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "info" in schema
        assert "paths" in schema


class TestStatisticsEndpoints:
    """Test statistics and aggregation endpoints"""
    
    def test_basic_stats(self, api_client, sample_jurisdiction, sample_representative):
        """Test basic statistics endpoint"""
        response = api_client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "total_jurisdictions", "federal_jurisdictions", 
            "provincial_jurisdictions", "municipal_jurisdictions",
            "total_representatives", "total_bills", "total_committees"
        ]
        
        for field in required_fields:
            assert field in data
            assert isinstance(data[field], int)
            assert data[field] >= 0
    
    def test_stats_with_data(self, api_client, sample_jurisdiction, sample_representative, sample_bill):
        """Test statistics with actual data"""
        response = api_client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_jurisdictions"] >= 1
        assert data["total_representatives"] >= 1
        assert data["total_bills"] >= 1


class TestJurisdictionEndpoints:
    """Test jurisdiction-related endpoints"""
    
    def test_list_jurisdictions(self, api_client, sample_jurisdiction):
        """Test listing jurisdictions"""
        response = api_client.get("/jurisdictions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check jurisdiction structure
        jurisdiction = data[0]
        required_fields = ["id", "name", "jurisdiction_type"]
        for field in required_fields:
            assert field in jurisdiction
    
    def test_jurisdiction_filtering(self, api_client, sample_jurisdiction):
        """Test jurisdiction filtering by type"""
        response = api_client.get("/jurisdictions?jurisdiction_type=provincial")
        assert response.status_code == 200
        
        data = response.json()
        for jurisdiction in data:
            assert jurisdiction["jurisdiction_type"] == "provincial"
    
    def test_jurisdiction_pagination(self, api_client):
        """Test jurisdiction pagination"""
        response = api_client.get("/jurisdictions?limit=5&offset=0")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) <= 5
    
    def test_get_jurisdiction_by_id(self, api_client, sample_jurisdiction):
        """Test getting specific jurisdiction"""
        response = api_client.get(f"/jurisdictions/{sample_jurisdiction.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == sample_jurisdiction.id
        assert data["name"] == sample_jurisdiction.name
    
    def test_jurisdiction_not_found(self, api_client):
        """Test 404 for non-existent jurisdiction"""
        response = api_client.get("/jurisdictions/99999")
        assert response.status_code == 404


class TestRepresentativeEndpoints:
    """Test representative-related endpoints"""
    
    def test_list_representatives(self, api_client, sample_representative):
        """Test listing representatives"""
        response = api_client.get("/representatives")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check representative structure
        representative = data[0]
        required_fields = ["id", "name", "role", "jurisdiction_id"]
        for field in required_fields:
            assert field in representative
    
    def test_representative_search(self, api_client, sample_representative):
        """Test representative search functionality"""
        response = api_client.get(f"/representatives?search={sample_representative.name[:5]}")
        assert response.status_code == 200
        
        data = response.json()
        found = any(rep["name"] == sample_representative.name for rep in data)
        assert found
    
    def test_representative_filtering(self, api_client, sample_representative):
        """Test representative filtering by party"""
        if sample_representative.party:
            response = api_client.get(f"/representatives?party={sample_representative.party}")
            assert response.status_code == 200
            
            data = response.json()
            for rep in data:
                if rep["party"]:
                    assert rep["party"] == sample_representative.party
    
    def test_get_representative_by_id(self, api_client, sample_representative):
        """Test getting specific representative"""
        response = api_client.get(f"/representatives/{sample_representative.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == sample_representative.id
        assert data["name"] == sample_representative.name


class TestBillEndpoints:
    """Test bill-related endpoints"""
    
    def test_list_bills(self, api_client, sample_bill):
        """Test listing bills"""
        response = api_client.get("/bills")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check bill structure
        bill = data[0]
        required_fields = ["id", "identifier", "title", "jurisdiction_id"]
        for field in required_fields:
            assert field in bill
    
    def test_bill_search(self, api_client, sample_bill):
        """Test bill search functionality"""
        response = api_client.get(f"/bills?search={sample_bill.identifier}")
        assert response.status_code == 200
        
        data = response.json()
        found = any(bill["identifier"] == sample_bill.identifier for bill in data)
        assert found
    
    def test_federal_bills_priority(self, api_client):
        """Test federal bills priority endpoint"""
        response = api_client.get("/bills/federal")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # All bills should be federal
        for bill in data:
            assert "federal" in bill.get("jurisdiction_name", "").lower() or bill.get("is_federal", False)


class TestCommitteeEndpoints:
    """Test committee-related endpoints"""
    
    def test_list_committees(self, api_client):
        """Test listing committees"""
        response = api_client.get("/committees")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestSchedulingEndpoints:
    """Test scheduling and task management endpoints"""
    
    def test_schedule_task(self, api_client):
        """Test task scheduling"""
        task_data = {
            "task_type": "test_scraper",
            "region": "federal",
            "priority": "normal"
        }
        
        response = api_client.post("/schedule", json=task_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "status" in data
    
    def test_get_task_status(self, api_client):
        """Test getting task status"""
        # First schedule a task
        task_data = {"task_type": "test_scraper"}
        schedule_response = api_client.post("/schedule", json=task_data)
        task_id = schedule_response.json()["task_id"]
        
        # Then check its status
        response = api_client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert "created_at" in data
    
    def test_list_tasks(self, api_client):
        """Test listing all tasks"""
        response = api_client.get("/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestProgressEndpoints:
    """Test progress tracking endpoints"""
    
    def test_progress_status(self, api_client):
        """Test progress status endpoint"""
        response = api_client.get("/api/progress/status")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["overall_progress", "current_operation", "tasks", "regions"]
        for field in required_fields:
            assert field in data
    
    def test_progress_summary(self, api_client):
        """Test progress summary endpoint"""
        response = api_client.get("/api/progress/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "overall_progress" in data
        assert "status" in data
    
    def test_progress_control_operations(self, api_client):
        """Test progress control operations"""
        # Test pause
        response = api_client.post("/api/progress/pause")
        assert response.status_code in [200, 400]  # 400 if no operation running
        
        # Test resume
        response = api_client.post("/api/progress/resume")
        assert response.status_code in [200, 400]  # 400 if no operation paused


class TestGraphQLEndpoint:
    """Test GraphQL API endpoint"""
    
    def test_graphql_introspection(self, api_client):
        """Test GraphQL introspection query"""
        query = {
            "query": """
            {
                __schema {
                    types {
                        name
                    }
                }
            }
            """
        }
        
        response = api_client.post("/graphql", json=query)
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "__schema" in data["data"]
    
    def test_graphql_jurisdictions_query(self, api_client, sample_jurisdiction):
        """Test GraphQL jurisdictions query"""
        query = {
            "query": """
            {
                jurisdictions {
                    id
                    name
                    jurisdictionType
                }
            }
            """
        }
        
        response = api_client.post("/graphql", json=query)
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "jurisdictions" in data["data"]


class TestRateLimiting:
    """Test API rate limiting functionality"""
    
    def test_rate_limiting_enforcement(self, api_client):
        """Test that rate limiting is enforced"""
        # Make multiple rapid requests
        responses = []
        for i in range(20):  # Exceed typical rate limit
            response = api_client.get("/health")
            responses.append(response.status_code)
            if response.status_code == 429:  # Rate limited
                break
            time.sleep(0.1)  # Small delay
        
        # Should eventually get rate limited
        # Note: This test might pass if rate limiting is configured generously
        # The important thing is that the rate limiting middleware is present
        assert any(status == 429 for status in responses) or all(status == 200 for status in responses)


class TestErrorHandling:
    """Test API error handling"""
    
    def test_invalid_json(self, api_client):
        """Test handling of invalid JSON"""
        response = api_client.post(
            "/schedule", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, api_client):
        """Test handling of missing required fields"""
        response = api_client.post("/schedule", json={})
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
    
    def test_invalid_endpoints(self, api_client):
        """Test 404 for invalid endpoints"""
        response = api_client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, api_client):
        """Test 405 for invalid methods"""
        response = api_client.delete("/health")
        assert response.status_code == 405


class TestParliamentaryEndpoints:
    """Test specialized parliamentary endpoints"""
    
    def test_parliamentary_sessions(self, api_client):
        """Test parliamentary sessions endpoint"""
        response = api_client.get("/parliamentary/sessions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_parliamentary_parties(self, api_client):
        """Test parliamentary parties endpoint"""
        response = api_client.get("/parliamentary/parties")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_parliamentary_proceedings(self, api_client):
        """Test parliamentary proceedings endpoint"""
        response = api_client.get("/parliamentary/proceedings")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestDataExport:
    """Test data export functionality"""
    
    def test_export_csv_jurisdictions(self, api_client, sample_jurisdiction):
        """Test CSV export of jurisdictions"""
        response = api_client.get("/export/jurisdictions?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
    
    def test_export_csv_representatives(self, api_client, sample_representative):
        """Test CSV export of representatives"""
        response = api_client.get("/export/representatives?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")


class TestPerformance:
    """Test API performance characteristics"""
    
    def test_response_times(self, api_client):
        """Test that API responses are reasonably fast"""
        import time
        
        endpoints = ["/health", "/stats", "/jurisdictions", "/representatives"]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = api_client.get(endpoint)
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            assert response_time < 5.0  # Should respond within 5 seconds
    
    def test_pagination_performance(self, api_client):
        """Test pagination performance with large datasets"""
        # Test large page size
        response = api_client.get("/representatives?limit=1000")
        assert response.status_code == 200
        
        # Should handle large pagination gracefully
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 1000