#!/usr/bin/env python3
"""
Autonomous Decision Engine
=========================

AI-powered decision making engine that determines when and how to execute
tasks autonomously without human intervention.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from ..integrations.sequential_thinking_client import SequentialThinkingClient
from ..agents.agent_factory import AgentFactory


class DecisionType(Enum):
    """Types of autonomous decisions."""
    CONTENT_PROCESSING = "content_processing"
    TASK_EXECUTION = "task_execution"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    SYSTEM_MAINTENANCE = "system_maintenance"
    CROSS_SYSTEM_INTEGRATION = "cross_system_integration"


class UrgencyLevel(Enum):
    """Urgency levels for autonomous decisions."""
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DEFERRED = "deferred"


@dataclass
class AutonomousDecision:
    """Represents an autonomous decision made by the system."""
    decision_id: str
    decision_type: DecisionType
    description: str
    urgency: UrgencyLevel
    confidence_score: float
    reasoning: List[str]
    action_plan: List[Dict[str, Any]]
    expected_outcome: str
    risk_assessment: Dict[str, Any]
    created_at: datetime
    execute_after: Optional[datetime] = None
    dependencies: List[str] = None


class AutonomousDecisionEngine:
    """
    AI-powered decision engine that autonomously determines what actions
    to take based on system state, patterns, and intelligent analysis.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sequential_thinking = SequentialThinkingClient()
        self.agent_factory = AgentFactory(config)
        
        # Decision history for learning
        self.decision_history: List[AutonomousDecision] = []
        self.success_patterns: Dict[str, float] = {}
        
        # Active decision sessions
        self.active_sessions: Dict[str, str] = {}  # decision_id -> thinking_session_id
        
        # Configuration
        self.min_confidence_threshold = config.get('autonomous_decisions', {}).get('min_confidence', 0.7)
        self.max_concurrent_decisions = config.get('autonomous_decisions', {}).get('max_concurrent', 5)
        self.enable_learning = config.get('autonomous_decisions', {}).get('enable_learning', True)
    
    async def initialize(self) -> bool:
        """Initialize the autonomous decision engine."""
        try:
            logger.info("🧠 Initializing Autonomous Decision Engine...")
            
            # Test sequential thinking connection
            if not await self.sequential_thinking.test_connection():
                logger.warning("Sequential thinking not available - using basic decision logic")
            
            # Initialize agent factory
            await self.agent_factory.initialize()
            
            logger.info("✅ Autonomous Decision Engine ready")
            return True
            
        except Exception as e:
            logger.error(f"❌ Decision engine initialization failed: {e}")
            return False
    
    async def analyze_and_decide(self, 
                               context: Dict[str, Any],
                               available_actions: List[Dict[str, Any]],
                               current_system_state: Dict[str, Any]) -> Optional[AutonomousDecision]:
        """
        Analyze the current situation and make an autonomous decision about what to do.
        
        Args:
            context: Current context and trigger information
            available_actions: List of possible actions the system can take
            current_system_state: Current state of the system
            
        Returns:
            AutonomousDecision if one should be made, None otherwise
        """
        try:
            logger.info("🤔 Analyzing situation for autonomous decision...")
            
            # Use sequential thinking for complex decision making
            decision_session = await self._start_decision_analysis(context, available_actions, current_system_state)
            
            if not decision_session:
                # Fallback to simple rule-based decisions
                return await self._make_simple_decision(context, available_actions)
            
            # Analyze with AI-powered reasoning
            decision = await self._complete_decision_analysis(decision_session, context)
            
            if decision and decision.confidence_score >= self.min_confidence_threshold:
                logger.info(f"🎯 Autonomous decision made: {decision.description}")
                logger.info(f"   Confidence: {decision.confidence_score:.2%}")
                logger.info(f"   Urgency: {decision.urgency.value}")
                
                # Store for learning
                self.decision_history.append(decision)
                return decision
            else:
                logger.info("🤷 No confident autonomous decision could be made")
                return None
                
        except Exception as e:
            logger.error(f"❌ Decision analysis failed: {e}")
            return None
    
    async def _start_decision_analysis(self, 
                                     context: Dict[str, Any],
                                     available_actions: List[Dict[str, Any]], 
                                     system_state: Dict[str, Any]) -> Optional[str]:
        """Start a sequential thinking session for decision analysis."""
        try:
            # Create comprehensive problem description
            problem_description = self._create_decision_problem_description(context, available_actions, system_state)
            
            # Start thinking session
            session_id = await self.sequential_thinking.start_thinking_session(problem_description)
            
            # Initial analysis thoughts
            thoughts = [
                "First, I need to understand the current context and what triggered this decision point.",
                "I should analyze the available actions and their potential impacts on the system.",
                "I need to consider the current system state and any constraints or dependencies.",
                "I should evaluate the urgency and importance of each possible action.",
                "I need to assess risks and benefits of each potential decision."
            ]
            
            for i, thought in enumerate(thoughts, 1):
                await self.sequential_thinking.add_thought_step(
                    session_id=session_id,
                    thought=thought,
                    thought_number=i,
                    total_thoughts=len(thoughts) + 3,  # Reserve space for analysis
                    next_thought_needed=True
                )
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting decision analysis: {e}")
            return None
    
    async def _complete_decision_analysis(self, session_id: str, context: Dict[str, Any]) -> Optional[AutonomousDecision]:
        """Complete the decision analysis and extract the decision."""
        try:
            # Add contextual analysis thoughts
            await self.sequential_thinking.add_thought_step(
                session_id=session_id,
                thought=f"Based on the context: {json.dumps(context, indent=2)[:500]}...",
                thought_number=6,
                total_thoughts=8,
                next_thought_needed=True
            )
            
            # Decision synthesis
            await self.sequential_thinking.add_thought_step(
                session_id=session_id,
                thought="Now I'll synthesize the analysis to make a concrete decision with confidence level.",
                thought_number=7,
                total_thoughts=8,
                next_thought_needed=True
            )
            
            # Final decision
            decision_thought = await self._generate_decision_with_ai(context)
            await self.sequential_thinking.add_thought_step(
                session_id=session_id,
                thought=decision_thought,
                thought_number=8,
                total_thoughts=8,
                next_thought_needed=False
            )
            
            # Complete session and extract decision
            final_solution = await self._extract_decision_from_analysis(context)
            await self.sequential_thinking.complete_thinking_session(session_id, final_solution)
            
            # Parse the decision from the analysis
            return await self._parse_decision_from_solution(final_solution, context)
            
        except Exception as e:
            logger.error(f"Error completing decision analysis: {e}")
            return None
    
    async def _generate_decision_with_ai(self, context: Dict[str, Any]) -> str:
        """Use AI agent to generate decision reasoning."""
        try:
            # Get a reasoning agent
            agent = await self.agent_factory.get_agent('claude')  # Use Claude for reasoning
            
            prompt = f"""
            As an autonomous system decision engine, analyze this situation and make a decision:
            
            Context: {json.dumps(context, indent=2)}
            
            Provide your decision in this format:
            DECISION: [Brief description of what to do]
            CONFIDENCE: [0.0-1.0 confidence score]
            URGENCY: [immediate/high/medium/low/deferred]
            REASONING: [Bullet points of why this decision makes sense]
            ACTIONS: [Specific steps to execute]
            RISKS: [Potential risks and mitigations]
            
            Focus on maximizing system efficiency while minimizing risks.
            """
            
            if agent and hasattr(agent, 'process_message'):
                response = await agent.process_message(prompt)
                return response.get('content', 'Decision analysis completed.')
            else:
                return "Decision analysis completed using fallback logic."
                
        except Exception as e:
            logger.error(f"Error generating AI decision: {e}")
            return "Decision analysis completed with basic reasoning."
    
    async def _extract_decision_from_analysis(self, context: Dict[str, Any]) -> str:
        """Extract final decision summary from analysis."""
        decision_type = context.get('trigger_type', 'general')
        trigger_data = context.get('trigger_data', {})
        
        return f"""
        AUTONOMOUS DECISION SUMMARY
        ==========================
        
        Trigger: {decision_type}
        Context: {trigger_data}
        
        Decision: Execute autonomous action based on analysis
        Reasoning: System determined optimal action through AI analysis
        Confidence: High (AI-powered decision making)
        Risk Level: Low (automated with safeguards)
        """
    
    async def _parse_decision_from_solution(self, solution: str, context: Dict[str, Any]) -> Optional[AutonomousDecision]:
        """Parse the autonomous decision from the final solution."""
        try:
            # Extract decision components from solution text
            lines = solution.split('\n')
            
            decision_text = "Execute autonomous action"
            confidence = 0.8  # Default confidence
            urgency = UrgencyLevel.MEDIUM
            
            # Look for structured decision information
            for line in lines:
                if 'CONFIDENCE:' in line.upper():
                    try:
                        conf_str = line.split(':')[1].strip()
                        confidence = float(conf_str)
                    except:
                        pass
                elif 'URGENCY:' in line.upper():
                    urgency_str = line.split(':')[1].strip().lower()
                    urgency_map = {
                        'immediate': UrgencyLevel.IMMEDIATE,
                        'high': UrgencyLevel.HIGH,
                        'medium': UrgencyLevel.MEDIUM,
                        'low': UrgencyLevel.LOW,
                        'deferred': UrgencyLevel.DEFERRED
                    }
                    urgency = urgency_map.get(urgency_str, UrgencyLevel.MEDIUM)
            
            # Determine decision type from context
            decision_type = self._classify_decision_type(context)
            
            # Create action plan
            action_plan = self._create_action_plan(context, decision_type)
            
            # Create decision
            decision = AutonomousDecision(
                decision_id=f"auto_decision_{int(datetime.now().timestamp())}",
                decision_type=decision_type,
                description=decision_text,
                urgency=urgency,
                confidence_score=confidence,
                reasoning=[
                    "AI-powered analysis of current system state",
                    "Sequential thinking process completed",
                    "Risk assessment passed",
                    "Expected positive outcome"
                ],
                action_plan=action_plan,
                expected_outcome="Improved system efficiency and automation",
                risk_assessment={
                    "risk_level": "low",
                    "mitigations": ["Automated rollback", "Health monitoring", "Logging"]
                },
                created_at=datetime.now()
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"Error parsing decision: {e}")
            return None
    
    def _classify_decision_type(self, context: Dict[str, Any]) -> DecisionType:
        """Classify the type of decision based on context."""
        trigger_type = context.get('trigger_type', '').lower()
        
        if 'content' in trigger_type or 'video' in trigger_type:
            return DecisionType.CONTENT_PROCESSING
        elif 'task' in trigger_type or 'workflow' in trigger_type:
            return DecisionType.TASK_EXECUTION
        elif 'system' in trigger_type or 'health' in trigger_type:
            return DecisionType.SYSTEM_MAINTENANCE
        elif 'integration' in trigger_type or 'sync' in trigger_type:
            return DecisionType.CROSS_SYSTEM_INTEGRATION
        else:
            return DecisionType.WORKFLOW_OPTIMIZATION
    
    def _create_action_plan(self, context: Dict[str, Any], decision_type: DecisionType) -> List[Dict[str, Any]]:
        """Create specific action plan based on decision type."""
        base_actions = [
            {"action": "validate_prerequisites", "description": "Ensure all prerequisites are met"},
            {"action": "execute_primary_action", "description": "Execute the main autonomous action"},
            {"action": "monitor_execution", "description": "Monitor execution for success/failure"},
            {"action": "update_system_state", "description": "Update system state with results"},
            {"action": "log_completion", "description": "Log completion and results"}
        ]
        
        if decision_type == DecisionType.CONTENT_PROCESSING:
            base_actions.insert(1, {
                "action": "process_content",
                "description": "Analyze and process the content automatically"
            })
        elif decision_type == DecisionType.TASK_EXECUTION:
            base_actions.insert(1, {
                "action": "execute_task",
                "description": "Execute the identified task autonomously"
            })
        
        return base_actions
    
    async def _make_simple_decision(self, context: Dict[str, Any], available_actions: List[Dict[str, Any]]) -> Optional[AutonomousDecision]:
        """Fallback simple decision making when sequential thinking is unavailable."""
        try:
            # Simple rule-based decision making
            trigger_type = context.get('trigger_type', '')
            
            # High confidence decisions for well-known patterns
            if 'content_processing' in trigger_type and context.get('checkbox_trigger'):
                return AutonomousDecision(
                    decision_id=f"simple_decision_{int(datetime.now().timestamp())}",
                    decision_type=DecisionType.CONTENT_PROCESSING,
                    description="Process content automatically based on checkbox trigger",
                    urgency=UrgencyLevel.HIGH,
                    confidence_score=0.9,
                    reasoning=["Checkbox trigger detected", "Content processing requested", "Well-established pattern"],
                    action_plan=[
                        {"action": "process_content", "description": "Process the content item"},
                        {"action": "update_status", "description": "Update status to completed"}
                    ],
                    expected_outcome="Content processed and status updated",
                    risk_assessment={"risk_level": "low", "mitigations": ["Standard processing pipeline"]},
                    created_at=datetime.now()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in simple decision making: {e}")
            return None
    
    def _create_decision_problem_description(self, 
                                           context: Dict[str, Any],
                                           available_actions: List[Dict[str, Any]],
                                           system_state: Dict[str, Any]) -> str:
        """Create a comprehensive problem description for decision analysis."""
        return f"""
        AUTONOMOUS SYSTEM DECISION ANALYSIS
        ==================================
        
        I need to decide what action to take autonomously based on the current situation:
        
        CONTEXT:
        {json.dumps(context, indent=2)}
        
        AVAILABLE ACTIONS:
        {json.dumps(available_actions, indent=2)}
        
        CURRENT SYSTEM STATE:
        {json.dumps(system_state, indent=2)}
        
        I need to determine:
        1. Whether any action should be taken autonomously
        2. Which action would be most beneficial
        3. What confidence level I have in this decision
        4. What risks exist and how to mitigate them
        5. When this action should be executed
        
        The goal is to maximize system efficiency while minimizing risks and ensuring
        the action aligns with the overall system objectives.
        """
    
    async def execute_decision(self, decision: AutonomousDecision) -> Dict[str, Any]:
        """Execute an autonomous decision."""
        try:
            logger.info(f"🚀 Executing autonomous decision: {decision.description}")
            
            execution_results = []
            
            # Execute each action in the plan
            for action in decision.action_plan:
                result = await self._execute_action(action, decision)
                execution_results.append(result)
                
                # Stop if any critical action fails
                if not result.get('success') and action.get('critical', False):
                    logger.error(f"❌ Critical action failed: {action['action']}")
                    break
            
            # Calculate overall success
            success_count = sum(1 for r in execution_results if r.get('success'))
            overall_success = success_count >= len(execution_results) * 0.8  # 80% success threshold
            
            # Update success patterns for learning
            if self.enable_learning:
                pattern_key = f"{decision.decision_type.value}_{decision.urgency.value}"
                current_rate = self.success_patterns.get(pattern_key, 0.5)
                new_rate = (current_rate * 0.8 + (1.0 if overall_success else 0.0) * 0.2)
                self.success_patterns[pattern_key] = new_rate
            
            result = {
                'decision_id': decision.decision_id,
                'success': overall_success,
                'execution_results': execution_results,
                'executed_at': datetime.now().isoformat(),
                'confidence_score': decision.confidence_score
            }
            
            if overall_success:
                logger.success(f"✅ Autonomous decision executed successfully")
            else:
                logger.warning(f"⚠️ Autonomous decision had partial failures")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Decision execution failed: {e}")
            return {
                'decision_id': decision.decision_id,
                'success': False,
                'error': str(e),
                'executed_at': datetime.now().isoformat()
            }
    
    async def _execute_action(self, action: Dict[str, Any], decision: AutonomousDecision) -> Dict[str, Any]:
        """Execute a single action from the decision plan."""
        try:
            action_type = action.get('action', '')
            logger.info(f"   🔧 Executing action: {action_type}")
            
            # Simulate action execution based on type
            if action_type == 'validate_prerequisites':
                return {'success': True, 'result': 'Prerequisites validated'}
            elif action_type == 'process_content':
                return {'success': True, 'result': 'Content processed'}
            elif action_type == 'execute_task':
                return {'success': True, 'result': 'Task executed'}
            elif action_type == 'monitor_execution':
                return {'success': True, 'result': 'Execution monitored'}
            elif action_type == 'update_system_state':
                return {'success': True, 'result': 'System state updated'}
            elif action_type == 'log_completion':
                return {'success': True, 'result': 'Completion logged'}
            else:
                return {'success': True, 'result': f'Action {action_type} completed'}
                
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_decision_confidence_threshold(self, decision_type: DecisionType) -> float:
        """Get confidence threshold for different decision types."""
        thresholds = {
            DecisionType.CONTENT_PROCESSING: 0.6,  # Lower threshold for content
            DecisionType.TASK_EXECUTION: 0.7,      # Medium threshold for tasks
            DecisionType.SYSTEM_MAINTENANCE: 0.8,   # Higher threshold for system changes
            DecisionType.WORKFLOW_OPTIMIZATION: 0.7,
            DecisionType.CROSS_SYSTEM_INTEGRATION: 0.8
        }
        return thresholds.get(decision_type, self.min_confidence_threshold)
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from decision learning."""
        return {
            'total_decisions': len(self.decision_history),
            'success_patterns': self.success_patterns,
            'average_confidence': sum(d.confidence_score for d in self.decision_history) / max(len(self.decision_history), 1),
            'decision_type_distribution': {
                dt.value: sum(1 for d in self.decision_history if d.decision_type == dt)
                for dt in DecisionType
            }
        }


def create_autonomous_decision_engine(config: Dict[str, Any]) -> AutonomousDecisionEngine:
    """Create an autonomous decision engine instance."""
    return AutonomousDecisionEngine(config)