#!/usr/bin/env python3
"""
Comprehensive Test Runner for OpenPolicy Database
Orchestrates all testing phases and provides detailed reporting
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results/test_run.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    """Comprehensive test runner with reporting"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            "start_time": self.start_time.isoformat(),
            "test_suites": {},
            "summary": {},
            "environment": self._get_environment_info(),
            "phased_loading_tests": {},
            "performance_metrics": {}
        }
        
        # Ensure results directory exists
        Path("test_results").mkdir(exist_ok=True)
    
    def _get_environment_info(self):
        """Get environment information"""
        return {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd(),
            "environment_variables": {
                "TESTING": os.getenv("TESTING", "0"),
                "DB_URL": os.getenv("DB_URL", "not_set"),
                "REDIS_URL": os.getenv("REDIS_URL", "not_set")
            }
        }
    
    def check_prerequisites(self):
        """Check that all prerequisites are met"""
        logger.info("🔍 Checking prerequisites...")
        
        checks = []
        
        # Check Python packages
        try:
            import pytest
            import sqlalchemy
            import fastapi
            import redis
            checks.append(("Python packages", True, "All required packages available"))
        except ImportError as e:
            checks.append(("Python packages", False, f"Missing package: {e}"))
        
        # Check database connection
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                database="opencivicdata",
                user="openpolicy",
                password="openpolicy123"
            )
            conn.close()
            checks.append(("Database", True, "PostgreSQL connection successful"))
        except Exception as e:
            checks.append(("Database", False, f"PostgreSQL connection failed: {e}"))
        
        # Check Redis connection
        try:
            import redis as redis_client
            r = redis_client.Redis(host="localhost", port=6379, db=0)
            r.ping()
            checks.append(("Redis", True, "Redis connection successful"))
        except Exception as e:
            checks.append(("Redis", False, f"Redis connection failed: {e}"))
        
        # Check API availability
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                checks.append(("API", True, "API server responding"))
            else:
                checks.append(("API", False, f"API returned status {response.status_code}"))
        except Exception as e:
            checks.append(("API", False, f"API connection failed: {e}"))
        
        # Report results
        all_passed = True
        for check_name, passed, message in checks:
            status = "✅" if passed else "❌"
            logger.info(f"{status} {check_name}: {message}")
            if not passed:
                all_passed = False
        
        self.results["prerequisites"] = {
            "all_passed": all_passed,
            "checks": checks
        }
        
        return all_passed
    
    def run_test_suite(self, suite_name, test_path, extra_args=None):
        """Run a specific test suite"""
        logger.info(f"🧪 Running {suite_name} tests...")
        
        cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=short"]
        if extra_args:
            cmd.extend(extra_args)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout per suite
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse pytest output for detailed results
            output_lines = result.stdout.split('\n')
            passed = sum(1 for line in output_lines if " PASSED " in line)
            failed = sum(1 for line in output_lines if " FAILED " in line)
            skipped = sum(1 for line in output_lines if " SKIPPED " in line)
            
            suite_result = {
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "total": passed + failed + skipped,
                "duration_seconds": duration,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            self.results["test_suites"][suite_name] = suite_result
            
            status = "✅" if suite_result["success"] else "❌"
            logger.info(f"{status} {suite_name}: {passed} passed, {failed} failed, {skipped} skipped ({duration:.1f}s)")
            
            return suite_result["success"]
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {suite_name}: Timed out after 10 minutes")
            self.results["test_suites"][suite_name] = {
                "success": False,
                "error": "Timeout after 10 minutes"
            }
            return False
        except Exception as e:
            logger.error(f"❌ {suite_name}: Failed to run - {e}")
            self.results["test_suites"][suite_name] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    def run_coverage_analysis(self):
        """Run code coverage analysis"""
        logger.info("📊 Running coverage analysis...")
        
        try:
            cmd = [
                "python", "-m", "pytest", "tests/", 
                "--cov=src", 
                "--cov-report=html:test_results/coverage_html",
                "--cov-report=json:test_results/coverage.json",
                "--cov-report=term"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Read coverage results
            coverage_file = Path("test_results/coverage.json")
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                
                total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
                
                self.results["coverage"] = {
                    "total_percentage": total_coverage,
                    "detailed_results": coverage_data,
                    "html_report": "test_results/coverage_html/index.html"
                }
                
                status = "✅" if total_coverage >= 80 else "⚠️" if total_coverage >= 70 else "❌"
                logger.info(f"{status} Coverage: {total_coverage:.1f}%")
                
                return total_coverage >= 80
            else:
                logger.warning("⚠️ Coverage report not generated")
                return False
                
        except Exception as e:
            logger.error(f"❌ Coverage analysis failed: {e}")
            return False
    
    def test_phased_loading_system(self):
        """Test the phased loading system specifically"""
        logger.info("🚀 Testing phased loading system...")
        
        try:
            # Import phased loading components
            sys.path.insert(0, 'src')
            from phased_loading import phased_loader, LoadingStrategy
            
            # Test 1: Start and cancel loading session
            logger.info("Testing loading session lifecycle...")
            session_id = phased_loader.start_phased_loading(
                strategy=LoadingStrategy.BALANCED,
                manual_controls=True
            )
            
            # Get status
            status = phased_loader.get_current_status()
            
            # Test pause/resume
            pause_success = phased_loader.pause_loading()
            resume_success = phased_loader.resume_loading()
            
            # Cancel session
            cancel_success = phased_loader.cancel_loading()
            
            # Test 2: API endpoints
            logger.info("Testing phased loading API...")
            import requests
            
            api_tests = []
            
            # Test phases preview
            try:
                response = requests.get("http://localhost:8000/api/phased-loading/phases/preview")
                api_tests.append(("phases_preview", response.status_code == 200))
            except:
                api_tests.append(("phases_preview", False))
            
            # Test configuration endpoints
            try:
                response = requests.get("http://localhost:8000/api/phased-loading/config/strategies")
                api_tests.append(("config_strategies", response.status_code == 200))
            except:
                api_tests.append(("config_strategies", False))
            
            self.results["phased_loading_tests"] = {
                "session_lifecycle": {
                    "start_session": session_id is not None,
                    "get_status": status is not None,
                    "pause_resume": pause_success and resume_success,
                    "cancel_session": cancel_success
                },
                "api_endpoints": dict(api_tests),
                "overall_success": all([
                    session_id is not None,
                    status is not None,
                    pause_success,
                    resume_success,
                    cancel_success,
                    all(result for _, result in api_tests)
                ])
            }
            
            logger.info("✅ Phased loading system tests completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Phased loading tests failed: {e}")
            self.results["phased_loading_tests"] = {
                "error": str(e),
                "overall_success": False
            }
            return False
    
    def run_performance_benchmarks(self):
        """Run performance benchmarks"""
        logger.info("⚡ Running performance benchmarks...")
        
        try:
            # API Response Time Test
            import requests
            import time
            
            endpoints = [
                "/health",
                "/stats", 
                "/jurisdictions",
                "/representatives?limit=10"
            ]
            
            performance_results = {}
            
            for endpoint in endpoints:
                times = []
                for _ in range(5):  # 5 requests per endpoint
                    start = time.time()
                    try:
                        response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
                        end = time.time()
                        if response.status_code == 200:
                            times.append(end - start)
                    except:
                        pass
                
                if times:
                    avg_time = sum(times) / len(times)
                    max_time = max(times)
                    performance_results[endpoint] = {
                        "average_response_time": avg_time,
                        "max_response_time": max_time,
                        "within_target": avg_time < 5.0,  # 5 second target
                        "samples": len(times)
                    }
            
            # Database Performance Test
            try:
                sys.path.insert(0, 'src')
                from database import get_database_config, create_engine_from_config
                
                config = get_database_config()
                engine = create_engine_from_config(config.get_url())
                
                start = time.time()
                with engine.connect() as conn:
                    result = conn.execute("SELECT COUNT(*) FROM jurisdictions")
                    count = result.fetchone()[0]
                end = time.time()
                
                performance_results["database_query"] = {
                    "query_time": end - start,
                    "within_target": (end - start) < 1.0,  # 1 second target
                    "record_count": count
                }
                
            except Exception as e:
                logger.warning(f"Database performance test failed: {e}")
            
            self.results["performance_metrics"] = performance_results
            
            # Check if performance targets are met
            all_within_target = all(
                result.get("within_target", False) 
                for result in performance_results.values()
            )
            
            status = "✅" if all_within_target else "⚠️"
            logger.info(f"{status} Performance benchmarks completed")
            
            return all_within_target
            
        except Exception as e:
            logger.error(f"❌ Performance benchmarks failed: {e}")
            return False
    
    def generate_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Calculate summary statistics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        for suite_name, suite_result in self.results["test_suites"].items():
            if isinstance(suite_result, dict) and "total" in suite_result:
                total_tests += suite_result["total"]
                total_passed += suite_result["passed"]
                total_failed += suite_result["failed"]
                total_skipped += suite_result["skipped"]
        
        self.results["summary"] = {
            "end_time": end_time.isoformat(),
            "total_duration_seconds": duration.total_seconds(),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "overall_success": total_failed == 0 and total_tests > 0
        }
        
        # Save detailed results
        report_file = f"test_results/test_report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Generate HTML report
        self._generate_html_report(report_file.replace('.json', '.html'))
        
        logger.info(f"📄 Detailed report saved: {report_file}")
        
        return self.results["summary"]
    
    def _generate_html_report(self, html_file):
        """Generate HTML test report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OpenPolicy Database - Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .success {{ color: green; }}
                .failure {{ color: red; }}
                .warning {{ color: orange; }}
                .suite {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
                .metric {{ background: #f9f9f9; padding: 10px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🇨🇦 OpenPolicy Database Test Report</h1>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Duration:</strong> {self.results['summary'].get('total_duration_seconds', 0):.1f} seconds</p>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <h3>Overall Success</h3>
                    <p class="{'success' if self.results['summary'].get('overall_success') else 'failure'}">
                        {'✅ PASSED' if self.results['summary'].get('overall_success') else '❌ FAILED'}
                    </p>
                </div>
                <div class="metric">
                    <h3>Total Tests</h3>
                    <p>{self.results['summary'].get('total_tests', 0)}</p>
                </div>
                <div class="metric">
                    <h3>Success Rate</h3>
                    <p>{self.results['summary'].get('success_rate', 0):.1f}%</p>
                </div>
                <div class="metric">
                    <h3>Coverage</h3>
                    <p>{self.results.get('coverage', {}).get('total_percentage', 0):.1f}%</p>
                </div>
            </div>
            
            <h2>Test Suites</h2>
        """
        
        for suite_name, suite_result in self.results["test_suites"].items():
            if isinstance(suite_result, dict):
                status_class = "success" if suite_result.get("success") else "failure"
                html_content += f"""
                <div class="suite">
                    <h3 class="{status_class}">{suite_name}</h3>
                    <p><strong>Passed:</strong> {suite_result.get('passed', 0)}</p>
                    <p><strong>Failed:</strong> {suite_result.get('failed', 0)}</p>
                    <p><strong>Skipped:</strong> {suite_result.get('skipped', 0)}</p>
                    <p><strong>Duration:</strong> {suite_result.get('duration_seconds', 0):.1f}s</p>
                </div>
                """
        
        html_content += """
            </body>
        </html>
        """
        
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"📊 HTML report saved: {html_file}")
    
    def run_all_tests(self, include_performance=True, include_coverage=True):
        """Run all test suites"""
        logger.info("🚀 Starting comprehensive test run...")
        
        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("❌ Prerequisites not met. Aborting test run.")
            return False
        
        # Test suites to run
        test_suites = [
            ("API Tests", "tests/test_comprehensive_api.py"),
            ("Database Tests", "tests/test_database_comprehensive.py"),
            ("Scraper Tests", "tests/test_scrapers_comprehensive.py"),
            ("UI Tests", "tests/test_ui_comprehensive.py"),
            ("Integration Tests", "tests/test_integration_comprehensive.py")
        ]
        
        # Run each test suite
        all_passed = True
        for suite_name, test_path in test_suites:
            if not self.run_test_suite(suite_name, test_path):
                all_passed = False
        
        # Run phased loading tests
        if not self.test_phased_loading_system():
            all_passed = False
        
        # Run performance benchmarks
        if include_performance:
            if not self.run_performance_benchmarks():
                logger.warning("⚠️ Some performance benchmarks failed")
        
        # Run coverage analysis
        if include_coverage:
            if not self.run_coverage_analysis():
                logger.warning("⚠️ Coverage analysis failed")
        
        # Generate report
        summary = self.generate_report()
        
        # Final status
        if all_passed and summary["overall_success"]:
            logger.info("🎉 All tests passed! System is ready for production.")
            return True
        else:
            logger.error("❌ Some tests failed. Review the results and fix issues before deployment.")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="OpenPolicy Database Comprehensive Test Runner")
    parser.add_argument("--no-performance", action="store_true", help="Skip performance benchmarks")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage analysis")
    parser.add_argument("--suite", help="Run specific test suite only")
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    if args.suite:
        # Run specific suite only
        suite_mapping = {
            "api": "tests/test_comprehensive_api.py",
            "database": "tests/test_database_comprehensive.py",
            "scrapers": "tests/test_scrapers_comprehensive.py",
            "ui": "tests/test_ui_comprehensive.py",
            "integration": "tests/test_integration_comprehensive.py"
        }
        
        if args.suite in suite_mapping:
            runner.check_prerequisites()
            success = runner.run_test_suite(args.suite.title(), suite_mapping[args.suite])
            runner.generate_report()
            return 0 if success else 1
        else:
            logger.error(f"Unknown test suite: {args.suite}")
            return 1
    else:
        # Run all tests
        success = runner.run_all_tests(
            include_performance=not args.no_performance,
            include_coverage=not args.no_coverage
        )
        return 0 if success else 1


if __name__ == "__main__":
    exit(main())