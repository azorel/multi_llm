#!/usr/bin/env python3
"""
YouTube Channel Processor Module
===============================

Integrated module for processing YouTube channels marked for processing
in the LifeOS YouTube Channels database.
"""

import os
import asyncio
import requests
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

# YouTube transcript extraction
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    TRANSCRIPT_AVAILABLE = True
except ImportError:
    TRANSCRIPT_AVAILABLE = False
    logger.warning("youtube_transcript_api not available - install with: pip install youtube_transcript_api")

# Import the channel database view manager
try:
    from ..integrations.channel_database_view_manager import ChannelDatabaseViewManager
    DATABASE_VIEW_MANAGER_AVAILABLE = True
except ImportError:
    DATABASE_VIEW_MANAGER_AVAILABLE = False
    logger.warning("Channel database view manager not available")


class YouTubeChannelProcessor:
    """
    Processes YouTube channels based on database checkboxes.
    
    Features:
    - Monitors "Process Channel" checkbox triggers
    - Processes all videos from marked channels
    - Updates processing status and timestamps
    - Integrates with existing YouTube processing pipeline
    """
    
        """Initialize the YouTube channel processor."""
        self.config = config or {}
        
        # Get database IDs from config or environment
        self.channels_db_id = (
            self.config.get("api", {}).get("notion", {}).get("channels_database_id") or
            self.config.get("notion", {}).get("channels_database_id") or
            os.getenv("NOTION_CHANNELS_DATABASE_ID")
        )
        self.knowledge_db_id = (
            self.config.get("api", {}).get("notion", {}).get("knowledge_database_id") or
            self.config.get("notion", {}).get("knowledge_database_id") or
            os.getenv("NOTION_KNOWLEDGE_DATABASE_ID")
        )
        
        self.headers = {
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # YouTube API configuration
        self.google_api_key = (
            self.config.get("api", {}).get("google", {}).get("api_key") or
            os.getenv("GOOGLE_API_KEY")
        )
        
        # Initialize database view manager
        self.view_manager = None
        if DATABASE_VIEW_MANAGER_AVAILABLE:
            try:
                logger.info("Database view manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize database view manager: {e}")
        
        logger.info("YouTube Channel Processor initialized")
    
    async def get_channels_to_process(self) -> List[Dict[str, Any]]:
        """Get channels marked for processing."""
        if not self.channels_db_id:
            logger.warning("No channels database ID configured")
            return []
        
        try:
            query_data = {
                "filter": {
                    "property": "Process Channel",
                    "checkbox": {
                        "equals": True
                    }
                }
            }
            
            response = requests.post(
                headers=self.headers,
                json=query_data,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to query channels: {response.status_code}")
                return []
            
            results = response.json().get('results', [])
            
            channels = []
            for page in results:
                props = page['properties']
                
                channel_data = {
                    'page_id': page['id'],
                    'name': '',
                    'url': '',
                    'channel_id': '',
                    'hashtags': []
                }
                
                # Extract channel information
                if props.get('Name', {}).get('title'):
                    channel_data['name'] = props['Name']['title'][0]['plain_text']
                
                if props.get('URL', {}).get('rich_text'):
                    channel_data['url'] = props['URL']['rich_text'][0]['plain_text']
                
                # Extract channel ID from URL or use Channel field as fallback
                if channel_data['url']:
                    channel_data['channel_id'] = self.extract_channel_id_from_url(channel_data['url'])
                
                # Fallback to Channel field if URL extraction failed
                if not channel_data['channel_id'] and props.get('Channel', {}).get('rich_text'):
                    channel_data['channel_id'] = props['Channel']['rich_text'][0]['plain_text']
                
                if props.get('Hashtags', {}).get('select'):
                    channel_data['hashtags'] = [props['Hashtags']['select']['name']]
                
                channels.append(channel_data)
            
            logger.info(f"Found {len(channels)} channels to process")
            return channels
            
        except Exception as e:
            logger.error(f"Error getting channels to process: {e}")
            return []
    
    def extract_channel_id_from_url(self, url: str) -> Optional[str]:
        """Extract channel ID from various YouTube URL formats."""
        if not url:
            return None
        
        import re
        
        # Direct channel ID format
        channel_id_match = re.search(r'youtube\.com/channel/([a-zA-Z0-9_-]+)', url)
        if channel_id_match:
            return channel_id_match.group(1)
        
        # Handle @username format - need to resolve to channel ID
        username_match = re.search(r'youtube\.com/@([a-zA-Z0-9_.-]+)', url)
        if username_match:
            username = username_match.group(1)
            return self.resolve_username_to_channel_id(username)
        
        # Handle /c/ format
        c_format_match = re.search(r'youtube\.com/c/([a-zA-Z0-9_.-]+)', url)
        if c_format_match:
            username = c_format_match.group(1)
            return self.resolve_username_to_channel_id(username)
        
        # Handle /user/ format
        user_format_match = re.search(r'youtube\.com/user/([a-zA-Z0-9_.-]+)', url)
        if user_format_match:
            username = user_format_match.group(1)
            return self.resolve_username_to_channel_id(username)
        
        logger.warning(f"Could not extract channel ID from URL: {url}")
        return None
    
    def resolve_username_to_channel_id(self, username: str) -> Optional[str]:
        """Resolve a YouTube username/handle to channel ID using multiple methods."""
        logger.info(f"🔍 Resolving username '{username}' to channel ID...")
        
        # Method 1: Try web scraping first (most reliable for @usernames)
        logger.info("📱 Trying web scraping method...")
        scraped_id = self._scrape_channel_id_from_page(username)
        if scraped_id:
            logger.info(f"✅ Web scraping found channel ID: {scraped_id}")
            return scraped_id
        
        # Method 2: Try YouTube API if we have a key
        if not self.google_api_key:
            logger.warning("No Google API key - skipping API method")
            return None
        
        try:
            import googleapiclient.discovery
            
            youtube = googleapiclient.discovery.build(
                "youtube", "v3", developerKey=self.google_api_key
            )
            
            logger.info("🔍 Trying YouTube API search...")
            
            # Try multiple search strategies
            search_terms = [
                username,  # Original username
                username.replace('FW', ''),  # Remove common suffixes
                username.replace('_', ' '),  # Replace underscores with spaces
                username.replace('BJones', 'B Jones'),  # Handle name patterns
                username.replace('Jones', ''),  # Try without last name
                f'"{username}"',  # Exact match in quotes
                f"Nate Jones",  # Convert username to likely real name
                f"Nathan Jones",  # Full name variant
                f"Jameson Nathan Jones",  # Based on the video we saw processing
            ]
            
            best_match = None
            best_subscribers = 0
            
            for search_term in search_terms:
                try:
                    search_response = youtube.search().list(
                        part="snippet",
                        q=search_term,
                        type="channel",
                        maxResults=10
                    ).execute()
                    
                    for item in search_response.get('items', []):
                        snippet = item['snippet']
                        channel_title = snippet['title'].lower()
                        channel_custom_url = snippet.get('customUrl', '').lower().replace('@', '')
                        
                        # Check for matches with more flexible criteria
                        username_lower = username.lower()
                        channel_title_lower = channel_title.lower()
                        
                        # Extract components for better matching
                        username_parts = username_lower.replace('bjones', ' b jones').replace('_', ' ').split()
                        channel_parts = channel_title_lower.split()
                        
                        # Match conditions
                        exact_match = username_lower == channel_title_lower
                        contains_match = username_lower in channel_title_lower or channel_title_lower in username_lower
                        url_match = username_lower == channel_custom_url or f"@{username_lower}" == snippet.get('customUrl', '').lower()
                        part_match = any(part in channel_parts for part in username_parts if len(part) > 2)
                        name_match = ('nate' in channel_title_lower and 'jones' in channel_title_lower) if 'nate' in username_lower else False
                        
                        if (exact_match or contains_match or url_match or part_match or name_match):
                            logger.debug(f"Found potential match: '{snippet['title']}' for username '{username}'")
                            logger.debug(f"  Match types: exact={exact_match}, contains={contains_match}, url={url_match}, part={part_match}, name={name_match}")
                            
                            # Get subscriber count to pick the best match
                            try:
                                channel_details = youtube.channels().list(
                                    part="statistics",
                                    id=snippet['channelId']
                                ).execute()
                                
                                if channel_details['items']:
                                    subscriber_count = int(channel_details['items'][0]['statistics'].get('subscriberCount', 0))
                                    if subscriber_count > best_subscribers:
                                        best_match = snippet
                                        best_subscribers = subscriber_count
                                        logger.info(f"Found potential match: {snippet['title']} ({subscriber_count:,} subs)")
                            except:
                                if not best_match:
                                    best_match = snippet
                                    logger.info(f"Found potential match: {snippet['title']} (subscriber count unknown)")
                        
                except Exception as search_error:
                    logger.debug(f"Search with term '{search_term}' failed: {search_error}")
                    continue
            
            if best_match:
                logger.info(f"✅ Best match found: {best_match['title']} -> {best_match['channelId']} ({best_subscribers:,} subscribers)")
                return best_match['channelId']
            
            # Try legacy forUsername endpoint
            try:
                channels_response = youtube.channels().list(
                    part="id,snippet",
                    forUsername=username
                ).execute()
                
                if channels_response.get('items'):
                    channel_id = channels_response['items'][0]['id']
                    channel_title = channels_response['items'][0]['snippet']['title']
                    logger.info(f"✅ Found via forUsername: {channel_title} -> {channel_id}")
                    return channel_id
            except Exception as e:
                logger.debug(f"forUsername lookup failed: {e}")
            
            # Final attempt: Try web scraping for any username format
            logger.info("🕷️ Trying final web scraping attempt...")
            channel_id = self._scrape_channel_id_from_page(username)
            if channel_id:
                return channel_id
            
            # Ultimate fallback: log detailed error and suggest manual entry
            logger.error(f"❌ Could not resolve username '{username}' to channel ID after trying all methods:")
            logger.error(f"   1. Web scraping from https://www.youtube.com/@{username}")
            logger.error(f"   2. YouTube API search with {len(search_terms)} different terms")
            logger.error(f"   3. Legacy forUsername API")
            logger.error(f"💡 Solution: Manually add the channel ID to the 'Channel' field in Notion")
            logger.error(f"   - Visit https://www.youtube.com/@{username}")
            logger.error(f"   - Copy the channel ID (starts with UC) from the page source")
            logger.error(f"   - Paste it into the 'Channel' field in the YouTube Channels database")
            
            return None
            
        except Exception as e:
            logger.error(f"Error resolving username to channel ID: {e}")
            return None
    
    def _scrape_channel_id_from_page(self, username_or_url: str) -> Optional[str]:
        """Scrape channel ID directly from YouTube page as fallback."""
        try:
            import requests
            import re
            import time
            
            # Construct the URL if we just have a username
            if username_or_url.startswith('@'):
                url = f"https://www.youtube.com/{username_or_url}"
            elif 'youtube.com/@' in username_or_url:
                url = username_or_url
            else:
                url = f"https://www.youtube.com/@{username_or_url}"
            
            logger.info(f"🕷️ Scraping channel ID from: {url}")
            
            # Use multiple user agents and retry logic
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            
            for attempt, user_agent in enumerate(user_agents):
                try:
                    headers = {
                        'User-Agent': user_agent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                    
                    response = requests.get(url, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        html_content = response.text
                        logger.debug(f"📄 Fetched page content ({len(html_content)} chars)")
                        
                        # Look for channel ID patterns in the HTML with more comprehensive patterns
                        patterns = [
                            r'"channelId":"(UC[a-zA-Z0-9_-]{22})"',
                            r'"externalId":"(UC[a-zA-Z0-9_-]{22})"',
                            r'channel/(UC[a-zA-Z0-9_-]{22})',
                            r'"webCommandMetadata":{"url":"/channel/(UC[a-zA-Z0-9_-]{22})"',
                            r'"browseEndpoint":{"browseId":"(UC[a-zA-Z0-9_-]{22})"',
                            r'"channelMetadataRenderer":{"title":"[^"]+","description":"[^"]*","rssUrl":"[^"]*","externalId":"(UC[a-zA-Z0-9_-]{22})"',
                            r'{"channelId":"(UC[a-zA-Z0-9_-]{22})"',
                            r'"ucid":"(UC[a-zA-Z0-9_-]{22})"'
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, html_content)
                            if matches:
                                # Take the first valid match
                                for match in matches:
                                    if len(match) == 24 and match.startswith('UC'):
                                        logger.info(f"✅ Found channel ID via pattern matching: {match}")
                                        return match
                        
                        # If no patterns match, look for any UC ID in the content
                        uc_matches = re.findall(r'(UC[a-zA-Z0-9_-]{22})', html_content)
                        if uc_matches:
                            # Return the most common one (likely the channel ID)
                            from collections import Counter
                            most_common = Counter(uc_matches).most_common(1)
                            if most_common:
                                channel_id = most_common[0][0]
                                logger.info(f"✅ Found channel ID via frequency analysis: {channel_id}")
                                return channel_id
                        
                        logger.warning(f"No channel ID patterns found in page content (attempt {attempt + 1})")
                        
                    else:
                        logger.warning(f"HTTP {response.status_code} on attempt {attempt + 1}")
                        
                except requests.RequestException as e:
                    logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
                
                # Small delay between attempts
                if attempt < len(user_agents) - 1:
                    time.sleep(1)
            
            logger.warning(f"Could not scrape channel ID after {len(user_agents)} attempts")
            return None
            
        except Exception as e:
            logger.error(f"Error scraping channel ID: {e}")
            return None
    
    async def get_channel_metadata(self, channel_id: str) -> Dict[str, Any]:
        """Get detailed channel metadata from YouTube API."""
        if not self.google_api_key:
            logger.warning("No Google API key - cannot fetch channel metadata")
            return {}
        
        try:
            import googleapiclient.discovery
            
            youtube = googleapiclient.discovery.build(
                "youtube", "v3", developerKey=self.google_api_key
            )
            
            # Get channel details
            channels_response = youtube.channels().list(
                part="snippet,statistics,brandingSettings",
                id=channel_id
            ).execute()
            
            if not channels_response.get('items'):
                logger.warning(f"No channel found for ID: {channel_id}")
                return {}
            
            channel = channels_response['items'][0]
            snippet = channel['snippet']
            statistics = channel.get('statistics', {})
            branding = channel.get('brandingSettings', {})
            
            # Extract metadata
            metadata = {
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'custom_url': snippet.get('customUrl', ''),
                'published_at': snippet.get('publishedAt', ''),
                'thumbnail_url': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                'country': snippet.get('country', ''),
                'view_count': int(statistics.get('viewCount', 0)),
                'subscriber_count': int(statistics.get('subscriberCount', 0)),
                'video_count': int(statistics.get('videoCount', 0)),
                'keywords': branding.get('channel', {}).get('keywords', '').split(',') if branding.get('channel', {}).get('keywords') else [],
                'channel_id': channel_id
            }
            
            logger.info(f"✅ Retrieved metadata for channel: {metadata['title']} ({metadata['subscriber_count']:,} subscribers)")
            return metadata
            
        except Exception as e:
            logger.error(f"Error fetching channel metadata: {e}")
            return {}
    
    async def update_channel_fields(self, page_id: str, channel_metadata: Dict[str, Any]) -> bool:
        """Update empty channel fields with metadata from YouTube."""
        try:
            # First get current page data to check what fields are empty
            response = requests.get(
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get current page data: {response.status_code}")
                return False
            
            current_page = response.json()
            current_props = current_page.get('properties', {})
            
            # Prepare updates for empty fields only
            updates = {}
            
            # Update Name if empty
            if not current_props.get('Name', {}).get('title'):
                if channel_metadata.get('title'):
                    updates['Name'] = {
                        "title": [{"text": {"content": channel_metadata['title']}}]
                    }
                    logger.info(f"📝 Adding channel name: {channel_metadata['title']}")
            
            # Update Description if empty  
            if not current_props.get('Description', {}).get('rich_text'):
                if channel_metadata.get('description'):
                    # Truncate description to fit Notion limits
                    description = channel_metadata['description'][:1900] + "..." if len(channel_metadata['description']) > 1900 else channel_metadata['description']
                    updates['Description'] = {
                        "rich_text": [{"text": {"content": description}}]
                    }
                    logger.info(f"📄 Adding channel description ({len(description)} chars)")
            
            # Update Channel ID if empty
            if not current_props.get('Channel', {}).get('rich_text'):
                if channel_metadata.get('channel_id'):
                    updates['Channel'] = {
                        "rich_text": [{"text": {"content": channel_metadata['channel_id']}}]
                    }
                    logger.info(f"🆔 Adding channel ID: {channel_metadata['channel_id']}")
            
            # Update Subscriber Count if empty
            if not current_props.get('Subscribers', {}).get('number'):
                if channel_metadata.get('subscriber_count'):
                    updates['Subscribers'] = {
                        "number": channel_metadata['subscriber_count']
                    }
                    logger.info(f"👥 Adding subscriber count: {channel_metadata['subscriber_count']:,}")
            
            # Update Video Count if empty
            if not current_props.get('Videos', {}).get('number'):
                if channel_metadata.get('video_count'):
                    updates['Videos'] = {
                        "number": channel_metadata['video_count']
                    }
                    logger.info(f"📹 Adding video count: {channel_metadata['video_count']:,}")
            
            # Update Country if empty
            if not current_props.get('Country', {}).get('select'):
                if channel_metadata.get('country'):
                    updates['Country'] = {
                        "select": {"name": channel_metadata['country']}
                    }
                    logger.info(f"🌍 Adding country: {channel_metadata['country']}")
            
            # Update Hashtags if empty and we have keywords
            if not current_props.get('Hashtags', {}).get('multi_select'):
                keywords = channel_metadata.get('keywords', [])
                if keywords:
                    # Clean and limit keywords
                    clean_keywords = []
                    for keyword in keywords[:10]:  # Limit to 10
                        clean_keyword = keyword.strip().replace('#', '')
                        if clean_keyword and len(clean_keyword) < 100:  # Notion limit
                            clean_keywords.append(clean_keyword)
                    
                    if clean_keywords:
                        updates['Hashtags'] = {
                            "multi_select": [{"name": tag} for tag in clean_keywords]
                        }
                        logger.info(f"🏷️ Adding hashtags: {clean_keywords}")
            
            # Update Last Updated
            updates['Last Updated'] = {
                "date": {"start": datetime.now().isoformat()}
            }
            
            # Update Notes with metadata summary
            if not current_props.get('Notes', {}).get('rich_text'):
                notes = f"🤖 **AUTO-POPULATED CHANNEL INFO**\\n\\n"
                notes += f"📺 **{channel_metadata.get('title', 'Unknown Channel')}**\\n"
                notes += f"👥 Subscribers: {channel_metadata.get('subscriber_count', 0):,}\\n"
                notes += f"📹 Videos: {channel_metadata.get('video_count', 0):,}\\n"
                notes += f"📅 Created: {channel_metadata.get('published_at', 'Unknown')[:10]}\\n"
                if channel_metadata.get('country'):
                    notes += f"🌍 Country: {channel_metadata.get('country')}\\n"
                notes += f"\\n📄 **Description:**\\n{channel_metadata.get('description', 'No description available')[:500]}{'...' if len(channel_metadata.get('description', '')) > 500 else ''}\\n"
                notes += f"\\n🤖 **Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                updates['Notes'] = {
                    "rich_text": [{"text": {"content": notes}}]
                }
                logger.info(f"📝 Adding channel summary notes")
            
            # Apply updates if any
            if len(updates) > 1:  # More than just Last Updated
                update_response = requests.patch(
                    headers=self.headers,
                    json={"properties": updates},
                    timeout=15
                )
                
                if update_response.status_code == 200:
                    logger.info(f"✅ Updated {len(updates)} channel fields successfully")
                    return True
                else:
                    logger.error(f"Failed to update channel fields: {update_response.status_code}")
                    return False
            else:
                logger.info("ℹ️ All channel fields already populated, no updates needed")
                return True
                
        except Exception as e:
            logger.error(f"Error updating channel fields: {e}")
            return False
    
    async def get_channel_videos(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get all videos from a YouTube channel with fallback methods."""
        
        # Method 1: Try YouTube API first
        if self.google_api_key:
            try:
                import googleapiclient.discovery
                
                youtube = googleapiclient.discovery.build(
                    "youtube", "v3", developerKey=self.google_api_key
                )
                
                logger.info(f"🔍 Fetching videos via YouTube API for channel: {channel_id}")
                
                # Get channel's uploads playlist
                channels_response = youtube.channels().list(
                    part="contentDetails",
                    id=channel_id
                ).execute()
                
                if not channels_response['items']:
                    logger.error(f"Channel not found: {channel_id}")
                    return await self._get_channel_videos_fallback(channel_id)
                
                uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                
                # Get ALL videos from uploads playlist (no limit)
                videos = []
                next_page_token = None
                
                logger.info(f"🔄 Fetching ALL videos from channel {channel_id} (no limit)")
                
                while True:  # Continue until all videos are fetched
                    playlist_response = youtube.playlistItems().list(
                        part="snippet",
                        playlistId=uploads_playlist_id,
                        maxResults=50,  # Maximum per request (YouTube API limit)
                        pageToken=next_page_token
                    ).execute()
                    
                    # Get video IDs for duration lookup
                    video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_response['items']]
                    
                    # Get video details including duration
                    videos_details = youtube.videos().list(
                        part="contentDetails,snippet",
                        id=','.join(video_ids)
                    ).execute()
                    
                    # Create a mapping of video_id -> duration
                    duration_map = {}
                    for video_detail in videos_details['items']:
                        video_id = video_detail['id']
                        duration_iso = video_detail['contentDetails']['duration']
                        duration_seconds = self._parse_youtube_duration(duration_iso)
                        duration_map[video_id] = duration_seconds
                    
                    for item in playlist_response['items']:
                        snippet = item['snippet']
                        video_id = snippet['resourceId']['videoId']
                        
                        # Include all videos (shorts filter removed as requested)
                        duration_seconds = duration_map.get(video_id, 0)
                        
                        video_data = {
                            'title': snippet['title'],
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'video_id': video_id,
                            'published_date': snippet['publishedAt'],
                            'description': snippet.get('description', '')[:500],
                            'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                            'channel_title': snippet['channelTitle'],
                            'duration_seconds': duration_seconds,
                            'duration_formatted': self._format_duration(duration_seconds)
                        }
                        
                        videos.append(video_data)
                    
                    next_page_token = playlist_response.get('nextPageToken')
                    if not next_page_token:
                        break
                
                logger.info(f"✅ Found {len(videos)} videos via YouTube API (ALL videos from channel)")
                return videos
                
            except Exception as e:
                error_str = str(e)
                if "quota" in error_str.lower() or "403" in error_str:
                    logger.warning(f"🚫 YouTube API quota exceeded, using fallback method")
                    return await self._get_channel_videos_fallback(channel_id)
                else:
                    logger.error(f"YouTube API error: {e}")
                    return await self._get_channel_videos_fallback(channel_id)
        else:
            logger.warning("No Google API key - using fallback method")
            return await self._get_channel_videos_fallback(channel_id)
    
    async def _get_channel_videos_fallback(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get channel videos using yt-dlp as fallback when API is exhausted."""
        try:
            import yt_dlp
            import asyncio
            
            logger.info(f"🔄 Using yt-dlp fallback to fetch videos for channel: {channel_id}")
            
            # Configure yt-dlp for channel video listing
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Don't download, just get metadata
                # Remove playlistend limit to get ALL videos
            }
            
            channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
            
            def extract_videos():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(channel_url, download=False)
                        return info.get('entries', [])
                    except Exception as e:
                        logger.error(f"yt-dlp extraction failed: {e}")
                        return []
            
            # Run yt-dlp in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            entries = await loop.run_in_executor(None, extract_videos)
            
            if not entries:
                logger.warning(f"No videos found via yt-dlp for channel: {channel_id}")
                return []
            
            videos = []
            logger.info(f"🔄 Processing {len(entries)} video entries from yt-dlp (ALL videos)")
            
            for entry in entries:
                if not entry:
                    continue
                
                try:
                    # Extract basic info from yt-dlp flat extraction
                    video_id = entry.get('id', '')
                    title = entry.get('title', 'Unknown Title')
                    duration = entry.get('duration', 0)
                    
                    # Include all videos (shorts filter removed as requested)
                    
                    # Create video data structure
                    video_data = {
                        'title': title,
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'video_id': video_id,
                        'published_date': entry.get('upload_date', ''),
                        'description': entry.get('description', '')[:500] if entry.get('description') else '',
                        'thumbnail': entry.get('thumbnail', ''),
                        'channel_title': entry.get('uploader', 'Unknown Channel'),
                        'duration_seconds': duration or 0,
                        'duration_formatted': self._format_duration(duration or 0)
                    }
                    
                    videos.append(video_data)
                    
                except Exception as e:
                    logger.debug(f"Error processing video entry: {e}")
                    continue
            
            logger.info(f"✅ Found {len(videos)} videos via yt-dlp fallback (ALL videos from channel)")
            return videos
            
        except Exception as e:
            logger.error(f"yt-dlp fallback failed: {e}")
            return []
    
    def _parse_youtube_duration(self, duration_iso: str) -> int:
        """Parse YouTube ISO 8601 duration format (PT4M13S) to seconds."""
        import re
        
        # YouTube duration format: PT#H#M#S or PT#M#S or PT#S
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_iso)
        
        if not match:
            return 0
        
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    async def check_video_exists(self, video_url: str, video_title: str = None) -> bool:
        """Check if video already exists in Knowledge Hub by URL or title."""
        if not self.knowledge_db_id:
            return False
        
        try:
            # Check by URL first (most reliable)
            url_query = {
                "filter": {
                    "property": "URL",
                    "url": {
                        "equals": video_url
                    }
                }
            }
            
            response = requests.post(
                headers=self.headers,
                json=url_query,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                if len(results) > 0:
                    logger.debug(f"Video exists (URL match): {video_title}")
                    return True
            
            # If no URL match and we have a title, check by title
            if video_title:
                title_query = {
                    "filter": {
                        "property": "Name",
                        "title": {
                            "equals": video_title
                        }
                    }
                }
                
                response = requests.post(
                    headers=self.headers,
                    json=title_query,
                    timeout=10
                )
                
                if response.status_code == 200:
                    results = response.json().get('results', [])
                    if len(results) > 0:
                        logger.debug(f"Video exists (title match): {video_title}")
                        return True
                
                # Also check for similar titles (to catch minor variations)
                similar_title_query = {
                    "filter": {
                        "property": "Name",
                        "title": {
                            "contains": video_title[:50]  # First 50 characters
                        }
                    }
                }
                
                response = requests.post(
                    headers=self.headers,
                    json=similar_title_query,
                    timeout=10
                )
                
                if response.status_code == 200:
                    results = response.json().get('results', [])
                    for result in results:
                        props = result.get('properties', {})
                        name_prop = props.get('Name', {})
                        if name_prop.get('title'):
                            existing_title = name_prop['title'][0]['plain_text']
                            
                            # Check for very similar titles (accounting for small differences)
                            if self._titles_are_similar(video_title, existing_title):
                                logger.debug(f"Video exists (similar title): {video_title} ~ {existing_title}")
                                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if video exists: {e}")
            return False
    
    def _titles_are_similar(self, title1: str, title2: str, threshold: float = 0.70) -> bool:
        """Check if two titles are similar enough to be considered duplicates."""
        import re
        
        # Normalize titles for comparison
        def normalize_title(title):
            # Convert to lowercase
            title = title.lower()
            # Remove special characters and extra spaces
            title = re.sub(r'[^\w\s]', '', title)
            title = re.sub(r'\s+', ' ', title).strip()
            return title
        
        norm_title1 = normalize_title(title1)
        norm_title2 = normalize_title(title2)
        
        # Exact match after normalization
        if norm_title1 == norm_title2:
            return True
        
        # Calculate similarity using word overlap
        words1 = set(norm_title1.split())
        words2 = set(norm_title2.split())
        
        if not words1 or not words2:
            return False
        
        # Calculate Jaccard similarity (intersection over union)
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        jaccard_similarity = intersection / union if union > 0 else 0
        
        # Also calculate overlap percentage (how much of the shorter title is in the longer one)
        min_words = min(len(words1), len(words2))
        overlap_percentage = intersection / min_words if min_words > 0 else 0
        
        # Consider titles similar if either metric passes threshold
        return jaccard_similarity >= threshold or overlap_percentage >= threshold
    
    async def _get_existing_video_page(self, video_url: str, video_title: str = None) -> Optional[Dict[str, Any]]:
        """Get existing video page data if it exists."""
        if not self.knowledge_db_id:
            return None
        
        try:
            # Check by URL first (most reliable)
            url_query = {
                "filter": {
                    "property": "URL",
                    "url": {
                        "equals": video_url
                    }
                }
            }
            
            response = requests.post(
                headers=self.headers,
                json=url_query,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                if len(results) > 0:
                    return results[0]  # Return first matching page
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting existing video page: {e}")
            return None
    
    def _has_user_status(self, page: Dict[str, Any]) -> bool:
        """Check if page has user-set status (not processing status)."""
        try:
            status_prop = page.get('properties', {}).get('Status', {})
            if status_prop.get('select'):
                status_name = status_prop['select']['name']
                # Consider these as user-set statuses
                user_statuses = ['📋 To Review', '👀 In Progress', '✅ Completed', '⭐ Favorite', '🔗 Reference']
                return status_name in user_statuses
            return False
        except:
            return False
    
    def _has_user_checkbox_choices(self, page: Dict[str, Any]) -> Dict[str, bool]:
        """Check which checkboxes have been set by user."""
        try:
            props = page.get('properties', {})
            return {
                'decision_made': props.get('Decision Made', {}).get('checkbox', False),
                'pass': props.get('📁 Pass', {}).get('checkbox', False),
                'yes': props.get('🚀 Yes', {}).get('checkbox', False)
            }
        except:
            return {'decision_made': False, 'pass': False, 'yes': False}
    
    def _should_preserve_field(self, existing_page: Dict[str, Any], field_name: str) -> bool:
        """Check if field has user content that should be preserved."""
        if not existing_page:
            return False
        
        try:
            props = existing_page.get('properties', {})
            field_data = props.get(field_name, {})
            
            # For rich text fields, check if they have non-AI content
            if field_data.get('rich_text'):
                content = field_data['rich_text'][0]['plain_text'] if field_data['rich_text'] else ""
                # Don't overwrite if content doesn't look AI-generated
                if content and not content.startswith('🤖') and not content.startswith('❌'):
                    return True
            
            return False
        except:
            return False
    
    def _extract_transcript(self, video_url: str, retry_count: int = 3) -> Optional[str]:
        """Extract actual closed captions from YouTube video using yt-dlp."""
        for attempt in range(retry_count):
            try:
                if attempt > 0:
                    # Wait before retry to avoid rate limits
                    wait_time = attempt * 2  # 2, 4 seconds
                    logger.info(f"⏳ Waiting {wait_time}s before retry attempt {attempt + 1}/{retry_count}")
                    import time
                    time.sleep(wait_time)
                
                logger.info(f"🎤 Extracting real closed captions using yt-dlp: {video_url}")
                
                import yt_dlp
                import tempfile
                import os
                import re
                
                # Configure yt-dlp to extract captions only
                ydl_opts = {
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': ['en', 'en-US', 'en-GB'],
                    'skip_download': True,
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                }
                
                # Create temporary directory for subtitle files
                with tempfile.TemporaryDirectory() as temp_dir:
                    ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(id)s.%(ext)s')
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        try:
                            # Extract info and download captions
                            info = ydl.extract_info(video_url, download=False)
                            video_id = info.get('id', 'unknown')
                            
                            # Check if captions are available
                            subtitles = info.get('subtitles', {})
                            automatic_captions = info.get('automatic_captions', {})
                            
                            logger.info(f"📋 Available manual subtitles: {list(subtitles.keys())}")
                            logger.info(f"📋 Available auto captions: {list(automatic_captions.keys())}")
                            
                            # Try to get English captions (manual first, then auto)
                            caption_data = None
                            caption_source = "none"
                            
                            # Priority order: manual en, auto en, manual en-*, auto en-*
                            for lang_code in ['en', 'en-US', 'en-GB']:
                                if lang_code in subtitles:
                                    caption_data = subtitles[lang_code]
                                    caption_source = f"manual_{lang_code}"
                                    break
                            
                            if not caption_data:
                                for lang_code in ['en', 'en-US', 'en-GB']:
                                    if lang_code in automatic_captions:
                                        caption_data = automatic_captions[lang_code]
                                        caption_source = f"auto_{lang_code}"
                                        break
                            
                            if not caption_data:
                                logger.warning(f"No English captions found for video: {video_id}")
                                continue
                            
                            logger.info(f"✅ Found captions: {caption_source}")
                            
                            # Download the caption file (prefer vtt format)
                            ydl_opts_download = ydl_opts.copy()
                            ydl_opts_download['writesubtitles'] = True
                            ydl_opts_download['writeautomaticsub'] = caption_source.startswith('auto')
                            ydl_opts_download['subtitlesformat'] = 'vtt'
                            
                            with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_download:
                                ydl_download.download([video_url])
                            
                            # Find and read the caption file
                            caption_files = []
                            for file in os.listdir(temp_dir):
                                if file.endswith('.vtt') and video_id in file:
                                    caption_files.append(os.path.join(temp_dir, file))
                            
                            if not caption_files:
                                logger.warning(f"No caption files downloaded for: {video_id}")
                                continue
                            
                            # Read the VTT file and extract text
                            caption_file = caption_files[0]
                            logger.info(f"📄 Reading caption file: {os.path.basename(caption_file)}")
                            
                            with open(caption_file, 'r', encoding='utf-8') as f:
                                vtt_content = f.read()
                            
                            # Parse VTT content and extract spoken text
                            transcript_text = self._parse_vtt_content(vtt_content)
                            
                            if transcript_text and len(transcript_text) > 50:
                                logger.info(f"✅ Real captions extracted successfully ({len(transcript_text)} characters)")
                                
# DEMO CODE REMOVED: # Log sample for verification
# DEMO CODE REMOVED: sample = transcript_text[:200] + "..." if len(transcript_text) > 200 else transcript_text
# DEMO CODE REMOVED: logger.info(f"📝 Sample: {sample}")
                                
                                return transcript_text
                            else:
                                logger.warning(f"Extracted text too short: {len(transcript_text) if transcript_text else 0} chars")
                                continue
                                
                        except Exception as extraction_error:
                            logger.warning(f"yt-dlp extraction failed: {extraction_error}")
                            continue
                            
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{retry_count} failed: {e}")
                if attempt < retry_count - 1:
                    continue
        
        # All attempts failed
        logger.warning(f"Failed to extract captions after {retry_count} attempts")
        return None
    
    def _parse_vtt_content(self, vtt_content: str) -> str:
        """Parse VTT subtitle content and extract clean spoken text."""
        import re
        
        # Split into lines and process
        lines = vtt_content.split('\n')
        text_lines = []
        
        # Skip VTT header and extract text lines
        in_cue = False
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and VTT headers
            if not line or line.startswith('WEBVTT') or line.startswith('NOTE'):
                continue
            
            # Skip timestamp lines (format: 00:00:00.000 --> 00:00:00.000)
            if '-->' in line and re.match(r'\d{2}:\d{2}:\d{2}\.\d{3}', line):
                in_cue = True
                continue
            
            # Skip cue settings lines
            if in_cue and (line.startswith('align:') or line.startswith('position:') or line.startswith('size:')):
                continue
            
            # This should be caption text
            if in_cue and line:
                # Clean up VTT formatting tags
                cleaned_line = re.sub(r'<[^>]+>', '', line)  # Remove HTML tags
                cleaned_line = re.sub(r'\{[^}]+\}', '', cleaned_line)  # Remove formatting
                
                # Clean up common caption artifacts
                cleaned_line = cleaned_line.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
                cleaned_line = re.sub(r'\[.*?\]', '', cleaned_line)  # Remove [Music], [Applause], etc.
                cleaned_line = re.sub(r'\(.*?\)', '', cleaned_line)  # Remove (inaudible), etc.
                
                if cleaned_line.strip():
                    text_lines.append(cleaned_line.strip())
                    
            # Reset for next cue
            if not line:
                in_cue = False
        
        # Join all text and clean up
        full_text = ' '.join(text_lines)
        
        # Final cleanup
        full_text = re.sub(r'\s+', ' ', full_text)  # Multiple spaces to single
        full_text = full_text.strip()
        
        return full_text
    
    async def _process_video_with_ai(self, video_url: str, video_title: str, video_metadata: Dict[str, Any] = None, hashtags: List[str] = None) -> Dict[str, Any]:
        """Process video content with AI analysis using Gemini."""
        try:
            # First try to extract transcript
            transcript = self._extract_transcript(video_url)
            
            # Use Gemini 2.0 Flash for native video analysis
            import google.generativeai as genai
            
            # Configure Gemini
            google_api_key = (
                self.config.get("api", {}).get("google", {}).get("api_key") or
                os.getenv("GOOGLE_API_KEY")
            )
            
            if not google_api_key:
                return {
                    "success": False,
                    "error": "No Google API key available for AI analysis"
                }
            
            genai.configure(api_key=google_api_key)
            
            # Get video metadata for enhanced context
            metadata = video_metadata or {}
            channel_name = metadata.get('channel_title', 'Unknown Channel')
            description = metadata.get('description', '')
            duration = metadata.get('duration_formatted', 'Unknown')
            published_date = metadata.get('published_date', 'Unknown')
            hashtags_context = hashtags or []
            
            # Create analysis prompt based on whether we have transcript
            if transcript:
                hashtags_text = f"- Channel Tags/Focus: {', '.join(hashtags_context)}" if hashtags_context else "- Channel Tags: None specified"
                analysis_prompt = f"""
                Analyze this YouTube video using ALL the provided context information. Create a comprehensive analysis in JSON format.
                
                VIDEO CONTEXT:
                - Title: {video_title}
                - Channel: {channel_name}
                - Duration: {duration}
                - Published: {published_date}
                {hashtags_text}
                - Description: {description[:300]}{'...' if len(description) > 300 else ''}
                
                FULL TRANSCRIPT (ACTUAL SPOKEN CONTENT):
                {transcript}
                
                Using the video title, channel context, hashtags/focus areas, description, and complete transcript, provide detailed analysis:

                {{
                    "content_summary": "Detailed 4-6 sentence summary of the main content based on the transcript, including key themes and conclusions",
                    "detailed_transcript_summary": "Comprehensive 300-500 word summary that captures the flow of the video, main arguments, key explanations, and important details from the transcript", 
                    "key_points": ["List of 5-8 specific key takeaways extracted from the transcript with details"],
                    "action_items": ["List of 3-6 specific, actionable steps or recommendations mentioned in the video"],
                    "assistant_prompt": "A detailed prompt for an AI assistant that incorporates the specific knowledge and context from this video transcript",
                    "lifeos_integration_prompt": "A specific prompt that could be used to update or enhance a LifeOS system (calendar, task management, knowledge base, habits, etc.) based on the insights from this video. Be very specific about which system to update and how",
                    "system_updates": {{
                        "calendar": "Specific calendar/time management updates if applicable",
                        "tasks": "Task management system updates if applicable",
                        "habits": "Habit tracking updates if applicable",
                        "knowledge": "Knowledge management updates if applicable",
                        "workflows": "Workflow automation updates if applicable"
                    }},
                    "implementation_strategy": "Step-by-step strategy for implementing the video's teachings into a personal productivity system",
                    "complexity_level": "Beginner|Intermediate|Advanced",
                    "content_type": "Tutorial|Educational|Review|Discussion|Entertainment|Other", 
                    "content_category": "Technology|Business|Education|Lifestyle|Science|Health|Finance|etc",
                    "implementation_time": "Quick (< 1h)|Medium (1-4h)|Long (> 4h)",
                    "transcript_available": true,
                    "priority": "High|Medium|Low",
                    "key_quotes": ["Extract 3-5 important direct quotes from the transcript"],
                    "tools_mentioned": ["List specific tools, software, websites, or resources mentioned in the transcript"],
                    "learning_outcomes": ["What specific skills or knowledge will someone gain from this content"]
                }}

                Analyze the transcript thoroughly to extract maximum value and practical insights. Focus especially on actionable content that could enhance personal productivity systems.
                """
            else:
                hashtags_text = f"- Channel Tags/Focus: {', '.join(hashtags_context)}" if hashtags_context else "- Channel Tags: None specified"
                analysis_prompt = f"""
                Analyze this YouTube video using ALL the provided context information. Create a comprehensive analysis in JSON format.
                
                VIDEO CONTEXT:
                - Title: {video_title}
                - Channel: {channel_name}
                - Duration: {duration}
                - Published: {published_date}
                {hashtags_text}
                - Description: {description[:300]}{'...' if len(description) > 300 else ''}
                
                IMPORTANT: Use the video title, channel name, hashtags/focus areas, and description to infer the content type and focus. If you can access the video's visual content, extract detailed information including key points and actionable insights.

                {{
                    "content_summary": "Detailed 4-6 sentence summary based on the title, description, and any available visual content. Focus on the main topic and expected value.",
                    "detailed_transcript_summary": "If visual content is accessible, provide a longer-form summary (300-500 words) based on what you can observe. Otherwise, base this on the title and description context.",
                    "key_points": ["List of 5-8 specific key takeaways based on the video context, title themes, and any visual content available"],
                    "action_items": ["List of 3-6 specific, actionable steps or recommendations that would likely be covered in a video with this title and description"],
                    "assistant_prompt": "A detailed prompt that could be used with an AI assistant to help implement or learn about the topic covered in this video, based on the title and description",
                    "lifeos_integration_prompt": "A specific prompt that could be used to update or enhance a LifeOS system (calendar, task management, knowledge base, habits, etc.) based on the likely insights from this video topic. Be very specific about which system to update and how",
                    "system_updates": {{
                        "calendar": "Specific calendar/time management updates if the video topic is relevant to time management or scheduling",
                        "tasks": "Task management system updates if the video covers productivity or goal-setting topics",
                        "habits": "Habit tracking updates if the video discusses routines, habits, or behavioral changes",
                        "knowledge": "Knowledge management updates if the video covers learning, information organization, or skill development",
                        "workflows": "Workflow automation updates if the video discusses process optimization or efficiency"
                    }},
                    "implementation_strategy": "Step-by-step strategy for implementing the video's likely teachings into a personal productivity system, based on the title and description",
                    "complexity_level": "Beginner|Intermediate|Advanced",
                    "content_type": "Tutorial|Educational|Review|Discussion|Entertainment|Other",
                    "content_category": "Technology|Business|Education|Lifestyle|Science|Health|Finance|etc",
                    "implementation_time": "Quick (< 1h)|Medium (1-4h)|Long (> 4h)",
                    "transcript_available": false,
                    "priority": "High|Medium|Low",
                    "key_quotes": ["If visual content shows text or key statements, extract them here"],
                    "tools_mentioned": ["List any specific tools, software, or resources that would likely be mentioned in a video with this title"],
                    "learning_outcomes": ["What specific skills or knowledge someone would likely gain from a video with this title and description"]
                }}

                Focus on making intelligent inferences based on the video title, channel name, and description. Use your knowledge of typical content in this domain to provide valuable insights even without transcript access.
                """
            
            # Use Gemini 2.0 Flash for analysis
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            try:
                if transcript:
                    logger.info(f"🤖 Analyzing video with transcript ({len(transcript)} chars): {video_title}")
                    # For transcript analysis, just send the prompt (transcript is already in prompt)
                    response = model.generate_content(analysis_prompt)
                else:
                    logger.info(f"🤖 Sending video to Gemini for visual analysis: {video_url}")
                    # For video analysis, send both URL and prompt
                    response = model.generate_content([video_url, analysis_prompt])
                
                if response and response.text:
                    logger.info(f"📄 Received response from Gemini ({len(response.text)} chars)")
                    # Try to parse JSON response
                    response_text = response.text.strip()
                    
                    # Clean up response if it has markdown formatting
                    if response_text.startswith('```'):
                        response_text = response_text.split('```')[1]
                        if response_text.startswith('json'):
                            response_text = response_text[4:]
                    
                    # Clean up control characters that cause JSON parsing issues
                    import re
                    response_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', response_text)  # Remove control characters
                    response_text = re.sub(r'\s+', ' ', response_text)  # Normalize whitespace
                    
                    try:
                        analysis = json.loads(response_text)
                        
                        # Validate required fields
                        required_fields = ['content_summary', 'key_points', 'action_items']
                        for field in required_fields:
                            if field not in analysis:
                                analysis[field] = f"Analysis for {field} not available"
                        
                        # Set defaults for optional fields
                        analysis.setdefault('complexity_level', 'Intermediate')
                        analysis.setdefault('content_type', 'Educational')
                        analysis.setdefault('content_category', 'General')
                        analysis.setdefault('implementation_time', 'Medium (1-4h)')
                        analysis.setdefault('transcript_available', False)
                        analysis.setdefault('priority', 'Medium')
                        analysis.setdefault('assistant_prompt', f"Help me understand and implement the concepts from this video: {video_title}")
                        analysis.setdefault('detailed_transcript_summary', '')
                        analysis.setdefault('key_quotes', [])
                        analysis.setdefault('tools_mentioned', [])
                        analysis.setdefault('learning_outcomes', [])
                        
                        logger.info(f"✅ AI analysis completed for: {video_title[:50]}...")
                        logger.info(f"📊 Analysis includes: {len(analysis.get('key_points', []))} key points, {len(analysis.get('action_items', []))} action items")
                        
                        return {
                            "success": True,
                            "analysis": analysis,
                            "priority": analysis.get('priority', 'Medium')
                        }
                        
                    except json.JSONDecodeError as json_err:
                        logger.warning(f"JSON parsing failed: {json_err}")
                        logger.warning(f"Raw response: {response_text[:200]}...")
                        
                        # If JSON parsing fails, create a basic analysis from the text
                        return {
                            "success": True,
                            "analysis": {
                                "content_summary": response_text[:500] + "..." if len(response_text) > 500 else response_text,
                                "key_points": ["AI analysis provided in summary"],
                                "action_items": ["Review the content summary for actionable insights"],
                                "assistant_prompt": f"Help me understand and implement the concepts from this video: {video_title}",
                                "complexity_level": "Intermediate",
                                "content_type": "Educational",
                                "content_category": "General",
                                "implementation_time": "Medium (1-4h)",
                                "transcript_available": True,
                                "priority": "Medium"
                            },
                            "priority": "Medium"
                        }
                
                else:
                    logger.error(f"❌ No response from Gemini AI for video: {video_title}")
                    return {
                        "success": False,
                        "error": "No response from Gemini AI"
                    }
                    
            except Exception as gemini_error:
                logger.error(f"❌ Gemini analysis failed for {video_title}: {gemini_error}")
                logger.error(f"   Video URL: {video_url}")
                logger.error(f"   Error type: {type(gemini_error).__name__}")
                
                # Fallback: Create basic analysis based on title and description
                return {
                    "success": True,
                    "analysis": {
                        "content_summary": f"⚠️ AI analysis failed for '{video_title}' - Manual review recommended. Error: {str(gemini_error)[:200]}",
                        "key_points": [
                            f"Main topic: {video_title}",
                            "AI processing failed - manual review required",
                            "May contain valuable information for further analysis"
                        ],
                        "action_items": [
                            "Watch the video manually for detailed insights",
                            "Take notes on key concepts presented",
                            "Consider how content applies to current projects"
                        ],
                        "assistant_prompt": f"Help me understand and implement the concepts from this video about: {video_title}",
                        "complexity_level": "Intermediate",
                        "content_type": "Educational", 
                        "content_category": "General",
                        "implementation_time": "Quick (< 1h)",
                        "transcript_available": False,
                        "priority": "Medium"
                    },
                    "priority": "Medium"
                }
                
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def import_video_to_knowledge_hub(self, video: Dict[str, Any], channel_name: str, hashtags: List[str]) -> bool:
        """Import a video to the Knowledge Hub database with full AI analysis."""
        if not self.knowledge_db_id:
            logger.error("No Knowledge Hub database ID configured")
            return False
        
        try:
            logger.info(f"🔄 Processing video with AI analysis: {video['title'][:50]}...")
            
            # Check if video already exists and get existing data
            existing_page = await self._get_existing_video_page(video['url'], video['title'])
            
            # Process the video content with AI (include full video metadata for context)
            ai_analysis = await self._process_video_with_ai(video['url'], video['title'], video, hashtags)
            
            # Use channel hashtags and add AI-generated content hashtags
            clean_hashtags = [tag for tag in hashtags if tag and tag.strip()]
            
            # Base properties (always update these)
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": video['title']
                            }
                        }
                    ]
                },
                "URL": {
                    "url": video['url']
                },
                "Type": {
                    "select": {
                        "name": "YouTube"
                    }
                },
                "Hashtags": {
                    "multi_select": [
                        {"name": tag} for tag in clean_hashtags[:10] if tag and tag.strip()
                    ]
                },
                "Channel": {
                    "rich_text": [{"text": {"content": channel_name}}]
                }
            }
            
            # Only set Status if not already set by user
            if not existing_page or not self._has_user_status(existing_page):
                properties["Status"] = {
                    "select": {
                        "name": "🔄 Processing"
                    }
                }
            
            # Add AI analysis results if successful
            if ai_analysis['success']:
                analysis = ai_analysis['analysis']
                
                # Add AI-generated hashtags to existing channel hashtags
                ai_hashtags = []
                if analysis.get('content_category'):
                    ai_hashtags.append(analysis['content_category'])
                if analysis.get('content_type'):
                    ai_hashtags.append(analysis['content_type'])
                ai_hashtags.extend(['AI', 'YouTube', channel_name.replace('@', '')])
                
                # Combine channel hashtags with AI hashtags
                all_hashtags = clean_hashtags + [tag for tag in ai_hashtags if tag not in clean_hashtags]
                properties["Hashtags"] = {
                    "multi_select": [
                        {"name": tag} for tag in all_hashtags[:10] if tag and tag.strip()
                    ]
                }
                
                # Get existing user choices
                user_checkboxes = self._has_user_checkbox_choices(existing_page) if existing_page else {'decision_made': False, 'pass': False, 'yes': False}
                
                # AI Summary and Content Summary (only if not user-modified)
                if analysis.get('content_summary'):
                    if not self._should_preserve_field(existing_page, "AI Summary"):
                        properties["AI Summary"] = {
                            "rich_text": [{"text": {"content": analysis['content_summary']}}]
                        }
                    if not self._should_preserve_field(existing_page, "Content Summary"):
                        properties["Content Summary"] = {
                            "rich_text": [{"text": {"content": analysis['content_summary']}}]
                        }
                
                # Key Points (only if not user-modified)
                if analysis.get('key_points') and not self._should_preserve_field(existing_page, "Key Points"):
                    key_points_text = "\n".join([f"• {point}" for point in analysis['key_points']])
                    properties["Key Points"] = {
                        "rich_text": [{"text": {"content": key_points_text}}]
                    }
                
                # Action Items (only if not user-modified)
                if analysis.get('action_items') and not self._should_preserve_field(existing_page, "Action Items"):
                    action_items_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(analysis['action_items'])])
                    properties["Action Items"] = {
                        "rich_text": [{"text": {"content": action_items_text}}]
                    }
                
                # Assistant Prompt (only if not user-modified)
                if analysis.get('assistant_prompt') and not self._should_preserve_field(existing_page, "Assistant Prompt"):
                    properties["Assistant Prompt"] = {
                        "rich_text": [{"text": {"content": analysis['assistant_prompt']}}]
                    }
                
                # Complexity Level (always update for consistency)
                complexity_mapping = {
                    'Beginner': 'Beginner',
                    'Intermediate': 'Intermediate', 
                    'Advanced': 'Advanced',
                    'Beginner/Intermediate': 'Beginner/Intermediate'
                }
                complexity = analysis.get('complexity_level', 'Intermediate')
                properties["Complexity Level"] = {
                    "select": {"name": complexity_mapping.get(complexity, 'Intermediate')}
                }
                
                # Content Type (always update for consistency)
                content_type_mapping = {
                    'Tutorial': 'Tutorial',
                    'Educational': 'Educational',
                    'Review': 'Review',
                    'Discussion': 'Discussion',
                    'Entertainment': 'Entertainment',
                    'Other': 'Other'
                }
                content_type = analysis.get('content_type', 'Educational')
                properties["Content Type"] = {
                    "select": {"name": content_type_mapping.get(content_type, 'Educational')}
                }
                
                # Priority (always update for consistency)
                priority_mapping = {
                    'High': '🔴 High',
                    'Medium': '🟡 Medium', 
                    'Low': '🟢 Low'
                }
                priority = analysis.get('priority', 'Medium')
                properties["Priority"] = {
                    "select": {"name": priority_mapping.get(priority, '🟡 Medium')}
                }
                
                # Status (only set if not already user-set)
                if not existing_page or not self._has_user_status(existing_page):
                    properties["Status"] = {
                        "select": {"name": "✅ Completed"}
                    }
                
                # Processing Status (always update)
                properties["Processing Status"] = {
                    "select": {"name": "Completed"}
                }
                
                # Preserve existing checkbox choices
                properties["Decision Made"] = {
                    "checkbox": user_checkboxes['decision_made']
                }
                properties["📁 Pass"] = {
                    "checkbox": user_checkboxes['pass']
                }
                properties["🚀 Yes"] = {
                    "checkbox": user_checkboxes['yes']
                }
                
                # Add Notes with key insights and useful information
                notes_content = []
                if analysis.get('content_summary'):
                    notes_content.append(f"📝 Summary: {analysis['content_summary']}")
                if analysis.get('key_points'):
                    notes_content.append(f"\n🔑 Key Points:\n" + "\n".join([f"• {point}" for point in analysis['key_points'][:3]]))
                if analysis.get('action_items'):
                    notes_content.append(f"\n✅ Actions:\n" + "\n".join([f"{i+1}. {item}" for i, item in enumerate(analysis['action_items'][:3])]))
                
                if notes_content and not self._should_preserve_field(existing_page, "Notes"):
                    properties["Notes"] = {
                        "rich_text": [{"text": {"content": "\n".join(notes_content)}}]
                    }
                
                # Add detailed transcript summary to AI Summary if it exists and AI Summary is not user-modified
                if analysis.get('detailed_transcript_summary') and not self._should_preserve_field(existing_page, "AI Summary"):
                    full_ai_summary = analysis.get('content_summary', '') + "\n\n" + analysis.get('detailed_transcript_summary', '')
                    # Truncate if needed
                    if len(full_ai_summary) > 1900:
                        full_ai_summary = full_ai_summary[:1900] + "... (Content truncated)"
                    properties["AI Summary"] = {
                        "rich_text": [{"text": {"content": full_ai_summary}}]
                    }
                
                # Processing Status
                properties["Processing Status"] = {
                    "select": {"name": "Completed"}
                }
            
            else:
                # If AI processing failed, keep clean - no clutter notes
                
                # Set all fields with default/error values
                properties["AI Summary"] = {
                    "rich_text": [{"text": {"content": f"❌ AI processing failed: {ai_analysis.get('error', 'Unknown error')}"}}]
                }
                properties["Content Summary"] = {
                    "rich_text": [{"text": {"content": f"Manual review required - AI processing failed"}}]
                }
                properties["Key Points"] = {
                    "rich_text": [{"text": {"content": "• AI processing failed - manual analysis required"}}]
                }
                properties["Action Items"] = {
                    "rich_text": [{"text": {"content": "1. Review video manually\n2. Add analysis if valuable"}}]
                }
                properties["Assistant Prompt"] = {
                    "rich_text": [{"text": {"content": f"Please help me analyze this video: {video['title']}"}}]
                }
                properties["Complexity Level"] = {
                    "select": {"name": "Intermediate"}
                }
                properties["Content Type"] = {
                    "select": {"name": "Other"}
                }
                properties["Priority"] = {
                    "select": {"name": "🟡 Medium"}
                }
                properties["Status"] = {
                    "select": {"name": "📋 To Review"}
                }
                properties["Processing Status"] = {
                    "select": {"name": "Failed"}
                }
                properties["Decision Made"] = {
                    "checkbox": False
                }
                properties["📁 Pass"] = {
                    "checkbox": False
                }
                properties["🚀 Yes"] = {
                    "checkbox": False
                }
                properties["Channel"] = {
                    "rich_text": [{"text": {"content": channel_name}}]
                }
            
            # Update existing page or create new one
            if existing_page:
                # Update existing page
                page_id = existing_page['id']
                response = requests.patch(
                    headers=self.headers,
                    json={"properties": properties},
                    timeout=15
                )
                
                if response.status_code == 200:
                    logger.debug(f"Successfully updated existing video: {video['title'][:50]}...")
                    return True
                else:
                    logger.error(f"Failed to update video: {response.status_code} - {response.text}")
                    return False
            else:
                # Create new page
                response = requests.post(
                    headers=self.headers,
                    json={
                        "parent": {"database_id": self.knowledge_db_id},
                        "properties": properties
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    logger.debug(f"Successfully imported new video: {video['title'][:50]}...")
                    return True
                else:
                    logger.error(f"Failed to import video: {response.status_code} - {response.text}")
                    return False
            
        except Exception as e:
            logger.error(f"Error importing video: {e}")
            return False
    
    async def process_channel(self, channel: Dict[str, Any]) -> Dict[str, Any]:
        """Process all videos from a single channel."""
        logger.info(f"Processing channel: {channel['name']}")
        logger.info(f"  Channel URL: {channel['url']}")
        logger.info(f"  Resolved Channel ID: {channel['channel_id']}")
        
        result = {
            "channel_name": channel['name'],
            "total_videos": 0,
            "new_videos": 0,
            "imported_videos": 0,
            "errors": []
        }
        
        try:
            # Check if we have a valid channel ID
            if not channel['channel_id']:
                error_msg = f"No valid channel ID found for URL: {channel['url']}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                return result
            
            # Fetch and update channel metadata for empty fields
            logger.info(f"🔍 Checking channel fields for auto-population...")
            channel_metadata = await self.get_channel_metadata(channel['channel_id'])
            
            if channel_metadata:
                logger.info(f"📊 Retrieved channel metadata: {channel_metadata['title']} ({channel_metadata['subscriber_count']:,} subs, {channel_metadata['video_count']:,} videos)")
                
                # Update empty fields in the channel page
                update_success = await self.update_channel_fields(channel['page_id'], channel_metadata)
                if update_success:
                    logger.info(f"✅ Channel fields updated successfully")
                else:
                    logger.warning(f"⚠️ Some channel fields could not be updated")
            else:
                logger.warning(f"⚠️ Could not retrieve channel metadata")
            
            # Get all videos from channel
            videos = await self.get_channel_videos(channel['channel_id'])
            result["total_videos"] = len(videos)
            
            if not videos:
                logger.warning(f"No videos found for channel: {channel['name']}")
                return result
            
            logger.info(f"Processing {len(videos)} videos from {channel['name']}")
            
            # Process each video  
            for i, video in enumerate(videos, 1):
                try:
                    logger.debug(f"  Video {i}/{len(videos)}: {video['title'][:50]}...")
                    
                    # Check if video exists and needs AI analysis
                    existing_page = await self._get_existing_video_page(video['url'], video['title'])
                    
                    if existing_page:
                        # Video exists - check if it needs AI analysis update
                        processing_status = existing_page.get('properties', {}).get('Processing Status', {}).get('select', {}).get('name', '')
                        if processing_status == 'Completed':
                            logger.debug(f"    Already processed with AI, skipping")
                            continue
                        else:
                            logger.debug(f"    Exists but missing AI analysis, updating...")
                    else:
                        logger.debug(f"    New video, importing...")
                        result["new_videos"] += 1
                    
                    # Import/Update video in Knowledge Hub with AI analysis
                    if await self.import_video_to_knowledge_hub(video, channel['name'], channel['hashtags']):
                        result["imported_videos"] += 1
                        action = "Updated" if existing_page else "Imported"
                        logger.debug(f"    {action} successfully")
                    else:
                        logger.warning(f"    Failed to process")
                        result["errors"].append(f"Failed to process: {video['title']}")
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error processing video {video.get('title', 'Unknown')}: {e}")
                    result["errors"].append(f"Video processing error: {str(e)}")
            
            logger.info(f"Channel processing complete: {result['imported_videos']}/{result['new_videos']} new videos imported")
            
            # Add filtered database view to channel page
            if self.view_manager and result['imported_videos'] > 0:
                try:
                    logger.info(f"📊 Adding filtered database view to channel page...")
                    view_success = await self.view_manager.add_database_view_to_channel(
                        channel['page_id'], 
                        channel['name']
                    )
                    if view_success:
                        logger.info(f"✅ Database view added to {channel['name']} page")
                    else:
                        logger.warning(f"⚠️ Failed to add database view to {channel['name']} page")
                except Exception as view_error:
                    logger.error(f"Error adding database view: {view_error}")
                    result["errors"].append(f"Database view error: {str(view_error)}")
            
        except Exception as e:
            logger.error(f"Error processing channel {channel['name']}: {e}")
            result["errors"].append(f"Channel processing error: {str(e)}")
        
        return result
    
    async def update_channel_status(self, page_id: str, success: bool = True, stats: Dict[str, Any] = None):
        """Update channel processing status."""
        try:
            properties = {
                "Process Channel": {
                    "checkbox": False  # Uncheck after processing
                },
                "Last Processed": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                }
            }
            
            # Add processing notes if stats provided
            if stats:
                notes = f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                notes += f"Total videos: {stats.get('total_videos', 0)}\n"
                notes += f"New videos: {stats.get('new_videos', 0)}\n"
                notes += f"Imported: {stats.get('imported_videos', 0)}\n"
                
                if stats.get('errors'):
                    notes += f"Errors: {len(stats['errors'])}\n"
                    notes += "\n".join(stats['errors'][:3])  # First 3 errors
                
                properties["Notes"] = {
                    "rich_text": [{"text": {"content": notes}}]
                }
            
            response = requests.patch(
                headers=self.headers,
                json={"properties": properties},
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error updating channel status: {e}")
            return False
    
    async def process_marked_channels(self) -> Dict[str, Any]:
        """Main function to process all marked channels."""
        logger.info("🚀 Starting YouTube channel processing cycle")
        
        result = {
            "channels_processed": 0,
            "total_videos_imported": 0,
            "errors": [],
            "start_time": datetime.now(),
            "end_time": None
        }
        
        try:
            # Get channels to process
            channels = await self.get_channels_to_process()
            
            if not channels:
                logger.info("No channels marked for processing")
                result["end_time"] = datetime.now()
                return result
            
            logger.info(f"Processing {len(channels)} marked channels")
            
            # Process each channel
            for i, channel in enumerate(channels, 1):
                logger.info(f"📺 Processing channel {i}/{len(channels)}: {channel['name']}")
                
                try:
                    # Process the channel
                    channel_result = await self.process_channel(channel)
                    
                    # Update channel status
                    success = len(channel_result["errors"]) == 0
                    await self.update_channel_status(channel['page_id'], success, channel_result)
                    
                    # Update totals
                    result["channels_processed"] += 1
                    result["total_videos_imported"] += channel_result["imported_videos"]
                    
                    if channel_result["errors"]:
                        result["errors"].extend(channel_result["errors"])
                    
                    logger.info(f"✅ Channel completed: {channel_result['imported_videos']} videos imported")
                    
                except Exception as e:
                    logger.error(f"Failed to process channel {channel['name']}: {e}")
                    result["errors"].append(f"Channel {channel['name']}: {str(e)}")
                    
                    # Still update status to uncheck the box
                    await self.update_channel_status(channel['page_id'], False)
                
                # Delay between channels
                await asyncio.sleep(2)
            
            result["end_time"] = datetime.now()
            duration = (result["end_time"] - result["start_time"]).total_seconds()
            
            logger.info(f"🎉 Channel processing complete!")
            logger.info(f"📊 Processed {result['channels_processed']} channels")
            logger.info(f"📹 Imported {result['total_videos_imported']} new videos")
            logger.info(f"⏱️ Duration: {duration:.1f} seconds")
            
            if result["errors"]:
                logger.warning(f"⚠️ {len(result['errors'])} errors occurred")
            
        except Exception as e:
            logger.error(f"Error in channel processing cycle: {e}")
            result["errors"].append(f"Processing cycle error: {str(e)}")
            result["end_time"] = datetime.now()
        
        return result


    """Factory function to create YouTube channel processor."""