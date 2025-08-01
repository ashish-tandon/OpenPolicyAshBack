"""
Parliamentary Data Validator - Enhanced Federal Bill Validation
Comprehensive validation system for Canadian federal bills and parliamentary data
Based on patterns from OpenParliament and Canadian parliamentary standards
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

from src.database.models import Bill, Representative, Jurisdiction

logger = logging.getLogger(__name__)

class ParliamentaryValidator:
    """
    Comprehensive validation system for Canadian parliamentary data
    Focus on federal bills with enhanced quality checks
    """
    
    BILL_IDENTIFIER_PATTERNS = {
        'commons': r'^C-\d+$',  # House of Commons bills (e.g., C-4, C-12)
        'senate': r'^S-\d+$',   # Senate bills (e.g., S-2, S-15)
        'private_member_commons': r'^C-\d+$',  # Private member bills from Commons
        'private_member_senate': r'^S-\d+$'    # Private member bills from Senate
    }
    
    VALID_BILL_STATUSES = [
        'First Reading',
        'Second Reading', 
        'Committee Stage',
        'Report Stage',
        'Third Reading',
        'Consideration by Senate',
        'Consideration by House of Commons',
        'Royal Assent',
        'Withdrawn',
        'Defeated',
        'Prorogued',
        'Died on Order Paper'
    ]
    
    CRITICAL_BILL_KEYWORDS = [
        'budget', 'tax', 'taxation', 'fiscal', 'revenue',
        'healthcare', 'health care', 'medicare',
        'education', 'student', 'university', 'college',
        'defence', 'defense', 'military', 'armed forces',
        'immigration', 'refugee', 'citizenship',
        'employment', 'labour', 'labor', 'worker',
        'economy', 'economic', 'trade', 'commerce',
        'environment', 'climate', 'carbon', 'emissions',
        'justice', 'criminal', 'court', 'legal',
        'privacy', 'data protection', 'surveillance',
        'infrastructure', 'transportation', 'transit'
    ]
    
    # Status progression rules (simplified - could be more complex)
    STATUS_PROGRESSION = {
        'First Reading': ['Second Reading', 'Withdrawn'],
        'Second Reading': ['Committee Stage', 'Third Reading', 'Defeated', 'Withdrawn'],
        'Committee Stage': ['Report Stage', 'Third Reading', 'Defeated'],
        'Report Stage': ['Third Reading', 'Defeated'],
        'Third Reading': ['Consideration by Senate', 'Royal Assent', 'Defeated'],
        'Consideration by Senate': ['Royal Assent', 'Defeated'],
        'Consideration by House of Commons': ['Royal Assent', 'Defeated']
    }
    
    def validate_federal_bill(self, bill: Bill) -> Dict:
        """
        Comprehensive validation of federal bill data
        Returns detailed validation results with scores and recommendations
        """
        validation_result = {
            'bill_id': bill.id,
            'identifier': bill.identifier,
            'title': bill.title,
            'passes': True,
            'warnings': [],
            'errors': [],
            'quality_score': 100,
            'is_critical': False,
            'is_government_bill': False,
            'recommendations': [],
            'detailed_checks': {}
        }
        
        try:
            # 1. Validate identifier format
            identifier_check = self._validate_bill_identifier(bill.identifier)
            validation_result['detailed_checks']['identifier'] = identifier_check
            
            if not identifier_check['valid']:
                validation_result['errors'].append(identifier_check['message'])
                validation_result['quality_score'] -= 20
                validation_result['passes'] = False
            else:
                validation_result['is_government_bill'] = identifier_check['is_government_bill']
            
            # 2. Validate title quality
            title_check = self._validate_title_quality(bill.title)
            validation_result['detailed_checks']['title'] = title_check
            validation_result['quality_score'] += title_check['score'] - 100  # Adjust score
            
            if title_check['score'] < 60:
                validation_result['warnings'].append(title_check['message'])
            
            # 3. Validate status progression
            status_check = self._validate_status_progression(bill)
            validation_result['detailed_checks']['status'] = status_check
            
            if not status_check['valid']:
                validation_result['warnings'].append(status_check['message'])
                validation_result['quality_score'] -= 10
            
            # 4. Check if bill is critical
            critical_check = self._is_critical_bill(bill)
            validation_result['detailed_checks']['critical'] = critical_check
            validation_result['is_critical'] = critical_check['is_critical']
            
            # 5. Data freshness check
            freshness_check = self._check_data_freshness(bill)
            validation_result['detailed_checks']['freshness'] = freshness_check
            validation_result['quality_score'] += freshness_check['score'] - 100
            
            if freshness_check['score'] < 80:
                validation_result['warnings'].append(freshness_check['message'])
            
            # 6. Content completeness check
            completeness_check = self._check_content_completeness(bill)
            validation_result['detailed_checks']['completeness'] = completeness_check
            validation_result['quality_score'] += completeness_check['score'] - 100
            
            if completeness_check['score'] < 70:
                validation_result['warnings'].append(completeness_check['message'])
            
            # 7. Generate recommendations
            validation_result['recommendations'] = self._generate_recommendations(validation_result)
            
            # Final quality score bounds
            validation_result['quality_score'] = max(0, min(100, validation_result['quality_score']))
            
            logger.info(f"Validated bill {bill.identifier}: score {validation_result['quality_score']}")
            
        except Exception as e:
            logger.error(f"Error validating bill {bill.id}: {e}")
            validation_result['errors'].append(f"Validation error: {str(e)}")
            validation_result['passes'] = False
            validation_result['quality_score'] = 0
        
        return validation_result
    
    def _validate_bill_identifier(self, identifier: str) -> Dict:
        """Validate Canadian federal bill identifier format"""
        result = {
            'valid': False,
            'message': '',
            'bill_type': None,
            'is_government_bill': False,
            'bill_number': None
        }
        
        if not identifier:
            result['message'] = "Bill identifier is missing"
            return result
        
        identifier = identifier.strip().upper()
        
        # Check Commons bills (C-#)
        commons_match = re.match(r'^C-(\d+)$', identifier)
        if commons_match:
            bill_number = int(commons_match.group(1))
            result['valid'] = True
            result['bill_type'] = 'commons'
            result['bill_number'] = bill_number
            result['is_government_bill'] = bill_number <= 200  # Government bills typically C-1 to C-200
            result['message'] = f"Valid House of Commons bill: {identifier}"
            return result
        
        # Check Senate bills (S-#)
        senate_match = re.match(r'^S-(\d+)$', identifier)
        if senate_match:
            bill_number = int(senate_match.group(1))
            result['valid'] = True
            result['bill_type'] = 'senate'
            result['bill_number'] = bill_number
            result['is_government_bill'] = bill_number <= 200  # Government bills typically S-1 to S-200
            result['message'] = f"Valid Senate bill: {identifier}"
            return result
        
        # If we get here, format is invalid
        result['message'] = f"Invalid bill identifier format: {identifier}. Expected C-# or S-# format."
        return result
    
    def _validate_title_quality(self, title: str) -> Dict:
        """Score title quality (0-100) with detailed feedback"""
        result = {
            'score': 0,
            'message': '',
            'issues': []
        }
        
        if not title:
            result['message'] = "Bill title is missing"
            return result
        
        title = title.strip()
        score = 50  # Base score
        issues = []
        
        # Length check
        if 10 <= len(title) <= 300:
            score += 20
        elif len(title) < 10:
            score -= 30
            issues.append("Title too short (less than 10 characters)")
        elif len(title) > 300:
            score -= 10
            issues.append("Title very long (over 300 characters)")
        
        # Proper formatting check
        if title.endswith(' Act') or title.endswith(' Act.'):
            score += 15
        elif not title.endswith('.'):
            issues.append("Title should end with 'Act' or proper punctuation")
        
        # Avoid too generic titles
        generic_patterns = [
            r'^Bill\s+C-\d+$',
            r'^Bill\s+S-\d+$',
            r'^An Act$',
            r'^A Bill$'
        ]
        
        for pattern in generic_patterns:
            if re.match(pattern, title, re.IGNORECASE):
                score -= 40
                issues.append("Title is too generic")
                break
        
        # Check for meaningful content
        if len(title.split()) >= 3:
            score += 15
        else:
            issues.append("Title lacks sufficient detail")
        
        # Check for common bill title patterns
        if re.search(r'An Act (to|respecting|concerning)', title, re.IGNORECASE):
            score += 10  # Proper parliamentary language
        
        # Penalize ALL CAPS titles
        if title.isupper() and len(title) > 20:
            score -= 15
            issues.append("Title should not be in all capitals")
        
        result['score'] = max(0, min(100, score))
        result['issues'] = issues
        
        if result['score'] >= 80:
            result['message'] = "Excellent title quality"
        elif result['score'] >= 60:
            result['message'] = "Good title quality"
        elif result['score'] >= 40:
            result['message'] = "Fair title quality - could be improved"
        else:
            result['message'] = "Poor title quality - needs improvement"
        
        return result
    
    def _validate_status_progression(self, bill: Bill) -> Dict:
        """Validate logical bill status progression"""
        result = {
            'valid': True,
            'message': '',
            'current_status': bill.status,
            'valid_next_statuses': []
        }
        
        if not bill.status:
            result['valid'] = False
            result['message'] = "Bill status is missing"
            return result
        
        if bill.status not in self.VALID_BILL_STATUSES:
            result['valid'] = False
            result['message'] = f"Invalid bill status: {bill.status}"
            return result
        
        # Get valid next statuses
        result['valid_next_statuses'] = self.STATUS_PROGRESSION.get(bill.status, [])
        
        # For now, we'll just validate that the status is in our known list
        # More sophisticated validation would check the progression history
        result['message'] = f"Valid status: {bill.status}"
        
        return result
    
    def _is_critical_bill(self, bill: Bill) -> Dict:
        """Determine if bill deals with critical national issues"""
        result = {
            'is_critical': False,
            'matching_keywords': [],
            'confidence': 0
        }
        
        if not bill.title and not bill.summary:
            return result
        
        # Combine title and summary for analysis
        text_to_check = f"{bill.title or ''} {bill.summary or ''}".lower()
        
        matching_keywords = []
        for keyword in self.CRITICAL_BILL_KEYWORDS:
            if keyword in text_to_check:
                matching_keywords.append(keyword)
        
        result['matching_keywords'] = matching_keywords
        
        if matching_keywords:
            result['is_critical'] = True
            result['confidence'] = min(100, len(matching_keywords) * 20)  # Max 100%
        
        return result
    
    def _check_data_freshness(self, bill: Bill) -> Dict:
        """Check how fresh the bill data is (0-100 score)"""
        result = {
            'score': 50,  # Neutral score if no update time
            'message': '',
            'age_hours': None,
            'last_updated': None
        }
        
        if not bill.updated_at:
            result['message'] = "No update timestamp available"
            return result
        
        now = datetime.utcnow()
        age = now - bill.updated_at
        age_hours = age.total_seconds() / 3600
        
        result['age_hours'] = round(age_hours, 2)
        result['last_updated'] = bill.updated_at.isoformat()
        
        if age <= timedelta(hours=4):
            result['score'] = 100
            result['message'] = "Excellent - data very fresh (under 4 hours)"
        elif age <= timedelta(hours=24):
            result['score'] = 90
            result['message'] = "Good - data fresh (under 24 hours)"
        elif age <= timedelta(days=3):
            result['score'] = 70
            result['message'] = "Fair - data somewhat fresh (under 3 days)"
        elif age <= timedelta(weeks=1):
            result['score'] = 50
            result['message'] = "Getting stale - data over 3 days old"
        elif age <= timedelta(weeks=4):
            result['score'] = 30
            result['message'] = "Stale - data over 1 week old"
        else:
            result['score'] = 10
            result['message'] = "Very stale - data over 1 month old"
        
        return result
    
    def _check_content_completeness(self, bill: Bill) -> Dict:
        """Check completeness of bill content"""
        result = {
            'score': 0,
            'message': '',
            'missing_fields': [],
            'present_fields': []
        }
        
        # Define expected fields and their importance weights
        field_weights = {
            'identifier': 30,    # Critical
            'title': 25,         # Critical
            'status': 20,        # Very important
            'summary': 15,       # Important
            'url': 10            # Nice to have
        }
        
        total_possible = sum(field_weights.values())
        score = 0
        
        for field, weight in field_weights.items():
            value = getattr(bill, field, None)
            if value and str(value).strip():
                score += weight
                result['present_fields'].append(field)
            else:
                result['missing_fields'].append(field)
        
        result['score'] = int((score / total_possible) * 100)
        
        if result['score'] >= 90:
            result['message'] = "Excellent completeness"
        elif result['score'] >= 70:
            result['message'] = "Good completeness"
        elif result['score'] >= 50:
            result['message'] = "Fair completeness - some fields missing"
        else:
            result['message'] = "Poor completeness - many fields missing"
        
        return result
    
    def _generate_recommendations(self, validation_result: Dict) -> List[str]:
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        
        # Quality score based recommendations
        if validation_result['quality_score'] < 70:
            recommendations.append("Consider re-scraping this bill for updated information")
        
        # Critical bill recommendations
        if validation_result['is_critical']:
            recommendations.append("Critical bill detected - prioritize for frequent updates and monitoring")
        
        # Error handling recommendations
        if validation_result['errors']:
            recommendations.append("Fix data quality errors before publishing or using in analysis")
        
        # Warning handling recommendations
        if len(validation_result['warnings']) > 2:
            recommendations.append("Multiple warnings detected - review data source and collection process")
        
        # Specific detailed check recommendations
        checks = validation_result.get('detailed_checks', {})
        
        # Freshness recommendations
        freshness = checks.get('freshness', {})
        if freshness.get('score', 100) < 60:
            recommendations.append("Data is stale - schedule immediate re-scraping")
        
        # Completeness recommendations
        completeness = checks.get('completeness', {})
        if completeness.get('missing_fields'):
            missing = ', '.join(completeness['missing_fields'])
            recommendations.append(f"Incomplete data - missing fields: {missing}")
        
        # Title quality recommendations
        title = checks.get('title', {})
        if title.get('score', 100) < 50:
            recommendations.append("Improve title data quality - may need manual review")
        
        # Government bill recommendations
        if validation_result.get('is_government_bill'):
            recommendations.append("Government bill - ensure extra monitoring and validation")
        
        return recommendations[:5]  # Limit to top 5 recommendations

    def validate_bulk_bills(self, bills: List[Bill]) -> Dict:
        """Validate multiple bills and return aggregate statistics"""
        results = {
            'total_bills': len(bills),
            'validation_results': [],
            'summary': {
                'passed': 0,
                'warnings': 0,
                'errors': 0,
                'critical_bills': 0,
                'government_bills': 0,
                'average_quality_score': 0
            },
            'recommendations': []
        }
        
        total_score = 0
        
        for bill in bills:
            validation = self.validate_federal_bill(bill)
            results['validation_results'].append(validation)
            
            # Update summary statistics
            if validation['passes']:
                results['summary']['passed'] += 1
            if validation['warnings']:
                results['summary']['warnings'] += 1
            if validation['errors']:
                results['summary']['errors'] += 1
            if validation['is_critical']:
                results['summary']['critical_bills'] += 1
            if validation.get('is_government_bill'):
                results['summary']['government_bills'] += 1
            
            total_score += validation['quality_score']
        
        # Calculate average quality score
        if bills:
            results['summary']['average_quality_score'] = round(total_score / len(bills), 2)
        
        # Generate bulk recommendations
        if results['summary']['average_quality_score'] < 70:
            results['recommendations'].append("Overall data quality below acceptable threshold")
        
        if results['summary']['errors'] > len(bills) * 0.1:  # More than 10% errors
            results['recommendations'].append("High error rate detected - review data collection process")
        
        if results['summary']['critical_bills'] > 0:
            results['recommendations'].append(f"Monitor {results['summary']['critical_bills']} critical bills closely")
        
        return results

# Utility functions for easy integration
def validate_federal_bill(bill: Bill) -> Dict:
    """Convenience function to validate a single federal bill"""
    validator = ParliamentaryValidator()
    return validator.validate_federal_bill(bill)

def validate_bills_batch(bills: List[Bill]) -> Dict:
    """Convenience function to validate multiple bills"""
    validator = ParliamentaryValidator()
    return validator.validate_bulk_bills(bills)