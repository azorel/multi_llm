#!/usr/bin/env python3
"""
Resolve Channel ID for @NateBJones
==================================

This script resolves the channel ID for @NateBJones and updates it in the Notion database.
"""

import os
import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# NOTION_REMOVED: def get_notion_config():
    """Get Notion configuration."""
        # Try to read from .env file
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                        break
        
    
    return {
        'channels_db_id': "203ec31c-9de2-8079-ae4e-ed754d474888",
        'headers': {
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    }


def scrape_channel_id(username: str) -> str:
    """Scrape channel ID from YouTube page."""
    import re
    import time
    
    url = f"https://www.youtube.com/@{username}"
    logger.info(f"🕷️ Scraping channel ID from: {url}")
    
    # Try multiple user agents
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
                logger.info(f"📄 Fetched page content ({len(html_content)} chars)")
                
                # Look for channel ID patterns
                patterns = [
                    r'"channelId":"(UC[a-zA-Z0-9_-]{22})"',
                    r'"externalId":"(UC[a-zA-Z0-9_-]{22})"',
                    r'channel/(UC[a-zA-Z0-9_-]{22})',
                    r'"browseEndpoint":{"browseId":"(UC[a-zA-Z0-9_-]{22})"',
                    r'"channelMetadataRenderer":[^}]*"externalId":"(UC[a-zA-Z0-9_-]{22})"',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html_content)
                    if matches:
                        channel_id = matches[0]
                        logger.info(f"✅ Found channel ID: {channel_id}")
                        return channel_id
                
                # If no patterns match, look for any UC ID
                uc_matches = re.findall(r'(UC[a-zA-Z0-9_-]{22})', html_content)
                if uc_matches:
                    # Return the most common one
                    from collections import Counter
                    most_common = Counter(uc_matches).most_common(1)
                    if most_common:
                        channel_id = most_common[0][0]
                        logger.info(f"✅ Found channel ID via frequency analysis: {channel_id}")
                        return channel_id
                
                logger.warning(f"No channel ID found in attempt {attempt + 1}")
                
            else:
                logger.warning(f"HTTP {response.status_code} on attempt {attempt + 1}")
                
        except Exception as e:
            logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
        
        # Small delay between attempts
        if attempt < len(user_agents) - 1:
            time.sleep(1)
    
    return None


# NOTION_REMOVED: def update_channel_in_notion(page_id: str, channel_id: str, config: dict) -> bool:
    """Update the channel ID in Notion."""
    try:
        logger.info(f"📝 Updating Notion page with channel ID: {channel_id}")
        
        properties = {
            "Channel": {
                "rich_text": [{"text": {"content": channel_id}}]
            }
        }
        
        response = requests.patch(
            headers=config['headers'],
            json={"properties": properties},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Successfully updated channel ID in Notion")
            return True
        else:
            logger.error(f"Failed to update Notion: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating Notion: {e}")
        return False


def main():
    """Main function."""
    try:
        # Get Notion config
# NOTION_REMOVED:         config = get_notion_config()
        
        # Query for @NateBJones channel
        logger.info("🔍 Finding @NateBJones channel in Notion...")
        
        query_data = {
            "filter": {
                "and": [
                    {
                        "property": "Name",
                        "title": {
                            "equals": "@NateBJones"
                        }
                    },
                    {
                        "property": "Process Channel",
                        "checkbox": {
                            "equals": True
                        }
                    }
                ]
            }
        }
        
        response = requests.post(
            headers=config['headers'],
            json=query_data,
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to query database: {response.status_code}")
            return
        
        results = response.json().get('results', [])
        
        if not results:
            logger.error("Channel @NateBJones not found in database")
            return
        
        # Get the page
        page = results[0]
        page_id = page['id']
        props = page['properties']
        
        # Check if channel ID already exists
        existing_channel_id = None
        if props.get('Channel', {}).get('rich_text'):
            existing_channel_id = props['Channel']['rich_text'][0]['plain_text']
        
        if existing_channel_id and existing_channel_id.startswith('UC'):
            logger.info(f"Channel already has ID: {existing_channel_id}")
            return
        
        # Scrape channel ID
        logger.info("🔍 Resolving channel ID for @NateBJones...")
        channel_id = scrape_channel_id("NateBJones")
        
        if not channel_id:
            logger.error("❌ Failed to resolve channel ID")
            logger.info("\n💡 Manual resolution required:")
            logger.info("1. Visit https://www.youtube.com/@NateBJones")
            logger.info("2. View page source (Ctrl+U or Cmd+Option+U)")
            logger.info("3. Search for 'channelId' or 'UC'")
            logger.info("4. Copy the channel ID (starts with UC, 24 characters)")
            logger.info("5. Update the 'Channel' field in Notion manually")
            return
        
        # Update Notion with the channel ID
        if update_channel_in_notion(page_id, channel_id, config):
            logger.info("\n🎉 Success! Channel ID resolved and updated:")
            logger.info(f"   Channel: @NateBJones")
            logger.info(f"   Channel ID: {channel_id}")
            logger.info(f"   Status: Ready for processing")
            logger.info("\n✅ The channel should now process successfully!")
        else:
            logger.error("❌ Failed to update channel ID in Notion")
            logger.info(f"\n💡 Please manually add this channel ID to Notion: {channel_id}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()