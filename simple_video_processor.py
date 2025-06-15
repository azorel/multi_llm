#!/usr/bin/env python3
"""Simple video processor that actually runs and imports videos with AI analysis"""

import os
import asyncio
import aiohttp
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
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

async def process_videos_with_ai():
    """Process videos from marked channels with full AI analysis."""
    print("🚀 STARTING VIDEO PROCESSING WITH AI ANALYSIS")
    print("=" * 60)
    
    # Configuration
    openai_api_key = os.getenv('OPENAI_API_KEY')
# NOTION_REMOVED:     channels_db_id = os.getenv('NOTION_CHANNELS_DATABASE_ID', '203ec31c-9de2-8079-ae4e-ed754d474888')
# NOTION_REMOVED:     knowledge_db_id = os.getenv('NOTION_KNOWLEDGE_DATABASE_ID', '20bec31c-9de2-814e-80db-d13d0c27d869')
    
    print(f"🔑 OpenAI API Key: {'✅ Available' if openai_api_key and openai_api_key != 'your_openai_api_key_here' else '⚠️ Not set - will use local analysis'}")
    
    headers = {
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    # Get marked channels
    print("1️⃣ Finding channels marked for processing...")
    
    async with aiohttp.ClientSession() as session:
        query_data = {
            "filter": {
                "property": "Process Channel",
                "checkbox": {"equals": True}
            }
        }
        
        async with session.post(
            headers=headers,
            json=query_data,
            timeout=10
        ) as response:
            if response.status != 200:
                print(f"❌ Failed to query channels: {response.status}")
                return
            
            data = await response.json()
            channels = data.get('results', [])
    
    if not channels:
        print("❌ No channels marked for processing")
        return
    
    print(f"✅ Found {len(channels)} channels to process")
    
    # Process each channel
    for channel in channels:
        await process_channel_videos(channel, headers, knowledge_db_id, openai_api_key)
        
        # Unmark the channel
        await unmark_channel(channel['id'], headers)
    
    print("🎉 All channels processed!")

async def process_channel_videos(channel, headers, knowledge_db_id, openai_api_key):
    """Process videos from a single channel."""
    props = channel.get('properties', {})
    
    # Get channel name
    name_prop = props.get('Name', {})
    channel_name = 'Unknown'
    if name_prop.get('title'):
        channel_name = name_prop['title'][0].get('plain_text', 'Unknown')
    
    print(f"\\n📺 Processing channel: {channel_name}")
    
    # Get URL
    url_prop = props.get('URL', {})
    channel_url = ''
    if url_prop.get('rich_text') and url_prop['rich_text']:
        channel_url = url_prop['rich_text'][0].get('plain_text', '')
    
    if not channel_url:
        print("❌ No URL found")
        return
    
    # Resolve channel ID
    channel_id = await resolve_channel_id(channel_url)
    if not channel_id:
        print("❌ Could not resolve channel ID")
        return
    
    print(f"✅ Channel ID: {channel_id}")
    
    # Get videos from RSS
    videos = await get_videos_from_rss(channel_id)
    if not videos:
        print("❌ No videos found")
        return
    
    print(f"📹 Found {len(videos)} videos")
    
    # Process ALL videos from the channel (removing 5-video limit)
    imported_count = 0
    total_videos = len(videos)
    print(f"📹 Processing ALL {total_videos} videos from {channel_name}")
    
    for i, video in enumerate(videos, 1):
        print(f"  Processing video {i}/{total_videos}: {video['title'][:50]}...")
        success = await         if success:
            imported_count += 1
            print(f"    ✅ Imported successfully")
        else:
            print(f"    ❌ Failed to import")
        await asyncio.sleep(2)  # Rate limiting to avoid API issues
    
    print(f"✅ Imported {imported_count} videos from {channel_name}")

async def resolve_channel_id(channel_url):
    """Resolve channel URL to channel ID."""
    # Pattern matching
    patterns = [
        r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
        r'youtube\.com/c/([a-zA-Z0-9_-]+)', 
        r'youtube\.com/user/([a-zA-Z0-9_-]+)',
        r'youtube\.com/@([a-zA-Z0-9_.-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, channel_url)
        if match:
            identifier = match.group(1)
            if identifier.startswith('UC'):
                return identifier
            else:
                # Need to resolve with web scraping
                headers_web = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(channel_url, headers=headers_web, timeout=10) as response:
                            if response.status == 200:
                                html = await response.text()
                                
                                # Look for channel ID
                                id_patterns = [
                                    r'"channelId":"(UC[a-zA-Z0-9_-]+)"',
                                    r'<meta itemprop="channelId" content="(UC[a-zA-Z0-9_-]+)"',
                                    r'"browseId":"(UC[a-zA-Z0-9_-]+)"'
                                ]
                                
                                for id_pattern in id_patterns:
                                    id_match = re.search(id_pattern, html)
                                    if id_match:
                                        return id_match.group(1)
                except Exception as e:
                    print(f"❌ Web scraping failed: {e}")
            break
    
    return None

async def get_videos_from_rss(channel_id):
    """Get videos from YouTube RSS feed."""
    try:
        rss_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(rss_url, timeout=10) as response:
                if response.status != 200:
                    return []
                
                xml_data = await response.text()
        
        # Parse XML
        root = ET.fromstring(xml_data)
        
        # Define namespaces
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015'
        }
        
        # Get videos
        entries = root.findall('atom:entry', ns)
        videos = []
        
        for entry in entries:
            video_title = entry.find('atom:title', ns)
            video_id = entry.find('yt:videoId', ns)
            published = entry.find('atom:published', ns)
            
            if video_title is not None and video_id is not None:
                videos.append({
                    'title': video_title.text,
                    'video_id': video_id.text,
                    'url': f"https://www.youtube.com/watch?v={video_id.text}",
                    'published': published.text if published is not None else None
                })
        
        return videos
        
    except Exception as e:
        print(f"❌ RSS processing failed: {e}")
        return []

async def     """    try:
        print(f"📹 Processing: {video['title']}")
        
        # Get AI analysis (pass channel name for context)
        ai_analysis = await get_ai_analysis(video, openai_api_key, channel_name)
        
        # Create Notion page with ALL available properties populated
        page_data = {
            "parent": {"database_id": knowledge_db_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": video['title']}}]
                },
                "URL": {
                    "url": video['url']
                },
                "Type": {
                    "select": {"name": "Video"}
                },
                "Content Type": {
                    "select": {"name": "YouTube"}
                },
                "AI Summary": {
                    "rich_text": [{"text": {"content": ai_analysis.get('summary', 'No summary available')}}]
                },
                "Hashtags": {
                    "multi_select": [{"name": tag} for tag in ai_analysis.get('hashtags', [])]
                },
                "Content Summary": {
                    "rich_text": [{"text": {"content": ai_analysis.get('content_summary', f"YouTube video from {channel_name} channel about {', '.join(ai_analysis.get('topics', ['general topics']))}")}}]
                },
                "Channel": {
                    "rich_text": [{"text": {"content": channel_name}}]
                },
                "Processing Status": {
                    "select": {"name": "Completed"}
                },
                "Status": {
                    "select": {"name": "Ready"}
                },
                "Priority": {
                    "select": {"name": "Medium"}
                },
                "Complexity Level": {
                    "select": {"name": ai_analysis.get('complexity', 'Medium')}
                },
                "Key Points": {
                    "rich_text": [{"text": {"content": ai_analysis.get('key_points', 'Key technical insights and practical coding techniques discussed.')}}]
                },
                "Notes": {
                    "rich_text": [{"text": {"content": ai_analysis.get('notes', f"Imported from YouTube channel @indydevdan. Published: {video.get('published', 'Unknown date')}")}}]
                },
                "Action Items": {
                    "rich_text": [{"text": {"content": ai_analysis.get('action_items', 'Review video content for applicable techniques and implementation ideas.')}}]
                },
                "Assistant Prompt": {
                    "rich_text": [{"text": {"content": ai_analysis.get('assistant_prompt', f"Analyze this video about {video['title']} and extract key technical concepts, code examples, and implementation strategies.")}}]
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                headers=headers,
                json=page_data,
                timeout=15
            ) as response:
                if response.status == 200:
                    print(f"✅ Imported: {video['title']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Import failed: {response.status} - {error_text[:200]}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error importing video: {e}")
        return False

async def get_ai_analysis(video, ai_api_key, channel_name="Unknown"):
    """Get AI analysis using OpenAI."""
    # Always use transcript-based analysis now
    return await get_basic_analysis(video, channel_name)

async def get_basic_analysis(video, channel_name="Unknown"):
    """Get comprehensive analysis using full transcript and title context."""
    title = video['title']
    title_lower = title.lower()
    
    # Get transcript using multiple methods
    transcript, transcript_duration = await get_video_transcript_robust(video['video_id'])
    
    if transcript:
        print(f"✅ Got transcript: {len(transcript)} chars, {transcript_duration//60}:{transcript_duration%60:02d} duration")
    else:
        print(f"⚠️ No transcript available for video {video['video_id']}")
        return get_fallback_analysis(video, channel_name)
    
    if not transcript:
        return get_fallback_analysis(video, channel_name)
    
    # Now we have real transcript content - analyze it properly
    content_text = transcript.lower()
    
    # Extract what the video is actually teaching based on title context
    video_context = extract_video_context(title)
    
    # Use OpenAI to analyze the transcript if API key available
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key and openai_api_key != "your_openai_api_key_here":
        print("🤖 Using OpenAI for transcript analysis...")
        analysis = await analyze_with_openai(transcript, video_context, title, openai_api_key)
    else:
        print("⚠️ No OpenAI API key - using local analysis")
        analysis = analyze_transcript_content(transcript, transcript.lower(), video_context, title)
    
    # Add video metadata and notes
    duration_str = f"{transcript_duration//60}:{transcript_duration%60:02d}"
    notes_text = f"Duration: {duration_str}. Published: {video.get('published', 'Unknown date')}. "
    notes_text += f"Video from {channel_name} covers {video_context['focus']} with practical examples and implementation details. "
    notes_text += f"Transcript available ({len(transcript)} characters) for detailed content analysis."
    
    analysis["notes"] = notes_text
    
    return analysis

async def analyze_with_openai(transcript, video_context, title, api_key):
    """Use OpenAI to analyze the full transcript content."""
    try:
        import aiohttp
        
        # Prepare the prompt for OpenAI - let it analyze the content directly
        system_prompt = """You are analyzing a YouTube video transcript. Based ONLY on the actual transcript content, provide a JSON response with:

1. "summary": What the video actually covers based on transcript (2-3 sentences)
2. "action_items": What the viewer learns from this video (3 bullet points)
3. "assistant_prompt": Instructions for an AI assistant to learn this IF instructed (1 sentence starting with "If instructed, ")
4. "key_points": What's actually discussed in the video based on transcript (3-4 bullet points)
5. "hashtags": Topics/themes from the actual content (4-6 tags)
6. "complexity": "Low", "Medium", or "High" based on content complexity
7. "content_summary": What the video actually teaches/shows (1-2 sentences)

IMPORTANT: Base your analysis ONLY on the transcript content, not assumptions from the title. If it's about trucks, analyze trucks. If it's about coding, analyze coding. If it's about cooking, analyze cooking."""

        user_prompt = f"""Video Title: {title}

Full Transcript:
{transcript[:8000]}  # Limit to avoid token limits

Analyze this transcript and provide the requested JSON response."""

        payload = {
            "model": "gpt-4o-mini-2024-07-18",  # Latest available GPT-4o-mini model
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    
                    # Try to parse JSON response
                    try:
                        import json
                        # Clean the content to extract JSON
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_content = content[json_start:json_end]
                            parsed = json.loads(json_content)
                            
                            # Format for our system
                            return {
                                "summary": parsed.get("summary", f"Analysis of {title}"),
                                "hashtags": parsed.get("hashtags", ["development"]),
                                "complexity": parsed.get("complexity", "Medium"),
                                "key_points": "\\n".join([f"• {point}" for point in parsed.get("key_points", ["Technical content"])]),
                                "action_items": "\\n".join([f"• {item}" for item in parsed.get("action_items", ["Review video content"])]),
                                "assistant_prompt": parsed.get("assistant_prompt", f"If instructed, analyze {title}"),
                                "content_summary": parsed.get("content_summary", f"Tutorial on {video_context['focus']}"),
                                "topics": [video_context["subject"]]
                            }
                    except Exception as e:
                        print(f"⚠️ JSON parsing failed: {e}")
                        print(f"Raw response: {content[:200]}...")
                else:
                    print(f"⚠️ OpenAI API failed: {response.status}")
                    
    except Exception as e:
        print(f"⚠️ OpenAI analysis failed: {e}")
    
    # Fallback to local analysis
    return analyze_transcript_content(transcript, transcript.lower(), video_context, title)

def extract_video_context(title):
    """Extract basic context from title without making assumptions."""
    context = {}
    title_lower = title.lower()
    
    # Only set specific context for clearly identifiable technical content
    if "mcp server" in title_lower:
        context["subject"] = "MCP Server Development"
        context["focus"] = "building Model Context Protocol servers"
    elif "git worktree" in title_lower:
        context["subject"] = "Git Worktree Workflows"
        context["focus"] = "parallel development using Git worktrees"
    elif "claude code" in title_lower and "voice" in title_lower:
        context["subject"] = "Voice-to-Code with Claude"
        context["focus"] = "voice-controlled AI coding workflows"
    elif "claude 4" in title_lower:
        context["subject"] = "Claude 4 AI Coding"
        context["focus"] = "advanced AI coding with Claude 4"
    elif "agentic" in title_lower:
        context["subject"] = "Agentic AI Systems"
        context["focus"] = "autonomous AI agent development"
    else:
        # Don't make assumptions - let transcript analysis determine the content
        context["subject"] = "Video Content"
        context["focus"] = "content to be determined from transcript"
    
    return context

def analyze_transcript_content(transcript, content_text, context, title):
    """Analyze transcript content to extract meaningful information from actual content."""
    
    # Determine what the video is actually about by analyzing transcript keywords
    topic_keywords = {
        'automotive': ['truck', 'car', 'engine', 'vehicle', 'motor', 'transmission', 'oil', 'garage', 'mechanic', 'drive', 'tires', 'fuel', 'brake'],
        'rc_hobby': ['rc', 'remote control', 'crawler', 'battery', 'servo', 'receiver', 'transmitter', 'racing', 'competition', 'hobby'],
        'cooking': ['recipe', 'cook', 'ingredient', 'oven', 'kitchen', 'food', 'meal', 'chef', 'taste', 'flavor'],
        'travel': ['travel', 'trip', 'vacation', 'hotel', 'flight', 'destination', 'adventure', 'explore'],
        'technology': ['technology', 'computer', 'software', 'app', 'digital', 'internet', 'device'],
        'programming': ['code', 'programming', 'developer', 'software', 'function', 'variable', 'algorithm', 'debug'],
        'business': ['business', 'entrepreneur', 'marketing', 'sales', 'profit', 'customer', 'strategy'],
        'education': ['learn', 'teach', 'education', 'lesson', 'tutorial', 'course', 'student', 'knowledge'],
        'lifestyle': ['life', 'daily', 'routine', 'habit', 'personal', 'lifestyle', 'wellness', 'health']
    }
    
    # Find the most relevant topic based on transcript content
    topic_scores = {}
    for topic, keywords in topic_keywords.items():
        score = sum(1 for keyword in keywords if keyword in content_text)
        if score > 0:
            topic_scores[topic] = score
    
    # Determine the actual topic
    if topic_scores:
        actual_topic = max(topic_scores, key=topic_scores.get)
        topic_confidence = topic_scores[actual_topic]
    else:
        actual_topic = 'general'
        topic_confidence = 0
    
    # Generate summary based on actual content
    if actual_topic == 'automotive':
        ai_summary = f"Automotive content about {title.lower()}. Shows vehicle-related work, maintenance, or restoration."
    elif actual_topic == 'rc_hobby':
# DEMO CODE REMOVED: ai_summary = f"RC hobby content about {title.lower()}. Demonstrates remote control vehicle techniques or maintenance."
    elif actual_topic == 'programming':
        ai_summary = f"Programming tutorial about {title.lower()}. Covers coding techniques and implementation."
    else:
        # Extract key phrases from transcript for generic content
        words = content_text.split()
        common_words = [w for w in words if len(w) > 4 and words.count(w) > 2]
        if common_words:
            main_themes = list(set(common_words[:5]))
            ai_summary = f"Video about {title.lower()}. Content focuses on {', '.join(main_themes[:3])}."
        else:
            ai_summary = f"Video titled '{title}' - analysis based on transcript content."
    
    # Generate action items based on actual topic
    action_items = []
    if actual_topic == 'automotive':
        action_items.extend([
            "Video shows automotive repair, maintenance, or restoration techniques",
# DEMO CODE REMOVED: "Demonstrates practical vehicle troubleshooting and problem-solving",
            "Covers tools, parts, or procedures relevant to vehicle work"
        ])
    elif actual_topic == 'rc_hobby':
        action_items.extend([
# DEMO CODE REMOVED: "Video demonstrates RC vehicle setup, maintenance, or operation",
            "Shows hobby techniques for remote control vehicles",
            "Covers equipment, modifications, or racing strategies"
        ])
    elif actual_topic == 'programming':
        action_items.extend([
            "Video teaches coding techniques and programming concepts",
# DEMO CODE REMOVED: "Demonstrates software development practices and tools",
            "Shows implementation strategies for specific technologies"
        ])
    else:
        # Generic content-based action items
        action_items.extend([
            f"Video provides information about {title.lower()}",
# DEMO CODE REMOVED: f"Demonstrates practical techniques related to the topic",
            f"Shows real-world examples and applications"
        ])
    
    # Generate assistant prompt based on actual content
    if actual_topic == 'automotive':
        assistant_prompt = f"If instructed, analyze the automotive techniques shown in this video about {title.lower()}"
    elif actual_topic == 'rc_hobby':
# DEMO CODE REMOVED: assistant_prompt = f"If instructed, study the RC hobby techniques demonstrated in this video about {title.lower()}"
    elif actual_topic == 'programming':
        assistant_prompt = f"If instructed, learn the programming concepts and techniques shown in this video about {title.lower()}"
    else:
# DEMO CODE REMOVED: assistant_prompt = f"If instructed, analyze the content and techniques demonstrated in this video about {title.lower()}"
    
    # Generate hashtags based on actual content
    hashtags = []
    if actual_topic == 'automotive':
        hashtags.extend(["automotive", "vehicle", "repair", "maintenance"])
    elif actual_topic == 'rc_hobby':
        hashtags.extend(["rc", "hobby", "remote-control", "racing"])
    elif actual_topic == 'programming':
        hashtags.extend(["programming", "development", "coding", "software"])
    else:
        # Extract relevant words from title and content
        title_words = [w.lower() for w in title.split() if len(w) > 3]
        hashtags.extend(title_words[:4])
    
    # Add topic-specific hashtags
    hashtags.append(actual_topic)
    hashtags = list(set(hashtags))[:6]
    
    # Generate key points based on actual content
    key_points = []
    if actual_topic == 'automotive':
        if "problem" in content_text or "issue" in content_text:
            key_points.append("Vehicle problems and diagnostic techniques")
        if "repair" in content_text or "fix" in content_text:
            key_points.append("Repair procedures and solutions")
        if "tools" in content_text or "equipment" in content_text:
            key_points.append("Tools and equipment usage")
        if "part" in content_text or "component" in content_text:
            key_points.append("Parts identification and replacement")
    elif actual_topic == 'rc_hobby':
        if "setup" in content_text or "assembly" in content_text:
            key_points.append("Setup and assembly procedures")
        if "tuning" in content_text or "adjustment" in content_text:
            key_points.append("Tuning and performance adjustments")
        if "racing" in content_text or "competition" in content_text:
            key_points.append("Racing techniques and strategies")
        if "maintenance" in content_text:
            key_points.append("Maintenance and care procedures")
    else:
        # Generic key points from content
# DEMO CODE REMOVED: if "example" in content_text or "demo" in content_text:
# DEMO CODE REMOVED: key_points.append("Practical examples and demonstrations")
        if "how" in content_text or "method" in content_text:
            key_points.append("Methods and techniques shown")
        if "result" in content_text or "outcome" in content_text:
            key_points.append("Results and outcomes discussed")
        if "tip" in content_text or "advice" in content_text:
            key_points.append("Tips and practical advice")
    
    # Complexity assessment based on content
    complexity = "Medium"
    if any(word in content_text for word in ["advanced", "complex", "difficult", "expert"]):
        complexity = "High"
    elif any(word in content_text for word in ["basic", "simple", "easy", "beginner", "intro"]):
        complexity = "Low"
    
    # Generate content summary based on actual topic
    if actual_topic == 'automotive':
        content_summary = f"Automotive video covering vehicle work, repairs, or restoration techniques."
    elif actual_topic == 'rc_hobby':
        content_summary = f"RC hobby content about remote control vehicles and related techniques."
    elif actual_topic == 'programming':
        content_summary = f"Programming tutorial covering coding concepts and implementation techniques."
    else:
        content_summary = f"Video content about {title.lower()} with practical information and techniques."
    
    return {
        "summary": ai_summary,
        "hashtags": hashtags,
        "complexity": complexity,
        "key_points": "\\n".join([f"• {point}" for point in key_points[:4]]) if key_points else f"• Content related to {actual_topic}\\n• Practical techniques and information",
        "action_items": "\\n".join([f"• {item}" for item in action_items[:3]]),
        "assistant_prompt": assistant_prompt,
        "content_summary": content_summary,
        "topics": [actual_topic.title().replace('_', ' ')]
    }

def get_fallback_analysis(video, channel_name="Unknown"):
    """Fallback analysis when no transcript is available."""
    title = video['title']
    title_lower = title.lower()
    
    # Extract what YOU need to know about the video content
    action_items = []
    if "mcp server" in title_lower:
        action_items.extend([
            "Video covers Model Context Protocol server development and architecture",
            "Shows practical MCP server creation and deployment techniques",
# DEMO CODE REMOVED: "Demonstrates integration between MCP servers and Claude Code workflows"
        ])
    elif "git worktree" in title_lower:
        action_items.extend([
            "Video explains Git worktree commands and parallel development strategies",
            "Shows when to use worktrees vs traditional branching approaches",
# DEMO CODE REMOVED: "Demonstrates practical worktree setup for multiple feature development"
        ])
    elif "voice" in title_lower and "claude" in title_lower:
        action_items.extend([
# DEMO CODE REMOVED: "Video demonstrates voice-to-text integration with Claude Code",
            "Shows productivity benefits of speech-controlled development workflows",
            "Covers setup and configuration of voice coding tools"
        ])
    elif "claude" in title_lower and "advanced" in title_lower:
        action_items.extend([
            "Video teaches advanced Claude prompting techniques for code generation",
            "Shows optimization strategies for AI-assisted development",
# DEMO CODE REMOVED: "Demonstrates integration patterns for Claude in development workflows"
        ])
    elif "agentic" in title_lower:
        action_items.extend([
            "Video covers autonomous agent design patterns and architectures",
            "Shows practical implementation of agentic AI systems",
# DEMO CODE REMOVED: "Demonstrates workflow automation using AI agents"
        ])
    else:
        action_items.extend([
# DEMO CODE REMOVED: "Video demonstrates practical implementation techniques",
            "Covers tools and frameworks for improved development workflows",
            "Shows best practices for the covered technology stack"
        ])
    
    # Generate assistant prompt for ME (Claude) to learn IF instructed
    if "mcp" in title_lower:
        assistant_prompt = "If instructed, analyze MCP server development patterns, study protocol implementation, and learn to build custom MCP integrations for specific workflows."
    elif "git worktree" in title_lower:
        assistant_prompt = "If instructed, study Git worktree strategies, learn parallel development patterns, and understand when worktrees are preferable to traditional branching."
    elif "voice" in title_lower:
        assistant_prompt = "If instructed, learn voice-controlled development techniques, study speech-to-code integration, and analyze voice command workflows."
    elif "claude" in title_lower:
        assistant_prompt = "If instructed, study advanced Claude prompting techniques, learn optimization strategies, and analyze effective AI-development integration patterns."
    else:
# DEMO CODE REMOVED: assistant_prompt = f"If instructed, analyze the {title.lower()} techniques, study implementation patterns, and learn the demonstrated development strategies."
    
    # Notes for YOU about the video
    notes_text = f"Duration: Unknown (transcript not available). Published: {video.get('published', 'Unknown date')}. "
    notes_text += f"Video from {channel_name} covering {title.lower()}. "
    notes_text += "Transcript analysis not available - content summary based on title analysis only. "
    notes_text += "Full transcript-based analysis would provide more detailed insights."
    
    # Determine content type based on channel name and title
    content_type = "video"
    if any(word in channel_name.lower() for word in ["tech", "dev", "code", "program"]):
        content_type = "technical tutorial"
        default_hashtags = ["development", "programming", "tutorial"]
    elif any(word in channel_name.lower() for word in ["rc", "crawler", "radio", "control"]):
        content_type = "RC/hobby video"
        default_hashtags = ["rc", "hobby", "remote-control"]
    elif any(word in channel_name.lower() for word in ["business", "entrepreneur", "marketing"]):
        content_type = "business/entrepreneurship content"
        default_hashtags = ["business", "entrepreneurship", "strategy"]
    else:
        content_type = "video content"
        default_hashtags = ["video", "content"]
    
    return {
        "summary": f"{content_type.capitalize()} titled '{title}' - detailed analysis requires transcript access",
        "hashtags": default_hashtags,
        "complexity": "Medium", 
        "key_points": "• Transcript not available for detailed content analysis\\n• Content type and focus based on channel context",
        "action_items": "\\n".join([f"• {item}" for item in action_items[:3]]),
        "assistant_prompt": assistant_prompt,
        "content_summary": f"{content_type.capitalize()} from {channel_name} covering {title.lower()}",
        "topics": [content_type.title().replace("/", " & ")],
        "notes": notes_text
    }

async def get_video_transcript_robust(video_id):
    """Self-healing transcript fetcher that tries EVERY possible method."""
    print(f"🔄 Attempting comprehensive transcript extraction for {video_id}")
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        import aiohttp
        import re
        
        # Method 1: Direct language attempts (most common)
        print("📋 Method 1: Direct language codes...")
        language_codes = [
            ['en'], ['en-US'], ['en-GB'], ['en-CA'], ['en-AU'],
            ['es'], ['fr'], ['de'], ['it'], ['pt'], ['ru'], ['ja'], ['ko'], ['zh'],
            None  # Default (any available)
        ]
        
        for i, lang_codes in enumerate(language_codes):
            try:
                if lang_codes:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=lang_codes)
                else:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                
                transcript_text, duration = parse_transcript_format(transcript_list)
                if transcript_text:
                    print(f"✅ Method 1.{i+1} SUCCESS: {lang_codes or 'default'} - {len(transcript_text)} chars")
                    return transcript_text, duration
            except Exception:
                continue
        
        # Method 2: List all available transcripts and try each
        print("📋 Method 2: Listing all available transcripts...")
        try:
            transcript_list_obj = YouTubeTranscriptApi.list_transcripts(video_id)
            for j, transcript in enumerate(transcript_list_obj):
                try:
                    transcript_data = transcript.fetch()
                    transcript_text, duration = parse_transcript_format(transcript_data)
                    if transcript_text:
                        print(f"✅ Method 2.{j+1} SUCCESS: {transcript.language_code} - {len(transcript_text)} chars")
                        return transcript_text, duration
                except Exception as e:
                    print(f"⚠️ Method 2.{j+1} failed for {getattr(transcript, 'language_code', 'unknown')}: {e}")
                    continue
        except Exception as e:
            print(f"⚠️ Method 2 listing failed: {e}")
        
        # Method 3: Try translated transcripts if auto-generated available
        print("📋 Method 3: Attempting translations...")
        try:
            transcript_list_obj = YouTubeTranscriptApi.list_transcripts(video_id)
            for transcript in transcript_list_obj:
                if transcript.is_translatable:
                    try:
                        # Try translating to English
                        translated = transcript.translate('en')
                        transcript_data = translated.fetch()
                        transcript_text, duration = parse_transcript_format(transcript_data)
                        if transcript_text:
                            print(f"✅ Method 3 SUCCESS: Translated from {transcript.language_code} - {len(transcript_text)} chars")
                            return transcript_text, duration
                    except Exception as e:
                        print(f"⚠️ Method 3 translation failed from {transcript.language_code}: {e}")
                        continue
        except Exception as e:
            print(f"⚠️ Method 3 failed: {e}")
        
        # Method 4: Try manual-generated before auto-generated
        print("📋 Method 4: Prioritizing manual transcripts...")
        try:
            transcript_list_obj = YouTubeTranscriptApi.list_transcripts(video_id)
            # Sort by manually created first
            manual_transcripts = [t for t in transcript_list_obj if not t.is_generated]
            auto_transcripts = [t for t in transcript_list_obj if t.is_generated]
            
            for transcript_list in [manual_transcripts, auto_transcripts]:
                for transcript in transcript_list:
                    try:
                        transcript_data = transcript.fetch()
                        transcript_text, duration = parse_transcript_format(transcript_data)
                        if transcript_text:
                            status = "MANUAL" if not transcript.is_generated else "AUTO"
                            print(f"✅ Method 4 SUCCESS: {status} {transcript.language_code} - {len(transcript_text)} chars")
                            return transcript_text, duration
                    except Exception:
                        continue
        except Exception as e:
            print(f"⚠️ Method 4 failed: {e}")
        
        # Method 5: Web scraping fallback (last resort)
        print("📋 Method 5: Web scraping fallback...")
        transcript_text = await scrape_transcript_from_web(video_id)
        if transcript_text:
            print(f"✅ Method 5 SUCCESS: Web scraped - {len(transcript_text)} chars")
            return transcript_text, 0  # Duration unknown from scraping
        
        # Method 6: Check if video exists at all
        print("📋 Method 6: Checking video accessibility...")
        video_exists = await check_video_exists(video_id)
        if not video_exists:
            print(f"❌ Video {video_id} may be private, deleted, or inaccessible")
        else:
            print(f"✅ Video {video_id} exists but no transcripts available")
        
        print(f"❌ ALL METHODS EXHAUSTED for {video_id}")
        return None, 0
            
    except Exception as e:
        print(f"❌ Critical error in transcript fetching: {e}")
        return None, 0

def parse_transcript_format(transcript_list):
    """Parse different transcript formats into text and duration."""
    try:
        # Handle standard dict format
        if isinstance(transcript_list, list) and len(transcript_list) > 0 and isinstance(transcript_list[0], dict):
            transcript_text = ' '.join([entry['text'] for entry in transcript_list])
            last_entry = transcript_list[-1]
            duration = int(last_entry['start'] + last_entry.get('duration', 0))
            return transcript_text, duration
            
        # Handle FetchedTranscript object format
        elif hasattr(transcript_list, '__iter__') and hasattr(transcript_list, '__len__'):
            transcript_text = ' '.join([entry.text for entry in transcript_list])
            last_entry = list(transcript_list)[-1]
            duration = int(last_entry.start + getattr(last_entry, 'duration', 0))
            return transcript_text, duration
            
        return None, 0
        
    except Exception as e:
        print(f"⚠️ Format parsing error: {e}")
        return None, 0

async def scrape_transcript_from_web(video_id):
    """Last resort: attempt to scrape transcript from YouTube page."""
    try:
        import aiohttp
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Look for transcript data in page
                    # This is a simplified approach - real implementation would be more complex
                    transcript_patterns = [
                        r'"text":"([^"]+)"',
                        r'captionTracks.*?"text":"([^"]+)"'
                    ]
                    
                    for pattern in transcript_patterns:
                        matches = re.findall(pattern, html)
                        if matches and len(matches) > 10:  # Reasonable transcript length
                            return ' '.join(matches[:100])  # Limit to avoid too much data
                    
        return None
        
    except Exception as e:
        print(f"⚠️ Web scraping failed: {e}")
        return None

async def check_video_exists(video_id):
    """Check if video is accessible."""
    try:
        import aiohttp
        
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                return response.status == 200
                
    except Exception:
        return False

async def get_video_transcript(video_id):
    """Legacy function - use get_video_transcript_robust instead."""
    transcript, _ = await get_video_transcript_robust(video_id)
    return transcript

async def unmark_channel(channel_id, headers):
    """Unmark the Process Channel checkbox."""
    try:
        update_data = {
            "properties": {
                "Process Channel": {
                    "checkbox": False
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                headers=headers,
                json=update_data,
                timeout=10
            ) as response:
                if response.status == 200:
                    print("✅ Channel unmarked")
                else:
                    print(f"⚠️ Failed to unmark channel: {response.status}")
                    
    except Exception as e:
        print(f"⚠️ Error unmarking channel: {e}")

if __name__ == "__main__":
    asyncio.run(process_videos_with_ai())