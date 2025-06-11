"""
Google Gemini agent implementation with multimodal capabilities.

This agent integrates with Google's Gemini models and provides
multimodal understanding, fast processing, and creative problem-solving.
"""

import asyncio
import json
import os
import re
import time
import hashlib
import base64
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from loguru import logger
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.agent_base import BaseAgent
from ..models.schemas import (
    AgentType, TaskType, ActionType, Priority, ExecutionStatus, VoteType,
    Proposal, Vote, Action, ExecutionResult, ValidationResult,
    TaskContext, AgentConfig, ImprovementPlan
)


class GeminiAgent(BaseAgent):
    """
    Google Gemini agent with multimodal capabilities and rapid processing.
    
    Features:
    - Gemini Pro, Pro Vision, and Ultra support
    - Multimodal understanding (text, images, code)
    - Fast iteration and creative problem-solving
    - Mathematical computation capabilities
    - Multilingual support
    - Safety filters and content moderation
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize Gemini agent with Google AI client."""
        super().__init__(config)
        
        # Google AI client initialization
        self.api_key = config.metadata.get("api_key") or os.getenv("GOOGLE_AI_API_KEY")
        if not self.api_key:
            raise ValueError("Google AI API key is required. Set GOOGLE_AI_API_KEY env var or pass in config.")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Model configuration
        self.primary_model = config.metadata.get("primary_model", "gemini-1.5-pro")
        self.vision_model = config.metadata.get("vision_model", "gemini-1.5-pro")
        self.ultra_model = config.metadata.get("ultra_model", "gemini-1.5-pro")
        
        # Initialize model instances
        self.model = genai.GenerativeModel(self.primary_model)
        self.vision_model_instance = genai.GenerativeModel(self.vision_model) if self.vision_model else None
        
        # Feature flags
        self.use_vision = config.metadata.get("use_vision", True)
        self.use_search = config.metadata.get("use_search", False)
        self.batch_processing = config.metadata.get("batch_processing", True)
        self.enable_caching = config.metadata.get("enable_caching", True)
        
        # Cost configuration (Gemini pricing as of 2024)
        self.input_cost_per_token = config.metadata.get("input_cost_per_token", 0.00000125)
        self.output_cost_per_token = config.metadata.get("output_cost_per_token", 0.00000375)
        
        # Safety settings for content moderation
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        # Generation configuration
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        # Response cache for optimization
        self.response_cache = {} if self.enable_caching else None
        self.cache_ttl = config.metadata.get("cache_ttl", 3600)  # 1 hour
        
        # Creative problem-solving patterns
        self.creative_patterns = {
            "divergent_thinking": "Explore multiple creative angles and unconventional approaches",
            "rapid_prototyping": "Focus on quick iteration and learning from feedback",
            "systems_thinking": "Consider holistic relationships and leverage points",
            "analogical_reasoning": "Draw insights from similar problems in other domains"
        }
        
        logger.info(f"GeminiAgent initialized with model {self.primary_model}")
    
    def _get_cache_key(self, prompt: str, config: Dict[str, Any]) -> str:
        """Generate cache key for response caching."""
        content = f"{prompt}_{json.dumps(config, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - timestamp < self.cache_ttl
    
    def _check_cache(self, cache_key: str) -> Optional[str]:
        """Check cache for existing response."""
        if not self.enable_caching or not self.response_cache:
            return None
        
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            if self._is_cache_valid(cached_data["timestamp"]):
                logger.debug(f"Cache hit for key: {cache_key[:8]}...")
                return cached_data["response"]
            else:
                del self.response_cache[cache_key]
        
        return None
    
    def _store_cache(self, cache_key: str, response: str):
        """Store response in cache."""
        if self.enable_caching and self.response_cache is not None:
            self.response_cache[cache_key] = {
                "response": response,
                "timestamp": time.time()
            }
    
    def _select_creative_approach(self, task_description: str) -> str:
        """Select appropriate creative approach based on task."""
        desc_lower = task_description.lower()
        
        if any(word in desc_lower for word in ["quick", "fast", "rapid", "immediate"]):
            return "rapid_prototyping"
        elif any(word in desc_lower for word in ["system", "complex", "integration", "holistic"]):
            return "systems_thinking"
        elif any(word in desc_lower for word in ["creative", "innovative", "novel", "unique"]):
            return "divergent_thinking"
        else:
            return "analogical_reasoning"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _actual_api_call(self, prompt: str, **kwargs) -> str:
        """Make API call to Google Gemini with comprehensive error handling."""
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        use_vision = kwargs.get("use_vision", False)
        images = kwargs.get("images", [])
        
        try:
            # Prepare generation config
            config = self.generation_config.copy()
            config.update({
                "temperature": temperature,
                "max_output_tokens": max_tokens
            })
            
            # Check cache first
            cache_key = self._get_cache_key(prompt, config)
            cached_response = self._check_cache(cache_key)
            if cached_response:
                return cached_response
            
            # Prepare content
            content = [prompt]
            
            # Add images for multimodal tasks
            if use_vision and images and self.use_vision and self.vision_model_instance:
                for image in images:
                    if isinstance(image, str):
                        # Handle image URLs or base64
                        if image.startswith(('http', 'data:')):
                            content.append(image)
                    else:
                        # Handle other image formats
                        content.append(image)
                
                model = self.vision_model_instance
            else:
                model = self.model
            
            # Generate response
            logger.debug(f"Making Gemini API call with model {model.model_name}")
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(
                    content,
                    generation_config=config,
                    safety_settings=self.safety_settings
                )
            )
            
            # Extract text from response
            response_text = response.text
            
            # Store in cache
            self._store_cache(cache_key, response_text)
            
            return response_text
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            
            # Try with reduced temperature for stability
            if temperature > 0.3:
                logger.info("Retrying with lower temperature for stability")
                return await self._actual_api_call(
                    prompt, 
                    temperature=0.3, 
                    max_tokens=max_tokens,
                    use_vision=use_vision,
                    images=images
                )
            
            raise
    
    async def generate_proposal(self, task_context: TaskContext) -> Proposal:
        """Generate creative proposal using Gemini's innovation capabilities."""
        logger.info(f"Gemini generating creative proposal for task: {task_context.description}")
        
        # Select creative approach
        creative_approach = self._select_creative_approach(task_context.description)
        
        prompt = f"""
        I need to create an innovative proposal using {creative_approach} methodology:
        
        **Task Description:** {task_context.description}
        **Task Type:** {task_context.task_type.value}
        **Priority:** {task_context.priority.value}
        **Input Data:** {json.dumps(task_context.input_data, indent=2)}
        **Parameters:** {json.dumps(task_context.parameters, indent=2)}
        **Constraints:** {json.dumps(task_context.constraints, indent=2)}
        
        **Creative Methodology - {creative_approach}:**
        {self.creative_patterns[creative_approach]}
        
        **Innovation Framework:**
        1. **Divergent Exploration**: What are 3 unconventional approaches?
        2. **Technology Integration**: How can emerging tech enhance this?
        3. **Cross-Domain Insights**: What can other fields teach us?
        4. **Rapid Iteration**: How can we prototype and learn quickly?
        5. **Multimodal Thinking**: How can we leverage different data types?
        
        **Implementation Focus:**
        - Fast execution and quick wins
        - Adaptable and scalable solutions
        - Creative use of available resources
        - Innovation through constraints
        
        Please provide a detailed proposal in JSON format:
        - approach: Innovative description of the method
        - estimated_time_minutes: Realistic time estimate (favor speed)
        - confidence: Confidence level (0.0-1.0)
        - required_tools: List of tools needed
        - dependencies: Any dependencies
        - risks: Identified risks
        - mitigation_strategies: How to address risks
        - innovation_score: How innovative is this (0.0-1.0)
        - rapid_iteration: How quickly can we iterate
        - multimodal_potential: Can this work with different data types
        - estimated_cost: Cost estimate
        
        Focus on creative, fast-to-implement solutions with high innovation potential.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                temperature=0.8,  # Higher temperature for creativity
                max_tokens=2500
            )
            
            # Extract JSON from response
            proposal_data = self._extract_json_from_response(response)
            
            # Create proposal object
            proposal = Proposal(
                agent_id=self.agent_id,
                task_context=task_context,
                approach=proposal_data.get("approach", "Gemini creative approach"),
                estimated_time=timedelta(minutes=proposal_data.get("estimated_time_minutes", 30)),
                estimated_cost=proposal_data.get("estimated_cost", 0.03),
                confidence=proposal_data.get("confidence", 0.75),
                required_tools=proposal_data.get("required_tools", []),
                dependencies=proposal_data.get("dependencies", []),
                risks=proposal_data.get("risks", []),
                mitigation_strategies=proposal_data.get("mitigation_strategies", []),
                expected_output={
                    "innovation_score": proposal_data.get("innovation_score", 0.8),
                    "rapid_iteration": proposal_data.get("rapid_iteration", "High potential"),
                    "multimodal_potential": proposal_data.get("multimodal_potential", "Moderate"),
                    "creative_methodology": creative_approach
                }
            )
            
            logger.info(f"Generated creative proposal with innovation score {proposal_data.get('innovation_score', 0.8):.2f}")
            return proposal
            
        except Exception as e:
            logger.error(f"Failed to generate proposal: {e}")
            
            # Rapid fallback proposal
            return Proposal(
                agent_id=self.agent_id,
                task_context=task_context,
                approach=f"Rapid iteration approach due to generation error: {str(e)}. Will use quick prototyping and fast feedback loops.",
                estimated_time=timedelta(minutes=25),
                estimated_cost=0.02,
                confidence=0.6,
                risks=["Generation error", "Limited by fallback approach"],
                mitigation_strategies=["Quick validation", "Rapid pivoting", "Fast learning cycles"]
            )
    
    async def vote_on_proposal(self, proposal: Proposal, task_context: TaskContext) -> Vote:
        """Vote on proposal with rapid assessment and innovation focus."""
        logger.info(f"Gemini voting on proposal from {proposal.agent_id}")
        
        prompt = f"""
        I need to rapidly evaluate this proposal with focus on innovation and practicality:
        
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
        
        **Rapid Evaluation Framework:**
        1. **Innovation Potential** (0.0-1.0): How creative and novel is this?
        2. **Speed to Value** (0.0-1.0): How quickly can this deliver results?
        3. **Adaptability** (0.0-1.0): How flexible is this approach?
        4. **Resource Efficiency** (0.0-1.0): How well does it use resources?
        5. **Scalability** (0.0-1.0): How well can this scale up?
        6. **Risk Management** (0.0-1.0): How well are risks addressed?
        
        **Multimodal Considerations:**
        - Can this work with different types of data/input?
        - Does it leverage multiple capabilities effectively?
        - How robust is it across different contexts?
        
        **Innovation Bias:**
        I tend to favor approaches that show creativity, rapid iteration potential,
        and innovative thinking, while still being practical and achievable.
        
        Please provide your vote in JSON format:
        - vote_type: "approve", "reject", "abstain", or "modify"
        - confidence: Confidence in this assessment (0.0-1.0)
        - reasoning: Detailed explanation of evaluation
        - suggested_modifications: If vote is "modify", what changes needed
        - estimated_success_probability: Likelihood of success (0.0-1.0)
        - innovation_assessment: How innovative is this approach
        - speed_assessment: How fast can this be implemented
        
        Balance innovation with practicality, favoring creative but achievable approaches.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                temperature=0.6,
                max_tokens=1200
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
            vote_type = vote_type_map.get(vote_data.get("vote_type", "approve"), VoteType.APPROVE)
            
            vote = Vote(
                voter_agent_id=self.agent_id,
                proposal_id=proposal.proposal_id,
                vote_type=vote_type,
                confidence=vote_data.get("confidence", 0.7),
                reasoning=vote_data.get("reasoning", "Gemini rapid evaluation completed"),
                suggested_modifications=vote_data.get("suggested_modifications", []),
                risk_assessment={
                    "innovation_level": vote_data.get("innovation_assessment", "High"),
                    "implementation_speed": vote_data.get("speed_assessment", "Fast")
                },
                estimated_success_probability=vote_data.get("estimated_success_probability", 0.7)
            )
            
            logger.info(f"Cast rapid vote: {vote_type.value} with confidence {vote.confidence:.2f}")
            return vote
            
        except Exception as e:
            logger.error(f"Failed to cast vote: {e}")
            
            # Optimistic fallback vote (Gemini tends to be positive about innovation)
            return Vote(
                voter_agent_id=self.agent_id,
                proposal_id=proposal.proposal_id,
                vote_type=VoteType.APPROVE,
                confidence=0.6,
                reasoning=f"Rapid assessment with optimistic bias due to error: {str(e)}. Favoring innovation and rapid iteration.",
                estimated_success_probability=0.7
            )
    
    async def execute_action(self, action: Action, task_context: TaskContext) -> ExecutionResult:
        """Execute action with multimodal capabilities and rapid processing."""
        logger.info(f"Gemini executing action: {action.action_type.value}")
        
        start_time = time.time()
        
        try:
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
                quality_score=0.8,
                confidence=0.85,
                metadata={
                    "gemini_processing": True,
                    "rapid_execution": True,
                    "multimodal_ready": self.use_vision
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
                metadata={"error_type": type(e).__name__, "retry_recommended": True}
            )
    
    async def _execute_task_action(self, action: Action, task_context: TaskContext) -> Dict[str, Any]:
        """Execute the main task with rapid processing."""
        approach = action.parameters.get("approach", "")
        
        prompt = f"""
        Execute this task using Gemini's rapid processing and creative capabilities:
        
        **Task:** {task_context.description}
        **Approach:** {approach}
        **Input Data:** {json.dumps(task_context.input_data, indent=2)}
        **Parameters:** {json.dumps(task_context.parameters, indent=2)}
        
        **Execution Strategy:**
        1. **Rapid Analysis**: Quickly understand the requirements
        2. **Creative Implementation**: Apply innovative solutions
        3. **Quality Focus**: Ensure accuracy and completeness
        4. **Iteration Ready**: Design for quick refinement
        5. **Multimodal Integration**: Consider different data types
        
        **Gemini Strengths:**
        - Fast processing and quick results
        - Creative problem-solving approaches
        - Multimodal understanding capabilities
        - Mathematical and analytical computation
        - Rapid iteration and learning
        
        Provide comprehensive output in JSON format:
        - result: The main execution result
        - methodology: How you approached this
        - quality_indicators: Self-assessment of quality
        - iteration_potential: How this can be improved
        - multimodal_opportunities: Ways to enhance with other data types
        - performance_metrics: Speed and efficiency indicators
        - confidence: Confidence in the result (0.0-1.0)
        """
        
        response = await self._actual_api_call(
            prompt=prompt,
            temperature=0.4,
            max_tokens=2000
        )
        
        try:
            return self._extract_json_from_response(response)
        except:
            return {
                "result": response,
                "methodology": "Rapid Gemini processing",
                "quality_indicators": "High-speed execution with creative elements",
                "confidence": 0.8
            }
    
    async def _execute_proposal_action(self, action: Action, task_context: TaskContext) -> Dict[str, Any]:
        """Execute proposal generation action."""
        proposal = await self.generate_proposal(task_context)
        return {
            "proposal": proposal.dict(),
            "status": "completed",
            "creative_processing": True
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
            "rapid_assessment": True
        }
    
    async def _execute_generic_action(self, action: Action, task_context: TaskContext) -> Dict[str, Any]:
        """Execute generic action with creative optimization."""
        prompt = f"""
        Execute this action using Gemini's creative and rapid processing:
        
        **Action Type:** {action.action_type.value}
        **Task Context:** {task_context.description}
        **Parameters:** {json.dumps(action.parameters, indent=2)}
        
        **Creative Execution Approach:**
        1. Rapid understanding and analysis
        2. Creative solution generation
        3. Efficient implementation
        4. Quality optimization
        5. Future adaptability consideration
        
        Provide results with innovation and speed focus in JSON format.
        """
        
        response = await self._actual_api_call(
            prompt=prompt,
            temperature=0.6,
            max_tokens=1200
        )
        
        try:
            return self._extract_json_from_response(response)
        except:
            return {
                "result": response,
                "action_type": action.action_type.value,
                "gemini_optimized": True
            }
    
    async def validate_result(self, result: ExecutionResult, task_context: TaskContext) -> ValidationResult:
        """Validate results with rapid assessment and innovation consideration."""
        logger.info(f"Gemini validating result with rapid assessment")
        
        prompt = f"""
        Rapidly validate this execution result with focus on innovation and quality:
        
        **Original Task:** {task_context.description}
        **Task Type:** {task_context.task_type.value}
        
        **EXECUTION RESULT:**
        - Status: {result.status.value}
        - Output: {json.dumps(result.output, indent=2)}
        - Error: {result.error_message}
        - Quality Score: {result.quality_score}
        - Confidence: {result.confidence}
        - Execution Time: {result.execution_time}
        
        **Rapid Validation Framework:**
        1. **Correctness**: Does it meet the requirements accurately?
        2. **Completeness**: Are all aspects properly addressed?
        3. **Quality**: Is it of professional standard?
        4. **Innovation**: Does it show creative elements?
        5. **Efficiency**: Was execution reasonably fast?
        6. **Adaptability**: Can this be easily modified or extended?
        
        **Innovation Bonus Points:**
        - Creative approaches or solutions
        - Efficient use of resources
        - Adaptable and extensible design
        - Multimodal integration potential
        
        **Gemini Assessment Style:**
        - Rapid but thorough evaluation
        - Positive bias toward innovation
        - Focus on practical value
        - Speed and quality balance
        
        Provide detailed validation in JSON format:
        - is_valid: boolean assessment
        - confidence: confidence in validation (0.0-1.0)
        - quality_score: overall quality rating (0.0-1.0)
        - issues_found: list of specific issues
        - suggestions: recommendations for improvement
        - innovation_score: how innovative is the result (0.0-1.0)
        - efficiency_rating: how efficient was execution (0.0-1.0)
        - reasoning: detailed explanation
        
        Be thorough but rapid, with positive bias toward creative solutions.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1200
            )
            
            validation_data = self._extract_json_from_response(response)
            
            return ValidationResult(
                result_id=result.result_id,
                validator_agent_id=self.agent_id,
                is_valid=validation_data.get("is_valid", True),
                confidence=validation_data.get("confidence", 0.75),
                quality_score=validation_data.get("quality_score", 0.8),
                validation_criteria={
                    "correctness": True,
                    "innovation": True,
                    "efficiency": True
                },
                issues_found=validation_data.get("issues_found", []),
                suggestions=validation_data.get("suggestions", []),
                reasoning=validation_data.get("reasoning", "Gemini rapid validation completed"),
                metadata={
                    "innovation_score": validation_data.get("innovation_score", 0.7),
                    "efficiency_rating": validation_data.get("efficiency_rating", 0.8),
                    "validation_speed": "rapid"
                }
            )
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            
            return ValidationResult(
                result_id=result.result_id,
                validator_agent_id=self.agent_id,
                is_valid=False,
                confidence=0.4,
                quality_score=0.5,
                issues_found=[f"Validation error: {str(e)}"],
                reasoning="Gemini validation encountered an error - recommend manual review"
            )
    
    async def reflect_on_failure(self, error: Exception, task_context: TaskContext) -> ImprovementPlan:
        """Analyze failure with rapid learning and creative solutions."""
        logger.info(f"Gemini conducting rapid failure analysis with creative solutions")
        
        prompt = f"""
        Conduct rapid failure analysis with creative improvement solutions:
        
        **Error Details:**
        - Type: {type(error).__name__}
        - Message: {str(error)}
        
        **Task Context:** {task_context.description}
        **Task Type:** {task_context.task_type.value}
        
        **Rapid Learning Framework:**
        
        1. **Quick Diagnosis:**
           - What immediately caused this failure?
           - What was the specific breakdown point?
           
        2. **Pattern Recognition:**
           - Is this a known failure pattern?
           - What similar issues have we seen?
           
        3. **Creative Solutions:**
           - What innovative approaches could prevent this?
           - How can we turn this failure into an advantage?
           - What creative monitoring or safeguards can help?
           
        4. **Rapid Implementation:**
           - What can be fixed immediately?
           - What quick wins are available?
           - How can we iterate rapidly to improve?
           
        5. **Innovation Opportunities:**
           - How can this failure inspire better solutions?
           - What new capabilities could prevent similar issues?
           - How can we make the system more adaptive?
           
        **Gemini's Rapid Learning Style:**
        - Fast analysis and quick insights
        - Creative and innovative solutions
        - Practical and implementable recommendations
        - Positive focus on learning and improvement
        
        Provide comprehensive improvement plan in JSON format:
        - trigger_event: description of the failure
        - analysis_summary: rapid analysis of what happened
        - root_causes: underlying causes identified
        - creative_solutions: innovative approaches to fix this
        - rapid_improvements: quick wins that can be implemented now
        - innovation_opportunities: ways this can lead to better solutions
        - prevention_measures: safeguards to implement
        - estimated_effort_hours: time needed for improvements
        - success_criteria: how to measure improvement
        - learning_potential: what this teaches us
        
        Focus on rapid learning, creative solutions, and positive outcomes.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            reflection_data = self._extract_json_from_response(response)
            
            # Create improvement plan steps
            steps = []
            for solution in reflection_data.get("creative_solutions", []):
                steps.append({
                    "description": solution,
                    "priority": "high",
                    "estimated_time": 30
                })
            
            # Add rapid improvements
            for improvement in reflection_data.get("rapid_improvements", []):
                steps.append({
                    "description": improvement,
                    "priority": "immediate",
                    "estimated_time": 15
                })
            
            return ImprovementPlan(
                trigger_event=reflection_data.get("trigger_event", str(error)),
                analysis_summary=reflection_data.get("analysis_summary", "Gemini rapid failure analysis completed"),
                steps=steps,
                expected_improvements={
                    "innovation": "Creative solutions implemented",
                    "speed": "Rapid implementation and learning",
                    "adaptability": "Enhanced system flexibility"
                },
                risk_assessment={
                    "recurrence_probability": "Low with creative solutions",
                    "impact_severity": "Minimized through rapid response"
                },
                implementation_priority=Priority.HIGH,
                estimated_effort=timedelta(hours=reflection_data.get("estimated_effort_hours", 2)),
                success_criteria=reflection_data.get("success_criteria", [
                    "No similar failures occur",
                    "Improved system adaptability",
                    "Enhanced error prevention"
                ]),
                metadata={
                    "creative_solutions": reflection_data.get("creative_solutions", []),
                    "innovation_opportunities": reflection_data.get("innovation_opportunities", []),
                    "learning_potential": reflection_data.get("learning_potential", "High")
                }
            )
            
        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            
            return ImprovementPlan(
                trigger_event=str(error),
                analysis_summary=f"Gemini reflection failed: {str(e)}",
                steps=[{
                    "description": "Manual creative analysis required",
                    "priority": "high",
                    "estimated_time": 45
                }],
                expected_improvements={},
                risk_assessment={},
                implementation_priority=Priority.HIGH,
                estimated_effort=timedelta(hours=1.5)
            )
    
    def _extract_json_from_response(self, response: str, fallback: Optional[Dict] = None) -> Dict[str, Any]:
        """Extract JSON from Gemini's response."""
        try:
            # Look for JSON code blocks
            json_pattern = r'```json\s*(.*?)\s*```'
            match = re.search(json_pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                return json.loads(match.group(1))
            
            # Look for JSON objects
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            
            # Try parsing entire response
            return json.loads(response)
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from Gemini response")
            return fallback or {
                "error": "JSON parsing failed", 
                "raw_response": response[:500] + "..." if len(response) > 500 else response
            }
    
    async def process_multimodal_input(self, text: str, images: List[Any] = None) -> Dict[str, Any]:
        """Process multimodal input with text and images."""
        if not self.use_vision or not self.vision_model_instance:
            return {"error": "Vision capability not available"}
        
        logger.info("Gemini processing multimodal input")
        
        prompt = f"""
        Analyze this multimodal input comprehensively:
        
        **Text Input:** {text}
        
        **Multimodal Analysis Tasks:**
        1. Describe what you observe in any provided images
        2. Explain how the visual and textual information relate
        3. Identify key insights from combining both modalities
        4. Suggest actions or decisions based on the combined analysis
        5. Note any creative opportunities this multimodal data reveals
        
        **Gemini's Multimodal Strengths:**
        - Rapid visual understanding
        - Creative connections between modalities
        - Practical insight generation
        - Innovation opportunity identification
        
        Provide comprehensive multimodal analysis with creative insights.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                temperature=0.5,
                max_tokens=1500,
                use_vision=True,
                images=images or []
            )
            
            return {
                "multimodal_analysis": response,
                "text_input": text,
                "images_processed": len(images) if images else 0,
                "processing_type": "multimodal",
                "gemini_insights": True
            }
            
        except Exception as e:
            logger.error(f"Multimodal processing failed: {e}")
            return {
                "error": f"Multimodal processing failed: {str(e)}",
                "text_input": text,
                "fallback_processing": True
            }
    
    async def batch_process_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple tasks efficiently in batch."""
        if not self.batch_processing:
            # Process individually if batch processing disabled
            results = []
            for task in tasks:
                result = await self._process_single_task(task)
                results.append(result)
            return results
        
        logger.info(f"Gemini batch processing {len(tasks)} tasks")
        
        # Create batch prompt
        batch_prompt = f"""
        Process these {len(tasks)} tasks efficiently using batch optimization:
        
        **Tasks:**
        """
        
        for i, task in enumerate(tasks, 1):
            batch_prompt += f"\n{i}. {json.dumps(task, indent=2)}\n"
        
        batch_prompt += f"""
        
        **Batch Processing Instructions:**
        1. Process all tasks efficiently
        2. Look for patterns and optimizations across tasks
        3. Provide consistent quality for all results
        4. Use rapid processing while maintaining accuracy
        
        **Output Format:**
        Provide results as JSON array:
        [
            {{"task_id": 1, "result": "...", "status": "completed"}},
            {{"task_id": 2, "result": "...", "status": "completed"}},
            ...
        ]
        
        Focus on speed and efficiency while maintaining quality.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=batch_prompt,
                temperature=0.4,
                max_tokens=3000
            )
            
            batch_results = self._extract_json_from_response(response, fallback={"results": []})
            results = batch_results if isinstance(batch_results, list) else batch_results.get("results", [])
            
            # Ensure we have results for all tasks
            while len(results) < len(tasks):
                results.append({
                    "task_id": len(results) + 1,
                    "result": "Batch processing incomplete",
                    "status": "partial"
                })
            
            return results[:len(tasks)]
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # Fallback to individual processing
            return [
                {
                    "task_id": i + 1,
                    "result": f"Batch failed, individual processing needed: {str(e)}",
                    "status": "error"
                }
                for i in range(len(tasks))
            ]
    
    async def _process_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single task efficiently."""
        task_type = task.get("type", "general")
        content = task.get("content", "")
        
        prompt = f"""
        Process this {task_type} task efficiently:
        
        **Task Content:** {content}
        
        **Processing Requirements:**
        - Rapid but accurate execution
        - Creative and innovative approach
        - High-quality results
        - Practical and actionable outcomes
        
        Provide efficient, high-quality results with Gemini's creative touch.
        """
        
        try:
            response = await self._actual_api_call(
                prompt=prompt,
                temperature=0.5,
                max_tokens=1000
            )
            
            return {
                "task_type": task_type,
                "result": response,
                "status": "completed",
                "processing_style": "gemini_optimized"
            }
            
        except Exception as e:
            return {
                "task_type": task_type,
                "result": f"Task processing failed: {str(e)}",
                "status": "error"
            }
    
    async def clear_cache(self):
        """Clear the response cache."""
        if self.response_cache:
            self.response_cache.clear()
            logger.info("Gemini response cache cleared")
    
    async def get_multimodal_capabilities(self) -> Dict[str, Any]:
        """Get current multimodal capabilities status."""
        return {
            "agent_type": self.agent_type.value,
            "agent_id": self.agent_id,
            "primary_model": self.primary_model,
            "vision_model": self.vision_model,
            "capabilities": {
                "multimodal_processing": self.use_vision and self.vision_model_instance is not None,
                "batch_processing": self.batch_processing,
                "response_caching": self.enable_caching,
                "creative_problem_solving": True,
                "rapid_iteration": True,
                "mathematical_computation": True
            },
            "features": {
                "vision_analysis": self.use_vision,
                "search_integration": self.use_search,
                "safety_filters": True,
                "content_moderation": True
            },
            "performance": {
                "cache_size": len(self.response_cache) if self.response_cache else 0,
                "total_requests": self.metrics["total_requests"],
                "success_rate": self.metrics["successful_requests"] / max(1, self.metrics["total_requests"]),
                "average_cost": self.metrics["total_cost"] / max(1, self.metrics["total_requests"])
            },
            "health_status": {
                "enabled": self.enabled,
                "healthy": self.is_healthy,
                "health_score": self.health_score
            }
        }