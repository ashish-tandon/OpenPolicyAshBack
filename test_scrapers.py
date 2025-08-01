#!/usr/bin/env python3
import os
import sys
import json
import importlib.util
import traceback
from pathlib import Path

# Add scrapers directory to Python path
sys.path.insert(0, 'scrapers')

def load_scraper_module(scraper_path):
    """Load a scraper module dynamically"""
    try:
        # Get the people.py file
        people_file = Path(scraper_path) / 'people.py'
        if not people_file.exists():
            return None, "No people.py file found"
        
        # Load the module
        spec = importlib.util.spec_from_file_location("scraper_module", people_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find the scraper class
        scraper_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and 
                name.endswith('PersonScraper') and 
                name != 'CanadianScraper' and 
                name != 'CSVScraper'):
                scraper_class = obj
                break
        
        if scraper_class is None:
            return None, "No scraper class found"
        
        return scraper_class, None
    except Exception as e:
        return None, str(e)

def test_scraper(scraper_class, region_name, max_records=5):
    """Test a scraper and return sample data"""
    try:
        # Create scraper instance
        scraper = scraper_class('jurisdiction-id')
        
        # Get sample data
        data = []
        count = 0
        
        print(f"Testing {region_name}...")
        
        for person in scraper.scrape():
            if count >= max_records:
                break
            
            # Extract key fields from the person object
            person_data = {
                'name': getattr(person, 'name', 'Unknown'),
                'role': getattr(person, 'role', None),
                'party': getattr(person, 'party', None),
                'district': getattr(person, 'district', None),
                'email': None,
                'phone': None,
                'image': getattr(person, 'image', None)
            }
            
            # Extract contact information
            if hasattr(person, 'contact_details'):
                for contact in person.contact_details:
                    if contact.type == 'email':
                        person_data['email'] = contact.value
                    elif contact.type == 'voice':
                        person_data['phone'] = contact.value
            
            # Extract additional fields that might be present
            for attr in dir(person):
                if not attr.startswith('_') and attr not in person_data:
                    value = getattr(person, attr)
                    if not callable(value) and value is not None:
                        person_data[f'extra_{attr}'] = str(value)
            
            data.append(person_data)
            count += 1
        
        return data, None
        
    except Exception as e:
        return None, str(e)

def main():
    # Test a sample of scrapers from different categories
    test_cases = [
        ('scrapers/ca', 'Canada (Federal)'),
        ('scrapers/ca_on', 'Ontario (Provincial)'),
        ('scrapers/ca_on_toronto', 'Toronto, ON'),
        ('scrapers/ca_qc_montreal', 'Montreal, QC'),
        ('scrapers/ca_bc_vancouver', 'Vancouver, BC'),
        ('scrapers/ca_ab_calgary', 'Calgary, AB'),
    ]
    
    results = {}
    
    for scraper_path, region_name in test_cases:
        print(f"\n=== Testing {region_name} ===")
        
        # Load scraper
        scraper_class, error = load_scraper_module(scraper_path)
        if error:
            print(f"❌ Failed to load scraper: {error}")
            results[region_name] = {'error': error, 'data': None}
            continue
        
        # Test scraper
        data, error = test_scraper(scraper_class, region_name)
        if error:
            print(f"❌ Failed to run scraper: {error}")
            results[region_name] = {'error': error, 'data': None}
            continue
        
        print(f"✅ Successfully collected {len(data)} sample records")
        
        # Show sample data
        if data:
            print("Sample record:")
            for key, value in data[0].items():
                if value:
                    print(f"  {key}: {value}")
        
        results[region_name] = {'error': None, 'data': data}
    
    # Save results
    with open('scraper_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print(f"\n=== SUMMARY ===")
    successful = sum(1 for r in results.values() if r['error'] is None)
    total = len(results)
    print(f"Successful: {successful}/{total}")
    
    if successful > 0:
        print("\nData fields collected across all scrapers:")
        all_fields = set()
        for result in results.values():
            if result['data']:
                for record in result['data']:
                    all_fields.update(record.keys())
        
        for field in sorted(all_fields):
            print(f"  - {field}")

if __name__ == "__main__":
    main()