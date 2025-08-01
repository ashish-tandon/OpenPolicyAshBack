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
from progress_tracker import progress_tracker, TaskStatus, TaskType

def init_database():
    """Initialize the database schema and load jurisdictions"""
    print("=== Initializing OpenPolicy Database ===")
    
    # Start progress tracking
    progress_tracker.start_operation("Database Initialization")
    
    # Add database initialization tasks
    db_init_task = progress_tracker.add_task(
        "db_init", TaskType.DATABASE_INIT, "Database Schema Creation", 5
    )
    jurisdiction_task = progress_tracker.add_task(
        "jurisdiction_load", TaskType.DATABASE_INIT, "Loading Jurisdictions", 100
    )
    
    try:
        # Step 1: Get config
        progress_tracker.start_task("db_init", "Getting database configuration")
        config = get_database_config()
        print(f"Connecting to database: {config.database} on {config.host}:{config.port}")
        progress_tracker.update_task_progress("db_init", 20, "Database config loaded")
        
        # Step 2: Create engine
        progress_tracker.update_task_progress("db_init", 40, "Creating database engine")
        engine = create_engine_from_config(config.get_url())
        
        # Step 3: Test connection
        progress_tracker.update_task_progress("db_init", 60, "Testing database connection")
        with engine.connect() as conn:
            print("✅ Database connection successful")
        
        # Step 4: Create schema
        progress_tracker.update_task_progress("db_init", 80, "Creating database schema")
        print("Creating database schema...")
        create_all_tables(engine)
        print("✅ Database schema created")
        
        # Complete database creation
        progress_tracker.complete_task("db_init", success=True)
        
        # Step 5: Load jurisdictions with progress tracking
        progress_tracker.start_task("jurisdiction_load", "Loading Canadian jurisdictions")
        print("Loading jurisdictions...")
        load_jurisdictions_with_progress(engine)
        print("✅ Database initialization completed")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Mark current task as failed
        if progress_tracker.current_task:
            progress_tracker.complete_task(progress_tracker.current_task, success=False, error_message=str(e))
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

def load_jurisdictions_with_progress(engine):
    """Load jurisdictions from regions report with progress tracking"""
    Session = get_session_factory(engine)
    session = Session()
    
    try:
        # Check if jurisdictions already exist
        progress_tracker.update_task_progress("jurisdiction_load", 5, "Checking existing jurisdictions")
        existing_count = session.query(Jurisdiction).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing jurisdictions. Skipping load.")
            progress_tracker.complete_task("jurisdiction_load", success=True)
            return
        
        # Load from regions report
        progress_tracker.update_task_progress("jurisdiction_load", 10, "Loading regions report")
        report_path = Path("regions_report.json")
        if not report_path.exists():
            print("❌ regions_report.json not found. Run: python region_analyzer.py")
            progress_tracker.complete_task("jurisdiction_load", success=False, 
                                         error_message="regions_report.json not found")
            return
        
        with open(report_path, 'r') as f:
            regions = json.load(f)
        
        # Count total jurisdictions to process
        total_jurisdictions = (len(regions.get('federal', [])) + 
                             len(regions.get('provincial', [])) + 
                             len(regions.get('municipal', [])))
        
        progress_tracker.update_task_progress("jurisdiction_load", 15, 
                                            f"Found {total_jurisdictions} jurisdictions to process")
        
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
        processed = 0
        
        # Federal
        for region in regions.get('federal', []):
            processed += 1
            progress = 15 + (processed / total_jurisdictions) * 75
            progress_tracker.update_task_progress("jurisdiction_load", progress, 
                                                "Processing federal jurisdiction")
            
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
            processed += 1
            progress = 15 + (processed / total_jurisdictions) * 75
            directory = region['directory']
            province_name = "Unknown Province"
            if directory.startswith('ca_'):
                province_code = directory.split('_')[1]
                if province_code in province_map:
                    province_name, _ = province_map[province_code]
            
            progress_tracker.update_task_progress("jurisdiction_load", progress, 
                                                f"Processing province: {province_name}")
            
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
            processed += 1
            progress = 15 + (processed / total_jurisdictions) * 75
            directory = region['directory']
            city_name = region['name'].split(',')[0] if ',' in region['name'] else region['name']
            
            progress_tracker.update_task_progress("jurisdiction_load", progress, 
                                                f"Processing municipality: {city_name}")
            
            parts = directory.split('_')
            if len(parts) >= 3:
                province_code = parts[1]
                city_code = '_'.join(parts[2:])
                
                if province_code in province_map:
                    _, province_abbr = province_map[province_code]
                    
                    jurisdiction = Jurisdiction(
                        name=city_name,
                        jurisdiction_type=JurisdictionType.MUNICIPAL,
                        division_id=f'ocd-division/country:ca/province:{province_code}/municipality:{city_code}',
                        province=province_abbr,
                        url=None
                    )
                    session.add(jurisdiction)
                    jurisdictions_added += 1
        
        progress_tracker.update_task_progress("jurisdiction_load", 95, "Committing changes to database")
        session.commit()
        print(f"Added {jurisdictions_added} jurisdictions")
        
        progress_tracker.complete_task("jurisdiction_load", success=True)
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error loading jurisdictions: {e}")
        progress_tracker.complete_task("jurisdiction_load", success=False, error_message=str(e))
        raise
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

def run_scrapers_with_progress(jurisdiction_types=None, test_mode=False, max_records=None):
    """Run scrapers with comprehensive progress tracking"""
    print(f"=== Running Scrapers with Progress Tracking ===")
    print(f"Jurisdiction types: {jurisdiction_types or 'All'}")
    print(f"Test mode: {test_mode}")
    print(f"Max records per scraper: {max_records or 'No limit'}")
    
    # Start progress tracking for scraping operation
    operation_name = "Test Scraping" if test_mode else "Full Regional Scraping"
    progress_tracker.start_operation(operation_name)
    
    try:
        # Get database configuration
        config = get_database_config()
        engine = create_engine_from_config(config.get_url())
        Session = get_session_factory(engine)
        session = Session()
        
        # Get all jurisdictions
        jurisdictions = session.query(Jurisdiction).all()
        session.close()
        
        # Group jurisdictions by region/province
        regions = {}
        federal_jurisdictions = []
        
        for jurisdiction in jurisdictions:
            if jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL:
                federal_jurisdictions.append(jurisdiction)
            elif jurisdiction.jurisdiction_type in [JurisdictionType.PROVINCIAL, JurisdictionType.MUNICIPAL]:
                province = jurisdiction.province or 'unknown'
                if province not in regions:
                    regions[province] = {
                        'name': jurisdiction.name if jurisdiction.jurisdiction_type == JurisdictionType.PROVINCIAL else province,
                        'jurisdictions': []
                    }
                regions[province]['jurisdictions'].append(jurisdiction)
        
        # Add federal region if we have federal jurisdictions
        if federal_jurisdictions:
            regions['federal'] = {
                'name': 'Federal Government',
                'jurisdictions': federal_jurisdictions
            }
        
        # Filter regions based on jurisdiction_types
        if jurisdiction_types:
            filtered_regions = {}
            for region_code, region_data in regions.items():
                if region_code == 'federal' and 'federal' in jurisdiction_types:
                    filtered_regions[region_code] = region_data
                elif region_code != 'federal' and ('provincial' in jurisdiction_types or 'municipal' in jurisdiction_types):
                    # Filter jurisdictions within the region
                    filtered_jurisdictions = []
                    for j in region_data['jurisdictions']:
                        if ('provincial' in jurisdiction_types and j.jurisdiction_type == JurisdictionType.PROVINCIAL) or \
                           ('municipal' in jurisdiction_types and j.jurisdiction_type == JurisdictionType.MUNICIPAL):
                            filtered_jurisdictions.append(j)
                    if filtered_jurisdictions:
                        filtered_regions[region_code] = {
                            'name': region_data['name'],
                            'jurisdictions': filtered_jurisdictions
                        }
            regions = filtered_regions
        
        print(f"🌍 Found {len(regions)} regions to process")
        
        # Create tasks and regions for progress tracking
        region_task_mapping = {}
        for region_code, region_data in regions.items():
            task_id = f"scrape_{region_code}"
            region_task_mapping[region_code] = task_id
            
            # Add task for this region
            progress_tracker.add_task(
                task_id,
                TaskType.REGION_SCRAPE,
                f"Scraping {region_data['name']}",
                len(region_data['jurisdictions'])
            )
            
            # Add region tracking
            progress_tracker.add_region(
                region_code,
                region_data['name'],
                [task_id]
            )
        
        # Initialize scraper manager
        manager = ScraperManager()
        results = {}
        
        # Process each region
        for region_code, region_data in regions.items():
            task_id = region_task_mapping[region_code]
            
            # Check for cancellation
            if progress_tracker.should_cancel():
                print("🛑 Scraping cancelled by user")
                break
            
            # Check if this task should be skipped
            if progress_tracker.should_skip_task(task_id):
                print(f"⏭️ Skipping region: {region_data['name']}")
                continue
            
            # Wait if paused
            while progress_tracker.should_pause():
                print(f"⏸️ Scraping paused for {region_data['name']}. Waiting for resume...")
                import time
                time.sleep(1)
            
            # Start the task
            progress_tracker.start_task(task_id, f"Initializing scraping for {region_data['name']}")
            
            try:
                jurisdictions_in_region = region_data['jurisdictions']
                completed_jurisdictions = 0
                
                progress_tracker.update_task_progress(
                    task_id, 5, 
                    f"Starting {len(jurisdictions_in_region)} jurisdictions in {region_data['name']}"
                )
                
                region_results = {
                    'successful_scrapers': 0,
                    'failed_scrapers': 0,
                    'total_records_processed': 0,
                    'total_records_created': 0,
                    'total_records_updated': 0,
                    'errors': []
                }
                
                # Process each jurisdiction in the region
                for jurisdiction in jurisdictions_in_region:
                    # Check for pause/cancel again
                    if progress_tracker.should_cancel():
                        break
                    
                    while progress_tracker.should_pause():
                        import time
                        time.sleep(1)
                    
                    try:
                        # Update progress
                        progress = 10 + (completed_jurisdictions / len(jurisdictions_in_region)) * 85
                        progress_tracker.update_task_progress(
                            task_id, progress,
                            f"Scraping {jurisdiction.name}"
                        )
                        
                        # Run scraper for this jurisdiction
                        result = manager.run_scraper_for_jurisdiction(
                            jurisdiction,
                            test_mode=test_mode,
                            max_records=max_records
                        )
                        
                        if result.get('success', False):
                            region_results['successful_scrapers'] += 1
                            region_results['total_records_processed'] += result.get('records_processed', 0)
                            region_results['total_records_created'] += result.get('records_created', 0)
                            region_results['total_records_updated'] += result.get('records_updated', 0)
                        else:
                            region_results['failed_scrapers'] += 1
                            region_results['errors'].append({
                                'jurisdiction': jurisdiction.name,
                                'error': result.get('error', 'Unknown error')
                            })
                        
                    except Exception as e:
                        region_results['failed_scrapers'] += 1
                        region_results['errors'].append({
                            'jurisdiction': jurisdiction.name,
                            'error': str(e)
                        })
                    
                    completed_jurisdictions += 1
                
                # Complete the task
                if progress_tracker.should_cancel():
                    progress_tracker.complete_task(task_id, success=False, error_message="Cancelled by user")
                else:
                    progress_tracker.complete_task(task_id, success=True)
                
                results[region_code] = region_results
                
                print(f"✅ Completed {region_data['name']}: {region_results['successful_scrapers']} successful, {region_results['failed_scrapers']} failed")
                
            except Exception as e:
                error_msg = f"Error processing region {region_data['name']}: {str(e)}"
                print(f"❌ {error_msg}")
                progress_tracker.complete_task(task_id, success=False, error_message=str(e))
                results[region_code] = {'error': str(e)}
        
        # Print overall results
        print("\n=== Overall Scraping Results ===")
        total_successful = sum(r.get('successful_scrapers', 0) for r in results.values() if isinstance(r, dict))
        total_failed = sum(r.get('failed_scrapers', 0) for r in results.values() if isinstance(r, dict))
        total_processed = sum(r.get('total_records_processed', 0) for r in results.values() if isinstance(r, dict))
        total_created = sum(r.get('total_records_created', 0) for r in results.values() if isinstance(r, dict))
        total_updated = sum(r.get('total_records_updated', 0) for r in results.values() if isinstance(r, dict))
        
        print(f"Regions processed: {len(results)}")
        print(f"Successful scrapers: {total_successful}")
        print(f"Failed scrapers: {total_failed}")
        print(f"Total records processed: {total_processed}")
        print(f"Total records created: {total_created}")
        print(f"Total records updated: {total_updated}")
        
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"scraper_results_detailed_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📄 Detailed results saved to: {results_file}")
        
        return results
        
    except Exception as e:
        print(f"❌ Scraping operation failed: {e}")
        if progress_tracker.current_task:
            progress_tracker.complete_task(progress_tracker.current_task, success=False, error_message=str(e))
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
    
    # Run scrapers with progress tracking
    run_progress_parser = subparsers.add_parser('run-progress', help='Run scrapers with progress tracking and control')
    run_progress_parser.add_argument('--type', choices=['federal', 'provincial', 'municipal'], 
                                   help='Jurisdiction type to scrape')
    run_progress_parser.add_argument('--test', action='store_true', help='Run in test mode')
    run_progress_parser.add_argument('--max-records', type=int, help='Maximum records per scraper')
    
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
    elif args.command == 'run-progress':
        jurisdiction_types = [args.type] if args.type else None
        run_scrapers_with_progress(jurisdiction_types, args.test, args.max_records)
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