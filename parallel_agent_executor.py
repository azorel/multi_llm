#!/usr/bin/env python3
"""
Parallel Agent Executor for TDD Refactoring
Executes multiple agent tasks simultaneously for faster development
"""

from real_agent_orchestrator import real_orchestrator, AgentType
import asyncio
import concurrent.futures
import time
import sys

async def execute_parallel_agents():
    """Execute multiple agents in parallel for TDD refactoring"""
    
    start_time = time.time()
    print('🚀 Starting parallel agent execution for TDD refactoring...')

    # Get all agents
    agents = list(real_orchestrator.agents.values())
    print(f'Available agents: {len(agents)}')

    # Get recent tasks from queue 
    tasks = real_orchestrator.task_queue[-5:]  # Last 5 tasks we added
    print(f'Tasks to execute: {len(tasks)}')

    if not tasks:
        print('❌ No tasks found in queue')
        return

    # Create agent-task pairs
    agent_task_pairs = []
    for task in tasks:
        # Find matching agent type
        suitable_agent = None
        for agent in agents:
            if agent.agent_type == task.agent_type:
                suitable_agent = agent
                break
        
        if suitable_agent:
            agent_task_pairs.append((suitable_agent, task))
            print(f'📋 {task.name} → {suitable_agent.name}')
        else:
            print(f'⚠️  No suitable agent found for {task.name} ({task.agent_type})')

    if not agent_task_pairs:
        print('❌ No suitable agent-task pairs found')
        return

    print(f'\n🔥 Executing {len(agent_task_pairs)} tasks in parallel...')

    # Execute all tasks concurrently
    async def execute_agent_task(agent, task):
        """Execute a single agent task"""
        try:
            print(f'🔄 Starting: {task.name}')
            result = await agent.execute_task(task)
            print(f'✅ Completed: {task.name}')
            return {
                'task_name': task.name,
                'task_id': task.id,
                'agent_name': agent.name,
                'success': result.get('success', False),
                'result': result.get('result', '')[:300] + '...' if len(str(result.get('result', ''))) > 300 else result.get('result', ''),
                'tokens_used': result.get('tokens_used', 0),
                'cost': result.get('cost', 0.0),
                'execution_time': result.get('execution_time', 0)
            }
        except Exception as e:
            print(f'❌ Failed: {task.name} - {str(e)}')
            return {
                'task_name': task.name,
                'task_id': task.id,
                'agent_name': agent.name,
                'success': False,
                'error': str(e)
            }

    # Run all tasks concurrently
    tasks_to_run = [execute_agent_task(agent, task) for agent, task in agent_task_pairs]
    results = await asyncio.gather(*tasks_to_run, return_exceptions=True)

    execution_time = time.time() - start_time
    print(f'\n⚡ Parallel execution completed in {execution_time:.2f} seconds')

    # Process results
    successful_results = []
    failed_results = []
    
    for result in results:
        if isinstance(result, Exception):
            failed_results.append({'error': str(result), 'success': False})
        elif result.get('success'):
            successful_results.append(result)
        else:
            failed_results.append(result)

    print(f'📊 Results: {len(successful_results)} success, {len(failed_results)} failed')
    
    # Show detailed results
    total_tokens = 0
    total_cost = 0.0
    
    print('\n🎯 SUCCESSFUL TASKS:')
    for result in successful_results:
        total_tokens += result.get('tokens_used', 0)
        total_cost += result.get('cost', 0.0)
        print(f'✅ {result["task_name"]} ({result["agent_name"]})')
        print(f'   Tokens: {result.get("tokens_used", 0)}, Cost: ${result.get("cost", 0):.4f}')
        if result.get('result'):
            print(f'   Result: {result["result"][:150]}...')
        print()

    if failed_results:
        print('❌ FAILED TASKS:')
        for result in failed_results:
            print(f'❌ {result.get("task_name", "Unknown")} - {result.get("error", "Unknown error")}')

    print(f'\n💰 Total Usage: {total_tokens} tokens, ${total_cost:.4f}')
    
    return {
        'successful': len(successful_results),
        'failed': len(failed_results),
        'total_tokens': total_tokens,
        'total_cost': total_cost,
        'execution_time': execution_time,
        'results': successful_results
    }

if __name__ == "__main__":
    try:
        # Run the parallel execution
        final_result = asyncio.run(execute_parallel_agents())
        
        if final_result['successful'] > 0:
            print(f'\n🎉 SUCCESS: {final_result["successful"]} tasks completed successfully!')
            print(f'⚡ Execution time: {final_result["execution_time"]:.2f}s')
            print(f'💎 Ready for next phase of TDD implementation')
        else:
            print('\n💥 No tasks completed successfully')
            sys.exit(1)
            
    except KeyboardInterrupt:
        print('\n🛑 Execution interrupted by user')
        sys.exit(1)
    except Exception as e:
        print(f'\n💥 Execution failed: {e}')
        sys.exit(1)