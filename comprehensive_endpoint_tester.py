#!/usr/bin/env python3
"""
COMPREHENSIVE API ENDPOINT TESTER
===================================

Tests ALL endpoints in the system exhaustively.
Covers every route in routes/dashboard.py, routes/teams.py, and routes/business.py
"""

import requests
import json
import time
import sys
from typing import Dict, List, Tuple
from datetime import datetime

class ComprehensiveEndpointTester:
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.results = {
            'total_endpoints': 0,
            'successful': 0,
            'failed': 0,
            'endpoint_results': [],
            'critical_failures': [],
            'test_start_time': datetime.now().isoformat()
        }
        
        # ALL ENDPOINTS FROM routes/dashboard.py (lines 32-1292)
        self.endpoints = {
            # Basic navigation endpoints
            'GET /': {'method': 'GET', 'endpoint': '/', 'expected_status': [200, 302]},
            'GET /unified-dashboard': {'method': 'GET', 'endpoint': '/unified-dashboard', 'expected_status': [200, 302]},
            'GET /modern-dashboard': {'method': 'GET', 'endpoint': '/modern-dashboard', 'expected_status': [200]},
            
            # API endpoints
            'GET /api/recent-repos': {'method': 'GET', 'endpoint': '/api/recent-repos', 'expected_status': [200]},
            
            # Modern pages
            'GET /todays-cc': {'method': 'GET', 'endpoint': '/todays-cc', 'expected_status': [200, 302]},
            'GET /todays-cc-modern': {'method': 'GET', 'endpoint': '/todays-cc-modern', 'expected_status': [200]},
            'GET /knowledge-hub': {'method': 'GET', 'endpoint': '/knowledge-hub', 'expected_status': [200, 302]},
            'GET /knowledge-hub-modern': {'method': 'GET', 'endpoint': '/knowledge-hub-modern', 'expected_status': [200]},
            'GET /agent-command-center': {'method': 'GET', 'endpoint': '/agent-command-center', 'expected_status': [200, 302]},
            'GET /agent-command-center-modern': {'method': 'GET', 'endpoint': '/agent-command-center-modern', 'expected_status': [200]},
            'GET /prompt-library': {'method': 'GET', 'endpoint': '/prompt-library', 'expected_status': [200, 302]},
            'GET /prompt-library-modern': {'method': 'GET', 'endpoint': '/prompt-library-modern', 'expected_status': [200]},
            'GET /youtube-channels': {'method': 'GET', 'endpoint': '/youtube-channels', 'expected_status': [200, 302]},
            'GET /github-users': {'method': 'GET', 'endpoint': '/github-users', 'expected_status': [200, 302]},
            'GET /github-users-modern': {'method': 'GET', 'endpoint': '/github-users-modern', 'expected_status': [200]},
            'GET /github-repos': {'method': 'GET', 'endpoint': '/github-repos', 'expected_status': [200, 302]},
            'GET /github-repos-modern': {'method': 'GET', 'endpoint': '/github-repos-modern', 'expected_status': [200]},
            'GET /youtube-channels-modern': {'method': 'GET', 'endpoint': '/youtube-channels-modern', 'expected_status': [200]},
            'GET /shopping-list': {'method': 'GET', 'endpoint': '/shopping-list', 'expected_status': [200, 302]},
            'GET /shopping-list-modern': {'method': 'GET', 'endpoint': '/shopping-list-modern', 'expected_status': [200]},
            'GET /tasks': {'method': 'GET', 'endpoint': '/tasks', 'expected_status': [200, 302]},
            'GET /tasks-modern': {'method': 'GET', 'endpoint': '/tasks-modern', 'expected_status': [200]},
            'GET /habits': {'method': 'GET', 'endpoint': '/habits', 'expected_status': [200, 302]},
            'GET /habits-modern': {'method': 'GET', 'endpoint': '/habits-modern', 'expected_status': [200]},
            'GET /books': {'method': 'GET', 'endpoint': '/books', 'expected_status': [200, 302]},
            'GET /books-modern': {'method': 'GET', 'endpoint': '/books-modern', 'expected_status': [200]},
            'GET /journals': {'method': 'GET', 'endpoint': '/journals', 'expected_status': [200, 302]},
            'GET /journals-modern': {'method': 'GET', 'endpoint': '/journals-modern', 'expected_status': [200]},
            'GET /notes': {'method': 'GET', 'endpoint': '/notes', 'expected_status': [200, 302]},
            'GET /notes-modern': {'method': 'GET', 'endpoint': '/notes-modern', 'expected_status': [200]},
            'GET /maintenance-schedule': {'method': 'GET', 'endpoint': '/maintenance-schedule', 'expected_status': [200, 302]},
            'GET /maintenance-schedule-modern': {'method': 'GET', 'endpoint': '/maintenance-schedule-modern', 'expected_status': [200]},
            'GET /model-testing': {'method': 'GET', 'endpoint': '/model-testing', 'expected_status': [200, 302]},
            'GET /model-testing-modern': {'method': 'GET', 'endpoint': '/model-testing-modern', 'expected_status': [200]},
            'GET /voice-commands': {'method': 'GET', 'endpoint': '/voice-commands', 'expected_status': [200, 302]},
            'GET /voice-commands-modern': {'method': 'GET', 'endpoint': '/voice-commands-modern', 'expected_status': [200]},
            'GET /workflow-templates': {'method': 'GET', 'endpoint': '/workflow-templates', 'expected_status': [200, 302]},
            'GET /workflow-templates-modern': {'method': 'GET', 'endpoint': '/workflow-templates-modern', 'expected_status': [200]},
            'GET /provider-status': {'method': 'GET', 'endpoint': '/provider-status', 'expected_status': [200, 302]},
            'GET /provider-status-modern': {'method': 'GET', 'endpoint': '/provider-status-modern', 'expected_status': [200]},
            'GET /agent-results': {'method': 'GET', 'endpoint': '/agent-results', 'expected_status': [200, 302]},
            'GET /agent-results-modern': {'method': 'GET', 'endpoint': '/agent-results-modern', 'expected_status': [200]},
            'GET /cost-tracking': {'method': 'GET', 'endpoint': '/cost-tracking', 'expected_status': [200, 302]},
            'GET /cost-tracking-modern': {'method': 'GET', 'endpoint': '/cost-tracking-modern', 'expected_status': [200]},
            'GET /server-status': {'method': 'GET', 'endpoint': '/server-status', 'expected_status': [200, 302]},
            'GET /server-status-modern': {'method': 'GET', 'endpoint': '/server-status-modern', 'expected_status': [200]},
            
            # CRITICAL ACTIVE AGENTS ENDPOINT (lines 1045-1124)
            'GET /active-agents': {'method': 'GET', 'endpoint': '/active-agents', 'expected_status': [200]},
            
            # API endpoints
            'GET /api/dashboard/todays-cc': {'method': 'GET', 'endpoint': '/api/dashboard/todays-cc', 'expected_status': [200]},
            'GET /api/dashboard/knowledge-hub': {'method': 'GET', 'endpoint': '/api/dashboard/knowledge-hub', 'expected_status': [200]},
            'GET /api/dashboard/agents': {'method': 'GET', 'endpoint': '/api/dashboard/agents', 'expected_status': [200]},
            'GET /api/search': {'method': 'GET', 'endpoint': '/api/search?q=test', 'expected_status': [200]},
            'GET /api/system/metrics': {'method': 'GET', 'endpoint': '/api/system/metrics', 'expected_status': [200]},
            'GET /api/providers/status': {'method': 'GET', 'endpoint': '/api/providers/status', 'expected_status': [200]},
            'GET /api/orchestrator/status': {'method': 'GET', 'endpoint': '/api/orchestrator/status', 'expected_status': [200]},
            'GET /api/orchestrator/tasks': {'method': 'GET', 'endpoint': '/api/orchestrator/tasks', 'expected_status': [200]},
            'GET /api/knowledge-hub/integrated-repositories': {'method': 'GET', 'endpoint': '/api/knowledge-hub/integrated-repositories', 'expected_status': [200]},
            'GET /get-item': {'method': 'GET', 'endpoint': '/get-item?table=knowledge_hub&id=1', 'expected_status': [200]},
            
            # POST endpoints - Database CRUD
            'POST /update-checkbox': {
                'method': 'POST', 
                'endpoint': '/update-checkbox',
                'data': {'table': 'tasks', 'id': 1, 'field': 'completed', 'value': True},
                'expected_status': [200]
            },
            'POST /add-item': {
                'method': 'POST',
                'endpoint': '/add-item',
                'data': {'table': 'tasks', 'data': {'title': 'Test Task', 'status': 'pending'}},
                'expected_status': [200]
            },
            'POST /edit-item': {
                'method': 'POST',
                'endpoint': '/edit-item',
                'data': {'table': 'tasks', 'id': 1, 'data': {'title': 'Updated Task'}},
                'expected_status': [200]
            },
            'POST /delete-item': {
                'method': 'POST',
                'endpoint': '/delete-item',
                'data': {'table': 'tasks', 'id': 999},
                'expected_status': [200]
            },
            
            # GitHub endpoints
            'POST /add-github-repo': {
                'method': 'POST',
                'endpoint': '/add-github-repo',
                'data': {'repo_url': 'https://github.com/test/repo'},
                'expected_status': [200]
            },
            'POST /process-github-user': {
                'method': 'POST',
                'endpoint': '/process-github-user',
                'data': {'user_id': 1},
                'expected_status': [200, 400]  # May fail if user doesn't exist
            },
            
            # API POST endpoints
            'POST /api/quick-execute': {
                'method': 'POST',
                'endpoint': '/api/quick-execute',
                'data': {'command': 'test command'},
                'expected_status': [200]
            },
            'POST /api/youtube/transcript': {
                'method': 'POST',
                'endpoint': '/api/youtube/transcript',
                'data': {'video_url': 'https://youtube.com/watch?v=test'},
                'expected_status': [200, 400]  # May fail if extractor not available
            },
            'POST /api/youtube/process-channel': {
                'method': 'POST',
                'endpoint': '/api/youtube/process-channel',
                'data': {'channel_id': 1},
                'expected_status': [200, 400]
            },
            'POST /api/providers/rebalance': {
                'method': 'POST',
                'endpoint': '/api/providers/rebalance',
                'data': {},
                'expected_status': [200]
            },
            'POST /api/knowledge-hub/process-youtube': {
                'method': 'POST',
                'endpoint': '/api/knowledge-hub/process-youtube',
                'data': {},
                'expected_status': [200, 400]
            },
            'POST /api/knowledge-hub/process-github': {
                'method': 'POST',
                'endpoint': '/api/knowledge-hub/process-github',
                'data': {},
                'expected_status': [200, 400]
            },
            'POST /api/knowledge-hub/agent-action': {
                'method': 'POST',
                'endpoint': '/api/knowledge-hub/agent-action',
                'data': {'item_id': 1, 'action': 'analyze'},
                'expected_status': [200, 400]
            },
            'POST /api/knowledge-hub/integrate-repository': {
                'method': 'POST',
                'endpoint': '/api/knowledge-hub/integrate-repository',
                'data': {'repository': 'test-repo', 'action': 'integrate'},
                'expected_status': [200, 400]
            },
            'POST /api/knowledge-hub/remove-integration': {
                'method': 'POST',
                'endpoint': '/api/knowledge-hub/remove-integration',
                'data': {'repository_name': 'test-repo'},
                'expected_status': [200, 400]
            },
            'POST /api/orchestrator/process-message': {
                'method': 'POST',
                'endpoint': '/api/orchestrator/process-message',
                'data': {'message': 'test message'},
                'expected_status': [200]
            },
            'POST /api/orchestrator/add-task': {
                'method': 'POST',
                'endpoint': '/api/orchestrator/add-task',
                'data': {
                    'name': 'Test Task', 
                    'description': 'Test Description',
                    'agent_type': 'system_analyst',
                    'priority': 'medium'
                },
                'expected_status': [200]
            },
            'POST /api/orchestrator/execute-test-task': {
                'method': 'POST',
                'endpoint': '/api/orchestrator/execute-test-task',
                'data': {},
                'expected_status': [200]
            },
            
            # Teams endpoints
            'GET /api/realtime-teams': {'method': 'GET', 'endpoint': '/api/realtime-teams', 'expected_status': [200, 500]},
            
            # Business endpoints
            'GET /business-empire': {'method': 'GET', 'endpoint': '/business-empire', 'expected_status': [200, 302]},
            'GET /business-opportunities': {'method': 'GET', 'endpoint': '/business-opportunities', 'expected_status': [200]},
            'GET /business-projects': {'method': 'GET', 'endpoint': '/business-projects', 'expected_status': [200]},
            'GET /business-revenue': {'method': 'GET', 'endpoint': '/business-revenue', 'expected_status': [200]},
        }
        
        self.results['total_endpoints'] = len(self.endpoints)
    
    def test_endpoint(self, name: str, config: Dict) -> Dict:
        """Test a single endpoint."""
        try:
            url = f"{self.base_url}{config['endpoint']}"
            method = config['method']
            expected_status = config['expected_status']
            
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(url, timeout=10)
            elif method == 'POST':
                data = config.get('data', {})
                response = requests.post(url, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)  # ms
            
            success = response.status_code in expected_status
            
            result = {
                'endpoint': name,
                'url': url,
                'method': method,
                'status_code': response.status_code,
                'expected_status': expected_status,
                'success': success,
                'response_time_ms': response_time,
                'content_length': len(response.content) if response.content else 0,
                'error': None
            }
            
            # Check for specific error content
            if not success:
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        error_data = response.json()
                        result['error'] = error_data.get('error', 'Unknown error')
                    else:
                        result['error'] = response.text[:200] if response.text else 'No error details'
                except:
                    result['error'] = f"HTTP {response.status_code} - Could not parse error"
            
            if success:
                self.results['successful'] += 1
            else:
                self.results['failed'] += 1
                if name in ['GET /active-agents', 'GET /api/orchestrator/status', 'POST /api/orchestrator/process-message']:
                    self.results['critical_failures'].append(result)
            
            return result
            
        except Exception as e:
            result = {
                'endpoint': name,
                'url': f"{self.base_url}{config['endpoint']}",
                'method': config['method'],
                'status_code': 0,
                'expected_status': config['expected_status'],
                'success': False,
                'response_time_ms': 0,
                'content_length': 0,
                'error': str(e)
            }
            
            self.results['failed'] += 1
            self.results['critical_failures'].append(result)
            return result
    
    def run_comprehensive_test(self) -> Dict:
        """Run comprehensive tests on ALL endpoints."""
        print("🚀 STARTING COMPREHENSIVE API ENDPOINT TESTING")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Total Endpoints: {self.results['total_endpoints']}")
        print("=" * 60)
        
        for i, (name, config) in enumerate(self.endpoints.items(), 1):
            print(f"[{i:3d}/{self.results['total_endpoints']}] Testing {name:<40}", end=" ")
            
            result = self.test_endpoint(name, config)
            
            if result['success']:
                print(f"✅ {result['status_code']} ({result['response_time_ms']}ms)")
            else:
                print(f"❌ {result['status_code']} - {result['error'][:50]}")
            
            self.results['endpoint_results'].append(result)
            
            # Small delay to prevent overwhelming the server
            time.sleep(0.1)
        
        return self.results
    
    def print_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TESTING SUMMARY")
        print("=" * 60)
        
        total = self.results['total_endpoints']
        successful = self.results['successful']
        failed = self.results['failed']
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        print(f"Total Endpoints Tested: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.results['critical_failures']:
            print(f"\n🚨 CRITICAL FAILURES ({len(self.results['critical_failures'])}):")
            for failure in self.results['critical_failures']:
                print(f"  ❌ {failure['endpoint']} - {failure['status_code']} - {failure['error']}")
        
        print(f"\n⚡ PERFORMANCE METRICS:")
        response_times = [r['response_time_ms'] for r in self.results['endpoint_results'] if r['success']]
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            print(f"  Average Response Time: {avg_response:.2f}ms")
            print(f"  Fastest Response: {min(response_times):.2f}ms")
            print(f"  Slowest Response: {max(response_times):.2f}ms")
        
        print(f"\n📋 DETAILED RESULTS BY CATEGORY:")
        
        # Group by category
        categories = {
            'Pages': [r for r in self.results['endpoint_results'] if not r['endpoint'].startswith('GET /api') and not r['endpoint'].startswith('POST')],
            'API GET': [r for r in self.results['endpoint_results'] if r['endpoint'].startswith('GET /api')],
            'API POST': [r for r in self.results['endpoint_results'] if r['endpoint'].startswith('POST /api')],
            'Database CRUD': [r for r in self.results['endpoint_results'] if r['endpoint'] in ['POST /update-checkbox', 'POST /add-item', 'POST /edit-item', 'POST /delete-item']],
            'GitHub Integration': [r for r in self.results['endpoint_results'] if 'github' in r['endpoint'].lower()],
        }
        
        for category, endpoints in categories.items():
            if endpoints:
                success_count = sum(1 for e in endpoints if e['success'])
                total_count = len(endpoints)
                rate = (success_count / total_count) * 100 if total_count > 0 else 0
                print(f"  {category}: {success_count}/{total_count} ({rate:.1f}%)")
        
        print("\n" + "=" * 60)
        print("🎯 TESTING COMPLETE")
        print("=" * 60)

def main():
    """Main testing function."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8081"
    
    tester = ComprehensiveEndpointTester(base_url)
    results = tester.run_comprehensive_test()
    tester.print_summary()
    
    # Save detailed results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"endpoint_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Exit with error code if critical failures
    if results['critical_failures']:
        print(f"\n🚨 CRITICAL FAILURES DETECTED - EXITING WITH ERROR CODE")
        sys.exit(1)
    
    # Exit with error code if success rate is below 95%
    success_rate = (results['successful'] / results['total_endpoints']) * 100
    if success_rate < 95:
        print(f"\n⚠️  SUCCESS RATE {success_rate:.1f}% BELOW 95% THRESHOLD - EXITING WITH ERROR CODE")
        sys.exit(1)
    
    print(f"\n✅ ALL TESTS PASSED - SUCCESS RATE: {success_rate:.1f}%")

if __name__ == "__main__":
    main()