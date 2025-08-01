"""
Scheduler Tasks

This module defines Celery tasks for automated scraping runs and data quality monitoring.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from celery import Celery
from database import (
    get_database_config, create_engine_from_config, get_session_factory,
    ScrapingRun, DataQualityIssue, Jurisdiction, JurisdictionType
)
from scrapers.manager import ScraperManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'openpolicy_scheduler',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['scheduler.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'daily-scraping-run': {
            'task': 'scheduler.tasks.run_daily_scrapers',
            'schedule': 60.0 * 60.0 * 24,  # Daily at midnight UTC
        },
        'hourly-data-quality-check': {
            'task': 'scheduler.tasks.check_data_quality',
            'schedule': 60.0 * 60.0,  # Every hour
        },
    },
)

@celery_app.task(bind=True)
def run_scrapers_task(self, jurisdiction_types: Optional[List[str]] = None, 
                     max_records_per_scraper: Optional[int] = None,
                     test_mode: bool = False):
    """
    Celery task to run scrapers for specified jurisdiction types
    """
    task_id = self.request.id
    logger.info(f"Starting scraper task {task_id}")
    
    try:
        # Initialize scraper manager
        manager = ScraperManager()
        
        # Run scrapers
        results = manager.run_all_scrapers(
            max_records_per_scraper=max_records_per_scraper,
            test_mode=test_mode,
            jurisdiction_types=jurisdiction_types
        )
        
        # Log results to database
        if not test_mode:
            log_scraping_run(results, task_id)
        
        logger.info(f"Scraper task {task_id} completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Scraper task {task_id} failed: {e}")
        raise

@celery_app.task
def run_daily_scrapers():
    """
    Daily automated scraper run for all jurisdictions
    """
    logger.info("Starting daily scraper run")
    
    return run_scrapers_task.delay(
        jurisdiction_types=None,  # All types
        max_records_per_scraper=None,  # No limit
        test_mode=False
    )

@celery_app.task
def run_federal_scrapers():
    """
    Run scrapers for federal jurisdictions only
    """
    logger.info("Starting federal scraper run")
    
    return run_scrapers_task.delay(
        jurisdiction_types=['federal'],
        max_records_per_scraper=None,
        test_mode=False
    )

@celery_app.task
def run_provincial_scrapers():
    """
    Run scrapers for provincial jurisdictions only
    """
    logger.info("Starting provincial scraper run")
    
    return run_scrapers_task.delay(
        jurisdiction_types=['provincial'],
        max_records_per_scraper=None,
        test_mode=False
    )

@celery_app.task
def run_municipal_scrapers():
    """
    Run scrapers for municipal jurisdictions only
    """
    logger.info("Starting municipal scraper run")
    
    return run_scrapers_task.delay(
        jurisdiction_types=['municipal'],
        max_records_per_scraper=None,
        test_mode=False
    )

@celery_app.task
def run_test_scrapers(max_records: int = 5):
    """
    Run scrapers in test mode with limited records
    """
    logger.info("Starting test scraper run")
    
    return run_scrapers_task.delay(
        jurisdiction_types=None,
        max_records_per_scraper=max_records,
        test_mode=True
    )

@celery_app.task
def check_data_quality():
    """
    Check data quality and identify issues
    """
    logger.info("Starting data quality check")
    
    try:
        config = get_database_config()
        engine = create_engine_from_config(config.get_url())
        Session = get_session_factory(engine)
        session = Session()
        
        issues_found = []
        
        try:
            # Check for representatives without contact information
            reps_without_contact = session.execute("""
                SELECT j.name as jurisdiction_name, r.name as rep_name, r.id
                FROM representatives r
                JOIN jurisdictions j ON r.jurisdiction_id = j.id
                WHERE r.email IS NULL AND r.phone IS NULL
            """).fetchall()
            
            for rep in reps_without_contact:
                issue = DataQualityIssue(
                    jurisdiction_id=session.query(Jurisdiction).filter(
                        Jurisdiction.name == rep.jurisdiction_name
                    ).first().id,
                    issue_type='missing_contact',
                    severity='medium',
                    description=f"Representative {rep.rep_name} has no contact information",
                    affected_table='representatives',
                    affected_record_id=str(rep.id)
                )
                session.add(issue)
                issues_found.append(issue.description)
            
            # Check for representatives without party affiliation
            reps_without_party = session.execute("""
                SELECT j.name as jurisdiction_name, r.name as rep_name, r.id
                FROM representatives r
                JOIN jurisdictions j ON r.jurisdiction_id = j.id
                WHERE r.party IS NULL AND j.jurisdiction_type != 'municipal'
            """).fetchall()
            
            for rep in reps_without_party:
                issue = DataQualityIssue(
                    jurisdiction_id=session.query(Jurisdiction).filter(
                        Jurisdiction.name == rep.jurisdiction_name
                    ).first().id,
                    issue_type='missing_party',
                    severity='low',
                    description=f"Representative {rep.rep_name} has no party affiliation",
                    affected_table='representatives',
                    affected_record_id=str(rep.id)
                )
                session.add(issue)
                issues_found.append(issue.description)
            
            # Check for duplicate representatives
            duplicates = session.execute("""
                SELECT jurisdiction_id, name, COUNT(*) as count
                FROM representatives
                GROUP BY jurisdiction_id, name
                HAVING COUNT(*) > 1
            """).fetchall()
            
            for dup in duplicates:
                jurisdiction = session.query(Jurisdiction).filter(
                    Jurisdiction.id == dup.jurisdiction_id
                ).first()
                
                issue = DataQualityIssue(
                    jurisdiction_id=dup.jurisdiction_id,
                    issue_type='duplicate_representative',
                    severity='high',
                    description=f"Duplicate representative {dup.name} in {jurisdiction.name} ({dup.count} records)",
                    affected_table='representatives'
                )
                session.add(issue)
                issues_found.append(issue.description)
            
            session.commit()
            
            logger.info(f"Data quality check completed. Found {len(issues_found)} issues.")
            return {
                'issues_found': len(issues_found),
                'issues': issues_found
            }
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"Data quality check failed: {e}")
        raise

@celery_app.task
def cleanup_old_logs(days_to_keep: int = 30):
    """
    Clean up old scraping run logs and resolved data quality issues
    """
    logger.info(f"Cleaning up logs older than {days_to_keep} days")
    
    try:
        config = get_database_config()
        engine = create_engine_from_config(config.get_url())
        Session = get_session_factory(engine)
        session = Session()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        try:
            # Clean up old scraping runs
            old_runs = session.query(ScrapingRun).filter(
                ScrapingRun.start_time < cutoff_date
            ).count()
            
            session.query(ScrapingRun).filter(
                ScrapingRun.start_time < cutoff_date
            ).delete()
            
            # Clean up resolved data quality issues
            resolved_issues = session.query(DataQualityIssue).filter(
                DataQualityIssue.resolved_at < cutoff_date,
                DataQualityIssue.resolved_at.isnot(None)
            ).count()
            
            session.query(DataQualityIssue).filter(
                DataQualityIssue.resolved_at < cutoff_date,
                DataQualityIssue.resolved_at.isnot(None)
            ).delete()
            
            session.commit()
            
            logger.info(f"Cleaned up {old_runs} old scraping runs and {resolved_issues} resolved issues")
            
            return {
                'scraping_runs_deleted': old_runs,
                'issues_deleted': resolved_issues
            }
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise

def log_scraping_run(results: Dict[str, Any], task_id: str):
    """
    Log scraping run results to the database
    """
    try:
        config = get_database_config()
        engine = create_engine_from_config(config.get_url())
        Session = get_session_factory(engine)
        session = Session()
        
        try:
            # Create scraping run records for each jurisdiction
            for jurisdiction_result in results.get('jurisdiction_results', []):
                jurisdiction_id = jurisdiction_result.get('jurisdiction_id')
                
                if jurisdiction_id:
                    scraping_run = ScrapingRun(
                        jurisdiction_id=jurisdiction_id,
                        run_type='scheduled',
                        status='completed' if jurisdiction_result.get('status') == 'completed' else 'failed',
                        start_time=datetime.fromisoformat(results.get('start_time', '')),
                        end_time=datetime.fromisoformat(results.get('end_time', '')),
                        records_processed=jurisdiction_result.get('records_processed', 0),
                        records_created=jurisdiction_result.get('records_created', 0),
                        records_updated=jurisdiction_result.get('records_updated', 0),
                        errors_count=1 if jurisdiction_result.get('error') else 0,
                        error_log={'error': jurisdiction_result.get('error')} if jurisdiction_result.get('error') else None,
                        summary={
                            'task_id': task_id,
                            'scraper_directory': jurisdiction_result.get('scraper_directory'),
                            'data_sample': jurisdiction_result.get('data_sample', [])
                        }
                    )
                    session.add(scraping_run)
            
            session.commit()
            logger.info("Scraping run logged to database")
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"Failed to log scraping run: {e}")

# Task monitoring and management functions
def get_task_status(task_id: str):
    """Get the status of a specific task"""
    result = celery_app.AsyncResult(task_id)
    return {
        'task_id': task_id,
        'status': result.status,
        'result': result.result if result.ready() else None,
        'traceback': result.traceback if result.failed() else None
    }

def cancel_task(task_id: str):
    """Cancel a running task"""
    celery_app.control.revoke(task_id, terminate=True)
    return {'task_id': task_id, 'status': 'cancelled'}

def get_active_tasks():
    """Get list of currently active tasks"""
    inspect = celery_app.control.inspect()
    active_tasks = inspect.active()
    return active_tasks

def get_scheduled_tasks():
    """Get list of scheduled tasks"""
    inspect = celery_app.control.inspect()
    scheduled_tasks = inspect.scheduled()
    return scheduled_tasks