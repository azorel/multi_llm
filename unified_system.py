#!/usr/bin/env python3
"""
UNIFIED MULTI-AGENT SYSTEM
==========================

One system to rule them all. SQL-based, self-healing, multi-agent YouTube processor.
"""

import asyncio
import sqlite3
import os
from datetime import datetime
from sql_multi_agent_system import SQLMultiAgentSystem
from sql_web_server import app

class UnifiedSystem:
    def __init__(self):
        self.db_path = 'autonomous_learning.db'
        self.multi_agent = SQLMultiAgentSystem()
        
    async def start_all_services(self):
        """Start all services concurrently"""
        print("🚀 STARTING UNIFIED SYSTEM")
        print("=" * 60)
        
        # Start tasks concurrently
        tasks = [
            self.start_web_server(),
            self.start_multi_agent_processor(),
            self.start_self_healing_monitor()
        ]
        
        await asyncio.gather(*tasks)
    
    async def start_web_server(self):
        """Start web server on port 5000"""
        print("🌐 Starting web server on http://localhost:5000")
        # Run Flask in thread to not block asyncio
        import threading
        def run_flask():
            app.run(host='0.0.0.0', port=5000, debug=False)
        
        thread = threading.Thread(target=run_flask, daemon=True)
        thread.start()
        
        # Keep running
        while True:
            await asyncio.sleep(60)
    
    async def start_multi_agent_processor(self):
        """Start multi-agent YouTube processor"""
        print("🤖 Starting multi-agent YouTube processor")
        await self.multi_agent.run_continuous_processing()
    
    async def start_self_healing_monitor(self):
        """Start self-healing monitor"""
        print("🔧 Starting self-healing monitor")
        
        while True:
            try:
                # Check system health
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Check for marked channels
                cursor.execute("SELECT COUNT(*) FROM youtube_channels WHERE process_channel = 1")
                marked_channels = cursor.fetchone()[0]
                
                if marked_channels > 0:
                    print(f"🔍 Found {marked_channels} channels to process")
                
                conn.close()
                
                # Wait before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"❌ Self-healing error: {e}")
                await asyncio.sleep(60)

if __name__ == "__main__":
    system = UnifiedSystem()
    asyncio.run(system.start_all_services())
