#!/usr/bin/env python3
"""
Final Multi-Agent System Test
Comprehensive validation of the enhanced Claude + Gemini orchestrator
"""

import asyncio
from enhanced_orchestrator_claude_gemini import enhanced_orchestrator, AgentType, TaskPriority

async def test_enhanced_multi_agent_system():
    print('🚀 COMPREHENSIVE MULTI-AGENT SYSTEM TEST')
    print('========================================')
    
    # Create diverse test tasks for different agents
    test_tasks = [
        {
            'name': 'Validate Code Quality',
            'description': 'Analyze the enhanced orchestrator code for quality, patterns, and optimizations. Focus on Claude vs Gemini usage patterns.',
            'agent_type': AgentType.CODE_DEVELOPER,
            'priority': TaskPriority.HIGH
        },
        {
            'name': 'System Performance Analysis', 
            'description': 'Analyze system performance metrics, provider selection efficiency, and identify optimization opportunities.',
            'agent_type': AgentType.SYSTEM_ANALYST,
            'priority': TaskPriority.HIGH
        },
        {
            'name': 'Database Schema Validation',
            'description': 'Validate enhanced database schema design and suggest improvements for better performance.',
            'agent_type': AgentType.DATABASE_SPECIALIST,
            'priority': TaskPriority.MEDIUM
        },
        {
            'name': 'Integration Testing Strategy',
            'description': 'Design comprehensive integration testing strategy for Claude+Gemini dual-provider system.',
            'agent_type': AgentType.WEB_TESTER,
            'priority': TaskPriority.MEDIUM
        }
    ]
    
    # Add all tasks
    tasks = []
    for task_data in test_tasks:
        task_id = enhanced_orchestrator.add_task(
            task_data['name'],
            task_data['description'], 
            task_data['agent_type'],
            task_data['priority']
        )
        tasks.append(enhanced_orchestrator.task_queue[-1])
        print(f'📋 Added: {task_data["name"]}')
    
    print(f'\n🔥 Executing {len(tasks)} tasks in parallel...')
    start_time = asyncio.get_event_loop().time()
    
    # Execute all tasks in parallel
    results = await enhanced_orchestrator.execute_tasks_parallel(tasks)
    
    end_time = asyncio.get_event_loop().time()
    execution_time = end_time - start_time
    
    # Analyze results
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    total_cost = sum(r.get('cost', 0) for r in successful)
    total_tokens = sum(r.get('tokens_used', 0) for r in successful)
    
    print(f'\n✅ EXECUTION COMPLETE in {execution_time:.2f}s')
    print(f'Success: {len(successful)}/{len(results)}')
    print(f'Failed: {len(failed)}')
    print(f'Total cost: ${total_cost:.4f}')
    print(f'Total tokens: {total_tokens}')
    
    # Show provider distribution
    providers_used = {}
    for result in successful:
        provider = result.get('provider', 'unknown')
        providers_used[provider] = providers_used.get(provider, 0) + 1
    
    print(f'Provider distribution: {providers_used}')
    
    # Show successful results summary
    print(f'\n🎯 SUCCESSFUL EXECUTIONS:')
    for i, result in enumerate(successful):
        task_name = tasks[i].name if i < len(tasks) else 'Unknown Task'
        print(f'{i+1}. {task_name}')
        print(f'   Agent: {result.get("agent", "Unknown")}')
        print(f'   Provider: {result.get("provider", "Unknown")}')
        print(f'   Tokens: {result.get("tokens_used", 0)}')
        print(f'   Cost: ${result.get("cost", 0):.4f}')
        if result.get('result'):
            print(f'   Result: {result["result"][:100]}...')
        print()
    
    # Show failed tasks
    if failed:
        print(f'❌ FAILED EXECUTIONS:')
        for i, result in enumerate(failed):
            print(f'{i+1}. Error: {result.get("error", "Unknown error")}')
    
    # System status after execution
    status = enhanced_orchestrator.get_system_status()
    print(f'📊 FINAL SYSTEM STATUS:')
    print(f'Total agents: {status["total_agents"]}')
    print(f'Tasks completed: {status["completed_tasks"]}')
    print(f'Total system cost: ${status["total_cost"]:.4f}')
    print(f'Total system tokens: {status["total_tokens_used"]}')
    print(f'Learning system entries: {status["learning_system_entries"]}')
    
    # Provider performance comparison
    provider_stats = status["provider_stats"]
    print(f'\n📈 PROVIDER PERFORMANCE:')
    for provider, stats in provider_stats.items():
        print(f'{provider.title()}:')
        print(f'  Requests: {stats["requests"]}')
        print(f'  Error rate: {stats.get("error_rate", 0):.2%}')
        print(f'  Avg response time: {stats.get("avg_response_time", 0):.2f}s')
        print(f'  Total cost: ${stats["cost"]:.4f}')
    
    return {
        'successful_tasks': len(successful),
        'total_tasks': len(results),
        'total_cost': total_cost,
        'total_tokens': total_tokens,
        'execution_time': execution_time,
        'provider_distribution': providers_used,
        'system_status': status
    }

async def main():
    try:
        print('🎯 Enhanced Multi-Agent Orchestrator - Final Validation')
        print('=' * 60)
        
        result = await test_enhanced_multi_agent_system()
        
        print(f'\n🏆 MULTI-AGENT SYSTEM VALIDATION COMPLETE')
        print(f'Success Rate: {result["successful_tasks"]}/{result["total_tasks"]} ({100*result["successful_tasks"]/result["total_tasks"]:.1f}%)')
        print(f'Total Execution Time: {result["execution_time"]:.2f}s')
        print(f'Cost Efficiency: ${result["total_cost"]/max(result["successful_tasks"], 1):.4f} per successful task')
        print(f'Token Efficiency: {result["total_tokens"]/max(result["successful_tasks"], 1):.0f} tokens per successful task')
        
        if result['successful_tasks'] == result['total_tasks']:
            print('\n🎉 ALL TESTS PASSED - SYSTEM FULLY OPERATIONAL!')
            return 0
        else:
            print(f'\n⚠️  {result["total_tasks"] - result["successful_tasks"]} tests failed')
            return 1
            
    except Exception as e:
        print(f'\n💥 System test failed: {e}')
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)