#!/usr/bin/env python3
"""
Production System Monitor & Dashboard
====================================

Professional monitoring system showing real-time status, self-healing, 
and system health with automated testing and fixes.
"""

import os
import sys
import json
import sqlite3
import subprocess
import traceback
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, request, jsonify, redirect, url_for
import psutil
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'production-monitor-key'

class SystemMonitor:
    """Production system monitoring and health checks."""
    
    def __init__(self):
        self.test_results = {}
        self.system_health = {}
        self.last_check = None
        
    def run_comprehensive_tests(self):
        """Run comprehensive system tests and collect results."""
        print("🔧 Running comprehensive system tests...")
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'tests': {},
            'system_info': self.get_system_info(),
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Test 1: Core System Files
        test_results['tests']['core_files'] = self.test_core_files()
        
        # Test 2: Database Connectivity
        test_results['tests']['database'] = self.test_databases()
        
        # Test 3: Python Dependencies
        test_results['tests']['dependencies'] = self.test_dependencies()
        
        # Test 4: Web Server Components
        test_results['tests']['web_components'] = self.test_web_components()
        
        # Test 5: Configuration Files
        test_results['tests']['config'] = self.test_configuration()
        
        # Test 6: Agent Systems
        test_results['tests']['agents'] = self.test_agent_systems()
        
        # Test 7: Integration Systems
        test_results['tests']['integrations'] = self.test_integrations()
        
        # Determine overall status
        failed_tests = [name for name, result in test_results['tests'].items() if not result['passed']]
        
        if not failed_tests:
            test_results['overall_status'] = 'healthy'
        elif len(failed_tests) <= 2:
            test_results['overall_status'] = 'degraded'
        else:
            test_results['overall_status'] = 'critical'
            
        # Collect issues and recommendations
        for test_name, result in test_results['tests'].items():
            if not result['passed']:
                if result.get('severity') == 'critical':
                    test_results['critical_issues'].append({
                        'test': test_name,
                        'issue': result['error'],
                        'fix': result.get('suggested_fix', 'Manual intervention required')
                    })
                else:
                    test_results['warnings'].append({
                        'test': test_name,
                        'issue': result['error'],
                        'fix': result.get('suggested_fix', 'Review recommended')
                    })
                    
            if result.get('recommendations'):
                test_results['recommendations'].extend(result['recommendations'])
        
        self.test_results = test_results
        self.last_check = datetime.now()
        
        # Save results to file
        with open('system_test_results.json', 'w') as f:
            json.dump(test_results, f, indent=2)
            
        return test_results
    
    def test_core_files(self):
        """Test if core system files exist and are accessible."""
        core_files = [
            'web_server.py',
            'core_system/main.py',
            'core_system/web_server.py',
            'core_system/requirements.txt',
            'core_system/src/',
            'templates/',
            'static/',
            '.gitignore',
            'README_CLEAN.md'
        ]
        
        missing_files = []
        for file_path in core_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            return {
                'passed': False,
                'error': f"Missing core files: {', '.join(missing_files)}",
                'severity': 'critical',
                'suggested_fix': "Restore missing files from GitHub repository or backup",
                'details': {'missing_files': missing_files}
            }
        
        return {
            'passed': True,
            'message': f"All {len(core_files)} core files present",
            'details': {'verified_files': len(core_files)}
        }
    
    def test_databases(self):
        """Test database connectivity and integrity."""
        databases = [
            'lifeos_local.db',
            'core_system/lifeos_local.db',  # Check both locations
            'agent_orchestrator.db',
            'real_orchestrator.db'
        ]
        
        db_status = {}
        accessible_dbs = 0
        
        for db_path in databases:
            try:
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    conn.close()
                    
                    db_status[db_path] = {
                        'accessible': True,
                        'tables': len(tables),
                        'size_mb': round(os.path.getsize(db_path) / (1024*1024), 2)
                    }
                    accessible_dbs += 1
                else:
                    db_status[db_path] = {'accessible': False, 'error': 'File not found'}
                    
            except Exception as e:
                db_status[db_path] = {'accessible': False, 'error': str(e)}
        
        if accessible_dbs == 0:
            return {
                'passed': False,
                'error': "No databases accessible",
                'severity': 'critical',
                'suggested_fix': "Initialize databases or restore from backup",
                'details': db_status
            }
        elif accessible_dbs < len(databases) / 2:
            return {
                'passed': False,
                'error': f"Only {accessible_dbs}/{len(databases)} databases accessible",
                'severity': 'warning',
                'suggested_fix': "Check database permissions and initialization",
                'details': db_status
            }
        
        return {
            'passed': True,
            'message': f"{accessible_dbs}/{len(databases)} databases accessible",
            'details': db_status
        }
    
    def test_dependencies(self):
        """Test Python dependencies."""
        required_packages = [
            'flask', 'psutil', 'sqlite3', 'pathlib', 'datetime',
            'json', 'logging', 'subprocess'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        # Test requirements file
        req_files = ['requirements.txt', 'core_system/requirements.txt']
        req_file_exists = any(os.path.exists(f) for f in req_files)
        
        if missing_packages:
            return {
                'passed': False,
                'error': f"Missing packages: {', '.join(missing_packages)}",
                'severity': 'critical',
                'suggested_fix': "pip install -r requirements.txt",
                'details': {
                    'missing_packages': missing_packages,
                    'requirements_file_exists': req_file_exists
                }
            }
        
        return {
            'passed': True,
            'message': f"All {len(required_packages)} required packages available",
            'details': {
                'verified_packages': len(required_packages),
                'requirements_file_exists': req_file_exists
            }
        }
    
    def test_web_components(self):
        """Test web server components."""
        template_files = []
        static_files = []
        
        # Check templates
        if os.path.exists('templates'):
            template_files = [f for f in os.listdir('templates') if f.endswith('.html')]
        if os.path.exists('core_system/templates'):
            template_files.extend([f for f in os.listdir('core_system/templates') if f.endswith('.html')])
        
        # Check static files
        if os.path.exists('static'):
            for root, dirs, files in os.walk('static'):
                static_files.extend(files)
        if os.path.exists('core_system/static'):
            for root, dirs, files in os.walk('core_system/static'):
                static_files.extend(files)
        
        issues = []
        if len(template_files) < 5:
            issues.append("Few template files found")
        if len(static_files) < 3:
            issues.append("Few static files found")
        
        # Test if Flask can import
        try:
            from flask import Flask
            flask_ok = True
        except ImportError:
            flask_ok = False
            issues.append("Flask not available")
        
        if issues:
            return {
                'passed': False,
                'error': "; ".join(issues),
                'severity': 'warning',
                'suggested_fix': "Check template and static file structure",
                'details': {
                    'template_files': len(template_files),
                    'static_files': len(static_files),
                    'flask_available': flask_ok
                }
            }
        
        return {
            'passed': True,
            'message': f"Web components OK - {len(template_files)} templates, {len(static_files)} static files",
            'details': {
                'template_files': len(template_files),
                'static_files': len(static_files),
                'flask_available': flask_ok
            }
        }
    
    def test_configuration(self):
        """Test configuration files."""
        config_paths = [
            'config/',
            'core_system/config/',
            '.env',
            '.env.example'
        ]
        
        config_status = {}
        for path in config_paths:
            config_status[path] = os.path.exists(path)
        
        # Check .gitignore
        gitignore_ok = os.path.exists('.gitignore')
        if gitignore_ok:
            with open('.gitignore', 'r') as f:
                gitignore_content = f.read()
                has_exclusions = '*.log' in gitignore_content and '*.db' in gitignore_content
        else:
            has_exclusions = False
        
        issues = []
        if not any(config_status.values()):
            issues.append("No configuration directories found")
        if not gitignore_ok:
            issues.append("No .gitignore file")
        elif not has_exclusions:
            issues.append(".gitignore missing important exclusions")
        
        if issues:
            return {
                'passed': False,
                'error': "; ".join(issues),
                'severity': 'warning',
                'suggested_fix': "Review configuration setup",
                'details': {
                    'config_paths': config_status,
                    'gitignore_exists': gitignore_ok,
                    'gitignore_configured': has_exclusions
                }
            }
        
        return {
            'passed': True,
            'message': "Configuration files OK",
            'details': {
                'config_paths': config_status,
                'gitignore_exists': gitignore_ok,
                'gitignore_configured': has_exclusions
            }
        }
    
    def test_agent_systems(self):
        """Test agent system components."""
        agent_files = [
            'src/agents/',
            'core_system/src/agents/',
            'src/orchestrator/',
            'core_system/src/orchestrator/',
            'real_agent_orchestrator.py',
            'autonomous_learning_agent.py'
        ]
        
        agent_status = {}
        for path in agent_files:
            if os.path.exists(path):
                if os.path.isdir(path):
                    files = [f for f in os.listdir(path) if f.endswith('.py')]
                    agent_status[path] = {'exists': True, 'python_files': len(files)}
                else:
                    agent_status[path] = {'exists': True, 'type': 'file'}
            else:
                agent_status[path] = {'exists': False}
        
        existing_components = sum(1 for status in agent_status.values() if status.get('exists'))
        
        if existing_components < len(agent_files) / 2:
            return {
                'passed': False,
                'error': f"Only {existing_components}/{len(agent_files)} agent components found",
                'severity': 'warning',
                'suggested_fix': "Review agent system structure",
                'details': agent_status
            }
        
        return {
            'passed': True,
            'message': f"Agent systems OK - {existing_components}/{len(agent_files)} components",
            'details': agent_status
        }
    
    def test_integrations(self):
        """Test integration components."""
        integration_indicators = [
            'src/integrations/',
            'core_system/src/integrations/',
            'notion-mcp-server/',
            'mcp-servers/',
            'github_repo_processor.py',
            'simple_video_processor.py'
        ]
        
        integration_status = {}
        for path in integration_indicators:
            integration_status[path] = os.path.exists(path)
        
        available_integrations = sum(integration_status.values())
        
        recommendations = []
        if not integration_status.get('github_repo_processor.py'):
            recommendations.append("Consider setting up GitHub integration")
        if not integration_status.get('simple_video_processor.py'):
            recommendations.append("Consider setting up YouTube processing")
        
        return {
            'passed': True,  # Integrations are optional
            'message': f"Integration status - {available_integrations}/{len(integration_indicators)} available",
            'details': integration_status,
            'recommendations': recommendations
        }
    
    def get_system_info(self):
        """Get current system information."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'python_version': sys.version,
                'working_directory': os.getcwd(),
                'timestamp': datetime.now().isoformat(),
                'uptime_hours': round((time.time() - psutil.boot_time()) / 3600, 1)
            }
        except Exception as e:
            return {'error': str(e)}

    def run_self_healing(self):
        """Attempt to automatically fix common issues."""
        fixes_applied = []
        
        # Fix 1: Create missing directories
        missing_dirs = ['logs', 'data', 'config']
        for dir_name in missing_dirs:
            if not os.path.exists(dir_name):
                try:
                    os.makedirs(dir_name, exist_ok=True)
                    fixes_applied.append(f"Created directory: {dir_name}")
                except Exception as e:
                    logger.error(f"Failed to create {dir_name}: {e}")
        
        # Fix 2: Initialize database if missing
        if not os.path.exists('lifeos_local.db'):
            try:
                conn = sqlite3.connect('lifeos_local.db')
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_health (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TEXT,
                        details TEXT
                    )
                ''')
                conn.commit()
                conn.close()
                fixes_applied.append("Initialized primary database")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
        
        # Fix 3: Set correct permissions
        try:
            for script in ['web_server.py', 'core_system/main.py']:
                if os.path.exists(script):
                    os.chmod(script, 0o755)
            fixes_applied.append("Set script permissions")
        except Exception as e:
            logger.error(f"Failed to set permissions: {e}")
        
        return fixes_applied

# Initialize monitor
monitor = SystemMonitor()

@app.route('/')
def dashboard():
    """Main production dashboard."""
    return render_template('production_dashboard.html', 
                         test_results=monitor.test_results,
                         system_info=monitor.get_system_info(),
                         last_check=monitor.last_check)

@app.route('/api/run-tests', methods=['POST'])
def run_tests():
    """API endpoint to trigger comprehensive testing."""
    try:
        results = monitor.run_comprehensive_tests()
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/self-heal', methods=['POST'])
def self_heal():
    """API endpoint to trigger self-healing."""
    try:
        fixes = monitor.run_self_healing()
        return jsonify({'success': True, 'fixes_applied': fixes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/system-status')
def system_status():
    """Get current system status."""
    try:
        return jsonify({
            'system_info': monitor.get_system_info(),
            'last_test_results': monitor.test_results,
            'last_check': monitor.last_check.isoformat() if monitor.last_check else None
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/start-system', methods=['POST'])
def start_system():
    """Start the main system."""
    try:
        # Try to start the main web server
        if os.path.exists('core_system/web_server.py'):
            result = subprocess.run([
                sys.executable, 'core_system/web_server.py'
            ], capture_output=True, text=True, timeout=5)
            
            return jsonify({
                'success': True,
                'message': 'System start initiated',
                'output': result.stdout[:200] if result.stdout else "Starting..."
            })
        elif os.path.exists('web_server.py'):
            result = subprocess.run([
                sys.executable, 'web_server.py'
            ], capture_output=True, text=True, timeout=5)
            
            return jsonify({
                'success': True,
                'message': 'System start initiated',
                'output': result.stdout[:200] if result.stdout else "Starting..."
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No web server file found'
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': True,
            'message': 'System is starting (background process)'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🏥 Production System Monitor Starting...")
    print("📊 Dashboard available at: http://localhost:8080")
    print("🔧 Features: System Testing, Self-Healing, Real-time Monitoring")
    print("=" * 60)
    
    # Run initial system check
    print("🔍 Running initial system assessment...")
    initial_results = monitor.run_comprehensive_tests()
    
    if initial_results['overall_status'] == 'critical':
        print("⚠️  CRITICAL ISSUES DETECTED:")
        for issue in initial_results['critical_issues']:
            print(f"   - {issue['test']}: {issue['issue']}")
        print("🔧 Attempting self-healing...")
        fixes = monitor.run_self_healing()
        if fixes:
            print("✅ Applied fixes:", ", ".join(fixes))
    elif initial_results['overall_status'] == 'degraded':
        print("⚠️  System is degraded but functional")
        print(f"📊 {len(initial_results['warnings'])} warnings detected")
    else:
        print("✅ System is healthy")
    
    print("🚀 Starting dashboard...")
    app.run(host='0.0.0.0', port=8080, debug=False)