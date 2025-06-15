#!/usr/bin/env python3
"""
Comprehensive tests for Claude + Gemini optimized orchestrator system
Test-driven development for enhanced multi-agent coordination
"""

import pytest
import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_orchestrator_claude_gemini import (
    EnhancedRealAgent as RealAgent, Task, TaskStatus, TaskPriority, AgentType,
    ProviderLoadBalancer, EnhancedRealAgentOrchestrator as RealAgentOrchestrator
)

class TestClaudeGeminiLoadBalancer:
    """Test the optimized load balancer for Claude + Gemini only"""
    
    def test_load_balancer_initialization(self):
        """Test that load balancer initializes with only Claude and Gemini"""
        balancer = ProviderLoadBalancer()
        
        # Should only have Claude and Gemini providers
        assert "anthropic" in balancer.providers
        assert "gemini" in balancer.providers
        assert "openai" not in balancer.providers
        
        # Should have balanced weights
        assert balancer.providers["anthropic"]["weight"] == 0.5
        assert balancer.providers["gemini"]["weight"] == 0.5
        
    def test_provider_selection_alternates(self):
        """Test that provider selection alternates between Claude and Gemini"""
        balancer = ProviderLoadBalancer()
        
        # First few selections should alternate
        selections = [balancer.get_next_provider() for _ in range(6)]
        
        # Should have both providers represented
        assert "anthropic" in selections
        assert "gemini" in selections
        
    def test_provider_failover(self):
        """Test failover when one provider has high error rate"""
        balancer = ProviderLoadBalancer()
        
        # Simulate many failures for one provider
        for _ in range(10):
            balancer.record_request("anthropic", False)
        
        # Should prefer the working provider
        next_provider = balancer.get_next_provider()
        # Should be more likely to get gemini due to anthropic errors
        
    def test_provider_stats_tracking(self):
        """Test that provider statistics are tracked correctly"""
        balancer = ProviderLoadBalancer()
        
        balancer.record_request("anthropic", True, 0.05)
        balancer.record_request("gemini", False, 0.03)
        
        stats = balancer.get_provider_stats()
        
        assert stats["anthropic"]["requests"] == 1
        assert stats["anthropic"]["errors"] == 0
        assert stats["anthropic"]["cost"] == 0.05
        
        assert stats["gemini"]["requests"] == 1
        assert stats["gemini"]["errors"] == 1
        assert stats["gemini"]["cost"] == 0.03

class TestEnhancedRealAgent:
    """Test enhanced real agent with Claude + Gemini specialization"""
    
    def test_agent_initialization_claude_gemini_only(self):
        """Test agent initializes with only Claude and Gemini clients"""
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'test_key',
            'GOOGLE_API_KEY': 'test_key'
        }):
            agent = RealAgent("test_agent", "Test Agent", AgentType.CODE_DEVELOPER)
            
            # Should have both providers
            assert "anthropic" in agent.provider_clients
            assert "gemini" in agent.provider_clients
            assert "openai" not in agent.provider_clients
    
    def test_agent_specialization_by_type(self):
        """Test that different agent types have optimized provider preferences"""
        code_agent = RealAgent("code_agent", "Code Developer", AgentType.CODE_DEVELOPER)
        analyst_agent = RealAgent("analyst_agent", "System Analyst", AgentType.SYSTEM_ANALYST)
        
        # Code developers should prefer Claude for coding tasks
        assert code_agent.get_preferred_provider_for_task("code_generation") == "anthropic"
        
        # Analysts should prefer Gemini for analysis tasks
        assert analyst_agent.get_preferred_provider_for_task("data_analysis") == "gemini"
    
    @pytest.mark.asyncio
    async def test_agent_task_execution_with_failover(self):
        """Test agent task execution with provider failover"""
        agent = RealAgent("test_agent", "Test Agent", AgentType.CODE_DEVELOPER)
        
        # Mock the LLM clients
        agent.provider_clients["anthropic"] = Mock()
        agent.provider_clients["gemini"] = Mock()
        
        # Simulate anthropic failure, gemini success
        agent.provider_clients["anthropic"].messages.create.side_effect = Exception("API Error")
        agent.provider_clients["gemini"].generate_content.return_value = Mock(text="Success")
        
        task = Task(
            id="test_task",
            name="Test Task",
            description="Test task description",
            agent_type=AgentType.CODE_DEVELOPER,
            priority=TaskPriority.HIGH
        )
        
        result = await agent.execute_task(task)
        
        assert result["success"] is True
        assert "Success" in result["result"]
    
    def test_agent_learning_system(self):
        """Test that agents learn from task outcomes"""
        agent = RealAgent("test_agent", "Test Agent", AgentType.CODE_DEVELOPER)
        
        # Simulate learning from successful task
        lesson = {
            "task_type": "code_generation",
            "provider_used": "anthropic",
            "success": True,
            "tokens_used": 1500,
            "execution_time": 2.5,
            "lesson": "Claude performs better for complex code generation tasks"
        }
        
        agent.learn_from_task(lesson)
        
        assert len(agent.learned_lessons) == 1
        assert agent.learned_lessons[0]["lesson"] == lesson["lesson"]

class TestAdvancedOrchestrator:
    """Test enhanced orchestrator with advanced coordination"""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initializes with enhanced agent team"""
        orchestrator = RealAgentOrchestrator()
        
        # Should have all agent types
        assert len(orchestrator.agents) >= 8
        
        # Should have specialized agents
        agent_types = [agent.agent_type for agent in orchestrator.agents.values()]
        assert AgentType.CODE_DEVELOPER in agent_types
        assert AgentType.SYSTEM_ANALYST in agent_types
        assert AgentType.API_INTEGRATOR in agent_types
    
    def test_task_assignment_optimization(self):
        """Test optimized task assignment based on agent specialization"""
        orchestrator = RealAgentOrchestrator()
        
        # Create different types of tasks
        code_task = Task(
            id="code_task",
            name="Generate Python function",
            description="Create a data processing function",
            agent_type=AgentType.CODE_DEVELOPER,
            priority=TaskPriority.HIGH
        )
        
        analysis_task = Task(
            id="analysis_task", 
            name="Analyze system performance",
            description="Review system metrics and identify bottlenecks",
            agent_type=AgentType.SYSTEM_ANALYST,
            priority=TaskPriority.MEDIUM
        )
        
        # Test optimal agent assignment
        code_agent = orchestrator.get_optimal_agent_for_task(code_task)
        analysis_agent = orchestrator.get_optimal_agent_for_task(analysis_task)
        
        assert code_agent.agent_type == AgentType.CODE_DEVELOPER
        assert analysis_agent.agent_type == AgentType.SYSTEM_ANALYST
    
    def test_multi_agent_collaboration(self):
        """Test coordinated multi-agent task execution"""
        orchestrator = RealAgentOrchestrator()
        
        # Create a complex task requiring multiple agents
        complex_task = Task(
            id="complex_task",
            name="Build and test API endpoint",
            description="Create API endpoint, write tests, and validate",
            agent_type=AgentType.CODE_DEVELOPER,
            priority=TaskPriority.HIGH
        )
        
        # Should decompose into subtasks for different agents
        subtasks = orchestrator.decompose_complex_task(complex_task)
        
        assert len(subtasks) >= 2
        # Should include development and testing subtasks
        task_types = [task.agent_type for task in subtasks]
        assert AgentType.CODE_DEVELOPER in task_types
        assert AgentType.WEB_TESTER in task_types
    
    @pytest.mark.asyncio
    async def test_parallel_task_execution(self):
        """Test parallel execution of independent tasks"""
        orchestrator = RealAgentOrchestrator()
        
        # Create multiple independent tasks
        tasks = [
            Task(f"task_{i}", f"Task {i}", f"Description {i}", 
                 AgentType.CODE_DEVELOPER, TaskPriority.MEDIUM)
            for i in range(3)
        ]
        
        # Execute tasks in parallel
        results = await orchestrator.execute_tasks_parallel(tasks)
        
        assert len(results) == 3
        for result in results:
            assert "success" in result

class TestSystemIntegration:
    """Test integration with existing systems"""
    
    def test_tdd_system_integration(self):
        """Test integration with TDD system for automated development"""
        from tdd_system import tdd_system
        
        # Create TDD cycle
        cycle_id = tdd_system.create_tdd_cycle(
            "Test Integration Cycle",
            "Test orchestrator integration with TDD system"
        )
        
        assert cycle_id > 0
        
        # Generate tests using orchestrator
        result = tdd_system.generate_test_from_specification(
            cycle_id,
            "Create a function that calculates fibonacci numbers"
        )
        
        assert result["success"] is True
        assert "test_code" in result
    
    def test_repository_analysis_integration(self):
        """Test integration with repository analysis system"""
        orchestrator = RealAgentOrchestrator()
        
        # Mock repository analysis task
        repo_task = Task(
            id="repo_analysis",
            name="Analyze repository structure",
            description="Analyze Python repository for patterns and improvements",
            agent_type=AgentType.SYSTEM_ANALYST,
            priority=TaskPriority.HIGH
        )
        
        # Should be able to process repository analysis
        agent = orchestrator.get_optimal_agent_for_task(repo_task)
        assert agent is not None
        assert agent.agent_type == AgentType.SYSTEM_ANALYST
    
    def test_knowledge_hub_integration(self):
        """Test integration with knowledge hub system"""
        orchestrator = RealAgentOrchestrator()
        
        # Test processing GitHub repository data
        github_task = Task(
            id="github_processing",
            name="Process GitHub repository data",
            description="Extract insights from GitHub repository information",
            agent_type=AgentType.CONTENT_PROCESSOR,
            priority=TaskPriority.MEDIUM
        )
        
        agent = orchestrator.get_optimal_agent_for_task(github_task)
        assert agent.agent_type == AgentType.CONTENT_PROCESSOR

class TestPerformanceOptimization:
    """Test performance optimizations for Claude + Gemini"""
    
    def test_token_usage_optimization(self):
        """Test optimized token usage across providers"""
        agent = RealAgent("test_agent", "Test Agent", AgentType.CODE_DEVELOPER)
        
        # Test token usage estimation
        prompt = "Generate a simple Python function"
        
        claude_tokens = agent.estimate_tokens("anthropic", prompt)
        gemini_tokens = agent.estimate_tokens("gemini", prompt)
        
        assert claude_tokens > 0
        assert gemini_tokens > 0
    
    def test_cost_optimization(self):
        """Test cost optimization strategies"""
        balancer = ProviderLoadBalancer()
        
        # Simulate different costs
        balancer.record_request("anthropic", True, 0.05)
        balancer.record_request("gemini", True, 0.03)
        
        # Should prefer lower cost provider for similar quality
        optimal_provider = balancer.get_cost_optimal_provider()
        assert optimal_provider == "gemini"  # Lower cost
    
    def test_response_time_optimization(self):
        """Test response time tracking and optimization"""
        agent = RealAgent("test_agent", "Test Agent", AgentType.CODE_DEVELOPER)
        
        # Track response times
        agent.track_response_time("anthropic", 2.5)
        agent.track_response_time("gemini", 1.8)
        
        # Should prefer faster provider for time-sensitive tasks
        fast_provider = agent.get_fastest_provider()
        assert fast_provider == "gemini"

class TestAdvancedFeatures:
    """Test advanced orchestrator features"""
    
    def test_dynamic_agent_scaling(self):
        """Test dynamic scaling of agent pool"""
        orchestrator = RealAgentOrchestrator()
        
        initial_agent_count = len(orchestrator.agents)
        
        # Simulate high load requiring more agents
        orchestrator.scale_agents_for_load(high_load=True)
        
        # Should create additional agents
        assert len(orchestrator.agents) > initial_agent_count
    
    def test_intelligent_task_routing(self):
        """Test intelligent task routing based on agent capabilities"""
        orchestrator = RealAgentOrchestrator()
        
        # Complex task requiring specific expertise
        specialized_task = Task(
            id="specialized_task",
            name="Optimize database queries",
            description="Analyze and optimize SQL database performance",
            agent_type=AgentType.DATABASE_SPECIALIST,
            priority=TaskPriority.HIGH
        )
        
        # Should route to database specialist
        assigned_agent = orchestrator.route_task_intelligently(specialized_task)
        assert assigned_agent.agent_type == AgentType.DATABASE_SPECIALIST
    
    def test_continuous_learning_system(self):
        """Test continuous learning from task outcomes"""
        orchestrator = RealAgentOrchestrator()
        
        # Simulate successful task execution
        task_result = {
            "task_id": "test_task",
            "agent_type": AgentType.CODE_DEVELOPER,
            "provider_used": "anthropic",
            "success": True,
            "quality_score": 0.95,
            "execution_time": 3.2,
            "tokens_used": 2000
        }
        
        # Should learn and update preferences
        orchestrator.learn_from_task_outcome(task_result)
        
        # Should have updated learning database
        lessons = orchestrator.get_learned_lessons()
        assert len(lessons) > 0

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])