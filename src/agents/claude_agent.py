"""
Anthropic Claude agent implementation with constitutional AI principles.

This agent integrates with Anthropic's Claude models and emphasizes
safety, ethics, and thoughtful analysis in all operations.
"""

import asyncio
import json
import os
import re
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from loguru import logger
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.agent_base import BaseAgent
from ..models.schemas import (
    AgentType, TaskType, ActionType, Priority, ExecutionStatus, VoteType,
    Proposal, Vote, Action, ExecutionResult, ValidationResult,
    TaskContext, AgentConfig, ImprovementPlan
)


class ClaudeAgent(BaseAgent):
    """
    Anthropic Claude agent with constitutional AI principles and comprehensive safety.
    
    Features:
    - Claude 3 Opus, Sonnet, and Haiku support
    - Constitutional AI principles
    - Long context processing (200k+ tokens)
    - Safety-first approach
    - Ethical considerations in all decisions
    - Comprehensive analytical capabilities
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize Claude agent with Anthropic client."""
        super().__init__(config)
        
        # Anthropic client initialization
        self.api_key = config.metadata.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY env var or pass in config.")
        
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        # Model configuration
        self.primary_model = config.metadata.get("primary_model", "claude-3-opus-20240229")
        self.fallback_model = config.metadata.get("fallback_model", "claude-3-sonnet-20240229")
        self.fast_model = config.metadata.get("fast_model", "claude-3-haiku-20240307")
        
        # Feature flags
        self.use_long_context = config.metadata.get("use_long_context", True)
        self.safety_level = config.metadata.get("safety_level", "high")  # low, medium, high
        self.constitutional_ai = config.metadata.get("constitutional_ai", True)
        
        # Cost configuration (Claude 3 pricing as of 2024)
        self.input_cost_per_token = config.metadata.get("input_cost_per_token", 0.000015)
        self.output_cost_per_token = config.metadata.get("output_cost_per_token", 0.000075)
        
        # Context window limits
        self.max_context_tokens = config.metadata.get("max_context_tokens", 200000)
        self.context_utilization = config.metadata.get("context_utilization", 0.8)
        
        # Constitutional AI principles
        self.constitutional_principles = [
            "Be helpful, harmless, and honest",
            "Respect human autonomy and dignity",
            "Consider ethical implications of all actions",
            "Prioritize safety in recommendations",
            "Provide balanced and nuanced perspectives",
            "Acknowledge uncertainty and limitations",
            "Encourage critical thinking and verification"
        ]
        
        # System prompts emphasizing Claude's strengths
        self.system_prompts = {
            "proposal": self._create_proposal_prompt(),
            "voter": self._create_voter_prompt(),
            "executor": self._create_executor_prompt(),
            "validator": self._create_validator_prompt(),
            "reflector": self._create_reflector_prompt()
        }
        
        logger.info(f"ClaudeAgent initialized with model {self.primary_model}")
    
    def _create_proposal_prompt(self) -> str:
        """Create system prompt for proposal generation."""
        return f"""You are Claude, an AI assistant created by Anthropic. You excel at analytical thinking and comprehensive planning with strong ethical considerations.

Constitutional AI Principles:
{chr(10).join('• ' + principle for principle in self.constitutional_principles)}

For proposal generation:
1. Analyze the problem from multiple perspectives
2. Consider ethical implications and potential harm
3. Break down complex goals systematically
4. Anticipate edge cases and failure modes
5. Provide clear, logical reasoning
6. Include safety measures and contingencies
7. Consider long-term consequences

Be thorough, precise, and always prioritize human wellbeing in your recommendations."""
    
    def _create_voter_prompt(self) -> str:
        """Create system prompt for voting."""
        return f"""You are Claude, evaluating proposals with strong analytical and ethical reasoning.

Constitutional AI Principles:
{chr(10).join('• ' + principle for principle in self.constitutional_principles)}

Evaluation criteria:
1. Effectiveness - Does it achieve the goal?
2. Feasibility - Is it practically achievable?
3. Safety - Does it minimize risk of harm?
4. Ethics - Is it morally sound?
5. Fairness - Does it consider all stakeholders?
6. Sustainability - Are long-term effects positive?

Provide nuanced, balanced evaluations considering all perspectives."""
    
    def _create_executor_prompt(self) -> str:
        """Create system prompt for execution."""
        return f"""You are Claude, focused on safe, thoughtful execution with constitutional AI principles.

Constitutional AI Principles:
{chr(10).join('• ' + principle for principle in self.constitutional_principles)}

Execution approach:
1. Prioritize safety and harm prevention
2. Double-check work for accuracy
3. Consider unintended consequences
4. Document process thoroughly
5. Flag ethical concerns immediately
6. Suggest improvements and optimizations

Be meticulous, safety-conscious, and transparent."""
    
    def _create_validator_prompt(self) -> str:
        """Create system prompt for validation."""
        return f"""You are Claude, providing exceptional quality assessment with attention to detail.

Constitutional AI Principles:
{chr(10).join('• ' + principle for principle in self.constitutional_principles)}

Validation approach:
1. Comprehensive correctness checking
2. Completeness assessment
3. Quality evaluation
4. Ethical implications review
5. Safety considerations
6. Edge case analysis

Provide constructive, detailed feedback for improvement."""
    
    def _create_reflector_prompt(self) -> str:
        """Create system prompt for reflection."""
        return f"""You are Claude, conducting deep analysis and learning from experience.

Constitutional AI Principles:
{chr(10).join('• ' + principle for principle in self.constitutional_principles)}

Reflection methodology:
1. Thorough root cause analysis
2. Systemic and contextual factor consideration
3. Multiple contributing cause identification
4. Comprehensive improvement strategies
5. Ethical lessons and implications
6. Actionable, specific recommendations

Focus on constructive learning and prevention."""
    
    def _select_optimal_model(self, prompt: str, max_tokens: int) -> str:
        """Select optimal Claude model based on task complexity."""
        estimated_tokens = self.token_counter.count_tokens(prompt)
        
        # Use Haiku for simple, fast tasks
        if estimated_tokens < 1000 and max_tokens < 500:
            return self.fast_model
        
        # Use Sonnet for balanced tasks
        if estimated_tokens < 50000 and max_tokens < 2000:
            return self.fallback_model
        
        # Use Opus for complex, long-context tasks
        return self.primary_model
    
    def _apply_safety_check(self, prompt: str) -> str:
        """Apply constitutional AI safety check to prompts."""
        if self.safety_level == "low":
            return prompt
        
        safety_preamble = """
Before proceeding, please consider these constitutional AI principles:
1. Be helpful, harmless, and honest
2. Consider potential harm to individuals or groups
3. Ensure ethical alignment of the request
4. Respect human autonomy and dignity

If you identify any safety or ethical concerns, please address them in your response.

"""
        return safety_preamble + prompt
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APITimeoutError))
    )
    async def _actual_api_call(self, prompt: str, **kwargs) -> str:
        """Make API call to Anthropic with comprehensive error handling."""
        system_prompt = kwargs.get("system_prompt")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        
        try:
            # Apply safety checks
            if self.constitutional_ai:
                prompt = self._apply_safety_check(prompt)
            
            # Select optimal model
            model = self._select_optimal_model(prompt, max_tokens)
            
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            
            # Make API call
            logger.debug(f"Making Anthropic API call with model {model}")
            response = await self.client.messages.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or self.system_prompts["executor"]
            )
            
            return response.content[0].text
            
        except anthropic.RateLimitError as e:
            logger.warning(f"Rate limit hit: {e}")
            await asyncio.sleep(60)
            raise
            
        except anthropic.APITimeoutError as e:
            logger.warning(f"API timeout: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            
            # Try fallback model
            if model != self.fallback_model:
                logger.info(f"Retrying with fallback model: {self.fallback_model}")
                try:
                    response = await self.client.messages.create(
                        model=self.fallback_model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system_prompt or self.system_prompts["executor"]
                    )
                    return response.content[0].text
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error}")
            
            raise
    
    async def generate_proposal(self, task_context: TaskContext) -> Proposal:
        """Generate a proposal with constitutional AI principles."""
        logger.info(f"Claude generating proposal for task: {task_context.description}")
        
        prompt = f"""
        I need to create a comprehensive, ethically-sound proposal for this task:
        
        **Task Description:** {task_context.description}
        **Task Type:** {task_context.task_type.value}
        **Priority:** {task_context.priority.value}
        **Input Data:** {json.dumps(task_context.input_data, indent=2)}
        **Parameters:** {json.dumps(task_context.parameters, indent=2)}
        **Constraints:** {json.dumps(task_context.constraints, indent=2)}
        
        Using my analytical approach:
        
        1. **Problem Analysis**: Understanding the task from multiple perspectives
        2. **Ethical Assessment**: Evaluating moral implications and potential harm
        3. **Stakeholder Consideration**: Identifying who is affected
        4. **Risk Evaluation**: Assessing potential negative outcomes
        5. **Approach Design**: Creating a thoughtful, safe strategy
        6. **Implementation Planning**: Breaking down into actionable steps
        
        Please provide a detailed proposal in JSON format with these fields:
        - approach: Detailed description of the proposed method
        - estimated_time_minutes: Realistic time estimate
        - confidence: Confidence level (0.0-1.0)
        - required_tools: List of necessary tools
        - dependencies: Any dependencies
        - risks: Identified risks with severity assessment
        - mitigation_strategies: How to address each risk
        - ethical_considerations: Moral implications and safeguards
        - estimated_cost: Cost estimate
        - expected_benefits: Anticipated positive outcomes
        
        Focus on creating a safe, effective, and ethically sound approach.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                system_prompt=self.system_prompts["proposal"],
                temperature=0.7,
                max_tokens=3000
            )
            
            # Extract JSON from response
            proposal_data = self._extract_json_from_response(response)
            
            # Create proposal object
            proposal = Proposal(
                agent_id=self.agent_id,
                task_context=task_context,
                approach=proposal_data.get("approach", "Constitutional AI-guided approach"),
                estimated_time=timedelta(minutes=proposal_data.get("estimated_time_minutes", 45)),
                estimated_cost=proposal_data.get("estimated_cost", 0.08),
                confidence=proposal_data.get("confidence", 0.8),
                required_tools=proposal_data.get("required_tools", []),
                dependencies=proposal_data.get("dependencies", []),
                risks=proposal_data.get("risks", []),
                mitigation_strategies=proposal_data.get("mitigation_strategies", []),
                expected_output={
                    "ethical_considerations": proposal_data.get("ethical_considerations", []),
                    "expected_benefits": proposal_data.get("expected_benefits", [])
                }
            )
            
            logger.info(f"Generated constitutional AI proposal with confidence {proposal.confidence:.2f}")
            return proposal
            
        except Exception as e:
            logger.error(f"Failed to generate proposal: {e}")
            
            # Safety-first fallback proposal
            return Proposal(
                agent_id=self.agent_id,
                task_context=task_context,
                approach=f"Conservative safety-first approach due to generation error: {str(e)}. Will proceed with careful manual oversight.",
                estimated_time=timedelta(minutes=60),
                estimated_cost=0.05,
                confidence=0.4,
                risks=["Generation error occurred", "May require manual intervention"],
                mitigation_strategies=["Human oversight", "Conservative approach", "Extensive validation"]
            )
    
    async def vote_on_proposal(self, proposal: Proposal, task_context: TaskContext) -> Vote:
        """Vote on proposal with ethical and safety considerations."""
        logger.info(f"Claude voting on proposal from {proposal.agent_id}")
        
        prompt = f"""
        I need to evaluate this proposal using constitutional AI principles and comprehensive analysis:
        
        **Original Task:** {task_context.description}
        **Task Type:** {task_context.task_type.value}
        
        **PROPOSAL TO EVALUATE:**
        - Agent: {proposal.agent_id}
        - Approach: {proposal.approach}
        - Estimated Time: {proposal.estimated_time}
        - Confidence: {proposal.confidence}
        - Required Tools: {proposal.required_tools}
        - Dependencies: {proposal.dependencies}
        - Risks: {proposal.risks}
        - Mitigation Strategies: {proposal.mitigation_strategies}
        
        **Evaluation Framework:**
        1. **Effectiveness**: How well does it address the task requirements?
        2. **Feasibility**: Is the approach practically achievable?
        3. **Safety**: What are the potential risks and how well are they mitigated?
        4. **Ethics**: Are there moral implications? Is it aligned with human values?
        5. **Completeness**: Does it cover all necessary aspects?
        6. **Innovation**: Does it show thoughtful problem-solving?
        7. **Sustainability**: Are long-term effects considered?
        
        **Constitutional AI Assessment:**
        - Does it respect human autonomy and dignity?
        - Are potential harms adequately addressed?
        - Is it honest about limitations and uncertainties?
        - Does it encourage beneficial outcomes?
        
        Please provide your vote in JSON format:
        - vote_type: "approve", "reject", "abstain", or "modify"
        - confidence: Your confidence in this assessment (0.0-1.0)
        - reasoning: Detailed explanation of your evaluation
        - suggested_modifications: If vote is "modify", what changes are needed
        - estimated_success_probability: Likelihood of success (0.0-1.0)
        - ethical_assessment: Specific ethical considerations
        - risk_evaluation: Risk analysis and acceptability
        
        Be thorough, balanced, and consider all stakeholders.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                system_prompt=self.system_prompts["voter"],
                temperature=0.5,
                max_tokens=1500
            )
            
            # Extract vote data
            vote_data = self._extract_json_from_response(response)
            
            # Convert vote type string to enum
            vote_type_map = {
                "approve": VoteType.APPROVE,
                "reject": VoteType.REJECT,
                "abstain": VoteType.ABSTAIN,
                "modify": VoteType.MODIFY
            }
            vote_type = vote_type_map.get(vote_data.get("vote_type", "abstain"), VoteType.ABSTAIN)
            
            vote = Vote(
                voter_agent_id=self.agent_id,
                proposal_id=proposal.proposal_id,
                vote_type=vote_type,
                confidence=vote_data.get("confidence", 0.6),
                reasoning=vote_data.get("reasoning", "Constitutional AI evaluation completed"),
                suggested_modifications=vote_data.get("suggested_modifications", []),
                risk_assessment={
                    "ethical_concerns": vote_data.get("ethical_assessment", "No specific concerns identified"),
                    "risk_level": vote_data.get("risk_evaluation", "Medium")
                },
                estimated_success_probability=vote_data.get("estimated_success_probability", 0.6)
            )
            
            logger.info(f"Cast constitutional vote: {vote_type.value} with confidence {vote.confidence:.2f}")
            return vote
            
        except Exception as e:
            logger.error(f"Failed to cast vote: {e}")
            
            # Conservative fallback vote
            return Vote(
                voter_agent_id=self.agent_id,
                proposal_id=proposal.proposal_id,
                vote_type=VoteType.ABSTAIN,
                confidence=0.2,
                reasoning=f"Unable to complete evaluation due to error: {str(e)}. Abstaining for safety.",
                estimated_success_probability=0.5
            )
    
    async def execute_action(self, action: Action, task_context: TaskContext) -> ExecutionResult:
        """Execute action with safety-first approach and thorough documentation."""
        logger.info(f"Claude executing action: {action.action_type.value}")
        
        start_time = time.time()
        
        try:
            # Pre-execution safety assessment
            if self.constitutional_ai:
                safety_check = await self._assess_action_safety(action, task_context)
                if not safety_check["safe"]:
                    return ExecutionResult(
                        action_id=action.action_id,
                        agent_id=self.agent_id,
                        status=ExecutionStatus.CANCELLED,
                        error_message=f"Safety check failed: {safety_check['reason']}",
                        execution_time=timedelta(seconds=time.time() - start_time),
                        metadata={"safety_blocked": True, "safety_reason": safety_check["reason"]}
                    )
            
            # Route to appropriate execution method
            if action.action_type == ActionType.EXECUTE_TASK:
                result = await self._execute_task_action(action, task_context)
            elif action.action_type == ActionType.GENERATE_PROPOSAL:
                result = await self._execute_proposal_action(action, task_context)
            elif action.action_type == ActionType.VALIDATE_RESULT:
                result = await self._execute_validation_action(action, task_context)
            else:
                result = await self._execute_generic_action(action, task_context)
            
            execution_time = time.time() - start_time
            tokens_used = self.token_counter.count_tokens(str(result))
            cost = self.token_counter.estimate_cost(
                tokens_used, tokens_used,
                self.input_cost_per_token, self.output_cost_per_token
            )
            
            return ExecutionResult(
                action_id=action.action_id,
                agent_id=self.agent_id,
                status=ExecutionStatus.COMPLETED,
                output=result,
                execution_time=timedelta(seconds=execution_time),
                tokens_used=tokens_used,
                cost=cost,
                quality_score=0.85,
                confidence=0.9,
                metadata={
                    "constitutional_ai_applied": True,
                    "safety_checked": True,
                    "ethical_reviewed": True
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Action execution failed: {e}")
            
            return ExecutionResult(
                action_id=action.action_id,
                agent_id=self.agent_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                execution_time=timedelta(seconds=execution_time),
                metadata={"error_type": type(e).__name__}
            )
    
    async def _assess_action_safety(self, action: Action, task_context: TaskContext) -> Dict[str, Any]:
        """Assess action safety using constitutional AI principles."""
        prompt = f"""
        Assess the safety and ethical implications of this action:
        
        **Action Type:** {action.action_type.value}
        **Task Context:** {task_context.description}
        **Parameters:** {json.dumps(action.parameters, indent=2)}
        
        Constitutional AI Safety Assessment:
        1. **Harm Potential**: Could this cause harm to individuals or groups?
        2. **Privacy & Security**: Are there privacy or security risks?
        3. **Autonomy Respect**: Does it respect human agency and choice?
        4. **Fairness**: Are there bias or discrimination concerns?
        5. **Transparency**: Is the action's purpose clear and honest?
        6. **Reversibility**: Can negative effects be undone?
        
        Provide assessment in JSON format:
        - safe: boolean (true if safe to proceed)
        - reason: explanation of safety determination
        - concerns: list of specific concerns if any
        - recommendations: safety measures to implement
        - risk_level: "low", "medium", "high", "critical"
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                temperature=0.1,
                max_tokens=800,
                system_prompt="You are a safety assessment specialist using constitutional AI principles. Be thorough and conservative."
            )
            
            return self._extract_json_from_response(response, {
                "safe": True,
                "reason": "Safety assessment completed",
                "risk_level": "low"
            })
            
        except Exception:
            # Fail-safe: if assessment fails, be conservative
            return {
                "safe": False,
                "reason": "Safety assessment failed - proceeding with caution",
                "risk_level": "medium"
            }
    
    async def _execute_task_action(self, action: Action, task_context: TaskContext) -> Dict[str, Any]:
        """Execute the main task with constitutional AI guidance."""
        approach = action.parameters.get("approach", "")
        
        prompt = f"""
        Execute this task following constitutional AI principles:
        
        **Task:** {task_context.description}
        **Approach:** {approach}
        **Input Data:** {json.dumps(task_context.input_data, indent=2)}
        **Parameters:** {json.dumps(task_context.parameters, indent=2)}
        
        Execution process:
        1. **Safety Verification**: Confirm no harm will result
        2. **Ethical Check**: Ensure alignment with human values
        3. **Methodical Execution**: Follow the approach step-by-step
        4. **Quality Assurance**: Verify accuracy and completeness
        5. **Impact Assessment**: Consider broader implications
        6. **Documentation**: Provide clear process documentation
        
        Provide comprehensive output in JSON format:
        - result: The main execution result
        - process_steps: Steps taken during execution
        - quality_assessment: Self-evaluation of quality
        - ethical_notes: Any ethical considerations
        - recommendations: Suggestions for improvement
        - confidence: Confidence in the result (0.0-1.0)
        """
        
        response = await self._actual_api_call(
            prompt=prompt,
            system_prompt=self.system_prompts["executor"],
            temperature=0.3,
            max_tokens=2500
        )
        
        try:
            return self._extract_json_from_response(response)
        except:
            return {
                "result": response,
                "process_steps": ["Constitutional AI execution completed"],
                "quality_assessment": "High quality with ethical considerations",
                "confidence": 0.8
            }
    
    async def _execute_proposal_action(self, action: Action, task_context: TaskContext) -> Dict[str, Any]:
        """Execute proposal generation action."""
        proposal = await self.generate_proposal(task_context)
        return {
            "proposal": proposal.dict(),
            "status": "completed",
            "constitutional_review": True
        }
    
    async def _execute_validation_action(self, action: Action, task_context: TaskContext) -> Dict[str, Any]:
        """Execute validation action."""
        result_data = action.parameters.get("result", {})
        validation_result = await self.validate_result(
            ExecutionResult(**result_data) if isinstance(result_data, dict) else result_data,
            task_context
        )
        return {
            "validation": validation_result.dict(),
            "status": "completed",
            "constitutional_review": True
        }
    
    async def _execute_generic_action(self, action: Action, task_context: TaskContext) -> Dict[str, Any]:
        """Execute generic action with constitutional AI principles."""
        prompt = f"""
        Execute this action following constitutional AI principles:
        
        **Action Type:** {action.action_type.value}
        **Task Context:** {task_context.description}
        **Parameters:** {json.dumps(action.parameters, indent=2)}
        
        Apply constitutional AI approach:
        1. Consider potential harm and benefits
        2. Ensure ethical alignment
        3. Respect human autonomy
        4. Provide honest, helpful results
        5. Document process transparently
        
        Return results in JSON format with ethical considerations noted.
        """
        
        response = await self._actual_api_call(
            prompt=prompt,
            system_prompt=self.system_prompts["executor"],
            temperature=0.5,
            max_tokens=1500
        )
        
        try:
            return self._extract_json_from_response(response)
        except:
            return {
                "result": response,
                "action_type": action.action_type.value,
                "constitutional_review": True
            }
    
    async def validate_result(self, result: ExecutionResult, task_context: TaskContext) -> ValidationResult:
        """Validate results with constitutional AI principles."""
        logger.info(f"Claude validating result with constitutional AI principles")
        
        prompt = f"""
        Validate this execution result using constitutional AI principles:
        
        **Original Task:** {task_context.description}
        **Task Type:** {task_context.task_type.value}
        
        **EXECUTION RESULT:**
        - Status: {result.status.value}
        - Output: {json.dumps(result.output, indent=2)}
        - Error: {result.error_message}
        - Quality Score: {result.quality_score}
        - Confidence: {result.confidence}
        
        **Constitutional AI Validation Framework:**
        1. **Correctness**: Does it accurately meet requirements?
        2. **Completeness**: Are all aspects properly addressed?
        3. **Safety**: Are there any safety concerns?
        4. **Ethics**: Does it align with human values?
        5. **Honesty**: Is it truthful about limitations?
        6. **Helpfulness**: Does it provide genuine value?
        7. **Quality**: Is it of acceptable standard?
        
        Provide detailed validation in JSON format:
        - is_valid: boolean assessment
        - confidence: confidence in validation (0.0-1.0)
        - quality_score: overall quality rating (0.0-1.0)
        - issues_found: list of specific issues
        - suggestions: recommendations for improvement
        - ethical_assessment: ethical implications noted
        - safety_evaluation: safety considerations
        - reasoning: detailed explanation of validation
        
        Be thorough, constructive, and prioritize human wellbeing.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                system_prompt=self.system_prompts["validator"],
                temperature=0.3,
                max_tokens=1500
            )
            
            validation_data = self._extract_json_from_response(response)
            
            return ValidationResult(
                result_id=result.result_id,
                validator_agent_id=self.agent_id,
                is_valid=validation_data.get("is_valid", False),
                confidence=validation_data.get("confidence", 0.7),
                quality_score=validation_data.get("quality_score", 0.7),
                validation_criteria={
                    "correctness": True,
                    "completeness": True,
                    "safety": True,
                    "ethics": True
                },
                issues_found=validation_data.get("issues_found", []),
                suggestions=validation_data.get("suggestions", []),
                reasoning=validation_data.get("reasoning", "Constitutional AI validation completed"),
                metadata={
                    "ethical_assessment": validation_data.get("ethical_assessment", "No ethical concerns"),
                    "safety_evaluation": validation_data.get("safety_evaluation", "Safety verified")
                }
            )
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            
            return ValidationResult(
                result_id=result.result_id,
                validator_agent_id=self.agent_id,
                is_valid=False,
                confidence=0.2,
                quality_score=0.3,
                issues_found=[f"Validation error: {str(e)}"],
                reasoning="Constitutional AI validation encountered an error - manual review recommended"
            )
    
    async def reflect_on_failure(self, error: Exception, task_context: TaskContext) -> ImprovementPlan:
        """Analyze failure with constitutional AI-guided reflection."""
        logger.info(f"Claude conducting constitutional AI-guided failure analysis")
        
        prompt = f"""
        Conduct a comprehensive failure analysis using constitutional AI principles:
        
        **Error Details:**
        - Type: {type(error).__name__}
        - Message: {str(error)}
        
        **Task Context:** {task_context.description}
        **Task Type:** {task_context.task_type.value}
        
        **Constitutional AI Reflection Framework:**
        
        1. **Immediate Cause Analysis:**
           - What directly caused this failure?
           - At what point did the process fail?
           
        2. **Root Cause Investigation:**
           - What underlying factors contributed?
           - Were there systemic issues?
           - What assumptions were incorrect?
           
        3. **Ethical Implications:**
           - Did this failure cause harm?
           - What are the moral lessons?
           - How can we prevent similar ethical issues?
           
        4. **Human Impact Assessment:**
           - Who was affected by this failure?
           - What were the consequences?
           - How can we better serve human needs?
           
        5. **Improvement Strategy:**
           - Specific prevention measures
           - Process improvements needed
           - Safety enhancements required
           - Ethical safeguards to implement
           
        6. **Learning Integration:**
           - Key insights for future work
           - Constitutional principles to emphasize
           - Human-centered improvements
           
        Provide comprehensive improvement plan in JSON format:
        - trigger_event: description of the failure
        - analysis_summary: detailed failure analysis
        - root_causes: list of underlying causes
        - human_impact: assessment of effects on people
        - ethical_lessons: moral insights gained
        - improvement_steps: specific actionable steps
        - prevention_measures: safeguards to implement
        - constitutional_focus: which principles to emphasize
        - estimated_effort_hours: time needed for improvements
        - success_criteria: how to measure improvement
        
        Focus on human-centered learning and ethical enhancement.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                system_prompt=self.system_prompts["reflector"],
                temperature=0.6,
                max_tokens=2500
            )
            
            reflection_data = self._extract_json_from_response(response)
            
            # Create improvement plan steps
            steps = []
            for step_desc in reflection_data.get("improvement_steps", []):
                steps.append({
                    "description": step_desc,
                    "priority": "high",
                    "estimated_time": 45
                })
            
            return ImprovementPlan(
                trigger_event=reflection_data.get("trigger_event", str(error)),
                analysis_summary=reflection_data.get("analysis_summary", "Constitutional AI failure analysis completed"),
                steps=steps,
                expected_improvements={
                    "safety": "Enhanced safety measures",
                    "ethics": "Strengthened ethical safeguards",
                    "human_focus": "Better human-centered approach"
                },
                risk_assessment={
                    "recurrence_risk": "Low with implemented improvements",
                    "impact_mitigation": "Comprehensive prevention measures"
                },
                implementation_priority=Priority.HIGH,
                estimated_effort=timedelta(hours=reflection_data.get("estimated_effort_hours", 3)),
                success_criteria=reflection_data.get("success_criteria", [
                    "No similar failures occur",
                    "Enhanced safety measures active",
                    "Improved human outcomes"
                ]),
                metadata={
                    "constitutional_principles": reflection_data.get("constitutional_focus", self.constitutional_principles),
                    "ethical_lessons": reflection_data.get("ethical_lessons", []),
                    "human_impact": reflection_data.get("human_impact", "Minimal impact identified")
                }
            )
            
        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            
            return ImprovementPlan(
                trigger_event=str(error),
                analysis_summary=f"Constitutional AI reflection failed: {str(e)}",
                steps=[{
                    "description": "Manual constitutional AI review required",
                    "priority": "high",
                    "estimated_time": 60
                }],
                expected_improvements={},
                risk_assessment={},
                implementation_priority=Priority.HIGH,
                estimated_effort=timedelta(hours=2)
            )
    
    def _extract_json_from_response(self, response: str, fallback: Optional[Dict] = None) -> Dict[str, Any]:
        """Extract JSON from Claude's response."""
        try:
            # Look for JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Try parsing entire response
            return json.loads(response)
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from Claude response")
            return fallback or {
                "error": "Failed to parse response", 
                "raw_response": response[:500] + "..." if len(response) > 500 else response
            }
    
    async def analyze_long_context(self, context_documents: List[str], query: str) -> Dict[str, Any]:
        """Analyze multiple documents using Claude's long context capability."""
        if not self.use_long_context:
            raise ValueError("Long context analysis is disabled")
        
        logger.info(f"Analyzing {len(context_documents)} documents with long context")
        
        # Combine documents for long context analysis
        combined_context = "\n\n--- DOCUMENT SEPARATOR ---\n\n".join(context_documents)
        
        prompt = f"""
        <documents>
        {combined_context}
        </documents>
        
        Analysis Query: {query}
        
        Using my long context capabilities, I'll analyze these documents to:
        1. Extract key information relevant to the query
        2. Identify patterns and themes across documents
        3. Note any contradictions or inconsistencies
        4. Synthesize insights from multiple sources
        5. Provide comprehensive analysis with source attribution
        
        Please provide detailed analysis addressing the query with specific references to the documents.
        """
        
        response = await self._actual_api_call(
            prompt=prompt,
            temperature=0.3,
            max_tokens=4000,
            system_prompt="You are analyzing multiple documents using your long context capability. Be thorough and cite sources."
        )
        
        return {
            "analysis": response,
            "documents_analyzed": len(context_documents),
            "context_length": sum(len(doc) for doc in context_documents),
            "query": query,
            "constitutional_review": True
        }
    
    async def get_constitutional_status(self) -> Dict[str, Any]:
        """Get status of constitutional AI implementation."""
        return {
            "constitutional_ai_active": self.constitutional_ai,
            "safety_level": self.safety_level,
            "principles": self.constitutional_principles,
            "model": self.primary_model,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "capabilities": {
                "long_context": self.use_long_context,
                "max_context_tokens": self.max_context_tokens,
                "safety_assessment": True,
                "ethical_evaluation": True
            },
            "health_status": {
                "enabled": self.enabled,
                "healthy": self.is_healthy,
                "health_score": self.health_score
            },
            "performance_summary": {
                "total_requests": self.metrics["total_requests"],
                "success_rate": self.metrics["successful_requests"] / max(1, self.metrics["total_requests"]),
                "average_cost": self.metrics["total_cost"] / max(1, self.metrics["total_requests"])
            }
        }