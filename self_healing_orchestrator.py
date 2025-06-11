#!/usr/bin/env python3
"""
Self-Healing Orchestrator
Extends the real orchestrator with actual system execution capabilities.
Can diagnose, fix, and heal system issues automatically.
"""

import asyncio
import subprocess
import psutil
import requests
import sqlite3
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from real_agent_orchestrator import real_orchestrator, AgentType, TaskPriority, RealAgent

logger = logging.getLogger(__name__)

class SelfHealingAgent(RealAgent):
    """Enhanced agent that can execute real system commands"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.healing_actions = []
        self.diagnostics = {}
    
    async def execute_system_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute real system commands"""
        try:
            logger.info(f"Agent {self.name} executing: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd()
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": command
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def diagnose_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health diagnosis"""
        diagnostics = {}
        
        # Check system resources
        diagnostics["cpu_percent"] = psutil.cpu_percent(interval=1)
        diagnostics["memory_percent"] = psutil.virtual_memory().percent
        diagnostics["disk_percent"] = psutil.disk_usage('/').percent
        
        # Check web server status
        try:
            response = requests.get("http://localhost:5000", timeout=5)
            diagnostics["web_server"] = {
                "status": "running",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            diagnostics["web_server"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check running processes
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] == 'python' or proc.info['name'] == 'python3':
                python_processes.append({
                    'pid': proc.info['pid'],
                    'cmdline': ' '.join(proc.info['cmdline'] or [])
                })
        diagnostics["python_processes"] = python_processes
        
        # Check port usage
        port_check = await self.execute_system_command("netstat -tulpn | grep :5000")
        diagnostics["port_5000"] = port_check
        
        # Check database
        try:
            conn = sqlite3.connect("lifeos_local.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            conn.close()
            diagnostics["database"] = {
                "status": "healthy",
                "table_count": table_count
            }
        except Exception as e:
            diagnostics["database"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check log files
        log_files = ["logs/main_agent.log", "logs/web_server.log", "real_orchestrator.log"]
        diagnostics["logs"] = {}
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        recent_errors = [line for line in lines[-50:] if 'ERROR' in line or 'Exception' in line]
                        diagnostics["logs"][log_file] = {
                            "exists": True,
                            "line_count": len(lines),
                            "recent_errors": recent_errors[-5:]  # Last 5 errors
                        }
                except Exception as e:
                    diagnostics["logs"][log_file] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                diagnostics["logs"][log_file] = {"exists": False}
        
        self.diagnostics = diagnostics
        return diagnostics
    
    async def heal_system_issues(self) -> List[Dict[str, Any]]:
        """Automatically heal detected system issues"""
        healing_actions = []
        
        # Diagnose first
        diagnostics = await self.diagnose_system_health()
        
        # Heal web server issues
        if diagnostics["web_server"]["status"] == "error":
            logger.warning("Web server is down, attempting to restart...")
            
            # Kill existing processes
            kill_result = await self.execute_system_command("pkill -f 'python.*web_server.py'")
            healing_actions.append({
                "action": "kill_web_server_processes",
                "result": kill_result
            })
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Start web server
            start_result = await self.execute_system_command(
                "source venv/bin/activate && python web_server.py > /dev/null 2>&1 &"
            )
            healing_actions.append({
                "action": "restart_web_server",
                "result": start_result
            })
            
            # Verify it's working
            await asyncio.sleep(3)
            try:
                response = requests.get("http://localhost:5000", timeout=5)
                healing_actions.append({
                    "action": "verify_web_server",
                    "result": {
                        "success": True,
                        "status_code": response.status_code
                    }
                })
            except Exception as e:
                healing_actions.append({
                    "action": "verify_web_server",
                    "result": {
                        "success": False,
                        "error": str(e)
                    }
                })
        
        # Heal database issues
        if diagnostics["database"]["status"] == "error":
            logger.warning("Database issues detected, attempting to repair...")
            
            # Backup database
            backup_result = await self.execute_system_command(
                f"cp lifeos_local.db lifeos_local.db.backup_{int(time.time())}"
            )
            healing_actions.append({
                "action": "backup_database",
                "result": backup_result
            })
            
            # Try to repair
            repair_result = await self.execute_system_command(
                "echo '.dump' | sqlite3 lifeos_local.db | sqlite3 lifeos_local_repaired.db"
            )
            if repair_result["success"]:
                move_result = await self.execute_system_command(
                    "mv lifeos_local_repaired.db lifeos_local.db"
                )
                healing_actions.append({
                    "action": "repair_database",
                    "result": move_result
                })
        
        # Heal high resource usage
        if diagnostics["cpu_percent"] > 90:
            logger.warning("High CPU usage detected")
            # Could implement CPU throttling or process management here
            
        if diagnostics["memory_percent"] > 90:
            logger.warning("High memory usage detected")
            # Could implement memory cleanup here
        
        self.healing_actions = healing_actions
        return healing_actions

class SelfHealingOrchestrator:
    """Orchestrator with self-healing capabilities"""
    
    def __init__(self):
        self.healing_agent = SelfHealingAgent(
            "self_healer_01", 
            "Self-Healing Specialist", 
            AgentType.ERROR_DIAGNOSTICIAN, 
            "anthropic"
        )
        self.monitoring_active = False
        self.healing_history = []
    
    async def start_monitoring(self, interval: int = 30):
        """Start continuous system monitoring"""
        logger.info("🔄 Starting self-healing system monitoring")
        self.monitoring_active = True
        
        while self.monitoring_active:
            try:
                # Diagnose system health
                diagnostics = await self.healing_agent.diagnose_system_health()
                
                # Check for issues
                issues_found = []
                
                if diagnostics["web_server"]["status"] == "error":
                    issues_found.append("web_server_down")
                
                if diagnostics["database"]["status"] == "error":
                    issues_found.append("database_error")
                
                if diagnostics["cpu_percent"] > 90:
                    issues_found.append("high_cpu")
                
                if diagnostics["memory_percent"] > 90:
                    issues_found.append("high_memory")
                
                # If issues found, trigger healing
                if issues_found:
                    logger.warning(f"🚨 Issues detected: {issues_found}")
                    healing_actions = await self.healing_agent.heal_system_issues()
                    
                    self.healing_history.append({
                        "timestamp": datetime.now(timezone.utc),
                        "issues": issues_found,
                        "actions": healing_actions,
                        "diagnostics": diagnostics
                    })
                    
                    logger.info("✅ Self-healing actions completed")
                
                else:
                    logger.info("✅ System health check passed")
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        logger.info("🛑 Self-healing monitoring stopped")
    
    async def emergency_heal(self) -> Dict[str, Any]:
        """Emergency healing for immediate issues"""
        logger.info("🚨 EMERGENCY HEALING ACTIVATED")
        
        diagnostics = await self.healing_agent.diagnose_system_health()
        healing_actions = await self.healing_agent.heal_system_issues()
        
        result = {
            "timestamp": datetime.now(timezone.utc),
            "diagnostics": diagnostics,
            "healing_actions": healing_actions,
            "status": "completed"
        }
        
        self.healing_history.append(result)
        return result

# Global self-healing orchestrator instance
self_healing_orchestrator = SelfHealingOrchestrator()

async def main():
    """Test the self-healing system"""
    print("🚨 TESTING SELF-HEALING ORCHESTRATOR")
    print("=" * 50)
    
    # Perform emergency healing
    result = await self_healing_orchestrator.emergency_heal()
    
    print("EMERGENCY HEALING RESULTS:")
    print(f"Status: {result['status']}")
    print(f"Issues found: {len(result['healing_actions'])} actions taken")
    
    # Show diagnostics
    print("\nSYSTEM DIAGNOSTICS:")
    diagnostics = result['diagnostics']
    print(f"CPU: {diagnostics['cpu_percent']}%")
    print(f"Memory: {diagnostics['memory_percent']}%") 
    print(f"Web Server: {diagnostics['web_server']['status']}")
    print(f"Database: {diagnostics['database']['status']}")
    
    # Show healing actions
    if result['healing_actions']:
        print("\nHEALING ACTIONS TAKEN:")
        for action in result['healing_actions']:
            print(f"- {action['action']}: {'✅' if action['result'].get('success') else '❌'}")

if __name__ == "__main__":
    asyncio.run(main())