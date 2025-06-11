#!/usr/bin/env python3
"""
Dashboard Test Runner
====================

Main script to run all unified dashboard tests with comprehensive reporting.
"""

import asyncio
import sys
import os
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/ikino/dev/autonomous-multi-llm-agent')

from test_unified_dashboard_complete import UnifiedDashboardTester, test_youtube_integration_with_indydandev, test_dashboard_performance
from test_utils import TestReporter, PerformanceMonitor, check_dependencies, get_test_config

class DashboardTestRunner:
    """Main test runner for unified dashboard system"""
    
    def __init__(self, config=None):
        self.config = config or get_test_config()
        self.reporter = TestReporter()
        self.performance_monitor = PerformanceMonitor()
        self.start_time = datetime.now()
        
    def print_banner(self):
        """Print test banner"""
        print("=" * 80)
        print("🧪 UNIFIED DASHBOARD COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"📅 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
# DEMO CODE REMOVED: print(f"🔧 Test Mode: {'Mock Data' if self.config.get('mock_data') else 'Live Data'}")
        print(f"⚡ Performance Monitoring: {'Enabled' if self.config.get('performance_monitoring') else 'Disabled'}")
        print("=" * 80)
        print()
        
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check dependencies
        deps = check_dependencies()
        missing_deps = [dep for dep, available in deps.items() if not available]
        
        if missing_deps:
            print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
            print("   Install with: pip install " + " ".join(missing_deps))
            return False
        else:
            print("✅ All dependencies available")
        
        # Check if database file exists
        if Path('lifeos_local.db').exists():
            print("✅ Main database found")
        else:
            print("⚠️  Main database not found - will create test database")
        
        # Check if web server files exist
        if Path('web_server.py').exists():
            print("✅ Web server file found")
        else:
            print("❌ Web server file not found")
            return False
        
        # Check if YouTube processor exists
        if Path('simple_video_processor.py').exists():
            print("✅ YouTube processor found")
        else:
            print("⚠️  YouTube processor not found - some tests will be skipped")
        
        print()
        return True
    
    async def run_pre_test_setup(self):
        """Run pre-test setup"""
        print("🔧 Running pre-test setup...")
        
        # Start performance monitoring if enabled
        if self.config.get('performance_monitoring'):
            self.performance_monitor.start_monitoring()
            print("✅ Performance monitoring started")
        
        # Check if server is already running
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        
        if result == 0:
            print("✅ Web server already running")
        else:
            print("⚠️  Web server not running - tests will attempt to start it")
        
        print()
    
    async def run_main_test_suite(self):
        """Run the main test suite"""
        print("🚀 Running main dashboard test suite...")
        
        tester = UnifiedDashboardTester()
        
        try:
            results = await tester.run_all_tests()
            
            # Record results in our reporter
            for test_name, result in results['detailed_results'].items():
                self.reporter.add_result(
                    test_name,
                    result['passed'],
                    result['message'],
                    0  # Duration not tracked in main tester
                )
            
            return results
            
        except Exception as e:
            print(f"❌ Main test suite failed: {str(e)}")
            return {'total_tests': 0, 'passed': 0, 'failed': 1, 'errors': [str(e)]}
    
    async def run_youtube_tests(self):
        """Run YouTube-specific tests"""
        print("🎥 Running YouTube integration tests...")
        
        try:
            start_time = time.time()
            results = await test_youtube_integration_with_indydandev()
            duration = time.time() - start_time
            
            # Record YouTube test results
            successful_tests = len([r for r in results if r.get('success', False)])
            total_tests = len(results)
            
            self.reporter.add_result(
                "YouTube Integration",
                successful_tests > 0,
                f"{successful_tests}/{total_tests} videos processed successfully",
                duration
            )
            
            return results
            
        except Exception as e:
            print(f"❌ YouTube tests failed: {str(e)}")
            self.reporter.add_result(
                "YouTube Integration",
                False,
                f"Exception: {str(e)}",
                0
            )
            return []
    
    async def run_performance_tests(self):
        """Run performance tests"""
        print("⚡ Running performance tests...")
        
        try:
            start_time = time.time()
            results = await test_dashboard_performance()
            duration = time.time() - start_time
            
            # Analyze performance results
            successful_tests = len([r for r in results if r['success']])
            total_tests = len(results)
            avg_load_time = sum(r['load_time'] for r in results if r['load_time'] > 0) / max(1, len([r for r in results if r['load_time'] > 0]))
            
            self.reporter.add_result(
                "Performance Tests",
                successful_tests == total_tests,
                f"{successful_tests}/{total_tests} pages loaded, avg: {avg_load_time:.2f}s",
                duration
            )
            
            # Record system metrics if monitoring is enabled
            if self.config.get('performance_monitoring'):
                system_metrics = self.performance_monitor.get_system_metrics()
                self.performance_monitor.record_metric("CPU Usage", system_metrics['cpu_percent'], "%")
                self.performance_monitor.record_metric("Memory Usage", system_metrics['memory_percent'], "%")
            
            return results
            
        except Exception as e:
            print(f"❌ Performance tests failed: {str(e)}")
            self.reporter.add_result(
                "Performance Tests",
                False,
                f"Exception: {str(e)}",
                0
            )
            return []
    
    def generate_summary_report(self, main_results, youtube_results, performance_results):
        """Generate comprehensive summary report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate overall statistics
        total_tests = len(self.reporter.results)
        passed_tests = len([r for r in self.reporter.results if r['passed']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        print(f"⏱️  Total Duration: {total_duration:.1f} seconds")
        print(f"🧪 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()
        
        # Detailed breakdown
        print("📋 DETAILED BREAKDOWN:")
        print(f"   🌐 Dashboard Tests: {main_results.get('passed', 0)}/{main_results.get('total_tests', 0)}")
        print(f"   🎥 YouTube Tests: {len([r for r in youtube_results if r.get('success', False)])}/{len(youtube_results)}")
        print(f"   ⚡ Performance Tests: {len([r for r in performance_results if r.get('success', False)])}/{len(performance_results)}")
        
        # System metrics if available
        if self.config.get('performance_monitoring') and self.performance_monitor.metrics:
            print("\n⚡ PERFORMANCE METRICS:")
            for metric in self.performance_monitor.metrics[-3:]:  # Last 3 metrics
                print(f"   {metric['name']}: {metric['value']:.2f} {metric['unit']}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if failed_tests == 0:
            print("   🎉 All tests passed! The unified dashboard system is working perfectly.")
            print("   ✅ System is ready for production use.")
        else:
            print(f"   🔧 {failed_tests} tests failed. Review the detailed results for specific issues.")
            print("   📝 Check server logs and ensure all services are running properly.")
            if len(youtube_results) == 0 or not any(r.get('success', False) for r in youtube_results):
                print("   🎥 YouTube integration needs attention - check API keys and network connectivity.")
        
        print("\n" + "=" * 80)
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'duration': total_duration,
            'overall_success': failed_tests == 0
        }
    
    def save_reports(self):
        """Save test reports"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save HTML report if enabled
        if self.config.get('html_reports'):
            html_file = self.reporter.save_html_report(f"dashboard_test_report_{timestamp}.html")
            print(f"📄 HTML report saved: {html_file}")
        
        # Save performance report if monitoring was enabled
        if self.config.get('performance_monitoring') and self.performance_monitor.metrics:
            perf_report = self.performance_monitor.generate_report()
            perf_file = f"performance_report_{timestamp}.txt"
            with open(perf_file, 'w') as f:
                f.write(perf_report)
            print(f"⚡ Performance report saved: {perf_file}")
        
        # Save JSON summary
        summary_data = {
            'timestamp': timestamp,
            'config': self.config,
            'results': [
                {
                    'test_name': r['test_name'],
                    'passed': r['passed'],
                    'details': r['details'],
                    'duration': r['duration']
                }
                for r in self.reporter.results
            ]
        }
        
        import json
        json_file = f"test_summary_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        print(f"📊 JSON summary saved: {json_file}")
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        self.print_banner()
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("❌ Prerequisites not met. Exiting.")
            return False
        
        # Pre-test setup
        await self.run_pre_test_setup()
        
        # Run test suites
        main_results = await self.run_main_test_suite()
        youtube_results = await self.run_youtube_tests()
        performance_results = await self.run_performance_tests()
        
        # Generate summary
        summary = self.generate_summary_report(main_results, youtube_results, performance_results)
        
        # Save reports
        self.save_reports()
        
        return summary['overall_success']

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run unified dashboard tests')
# DEMO CODE REMOVED: parser.add_argument('--mock-data', action='store_true', help='Use mock data instead of live data')
    parser.add_argument('--no-performance', action='store_true', help='Disable performance monitoring')
    parser.add_argument('--no-html', action='store_true', help='Disable HTML report generation')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    
    args = parser.parse_args()
    
    # Configure test settings
    config = get_test_config()
# DEMO CODE REMOVED: if args.mock_data:
# DEMO CODE REMOVED: config['mock_data'] = True
    if args.no_performance:
        config['performance_monitoring'] = False
    if args.no_html:
        config['html_reports'] = False
    if args.quick:
        config['timeout_seconds'] = 10
        config['performance_monitoring'] = False
    
    # Run tests
    runner = DashboardTestRunner(config)
    
    try:
        success = asyncio.run(runner.run_all_tests())
        exit_code = 0 if success else 1
        
        if success:
            print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        else:
            print("\n❌ Some tests failed. Check the detailed reports.")
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()