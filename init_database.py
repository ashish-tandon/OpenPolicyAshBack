#!/usr/bin/env python3
"""
Database Initialization Script

This script creates the database schema and populates initial data.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from database import (
    create_engine_from_config, create_all_tables, get_session_factory,
    get_database_config, Jurisdiction, JurisdictionType
)

def load_jurisdictions_from_report():
    """Load jurisdictions from the regions report"""
    jurisdictions = []
    
    try:
        with open('regions_report.json', 'r') as f:
            regions = json.load(f)
        
        # Federal jurisdiction
        for region in regions.get('federal', []):
            jurisdictions.append({
                'name': 'Canada',
                'jurisdiction_type': JurisdictionType.FEDERAL,
                'division_id': 'ocd-division/country:ca',
                'province': None,
                'url': 'https://www.ourcommons.ca/',
                'scraper_directory': region['directory']
            })
        
        # Provincial jurisdictions
        province_map = {
            'ab': ('Alberta', 'AB'),
            'bc': ('British Columbia', 'BC'),
            'mb': ('Manitoba', 'MB'),
            'nb': ('New Brunswick', 'NB'),
            'nl': ('Newfoundland and Labrador', 'NL'),
            'ns': ('Nova Scotia', 'NS'),
            'nt': ('Northwest Territories', 'NT'),
            'nu': ('Nunavut', 'NU'),
            'on': ('Ontario', 'ON'),
            'pe': ('Prince Edward Island', 'PE'),
            'qc': ('Quebec', 'QC'),
            'sk': ('Saskatchewan', 'SK'),
            'yt': ('Yukon', 'YT')
        }
        
        for region in regions.get('provincial', []):
            directory = region['directory']
            if directory.startswith('ca_'):
                province_code = directory.split('_')[1]
                if province_code in province_map:
                    province_name, province_abbr = province_map[province_code]
                    jurisdictions.append({
                        'name': province_name,
                        'jurisdiction_type': JurisdictionType.PROVINCIAL,
                        'division_id': f'ocd-division/country:ca/province:{province_code}',
                        'province': province_abbr,
                        'url': None,  # To be filled in later
                        'scraper_directory': directory
                    })
        
        # Municipal jurisdictions
        for region in regions.get('municipal', []):
            directory = region['directory']
            parts = directory.split('_')
            if len(parts) >= 3:
                province_code = parts[1]
                city_code = '_'.join(parts[2:])
                
                if province_code in province_map:
                    _, province_abbr = province_map[province_code]
                    city_name = region['name'].split(',')[0]  # Get city name before province
                    
                    jurisdictions.append({
                        'name': city_name,
                        'jurisdiction_type': JurisdictionType.MUNICIPAL,
                        'division_id': f'ocd-division/country:ca/province:{province_code}/municipality:{city_code}',
                        'province': province_abbr,
                        'url': None,  # To be filled in later
                        'scraper_directory': directory
                    })
        
        return jurisdictions
    
    except FileNotFoundError:
        print("regions_report.json not found. Please run region_analyzer.py first.")
        return []

def main():
    print("=== OpenPolicy Database Initialization ===")
    
    # Get database configuration
    config = get_database_config()
    print(f"Connecting to database: {config.database} on {config.host}:{config.port}")
    
    # Create engine and session factory
    engine = create_engine_from_config(config.get_url())
    Session = get_session_factory(engine)
    
    try:
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful")
        
        # Create all tables
        print("Creating database schema...")
        create_all_tables(engine)
        print("✅ Database schema created successfully")
        
        # Load and insert jurisdictions
        print("Loading jurisdictions...")
        jurisdictions_data = load_jurisdictions_from_report()
        
        if not jurisdictions_data:
            print("❌ No jurisdictions data found")
            return
        
        session = Session()
        
        try:
            # Check if jurisdictions already exist
            existing_count = session.query(Jurisdiction).count()
            
            if existing_count > 0:
                print(f"Found {existing_count} existing jurisdictions. Skipping insert.")
            else:
                # Insert jurisdictions
                for jur_data in jurisdictions_data:
                    jurisdiction = Jurisdiction(
                        name=jur_data['name'],
                        jurisdiction_type=jur_data['jurisdiction_type'],
                        division_id=jur_data['division_id'],
                        province=jur_data['province'],
                        url=jur_data['url']
                    )
                    session.add(jurisdiction)
                
                session.commit()
                print(f"✅ Inserted {len(jurisdictions_data)} jurisdictions")
            
            # Print summary
            federal_count = session.query(Jurisdiction).filter_by(jurisdiction_type=JurisdictionType.FEDERAL).count()
            provincial_count = session.query(Jurisdiction).filter_by(jurisdiction_type=JurisdictionType.PROVINCIAL).count()
            municipal_count = session.query(Jurisdiction).filter_by(jurisdiction_type=JurisdictionType.MUNICIPAL).count()
            
            print(f"\n=== JURISDICTION SUMMARY ===")
            print(f"Federal: {federal_count}")
            print(f"Provincial: {provincial_count}")
            print(f"Municipal: {municipal_count}")
            print(f"Total: {federal_count + provincial_count + municipal_count}")
            
        finally:
            session.close()
    
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return 1
    
    print("\n✅ Database initialization completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())