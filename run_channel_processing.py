#!/usr/bin/env python3
"""Run the actual channel processing that imports videos with AI analysis"""

import sys
import os
import asyncio
from pathlib import Path

# Add project paths
sys.path.insert(0, '.')
sys.path.insert(0, './src')

# Load environment
env_path = Path('.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                if '#' in value:
                    value = value.split('#')[0].strip()
                os.environ[key] = value

async def run_processing():
    """Actually run the channel processing to import videos."""
    try:
        print("🚀 RUNNING YOUTUBE CHANNEL PROCESSING")
        print("=" * 50)
        
        # Import the processor
        from src.processors.youtube_channel_processor import create_youtube_channel_processor
        
        # Get config
        config = {
            "notion": {
                "channels_database_id": os.getenv('NOTION_CHANNELS_DATABASE_ID'),
                "knowledge_database_id": os.getenv('NOTION_KNOWLEDGE_DATABASE_ID')
            },
            "api": {
                "google": {
                    "api_key": os.getenv('GOOGLE_API_KEY')
                }
            }
        }
        
        # Create processor
        print("📺 Initializing YouTube processor...")
        
        # Check for marked channels
        print("🔍 Checking for marked channels...")
        channels = await processor.get_channels_to_process()
        print(f"📋 Found {len(channels)} channels marked for processing")
        
        if not channels:
            print("❌ No channels marked with 'Process Channel' = True")
            print("💡 Go to your Notion YouTube Channels database and check the 'Process Channel' box")
            return
        
        # Process the marked channels
        print("🔄 Processing marked channels...")
        result = await processor.process_marked_channels()
        
        # Show results
        print("\n🎉 PROCESSING COMPLETE!")
        print("=" * 30)
        print(f"📊 Channels processed: {result.get('channels_processed', 0)}")
        print(f"📹 Videos imported: {result.get('total_videos_imported', 0)}")
        print(f"⏱️ Duration: {result.get('duration', 0):.1f} seconds")
        
        if result.get('errors'):
            print(f"⚠️ Errors: {len(result['errors'])}")
            for error in result['errors'][:3]:
                print(f"  • {error}")
        
        print(f"\n✅ Videos imported to Knowledge Hub with full AI analysis!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_processing())