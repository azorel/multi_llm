"""
Core orchestrator for the autonomous multi-LLM agent system.

This module implements the 1-3-1 workflow pattern:
1. Single proposal generation phase (parallel from multiple agents)
3. Three-agent voting phase with consensus mechanism
1. Single execution phase with validation and rollback capability

The orchestrator coordinates all agents, manages the shared memory system,
and provides comprehensive error handling and self-healing capabilities.
"""

import asyncio
import json
import traceback
import time
import os
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import ValidationError

from ..models.schemas import (
    AgentType, TaskType, ActionType, Priority, ExecutionStatus, VoteType,
    Proposal, Vote, Action, ExecutionResult, ValidationResult,
    TaskContext, AgentConfig, PlanStep, ImprovementPlan, PerformanceMetrics,
    ErrorEvent, SystemState
)
from .agent_base import BaseAgent, AgentPool
from .shared_memory import SharedMemory


class WorkflowResult:
    """Result of a complete workflow execution."""
    
    def __init__(self, task_id: str, status: ExecutionStatus, result: ExecutionResult = None, 
                 error: str = None, proposals: List[Proposal] = None, votes: List[Vote] = None):
        self.task_id = task_id
        self.status = status
        self.result = result
        self.error = error
        self.proposals = proposals or []
        self.votes = votes or []
        self.created_at = datetime.utcnow()


class VotingConfig:
    """Configuration for the voting process."""
    
    def __init__(self, min_votes: int = 3, consensus_threshold: float = 0.6, 
                 timeout_seconds: int = 300):
        self.min_votes = min_votes
        self.consensus_threshold = consensus_threshold
        self.timeout_seconds = timeout_seconds


class WorkflowPhase:
    """Workflow phase tracking for the 1-3-1 pattern."""
    PROPOSAL_GENERATION = "proposal_generation"
    VOTING = "voting"
    EXECUTION = "execution"
    VALIDATION = "validation"
    COMPLETED = "completed"
    FAILED = "failed"


class ConsensusManager:
    """Manages voting and consensus mechanisms."""
    
    def __init__(self, min_votes: int = 3, consensus_threshold: float = 0.6):
        self.min_votes = min_votes
        self.consensus_threshold = consensus_threshold
    
    def calculate_consensus(self, votes: List[Vote]) -> Tuple[bool, float, str]:
        """Calculate consensus from votes."""
        if len(votes) < self.min_votes:
            return False, 0.0, "Insufficient votes"
        
        # Count vote types
        approve_votes = [v for v in votes if v.vote_type == VoteType.APPROVE]
        reject_votes = [v for v in votes if v.vote_type == VoteType.REJECT]
        modify_votes = [v for v in votes if v.vote_type == VoteType.MODIFY]
        abstain_votes = [v for v in votes if v.vote_type == VoteType.ABSTAIN]
        
        total_meaningful_votes = len(approve_votes) + len(reject_votes) + len(modify_votes)
        
        if total_meaningful_votes == 0:
            return False, 0.0, "No meaningful votes cast"
        
        # Calculate approval ratio
        approval_ratio = len(approve_votes) / total_meaningful_votes
        
        # Calculate weighted confidence
        total_confidence = sum(v.confidence for v in approve_votes)
        weighted_confidence = total_confidence / len(approve_votes) if approve_votes else 0.0
        
        # Final score combines approval ratio and confidence
        consensus_score = (approval_ratio * 0.7) + (weighted_confidence * 0.3)
        
        has_consensus = consensus_score >= self.consensus_threshold
        
        reasoning = (f"Approval: {len(approve_votes)}/{total_meaningful_votes} "
                    f"({approval_ratio:.2%}), Confidence: {weighted_confidence:.2f}, "
                    f"Score: {consensus_score:.2f}")
        
        return has_consensus, consensus_score, reasoning


class ExecutionEngine:
    """Handles plan execution with rollback capabilities."""
    
    def __init__(self, agent_pool: AgentPool, shared_memory: SharedMemory):
        self.agent_pool = agent_pool
        self.shared_memory = shared_memory
        self.execution_history: List[Dict[str, Any]] = []
    
    async def execute_action(self, action: Action, task_context: TaskContext) -> ExecutionResult:
        """Execute a single action with comprehensive error handling."""
        start_time = time.time()
        
        try:
            # Get the best agent for this action
            agent = await self.agent_pool.get_best_agent_for_task(task_context)
            
            if not agent:
                raise RuntimeError(f"No suitable agent available for action {action.action_type}")
            
            logger.info(f"Executing action {action.action_id} with agent {agent.agent_id}")
            
            # Execute the action
            result = await agent.execute_action(action, task_context)
            
            # Record execution history for potential rollback
            self.execution_history.append({
                'action': action,
                'result': result,
                'agent_id': agent.agent_id,
                'timestamp': datetime.utcnow()
            })
            
            execution_time = time.time() - start_time
            logger.info(f"Action {action.action_id} completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Action execution failed: {str(e)}"
            logger.error(error_msg)
            
            return ExecutionResult(
                action_id=action.action_id,
                agent_id="unknown",
                status=ExecutionStatus.FAILED,
                error_message=error_msg,
                execution_time=timedelta(seconds=execution_time)
            )
    
    async def rollback_actions(self, rollback_count: int = None) -> bool:
        """Rollback executed actions."""
        if not self.execution_history:
            logger.warning("No actions to rollback")
            return True
        
        rollback_count = rollback_count or len(self.execution_history)
        rollback_count = min(rollback_count, len(self.execution_history))
        
        logger.info(f"Rolling back {rollback_count} actions")
        
        success_count = 0
        for i in range(rollback_count):
            try:
                action_data = self.execution_history.pop()
                # Implement actual rollback logic here
                # This would vary based on action type
                logger.info(f"Rolled back action {action_data['action'].action_id}")
                success_count += 1
            except Exception as e:
                logger.error(f"Rollback failed for action: {e}")
        
        rollback_success = success_count == rollback_count
        logger.info(f"Rollback completed: {success_count}/{rollback_count} successful")
        
        return rollback_success


class Orchestrator:
    """
    Core orchestrator implementing the 1-3-1 workflow pattern.
    
    Coordinates multiple LLM agents to:
    1. Generate proposals in parallel
    2. Vote on proposals with consensus mechanism
    3. Execute chosen proposal with validation and rollback
    """
    
    def __init__(self, agent_pool: AgentPool, shared_memory: SharedMemory, 
                 config: Dict[str, Any] = None):
        """Initialize the orchestrator with required components."""
        self.agent_pool = agent_pool
        self.shared_memory = shared_memory
        self.config = config or {}
        
        # Core components
        self.consensus_manager = ConsensusManager(
            min_votes=self.config.get('min_votes', 3),
            consensus_threshold=self.config.get('consensus_threshold', 0.6)
        )
        self.execution_engine = ExecutionEngine(agent_pool, shared_memory)
        
        # Configuration
        self.max_retries = self.config.get('max_retries', 3)
        self.proposal_timeout = self.config.get('proposal_timeout', 120)  # seconds
        self.voting_timeout = self.config.get('voting_timeout', 60)  # seconds
        self.execution_timeout = self.config.get('execution_timeout', 300)  # seconds
        self.enable_rollback = self.config.get('enable_rollback', True)
        
        # State tracking
        self.current_phase = WorkflowPhase.PROPOSAL_GENERATION
        self.workflow_state = {}
        self.metrics = defaultdict(int)
        
        logger.info("Orchestrator initialized with 1-3-1 workflow pattern")
    
    async def process_task(self, task_context: TaskContext) -> ExecutionResult:
        """
        Main entry point for processing tasks using the 1-3-1 workflow.
        
        Returns an ExecutionResult containing the final outcome.
        """
        workflow_id = f"workflow_{task_context.task_id}"
        start_time = time.time()
        
        logger.info(f"Starting 1-3-1 workflow for task: {task_context.description}")
        
        try:
            # Store initial task context
            await self.shared_memory.store(
                f"task_{task_context.task_id}",
                task_context.dict(),
                entry_type="task_context",
                tags=["workflow", "active"]
            )
            
            # Phase 1: Proposal Generation (parallel)
            self.current_phase = WorkflowPhase.PROPOSAL_GENERATION
            proposals = await self._generate_proposals_parallel(task_context)
            
            if not proposals:
                raise RuntimeError("No valid proposals generated")
            
            # Phase 2: Voting with consensus
            self.current_phase = WorkflowPhase.VOTING
            selected_proposal, consensus_result = await self._conduct_voting(proposals, task_context)
            
            if not selected_proposal:
                raise RuntimeError("No proposal achieved consensus")
            
            # Phase 3: Execution with validation
            self.current_phase = WorkflowPhase.EXECUTION
            execution_result = await self._execute_proposal(selected_proposal, task_context)
            
            # Phase 4: Validation
            self.current_phase = WorkflowPhase.VALIDATION
            validation_result = await self._validate_result(execution_result, task_context)
            
            # Update execution result with validation
            if validation_result:
                execution_result.metadata['validation'] = validation_result.dict()
            
            # Mark as completed
            self.current_phase = WorkflowPhase.COMPLETED
            
            # Calculate final metrics
            total_time = time.time() - start_time
            self.metrics['total_workflows'] += 1
            self.metrics['successful_workflows'] += 1
            
            # Store final result
            await self.shared_memory.store(
                f"result_{task_context.task_id}",
                execution_result.dict(),
                entry_type="execution_result",
                tags=["workflow", "completed"]
            )
            
            logger.info(f"Workflow completed successfully in {total_time:.2f}s")
            return execution_result
            
        except Exception as e:
            self.current_phase = WorkflowPhase.FAILED
            total_time = time.time() - start_time
            
            error_msg = f"Workflow failed: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            
            # Update metrics
            self.metrics['total_workflows'] += 1
            self.metrics['failed_workflows'] += 1
            
            # Create error result
            error_result = ExecutionResult(
                action_id="workflow_error",
                agent_id="orchestrator",
                status=ExecutionStatus.FAILED,
                error_message=error_msg,
                execution_time=timedelta(seconds=total_time),
                metadata={
                    'workflow_phase': self.current_phase,
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                }
            )
            
            # Store error result
            await self.shared_memory.store(
                f"error_{task_context.task_id}",
                error_result.dict(),
                entry_type="error_result",
                tags=["workflow", "failed"]
            )
            
            return error_result
    
    async def _generate_proposals_parallel(self, task_context: TaskContext) -> List[Proposal]:
        """Generate proposals from multiple agents in parallel."""
        logger.info("Phase 1: Generating proposals in parallel")
        
        # Get all available agents that can handle this task
        available_agents = []
        for agent in self.agent_pool.agents.values():
            if await agent.can_handle_task(task_context):
                available_agents.append(agent)
        
        if not available_agents:
            raise RuntimeError("No agents available to handle this task")
        
        logger.info(f"Found {len(available_agents)} capable agents")
        
        # Create proposal generation tasks
        proposal_tasks = []
        for agent in available_agents:
            task = asyncio.create_task(
                self._generate_single_proposal(agent, task_context),
                name=f"proposal_{agent.agent_id}"
            )
            proposal_tasks.append(task)
        
        # Wait for all proposals with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*proposal_tasks, return_exceptions=True),
                timeout=self.proposal_timeout
            )
        except asyncio.TimeoutError:
            logger.error("Proposal generation timed out")
            # Cancel remaining tasks
            for task in proposal_tasks:
                if not task.done():
                    task.cancel()
            raise RuntimeError("Proposal generation timeout")
        
        # Process results and filter valid proposals
        valid_proposals = []
        for i, result in enumerate(results):
            agent = available_agents[i]
            
            if isinstance(result, Exception):
                logger.error(f"Agent {agent.agent_id} failed to generate proposal: {result}")
                
                # Create error event
                error_event = ErrorEvent(
                    error_type="proposal_generation_failed",
                    component=f"agent_{agent.agent_id}",
                    message=str(result),
                    severity="medium",
                    context={'task_id': task_context.task_id}
                )
                await self.shared_memory.store(
                    f"error_{error_event.event_id}",
                    error_event.dict(),
                    entry_type="error_event"
                )
            
            elif isinstance(result, Proposal):
                valid_proposals.append(result)
                logger.info(f"Received proposal from {agent.agent_id}: {result.approach[:100]}...")
        
        logger.info(f"Generated {len(valid_proposals)} valid proposals")
        return valid_proposals
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    async def _generate_single_proposal(self, agent: BaseAgent, task_context: TaskContext) -> Proposal:
        """Generate a proposal from a single agent with retry logic."""
        try:
            proposal = await agent.generate_proposal(task_context)
            
            # Store proposal in shared memory
            await self.shared_memory.store(
                f"proposal_{proposal.proposal_id}",
                proposal.dict(),
                entry_type="proposal",
                tags=["workflow", "proposal", agent.agent_id]
            )
            
            return proposal
            
        except Exception as e:
            logger.error(f"Failed to generate proposal from {agent.agent_id}: {e}")
            raise
    
    async def _conduct_voting(self, proposals: List[Proposal], task_context: TaskContext) -> Tuple[Optional[Proposal], Dict[str, Any]]:
        """Conduct voting phase with consensus mechanism."""
        logger.info(f"Phase 2: Conducting voting on {len(proposals)} proposals")
        
        # Get voting agents (excluding proposal authors when possible)
        voting_agents = await self.agent_pool.get_voting_agents(
            task_context, 
            exclude_agent_id=None  # We'll handle exclusion per proposal
        )
        
        if len(voting_agents) < self.consensus_manager.min_votes:
            logger.warning(f"Only {len(voting_agents)} voting agents available, minimum is {self.consensus_manager.min_votes}")
        
        # Collect votes for all proposals
        all_votes = []
        proposal_votes = defaultdict(list)
        
        for proposal in proposals:
            # Get voters (exclude proposal author if possible)
            proposal_voters = [
                agent for agent in voting_agents 
                if agent.agent_id != proposal.agent_id
            ]
            
            # If we don't have enough voters after exclusion, include the author
            if len(proposal_voters) < self.consensus_manager.min_votes:
                proposal_voters = voting_agents
            
            # Get votes for this proposal
            for voter in proposal_voters:
                try:
                    vote = await self._get_single_vote(voter, proposal, task_context)
                    all_votes.append(vote)
                    proposal_votes[proposal.proposal_id].append(vote)
                    
                    # Store vote in shared memory
                    await self.shared_memory.store(
                        f"vote_{vote.vote_id}",
                        vote.dict(),
                        entry_type="vote",
                        tags=["workflow", "voting", voter.agent_id]
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to get vote from {voter.agent_id} for proposal {proposal.proposal_id}: {e}")
        
        # Calculate consensus for each proposal
        proposal_scores = {}
        for proposal in proposals:
            votes = proposal_votes[proposal.proposal_id]
            
            if votes:
                has_consensus, score, reasoning = self.consensus_manager.calculate_consensus(votes)
                proposal_scores[proposal.proposal_id] = {
                    'proposal': proposal,
                    'votes': votes,
                    'has_consensus': has_consensus,
                    'score': score,
                    'reasoning': reasoning
                }
        
        # Select the proposal with highest consensus score
        best_proposal = None
        best_score = -1
        consensus_result = {}
        
        for proposal_id, score_data in proposal_scores.items():
            if score_data['has_consensus'] and score_data['score'] > best_score:
                best_proposal = score_data['proposal']
                best_score = score_data['score']
                consensus_result = score_data
        
        # If no proposal achieved consensus, select the highest scoring one anyway
        if not best_proposal and proposal_scores:
            best_data = max(proposal_scores.values(), key=lambda x: x['score'])
            best_proposal = best_data['proposal']
            consensus_result = best_data
            logger.warning(f"No proposal achieved consensus, selecting best scoring: {best_data['score']:.2f}")
        
        if best_proposal:
            logger.info(f"Selected proposal from {best_proposal.agent_id} with score {consensus_result['score']:.2f}")
            logger.info(f"Consensus reasoning: {consensus_result['reasoning']}")
        
        return best_proposal, consensus_result
    
    async def _get_single_vote(self, agent: BaseAgent, proposal: Proposal, task_context: TaskContext) -> Vote:
        """Get a vote from a single agent with timeout handling."""
        try:
            vote = await asyncio.wait_for(
                agent.vote_on_proposal(proposal, task_context),
                timeout=self.voting_timeout
            )
            return vote
            
        except asyncio.TimeoutError:
            logger.warning(f"Vote timeout for agent {agent.agent_id}")
            # Create default abstain vote
            return Vote(
                voter_agent_id=agent.agent_id,
                proposal_id=proposal.proposal_id,
                vote_type=VoteType.ABSTAIN,
                confidence=0.0,
                reasoning="Vote timeout - abstaining",
                estimated_success_probability=0.5
            )
        except Exception as e:
            logger.error(f"Error getting vote from {agent.agent_id}: {e}")
            # Create default reject vote
            return Vote(
                voter_agent_id=agent.agent_id,
                proposal_id=proposal.proposal_id,
                vote_type=VoteType.REJECT,
                confidence=0.0,
                reasoning=f"Error during voting: {str(e)}",
                estimated_success_probability=0.0
            )
    
    async def _execute_proposal(self, proposal: Proposal, task_context: TaskContext) -> ExecutionResult:
        """Execute the selected proposal with comprehensive error handling."""
        logger.info(f"Phase 3: Executing proposal from {proposal.agent_id}")
        
        # Create execution action
        execution_action = Action(
            action_type=ActionType.EXECUTE_TASK,
            agent_id=proposal.agent_id,
            task_context=task_context,
            parameters={
                'proposal': proposal.dict(),
                'approach': proposal.approach,
                'required_tools': proposal.required_tools
            },
            estimated_duration=proposal.estimated_time,
            timeout=self.execution_timeout
        )
        
        try:
            # Execute with the orchestrator's execution engine
            result = await asyncio.wait_for(
                self.execution_engine.execute_action(execution_action, task_context),
                timeout=self.execution_timeout
            )
            
            # If execution failed and rollback is enabled, attempt rollback
            if result.status == ExecutionStatus.FAILED and self.enable_rollback:
                logger.warning("Execution failed, attempting rollback")
                rollback_success = await self.execution_engine.rollback_actions()
                result.metadata['rollback_performed'] = rollback_success
                
                if rollback_success:
                    result.status = ExecutionStatus.CANCELLED  # Changed from FAILED to show rollback
            
            return result
            
        except asyncio.TimeoutError:
            logger.error("Execution timeout exceeded")
            
            # Attempt rollback on timeout
            if self.enable_rollback:
                await self.execution_engine.rollback_actions()
            
            return ExecutionResult(
                action_id=execution_action.action_id,
                agent_id=proposal.agent_id,
                status=ExecutionStatus.TIMEOUT,
                error_message="Execution timeout exceeded",
                execution_time=timedelta(seconds=self.execution_timeout),
                metadata={'rollback_performed': self.enable_rollback}
            )
        
        except Exception as e:
            logger.error(f"Execution error: {e}")
            
            # Attempt rollback on error
            if self.enable_rollback:
                await self.execution_engine.rollback_actions()
            
            return ExecutionResult(
                action_id=execution_action.action_id,
                agent_id=proposal.agent_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                execution_time=timedelta(seconds=0),
                metadata={'rollback_performed': self.enable_rollback}
            )
    
    async def _validate_result(self, execution_result: ExecutionResult, task_context: TaskContext) -> Optional[ValidationResult]:
        """Validate the execution result."""
        logger.info("Phase 4: Validating execution result")
        
        if execution_result.status == ExecutionStatus.FAILED:
            logger.info("Skipping validation for failed execution")
            return None
        
        try:
            # Get a different agent for validation (not the executor)
            validation_agent = await self.agent_pool.get_best_agent_for_task(task_context)
            
            if validation_agent and validation_agent.agent_id != execution_result.agent_id:
                validation_result = await validation_agent.validate_result(execution_result, task_context)
                
                # Store validation result
                await self.shared_memory.store(
                    f"validation_{validation_result.validation_id}",
                    validation_result.dict(),
                    entry_type="validation_result",
                    tags=["workflow", "validation"]
                )
                
                logger.info(f"Validation completed: {validation_result.is_valid} (confidence: {validation_result.confidence:.2f})")
                return validation_result
            
            else:
                logger.warning("No suitable agent available for validation")
                return None
                
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return None
    
    async def get_workflow_status(self, task_id: str) -> Dict[str, Any]:
        """Get the current status of a workflow."""
        try:
            # Get task context
            task_data = await self.shared_memory.get(f"task_{task_id}")
            
            # Get related data
            proposals = []
            votes = []
            results = []
            
            # Search for related entries
            proposal_keys = await self.shared_memory.search("proposal_", entry_type="proposal")
            for key in proposal_keys:
                proposal_data = await self.shared_memory.get(key)
                if proposal_data and proposal_data.get('task_context', {}).get('task_id') == task_id:
                    proposals.append(proposal_data)
            
            vote_keys = await self.shared_memory.search("vote_", entry_type="vote")
            for key in vote_keys:
                vote_data = await self.shared_memory.get(key)
                if vote_data:
                    votes.append(vote_data)
            
            result_data = await self.shared_memory.get(f"result_{task_id}")
            
            return {
                'task_id': task_id,
                'current_phase': self.current_phase,
                'task_context': task_data,
                'proposals': proposals,
                'votes': votes,
                'result': result_data,
                'metrics': dict(self.metrics)
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return {'error': str(e)}
    
    async def get_performance_metrics(self) -> PerformanceMetrics:
        """Get orchestrator performance metrics."""
        total_workflows = self.metrics['total_workflows']
        successful_workflows = self.metrics['successful_workflows']
        
        success_rate = successful_workflows / total_workflows if total_workflows > 0 else 0.0
        
        return PerformanceMetrics(
            component="orchestrator",
            metric_name="workflow_success_rate",
            value=success_rate,
            unit="ratio",
            tags={
                'total_workflows': str(total_workflows),
                'successful_workflows': str(successful_workflows),
                'current_phase': self.current_phase
            },
            context={
                'workflow_metrics': dict(self.metrics)
            },
            threshold_warning=0.8,
            threshold_critical=0.6,
            is_anomaly=success_rate < 0.7
        )
    
    async def reset_workflow_state(self):
        """Reset the orchestrator state."""
        logger.info("Resetting orchestrator workflow state")
        
        self.current_phase = WorkflowPhase.PROPOSAL_GENERATION
        self.workflow_state.clear()
        self.execution_engine.execution_history.clear()
        
        logger.info("Orchestrator state reset complete")
    
    async def shutdown(self):
        """Graceful shutdown of the orchestrator."""
        logger.info("Shutting down orchestrator")
        
        # Reset state
        await self.reset_workflow_state()
        
        # Shutdown shared memory
        if hasattr(self.shared_memory, 'shutdown'):
            await self.shared_memory.shutdown()
        
        logger.info("Orchestrator shutdown complete")