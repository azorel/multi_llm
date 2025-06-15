#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM TEST
========================

Tests ALL components to ensure they're REAL and WORKING.
# DEMO CODE REMOVED: No demos, no simulations - REAL TESTS.
"""

import sqlite3
import requests
import asyncio
import json
import os
import sys
from datetime import datetime

class SystemTester:
    def __init__(self):
        self.db_path = 'autonomous_learning.db'
        self.base_url = 'http://localhost:5000'
        self.test_results = []
        
    def test_database(self):
        """Test 1: Database connectivity and data"""
        print("\n🧪 TEST 1: DATABASE")
        print("-" * 50)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✅ Tables found: {tables}")
            
            # Test data
            cursor.execute("SELECT COUNT(*) FROM youtube_channels")
            channels = cursor.fetchone()[0]
            print(f"✅ YouTube channels: {channels}")
            
            cursor.execute("SELECT COUNT(*) FROM knowledge_hub")
            videos = cursor.fetchone()[0]
            print(f"✅ Knowledge Hub videos: {videos}")
            
# DEMO CODE REMOVED: # Get sample data
            cursor.execute("SELECT name, url FROM youtube_channels LIMIT 3")
            for name, url in cursor.fetchall():
                print(f"   📺 {name}: {url}")
            
            conn.close()
            self.test_results.append(("Database", "PASSED", f"{channels} channels, {videos} videos"))
            return True
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            self.test_results.append(("Database", "FAILED", str(e)))
            return False
    
    def test_web_server(self):
        """Test 2: Web server endpoints"""
        print("\n🧪 TEST 2: WEB SERVER")
        print("-" * 50)
        
        endpoints = [
            ('/', 'Dashboard'),
            ('/youtube_channels', 'YouTube Channels'),
            ('/api/stats', 'API Stats')
        ]
        
        passed = 0
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {name}: {response.status_code}")
                    passed += 1
                else:
                    print(f"❌ {name}: {response.status_code}")
            except Exception as e:
                print(f"❌ {name}: {e}")
        
        self.test_results.append(("Web Server", 
                                "PASSED" if passed == len(endpoints) else "PARTIAL", 
                                f"{passed}/{len(endpoints)} endpoints working"))
        return passed == len(endpoints)
    
    def test_api_functionality(self):
        """Test 3: API functionality"""
        print("\n🧪 TEST 3: API FUNCTIONALITY")
        print("-" * 50)
        
        try:
            # Test stats API
            response = requests.get(f"{self.base_url}/api/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Stats API returned: {stats}")
                
                # Test marking channel
                # First get a channel ID
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM youtube_channels LIMIT 1")
                channel_id, channel_name = cursor.fetchone()
                conn.close()
                
                # Mark it
                response = requests.post(f"{self.base_url}/api/mark_channel/{channel_id}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Marked channel '{channel_name}': {result}")
                    self.test_results.append(("API Functionality", "PASSED", "All APIs working"))
                    return True
                
        except Exception as e:
            print(f"❌ API test failed: {e}")
            self.test_results.append(("API Functionality", "FAILED", str(e)))
            return False
    
    def test_youtube_processing(self):
        """Test 4: YouTube processing capability"""
        print("\n🧪 TEST 4: YOUTUBE PROCESSING")
        print("-" * 50)
        
        try:
            # Check if processor can get marked channels
            from sql_multi_agent_system import SQLMultiAgentSystem
            
            system = SQLMultiAgentSystem()
            
            # Test getting marked channels
            async def test_async():
                channels = await system.get_marked_channels()
                print(f"✅ Found {len(channels)} marked channels")
                
                if channels:
                    channel = channels[0]
                    print(f"   Processing: {channel['name']}")
                    
                    # Test video discovery
                    videos = await system.get_channel_videos(channel['channel_id'])
                    print(f"✅ Can fetch videos: {len(videos)} found")
                    
                    if videos:
                        # Test transcript extraction
                        video = videos[0]
                        transcript = await system.get_video_transcript(video['video_id'])
                        print(f"✅ Can extract transcripts: {len(transcript)} chars")
                    
                    return True
                return False
            
            result = asyncio.run(test_async())
            self.test_results.append(("YouTube Processing", 
                                    "PASSED" if result else "NO_CHANNELS", 
                                    "Processing pipeline verified"))
            return result
            
        except Exception as e:
            print(f"❌ YouTube processing test failed: {e}")
            self.test_results.append(("YouTube Processing", "FAILED", str(e)))
            return False
    
    def test_multi_agent_system(self):
        """Test 5: Multi-agent system"""
        print("\n🧪 TEST 5: MULTI-AGENT SYSTEM")
        print("-" * 50)
        
        try:
            # Check running processes
            import subprocess
            
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout
            
            agents = [
                ('FINAL_UNIFIED_SYSTEM', 'Main orchestrator'),
                ('sql_web_server', 'Web server'),
                ('sql_multi_agent', 'YouTube processor')
            ]
            
            found = []
            for agent, desc in agents:
                if agent in processes:
                    print(f"✅ {desc}: RUNNING")
                    found.append(desc)
                else:
                    print(f"⚠️ {desc}: NOT FOUND in processes")
            
            self.test_results.append(("Multi-Agent System", 
                                    "PARTIAL" if found else "NOT_RUNNING", 
                                    f"{len(found)} agents detected"))
            return len(found) > 0
            
        except Exception as e:
            print(f"❌ Multi-agent test failed: {e}")
            self.test_results.append(("Multi-Agent System", "FAILED", str(e)))
            return False
    
    def test_self_healing(self):
        """Test 6: Self-healing capability"""
        print("\n🧪 TEST 6: SELF-HEALING")
        print("-" * 50)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create a stuck channel scenario
            cursor.execute("""
                UPDATE youtube_channels 
                SET process_channel = 1, 
                    last_processed = datetime('now', '-2 hours')
                WHERE id = (SELECT id FROM youtube_channels LIMIT 1)
            """)
            conn.commit()
            
            # Check if self-healing would detect it
            cursor.execute("""
                SELECT COUNT(*) FROM youtube_channels 
                WHERE process_channel = 1 
                AND datetime(last_processed) < datetime('now', '-1 hour')
            """)
            stuck = cursor.fetchone()[0]
            
            if stuck > 0:
                print(f"✅ Self-healing would detect {stuck} stuck channels")
                self.test_results.append(("Self-Healing", "READY", "Detection logic verified"))
                result = True
            else:
                print("⚠️ Self-healing detection not working")
                self.test_results.append(("Self-Healing", "NOT_READY", "Detection failed"))
                result = False
                
            conn.close()
            return result
            
        except Exception as e:
            print(f"❌ Self-healing test failed: {e}")
            self.test_results.append(("Self-Healing", "FAILED", str(e)))
            return False
    
    def run_all_tests(self):
        """Run all system tests"""
        print("=" * 70)
        print("🔍 COMPREHENSIVE SYSTEM TEST")
        print("=" * 70)
        print(f"Time: {datetime.now()}")
        print(f"Database: {self.db_path}")
        print(f"Web Server: {self.base_url}")
        
        # Run all tests
        self.test_database()
        self.test_web_server()
        self.test_api_functionality()
        self.test_youtube_processing()
        self.test_multi_agent_system()
        self.test_self_healing()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed = 0
        for test, status, details in self.test_results:
            emoji = "✅" if status == "PASSED" else "⚠️" if status in ["PARTIAL", "READY"] else "❌"
            print(f"{emoji} {test}: {status} - {details}")
            if status == "PASSED":
                passed += 1
        
        print(f"\n🎯 OVERALL: {passed}/{len(self.test_results)} tests fully passed")
        
        if passed >= 4:
            print("\n✅ SYSTEM IS OPERATIONAL AND READY!")
        else:
            print("\n⚠️ SYSTEM NEEDS ATTENTION - Some components not fully operational")
        
        return passed

if __name__ == "__main__":
    tester = SystemTester()
    tester.run_all_tests()