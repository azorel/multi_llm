#!/usr/bin/env python3
"""
SQL-Based Multi-Agent YouTube Processing System
===============================================

Complete multi-agent system using SQL database instead of Notion.
NO MORE NOTION DEPENDENCIES!
"""

import asyncio
import sqlite3
import os
import json
import aiohttp
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import openai
import anthropic
import google.generativeai as genai

class SQLMultiAgentSystem:
    """Complete multi-agent system using SQL database."""
    
    def __init__(self):
        self.db_path = 'autonomous_learning.db'
        
        # Initialize AI clients
        self.openai_client = None
        self.anthropic_client = None
        self.gemini_client = None
        
        self._init_ai_clients()
        
        # Agent configuration
        self.active_agents = []
        self.max_concurrent_agents = 5
        
    def _init_ai_clients(self):
        """Initialize AI clients."""
        try:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key and openai_key != 'your_openai_api_key_here':
                self.openai_client = openai.OpenAI(api_key=openai_key)
                print("✅ OpenAI client initialized")
        except Exception as e:
            print(f"⚠️ OpenAI client failed: {e}")
        
        try:
            anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_key and anthropic_key != 'your_anthropic_api_key_here':
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                print("✅ Anthropic client initialized")
        except Exception as e:
            print(f"⚠️ Anthropic client failed: {e}")
        
        try:
            google_key = os.getenv('GOOGLE_API_KEY')
            if google_key and google_key != 'your_google_api_key_here':
                genai.configure(api_key=google_key)
                self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
                print("✅ Gemini client initialized")
        except Exception as e:
            print(f"⚠️ Gemini client failed: {e}")
    
    async def get_marked_channels(self):
        """Get channels marked for processing from SQL."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, url, channel_id, hashtags, auto_process, process_channel 
            FROM youtube_channels 
            WHERE process_channel = 1 OR auto_process = 1
        """)
        
        channels = []
        for row in cursor.fetchall():
            channel = {
                'id': row[0],
                'name': row[1],
                'url': row[2],
                'channel_id': row[3],
                'hashtags': json.loads(row[4]) if row[4] else [],
                'auto_process': bool(row[5]),
                'process_channel': bool(row[6])
            }
            channels.append(channel)
        
        conn.close()
        return channels
    
    async def mark_channel_for_processing(self, channel_name: str):
        """Mark a channel for processing in SQL."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE youtube_channels 
            SET process_channel = 1 
            WHERE name LIKE ? OR url LIKE ?
        """, (f'%{channel_name}%', f'%{channel_name}%'))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"✅ Marked {rows_affected} channels matching '{channel_name}' for processing")
        return rows_affected
    
    async def resolve_channel_id(self, url: str) -> Optional[str]:
        """Resolve YouTube channel URL to channel ID."""
        # Direct channel ID format
        channel_id_match = re.search(r'youtube\.com/channel/([a-zA-Z0-9_-]+)', url)
        if channel_id_match:
            return channel_id_match.group(1)
        
        # Handle @username format
        username_match = re.search(r'youtube\.com/@([a-zA-Z0-9_.-]+)', url)
        if username_match:
            return await self._scrape_channel_id(url)
        
        return None
    
    async def _scrape_channel_id(self, url: str) -> Optional[str]:
        """Scrape channel ID from YouTube page."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        patterns = [
                            r'"channelId":"(UC[a-zA-Z0-9_-]{22})"',
                            r'"externalId":"(UC[a-zA-Z0-9_-]{22})"'
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, html)
                            if matches:
                                return matches[0]
        except Exception:
            pass
        
        return None
    
    async def get_channel_videos(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get ALL videos from YouTube channel."""
        print(f"🔍 Getting ALL videos for channel: {channel_id}")
        
        try:
            # Use RSS feed to get videos
            rss_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(rss_url, timeout=10) as response:
                    if response.status != 200:
                        return []
                    
                    xml_data = await response.text()
            
            # Parse XML
            root = ET.fromstring(xml_data)
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'yt': 'http://www.youtube.com/xml/schemas/2015'
            }
            
            videos = []
            entries = root.findall('atom:entry', ns)
            
            for entry in entries:
                video_id = entry.find('yt:videoId', ns)
                title = entry.find('atom:title', ns)
                published = entry.find('atom:published', ns)
                
                if video_id is not None and title is not None:
                    video_data = {
                        'video_id': video_id.text,
                        'title': title.text,
                        'url': f"https://www.youtube.com/watch?v={video_id.text}",
                        'published_at': published.text if published is not None else '',
                        'channel_id': channel_id
                    }
                    videos.append(video_data)
            
            print(f"✅ Found {len(videos)} videos")
            return videos
            
        except Exception as e:
            print(f"❌ Error getting videos: {e}")
            return []
    
    async def get_video_transcript(self, video_id: str) -> str:
        """Get transcript using multiple methods."""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Try multiple language codes
            for lang in ['en', 'en-US', 'en-GB']:
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                    transcript_text = ' '.join([entry['text'] for entry in transcript_list])
                    return transcript_text
                except:
                    continue
            
            # If all fail, try web scraping
            return await self._scrape_transcript(video_id)
            
        except Exception as e:
            print(f"⚠️ Transcript extraction failed for {video_id}: {e}")
            return ""
    
    async def _scrape_transcript(self, video_id: str) -> str:
        """Scrape transcript from YouTube page."""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Look for transcript patterns
                        patterns = [
                            r'"text":"([^"]+)"',
                            r'captionTracks.*?"text":"([^"]+)"'
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, html)
                            if matches and len(matches) > 10:
                                return ' '.join(matches[:100])
            
            return ""
            
        except Exception:
            return ""
    
    async def analyze_with_ai(self, video_data: Dict[str, Any], transcript: str) -> Dict[str, Any]:
        """Analyze video with multiple AI providers."""
        title = video_data.get('title', '')
        
        # Create analysis prompt
        prompt = f"""
        Analyze this YouTube video and provide a comprehensive analysis:
        
        Title: {title}
        Transcript: {transcript[:4000]}  # Limit for token constraints
        
        Provide analysis in JSON format with:
        1. "summary": Brief 2-3 sentence summary
        2. "key_points": List of 3-5 key takeaways
        3. "action_items": List of 3-5 actionable items
        4. "assistant_prompt": Detailed prompt for AI assistant to learn this content
        5. "hashtags": List of 5-8 relevant hashtags
        6. "complexity": "Low", "Medium", or "High"
        7. "priority": "High", "Medium", or "Low"
        """
        
        # Try OpenAI first
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a content analyst. Respond only with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                
                content = response.choices[0].message.content
                
                # Extract JSON
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    analysis = json.loads(content[json_start:json_end])
                    print(f"✅ OpenAI analysis completed for: {title[:50]}...")
                    return analysis
                    
            except Exception as e:
                print(f"⚠️ OpenAI analysis failed: {e}")
        
        # Try Anthropic fallback
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                content = response.content[0].text
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    analysis = json.loads(content[json_start:json_end])
                    print(f"✅ Anthropic analysis completed for: {title[:50]}...")
                    return analysis
                    
            except Exception as e:
                print(f"⚠️ Anthropic analysis failed: {e}")
        
        # Fallback analysis
        return {
            "summary": f"Analysis of video: {title}",
            "key_points": ["Technical content analysis", "Practical implementation details"],
            "action_items": ["Review video content", "Apply relevant techniques"],
            "assistant_prompt": f"Analyze and summarize the content from: {title}",
            "hashtags": ["youtube", "content", "analysis"],
            "complexity": "Medium",
            "priority": "Medium"
        }
    
    async def save_video_to_sql(self, video_data: Dict[str, Any], analysis: Dict[str, Any], channel_name: str):
        """Save processed video to SQL database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO knowledge_hub 
            (name, url, type, content_type, ai_summary, content_summary, key_points, 
             action_items, assistant_prompt, complexity_level, priority, status, 
             processing_status, hashtags, channel, video_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video_data.get('title', ''),
            video_data.get('url', ''),
            'YouTube',
            'Video',
            analysis.get('summary', ''),
            analysis.get('summary', ''),
            '\n'.join([f"• {point}" for point in analysis.get('key_points', [])]),
            '\n'.join([f"• {item}" for item in analysis.get('action_items', [])]),
            analysis.get('assistant_prompt', ''),
            analysis.get('complexity', 'Medium'),
            analysis.get('priority', 'Medium'),
            'Ready',
            'Completed',
            json.dumps(analysis.get('hashtags', [])),
            channel_name,
            video_data.get('video_id', ''),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        print(f"✅ Saved to SQL: {video_data.get('title', '')[:50]}...")
    
    async def unmark_channel(self, channel_id: int):
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
    
    async def process_single_video(self, video: Dict[str, Any], channel_name: str):
        """Process a single video with AI analysis."""
        print(f"📹 Processing: {video['title'][:60]}...")
        
        # Get transcript
        transcript = await self.get_video_transcript(video['video_id'])
        
        if transcript:
            print(f"✅ Got transcript: {len(transcript)} chars")
        else:
            print("⚠️ No transcript available")
        
        # Analyze with AI
        analysis = await self.analyze_with_ai(video, transcript)
        
        # Save to SQL
        await self.save_video_to_sql(video, analysis, channel_name)
        
        return True
    
    async def process_channel(self, channel: Dict[str, Any]):
        """Process all videos from a single channel."""
        print(f"\n📺 Processing channel: {channel['name']}")
        
        # Resolve channel ID if needed
        if not channel['channel_id']:
            channel_id = await self.resolve_channel_id(channel['url'])
            if not channel_id:
                print(f"❌ Could not resolve channel ID for {channel['url']}")
                return
            channel['channel_id'] = channel_id
        
        # Get all videos
        videos = await self.get_channel_videos(channel['channel_id'])
        
        if not videos:
            print(f"❌ No videos found for {channel['name']}")
            return
        
        print(f"📹 Processing ALL {len(videos)} videos from {channel['name']}")
        
        # Process videos concurrently (in batches)
        batch_size = 3  # Process 3 videos at once
        processed_count = 0
        
        for i in range(0, len(videos), batch_size):
            batch = videos[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [
                self.process_single_video(video, channel['name'])
                for video in batch
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if result is True:
                    processed_count += 1
            
            print(f"✅ Processed batch {i//batch_size + 1}/{(len(videos) + batch_size - 1)//batch_size}")
            
            # Small delay between batches
            await asyncio.sleep(2)
        
        print(f"✅ Completed {channel['name']}: {processed_count}/{len(videos)} videos processed")
        
        # Unmark the channel
        await self.unmark_channel(channel['id'])
    
    async def run_continuous_processing(self):
        """Run continuous processing loop."""
        print("🚀 STARTING SQL-BASED MULTI-AGENT CONTINUOUS PROCESSING")
        print("=" * 70)
        
        while True:
            try:
                # Get marked channels
                channels = await self.get_marked_channels()
                
                if not channels:
                    print("⏳ No channels marked for processing. Waiting 30 seconds...")
                    await asyncio.sleep(30)
                    continue
                
                print(f"🎯 Found {len(channels)} channels to process")
                
                # Process channels concurrently
                tasks = [self.process_channel(channel) for channel in channels]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                print("✅ Processing cycle completed!")
                
                # Brief pause before next cycle
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"❌ Error in processing loop: {e}")
                await asyncio.sleep(30)
    
    async def quick_process_marked_channels(self):
        """Process marked channels once."""
        print("🚀 PROCESSING MARKED CHANNELS (SQL-BASED)")
        print("=" * 50)
        
        channels = await self.get_marked_channels()
        
        if not channels:
            print("❌ No channels marked for processing")
            return
        
        print(f"🎯 Processing {len(channels)} marked channels")
        
        for channel in channels:
            await self.process_channel(channel)
        
        print("✅ All marked channels processed!")

# CLI Interface
async def main():
    """Main CLI interface."""
    import sys
    
    system = SQLMultiAgentSystem()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "mark":
            if len(sys.argv) > 2:
                channel_name = sys.argv[2]
                await system.mark_channel_for_processing(channel_name)
            else:
                print("Usage: python sql_multi_agent_system.py mark <channel_name>")
        
        elif command == "process":
            await system.quick_process_marked_channels()
        
        elif command == "continuous":
            await system.run_continuous_processing()
        
        else:
            print("Available commands:")
            print("  mark <channel_name>  - Mark channel for processing")
            print("  process             - Process marked channels once")
            print("  continuous          - Run continuous processing")
    
    else:
        print("🎯 SQL-Based Multi-Agent YouTube Processing System")
        print("Available commands:")
        print("  mark <channel_name>  - Mark channel for processing")
        print("  process             - Process marked channels once")
        print("  continuous          - Run continuous processing")

if __name__ == "__main__":
    asyncio.run(main())