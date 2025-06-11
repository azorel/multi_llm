#!/usr/bin/env python3
"""
Resolve Channel IDs for YouTube Channels
========================================

Resolves @username URLs to channel IDs for the marked channels.
"""

import os
import asyncio
import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('channel_resolution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import the processor
import sys
sys.path.append('src')

class ChannelIDResolver:
    """Resolve channel IDs for @username URLs."""
    
    def __init__(self):
        """Initialize the resolver."""
        # Get Notion token from environment
            # Try to read from .env file
            env_path = ".env"
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                            break
            
        
        # Get database ID
        self.channels_db_id = (
            os.getenv("NOTION_CHANNELS_DATABASE_ID") or
            "203ec31c-9de2-8079-ae4e-ed754d474888"  # From discovery
        )
        
        self.headers = {
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        logger.info("Channel ID Resolver initialized")
    
    def _scrape_channel_id_from_page(self, username_or_url: str) -> Optional[str]:
        """Scrape channel ID directly from YouTube page."""
        try:
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
                        
                        # Look for channel ID patterns in the HTML
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
    
# NOTION_REMOVED:     def update_channel_id_in_notion(self, page_id: str, channel_id: str) -> bool:
        """Update the Channel field in Notion with the resolved ID."""
        try:
            properties = {
                "Channel": {
                    "rich_text": [{"text": {"content": channel_id}}]
                }
            }
            
            response = requests.patch(
                headers=self.headers,
                json={"properties": properties},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Updated channel ID in Notion: {channel_id}")
                return True
            else:
                logger.error(f"Failed to update Notion: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating channel ID in Notion: {e}")
            return False
    
    def get_channels_needing_resolution(self) -> List[Dict[str, Any]]:
        """Get channels marked for processing that need channel ID resolution."""
        try:
            query_data = {
                "filter": {
                    "and": [
                        {
                            "property": "Process Channel",
                            "checkbox": {"equals": True}
                        },
                        {
                            "or": [
                                {
                                    "property": "Channel",
                                    "rich_text": {"is_empty": True}
                                },
                                {
                                    "property": "Channel",
                                    "rich_text": {"does_not_equal": ""}
                                }
                            ]
                        }
                    ]
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
                
                # Check if channel ID is missing or doesn't look valid
                channel_id = ""
                if props.get('Channel', {}).get('rich_text'):
                    channel_id = props['Channel']['rich_text'][0]['plain_text']
                
                # Only include if channel ID is missing or invalid
                if not channel_id or not channel_id.startswith('UC') or len(channel_id) != 24:
                    channel_data = {
                        'page_id': page['id'],
                        'name': '',
                        'url': '',
                        'current_channel_id': channel_id
                    }
                    
                    # Extract channel information
                    if props.get('Name', {}).get('title'):
                        channel_data['name'] = props['Name']['title'][0]['plain_text']
                    
                    if props.get('URL', {}).get('rich_text'):
                        channel_data['url'] = props['URL']['rich_text'][0]['plain_text']
                    
                    channels.append(channel_data)
            
            return channels
            
        except Exception as e:
            logger.error(f"Error getting channels needing resolution: {e}")
            return []
    
    def resolve_all_channels(self):
        """Resolve channel IDs for all channels that need it."""
        logger.info("🔍 Finding channels that need channel ID resolution...")
        
        channels = self.get_channels_needing_resolution()
        
        if not channels:
            logger.info("✅ All channels already have valid channel IDs")
            return
        
        logger.info(f"Found {len(channels)} channels needing resolution")
        
        for i, channel in enumerate(channels, 1):
            logger.info(f"\n📺 Channel {i}/{len(channels)}: {channel['name']}")
            logger.info(f"   URL: {channel['url']}")
            logger.info(f"   Current Channel ID: {channel['current_channel_id'] or 'None'}")
            
            if not channel['url'] or '@' not in channel['url']:
                logger.warning(f"   ⚠️ Skipping - no @username URL found")
                continue
            
            # Try to resolve the channel ID
            logger.info(f"   🔍 Resolving channel ID...")
            channel_id = self._scrape_channel_id_from_page(channel['url'])
            
            if channel_id:
                logger.info(f"   ✅ Resolved: {channel_id}")
                
                # Update in Notion
# NOTION_REMOVED:                 success = self.update_channel_id_in_notion(channel['page_id'], channel_id)
                if success:
                    logger.info(f"   ✅ Updated in Notion successfully")
                else:
                    logger.error(f"   ❌ Failed to update in Notion")
            else:
                logger.error(f"   ❌ Could not resolve channel ID")
                logger.error(f"   💡 Manual solution:")
                logger.error(f"      1. Visit {channel['url']} in browser")
                logger.error(f"      2. View page source, search for 'UC'")
                logger.error(f"      3. Copy 24-character channel ID starting with UC")
                logger.error(f"      4. Paste into 'Channel' field in Notion")


def main():
    """Main function."""
    try:
        resolver = ChannelIDResolver()
        resolver.resolve_all_channels()
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()