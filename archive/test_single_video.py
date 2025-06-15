#!/usr/bin/env python3
"""
Test Single Video Import
========================

Quick test of video import to verify database ID works.
"""

import os
import asyncio
import sys
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append('src')

async def main():
    """Test function."""
    try:
        from processors.youtube_channel_processor import YouTubeChannelProcessor
        
        logger.info("🧪 Testing single video import...")
        
        # Get Notion token
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                            break
        
            logger.error('❌ No Notion token found')
            return
        
        # Correct config with right database ID
        config = {
            'api': {
                'notion': {
                    'channels_database_id': '203ec31c-9de2-8079-ae4e-ed754d474888',
                    'knowledge_database_id': '20bec31c-9de2-814e-80db-d13d0c27d869'  # Correct ID
                },
                'google': {
                    'api_key': None
                }
            }
        }
        
        # Create processor
        
        # Test a simple video import without transcript processing
        test_video = {
            'title': 'Test Video Import',
            'url': 'https://www.youtube.com/watch?v=test123',
            'video_id': 'test123',
            'published_date': '2025-01-01',
            'description': 'Test video for database connection',
            'thumbnail': '',
            'channel_title': 'Test Channel',
            'duration_seconds': 300,
            'duration_formatted': '5m 0s'
        }
        
        logger.info("📝 Testing database connection...")
        
        # Try to import the test video (it will check database access)
        try:
            success = await processor.import_video_to_knowledge_hub(
                test_video,
                'Test Channel Name',
                ['test']
            )
            
            if success:
                logger.info("✅ Database connection works! Video import successful")
            else:
                logger.warning("❌ Video import failed - check logs")
                
        except Exception as e:
            if "Channel is not a property that exists" in str(e):
                logger.error("❌ Channel field missing from Knowledge Hub database")
                logger.error("💡 Please add 'Channel' field to your Knowledge Hub database in Notion")
            elif "Could not find database" in str(e):
                logger.error(f"❌ Database ID incorrect: {str(e)}")
            else:
                logger.error(f"❌ Import error: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())