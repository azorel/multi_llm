#!/usr/bin/env python3
"""
Fixed YouTube Transcript Extractor - Working Solution
=====================================================

This module provides working YouTube transcript extraction using multiple methods:
1. Web scraping (always available)
2. youtube-transcript-api (if available)
3. yt-dlp (if available)
"""

import re
import json
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime
import asyncio

class WorkingYouTubeTranscriptExtractor:
    """
    A robust YouTube transcript extractor that works without additional dependencies.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats."""
        if not url:
            return None
            
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/watch\?.*v=([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If it's already just a video ID
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url
            
        return None
    
    def get_transcript_via_web_scraping(self, video_id: str) -> Dict[str, Any]:
        """
        Extract transcript via web scraping - most reliable method.
        """
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            html = response.text
            
            # Look for caption tracks in the page
            patterns = [
                r'"captionTracks":\s*(\[.*?\])',
                r'"captions".*?"playerCaptionsTracklistRenderer".*?"captionTracks":\s*(\[.*?\])',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    try:
                        caption_tracks = json.loads(match.group(1))
                        
                        # Find English track
                        english_track = None
                        for track in caption_tracks:
                            lang_code = track.get('languageCode', '')
                            if lang_code.startswith('en') or track.get('kind') == 'asr':
                                english_track = track
                                break
                        
                        if not english_track:
                            continue
                            
                        # Get the transcript URL
                        base_url = english_track.get('baseUrl')
                        if not base_url:
                            continue
                        
                        # Fetch the actual transcript
                        transcript_response = self.session.get(base_url, timeout=10)
                        if transcript_response.status_code == 200:
                            return self._parse_transcript_xml(transcript_response.text, video_id)
                            
                    except (json.JSONDecodeError, KeyError) as e:
                        continue
            
            return {"success": False, "error": "No transcript data found in page"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_transcript_xml(self, xml_content: str, video_id: str) -> Dict[str, Any]:
        """Parse YouTube's transcript XML format."""
        try:
            # Clean up the XML content
            xml_content = xml_content.replace('&nbsp;', ' ')
            
            root = ET.fromstring(xml_content)
            
            transcript_segments = []
            full_text = ""
            
            for text_elem in root.findall('.//text'):
                start_time = float(text_elem.get('start', 0))
                duration = float(text_elem.get('dur', 0))
                text_content = text_elem.text or ""
                
                # Decode HTML entities
                text_content = self._decode_html_entities(text_content)
                text_content = text_content.strip()
                
                if text_content:
                    transcript_segments.append({
                        "start": start_time,
                        "duration": duration,
                        "text": text_content,
                        "timestamp": self._format_timestamp(start_time)
                    })
                    
                    full_text += text_content + " "
            
            full_text = full_text.strip()
            word_count = len(full_text.split()) if full_text else 0
            
            return {
                "success": True,
                "video_id": video_id,
                "transcript_type": "auto-generated",
                "language": "en",
                "full_text": full_text,
                "formatted_transcript": transcript_segments,
                "word_count": word_count,
                "segment_count": len(transcript_segments),
                "extracted_at": datetime.now().isoformat(),
                "method": "web_scraping"
            }
            
        except ET.ParseError as e:
            return {"success": False, "error": f"XML parsing error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Transcript parsing error: {str(e)}"}
    
    def _decode_html_entities(self, text: str) -> str:
        """Decode common HTML entities."""
        replacements = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
        }
        
        for entity, replacement in replacements.items():
            text = text.replace(entity, replacement)
        
        return text
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp from seconds to MM:SS or HH:MM:SS format."""
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def get_transcript_via_api(self, video_id: str) -> Dict[str, Any]:
        """Try to get transcript via YouTube Transcript API if available."""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try manual transcript first
            try:
                transcript = transcript_list.find_manually_created_transcript(['en'])
                data = transcript.fetch()
                return self._format_api_transcript(data, video_id, "manual")
            except:
                pass
            
            # Try auto-generated
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
                data = transcript.fetch()
                return self._format_api_transcript(data, video_id, "auto-generated")
            except:
                pass
            
            return {"success": False, "error": "No English transcript available", "method": "youtube_transcript_api"}
            
        except ImportError:
            return {"success": False, "error": "youtube_transcript_api not available", "method": "youtube_transcript_api"}
        except Exception as e:
            return {"success": False, "error": str(e), "method": "youtube_transcript_api"}
    
    def _format_api_transcript(self, data: List[Dict], video_id: str, transcript_type: str) -> Dict[str, Any]:
        """Format transcript data from YouTube Transcript API."""
        try:
            full_text = ""
            formatted_transcript = []
            
            for entry in data:
                text = entry.get('text', '').strip()
                start_time = entry.get('start', 0)
                duration = entry.get('duration', 0)
                
                if text:
                    formatted_transcript.append({
                        "start": start_time,
                        "duration": duration,
                        "text": text,
                        "timestamp": self._format_timestamp(start_time)
                    })
                    
                    full_text += text + " "
            
            full_text = full_text.strip()
            word_count = len(full_text.split()) if full_text else 0
            
            return {
                "success": True,
                "video_id": video_id,
                "transcript_type": transcript_type,
                "language": "en",
                "full_text": full_text,
                "formatted_transcript": formatted_transcript,
                "word_count": word_count,
                "segment_count": len(formatted_transcript),
                "extracted_at": datetime.now().isoformat(),
                "method": "youtube_transcript_api"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "method": "youtube_transcript_api"}
    
    def get_transcript(self, video_url: str) -> Dict[str, Any]:
        """
        Get transcript using the best available method.
        
        Args:
            video_url: YouTube video URL or video ID
            
        Returns:
            Dictionary with transcript data or error information
        """
        video_id = self.extract_video_id(video_url)
        if not video_id:
            return {"success": False, "error": "Invalid YouTube URL or video ID"}
        
        # Try methods in order of preference
        methods = [
            ("YouTube Transcript API", self.get_transcript_via_api),
            ("Web Scraping", self.get_transcript_via_web_scraping),
        ]
        
        last_error = "No methods available"
        
        for method_name, method_func in methods:
            try:
                result = method_func(video_id)
                if result.get("success"):
                    result["extraction_method"] = method_name
                    return result
                else:
                    last_error = f"{method_name}: {result.get('error', 'Unknown error')}"
            except Exception as e:
                last_error = f"{method_name}: {str(e)}"
                continue
        
        return {
            "success": False,
            "error": f"All methods failed. Last error: {last_error}",
            "video_id": video_id
        }
    
    async def get_transcript_async(self, video_url: str) -> Dict[str, Any]:
        """Async version of get_transcript."""
        # For now, just run sync version in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_transcript, video_url)


# Factory function for easy integration
def create_working_transcript_extractor() -> WorkingYouTubeTranscriptExtractor:
    """Create a working YouTube transcript extractor instance."""
    return WorkingYouTubeTranscriptExtractor()


# Test function
def test_transcript_extraction():
# DEMO CODE REMOVED: """Test the transcript extraction with sample videos."""
    extractor = create_working_transcript_extractor()
    
    test_videos = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo
    ]
    
    for video_url in test_videos:
        print(f"\n🧪 Testing: {video_url}")
        print("-" * 50)
        
        result = extractor.get_transcript(video_url)
        
        if result["success"]:
            print(f"✅ SUCCESS!")
            print(f"   Method: {result.get('extraction_method', 'Unknown')}")
            print(f"   Type: {result.get('transcript_type', 'Unknown')}")
            print(f"   Words: {result.get('word_count', 0):,}")
            print(f"   Segments: {result.get('segment_count', 0)}")
            
            # Show first few words
            full_text = result.get('full_text', '')
            preview = full_text[:100] + "..." if len(full_text) > 100 else full_text
            print(f"   Preview: {preview}")
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    test_transcript_extraction()