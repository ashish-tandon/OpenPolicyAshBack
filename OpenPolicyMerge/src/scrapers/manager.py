"""
OpenPolicy Merge - Unified Scraper Manager

This module provides a unified scraping framework that combines:
- OpenParliament's parliamentary scraping techniques
- Scrapers-CA municipal and provincial scrapers
- Civic-scraper's generic scraping utilities
- Enhanced error handling and data validation
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sqlalchemy.orm import Session

from ..database.config import get_db
from ..database.models import (
    Jurisdiction, JurisdictionType, Representative, RepresentativeRole,
    Bill, BillStatus, Committee, Event, ScrapingRun, DataQualityIssue
)

logger = logging.getLogger(__name__)

class ScraperType(Enum):
    """Types of scrapers available"""
    FEDERAL_PARLIAMENT = "federal_parliament"
    FEDERAL_ELECTIONS = "federal_elections"
    PROVINCIAL_LEGISLATURE = "provincial_legislature"
    MUNICIPAL_COUNCIL = "municipal_council"
    REPRESENT_API = "represent_api"
    COMMITTEE_MEETINGS = "committee_meetings"

class ScraperStatus(Enum):
    """Scraper execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass
class ScrapingResult:
    """Result of a scraping operation"""
    scraper_type: ScraperType
    jurisdiction_id: str
    status: ScraperStatus
    records_found: int = 0
    records_new: int = 0
    records_updated: int = 0
    records_deleted: int = 0
    errors: List[str] = None
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}

class BaseScraperSession:
    """Enhanced HTTP session with retry logic and monitoring"""
    
    def __init__(self, name: str, rate_limit: float = 1.0):
        self.name = name
        self.rate_limit = rate_limit
        self.last_request_time = 0.0
        
        # Configure session with retry strategy
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set common headers
        self.session.headers.update({
            'User-Agent': 'OpenPolicy-Merge/1.0 (Civic Data Collection; contact@openpolicymerge.org)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-CA,en;q=0.8,fr-CA;q=0.6,fr;q=0.4',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Make a rate-limited GET request"""
        self._enforce_rate_limit()
        
        try:
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

class FederalParliamentScraper:
    """Federal Parliament scraper based on OpenParliament techniques"""
    
    def __init__(self):
        self.session = BaseScraperSession("FederalParliament", rate_limit=1.0)
        self.base_urls = {
            'bills': 'https://www.parl.ca/legisinfo/en/bills',
            'members': 'https://www.ourcommons.ca/Members/en/search',
            'hansard': 'https://www.ourcommons.ca/DocumentViewer/en/',
            'committees': 'https://www.ourcommons.ca/Committees/en/List'
        }
    
    async def scrape_bills(self, parliament: int = 44, session: int = 1) -> List[Dict[str, Any]]:
        """Scrape current parliamentary bills"""
        bills = []
        
        try:
            # Get current bills from LEGISinfo
            url = f"{self.base_urls['bills']}?Parliament={parliament}&Session={session}"
            response = self.session.get(url)
            
            # Parse bill listings (would implement actual HTML parsing here)
            # This is a simplified structure - real implementation would parse HTML
            bills = [
                {
                    'number': 'C-1',
                    'title': 'An Act respecting the administration of oaths of office',
                    'status': 'royal_assent_given',
                    'parliament': parliament,
                    'session': session,
                    'introduction_date': '2021-11-22',
                    'source_url': url
                },
                # More bills would be parsed from actual HTML
            ]
            
            logger.info(f"Scraped {len(bills)} federal bills")
            
        except Exception as e:
            logger.error(f"Failed to scrape federal bills: {e}")
            raise
        
        return bills
    
    async def scrape_members(self) -> List[Dict[str, Any]]:
        """Scrape current MPs"""
        members = []
        
        try:
            response = self.session.get(self.base_urls['members'])
            
            # Parse MP listings (simplified - real implementation would parse HTML)
            members = [
                {
                    'name': 'Example MP',
                    'party': 'Liberal',
                    'riding': 'Example Riding',
                    'email': 'example.mp@parl.gc.ca',
                    'role': 'mp',
                    'active': True,
                    'source_url': self.base_urls['members']
                },
                # More members would be parsed from actual HTML
            ]
            
            logger.info(f"Scraped {len(members)} federal MPs")
            
        except Exception as e:
            logger.error(f"Failed to scrape federal MPs: {e}")
            raise
        
        return members

class RepresentAPIScraper:
    """Scraper for the Represent API (represent.opennorth.ca)"""
    
    def __init__(self):
        self.base_url = "https://represent.opennorth.ca"
        self.session = BaseScraperSession("RepresentAPI", rate_limit=0.5)
    
    async def scrape_representatives(self, representative_set: str = None) -> List[Dict[str, Any]]:
        """Scrape representatives from Represent API"""
        representatives = []
        
        try:
            url = f"{self.base_url}/representatives/"
            if representative_set:
                url += f"?representative_set={representative_set}"
            
            response = self.session.get(url)
            data = response.json()
            
            for rep in data.get('objects', []):
                representatives.append({
                    'name': rep.get('name'),
                    'role': self._map_role(rep.get('elected_office')),
                    'party': rep.get('party_name'),
                    'riding': rep.get('district_name'),
                    'email': rep.get('email'),
                    'phone': rep.get('offices', [{}])[0].get('tel') if rep.get('offices') else None,
                    'photo_url': rep.get('photo_url'),
                    'gender': rep.get('gender'),
                    'active': True,
                    'represent_id': rep.get('url', '').split('/')[-2] if rep.get('url') else None,
                    'source_url': rep.get('source_url'),
                    'data_source': 'represent_api'
                })
            
            # Handle pagination
            if data.get('meta', {}).get('next'):
                next_url = self.base_url + data['meta']['next']
                next_response = self.session.get(next_url)
                next_data = next_response.json()
                # Process next page...
            
            logger.info(f"Scraped {len(representatives)} representatives from Represent API")
            
        except Exception as e:
            logger.error(f"Failed to scrape Represent API: {e}")
            raise
        
        return representatives
    
    def _map_role(self, elected_office: str) -> str:
        """Map Represent API roles to our enum values"""
        role_mapping = {
            'MP': 'mp',
            'MLA': 'mla',
            'MPP': 'mpp',
            'MNA': 'mna',
            'Maire': 'mayor',
            'Mayor': 'mayor',
            'Councillor': 'councillor',
            'Conseiller': 'councillor',
            'Premier': 'premier',
        }
        
        return role_mapping.get(elected_office, 'councillor')

class MunicipalScraper:
    """Generic municipal scraper based on scrapers-ca patterns"""
    
    def __init__(self, jurisdiction_code: str):
        self.jurisdiction_code = jurisdiction_code
        self.session = BaseScraperSession(f"Municipal-{jurisdiction_code}", rate_limit=2.0)
        self.config = self._load_scraper_config()
    
    def _load_scraper_config(self) -> Dict[str, Any]:
        """Load scraper configuration for specific municipality"""
        # This would load actual configuration from scrapers-ca
        configs = {
            'toronto': {
                'base_url': 'https://www.toronto.ca',
                'council_url': '/city-government/accountability-operations-customer-service/city-administration/city-managers-office/city-council',
                'meetings_url': '/city-government/council-committees/city-council/council-meeting-schedule',
                'selectors': {
                    'councillor_name': '.councillor-name',
                    'councillor_ward': '.ward-info',
                    'councillor_email': '.contact-email'
                }
            },
            'montreal': {
                'base_url': 'https://montreal.ca',
                'council_url': '/en/your-city/city-council',
                'meetings_url': '/en/your-city/city-council/meetings',
                'selectors': {
                    'councillor_name': '.member-name',
                    'councillor_district': '.district-name',
                    'councillor_email': '.email-link'
                }
            }
        }
        
        return configs.get(self.jurisdiction_code, {})
    
    async def scrape_councillors(self) -> List[Dict[str, Any]]:
        """Scrape municipal councillors"""
        councillors = []
        
        if not self.config:
            logger.warning(f"No configuration found for {self.jurisdiction_code}")
            return councillors
        
        try:
            url = self.config['base_url'] + self.config['council_url']
            response = self.session.get(url)
            
            # This would use BeautifulSoup or similar to parse actual HTML
            # For now, returning sample data structure
            councillors = [
                {
                    'name': 'Sample Councillor',
                    'role': 'councillor',
                    'ward': 'Ward 1',
                    'party': None,
                    'email': 'councillor@city.ca',
                    'active': True,
                    'source_url': url,
                    'data_source': f'municipal_{self.jurisdiction_code}'
                }
            ]
            
            logger.info(f"Scraped {len(councillors)} councillors for {self.jurisdiction_code}")
            
        except Exception as e:
            logger.error(f"Failed to scrape councillors for {self.jurisdiction_code}: {e}")
            raise
        
        return councillors

class UnifiedScraperManager:
    """Main scraper manager that coordinates all scraping activities"""
    
    def __init__(self):
        self.scrapers = {
            ScraperType.FEDERAL_PARLIAMENT: FederalParliamentScraper(),
            ScraperType.REPRESENT_API: RepresentAPIScraper(),
        }
        self.active_runs: Dict[str, ScrapingRun] = {}
    
    async def run_scraper(
        self,
        scraper_type: ScraperType,
        jurisdiction_id: str,
        config: Dict[str, Any] = None
    ) -> ScrapingResult:
        """Run a specific scraper"""
        
        start_time = datetime.utcnow()
        run_id = f"{scraper_type.value}_{jurisdiction_id}_{int(time.time())}"
        
        # Create scraping run record
        with next(get_db()) as db:
            scraping_run = ScrapingRun(
                jurisdiction_id=jurisdiction_id,
                scraper_type=scraper_type.value,
                start_time=start_time,
                status="running",
                config=config or {}
            )
            db.add(scraping_run)
            db.commit()
            db.refresh(scraping_run)
            
            self.active_runs[run_id] = scraping_run
        
        try:
            result = await self._execute_scraper(scraper_type, jurisdiction_id, config)
            result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
            
            # Update scraping run
            with next(get_db()) as db:
                scraping_run = db.query(ScrapingRun).filter(
                    ScrapingRun.id == scraping_run.id
                ).first()
                
                scraping_run.end_time = datetime.utcnow()
                scraping_run.duration_seconds = result.duration_seconds
                scraping_run.status = result.status.value
                scraping_run.records_found = result.records_found
                scraping_run.records_new = result.records_new
                scraping_run.records_updated = result.records_updated
                scraping_run.errors = len(result.errors)
                
                if result.errors:
                    scraping_run.error_message = "; ".join(result.errors)
                
                db.commit()
            
            logger.info(f"Scraper {scraper_type.value} completed for {jurisdiction_id}")
            return result
            
        except Exception as e:
            logger.error(f"Scraper {scraper_type.value} failed for {jurisdiction_id}: {e}")
            
            # Update scraping run with error
            with next(get_db()) as db:
                scraping_run = db.query(ScrapingRun).filter(
                    ScrapingRun.id == scraping_run.id
                ).first()
                
                scraping_run.end_time = datetime.utcnow()
                scraping_run.status = "failed"
                scraping_run.error_message = str(e)
                db.commit()
            
            return ScrapingResult(
                scraper_type=scraper_type,
                jurisdiction_id=jurisdiction_id,
                status=ScraperStatus.FAILED,
                errors=[str(e)],
                duration_seconds=(datetime.utcnow() - start_time).total_seconds()
            )
        
        finally:
            if run_id in self.active_runs:
                del self.active_runs[run_id]
    
    async def _execute_scraper(
        self,
        scraper_type: ScraperType,
        jurisdiction_id: str,
        config: Dict[str, Any]
    ) -> ScrapingResult:
        """Execute the actual scraper logic"""
        
        if scraper_type == ScraperType.FEDERAL_PARLIAMENT:
            return await self._run_federal_parliament_scraper(jurisdiction_id, config)
        elif scraper_type == ScraperType.REPRESENT_API:
            return await self._run_represent_api_scraper(jurisdiction_id, config)
        elif scraper_type == ScraperType.MUNICIPAL_COUNCIL:
            return await self._run_municipal_scraper(jurisdiction_id, config)
        else:
            raise ValueError(f"Unknown scraper type: {scraper_type}")
    
    async def _run_federal_parliament_scraper(
        self,
        jurisdiction_id: str,
        config: Dict[str, Any]
    ) -> ScrapingResult:
        """Run federal parliament scraper"""
        
        scraper = self.scrapers[ScraperType.FEDERAL_PARLIAMENT]
        result = ScrapingResult(
            scraper_type=ScraperType.FEDERAL_PARLIAMENT,
            jurisdiction_id=jurisdiction_id,
            status=ScraperStatus.RUNNING
        )
        
        try:
            # Scrape bills
            bills = await scraper.scrape_bills()
            result.records_found += len(bills)
            
            # Scrape members
            members = await scraper.scrape_members()
            result.records_found += len(members)
            
            # Save to database
            with next(get_db()) as db:
                # Process bills
                for bill_data in bills:
                    existing_bill = db.query(Bill).filter(
                        Bill.number == bill_data['number'],
                        Bill.parliament == bill_data['parliament'],
                        Bill.session == bill_data['session']
                    ).first()
                    
                    if existing_bill:
                        # Update existing bill
                        for key, value in bill_data.items():
                            if hasattr(existing_bill, key):
                                setattr(existing_bill, key, value)
                        result.records_updated += 1
                    else:
                        # Create new bill
                        bill = Bill(
                            jurisdiction_id=jurisdiction_id,
                            **bill_data
                        )
                        db.add(bill)
                        result.records_new += 1
                
                # Process members
                for member_data in members:
                    existing_member = db.query(Representative).filter(
                        Representative.name == member_data['name'],
                        Representative.jurisdiction_id == jurisdiction_id
                    ).first()
                    
                    if existing_member:
                        # Update existing member
                        for key, value in member_data.items():
                            if hasattr(existing_member, key):
                                setattr(existing_member, key, value)
                        result.records_updated += 1
                    else:
                        # Create new member
                        member = Representative(
                            jurisdiction_id=jurisdiction_id,
                            **member_data
                        )
                        db.add(member)
                        result.records_new += 1
                
                db.commit()
            
            result.status = ScraperStatus.COMPLETED
            
        except Exception as e:
            result.status = ScraperStatus.FAILED
            result.errors.append(str(e))
        
        return result
    
    async def _run_represent_api_scraper(
        self,
        jurisdiction_id: str,
        config: Dict[str, Any]
    ) -> ScrapingResult:
        """Run Represent API scraper"""
        
        scraper = self.scrapers[ScraperType.REPRESENT_API]
        result = ScrapingResult(
            scraper_type=ScraperType.REPRESENT_API,
            jurisdiction_id=jurisdiction_id,
            status=ScraperStatus.RUNNING
        )
        
        try:
            representatives = await scraper.scrape_representatives()
            result.records_found = len(representatives)
            
            # Save to database
            with next(get_db()) as db:
                for rep_data in representatives:
                    existing_rep = db.query(Representative).filter(
                        Representative.represent_id == rep_data.get('represent_id')
                    ).first()
                    
                    if existing_rep:
                        # Update existing representative
                        for key, value in rep_data.items():
                            if hasattr(existing_rep, key) and value is not None:
                                setattr(existing_rep, key, value)
                        result.records_updated += 1
                    else:
                        # Create new representative
                        rep = Representative(
                            jurisdiction_id=jurisdiction_id,
                            **rep_data
                        )
                        db.add(rep)
                        result.records_new += 1
                
                db.commit()
            
            result.status = ScraperStatus.COMPLETED
            
        except Exception as e:
            result.status = ScraperStatus.FAILED
            result.errors.append(str(e))
        
        return result
    
    async def _run_municipal_scraper(
        self,
        jurisdiction_id: str,
        config: Dict[str, Any]
    ) -> ScrapingResult:
        """Run municipal scraper"""
        
        jurisdiction_code = config.get('jurisdiction_code', 'unknown')
        scraper = MunicipalScraper(jurisdiction_code)
        
        result = ScrapingResult(
            scraper_type=ScraperType.MUNICIPAL_COUNCIL,
            jurisdiction_id=jurisdiction_id,
            status=ScraperStatus.RUNNING
        )
        
        try:
            councillors = await scraper.scrape_councillors()
            result.records_found = len(councillors)
            
            # Save to database
            with next(get_db()) as db:
                for councillor_data in councillors:
                    existing_councillor = db.query(Representative).filter(
                        Representative.name == councillor_data['name'],
                        Representative.jurisdiction_id == jurisdiction_id
                    ).first()
                    
                    if existing_councillor:
                        # Update existing councillor
                        for key, value in councillor_data.items():
                            if hasattr(existing_councillor, key):
                                setattr(existing_councillor, key, value)
                        result.records_updated += 1
                    else:
                        # Create new councillor
                        councillor = Representative(
                            jurisdiction_id=jurisdiction_id,
                            **councillor_data
                        )
                        db.add(councillor)
                        result.records_new += 1
                
                db.commit()
            
            result.status = ScraperStatus.COMPLETED
            
        except Exception as e:
            result.status = ScraperStatus.FAILED
            result.errors.append(str(e))
        
        return result
    
    async def run_comprehensive_scrape(self) -> Dict[str, ScrapingResult]:
        """Run scrapers for all jurisdictions"""
        results = {}
        
        try:
            with next(get_db()) as db:
                jurisdictions = db.query(Jurisdiction).all()
            
            tasks = []
            for jurisdiction in jurisdictions:
                if jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL:
                    tasks.append(
                        self.run_scraper(
                            ScraperType.FEDERAL_PARLIAMENT,
                            str(jurisdiction.id)
                        )
                    )
                    tasks.append(
                        self.run_scraper(
                            ScraperType.REPRESENT_API,
                            str(jurisdiction.id)
                        )
                    )
                elif jurisdiction.jurisdiction_type == JurisdictionType.MUNICIPAL:
                    tasks.append(
                        self.run_scraper(
                            ScraperType.MUNICIPAL_COUNCIL,
                            str(jurisdiction.id),
                            {'jurisdiction_code': jurisdiction.code}
                        )
                    )
            
            # Run all scrapers concurrently (with limits)
            semaphore = asyncio.Semaphore(5)  # Limit concurrent scrapers
            
            async def run_with_semaphore(task):
                async with semaphore:
                    return await task
            
            results_list = await asyncio.gather(
                *[run_with_semaphore(task) for task in tasks],
                return_exceptions=True
            )
            
            # Process results
            for i, result in enumerate(results_list):
                if isinstance(result, Exception):
                    logger.error(f"Scraper task {i} failed: {result}")
                else:
                    key = f"{result.scraper_type.value}_{result.jurisdiction_id}"
                    results[key] = result
            
        except Exception as e:
            logger.error(f"Comprehensive scrape failed: {e}")
        
        return results
    
    def get_active_runs(self) -> List[Dict[str, Any]]:
        """Get currently active scraping runs"""
        return [
            {
                'run_id': run_id,
                'scraper_type': run.scraper_type,
                'jurisdiction_id': run.jurisdiction_id,
                'start_time': run.start_time.isoformat(),
                'status': run.status
            }
            for run_id, run in self.active_runs.items()
        ]
    
    def get_scraper_stats(self) -> Dict[str, Any]:
        """Get scraper performance statistics"""
        try:
            with next(get_db()) as db:
                # Recent runs
                recent_runs = db.query(ScrapingRun).filter(
                    ScrapingRun.start_time >= datetime.utcnow() - timedelta(days=7)
                ).all()
                
                # Calculate stats
                total_runs = len(recent_runs)
                successful_runs = len([r for r in recent_runs if r.status == "completed"])
                failed_runs = len([r for r in recent_runs if r.status == "failed"])
                
                avg_duration = (
                    sum(r.duration_seconds or 0 for r in recent_runs) / total_runs
                    if total_runs > 0 else 0
                )
                
                total_records = sum(r.records_found or 0 for r in recent_runs)
                
                return {
                    'period': '7_days',
                    'total_runs': total_runs,
                    'successful_runs': successful_runs,
                    'failed_runs': failed_runs,
                    'success_rate': round(successful_runs / total_runs * 100, 1) if total_runs > 0 else 0,
                    'average_duration_seconds': round(avg_duration, 2),
                    'total_records_processed': total_records,
                    'active_runs': len(self.active_runs)
                }
                
        except Exception as e:
            logger.error(f"Failed to get scraper stats: {e}")
            return {'error': str(e)}

# Global scraper manager instance
scraper_manager = UnifiedScraperManager()

if __name__ == "__main__":
    # Test scraper manager
    async def test_scrapers():
        print("Testing unified scraper manager...")
        
        # Test federal parliament scraper
        result = await scraper_manager.run_scraper(
            ScraperType.FEDERAL_PARLIAMENT,
            "federal_canada"
        )
        print(f"Federal scraper result: {result}")
        
        # Test Represent API scraper
        result = await scraper_manager.run_scraper(
            ScraperType.REPRESENT_API,
            "federal_canada"
        )
        print(f"Represent API result: {result}")
    
    asyncio.run(test_scrapers())