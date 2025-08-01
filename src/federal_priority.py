"""
Federal Bills Priority Monitoring System

This module provides enhanced monitoring and validation specifically for Federal Canadian bills,
implementing pre-built spot checks and quality assurance measures.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from dataclasses import dataclass
import re

from database import Bill, Jurisdiction, JurisdictionType, BillStatus
from database import get_session_factory, get_database_config, create_engine_from_config

logger = logging.getLogger(__name__)

@dataclass
class FederalBillCheck:
    """Represents a spot check result for a federal bill"""
    bill_id: str
    bill_identifier: str
    check_type: str
    status: str  # 'pass', 'warning', 'fail'
    message: str
    checked_at: datetime
    details: Dict[str, Any] = None

@dataclass
class FederalMonitoringReport:
    """Federal bills monitoring report"""
    checked_at: datetime
    total_bills: int
    checks_performed: int
    passed_checks: int
    warnings: int
    failures: int
    checks: List[FederalBillCheck]
    recommendations: List[str]

class FederalBillsMonitor:
    """Enhanced monitoring for Federal Canadian bills"""
    
    def __init__(self):
        config = get_database_config()
        engine = create_engine_from_config(config.get_url())
        self.SessionLocal = get_session_factory(engine)
    
    def get_federal_bills(self, db: Session, days_back: int = 30) -> List[Bill]:
        """Get federal bills from the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        federal_jurisdiction = db.query(Jurisdiction).filter(
            Jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL
        ).first()
        
        if not federal_jurisdiction:
            logger.warning("No federal jurisdiction found")
            return []
        
        bills = db.query(Bill).filter(
            Bill.jurisdiction_id == federal_jurisdiction.id,
            Bill.updated_at >= cutoff_date
        ).all()
        
        return bills
    
    def check_bill_identifier_format(self, bill: Bill) -> FederalBillCheck:
        """Validate federal bill identifier format (e.g., C-1, S-1)"""
        federal_pattern = r'^[CS]-\d+$'
        
        if re.match(federal_pattern, bill.identifier):
            return FederalBillCheck(
                bill_id=bill.id,
                bill_identifier=bill.identifier,
                check_type="identifier_format",
                status="pass",
                message="Bill identifier follows correct federal format",
                checked_at=datetime.now()
            )
        else:
            return FederalBillCheck(
                bill_id=bill.id,
                bill_identifier=bill.identifier,
                check_type="identifier_format",
                status="fail",
                message=f"Bill identifier '{bill.identifier}' does not match federal format (C-# or S-#)",
                checked_at=datetime.now(),
                details={"expected_pattern": "C-# or S-# (e.g., C-1, S-15)"}
            )
    
    def check_bill_title_quality(self, bill: Bill) -> FederalBillCheck:
        """Check if bill title meets quality standards"""
        if not bill.title:
            return FederalBillCheck(
                bill_id=bill.id,
                bill_identifier=bill.identifier,
                check_type="title_quality",
                status="fail",
                message="Bill title is missing",
                checked_at=datetime.now()
            )
        
        title_length = len(bill.title)
        
        if title_length < 10:
            return FederalBillCheck(
                bill_id=bill.id,
                bill_identifier=bill.identifier,
                check_type="title_quality",
                status="warning",
                message=f"Bill title is very short ({title_length} characters)",
                checked_at=datetime.now(),
                details={"title_length": title_length}
            )
        elif title_length > 200:
            return FederalBillCheck(
                bill_id=bill.id,
                bill_identifier=bill.identifier,
                check_type="title_quality",
                status="warning",
                message=f"Bill title is very long ({title_length} characters)",
                checked_at=datetime.now(),
                details={"title_length": title_length}
            )
        else:
            return FederalBillCheck(
                bill_id=bill.id,
                bill_identifier=bill.identifier,
                check_type="title_quality",
                status="pass",
                message="Bill title length is appropriate",
                checked_at=datetime.now(),
                details={"title_length": title_length}
            )
    
    def check_bill_status_progression(self, bill: Bill) -> FederalBillCheck:
        """Validate bill status follows logical progression"""
        valid_statuses = ['introduced', 'first_reading', 'second_reading', 
                         'committee', 'third_reading', 'senate', 'royal_assent', 
                         'passed', 'failed', 'withdrawn']
        
        if bill.status not in valid_statuses:
            return FederalBillCheck(
                bill_id=bill.id,
                bill_identifier=bill.identifier,
                check_type="status_progression",
                status="warning",
                message=f"Unusual bill status: '{bill.status}'",
                checked_at=datetime.now(),
                details={"current_status": bill.status, "valid_statuses": valid_statuses}
            )
        
        return FederalBillCheck(
            bill_id=bill.id,
            bill_identifier=bill.identifier,
            check_type="status_progression",
            status="pass",
            message="Bill status is valid",
            checked_at=datetime.now(),
            details={"current_status": bill.status}
        )
    
    def check_data_freshness(self, bill: Bill) -> FederalBillCheck:
        """Check if bill data is recent enough"""
        days_since_update = (datetime.now() - bill.updated_at).days
        
        if days_since_update > 7:
            return FederalBillCheck(
                bill_id=bill.id,
                bill_identifier=bill.identifier,
                check_type="data_freshness",
                status="warning",
                message=f"Bill data is {days_since_update} days old",
                checked_at=datetime.now(),
                details={"days_since_update": days_since_update}
            )
        
        return FederalBillCheck(
            bill_id=bill.id,
            bill_identifier=bill.identifier,
            check_type="data_freshness",
            status="pass",
            message="Bill data is recent",
            checked_at=datetime.now(),
            details={"days_since_update": days_since_update}
        )
    
    def check_critical_federal_bills(self, bill: Bill) -> FederalBillCheck:
        """Identify potentially critical federal bills requiring special attention"""
        critical_keywords = [
            'budget', 'tax', 'healthcare', 'climate', 'environment',
            'immigration', 'defence', 'security', 'election', 'charter'
        ]
        
        title_lower = bill.title.lower() if bill.title else ""
        summary_lower = bill.summary.lower() if bill.summary else ""
        
        found_keywords = [kw for kw in critical_keywords 
                         if kw in title_lower or kw in summary_lower]
        
        if found_keywords:
            return FederalBillCheck(
                bill_id=bill.id,
                bill_identifier=bill.identifier,
                check_type="critical_bill_detection",
                status="pass",
                message=f"Critical federal bill detected (keywords: {', '.join(found_keywords)})",
                checked_at=datetime.now(),
                details={"critical_keywords": found_keywords, "priority": "high"}
            )
        
        return FederalBillCheck(
            bill_id=bill.id,
            bill_identifier=bill.identifier,
            check_type="critical_bill_detection",
            status="pass",
            message="Standard federal bill",
            checked_at=datetime.now(),
            details={"priority": "normal"}
        )
    
    def run_comprehensive_check(self, days_back: int = 30) -> FederalMonitoringReport:
        """Run comprehensive spot checks on federal bills"""
        logger.info(f"Starting federal bills monitoring (last {days_back} days)")
        
        with self.SessionLocal() as db:
            bills = self.get_federal_bills(db, days_back)
            
            all_checks = []
            
            for bill in bills:
                # Run all checks on each bill
                checks = [
                    self.check_bill_identifier_format(bill),
                    self.check_bill_title_quality(bill),
                    self.check_bill_status_progression(bill),
                    self.check_data_freshness(bill),
                    self.check_critical_federal_bills(bill)
                ]
                all_checks.extend(checks)
            
            # Generate statistics
            total_checks = len(all_checks)
            passed = len([c for c in all_checks if c.status == 'pass'])
            warnings = len([c for c in all_checks if c.status == 'warning'])
            failures = len([c for c in all_checks if c.status == 'fail'])
            
            # Generate recommendations
            recommendations = self._generate_recommendations(all_checks)
            
            report = FederalMonitoringReport(
                checked_at=datetime.now(),
                total_bills=len(bills),
                checks_performed=total_checks,
                passed_checks=passed,
                warnings=warnings,
                failures=failures,
                checks=all_checks,
                recommendations=recommendations
            )
            
            logger.info(f"Federal monitoring complete: {len(bills)} bills, "
                       f"{total_checks} checks, {failures} failures, {warnings} warnings")
            
            return report
    
    def _generate_recommendations(self, checks: List[FederalBillCheck]) -> List[str]:
        """Generate actionable recommendations based on check results"""
        recommendations = []
        
        failures = [c for c in checks if c.status == 'fail']
        warnings = [c for c in checks if c.status == 'warning']
        
        if failures:
            recommendations.append(f"Address {len(failures)} critical issues immediately")
        
        if warnings:
            recommendations.append(f"Review {len(warnings)} warnings for potential improvements")
        
        # Specific recommendations based on check types
        identifier_failures = [c for c in failures if c.check_type == 'identifier_format']
        if identifier_failures:
            recommendations.append("Fix bill identifier formats to match federal standards (C-# or S-#)")
        
        missing_titles = [c for c in failures if c.check_type == 'title_quality' and 'missing' in c.message]
        if missing_titles:
            recommendations.append("Update bills with missing titles")
        
        stale_data = [c for c in warnings if c.check_type == 'data_freshness']
        if stale_data:
            recommendations.append("Schedule more frequent updates for federal bills with stale data")
        
        critical_bills = [c for c in checks if c.check_type == 'critical_bill_detection' 
                         and c.details and c.details.get('priority') == 'high']
        if critical_bills:
            recommendations.append(f"Monitor {len(critical_bills)} critical federal bills for priority updates")
        
        if not recommendations:
            recommendations.append("All federal bills pass quality checks - maintain current monitoring standards")
        
        return recommendations
    
    def get_federal_priority_metrics(self) -> Dict[str, Any]:
        """Get key metrics for federal bills priority monitoring"""
        with self.SessionLocal() as db:
            federal_jurisdiction = db.query(Jurisdiction).filter(
                Jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL
            ).first()
            
            if not federal_jurisdiction:
                return {"error": "No federal jurisdiction found"}
            
            total_bills = db.query(Bill).filter(
                Bill.jurisdiction_id == federal_jurisdiction.id
            ).count()
            
            recent_bills = db.query(Bill).filter(
                Bill.jurisdiction_id == federal_jurisdiction.id,
                Bill.updated_at >= datetime.now() - timedelta(days=7)
            ).count()
            
            active_bills = db.query(Bill).filter(
                Bill.jurisdiction_id == federal_jurisdiction.id,
                Bill.status.in_(['introduced', 'committee', 'first_reading', 'second_reading', 'third_reading'])
            ).count()
            
            return {
                "total_federal_bills": total_bills,
                "recent_updates_7d": recent_bills,
                "active_bills": active_bills,
                "monitoring_enabled": True,
                "last_check": datetime.now().isoformat(),
                "priority_status": "enhanced_monitoring_active"
            }

# Global instance for easy access
federal_monitor = FederalBillsMonitor()