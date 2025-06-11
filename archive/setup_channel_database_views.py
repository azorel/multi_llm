#!/usr/bin/env python3
"""
Setup Channel Database Views
============================

Simple script to add filtered database views to YouTube channel pages.
This script will automatically find your channel pages and add filtered
views of the Knowledge Hub database showing only videos from each channel.

Usage:
    python setup_channel_database_views.py
    
Or for a specific channel:
    python setup_channel_database_views.py --channel "@NateBJones"
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
        from loguru import logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


    """Get Notion API token from environment or .env file."""
    
    if not token:
        # Try to read from .env file
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                        token = line.split("=", 1)[1].strip()
                        break
    
    return token


async def setup_all_channels():
    """Setup database views for all channel pages."""
    print("🚀 Setting up filtered database views for all YouTube channels...")
    
    # Get Notion token
        print("Please set your Notion API token:")
        return False
    
    # Get Knowledge Hub database ID
# NOTION_REMOVED:     knowledge_db_id = os.getenv("NOTION_KNOWLEDGE_DATABASE_ID") or "20bec31c-9de2-814e-80db-d13d0c27d869"
    print(f"📚 Using Knowledge Hub Database ID: {knowledge_db_id}")
    
    try:
        # Initialize clients
# NOTION_REMOVED:         processor = EnhancedChannelProcessor(notion_client, knowledge_db_id)
        
        print("✅ Clients initialized successfully")
        
        # Test connection
        if not await notion_client.test_connection():
            print("❌ Failed to connect to Notion. Please check your API token.")
            return False
        
        print("🔗 Connection to Notion verified")
        
        # Process all channels
        result = await processor.process_all_channels_for_database_views()
        
        # Display results
        print("\n" + "="*60)
        print("📈 SETUP RESULTS")
        print("="*60)
        print(f"📊 Pages processed: {result['channels_processed']}")
        print(f"✅ Database views added: {result['channels_updated']}")
        print(f"⏭️ Pages skipped (already had views): {result['channels_skipped']}")
        
        if result["errors"]:
            print(f"❌ Errors: {len(result['errors'])}")
            print("\nError details:")
            for error in result["errors"]:
                print(f"  • {error}")
        else:
            print("🎉 All channel pages processed successfully!")
        
        print("\n💡 What's next:")
        print("1. Visit your YouTube channel pages in Notion")
        print("2. Each page should now have a 'Videos from [Channel Name]' section")
        print("3. Click the 'Filter' button in the database view")
        print("4. Add filter: Channel → Contains → [channel name]")
        print("5. The view will show only videos from that channel")
        
        return result['channels_updated'] > 0
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        return False


async def setup_specific_channel(channel_name: str):
    """Setup database view for a specific channel."""
    print(f"🚀 Setting up filtered database view for channel: {channel_name}")
    
    # Get Notion token
        print("Please set your Notion API token:")
        return False
    
    # Get Knowledge Hub database ID
# NOTION_REMOVED:     knowledge_db_id = os.getenv("NOTION_KNOWLEDGE_DATABASE_ID") or "20bec31c-9de2-814e-80db-d13d0c27d869"
    print(f"📚 Using Knowledge Hub Database ID: {knowledge_db_id}")
    
    try:
        # Initialize clients
# NOTION_REMOVED:         processor = EnhancedChannelProcessor(notion_client, knowledge_db_id)
        
        print("✅ Clients initialized successfully")
        
        # Test connection
        if not await notion_client.test_connection():
            print("❌ Failed to connect to Notion. Please check your API token.")
            return False
        
        print("🔗 Connection to Notion verified")
        
        # Process specific channel
        success = await processor.add_database_view_for_specific_channel(channel_name)
        
        if success:
            print(f"✅ Successfully added database view for {channel_name}")
            print("\n💡 Next steps:")
            print(f"1. Visit the {channel_name} page in Notion")
            print("2. Look for the 'Videos from [Channel Name]' section")
            print("3. Use the filter instructions to customize the view")
        else:
            print(f"❌ Failed to add database view for {channel_name}")
            print("Please check that the channel page exists and try again.")
        
        return success
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Setup filtered database views for YouTube channel pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup views for all channels:
  python setup_channel_database_views.py
  
  # Setup view for a specific channel:
  python setup_channel_database_views.py --channel "@NateBJones"
  python setup_channel_database_views.py --channel "Nate B Jones"
        """
    )
    
    parser.add_argument(
        "--channel", "-c",
        type=str,
        help="Setup database view for a specific channel (by name)"
    )
    
    args = parser.parse_args()
    
    # Configure logging to be less verbose for end users
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | {message}")
    
    try:
        if args.channel:
            success = asyncio.run(setup_specific_channel(args.channel))
        else:
            success = asyncio.run(setup_all_channels())
        
        if success:
            print("\n🎉 Setup completed successfully!")
        else:
            print("\n💔 Setup failed. Please check the error messages above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()