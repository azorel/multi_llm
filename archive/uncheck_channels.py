#!/usr/bin/env python3
"""
Uncheck Process Channel Checkboxes
==================================

Reverts all channels back to non-processing state.
"""

import os
import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChannelUncheckerService:
    """Uncheck all Process Channel checkboxes."""
    
    def __init__(self):
        """Initialize the service."""
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
        
        logger.info("Channel Unchecker Service initialized")
    
    def get_checked_channels(self):
        """Get all channels that are currently checked for processing."""
        try:
            query_data = {
                "filter": {
                    "property": "Process Channel",
                    "checkbox": {"equals": True}
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
                }
                
                # Extract channel name
                if props.get('Name', {}).get('title'):
                    channel_data['name'] = props['Name']['title'][0]['plain_text']
                
                channels.append(channel_data)
            
            return channels
            
        except Exception as e:
            logger.error(f"Error getting checked channels: {e}")
            return []
    
    def uncheck_channel(self, page_id: str, channel_name: str) -> bool:
        """Uncheck a single channel."""
        try:
            properties = {
                "Process Channel": {
                    "checkbox": False
                }
            }
            
            response = requests.patch(
                headers=self.headers,
                json={"properties": properties},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Unchecked: {channel_name}")
                return True
            else:
                logger.error(f"❌ Failed to uncheck {channel_name}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error unchecking channel {channel_name}: {e}")
            return False
    
    def uncheck_all_channels(self):
        """Uncheck all channels marked for processing."""
        logger.info("🔄 Finding channels marked for processing...")
        
        channels = self.get_checked_channels()
        
        if not channels:
            logger.info("✅ No channels currently marked for processing")
            return
        
        logger.info(f"Found {len(channels)} channels to uncheck")
        
        success_count = 0
        for channel in channels:
            logger.info(f"📺 Unchecking: {channel['name']}")
            if self.uncheck_channel(channel['page_id'], channel['name']):
                success_count += 1
        
        logger.info(f"🎉 Successfully unchecked {success_count}/{len(channels)} channels")
        logger.info("✅ All channels have been reverted to non-processing state")


def main():
    """Main function."""
    try:
        service = ChannelUncheckerService()
        service.uncheck_all_channels()
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()