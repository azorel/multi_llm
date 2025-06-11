#!/usr/bin/env python3
"""
Check YouTube Channels Database
==============================

This script checks the YouTube Channels database in Notion to see which channels
are marked for processing and identifies any issues with the latest channel added.
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
        logging.FileHandler('youtube_channels_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class YouTubeChannelsChecker:
    """Check YouTube Channels database for processing status and issues."""
    
    def __init__(self):
        """Initialize the checker."""
        # Get Notion token from environment or config
            # Try to read from .env file
            env_path = ".env"
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                            break
            
        
        # Get database ID - use discovered ID as fallback
        self.channels_db_id = (
            os.getenv("NOTION_CHANNELS_DATABASE_ID") or
            "203ec31c-9de2-8079-ae4e-ed754d474888"  # From discovery
        )
        
        self.headers = {
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        logger.info("YouTube Channels Checker initialized")
    
    def get_all_channels(self) -> List[Dict[str, Any]]:
        """Get all channels from the database."""
        try:
            all_results = []
            has_more = True
            start_cursor = None
            
            while has_more:
                query_data = {}
                
                if start_cursor:
                    query_data["start_cursor"] = start_cursor
                
                response = requests.post(
                    headers=self.headers,
                    json=query_data,
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to query channels: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return []
                
                data = response.json()
                all_results.extend(data.get('results', []))
                
                has_more = data.get('has_more', False)
                start_cursor = data.get('next_cursor')
            
            return all_results
            
        except Exception as e:
            logger.error(f"Error getting all channels: {e}")
            return []
    
    def extract_channel_info(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Extract channel information from a Notion page."""
        props = page['properties']
        
        info = {
            'page_id': page['id'],
            'created': page.get('created_time', ''),
            'last_edited': page.get('last_edited_time', ''),
            'name': '',
            'url': '',
            'channel_id': '',
            'process_channel': False,
            'last_processed': '',
            'status': '',
            'subscribers': None,
            'videos': None,
            'hashtags': [],
            'notes': '',
            'issues': []
        }
        
        # Extract Name
        if props.get('Name', {}).get('title'):
            info['name'] = props['Name']['title'][0]['plain_text']
        else:
            info['issues'].append("Missing channel name")
        
        # Extract URL
        if props.get('URL', {}).get('rich_text'):
            info['url'] = props['URL']['rich_text'][0]['plain_text']
        else:
            info['issues'].append("Missing channel URL")
        
        # Extract Channel ID
        if props.get('Channel', {}).get('rich_text'):
            info['channel_id'] = props['Channel']['rich_text'][0]['plain_text']
        
        # Extract Process Channel checkbox
        info['process_channel'] = props.get('Process Channel', {}).get('checkbox', False)
        
        # Extract Last Processed date
        if props.get('Last Processed', {}).get('date'):
            info['last_processed'] = props['Last Processed']['date'].get('start', '')
        
        # Extract Status
        if props.get('Status', {}).get('select'):
            info['status'] = props['Status']['select']['name']
        
        # Extract Subscribers count
        if props.get('Subscribers', {}).get('number') is not None:
            info['subscribers'] = props['Subscribers']['number']
        
        # Extract Videos count
        if props.get('Videos', {}).get('number') is not None:
            info['videos'] = props['Videos']['number']
        
        # Extract Hashtags
        if props.get('Hashtags', {}).get('multi_select'):
            info['hashtags'] = [tag['name'] for tag in props['Hashtags']['multi_select']]
        elif props.get('Hashtags', {}).get('select'):
            info['hashtags'] = [props['Hashtags']['select']['name']]
        
        # Extract Notes
        if props.get('Notes', {}).get('rich_text'):
            info['notes'] = props['Notes']['rich_text'][0]['plain_text']
        
        # Analyze URL issues
        if info['url']:
            if '@' in info['url'] and not info['channel_id']:
                info['issues'].append("URL uses @username format but no channel ID resolved")
            elif 'youtube.com' not in info['url']:
                info['issues'].append("Invalid YouTube URL format")
        
        # Check if channel ID looks valid
        if info['channel_id'] and not info['channel_id'].startswith('UC'):
            info['issues'].append(f"Invalid channel ID format: {info['channel_id']}")
        
        # Check processing status
        if info['process_channel'] and not info['channel_id']:
            info['issues'].append("Marked for processing but missing channel ID")
        
        return info
    
    def analyze_channels(self):
        """Analyze all channels and identify issues."""
        logger.info("🔍 Analyzing YouTube Channels database...")
        
        channels = self.get_all_channels()
        
        if not channels:
            logger.error("No channels found in database")
            return
        
        logger.info(f"Found {len(channels)} total channels")
        
        # Analyze each channel
        channels_to_process = []
        channels_with_issues = []
        
        for i, page in enumerate(channels):
            info = self.extract_channel_info(page)
            
            # Check if marked for processing
            if info['process_channel']:
                channels_to_process.append(info)
            
            # Check if has issues
            if info['issues']:
                channels_with_issues.append(info)
        
        # Display results
        logger.info("\n" + "="*80)
        logger.info("📊 SUMMARY")
        logger.info("="*80)
        logger.info(f"Total channels: {len(channels)}")
        logger.info(f"Channels marked for processing: {len(channels_to_process)}")
        logger.info(f"Channels with issues: {len(channels_with_issues)}")
        
        # Show channels marked for processing
        if channels_to_process:
            logger.info("\n" + "="*80)
            logger.info("✅ CHANNELS MARKED FOR PROCESSING")
            logger.info("="*80)
            
            for channel in channels_to_process:
                logger.info(f"\n📺 {channel['name']}")
                logger.info(f"   URL: {channel['url']}")
                logger.info(f"   Channel ID: {channel['channel_id'] or 'NOT RESOLVED'}")
                logger.info(f"   Last Processed: {channel['last_processed'] or 'Never'}")
                if channel['issues']:
                    logger.warning(f"   ⚠️  Issues: {', '.join(channel['issues'])}")
        
        # Show latest channel (most recently added)
        if channels:
            logger.info("\n" + "="*80)
            logger.info("🆕 LATEST CHANNEL ADDED")
            logger.info("="*80)
            
            latest = self.extract_channel_info(channels[0])
            logger.info(f"\n📺 {latest['name']}")
            logger.info(f"   Created: {latest['created']}")
            logger.info(f"   URL: {latest['url']}")
            logger.info(f"   Channel ID: {latest['channel_id'] or 'NOT RESOLVED'}")
            logger.info(f"   Process Channel: {'Yes' if latest['process_channel'] else 'No'}")
            logger.info(f"   Last Processed: {latest['last_processed'] or 'Never'}")
            logger.info(f"   Subscribers: {latest['subscribers']:,}" if latest['subscribers'] else "   Subscribers: Not set")
            logger.info(f"   Videos: {latest['videos']:,}" if latest['videos'] else "   Videos: Not set")
            logger.info(f"   Hashtags: {', '.join(latest['hashtags']) if latest['hashtags'] else 'None'}")
            
            if latest['notes']:
                logger.info(f"   Notes: {latest['notes'][:200]}...")
            
            if latest['issues']:
                logger.warning(f"\n   ⚠️  ISSUES DETECTED:")
                for issue in latest['issues']:
                    logger.warning(f"      - {issue}")
                
                # Provide solutions
                logger.info(f"\n   💡 SOLUTIONS:")
                if "URL uses @username format but no channel ID resolved" in latest['issues']:
                    logger.info(f"      1. The @username format requires channel ID resolution")
                    logger.info(f"      2. Visit {latest['url']} in a browser")
                    logger.info(f"      3. View page source and search for 'channelId' or 'UC'")
                    logger.info(f"      4. Copy the channel ID (starts with UC, 24 characters)")
                    logger.info(f"      5. Paste it into the 'Channel' field in Notion")
                    logger.info(f"      6. Alternative: Use the channel URL format instead")
                    logger.info(f"         Example: https://www.youtube.com/channel/UCxxxxxx...")
        
        # Show all channels with issues
        if channels_with_issues:
            logger.info("\n" + "="*80)
            logger.info("⚠️  ALL CHANNELS WITH ISSUES")
            logger.info("="*80)
            
            for channel in channels_with_issues:
                logger.warning(f"\n📺 {channel['name']}")
                logger.warning(f"   URL: {channel['url']}")
                logger.warning(f"   Issues: {', '.join(channel['issues'])}")


def main():
    """Main function."""
    try:
        checker = YouTubeChannelsChecker()
        checker.analyze_channels()
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()