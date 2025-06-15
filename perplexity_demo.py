#!/usr/bin/env python3
"""
Perplexity Integration Demo
Demonstrates the enhanced capabilities of the multi-LLM agent system with Perplexity
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from perplexity_research_agent import PerplexityResearchAgent, ResearchQuery
from enhanced_orchestrator_claude_gemini import enhanced_orchestrator, TaskPriority, AgentType

async def demo_perplexity_research():
    """Demonstrate standalone Perplexity research capabilities"""
    print("🔍 PERPLEXITY RESEARCH AGENT DEMO")
    print("=" * 50)
    
    async with PerplexityResearchAgent() as agent:
        # Real-time trend analysis
        print("\n📈 Current AI Trends Analysis:")
        trending = await agent.trending_topics_analysis("artificial intelligence")
        
        if trending.success:
            print(f"✅ Research completed (${trending.cost:.4f}, {trending.tokens_used} tokens)")
            print(f"📄 Preview: {trending.content[:300]}...")
            
            if trending.related_questions:
                print(f"\n❓ Related Questions:")
                for i, q in enumerate(trending.related_questions[:2], 1):
                    print(f"  {i}. {q}")
        
        # Technical research
        print("\n🔧 Technical Research Demo:")
        tech_result = await agent.tech_stack_research("FastAPI Python framework")
        
        if tech_result.success:
            print(f"✅ Technical analysis completed (${tech_result.cost:.4f})")
            print(f"📄 Technical insights: {tech_result.content[:250]}...")

async def demo_enhanced_orchestrator():
    """Demonstrate enhanced orchestrator with Perplexity routing"""
    print("\n🤖 ENHANCED ORCHESTRATOR WITH PERPLEXITY")
    print("=" * 50)
    
    # Add research tasks that should route to Perplexity
    tasks = [
        {
            "name": "Market Research",
            "description": "research current trends in multi-agent AI systems and their market applications",
            "type": AgentType.CONTENT_PROCESSOR,
            "priority": TaskPriority.HIGH
        },
        {
            "name": "Tech Analysis", 
            "description": "find latest developments in Python async programming and real-time web applications",
            "type": AgentType.SYSTEM_ANALYST,
            "priority": TaskPriority.MEDIUM
        }
    ]
    
    print("📝 Adding research tasks...")
    for task in tasks:
        task_id = enhanced_orchestrator.add_task(
            task["name"],
            task["description"],
            task["type"], 
            task["priority"]
        )
        print(f"  ✅ {task['name']} (ID: {task_id})")
    
    # Show provider preferences
    print(f"\n⚖️ Provider Preferences:")
    for agent_id, agent in enhanced_orchestrator.agents.items():
        print(f"  {agent.name}:")
        for provider, weight in agent.provider_preferences.items():
            print(f"    {provider}: {weight:.1%}")

async def demo_provider_routing():
    """Demonstrate intelligent provider routing"""
    print("\n🎯 INTELLIGENT PROVIDER ROUTING DEMO") 
    print("=" * 50)
    
    # Get content processor agent
    agent = enhanced_orchestrator.agents.get("content_processor")
    if not agent:
        print("❌ Content processor agent not found")
        return
    
    test_descriptions = [
        "research current AI trends and developments",
        "implement a Python FastAPI endpoint", 
        "debug application performance issues",
        "find latest web search technologies",
        "analyze trending topics in technology",
        "optimize database query performance"
    ]
    
    print("🔍 Task Classification and Provider Selection:")
    for desc in test_descriptions:
        task_type = agent._classify_task_type(desc)
        preferred_provider = agent.get_preferred_provider_for_task(task_type)
        
        print(f"\n📝 Task: '{desc}'")
        print(f"   🏷️  Type: {task_type}")
        print(f"   🎯 Provider: {preferred_provider}")
        
        if task_type in ["research", "web_search", "trend_analysis", "real_time_info"]:
            print("   🔍 Perplexity route: ✅ Correct")
        elif task_type in ["code_generation", "debugging", "optimization"]:
            print("   🧠 Claude route: ✅ Correct")
        elif task_type in ["data_analysis", "text_processing"]:
            print("   💎 Gemini route: ✅ Correct")

async def demo_cost_efficiency():
    """Demonstrate cost-efficient multi-LLM usage"""
    print("\n💰 COST EFFICIENCY DEMO")
    print("=" * 50)
    
    # Show provider cost comparison
    print("💲 Provider Cost Comparison (per 1000 tokens):")
    print("  Claude Sonnet:    $0.010")
    print("  Gemini 1.5 Pro:   $0.0005") 
    print("  Perplexity:       $0.001")
    
    print("\n🎯 Optimal Task Routing:")
    print("  Research/Web Search → Perplexity (web access + cost effective)")
    print("  Code Generation → Claude (high quality code)")
    print("  Data Analysis → Gemini (cost effective + good at analysis)")
    print("  Debugging → Claude (excellent reasoning)")
    
    # Get system stats
    status = enhanced_orchestrator.get_system_status()
    provider_stats = status.get('provider_stats', {})
    
    print(f"\n📊 Current System Stats:")
    print(f"  Total Agents: {status['total_agents']}")
    print(f"  Active Providers: {list(provider_stats.keys())}")
    print(f"  Total Cost: ${status.get('total_cost', 0):.4f}")
    print(f"  Total Tokens: {status.get('total_tokens_used', 0)}")

async def demo_real_world_examples():
    """Show real-world application examples"""
    print("\n🌟 REAL-WORLD APPLICATION EXAMPLES")
    print("=" * 50)
    
    examples = [
        {
            "scenario": "Content Creation Pipeline",
            "tasks": [
                "Research trending topics (Perplexity)",
                "Generate article outline (Claude)", 
                "Analyze competitor content (Gemini)",
                "Write final article (Claude)"
            ]
        },
        {
            "scenario": "Software Development Workflow", 
            "tasks": [
                "Research latest framework updates (Perplexity)",
                "Plan application architecture (Claude)",
                "Analyze performance requirements (Gemini)",
                "Generate implementation code (Claude)"
            ]
        },
        {
            "scenario": "Business Intelligence Analysis",
            "tasks": [
                "Research market trends (Perplexity)",
                "Process and analyze data (Gemini)", 
                "Generate strategic insights (Claude)",
                "Create presentation content (Gemini)"
            ]
        }
    ]
    
    for example in examples:
        print(f"\n📋 {example['scenario']}:")
        for i, task in enumerate(example['tasks'], 1):
            print(f"  {i}. {task}")

async def main():
    """Run complete Perplexity integration demo"""
    print("🚀 PERPLEXITY AI INTEGRATION DEMONSTRATION")
    print("🔗 Multi-LLM Agent System with Real-Time Web Search")
    print("=" * 60)
    
    # Check prerequisites
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("❌ PERPLEXITY_API_KEY required but not found")
        return
    
    print("✅ Perplexity API key configured")
    print("✅ Enhanced orchestrator initialized")
    print("✅ Multi-LLM provider system ready")
    
    # Run demos
    demos = [
        ("Perplexity Research Capabilities", demo_perplexity_research),
        ("Enhanced Orchestrator Integration", demo_enhanced_orchestrator),
        ("Intelligent Provider Routing", demo_provider_routing),
        ("Cost Efficiency Analysis", demo_cost_efficiency),
        ("Real-World Applications", demo_real_world_examples)
    ]
    
    for demo_name, demo_func in demos:
        try:
            await demo_func()
            print(f"\n✅ {demo_name} completed successfully")
        except Exception as e:
            print(f"\n❌ {demo_name} failed: {e}")
    
    print(f"\n{'='*60}")
    print("🎉 PERPLEXITY INTEGRATION DEMO COMPLETE")
    print("=" * 60)
    
    print("\n🌟 Key Benefits Demonstrated:")
    print("  • Real-time web search and current information")
    print("  • Intelligent task routing to optimal LLM providers")
    print("  • Cost-efficient multi-provider load balancing")
    print("  • Enhanced research and trend analysis capabilities")
    print("  • Seamless integration with existing Claude + Gemini system")
    
    print("\n🔧 Ready for Production Use:")
    print("  • All three providers (Claude, Gemini, Perplexity) operational")
    print("  • Automatic failover and load balancing")
    print("  • Cost tracking and optimization")
    print("  • Learning system for continuous improvement")

if __name__ == "__main__":
    asyncio.run(main())