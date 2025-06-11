#!/usr/bin/env python3
"""
Start the real multi-agent system with actual tasks
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from real_agent_orchestrator import real_orchestrator, AgentType, TaskPriority

async def create_real_tasks():
    """Create actual working tasks for the agents"""
    print("🚀 Starting Real Multi-Agent System")
    
    # Task 1: Process YouTube channels from the database
    task1_id = real_orchestrator.add_task(
        name="Process Marked YouTube Channels",
        description="Check the lifeos_local.db database for youtube_channels where marked=1 and process them using the YouTube processor",
        agent_type=AgentType.CODE_DEVELOPER,
        priority=TaskPriority.HIGH
    )
    print(f"✅ Created YouTube processing task: {task1_id}")
    
    # Task 2: Monitor system health
    task2_id = real_orchestrator.add_task(
        name="System Health Monitor",
        description="Monitor the web server endpoints and database connections for errors",
        agent_type=AgentType.SYSTEM_ANALYST,
        priority=TaskPriority.MEDIUM
    )
    print(f"✅ Created system monitoring task: {task2_id}")
    
    # Task 3: Database optimization
    task3_id = real_orchestrator.add_task(
        name="Database Schema Analysis",
        description="Analyze the lifeos_local.db schema and recommend optimizations for the knowledge_hub table",
        agent_type=AgentType.DATABASE_SPECIALIST,
        priority=TaskPriority.MEDIUM
    )
    print(f"✅ Created database analysis task: {task3_id}")
    
    # Task 4: GitHub integration
    task4_id = real_orchestrator.add_task(
        name="GitHub Repository Processor",
        description="Process the github_users table and fetch repository data for users marked for processing",
        agent_type=AgentType.API_INTEGRATOR,
        priority=TaskPriority.HIGH
    )
    print(f"✅ Created GitHub integration task: {task4_id}")
    
    # Task 5: Template error checking
    task5_id = real_orchestrator.add_task(
        name="Template Error Scan",
        description="Scan all HTML templates in the templates/ directory for potential Jinja2 errors and fix them",
        agent_type=AgentType.TEMPLATE_FIXER,
        priority=TaskPriority.LOW
    )
    print(f"✅ Created template scanning task: {task5_id}")
    
    print(f"\n📊 Total tasks created: {len(real_orchestrator.task_queue)}")
    print(f"🤖 Total agents available: {len(real_orchestrator.agents)}")
    
    # Process some tasks to show real activity
    print("\n🔄 Processing tasks...")
    
    # Process the system analysis task first
    analyst_task = next(t for t in real_orchestrator.task_queue if t.id == task2_id)
    analyst_agent = next(a for a in real_orchestrator.agents.values() if a.agent_type == AgentType.SYSTEM_ANALYST)
    
    try:
        print(f"🔍 Executing: {analyst_task.name}")
        result = await analyst_agent.execute_task(analyst_task)
        print(f"✅ Task result: {result['success']}")
        if result['success']:
            print(f"📝 Output: {result['result'][:100]}...")
    except Exception as e:
        print(f"❌ Task failed: {e}")
    
    print(f"\n🎯 Real orchestrator is now running with {len(real_orchestrator.task_queue)} tasks")
    print("🌐 Check http://localhost:5000/active-agents to see real data")
    
    return True

if __name__ == "__main__":
    print("🤖 REAL MULTI-AGENT SYSTEM STARTUP")
    print("=" * 50)
    
    try:
        # Run the task creation
        asyncio.run(create_real_tasks())
        
        print("\n✅ System started successfully!")
        print("💡 The orchestrator is now populated with real tasks and agent data")
        print("🔗 Visit: http://localhost:5000/active-agents")
        
    except Exception as e:
        print(f"❌ Failed to start system: {e}")
        import traceback
        traceback.print_exc()