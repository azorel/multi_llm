"""
Base agent implementation for the autonomous multi-LLM agent system.

This module provides the abstract base class and core functionality that all
agents must implement, including the 1-3-1 workflow pattern, rate limiting,
token counting, and error handling.
"""

import asyncio
import time
import json
import re
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque

from pydantic import BaseModel, ValidationError
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..models.schemas import (
    AgentType, TaskType, ActionType, Priority, ExecutionStatus,
    VoteType, Proposal, Vote, Action, ExecutionResult, ValidationResult,
    TaskContext, AgentConfig, PlanStep, ImprovementPlan, PerformanceMetrics
)


class RateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire a rate limit token."""
        async with self._lock:
            now = time.time()
            
            # Remove old requests outside the window
            while self.requests and now - self.requests[0] > self.window_seconds:
                self.requests.popleft()
            
            # Check if we can make a request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            
            return False
    
    async def wait_for_availability(self) -> None:
        """Wait until a rate limit token becomes available."""
        while not await self.acquire():
            await asyncio.sleep(1)


class TokenCounter:
    """Utility class for counting tokens in text."""
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self._encoding_cache = {}
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using approximation."""
        if not text:
            return 0
        
        # Simple approximation: ~4 characters per token for most models
        # This is rough but sufficient for rate limiting
        return max(1, len(text) // 4)
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, 
                     cost_per_input: float, cost_per_output: float) -> float:
        """Estimate the cost of a request."""
        return (input_tokens * cost_per_input) + (output_tokens * cost_per_output)


class AgentCapabilities:
    """Manages agent capabilities and specializations."""
    
    def __init__(self, capabilities: List[str], specializations: List[TaskType]):
        self.capabilities = set(capabilities)
        self.specializations = set(specializations)
        self.performance_history = defaultdict(list)
    
    def can_handle_task(self, task_type: TaskType) -> bool:
        """Check if agent can handle a specific task type."""
        return (task_type in self.specializations or 
                len(self.specializations) == 0)  # General purpose if no specializations
    
    def get_proficiency_score(self, task_type: TaskType) -> float:
        """Get proficiency score for a task type based on history."""
        if task_type not in self.performance_history:
            return 0.5  # Default proficiency
        
        recent_scores = self.performance_history[task_type][-10:]  # Last 10 attempts
        if not recent_scores:
            return 0.5
        
        return sum(recent_scores) / len(recent_scores)
    
    def update_performance(self, task_type: TaskType, success_score: float):
        """Update performance history for a task type."""
        self.performance_history[task_type].append(success_score)
        
        # Keep only last 50 records per task type
        if len(self.performance_history[task_type]) > 50:
            self.performance_history[task_type] = self.performance_history[task_type][-50:]


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the autonomous multi-LLM system.
    
    Implements the 1-3-1 workflow pattern:
    1. Single proposal generation phase
    3. Three-agent voting phase  
    1. Single execution phase with validation
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize the base agent with configuration."""
        self.config = config
        self.agent_id = config.agent_id
        self.agent_type = config.agent_type
        self.model = config.model
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            max_requests=config.rate_limit,
            window_seconds=60
        )
        
        # Token counting
        self.token_counter = TokenCounter(model=config.model)
        
        # Capabilities management
        self.capabilities = AgentCapabilities(
            capabilities=config.capabilities,
            specializations=config.specializations
        )
        
        # Performance tracking
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens_used': 0,
            'total_cost': 0.0,
            'average_response_time': 0.0,
            'last_request_time': None
        }
        
        # Error tracking
        self.error_history = deque(maxlen=100)
        self.consecutive_failures = 0
        self.last_failure_time = None
        
        # Status
        self.enabled = config.enabled
        self.busy = False
        self.current_task = None
        self.health_score = 1.0
        
        logger.info(f"Initialized {self.agent_type.value} agent: {self.agent_id}")
    
    @property
    def is_healthy(self) -> bool:
        """Check if agent is healthy and available."""
        return (self.enabled and 
                not self.busy and 
                self.health_score > 0.5 and
                self.consecutive_failures < 5)
    
    @property
    def load_factor(self) -> float:
        """Get current load factor (0.0 = idle, 1.0 = fully loaded)."""
        if self.busy:
            return 1.0
        
        # Factor in recent error rate
        error_factor = min(self.consecutive_failures / 10.0, 0.5)
        return error_factor
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    async def generate_proposal(self, task_context: TaskContext) -> Proposal:
        """
        Generate a proposal for how to handle the given task.
        
        This is the first phase of the 1-3-1 workflow.
        """
        pass
    
    @abstractmethod
    async def vote_on_proposal(self, proposal: Proposal, task_context: TaskContext) -> Vote:
        """
        Vote on a proposal from another agent.
        
        This is part of the second phase (voting) of the 1-3-1 workflow.
        """
        pass
    
    @abstractmethod
    async def execute_action(self, action: Action, task_context: TaskContext) -> ExecutionResult:
        """
        Execute a specific action.
        
        This is the third phase of the 1-3-1 workflow.
        """
        pass
    
    @abstractmethod
    async def validate_result(self, result: ExecutionResult, task_context: TaskContext) -> ValidationResult:
        """
        Validate the result of an execution.
        
        This is the validation part of the 1-3-1 workflow.
        """
        pass
    
    @abstractmethod
    async def reflect_on_failure(self, error: Exception, task_context: TaskContext) -> ImprovementPlan:
        """
        Analyze a failure and generate an improvement plan.
        
        This is called when the 1-3-1 workflow fails.
        """
        pass
    
    # Concrete methods with default implementations
    
    async def can_handle_task(self, task_context: TaskContext) -> bool:
        """Check if this agent can handle the given task."""
        if not self.is_healthy:
            return False
        
        return self.capabilities.can_handle_task(task_context.task_type)
    
    async def estimate_task_cost(self, task_context: TaskContext) -> Tuple[float, int]:
        """Estimate the cost and time for handling a task."""
        # Base estimation - subclasses should override for more accuracy
        estimated_tokens = self.token_counter.count_tokens(
            task_context.description + str(task_context.input_data)
        )
        
        # Assume some output tokens
        output_tokens = estimated_tokens * 2
        total_tokens = estimated_tokens + output_tokens
        
        estimated_cost = self.token_counter.estimate_cost(
            estimated_tokens, output_tokens,
            self.config.cost_per_token, self.config.cost_per_token
        )
        
        return estimated_cost, total_tokens
    
    async def get_proficiency_score(self, task_type: TaskType) -> float:
        """Get proficiency score for a specific task type."""
        return self.capabilities.get_proficiency_score(task_type)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    async def _make_api_call(self, prompt: str, **kwargs) -> str:
        """
        Make an API call with rate limiting, retries, and error handling.
        
        This is a template method that subclasses should override.
        """
        # Wait for rate limit availability
        await self.rate_limiter.wait_for_availability()
        
        start_time = time.time()
        
        try:
            self.busy = True
            self.current_task = prompt[:100] + "..." if len(prompt) > 100 else prompt
            
            # Count input tokens
            input_tokens = self.token_counter.count_tokens(prompt)
            
            # This should be implemented by subclasses
            response = await self._actual_api_call(prompt, **kwargs)
            
            # Count output tokens
            output_tokens = self.token_counter.count_tokens(response)
            
            # Update metrics
            execution_time = time.time() - start_time
            cost = self.token_counter.estimate_cost(
                input_tokens, output_tokens,
                self.config.cost_per_token, self.config.cost_per_token
            )
            
            await self._update_metrics(True, execution_time, input_tokens + output_tokens, cost)
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            await self._update_metrics(False, execution_time, 0, 0.0)
            
            self.error_history.append({
                'timestamp': datetime.utcnow(),
                'error': str(e),
                'error_type': type(e).__name__,
                'prompt_hash': hashlib.md5(prompt.encode()).hexdigest()[:8]
            })
            
            raise
        
        finally:
            self.busy = False
            self.current_task = None
    
    @abstractmethod
    async def _actual_api_call(self, prompt: str, **kwargs) -> str:
        """Actual API call implementation - must be implemented by subclasses."""
        pass
    
    async def _update_metrics(self, success: bool, execution_time: float, 
                            tokens_used: int, cost: float):
        """Update agent performance metrics."""
        self.metrics['total_requests'] += 1
        self.metrics['total_tokens_used'] += tokens_used
        self.metrics['total_cost'] += cost
        self.metrics['last_request_time'] = datetime.utcnow()
        
        if success:
            self.metrics['successful_requests'] += 1
            self.consecutive_failures = 0
            
            # Update health score (improve slowly)
            self.health_score = min(1.0, self.health_score + 0.01)
        else:
            self.metrics['failed_requests'] += 1
            self.consecutive_failures += 1
            self.last_failure_time = datetime.utcnow()
            
            # Decrease health score
            self.health_score = max(0.0, self.health_score - 0.05)
        
        # Update average response time
        total_requests = self.metrics['total_requests']
        current_avg = self.metrics['average_response_time']
        self.metrics['average_response_time'] = (
            (current_avg * (total_requests - 1) + execution_time) / total_requests
        )
    
    def update_task_performance(self, task_type: TaskType, success_score: float):
        """Update performance tracking for a specific task type."""
        self.capabilities.update_performance(task_type, success_score)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of agent status and metrics."""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'model': self.model,
            'enabled': self.enabled,
            'busy': self.busy,
            'is_healthy': self.is_healthy,
            'health_score': self.health_score,
            'load_factor': self.load_factor,
            'consecutive_failures': self.consecutive_failures,
            'metrics': self.metrics.copy(),
            'capabilities': list(self.capabilities.capabilities),
            'specializations': [spec.value for spec in self.capabilities.specializations],
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'error_count_recent': len([
                e for e in self.error_history 
                if (datetime.utcnow() - e['timestamp']).total_seconds() < 3600
            ])
        }
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get structured performance metrics."""
        return PerformanceMetrics(
            component=f"agent_{self.agent_id}",
            metric_name="performance_summary",
            value=self.health_score,
            unit="score",
            tags={
                'agent_type': self.agent_type.value,
                'model': self.model
            },
            context={
                'total_requests': self.metrics['total_requests'],
                'success_rate': (self.metrics['successful_requests'] / 
                               max(1, self.metrics['total_requests'])),
                'average_response_time': self.metrics['average_response_time'],
                'total_cost': self.metrics['total_cost'],
                'tokens_used': self.metrics['total_tokens_used']
            },
            threshold_warning=0.7,
            threshold_critical=0.5,
            is_anomaly=self.health_score < 0.7
        )
    
    async def reset_agent(self):
        """Reset agent state (useful for recovery)."""
        logger.info(f"Resetting agent {self.agent_id}")
        
        self.busy = False
        self.current_task = None
        self.consecutive_failures = 0
        self.last_failure_time = None
        self.health_score = 1.0
        
        # Clear rate limiter
        self.rate_limiter.requests.clear()
        
        logger.info(f"Agent {self.agent_id} reset complete")
    
    async def shutdown(self):
        """Graceful shutdown of the agent."""
        logger.info(f"Shutting down agent {self.agent_id}")
        
        self.enabled = False
        
        # Wait for current task to complete if busy
        max_wait = 30  # seconds
        waited = 0
        while self.busy and waited < max_wait:
            await asyncio.sleep(1)
            waited += 1
        
        if self.busy:
            logger.warning(f"Agent {self.agent_id} forced shutdown while busy")
        
        logger.info(f"Agent {self.agent_id} shutdown complete")
    
    def __str__(self) -> str:
        return f"{self.agent_type.value}Agent({self.agent_id})"
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(agent_id='{self.agent_id}', "
                f"agent_type={self.agent_type}, model='{self.model}', "
                f"health_score={self.health_score:.2f})")


class AgentPool:
    """Manages a pool of agents for load balancing and task distribution."""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self._lock = asyncio.Lock()
    
    async def add_agent(self, agent: BaseAgent):
        """Add an agent to the pool."""
        async with self._lock:
            self.agents[agent.agent_id] = agent
            logger.info(f"Added agent {agent.agent_id} to pool")
    
    async def remove_agent(self, agent_id: str):
        """Remove an agent from the pool."""
        async with self._lock:
            if agent_id in self.agents:
                agent = self.agents.pop(agent_id)
                await agent.shutdown()
                logger.info(f"Removed agent {agent_id} from pool")
    
    async def get_best_agent_for_task(self, task_context: TaskContext) -> Optional[BaseAgent]:
        """Get the best available agent for a specific task."""
        async with self._lock:
            available_agents = [
                agent for agent in self.agents.values()
                if await agent.can_handle_task(task_context) and agent.is_healthy
            ]
            
            if not available_agents:
                return None
            
            # Score agents based on proficiency and current load
            scored_agents = []
            for agent in available_agents:
                proficiency = await agent.get_proficiency_score(task_context.task_type)
                load_penalty = agent.load_factor
                score = proficiency - load_penalty
                scored_agents.append((score, agent))
            
            # Return the highest scoring agent
            scored_agents.sort(key=lambda x: x[0], reverse=True)
            return scored_agents[0][1]
    
    async def get_voting_agents(self, task_context: TaskContext, exclude_agent_id: str = None) -> List[BaseAgent]:
        """Get agents for voting (excluding the proposing agent)."""
        async with self._lock:
            voting_agents = [
                agent for agent in self.agents.values()
                if (agent.agent_id != exclude_agent_id and 
                    await agent.can_handle_task(task_context) and 
                    agent.is_healthy)
            ]
            
            # Return up to 3 agents for voting, prioritizing different types
            agent_types_used = set()
            selected_agents = []
            
            # First pass: select different agent types
            for agent in voting_agents:
                if agent.agent_type not in agent_types_used and len(selected_agents) < 3:
                    selected_agents.append(agent)
                    agent_types_used.add(agent.agent_type)
            
            # Second pass: fill remaining slots with best available
            if len(selected_agents) < 3:
                remaining_agents = [a for a in voting_agents if a not in selected_agents]
                remaining_needed = 3 - len(selected_agents)
                selected_agents.extend(remaining_agents[:remaining_needed])
            
            return selected_agents
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Get status of all agents in the pool."""
        async with self._lock:
            total_agents = len(self.agents)
            healthy_agents = sum(1 for agent in self.agents.values() if agent.is_healthy)
            busy_agents = sum(1 for agent in self.agents.values() if agent.busy)
            
            agent_types = defaultdict(int)
            for agent in self.agents.values():
                agent_types[agent.agent_type.value] += 1
            
            return {
                'total_agents': total_agents,
                'healthy_agents': healthy_agents,
                'busy_agents': busy_agents,
                'idle_agents': healthy_agents - busy_agents,
                'agent_types': dict(agent_types),
                'agents': [agent.get_status_summary() for agent in self.agents.values()]
            }
    
    async def reset_all_agents(self):
        """Reset all agents in the pool."""
        async with self._lock:
            for agent in self.agents.values():
                await agent.reset_agent()
    
    async def shutdown_all_agents(self):
        """Shutdown all agents in the pool."""
        async with self._lock:
            shutdown_tasks = [agent.shutdown() for agent in self.agents.values()]
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
            self.agents.clear()