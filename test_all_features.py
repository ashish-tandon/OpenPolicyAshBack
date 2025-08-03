#!/usr/bin/env python3
"""
Comprehensive Feature Test Script for OpenPolicy Backend
Tests all major features and integrations
"""

import requests
import psycopg2
import json
import sys
from datetime import datetime
from termcolor import colored

BASE_URL = "http://localhost:8000"
OPA_URL = "http://localhost:8181"
FLOWER_URL = "http://localhost:5555"

def print_test(test_name, passed, message=""):
    """Print test result with color"""
    if passed:
        print(colored(f"✓ {test_name}", "green"))
    else:
        print(colored(f"✗ {test_name}", "red"))
        if message:
            print(colored(f"  Error: {message}", "yellow"))

def test_api_health():
    """Test if the main API is healthy"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        passed = response.status_code == 200 and response.json()["status"] == "healthy"
        print_test("API Health Check", passed)
        return passed
    except Exception as e:
        print_test("API Health Check", False, str(e))
        return False

def test_database_connection():
    """Test database connectivity and tables"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="opencivicdata",
            user="openpolicy",
            password="openpolicy123"
        )
        cur = conn.cursor()
        
        # Check core tables
        tables_to_check = [
            'jurisdiction', 'representative', 'bill', 'committee', 
            'event', 'vote', 'parliamentary_session', 'hansard_record',
            'speech', 'committee_meeting'
        ]
        
        all_tables_exist = True
        for table in tables_to_check:
            cur.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
            exists = cur.fetchone()[0]
            if not exists:
                print_test(f"  Table {table}", False, "Table does not exist")
                all_tables_exist = False
        
        conn.close()
        print_test("Database Connection & Tables", all_tables_exist)
        return all_tables_exist
    except Exception as e:
        print_test("Database Connection", False, str(e))
        return False

def test_opa_service():
    """Test Open Policy Agent service"""
    try:
        response = requests.get(f"{OPA_URL}/health")
        passed = response.status_code == 200
        print_test("OPA Service Health", passed)
        
        # Test if policies are loaded
        response = requests.get(f"{OPA_URL}/v1/policies")
        policies = response.json().get("result", [])
        policies_loaded = len(policies) > 0
        print_test("  OPA Policies Loaded", policies_loaded, 
                  f"Found {len(policies)} policies" if policies_loaded else "No policies found")
        
        return passed and policies_loaded
    except Exception as e:
        print_test("OPA Service", False, str(e))
        return False

def test_api_endpoints():
    """Test various API endpoints"""
    endpoints = [
        ("/stats", "Statistics"),
        ("/jurisdictions", "Jurisdictions"),
        ("/representatives", "Representatives"),
        ("/bills", "Bills"),
        ("/committees", "Committees"),
        ("/events", "Events"),
        ("/docs", "API Documentation"),
        ("/api/parliamentary/sessions", "Parliamentary Sessions"),
        ("/api/parliamentary/hansard", "Hansard Records"),
        ("/api/parliamentary/policy/health", "Policy Health"),
        ("/api/progress/status", "Progress Status")
    ]
    
    all_passed = True
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            passed = response.status_code in [200, 307]  # 307 for redirects like /docs
            print_test(f"  {name} Endpoint", passed)
            if not passed:
                all_passed = False
        except Exception as e:
            print_test(f"  {name} Endpoint", False, str(e))
            all_passed = False
    
    return all_passed

def test_rate_limiting():
    """Test rate limiting functionality"""
    try:
        # Make multiple requests quickly
        responses = []
        for i in range(5):
            response = requests.get(f"{BASE_URL}/bills")
            responses.append(response.status_code)
        
        # Check if we got rate limiting headers
        last_response = requests.get(f"{BASE_URL}/bills")
        has_rate_limit_headers = 'x-ratelimit-limit' in last_response.headers
        
        print_test("Rate Limiting", has_rate_limit_headers,
                  "Rate limit headers present" if has_rate_limit_headers else "No rate limit headers found")
        return has_rate_limit_headers
    except Exception as e:
        print_test("Rate Limiting", False, str(e))
        return False

def test_parliamentary_features():
    """Test parliamentary-specific features"""
    try:
        # Test federal bill validation
        response = requests.get(f"{BASE_URL}/api/parliamentary/validation/federal-bills")
        validation_works = response.status_code == 200
        print_test("  Federal Bill Validation", validation_works)
        
        # Test speech search
        response = requests.get(f"{BASE_URL}/api/parliamentary/search/speeches?query=test&limit=10")
        search_works = response.status_code == 200
        print_test("  Speech Search", search_works)
        
        return validation_works and search_works
    except Exception as e:
        print_test("Parliamentary Features", False, str(e))
        return False

def test_scheduling_api():
    """Test scheduling functionality"""
    try:
        # Test scheduling a task
        response = requests.post(f"{BASE_URL}/schedule", json={"task_type": "test"})
        can_schedule = response.status_code == 200 and "task_id" in response.json()
        print_test("  Task Scheduling", can_schedule)
        
        # Test recent runs
        response = requests.get(f"{BASE_URL}/scraping-runs")
        can_get_runs = response.status_code == 200
        print_test("  Get Recent Runs", can_get_runs)
        
        return can_schedule and can_get_runs
    except Exception as e:
        print_test("Scheduling API", False, str(e))
        return False

def test_graphql_endpoint():
    """Test GraphQL endpoint"""
    try:
        query = """
        query {
            jurisdictions(first: 5) {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
        """
        response = requests.post(f"{BASE_URL}/graphql", 
                               json={"query": query},
                               headers={"Content-Type": "application/json"})
        passed = response.status_code == 200
        print_test("GraphQL Endpoint", passed)
        return passed
    except Exception as e:
        print_test("GraphQL Endpoint", False, str(e))
        return False

def test_flower_monitoring():
    """Test Flower (Celery monitoring) service"""
    try:
        response = requests.get(f"{FLOWER_URL}/api/workers")
        passed = response.status_code == 200
        print_test("Flower Monitoring", passed)
        return passed
    except Exception as e:
        print_test("Flower Monitoring", False, str(e))
        return False

def main():
    """Run all tests"""
    print(colored("\n🔍 OpenPolicy Backend Feature Test Suite\n", "blue", attrs=["bold"]))
    print(f"Testing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    test_results = []
    
    # Core API Tests
    print(colored("Core API Tests:", "cyan", attrs=["bold"]))
    test_results.append(test_api_health())
    test_results.append(test_api_endpoints())
    
    # Database Tests
    print(colored("\nDatabase Tests:", "cyan", attrs=["bold"]))
    test_results.append(test_database_connection())
    
    # Policy Engine Tests
    print(colored("\nPolicy Engine Tests:", "cyan", attrs=["bold"]))
    test_results.append(test_opa_service())
    test_results.append(test_rate_limiting())
    
    # Feature Tests
    print(colored("\nFeature Tests:", "cyan", attrs=["bold"]))
    test_results.append(test_parliamentary_features())
    test_results.append(test_scheduling_api())
    test_results.append(test_graphql_endpoint())
    
    # Monitoring Tests
    print(colored("\nMonitoring Tests:", "cyan", attrs=["bold"]))
    test_results.append(test_flower_monitoring())
    
    # Summary
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(colored(f"\n{'='*50}", "blue"))
    print(colored(f"Test Summary: {passed_tests}/{total_tests} tests passed", 
                 "green" if passed_tests == total_tests else "yellow", attrs=["bold"]))
    
    if passed_tests < total_tests:
        print(colored("\n⚠️  Some tests failed. Please check the services and configuration.", "yellow"))
        print("\nTroubleshooting tips:")
        print("1. Ensure all Docker services are running: docker-compose ps")
        print("2. Check service logs: docker-compose logs [service_name]")
        print("3. Verify database migrations: psql -h localhost -U openpolicy -d opencivicdata -f migrations/001_add_parliamentary_models.sql")
        print("4. Check OPA policies are mounted correctly in docker-compose.yml")
        sys.exit(1)
    else:
        print(colored("\n✅ All features are working correctly!", "green", attrs=["bold"]))
        sys.exit(0)

if __name__ == "__main__":
    main()