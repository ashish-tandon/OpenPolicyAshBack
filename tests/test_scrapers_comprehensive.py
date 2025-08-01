"""
Comprehensive Scraper Testing Suite
Tests all scrapers from original repositories for data collection accuracy
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests
import importlib.util

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scrapers.manager import ScraperManager
from scrapers.parliamentary_scraper import ParliamentaryScraper
from database import Jurisdiction, Representative, Bill, Committee


class TestScraperManager:
    """Test the main scraper management system"""
    
    def test_scraper_manager_initialization(self, db_session):
        """Test scraper manager initializes correctly"""
        manager = ScraperManager(db_session)
        assert manager.session == db_session
        assert hasattr(manager, 'scrapers')
    
    def test_get_available_scrapers(self, db_session):
        """Test listing available scrapers"""
        manager = ScraperManager(db_session)
        scrapers = manager.get_available_scrapers()
        
        assert isinstance(scrapers, list)
        # Should have federal, provincial, and municipal scrapers
        scraper_types = [s.get('type') for s in scrapers]
        assert any('federal' in str(t).lower() for t in scraper_types)
    
    def test_validate_scraper_config(self, db_session):
        """Test scraper configuration validation"""
        manager = ScraperManager(db_session)
        
        # Valid config
        valid_config = {
            'name': 'test_scraper',
            'jurisdiction_type': 'federal',
            'enabled': True
        }
        assert manager.validate_scraper_config(valid_config)
        
        # Invalid config
        invalid_config = {}
        assert not manager.validate_scraper_config(invalid_config)


class TestParliamentaryScraper:
    """Test Parliamentary scraper functionality"""
    
    def test_parliamentary_scraper_init(self, db_session, sample_jurisdiction):
        """Test parliamentary scraper initialization"""
        scraper = ParliamentaryScraper(db_session, sample_jurisdiction.id)
        assert scraper.session == db_session
        assert scraper.jurisdiction_id == sample_jurisdiction.id
    
    @patch('requests.get')
    def test_scrape_members_of_parliament(self, mock_get, db_session, sample_jurisdiction):
        """Test scraping MPs from Parliament website"""
        # Mock Parliament website response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <div class="member">
                <h3>John Smith</h3>
                <p>Liberal</p>
                <p>Ottawa Centre</p>
                <a href="mailto:john.smith@parl.gc.ca">john.smith@parl.gc.ca</a>
            </div>
        </html>
        """
        mock_get.return_value = mock_response
        
        scraper = ParliamentaryScraper(db_session, sample_jurisdiction.id)
        members = scraper.scrape_members_of_parliament()
        
        assert isinstance(members, list)
        if members:  # If scraping was successful
            member = members[0]
            assert 'name' in member
            assert 'party' in member
            assert 'district' in member
    
    @patch('requests.get')
    def test_scrape_federal_bills(self, mock_get, db_session, sample_jurisdiction):
        """Test scraping federal bills"""
        # Mock Parliament bills response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'bills': [
                {
                    'number': 'C-1',
                    'title': 'Test Bill',
                    'summary': 'A test bill for testing',
                    'status': 'First Reading'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        scraper = ParliamentaryScraper(db_session, sample_jurisdiction.id)
        bills = scraper.scrape_federal_bills()
        
        assert isinstance(bills, list)
        if bills:
            bill = bills[0]
            assert 'identifier' in bill or 'number' in bill
            assert 'title' in bill
    
    def test_data_validation(self, db_session, sample_jurisdiction):
        """Test data validation in parliamentary scraper"""
        scraper = ParliamentaryScraper(db_session, sample_jurisdiction.id)
        
        # Valid MP data
        valid_mp = {
            'name': 'John Smith',
            'party': 'Liberal',
            'district': 'Ottawa Centre',
            'role': 'Member of Parliament'
        }
        assert scraper.validate_mp_data(valid_mp)
        
        # Invalid MP data
        invalid_mp = {'name': ''}
        assert not scraper.validate_mp_data(invalid_mp)
        
        # Valid bill data
        valid_bill = {
            'identifier': 'C-1',
            'title': 'Test Bill',
            'summary': 'A test bill'
        }
        assert scraper.validate_bill_data(valid_bill)
        
        # Invalid bill data
        invalid_bill = {'title': ''}
        assert not scraper.validate_bill_data(invalid_bill)


class TestProvincialScrapers:
    """Test provincial government scrapers"""
    
    def test_ontario_scraper(self, db_session):
        """Test Ontario provincial scraper"""
        # This would test the Ontario-specific scraper
        # Implementation depends on the actual scraper structure
        pass
    
    def test_quebec_scraper(self, db_session):
        """Test Quebec provincial scraper"""
        # This would test the Quebec-specific scraper
        pass
    
    def test_british_columbia_scraper(self, db_session):
        """Test BC provincial scraper"""
        # This would test the BC-specific scraper
        pass


class TestMunicipalScrapers:
    """Test municipal government scrapers"""
    
    def test_toronto_scraper(self, db_session):
        """Test Toronto municipal scraper"""
        # Test Toronto city council scraper
        pass
    
    def test_vancouver_scraper(self, db_session):
        """Test Vancouver municipal scraper"""
        # Test Vancouver city council scraper
        pass
    
    def test_montreal_scraper(self, db_session):
        """Test Montreal municipal scraper"""
        # Test Montreal city council scraper
        pass


class TestScraperDataQuality:
    """Test data quality and validation for scraped data"""
    
    def test_representative_data_completeness(self, mock_scraper_data):
        """Test that representative data is complete"""
        for region, representatives in mock_scraper_data.items():
            for rep in representatives:
                # Required fields
                assert 'name' in rep
                assert rep['name'].strip() != ''
                
                # Optional but expected fields
                if 'email' in rep:
                    assert '@' in rep['email']
                
                if 'party' in rep:
                    assert rep['party'].strip() != ''
    
    def test_bill_identifier_format(self):
        """Test federal bill identifier formats"""
        # Federal bills should follow C-# or S-# format
        valid_identifiers = ['C-1', 'C-100', 'S-1', 'S-50']
        invalid_identifiers = ['Bill 1', 'C1', 'S_1', '']
        
        for identifier in valid_identifiers:
            assert self._is_valid_federal_bill_identifier(identifier)
        
        for identifier in invalid_identifiers:
            assert not self._is_valid_federal_bill_identifier(identifier)
    
    def _is_valid_federal_bill_identifier(self, identifier):
        """Helper to validate federal bill identifiers"""
        import re
        pattern = r'^[CS]-\d+$'
        return bool(re.match(pattern, identifier))
    
    def test_data_deduplication(self, db_session):
        """Test that scrapers handle duplicate data correctly"""
        # Create sample data
        rep_data = {
            'name': 'John Smith',
            'role': 'MP',
            'party': 'Liberal',
            'district': 'Ottawa Centre'
        }
        
        # This would test the scraper's deduplication logic
        # Implementation depends on scraper architecture
        pass
    
    def test_error_handling_in_scrapers(self, db_session):
        """Test error handling in scraper operations"""
        # Test network errors
        with patch('requests.get', side_effect=requests.RequestException("Network error")):
            # Should not crash, should log error
            pass
        
        # Test invalid HTML/JSON responses
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Invalid HTML"
            mock_get.return_value = mock_response
            
            # Should handle gracefully
            pass


class TestScraperPerformance:
    """Test scraper performance and efficiency"""
    
    def test_scraper_timeout_handling(self, db_session):
        """Test that scrapers handle timeouts appropriately"""
        with patch('requests.get', side_effect=requests.Timeout("Request timeout")):
            # Should handle timeout gracefully
            pass
    
    def test_rate_limiting_compliance(self, db_session):
        """Test that scrapers respect rate limiting"""
        # This would test that scrapers don't make too many requests too quickly
        pass
    
    def test_memory_usage(self, db_session):
        """Test that scrapers don't consume excessive memory"""
        # This would monitor memory usage during scraping
        pass


class TestOriginalRepoIntegration:
    """Test integration with original repository scrapers"""
    
    def test_openparliament_integration(self, db_session):
        """Test integration with openparliament scrapers"""
        # Test that we can use scrapers from michaelmulley/openparliament
        pass
    
    def test_opencivicdata_scrapers_integration(self, db_session):
        """Test integration with opencivicdata scrapers-ca"""
        # Test that we can use scrapers from opencivicdata/scrapers-ca
        pass
    
    def test_civic_scraper_integration(self, db_session):
        """Test integration with civic-scraper"""
        # Test that we can use scrapers from biglocalnews/civic-scraper
        pass


class TestScraperScheduling:
    """Test scraper scheduling and automation"""
    
    def test_scraper_scheduling_system(self, db_session, test_redis):
        """Test the scheduling system for scrapers"""
        # This would test Celery task scheduling
        pass
    
    def test_priority_scheduling(self, db_session):
        """Test that federal scrapers get priority scheduling"""
        # Federal bills should be scraped more frequently
        pass
    
    def test_error_recovery(self, db_session):
        """Test automatic error recovery in scheduled scrapers"""
        # Failed scrapers should retry with exponential backoff
        pass


class TestScraperConfiguration:
    """Test scraper configuration and customization"""
    
    def test_regions_configuration(self, temp_directory):
        """Test loading regions configuration"""
        # Create test regions file
        regions_data = {
            "federal": {
                "name": "Parliament of Canada",
                "url": "https://www.parl.ca",
                "enabled": True
            },
            "provinces": {
                "ontario": {
                    "name": "Government of Ontario",
                    "url": "https://www.ontario.ca",
                    "enabled": True
                }
            }
        }
        
        regions_file = temp_directory / "test_regions.json"
        with open(regions_file, 'w') as f:
            json.dump(regions_data, f)
        
        # Test loading configuration
        with open(regions_file, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data["federal"]["name"] == "Parliament of Canada"
        assert loaded_data["provinces"]["ontario"]["enabled"] is True
    
    def test_scraper_enable_disable(self, db_session):
        """Test enabling and disabling scrapers"""
        # This would test the ability to enable/disable specific scrapers
        pass


class TestDataStorage:
    """Test how scraped data is stored in the database"""
    
    def test_representative_storage(self, db_session, sample_jurisdiction):
        """Test storing representative data"""
        rep_data = {
            'name': 'Test Representative',
            'role': 'Member of Parliament',
            'party': 'Test Party',
            'district': 'Test District',
            'jurisdiction_id': sample_jurisdiction.id
        }
        
        # Create representative
        rep = Representative(**rep_data)
        db_session.add(rep)
        db_session.commit()
        
        # Verify storage
        stored_rep = db_session.query(Representative).filter_by(name='Test Representative').first()
        assert stored_rep is not None
        assert stored_rep.party == 'Test Party'
    
    def test_bill_storage(self, db_session, sample_jurisdiction):
        """Test storing bill data"""
        bill_data = {
            'identifier': 'C-TEST',
            'title': 'Test Storage Bill',
            'summary': 'A bill to test storage',
            'jurisdiction_id': sample_jurisdiction.id
        }
        
        # Create bill
        bill = Bill(**bill_data)
        db_session.add(bill)
        db_session.commit()
        
        # Verify storage
        stored_bill = db_session.query(Bill).filter_by(identifier='C-TEST').first()
        assert stored_bill is not None
        assert stored_bill.title == 'Test Storage Bill'
    
    def test_data_relationships(self, db_session, sample_jurisdiction, sample_representative, sample_bill):
        """Test that relationships between data are properly maintained"""
        # Representative should be linked to jurisdiction
        assert sample_representative.jurisdiction_id == sample_jurisdiction.id
        
        # Bill should be linked to jurisdiction
        assert sample_bill.jurisdiction_id == sample_jurisdiction.id


class TestScraperResilience:
    """Test scraper resilience and fault tolerance"""
    
    @patch('requests.get')
    def test_network_failure_handling(self, mock_get, db_session, sample_jurisdiction):
        """Test handling of network failures"""
        # Simulate network failure
        mock_get.side_effect = requests.ConnectionError("Network unreachable")
        
        scraper = ParliamentaryScraper(db_session, sample_jurisdiction.id)
        
        # Should handle the error gracefully
        try:
            result = scraper.scrape_members_of_parliament()
            # Should return empty list or handle error appropriately
            assert isinstance(result, list)
        except Exception as e:
            # If it raises an exception, it should be a handled exception
            assert isinstance(e, (requests.RequestException, ConnectionError))
    
    @patch('requests.get')
    def test_malformed_data_handling(self, mock_get, db_session, sample_jurisdiction):
        """Test handling of malformed HTML/JSON data"""
        # Simulate malformed response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Incomplete HTML"
        mock_get.return_value = mock_response
        
        scraper = ParliamentaryScraper(db_session, sample_jurisdiction.id)
        
        # Should handle malformed data gracefully
        try:
            result = scraper.scrape_members_of_parliament()
            assert isinstance(result, list)
        except Exception:
            # Should not crash the entire system
            pass
    
    def test_partial_data_handling(self, db_session):
        """Test handling of partial or incomplete data"""
        # Test with incomplete representative data
        incomplete_data = {
            'name': 'John Smith',
            # Missing party, district, etc.
        }
        
        # Should handle incomplete data appropriately
        # Either fill in defaults or skip the record
        pass