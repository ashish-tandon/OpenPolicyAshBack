"""
Scraper Manager

This module manages the execution of all Canadian civic data scrapers and
coordinates data storage in the OpenPolicy Database.
"""

import sys
import os
import json
import importlib.util
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

# Add scrapers directory to path
scrapers_path = str(Path(__file__).parent.parent.parent / "scrapers")
sys.path.insert(0, scrapers_path)

from database import (
    create_engine_from_config, get_session_factory, get_database_config,
    Jurisdiction, Representative, ScrapingRun, DataQualityIssue,
    JurisdictionType, RepresentativeRole
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperError(Exception):
    """Custom exception for scraper errors"""
    pass

class ScraperManager:
    """Manages the execution of all Canadian civic data scrapers"""
    
    def __init__(self):
        self.db_config = get_database_config()
        self.engine = create_engine_from_config(self.db_config.get_url())
        self.Session = get_session_factory(self.engine)
        self.scrapers_base_path = Path(scrapers_path)
        
    def load_regions_report(self) -> Dict[str, Any]:
        """Load the regions report from JSON file"""
        report_path = Path("regions_report.json")
        if not report_path.exists():
            raise FileNotFoundError("regions_report.json not found. Run region_analyzer.py first.")
        
        with open(report_path, 'r') as f:
            return json.load(f)
    
    def load_scraper_module(self, scraper_directory: str) -> Tuple[Optional[Any], Optional[str]]:
        """Dynamically load a scraper module"""
        try:
            scraper_path = self.scrapers_base_path / scraper_directory
            people_file = scraper_path / 'people.py'
            
            if not people_file.exists():
                return None, f"No people.py file found in {scraper_directory}"
            
            # Load the module
            spec = importlib.util.spec_from_file_location(f"{scraper_directory}_people", people_file)
            module = importlib.util.module_from_spec(spec)
            
            # Execute the module
            spec.loader.exec_module(module)
            
            # Find the scraper class
            scraper_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and 
                    name.endswith('PersonScraper') and 
                    name not in ['CanadianScraper', 'CSVScraper']):
                    scraper_class = obj
                    break
            
            if scraper_class is None:
                return None, f"No valid scraper class found in {scraper_directory}"
            
            return scraper_class, None
            
        except Exception as e:
            return None, f"Failed to load scraper {scraper_directory}: {str(e)}"
    
    def extract_person_data(self, person_obj: Any) -> Dict[str, Any]:
        """Extract data from a person object returned by scrapers"""
        data = {}
        
        # Basic fields
        for field in ['name', 'role', 'party', 'district', 'image']:
            if hasattr(person_obj, field):
                data[field] = getattr(person_obj, field)
        
        # Contact details
        if hasattr(person_obj, 'contact_details'):
            for contact in person_obj.contact_details:
                if hasattr(contact, 'type') and hasattr(contact, 'value'):
                    if contact.type == 'email':
                        data['email'] = contact.value
                    elif contact.type == 'voice':
                        data['phone'] = contact.value
                    elif contact.type == 'address':
                        data['office_address'] = contact.value
        
        # Links (social media, website)
        if hasattr(person_obj, 'links'):
            for link in person_obj.links:
                if hasattr(link, 'url'):
                    url = link.url.lower()
                    if 'facebook.com' in url:
                        data['facebook_url'] = link.url
                    elif 'twitter.com' in url or 'x.com' in url:
                        data['twitter_url'] = link.url
                    elif 'instagram.com' in url:
                        data['instagram_url'] = link.url
                    elif 'linkedin.com' in url:
                        data['linkedin_url'] = link.url
                    else:
                        data['website'] = link.url
        
        # Sources
        if hasattr(person_obj, 'sources'):
            data['source_url'] = person_obj.sources[0].url if person_obj.sources else None
        
        # Other attributes that might be useful
        for attr in dir(person_obj):
            if (not attr.startswith('_') and 
                not callable(getattr(person_obj, attr)) and
                attr not in ['name', 'role', 'party', 'district', 'image', 'contact_details', 'links', 'sources']):
                value = getattr(person_obj, attr)
                if value is not None and str(value).strip():
                    data[f'extra_{attr}'] = str(value)
        
        return data
    
    def map_role_to_enum(self, role_str: str) -> RepresentativeRole:
        """Map role string to enum"""
        if not role_str:
            return RepresentativeRole.OTHER
        
        role_str = role_str.upper()
        if 'MP' in role_str and 'MPP' not in role_str:
            return RepresentativeRole.MP
        elif 'MPP' in role_str:
            return RepresentativeRole.MPP
        elif 'MLA' in role_str:
            return RepresentativeRole.MLA
        elif 'MNA' in role_str:
            return RepresentativeRole.MNA
        elif 'MAYOR' in role_str:
            return RepresentativeRole.MAYOR
        elif 'COUNCILLOR' in role_str or 'COUNCILOR' in role_str:
            return RepresentativeRole.COUNCILLOR
        elif 'REEVE' in role_str:
            return RepresentativeRole.REEVE
        else:
            return RepresentativeRole.OTHER
    
    def run_scraper(self, jurisdiction: Jurisdiction, scraper_directory: str, 
                   max_records: Optional[int] = None, test_mode: bool = False) -> Dict[str, Any]:
        """Run a single scraper and return results"""
        result = {
            'jurisdiction_id': str(jurisdiction.id),
            'jurisdiction_name': jurisdiction.name,
            'scraper_directory': scraper_directory,
            'status': 'failed',
            'error': None,
            'records_processed': 0,
            'records_created': 0,
            'records_updated': 0,
            'data_sample': []
        }
        
        try:
            # Load scraper
            scraper_class, error = self.load_scraper_module(scraper_directory)
            if error:
                result['error'] = error
                return result
            
            logger.info(f"Running scraper for {jurisdiction.name} ({scraper_directory})")
            
            # Create scraper instance
            scraper = scraper_class(jurisdiction.division_id or 'test-jurisdiction')
            
            # Get data from scraper
            people_data = []
            
            try:
                for person in scraper.scrape():
                    if max_records and len(people_data) >= max_records:
                        break
                    
                    person_data = self.extract_person_data(person)
                    people_data.append(person_data)
                    result['records_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error during scraping: {e}")
                result['error'] = f"Scraping error: {str(e)}"
                if people_data:  # If we got some data before the error
                    result['data_sample'] = people_data[:5]
                return result
            
            # Store sample data
            result['data_sample'] = people_data[:5]
            
            if not test_mode and people_data:
                # Store in database
                session = self.Session()
                try:
                    for person_data in people_data:
                        # Check if representative already exists
                        existing = session.query(Representative).filter_by(
                            jurisdiction_id=jurisdiction.id,
                            name=person_data.get('name', '')
                        ).first()
                        
                        if existing:
                            # Update existing record
                            for key, value in person_data.items():
                                if hasattr(existing, key) and value:
                                    setattr(existing, key, value)
                            result['records_updated'] += 1
                        else:
                            # Create new record
                            representative = Representative(
                                jurisdiction_id=jurisdiction.id,
                                name=person_data.get('name', ''),
                                role=self.map_role_to_enum(person_data.get('role', '')),
                                party=person_data.get('party'),
                                district=person_data.get('district'),
                                email=person_data.get('email'),
                                phone=person_data.get('phone'),
                                office_address=person_data.get('office_address'),
                                website=person_data.get('website'),
                                facebook_url=person_data.get('facebook_url'),
                                twitter_url=person_data.get('twitter_url'),
                                instagram_url=person_data.get('instagram_url'),
                                linkedin_url=person_data.get('linkedin_url'),
                                photo_url=person_data.get('image'),
                                source_url=person_data.get('source_url')
                            )
                            session.add(representative)
                            result['records_created'] += 1
                    
                    session.commit()
                    logger.info(f"Stored {result['records_created']} new and updated {result['records_updated']} representatives")
                    
                finally:
                    session.close()
            
            result['status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Unexpected error in scraper {scraper_directory}: {e}")
            result['error'] = f"Unexpected error: {str(e)}"
        
        return result
    
    def run_all_scrapers(self, max_records_per_scraper: Optional[int] = None, 
                        test_mode: bool = False, jurisdiction_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run all scrapers and return comprehensive results"""
        results = {
            'start_time': datetime.utcnow().isoformat(),
            'end_time': None,
            'total_jurisdictions': 0,
            'successful_scrapers': 0,
            'failed_scrapers': 0,
            'total_records_processed': 0,
            'total_records_created': 0,
            'total_records_updated': 0,
            'jurisdiction_results': [],
            'errors': []
        }
        
        try:
            # Load regions and jurisdictions
            regions = self.load_regions_report()
            session = self.Session()
            
            try:
                # Get jurisdictions from database
                query = session.query(Jurisdiction)
                if jurisdiction_types:
                    type_enums = [JurisdictionType(jt) for jt in jurisdiction_types]
                    query = query.filter(Jurisdiction.jurisdiction_type.in_(type_enums))
                
                jurisdictions = query.all()
                results['total_jurisdictions'] = len(jurisdictions)
                
                # Create mapping of jurisdiction to scraper directory
                jurisdiction_to_scraper = {}
                
                for region_type, regions_list in regions.items():
                    if region_type == 'disabled':
                        continue
                    
                    for region in regions_list:
                        # Find matching jurisdiction
                        scraper_dir = region['directory']
                        
                        for jurisdiction in jurisdictions:
                            if self._match_jurisdiction_to_scraper(jurisdiction, scraper_dir, region_type):
                                jurisdiction_to_scraper[jurisdiction.id] = scraper_dir
                                break
                
                logger.info(f"Found {len(jurisdiction_to_scraper)} jurisdiction-scraper mappings")
                
                # Run scrapers
                for jurisdiction in jurisdictions:
                    if jurisdiction.id not in jurisdiction_to_scraper:
                        logger.warning(f"No scraper found for jurisdiction: {jurisdiction.name}")
                        continue
                    
                    scraper_dir = jurisdiction_to_scraper[jurisdiction.id]
                    result = self.run_scraper(jurisdiction, scraper_dir, max_records_per_scraper, test_mode)
                    
                    results['jurisdiction_results'].append(result)
                    
                    if result['status'] == 'completed':
                        results['successful_scrapers'] += 1
                        results['total_records_processed'] += result['records_processed']
                        results['total_records_created'] += result['records_created']
                        results['total_records_updated'] += result['records_updated']
                    else:
                        results['failed_scrapers'] += 1
                        results['errors'].append({
                            'jurisdiction': jurisdiction.name,
                            'scraper': scraper_dir,
                            'error': result['error']
                        })
                
            finally:
                session.close()
        
        except Exception as e:
            logger.error(f"Error in run_all_scrapers: {e}")
            results['errors'].append(f"Global error: {str(e)}")
        
        results['end_time'] = datetime.utcnow().isoformat()
        return results
    
    def _match_jurisdiction_to_scraper(self, jurisdiction: Jurisdiction, 
                                     scraper_dir: str, region_type: str) -> bool:
        """Match a jurisdiction to its corresponding scraper directory"""
        if region_type == 'federal':
            return jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL
        
        elif region_type == 'provincial':
            if jurisdiction.jurisdiction_type != JurisdictionType.PROVINCIAL:
                return False
            
            # Extract province code from scraper directory
            if scraper_dir.startswith('ca_'):
                province_code = scraper_dir.split('_')[1]
                return jurisdiction.division_id and province_code in jurisdiction.division_id
        
        elif region_type == 'municipal':
            if jurisdiction.jurisdiction_type != JurisdictionType.MUNICIPAL:
                return False
            
            # For municipal, try to match based on name and province
            if scraper_dir.startswith('ca_'):
                parts = scraper_dir.split('_')
                if len(parts) >= 3:
                    province_code = parts[1]
                    city_code = '_'.join(parts[2:])
                    
                    # Check if province matches
                    if jurisdiction.division_id and province_code in jurisdiction.division_id:
                        # Check if city name roughly matches
                        city_name_normalized = city_code.replace('_', ' ').lower()
                        jurisdiction_name_normalized = jurisdiction.name.lower()
                        
                        return (city_name_normalized in jurisdiction_name_normalized or 
                               jurisdiction_name_normalized in city_name_normalized)
        
        return False