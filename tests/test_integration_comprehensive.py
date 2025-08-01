"""
Comprehensive Integration Testing Suite
Tests end-to-end workflows and system interactions
"""

import pytest
import asyncio
import json
import time
import tempfile
from unittest.mock import patch, Mock
from pathlib import Path
import subprocess
import requests
from datetime import datetime, timedelta

from database import create_all_tables, get_session_factory, get_database_config
from phased_loading import phased_loader, LoadingStrategy, LoadingPhase
from progress_tracker import progress_tracker


class TestSystemIntegration:
    """Test complete system integration"""
    
    def test_full_system_startup(self, services_running):
        """Test complete system startup sequence"""
        # Check that all required services are available
        required_services = ["database", "redis"]
        
        for service in required_services:
            if not services_running.get(service, False):
                pytest.skip(f"Required service {service} not available")
        
        # Test database connection
        assert services_running["database"]
        
        # Test Redis connection
        assert services_running["redis"]
        
        # Test API availability if running
        if services_running.get("api", False):
            response = requests.get("http://localhost:8000/health", timeout=5)
            assert response.status_code == 200
    
    def test_database_to_api_integration(self, db_session, sample_jurisdiction, api_client):
        """Test database to API integration"""
        # Create data in database
        jurisdiction_id = sample_jurisdiction.id
        jurisdiction_name = sample_jurisdiction.name
        
        # Query via API
        response = api_client.get(f"/jurisdictions/{jurisdiction_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == jurisdiction_name
    
    def test_scraper_to_database_integration(self, db_session, sample_jurisdiction):
        """Test scraper to database integration"""
        # This would test the complete flow from scraping to database storage
        # For now, we'll simulate the process
        
        # Test scraper manager initialization
        from scrapers.manager import ScraperManager
        scraper_manager = ScraperManager(db_session)
        
        # Test that scrapers can be listed
        available_scrapers = scraper_manager.get_available_scrapers()
        assert isinstance(available_scrapers, list)
    
    def test_progress_tracking_integration(self, test_redis):
        """Test progress tracking system integration"""
        # Test progress tracker initialization
        operation_name = "Integration Test Operation"
        progress_tracker.start_operation(operation_name)
        
        # Add a test task
        task_id = "integration_test_task"
        progress_tracker.add_task(task_id, "test", "Integration Test Task", 100)
        
        # Update progress
        progress_tracker.start_task(task_id, "Starting integration test")
        progress_tracker.update_task_progress(task_id, 50, "Halfway through test")
        progress_tracker.complete_task(task_id, success=True)
        
        # Get status
        status = progress_tracker.get_status()
        assert status is not None
        assert operation_name in str(status)


class TestPhasedLoadingIntegration:
    """Test phased loading system integration"""
    
    def test_phased_loading_lifecycle(self, test_database, test_redis):
        """Test complete phased loading lifecycle"""
        # Test starting a loading session
        session_id = phased_loader.start_phased_loading(
            strategy=LoadingStrategy.BALANCED,
            manual_controls=True
        )
        
        assert session_id is not None
        assert session_id.startswith("loading_")
        
        # Test getting status
        status = phased_loader.get_current_status()
        assert status["session_id"] == session_id
        assert status["strategy"] == "balanced"
        assert status["current_phase"]["phase_key"] == "preparation"
        
        # Test phase execution
        success = phased_loader.execute_current_phase()
        assert success
        
        # Verify phase advancement
        new_status = phased_loader.get_current_status()
        assert new_status["current_phase"]["phase_key"] == "federal_core"
        
        # Test pause/resume
        pause_success = phased_loader.pause_loading()
        assert pause_success
        
        paused_status = phased_loader.get_current_status()
        assert paused_status["status"] == "paused"
        
        resume_success = phased_loader.resume_loading()
        assert resume_success
        
        resumed_status = phased_loader.get_current_status()
        assert resumed_status["status"] == "running"
        
        # Test cancellation
        cancel_success = phased_loader.cancel_loading()
        assert cancel_success
        
        final_status = phased_loader.get_current_status()
        assert final_status["status"] == "no_session"
    
    def test_phased_loading_api_integration(self, api_client):
        """Test phased loading API integration"""
        # Test getting phases preview
        response = api_client.get("/api/phased-loading/phases/preview")
        assert response.status_code == 200
        
        data = response.json()
        assert "phases" in data
        assert "total_phases" in data
        assert len(data["phases"]) > 0
        
        # Test starting loading via API
        start_request = {
            "strategy": "balanced",
            "manual_controls": True
        }
        
        response = api_client.post("/api/phased-loading/start", json=start_request)
        assert response.status_code == 200
        
        start_data = response.json()
        assert start_data["success"] is True
        assert "session_id" in start_data
        
        # Test getting status via API
        response = api_client.get("/api/phased-loading/status")
        assert response.status_code == 200
        
        status_data = response.json()
        assert status_data["session_id"] == start_data["session_id"]
        
        # Test pause via API
        response = api_client.post("/api/phased-loading/pause")
        assert response.status_code == 200
        
        # Test resume via API
        response = api_client.post("/api/phased-loading/resume")
        assert response.status_code == 200
        
        # Test cancel via API
        response = api_client.post("/api/phased-loading/cancel")
        assert response.status_code == 200


class TestDataFlowIntegration:
    """Test complete data flow from scraping to API"""
    
    @patch('requests.get')
    def test_federal_data_flow(self, mock_get, db_session, api_client):
        """Test federal data flow integration"""
        # Mock federal data source
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "members": [
                {
                    "name": "John Test MP",
                    "party": "Test Party",
                    "riding": "Test Riding",
                    "email": "john@parl.gc.ca"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test that data flows through the system
        # This would typically involve:
        # 1. Scraping data from source
        # 2. Processing and validating data
        # 3. Storing in database
        # 4. Making available via API
        
        # For now, test API access to federal data
        response = api_client.get("/representatives?search=federal")
        assert response.status_code == 200
    
    def test_provincial_data_flow(self, db_session, api_client):
        """Test provincial data flow integration"""
        # Test provincial data availability
        response = api_client.get("/jurisdictions?jurisdiction_type=provincial")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_municipal_data_flow(self, db_session, api_client):
        """Test municipal data flow integration"""
        # Test municipal data availability
        response = api_client.get("/jurisdictions?jurisdiction_type=municipal")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestErrorHandlingIntegration:
    """Test error handling across system components"""
    
    def test_database_failure_handling(self, api_client):
        """Test handling of database failures"""
        # This would test what happens when database is unavailable
        # For now, test that API handles errors gracefully
        
        # Test with potentially invalid ID
        response = api_client.get("/jurisdictions/999999")
        assert response.status_code == 404
    
    def test_scraper_failure_handling(self, db_session):
        """Test handling of scraper failures"""
        # Test that scraper failures don't crash the system
        with patch('requests.get', side_effect=Exception("Network error")):
            # Scraping should handle the error gracefully
            pass
    
    def test_redis_failure_handling(self, api_client):
        """Test handling of Redis failures"""
        # Test that Redis failures don't crash the system
        # Progress tracking might be affected but system should continue
        response = api_client.get("/health")
        assert response.status_code == 200


class TestPerformanceIntegration:
    """Test system performance under various conditions"""
    
    def test_concurrent_api_requests(self, api_client):
        """Test handling of concurrent API requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            start_time = time.time()
            response = api_client.get("/health")
            end_time = time.time()
            results.append({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(results) == 10
        assert all(r["status_code"] == 200 for r in results)
        assert all(r["response_time"] < 5.0 for r in results)  # All under 5 seconds
    
    def test_large_dataset_handling(self, db_session, sample_jurisdiction):
        """Test handling of large datasets"""
        # Create a larger dataset for testing
        from database import Representative, RepresentativeRole
        
        # Add many representatives
        representatives = []
        for i in range(100):
            rep = Representative(
                name=f"Performance Test Rep {i}",
                role=RepresentativeRole.MP,
                party=f"Party {i % 5}",
                district=f"District {i}",
                jurisdiction_id=sample_jurisdiction.id
            )
            representatives.append(rep)
        
        # Bulk insert
        start_time = time.time()
        db_session.bulk_save_objects(representatives)
        db_session.commit()
        end_time = time.time()
        
        # Should complete reasonably quickly
        assert end_time - start_time < 10.0
        
        # Test querying large dataset
        start_time = time.time()
        results = db_session.query(Representative).filter_by(
            jurisdiction_id=sample_jurisdiction.id
        ).all()
        end_time = time.time()
        
        assert len(results) >= 100
        assert end_time - start_time < 5.0  # Query should be fast


class TestSecurityIntegration:
    """Test security aspects across system components"""
    
    def test_api_rate_limiting(self, api_client):
        """Test API rate limiting"""
        # Make many rapid requests
        responses = []
        for i in range(20):
            response = api_client.get("/health")
            responses.append(response.status_code)
            time.sleep(0.1)
        
        # Should either handle all requests or rate limit gracefully
        success_count = sum(1 for status in responses if status == 200)
        rate_limited_count = sum(1 for status in responses if status == 429)
        
        # All requests should either succeed or be rate limited
        assert success_count + rate_limited_count == len(responses)
    
    def test_input_validation(self, api_client):
        """Test input validation across APIs"""
        # Test invalid JSON
        response = api_client.post(
            "/api/phased-loading/start",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
        # Test invalid parameters
        response = api_client.get("/representatives?limit=invalid")
        assert response.status_code == 422
    
    def test_error_information_disclosure(self, api_client):
        """Test that errors don't disclose sensitive information"""
        # Test that error messages don't reveal system internals
        response = api_client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        
        # Error should not reveal sensitive system information
        error_text = response.text.lower()
        sensitive_terms = ["password", "secret", "key", "token", "internal"]
        
        for term in sensitive_terms:
            assert term not in error_text


class TestMonitoringIntegration:
    """Test monitoring and observability integration"""
    
    def test_health_check_integration(self, api_client):
        """Test health check endpoints"""
        # Test main health check
        response = api_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        
        # Test phased loading health check
        response = api_client.get("/api/phased-loading/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert "services" in health_data
    
    def test_metrics_collection(self, api_client):
        """Test metrics collection"""
        # Test statistics endpoints
        response = api_client.get("/stats")
        assert response.status_code == 200
        
        stats = response.json()
        required_metrics = [
            "total_jurisdictions", "total_representatives", 
            "total_bills", "total_committees"
        ]
        
        for metric in required_metrics:
            assert metric in stats
            assert isinstance(stats[metric], int)
    
    def test_logging_integration(self, caplog):
        """Test logging integration across components"""
        # Test that operations are properly logged
        operation_name = "Test Logging Operation"
        progress_tracker.start_operation(operation_name)
        
        # Check that operation was logged
        assert any(operation_name in record.message for record in caplog.records)


class TestBackupAndRecoveryIntegration:
    """Test backup and recovery procedures"""
    
    def test_session_persistence(self, temp_directory):
        """Test session persistence and recovery"""
        # Start a loading session
        session_id = phased_loader.start_phased_loading(
            strategy=LoadingStrategy.BALANCED
        )
        
        # Verify session is saved
        assert phased_loader.current_session is not None
        
        # Simulate system restart by creating new loader instance
        from phased_loading import PhasedLoader
        new_loader = PhasedLoader()
        
        # Should load existing session
        # Note: This test might need adjustment based on actual implementation
        pass
    
    def test_data_recovery_procedures(self, db_session):
        """Test data recovery procedures"""
        # This would test database backup/restore procedures
        # For now, test basic data integrity
        from database import Jurisdiction
        
        # Create test data
        jurisdiction = Jurisdiction(
            name="Recovery Test Jurisdiction",
            jurisdiction_type="municipal",
            division_id="ocd-division/country:ca/recovery-test"
        )
        
        db_session.add(jurisdiction)
        db_session.commit()
        
        # Verify data persists
        recovered = db_session.query(Jurisdiction).filter_by(
            name="Recovery Test Jurisdiction"
        ).first()
        
        assert recovered is not None
        assert recovered.name == "Recovery Test Jurisdiction"


class TestScalabilityIntegration:
    """Test system scalability characteristics"""
    
    def test_database_scaling(self, db_session, sample_jurisdiction):
        """Test database performance with larger datasets"""
        # This would test database performance under load
        # For now, test basic scaling characteristics
        
        from database import Representative, RepresentativeRole
        
        # Test batch operations
        batch_size = 50
        representatives = []
        
        for i in range(batch_size):
            rep = Representative(
                name=f"Scaling Test Rep {i}",
                role=RepresentativeRole.MP,
                jurisdiction_id=sample_jurisdiction.id
            )
            representatives.append(rep)
        
        # Time the batch insert
        start_time = time.time()
        db_session.bulk_save_objects(representatives)
        db_session.commit()
        end_time = time.time()
        
        # Should handle batch operations efficiently
        assert end_time - start_time < 5.0
        
        # Verify all data was inserted
        count = db_session.query(Representative).filter(
            Representative.name.like("Scaling Test Rep%")
        ).count()
        
        assert count == batch_size
    
    def test_api_scaling(self, api_client):
        """Test API performance under load"""
        # Test pagination with larger datasets
        response = api_client.get("/representatives?limit=100&offset=0")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 100  # Should respect limit
    
    def test_concurrent_loading_sessions(self):
        """Test handling of multiple loading sessions"""
        # Test that system properly handles concurrent operations
        # For now, test that only one session can run at a time
        
        try:
            session1 = phased_loader.start_phased_loading(LoadingStrategy.BALANCED)
            
            # Attempting to start another session should fail
            with pytest.raises(ValueError):
                session2 = phased_loader.start_phased_loading(LoadingStrategy.CONSERVATIVE)
        
        finally:
            # Clean up
            phased_loader.cancel_loading()


class TestDataConsistencyIntegration:
    """Test data consistency across system components"""
    
    def test_referential_integrity(self, db_session, sample_jurisdiction, sample_representative):
        """Test referential integrity across tables"""
        # Verify that relationships are maintained
        assert sample_representative.jurisdiction_id == sample_jurisdiction.id
        
        # Test that jurisdiction can access its representatives
        jurisdiction_reps = sample_jurisdiction.representatives
        assert sample_representative in jurisdiction_reps
    
    def test_data_synchronization(self, db_session, api_client, sample_jurisdiction):
        """Test data synchronization between database and API"""
        # Create data in database
        from database import Representative, RepresentativeRole
        
        rep = Representative(
            name="Sync Test Representative",
            role=RepresentativeRole.MP,
            party="Sync Test Party",
            jurisdiction_id=sample_jurisdiction.id
        )
        
        db_session.add(rep)
        db_session.commit()
        
        # Verify data is available via API
        response = api_client.get("/representatives?search=Sync Test")
        assert response.status_code == 200
        
        data = response.json()
        found = any(r["name"] == "Sync Test Representative" for r in data)
        assert found
    
    def test_transaction_consistency(self, db_session, sample_jurisdiction):
        """Test transaction consistency"""
        from database import Representative, Bill, RepresentativeRole
        
        # Test that transactions are properly handled
        try:
            # Start a transaction
            rep = Representative(
                name="Transaction Test Rep",
                role=RepresentativeRole.MP,
                jurisdiction_id=sample_jurisdiction.id
            )
            db_session.add(rep)
            
            bill = Bill(
                identifier="C-TRANS",
                title="Transaction Test Bill",
                jurisdiction_id=sample_jurisdiction.id
            )
            db_session.add(bill)
            
            # Commit transaction
            db_session.commit()
            
            # Verify both objects were saved
            saved_rep = db_session.query(Representative).filter_by(
                name="Transaction Test Rep"
            ).first()
            saved_bill = db_session.query(Bill).filter_by(
                identifier="C-TRANS"
            ).first()
            
            assert saved_rep is not None
            assert saved_bill is not None
            
        except Exception as e:
            # Should rollback on error
            db_session.rollback()
            raise e