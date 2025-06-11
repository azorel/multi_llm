#!/usr/bin/env python3
"""
YouTube Video Discovery Agent
============================

Discovers all videos from YouTube channels and manages the processing pipeline.
Part of the multi-agent YouTube processing system.
"""

import asyncio
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from loguru import logger

from ..agents.agent_base import AgentBase
from ..core.shared_memory import SharedMemory


class YouTubeVideoDiscoveryAgent(AgentBase):
    """
    Agent responsible for discovering videos from YouTube channels.
    
    Features:
    - Resolves channel IDs from various URL formats
# DEMO CODE REMOVED: - Fetches ALL videos from channels (not just samples)
    - Uses multiple methods: YouTube API, RSS feeds, yt-dlp
    - Manages video processing queue
    - Handles API quotas with fallback methods
    """
    
    def __init__(self, agent_id: str, shared_memory: SharedMemory):
        super().__init__(agent_id, shared_memory)
        self.name = "YouTube Video Discovery"
        self.description = "Discovers and queues videos from YouTube channels"
        
        # API configuration
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
# NOTION_REMOVED:         self.knowledge_db_id = os.getenv('NOTION_KNOWLEDGE_DATABASE_ID', '20bec31c-9de2-814e-80db-d13d0c27d869')
        
        self.headers = {
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Discovery settings
# DEMO CODE REMOVED: self.max_videos_per_channel = 500  # Get ALL videos, not samples
        self.batch_size = 50  # Process in batches
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute video discovery task."""
        try:
            channel = task.get('channel', {})
            logger.info(f"🔍 Discovering videos for channel: {channel.get('name', 'Unknown')}")
            
            # Resolve channel ID if needed
            channel_id = await self._resolve_channel_id(channel)
            if not channel_id:
                logger.error(f"Could not resolve channel ID for: {channel.get('url')}")
                return {
                    "status": "error",
                    "error": "Channel ID resolution failed"
                }
            
            # Update channel with resolved ID
            channel['channel_id'] = channel_id
            
            # Discover videos using multiple methods
            videos = await self._discover_all_videos(channel_id, channel.get('name', 'Unknown'))
            
            if not videos:
                logger.warning(f"No videos found for channel: {channel.get('name')}")
                return {
                    "status": "success",
                    "videos_found": 0,
                    "new_videos": 0
                }
            
            logger.info(f"📹 Found {len(videos)} total videos for {channel.get('name')}")
            
            # Check which videos are new
            new_videos = await self._filter_new_videos(videos)
            logger.info(f"🆕 {len(new_videos)} new videos to process")
            
            # Queue videos for processing
            queued_count = 0
            for i in range(0, len(new_videos), self.batch_size):
                batch = new_videos[i:i + self.batch_size]
                
                for video in batch:
                    # Create processing task
                    processing_task = {
                        "type": "process_video",
                        "video": video,
                        "channel": channel,
                        "triggered_by": self.agent_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Queue for transcript extraction
                    await self.shared_memory.set(
                        f"youtube_transcript_{video['video_id']}", 
                        processing_task
                    )
                    
                    queued_count += 1
                
                # Small delay between batches
                await asyncio.sleep(1)
            
            # Log discovery completion
            await self.log_event(
                "video_discovery_complete",
                {
                    "channel_name": channel.get('name'),
                    "channel_id": channel_id,
                    "total_videos": len(videos),
                    "new_videos": len(new_videos),
                    "queued_for_processing": queued_count
                }
            )
            
            return {
                "status": "success",
                "channel_id": channel_id,
                "videos_found": len(videos),
                "new_videos": len(new_videos),
                "queued_count": queued_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in video discovery: {e}")
            await self.log_error("video_discovery_error", str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _resolve_channel_id(self, channel: Dict[str, Any]) -> Optional[str]:
        """Resolve channel ID from URL or use existing ID."""
        # If we already have a channel ID, validate and use it
        if channel.get('channel_id'):
            channel_id = channel['channel_id']
            if channel_id.startswith('UC') and len(channel_id) == 24:
                return channel_id
        
        # Try to extract from URL
        if channel.get('url'):
            return await self._extract_channel_id_from_url(channel['url'])
        
        return None
    
    async def _extract_channel_id_from_url(self, url: str) -> Optional[str]:
        """Extract channel ID from various YouTube URL formats."""
        # Direct channel ID format
        channel_id_match = re.search(r'youtube\.com/channel/([a-zA-Z0-9_-]+)', url)
        if channel_id_match:
            return channel_id_match.group(1)
        
        # Handle @username, /c/, /user/ formats
        patterns = [
            (r'youtube\.com/@([a-zA-Z0-9_.-]+)', 'handle'),
            (r'youtube\.com/c/([a-zA-Z0-9_.-]+)', 'custom'),
            (r'youtube\.com/user/([a-zA-Z0-9_.-]+)', 'user')
        ]
        
        for pattern, url_type in patterns:
            match = re.search(pattern, url)
            if match:
                identifier = match.group(1)
                # Resolve to channel ID
                return await self._resolve_identifier_to_channel_id(identifier, url_type, url)
        
        logger.warning(f"Could not extract channel identifier from URL: {url}")
        return None
    
    async def _resolve_identifier_to_channel_id(self, identifier: str, url_type: str, original_url: str) -> Optional[str]:
        """Resolve username/handle to channel ID using multiple methods."""
        logger.info(f"🔍 Resolving {url_type} '{identifier}' to channel ID...")
        
        # Method 1: YouTube API (if available)
        if self.google_api_key:
            channel_id = await self._resolve_via_youtube_api(identifier, url_type)
            if channel_id:
                return channel_id
        
        # Method 2: Web scraping
        channel_id = await self._resolve_via_web_scraping(original_url)
        if channel_id:
            return channel_id
        
        # Method 3: RSS feed probe
        channel_id = await self._resolve_via_rss_probe(identifier)
        if channel_id:
            return channel_id
        
        logger.error(f"Failed to resolve {url_type} '{identifier}' to channel ID")
        return None
    
    async def _resolve_via_youtube_api(self, identifier: str, url_type: str) -> Optional[str]:
        """Resolve using YouTube Data API."""
        try:
            import aiohttp
            
            # Different API approaches based on URL type
            if url_type == 'user':
                # Try forUsername endpoint
                params = {
                    'part': 'id',
                    'forUsername': identifier,
                    'key': self.google_api_key
                }
                url = 'https://www.googleapis.com/youtube/v3/channels'
            else:
                # Use search for handles and custom URLs
                params = {
                    'part': 'snippet',
                    'q': identifier,
                    'type': 'channel',
                    'maxResults': 10,
                    'key': self.google_api_key
                }
                url = 'https://www.googleapis.com/youtube/v3/search'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if url_type == 'user' and data.get('items'):
                            return data['items'][0]['id']
                        elif data.get('items'):
                            # Search through results for best match
                            for item in data['items']:
                                snippet = item.get('snippet', {})
                                channel_id = item.get('id', {}).get('channelId') or item.get('snippet', {}).get('channelId')
                                
                                # Check various matching criteria
                                custom_url = snippet.get('customUrl', '').lower().replace('@', '')
                                title_lower = snippet.get('title', '').lower()
                                identifier_lower = identifier.lower()
                                
                                if (custom_url == identifier_lower or 
                                    identifier_lower in title_lower or
                                    title_lower in identifier_lower):
                                    logger.info(f"✅ Found channel via API: {snippet.get('title')} -> {channel_id}")
                                    return channel_id
                    
                    elif response.status == 403:
                        logger.warning("YouTube API quota exceeded")
                        
        except Exception as e:
            logger.debug(f"YouTube API resolution failed: {e}")
        
        return None
    
    async def _resolve_via_web_scraping(self, url: str) -> Optional[str]:
        """Scrape channel ID from YouTube page."""
        try:
            import aiohttp
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Look for channel ID patterns
                        patterns = [
                            r'"channelId":"(UC[a-zA-Z0-9_-]{22})"',
                            r'"externalId":"(UC[a-zA-Z0-9_-]{22})"',
                            r'<meta itemprop="channelId" content="(UC[a-zA-Z0-9_-]{22})">',
                            r'"browseId":"(UC[a-zA-Z0-9_-]{22})"'
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, html)
                            if matches:
                                channel_id = matches[0]
                                logger.info(f"✅ Found channel ID via scraping: {channel_id}")
                                return channel_id
                                
        except Exception as e:
            logger.debug(f"Web scraping failed: {e}")
        
        return None
    
    async def _resolve_via_rss_probe(self, identifier: str) -> Optional[str]:
        """Try common channel ID patterns with RSS feed."""
        # This is a last resort - try common patterns
        # YouTube channel IDs always start with UC
        return None  # Not implementing guessing
    
    async def _discover_all_videos(self, channel_id: str, channel_name: str) -> List[Dict[str, Any]]:
        """Discover ALL videos from channel using multiple methods."""
        videos = []
        
        # Method 1: YouTube API (if quota available)
        if self.google_api_key:
            api_videos = await self._get_videos_via_api(channel_id)
            if api_videos:
                logger.info(f"✅ Found {len(api_videos)} videos via YouTube API")
                videos.extend(api_videos)
                if len(api_videos) >= self.max_videos_per_channel:
                    return videos[:self.max_videos_per_channel]
        
        # Method 2: RSS Feed (recent videos)
        if not videos:  # Only if API failed
            rss_videos = await self._get_videos_via_rss(channel_id)
            if rss_videos:
                logger.info(f"✅ Found {len(rss_videos)} videos via RSS feed")
                videos.extend(rss_videos)
        
        # Method 3: yt-dlp (comprehensive but slower)
        if len(videos) < 50:  # If we got very few videos
            ytdlp_videos = await self._get_videos_via_ytdlp(channel_id)
            if ytdlp_videos:
                logger.info(f"✅ Found {len(ytdlp_videos)} videos via yt-dlp")
                # Merge with existing, avoiding duplicates
                existing_ids = {v['video_id'] for v in videos}
                for video in ytdlp_videos:
                    if video['video_id'] not in existing_ids:
                        videos.append(video)
        
        # Deduplicate and sort by date (newest first)
        seen_ids = set()
        unique_videos = []
        for video in videos:
            if video['video_id'] not in seen_ids:
                seen_ids.add(video['video_id'])
                unique_videos.append(video)
        
        # Sort by published date
        unique_videos.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        return unique_videos[:self.max_videos_per_channel]
    
    async def _get_videos_via_api(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get videos using YouTube Data API."""
        try:
            import aiohttp
            
            # First get the uploads playlist ID
            params = {
                'part': 'contentDetails',
                'id': channel_id,
                'key': self.google_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://www.googleapis.com/youtube/v3/channels',
                    params=params,
                    timeout=10
                ) as response:
                    if response.status != 200:
                        return []
                    
                    data = await response.json()
                    if not data.get('items'):
                        return []
                    
                    uploads_playlist_id = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get all videos from uploads playlist
            videos = []
            next_page_token = None
            
            while len(videos) < self.max_videos_per_channel:
                params = {
                    'part': 'snippet,contentDetails',
                    'playlistId': uploads_playlist_id,
                    'maxResults': min(50, self.max_videos_per_channel - len(videos)),
                    'key': self.google_api_key
                }
                
                if next_page_token:
                    params['pageToken'] = next_page_token
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        'https://www.googleapis.com/youtube/v3/playlistItems',
                        params=params,
                        timeout=10
                    ) as response:
                        if response.status != 200:
                            break
                        
                        data = await response.json()
                        
                        for item in data.get('items', []):
                            snippet = item['snippet']
                            video_id = snippet['resourceId']['videoId']
                            
                            video_data = {
                                'video_id': video_id,
                                'title': snippet['title'],
                                'url': f"https://www.youtube.com/watch?v={video_id}",
                                'published_at': snippet['publishedAt'],
                                'description': snippet.get('description', '')[:500],
                                'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                                'channel_title': snippet['channelTitle']
                            }
                            
                            videos.append(video_data)
                        
                        next_page_token = data.get('nextPageToken')
                        if not next_page_token:
                            break
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
            
            return videos
            
        except Exception as e:
            logger.error(f"YouTube API error: {e}")
            return []
    
    async def _get_videos_via_rss(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get recent videos from RSS feed."""
        try:
            import aiohttp
            import xml.etree.ElementTree as ET
            
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
                'yt': 'http://www.youtube.com/xml/schemas/2015',
                'media': 'http://search.yahoo.com/mrss/'
            }
            
            videos = []
            entries = root.findall('atom:entry', ns)
            
            for entry in entries[:self.max_videos_per_channel]:
                video_id = entry.find('yt:videoId', ns)
                title = entry.find('atom:title', ns)
                published = entry.find('atom:published', ns)
                author = entry.find('atom:author/atom:name', ns)
                
                if video_id is not None and title is not None:
                    video_data = {
                        'video_id': video_id.text,
                        'title': title.text,
                        'url': f"https://www.youtube.com/watch?v={video_id.text}",
                        'published_at': published.text if published is not None else '',
                        'description': '',  # RSS doesn't include full description
                        'thumbnail': f"https://i.ytimg.com/vi/{video_id.text}/mqdefault.jpg",
                        'channel_title': author.text if author is not None else ''
                    }
                    
                    videos.append(video_data)
            
            return videos
            
        except Exception as e:
            logger.error(f"RSS feed error: {e}")
            return []
    
    async def _get_videos_via_ytdlp(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get videos using yt-dlp as fallback."""
        try:
            import yt_dlp
            
            channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlistend': self.max_videos_per_channel
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                
                if not info or 'entries' not in info:
                    return []
                
                videos = []
                for entry in info['entries']:
                    if entry and entry.get('id'):
                        video_data = {
                            'video_id': entry['id'],
                            'title': entry.get('title', 'Unknown Title'),
                            'url': f"https://www.youtube.com/watch?v={entry['id']}",
                            'published_at': entry.get('upload_date', ''),
                            'description': entry.get('description', '')[:500] if entry.get('description') else '',
                            'thumbnail': entry.get('thumbnail', ''),
                            'channel_title': entry.get('uploader', '')
                        }
                        
                        videos.append(video_data)
                
                return videos
                
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            return []
    
    async def _filter_new_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter videos to only include those not already in Knowledge Hub."""
        try:
            import aiohttp
            
            new_videos = []
            
            # Check videos in batches
            for i in range(0, len(videos), 50):
                batch = videos[i:i + 50]
                video_urls = [v['url'] for v in batch]
                
                # Query Knowledge Hub for existing videos
                filter_conditions = []
                for url in video_urls:
                    filter_conditions.append({
                        "property": "URL",
                        "url": {"equals": url}
                    })
                
                query_data = {
                    "filter": {
                        "or": filter_conditions
                    },
                    "page_size": 100
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        headers=self.headers,
                        json=query_data,
                        timeout=15
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            existing_urls = set()
                            
                            for page in data.get('results', []):
                                url_prop = page.get('properties', {}).get('URL', {})
                                if url_prop.get('url'):
                                    existing_urls.add(url_prop['url'])
                            
                            # Add videos not in existing set
                            for video in batch:
                                if video['url'] not in existing_urls:
                                    new_videos.append(video)
                        else:
                            # If query fails, assume all are new
                            new_videos.extend(batch)
                
                # Small delay between batches
                await asyncio.sleep(0.5)
            
            return new_videos
            
        except Exception as e:
            logger.error(f"Error filtering new videos: {e}")
            # On error, return all videos to be safe
            return videos
    
    async def continuous_discovery(self):
        """Run continuous discovery loop."""
        logger.info("🚀 Starting continuous video discovery")
        
        while self.is_running:
            try:
                # Check for discovery tasks
                discovery_keys = await self.shared_memory.list_keys("youtube_discovery_*")
                
                for key in discovery_keys:
                    task = await self.shared_memory.get(key)
                    if task:
                        # Process the discovery task
                        result = await self.execute(task)
                        
                        # Store result for channel monitor
                        completion_data = {
                            "channel_id": task['channel']['id'],
                            "channel_name": task['channel']['name'],
                            "manual_process": task['channel'].get('manual_process', False),
                            "stats": {
                                "total_videos": result.get('videos_found', 0),
                                "new_videos": result.get('new_videos', 0),
                                "imported_videos": result.get('queued_count', 0)
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await self.shared_memory.set(
                            f"youtube_complete_{task['channel']['id']}", 
                            completion_data
                        )
                        
                        # Clear the discovery task
                        await self.shared_memory.delete(key)
                
                # Brief pause
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}")
                await asyncio.sleep(10)


def create_youtube_video_discovery_agent(agent_id: str, shared_memory: SharedMemory) -> YouTubeVideoDiscoveryAgent:
    """Factory function to create YouTube video discovery agent."""
    return YouTubeVideoDiscoveryAgent(agent_id, shared_memory)