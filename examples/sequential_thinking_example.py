#!/usr/bin/env python3
"""
Sequential Thinking Example
===========================

# DEMO CODE REMOVED: Example demonstrating how to use the sequential thinking capabilities
in the autonomous multi-LLM agent system.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger
from src.integrations.sequential_thinking_client import SequentialThinkingClient
from src.integrations.manager import IntegrationManager


async def basic_thinking_example():
    """Basic example of sequential thinking."""
    logger.info("=== Basic Sequential Thinking Example ===")
    
    # Create a sequential thinking client
    client = SequentialThinkingClient()
    
    # Test connection
    if not await client.test_connection():
        logger.error("Cannot connect to Sequential Thinking MCP server")
        return False
    
    # Start a thinking session
    problem = "How can we implement rate limiting in a distributed API gateway?"
    session_id = await client.start_thinking_session(problem)
    
    logger.info(f"Started thinking session: {session_id}")
    logger.info(f"Problem: {problem}")
    
    # Add structured thought steps
    thoughts = [
        "First, I need to understand the requirements: rate limiting scope, algorithms, and storage.",
        "I should consider different rate limiting algorithms: token bucket, sliding window, fixed window.",
        "For distributed systems, I need to think about shared state management - Redis or database.",
        "Implementation considerations: performance, accuracy vs. efficiency trade-offs.",
        "Final architecture: Redis-backed sliding window with local caching for performance."
    ]
    
    for i, thought in enumerate(thoughts, 1):
        is_last = i == len(thoughts)
        await client.add_thought_step(
            session_id=session_id,
            thought=thought,
            thought_number=i,
            total_thoughts=len(thoughts),
            next_thought_needed=not is_last
        )
        logger.info(f"Thought {i}: {thought}")
    
    # Complete the session
    final_solution = """
    Distributed Rate Limiting Solution:
    1. Use Redis as shared state store with sliding window counters
    2. Implement local caching to reduce Redis calls
    3. Use consistent hashing for Redis sharding
    4. Add circuit breakers for Redis failures
    5. Monitor and alert on rate limiting metrics
    """
    
    completed_session = await client.complete_thinking_session(session_id, final_solution.strip())
    
    logger.success("✓ Basic thinking session completed")
    logger.info(f"Final solution:\n{completed_session.final_solution}")
    
    return True


async def advanced_thinking_with_revisions():
    """Advanced example with thought revisions and branching."""
    logger.info("\n=== Advanced Sequential Thinking with Revisions ===")
    
    client = SequentialThinkingClient()
    
    # Complex software architecture problem
    problem = "Design a real-time collaborative document editing system like Google Docs"
    session_id = await client.start_thinking_session(problem)
    
    logger.info(f"Problem: {problem}")
    
    # Initial thoughts
    await client.add_thought_step(
        session_id=session_id,
        thought="I need to handle real-time synchronization, conflict resolution, and offline support.",
        thought_number=1,
        total_thoughts=5,
        next_thought_needed=True
    )
    
    await client.add_thought_step(
        session_id=session_id,
        thought="For real-time sync, I could use WebSockets with operational transformation (OT).",
        thought_number=2,
        total_thoughts=5,
        next_thought_needed=True
    )
    
    # Revision - better approach
    await client.revise_thought(
        session_id=session_id,
        original_thought_number=2,
        revised_thought="Actually, Conflict-free Replicated Data Types (CRDTs) might be better than OT for this use case.",
        new_total_thoughts=6
    )
    
    # Create a branch to explore alternative
    await client.create_thought_branch(
        session_id=session_id,
        branch_from_thought_number=2,
        branch_thought="Alternative approach: Event sourcing with CQRS for document state management.",
        branch_id="event_sourcing_branch"
    )
    
    # Continue main thought line
    await client.add_thought_step(
        session_id=session_id,
        thought="For the data model, I'll use a tree structure with CRDT nodes for each document element.",
        thought_number=4,
        total_thoughts=6,
        next_thought_needed=True
    )
    
    await client.add_thought_step(
        session_id=session_id,
        thought="Architecture: WebSocket gateway, CRDT service, persistence layer, and conflict resolution engine.",
        thought_number=5,
        total_thoughts=6,
        next_thought_needed=True
    )
    
    await client.add_thought_step(
        session_id=session_id,
        thought="For offline support, implement local CRDT state with sync queues for reconnection.",
        thought_number=6,
        total_thoughts=6,
        next_thought_needed=False
    )
    
    # Get session summary to see the thinking process
    summary = await client.get_session_summary(session_id)
    logger.info(f"Thinking process summary: {summary}")
    
    # Complete with final solution
    final_solution = """
    Real-time Collaborative Document Editor Architecture:
    
    Core Components:
    1. CRDT-based document model for conflict-free merging
    2. WebSocket gateway for real-time communication
    3. Document state service with efficient delta synchronization
    4. Offline-first client with local CRDT state
    5. Persistence layer with event sourcing for audit trails
    
    Key Features:
    - Automatic conflict resolution using CRDT properties
    - Efficient network usage with delta-only synchronization
    - Offline editing with seamless reconnection
    - Real-time cursor and selection tracking
    - Version history and branching support
    """
    
    completed_session = await client.complete_thinking_session(session_id, final_solution.strip())
    
    logger.success("✓ Advanced thinking session with revisions completed")
    logger.info(f"Final solution:\n{completed_session.final_solution}")
    
    return True


async def integration_manager_example():
    """Example using the integration manager for sequential thinking."""
    logger.info("\n=== Integration Manager Sequential Thinking Example ===")
    
    # Configure integration manager
    config = {
        "integrations": {
            "sequential_thinking": {
                "enabled": True,
                "priority": 9,
                "timeout": 60.0,
                "max_retries": 2,
                "retry_policy": "linear_backoff",
                "health_check_interval": 600.0,
                "circuit_breaker_threshold": 3,
                "circuit_breaker_timeout": 180.0,
                "authentication": {},
                "config": {
                    "server_path": None,
                    "max_concurrent_sessions": 5,
                    "session_timeout_minutes": 30,
                    "auto_cleanup_completed_sessions": True
                }
            }
        }
    }
    
    # Create and start integration manager
    manager = IntegrationManager(config)
    await manager.start()
    
    try:
        # Use integration manager for step-by-step problem solving
        problem = "Optimize database queries in a high-traffic e-commerce application"
        
        # Start thinking session through integration manager
        result = await manager.solve_problem_step_by_step(
            problem_description=problem,
            initial_thought_estimate=4,
            max_thoughts=10
        )
        
        if result.success:
            session_data = result.result_data
            logger.success("✓ Problem solved through integration manager")
            logger.info(f"Session completed with solution: {session_data.final_solution}")
        else:
            logger.error(f"✗ Problem solving failed: {result.error_message}")
            return False
        
        # Check integration health
        health = manager.get_integration_status('sequential_thinking')
        if health:
            logger.info(f"Sequential thinking integration health: {health.status.value}")
            logger.info(f"Success rate: {health.success_rate:.2%}")
            logger.info(f"Average response time: {health.average_response_time:.2f}s")
        
        return True
        
    finally:
        await manager.stop()


async def main():
    """Run sequential thinking examples."""
    logger.info("Sequential Thinking Integration Examples")
    logger.info("=" * 50)
    
    examples = [
        ("Basic Sequential Thinking", basic_thinking_example),
        ("Advanced Thinking with Revisions", advanced_thinking_with_revisions),
        ("Integration Manager Usage", integration_manager_example)
    ]
    
    results = []
    
    for name, example_func in examples:
        try:
            logger.info(f"\nRunning: {name}")
            success = await example_func()
            results.append((name, success))
            
            if success:
                logger.success(f"✓ {name} completed successfully")
            else:
                logger.error(f"✗ {name} failed")
                
        except Exception as e:
            logger.error(f"✗ {name} failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("EXAMPLES SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        logger.info(f"{name}: {status}")
    
    logger.info(f"\nResults: {passed}/{total} examples completed successfully")
    
    if passed == total:
        logger.success("🎉 All sequential thinking examples completed successfully!")
    else:
        logger.warning(f"⚠️  {total - passed} examples had issues")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Examples interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Example execution failed: {e}")
        sys.exit(1)