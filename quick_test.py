#!/usr/bin/env python3
"""
Quick Dashboard Test
==================

Quick test to verify the unified dashboard system is working.
Runs essential tests only for immediate feedback.
"""

import asyncio
import aiohttp
import sqlite3
import time
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/home/ikino/dev/autonomous-multi-llm-agent')

async def quick_test_dashboard():
    """Run quick tests to verify dashboard is working"""
    print("🚀 QUICK DASHBOARD TEST")
    print("=" * 50)
    
    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    def log_test(name, passed, message=""):
        results['total'] += 1
        if passed:
            results['passed'] += 1
            print(f"✅ {name}: PASSED {message}")
        else:
            results['failed'] += 1
            error = f"❌ {name}: FAILED - {message}"
            print(error)
            results['errors'].append(error)
    
    # Test 1: Check if required files exist
    print("1️⃣ Checking required files...")
    required_files = ['web_server.py', 'simple_video_processor.py']
    for file in required_files:
        exists = Path(file).exists()
        log_test(f"File {file}", exists, "" if exists else "File not found")
    
    # Test 2: Check database
    print("\n2️⃣ Checking database...")
    db_exists = Path('lifeos_local.db').exists()
    log_test("Database file", db_exists, "lifeos_local.db" if db_exists else "Will be created")
    
    if db_exists:
        try:
            conn = sqlite3.connect('lifeos_local.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            log_test("Database tables", len(tables) > 0, f"Found {len(tables)} tables")
        except Exception as e:
            log_test("Database access", False, str(e))
    
    # Test 3: Test server connectivity
    print("\n3️⃣ Testing server connectivity...")
    server_running = False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:5000/", timeout=5) as response:
                server_running = response.status in [200, 302]
                log_test("Server connectivity", server_running, f"Status: {response.status}")
    except Exception as e:
        log_test("Server connectivity", False, "Server not responding - start with 'python3 web_server.py'")
    
    # Test 4: Test key pages (if server is running)
    if server_running:
        print("\n4️⃣ Testing key pages...")
        pages = [
            "/todays-cc",
            "/knowledge-hub", 
            "/agent-command-center",
            "/active-agents"
        ]
        
        async with aiohttp.ClientSession() as session:
            for page in pages:
                try:
                    async with session.get(f"http://localhost:5000{page}", timeout=10) as response:
                        content = await response.text()
                        success = response.status == 200 and len(content) > 100
                        log_test(f"Page {page}", success, f"Status: {response.status}, Size: {len(content)}")
                except Exception as e:
                    log_test(f"Page {page}", False, str(e))
    
    # Test 5: Test basic API functionality (if server is running)
    if server_running:
        print("\n5️⃣ Testing API functionality...")
        async with aiohttp.ClientSession() as session:
            # Test orchestrator command
            try:
                test_data = {'command': 'test'}
                async with session.post(
                    "http://localhost:5000/orchestrator-command",
                    json=test_data,
                    timeout=10
                ) as response:
                    result = await response.json()
                    success = response.status == 200 and result.get('success', False)
                    log_test("Orchestrator API", success, f"Response: {result.get('response', '')[:50]}...")
            except Exception as e:
                log_test("Orchestrator API", False, str(e))
    
    # Test 6: Test YouTube processor import
    print("\n6️⃣ Testing YouTube processor...")
    try:
        import simple_video_processor
        has_function = hasattr(simple_video_processor, 'get_video_transcript_robust')
        log_test("YouTube processor import", True, "")
        log_test("Transcript function", has_function, "get_video_transcript_robust" if has_function else "Function missing")
    except Exception as e:
        log_test("YouTube processor import", False, str(e))
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 QUICK TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success Rate: {(results['passed'] / results['total'] * 100):.1f}%")
    
    if results['failed'] == 0:
        print("\n🎉 All quick tests passed! Dashboard system is ready.")
        print("💡 Run 'python3 run_dashboard_tests.py' for comprehensive testing.")
    else:
        print(f"\n🔧 {results['failed']} tests failed. Issues found:")
        for error in results['errors']:
            print(f"   • {error}")
        print("\n💡 Fix the issues above, then run comprehensive tests.")
    
    if not server_running:
        print("\n🚀 To start the dashboard server:")
        print("   python3 web_server.py")
        print("   Then visit: http://localhost:5000")
    
    return results['failed'] == 0

def check_environment():
    """Check if environment is set up correctly"""
    print("🔍 ENVIRONMENT CHECK")
    print("=" * 30)
    
    # Check Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"Python Version: {py_version}")
    
    # Check working directory
    print(f"Working Directory: {os.getcwd()}")
    
    # Check if we're in the right directory
    if not Path('web_server.py').exists():
        print("❌ Not in the autonomous-multi-llm-agent directory!")
        print("   cd /home/ikino/dev/autonomous-multi-llm-agent")
        return False
    
    # Check basic imports
    try:
        import flask
        print("✅ Flask available")
    except ImportError:
        print("❌ Flask not installed: pip install flask")
        return False
    
    try:
        import aiohttp
        print("✅ aiohttp available")
    except ImportError:
        print("❌ aiohttp not installed: pip install aiohttp")
        return False
    
    print("✅ Environment looks good!")
    return True

async def main():
    """Main function"""
    print("🧪 UNIFIED DASHBOARD QUICK TEST")
    print("=" * 60)
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed. Fix the issues above.")
        return False
    
    print()
    
    # Run quick tests
    success = await quick_test_dashboard()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 QUICK TEST COMPLETE - System is working!")
        print("🚀 Ready for comprehensive testing with:")
        print("   python3 run_dashboard_tests.py")
    else:
        print("🔧 QUICK TEST FOUND ISSUES - Fix them first:")
        print("   1. Make sure you're in the right directory")
        print("   2. Install missing dependencies")
        print("   3. Start the web server if needed")
        print("   4. Check database setup")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Error: {str(e)}")
        sys.exit(1)