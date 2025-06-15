#!/usr/bin/env python3
"""
Simple TDD System Test Script
Test the TDD system with a basic cycle to verify it works
"""

import sys
import os
import asyncio
from datetime import datetime

# Add current directory to path
sys.path.append('/home/ikino/dev/autonomous-multi-llm-agent')

def test_basic_tdd_system():
    """Test basic TDD system functionality"""
    try:
        print("🧪 Testing TDD System...")
        
        # Import TDD system
        from tdd_system import tdd_system
        
        print("✅ TDD System imported successfully")
        
        # Create a simple TDD cycle
        cycle_id = tdd_system.create_tdd_cycle(
            name="Simple Math Test",
            description="Test basic math operations"
        )
        
        print(f"✅ Created TDD cycle: {cycle_id}")
        
        # Test the database tables exist
        cycles = tdd_system.db.get_table_data('tdd_cycles')
        print(f"✅ Found {len(cycles)} TDD cycles in database")
        
        # Check if we can generate tests (without actually calling the LLM)
        print("🔧 Testing test generation structure...")
        
        # Mock test generation
        test_code = '''
import pytest

def test_add_numbers():
    """Test basic addition"""
    # This test should fail initially (Red phase)
    from math_utils import add_numbers
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0

def test_multiply_numbers():
    """Test basic multiplication"""
    from math_utils import multiply_numbers  
    assert multiply_numbers(2, 3) == 6
    assert multiply_numbers(-1, 5) == -5
    assert multiply_numbers(0, 10) == 0
'''
        
        # Save manual test case
        test_case_id = tdd_system.db.add_record('test_cases', {
            'cycle_id': cycle_id,
            'name': 'Manual Math Test',
            'description': 'Basic math operations test',
            'test_code': test_code,
            'status': 'red',
            'created_date': datetime.now().isoformat()
        })
        
        print(f"✅ Created test case: {test_case_id}")
        
        # Test file creation
        test_file = tdd_system.test_dir / f"test_cycle_{cycle_id}_{test_case_id}.py"
        test_file.write_text(test_code)
        
        print(f"✅ Created test file: {test_file}")
        
        # Test basic test running (should fail because math_utils doesn't exist)
        print("🧪 Testing test execution...")
        
        test_results = tdd_system.run_tests(cycle_id)
        print(f"✅ Test run completed: {test_results.get('success', False)}")
        print(f"   - Total tests: {test_results.get('total_tests', 0)}")
        print(f"   - Failing tests: {test_results.get('failing_tests', 0)}")
        
        # Create simple implementation to make tests pass
        impl_code = '''
def add_numbers(a, b):
    """Add two numbers"""
    return a + b

def multiply_numbers(a, b):
    """Multiply two numbers"""
    return a * b
'''
        
        # Save implementation
        impl_file = tdd_system.src_dir / "math_utils.py"
        impl_file.write_text(impl_code)
        
        print(f"✅ Created implementation: {impl_file}")
        
        # Test again (should pass now)
        print("🧪 Testing with implementation...")
        test_results = tdd_system.run_tests(cycle_id)
        print(f"✅ Test run completed: {test_results.get('success', False)}")
        print(f"   - Total tests: {test_results.get('total_tests', 0)}")
        print(f"   - Passing tests: {test_results.get('passing_tests', 0)}")
        print(f"   - Failing tests: {test_results.get('failing_tests', 0)}")
        
        # Get cycle status
        status = tdd_system.get_cycle_status(cycle_id)
        print(f"✅ Cycle status retrieved: {status.get('success', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ TDD System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_orchestrator_import():
    """Test if we can import the orchestrator"""
    try:
        print("🤖 Testing Enhanced Orchestrator import...")
        
        # Test orchestrator import
        from enhanced_orchestrator_claude_gemini import enhanced_orchestrator, AgentType, TaskPriority
        
        print("✅ Enhanced Orchestrator imported successfully")
        
        # Test system status
        status = enhanced_orchestrator.get_system_status()
        print(f"✅ System status: {status['total_agents']} agents, {status['pending_tasks']} pending tasks")
        
        # Test agent creation
        agents = enhanced_orchestrator.agents
        print(f"✅ Available agents:")
        for agent_id, agent in agents.items():
            print(f"   - {agent.name} ({agent.agent_type.value})")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting TDD System Tests...")
    print("=" * 50)
    
    # Test basic TDD system
    tdd_success = test_basic_tdd_system()
    print("=" * 50)
    
    # Test orchestrator
    orchestrator_success = test_orchestrator_import()
    print("=" * 50)
    
    if tdd_success and orchestrator_success:
        print("🎉 ALL TESTS PASSED - TDD System is working!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - TDD System needs fixes")
        sys.exit(1)