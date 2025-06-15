#!/usr/bin/env python3
"""
Content Analysis Engine for Vanlife & RC Truck Social Media
Analyzes content, generates captions, and optimizes hashtags
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
from pathlib import Path

# Import AI providers
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

class VanlifeRCContentAnalyzer:
    """
    Intelligent content analyzer for vanlife and RC truck content
    """
    
    def __init__(self, db_path="lifeos_local.db"):
        self.db_path = db_path
        
        # Initialize AI providers
        if os.getenv("ANTHROPIC_API_KEY"):
            self.claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            self.claude = None
            
        if os.getenv("GOOGLE_API_KEY"):
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.gemini = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.gemini = None
    
    def analyze_content(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze uploaded content to determine type and generate metadata
        """
        try:
            # Get file info
            file_info = self._get_file_info(file_path)
            
            # Perform AI analysis
            analysis_result = self._ai_content_analysis(file_path, file_info)
            
            # Generate caption and hashtags
            caption = self._generate_caption(analysis_result)
            hashtags = self._optimize_hashtags(analysis_result)
            
            # Get posting recommendations
            posting_recommendations = self._get_posting_recommendations(analysis_result)
            
            return {
                'success': True,
                'file_info': file_info,
                'content_type': analysis_result.get('content_type', 'unknown'),
                'analysis': analysis_result,
                'caption': caption,
                'hashtags': hashtags,
                'posting_recommendations': posting_recommendations,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Extract basic file information"""
        path = Path(file_path)
        
        return {
            'filename': path.name,
            'extension': path.suffix.lower(),
            'size': path.stat().st_size if path.exists() else 0,
            'is_video': path.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv'],
            'is_image': path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif'],
            'created': datetime.fromtimestamp(path.stat().st_ctime).isoformat() if path.exists() else None
        }
    
    def _ai_content_analysis(self, file_path: str, file_info: Dict) -> Dict[str, Any]:
        """
        Use AI to analyze content and determine type/context
        """
        # Create analysis prompt
        prompt = f"""
Analyze this {file_info['extension']} file for vanlife and RC truck content analysis.

Context: This is for a Southern BC vanlife content creator who explores trails with RC trucks (mainly Axial Racing and Vanquish brands).

Please analyze and determine:

1. Content Type Classification:
   - vanlife (van exterior, interior, camping setups, travel scenes)
   - rc_truck (RC vehicles, trail runs, technical driving)
   - trail_exploration (hiking trails, scenic views, outdoor adventures)
   - mixed (combination of the above)

2. RC Brand Detection:
   - Look for Axial Racing models (SCX24, SCX10, RBX10)
   - Look for Vanquish Products (VS4-10, VS4-18)
   - Other brands (Traxxas, Element RC, Associated)

3. Location Context:
   - Southern BC trails, mountains, forests
   - Specific locations if identifiable (Whistler, Squamish, etc.)
   - Terrain type (rocky, forest, mountain, technical)

4. Scene Description:
   - Activity happening in the content
   - Difficulty level of terrain
   - Weather conditions
   - Time of day

5. Mood/Theme:
   - Adventure, exploration, challenge, relaxation
   - Technical achievement, scenic beauty, lifestyle

Filename: {file_info['filename']}

Respond with a JSON object containing your analysis.
"""

        try:
            # Try Gemini first (better for image analysis)
            if self.gemini and file_info['is_image']:
                response = self.gemini.generate_content(prompt)
                analysis_text = response.text
            # Try Claude for text analysis
            elif self.claude:
                response = self.claude.messages.create(
                    model="claude-3-sonnet-20241022",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                analysis_text = response.content[0].text
            else:
                # Fallback analysis based on filename
                return self._fallback_analysis(file_info)
            
            # Try to parse JSON response
            try:
                # Extract JSON from response if it's wrapped in markdown
                if '```json' in analysis_text:
                    json_start = analysis_text.find('```json') + 7
                    json_end = analysis_text.find('```', json_start)
                    analysis_text = analysis_text[json_start:json_end].strip()
                
                analysis = json.loads(analysis_text)
                return analysis
                
            except json.JSONDecodeError:
                # If JSON parsing fails, create structured response from text
                return self._parse_text_analysis(analysis_text, file_info)
                
        except Exception as e:
            print(f"AI analysis error: {e}")
            return self._fallback_analysis(file_info)
    
    def _fallback_analysis(self, file_info: Dict) -> Dict[str, Any]:
        """Fallback analysis based on filename patterns"""
        filename = file_info['filename'].lower()
        
        # Determine content type from filename
        if any(word in filename for word in ['van', 'camp', 'travel', 'road']):
            content_type = 'vanlife'
        elif any(word in filename for word in ['rc', 'truck', 'crawler', 'axial', 'vanquish']):
            content_type = 'rc_truck'
        elif any(word in filename for word in ['trail', 'hike', 'mountain', 'outdoor']):
            content_type = 'trail_exploration'
        else:
            content_type = 'mixed'
        
        # Basic brand detection
        detected_brands = []
        if 'axial' in filename or 'scx' in filename:
            detected_brands.append('Axial Racing')
        if 'vanquish' in filename or 'vs4' in filename:
            detected_brands.append('Vanquish Products')
        
        return {
            'content_type': content_type,
            'detected_brands': detected_brands,
            'location_context': 'Southern BC',
            'terrain_type': 'trail',
            'mood': 'adventure',
            'confidence': 0.6,
            'analysis_method': 'filename_fallback'
        }
    
    def _parse_text_analysis(self, analysis_text: str, file_info: Dict) -> Dict[str, Any]:
        """Parse AI analysis from text format"""
        # Extract key information from text
        content_type = 'mixed'
        if 'vanlife' in analysis_text.lower():
            content_type = 'vanlife'
        elif 'rc' in analysis_text.lower() and 'truck' in analysis_text.lower():
            content_type = 'rc_truck'
        elif 'trail' in analysis_text.lower():
            content_type = 'trail_exploration'
        
        # Extract brands mentioned
        detected_brands = []
        if 'axial' in analysis_text.lower():
            detected_brands.append('Axial Racing')
        if 'vanquish' in analysis_text.lower():
            detected_brands.append('Vanquish Products')
        
        return {
            'content_type': content_type,
            'detected_brands': detected_brands,
            'raw_analysis': analysis_text,
            'confidence': 0.7,
            'analysis_method': 'text_parsing'
        }
    
    def _generate_caption(self, analysis: Dict[str, Any]) -> str:
        """
        Generate caption with relaxed traveler voice
        """
        content_type = analysis.get('content_type', 'mixed')
        detected_brands = analysis.get('detected_brands', [])
        location = analysis.get('location_context', 'Southern BC')
        terrain = analysis.get('terrain_type', 'trail')
        mood = analysis.get('mood', 'adventure')
        
        # Caption templates based on content type
        vanlife_templates = [
            f"Exploring new trails around {location} 🚐",
            f"Home is where you park it - today it's {location} 🏔️",
            f"Van life adventures in beautiful {location}",
            f"Finding the perfect spots to camp and explore in {location}",
            f"The road less traveled leads to the best views in {location}"
        ]
        
        rc_templates = [
            f"Trail therapy session in {location} 🏔️",
            f"The little crawler handled this {terrain} section like a champ!",
            f"Technical {terrain} calls for precision driving",
            f"Nothing beats combining van life with some RC trail time",
            f"Exploring {location} trails one scale at a time"
        ]
        
        mixed_templates = [
            f"Perfect day combining van life and RC adventures in {location}",
            f"Exploring {location} with the best of both worlds - van and RC",
            f"Trail exploration made better with good company and RC trucks",
            f"Southern BC adventures: van life meets RC trail therapy"
        ]
        
        # Select template based on content type
        if content_type == 'vanlife':
            base_caption = vanlife_templates[hash(str(analysis)) % len(vanlife_templates)]
        elif content_type == 'rc_truck':
            base_caption = rc_templates[hash(str(analysis)) % len(rc_templates)]
        else:
            base_caption = mixed_templates[hash(str(analysis)) % len(mixed_templates)]
        
        # Add brand mention if detected
        if detected_brands:
            brand = detected_brands[0]
            if 'Axial' in brand:
                base_caption += f" The {brand} handled this terrain perfectly!"
            elif 'Vanquish' in brand:
                base_caption += f" {brand} engineering at its finest!"
        
        # Add location-specific elements
        if 'whistler' in location.lower():
            base_caption += " #WhistlerAdventures"
        elif 'squamish' in location.lower():
            base_caption += " #SquamishTrails"
        
        return base_caption
    
    def _optimize_hashtags(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate optimized hashtags based on content analysis
        """
        content_type = analysis.get('content_type', 'mixed')
        detected_brands = analysis.get('detected_brands', [])
        location = analysis.get('location_context', 'Southern BC')
        
        # Base hashtags for each content type (Instagram optimized)
        vanlife_hashtags = ['#vanlife', '#nomadlife', '#roadtrip', '#homeiswhereyouparkit', '#vanlifestyle', '#vanlifeadventure']
        rc_hashtags = ['#rctrucks', '#rccrawler', '#scalerc', '#trailtherapy', '#radiocontrol', '#rclife']
        location_hashtags = ['#southernbc', '#bcoutdoors', '#bctrails', '#explorebc', '#beautifulbc']
        general_hashtags = ['#adventure', '#outdoors', '#explore', '#nature', '#traillife']
        
        # Instagram-specific high-engagement hashtags
        instagram_vanlife = ['#vanlifelife', '#homeonwheels', '#digitalnomad', '#roadtriplife', '#vanlifeexplorers']
        instagram_rc = ['#rcaddict', '#scalecrawler', '#rcbashing', '#remotecontrol', '#rchobbies']
        instagram_general = ['#wanderlust', '#getoutside', '#adventuretime', '#exploremore', '#naturelover']
        
        # Get high-performing hashtags from database
        high_performance_tags = self._get_trending_hashtags(content_type)
        
        # Combine based on content type (Instagram optimized with 15-20 hashtags)
        if content_type == 'vanlife':
            hashtags = (vanlife_hashtags[:4] + instagram_vanlife[:3] + 
                       location_hashtags[:3] + instagram_general[:2] + general_hashtags[:2])
        elif content_type == 'rc_truck':
            hashtags = (rc_hashtags[:4] + instagram_rc[:3] + 
                       location_hashtags[:3] + instagram_general[:2] + general_hashtags[:2])
        else:
            hashtags = (vanlife_hashtags[:2] + rc_hashtags[:2] + instagram_vanlife[:2] + 
                       instagram_rc[:2] + location_hashtags[:3] + instagram_general[:2] + general_hashtags[:1])
        
        # Add brand-specific hashtags
        for brand in detected_brands:
            if 'Axial' in brand:
                hashtags.extend(['#axialracing', '#scaletrail'])
            elif 'Vanquish' in brand:
                hashtags.extend(['#vanquish', '#scalebuilds'])
        
        # Add high-performing hashtags
        hashtags.extend(high_performance_tags[:3])
        
        # Remove duplicates and optimize for Instagram (limit to 20 hashtags)
        unique_hashtags = list(dict.fromkeys(hashtags))[:20]
        
        # Add Instagram-specific trending hashtags based on current trends
        if len(unique_hashtags) < 20:
            trending_instagram = self._get_instagram_trending_hashtags(content_type)
            for tag in trending_instagram:
                if tag not in unique_hashtags and len(unique_hashtags) < 20:
                    unique_hashtags.append(tag)
        
        return unique_hashtags
    
    def _get_instagram_trending_hashtags(self, content_type: str) -> List[str]:
        """Get Instagram-specific trending hashtags"""
        instagram_trending = {
            'vanlife': ['#vanlifecommunity', '#roadtripcanada', '#bcvanlife', '#outdoorliving', '#tinyhome'],
            'rc_truck': ['#rcworld', '#scalecrawling', '#rchobby', '#rcfun', '#remotecontrolcar'],
            'trail_exploration': ['#trailrunning', '#hikingadventures', '#mountainlife', '#wilderness', '#naturetherapy'],
            'mixed': ['#adventurelife', '#outdooradventure', '#explorecanada', '#weekendwarrior', '#getlost']
        }
        
        return instagram_trending.get(content_type, instagram_trending['mixed'])[:3]
    
    def _get_trending_hashtags(self, content_type: str) -> List[str]:
        """Get trending hashtags from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT hashtag FROM hashtag_performance 
                WHERE niche = ? OR niche = 'general'
                ORDER BY trending_score DESC, avg_engagement DESC
                LIMIT 5
            ''', (content_type,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in results]
            
        except Exception as e:
            print(f"Error getting trending hashtags: {e}")
            return []
    
    def _get_posting_recommendations(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get optimal posting recommendations"""
        content_type = analysis.get('content_type', 'mixed')
        
        # Default posting recommendations
        recommendations = {
            'best_platforms': [],
            'optimal_times': [],
            'content_strategy': '',
            'engagement_tips': []
        }
        
        if content_type == 'vanlife':
            recommendations.update({
                'best_platforms': ['instagram', 'youtube'],
                'optimal_times': ['6:00 AM', '7:00 PM'],
                'content_strategy': 'Focus on lifestyle and travel inspiration',
                'engagement_tips': [
                    'Ask about favorite camping spots',
                    'Share van setup details',
                    'Include location for travel planning'
                ]
            })
        elif content_type == 'rc_truck':
            recommendations.update({
                'best_platforms': ['youtube', 'instagram'],
                'optimal_times': ['2:00 PM', '8:00 PM'],
                'content_strategy': 'Highlight technical challenges and equipment',
                'engagement_tips': [
                    'Ask about RC modifications',
                    'Share trail difficulty ratings',
                    'Include setup/tuning details'
                ]
            })
        
        return recommendations
    
    def optimize_for_instagram(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize content specifically for Instagram posting"""
        try:
            content_type = analysis_result.get('content_type', 'mixed')
            
            # Instagram-specific caption optimization
            original_caption = analysis_result.get('caption', '')
            instagram_caption = self._optimize_instagram_caption(original_caption, content_type)
            
            # Instagram hashtag optimization (separate from general hashtags)
            instagram_hashtags = self._optimize_instagram_hashtags(analysis_result.get('analysis', {}))
            
            # Instagram posting recommendations
            posting_recs = self._get_posting_recommendations(analysis_result.get('analysis', {}))
            instagram_recs = posting_recs.get('instagram_specific', {})
            
            return {
                'instagram_caption': instagram_caption,
                'instagram_hashtags': instagram_hashtags,
                'story_suggestions': instagram_recs.get('story_ideas', []),
                'reel_suggestions': instagram_recs.get('reel_ideas', []),
                'optimal_aspect_ratio': instagram_recs.get('optimal_aspect_ratio', '4:5'),
                'posting_times': posting_recs.get('optimal_times', []),
                'engagement_strategy': instagram_recs.get('post_style', 'Authentic storytelling'),
                'content_optimization': {
                    'use_carousel': content_type == 'mixed',
                    'add_story_highlight': True,
                    'create_reel_version': content_type in ['rc_truck', 'trail_exploration'],
                    'optimize_for_explore': True
                }
            }
            
        except Exception as e:
            print(f"Error optimizing for Instagram: {e}")
            return {}
    
    def _optimize_instagram_caption(self, original_caption: str, content_type: str) -> str:
        """Optimize caption specifically for Instagram engagement"""
        # Instagram performs better with line breaks and emojis
        if content_type == 'vanlife':
            instagram_caption = f"{original_caption} 🚐\n\n"
            instagram_caption += "What's your favorite vanlife destination? 👇\n\n"
            instagram_caption += "#VanLifeAdventure #ExploreMore"
        elif content_type == 'rc_truck':
            instagram_caption = f"{original_caption} 🏔️\n\n"
            instagram_caption += "What's your favorite RC trail challenge? 🤔\n\n"
            instagram_caption += "#RCLife #TrailTherapy"
        else:
            instagram_caption = f"{original_caption} 🌲\n\n"
            instagram_caption += "Adventure awaits! Where are you exploring next? 🗺️\n\n"
            instagram_caption += "#AdventureLife #GetOutside"
        
        return instagram_caption
    
    def _optimize_instagram_hashtags(self, analysis: Dict[str, Any]) -> List[str]:
        """Create Instagram-optimized hashtag strategy"""
        content_type = analysis.get('content_type', 'mixed')
        
        # Instagram algorithm prefers mix of popular and niche hashtags
        popular_tags = []  # 1M+ posts
        medium_tags = []   # 100K-1M posts  
        niche_tags = []    # 10K-100K posts
        
        if content_type == 'vanlife':
            popular_tags = ['#vanlife', '#roadtrip', '#adventure']
            medium_tags = ['#vanlifeadventure', '#nomadlife', '#homeonwheels', '#vanlifestyle']
            niche_tags = ['#bcvanlife', '#vanlifecommunity', '#roadtripcanada', '#vanlifeexplorers']
        elif content_type == 'rc_truck':
            popular_tags = ['#rc', '#adventure', '#outdoors']
            medium_tags = ['#rctrucks', '#rccrawler', '#radiocontrol', '#rclife']
            niche_tags = ['#scalecrawler', '#rcaddict', '#trailtherapy', '#rcworld', '#axialracing']
        
        # Instagram strategy: 3-5 popular, 5-7 medium, 7-10 niche hashtags
        instagram_hashtags = popular_tags[:3] + medium_tags[:6] + niche_tags[:8]
        
        # Add location-based hashtags
        location_tags = ['#southernbc', '#bcoutdoors', '#explorebc', '#beautifulbc']
        instagram_hashtags.extend(location_tags[:3])
        
        return instagram_hashtags[:20]  # Instagram limit
    
    def save_analysis_to_db(self, file_path: str, analysis_result: Dict[str, Any]) -> int:
        """Save content analysis to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO social_media_posts 
                (file_path, original_filename, content_type, caption, hashtags, 
                 analysis_data, status, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_path,
                analysis_result['file_info']['filename'],
                analysis_result['content_type'],
                analysis_result['caption'],
                json.dumps(analysis_result['hashtags']),
                json.dumps(analysis_result['analysis']),
                'analyzed',
                datetime.now().isoformat()
            ))
            
            post_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return post_id
            
        except Exception as e:
            print(f"Error saving to database: {e}")
            return -1

# Usage example and testing
if __name__ == "__main__":
    analyzer = VanlifeRCContentAnalyzer()
    
    # Test with a sample filename
    test_analysis = analyzer._fallback_analysis({
        'filename': 'axial_scx24_whistler_trail_run.jpg',
        'extension': '.jpg',
        'is_image': True
    })
    
    print("🧪 CONTENT ANALYZER TEST")
    print("=" * 40)
    print(f"Content Type: {test_analysis['content_type']}")
    print(f"Detected Brands: {test_analysis['detected_brands']}")
    
    # Generate caption and hashtags
    caption = analyzer._generate_caption(test_analysis)
    hashtags = analyzer._optimize_hashtags(test_analysis)
    
    print(f"\n📝 Generated Caption:")
    print(f"   {caption}")
    
    print(f"\n🏷️ Optimized Hashtags:")
    print(f"   {' '.join(hashtags)}")
    
    print(f"\n✅ Content analyzer ready for integration!")