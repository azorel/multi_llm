#!/usr/bin/env python3
"""Mark a specific channel for processing"""

import os
import asyncio
import aiohttp
from pathlib import Path

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

async def mark_channel_for_processing():
    """Mark IndyDan channel for processing."""
# NOTION_REMOVED:     channels_db_id = os.getenv('NOTION_CHANNELS_DATABASE_ID', '203ec31c-9de2-8079-ae4e-ed754d474888')
    
    headers = {
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    print("🔍 Finding IndyDan channel...")
    
    # Find IndyDan channel
    async with aiohttp.ClientSession() as session:
        query_data = {
            "filter": {
                "property": "Name",
                "title": {"contains": "IndyDan"}
            }
        }
        
        async with session.post(
            headers=headers,
            json=query_data,
            timeout=10
        ) as response:
            if response.status != 200:
                print(f"❌ Query failed: {response.status}")
                return
            
            data = await response.json()
            channels = data.get('results', [])
    
    if not channels:
        print("❌ IndyDan channel not found")
        return
    
    channel = channels[0]
    channel_id = channel['id']
    
    # Get channel URL to debug
    props = channel.get('properties', {})
    url_prop = props.get('URL', {})
    channel_url = ''
    if url_prop.get('rich_text') and url_prop['rich_text']:
        channel_url = url_prop['rich_text'][0].get('plain_text', '')
    
    print(f"📺 Found channel: {channel_id}")
    print(f"🔗 URL: {channel_url}")
    
    # Mark for processing
    update_data = {
        "properties": {
            "Process Channel": {
                "checkbox": True
            }
        }
    }
    
    async with aiohttp.ClientSession() as session2:
        async with session2.patch(
            headers=headers,
            json=update_data,
            timeout=10
        ) as response:
            if response.status == 200:
                print("✅ Channel marked for processing")
            else:
                print(f"❌ Failed to mark channel: {response.status}")

if __name__ == "__main__":
    asyncio.run(mark_channel_for_processing())