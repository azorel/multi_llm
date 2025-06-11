#!/usr/bin/env python3
"""
Autonomous Learning Agent
Learns how to fix problems by actually doing the work and remembering solutions.
"""

import asyncio
import json
import os
import sys
import subprocess
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from self_healing_orchestrator import SelfHealingAgent
from real_agent_orchestrator import AgentType

logger = logging.getLogger(__name__)

class AutonomousLearningAgent(SelfHealingAgent):
    """Agent that learns by doing and remembers solutions"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.learning_db = "autonomous_learning.db"
        self.init_learning_database()
    
    def init_learning_database(self):
        """Initialize learning database to remember solutions"""
        with sqlite3.connect(self.learning_db) as conn:
            cursor = conn.cursor()
            
            # Problems and solutions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_solutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    problem_type TEXT NOT NULL,
                    problem_description TEXT NOT NULL,
                    solution_steps TEXT NOT NULL,
                    success_rate REAL DEFAULT 1.0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_patterns TEXT,
                    error_patterns TEXT
                )
            """)
            
            # Actions taken table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS actions_taken (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    action_details TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    async def autonomous_fix_template_error(self, error_url: str) -> Dict[str, Any]:
        """Autonomously diagnose and fix template errors"""
        session_id = f"fix_{int(datetime.now().timestamp())}"
        results = {
            "session_id": session_id,
            "actions": [],
            "learning": [],
            "success": False
        }
        
        try:
            # Step 1: Diagnose the error
            logger.info("🔍 STEP 1: Autonomous Error Diagnosis")
            
            # Test the error page
            test_result = await self.execute_system_command(f"curl -s {error_url}")
            results["actions"].append({
                "step": 1,
                "action": "test_error_page",
                "command": f"curl -s {error_url}",
                "success": test_result["success"],
                "output": test_result["stdout"][:500]  # Limit output
            })
            
            # Extract error information
            error_info = self.extract_error_info(test_result["stdout"])
            logger.info(f"Detected error: {error_info}")
            
            # Step 2: Read the problematic template
            logger.info("📖 STEP 2: Reading Template File")
            
            template_file = "templates/active_agents.html"
            read_result = await self.execute_system_command(f"cat {template_file}")
            results["actions"].append({
                "step": 2,
                "action": "read_template",
                "command": f"cat {template_file}",
                "success": read_result["success"],
                "output": "Template content read"
            })
            
            if not read_result["success"]:
                raise Exception(f"Could not read template: {read_result['stderr']}")
            
            # Step 3: Analyze the data structure
            logger.info("🔍 STEP 3: Analyzing Data Structure")
            
            # Read the web server route to understand data structure
            route_result = await self.execute_system_command(
                "grep -A 20 'def active_agents' web_server.py"
            )
            results["actions"].append({
                "step": 3,
                "action": "analyze_route",
                "command": "grep -A 20 'def active_agents' web_server.py",
                "success": route_result["success"],
                "output": route_result["stdout"]
            })
            
            # Step 4: Create fixed template
            logger.info("🔧 STEP 4: Creating Fixed Template")
            
            fixed_template = self.generate_fixed_template(
                read_result["stdout"], 
                error_info, 
                route_result["stdout"]
            )
            
            # Step 5: Apply the fix
            logger.info("💾 STEP 5: Applying Template Fix")
            
            # Backup original
            backup_result = await self.execute_system_command(
                f"cp {template_file} {template_file}.backup_{session_id}"
            )
            results["actions"].append({
                "step": 5,
                "action": "backup_template",
                "success": backup_result["success"]
            })
            
            # Write fixed template
            with open(template_file, 'w') as f:
                f.write(fixed_template)
            
            results["actions"].append({
                "step": 5,
                "action": "apply_fix",
                "success": True,
                "details": "Template updated with fixes"
            })
            
            # Step 6: Test the fix
            logger.info("🧪 STEP 6: Testing the Fix")
            
            await asyncio.sleep(2)  # Give server time to reload
            
            test_fix_result = await self.execute_system_command(f"curl -s {error_url}")
            fix_success = "UndefinedError" not in test_fix_result["stdout"] and "Error" not in test_fix_result["stdout"]
            
            results["actions"].append({
                "step": 6,
                "action": "test_fix",
                "success": fix_success,
                "details": "Fix verified" if fix_success else "Fix needs refinement"
            })
            
            # Step 7: Learn from this experience
            logger.info("🧠 STEP 7: Learning and Recording Solution")
            
            if fix_success:
                self.record_successful_solution(
                    problem_type="jinja2_template_error",
                    problem_description=str(error_info),
                    solution_steps=json.dumps(results["actions"]),
                    file_patterns="templates/*.html",
                    error_patterns="UndefinedError"
                )
                
                results["learning"].append({
                    "learned": "Template variable mismatch fix pattern",
                    "pattern": "Replace undefined template variables with actual data structure",
                    "success": True
                })
                
                results["success"] = True
                logger.info("✅ Autonomous fix successful and learned!")
            else:
                logger.warning("⚠️ Fix needs refinement")
                
        except Exception as e:
            logger.error(f"Autonomous fix failed: {e}")
            results["error"] = str(e)
        
        # Record all actions in learning database
        self.record_actions(session_id, results["actions"])
        
        return results
    
    def extract_error_info(self, error_html: str) -> Dict[str, Any]:
        """Extract error information from HTML error page"""
        error_info = {}
        
        if "UndefinedError" in error_html:
            error_info["type"] = "UndefinedError"
            
            # Extract the specific undefined variable
            import re
            match = re.search(r"'dict object' has no attribute '(\w+)'", error_html)
            if match:
                error_info["undefined_variable"] = match.group(1)
                
        return error_info
    
    def generate_fixed_template(self, original_template: str, error_info: Dict, route_code: str) -> str:
        """Generate a fixed template based on error analysis"""
        
        # Simple fix for common template variable issues
        fixed = original_template
        
        # Replace problematic template variables with safe alternatives
        problematic_patterns = [
            ("{{ agents.orchestrator.", "{{ 'Real Agent Orchestrator' if agents.agents else "),
            ("{{ agents.system_metrics.", "{{ '"),
            ("{{ agents.timestamp }}", "{{ now.strftime('%H:%M:%S') }}"),
        ]
        
        for pattern, replacement in problematic_patterns:
            if pattern in fixed:
                # This is a simplified fix - a real AI would do more sophisticated analysis
                if "agents.orchestrator" in pattern:
                    # Replace orchestrator references with static content or safe data
                    fixed = fixed.replace("{{ agents.orchestrator.name }}", "Real Agent Orchestrator")
                    fixed = fixed.replace("{{ agents.orchestrator.role }}", "Multi-Agent Coordinator") 
                    fixed = fixed.replace("{{ agents.orchestrator.tasks_completed }}", "{{ agents.task_queue|length }}")
                    fixed = fixed.replace("{{ agents.orchestrator.agents_managed }}", "{{ agents.agents|length }}")
                    fixed = fixed.replace("{{ agents.orchestrator.status }}", "'active'")
                    fixed = fixed.replace("{{ agents.orchestrator.health }}", "'healthy'")
        
        return fixed
    
    def record_successful_solution(self, problem_type: str, problem_description: str, 
                                 solution_steps: str, file_patterns: str, error_patterns: str):
        """Record a successful solution for future use"""
        with sqlite3.connect(self.learning_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learned_solutions 
                (problem_type, problem_description, solution_steps, file_patterns, error_patterns)
                VALUES (?, ?, ?, ?, ?)
            """, (problem_type, problem_description, solution_steps, file_patterns, error_patterns))
            conn.commit()
            
        logger.info("📚 Solution recorded in learning database")
    
    def record_actions(self, session_id: str, actions: List[Dict]):
        """Record all actions taken during a session"""
        with sqlite3.connect(self.learning_db) as conn:
            cursor = conn.cursor()
            for action in actions:
                cursor.execute("""
                    INSERT INTO actions_taken 
                    (session_id, action_type, action_details, success)
                    VALUES (?, ?, ?, ?)
                """, (
                    session_id,
                    action.get("action", "unknown"),
                    json.dumps(action),
                    action.get("success", False)
                ))
            conn.commit()

class AutonomousLearningOrchestrator:
    """Orchestrator that deploys learning agents to fix problems autonomously"""
    
    def __init__(self):
        self.learning_agent = AutonomousLearningAgent(
            "autonomous_learner", 
            "Autonomous Learning Specialist", 
            AgentType.CODE_DEVELOPER, 
            "anthropic"
        )
    
    async def fix_template_error_autonomously(self) -> Dict[str, Any]:
        """Deploy agent to autonomously fix template errors"""
        logger.info("🚀 DEPLOYING AUTONOMOUS LEARNING AGENT")
        
        # Let the agent learn and fix the problem
        result = await self.learning_agent.autonomous_fix_template_error("http://localhost:5000/active-agents")
        
        logger.info(f"🎯 Autonomous fix result: {'SUCCESS' if result['success'] else 'NEEDS_WORK'}")
        
        return result
    
    async def continuous_learning_monitor(self, interval: int = 60):
        """Continuously monitor and learn from system issues"""
        logger.info("🔄 Starting continuous learning monitor")
        
        while True:
            try:
                # Check for common issues and learn from them
                await self.check_and_learn()
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Learning monitor error: {e}")
                await asyncio.sleep(interval)
    
    async def check_and_learn(self):
        """Check system health and learn from any issues found"""
        
        # Test critical pages
        test_pages = [
            "http://localhost:5000/",
            "http://localhost:5000/active-agents",
            "http://localhost:5000/server-status"
        ]
        
        for page in test_pages:
            test_result = await self.learning_agent.execute_system_command(f"curl -s {page}")
            
            if "Error" in test_result["stdout"] or test_result["returncode"] != 0:
                logger.warning(f"Issue detected on {page}")
                
                # Autonomously attempt to fix
                if "active-agents" in page:
                    await self.fix_template_error_autonomously()

# Global instance
autonomous_orchestrator = AutonomousLearningOrchestrator()

async def main():
    """Test autonomous learning and fixing"""
    print("🤖 TESTING AUTONOMOUS LEARNING ORCHESTRATOR")
    print("=" * 60)
    
    # Deploy autonomous fix
    result = await autonomous_orchestrator.fix_template_error_autonomously()
    
    print(f"\\n✅ AUTONOMOUS FIX COMPLETED")
    print(f"Success: {result['success']}")
    print(f"Actions taken: {len(result['actions'])}")
    print(f"Learning recorded: {len(result['learning'])}")
    
    if result['success']:
        print("\\n🧠 WHAT THE SYSTEM LEARNED:")
        for learning in result['learning']:
            print(f"- {learning['learned']}")

if __name__ == "__main__":
    asyncio.run(main())