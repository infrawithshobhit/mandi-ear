#!/usr/bin/env python3
"""
Integration test runner for MANDI EAR system
Runs comprehensive integration tests and generates reports
"""

import asyncio
import subprocess
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import argparse

class IntegrationTestRunner:
    """Runs and manages integration tests"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.test_results: Dict[str, Any] = {}
        self.start_time = None
        self.end_time = None
    
    def log(self, message: str):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")
    
    def run_pytest(self, test_file: str, markers: str = None) -> Dict[str, Any]:
        """Run pytest on a specific test file"""
        self.log(f"Running tests in {test_file}")
        
        cmd = ["python", "-m", "pytest", test_file, "-v", "--tb=short", "--json-report", "--json-report-file=test_report.json"]
        
        if markers:
            cmd.extend(["-m", markers])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Try to load JSON report
            report_data = {}
            try:
                with open("test_report.json", "r") as f:
                    report_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "report": report_data
            }
            
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Test execution timed out",
                "report": {}
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "report": {}
            }
    
    def check_system_health(self) -> bool:
        """Check if the system is healthy before running tests"""
        self.log("Checking system health...")
        
        try:
            import httpx
            
            async def health_check():
                async with httpx.AsyncClient(timeout=10.0) as client:
                    try:
                        response = await client.get("http://localhost:8000/health/")
                        return response.status_code == 200
                    except Exception:
                        return False
            
            return asyncio.run(health_check())
            
        except ImportError:
            self.log("httpx not available, skipping health check")
            return True
        except Exception as e:
            self.log(f"Health check failed: {e}")
            return False
    
    def run_all_tests(self, include_slow: bool = False, include_performance: bool = False) -> Dict[str, Any]:
        """Run all integration tests"""
        self.start_time = time.time()
        self.log("Starting integration test suite")
        
        # Check system health first
        if not self.check_system_health():
            self.log("WARNING: System health check failed, tests may fail")
        
        test_suites = [
            {
                "name": "Integration Workflows",
                "file": "tests/test_integration_workflows.py",
                "markers": None
            }
        ]
        
        if include_performance:
            test_suites.append({
                "name": "Performance Tests",
                "file": "tests/test_performance_load.py",
                "markers": "slow" if include_slow else "not slow"
            })
        
        results = {}
        
        for suite in test_suites:
            self.log(f"Running {suite['name']}...")
            result = self.run_pytest(suite["file"], suite["markers"])
            results[suite["name"]] = result
            
            if result["returncode"] == 0:
                self.log(f"✓ {suite['name']} passed")
            else:
                self.log(f"✗ {suite['name']} failed")
                if self.verbose:
                    self.log(f"STDOUT: {result['stdout']}")
                    self.log(f"STDERR: {result['stderr']}")
        
        self.end_time = time.time()
        self.test_results = results
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        if not self.test_results:
            return {"error": "No test results available"}
        
        total_duration = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": total_duration,
            "summary": {
                "total_suites": len(self.test_results),
                "passed_suites": sum(1 for r in self.test_results.values() if r["returncode"] == 0),
                "failed_suites": sum(1 for r in self.test_results.values() if r["returncode"] != 0)
            },
            "suites": {}
        }
        
        for suite_name, result in self.test_results.items():
            suite_report = {
                "status": "passed" if result["returncode"] == 0 else "failed",
                "returncode": result["returncode"]
            }
            
            # Extract test details from pytest report
            if result.get("report"):
                pytest_report = result["report"]
                suite_report.update({
                    "total_tests": pytest_report.get("summary", {}).get("total", 0),
                    "passed_tests": pytest_report.get("summary", {}).get("passed", 0),
                    "failed_tests": pytest_report.get("summary", {}).get("failed", 0),
                    "skipped_tests": pytest_report.get("summary", {}).get("skipped", 0),
                    "duration": pytest_report.get("duration", 0)
                })
                
                # Add failed test details
                if pytest_report.get("tests"):
                    failed_tests = [
                        {
                            "name": test.get("nodeid", "unknown"),
                            "outcome": test.get("outcome", "unknown"),
                            "error": test.get("call", {}).get("longrepr", "")
                        }
                        for test in pytest_report["tests"]
                        if test.get("outcome") == "failed"
                    ]
                    if failed_tests:
                        suite_report["failed_test_details"] = failed_tests
            
            # Add stdout/stderr if there were failures
            if result["returncode"] != 0:
                suite_report["stdout"] = result["stdout"]
                suite_report["stderr"] = result["stderr"]
            
            report["suites"][suite_name] = suite_report
        
        return report
    
    def print_summary(self):
        """Print test summary to console"""
        if not self.test_results:
            print("No test results available")
            return
        
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("MANDI EAR INTEGRATION TEST SUMMARY")
        print("="*60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Duration: {report['duration_seconds']:.2f} seconds")
        print(f"Total Suites: {report['summary']['total_suites']}")
        print(f"Passed Suites: {report['summary']['passed_suites']}")
        print(f"Failed Suites: {report['summary']['failed_suites']}")
        
        print("\nSuite Details:")
        print("-" * 40)
        
        for suite_name, suite_data in report["suites"].items():
            status_icon = "✓" if suite_data["status"] == "passed" else "✗"
            print(f"{status_icon} {suite_name}: {suite_data['status'].upper()}")
            
            if "total_tests" in suite_data:
                print(f"  Tests: {suite_data['passed_tests']}/{suite_data['total_tests']} passed")
                if suite_data.get("duration"):
                    print(f"  Duration: {suite_data['duration']:.2f}s")
            
            if suite_data.get("failed_test_details"):
                print("  Failed tests:")
                for failed_test in suite_data["failed_test_details"][:3]:  # Show first 3
                    print(f"    - {failed_test['name']}")
                if len(suite_data["failed_test_details"]) > 3:
                    print(f"    ... and {len(suite_data['failed_test_details']) - 3} more")
        
        print("\n" + "="*60)
        
        # Overall result
        if report['summary']['failed_suites'] == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"❌ {report['summary']['failed_suites']} suite(s) failed")
        
        print("="*60)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run MANDI EAR integration tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--slow", action="store_true", help="Include slow tests")
    parser.add_argument("--performance", action="store_true", help="Include performance tests")
    parser.add_argument("--report", help="Save detailed report to JSON file")
    parser.add_argument("--health-check", action="store_true", help="Only run health check")
    
    args = parser.parse_args()
    
    runner = IntegrationTestRunner(verbose=args.verbose)
    
    if args.health_check:
        if runner.check_system_health():
            print("✓ System is healthy")
            sys.exit(0)
        else:
            print("✗ System health check failed")
            sys.exit(1)
    
    # Run tests
    try:
        results = runner.run_all_tests(
            include_slow=args.slow,
            include_performance=args.performance
        )
        
        # Print summary
        runner.print_summary()
        
        # Save detailed report if requested
        if args.report:
            report = runner.generate_report()
            with open(args.report, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nDetailed report saved to: {args.report}")
        
        # Exit with appropriate code
        failed_suites = sum(1 for r in results.values() if r["returncode"] != 0)
        sys.exit(failed_suites)
        
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nTest execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()