#!/usr/bin/env python3
"""
Complete YouTube Processing System Starter
==========================================
Starts the complete multi-agent YouTube processing system with:
- No video limits (processes ALL videos)
- Multi-agent orchestrator with multiple LLMs
- Self-healing monitoring system
- Autonomous error detection and resolution
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_youtube_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_configuration():
    """Check if all required configuration is present."""
    print("🔧 Checking system configuration...")
    
    required_env_vars = [
        'NOTION_CHANNELS_DATABASE_ID', 
        'NOTION_KNOWLEDGE_DATABASE_ID'
    ]
    
    optional_env_vars = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY', 
        'GOOGLE_API_KEY'
    ]
    
    missing_required = []
    available_providers = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"✅ {var}: configured")
    
    for var in optional_env_vars:
        if os.getenv(var):
            available_providers.append(var.replace('_API_KEY', '').lower())
            print(f"✅ {var}: configured")
        else:
            print(f"⚠️ {var}: not configured")
    
    if missing_required:
        print(f"❌ Missing required configuration: {missing_required}")
        return False
    
    if not available_providers:
        print("❌ No AI provider API keys configured!")
        return False
    
    print(f"🤖 Available AI providers: {available_providers}")
    print("✅ Configuration check passed")
    return True

async def start_youtube_processing_system():
    """Start the complete YouTube processing system."""
    print("🚀 STARTING COMPLETE YOUTUBE PROCESSING SYSTEM")
    print("=" * 60)
    print("📺 NO LIMITS - Processing ALL videos from ALL marked channels")
    print("🤖 Multi-agent orchestrator with multiple LLMs")
    print("🔄 Self-healing monitoring and autonomous error resolution")
    print("=" * 60)
    
    # Check configuration
    if not check_configuration():
        print("❌ Configuration check failed. Please fix configuration and try again.")
        return
    
    try:
        # Import the processors
        from multi_agent_youtube_processor import MultiAgentYouTubeProcessor
        from autonomous_self_healing_system import AutonomousSelfHealingSystem
        
        # Create instances
        youtube_processor = MultiAgentYouTubeProcessor()
        healing_system = AutonomousSelfHealingSystem()
        
        print("✅ All systems initialized successfully")
        print("\n🎯 Choose operation mode:")
        print("1. Process marked channels once (with multi-agent system)")
        print("2. Start continuous monitoring (self-healing + processing)")
        print("3. Run one-time processing with simple processor")
        print("4. System status and diagnostics")
        
        while True:
            try:
                choice = input("\nEnter choice (1-4): ").strip()
                
                if choice == "1":
                    print("🚀 Starting one-time multi-agent processing...")
                    result = await youtube_processor.start_full_channel_processing()
                    
                    print("\n📊 PROCESSING COMPLETE - FINAL REPORT:")
                    print("=" * 50)
                    print(json.dumps(result, indent=2))
                    break
                
                elif choice == "2":
                    print("🔄 Starting continuous monitoring mode...")
                    print("🤖 Self-healing system will automatically:")
                    print("  - Monitor for marked channels")
                    print("  - Process ALL videos when found") 
                    print("  - Fix errors autonomously")
                    print("  - Use multi-agent orchestrator")
                    print("\nPress Ctrl+C to stop\n")
                    
                    # Start both systems concurrently
                    tasks = [
                        asyncio.create_task(youtube_processor.start_monitoring_mode()),
                        asyncio.create_task(healing_system.continuous_monitoring_and_healing())
                    ]
                    
                    await asyncio.gather(*tasks)
                    break
                
                elif choice == "3":
                    print("🔄 Starting simple one-time processing...")
                    
                    # Import and run simple processor
                    from simple_video_processor import process_videos_with_ai
                    await process_videos_with_ai()
                    
                    print("✅ Simple processing complete")
                    break
                
                elif choice == "4":
                    print("📊 SYSTEM STATUS AND DIAGNOSTICS")
                    print("=" * 40)
                    
                    # Check orchestrator status
                    orchestrator_status = youtube_processor.orchestrator.get_system_status()
                    
                    print("🤖 MULTI-AGENT ORCHESTRATOR:")
                    print(f"  Active agents: {orchestrator_status['system_overview']['active_agents']}")
                    print(f"  Total tasks: {orchestrator_status['system_overview']['total_tasks']}")
                    print(f"  Success rate: {orchestrator_status['system_overview']['success_rate']:.1f}%")
                    
                    print("\n🔧 AI PROVIDERS:")
                    for provider, stats in orchestrator_status['provider_statistics'].items():
                        print(f"  {provider.title()}: {stats['requests']} requests, {stats['errors']} errors")
                    
                    print("\n📺 YOUTUBE PROCESSOR:")
                    print(f"  Configuration: {'✅ Valid' if check_configuration() else '❌ Invalid'}")
                    print(f"  Video limits: ❌ REMOVED - Processing ALL videos")
                    print(f"  Channel limits: ❌ REMOVED - Processing ALL marked channels")
                    print(f"  Multi-agent: ✅ ENABLED")
                    print(f"  Self-healing: ✅ ENABLED")
                    
                    # Check for marked channels
                    try:
                        from src.processors.youtube_channel_processor import YouTubeChannelProcessor
                        marked_channels = await checker.get_channels_to_process()
                        print(f"\n📋 MARKED CHANNELS: {len(marked_channels)} ready for processing")
                        
                        for i, channel in enumerate(marked_channels[:3], 1):
                            print(f"  {i}. {channel.get('name', 'Unknown')} ({channel.get('url', 'No URL')})")
                        
                        if len(marked_channels) > 3:
                            print(f"  ... and {len(marked_channels) - 3} more")
                    
                    except Exception as e:
                        print(f"❌ Error checking marked channels: {e}")
                    
                    print("\n💡 RECOMMENDATIONS:")
                    if len(marked_channels) > 0:
                        print("  🚀 Choose option 1 or 2 to process marked channels")
                    else:
                        print("  📝 Mark some channels for processing in Notion")
                    print("  🔄 Use option 2 for continuous autonomous operation")
                    
                    continue
                
                else:
                    print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
                    continue
                    
            except KeyboardInterrupt:
                print("\n🛑 Stopping system...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all required modules are installed")
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function."""
    try:
        asyncio.run(start_youtube_processing_system())
    except KeyboardInterrupt:
        print("\n👋 System stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()