"""
OpenAI GPT agent implementation with complete BaseAgent methods.

This agent provides full integration with OpenAI's GPT models including
GPT-4, function calling, vision capabilities, and structured output parsing.
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from loguru import logger
from openai import AsyncOpenAI
from openai import RateLimitError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.agent_base import BaseAgent
from ..models.schemas import (
    AgentType, TaskType, ActionType, Priority, ExecutionStatus, VoteType,
    Proposal, Vote, Action, ExecutionResult, ValidationResult,
    TaskContext, AgentConfig, ImprovementPlan
)


class GPTAgent(BaseAgent):
    """
    OpenAI GPT agent with complete 1-3-1 workflow implementation.
    
    Features:
    - GPT-4 and GPT-3.5-turbo support
    - Function calling for structured outputs
    - Vision capabilities (GPT-4V)
    - Code interpreter integration
    - Cost optimization
    - Comprehensive error handling
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize GPT agent with OpenAI client."""
        super().__init__(config)
        
        # OpenAI client initialization
        self.api_key = config.metadata.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY env var or pass in config.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Model configuration
        self.primary_model = config.metadata.get("primary_model", "gpt-4")
        self.fallback_model = config.metadata.get("fallback_model", "gpt-3.5-turbo")
        self.vision_model = config.metadata.get("vision_model", "gpt-4-vision-preview")
        
        # Feature flags
        self.use_function_calling = config.metadata.get("use_function_calling", True)
        self.use_vision = config.metadata.get("use_vision", True)
        self.use_json_mode = config.metadata.get("use_json_mode", True)
        
        # Cost configuration (GPT-4 pricing as of 2024)
        self.input_cost_per_token = config.metadata.get("input_cost_per_token", 0.00003)
        self.output_cost_per_token = config.metadata.get("output_cost_per_token", 0.00006)
        
        # System prompts for different roles
        self.system_prompts = {
            "proposal": """You are an expert planning agent. Create detailed, actionable proposals that break down complex goals into specific steps. Consider all aspects including risks, dependencies, and resource requirements. Use systematic thinking and provide clear reasoning.""",
            
            "voter": """You are an expert evaluation agent. Objectively assess proposals using structured criteria: feasibility, completeness, efficiency, risk management, and innovation. Provide comparative analysis and detailed reasoning for your votes.""",
            
            "executor": """You are an expert execution agent. Execute tasks with precision and attention to detail. Focus on accuracy, proper error handling, and clear status reporting. Validate your work before completion.""",
            
            "validator": """You are an expert quality assurance agent. Thoroughly validate results against requirements. Be analytical and constructive, identifying both strengths and areas for improvement with specific feedback.""",
            
            "reflector": """You are an expert learning agent. Analyze failures systematically to identify root causes and create actionable improvement strategies. Focus on prevention and process enhancement."""
        }
        
        # Function definitions for structured outputs
        self.functions = self._initialize_functions()
        
        logger.info(f"GPTAgent initialized with model {self.primary_model}")
    
    def _initialize_functions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize OpenAI function definitions for structured outputs."""
        return {
            "create_proposal": {
                "name": "create_proposal",
                "description": "Create a structured proposal for achieving a goal",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "approach": {
                            "type": "string",
                            "description": "Detailed description of the proposed approach"
                        },
                        "estimated_time_minutes": {
                            "type": "integer",
                            "description": "Estimated time in minutes"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence level in the proposal"
                        },
                        "required_tools": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of tools required for execution"
                        },
                        "dependencies": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of dependencies"
                        },
                        "risks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Identified risks"
                        },
                        "mitigation_strategies": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Risk mitigation strategies"
                        },
                        "estimated_cost": {
                            "type": "number",
                            "minimum": 0.0,
                            "description": "Estimated cost in dollars"
                        }
                    },
                    "required": ["approach", "estimated_time_minutes", "confidence"]
                }
            },
            
            "cast_vote": {
                "name": "cast_vote",
                "description": "Vote on a proposal with detailed reasoning",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vote_type": {
                            "type": "string",
                            "enum": ["approve", "reject", "abstain", "modify"],
                            "description": "Type of vote"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence in the vote"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed reasoning for the vote"
                        },
                        "suggested_modifications": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Suggested modifications if vote is 'modify'"
                        },
                        "estimated_success_probability": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Estimated probability of success"
                        }
                    },
                    "required": ["vote_type", "confidence", "reasoning", "estimated_success_probability"]
                }
            },
            
            "validate_result": {
                "name": "validate_result",
                "description": "Validate execution results",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_valid": {
                            "type": "boolean",
                            "description": "Whether the result is valid"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence in validation"
                        },
                        "quality_score": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Quality score of the result"
                        },
                        "issues_found": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of issues found"
                        },
                        "suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Suggestions for improvement"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed reasoning for validation result"
                        }
                    },
                    "required": ["is_valid", "confidence", "quality_score", "reasoning"]
                }
            }
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError))
    )
    async def _actual_api_call(self, prompt: str, **kwargs) -> str:
        """Make API call to OpenAI with comprehensive error handling."""
        system_prompt = kwargs.get("system_prompt")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        functions = kwargs.get("functions")
        use_json = kwargs.get("use_json", False)
        images = kwargs.get("images")
        
        try:
            # Prepare messages
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Handle vision capabilities
            if images and self.use_vision:
                content = [{"type": "text", "text": prompt}]
                for image in images:
                    if isinstance(image, str) and image.startswith(('http', 'data:')):
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": image}
                        })
                messages.append({"role": "user", "content": content})
                model = self.vision_model
            else:
                messages.append({"role": "user", "content": prompt})
                model = self.primary_model
            
            # Prepare API parameters
            api_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Add JSON mode if requested
            if use_json and self.use_json_mode and "gpt-4" in model:
                api_params["response_format"] = {"type": "json_object"}
            
            # Add functions if provided
            if functions and self.use_function_calling:
                api_params["functions"] = functions
                api_params["function_call"] = "auto"
            
            # Make the API call
            logger.debug(f"Making OpenAI API call with model {model}")
            response = await self.client.chat.completions.create(**api_params)
            
            # Extract response
            if response.choices[0].message.function_call:
                function_call = response.choices[0].message.function_call
                return json.dumps({
                    "function_name": function_call.name,
                    "arguments": json.loads(function_call.arguments)
                })
            else:
                return response.choices[0].message.content or ""
                
        except RateLimitError as e:
            logger.warning(f"Rate limit hit: {e}")
            await asyncio.sleep(60)  # Wait 1 minute
            raise
            
        except APITimeoutError as e:
            logger.warning(f"API timeout: {e}")
            raise
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            
            # Try fallback model if different
            if model != self.fallback_model:
                logger.info(f"Retrying with fallback model: {self.fallback_model}")
                api_params["model"] = self.fallback_model
                try:
                    response = await self.client.chat.completions.create(**api_params)
                    return response.choices[0].message.content or ""
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error}")
            
            raise
    
    async def generate_proposal(self, task_context: TaskContext) -> Proposal:
        """Generate a proposal for the given task context."""
        logger.info(f"GPT generating proposal for task: {task_context.description}")
        
        prompt = f"""
        Create a comprehensive proposal to accomplish this task:
        
        **Task Description:** {task_context.description}
        **Task Type:** {task_context.task_type.value}
        **Priority:** {task_context.priority.value}
        **Input Data:** {json.dumps(task_context.input_data, indent=2)}
        **Parameters:** {json.dumps(task_context.parameters, indent=2)}
        **Constraints:** {json.dumps(task_context.constraints, indent=2)}
        
        Analyze the task thoroughly and create a detailed proposal including:
        1. A clear approach description
        2. Realistic time estimate
        3. Confidence assessment
        4. Required tools and dependencies
        5. Risk analysis with mitigation strategies
        6. Cost estimation
        
        Consider the task complexity, available resources, and potential challenges.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                system_prompt=self.system_prompts["proposal"],
                temperature=0.7,
                max_tokens=2000,
                functions=[self.functions["create_proposal"]]
            )
            
            # Parse function call response
            if response.startswith('{"function_name"'):
                function_data = json.loads(response)
                proposal_data = function_data["arguments"]
            else:
                # Fallback to JSON parsing
                proposal_data = json.loads(response)
            
            # Create proposal object
            proposal = Proposal(
                agent_id=self.agent_id,
                task_context=task_context,
                approach=proposal_data.get("approach", "GPT-based approach"),
                estimated_time=timedelta(minutes=proposal_data.get("estimated_time_minutes", 30)),
                estimated_cost=proposal_data.get("estimated_cost", 0.05),
                confidence=proposal_data.get("confidence", 0.7),
                required_tools=proposal_data.get("required_tools", []),
                dependencies=proposal_data.get("dependencies", []),
                risks=proposal_data.get("risks", []),
                mitigation_strategies=proposal_data.get("mitigation_strategies", [])
            )
            
            logger.info(f"Generated proposal with confidence {proposal.confidence:.2f}")
            return proposal
            
        except Exception as e:
            logger.error(f"Failed to generate proposal: {e}")
            
            # Return fallback proposal
            return Proposal(
                agent_id=self.agent_id,
                task_context=task_context,
                approach=f"Fallback proposal due to error: {str(e)}. Will attempt basic approach.",
                estimated_time=timedelta(minutes=30),
                estimated_cost=0.02,
                confidence=0.3,
                risks=["Generation error occurred"],
                mitigation_strategies=["Manual intervention may be required"]
            )
    
    async def vote_on_proposal(self, proposal: Proposal, task_context: TaskContext) -> Vote:
        """Vote on a proposal with detailed analysis."""
        logger.info(f"GPT voting on proposal from {proposal.agent_id}")
        
        prompt = f"""
        Evaluate this proposal for the task and cast your vote:
        
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
        
        Evaluate based on these criteria:
        1. **Feasibility**: How realistic and achievable is this approach?
        2. **Completeness**: Does it fully address the task requirements?
        3. **Efficiency**: Is it resource-efficient and well-planned?
        4. **Risk Management**: Are risks properly identified and mitigated?
        5. **Innovation**: Does it show creative problem-solving?
        
        Cast your vote (approve/reject/abstain/modify) and provide detailed reasoning.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                system_prompt=self.system_prompts["voter"],
                temperature=0.5,
                max_tokens=1000,
                functions=[self.functions["cast_vote"]]
            )
            
            # Parse vote response
            if response.startswith('{"function_name"'):
                function_data = json.loads(response)
                vote_data = function_data["arguments"]
            else:
                vote_data = json.loads(response)
            
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
                confidence=vote_data.get("confidence", 0.5),
                reasoning=vote_data.get("reasoning", "No reasoning provided"),
                suggested_modifications=vote_data.get("suggested_modifications", []),
                estimated_success_probability=vote_data.get("estimated_success_probability", 0.5)
            )
            
            logger.info(f"Cast vote: {vote_type.value} with confidence {vote.confidence:.2f}")
            return vote
            
        except Exception as e:
            logger.error(f"Failed to cast vote: {e}")
            
            # Return fallback vote
            return Vote(
                voter_agent_id=self.agent_id,
                proposal_id=proposal.proposal_id,
                vote_type=VoteType.ABSTAIN,
                confidence=0.1,
                reasoning=f"Error during voting: {str(e)}",
                estimated_success_probability=0.5
            )
    
    async def execute_action(self, action: Action, task_context: TaskContext) -> ExecutionResult:
        """Execute an action based on its type."""
        logger.info(f"GPT executing action: {action.action_type.value}")
        
        start_time = time.time()
        
        try:
            # Route to specific execution methods based on action type
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
                quality_score=0.8,
                confidence=0.9
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Action execution failed: {e}")
            
            return ExecutionResult(
                action_id=action.action_id,
                agent_id=self.agent_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                execution_time=timedelta(seconds=execution_time)
            )
    
    async def _execute_task_action(self, action: Action, task_context: TaskContext) -> Dict[str, Any]:
        """Execute the main task."""
        proposal_data = action.parameters.get("proposal", {})
        approach = action.parameters.get("approach", "")
        
        prompt = f"""
        Execute this task using the approved approach:
        
        **Task:** {task_context.description}
        **Approach:** {approach}
        **Input Data:** {json.dumps(task_context.input_data, indent=2)}
        **Parameters:** {json.dumps(task_context.parameters, indent=2)}
        
        Execute the task step by step following the approved approach.
        Provide detailed output including:
        - Results of execution
        - Any intermediate steps
        - Quality assessment
        - Completion status
        
        Return your response as JSON with: result, steps_completed, quality_notes, status
        """
        
        response = await self._actual_api_call(
            prompt=prompt,
            system_prompt=self.system_prompts["executor"],
            temperature=0.3,
            max_tokens=2000,
            use_json=True
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "result": response,
                "status": "completed",
                "quality_notes": "Direct text response"
            }
    
    async def _execute_proposal_action(self, action: Action, task_context: TaskContext) -> Dict[str, Any]:
        """Execute proposal generation action."""
        proposal = await self.generate_proposal(task_context)
        return {
            "proposal": proposal.dict(),
            "status": "completed",
            "confidence": proposal.confidence
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
            "status": "completed"
        }
    
    async def _execute_generic_action(self, action: Action, task_context: TaskContext) -> Dict[str, Any]:
        """Execute generic action types."""
        prompt = f"""
        Execute this action:
        
        **Action Type:** {action.action_type.value}
        **Parameters:** {json.dumps(action.parameters, indent=2)}
        **Context:** {task_context.description}
        
        Provide appropriate execution based on the action type and parameters.
        Return results as JSON with relevant fields for this action type.
        """
        
        response = await self._actual_api_call(
            prompt=prompt,
            system_prompt=self.system_prompts["executor"],
            temperature=0.5,
            max_tokens=1500,
            use_json=True
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "result": response,
                "action_type": action.action_type.value,
                "status": "completed"
            }
    
    async def validate_result(self, result: ExecutionResult, task_context: TaskContext) -> ValidationResult:
        """Validate execution results."""
        logger.info(f"GPT validating result for action {result.action_id}")
        
        prompt = f"""
        Validate this execution result against the task requirements:
        
        **Original Task:** {task_context.description}
        **Expected Outcome:** Based on task type {task_context.task_type.value}
        
        **EXECUTION RESULT:**
        - Status: {result.status.value}
        - Output: {json.dumps(result.output, indent=2)}
        - Error: {result.error_message}
        - Quality Score: {result.quality_score}
        - Confidence: {result.confidence}
        
        Validate based on:
        1. **Correctness**: Does the result meet the task requirements?
        2. **Completeness**: Are all aspects of the task addressed?
        3. **Quality**: Is the output of acceptable quality?
        4. **Accuracy**: Are there any errors or inconsistencies?
        
        Provide detailed validation with specific feedback.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                system_prompt=self.system_prompts["validator"],
                temperature=0.3,
                max_tokens=1000,
                functions=[self.functions["validate_result"]]
            )
            
            # Parse validation response
            if response.startswith('{"function_name"'):
                function_data = json.loads(response)
                validation_data = function_data["arguments"]
            else:
                validation_data = json.loads(response)
            
            return ValidationResult(
                result_id=result.result_id,
                validator_agent_id=self.agent_id,
                is_valid=validation_data.get("is_valid", False),
                confidence=validation_data.get("confidence", 0.5),
                quality_score=validation_data.get("quality_score", 0.5),
                issues_found=validation_data.get("issues_found", []),
                suggestions=validation_data.get("suggestions", []),
                reasoning=validation_data.get("reasoning", "No detailed reasoning provided")
            )
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            
            return ValidationResult(
                result_id=result.result_id,
                validator_agent_id=self.agent_id,
                is_valid=False,
                confidence=0.1,
                quality_score=0.0,
                issues_found=[f"Validation error: {str(e)}"],
                reasoning="Failed to perform validation due to technical error"
            )
    
    async def reflect_on_failure(self, error: Exception, task_context: TaskContext) -> ImprovementPlan:
        """Analyze failure and create improvement plan."""
        logger.info(f"GPT reflecting on failure: {type(error).__name__}")
        
        prompt = f"""
        Analyze this failure and create an improvement plan:
        
        **Error:** {str(error)}
        **Error Type:** {type(error).__name__}
        **Task Context:** {task_context.description}
        **Task Type:** {task_context.task_type.value}
        
        Perform systematic failure analysis:
        1. **Root Cause**: What exactly caused this failure?
        2. **Contributing Factors**: What conditions led to this issue?
        3. **Impact Assessment**: How severe is this failure?
        4. **Prevention**: How can we prevent this in the future?
        5. **Process Improvement**: What process changes are needed?
        
        Create specific, actionable improvement recommendations.
        
        Return JSON with: trigger_event, analysis_summary, steps, expected_improvements, 
        risk_assessment, implementation_priority, estimated_effort_hours
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                system_prompt=self.system_prompts["reflector"],
                temperature=0.6,
                max_tokens=1500,
                use_json=True
            )
            
            reflection_data = json.loads(response)
            
            # Create improvement plan steps (simplified for this implementation)
            steps = []
            for step_desc in reflection_data.get("steps", []):
                steps.append({
                    "description": step_desc,
                    "priority": "high",
                    "estimated_time": 30
                })
            
            return ImprovementPlan(
                trigger_event=reflection_data.get("trigger_event", str(error)),
                analysis_summary=reflection_data.get("analysis_summary", ""),
                steps=steps,
                expected_improvements=reflection_data.get("expected_improvements", {}),
                risk_assessment=reflection_data.get("risk_assessment", {}),
                implementation_priority=Priority.HIGH,
                estimated_effort=timedelta(hours=reflection_data.get("estimated_effort_hours", 2))
            )
            
        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            
            return ImprovementPlan(
                trigger_event=str(error),
                analysis_summary=f"Failed to analyze error: {str(e)}",
                steps=[{
                    "description": "Manual investigation required",
                    "priority": "high",
                    "estimated_time": 60
                }],
                expected_improvements={},
                risk_assessment={},
                implementation_priority=Priority.HIGH,
                estimated_effort=timedelta(hours=1)
            )
    
    async def analyze_image(self, image_url: str, description: str) -> str:
        """Analyze images using GPT-4 Vision."""
        if not self.use_vision:
            raise ValueError("Vision capability is disabled for this agent")
        
        logger.info("GPT analyzing image with vision capability")
        
        prompt = f"""
        Analyze this image and provide detailed insights:
        
        **Analysis Request:** {description}
        
        Please provide:
        - Detailed description of what you see
        - Key elements and features
        - Any relevant observations
        - Answers to specific questions if provided
        
        Be thorough and accurate in your analysis.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1000,
                images=[image_url]
            )
            
            logger.info("Image analysis completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return f"Failed to analyze image: {str(e)}"
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get current agent capabilities and configuration."""
        return {
            "agent_type": self.agent_type.value,
            "agent_id": self.agent_id,
            "model": self.primary_model,
            "fallback_model": self.fallback_model,
            "vision_model": self.vision_model,
            "capabilities": list(self.capabilities.capabilities),
            "specializations": [spec.value for spec in self.capabilities.specializations],
            "features": {
                "function_calling": self.use_function_calling,
                "vision_analysis": self.use_vision,
                "json_mode": self.use_json_mode
            },
            "health_status": {
                "enabled": self.enabled,
                "healthy": self.is_healthy,
                "health_score": self.health_score,
                "consecutive_failures": self.consecutive_failures
            },
            "performance": {
                "total_requests": self.metrics["total_requests"],
                "success_rate": self.metrics["successful_requests"] / max(1, self.metrics["total_requests"]),
                "average_response_time": self.metrics["average_response_time"],
                "total_cost": self.metrics["total_cost"]
            }
        }