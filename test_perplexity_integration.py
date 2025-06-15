#!/usr/bin/env python3
"""
Test Perplexity API Integration
Validates all Perplexity features in the multi-LLM agent system
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from perplexity_research_agent import PerplexityResearchAgent, ResearchQuery
from enhanced_orchestrator_claude_gemini import enhanced_orchestrator, TaskPriority, AgentType

async def test_perplexity_api_connection():
    """Test basic Perplexity API connection"""
    print("🔍 Testing Perplexity API Connection")
    print("-" * 50)
    
    try:
        async with PerplexityResearchAgent() as agent:
            query = ResearchQuery(
                id="connection_test",
                query="What is the current state of AI agent orchestration?",
                context="Testing API connection",
                research_type="general"
            )
            
            result = await agent.research(query)
            
            if result.success:
                print("✅ Perplexity API connection successful")
                print(f"💰 Cost: ${result.cost:.4f}")
                print(f"🔤 Tokens: {result.tokens_used}")
                print(f"⏱️ Time: {result.processing_time:.2f}s")
                print(f"📄 Response preview: {result.content[:200]}...")
                return True
            else:
                print(f"❌ API connection failed: {result.error}")
                return False
                
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

async def test_research_capabilities():
    """Test various research capabilities"""
    print("\n🔬 Testing Research Capabilities")
    print("-" * 50)
    
    test_queries = [
        {
            "name": "Technical Research",
            "query": "latest developments in Python FastAPI framework",
            "type": "technical"
        },
        {
            "name": "Trend Analysis", 
            "query": "current AI and machine learning trends",
            "type": "trending"
        },
        {
            "name": "Comparison Research",
            "query": "Claude vs Gemini vs GPT-4 comparison",
            "type": "comparison"
        }
    ]
    
    async with PerplexityResearchAgent() as agent:
        for test in test_queries:
            print(f"\n📋 {test['name']}:")
            
            query = ResearchQuery(
                id=f"test_{test['name'].lower().replace(' ', '_')}",
                query=test["query"],
                context=f"Testing {test['name']} capability",
                research_type=test["type"]
            )
            
            result = await agent.research(query)
            
            if result.success:
                print(f"  ✅ Success - ${result.cost:.4f} - {result.tokens_used} tokens")
                print(f"  📝 Preview: {result.content[:150]}...")
                
                if result.related_questions:
                    print(f"  ❓ Related: {result.related_questions[0]}")
            else:
                print(f"  ❌ Failed: {result.error}")

async def test_enhanced_orchestrator_integration():
    """Test Perplexity integration with enhanced orchestrator"""
    print("\n🤖 Testing Enhanced Orchestrator Integration")
    print("-" * 50)
    
    try:
        # Add research tasks that should use Perplexity
        research_tasks = [
            {
                "name": "Current AI Trends Research",
                "description": "research current trends in artificial intelligence and machine learning for 2024",
                "agent_type": AgentType.CONTENT_PROCESSOR,
                "priority": TaskPriority.HIGH
            },
            {
                "name": "Web Search Task",
                "description": "find latest information about multi-agent systems and orchestration patterns",
                "agent_type": AgentType.SYSTEM_ANALYST, 
                "priority": TaskPriority.MEDIUM
            },
            {
                "name": "Technical Research",
                "description": "research best practices for Python async programming and FastAPI development",
                "agent_type": AgentType.CODE_DEVELOPER,
                "priority": TaskPriority.MEDIUM
            }
        ]
        
        task_ids = []
        for task in research_tasks:
            task_id = enhanced_orchestrator.add_task(
                task["name"],
                task["description"], 
                task["agent_type"],
                task["priority"]
            )
            task_ids.append(task_id)
            print(f"✅ Added task: {task['name']}")
        
        # Execute first task to test integration
        if enhanced_orchestrator.task_queue:
            test_task = enhanced_orchestrator.task_queue[0]
            agent = enhanced_orchestrator.get_optimal_agent_for_task(test_task)
            
            print(f"\n🎯 Executing test task with {agent.name}")
            result = await agent.execute_task(test_task)
            
            if result.get("success"):
                print(f"✅ Task executed successfully")
                print(f"🔧 Provider used: {result.get('provider', 'unknown')}")
                print(f"💰 Cost: ${result.get('cost', 0):.4f}")
                print(f"🔤 Tokens: {result.get('tokens_used', 0)}")
                
                if result.get("has_web_search"):
                    print("🌐 Web search capability confirmed")
                
                return True
            else:
                print(f"❌ Task execution failed: {result.get('error', 'Unknown error')}")
                return False
        
    except Exception as e:
        print(f"❌ Orchestrator integration test failed: {e}")
        return False

async def test_provider_selection():
    """Test that research tasks prefer Perplexity"""
    print("\n⚖️ Testing Provider Selection Logic")
    print("-" * 50)
    
    try:
        # Get a content processor agent (should prefer Perplexity for research)
        agent = enhanced_orchestrator.agents.get("content_processor")
        
        if not agent:
            print("❌ Content processor agent not found")
            return False
        
        # Test task classification
        research_tasks = [
            "research current trends in AI",
            "find latest information about Python frameworks", 
            "investigate web search capabilities",
            "analyze trending topics in technology"
        ]
        
        for task_desc in research_tasks:
            task_type = agent._classify_task_type(task_desc)
            preferred_provider = agent.get_preferred_provider_for_task(task_type)
            
            print(f"📝 '{task_desc}'")
            print(f"   Type: {task_type}")
            print(f"   Preferred: {preferred_provider}")
            
            # Research-type tasks should prefer Perplexity
            if task_type in ["research", "web_search", "trend_analysis", "real_time_info"]:
                if preferred_provider == "perplexity":
                    print("   ✅ Correctly routed to Perplexity")
                else:
                    print(f"   ⚠️ Expected Perplexity, got {preferred_provider}")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider selection test failed: {e}")
        return False

async def test_cost_and_performance():
    """Test cost tracking and performance metrics"""
    print("\n💰 Testing Cost and Performance Metrics")
    print("-" * 50)
    
    try:
        async with PerplexityResearchAgent() as agent:
            # Test different model costs
            queries = [
                ResearchQuery(
                    id="cost_test_1",
                    query="quick test query",
                    context="Cost testing",
                    research_type="general"
                ),
                ResearchQuery(
                    id="cost_test_2", 
                    query="more detailed technical analysis query that should use more tokens",
                    context="Cost testing for larger responses",
                    research_type="technical"
                )
            ]
            
            total_cost = 0
            total_tokens = 0
            
            for query in queries:
                result = await agent.research(query)
                
                if result.success:
                    total_cost += result.cost
                    total_tokens += result.tokens_used
                    
                    print(f"Query {query.id}:")
                    print(f"  💰 Cost: ${result.cost:.4f}")
                    print(f"  🔤 Tokens: {result.tokens_used}")
                    print(f"  ⏱️ Time: {result.processing_time:.2f}s")
            
            print(f"\n📊 Total Cost: ${total_cost:.4f}")
            print(f"📊 Total Tokens: {total_tokens}")
            print(f"📊 Average Cost per Token: ${(total_cost/total_tokens):.6f}" if total_tokens > 0 else "N/A")
            
            return True
            
    except Exception as e:
        print(f"❌ Cost and performance test failed: {e}")
        return False

async def main():
    """Run all Perplexity integration tests"""
    print("🚀 PERPLEXITY INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Check API key
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("❌ PERPLEXITY_API_KEY not found in environment")
        return
    
    tests = [
        ("API Connection", test_perplexity_api_connection),
        ("Research Capabilities", test_research_capabilities),
        ("Orchestrator Integration", test_enhanced_orchestrator_integration),
        ("Provider Selection", test_provider_selection),
        ("Cost & Performance", test_cost_and_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Perplexity integration is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    # Show system status
    print(f"\n🔍 System Status:")
    status = enhanced_orchestrator.get_system_status()
    print(f"  Agents: {status['total_agents']}")
    print(f"  Provider Stats: {list(status['provider_stats'].keys())}")

if __name__ == "__main__":
    asyncio.run(main())