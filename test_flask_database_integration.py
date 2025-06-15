#!/usr/bin/env python3
"""
Test Flask Database Integration
Tests all Flask routes that interact with the database to ensure they work properly.
"""

import sys
import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class FlaskDatabaseTester:
    """Test Flask application database integration."""
    
    def __init__(self, base_url="http://localhost:8081"):
        self.base_url = base_url
        self.test_results = {}
        self.errors = []
        
    def test_database_routes(self) -> Dict[str, Any]:
        """Test all database-dependent routes."""
        routes_to_test = [
            # Dashboard routes
            ('GET', '/', 'home_page'),
            ('GET', '/unified-dashboard', 'unified_dashboard'),
            
            # Knowledge Hub routes
            ('GET', '/knowledge-hub', 'knowledge_hub'),
            ('GET', '/api/knowledge-hub', 'knowledge_hub_api'),
            
            # GitHub routes
            ('GET', '/github-users', 'github_users'),
            ('GET', '/api/github-users', 'github_users_api'),
            
            # Agent routes
            ('GET', '/active-agents', 'active_agents'),
            ('GET', '/api/active-agents', 'active_agents_api'),
            
            # Business routes
            ('GET', '/business/opportunities', 'business_opportunities'),
            ('GET', '/api/business/opportunities', 'business_opportunities_api'),
            ('GET', '/business/projects', 'business_projects'),
            ('GET', '/api/business/projects', 'business_projects_api'),
            
            # Task routes
            ('GET', '/tasks', 'tasks'),
            ('GET', '/api/tasks', 'tasks_api'),
            
            # Social media routes
            ('GET', '/social-media', 'social_media'),
            ('GET', '/api/social-media/posts', 'social_media_posts_api'),
            
            # TDD routes
            ('GET', '/tdd', 'tdd_dashboard'),
            ('GET', '/api/tdd/cycles', 'tdd_cycles_api'),
            
            # Analytics routes
            ('GET', '/analytics', 'analytics_dashboard'),
            ('GET', '/api/analytics/overview', 'analytics_overview_api'),
        ]
        
        results = {}
        
        for method, route, test_name in routes_to_test:
            try:
                print(f"Testing {method} {route}...")
                
                start_time = time.time()
                
                if method == 'GET':
                    response = requests.get(f"{self.base_url}{route}", timeout=30)
                else:
                    response = requests.request(method, f"{self.base_url}{route}", timeout=30)
                
                response_time = time.time() - start_time
                
                result = {
                    'method': method,
                    'route': route,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 200,
                    'content_length': len(response.content),
                    'headers': dict(response.headers)
                }
                
                # Additional checks for API routes
                if route.startswith('/api/'):
                    try:
                        json_data = response.json()
                        result['json_valid'] = True
                        result['json_keys'] = list(json_data.keys()) if isinstance(json_data, dict) else []
                        result['data_count'] = len(json_data) if isinstance(json_data, list) else 1
                    except:
                        result['json_valid'] = False
                
                results[test_name] = result
                
                if response.status_code == 200:
                    print(f"  ✅ {test_name}: {response.status_code} ({response_time:.3f}s)")
                else:
                    print(f"  ❌ {test_name}: {response.status_code} ({response_time:.3f}s)")
                    
            except Exception as e:
                print(f"  💥 {test_name}: Error - {str(e)}")
                results[test_name] = {
                    'method': method,
                    'route': route,
                    'error': str(e),
                    'success': False
                }
                self.errors.append(f"{test_name}: {str(e)}")
        
        return results
    
    def test_database_operations(self) -> Dict[str, Any]:
        """Test database CRUD operations through API."""
        operations_results = {}
        
        # Test adding a new task
        try:
            print("Testing task creation...")
            task_data = {
                'title': 'Database Integration Test Task',
                'description': 'Test task created by database integration tester',
                'priority': 'High',
                'status': 'Todo'
            }
            
            response = requests.post(
                f"{self.base_url}/api/tasks",
                json=task_data,
                timeout=10
            )
            
            operations_results['create_task'] = {
                'success': response.status_code in [200, 201],
                'status_code': response.status_code,
                'response': response.json() if response.status_code in [200, 201] else response.text
            }
            
            if response.status_code in [200, 201]:
                print("  ✅ Task creation successful")
                
                # Try to update the task
                task_id = response.json().get('id')
                if task_id:
                    update_data = {'status': 'In Progress'}
                    update_response = requests.put(
                        f"{self.base_url}/api/tasks/{task_id}",
                        json=update_data,
                        timeout=10
                    )
                    
                    operations_results['update_task'] = {
                        'success': update_response.status_code == 200,
                        'status_code': update_response.status_code
                    }
                    
                    if update_response.status_code == 200:
                        print("  ✅ Task update successful")
                    else:
                        print(f"  ❌ Task update failed: {update_response.status_code}")
            else:
                print(f"  ❌ Task creation failed: {response.status_code}")
                
        except Exception as e:
            print(f"  💥 Task operations error: {str(e)}")
            operations_results['create_task'] = {'error': str(e), 'success': False}
        
        # Test knowledge hub operations
        try:
            print("Testing knowledge hub operations...")
            
            # Get knowledge hub data
            response = requests.get(f"{self.base_url}/api/knowledge-hub", timeout=10)
            
            operations_results['get_knowledge_hub'] = {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data_count': len(response.json()) if response.status_code == 200 else 0
            }
            
            if response.status_code == 200:
                print(f"  ✅ Knowledge hub retrieval successful ({len(response.json())} items)")
            else:
                print(f"  ❌ Knowledge hub retrieval failed: {response.status_code}")
                
        except Exception as e:
            print(f"  💥 Knowledge hub operations error: {str(e)}")
            operations_results['get_knowledge_hub'] = {'error': str(e), 'success': False}
        
        return operations_results
    
    def generate_test_report(self, route_results: Dict, operation_results: Dict) -> str:
        """Generate comprehensive test report."""
        report = []
        report.append("="*80)
        report.append("🧪 FLASK DATABASE INTEGRATION TEST REPORT")
        report.append("="*80)
        report.append(f"🕐 Generated: {datetime.now().isoformat()}")
        report.append(f"🌐 Base URL: {self.base_url}")
        
        # Route test summary
        total_routes = len(route_results)
        successful_routes = sum(1 for r in route_results.values() if r.get('success', False))
        
        report.append(f"\n📊 ROUTE TESTING SUMMARY")
        report.append(f"   Total Routes Tested: {total_routes}")
        report.append(f"   Successful Routes: {successful_routes}")
        report.append(f"   Failed Routes: {total_routes - successful_routes}")
        report.append(f"   Success Rate: {successful_routes/total_routes:.1%}")
        
        # Detailed route results
        report.append(f"\n📝 DETAILED ROUTE RESULTS")
        for test_name, result in route_results.items():
            if result.get('success', False):
                response_time = result.get('response_time', 0)
                content_length = result.get('content_length', 0)
                report.append(f"   ✅ {test_name}: {result['status_code']} ({response_time:.3f}s, {content_length} bytes)")
                
                if result.get('json_valid'):
                    data_count = result.get('data_count', 0)
                    report.append(f"      JSON: Valid ({data_count} items)")
            else:
                error = result.get('error', 'Unknown error')
                status_code = result.get('status_code', 'N/A')
                report.append(f"   ❌ {test_name}: {status_code} - {error}")
        
        # Database operations summary
        total_ops = len(operation_results)
        successful_ops = sum(1 for r in operation_results.values() if r.get('success', False))
        
        report.append(f"\n🗄️ DATABASE OPERATIONS SUMMARY")
        report.append(f"   Total Operations Tested: {total_ops}")
        report.append(f"   Successful Operations: {successful_ops}")
        report.append(f"   Failed Operations: {total_ops - successful_ops}")
        report.append(f"   Success Rate: {successful_ops/total_ops:.1%}" if total_ops > 0 else "   Success Rate: N/A")
        
        # Detailed operation results
        report.append(f"\n🔧 DETAILED OPERATION RESULTS")
        for op_name, result in operation_results.items():
            if result.get('success', False):
                status_code = result.get('status_code', 'N/A')
                data_count = result.get('data_count', '')
                report.append(f"   ✅ {op_name}: {status_code} {data_count}")
            else:
                error = result.get('error', 'Unknown error')
                status_code = result.get('status_code', 'N/A')
                report.append(f"   ❌ {op_name}: {status_code} - {error}")
        
        # Performance metrics
        response_times = [r.get('response_time', 0) for r in route_results.values() if 'response_time' in r]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            report.append(f"\n⚡ PERFORMANCE METRICS")
            report.append(f"   Average Response Time: {avg_response_time:.3f}s")
            report.append(f"   Fastest Response: {min_response_time:.3f}s")
            report.append(f"   Slowest Response: {max_response_time:.3f}s")
        
        # Errors
        if self.errors:
            report.append(f"\n❌ ERRORS ENCOUNTERED")
            for error in self.errors:
                report.append(f"   • {error}")
        
        # Overall status
        overall_success = (successful_routes == total_routes) and (successful_ops == total_ops)
        report.append(f"\n🎯 OVERALL STATUS")
        if overall_success:
            report.append("   ✅ ALL TESTS PASSED - Flask database integration is working correctly")
        else:
            report.append("   ⚠️  SOME TESTS FAILED - Review failed routes and operations")
        
        report.append("\n" + "="*80)
        
        return "\n".join(report)
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Flask database integration test."""
        print("🧪 Starting Flask Database Integration Test...")
        print("="*60)
        
        # Test routes
        print("\n📊 Testing Database-Dependent Routes...")
        route_results = self.test_database_routes()
        
        # Test database operations
        print("\n🗄️ Testing Database Operations...")
        operation_results = self.test_database_operations()
        
        # Generate report
        report = self.generate_test_report(route_results, operation_results)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'route_results': route_results,
            'operation_results': operation_results,
            'report': report,
            'errors': self.errors
        }

def main():
    """Run Flask database integration tests."""
    tester = FlaskDatabaseTester()
    
    # Check if server is running
    try:
        response = requests.get(f"{tester.base_url}/", timeout=5)
        if response.status_code != 200:
            print(f"⚠️  Server responded with status {response.status_code}")
            print("🚀 Starting Flask server...")
            os.system("python3 web_server.py &")
            time.sleep(5)  # Wait for server to start
    except requests.exceptions.ConnectionError:
        print("❌ Flask server is not running. Please start it first:")
        print("   python3 web_server.py")
        print("\nOr run this script with auto-start:")
        print("   python3 test_flask_database_integration.py --auto-start")
        return
    
    # Run tests
    results = tester.run_comprehensive_test()
    
    # Print report
    print("\n" + results['report'])
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"flask_database_integration_test_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    main()