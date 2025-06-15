import psutil
import platform
import sqlite3
import requests
import json
from datetime import datetime
import os

class SystemMonitor:
    def __init__(self):
        self.status_data = {}
        
    def check_system_health(self):
        try:
            # CPU Usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory Usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk Usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # System Info
            system_info = {
                'platform': platform.system(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            }
            
            self.status_data['system_health'] = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'system_info': system_info,
                'timestamp': datetime.now().isoformat()
            }
            return True
            
        except Exception as e:
            self.status_data['system_health'] = {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return False

    def check_database_connectivity(self, db_path='agents.db'):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT SQLITE_VERSION()")
            version = cursor.fetchone()
            conn.close()
            
            self.status_data['database'] = {
                'status': 'connected',
                'version': version[0],
                'timestamp': datetime.now().isoformat()
            }
            return True
            
        except Exception as e:
            self.status_data['database'] = {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return False

    def check_agent_status(self, agent_endpoints=None):
        if agent_endpoints is None:
            agent_endpoints = {
                'code_developer': 'http://localhost:5000/status',
                'task_manager': 'http://localhost:5001/status',
                'data_analyst': 'http://localhost:5002/status'
            }
        
        self.status_data['agents'] = {}
        
        for agent_name, endpoint in agent_endpoints.items():
            try:
                response = requests.get(endpoint, timeout=5)
                self.status_data['agents'][agent_name] = {
                    'status': 'active' if response.status_code == 200 else 'error',
                    'response_code': response.status_code,
                    'timestamp': datetime.now().isoformat()
                }
            except requests.exceptions.RequestException as e:
                self.status_data['agents'][agent_name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }

    def save_status_report(self, output_file='system_status_report.json'):
        try:
            with open(output_file, 'w') as f:
                json.dump(self.status_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving status report: {e}")
            return False

    def run_full_check(self):
        print("Starting system status check...")
        
        system_ok = self.check_system_health()
        print("System health check complete")
        
        db_ok = self.check_database_connectivity()
        print("Database connectivity check complete")
        
        self.check_agent_status()
        print("Agent status check complete")
        
        self.save_status_report()
        print("Status report saved")
        
        return all([system_ok, db_ok])

if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.run_full_check()