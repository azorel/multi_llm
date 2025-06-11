#!/usr/bin/env python3
"""Get actual video IDs from IndyDan's RSS feed"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET

async def get_video_ids():
    """Get video IDs from IndyDan's channel."""
    channel_id = "UC_x36zCEGilGpB1m-V4gmjg"  # IndyDan's channel ID
    rss_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(rss_url, timeout=10) as response:
                if response.status != 200:
                    print(f"❌ RSS failed: {response.status}")
                    return
                
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
        print(f"📹 Found {len(entries)} videos:")
        
        video_ids = []
        for i, entry in enumerate(entries[:3]):  # Just first 3
            video_title = entry.find('atom:title', ns)
            video_id = entry.find('yt:videoId', ns)
            
            if video_title is not None and video_id is not None:
                print(f"  {i+1}. {video_title.text}")
                print(f"     ID: {video_id.text}")
                video_ids.append(video_id.text)
        
        return video_ids
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    asyncio.run(get_video_ids())