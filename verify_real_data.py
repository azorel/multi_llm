#!/usr/bin/env python3
"""
Verify Real YouTube Data Extraction
===================================

Script to verify that real YouTube data has been successfully extracted
# DEMO CODE REMOVED: and compare it with the old fake data system.
"""

import sqlite3
import json
from datetime import datetime

def verify_real_data_extraction():
    """Verify that real YouTube data extraction is working."""
    
    print("🔍 VERIFYING REAL YOUTUBE DATA EXTRACTION")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('autonomous_learning.db')
        cursor = conn.cursor()
        
        # Get overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_videos,
                COUNT(CASE WHEN data_source = 'real_extraction' THEN 1 END) as real_data,
# DEMO CODE REMOVED: COUNT(CASE WHEN data_source = 'legacy_fake' THEN 1 END) as fake_data,
                COUNT(CASE WHEN view_count > 0 THEN 1 END) as has_views,
                COUNT(CASE WHEN duration_seconds > 0 THEN 1 END) as has_duration,
                COUNT(CASE WHEN channel IS NOT NULL AND channel != '' THEN 1 END) as has_channel,
                COUNT(CASE WHEN upload_date IS NOT NULL AND upload_date != '' THEN 1 END) as has_upload_date
            FROM knowledge_hub 
            WHERE url LIKE '%youtube.com%'
        """)
        
        stats = cursor.fetchone()
        
        print(f"📊 OVERALL STATISTICS:")
        print(f"   Total YouTube videos: {stats[0]}")
        print(f"   ✅ Real data extracted: {stats[1]}")
# DEMO CODE REMOVED: print(f"   ❌ Still fake/legacy: {stats[2]}")
        print(f"   👀 Videos with view counts: {stats[3]}")
        print(f"   ⏱️ Videos with duration: {stats[4]}")
        print(f"   📺 Videos with channel info: {stats[5]}")
        print(f"   📅 Videos with upload dates: {stats[6]}")
        
        print("\n" + "=" * 60)
        
# DEMO CODE REMOVED: # Show examples of real data vs fake data
# DEMO CODE REMOVED: print("🔬 SAMPLE REAL DATA EXTRACTION:")
        cursor.execute("""
            SELECT name, channel, view_count, duration_seconds, upload_date, data_source
            FROM knowledge_hub 
            WHERE data_source = 'real_extraction' AND url LIKE '%youtube.com%'
            LIMIT 5
        """)
        
# DEMO CODE REMOVED: real_samples = cursor.fetchall()
        
# DEMO CODE REMOVED: if real_samples:
# DEMO CODE REMOVED: for i, sample in enumerate(real_samples, 1):
# DEMO CODE REMOVED: title, channel, views, duration, upload_date, source = sample
                
                # Format duration
                if duration:
                    hours = duration // 3600
                    minutes = (duration % 3600) // 60
                    secs = duration % 60
                    duration_str = f"{hours}:{minutes:02d}:{secs:02d}" if hours > 0 else f"{minutes}:{secs:02d}"
                else:
                    duration_str = "Unknown"
                
                print(f"\n   {i}. {title[:50]}...")
                print(f"      📺 Channel: {channel}")
                print(f"      👀 Views: {views:,}" if views else "      👀 Views: Unknown")
                print(f"      ⏱️ Duration: {duration_str}")
                print(f"      📅 Upload: {upload_date}")
                print(f"      🔧 Source: {source}")
        else:
            print("   ❌ No real data found!")
        
        print("\n" + "=" * 60)
        
# DEMO CODE REMOVED: # Show comparison with legacy fake data
# DEMO CODE REMOVED: print("📼 SAMPLE LEGACY/FAKE DATA:")
        cursor.execute("""
            SELECT name, channel, view_count, duration_seconds, upload_date, data_source
            FROM knowledge_hub 
# DEMO CODE REMOVED: WHERE (data_source = 'legacy_fake' OR data_source IS NULL) AND url LIKE '%youtube.com%'
            LIMIT 3
        """)
        
# DEMO CODE REMOVED: fake_samples = cursor.fetchall()
        
# DEMO CODE REMOVED: if fake_samples:
# DEMO CODE REMOVED: for i, sample in enumerate(fake_samples, 1):
# DEMO CODE REMOVED: title, channel, views, duration, upload_date, source = sample
                print(f"\n   {i}. {title[:50]}...")
                print(f"      📺 Channel: {channel or 'Unknown Channel'}")
                print(f"      👀 Views: {views or 0:,}")
                print(f"      ⏱️ Duration: {duration or 0} seconds")
                print(f"      📅 Upload: {upload_date or 'Unknown'}")
# DEMO CODE REMOVED: print(f"      🔧 Source: {source or 'legacy/fake'}")
        
        print("\n" + "=" * 60)
        
        # Quality assessment
        real_percentage = (stats[1] / stats[0] * 100) if stats[0] > 0 else 0
        metadata_completeness = (stats[3] / stats[0] * 100) if stats[0] > 0 else 0
        
        print("📈 QUALITY ASSESSMENT:")
        print(f"   Real data coverage: {real_percentage:.1f}%")
        print(f"   Metadata completeness: {metadata_completeness:.1f}%")
        
        if real_percentage > 50:
            print("   ✅ GOOD: Majority of videos have real data")
        elif real_percentage > 10:
            print("   ⚠️ PARTIAL: Some videos have real data, continue processing")
        else:
# DEMO CODE REMOVED: print("   ❌ POOR: Most videos still have fake data")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if stats[2] > 0:
            print(f"   🔄 Process remaining {stats[2]} videos with real extraction")
            print("   📋 Run: python3 real_youtube_processor.py")
        
        if real_percentage > 80:
            print("   🎉 Real data extraction is working excellently!")
            print("   ✅ System rebuilt successfully with meaningful information")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ VERIFICATION COMPLETE")
        
        return {
            'total_videos': stats[0],
            'real_data_count': stats[1],
# DEMO CODE REMOVED: 'fake_data_count': stats[2],
            'real_percentage': real_percentage,
            'metadata_completeness': metadata_completeness
        }
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return None

def show_before_after_comparison():
# DEMO CODE REMOVED: """Show the transformation from fake to real data."""
    
    print("\n🔄 BEFORE vs AFTER COMPARISON")
    print("=" * 40)
    
# DEMO CODE REMOVED: print("❌ BEFORE (Fake System):")
    print("   • Only video titles from RSS feeds")
    print("   • No real metadata (duration, views, upload dates)")
    print("   • No transcripts")
    print("   • AI summaries based on titles only")
    print("   • No meaningful video information")
    
    print("\n✅ AFTER (Real System):")
    print("   • Complete video metadata via yt-dlp")
    print("   • Real view counts, like counts, durations")
    print("   • Actual upload dates and channel information")
    print("   • Real transcript extraction")
# DEMO CODE REMOVED: print("   • Proper error handling without fake fallbacks")
    print("   • Meaningful video information for analysis")

if __name__ == "__main__":
    # Run verification
    results = verify_real_data_extraction()
    
    # Show before/after comparison
    show_before_after_comparison()
    
    if results:
        print(f"\n🎯 FINAL SUMMARY:")
        print(f"   Successfully extracted real data for {results['real_data_count']}/{results['total_videos']} videos")
        print(f"   System transformation: {results['real_percentage']:.1f}% complete")
        
        if results['real_percentage'] > 10:
            print("   ✅ Real YouTube processor is working and extracting meaningful information!")
# DEMO CODE REMOVED: print("   🚫 No more fake summaries or error fallouts!")
        else:
            print("   ⚠️ Need to run more real data extraction")