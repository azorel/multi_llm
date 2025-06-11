#!/usr/bin/env python3
"""
ENHANCED VIDEO PROCESSOR
=======================

Multi-agent video processing system with:
- Complete metadata extraction (title, hashtags, duration, etc)
- Full transcript/closed caption download
- Multi-LLM analysis pipeline
- AI-generated summaries and integration prompts
- Video management capabilities
- Auto-check for new videos

Based on Disler's multi-agent patterns for parallel processing.
"""

import asyncio
import sqlite3
import os
import json
import aiohttp
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import traceback
from urllib.parse import urlparse, parse_qs
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import openai
import anthropic
import google.generativeai as genai

class EnhancedVideoProcessor:
    """Enhanced multi-agent video processor with comprehensive analysis."""
    
    def __init__(self):
        self.db_path = 'autonomous_learning.db'
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        
        # Initialize LLM clients
        self.openai_client = None
        self.anthropic_client = None
        
        if self.openai_key:
            self.openai_client = openai.AsyncOpenAI(api_key=self.openai_key)
        
        if self.anthropic_key:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)
            
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
        
        # Enhanced schema
        self.init_enhanced_schema()
        
        print("🎥 Enhanced Video Processor initialized")
        print(f"🔑 LLMs available: OpenAI: {bool(self.openai_key)}, Anthropic: {bool(self.anthropic_key)}, Gemini: {bool(self.gemini_key)}")
    
    def init_enhanced_schema(self):
        """Initialize enhanced database schema for rich video data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add new columns for enhanced video data
        new_columns = [
            ("description", "TEXT"),
            ("tags", "TEXT"),  # JSON array of tags
            ("category_id", "TEXT"),
            ("view_count", "INTEGER"),
            ("like_count", "INTEGER"),
            ("comment_count", "INTEGER"),
            ("upload_date", "TEXT"),
            ("uploader", "TEXT"),
            ("uploader_id", "TEXT"),
            ("language", "TEXT"),
            ("availability", "TEXT"),
            ("age_limit", "INTEGER"),
            ("live_status", "TEXT"),
            ("was_live", "BOOLEAN"),
            ("playable_in_embed", "BOOLEAN"),
            ("chapters", "TEXT"),  # JSON array
            ("automatic_captions", "TEXT"),  # JSON
            ("subtitles", "TEXT"),  # JSON
            ("ai_extracted_hashtags", "TEXT"),  # From transcript analysis
            ("ai_context", "TEXT"),  # Context extracted by cheap LLM
            ("ai_detailed_summary", "TEXT"),  # Detailed summary by premium LLM
            ("ai_key_insights", "TEXT"),  # JSON array of key insights
            ("integration_prompt", "TEXT"),  # What you'd get from integrating this
            ("improvement_potential", "TEXT"),  # What improvements it would bring
            ("mark_for_delete", "BOOLEAN DEFAULT FALSE"),
            ("mark_for_edit", "BOOLEAN DEFAULT FALSE"),
            ("mark_for_integration", "BOOLEAN DEFAULT FALSE"),
            ("integration_notes", "TEXT"),
            ("auto_check_enabled", "BOOLEAN DEFAULT FALSE"),
            ("last_auto_check", "DATETIME"),
            ("processing_agent", "TEXT"),  # Which agent processed it
            ("processing_time", "REAL"),  # Processing time in seconds
            ("quality_score", "REAL"),  # AI-assessed content quality (0-1)
            ("relevance_score", "REAL"),  # How relevant to user interests (0-1)
            ("technical_complexity", "INTEGER"),  # 1-10 scale
        ]
        
        for column_name, column_type in new_columns:
            try:
                cursor.execute(f"ALTER TABLE knowledge_hub ADD COLUMN {column_name} {column_type}")
                print(f"✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    print(f"⚠️ Column issue {column_name}: {e}")
        
        conn.commit()
        conn.close()
        print("✅ Enhanced database schema ready")
    
    async def process_all_channels(self):
        """Main orchestrator: Process all marked channels with multi-agents."""
        print("🚀 Starting Enhanced Multi-Agent Channel Processing")
        print("=" * 70)
        
        marked_channels = await self.get_marked_channels()
        
        if not marked_channels:
            print("📺 No channels marked for processing")
            return
        
        print(f"🎯 Found {len(marked_channels)} channels to process")
        
        # Create processing tasks for each channel (multi-agent approach)
        tasks = []
        for i, channel in enumerate(marked_channels):
            agent_id = f"Agent_{i+1}"
            task = self.agent_process_channel(channel, agent_id)
            tasks.append(task)
        
        # Run all agents in parallel
        print(f"🤖 Deploying {len(tasks)} agents for parallel processing...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Summary
        successful = sum(1 for r in results if not isinstance(r, Exception))
        print(f"\\n✅ Processing complete: {successful}/{len(results)} channels processed successfully")
        
        # Update channel statuses
        await self.update_processed_channels(marked_channels)
    
    async def agent_process_channel(self, channel: Dict, agent_id: str):
        """Individual agent to process a channel."""
        start_time = datetime.now()
        print(f"\\n🤖 {agent_id}: Processing channel '{channel['name']}'")
        
        try:
            # Step 1: Get all videos from channel
            videos = await self.get_channel_videos_detailed(channel['url'])
            print(f"📹 {agent_id}: Found {len(videos)} videos")
            
            if not videos:
                print(f"⚠️ {agent_id}: No videos found for {channel['name']}")
                return
            
            # Step 2: Process each video with full enhancement
            processed_count = 0
            for video in videos:
                try:
                    success = await self.process_video_enhanced(video, channel, agent_id)
                    if success:
                        processed_count += 1
                    
                    # Brief pause to avoid rate limits
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"❌ {agent_id}: Error processing video {video.get('title', 'Unknown')}: {e}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"✅ {agent_id}: Completed {processed_count}/{len(videos)} videos in {processing_time:.1f}s")
            
        except Exception as e:
            print(f"❌ {agent_id}: Channel processing failed: {e}")
            traceback.print_exc()
    
    async def get_channel_videos_detailed(self, channel_url: str) -> List[Dict]:
        """Get all videos from a channel with detailed metadata."""
        try:
            # Configure yt-dlp for comprehensive metadata extraction
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,  # Get full info
                'writesubtitles': True,
                'writeautomaticsub': True,
                'skip_download': True,
                'ignoreerrors': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract channel info and videos
                channel_info = ydl.extract_info(channel_url, download=False)
                
                if 'entries' not in channel_info:
                    print(f"⚠️ No videos found in channel")
                    return []
                
                videos = []
                for entry in channel_info['entries']:
                    if entry and entry.get('id'):
                        # Get detailed video info
                        try:
                            video_info = ydl.extract_info(f"https://www.youtube.com/watch?v={entry['id']}", download=False)
                            videos.append(video_info)
                        except Exception as e:
                            print(f"⚠️ Couldn't get details for video {entry.get('id')}: {e}")
                            continue
                
                print(f"📹 Extracted {len(videos)} videos with full metadata")
                return videos
                
        except Exception as e:
            print(f"❌ Error getting channel videos: {e}")
            return []
    
    async def process_video_enhanced(self, video_info: Dict, channel: Dict, agent_id: str) -> bool:
        """Process a single video with comprehensive enhancement."""
        try:
            video_id = video_info.get('id')
            title = video_info.get('title', 'Unknown Title')
            
            print(f"🎬 {agent_id}: Processing '{title[:50]}...'")
            
            # Check if already processed
            if await self.is_video_processed(video_id):
                print(f"⏭️ {agent_id}: Video already processed, skipping")
                return True
            
            # Step 1: Extract comprehensive metadata
            metadata = self.extract_comprehensive_metadata(video_info)
            
            # Step 2: Get transcript/closed captions
            transcript = await self.get_video_transcript_enhanced(video_info)
            
            # Step 3: AI Analysis Pipeline
            ai_analysis = await self.ai_analysis_pipeline(transcript, metadata, agent_id)
            
            # Step 4: Store everything in database
            await self.store_enhanced_video(metadata, transcript, ai_analysis, channel, agent_id)
            
            print(f"✅ {agent_id}: Enhanced processing complete for '{title[:30]}...'")
            return True
            
        except Exception as e:
            print(f"❌ {agent_id}: Video processing failed: {e}")
            return False
    
    def extract_comprehensive_metadata(self, video_info: Dict) -> Dict:
        """Extract all available metadata from video."""
        metadata = {
            'video_id': video_info.get('id'),
            'title': video_info.get('title'),
            'description': video_info.get('description'),
            'duration_seconds': video_info.get('duration'),
            'view_count': video_info.get('view_count'),
            'like_count': video_info.get('like_count'),
            'comment_count': video_info.get('comment_count'),
            'upload_date': video_info.get('upload_date'),
            'uploader': video_info.get('uploader'),
            'uploader_id': video_info.get('uploader_id'),
            'thumbnail_url': video_info.get('thumbnail'),
            'language': video_info.get('language'),
            'category_id': video_info.get('category_id'),
            'tags': json.dumps(video_info.get('tags', [])),
            'availability': video_info.get('availability'),
            'age_limit': video_info.get('age_limit'),
            'live_status': video_info.get('live_status'),
            'was_live': video_info.get('was_live'),
            'playable_in_embed': video_info.get('playable_in_embed'),
            'chapters': json.dumps(video_info.get('chapters', [])),
            'automatic_captions': json.dumps(video_info.get('automatic_captions', {})),
            'subtitles': json.dumps(video_info.get('subtitles', {})),
            'published_at': self.parse_upload_date(video_info.get('upload_date')),
        }
        
        # Extract hashtags from title and description
        hashtags = self.extract_hashtags_from_text(
            f"{metadata['title']} {metadata['description']}"
        )
        metadata['hashtags'] = json.dumps(hashtags)
        
        return metadata
    
    def extract_hashtags_from_text(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        if not text:
            return []
        
        # Find hashtags
        hashtag_pattern = r'#\\w+'
        hashtags = re.findall(hashtag_pattern, text)
        return list(set(hashtags))  # Remove duplicates
    
    def parse_upload_date(self, upload_date: str) -> str:
        """Parse upload date to ISO format."""
        if not upload_date:
            return None
        
        try:
            # yt-dlp format: YYYYMMDD
            if len(upload_date) == 8:
                year = upload_date[:4]
                month = upload_date[4:6]
                day = upload_date[6:8]
                return f"{year}-{month}-{day}T00:00:00Z"
        except:
            pass
        
        return upload_date
    
    async def get_video_transcript_enhanced(self, video_info: Dict) -> str:
        """Get comprehensive transcript with fallbacks."""
        try:
            video_id = video_info.get('id')
            
            # Try multiple transcript sources
            transcript_sources = [
                video_info.get('subtitles', {}),
                video_info.get('automatic_captions', {}),
            ]
            
            for source in transcript_sources:
                if source:
                    # Try different languages
                    for lang in ['en', 'en-US', 'en-GB']:
                        if lang in source:
                            # Extract transcript URL and download
                            transcript_info = source[lang]
                            if isinstance(transcript_info, list) and transcript_info:
                                transcript_url = transcript_info[0].get('url')
                                if transcript_url:
                                    transcript = await self.download_transcript(transcript_url)
                                    if transcript:
                                        return transcript
            
            # Fallback: Try youtube-transcript-api
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                transcript = ' '.join([entry['text'] for entry in transcript_list])
                return transcript
            except:
                pass
            
            print(f"⚠️ No transcript found for video {video_id}")
            return ""
            
        except Exception as e:
            print(f"❌ Transcript extraction failed: {e}")
            return ""
    
    async def download_transcript(self, url: str) -> str:
        """Download transcript from URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Basic VTT/SRT parsing
                        lines = content.split('\\n')
                        transcript_lines = []
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith(('WEBVTT', '-->', 'NOTE')):
                                # Remove timestamps and tags
                                clean_line = re.sub(r'<.*?>', '', line)
                                clean_line = re.sub(r'\\d{2}:\\d{2}:\\d{2}.*', '', clean_line)
                                if clean_line:
                                    transcript_lines.append(clean_line)
                        
                        return ' '.join(transcript_lines)
        except Exception as e:
            print(f"⚠️ Transcript download failed: {e}")
        
        return ""
    
    async def ai_analysis_pipeline(self, transcript: str, metadata: Dict, agent_id: str) -> Dict:
        """Multi-LLM analysis pipeline for comprehensive video understanding."""
        print(f"🧠 {agent_id}: Starting AI analysis pipeline...")
        
        analysis = {}
        
        try:
            # Step 1: Cheap LLM for hashtags and context extraction
            context_analysis = await self.extract_context_with_cheap_llm(transcript, metadata)
            analysis.update(context_analysis)
            
            # Step 2: Premium LLM for detailed summary and insights
            detailed_analysis = await self.generate_detailed_summary(transcript, metadata, context_analysis)
            analysis.update(detailed_analysis)
            
            # Step 3: Generate integration prompt
            integration_prompt = await self.generate_integration_prompt(transcript, metadata, analysis)
            analysis['integration_prompt'] = integration_prompt
            
            # Step 4: Calculate quality and relevance scores
            scores = await self.calculate_content_scores(transcript, metadata, analysis)
            analysis.update(scores)
            
            print(f"✅ {agent_id}: AI analysis complete")
            return analysis
            
        except Exception as e:
            print(f"❌ {agent_id}: AI analysis failed: {e}")
            return {}
    
    async def extract_context_with_cheap_llm(self, transcript: str, metadata: Dict) -> Dict:
        """Use cheap LLM to extract hashtags and context."""
        if not transcript:
            return {'ai_extracted_hashtags': '[]', 'ai_context': 'No transcript available'}
        
        prompt = f"""
        Analyze this video transcript and extract:

        1. HASHTAGS: Generate 5-10 relevant hashtags for this content
        2. CONTEXT: Summarize what this video is about in 2-3 sentences
        3. TOPICS: List the main topics discussed

        Video Title: {metadata.get('title', 'Unknown')}
        Transcript: {transcript[:3000]}...

        Respond in JSON format:
        {{
            "hashtags": ["#topic1", "#topic2", ...],
            "context": "Brief context summary...",
            "main_topics": ["topic1", "topic2", ...]
        }}
        """
        
        try:
            # Use Gemini (cheapest) or fallback to others
            if self.gemini_key:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                result = response.text
            elif self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=800
                )
                result = response.choices[0].message.content
            else:
                return {'ai_extracted_hashtags': '[]', 'ai_context': 'No LLM available'}
            
            # Parse JSON response
            try:
                parsed = json.loads(result.strip('```json').strip('```').strip())
                return {
                    'ai_extracted_hashtags': json.dumps(parsed.get('hashtags', [])),
                    'ai_context': parsed.get('context', ''),
                    'main_topics': json.dumps(parsed.get('main_topics', []))
                }
            except:
                # Fallback if JSON parsing fails
                return {
                    'ai_extracted_hashtags': '[]',
                    'ai_context': result[:500],
                    'main_topics': '[]'
                }
                
        except Exception as e:
            print(f"❌ Context extraction failed: {e}")
            return {'ai_extracted_hashtags': '[]', 'ai_context': 'Analysis failed'}
    
    async def generate_detailed_summary(self, transcript: str, metadata: Dict, context: Dict) -> Dict:
        """Generate detailed summary using premium LLM."""
        if not transcript:
            return {'ai_detailed_summary': 'No transcript available', 'ai_key_insights': '[]'}
        
        prompt = f"""
        Create a comprehensive analysis of this video:

        Video Title: {metadata.get('title', 'Unknown')}
        Context: {context.get('ai_context', '')}
        Duration: {metadata.get('duration_seconds', 0)} seconds
        
        Full Transcript: {transcript}

        Provide:
        1. DETAILED SUMMARY: Comprehensive summary covering all major points
        2. KEY INSIGHTS: 5-7 specific insights or takeaways
        3. TECHNICAL COMPLEXITY: Rate 1-10 (1=basic, 10=expert level)
        4. ACTION ITEMS: Practical steps viewers could take

        Respond in JSON format:
        {{
            "detailed_summary": "Comprehensive summary...",
            "key_insights": ["insight1", "insight2", ...],
            "technical_complexity": 5,
            "action_items": ["action1", "action2", ...]
        }}
        """
        
        try:
            # Use premium LLM (Claude or GPT-4)
            if self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text
            elif self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=2000
                )
                result = response.choices[0].message.content
            else:
                return {'ai_detailed_summary': 'No premium LLM available', 'ai_key_insights': '[]'}
            
            # Parse response
            try:
                parsed = json.loads(result.strip('```json').strip('```').strip())
                return {
                    'ai_detailed_summary': parsed.get('detailed_summary', result[:1000]),
                    'ai_key_insights': json.dumps(parsed.get('key_insights', [])),
                    'technical_complexity': parsed.get('technical_complexity', 5),
                    'action_items': json.dumps(parsed.get('action_items', []))
                }
            except:
                return {
                    'ai_detailed_summary': result[:1000],
                    'ai_key_insights': '[]',
                    'technical_complexity': 5,
                    'action_items': '[]'
                }
                
        except Exception as e:
            print(f"❌ Detailed summary failed: {e}")
            return {'ai_detailed_summary': 'Summary generation failed', 'ai_key_insights': '[]'}
    
    async def generate_integration_prompt(self, transcript: str, metadata: Dict, analysis: Dict) -> str:
        """Generate integration prompt explaining what you'd get from this video."""
        prompt = f"""
        Based on this video analysis, create an integration prompt that explains:

        1. What specific knowledge/skills this video provides
        2. How it could improve the user's system/workflow
        3. What improvements would come from integrating this content
        4. Specific benefits and use cases

        Video: {metadata.get('title', 'Unknown')}
        Context: {analysis.get('ai_context', '')}
        Key Insights: {analysis.get('ai_key_insights', '[]')}

        Write a compelling integration prompt that tells the user exactly what they'd gain.
        """
        
        try:
            if self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            elif self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            else:
                return "Integration analysis not available - no LLM configured"
                
        except Exception as e:
            print(f"❌ Integration prompt generation failed: {e}")
            return "Integration prompt generation failed"
    
    async def calculate_content_scores(self, transcript: str, metadata: Dict, analysis: Dict) -> Dict:
        """Calculate quality and relevance scores."""
        try:
            quality_factors = []
            
            # Length factor
            duration = metadata.get('duration_seconds', 0)
            if duration > 300:  # >5 min
                quality_factors.append(0.8)
            elif duration > 60:  # >1 min
                quality_factors.append(0.6)
            else:
                quality_factors.append(0.3)
            
            # Engagement factor
            views = metadata.get('view_count', 0)
            likes = metadata.get('like_count', 0)
            if views > 0 and likes > 0:
                engagement = likes / views
                quality_factors.append(min(engagement * 100, 1.0))
            
            # Content depth (based on transcript length)
            if len(transcript) > 5000:
                quality_factors.append(0.9)
            elif len(transcript) > 1000:
                quality_factors.append(0.7)
            else:
                quality_factors.append(0.4)
            
            quality_score = sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
            
            # Relevance score (simplified - could be enhanced with user preferences)
            relevance_score = 0.7  # Default moderate relevance
            
            return {
                'quality_score': round(quality_score, 2),
                'relevance_score': relevance_score
            }
            
        except Exception as e:
            print(f"❌ Score calculation failed: {e}")
            return {'quality_score': 0.5, 'relevance_score': 0.5}
    
    async def store_enhanced_video(self, metadata: Dict, transcript: str, analysis: Dict, channel: Dict, agent_id: str):
        """Store all enhanced video data in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prepare insert data
            insert_data = {
                'name': metadata.get('title'),
                'url': f"https://www.youtube.com/watch?v={metadata.get('video_id')}",
                'video_id': metadata.get('video_id'),
                'type': 'YouTube',
                'channel': channel.get('name'),
                'transcript': transcript,
                'description': metadata.get('description'),
                'tags': metadata.get('tags'),
                'hashtags': metadata.get('hashtags'),
                'duration_seconds': metadata.get('duration_seconds'),
                'view_count': metadata.get('view_count'),
                'like_count': metadata.get('like_count'),
                'comment_count': metadata.get('comment_count'),
                'upload_date': metadata.get('upload_date'),
                'published_at': metadata.get('published_at'),
                'uploader': metadata.get('uploader'),
                'uploader_id': metadata.get('uploader_id'),
                'thumbnail_url': metadata.get('thumbnail_url'),
                'language': metadata.get('language'),
                'category_id': metadata.get('category_id'),
                'chapters': metadata.get('chapters'),
                'automatic_captions': metadata.get('automatic_captions'),
                'subtitles': metadata.get('subtitles'),
                'ai_extracted_hashtags': analysis.get('ai_extracted_hashtags'),
                'ai_context': analysis.get('ai_context'),
                'ai_detailed_summary': analysis.get('ai_detailed_summary'),
                'ai_key_insights': analysis.get('ai_key_insights'),
                'integration_prompt': analysis.get('integration_prompt'),
                'technical_complexity': analysis.get('technical_complexity'),
                'quality_score': analysis.get('quality_score'),
                'relevance_score': analysis.get('relevance_score'),
                'processing_agent': agent_id,
                'processing_status': 'Completed',
                'auto_check_enabled': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Check if video already exists
            cursor.execute("SELECT id FROM knowledge_hub WHERE video_id = ?", (metadata.get('video_id'),))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                set_clause = ', '.join([f"{k} = ?" for k in insert_data.keys()])
                cursor.execute(f"UPDATE knowledge_hub SET {set_clause} WHERE video_id = ?", 
                             list(insert_data.values()) + [metadata.get('video_id')])
                print(f"📝 Updated existing video: {metadata.get('title', 'Unknown')[:50]}...")
            else:
                # Insert new
                columns = ', '.join(insert_data.keys())
                placeholders = ', '.join(['?' for _ in insert_data])
                cursor.execute(f"INSERT INTO knowledge_hub ({columns}) VALUES ({placeholders})", 
                             list(insert_data.values()))
                print(f"➕ Added new video: {metadata.get('title', 'Unknown')[:50]}...")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Database storage failed: {e}")
            traceback.print_exc()
    
    async def get_marked_channels(self) -> List[Dict]:
        """Get channels marked for processing."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, url, channel_id 
                FROM youtube_channels 
                WHERE process_channel = 1
            """)
            
            channels = []
            for row in cursor.fetchall():
                channels.append({
                    'id': row[0],
                    'name': row[1],
                    'url': row[2],
                    'channel_id': row[3]
                })
            
            conn.close()
            return channels
            
        except Exception as e:
            print(f"❌ Error getting marked channels: {e}")
            return []
    
    async def is_video_processed(self, video_id: str) -> bool:
        """Check if video is already processed."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM knowledge_hub WHERE video_id = ?", (video_id,))
            result = cursor.fetchone()
            
            conn.close()
            return result is not None
            
        except Exception as e:
            print(f"❌ Error checking video: {e}")
            return False
    
    async def update_processed_channels(self, channels: List[Dict]):
        """Update processed channels."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for channel in channels:
                cursor.execute("""
                    UPDATE youtube_channels 
                    SET process_channel = 0, 
                        last_processed = datetime('now'),
                        updated_at = datetime('now')
                    WHERE id = ?
                """, (channel['id'],))
            
            conn.commit()
            conn.close()
            print(f"✅ Updated {len(channels)} processed channels")
            
        except Exception as e:
            print(f"❌ Error updating channels: {e}")
    
    async def auto_check_new_videos(self):
        """Auto-check for new videos on enabled channels."""
        print("🔄 Auto-checking for new videos...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get channels with auto-check enabled
            cursor.execute("""
                SELECT DISTINCT uploader_id, uploader 
                FROM knowledge_hub 
                WHERE auto_check_enabled = 1
                AND (last_auto_check IS NULL OR 
                     datetime(last_auto_check) < datetime('now', '-1 hour'))
            """)
            
            auto_channels = cursor.fetchall()
            conn.close()
            
            if auto_channels:
                print(f"🔍 Auto-checking {len(auto_channels)} channels for new videos")
                
                for uploader_id, uploader_name in auto_channels:
                    await self.check_channel_for_new_videos(uploader_id, uploader_name)
            else:
                print("📺 No channels need auto-checking")
                
        except Exception as e:
            print(f"❌ Auto-check failed: {e}")
    
    async def check_channel_for_new_videos(self, uploader_id: str, uploader_name: str):
        """Check specific channel for new videos."""
        try:
            channel_url = f"https://www.youtube.com/channel/{uploader_id}"
            
            # Get latest videos
            recent_videos = await self.get_channel_videos_detailed(channel_url)
            
            # Check which are new
            new_videos = []
            for video in recent_videos[:5]:  # Check last 5 videos
                if not await self.is_video_processed(video.get('id')):
                    new_videos.append(video)
            
            if new_videos:
                print(f"🆕 Found {len(new_videos)} new videos in {uploader_name}")
                
                # Process new videos
                for video in new_videos:
                    channel_info = {'name': uploader_name, 'id': uploader_id}
                    await self.process_video_enhanced(video, channel_info, "AutoCheck")
            else:
                print(f"✅ No new videos in {uploader_name}")
            
            # Update last check time
            await self.update_auto_check_time(uploader_id)
            
        except Exception as e:
            print(f"❌ New video check failed for {uploader_name}: {e}")
    
    async def update_auto_check_time(self, uploader_id: str):
        """Update last auto-check time."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE knowledge_hub 
                SET last_auto_check = datetime('now')
                WHERE uploader_id = ?
            """, (uploader_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error updating auto-check time: {e}")

async def main():
    """Main function to run enhanced video processing."""
    print("🚀 Enhanced Video Processor Starting")
    print("=" * 70)
    
    processor = EnhancedVideoProcessor()
    
    try:
        # Process all marked channels
        await processor.process_all_channels()
        
        # Auto-check for new videos
        await processor.auto_check_new_videos()
        
        print("\\n✅ Enhanced video processing complete!")
        
    except KeyboardInterrupt:
        print("\\n🛑 Processing stopped by user")
    except Exception as e:
        print(f"\\n❌ Processing failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())