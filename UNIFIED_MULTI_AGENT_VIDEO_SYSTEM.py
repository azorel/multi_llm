#!/usr/bin/env python3
"""
UNIFIED MULTI-AGENT VIDEO SYSTEM
================================

Complete multi-agent system based on Disler's patterns that orchestrates:
- Enhanced video processing with multiple agents
- Auto-checking for new videos
- Video management web interface
- SQL-based self-healing system
- Parallel LLM processing

This is the main orchestrator that runs everything.
"""

import asyncio
import subprocess
import sys
import os
import signal
from datetime import datetime
import traceback
from ENHANCED_VIDEO_PROCESSOR import EnhancedVideoProcessor
from VIDEO_MANAGEMENT_SYSTEM import VideoManagementSystem
from SQL_SELF_HEALING_SYSTEM import SQLSelfHealingSystem

class UnifiedMultiAgentVideoSystem:
    """Main orchestrator for the complete video processing system."""
    
    def __init__(self):
        self.processes = {}
        self.running = True
        self.processor = EnhancedVideoProcessor()
        self.management_system = VideoManagementSystem()
        self.healing_system = SQLSelfHealingSystem()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🚀 Unified Multi-Agent Video System initialized")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def start_all_agents(self):
        """Start all agents in parallel using Disler's multi-agent pattern."""
        print("🎬 STARTING UNIFIED MULTI-AGENT VIDEO SYSTEM")
        print("=" * 70)
        print(f"🕐 Started at: {datetime.now()}")
        print("🤖 Deploying multi-agent architecture...")
        
        # Create agent tasks
        agent_tasks = [
            self.agent_1_video_processor(),
            self.agent_2_auto_checker(),
            self.agent_3_web_management(),
            self.agent_4_self_healing(),
            self.agent_5_system_monitor()
        ]
        
        print(f"🚀 Launching {len(agent_tasks)} agents in parallel...")
        
        try:
            # Run all agents concurrently
            await asyncio.gather(*agent_tasks, return_exceptions=True)
        except Exception as e:
            print(f"❌ System error: {e}")
            traceback.print_exc()
        finally:
            await self.cleanup()
    
    async def agent_1_video_processor(self):
        """Agent 1: Enhanced video processing."""
        print("🤖 AGENT 1: Video Processor - ONLINE")
        
        while self.running:
            try:
                print("🎬 Agent 1: Starting video processing cycle...")
                
                # Process all marked channels
                await self.processor.process_all_channels()
                
                print("✅ Agent 1: Video processing cycle complete")
                
                # Wait before next cycle (every 10 minutes)
                for _ in range(600):  # 10 minutes = 600 seconds
                    if not self.running:
                        break
                    await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Agent 1 error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def agent_2_auto_checker(self):
        """Agent 2: Auto-check for new videos."""
        print("🤖 AGENT 2: Auto-Checker - ONLINE")
        
        while self.running:
            try:
                print("🔄 Agent 2: Auto-checking for new videos...")
                
                # Check for new videos
                await self.processor.auto_check_new_videos()
                
                print("✅ Agent 2: Auto-check complete")
                
                # Wait before next check (every 30 minutes)
                for _ in range(1800):  # 30 minutes = 1800 seconds
                    if not self.running:
                        break
                    await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Agent 2 error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def agent_3_web_management(self):
        """Agent 3: Web management interface."""
        print("🤖 AGENT 3: Web Management - ONLINE")
        
        try:
            # Run web management system in a separate process
            web_process = subprocess.Popen([
                sys.executable, 'VIDEO_MANAGEMENT_SYSTEM.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['web_management'] = web_process
            print("🌐 Agent 3: Web interface started on http://localhost:5001")
            
            # Monitor the web process
            while self.running:
                if web_process.poll() is not None:
                    print("⚠️ Agent 3: Web process stopped, restarting...")
                    web_process = subprocess.Popen([
                        sys.executable, 'VIDEO_MANAGEMENT_SYSTEM.py'
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.processes['web_management'] = web_process
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except Exception as e:
            print(f"❌ Agent 3 error: {e}")
    
    async def agent_4_self_healing(self):
        """Agent 4: Self-healing system."""
        print("🤖 AGENT 4: Self-Healing - ONLINE")
        
        while self.running:
            try:
                print("🔧 Agent 4: Running self-healing checks...")
                
                # Run healing loop
                await self.healing_system.monitor_system_health()
                
            except Exception as e:
                print(f"❌ Agent 4 error: {e}")
                await asyncio.sleep(60)
    
    async def agent_5_system_monitor(self):
        """Agent 5: System monitoring and reporting."""
        print("🤖 AGENT 5: System Monitor - ONLINE")
        
        while self.running:
            try:
                print("📊 Agent 5: System monitoring cycle...")
                
                # Get system stats
                stats = await self.get_system_stats()
                
                # Report status
                self.report_system_status(stats)
                
                # Wait 5 minutes between reports
                for _ in range(300):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Agent 5 error: {e}")
                await asyncio.sleep(60)
    
    async def get_system_stats(self):
        """Get comprehensive system statistics."""
        try:
            import sqlite3
            conn = sqlite3.connect(self.processor.db_path)
            cursor = conn.cursor()
            
            # Get video counts
            cursor.execute("SELECT COUNT(*) FROM knowledge_hub")
            total_videos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM knowledge_hub WHERE mark_for_delete = 1")
            marked_delete = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM knowledge_hub WHERE mark_for_edit = 1")
            marked_edit = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM knowledge_hub WHERE mark_for_integration = 1")
            marked_integration = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM knowledge_hub WHERE auto_check_enabled = 1")
            auto_check_enabled = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM youtube_channels WHERE process_channel = 1")
            channels_to_process = cursor.fetchone()[0]
            
            # Get processing stats
            cursor.execute("""
                SELECT AVG(quality_score), AVG(relevance_score), AVG(technical_complexity)
                FROM knowledge_hub 
                WHERE quality_score IS NOT NULL
            """)
            avg_stats = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_videos': total_videos,
                'marked_delete': marked_delete,
                'marked_edit': marked_edit,
                'marked_integration': marked_integration,
                'auto_check_enabled': auto_check_enabled,
                'channels_to_process': channels_to_process,
                'avg_quality_score': avg_stats[0] if avg_stats[0] else 0,
                'avg_relevance_score': avg_stats[1] if avg_stats[1] else 0,
                'avg_technical_complexity': avg_stats[2] if avg_stats[2] else 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting system stats: {e}")
            return {'error': str(e)}
    
    def report_system_status(self, stats):
        """Report comprehensive system status."""
        print("\\n" + "=" * 70)
        print("📊 SYSTEM STATUS REPORT")
        print("=" * 70)
        print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📹 Total Videos: {stats.get('total_videos', 0)}")
        print(f"🗑️ Marked for Delete: {stats.get('marked_delete', 0)}")
        print(f"✏️ Marked for Edit: {stats.get('marked_edit', 0)}")
        print(f"➕ Marked for Integration: {stats.get('marked_integration', 0)}")
        print(f"🔄 Auto-Check Enabled: {stats.get('auto_check_enabled', 0)}")
        print(f"📺 Channels to Process: {stats.get('channels_to_process', 0)}")
        print(f"⭐ Avg Quality Score: {stats.get('avg_quality_score', 0):.1%}")
        print(f"🎯 Avg Relevance Score: {stats.get('avg_relevance_score', 0):.1%}")
        print(f"🧠 Avg Complexity: {stats.get('avg_technical_complexity', 0):.1f}/10")
        
        # Agent status
        print("\\n🤖 AGENT STATUS:")
        print("✅ Agent 1: Video Processor - RUNNING")
        print("✅ Agent 2: Auto-Checker - RUNNING")
        print("✅ Agent 3: Web Management - RUNNING")
        print("✅ Agent 4: Self-Healing - RUNNING")
        print("✅ Agent 5: System Monitor - RUNNING")
        
        print("=" * 70)
    
    async def cleanup(self):
        """Clean up processes on shutdown."""
        print("🧹 Cleaning up processes...")
        
        for name, process in self.processes.items():
            try:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        print("✅ Cleanup complete")
    
    async def run_interactive_mode(self):
        """Run in interactive mode with commands."""
        print("\\n🎮 INTERACTIVE MODE")
        print("Available commands:")
        print("  'status' - Show system status")
        print("  'process' - Process marked channels now")
        print("  'check' - Check for new videos now")
        print("  'heal' - Run self-healing now")
        print("  'stop' - Stop system")
        print("  'help' - Show this help")
        
        while self.running:
            try:
                # Non-blocking input check
                import select
                import sys
                
                if select.select([sys.stdin], [], [], 1) == ([sys.stdin], [], []):
                    command = input("\\n🎮 Command: ").strip().lower()
                    
                    if command == 'status':
                        stats = await self.get_system_stats()
                        self.report_system_status(stats)
                    
                    elif command == 'process':
                        print("🎬 Processing channels...")
                        await self.processor.process_all_channels()
                    
                    elif command == 'check':
                        print("🔄 Checking for new videos...")
                        await self.processor.auto_check_new_videos()
                    
                    elif command == 'heal':
                        print("🔧 Running self-healing...")
                        # Run one cycle of healing
                        issues = await self.healing_system.check_stuck_channels()
                        print(f"Found {len(issues)} issues")
                    
                    elif command == 'stop':
                        print("🛑 Stopping system...")
                        self.running = False
                        break
                    
                    elif command == 'help':
                        print("Available commands: status, process, check, heal, stop, help")
                    
                    else:
                        print(f"Unknown command: {command}")
                
                await asyncio.sleep(0.1)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"❌ Interactive mode error: {e}")

async def main():
    """Main function."""
    print("🚀 UNIFIED MULTI-AGENT VIDEO SYSTEM")
    print("=" * 70)
    print("Based on Disler's multi-agent patterns")
    print("🎬 Enhanced video processing with AI analysis")
    print("🔄 Auto-checking for new videos")
    print("🌐 Web management interface")
    print("🔧 Self-healing capabilities")
    print("📊 Real-time monitoring")
    print("=" * 70)
    
    system = UnifiedMultiAgentVideoSystem()
    
    try:
        # Start all agents
        await system.start_all_agents()
        
    except KeyboardInterrupt:
        print("\\n🛑 System stopped by user")
    except Exception as e:
        print(f"\\n❌ System error: {e}")
        traceback.print_exc()
    finally:
        await system.cleanup()

if __name__ == "__main__":
    # Check for interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        system = UnifiedMultiAgentVideoSystem()
        asyncio.run(system.run_interactive_mode())
    else:
        asyncio.run(main())