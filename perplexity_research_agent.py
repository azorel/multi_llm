#!/usr/bin/env python3
"""
Perplexity Research Agent - Specialized AI agent for real-time research and web search
Integrates with the multi-LLM agent system to provide current information capabilities
"""

import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ResearchQuery:
    """Research query data structure"""
    id: str
    query: str
    context: str
    research_type: str  # "general", "trending", "technical", "news", "comparison"
    time_filter: str = "month"  # "hour", "day", "week", "month", "year", "all"
    max_results: int = 5
    include_images: bool = False
    include_related_questions: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

@dataclass 
class ResearchResult:
    """Research result data structure"""
    query_id: str
    success: bool
    content: str
    sources: List[Dict[str, Any]]
    related_questions: List[str]
    search_metadata: Dict[str, Any]
    tokens_used: int
    cost: float
    processing_time: float
    error: Optional[str] = None

class PerplexityResearchAgent:
    """Advanced research agent powered by Perplexity AI"""
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai"
        self.session = None
        
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
        
        # Research specializations
        self.research_models = {
            "general": "llama-3.1-sonar-large-128k-online",
            "technical": "llama-3.1-sonar-large-128k-online", 
            "trending": "llama-3.1-sonar-small-128k-online",
            "news": "llama-3.1-sonar-small-128k-online",
            "comparison": "llama-3.1-sonar-large-128k-online"
        }
        
        self.research_templates = {
            "general": "Provide comprehensive research on: {query}. Include current information, key insights, and authoritative sources.",
            "technical": "Provide detailed technical analysis of: {query}. Include current best practices, recent developments, and expert opinions.",
            "trending": "Research current trends and developments related to: {query}. Focus on what's happening now and recent changes.",
            "news": "Find the latest news and updates about: {query}. Prioritize recent developments and breaking news.",
            "comparison": "Provide a detailed comparison and analysis of: {query}. Include pros/cons, current market status, and expert recommendations."
        }
        
        logger.info("Perplexity Research Agent initialized successfully")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def research(self, query: ResearchQuery) -> ResearchResult:
        """Perform research using Perplexity AI"""
        start_time = datetime.now()
        
        try:
            # Get appropriate model and template
            model = self.research_models.get(query.research_type, self.research_models["general"])
            template = self.research_templates.get(query.research_type, self.research_templates["general"])
            
            # Prepare the request
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": f"""You are a specialized research agent with access to real-time web search. 
                        Your task is to provide accurate, current, and comprehensive information. 
                        Always cite your sources and indicate when information is current as of your search.
                        
                        Context: {query.context}"""
                    },
                    {
                        "role": "user",
                        "content": template.format(query=query.query)
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.1,
                "top_p": 0.9,
                "search_recency_filter": query.time_filter,
                "return_images": query.include_images,
                "return_related_questions": query.include_related_questions,
                "stream": False,
                "presence_penalty": 0,
                "frequency_penalty": 0.1
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make the request
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
                
                result = await response.json()
            
            # Process the response
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if "choices" not in result or not result["choices"]:
                raise Exception("Invalid response format from Perplexity API")
            
            content = result["choices"][0]["message"]["content"]
            
            # Extract metadata
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            cost = self._calculate_cost(model, tokens_used)
            
            # Extract sources and related questions if available
            sources = result.get("sources", [])
            related_questions = result.get("related_questions", [])
            
            return ResearchResult(
                query_id=query.id,
                success=True,
                content=content,
                sources=sources,
                related_questions=related_questions,
                search_metadata={
                    "model_used": model,
                    "search_recency": query.time_filter,
                    "response_time": processing_time,
                    "api_response": result
                },
                tokens_used=tokens_used,
                cost=cost,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Research failed for query {query.id}: {str(e)}")
            
            return ResearchResult(
                query_id=query.id,
                success=False,
                content="",
                sources=[],
                related_questions=[],
                search_metadata={},
                tokens_used=0,
                cost=0.0,
                processing_time=processing_time,
                error=str(e)
            )
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost based on model and token usage"""
        # Perplexity pricing (approximate per 1000 tokens)
        model_costs = {
            "llama-3.1-sonar-small-128k-online": 0.0002,
            "llama-3.1-sonar-large-128k-online": 0.001,
            "llama-3.1-sonar-huge-128k-online": 0.005
        }
        
        cost_per_1k = model_costs.get(model, 0.001)
        return (tokens / 1000) * cost_per_1k
    
    async def batch_research(self, queries: List[ResearchQuery]) -> List[ResearchResult]:
        """Perform multiple research queries in parallel"""
        tasks = [self.research(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ResearchResult(
                    query_id=queries[i].id,
                    success=False,
                    content="",
                    sources=[],
                    related_questions=[],
                    search_metadata={},
                    tokens_used=0,
                    cost=0.0,
                    processing_time=0.0,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def trending_topics_analysis(self, domain: str = "technology") -> ResearchResult:
        """Analyze current trending topics in a specific domain"""
        query = ResearchQuery(
            id=f"trending_{domain}_{int(datetime.now().timestamp())}",
            query=f"current trending topics in {domain}",
            context=f"Analyze what's currently trending and popular in the {domain} domain",
            research_type="trending",
            time_filter="day",
            include_related_questions=True
        )
        
        return await self.research(query)
    
    async def competitive_analysis(self, topic: str, competitors: List[str]) -> ResearchResult:
        """Perform competitive analysis research"""
        competitors_str = ", ".join(competitors)
        query = ResearchQuery(
            id=f"competitive_{topic}_{int(datetime.now().timestamp())}",
            query=f"competitive analysis of {topic} comparing {competitors_str}",
            context=f"Provide detailed competitive analysis and market positioning",
            research_type="comparison",
            time_filter="month",
            include_related_questions=True
        )
        
        return await self.research(query)
    
    async def tech_stack_research(self, technology: str) -> ResearchResult:
        """Research technical information about a technology stack"""
        query = ResearchQuery(
            id=f"tech_{technology}_{int(datetime.now().timestamp())}",
            query=f"comprehensive technical analysis of {technology} including best practices, current status, and implementation guidance",
            context="Provide technical insights for development and implementation decisions",
            research_type="technical",
            time_filter="month",
            include_related_questions=True
        )
        
        return await self.research(query)
    
    async def market_research(self, market_topic: str) -> ResearchResult:
        """Perform market research on a specific topic"""
        query = ResearchQuery(
            id=f"market_{market_topic}_{int(datetime.now().timestamp())}",
            query=f"current market analysis and trends for {market_topic}",
            context="Provide market insights including size, trends, opportunities, and key players",
            research_type="general",
            time_filter="month",
            include_related_questions=True
        )
        
        return await self.research(query)

# Example usage and testing
async def demo_perplexity_research():
    """Demonstrate Perplexity research capabilities"""
    async with PerplexityResearchAgent() as agent:
        print("🔍 Perplexity Research Agent Demo")
        
        # Test general research
        query = ResearchQuery(
            id="demo_1",
            query="latest developments in AI agent orchestration",
            context="Research for multi-LLM agent system development",
            research_type="technical"
        )
        
        result = await agent.research(query)
        
        print(f"\n✅ Research completed: {result.success}")
        print(f"💰 Cost: ${result.cost:.4f}")
        print(f"🔤 Tokens: {result.tokens_used}")
        print(f"⏱️ Time: {result.processing_time:.2f}s")
        
        if result.success:
            print(f"\n📄 Content Preview:")
            print(result.content[:500] + "..." if len(result.content) > 500 else result.content)
            
            if result.related_questions:
                print(f"\n❓ Related Questions:")
                for i, question in enumerate(result.related_questions[:3], 1):
                    print(f"  {i}. {question}")
        
        # Test trending topics
        trending = await agent.trending_topics_analysis("AI and machine learning")
        print(f"\n📈 Trending Topics Analysis: {trending.success}")
        if trending.success:
            print(f"Preview: {trending.content[:300]}...")

if __name__ == "__main__":
    asyncio.run(demo_perplexity_research())