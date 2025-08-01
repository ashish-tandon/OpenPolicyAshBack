#!/usr/bin/env python3
"""
Comprehensive System Test for OpenPolicy Database

This script validates that all components are working correctly after setup.
"""

import sys
import requests
import time
import json
from datetime import datetime
import subprocess
import psycopg2

def print_status(message, status="INFO"):
    """Print colored status message"""
    colors = {
        "INFO": "\033[94m",    # Blue
        "PASS": "\033[92m",    # Green
        "FAIL": "\033[91m",    # Red
        "WARN": "\033[93m",    # Yellow
        "END": "\033[0m"       # Reset
    }
    print(f"{colors.get(status, '')}{status}: {message}{colors['END']}")

def test_docker_services():
    """Test that all Docker services are running"""
    print_status("Testing Docker services...")
    
    try:
        result = subprocess.run(['docker-compose', 'ps'], 
                              capture_output=True, text=True, check=True)
        
        required_services = ['postgres', 'redis', 'api', 'dashboard', 'celery_worker', 'celery_beat', 'flower']
        running_services = []
        
        for line in result.stdout.split('\n'):
            for service in required_services:
                if service in line and 'Up' in line:
                    running_services.append(service)
                    print_status(f"Service {service} is running", "PASS")
        
        missing_services = set(required_services) - set(running_services)
        if missing_services:
            for service in missing_services:
                print_status(f"Service {service} is not running", "FAIL")
            return False
        
        return True
    except Exception as e:
        print_status(f"Failed to check Docker services: {e}", "FAIL")
        return False

def test_database_connection():
    """Test database connectivity and basic structure"""
    print_status("Testing database connection...")
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="opencivicdata",
            user="openpolicy",
            password="openpolicy123"
        )
        
        cursor = conn.cursor()
        
        # Test basic tables exist
        tables = ['jurisdictions', 'representatives', 'bills', 'committees']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print_status(f"Table {table} exists with {count} records", "PASS")
        
        conn.close()
        return True
    except Exception as e:
        print_status(f"Database connection failed: {e}", "FAIL")
        return False

def test_api_endpoints():
    """Test API endpoints are responding"""
    print_status("Testing API endpoints...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/health",
        "/stats", 
        "/jurisdictions",
        "/representatives",
        "/bills",
        "/docs"
    ]
    
    all_passed = True
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print_status(f"API endpoint {endpoint} is responding", "PASS")
            else:
                print_status(f"API endpoint {endpoint} returned {response.status_code}", "FAIL")
                all_passed = False
        except Exception as e:
            print_status(f"API endpoint {endpoint} failed: {e}", "FAIL")
            all_passed = False
    
    return all_passed

def test_dashboard():
    """Test dashboard is accessible"""
    print_status("Testing dashboard...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print_status("Dashboard is accessible", "PASS")
            return True
        else:
            print_status(f"Dashboard returned {response.status_code}", "FAIL")
            return False
    except Exception as e:
        print_status(f"Dashboard test failed: {e}", "FAIL")
        return False

def test_flower_monitoring():
    """Test Flower monitoring interface"""
    print_status("Testing Flower monitoring...")
    
    try:
        response = requests.get("http://localhost:5555", timeout=10)
        if response.status_code == 200:
            print_status("Flower monitoring is accessible", "PASS")
            return True
        else:
            print_status(f"Flower returned {response.status_code}", "FAIL")
            return False
    except Exception as e:
        print_status(f"Flower test failed: {e}", "FAIL")
        return False

def test_federal_priority():
    """Test federal bills priority features"""
    print_status("Testing federal priority features...")
    
    try:
        # Test if federal monitoring module can be imported
        sys.path.append('./src')
        from federal_priority import federal_monitor
        
        # Test getting federal metrics
        metrics = federal_monitor.get_federal_priority_metrics()
        
        if 'total_federal_bills' in metrics:
            print_status("Federal priority monitoring is active", "PASS")
            print_status(f"Federal bills tracked: {metrics.get('total_federal_bills', 0)}", "INFO")
            return True
        else:
            print_status("Federal priority metrics not available", "FAIL")
            return False
    except Exception as e:
        print_status(f"Federal priority test failed: {e}", "FAIL")
        return False

def test_scheduling_api():
    """Test scheduling API endpoints"""
    print_status("Testing scheduling API...")
    
    try:
        # Test scheduling a test task
        response = requests.post(
            "http://localhost:8000/schedule",
            json={"task_type": "test"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print_status(f"Test task scheduled successfully: {task_id}", "PASS")
            
            # Wait a moment and check task status
            time.sleep(2)
            status_response = requests.get(f"http://localhost:8000/tasks/{task_id}", timeout=10)
            
            if status_response.status_code == 200:
                print_status("Task status endpoint working", "PASS")
                return True
            else:
                print_status("Task status endpoint failed", "FAIL")
                return False
        else:
            print_status(f"Scheduling API returned {response.status_code}", "FAIL")
            return False
    except Exception as e:
        print_status(f"Scheduling API test failed: {e}", "FAIL")
        return False

def test_data_quality():
    """Test basic data quality"""
    print_status("Testing data quality...")
    
    try:
        # Check if we have some basic data
        response = requests.get("http://localhost:8000/stats", timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            
            checks = [
                ("jurisdictions", stats.get('total_jurisdictions', 0) > 0),
                ("representatives", stats.get('total_representatives', 0) >= 0),
                ("bills", stats.get('total_bills', 0) >= 0)
            ]
            
            all_passed = True
            for check_name, passed in checks:
                if passed:
                    print_status(f"Data quality check {check_name}: PASS", "PASS")
                else:
                    print_status(f"Data quality check {check_name}: FAIL", "FAIL")
                    all_passed = False
            
            return all_passed
        else:
            print_status("Could not fetch stats for data quality check", "FAIL")
            return False
    except Exception as e:
        print_status(f"Data quality test failed: {e}", "FAIL")
        return False

def main():
    """Run all system tests"""
    print_status("🇨🇦 OpenPolicy Database System Test", "INFO")
    print_status("=" * 50, "INFO")
    
    tests = [
        ("Docker Services", test_docker_services),
        ("Database Connection", test_database_connection),
        ("API Endpoints", test_api_endpoints),
        ("Dashboard", test_dashboard),
        ("Flower Monitoring", test_flower_monitoring),
        ("Federal Priority", test_federal_priority),
        ("Scheduling API", test_scheduling_api),
        ("Data Quality", test_data_quality)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print_status(f"\nRunning {test_name} test...", "INFO")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_status(f"Test {test_name} crashed: {e}", "FAIL")
            results.append((test_name, False))
    
    # Summary
    print_status("\n" + "=" * 50, "INFO")
    print_status("TEST SUMMARY", "INFO")
    print_status("=" * 50, "INFO")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_status(f"✅ {test_name}", "PASS")
            passed += 1
        else:
            print_status(f"❌ {test_name}", "FAIL")
    
    print_status(f"\nResults: {passed}/{total} tests passed", "INFO")
    
    if passed == total:
        print_status("🎉 All tests passed! OpenPolicy Database is working correctly.", "PASS")
        print_status("\n📊 Access your system:", "INFO")
        print_status("   Dashboard: http://localhost:3000", "INFO")
        print_status("   API Docs: http://localhost:8000/docs", "INFO")
        print_status("   Monitoring: http://localhost:5555", "INFO")
        return 0
    else:
        print_status(f"❌ {total - passed} tests failed. Please check the errors above.", "FAIL")
        return 1

if __name__ == "__main__":
    exit(main())