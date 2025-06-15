#!/usr/bin/env python3
"""
TDD System Validation Test
Tests the complete TDD cycle functionality
"""

import asyncio
import logging
import sys
import os
from tdd_system import tdd_system

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_tdd_cycle():
    """Test complete TDD cycle functionality"""
    print('🧪 TDD System Complete Test Cycle')
    print('='*50)
    
    try:
        # Create a TDD cycle
        cycle_id = tdd_system.create_tdd_cycle(
            'Test Calculator Functions',
            'Create basic calculator functions with proper error handling'
        )
        
        if cycle_id == -1:
            print('❌ Failed to create TDD cycle')
            return False
            
        print(f'✅ Created TDD cycle: {cycle_id}')
        
        # Test specification
        specification = '''
        Create a Calculator class with the following methods:
        - add(a, b): Returns the sum of two numbers
        - subtract(a, b): Returns the difference of two numbers  
        - multiply(a, b): Returns the product of two numbers
        - divide(a, b): Returns the quotient, raises ValueError for division by zero
        
        All methods should handle integer and float inputs.
        Include proper error handling and type validation.
        '''
        
        # Complete full TDD cycle
        print('🔄 Starting complete TDD cycle...')
        result = await tdd_system.complete_tdd_cycle(cycle_id, specification)
        
        print()
        print('📊 TDD Cycle Results:')
        print(f'Success: {result.get("success", False)}')
        print(f'Total Cost: ${result.get("total_cost", 0):.4f}')
        print(f'Total Tokens: {result.get("total_tokens", 0)}')
        
        # Show phase results
        for phase, phase_result in result.get('phases', {}).items():
            success_symbol = "✅" if phase_result.get("success", False) else "❌"
            print(f'  {phase.upper()}: {success_symbol}')
            if phase_result.get('error'):
                print(f'    Error: {phase_result["error"]}')
        
        # Get cycle status
        print()
        print('📈 Final Cycle Status:')
        status = tdd_system.get_cycle_status(cycle_id)
        if status['success']:
            metrics = status['metrics']
            print(f'Total Tests: {metrics["total_tests"]}')
            print(f'Passing Tests: {metrics["passing_tests"]}')
            print(f'Failing Tests: {metrics["failing_tests"]}')
            coverage = metrics["coverage_percentage"]
            if coverage is not None:
                print(f'Coverage: {coverage:.1f}%')
            else:
                print('Coverage: N/A')
        else:
            print(f'Error getting status: {status.get("error", "Unknown")}')
        
        return result.get("success", False)
        
    except Exception as e:
        print(f'❌ TDD System Test Failed: {e}')
        logger.error(f"TDD test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic TDD system functionality without async"""
    print('🔧 Testing Basic TDD Functionality')
    print('='*40)
    
    try:
        # Test cycle creation
        cycle_id = tdd_system.create_tdd_cycle(
            'Basic Test Cycle',
            'Test basic functionality'
        )
        
        if cycle_id == -1:
            print('❌ Failed to create basic cycle')
            return False
            
        print(f'✅ Created basic cycle: {cycle_id}')
        
        # Test listing cycles
        cycles = tdd_system.list_all_cycles()
        if cycles['success']:
            print(f'✅ Total cycles: {cycles["total_cycles"]}')
            print(f'✅ Active cycles: {cycles["active_cycles"]}')
        else:
            print(f'❌ Failed to list cycles: {cycles.get("error")}')
            return False
        
        # Test getting cycle status
        status = tdd_system.get_cycle_status(cycle_id)
        if status['success']:
            print('✅ Successfully retrieved cycle status')
        else:
            print(f'❌ Failed to get cycle status: {status.get("error")}')
            return False
        
        return True
        
    except Exception as e:
        print(f'❌ Basic functionality test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print('🚀 TDD System Validation Test Suite')
    print('='*60)
    
    # Test basic functionality first
    basic_success = test_basic_functionality()
    print()
    
    if not basic_success:
        print('❌ Basic tests failed, skipping full cycle test')
        return False
    
    # Test full TDD cycle
    try:
        full_success = asyncio.run(test_tdd_cycle())
        print()
        
        if full_success:
            print('🎉 All TDD System Tests Passed!')
            return True
        else:
            print('❌ TDD System Tests Failed!')
            return False
            
    except Exception as e:
        print(f'❌ Full cycle test failed: {e}')
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)