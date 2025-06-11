#!/usr/bin/env python3
"""Check Knowledge database properties"""

import os
import asyncio
import aiohttp
import json
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

async def check_database_properties():
    """Check the Knowledge database properties."""
# NOTION_REMOVED:     knowledge_db_id = os.getenv('NOTION_KNOWLEDGE_DATABASE_ID', '20bec31c-9de2-814e-80db-d13d0c27d869')
    
    headers = {
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    print("🔍 Checking Knowledge database properties...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            headers=headers,
            timeout=10
        ) as response:
            if response.status != 200:
                print(f"❌ Failed to get database: {response.status}")
                return
            
            data = await response.json()
            properties = data.get('properties', {})
            
            print(f"✅ Database: {data.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            print("📋 Available properties:")
            
            for prop_name, prop_data in properties.items():
                prop_type = prop_data.get('type', 'unknown')
                print(f"  • {prop_name}: {prop_type}")
    
    # Also check Gemini API key
    gemini_key = os.getenv('GEMINI_API_KEY')
    print(f"\\n🔑 Gemini API Key: {'✅ Set' if gemini_key else '❌ Not set'}")
    if gemini_key:
        print(f"   First 10 chars: {gemini_key[:10]}...")

if __name__ == "__main__":
    asyncio.run(check_database_properties())