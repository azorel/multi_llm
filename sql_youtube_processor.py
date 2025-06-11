#!/usr/bin/env python3
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
