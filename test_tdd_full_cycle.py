#!/usr/bin/env python3
"""
Full TDD Cycle Test
Test the complete TDD system including API calls
"""

import sys
import os
import asyncio
from datetime import datetime

# Add current directory to path
sys.path.append('/home/ikino/dev/autonomous-multi-llm-agent')

def test_complete_tdd_cycle():
    """Test a complete TDD cycle with API integration"""
    try:
        print("🔄 Testing Complete TDD Cycle...")
        
        # Import TDD system
        from tdd_system import tdd_system
        
        # Create a TDD cycle
        cycle_id = tdd_system.create_tdd_cycle(
            name="String Utilities Test",
            description="Create a string utility module with functions to reverse strings and count words"
        )
        
        print(f"✅ Created TDD cycle: {cycle_id}")
        
        # Test the complete cycle (this will use the API)
        specification = """
        Create a string utility module with the following functions:
        1. reverse_string(text): Returns the reverse of a string
        2. count_words(text): Returns the number of words in a string
        3. is_palindrome(text): Returns True if the string is a palindrome
        
        Requirements:
        - Handle empty strings gracefully
        - Ignore case and spaces for palindrome checking
        - Count words by splitting on whitespace
        """
        
        print("🚀 Starting complete TDD cycle...")
        
        # This will test the full Red-Green-Refactor cycle
        results = tdd_system.complete_tdd_cycle(cycle_id, specification)
        
        print(f"✅ TDD Cycle completed: {results.get('success', False)}")
        
        if results.get('success'):
            print(f"💰 Total cost: ${results.get('total_cost', 0):.4f}")
            print(f"🔤 Total tokens: {results.get('total_tokens', 0)}")
            
            # Check each phase
            phases = results.get('phases', {})
            for phase_name, phase_result in phases.items():
                if isinstance(phase_result, dict):
                    success = phase_result.get('success', False)
                    print(f"   {phase_name}: {'✅' if success else '❌'}")
        else:
            print(f"❌ TDD Cycle failed: {results.get('error', 'Unknown error')}")
            
        return results.get('success', False)
        
    except Exception as e:
        print(f"❌ Complete TDD cycle test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_api_integration():
    """Test manual API integration to verify orchestrator works"""
    try:
        print("🤖 Testing Manual API Integration...")
        
        # Import orchestrator
        from enhanced_orchestrator_claude_gemini import enhanced_orchestrator, AgentType, TaskPriority
        
        # Add a simple task
        task_id = enhanced_orchestrator.add_task(
            "Simple Test Task",
            "Create a Python function that calculates the factorial of a number",
            AgentType.CODE_DEVELOPER,
            TaskPriority.HIGH
        )
        
        print(f"✅ Added task: {task_id}")
        
        # Get the task and agent
        task = next(t for t in enhanced_orchestrator.task_queue if t.id == task_id)
        agent = enhanced_orchestrator.get_optimal_agent_for_task(task)
        
        print(f"✅ Selected agent: {agent.name}")
        
        # Execute the task
        async def run_task():
            result = await agent.execute_task(task)
            return result
        
        print("🚀 Executing task...")
        result = asyncio.run(run_task())
        
        print(f"✅ Task completed: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"💰 Cost: ${result.get('cost', 0):.4f}")
            print(f"🔤 Tokens: {result.get('tokens_used', 0)}")
            print(f"🤖 Provider: {result.get('provider', 'unknown')}")
            
            # Print first 200 chars of result
            task_result = result.get('result', '')
            if task_result:
                print(f"📝 Result preview: {task_result[:200]}...")
        else:
            print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Manual API integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Full TDD System Tests...")
    print("=" * 60)
    
    # Test manual API integration first
    api_success = test_manual_api_integration()
    print("=" * 60)
    
    if api_success:
        # If API works, test complete TDD cycle
        tdd_success = test_complete_tdd_cycle()
        print("=" * 60)
        
        if tdd_success:
            print("🎉 ALL TESTS PASSED - Full TDD System is working!")
            sys.exit(0)
        else:
            print("❌ TDD CYCLE FAILED - But API integration works")
            sys.exit(1)
    else:
        print("❌ API INTEGRATION FAILED - Skipping TDD cycle test")
        sys.exit(1)