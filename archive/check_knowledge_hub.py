#!/usr/bin/env python3
"""
Check Knowledge Hub Videos
==========================

Check what videos are in the Knowledge Hub database.
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
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class KnowledgeHubChecker:
    """Check Knowledge Hub database contents."""
    
    def __init__(self):
        """Initialize the checker."""
        # Get Notion token
            env_path = ".env"
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                            break
        
        
        # Correct Knowledge Hub database ID
        self.knowledge_db_id = "20bec31c-9de2-814e-80db-d13d0c27d869"
        
        self.headers = {
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        logger.info("Knowledge Hub Checker initialized")
    
    def get_recent_videos(self, limit=10):
        """Get recent videos from Knowledge Hub."""
        try:
            query_data = {
                "filter": {
                    "property": "Type",
                    "select": {"equals": "YouTube"}
                },
                "sorts": [
                    {
                        "timestamp": "created_time",
                        "direction": "descending"
                    }
                ],
                "page_size": limit
            }
            
            response = requests.post(
                headers=self.headers,
                json=query_data,
                timeout=15
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to query Knowledge Hub: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return []
            
            results = response.json().get('results', [])
            
            videos = []
            for page in results:
                props = page['properties']
                
                video_data = {
                    'page_id': page['id'],
                    'created': page.get('created_time', ''),
                    'title': '',
                    'url': '',
                    'channel': '',
                    'status': '',
                    'processing_status': ''
                }
                
                # Extract info
                if props.get('Name', {}).get('title'):
                    video_data['title'] = props['Name']['title'][0]['plain_text']
                
                if props.get('URL', {}).get('url'):
                    video_data['url'] = props['URL']['url']
                
                if props.get('Channel', {}).get('rich_text'):
                    video_data['channel'] = props['Channel']['rich_text'][0]['plain_text']
                
                if props.get('Status', {}).get('select'):
                    video_data['status'] = props['Status']['select']['name']
                
                if props.get('Processing Status', {}).get('select'):
                    video_data['processing_status'] = props['Processing Status']['select']['name']
                
                videos.append(video_data)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error getting recent videos: {e}")
            return []
    
    def show_recent_videos(self):
        """Show recent YouTube videos in Knowledge Hub."""
        logger.info("🔍 Checking Knowledge Hub for recent YouTube videos...")
        
        videos = self.get_recent_videos(15)
        
        if not videos:
            logger.info("No YouTube videos found in Knowledge Hub")
            return
        
        logger.info(f"Found {len(videos)} YouTube videos:")
        logger.info("=" * 80)
        
        for i, video in enumerate(videos, 1):
            created_date = video['created'][:10] if video['created'] else 'Unknown'
            logger.info(f"{i:2d}. {video['title'][:60]}...")
            logger.info(f"     Channel: {video['channel'] or 'Not set'}")
            logger.info(f"     Status: {video['status'] or 'Not set'} | Processing: {video['processing_status'] or 'Not set'}")
            logger.info(f"     Created: {created_date}")
            logger.info(f"     URL: {video['url'][:50]}..." if video['url'] else "     URL: Not set")
            logger.info("")

def main():
    """Main function."""
    try:
        checker = KnowledgeHubChecker()
        checker.show_recent_videos()
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()