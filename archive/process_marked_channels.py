#!/usr/bin/env python3
"""
Process Marked YouTube Channels
===============================

Process all channels marked for processing with clean imports.
"""

import os
import asyncio
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('channel_processing.log'),
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
        
        logger.info("🚀 Starting YouTube channel processing...")
        
        # Get Notion token from environment
            # Try to read from .env file
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                            break
        
            logger.error('❌ Error: No Notion token found')
            return
        
        # Basic config
        config = {
            'api': {
                'notion': {
                    'channels_database_id': '203ec31c-9de2-8079-ae4e-ed754d474888',
                    'knowledge_database_id': os.getenv('NOTION_KNOWLEDGE_DATABASE_ID') or '20bec31c-9de2-814e-80db-d13d0c27d869'
                },
                'google': {
                    'api_key': os.getenv('GOOGLE_API_KEY')
                }
            }
        }
        
        # Create processor
        
        # Process all marked channels
        result = await processor.process_marked_channels()
        
        logger.info(f"🎉 Processing complete!")
        logger.info(f"📊 Channels processed: {result['channels_processed']}")
        logger.info(f"📹 Videos imported: {result['total_videos_imported']}")
        
        if result['errors']:
            logger.warning(f"⚠️ Errors encountered: {len(result['errors'])}")
            for error in result['errors']:
                logger.error(f"   - {error}")
        
        duration = (result['end_time'] - result['start_time']).total_seconds()
        logger.info(f"⏱️ Total duration: {duration:.1f} seconds")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())