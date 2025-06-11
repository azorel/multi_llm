"""
Temporary stubs for missing components to test the core system.
"""

from typing import Dict, Any, Optional, List
import asyncio
import time
from datetime import datetime, timedelta


class TemporaryObservability:
    """Temporary observability stub."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
    
    def start(self):
        self.running = True
    
    def stop(self):
        self.running = False
    
    def get_health_status(self):
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}


def initialize_observability(config: Dict[str, Any]) -> TemporaryObservability:
    """Initialize temporary observability system."""
    return TemporaryObservability(config)


class TemporarySharedMemory:
    """Temporary shared memory implementation."""
    
    def __init__(self):
        self.storage = {}
    
    def store(self, key: str, value: Any, entry_type: str = "data", tags: List[str] = None):
        self.storage[key] = {
            "value": value,
            "entry_type": entry_type,
            "tags": tags or [],
            "timestamp": datetime.now()
        }
    
    def retrieve(self, key: str) -> Optional[Any]:
        entry = self.storage.get(key)
        return entry["value"] if entry else None
    
    def delete(self, key: str):
        if key in self.storage:
            del self.storage[key]
    
    def search(self, pattern: str, entry_type: str = None) -> List[str]:
        results = []
        for key, entry in self.storage.items():
            if pattern in key:
                if entry_type is None or entry.get("entry_type") == entry_type:
                    results.append(key)
        return results


class TemporaryAgent:
    """Temporary agent implementation."""
    
    def __init__(self, agent_id: str, model: str = "unknown"):
        self.agent_id = agent_id
        self.model = model
        self.__class__.__name__ = f"Temporary{agent_id.title()}Agent"
    
    async def can_handle_task(self, task_context):
        return True
    
    async def generate_proposal(self, task_context):
        from models.schemas import Proposal
        return Proposal(
            agent_id=self.agent_id,
            approach=f"Process task: {task_context.description}",
            required_tools=["basic"],
            estimated_time=timedelta(seconds=30),
            confidence=0.8
        )
    
    async def vote_on_proposal(self, proposal, task_context):
        from models.schemas import Vote, VoteType
        return Vote(
            voter_agent_id=self.agent_id,
            proposal_id=proposal.proposal_id,
            vote_type=VoteType.APPROVE,
            confidence=0.7,
            reasoning="Temporary approval",
            estimated_success_probability=0.7
        )
    
    async def execute_action(self, action, task_context):
        from models.schemas import ExecutionResult, ExecutionStatus
        await asyncio.sleep(1)  # Simulate work
        return ExecutionResult(
            action_id=action.action_id,
            agent_id=self.agent_id,
            status=ExecutionStatus.COMPLETED,
            output=f"Task completed: {task_context.description}",
            execution_time=timedelta(seconds=1)
        )
    
    async def validate_result(self, execution_result, task_context):
        from models.schemas import ValidationResult
        return ValidationResult(
            execution_result_id=execution_result.action_id,
            validator_agent_id=self.agent_id,
            is_valid=True,
            confidence=0.8,
            feedback="Result looks good"
        )


class TemporaryAgentPool:
    """Temporary agent pool implementation."""
    
    def __init__(self, agents: Dict[str, Any] = None):
        self.agents = agents or {
            "temp_agent1": TemporaryAgent("temp_agent1", "temporary-model-1"),
            "temp_agent2": TemporaryAgent("temp_agent2", "temporary-model-2"),
            "temp_agent3": TemporaryAgent("temp_agent3", "temporary-model-3")
        }
    
    async def get_best_agent_for_task(self, task_context):
        return list(self.agents.values())[0]
    
    async def get_voting_agents(self, task_context, exclude_agent_id=None):
        return [agent for agent_id, agent in self.agents.items() 
                if agent_id != exclude_agent_id]


class TemporaryRecoveryManager:
    """Temporary recovery manager."""
    
    def __init__(self, agents, shared_memory, config):
        self.agents = agents
        self.shared_memory = shared_memory
        self.config = config
    
    async def monitor_system_health(self):
        pass  # Temporary stub


class TemporaryNotionClient:
    """Temporary Notion client stub."""
    
    def __init__(self, api_key, database_ids):
        self.api_key = api_key
        self.database_ids = database_ids
    
    async def get_pending_tasks(self):
        return []  # No tasks for now
    
    async def update_task_result(self, task_id, result):
        pass
    
    async def log_execution(self, task_context, result):
        pass


class TemporaryGitHubClient:
    """Temporary GitHub client stub."""
    
    def __init__(self, token, owner, repo):
        self.token = token
        self.owner = owner
        self.repo = repo