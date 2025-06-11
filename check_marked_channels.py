#!/usr/bin/env python3
"""Check which channels are actually marked for processing"""

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

async def check_marked_channels():
    """Check which channels are currently marked for processing."""
# NOTION_REMOVED:     channels_db_id = os.getenv('NOTION_CHANNELS_DATABASE_ID', '203ec31c-9de2-8079-ae4e-ed754d474888')
    
    headers = {
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    print("🔍 CHECKING MARKED CHANNELS")
    print("=" * 40)
    
    try:
        query_data = {
            "filter": {
                "property": "Process Channel",
                "checkbox": {"equals": True}
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                headers=headers,
                json=query_data,
                timeout=10
            ) as response:
                if response.status != 200:
                    print(f"❌ Query failed: {response.status}")
                    return
                
                data = await response.json()
                marked_channels = data.get('results', [])
                
                print(f"📋 Found {len(marked_channels)} channels marked for processing:")
                
                for i, channel in enumerate(marked_channels, 1):
                    props = channel.get('properties', {})
                    
                    # Get channel name
                    name_prop = props.get('Name', {})
                    channel_name = 'Unknown'
                    if name_prop.get('title'):
                        channel_name = name_prop['title'][0].get('plain_text', 'Unknown')
                    
                    # Get URL
                    url_prop = props.get('URL', {})
                    channel_url = ''
                    if url_prop.get('rich_text') and url_prop['rich_text']:
                        channel_url = url_prop['rich_text'][0].get('plain_text', '')
                    
                    print(f"  {i}. {channel_name}")
                    print(f"     URL: {channel_url}")
                    print(f"     ID: {channel['id']}")
                    print()
                
                if not marked_channels:
                    print("❌ No channels are currently marked for processing")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_marked_channels())