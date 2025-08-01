#!/usr/bin/env python3
"""
OpenPolicy Database Management Script

This script provides management commands for the OpenPolicy Database system.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from database import (
    create_engine_from_config, create_all_tables, get_session_factory,
    get_database_config, Jurisdiction, Representative, JurisdictionType
)
from scrapers.manager import ScraperManager
from scheduler.tasks import (
    run_test_scrapers, run_federal_scrapers, run_provincial_scrapers,
    run_municipal_scrapers, get_task_status, cancel_task
)

def init_database():
    """Initialize the database schema and load jurisdictions"""
    print("=== Initializing OpenPolicy Database ===")
    
    try:
        config = get_database_config()
        print(f"Connecting to database: {config.database} on {config.host}:{config.port}")
        
        engine = create_engine_from_config(config.get_url())
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful")
        
        # Create schema
        print("Creating database schema...")
        create_all_tables(engine)
        print("✅ Database schema created")
        
        # Load jurisdictions from regions report
        print("Loading jurisdictions...")
        load_jurisdictions(engine)
        print("✅ Database initialization completed")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    return True

def load_jurisdictions(engine):
    """Load jurisdictions from regions report"""
    Session = get_session_factory(engine)
    session = Session()
    
    try:
        # Check if jurisdictions already exist
        existing_count = session.query(Jurisdiction).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing jurisdictions. Skipping load.")
            return
        
        # Load from regions report
        report_path = Path("regions_report.json")
        if not report_path.exists():
            print("❌ regions_report.json not found. Run: python region_analyzer.py")
            return
        
        with open(report_path, 'r') as f:
            regions = json.load(f)
        
        # Province mapping
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
        
        jurisdictions_added = 0
        
        # Federal
        for region in regions.get('federal', []):
            jurisdiction = Jurisdiction(
                name='Canada',
                jurisdiction_type=JurisdictionType.FEDERAL,
                division_id='ocd-division/country:ca',
                province=None,
                url='https://www.ourcommons.ca/'
            )
            session.add(jurisdiction)
            jurisdictions_added += 1
        
        # Provincial
        for region in regions.get('provincial', []):
            directory = region['directory']
            if directory.startswith('ca_'):
                province_code = directory.split('_')[1]
                if province_code in province_map:
                    province_name, province_abbr = province_map[province_code]
                    jurisdiction = Jurisdiction(
                        name=province_name,
                        jurisdiction_type=JurisdictionType.PROVINCIAL,
                        division_id=f'ocd-division/country:ca/province:{province_code}',
                        province=province_abbr,
                        url=None
                    )
                    session.add(jurisdiction)
                    jurisdictions_added += 1
        
        # Municipal
        for region in regions.get('municipal', []):
            directory = region['directory']
            parts = directory.split('_')
            if len(parts) >= 3:
                province_code = parts[1]
                city_code = '_'.join(parts[2:])
                
                if province_code in province_map:
                    _, province_abbr = province_map[province_code]
                    city_name = region['name'].split(',')[0]
                    
                    jurisdiction = Jurisdiction(
                        name=city_name,
                        jurisdiction_type=JurisdictionType.MUNICIPAL,
                        division_id=f'ocd-division/country:ca/province:{province_code}/municipality:{city_code}',
                        province=province_abbr,
                        url=None
                    )
                    session.add(jurisdiction)
                    jurisdictions_added += 1
        
        session.commit()
        print(f"Added {jurisdictions_added} jurisdictions")
        
    finally:
        session.close()

def run_scrapers(jurisdiction_types=None, test_mode=False, max_records=None):
    """Run scrapers"""
    print(f"=== Running Scrapers ===")
    print(f"Jurisdiction types: {jurisdiction_types or 'All'}")
    print(f"Test mode: {test_mode}")
    print(f"Max records per scraper: {max_records or 'No limit'}")
    
    try:
        manager = ScraperManager()
        results = manager.run_all_scrapers(
            max_records_per_scraper=max_records,
            test_mode=test_mode,
            jurisdiction_types=jurisdiction_types
        )
        
        print("\n=== Results ===")
        print(f"Total jurisdictions: {results['total_jurisdictions']}")
        print(f"Successful scrapers: {results['successful_scrapers']}")
        print(f"Failed scrapers: {results['failed_scrapers']}")
        print(f"Total records processed: {results['total_records_processed']}")
        print(f"Total records created: {results['total_records_created']}")
        print(f"Total records updated: {results['total_records_updated']}")
        
        if results['errors']:
            print("\n=== Errors ===")
            for error in results['errors']:
                print(f"❌ {error['jurisdiction']} ({error['scraper']}): {error['error']}")
        
        # Save results
        with open(f"scraper_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        return results
        
    except Exception as e:
        print(f"❌ Scraper run failed: {e}")
        return None

def schedule_task(task_type):
    """Schedule a scraper task"""
    print(f"=== Scheduling {task_type} Task ===")
    
    task_map = {
        'test': run_test_scrapers,
        'federal': run_federal_scrapers,
        'provincial': run_provincial_scrapers,
        'municipal': run_municipal_scrapers
    }
    
    if task_type not in task_map:
        print(f"❌ Unknown task type: {task_type}")
        return None
    
    try:
        task = task_map[task_type].delay()
        print(f"✅ Task scheduled with ID: {task.id}")
        return task.id
    except Exception as e:
        print(f"❌ Failed to schedule task: {e}")
        return None

def check_task(task_id):
    """Check task status"""
    print(f"=== Checking Task {task_id} ===")
    
    try:
        status = get_task_status(task_id)
        print(f"Status: {status['status']}")
        
        if status['result']:
            print(f"Result: {json.dumps(status['result'], indent=2)}")
        
        if status['traceback']:
            print(f"Error: {status['traceback']}")
        
        return status
    except Exception as e:
        print(f"❌ Failed to check task: {e}")
        return None

def show_stats():
    """Show database statistics"""
    print("=== Database Statistics ===")
    
    try:
        config = get_database_config()
        engine = create_engine_from_config(config.get_url())
        Session = get_session_factory(engine)
        session = Session()
        
        try:
            # Jurisdiction counts
            total_jurisdictions = session.query(Jurisdiction).count()
            federal_count = session.query(Jurisdiction).filter_by(jurisdiction_type=JurisdictionType.FEDERAL).count()
            provincial_count = session.query(Jurisdiction).filter_by(jurisdiction_type=JurisdictionType.PROVINCIAL).count()
            municipal_count = session.query(Jurisdiction).filter_by(jurisdiction_type=JurisdictionType.MUNICIPAL).count()
            
            print(f"Jurisdictions: {total_jurisdictions}")
            print(f"  Federal: {federal_count}")
            print(f"  Provincial: {provincial_count}")
            print(f"  Municipal: {municipal_count}")
            
            # Representative counts
            total_reps = session.query(Representative).count()
            print(f"Representatives: {total_reps}")
            
            # By province
            province_counts = session.execute("""
                SELECT j.province, COUNT(r.id) as count
                FROM jurisdictions j
                LEFT JOIN representatives r ON j.id = r.jurisdiction_id
                WHERE j.province IS NOT NULL
                GROUP BY j.province
                ORDER BY count DESC
            """).fetchall()
            
            print("\nRepresentatives by Province:")
            for province, count in province_counts:
                print(f"  {province}: {count}")
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")

def main():
    parser = argparse.ArgumentParser(description='OpenPolicy Database Management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    subparsers.add_parser('init', help='Initialize database schema and load jurisdictions')
    
    # Run scrapers command
    run_parser = subparsers.add_parser('run', help='Run scrapers')
    run_parser.add_argument('--type', choices=['federal', 'provincial', 'municipal'], 
                          help='Jurisdiction type to scrape')
    run_parser.add_argument('--test', action='store_true', help='Run in test mode')
    run_parser.add_argument('--max-records', type=int, help='Maximum records per scraper')
    
    # Schedule command
    schedule_parser = subparsers.add_parser('schedule', help='Schedule scraper task')
    schedule_parser.add_argument('task_type', choices=['test', 'federal', 'provincial', 'municipal'],
                               help='Type of task to schedule')
    
    # Check task command
    check_parser = subparsers.add_parser('check', help='Check task status')
    check_parser.add_argument('task_id', help='Task ID to check')
    
    # Cancel task command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel task')
    cancel_parser.add_argument('task_id', help='Task ID to cancel')
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_database()
    elif args.command == 'run':
        jurisdiction_types = [args.type] if args.type else None
        run_scrapers(jurisdiction_types, args.test, args.max_records)
    elif args.command == 'schedule':
        schedule_task(args.task_type)
    elif args.command == 'check':
        check_task(args.task_id)
    elif args.command == 'cancel':
        task_id = args.task_id
        cancel_task(task_id)
        print(f"✅ Cancelled task {task_id}")
    elif args.command == 'stats':
        show_stats()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()