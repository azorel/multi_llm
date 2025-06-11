#!/usr/bin/env python3
"""
SQL-BASED SELF-HEALING & SELF-LEARNING SYSTEM
==============================================

Autonomous system that monitors, learns, and fixes issues using SQL database.
NO MORE NOTION - Pure SQL-based healing and learning.
"""

import asyncio
import sqlite3
import os
import json
from datetime import datetime, timedelta
import traceback
import subprocess
import sys

class SQLSelfHealingSystem:
    """SQL-based self-healing system with learning capabilities."""
    
    def __init__(self):
        self.db_path = 'autonomous_learning.db'
        self.healing_active = True
        self.learning_enabled = True
        
        # Initialize healing tables
        self.init_healing_tables()
        
        print("🔧 SQL Self-Healing System initialized")
    
    def init_healing_tables(self):
        """Initialize self-healing and learning tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Issues detected table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detected_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_type TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                system_component TEXT,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME,
                resolution_method TEXT,
                status TEXT DEFAULT 'open'
            )
        """)
        
        # Learning patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                trigger_condition TEXT NOT NULL,
                successful_action TEXT NOT NULL,
                confidence_score REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                last_used DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Healing actions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS healing_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER,
                action_type TEXT NOT NULL,
                action_description TEXT NOT NULL,
                success BOOLEAN,
                result_details TEXT,
                executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (issue_id) REFERENCES detected_issues (id)
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Self-healing tables initialized")
    
    async def monitor_system_health(self):
        """Continuously monitor system health and detect issues."""
        print("🔍 Starting continuous system health monitoring...")
        
        while self.healing_active:
            try:
                issues_found = []
                
                # Check 1: Stuck YouTube channels
                stuck_channels = await self.check_stuck_channels()
                if stuck_channels:
                    issues_found.extend(stuck_channels)
                
                # Check 2: Failed video processing
                failed_videos = await self.check_failed_processing()
                if failed_videos:
                    issues_found.extend(failed_videos)
                
                # Check 3: System processes
                process_issues = await self.check_system_processes()
                if process_issues:
                    issues_found.extend(process_issues)
                
                # Check 4: Database integrity
                db_issues = await self.check_database_integrity()
                if db_issues:
                    issues_found.extend(db_issues)
                
                # Log and handle issues
                for issue in issues_found:
                    await self.handle_detected_issue(issue)
                
                if issues_found:
                    print(f"🔧 Detected and handling {len(issues_found)} issues")
                else:
                    print("✅ System health check: All systems operational")
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"❌ Error in health monitoring: {e}")
                await asyncio.sleep(60)
    
    async def check_stuck_channels(self):
        """Check for YouTube channels stuck in processing."""
        issues = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find channels marked for processing but not processed recently
            cursor.execute("""
                SELECT id, name, url, last_processed 
                FROM youtube_channels 
                WHERE process_channel = 1 
                AND (last_processed IS NULL OR 
                     datetime(last_processed) < datetime('now', '-30 minutes'))
            """)
            
            stuck_channels = cursor.fetchall()
            
            for channel_id, name, url, last_processed in stuck_channels:
                issue = {
                    'type': 'stuck_channel',
                    'description': f"Channel '{name}' stuck in processing for >30 minutes",
                    'severity': 'high',
                    'component': 'youtube_processor',
                    'data': {
                        'channel_id': channel_id,
                        'channel_name': name,
                        'url': url,
                        'last_processed': last_processed
                    }
                }
                issues.append(issue)
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Error checking stuck channels: {e}")
        
        return issues
    
    async def check_failed_processing(self):
        """Check for videos with failed processing status."""
        issues = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find videos with failed processing
            cursor.execute("""
                SELECT COUNT(*) FROM knowledge_hub 
                WHERE processing_status = 'Failed'
            """)
            
            failed_count = cursor.fetchone()[0]
            
            if failed_count > 0:
                issue = {
                    'type': 'failed_videos',
                    'description': f"{failed_count} videos failed processing",
                    'severity': 'medium',
                    'component': 'video_processor',
                    'data': {'failed_count': failed_count}
                }
                issues.append(issue)
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Error checking failed processing: {e}")
        
        return issues
    
    async def check_system_processes(self):
        """Check if required system processes are running."""
        issues = []
        
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout
            
            required_processes = [
                ('FINAL_UNIFIED_SYSTEM', 'Main orchestrator'),
                ('sql_multi_agent_system', 'YouTube processor')
            ]
            
            for process_name, description in required_processes:
                if process_name not in processes:
                    issue = {
                        'type': 'missing_process',
                        'description': f"Required process '{description}' not running",
                        'severity': 'high',
                        'component': 'system_processes',
                        'data': {'process_name': process_name, 'description': description}
                    }
                    issues.append(issue)
            
        except Exception as e:
            print(f"⚠️ Error checking processes: {e}")
        
        return issues
    
    async def check_database_integrity(self):
        """Check database for integrity issues."""
        issues = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for corrupted data
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            if integrity_result != 'ok':
                issue = {
                    'type': 'database_corruption',
                    'description': f"Database integrity check failed: {integrity_result}",
                    'severity': 'critical',
                    'component': 'database',
                    'data': {'integrity_result': integrity_result}
                }
                issues.append(issue)
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Error checking database integrity: {e}")
        
        return issues
    
    async def handle_detected_issue(self, issue):
        """Handle a detected issue using learned patterns or new solutions."""
        print(f"🔧 Handling issue: {issue['description']}")
        
        try:
            # Log the issue
            issue_id = await self.log_issue(issue)
            
            # Check if we've learned how to handle this type of issue
            learned_solution = await self.get_learned_solution(issue['type'])
            
            if learned_solution:
                print(f"🧠 Using learned solution for {issue['type']}")
                success = await self.apply_learned_solution(issue, learned_solution, issue_id)
            else:
                print(f"🔍 Learning new solution for {issue['type']}")
                success = await self.discover_new_solution(issue, issue_id)
            
            # Update issue status
            await self.update_issue_status(issue_id, 'resolved' if success else 'failed')
            
        except Exception as e:
            print(f"❌ Error handling issue: {e}")
    
    async def log_issue(self, issue):
        """Log detected issue to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO detected_issues (issue_type, description, severity, system_component)
            VALUES (?, ?, ?, ?)
        """, (issue['type'], issue['description'], issue['severity'], issue['component']))
        
        issue_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return issue_id
    
    async def get_learned_solution(self, issue_type):
        """Get previously learned solution for this issue type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pattern_type, trigger_condition, successful_action, confidence_score
            FROM learning_patterns 
            WHERE pattern_type = ? 
            ORDER BY confidence_score DESC, usage_count DESC
            LIMIT 1
        """, (issue_type,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'pattern_type': result[0],
                'trigger_condition': result[1],
                'successful_action': result[2],
                'confidence_score': result[3]
            }
        
        return None
    
    async def apply_learned_solution(self, issue, solution, issue_id):
        """Apply a previously learned solution."""
        try:
            action_type = f"learned_{solution['pattern_type']}"
            
            if issue['type'] == 'stuck_channel':
                # Reset stuck channel
                success = await self.fix_stuck_channel(issue['data'])
                action_desc = f"Reset stuck channel using learned pattern"
                
            elif issue['type'] == 'missing_process':
                # Restart missing process
                success = await self.restart_missing_process(issue['data'])
                action_desc = f"Restarted missing process using learned pattern"
                
            else:
                success = False
                action_desc = f"No learned action available for {issue['type']}"
            
            # Log the action
            await self.log_healing_action(issue_id, action_type, action_desc, success)
            
            if success:
                # Update learning pattern usage
                await self.update_pattern_usage(solution['pattern_type'])
            
            return success
            
        except Exception as e:
            print(f"❌ Error applying learned solution: {e}")
            return False
    
    async def discover_new_solution(self, issue, issue_id):
        """Discover and learn new solution for unknown issue."""
        try:
            success = False
            action_desc = ""
            
            if issue['type'] == 'stuck_channel':
                success = await self.fix_stuck_channel(issue['data'])
                action_desc = "Reset stuck channel and clear processing flag"
                
                if success:
                    # Learn this solution
                    await self.learn_new_pattern(
                        'stuck_channel',
                        'process_channel=1 AND last_processed > 30min ago',
                        'reset_channel_processing_flag'
                    )
                
            elif issue['type'] == 'missing_process':
                success = await self.restart_missing_process(issue['data'])
                action_desc = "Restart required system process"
                
                if success:
                    await self.learn_new_pattern(
                        'missing_process',
                        'required_process_not_in_ps_output',
                        'restart_process_command'
                    )
            
            elif issue['type'] == 'failed_videos':
                success = await self.retry_failed_videos()
                action_desc = "Retry processing failed videos"
                
                if success:
                    await self.learn_new_pattern(
                        'failed_videos',
                        'processing_status=Failed',
                        'reset_status_and_reprocess'
                    )
            
            # Log the action
            await self.log_healing_action(issue_id, f"discovery_{issue['type']}", action_desc, success)
            
            return success
            
        except Exception as e:
            print(f"❌ Error discovering solution: {e}")
            return False
    
    async def fix_stuck_channel(self, channel_data):
        """Fix a stuck YouTube channel."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Reset the channel processing flag and update timestamp
            cursor.execute("""
                UPDATE youtube_channels 
                SET process_channel = 1, last_processed = NULL, updated_at = datetime('now')
                WHERE id = ?
            """, (channel_data['channel_id'],))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Fixed stuck channel: {channel_data['channel_name']}")
            return True
            
        except Exception as e:
            print(f"❌ Error fixing stuck channel: {e}")
            return False
    
    async def restart_missing_process(self, process_data):
        """Restart a missing system process."""
        try:
            process_name = process_data['process_name']
            
            if process_name == 'sql_multi_agent_system':
                # Start the YouTube processor
                subprocess.Popen([
                    sys.executable, 'sql_multi_agent_system.py', 'continuous'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                print(f"✅ Restarted YouTube processor")
                return True
                
            elif process_name == 'FINAL_UNIFIED_SYSTEM':
                # This would restart the main system (careful!)
                print(f"⚠️ Main system restart required - manual intervention needed")
                return False
            
        except Exception as e:
            print(f"❌ Error restarting process: {e}")
            return False
    
    async def retry_failed_videos(self):
        """Retry processing failed videos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Reset failed videos to pending
            cursor.execute("""
                UPDATE knowledge_hub 
                SET processing_status = 'Pending' 
                WHERE processing_status = 'Failed'
            """)
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            print(f"✅ Reset {rows_affected} failed videos for retry")
            return rows_affected > 0
            
        except Exception as e:
            print(f"❌ Error retrying failed videos: {e}")
            return False
    
    async def learn_new_pattern(self, pattern_type, trigger_condition, successful_action):
        """Learn a new solution pattern."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO learning_patterns (pattern_type, trigger_condition, successful_action, confidence_score)
            VALUES (?, ?, ?, ?)
        """, (pattern_type, trigger_condition, successful_action, 0.7))  # Start with 70% confidence
        
        conn.commit()
        conn.close()
        
        print(f"🧠 Learned new pattern: {pattern_type} -> {successful_action}")
    
    async def update_pattern_usage(self, pattern_type):
        """Update usage statistics for a learned pattern."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE learning_patterns 
            SET usage_count = usage_count + 1, 
                last_used = datetime('now'),
                confidence_score = MIN(confidence_score + 0.1, 1.0)
            WHERE pattern_type = ?
        """, (pattern_type,))
        
        conn.commit()
        conn.close()
    
    async def log_healing_action(self, issue_id, action_type, action_description, success):
        """Log a healing action taken."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO healing_actions (issue_id, action_type, action_description, success)
            VALUES (?, ?, ?, ?)
        """, (issue_id, action_type, action_description, success))
        
        conn.commit()
        conn.close()
    
    async def update_issue_status(self, issue_id, status):
        """Update issue resolution status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE detected_issues 
            SET status = ?, resolved_at = datetime('now')
            WHERE id = ?
        """, (status, issue_id))
        
        conn.commit()
        conn.close()
    
    async def run_healing_loop(self):
        """Main healing loop."""
        print("🚀 Starting SQL-based self-healing system")
        print("=" * 60)
        
        # Start continuous monitoring
        await self.monitor_system_health()

if __name__ == "__main__":
    healing_system = SQLSelfHealingSystem()
    asyncio.run(healing_system.run_healing_loop())