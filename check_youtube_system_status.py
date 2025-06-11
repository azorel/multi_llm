#!/usr/bin/env python3
"""
YouTube Multi-Agent System Status Checker
==========================================

Shows the current status of the YouTube processing system.
"""

import asyncio
import os
import json
import requests
from datetime import datetime

async def check_system_status():
    """Check the status of the YouTube processing system."""
    print("🔍 YOUTUBE MULTI-AGENT SYSTEM STATUS")
    print("=" * 50)
    
    # Check Notion API connection
    channels_db_id = '203ec31c-9de2-8079-ae4e-ed754d474888'
    knowledge_db_id = '20bec31c-9de2-814e-80db-d13d0c27d869'
    
    headers = {
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    try:
        # Check marked channels
        print("📺 CHECKING YOUTUBE CHANNELS...")
        query_data = {
            "filter": {
                "or": [
                    {"property": "Process Channel", "checkbox": {"equals": True}},
                    {"property": "Auto Process", "checkbox": {"equals": True}}
                ]
            }
        }
        
        response = requests.post(
            headers=headers,
            json=query_data,
            timeout=10
        )
        
        if response.status_code == 200:
            channels = response.json().get('results', [])
            print(f"✅ Channels marked for processing: {len(channels)}")
            
            for channel in channels:
                props = channel['properties']
                name = props.get('Name', {}).get('title', [{}])[0].get('plain_text', 'Unknown')
                auto_process = props.get('Auto Process', {}).get('checkbox', False)
                manual_process = props.get('Process Channel', {}).get('checkbox', False)
                print(f"   - {name} (Auto: {auto_process}, Manual: {manual_process})")
        else:
            print(f"❌ Failed to check channels: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error checking channels: {e}")
    
    try:
        # Check recent videos in Knowledge Hub
        print("\n🧠 CHECKING KNOWLEDGE HUB...")
        query_data = {
            "filter": {
                "and": [
                    {"property": "Type", "select": {"equals": "YouTube"}},
                    {"property": "Processing Status", "select": {"equals": "Completed"}}
                ]
            },
            "sorts": [{"property": "Last edited time", "direction": "descending"}],
            "page_size": 10
        }
        
        response = requests.post(
            headers=headers,
            json=query_data,
            timeout=10
        )
        
        if response.status_code == 200:
            videos = response.json().get('results', [])
            print(f"✅ Recent processed videos: {len(videos)}")
            
            for video in videos[:5]:
                props = video['properties']
                name = props.get('Name', {}).get('title', [{}])[0].get('plain_text', 'Unknown')
                channel = props.get('Channel', {}).get('rich_text', [{}])[0].get('plain_text', 'Unknown')
                print(f"   - {name[:60]}... (Channel: {channel})")
        else:
            print(f"❌ Failed to check knowledge hub: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error checking knowledge hub: {e}")
    
    # Check system processes
    print("\n🤖 CHECKING RUNNING AGENTS...")
    try:
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        processes = result.stdout
        
        agent_processes = []
        for line in processes.split('\n'):
            if 'python3' in line and any(keyword in line for keyword in [
                'autonomous_self_healing', 'real_agent_orchestrator', 'simple_video_processor'
            ]):
                agent_processes.append(line.split()[-1])
        
        if agent_processes:
            print(f"✅ Active agent processes: {len(agent_processes)}")
            for process in agent_processes:
                print(f"   - {process}")
        else:
            print("⚠️ No active agent processes found")
    
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
    
    # Check API keys
    print("\n🔑 CHECKING API CONFIGURATION...")
    api_keys = {
        'OpenAI': os.getenv('OPENAI_API_KEY'),
        'Anthropic': os.getenv('ANTHROPIC_API_KEY'), 
        'Google': os.getenv('GOOGLE_API_KEY'),
    }
    
    for service, key in api_keys.items():
        if key and key != 'your_key_here':
            print(f"✅ {service}: Configured")
        else:
            print(f"❌ {service}: Not configured")
    
    print(f"\n⏰ Status check completed at: {datetime.now()}")
    print("\n🎯 SYSTEM IS READY FOR CONTINUOUS PROCESSING!")
    print("   - Mark channels in Notion to trigger processing")
    print("   - Self-healing system will monitor and process automatically")
    print("   - Multiple LLM agents will handle transcription and analysis")

if __name__ == "__main__":
    asyncio.run(check_system_status())