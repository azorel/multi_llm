#!/usr/bin/env python3
"""
YouTube Video Processor - Updated with Working Transcript
=========================================================

Enhanced YouTube processor with reliable transcript extraction.
"""

import re
import json
import asyncio
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Import our working transcript extractor
import sys
import os
sys.path.append(os.path.dirname(__file__))
from youtube_transcript_fixed import create_working_transcript_extractor

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class YouTubeProcessorUpdated:
    """
    Enhanced YouTube processor with reliable transcript extraction.
    """
    
    def __init__(self):
        """Initialize the YouTube processor with working transcript extractor."""
        self.supported_languages = ['en', 'en-US', 'en-GB', 'auto']
        self.transcript_extractor = create_working_transcript_extractor()
        
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats."""
        return self.transcript_extractor.extract_video_id(url)
    
    async def get_video_metadata(self, video_url: str) -> Dict[str, Any]:
        """Get video metadata using yt-dlp or fallback method."""
        try:
            if not yt_dlp:
                logger.warning("yt-dlp not available, using basic metadata extraction")
                return await self._get_basic_metadata(video_url)
            
            video_id = self.extract_video_id(video_url)
            if not video_id:
                return {"error": "Invalid YouTube URL"}
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                    
                    # Parse duration
                    duration_seconds = info.get('duration', 0)
                    duration_formatted = self._format_duration(duration_seconds)
                    
                    metadata = {
                        "video_id": video_id,
                        "title": info.get('title', 'Unknown Title'),
                        "description": info.get('description', ''),
                        "uploader": info.get('uploader', 'Unknown'),
                        "upload_date": info.get('upload_date', ''),
                        "duration_seconds": duration_seconds,
                        "duration_formatted": duration_formatted,
                        "view_count": info.get('view_count', 0),
                        "like_count": info.get('like_count', 0),
                        "thumbnail": info.get('thumbnail', ''),
                        "tags": info.get('tags', []),
                        "categories": info.get('categories', []),
                        "extracted_at": datetime.now().isoformat()
                    }
                    
                    return metadata
                    
                except Exception as e:
                    logger.error(f"yt-dlp extraction failed: {e}")
                    return {"error": f"Failed to extract metadata: {str(e)}"}
                    
        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            return {"error": str(e)}
    
    async def _get_basic_metadata(self, video_url: str) -> Dict[str, Any]:
        """Fallback basic metadata extraction."""
        video_id = self.extract_video_id(video_url)
        if not video_id:
            return {"error": "Invalid YouTube URL"}
        
        return {
            "video_id": video_id,
            "title": "Title extraction requires yt-dlp",
            "url": video_url,
            "extracted_at": datetime.now().isoformat(),
            "metadata_limited": True
        }
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration from seconds to human-readable format."""
        if seconds == 0:
            return "Unknown"
        
        duration = timedelta(seconds=seconds)
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    async def get_transcript(self, video_url: str, languages: List[str] = None) -> Dict[str, Any]:
        """
        Get video transcript using our reliable transcript extractor.
        """
        try:
            logger.info(f"Extracting transcript for: {video_url}")
            
            # Use our working transcript extractor
            result = await self.transcript_extractor.get_transcript_async(video_url)
            
            if result.get("success"):
                logger.info(f"Transcript extracted successfully: {result.get('word_count', 0)} words")
                return result
            else:
                logger.warning(f"Transcript extraction failed: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            logger.error(f"Error getting transcript: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_summary(self, transcript_text: str, max_length: int = 500) -> str:
        """Generate a summary of the transcript."""
        if not transcript_text:
            return "No transcript available for summary"
        
        # Simple extractive summary (first sentences up to max_length)
        words = transcript_text.split()
        if len(words) <= max_length // 5:  # Rough word to char ratio
            return transcript_text
        
        # Take first portion and try to end at sentence boundary
        summary_words = words[:max_length // 5]
        summary = " ".join(summary_words)
        
        # Try to end at a sentence
        last_period = summary.rfind('.')
        if last_period > len(summary) // 2:
            summary = summary[:last_period + 1]
        
        return summary + "..." if len(summary) < len(transcript_text) else summary
    
    async def generate_ai_summary(self, metadata: Dict[str, Any], transcript_text: str = "") -> str:
        """Generate an AI-powered summary for the Knowledge Hub."""
        try:
            title = metadata.get('title', 'Unknown Video')
            channel = metadata.get('uploader', 'Unknown Channel')
            duration = metadata.get('duration_formatted', 'Unknown')
            description = metadata.get('description', '')[:500]  # First 500 chars
            
            # Create structured summary
            summary_parts = []
            
            # Basic info
            summary_parts.append(f"📺 **{title}**")
            summary_parts.append(f"🎬 Channel: {channel} | Duration: {duration}")
            
            # Description insights
            if description:
                desc_preview = description[:200] + "..." if len(description) > 200 else description
                summary_parts.append(f"\n📝 **Description Preview:**\n{desc_preview}")
            
            # Transcript insights
            if transcript_text:
                # Extract key sentences (simple approach)
                sentences = transcript_text.split('.')
                key_sentences = []
                
                # Look for sentences with important keywords
                important_keywords = [
                    'important', 'key', 'crucial', 'essential', 'remember', 'takeaway',
                    'lesson', 'strategy', 'method', 'approach', 'technique', 'tip',
                    'secret', 'principle', 'framework', 'system', 'process', 'step'
                ]
                
                for sentence in sentences[:50]:  # First 50 sentences
                    sentence = sentence.strip()
                    if len(sentence) > 20 and any(keyword in sentence.lower() for keyword in important_keywords):
                        key_sentences.append(sentence)
                        if len(key_sentences) >= 3:
                            break
                
                if key_sentences:
                    summary_parts.append(f"\n🔍 **Key Points:**")
                    for i, sentence in enumerate(key_sentences, 1):
                        summary_parts.append(f"{i}. {sentence.strip()}")
                
                # Word count and reading info
                word_count = len(transcript_text.split())
                reading_time = max(1, word_count // 200)  # ~200 words per minute
                summary_parts.append(f"\n📊 **Content:** {word_count:,} words (~{reading_time} min read)")
            else:
                summary_parts.append(f"\n⚠️ **Transcript:** Not available for this video")
            
            summary_parts.append(f"\n🤖 **Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return f"🤖 AI Summary generation failed: {str(e)}"
    
    async def extract_knowledge_insights(self, metadata: Dict[str, Any], transcript_text: str = "") -> Dict[str, Any]:
        """Extract structured knowledge insights from video content."""
        insights = {
            "key_insights": [],
            "action_items": [],
            "concepts": [],
            "quotes": [],
            "relevance_indicators": [],
            "content_category": "General",
            "difficulty_level": "Unknown",
            "implementation_time": "Unknown"
        }
        
        try:
            title = metadata.get('title', '').lower()
            description = metadata.get('description', '').lower()
            
            # Categorize content based on title and description
            categories = {
                "Business": ['business', 'entrepreneur', 'startup', 'marketing', 'sales', 'revenue', 'profit'],
                "Technology": ['tech', 'ai', 'artificial intelligence', 'software', 'programming', 'code', 'development'],
                "Personal Development": ['productivity', 'habits', 'mindset', 'self-improvement', 'growth', 'learning'],
                "AI & Automation": ['ai', 'automation', 'machine learning', 'artificial intelligence', 'claude', 'gpt'],
                "LifeOS": ['notion', 'organization', 'system', 'workflow', 'productivity system', 'lifeos']
            }
            
            content_text = f"{title} {description}".lower()
            for category, keywords in categories.items():
                if any(keyword in content_text for keyword in keywords):
                    insights["content_category"] = category
                    break
            
            # Assess difficulty level
            complexity_indicators = {
                "Beginner": ['intro', 'basic', 'getting started', 'beginner', 'simple', 'easy'],
                "Intermediate": ['intermediate', 'advanced', 'deep dive', 'comprehensive', 'detailed'],
                "Advanced": ['expert', 'advanced', 'complex', 'technical', 'professional', 'enterprise']
            }
            
            for level, indicators in complexity_indicators.items():
                if any(indicator in content_text for indicator in indicators):
                    insights["difficulty_level"] = level
                    break
            
            # Estimate implementation time based on content
            duration_seconds = metadata.get('duration_seconds', 0)
            if duration_seconds > 0:
                if duration_seconds < 600:  # < 10 minutes
                    insights["implementation_time"] = "Quick (< 1h)"
                elif duration_seconds < 1800:  # < 30 minutes
                    insights["implementation_time"] = "Medium (1-4h)"
                else:
                    insights["implementation_time"] = "Long (> 4h)"
            
            # Extract insights from transcript
            if transcript_text:
                # Look for actionable content
                action_patterns = [
                    r'you should ([^.]+)',
                    r'you need to ([^.]+)',
                    r'make sure you ([^.]+)',
                    r'the first step is ([^.]+)',
                    r'start by ([^.]+)',
                    r'remember to ([^.]+)'
                ]
                
                for pattern in action_patterns:
                    matches = re.findall(pattern, transcript_text.lower(), re.IGNORECASE)
                    for match in matches[:3]:  # Limit to first 3 matches per pattern
                        insights["action_items"].append(match.strip())
                
                # Extract potential quotes (sentences with impact words)
                sentences = transcript_text.split('.')
                quote_keywords = ['important', 'remember', 'key', 'crucial', 'secret', 'truth', 'fact']
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if (len(sentence) > 30 and len(sentence) < 150 and 
                        any(keyword in sentence.lower() for keyword in quote_keywords)):
                        insights["quotes"].append(f'"{sentence}"')
                        if len(insights["quotes"]) >= 3:
                            break
                
                # Extract concepts (capitalized terms that might be important)
                concept_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
                concepts = re.findall(concept_pattern, transcript_text)
                # Filter out common phrases
                filtered_concepts = [c for c in concepts if c not in ['YouTube Video', 'United States', 'New York']]
                insights["concepts"] = list(set(filtered_concepts))[:5]
            
            # Determine relevance indicators
            relevance_keywords = {
                'High Priority': ['urgent', 'critical', 'important', 'essential', 'must-know'],
                'Learning': ['tutorial', 'how-to', 'guide', 'learn', 'course', 'education'],
                'Implementation': ['actionable', 'practical', 'step-by-step', 'framework', 'system'],
                'Reference': ['reference', 'documentation', 'resource', 'tool', 'library']
            }
            
            for relevance_type, keywords in relevance_keywords.items():
                if any(keyword in content_text for keyword in keywords):
                    insights["relevance_indicators"].append(relevance_type)
            
        except Exception as e:
            logger.error(f"Error extracting knowledge insights: {e}")
            insights["error"] = str(e)
        
        return insights
    
    async def generate_hashtags(self, metadata: Dict[str, Any], insights: Dict[str, Any]) -> List[str]:
        """Generate relevant hashtags for the content."""
        hashtags = set()
        
        try:
            title = metadata.get('title', '').lower()
            description = metadata.get('description', '').lower()
            category = insights.get('content_category', '').lower()
            
            # Base hashtags from category
            category_tags = {
                'business': ['#business', '#entrepreneur'],
                'technology': ['#technology', '#tech'],
                'personal development': ['#productivity', '#development'],
                'ai & automation': ['#ai', '#automation'],
                'lifeos': ['#lifeos', '#productivity']
            }
            
            if category in category_tags:
                hashtags.update(category_tags[category])
            
            # Content-based hashtags
            content_text = f"{title} {description}"
            
            tag_keywords = {
                '#tutorial': ['tutorial', 'how-to', 'guide', 'walkthrough'],
                '#learning': ['learn', 'education', 'course', 'training'],
                '#inspiration': ['motivation', 'inspire', 'success', 'growth'],
                '#reference': ['reference', 'documentation', 'resource'],
                '#video-content': ['video', 'youtube'],  # Always add for YouTube
                '#ai': ['ai', 'artificial intelligence', 'claude', 'gpt'],
                '#productivity': ['productivity', 'efficient', 'workflow', 'system'],
                '#business': ['business', 'startup', 'marketing', 'sales'],
                '#development': ['development', 'programming', 'coding', 'software']
            }
            
            for tag, keywords in tag_keywords.items():
                if any(keyword in content_text for keyword in keywords):
                    hashtags.add(tag)
            
            # Ensure we have video-content tag for all YouTube videos
            hashtags.add('#video-content')
            
            # Limit to reasonable number
            return list(hashtags)[:8]
            
        except Exception as e:
            logger.error(f"Error generating hashtags: {e}")
            return ['#video-content']
    
    async def process_video(self, video_url: str) -> Dict[str, Any]:
        """Complete video processing: metadata + transcript + analysis."""
        logger.info(f"🎬 Processing YouTube video: {video_url}")
        
        results = {
            "url": video_url,
            "processed_at": datetime.now().isoformat(),
            "success": False
        }
        
        try:
            # Get metadata
            logger.info("📊 Extracting video metadata...")
            metadata = await self.get_video_metadata(video_url)
            results["metadata"] = metadata
            
            if "error" in metadata:
                logger.error(f"Metadata extraction failed: {metadata['error']}")
                # Continue with basic metadata
                video_id = self.extract_video_id(video_url)
                metadata = {
                    "video_id": video_id,
                    "title": "Unknown Video",
                    "uploader": "Unknown Channel",
                    "duration_formatted": "Unknown",
                    "description": "",
                    "extracted_at": datetime.now().isoformat()
                }
                results["metadata"] = metadata
            
            # Get transcript using our working extractor
            logger.info("📝 Extracting video transcript...")
            transcript_result = await self.get_transcript(video_url)
            results["transcript"] = transcript_result
            
            if transcript_result.get("success"):
                transcript_text = transcript_result.get("full_text", "")
                logger.info(f"✅ Transcript extracted: {len(transcript_text.split())} words")
            else:
                logger.warning(f"⚠️ Transcript extraction failed: {transcript_result.get('error', 'Unknown error')}")
                transcript_text = ""
            
            # Generate enhanced analysis
            logger.info("🧠 Generating enhanced content analysis...")
            
            # AI Summary for Knowledge Hub
            ai_summary = await self.generate_ai_summary(metadata, transcript_text)
            
            # Extract knowledge insights
            knowledge_insights = await self.extract_knowledge_insights(metadata, transcript_text)
            
            # Generate hashtags
            hashtags = await self.generate_hashtags(metadata, knowledge_insights)
            
            # Basic analysis
            if transcript_text:
                summary = await self.generate_summary(transcript_text)
                
                results["analysis"] = {
                    "summary": summary,
                    "word_count": len(transcript_text.split()),
                    "has_transcript": True
                }
            else:
                results["analysis"] = {
                    "summary": "No transcript available for analysis",
                    "word_count": 0,
                    "has_transcript": False
                }
            
            # Enhanced Knowledge Hub data
            results["knowledge_hub"] = {
                "ai_summary": ai_summary,
                **knowledge_insights,
                "hashtags": hashtags
            }
            
            results["success"] = True
            results["content_type"] = "YouTube"
            logger.info("✅ Enhanced video processing completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Video processing failed: {e}")
            results["error"] = str(e)
        
        return results


# Factory function
def create_youtube_processor_updated() -> YouTubeProcessorUpdated:
    """Create an updated YouTube processor instance."""
    return YouTubeProcessorUpdated()


# CLI interface for testing
async def main():
    """Test the updated YouTube processor."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python youtube_processor_updated.py <youtube_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    processor = create_youtube_processor_updated()
    
    print(f"🎬 Processing YouTube video: {url}")
    print("=" * 70)
    
    result = await processor.process_video(url)
    
    if result["success"]:
        print("✅ Processing completed successfully!")
        
        if "metadata" in result:
            meta = result["metadata"]
            print(f"\n📊 Metadata:")
            print(f"   Title: {meta.get('title', 'Unknown')}")
            print(f"   Duration: {meta.get('duration_formatted', 'Unknown')}")
            print(f"   Uploader: {meta.get('uploader', 'Unknown')}")
            print(f"   Views: {meta.get('view_count', 0):,}")
        
        if "transcript" in result and result["transcript"].get("success"):
            trans = result["transcript"]
            print(f"\n📝 Transcript:")
            print(f"   Method: {trans.get('extraction_method', 'Unknown')}")
            print(f"   Type: {trans.get('transcript_type', 'Unknown')}")
            print(f"   Word count: {trans.get('word_count', 0):,}")
            print(f"   Segments: {trans.get('segment_count', 0)}")
        
        if "knowledge_hub" in result:
            kb = result["knowledge_hub"]
            print(f"\n🧠 Knowledge Hub:")
            print(f"   Category: {kb.get('content_category', 'Unknown')}")
            print(f"   Difficulty: {kb.get('difficulty_level', 'Unknown')}")
            print(f"   Hashtags: {', '.join(kb.get('hashtags', []))}")
            
            if kb.get("action_items"):
                print(f"   Action Items: {len(kb['action_items'])}")
    else:
        print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())