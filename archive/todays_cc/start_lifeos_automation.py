#!/usr/bin/env python3
"""
LifeOS Full Automation Starter
===============================

Comprehensive automation service that starts all LifeOS components:
- Today's CC monitoring
- Background automation engine
- Intelligent task generation
- Real-time database updates
- System health monitoring

Usage:
    python start_lifeos_automation.py [--mode=full|monitor|engine]

Modes:
    full    - Start complete automation system (default)
    monitor - Only Today's CC monitoring
    engine  - Only background automation engine
"""

import asyncio
import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.automation.background_automation_engine import create_background_automation_engine
from src.automation.todays_cc_monitor import create_todays_cc_monitor


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


    """Start the complete LifeOS automation system."""
    logger.info("🚀 Starting Complete LifeOS Automation System")
    logger.info("=" * 60)
    
    try:
        # Create automation engine
        
        # Initialize
        success = await engine.initialize()
        if not success:
            logger.error("Failed to initialize automation engine")
            return
        
        # Display startup information
        status = engine.get_engine_status()
        logger.info("✅ LifeOS Automation System Initialized")
        logger.info("")
        logger.info("🎯 Active Components:")
        logger.info("  📋 Today's CC Monitoring - Real-time checkbox interactions")
        logger.info("  🧠 Intelligent Task Generation - AI-powered suggestions")
        logger.info("  📦 Inventory Management - Automated restocking")
        logger.info("  🚛 RC Hobby Monitoring - Vehicle maintenance tracking")
        logger.info("  📊 System Health Monitoring - Performance tracking")
        logger.info("  🔄 Database Maintenance - Automated cleanup")
        logger.info("")
        logger.info("📅 Automation Schedules:")
        for schedule in status['schedules']:
            if schedule['enabled']:
                logger.info(f"  • {schedule['name']}: every {schedule['interval_minutes']}min ({schedule['priority']} priority)")
        logger.info("")
        logger.info("💡 Features Active:")
        logger.info("  ⚡ Quick action processing from Today's CC checkboxes")
        logger.info("  🛒 Automatic shopping list generation from low inventory")
        logger.info("  🏆 Competition preparation workflow automation")
        logger.info("  📝 Smart routine tracking and optimization")
        logger.info("  🔔 Proactive maintenance reminders")
        logger.info("")
        logger.info("🔗 Connected Databases:")
        logger.info("  📋 chores, 📅 habits, 📦 food_onhand, 🥤 drinks")
        logger.info("  🚛 home_garage, 🏆 event_records, 📝 notes, 📚 knowledge_hub")
        logger.info("")
        logger.info("👀 Monitoring Today's CC Page:")
        logger.info(f"  📋 Page ID: {page_id}")
        logger.info("  🔄 Checking for interactions every 30 seconds")
        logger.info("")
        logger.info("🛑 Press Ctrl+C to stop all automation")
        logger.info("-" * 60)
        
        # Start the automation engine
        await engine.start()
        
    except KeyboardInterrupt:
        logger.info("\n👋 LifeOS Automation System stopped by user")
    except Exception as e:
        logger.error(f"Automation system error: {e}")


    """Start only the Today's CC monitoring."""
    logger.info("👀 Starting Today's CC Monitor Only")
    logger.info("=" * 40)
    
    try:
        
        success = await monitor.initialize()
        if not success:
            logger.error("Failed to initialize monitor")
            return
        
        logger.info("✅ Today's CC Monitor initialized")
        logger.info(f"📋 Monitoring page: {page_id}")
        logger.info("⚡ Watching for checkbox interactions...")
        logger.info("🛑 Press Ctrl+C to stop")
        logger.info("-" * 40)
        
        await monitor.start_monitoring(30)
        
    except KeyboardInterrupt:
        logger.info("\n👋 Monitor stopped")
    except Exception as e:
        logger.error(f"Monitor error: {e}")


    """Start only the background automation engine."""
    logger.info("🔧 Starting Background Automation Engine Only")
    logger.info("=" * 45)
    
    try:
        
        success = await engine.initialize()
        if not success:
            logger.error("Failed to initialize engine")
            return
        
        # Disable CC monitoring in this mode
        for schedule in engine.schedules:
            if schedule.name == "Today's CC Update":
                schedule.enabled = False
        
        status = engine.get_engine_status()
        logger.info("✅ Background Engine initialized")
        logger.info("📅 Active schedules:")
        for schedule in status['schedules']:
            if schedule['enabled']:
                logger.info(f"  • {schedule['name']}: {schedule['interval_minutes']}min")
        logger.info("🛑 Press Ctrl+C to stop")
        logger.info("-" * 45)
        
        await engine.start()
        
    except KeyboardInterrupt:
        logger.info("\n👋 Engine stopped")
    except Exception as e:
        logger.error(f"Engine error: {e}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="LifeOS Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_lifeos_automation.py                 # Full automation
  python start_lifeos_automation.py --mode=monitor  # Monitor only
  python start_lifeos_automation.py --mode=engine   # Engine only
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['full', 'monitor', 'engine'],
        default='full',
        help='Automation mode to run (default: full)'
    )
    
    parser.add_argument(
        '--page-id',
        help='Today\'s CC page ID (overrides environment variable)'
    )
    
    parser.add_argument(
        '--check-interval',
        type=int,
        default=30,
        help='Check interval in seconds (default: 30)'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_arguments()
    
    print("🎯 LifeOS - Autonomous Life Management System")
    print("=" * 50)
    
    # Load environment
    load_env_config()
    
    # Get configuration
        return
    
    # Get Today's CC page ID
    page_id = args.page_id or os.getenv("TODAYS_CC_PAGE_ID", "20dec31c-9de2-81db-aebe-ccde2cba609f")
    
    print(f"🔧 Mode: {args.mode}")
    print(f"📋 Page ID: {page_id}")
    print()
    
    # Start appropriate mode
    if args.mode == "full":
    elif args.mode == "monitor":
    elif args.mode == "engine":


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")