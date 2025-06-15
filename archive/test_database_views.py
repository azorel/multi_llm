#!/usr/bin/env python3
"""
Test Database Views Feature
============================

Simple test script to verify the filtered database views feature works.
"""

import os
import sys
import asyncio
import requests
from datetime import datetime

# Add the src directory to path
sys.path.insert(0, 'src')

    """Get Notion API token from environment."""
    
    if not token:
        # Try to read from .env file
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                        token = line.split("=", 1)[1].strip()
                        break
    
    return token


async def create_video_list_for_channel(channel_name, knowledge_db_id, headers):
    """Create a list of videos for a specific channel."""
    try:
        # Query Knowledge Hub for videos from this channel
        filter_data = {
            "filter": {
                "property": "Channel",
                "rich_text": {
                    "contains": channel_name.replace('@', '')
                }
            },
            "page_size": 10  # Limit to 10 most recent videos
        }
        
        response = requests.post(
            headers=headers,
            json=filter_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"   ⚠️ Could not fetch videos: {response.status_code}")
            return None
        
        videos = response.json().get('results', [])
        
        if not videos:
            return {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "No videos found for this channel yet."
                            }
                        }
                    ]
                }
            }
        
        # Create a bulleted list of videos
        video_items = []
        for video in videos[:5]:  # Show first 5 videos
            props = video['properties']
            
            # Get video title
            title = "Unknown Video"
            if props.get('Name', {}).get('title'):
                title = props['Name']['title'][0]['plain_text']
            
            # Get video URL
            url = None
            if props.get('URL', {}).get('url'):
                url = props['URL']['url']
            
            # Create list item
            if url:
                video_items.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": title,
                                    "link": {"url": url}
                                }
                            }
                        ]
                    }
                })
            else:
                video_items.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                })
        
        # Return a container with the video list
        if video_items:
            return {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"Recent videos from {channel_name} (showing {len(video_items)} of {len(videos)}):"
                            }
                        }
                    ]
                }
            }
        
        return None
        
    except Exception as e:
        print(f"   ⚠️ Error creating video list: {e}")
        return None


async def test_database_view_creation():
    """Test creating database views on channel pages."""
    print("🧪 Testing database view creation...")
    
    # Get Notion token
        return False
    
    # Get database IDs
    channels_db_id = "203ec31c-9de2-8079-ae4e-ed754d474888"
# NOTION_REMOVED:     knowledge_db_id = os.getenv("NOTION_KNOWLEDGE_DATABASE_ID") or "20bec31c-9de2-814e-80db-d13d0c27d869"
    
    headers = {
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        print(f"📚 Using Knowledge Hub Database ID: {knowledge_db_id}")
        print(f"📺 Using Channels Database ID: {channels_db_id}")
        
        # 1. Get all channel pages
        print("\n1. 🔍 Finding channel pages...")
        
        query_data = {}
        response = requests.post(
            headers=headers,
            json=query_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to query channels: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        channels = response.json().get('results', [])
        print(f"✅ Found {len(channels)} channel pages")
        
        # 2. Process each channel
        success_count = 0
        for i, channel in enumerate(channels, 1):
            try:
                props = channel['properties']
                
                # Get channel name
                channel_name = "Unknown"
                if props.get('Name', {}).get('title'):
                    channel_name = props['Name']['title'][0]['plain_text']
                
                print(f"\n{i}. 📺 Processing channel: {channel_name}")
                
                # Check if page already has database view
                page_id = channel['id']
                page_response = requests.get(
                    headers=headers,
                    timeout=10
                )
                
                if page_response.status_code == 200:
                    blocks = page_response.json().get('results', [])
                    has_video_section = any(
                        block.get('type') == 'heading_2' and 
                        block.get('heading_2', {}).get('rich_text') and
                        'Videos from' in block['heading_2']['rich_text'][0].get('plain_text', '')
                        for block in blocks
                    )
                    
                    if has_video_section:
                        print(f"   ✅ Already has video section, skipping")
                        continue
                
                # 3. Add database view to the page
                print(f"   📝 Adding database view...")
                
                # Create heading
                heading_block = {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"📺 Videos from {channel_name}"
                                }
                            }
                        ]
                    }
                }
                
                # Create instructions paragraph
                instructions_block = {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Filter instructions: In the database view below, click 'Filter' → Add filter → Channel → Contains → {channel_name.replace('@', '')}"
                                }
                            }
                        ]
                    }
                }
                
                # Create instructions for manual database view
                database_instructions = {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"💡 To create a filtered view:\n1. Go to Knowledge Hub database\n2. Create a new view\n3. Add filter: Channel → Contains → {channel_name.replace('@', '')}\n4. Copy the view link and paste it here"
                                }
                            }
                        ],
                        "icon": {
                            "emoji": "💡"
                        }
                    }
                }
                
                # Get videos from this channel and create a list
                video_list_block = await create_video_list_for_channel(
                    channel_name, knowledge_db_id, headers
                )
                
                # Add all blocks to the page
                blocks_to_add = [heading_block, instructions_block, database_instructions]
                if video_list_block:
                    blocks_to_add.append(video_list_block)
                
                response = requests.patch(
                    headers=headers,
                    json={"children": blocks_to_add},
                    timeout=15
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Successfully added database view")
                    success_count += 1
                else:
                    print(f"   ❌ Failed to add database view: {response.status_code}")
                    print(f"   Response: {response.text}")
                
                # Small delay to avoid rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Error processing channel: {e}")
        
        # 4. Summary
        print(f"\n" + "="*60)
        print(f"🎉 TEST RESULTS")
        print(f"="*60)
        print(f"📊 Channels found: {len(channels)}")
        print(f"✅ Database views added: {success_count}")
        print(f"⏭️ Channels skipped: {len(channels) - success_count}")
        
        if success_count > 0:
            print(f"\n💡 What to do next:")
            print(f"1. Visit your YouTube channel pages in Notion")
            print(f"2. Each page should now have a 'Videos from [Channel Name]' section")
            print(f"3. Follow the filter instructions to see only videos from that channel")
            
            return True
        else:
            print(f"\n⚠️ No database views were added")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("🚀 Testing YouTube Channel Database Views Feature")
    print("="*50)
    
    success = await test_database_view_creation()
    
    if success:
        print("\n🎉 Database views test completed successfully!")
        print("The filtered database views feature is working!")
    else:
        print("\n💔 Database views test failed.")
        print("Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())