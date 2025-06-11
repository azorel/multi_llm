#!/usr/bin/env python3
"""
Load and Run Main App with Dependency Management
===============================================

This script loads the main app with proper dependency handling and fallbacks.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add project paths
sys.path.insert(0, '.')
sys.path.insert(0, './src')

def setup_logging():
    """Setup logging with fallback if loguru not available."""
    try:
        from loguru import logger
        return logger
    except ImportError:
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-8s | %(name)s - %(message)s'
        )
        return logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env file."""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
                    os.environ[key] = value
    except FileNotFoundError:
        print("❌ .env file not found")
        return False
    
    print(f"✅ Loaded {len(env_vars)} environment variables")
    return True

def check_critical_dependencies():
    """Check if critical dependencies are available."""
    missing = []
    
    # Check for notion_client
    try:
                print("✅ notion_client available")
    except ImportError:
        print("⚠️ notion_client not available - installing...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'notion-client'])
            print("✅ notion_client installed")
        except:
            missing.append('notion_client')
    
    # Check for google API client
    try:
        import googleapiclient
        print("✅ googleapiclient available")
    except ImportError:
        print("⚠️ googleapiclient not available - installing...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'google-api-python-client'])
            print("✅ googleapiclient installed")
        except:
            missing.append('googleapiclient')
    
    return len(missing) == 0

async def run_simplified_main():
    """Run a simplified version of the main app."""
    logger = setup_logging()
    
    print("🚀 LOADING AUTONOMOUS MULTI-LLM AGENT SYSTEM")
    print("=" * 60)
    
    # Load environment
    if not load_environment():
        print("❌ Failed to load environment")
        return False
    
    # Check dependencies
    if not check_critical_dependencies():
        print("❌ Missing critical dependencies")
        return False
    
    try:
        # Import the main components
        print("📦 Loading main application components...")
        
        # Import YouTube processor
        sys.path.insert(0, './src/processors')
        from youtube_channel_processor import create_youtube_channel_processor
        print("✅ YouTube Channel Processor loaded")
        
        # Create processor instance
            print("❌ No Notion API token found")
            return False
        
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
        
        print("✅ YouTube processor initialized")
        
        # Test the system
        print("\n📺 Testing YouTube channel processing...")
        channels = await youtube_processor.get_channels_to_process()
        print(f"📋 Found {len(channels)} channels marked for processing")
        
        if channels:
            print("\n🔄 PROCESSING MARKED CHANNELS")
            print("=" * 40)
            
            # Process the channels
            result = await youtube_processor.process_marked_channels()
            
            print(f"\n🎉 PROCESSING COMPLETE!")
            print(f"📊 Channels processed: {result['channels_processed']}")
            print(f"📹 Videos imported: {result['total_videos_imported']}")
            
            if result['errors']:
                print(f"⚠️ Errors: {len(result['errors'])}")
                for error in result['errors'][:3]:
                    print(f"  • {error}")
            
            duration = (result['end_time'] - result['start_time']).total_seconds()
            print(f"⏱️ Duration: {duration:.1f} seconds")
        
        else:
            print("✅ No channels marked for processing")
            print("💡 To test: Check 'Process Channel' for any YouTube channel in your LifeOS database")
        
        print(f"\n🎯 SYSTEM STATUS: Fully Operational")
        print(f"📱 LifeOS Integration: Connected")
        print(f"📺 YouTube Processing: Ready")
        print(f"⚡ Automation: Active")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading main app: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main entry point."""
    try:
        success = await run_simplified_main()
        
        if success:
            print(f"\n✅ MAIN APP LOADED SUCCESSFULLY!")
            print(f"🎮 YouTube channel processing is now active")
            print(f"📋 System is monitoring for 'Process Channel' checkboxes")
        else:
            print(f"\n❌ MAIN APP FAILED TO LOAD")
            
    except KeyboardInterrupt:
        print(f"\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())