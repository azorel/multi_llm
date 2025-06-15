#!/usr/bin/env python3
"""
Social Media Research Agent - Specialized Perplexity-powered agent for social media research
Integrates vanlife, RC truck, and outdoor content research with real-time trend analysis
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from perplexity_research_agent import PerplexityResearchAgent, ResearchQuery, ResearchResult
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SocialMediaResearchTask:
    """Social media research task structure"""
    id: str
    task_type: str  # "hashtag_research", "trend_analysis", "competitor_analysis", etc.
    content_niche: str  # "vanlife", "rc_trucks", "outdoor_adventures", "southern_bc_trails"
    platform: str  # "instagram", "tiktok", "youtube", "facebook", "all"
    time_filter: str = "week"
    max_results: int = 10
    specific_query: str = ""
    location_filter: str = "Southern BC, Canada"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

@dataclass
class SocialMediaInsights:
    """Social media research insights"""
    task_id: str
    insights: Dict[str, Any]
    trending_hashtags: List[str]
    optimal_posting_times: List[str]
    competitor_analysis: Dict[str, Any]
    content_opportunities: List[str]
    engagement_strategies: List[str]
    location_trends: Dict[str, Any]
    success: bool
    error: Optional[str] = None

class SocialMediaResearchAgent:
    """Advanced social media research agent powered by Perplexity AI"""
    
    def __init__(self):
        self.perplexity_agent = None
        self.niche_templates = {
            "vanlife": {
                "hashtag_research": "Research trending vanlife hashtags for {platform} in {location}. Focus on current popular tags, engagement rates, and posting strategies for van life content creators.",
                "trend_analysis": "Analyze current vanlife trends on {platform} for {location}. Include popular destinations, gear trends, lifestyle topics, and content formats.",
                "competitor_analysis": "Research top vanlife influencers and content creators on {platform} in {location}. Analyze their content strategies, posting frequency, engagement rates, and successful content types.",
                "destination_research": "Research trending vanlife destinations in {location}. Include hidden gems, popular stops, seasonal considerations, and Instagram-worthy locations."
            },
            "rc_trucks": {
                "hashtag_research": "Research trending RC truck and crawler hashtags for {platform}. Focus on scale RC, SCX24, rock crawling, and hobby-related tags with high engagement.",
                "trend_analysis": "Analyze current RC truck trends on {platform}. Include new model releases, popular modifications, racing events, and hobby developments.",
                "competitor_analysis": "Research top RC truck content creators and channels on {platform}. Analyze their content strategies, review formats, and audience engagement.",
                "product_research": "Research trending RC truck models, parts, and modifications. Include market analysis, pricing trends, and consumer preferences."
            },
            "outdoor_adventures": {
                "hashtag_research": "Research trending outdoor adventure hashtags for {platform} in {location}. Focus on hiking, camping, outdoor gear, and adventure travel tags.",
                "trend_analysis": "Analyze current outdoor adventure trends on {platform} for {location}. Include popular activities, gear trends, and seasonal content opportunities.",
                "competitor_analysis": "Research top outdoor adventure influencers on {platform} in {location}. Analyze content strategies, gear reviews, and adventure documentation.",
                "trail_research": "Research trending hiking trails and outdoor locations in {location}. Include difficulty ratings, seasonal access, and photography opportunities."
            },
            "southern_bc_trails": {
                "hashtag_research": "Research trending British Columbia trail and hiking hashtags for {platform}. Focus on BC Parks, hiking trails, and outdoor recreation tags.",
                "trend_analysis": "Analyze current BC trail conditions and trending outdoor locations. Include seasonal accessibility, popular trails, and recent developments.",
                "competitor_analysis": "Research BC-based outdoor content creators and trail guides on {platform}. Analyze local expertise and content strategies.",
                "trail_conditions": "Research current trail conditions, closures, and accessibility for popular BC trails. Include weather impacts and seasonal considerations."
            }
        }
        
        self.platform_strategies = {
            "instagram": {
                "optimal_times": ["6-9 AM", "12-2 PM", "5-7 PM"],
                "hashtag_limit": 30,
                "content_types": ["photos", "reels", "stories", "carousels"],
                "engagement_tactics": ["story polls", "location tags", "user-generated content"]
            },
            "tiktok": {
                "optimal_times": ["6-10 AM", "7-9 PM"],
                "hashtag_limit": 100,
                "content_types": ["short videos", "trends", "challenges"],
                "engagement_tactics": ["trending sounds", "duets", "challenges"]
            },
            "youtube": {
                "optimal_times": ["2-4 PM", "6-8 PM"],
                "hashtag_limit": 15,
                "content_types": ["long form", "shorts", "live streams"],
                "engagement_tactics": ["thumbnails", "titles", "descriptions", "community posts"]
            },
            "facebook": {
                "optimal_times": ["9 AM-1 PM", "3-4 PM"],
                "hashtag_limit": 20,
                "content_types": ["posts", "videos", "stories", "events"],
                "engagement_tactics": ["groups", "events", "live videos"]
            }
        }
        
        logger.info("Social Media Research Agent initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.perplexity_agent = PerplexityResearchAgent()
        await self.perplexity_agent.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.perplexity_agent:
            await self.perplexity_agent.__aexit__(exc_type, exc_val, exc_tb)
    
    async def research_hashtags(self, task: SocialMediaResearchTask) -> SocialMediaInsights:
        """Research trending hashtags for specific niche and platform"""
        try:
            template = self.niche_templates.get(task.content_niche, {}).get("hashtag_research", 
                "Research trending hashtags for {platform} related to {niche}")
            
            query_text = template.format(
                platform=task.platform,
                location=task.location_filter,
                niche=task.content_niche
            )
            
            if task.specific_query:
                query_text += f". Specific focus: {task.specific_query}"
            
            research_query = ResearchQuery(
                id=f"hashtag_{task.id}",
                query=query_text,
                context=f"Social media hashtag research for {task.content_niche} content on {task.platform}",
                research_type="trending",
                time_filter=task.time_filter,
                include_related_questions=True
            )
            
            result = await self.perplexity_agent.research(research_query)
            
            if result.success:
                hashtags = self._extract_hashtags_from_content(result.content)
                insights = self._analyze_hashtag_performance(result.content, task.platform)
                
                return SocialMediaInsights(
                    task_id=task.id,
                    insights=insights,
                    trending_hashtags=hashtags,
                    optimal_posting_times=self.platform_strategies.get(task.platform, {}).get("optimal_times", []),
                    competitor_analysis={},
                    content_opportunities=self._extract_content_opportunities(result.content),
                    engagement_strategies=self.platform_strategies.get(task.platform, {}).get("engagement_tactics", []),
                    location_trends=self._extract_location_trends(result.content),
                    success=True
                )
            else:
                return SocialMediaInsights(
                    task_id=task.id,
                    insights={},
                    trending_hashtags=[],
                    optimal_posting_times=[],
                    competitor_analysis={},
                    content_opportunities=[],
                    engagement_strategies=[],
                    location_trends={},
                    success=False,
                    error=result.error
                )
                
        except Exception as e:
            logger.error(f"Hashtag research failed: {e}")
            return SocialMediaInsights(
                task_id=task.id,
                insights={},
                trending_hashtags=[],
                optimal_posting_times=[],
                competitor_analysis={},
                content_opportunities=[],
                engagement_strategies=[],
                location_trends={},
                success=False,
                error=str(e)
            )
    
    async def analyze_trends(self, task: SocialMediaResearchTask) -> SocialMediaInsights:
        """Analyze current trends for specific niche and platform"""
        try:
            template = self.niche_templates.get(task.content_niche, {}).get("trend_analysis",
                "Analyze current trends for {niche} content on {platform}")
            
            query_text = template.format(
                platform=task.platform,
                location=task.location_filter,
                niche=task.content_niche
            )
            
            research_query = ResearchQuery(
                id=f"trends_{task.id}",
                query=query_text,
                context=f"Trend analysis for {task.content_niche} on {task.platform}",
                research_type="trending",
                time_filter=task.time_filter,
                include_related_questions=True
            )
            
            result = await self.perplexity_agent.research(research_query)
            
            if result.success:
                return SocialMediaInsights(
                    task_id=task.id,
                    insights=self._extract_trend_insights(result.content),
                    trending_hashtags=self._extract_hashtags_from_content(result.content),
                    optimal_posting_times=self.platform_strategies.get(task.platform, {}).get("optimal_times", []),
                    competitor_analysis={},
                    content_opportunities=self._extract_content_opportunities(result.content),
                    engagement_strategies=self._extract_engagement_strategies(result.content),
                    location_trends=self._extract_location_trends(result.content),
                    success=True
                )
            else:
                return self._create_failed_insights(task.id, result.error)
                
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return self._create_failed_insights(task.id, str(e))
    
    async def analyze_competitors(self, task: SocialMediaResearchTask) -> SocialMediaInsights:
        """Analyze competitor strategies and performance"""
        try:
            template = self.niche_templates.get(task.content_niche, {}).get("competitor_analysis",
                "Research and analyze top {niche} content creators on {platform}")
            
            query_text = template.format(
                platform=task.platform,
                location=task.location_filter,
                niche=task.content_niche
            )
            
            research_query = ResearchQuery(
                id=f"competitors_{task.id}",
                query=query_text,
                context=f"Competitor analysis for {task.content_niche} creators on {task.platform}",
                research_type="comparison",
                time_filter=task.time_filter,
                include_related_questions=True
            )
            
            result = await self.perplexity_agent.research(research_query)
            
            if result.success:
                competitor_data = self._extract_competitor_data(result.content)
                
                return SocialMediaInsights(
                    task_id=task.id,
                    insights=self._extract_competitive_insights(result.content),
                    trending_hashtags=self._extract_hashtags_from_content(result.content),
                    optimal_posting_times=self.platform_strategies.get(task.platform, {}).get("optimal_times", []),
                    competitor_analysis=competitor_data,
                    content_opportunities=self._extract_content_gaps(result.content),
                    engagement_strategies=self._extract_successful_strategies(result.content),
                    location_trends=self._extract_location_trends(result.content),
                    success=True
                )
            else:
                return self._create_failed_insights(task.id, result.error)
                
        except Exception as e:
            logger.error(f"Competitor analysis failed: {e}")
            return self._create_failed_insights(task.id, str(e))
    
    async def research_trail_conditions(self, task: SocialMediaResearchTask) -> SocialMediaInsights:
        """Research current trail conditions and outdoor updates for BC"""
        try:
            query_text = f"Current trail conditions and accessibility for hiking trails in {task.location_filter}. Include recent updates, closures, weather impacts, and seasonal considerations."
            
            research_query = ResearchQuery(
                id=f"trails_{task.id}",
                query=query_text,
                context="Real-time trail conditions and outdoor accessibility research",
                research_type="news",
                time_filter="week",
                include_related_questions=True
            )
            
            result = await self.perplexity_agent.research(research_query)
            
            if result.success:
                return SocialMediaInsights(
                    task_id=task.id,
                    insights=self._extract_trail_insights(result.content),
                    trending_hashtags=self._extract_hashtags_from_content(result.content),
                    optimal_posting_times=self.platform_strategies.get(task.platform, {}).get("optimal_times", []),
                    competitor_analysis={},
                    content_opportunities=self._extract_trail_content_opportunities(result.content),
                    engagement_strategies=["location tagging", "condition updates", "safety tips"],
                    location_trends=self._extract_trail_trends(result.content),
                    success=True
                )
            else:
                return self._create_failed_insights(task.id, result.error)
                
        except Exception as e:
            logger.error(f"Trail conditions research failed: {e}")
            return self._create_failed_insights(task.id, str(e))
    
    async def optimize_posting_strategy(self, task: SocialMediaResearchTask) -> SocialMediaInsights:
        """Research optimal posting strategies for specific niche and platform"""
        try:
            query_text = f"Optimal posting strategies and times for {task.content_niche} content on {task.platform}. Include engagement patterns, audience behavior, and best practices for content creators."
            
            research_query = ResearchQuery(
                id=f"posting_{task.id}",
                query=query_text,
                context=f"Posting optimization research for {task.content_niche} on {task.platform}",
                research_type="technical",
                time_filter="month",
                include_related_questions=True
            )
            
            result = await self.perplexity_agent.research(research_query)
            
            if result.success:
                return SocialMediaInsights(
                    task_id=task.id,
                    insights=self._extract_posting_insights(result.content),
                    trending_hashtags=self._extract_hashtags_from_content(result.content),
                    optimal_posting_times=self._extract_optimal_times(result.content, task.platform),
                    competitor_analysis={},
                    content_opportunities=self._extract_content_opportunities(result.content),
                    engagement_strategies=self._extract_engagement_optimization(result.content),
                    location_trends={},
                    success=True
                )
            else:
                return self._create_failed_insights(task.id, result.error)
                
        except Exception as e:
            logger.error(f"Posting strategy optimization failed: {e}")
            return self._create_failed_insights(task.id, str(e))
    
    # Content analysis helper methods
    def _extract_hashtags_from_content(self, content: str) -> List[str]:
        """Extract hashtags from research content"""
        import re
        hashtags = re.findall(r'#\w+', content)
        # Remove duplicates and return top 20
        return list(dict.fromkeys(hashtags))[:20]
    
    def _analyze_hashtag_performance(self, content: str, platform: str) -> Dict[str, Any]:
        """Analyze hashtag performance insights"""
        return {
            "platform": platform,
            "analysis_type": "hashtag_performance",
            "key_findings": self._extract_key_findings(content),
            "recommendations": self._extract_recommendations(content),
            "engagement_potential": "high"  # Could be enhanced with ML analysis
        }
    
    def _extract_content_opportunities(self, content: str) -> List[str]:
        """Extract content opportunities from research"""
        opportunities = []
        content_lower = content.lower()
        
        # Look for opportunity indicators
        if "gap" in content_lower or "opportunity" in content_lower:
            lines = content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ["opportunity", "gap", "missing", "needed"]):
                    opportunities.append(line.strip())
        
        return opportunities[:5]
    
    def _extract_location_trends(self, content: str) -> Dict[str, Any]:
        """Extract location-specific trends"""
        return {
            "trending_locations": self._extract_locations(content),
            "seasonal_patterns": self._extract_seasonal_info(content),
            "regional_preferences": self._extract_regional_data(content)
        }
    
    def _extract_trend_insights(self, content: str) -> Dict[str, Any]:
        """Extract trend analysis insights"""
        return {
            "current_trends": self._extract_trends(content),
            "emerging_topics": self._extract_emerging_topics(content),
            "declining_trends": self._extract_declining_trends(content),
            "trend_analysis": self._extract_key_findings(content)
        }
    
    def _extract_competitor_data(self, content: str) -> Dict[str, Any]:
        """Extract competitor analysis data"""
        return {
            "top_creators": self._extract_creator_names(content),
            "successful_strategies": self._extract_strategies(content),
            "content_formats": self._extract_content_formats(content),
            "engagement_tactics": self._extract_engagement_tactics(content)
        }
    
    def _create_failed_insights(self, task_id: str, error: str) -> SocialMediaInsights:
        """Create failed insights object"""
        return SocialMediaInsights(
            task_id=task_id,
            insights={},
            trending_hashtags=[],
            optimal_posting_times=[],
            competitor_analysis={},
            content_opportunities=[],
            engagement_strategies=[],
            location_trends={},
            success=False,
            error=error
        )
    
    # Additional helper methods for content extraction
    def _extract_key_findings(self, content: str) -> List[str]:
        """Extract key findings from content"""
        findings = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['key', 'important', 'finding', 'insight']):
                findings.append(line.strip())
        return findings[:5]
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from content"""
        recommendations = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['recommend', 'suggest', 'should', 'consider']):
                recommendations.append(line.strip())
        return recommendations[:5]
    
    def _extract_locations(self, content: str) -> List[str]:
        """Extract trending locations from content"""
        # This could be enhanced with named entity recognition
        locations = []
        content_lower = content.lower()
        bc_locations = ['whistler', 'vancouver', 'victoria', 'kamloops', 'kelowna', 'squamish', 'chilliwack']
        
        for location in bc_locations:
            if location in content_lower:
                locations.append(location.title())
        
        return locations
    
    def _extract_seasonal_info(self, content: str) -> List[str]:
        """Extract seasonal information"""
        seasonal_info = []
        seasons = ['spring', 'summer', 'fall', 'winter', 'seasonal']
        
        for season in seasons:
            if season in content.lower():
                seasonal_info.append(f"{season.title()} considerations found")
        
        return seasonal_info
    
    def _extract_regional_data(self, content: str) -> List[str]:
        """Extract regional preferences"""
        return ["BC-specific outdoor preferences", "Local community engagement patterns"]
    
    def _extract_trends(self, content: str) -> List[str]:
        """Extract current trends"""
        trends = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['trend', 'popular', 'growing', 'increasing']):
                trends.append(line.strip())
        return trends[:5]
    
    def _extract_emerging_topics(self, content: str) -> List[str]:
        """Extract emerging topics"""
        topics = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['emerging', 'new', 'upcoming', 'rising']):
                topics.append(line.strip())
        return topics[:3]
    
    def _extract_declining_trends(self, content: str) -> List[str]:
        """Extract declining trends"""
        declining = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['declining', 'decreasing', 'fading', 'less popular']):
                declining.append(line.strip())
        return declining[:3]
    
    def _extract_creator_names(self, content: str) -> List[str]:
        """Extract creator names (would need enhancement for real extraction)"""
        return ["Top creator analysis available in full research results"]
    
    def _extract_strategies(self, content: str) -> List[str]:
        """Extract successful strategies"""
        strategies = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['strategy', 'approach', 'tactic', 'method']):
                strategies.append(line.strip())
        return strategies[:5]
    
    def _extract_content_formats(self, content: str) -> List[str]:
        """Extract successful content formats"""
        formats = []
        format_types = ['video', 'photo', 'story', 'reel', 'live', 'carousel', 'tutorial', 'review']
        
        for format_type in format_types:
            if format_type in content.lower():
                formats.append(f"{format_type.title()} content")
        
        return formats
    
    def _extract_engagement_tactics(self, content: str) -> List[str]:
        """Extract engagement tactics"""
        tactics = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['engagement', 'interact', 'comment', 'share']):
                tactics.append(line.strip())
        return tactics[:5]
    
    def _extract_content_gaps(self, content: str) -> List[str]:
        """Extract content gaps and opportunities"""
        gaps = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['gap', 'missing', 'opportunity', 'underserved']):
                gaps.append(line.strip())
        return gaps[:5]
    
    def _extract_successful_strategies(self, content: str) -> List[str]:
        """Extract successful engagement strategies"""
        return self._extract_strategies(content)
    
    def _extract_competitive_insights(self, content: str) -> Dict[str, Any]:
        """Extract competitive insights"""
        return {
            "market_position": "Analysis available in research results",
            "content_differentiation": self._extract_differentiation(content),
            "opportunity_areas": self._extract_content_gaps(content)
        }
    
    def _extract_differentiation(self, content: str) -> List[str]:
        """Extract differentiation opportunities"""
        return ["Unique content angle opportunities identified"]
    
    def _extract_trail_insights(self, content: str) -> Dict[str, Any]:
        """Extract trail-specific insights"""
        return {
            "current_conditions": self._extract_conditions(content),
            "accessibility": self._extract_accessibility(content),
            "safety_updates": self._extract_safety_info(content)
        }
    
    def _extract_conditions(self, content: str) -> List[str]:
        """Extract current trail conditions"""
        conditions = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['condition', 'access', 'open', 'closed', 'weather']):
                conditions.append(line.strip())
        return conditions[:5]
    
    def _extract_accessibility(self, content: str) -> List[str]:
        """Extract accessibility information"""
        access_info = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['accessible', 'access', 'difficulty', 'route']):
                access_info.append(line.strip())
        return access_info[:3]
    
    def _extract_safety_info(self, content: str) -> List[str]:
        """Extract safety information"""
        safety = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['safety', 'warning', 'caution', 'alert']):
                safety.append(line.strip())
        return safety[:3]
    
    def _extract_trail_content_opportunities(self, content: str) -> List[str]:
        """Extract trail-specific content opportunities"""
        return [
            "Trail condition updates",
            "Seasonal accessibility guides", 
            "Safety tip content",
            "Hidden gem discoveries",
            "Weather impact stories"
        ]
    
    def _extract_trail_trends(self, content: str) -> Dict[str, Any]:
        """Extract trail and outdoor trends"""
        return {
            "popular_trails": self._extract_locations(content),
            "seasonal_trends": self._extract_seasonal_info(content),
            "activity_trends": self._extract_activity_trends(content)
        }
    
    def _extract_activity_trends(self, content: str) -> List[str]:
        """Extract outdoor activity trends"""
        activities = ['hiking', 'camping', 'backpacking', 'rock climbing', 'mountain biking']
        found_activities = []
        
        for activity in activities:
            if activity in content.lower():
                found_activities.append(f"{activity.title()} trend identified")
        
        return found_activities
    
    def _extract_posting_insights(self, content: str) -> Dict[str, Any]:
        """Extract posting strategy insights"""
        return {
            "timing_analysis": self._extract_timing_analysis(content),
            "frequency_recommendations": self._extract_frequency_info(content),
            "content_mix": self._extract_content_mix(content)
        }
    
    def _extract_timing_analysis(self, content: str) -> List[str]:
        """Extract timing analysis"""
        timing = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['time', 'timing', 'when', 'schedule']):
                timing.append(line.strip())
        return timing[:3]
    
    def _extract_frequency_info(self, content: str) -> List[str]:
        """Extract posting frequency information"""
        frequency = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['frequency', 'often', 'daily', 'weekly']):
                frequency.append(line.strip())
        return frequency[:3]
    
    def _extract_content_mix(self, content: str) -> List[str]:
        """Extract content mix recommendations"""
        return ["Content variety recommendations available in research results"]
    
    def _extract_optimal_times(self, content: str, platform: str) -> List[str]:
        """Extract optimal posting times with fallback to platform defaults"""
        times = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['time', 'pm', 'am', 'hour']):
                if any(time_word in line.lower() for time_word in ['best', 'optimal', 'peak']):
                    times.append(line.strip())
        
        # Fallback to platform defaults if no specific times found
        if not times:
            times = self.platform_strategies.get(platform, {}).get("optimal_times", [])
        
        return times[:5]
    
    def _extract_engagement_optimization(self, content: str) -> List[str]:
        """Extract engagement optimization strategies"""
        strategies = []
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['engagement', 'optimize', 'increase', 'boost']):
                strategies.append(line.strip())
        return strategies[:5]

# Example usage and testing
async def demo_social_media_research():
    """Demonstrate social media research capabilities"""
    async with SocialMediaResearchAgent() as agent:
        print("📱 Social Media Research Agent Demo")
        
        # Test hashtag research for vanlife content
        vanlife_task = SocialMediaResearchTask(
            id="demo_vanlife_hashtags",
            task_type="hashtag_research",
            content_niche="vanlife",
            platform="instagram",
            time_filter="week",
            location_filter="Southern BC, Canada"
        )
        
        print("\n🏕️ Researching vanlife hashtags...")
        hashtag_results = await agent.research_hashtags(vanlife_task)
        
        if hashtag_results.success:
            print(f"✅ Found {len(hashtag_results.trending_hashtags)} trending hashtags")
            print(f"📈 Content opportunities: {len(hashtag_results.content_opportunities)}")
            print(f"🎯 Engagement strategies: {len(hashtag_results.engagement_strategies)}")
        else:
            print(f"❌ Research failed: {hashtag_results.error}")
        
        # Test trail conditions research
        trail_task = SocialMediaResearchTask(
            id="demo_trail_conditions",
            task_type="trail_conditions",
            content_niche="southern_bc_trails",
            platform="instagram",
            location_filter="Southern BC, Canada"
        )
        
        print("\n🥾 Researching BC trail conditions...")
        trail_results = await agent.research_trail_conditions(trail_task)
        
        if trail_results.success:
            print(f"✅ Trail insights gathered")
            print(f"📍 Location trends: {len(trail_results.location_trends)}")
        else:
            print(f"❌ Trail research failed: {trail_results.error}")

if __name__ == "__main__":
    asyncio.run(demo_social_media_research())