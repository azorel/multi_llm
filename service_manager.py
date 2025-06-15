#!/usr/bin/env python3
"""
Service Manager - Kill all services and start only what's needed
"""

import subprocess
import time
import os
import signal

def kill_all_services():
    """Kill all running services"""
    print("🔥 KILLING ALL SERVICES")
    
    # List of processes to kill
    processes_to_kill = [
        'flask',
        'python3 -m flask',
        'web_server',
        'gunicorn',
        'uvicorn',
        'celery',
        'redis-server',
        'nginx',
        'apache2',
        'httpd',
        'node',
        'npm',
        'yarn'
    ]
    
    for process in processes_to_kill:
        try:
            # Kill by process name
            subprocess.run(['pkill', '-f', process], capture_output=True)
            print(f"✅ Killed: {process}")
        except Exception as e:
            print(f"⚠️ Could not kill {process}: {e}")
    
    # Kill by specific ports
    ports_to_kill = [8080, 8081, 8082, 5000, 3000, 80, 443]
    
    for port in ports_to_kill:
        try:
            # Find process using port
            result = subprocess.run(
                ['lsof', '-t', f'-i:{port}'], 
                capture_output=True, text=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"✅ Killed process {pid} on port {port}")
                    except:
                        pass
        except Exception as e:
            print(f"⚠️ Could not check port {port}: {e}")
    
    # Wait for processes to die
    time.sleep(3)
    print("🔥 All services killed")

def start_essential_services():
    """Start only the essential services needed"""
    print("🚀 STARTING ESSENTIAL SERVICES")
    
    # Check if we're in the right directory
    if not os.path.exists('web_server.py'):
        print("❌ ERROR: web_server.py not found. Are you in the right directory?")
        return False
    
    # Start Flask web server
    try:
        print("🌐 Starting Flask web server on port 8081...")
        
        # Start Flask in background
        process = subprocess.Popen([
            'python3', '-m', 'flask', 
            '--app', 'web_server',
            'run', 
            '--host=0.0.0.0', 
            '--port=8081',
            '--reload'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for startup
        time.sleep(5)
        
        # Test if server is running
        test_result = subprocess.run([
            'curl', '-s', '-I', 'http://localhost:8081/'
        ], capture_output=True, text=True)
        
        if 'HTTP/1.1' in test_result.stdout:
            print("✅ Flask server started successfully")
            print(f"🌐 Web interface: http://localhost:8081/")
            return True
        else:
            print("❌ Flask server failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Flask: {e}")
        return False

def check_database():
    """Check if database is accessible"""
    print("🗄️ CHECKING DATABASE")
    
    try:
        import sqlite3
        conn = sqlite3.connect('lifeos_local.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"✅ Database accessible with {len(tables)} tables")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def verify_core_systems():
    """Verify core systems are working"""
    print("🔧 VERIFYING CORE SYSTEMS")
    
    # Test TDD system
    try:
        from tdd_system import tdd_system
        print("✅ TDD system importable")
    except Exception as e:
        print(f"❌ TDD system error: {e}")
    
    # Test orchestrator
    try:
        from enhanced_orchestrator_claude_gemini import enhanced_orchestrator
        print(f"✅ Orchestrator available with {len(enhanced_orchestrator.agents)} agents")
    except Exception as e:
        print(f"❌ Orchestrator error: {e}")
    
    # Test database
    database_ok = check_database()
    
    return database_ok

def main():
    """Main service management function"""
    print("🎯 SERVICE MANAGER - CLEAN RESTART")
    print("=" * 50)
    
    # Step 1: Kill everything
    kill_all_services()
    
    # Step 2: Verify core systems
    systems_ok = verify_core_systems()
    
    # Step 3: Start essential services
    if systems_ok:
        server_ok = start_essential_services()
        
        if server_ok:
            print("\n🎉 SYSTEM READY")
            print("=" * 30)
            print("🌐 Web Interface: http://localhost:8081/")
            print("🔧 Dashboard: http://localhost:8081/unified-dashboard")
            print("📱 Social Media: http://localhost:8081/social-media")
            print("\n💡 Only essential services are running:")
            print("   - Flask web server (port 8081)")
            print("   - SQLite database")
            print("   - Multi-agent orchestrator")
            print("   - TDD system")
        else:
            print("\n❌ STARTUP FAILED")
            print("Could not start essential services")
    else:
        print("\n❌ CORE SYSTEMS BROKEN")
        print("Fix core systems before starting services")

if __name__ == "__main__":
    main()