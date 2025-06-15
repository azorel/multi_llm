#!/usr/bin/env python3
"""
Agent Accountability System
Forces agents to execute actual fixes and verify results before claiming success
"""

import asyncio
import subprocess
import requests
import os
from typing import Dict, List, Any
from enhanced_orchestrator_claude_gemini import enhanced_orchestrator, AgentType, TaskPriority

class AgentAccountabilitySystem:
    """System that forces agents to prove their work through verification"""
    
    def __init__(self):
        self.verification_tests = {
            'social_media_route': self._verify_social_media_route,
            'tdd_system': self._verify_tdd_system,
            'upload_system': self._verify_upload_system,
            'database_setup': self._verify_database_setup
        }
    
    async def execute_with_verification(self, task_name: str, task_description: str, 
                                      agent_type: AgentType, verification_type: str) -> Dict[str, Any]:
        """Execute task and force verification before accepting success"""
        
        print(f"🎯 EXECUTING: {task_name}")
        print(f"📋 VERIFICATION: {verification_type}")
        
        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"🔄 Attempt {attempt + 1}/{max_attempts}")
            
            # Add task to orchestrator
            task_id = enhanced_orchestrator.add_task(
                task_name,
                f"{task_description}\n\nCRITICAL: You must execute actual code changes, not just provide solutions.",
                agent_type,
                TaskPriority.HIGH
            )
            
            # Execute task
            task = enhanced_orchestrator.task_queue[-1]
            agents = list(enhanced_orchestrator.agents.values())
            agent = next(a for a in agents if a.agent_type == agent_type)
            
            result = await agent.execute_task(task)
            
            # Force verification
            verification_result = await self._run_verification(verification_type)
            
            if verification_result['success']:
                print(f"✅ SUCCESS: {task_name} verified working")
                return {
                    'success': True,
                    'agent_result': result,
                    'verification': verification_result,
                    'attempts': attempt + 1
                }
            else:
                print(f"❌ FAILED: {verification_result['error']}")
                if attempt < max_attempts - 1:
                    print("🔄 Retrying with more specific instructions...")
                    task_description += f"\n\nPREVIOUS ATTEMPT FAILED: {verification_result['error']}\nFIX THIS SPECIFIC ISSUE."
        
        return {
            'success': False,
            'error': f"Failed after {max_attempts} attempts",
            'last_verification': verification_result
        }
    
    async def _run_verification(self, verification_type: str) -> Dict[str, Any]:
        """Run specific verification test"""
        if verification_type not in self.verification_tests:
            return {'success': False, 'error': f'Unknown verification type: {verification_type}'}
        
        try:
            return await self.verification_tests[verification_type]()
        except Exception as e:
            return {'success': False, 'error': f'Verification error: {str(e)}'}
    
    async def _verify_social_media_route(self) -> Dict[str, Any]:
        """Verify social media route returns HTML instead of redirect"""
        try:
            response = requests.get('http://localhost:8081/social-media', timeout=5, allow_redirects=False)
            
            if response.status_code == 302:
                return {'success': False, 'error': 'Route still redirects instead of showing content'}
            
            if response.status_code == 200 and 'html' in response.text.lower():
                return {'success': True, 'message': 'Route returns HTML content successfully'}
            
            return {'success': False, 'error': f'Route returned status {response.status_code}'}
            
        except requests.RequestException as e:
            return {'success': False, 'error': f'Request failed: {str(e)}'}
    
    async def _verify_tdd_system(self) -> Dict[str, Any]:
        """Verify TDD system can complete a cycle successfully"""
        try:
            result = subprocess.run([
                'python3', '-c', 
                '''
from tdd_system import tdd_system
import asyncio
async def test():
    cycle_id = tdd_system.create_tdd_cycle("Test", "Simple test")
    result = await tdd_system.complete_tdd_cycle(cycle_id, "Create a simple function that returns True")
    print(f"SUCCESS: {result.get('success', False)}")
asyncio.run(test())
                '''
            ], capture_output=True, text=True, timeout=60)
            
            if 'SUCCESS: True' in result.stdout:
                return {'success': True, 'message': 'TDD system completed cycle successfully'}
            else:
                return {'success': False, 'error': f'TDD failed: {result.stderr or result.stdout}'}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'TDD system timed out'}
        except Exception as e:
            return {'success': False, 'error': f'TDD verification error: {str(e)}'}
    
    async def _verify_upload_system(self) -> Dict[str, Any]:
        """Verify upload system can process a test file"""
        try:
            # Check if upload endpoint exists and responds
            response = requests.get('http://localhost:8081/social-media/upload', timeout=5)
            
            if response.status_code == 200:
                return {'success': True, 'message': 'Upload system accessible'}
            else:
                return {'success': False, 'error': f'Upload system returned status {response.status_code}'}
                
        except requests.RequestException as e:
            return {'success': False, 'error': f'Upload system not accessible: {str(e)}'}
    
    async def _verify_database_setup(self) -> Dict[str, Any]:
        """Verify database has required social media tables"""
        try:
            result = subprocess.run([
                'python3', '-c',
                '''
import sqlite3
conn = sqlite3.connect("lifeos_local.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%social_media%'")
tables = cursor.fetchall()
conn.close()
print(f"TABLES: {len(tables)}")
                '''
            ], capture_output=True, text=True, timeout=10)
            
            if 'TABLES:' in result.stdout and not result.stdout.strip().endswith('0'):
                return {'success': True, 'message': 'Social media database tables exist'}
            else:
                return {'success': False, 'error': 'No social media tables found in database'}
                
        except Exception as e:
            return {'success': False, 'error': f'Database verification error: {str(e)}'}

    async def fix_vanlife_system(self) -> Dict[str, Any]:
        """Execute complete vanlife system fixes with verification"""
        print("🚀 VANLIFE SYSTEM REPAIR WITH ACCOUNTABILITY")
        print("=" * 60)
        
        fixes = [
            {
                'name': 'Fix Social Media Route',
                'description': '''
                The /social-media route redirects to / instead of showing content.
                You must:
                1. Read routes/social_media.py
                2. Find the dashboard() function that has return redirect('/')
                3. Change it to return render_template('social_media_dashboard.html') or call social_dashboard()
                4. Ensure the template exists and renders
                5. The route must return HTML content, not a redirect
                ''',
                'agent_type': AgentType.WEB_TESTER,
                'verification': 'social_media_route'
            },
            {
                'name': 'Fix TDD System Async Issues',
                'description': '''
                TDD system fails with async/await errors in complete_tdd_cycle.
                You must:
                1. Fix all async/await issues in tdd_system.py
                2. Ensure complete_tdd_cycle runs without "Unknown error"
                3. Make it complete full Red-Green-Refactor cycle
                4. Test must actually pass and return success=True
                ''',
                'agent_type': AgentType.TEMPLATE_FIXER,
                'verification': 'tdd_system'
            },
            {
                'name': 'Build Working Upload System',
                'description': '''
                Create functional vanlife/RC content upload system.
                You must:
                1. Ensure /social-media/upload route works and returns HTML
                2. Create working upload form for photos/videos
                3. Add basic file processing for vanlife/RC content
                4. Make upload endpoint accessible without errors
                ''',
                'agent_type': AgentType.CONTENT_PROCESSOR,
                'verification': 'upload_system'
            },
            {
                'name': 'Setup Social Media Database',
                'description': '''
                Ensure social media database tables exist and work.
                You must:
                1. Create/verify social_media_posts table
                2. Create trail_locations and rc_brands tables
                3. Ensure database can be queried without errors
                4. Tables must actually exist in lifeos_local.db
                ''',
                'agent_type': AgentType.DATABASE_SPECIALIST,
                'verification': 'database_setup'
            }
        ]
        
        results = []
        for fix in fixes:
            result = await self.execute_with_verification(
                fix['name'],
                fix['description'],
                fix['agent_type'],
                fix['verification']
            )
            results.append(result)
            
            if not result['success']:
                print(f"🚨 CRITICAL FAILURE: {fix['name']}")
                break
        
        success_count = sum(1 for r in results if r['success'])
        
        print(f"\n🎯 FINAL ACCOUNTABILITY REPORT:")
        print(f"✅ Successful fixes: {success_count}/{len(results)}")
        
        if success_count == len(results):
            print("🎉 ALL SYSTEMS OPERATIONAL - VANLIFE AUTOMATION READY")
            return {'success': True, 'fixes': results}
        else:
            print("❌ SYSTEM FAILED ACCOUNTABILITY VERIFICATION")
            return {'success': False, 'fixes': results}

# Initialize system
accountability_system = AgentAccountabilitySystem()

if __name__ == "__main__":
    result = asyncio.run(accountability_system.fix_vanlife_system())
    if result['success']:
        print("\n🚀 Ready for vanlife income generation!")
    else:
        print("\n⚠️ System requires manual intervention")