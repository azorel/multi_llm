#!/usr/bin/env python3
"""
BUSINESS EMPIRE LAUNCHER - MASTER CONTROL SYSTEM
================================================

Launch and coordinate all business ventures in the AI-powered empire.
Features: Multi-service orchestration, health monitoring, revenue tracking.

Services Managed:
- RC Trail Finder (Port 5001)
- Van Life Optimizer (Port 5003) 
- Custom Parts Marketplace (Port 5004)
- Business Empire Dashboard (Port 5000)
- Business Automation Engine (Background)

Revenue Target: $25,000+/month across all ventures
"""

import subprocess
import threading
import time
import requests
import asyncio
import json
from datetime import datetime
import os
import signal
import sys

class BusinessEmpireLauncher:
    """Master launcher and coordinator for the business empire."""
    
    def __init__(self):
        self.services = {
            'rc_trail_finder': {
                'script': 'rc_trail_finder.py',
                'port': 5001,
                'name': 'RC Trail Finder',
                'revenue_target': 5000,
                'process': None,
                'status': 'stopped'
            },
            'van_life_optimizer': {
                'script': 'van_life_optimizer.py',
                'port': 5003,
                'name': 'Van Life Workspace Optimizer',
                'revenue_target': 4000,
                'process': None,
                'status': 'stopped'
            },
            'custom_parts_marketplace': {
                'script': 'custom_parts_marketplace.py',
                'port': 5004,
                'name': 'Custom Parts Marketplace',
                'revenue_target': 3200,
                'process': None,
                'status': 'stopped'
            },
            'business_dashboard': {
                'script': 'web_server.py',
                'port': 5000,
                'name': 'Business Empire Dashboard',
                'revenue_target': 0,  # Coordination hub
                'process': None,
                'status': 'stopped'
            }
        }
        
        self.automation_engine = None
        self.total_revenue_target = sum(s['revenue_target'] for s in self.services.values())
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.shutdown_handler)
        signal.signal(signal.SIGTERM, self.shutdown_handler)
    
    def print_empire_header(self):
        """Print the business empire startup header."""
        print("🏢" + "=" * 78 + "🏢")
        print("👑                    AI BUSINESS EMPIRE LAUNCHER                     👑")
        print("🚀                Transforming Lifestyle into Profit                  🚀")
        print("=" * 80)
        print(f"📊 REVENUE TARGET: ${self.total_revenue_target:,}/month")
        print(f"🤖 MULTI-AGENT AI: 8 specialized agents with Gemini 2.5 Pro")
        print(f"🏗️  BUSINESS VENTURES: {len([s for s in self.services.values() if s['revenue_target'] > 0])}")
        print("=" * 80)
        print()
    
    def launch_service(self, service_key: str):
        """Launch a specific service."""
        service = self.services[service_key]
        
        print(f"🚀 Launching {service['name']}...")
        print(f"   📜 Script: {service['script']}")
        print(f"   🌐 Port: {service['port']}")
        print(f"   💰 Revenue Target: ${service['revenue_target']:,}/month")
        
        try:
            # Launch the service
            process = subprocess.Popen([
                'python3', service['script']
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            service['process'] = process
            service['status'] = 'starting'
            
            # Give service time to start
            time.sleep(3)
            
            # Check if service is responding
            if self.check_service_health(service_key):
                service['status'] = 'running'
                print(f"   ✅ {service['name']} is running on port {service['port']}")
                print(f"   🌐 URL: http://localhost:{service['port']}")
            else:
                service['status'] = 'failed'
                print(f"   ❌ {service['name']} failed to start properly")
            
        except Exception as e:
            service['status'] = 'failed'
            print(f"   ❌ Error launching {service['name']}: {e}")
        
        print()
    
    def check_service_health(self, service_key: str) -> bool:
        """Check if a service is responding."""
        service = self.services[service_key]
        
        try:
            response = requests.get(f"http://localhost:{service['port']}", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def launch_all_services(self):
        """Launch all business services."""
        print("🚀 LAUNCHING ALL BUSINESS SERVICES")
        print("-" * 50)
        
        # Launch services in order
        service_order = ['business_dashboard', 'rc_trail_finder', 'van_life_optimizer', 'custom_parts_marketplace']
        
        for service_key in service_order:
            self.launch_service(service_key)
            time.sleep(2)  # Stagger launches
        
        # Start automation engine
        self.start_automation_engine()
        
        # Print summary
        self.print_launch_summary()
    
    def start_automation_engine(self):
        """Start the business automation engine."""
        print("🤖 Starting Business Automation Engine...")
        
        try:
            from business_automation_engine import automation_engine
            
            # Run initial automation in background thread
            def run_automation():
                asyncio.run(automation_engine.run_daily_automation())
            
            automation_thread = threading.Thread(target=run_automation, daemon=True)
            automation_thread.start()
            
            print("   ✅ Business Automation Engine started")
            print("   🧠 AI-powered optimization active")
            print("   📊 Cross-business analytics running")
            print()
            
        except Exception as e:
            print(f"   ⚠️ Automation engine warning: {e}")
            print("   📝 Empire will run without AI automation")
            print()
    
    def print_launch_summary(self):
        """Print launch summary and status."""
        print("📊 BUSINESS EMPIRE STATUS")
        print("=" * 50)
        
        running_services = 0
        total_revenue_potential = 0
        
        for service_key, service in self.services.items():
            status_icon = "✅" if service['status'] == 'running' else "❌" if service['status'] == 'failed' else "⏳"
            
            print(f"{status_icon} {service['name']}")
            print(f"   🌐 http://localhost:{service['port']}")
            print(f"   💰 ${service['revenue_target']:,}/month target")
            print(f"   📊 Status: {service['status']}")
            print()
            
            if service['status'] == 'running':
                running_services += 1
                total_revenue_potential += service['revenue_target']
        
        print(f"🎯 EMPIRE METRICS:")
        print(f"   🏃 Services Running: {running_services}/{len(self.services)}")
        print(f"   💰 Revenue Potential: ${total_revenue_potential:,}/month")
        print(f"   🎯 Target Achievement: {(total_revenue_potential/self.total_revenue_target)*100:.1f}%")
        print()
        
        if running_services == len(self.services):
            print("🎉 BUSINESS EMPIRE FULLY OPERATIONAL!")
            print("👑 All services running successfully")
            print("🚀 Ready to transform lifestyle into profit!")
        else:
            print("⚠️  Some services failed to start")
            print("🔧 Check individual service logs for details")
        
        print("\n" + "=" * 50)
        self.print_access_urls()
    
    def print_access_urls(self):
        """Print all access URLs."""
        print("🌐 BUSINESS EMPIRE ACCESS URLS")
        print("-" * 30)
        
        for service_key, service in self.services.items():
            if service['status'] == 'running':
                print(f"🔗 {service['name']}: http://localhost:{service['port']}")
        
        print(f"\n👑 MASTER DASHBOARD: http://localhost:5000/business-empire")
        print(f"📊 UNIFIED CONTROL: http://localhost:5000/unified-dashboard")
        print()
    
    def monitor_empire(self):
        """Monitor empire health and performance."""
        print("🔍 Starting Empire Health Monitor...")
        print("📊 Checking services every 30 seconds")
        print("💡 Press Ctrl+C to stop monitoring")
        print("-" * 50)
        
        try:
            while True:
                time.sleep(30)  # Check every 30 seconds
                
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"\n⏰ Health Check - {current_time}")
                
                healthy_services = 0
                for service_key, service in self.services.items():
                    if service['status'] == 'running':
                        if self.check_service_health(service_key):
                            print(f"   ✅ {service['name']} - Healthy")
                            healthy_services += 1
                        else:
                            print(f"   ⚠️ {service['name']} - Not responding")
                            service['status'] = 'unhealthy'
                    else:
                        print(f"   ❌ {service['name']} - Not running")
                
                health_percentage = (healthy_services / len(self.services)) * 100
                print(f"📊 Empire Health: {health_percentage:.1f}% ({healthy_services}/{len(self.services)} services)")
                
                if health_percentage < 75:
                    print("⚠️  Empire health below 75% - consider restarting services")
        
        except KeyboardInterrupt:
            print("\n🛑 Stopping health monitor...")
    
    def shutdown_handler(self, signum, frame):
        """Handle graceful shutdown."""
        print("\n🛑 Shutting down Business Empire...")
        self.shutdown_all_services()
        sys.exit(0)
    
    def shutdown_all_services(self):
        """Shutdown all running services."""
        print("📤 Stopping all services...")
        
        for service_key, service in self.services.items():
            if service['process'] and service['status'] == 'running':
                print(f"   🛑 Stopping {service['name']}...")
                try:
                    service['process'].terminate()
                    service['process'].wait(timeout=5)
                    service['status'] = 'stopped'
                    print(f"   ✅ {service['name']} stopped")
                except:
                    service['process'].kill()
                    print(f"   🔥 {service['name']} force killed")
        
        print("✅ All services stopped")
        print("👋 Business Empire shutdown complete")
    
# DEMO CODE REMOVED: def run_empire_demo(self):
# DEMO CODE REMOVED: """Run a quick empire demonstration."""
# DEMO CODE REMOVED: print("🎬 BUSINESS EMPIRE DEMO MODE")
        print("-" * 40)
        
        # Show what would be launched
        print("📋 Services that would be launched:")
        for service_key, service in self.services.items():
            print(f"   🚀 {service['name']} (Port {service['port']})")
            print(f"      💰 ${service['revenue_target']:,}/month target")
        
        print(f"\n💰 Total Revenue Target: ${self.total_revenue_target:,}/month")
        print("🤖 AI automation would optimize across all ventures")
        print("📊 Cross-business analytics would identify growth opportunities")
        print("\n✨ Ready to launch full empire!")

def main():
    """Main launcher function."""
    launcher = BusinessEmpireLauncher()
    launcher.print_empire_header()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
# DEMO CODE REMOVED: if command == 'demo':
# DEMO CODE REMOVED: launcher.run_empire_demo()
        elif command == 'monitor':
            launcher.launch_all_services()
            launcher.monitor_empire()
        elif command == 'start':
            launcher.launch_all_services()
            print("🎯 Empire launched! Services running in background.")
            print("💡 Use 'python3 launch_business_empire.py monitor' to watch health")
        else:
            print(f"❌ Unknown command: {command}")
            print("📖 Usage:")
# DEMO CODE REMOVED: print("   python3 launch_business_empire.py demo     # Show what would launch")
            print("   python3 launch_business_empire.py start    # Launch all services")
            print("   python3 launch_business_empire.py monitor  # Launch + monitor")
    else:
        # Default: Launch and monitor
        launcher.launch_all_services()
        launcher.monitor_empire()

if __name__ == "__main__":
    main()