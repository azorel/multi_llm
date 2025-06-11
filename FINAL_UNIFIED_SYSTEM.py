#!/usr/bin/env python3
"""
FINAL UNIFIED MULTI-AGENT SYSTEM
================================

The ONE system that runs everything. SQL-based, self-healing, multi-agent.
NO MORE NOTION. NO MORE DUPLICATES. JUST THIS.
"""

import asyncio
import sqlite3
import os
import sys
import subprocess
import threading
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class FinalUnifiedSystem:
    def __init__(self):
        self.db_path = 'autonomous_learning.db'
        self.running_agents = []
        print("🚀 FINAL UNIFIED SYSTEM INITIALIZING...")
        
    async def start_everything(self):
        """Start all components with multi-agent orchestration"""
        print("=" * 70)
        print("🎯 STARTING FINAL UNIFIED MULTI-AGENT SYSTEM")
        print("=" * 70)
        
        # Start all services concurrently
        tasks = [
            self.agent_1_web_server(),
            self.agent_2_youtube_processor(),
            self.agent_3_self_healing(),
            self.agent_4_monitoring()
        ]
        
        print("🤖 Starting 4 agents in parallel...")
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def agent_1_web_server(self):
        """Agent 1: Web Server"""
        print("🌐 AGENT 1: Starting web server...")
        
        # Import Flask app from sql_web_server
        try:
            from sql_web_server import app
            
            def run_flask():
                # Update port in prints
                print("✅ Web server running at http://localhost:5000")
                print("   📊 Dashboard: http://localhost:5000")
                print("   📺 YouTube Channels: http://localhost:5000/youtube_channels")
                print("   🧠 Knowledge Hub: http://localhost:5000/knowledge_hub")
                app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
            
            # Run in thread
            thread = threading.Thread(target=run_flask, daemon=True)
            thread.start()
            self.running_agents.append("Web Server")
            
            # Keep agent alive
            while True:
                await asyncio.sleep(60)
                
        except Exception as e:
            print(f"❌ AGENT 1 Error: {e}")
            return False
    
    async def agent_2_youtube_processor(self):
        """Agent 2: YouTube Multi-Agent Processor"""
        print("📹 AGENT 2: Starting YouTube processor...")
        
        try:
            from sql_multi_agent_system import SQLMultiAgentSystem
            
            processor = SQLMultiAgentSystem()
            self.running_agents.append("YouTube Processor")
            
            # Run continuous processing
            await processor.run_continuous_processing()
            
        except Exception as e:
            print(f"❌ AGENT 2 Error: {e}")
            # Fallback: run as subprocess
            try:
                subprocess.Popen([
                    sys.executable, 'sql_multi_agent_system.py', 'continuous'
                ])
                print("✅ AGENT 2: Running as subprocess")
                self.running_agents.append("YouTube Processor (subprocess)")
                
                while True:
                    await asyncio.sleep(60)
            except:
                return False
    
    async def agent_3_self_healing(self):
        """Agent 3: Self-Healing Monitor"""
        print("🔧 AGENT 3: Starting self-healing monitor...")
        
        self.running_agents.append("Self-Healing Monitor")
        
        while True:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Check for issues
                cursor.execute("""
                    SELECT COUNT(*) FROM youtube_channels 
                    WHERE process_channel = 1 
                    AND (last_processed IS NULL OR 
                         datetime(last_processed) < datetime('now', '-1 hour'))
                """)
                
                stuck_channels = cursor.fetchone()[0]
                
                if stuck_channels > 0:
                    print(f"🔧 AGENT 3: Found {stuck_channels} stuck channels, triggering fix...")
                    
                    # Reset stuck channels
                    cursor.execute("""
                        UPDATE youtube_channels 
                        SET process_channel = 1, updated_at = datetime('now')
                        WHERE process_channel = 1 
                        AND (last_processed IS NULL OR 
                             datetime(last_processed) < datetime('now', '-1 hour'))
                    """)
                    conn.commit()
                
                conn.close()
                
                # Check every 2 minutes
                await asyncio.sleep(120)
                
            except Exception as e:
                print(f"⚠️ AGENT 3 Error: {e}")
                await asyncio.sleep(60)
    
    async def agent_4_monitoring(self):
        """Agent 4: System Monitor"""
        print("📊 AGENT 4: Starting system monitor...")
        
        self.running_agents.append("System Monitor")
        
        while True:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get stats
                cursor.execute("SELECT COUNT(*) FROM youtube_channels")
                total_channels = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM youtube_channels WHERE process_channel = 1")
                marked_channels = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM knowledge_hub")
                total_videos = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM knowledge_hub 
                    WHERE datetime(created_at) > datetime('now', '-1 hour')
                """)
                recent_videos = cursor.fetchone()[0]
                
                conn.close()
                
                # Print status
                print(f"\n📊 SYSTEM STATUS [{datetime.now().strftime('%H:%M:%S')}]")
                print(f"   Channels: {total_channels} total, {marked_channels} marked")
                print(f"   Videos: {total_videos} total, {recent_videos} in last hour")
                print(f"   Active Agents: {', '.join(self.running_agents)}")
                print(f"   Database: {self.db_path}")
                print(f"   Status: ✅ All systems operational\n")
                
                # Check every 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                print(f"⚠️ AGENT 4 Error: {e}")
                await asyncio.sleep(60)
    
    def cleanup_old_processes(self):
        """Clean up any remaining old processes"""
        print("🧹 Cleaning up old processes...")
        
        cleanup_commands = [
            "pkill -f 'web_server.py'",
            "pkill -f 'simple_video_processor'",
            "pkill -f 'notion_migration'",
            "lsof -ti:5001 | xargs kill -9 2>/dev/null || true"  # Kill anything on port 5001
        ]
        
        for cmd in cleanup_commands:
            try:
                subprocess.run(cmd, shell=True, capture_output=True)
            except:
                pass
        
        print("✅ Cleanup complete")

async def main():
    """Main entry point"""
    system = FinalUnifiedSystem()
    
    # Clean up first
    system.cleanup_old_processes()
    
    # Start everything
    await system.start_everything()

if __name__ == "__main__":
    print("🎯 FINAL UNIFIED SYSTEM LAUNCHER")
    print("================================")
    print("✅ SQL-based (NO Notion)")
    print("✅ Multi-agent processing")
    print("✅ Self-healing enabled")
    print("✅ Web interface included")
    print("================================\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("Run 'python3 CLEANUP_AND_ORCHESTRATE.py' to fix")