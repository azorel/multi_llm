#!/usr/bin/env python3
"""
Simple YouTube Channel Processing
=================================

Process channels without getting stuck on transcript downloads.
"""

import os
import asyncio
import sys
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append('src')

async def main():
    """Main processing function."""
    try:
        # Import the processor directly
        from processors.youtube_channel_processor import YouTubeChannelProcessor
        
        logger.info("🚀 Starting simple YouTube channel processing...")
        
        # Get Notion token from environment
            # Try to read from .env file
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                            break
        
            logger.error('❌ Error: No Notion token found')
            return
        
        # Get Google API key for AI processing
        google_api_key = os.getenv('GOOGLE_API_KEY')
        
        config = {
            'api': {
                'notion': {
                    'channels_database_id': '203ec31c-9de2-8079-ae4e-ed754d474888',
                    'knowledge_database_id': os.getenv('NOTION_KNOWLEDGE_DATABASE_ID') or '20bec31c-9de2-814e-80db-d13d0c27d869'
                },
                'google': {
                    'api_key': google_api_key
                }
            }
        }
        
        # Create processor
        
        # Get channels to process
        channels = await processor.get_channels_to_process()
        
        if not channels:
            logger.info("No channels marked for processing")
            return
        
        logger.info(f"Found {len(channels)} channels to process")
        
        # Process each channel with limited videos to avoid getting stuck
        for i, channel in enumerate(channels, 1):
            logger.info(f"📺 Processing channel {i}/{len(channels)}: {channel['name']}")
            logger.info(f"   Channel ID: {channel['channel_id']}")
            
            if not channel['channel_id']:
                logger.warning(f"   ⚠️ Skipping - no channel ID")
                continue
            
            try:
                # Get just a few videos to test
                logger.info(f"   🔍 Fetching videos...")
                videos = await processor.get_channel_videos(channel['channel_id'])
                
                if not videos:
                    logger.warning(f"   ⚠️ No videos found")
                    continue
                
                logger.info(f"   ✅ Found {len(videos)} videos")
                
                # Process all videos (removed limit for full processing)
                test_videos = videos
                logger.info(f"   📹 Processing all {len(test_videos)} videos...")
                
                imported_count = 0
                for j, video in enumerate(test_videos, 1):
                    logger.info(f"      Video {j}/{len(test_videos)}: {video['title'][:50]}...")
                    
                    # Check if video already exists
                    existing = await processor._get_existing_video_page(video['url'], video['title'])
                    if existing:
                        logger.info(f"      ↪️ Already exists, skipping")
                        continue
                    
                    # Import without AI processing for now (just basic info)
                    try:
                        success = await processor.import_video_to_knowledge_hub(
                            video, 
                            channel['name'], 
                            channel['hashtags']
                        )
                        if success:
                            imported_count += 1
                            logger.info(f"      ✅ Imported successfully")
                        else:
                            logger.warning(f"      ❌ Import failed")
                    except Exception as e:
                        if "Channel is not a property that exists" in str(e):
                            logger.error(f"      ❌ Channel field not in Knowledge Hub database schema")
                            logger.error(f"      💡 Please add 'Channel' field to your Knowledge Hub database in Notion")
                            return
                        else:
                            logger.error(f"      ❌ Import error: {e}")
                
                logger.info(f"   🎉 Channel complete: {imported_count}/{len(test_videos)} videos imported")
                
                # Update channel status
                await processor.update_channel_status(channel['page_id'], True, {
                    'total_videos': len(videos),
                    'new_videos': len(test_videos),
                    'imported_videos': imported_count,
                    'errors': []
                })
                
            except Exception as e:
                logger.error(f"   ❌ Channel processing error: {e}")
                await processor.update_channel_status(channel['page_id'], False)
        
        logger.info(f"🎉 Simple processing complete!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())