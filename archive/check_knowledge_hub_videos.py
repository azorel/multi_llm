#!/usr/bin/env python3
"""
Check Knowledge Hub Database for New Videos
===========================================

This script checks the Knowledge Hub database for videos imported from
NateBJones channel today (2025-06-08).
"""

import os
import requests
import json
from datetime import datetime

def main():
    # Configuration
    KNOWLEDGE_HUB_DB_ID = '20bec31c-9de2-814e-80db-d13d0c27d869'

        # Try to read from .env file
        try:
            with open('.env', 'r') as f:
                for line in f:
                        break
        except:
            pass

        return

    headers = {
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28'
    }

    # Today's date in ISO format
    today = datetime.now().strftime('%Y-%m-%d')
    print(f'🔍 Checking Knowledge Hub for videos imported today: {today}')
    print(f'📁 Database ID: {KNOWLEDGE_HUB_DB_ID}')
    print('=' * 80)

    try:
        # Query for all pages - we'll filter by date after getting them
        query_data = {
            'sorts': [
                {
                    'property': 'Last Updated',
                    'direction': 'descending'
                }
            ],
            'page_size': 100
        }
        
        response = requests.post(
            headers=headers,
            json=query_data,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f'❌ Error querying database: {response.status_code}')
            print(f'Response: {response.text}')
            return
        
        data = response.json()
        all_results = data.get('results', [])
        
        # Filter for today's entries
        today_results = []
        for page in all_results:
            created_time = page.get('created_time', '')
            last_edited_time = page.get('last_edited_time', '')
            
            if (created_time.startswith(today) or last_edited_time.startswith(today)):
                today_results.append(page)
        
        print(f'📊 Total videos processed today: {len(today_results)}')
        
        # Filter for NateBJones channel specifically
        nate_jones_videos = []
        
        for page in today_results:
            props = page.get('properties', {})
            
            # Check URL field for NateBJones
            url_field = props.get('URL', {})
            url = ''
            if url_field.get('url'):
                url = url_field['url']
            elif url_field.get('rich_text') and len(url_field['rich_text']) > 0:
                url = url_field['rich_text'][0].get('plain_text', '')
            
            # Check Name field for NateBJones
            name_field = props.get('Name', {})
            name = ''
            if name_field.get('title') and len(name_field['title']) > 0:
                name = name_field['title'][0].get('plain_text', '')
            
            # Check Notes field for NateBJones
            notes_field = props.get('Notes', {})
            notes = ''
            if notes_field.get('rich_text') and len(notes_field['rich_text']) > 0:
                notes = notes_field['rich_text'][0].get('plain_text', '')
            
            # Check if this is a NateBJones video
            if any('NateBJones' in text or 'nateb' in text.lower() for text in [url, name, notes]):
                nate_jones_videos.append({
                    'page_id': page['id'],
                    'name': name,
                    'url': url,
                    'created': page.get('created_time', ''),
                    'last_edited': page.get('last_edited_time', ''),
                    'properties': props
                })
        
        print(f'\n🎯 Videos from NateBJones channel imported today: {len(nate_jones_videos)}')
        
        if nate_jones_videos:
            print('\n📺 NateBJones Videos Details:')
            print('=' * 80)
            
            for i, video in enumerate(nate_jones_videos, 1):
                print(f'\n{i}. {video["name"] or "Untitled Video"}')
                print(f'   Page ID: {video["page_id"]}')
                print(f'   URL: {video["url"]}')
                print(f'   Created: {video["created"]}')
                print(f'   Last Edited: {video["last_edited"]}')
                
                # Check processing status
                status_field = video['properties'].get('Status', {})
                if status_field.get('select'):
                    status = status_field['select']['name']
                    print(f'   Status: {status}')
                
                # Check AI Summary
                summary_field = video['properties'].get('AI Summary', {})
                if summary_field.get('rich_text') and len(summary_field['rich_text']) > 0:
                    summary = summary_field['rich_text'][0].get('plain_text', '')
                    if summary:
                        print(f'   AI Summary: {summary[:100]}...' if len(summary) > 100 else f'   AI Summary: {summary}')
        else:
            print('\n📺 No videos from NateBJones channel found for today.')
            
            if today_results:
                print('\n🔍 Let me show all videos processed today:')
                print('=' * 80)
                
                for i, page in enumerate(today_results, 1):
                    props = page.get('properties', {})
                    
                    name_field = props.get('Name', {})
                    name = ''
                    if name_field.get('title') and len(name_field['title']) > 0:
                        name = name_field['title'][0].get('plain_text', '')
                    
                    url_field = props.get('URL', {})
                    url = ''
                    if url_field.get('url'):
                        url = url_field['url']
                    elif url_field.get('rich_text') and len(url_field['rich_text']) > 0:
                        url = url_field['rich_text'][0].get('plain_text', '')
                    
                    print(f'\n{i}. {name or "Untitled Video"}')
                    if url:
                        print(f'   URL: {url}')
                    print(f'   Created: {page.get("created_time", "")}')
            else:
                print('\n📭 No videos were processed today at all.')

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()