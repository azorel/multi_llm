#!/usr/bin/env python3
"""
Today's CC Monitoring Service
=============================

Standalone service to monitor your Today's CC Notion page for checkbox
interactions and automatically process them through your LifeOS system.

Usage:
    python monitor_todays_cc.py

Features:
    - Real-time checkbox monitoring
    - Automatic action processing
    - LifeOS integration
    - Background service mode
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.automation.todays_cc_monitor import create_todays_cc_monitor, start_monitoring_service


def load_env_config():
    """Load environment configuration from .env file."""
    env_path = project_root / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    # Clean up value by removing comments
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    os.environ[key] = value


async def main():
    """Main monitoring service entry point."""
    print("🎯 Today's CC - Automated Monitoring Service")
    print("=" * 55)
    
    # Load environment
    load_env_config()
    
    # Get configuration
        return
    
    # Get the Today's CC page ID
    page_id = os.getenv("TODAYS_CC_PAGE_ID", "20dec31c-9de2-81db-aebe-ccde2cba609f")
    check_interval = int(os.getenv("CC_CHECK_INTERVAL", "30"))
    
    print(f"📋 Monitoring Page ID: {page_id}")
    print(f"⏱️  Check Interval: {check_interval} seconds")
    print()
    
    try:
        # Initialize the monitor
        print("🚀 Initializing Today's CC monitor...")
        
        success = await monitor.initialize()
        if not success:
            print("❌ Failed to initialize monitoring service")
            return
        
        print("✅ Monitor initialized successfully")
        print()
        print("🎯 Monitoring Features Active:")
        print("  ⚡ Quick action checkbox detection")
        print("  🔄 Automatic LifeOS task processing")
        print("  📊 Real-time database updates")
        print("  📝 Action completion logging")
        print("  🛒 Smart shopping list generation")
        print("  🚛 RC maintenance tracking")
        print()
        print("📱 Available Quick Actions:")
        status = monitor.get_monitoring_status()
        for action in status['quick_actions_available']:
            print(f"  • {action}")
        print()
        print("👀 Monitoring started - watching for checkbox interactions...")
        print("💡 Check any quick action box in your Today's CC page to trigger automation!")
        print("🛑 Press Ctrl+C to stop monitoring")
        print("-" * 55)
        
        # Start monitoring
        await monitor.start_monitoring(check_interval)
        
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring service error: {e}")
        print(f"❌ Error: {e}")


async def test_single_action():
    """Test a single action without continuous monitoring."""
    print("🧪 Today's CC - Single Action Test")
    print("=" * 40)
    
    load_env_config()
    
        return
    
    page_id = os.getenv("TODAYS_CC_PAGE_ID", "20dec31c-9de2-81db-aebe-ccde2cba609f")
    
    # Create monitor
    success = await monitor.initialize()
    
    if not success:
        print("❌ Failed to initialize")
        return
    
    # Show available actions
    status = monitor.get_monitoring_status()
    print("Available actions:")
    actions = status['quick_actions_available']
    for i, action in enumerate(actions, 1):
        print(f"{i}. {action}")
    
    try:
        choice = int(input("\nEnter action number to test: ")) - 1
        if 0 <= choice < len(actions):
            action = actions[choice]
            print(f"\n🔄 Testing action: {action}")
            
            result = await monitor.process_single_action(action)
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
            else:
                print("✅ Action processed successfully!")
                print(f"📋 Result: {result}")
        else:
            print("Invalid choice")
            
    except (ValueError, KeyboardInterrupt):
        print("\n👋 Test cancelled")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_single_action())
    else:
        asyncio.run(main())