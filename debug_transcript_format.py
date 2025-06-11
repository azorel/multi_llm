#!/usr/bin/env python3
"""Debug transcript format issue"""

from youtube_transcript_api import YouTubeTranscriptApi

video_id = "y-_xknNOapo"  # One that worked with Method 1

def debug_transcript_format():
    print(f"Testing video: {video_id}")
    
    # Test Method 1 (direct)
    try:
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        print(f"✅ Method 1 - Direct:")
        print(f"Type: {type(transcript_data)}")
        print(f"Length: {len(transcript_data)}")
        if len(transcript_data) > 0:
            print(f"First entry type: {type(transcript_data[0])}")
            print(f"First entry: {transcript_data[0]}")
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    # Test Method 2 (list_transcripts)
    try:
        transcript_list_obj = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list_obj:
            try:
                transcript_data = transcript.fetch()
                print(f"\\n✅ Method 2 - List transcripts:")
                print(f"Type: {type(transcript_data)}")
                if hasattr(transcript_data, '__len__'):
                    print(f"Length: {len(transcript_data)}")
                if hasattr(transcript_data, '__iter__'):
                    first_entry = next(iter(transcript_data))
                    print(f"First entry type: {type(first_entry)}")
                    print(f"First entry: {first_entry}")
                    if hasattr(first_entry, '__dict__'):
                        print(f"Attributes: {vars(first_entry)}")
                break
            except Exception as e:
                print(f"❌ Method 2 inner failed: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")

if __name__ == "__main__":
    debug_transcript_format()