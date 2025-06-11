#!/usr/bin/env python3
"""
Notion to SQL Migration System
==============================

Complete migration from Notion to SQL using multi-agent system.
No more Notion dependencies!
"""

import asyncio
import sqlite3
import os
import json
import requests
from datetime import datetime
from pathlib import Path

class NotionToSQLMigrator:
    """Multi-agent system to migrate all Notion data to SQL."""
    
    def __init__(self):
        # Notion config (to extract data one last time)
        self.channels_db_id = '203ec31c-9de2-8079-ae4e-ed754d474888'
        self.knowledge_db_id = '20bec31c-9de2-814e-80db-d13d0c27d869'
        
        self.headers = {
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        # SQL database
        self.db_path = 'autonomous_learning.db'
        self.init_sql_database()
    
    def init_sql_database(self):
        """Initialize complete SQL database schema."""
        print("🗄️ Creating SQL database schema...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # YouTube Channels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS youtube_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                channel_id TEXT UNIQUE,
                description TEXT,
                subscriber_count INTEGER DEFAULT 0,
                video_count INTEGER DEFAULT 0,
                country TEXT,
                hashtags TEXT, -- JSON array
                auto_process BOOLEAN DEFAULT FALSE,
                process_channel BOOLEAN DEFAULT FALSE,
                last_processed DATETIME,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Knowledge Hub table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_hub (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT UNIQUE,
                type TEXT DEFAULT 'YouTube',
                content_type TEXT,
                ai_summary TEXT,
                content_summary TEXT,
                key_points TEXT,
                action_items TEXT,
                assistant_prompt TEXT,
                complexity_level TEXT DEFAULT 'Medium',
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Ready',
                processing_status TEXT DEFAULT 'Pending',
                hashtags TEXT, -- JSON array
                channel TEXT,
                video_id TEXT,
                duration_seconds INTEGER,
                published_at DATETIME,
                decision_made BOOLEAN DEFAULT FALSE,
                pass_flag BOOLEAN DEFAULT FALSE,
                yes_flag BOOLEAN DEFAULT FALSE,
                notes TEXT,
                thumbnail_url TEXT,
                transcript TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Agent Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                agent_id TEXT,
                result TEXT,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            )
        """)
        
        # Processing Logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT, -- JSON
                level TEXT DEFAULT 'INFO',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ SQL database schema created")
    
    async def migrate_youtube_channels(self):
        """Migrate all YouTube channels from Notion to SQL."""
        print("📺 Migrating YouTube channels...")
        
        try:
            # Get all channels from Notion
            response = requests.post(
                headers=self.headers,
                json={"page_size": 100},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch channels: {response.status_code}")
                return
            
            channels_data = response.json().get('results', [])
            print(f"Found {len(channels_data)} channels to migrate")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            migrated_count = 0
            for channel in channels_data:
                props = channel.get('properties', {})
                
                # Extract channel data
                name = self._extract_text(props.get('Name', {}))
                url = self._extract_text(props.get('URL', {}))
                channel_id = self._extract_text(props.get('Channel', {}))
                description = self._extract_text(props.get('Description', {}))
                subscriber_count = props.get('Subscribers', {}).get('number', 0) or 0
                video_count = props.get('Videos', {}).get('number', 0) or 0
                country = props.get('Country', {}).get('select', {}).get('name', '')
                
                # Extract hashtags
                hashtags = []
                if props.get('Hashtags', {}).get('multi_select'):
                    hashtags = [tag['name'] for tag in props['Hashtags']['multi_select']]
                
                auto_process = props.get('Auto Process', {}).get('checkbox', False)
                process_channel = props.get('Process Channel', {}).get('checkbox', False)
                
                last_processed = None
                if props.get('Last Processed', {}).get('date'):
                    last_processed = props['Last Processed']['date'].get('start')
                
                notes = self._extract_text(props.get('Notes', {}))
                
                # Insert into SQL
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO youtube_channels 
                        (name, url, channel_id, description, subscriber_count, video_count, 
                         country, hashtags, auto_process, process_channel, last_processed, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name, url, channel_id, description, subscriber_count, video_count,
                        country, json.dumps(hashtags), auto_process, process_channel, 
                        last_processed, notes
                    ))
                    migrated_count += 1
                    print(f"✅ Migrated channel: {name}")
                    
                except Exception as e:
                    print(f"❌ Error migrating channel {name}: {e}")
            
            conn.commit()
            conn.close()
            
            print(f"✅ Migrated {migrated_count} YouTube channels to SQL")
            
        except Exception as e:
            print(f"❌ Migration error: {e}")
    
    async def migrate_knowledge_hub(self):
        """Migrate all Knowledge Hub videos from Notion to SQL."""
        print("🧠 Migrating Knowledge Hub...")
        
        try:
            # Get all videos from Notion in batches
            all_videos = []
            has_more = True
            next_cursor = None
            
            while has_more:
                query_data = {"page_size": 100}
                if next_cursor:
                    query_data["start_cursor"] = next_cursor
                
                response = requests.post(
                    headers=self.headers,
                    json=query_data,
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"❌ Failed to fetch videos: {response.status_code}")
                    break
                
                data = response.json()
                all_videos.extend(data.get('results', []))
                has_more = data.get('has_more', False)
                next_cursor = data.get('next_cursor')
                
                print(f"Fetched {len(all_videos)} videos so far...")
                await asyncio.sleep(1)  # Rate limiting
            
            print(f"Found {len(all_videos)} videos to migrate")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            migrated_count = 0
            for video in all_videos:
                props = video.get('properties', {})
                
                # Extract video data
                name = self._extract_text(props.get('Name', {}))
                url = props.get('URL', {}).get('url', '')
                video_type = props.get('Type', {}).get('select', {}).get('name', 'YouTube')
                content_type = props.get('Content Type', {}).get('select', {}).get('name', '')
                
                ai_summary = self._extract_text(props.get('AI Summary', {}))
                content_summary = self._extract_text(props.get('Content Summary', {}))
                key_points = self._extract_text(props.get('Key Points', {}))
                action_items = self._extract_text(props.get('Action Items', {}))
                assistant_prompt = self._extract_text(props.get('Assistant Prompt', {}))
                
                complexity_level = props.get('Complexity Level', {}).get('select', {}).get('name', 'Medium')
                priority = props.get('Priority', {}).get('select', {}).get('name', 'Medium')
                status = props.get('Status', {}).get('select', {}).get('name', 'Ready')
                processing_status = props.get('Processing Status', {}).get('select', {}).get('name', 'Pending')
                
                # Extract hashtags
                hashtags = []
                if props.get('Hashtags', {}).get('multi_select'):
                    hashtags = [tag['name'] for tag in props['Hashtags']['multi_select']]
                
                channel = self._extract_text(props.get('Channel', {}))
                notes = self._extract_text(props.get('Notes', {}))
                
                # Extract video ID from URL
                video_id = ''
                if 'youtube.com/watch?v=' in url:
                    video_id = url.split('v=')[1].split('&')[0]
                
                # Checkbox flags
                decision_made = props.get('Decision Made', {}).get('checkbox', False)
                pass_flag = props.get('📁 Pass', {}).get('checkbox', False)
                yes_flag = props.get('🚀 Yes', {}).get('checkbox', False)
                
                # Insert into SQL
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO knowledge_hub 
                        (name, url, type, content_type, ai_summary, content_summary, key_points, 
                         action_items, assistant_prompt, complexity_level, priority, status, 
                         processing_status, hashtags, channel, video_id, decision_made, 
                         pass_flag, yes_flag, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name, url, video_type, content_type, ai_summary, content_summary, 
                        key_points, action_items, assistant_prompt, complexity_level, priority, 
                        status, processing_status, json.dumps(hashtags), channel, video_id, 
                        decision_made, pass_flag, yes_flag, notes
                    ))
                    migrated_count += 1
                    
                    if migrated_count % 100 == 0:
                        print(f"✅ Migrated {migrated_count} videos...")
                        
                except Exception as e:
                    print(f"❌ Error migrating video {name}: {e}")
            
            conn.commit()
            conn.close()
            
            print(f"✅ Migrated {migrated_count} videos to SQL")
            
        except Exception as e:
            print(f"❌ Migration error: {e}")
    
    def _extract_text(self, prop):
        """Extract text from Notion property."""
        if not prop:
            return ""
        
        if prop.get('title'):
            return prop['title'][0].get('plain_text', '') if prop['title'] else ""
        
        if prop.get('rich_text'):
            return prop['rich_text'][0].get('plain_text', '') if prop['rich_text'] else ""
        
        return ""
    
    async def create_sql_based_agents(self):
        """Create new SQL-based agents."""
        print("🤖 Creating SQL-based multi-agent system...")
        
        sql_agent_code = '''#!/usr/bin/env python3
"""
SQL-Based YouTube Processing Agent
=================================

Processes YouTube channels using SQL database instead of Notion.
"""

import sqlite3
import asyncio
import os
import json
from datetime import datetime

class SQLYouTubeProcessor:
    """SQL-based YouTube processor."""
    
    def __init__(self):
        self.db_path = 'autonomous_learning.db'
    
    async def get_marked_channels(self):
        """Get channels marked for processing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM youtube_channels 
            WHERE process_channel = 1 OR auto_process = 1
        """)
        
        channels = []
        for row in cursor.fetchall():
            channel = {
                'id': row[0],
                'name': row[1],
                'url': row[2],
                'channel_id': row[3],
                'hashtags': json.loads(row[8]) if row[8] else [],
                'auto_process': bool(row[9]),
                'process_channel': bool(row[10])
            }
            channels.append(channel)
        
        conn.close()
        return channels
    
    async def save_video(self, video_data):
        """Save video to SQL database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO knowledge_hub 
            (name, url, type, content_type, ai_summary, content_summary, 
             key_points, action_items, assistant_prompt, hashtags, channel, 
             video_id, processing_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video_data.get('title', ''),
            video_data.get('url', ''),
            'YouTube',
            'Video',
            video_data.get('ai_summary', ''),
            video_data.get('content_summary', ''),
            video_data.get('key_points', ''),
            video_data.get('action_items', ''),
            video_data.get('assistant_prompt', ''),
            json.dumps(video_data.get('hashtags', [])),
            video_data.get('channel', ''),
            video_data.get('video_id', ''),
            'Completed'
        ))
        
        conn.commit()
        conn.close()
        print(f"✅ Saved video to SQL: {video_data.get('title', '')[:50]}...")
    
    async def unmark_channel(self, channel_id):
        """Unmark channel after processing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE youtube_channels 
            SET process_channel = 0, last_processed = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), channel_id))
        
        conn.commit()
        conn.close()
        print(f"✅ Unmarked channel {channel_id}")

if __name__ == "__main__":
    processor = SQLYouTubeProcessor()
    
    async def test_sql_processor():
        channels = await processor.get_marked_channels()
        print(f"Found {len(channels)} channels marked for processing")
        
        for channel in channels:
            print(f"Channel: {channel['name']} - {channel['url']}")
    
    asyncio.run(test_sql_processor())
'''
        
        # Write SQL-based processor
        with open('sql_youtube_processor.py', 'w') as f:
            f.write(sql_agent_code)
        
        print("✅ Created SQL-based YouTube processor")
    
    async def run_migration(self):
        """Run complete migration."""
        print("🚀 STARTING COMPLETE NOTION TO SQL MIGRATION")
        print("=" * 60)
        
        # Step 1: Migrate YouTube channels
        await self.migrate_youtube_channels()
        
        # Step 2: Migrate Knowledge Hub
        await self.migrate_knowledge_hub()
        
        # Step 3: Create SQL-based agents
        await self.create_sql_based_agents()
        
        # Step 4: Test the new system
        print("\n🧪 Testing SQL-based system...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM youtube_channels")
        channel_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_hub")
        video_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Migration complete!")
        print(f"📺 YouTube channels: {channel_count}")
        print(f"🧠 Knowledge videos: {video_count}")
        print(f"🗄️ Database: {self.db_path}")
        print("\n🎯 NOTION IS NO LONGER NEEDED!")
        print("   All data is now in SQL database")
        print("   Multi-agents can process using SQL only")

if __name__ == "__main__":
# NOTION_REMOVED:     migrator = NotionToSQLMigrator()
    asyncio.run(migrator.run_migration())