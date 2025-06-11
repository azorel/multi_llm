#!/usr/bin/env python3
"""Debug why channel processing isn't working"""

import os
import requests
import asyncio
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

async def debug_channel_processing():
    """Debug the entire channel processing pipeline."""
# NOTION_REMOVED:     channels_db_id = os.getenv('NOTION_CHANNELS_DATABASE_ID', '203ec31c-9de2-8079-ae4e-ed754d474888')
    
    headers = {
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    print("🔍 DEBUGGING CHANNEL PROCESSING PIPELINE")
    print("=" * 50)
    
    # Step 1: Check for marked channels
    print("1️⃣ Checking for channels marked for processing...")
    
    try:
        query_data = {
            "filter": {
                "property": "Process Channel",
                "checkbox": {"equals": True}
            }
        }
        
        response = requests.post(
            headers=headers,
            json=query_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Query failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        marked_channels = response.json().get('results', [])
        print(f"✅ Found {len(marked_channels)} channels marked for processing")
        
        if not marked_channels:
            print("❌ No channels are marked with 'Process Channel' = True")
            return
        
        # Step 2: Process each marked channel
        for i, channel in enumerate(marked_channels, 1):
            print(f"\n2️⃣ Processing channel {i}/{len(marked_channels)}")
            
            props = channel.get('properties', {})
            
            # Get channel name
            name_prop = props.get('Name', {})
            channel_name = 'Unknown'
            if name_prop.get('title'):
                channel_name = name_prop['title'][0].get('plain_text', 'Unknown')
            
            print(f"📺 Channel: {channel_name}")
            print(f"📋 Page ID: {channel['id']}")
            
            # Get URL
            url_prop = props.get('URL', {})
            channel_url = ''
            if url_prop.get('rich_text') and url_prop['rich_text']:
                channel_url = url_prop['rich_text'][0].get('plain_text', '')
            
            print(f"🔗 URL: {channel_url}")
            
            if not channel_url:
                print("❌ No URL found - cannot process")
                continue
            
            # Step 3: Try to resolve channel ID
            print("3️⃣ Attempting to resolve channel ID...")
            
            import re
            import aiohttp
            
            # Extract patterns
            patterns = [
                r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
                r'youtube\.com/c/([a-zA-Z0-9_-]+)', 
                r'youtube\.com/user/([a-zA-Z0-9_-]+)',
                r'youtube\.com/@([a-zA-Z0-9_.-]+)'
            ]
            
            channel_id = None
            for pattern in patterns:
                match = re.search(pattern, channel_url)
                if match:
                    identifier = match.group(1)
                    if identifier.startswith('UC'):
                        channel_id = identifier
                        break
                    else:
                        # Need to resolve with web scraping
                        print(f"🔄 Resolving '@{identifier}' to channel ID...")
                        
                        headers_web = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(channel_url, headers=headers_web, timeout=10) as response:
                                    if response.status == 200:
                                        html = await response.text()
                                        
                                        # Look for channel ID
                                        id_patterns = [
                                            r'"channelId":"(UC[a-zA-Z0-9_-]+)"',
                                            r'<meta itemprop="channelId" content="(UC[a-zA-Z0-9_-]+)"',
                                            r'"browseId":"(UC[a-zA-Z0-9_-]+)"'
                                        ]
                                        
                                        for id_pattern in id_patterns:
                                            id_match = re.search(id_pattern, html)
                                            if id_match:
                                                channel_id = id_match.group(1)
                                                break
                        except Exception as e:
                            print(f"❌ Web scraping failed: {e}")
                    break
            
            if not channel_id:
                print("❌ Could not resolve channel ID")
                continue
            
            print(f"✅ Channel ID: {channel_id}")
            
            # Step 4: Try to get videos from RSS
            print("4️⃣ Fetching videos from RSS feed...")
            
            import xml.etree.ElementTree as ET
            
            try:
                rss_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
                print(f"🔗 RSS URL: {rss_url}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(rss_url, timeout=10) as response:
                        if response.status != 200:
                            print(f"❌ RSS failed: {response.status}")
                            continue
                        
                        xml_data = await response.text()
                
                # Parse XML
                root = ET.fromstring(xml_data)
                
                # Define namespaces
                ns = {
                    'atom': 'http://www.w3.org/2005/Atom',
                    'yt': 'http://www.youtube.com/xml/schemas/2015'
                }
                
                # Get videos
                entries = root.findall('atom:entry', ns)
                print(f"✅ Found {len(entries)} videos in RSS feed")
                
                if entries:
                    print("📺 Recent videos:")
                    for j, entry in enumerate(entries[:3]):
                        video_title = entry.find('atom:title', ns)
                        video_id = entry.find('yt:videoId', ns)
                        published = entry.find('atom:published', ns)
                        
                        if video_title is not None and video_id is not None:
                            print(f"  {j+1}. {video_title.text}")
                            print(f"     ID: {video_id.text}")
                            if published is not None:
                                print(f"     Published: {published.text}")
                else:
                    print("❌ No videos found in RSS feed")
                
            except Exception as e:
                print(f"❌ RSS processing failed: {e}")
                continue
            
            print(f"\n5️⃣ Would import up to 5 videos to Knowledge Hub")
            print(f"6️⃣ Would unmark 'Process Channel' checkbox")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_channel_processing())