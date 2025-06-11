#!/usr/bin/env python3
"""Debug transcript issues"""

from youtube_transcript_api import YouTubeTranscriptApi

video_ids = [
    "mKEq_YaJjPI",  # How I build Agentic MCP Servers for Claude Code
    "f8RnRuaxee8",  # Claude 4 ADVANCED AI Coding: Git Worktrees
    "y-_xknNOapo"   # Claude Code INSIDERS: Codex FIRST Look
]

def test_transcript_methods(video_id):
    print(f"\\n🎬 Testing video: {video_id}")
    
    # Method 1: Direct transcript
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        print(f"✅ Direct transcript: {len(transcript)} entries")
        return True
    except Exception as e:
        print(f"❌ Direct failed: {e}")
    
    # Method 2: Try different languages
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        print(f"✅ English transcript: {len(transcript)} entries")
        return True
    except Exception as e:
        print(f"❌ English failed: {e}")
    
    # Method 3: Try auto-generated
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en-US'])
        print(f"✅ EN-US transcript: {len(transcript)} entries")
        return True
    except Exception as e:
        print(f"❌ EN-US failed: {e}")
    
    # Method 4: List available transcripts
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        print(f"📋 Available transcripts:")
        for transcript in transcript_list:
            print(f"   - {transcript.language_code}: {transcript.language}")
        return False
    except Exception as e:
        print(f"❌ List failed: {e}")
        return False

if __name__ == "__main__":
    for video_id in video_ids:
        success = test_transcript_methods(video_id)
        if success:
            break