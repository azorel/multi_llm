#!/usr/bin/env python3
"""
Video Import Summary Report
===========================

This script provides a summary of video imports from YouTube processing system.
"""

import os
import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict

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

    # Date ranges
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    print(f'📊 YouTube Video Import Summary Report')
    print(f'📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)

    try:
        # Get recent pages (last 100)
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
        
        # Categorize by date
        today_videos = []
        yesterday_videos = []
        week_videos = []
        channel_counts = defaultdict(int)
        
        for page in all_results:
            created_time = page.get('created_time', '')
            last_edited_time = page.get('last_edited_time', '')
            props = page.get('properties', {})
            
            # Get video info
            name_field = props.get('Name', {})
            name = ''
            if name_field.get('title') and len(name_field['title']) > 0:
                name = name_field['title'][0].get('plain_text', '')
            
            url_field = props.get('URL', {})
            url = ''
            if url_field.get('url'):
                url = url_field['url']
            
            # Extract channel from URL
            channel = 'Unknown'
            if 'youtube.com' in url:
                if '/channel/' in url:
                    channel = url.split('/channel/')[1].split('/')[0][:10] + '...'
                elif '/watch' in url and 'v=' in url:
                    # This is a video URL, can't easily extract channel without additional API call
                    channel = 'YouTube Video'
                elif '@' in url:
                    # Handle @username format
                    channel = url.split('@')[1].split('/')[0] if '@' in url else 'YouTube'
            
            # Detect NateBJones specifically
            if any('NateBJones' in text or 'nateb' in text.lower() for text in [url, name]):
                channel = 'NateBJones'
            
            video_info = {
                'name': name,
                'url': url,
                'channel': channel,
                'created': created_time,
                'last_edited': last_edited_time
            }
            
            # Categorize by date
            if created_time.startswith(today) or last_edited_time.startswith(today):
                today_videos.append(video_info)
                channel_counts[channel] += 1
            elif created_time.startswith(yesterday) or last_edited_time.startswith(yesterday):
                yesterday_videos.append(video_info)
            elif (created_time >= week_ago) or (last_edited_time >= week_ago):
                week_videos.append(video_info)
        
        # Generate report
        print(f'📈 IMPORT STATISTICS')
        print(f'📅 Today ({today}): {len(today_videos)} videos')
        print(f'📅 Yesterday ({yesterday}): {len(yesterday_videos)} videos')
        print(f'📅 This week (since {week_ago}): {len(week_videos)} videos')
        print(f'📊 Total recent entries checked: {len(all_results)}')
        
        print(f'\n🎯 TODAY\'S CHANNEL BREAKDOWN')
        print('=' * 50)
        if channel_counts:
            for channel, count in sorted(channel_counts.items(), key=lambda x: x[1], reverse=True):
                print(f'{channel}: {count} videos')
        else:
            print('No videos imported today')
        
        print(f'\n📺 NATEBJONES CHANNEL SUMMARY')
        print('=' * 50)
        nate_today = [v for v in today_videos if v['channel'] == 'NateBJones']
        nate_yesterday = [v for v in yesterday_videos if any('NateBJones' in text or 'nateb' in text.lower() for text in [v['url'], v['name']])]
        nate_week = [v for v in week_videos if any('NateBJones' in text or 'nateb' in text.lower() for text in [v['url'], v['name']])]
        
        print(f'Today: {len(nate_today)} videos')
        print(f'Yesterday: {len(nate_yesterday)} videos')
        print(f'This week: {len(nate_week)} videos')
        
        if nate_today:
            print(f'\n🎬 Today\'s NateBJones Videos:')
            for i, video in enumerate(nate_today, 1):
                print(f'{i}. {video["name"]}')
                print(f'   URL: {video["url"]}')
        
        # Check processing status
        print(f'\n⚙️ PROCESSING STATUS OVERVIEW')
        print('=' * 50)
        status_counts = defaultdict(int)
        for page in all_results[:50]:  # Check status of recent 50 entries
            props = page.get('properties', {})
            status_field = props.get('Status', {})
            if status_field.get('select'):
                status = status_field['select']['name']
                status_counts[status] += 1
        
        for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            print(f'{status}: {count} entries')

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()