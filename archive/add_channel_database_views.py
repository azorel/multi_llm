#!/usr/bin/env python3
"""
Add Channel Database Views
=========================

Standalone script to add filtered database views to all YouTube channel pages.
This script will:

1. Find all YouTube channel pages
2. Add filtered views of the Knowledge Hub database to each channel page
3. Show only videos from that specific channel in each view

Usage:
    python add_channel_database_views.py
"""

import os
import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from integrations.channel_database_view_manager import ChannelDatabaseViewManager
    from loguru import logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


async def main():
    """Main function to add database views to all channel pages."""
    print("🚀 Adding filtered database views to YouTube channel pages...")
    
    # Get Notion token
        # Try to read from .env file
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                        break
        
            print("Please set your Notion API token:")
            sys.exit(1)
    
    # Get database IDs
# NOTION_REMOVED:     channels_db_id = os.getenv("NOTION_CHANNELS_DATABASE_ID") or "203ec31c-9de2-8079-ae4e-ed754d474888"
# NOTION_REMOVED:     knowledge_db_id = os.getenv("NOTION_KNOWLEDGE_DATABASE_ID") or "20bec31c-9de2-814e-80db-d13d0c27d869"
    
    print(f"📋 Using Channels Database ID: {channels_db_id}")
    print(f"📚 Using Knowledge Hub Database ID: {knowledge_db_id}")
    
    # Configuration
    config = {
        "notion": {
            "channels_database_id": channels_db_id,
            "knowledge_database_id": knowledge_db_id
        }
    }
    
    # Initialize the database view manager
    try:
        print("✅ Database view manager initialized")
    except Exception as e:
        print(f"❌ Failed to initialize database view manager: {e}")
        sys.exit(1)
    
    # Process all channels
    try:
        print("\n📊 Starting database view creation process...")
        result = await view_manager.update_all_channel_views()
        
        # Display results
        print("\n" + "="*60)
        print("📈 RESULTS SUMMARY")
        print("="*60)
        
        total_time = (result["end_time"] - result["start_time"]).total_seconds()
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"✅ Channels updated: {result['channels_updated']}")
        
        if result["errors"]:
            print(f"❌ Errors: {len(result['errors'])}")
            print("\nError details:")
            for error in result["errors"]:
                print(f"  • {error}")
        else:
            print("🎉 All channels processed successfully!")
        
        print("\n💡 Next steps:")
        print("1. Visit your YouTube channel pages in Notion")
        print("2. Each page should now have a 'Videos from [Channel Name]' section")
        print("3. Use the filter instructions to customize the view if needed")
        print("4. The views will automatically include new videos as they're processed")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())