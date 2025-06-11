#!/usr/bin/env python3
"""
Build Today's CC in Notion
==========================

Creates the "Today's CC" page in your Notion workspace.
This script builds your daily command center as a comprehensive Notion page.

Usage:
    python build_todays_cc.py

Requirements:
    - Existing Notion workspace with databases
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.integrations.notion_mcp_client from src.automation.notion_todays_cc 

async def build_todays_cc_page():
    """Build the Today's CC page in Notion."""
    try:
        # Check for Notion token
            return False
        
        print("🚀 Building Today's CC in your Notion workspace...")
        print("=" * 60)
        
        # Initialize Notion client
        
        # Test connection
        print("🔗 Testing Notion connection...")
        try:
            await notion_client.test_connection()
            print("✅ Notion connection successful")
        except Exception as e:
            print(f"❌ Notion connection failed: {e}")
            return False
        
        # Create Today's CC builder
# NOTION_REMOVED:         todays_cc = create_notion_todays_cc(notion_client)
        
        # Build the page
        print("📄 Creating Today's CC page...")
        page_id = await todays_cc.create_todays_cc_page()
        
        if page_id:
            print(f"✅ Today's CC page created successfully!")
            print(f"📋 Page ID: {page_id}")
            print()
            print("🎯 Your Today's CC includes:")
            print("  📊 Real-time system overview")
            print("  ⚡ Quick action checkboxes") 
            print("  📅 Today's routine tracking")
            print("  📋 Task management view")
            print("  📦 Inventory alerts")
            print("  🚛 RC status dashboard")
            print("  📝 Quick notes section")
            print()
            print("💡 How to use:")
            print("  1. Open the 'Today's CC' page in your Notion")
            print("  2. Check quick action boxes to trigger automation")
            print("  3. View embedded database views for real-time data")
            print("  4. Add notes and track routine completions")
            print()
            print("🔄 The page will automatically:")
            print("  • Process checked quick actions")
            print("  • Update embedded database views")
            print("  • Log activities to your existing databases")
            print("  • Generate shopping lists and tasks")
            
            return True
        else:
            print("❌ Failed to create Today's CC page")
            return False
            
    except Exception as e:
        logger.error(f"Error building Today's CC: {e}")
        print(f"❌ Error: {e}")
        return False


async def monitor_todays_cc():
    """Monitor Today's CC for quick action processing."""
    try:
            return
        
        print("👁️  Starting Today's CC monitoring...")
        print("Watching for quick action checkbox interactions...")
        print("Press Ctrl+C to stop")
        
        # Initialize components
# NOTION_REMOVED:         todays_cc = create_notion_todays_cc(notion_client)
        
        # Set the page ID if we have it stored somewhere
        # In a real implementation, you'd store/retrieve this
        
        # Monitor loop
        while True:
            try:
                await todays_cc.monitor_quick_actions()
                await todays_cc.update_page_content()
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
        
        print("👋 Today's CC monitoring stopped")
        
    except Exception as e:
        logger.error(f"Error in monitoring: {e}")


async def main():
    """Main entry point."""
    print("🎯 Today's CC - Notion Integration Builder")
    print("=" * 50)
    
    # Ask user what they want to do
    print("What would you like to do?")
    print("1. Build Today's CC page in Notion")
    print("2. Start monitoring for quick actions")
    print("3. Build page and start monitoring")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            success = await build_todays_cc_page()
            if success:
                print("\n🎉 Today's CC is ready!")
                print("Go to your Notion workspace and find the 'Today's CC' page")
        
        elif choice == "2":
            await monitor_todays_cc()
        
        elif choice == "3":
            success = await build_todays_cc_page()
            if success:
                print("\n🔄 Starting monitoring...")
                await asyncio.sleep(2)
                await monitor_todays_cc()
        
        else:
            print("Invalid choice. Please run again and select 1, 2, or 3.")
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())