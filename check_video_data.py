import sqlite3

conn = sqlite3.connect('autonomous_learning.db')
cursor = conn.cursor()

# Check if any videos have transcripts
cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN transcript IS NOT NULL AND transcript != '' THEN 1 ELSE 0 END) as with_transcript,
           SUM(CASE WHEN duration_seconds IS NOT NULL THEN 1 ELSE 0 END) as with_duration,
           SUM(CASE WHEN view_count IS NOT NULL THEN 1 ELSE 0 END) as with_views,
           SUM(CASE WHEN ai_summary IS NOT NULL AND ai_summary != '' THEN 1 ELSE 0 END) as with_summary
    FROM knowledge_hub
""")

stats = cursor.fetchone()
print('Video Data Statistics:')
print(f'Total videos: {stats[0]}')
print(f'Videos with transcript: {stats[1]}')
print(f'Videos with duration: {stats[2]}')
print(f'Videos with view count: {stats[3]}')
print(f'Videos with AI summary: {stats[4]}')

# Check processing status distribution
cursor.execute("""
    SELECT processing_status, COUNT(*) 
    FROM knowledge_hub 
    GROUP BY processing_status
""")

print('\nProcessing Status Distribution:')
for status, count in cursor.fetchall():
    print(f'{status}: {count}')

# Check one video's AI summary
cursor.execute("""
    SELECT name, ai_summary, transcript, content_summary, key_points
    FROM knowledge_hub 
    WHERE ai_summary IS NOT NULL AND ai_summary != ''
    LIMIT 3
""")

# DEMO CODE REMOVED: print('\nSample Video Data:')
for video in cursor.fetchall():
    print(f'\nTitle: {video[0]}')
    print(f'AI Summary: {video[1][:200] if video[1] else "None"}...')
    print(f'Transcript: {"Yes" if video[2] else "No"} ({len(video[2]) if video[2] else 0} chars)')
    print(f'Content Summary: {video[3][:100] if video[3] else "None"}...')
    print(f'Key Points: {video[4][:100] if video[4] else "None"}...')

# Check the actual processing system
print('\n\nChecking for real YouTube data extraction...')
cursor.execute("""
    SELECT name, url, video_id, channel, description
    FROM knowledge_hub
    WHERE description IS NOT NULL AND description != ''
    LIMIT 3
""")

for video in cursor.fetchall():
    print(f'\nVideo: {video[0]}')
    print(f'URL: {video[1]}')
    print(f'Video ID: {video[2]}')
    print(f'Channel: {video[3]}')
    print(f'Description: {video[4][:200] if video[4] else "None"}...')

conn.close()