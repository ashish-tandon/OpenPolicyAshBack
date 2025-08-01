"""
Open Policy Agent (OPA) Client
Provides integration with OPA policy engine for governance and validation
"""

import requests
import json
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class OPAClient:
    """
    Client for communicating with Open Policy Agent service
    Handles policy evaluation for data quality and API access control
    """
    
    def __init__(self, opa_url: str = "http://opa:8181"):
        self.opa_url = opa_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'OpenPolicy-OPA-Client/1.0'
        })
        
    def evaluate_policy(self, policy_path: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a policy with given input data
        
        Args:
            policy_path: OPA policy path (e.g., 'openpolicy/data_quality/federal_bill_valid')
            input_data: Input data for policy evaluation
            
        Returns:
            Policy evaluation result
        """
        url = f"{self.opa_url}/v1/data/{policy_path}"
        
        payload = {"input": input_data}
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("result", {})
            
        except requests.RequestException as e:
            logger.error(f"OPA policy evaluation failed for {policy_path}: {e}")
            return {"error": str(e), "policy_available": False}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from OPA: {e}")
            return {"error": "Invalid JSON response", "policy_available": False}
    
    def validate_federal_bill(self, bill_data: Dict) -> Dict:
        """
        Validate federal bill against data quality policies
        
        Args:
            bill_data: Bill data dictionary
            
        Returns:
            Validation result with score and recommendations
        """
        # Calculate age_hours for freshness check
        if bill_data.get('updated_at'):
            try:
                updated_at = datetime.fromisoformat(bill_data['updated_at'].replace('Z', '+00:00'))
                age_hours = (datetime.utcnow() - updated_at).total_seconds() / 3600
                bill_data['age_hours'] = age_hours
            except:
                bill_data['age_hours'] = 999  # Very old if can't parse
        
        # Basic validation
        is_valid = self.evaluate_policy(
            "openpolicy/data_quality/federal_bill_valid",
            {"bill": bill_data}
        )
        
        # Quality score
        quality_score = self.evaluate_policy(
            "openpolicy/data_quality/federal_bill_quality_score",
            {"bill": bill_data, "age_hours": bill_data.get('age_hours', 999)}
        )
        
        # Critical bill check
        is_critical = self.evaluate_policy(
            "openpolicy/data_quality/is_critical_bill",
            {"bill": bill_data}
        )
        
        # Government bill check
        is_government = self.evaluate_policy(
            "openpolicy/data_quality/is_government_bill",
            {"bill": bill_data}
        )
        
        return {
            "valid": bool(is_valid),
            "quality_score": quality_score if isinstance(quality_score, (int, float)) else 0,
            "is_critical": bool(is_critical),
            "is_government_bill": bool(is_government),
            "bill_id": bill_data.get('id'),
            "identifier": bill_data.get('identifier'),
            "policy_timestamp": datetime.utcnow().isoformat()
        }
    
    def check_api_access(self, user_data: Dict, request_data: Dict) -> Dict:
        """
        Check if API request should be allowed based on access policies
        
        Args:
            user_data: User authentication and role information
            request_data: Request details (endpoint, method, etc.)
            
        Returns:
            Access decision with detailed information
        """
        input_data = {
            "user": user_data,
            "endpoint": request_data.get("endpoint", ""),
            "method": request_data.get("method", "GET"),
            "requests_per_hour": request_data.get("requests_per_hour", 0),
            "export_size": request_data.get("export_size", 0),
            "country_code": request_data.get("country_code", ""),
            "api_key": user_data.get("api_key", "")
        }
        
        # Get comprehensive access decision
        access_result = self.evaluate_policy(
            "openpolicy/api_access/access_decision",
            input_data
        )
        
        # Fallback to basic checks if comprehensive policy fails
        if not access_result or access_result.get("error"):
            basic_access = self.evaluate_policy(
                "openpolicy/api_access/allow_request",
                input_data
            )
            return {
                "allowed": bool(basic_access),
                "rate_limit_status": {"allowed": bool(basic_access)},
                "audit_required": False,
                "restrictions": [],
                "fallback_mode": True
            }
        
        return access_result
    
    def validate_data_quality(self, data: Dict) -> Dict:
        """
        Comprehensive data quality validation for jurisdictions and bills
        
        Args:
            data: Dictionary containing bills, jurisdictions, and other data
            
        Returns:
            Comprehensive validation results
        """
        # Prepare data with age calculations
        processed_data = self._prepare_data_for_validation(data)
        
        # Get comprehensive validation result
        validation_result = self.evaluate_policy(
            "openpolicy/data_quality/validation_result",
            processed_data
        )
        
        # Get overall quality assessment
        overall_quality = self.evaluate_policy(
            "openpolicy/data_quality/overall_quality",
            processed_data
        )
        
        return {
            "validation_summary": validation_result,
            "overall_quality": overall_quality,
            "total_items_validated": {
                "bills": len(processed_data.get("bills", [])),
                "jurisdictions": len(processed_data.get("jurisdictions", [])),
                "data_items": len(processed_data.get("data_items", []))
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def validate_provincial_jurisdiction(self, jurisdiction_data: Dict) -> Dict:
        """
        Validate provincial jurisdiction data quality
        
        Args:
            jurisdiction_data: Provincial jurisdiction data
            
        Returns:
            Validation result with quality score
        """
        # Basic completeness check
        is_complete = self.evaluate_policy(
            "openpolicy/data_quality/provincial_data_complete",
            {"jurisdiction": jurisdiction_data}
        )
        
        # Quality score
        quality_score = self.evaluate_policy(
            "openpolicy/data_quality/provincial_data_quality_score",
            {"jurisdiction": jurisdiction_data}
        )
        
        return {
            "complete": bool(is_complete),
            "quality_score": quality_score if isinstance(quality_score, (int, float)) else 0,
            "jurisdiction_name": jurisdiction_data.get("name"),
            "province": jurisdiction_data.get("province")
        }
    
    def validate_municipal_jurisdiction(self, jurisdiction_data: Dict) -> Dict:
        """
        Validate municipal jurisdiction data quality
        
        Args:
            jurisdiction_data: Municipal jurisdiction data
            
        Returns:
            Validation result with quality score
        """
        # Basic quality check
        has_quality = self.evaluate_policy(
            "openpolicy/data_quality/municipal_data_quality",
            {"jurisdiction": jurisdiction_data}
        )
        
        # Quality score
        quality_score = self.evaluate_policy(
            "openpolicy/data_quality/municipal_data_quality_score",
            {"jurisdiction": jurisdiction_data}
        )
        
        return {
            "has_quality": bool(has_quality),
            "quality_score": quality_score if isinstance(quality_score, (int, float)) else 0,
            "jurisdiction_name": jurisdiction_data.get("name"),
            "province": jurisdiction_data.get("province"),
            "population": jurisdiction_data.get("population")
        }
    
    def bulk_validate_bills(self, bills: List[Dict]) -> Dict:
        """
        Validate multiple bills efficiently
        
        Args:
            bills: List of bill data dictionaries
            
        Returns:
            Bulk validation results with statistics
        """
        results = {
            "total_bills": len(bills),
            "federal_bills": 0,
            "valid_bills": 0,
            "critical_bills": 0,
            "government_bills": 0,
            "average_quality_score": 0,
            "bill_results": []
        }
        
        total_score = 0
        
        for bill in bills:
            validation = self.validate_federal_bill(bill)
            results["bill_results"].append(validation)
            
            if bill.get("jurisdiction_type") == "federal":
                results["federal_bills"] += 1
            
            if validation.get("valid"):
                results["valid_bills"] += 1
            
            if validation.get("is_critical"):
                results["critical_bills"] += 1
            
            if validation.get("is_government_bill"):
                results["government_bills"] += 1
            
            total_score += validation.get("quality_score", 0)
        
        if bills:
            results["average_quality_score"] = round(total_score / len(bills), 2)
        
        return results
    
    def check_federal_priority_access(self, user_data: Dict) -> bool:
        """
        Check if user has access to federal priority data
        
        Args:
            user_data: User information
            
        Returns:
            True if access is allowed
        """
        result = self.evaluate_policy(
            "openpolicy/api_access/allow_federal_priority_data",
            {"user": user_data}
        )
        return bool(result)
    
    def check_policy_validation_access(self, user_data: Dict) -> bool:
        """
        Check if user can access policy validation features
        
        Args:
            user_data: User information
            
        Returns:
            True if access is allowed
        """
        result = self.evaluate_policy(
            "openpolicy/api_access/allow_policy_validation",
            {"user": user_data}
        )
        return bool(result)
    
    def health_check(self) -> Dict:
        """
        Check if OPA service is healthy and policies are loaded
        
        Returns:
            Health status information
        """
        try:
            # Basic health check
            response = self.session.get(f"{self.opa_url}/health", timeout=5.0)
            basic_health = response.status_code == 200
            
            if not basic_health:
                return {
                    "healthy": False,
                    "opa_service": False,
                    "policies_loaded": False,
                    "error": f"OPA service returned status {response.status_code}"
                }
            
            # Check if our policies are loaded
            policies_response = self.session.get(
                f"{self.opa_url}/v1/data/openpolicy",
                timeout=5.0
            )
            policies_loaded = policies_response.status_code == 200
            
            # Test a simple policy evaluation
            test_result = self.evaluate_policy(
                "openpolicy/data_quality/valid_statuses",
                {}
            )
            policies_working = isinstance(test_result, list) and len(test_result) > 0
            
            return {
                "healthy": basic_health and policies_loaded and policies_working,
                "opa_service": basic_health,
                "policies_loaded": policies_loaded,
                "policies_working": policies_working,
                "opa_url": self.opa_url,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "opa_service": False,
                "policies_loaded": False,
                "error": str(e),
                "opa_url": self.opa_url
            }
    
    def _prepare_data_for_validation(self, data: Dict) -> Dict:
        """
        Prepare data for policy validation by adding calculated fields
        
        Args:
            data: Raw data dictionary
            
        Returns:
            Processed data with additional fields
        """
        processed_data = data.copy()
        
        # Add age calculations for bills
        if "bills" in processed_data:
            for bill in processed_data["bills"]:
                if bill.get('updated_at'):
                    try:
                        updated_at = datetime.fromisoformat(bill['updated_at'].replace('Z', '+00:00'))
                        age_hours = (datetime.utcnow() - updated_at).total_seconds() / 3600
                        bill['age_hours'] = age_hours
                    except:
                        bill['age_hours'] = 999
        
        # Add age calculations for other data items
        if "data_items" not in processed_data:
            processed_data["data_items"] = processed_data.get("bills", []) + processed_data.get("jurisdictions", [])
        
        return processed_data

# Convenience functions for easy integration
def get_opa_client() -> OPAClient:
    """Get configured OPA client instance"""
    return OPAClient()

def validate_federal_bill_simple(bill_data: Dict) -> bool:
    """Simple federal bill validation"""
    client = get_opa_client()
    result = client.validate_federal_bill(bill_data)
    return result.get("valid", False)

def check_api_access_simple(user_data: Dict, request_data: Dict) -> bool:
    """Simple API access check"""
    client = get_opa_client()
    result = client.check_api_access(user_data, request_data)
    return result.get("allowed", False)