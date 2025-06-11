#!/usr/bin/env python3
"""
Enhanced Agent Factory using disler's just-prompt unified LLM interface
=======================================================================

Replaces the basic agent factory with a sophisticated multi-provider LLM system
that supports OpenAI, Anthropic, Google Gemini, Groq, DeepSeek, and Ollama.
"""

import asyncio
import os
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

# Import just-prompt components
from ..just_prompt.atoms.shared.model_router import ModelRouter
from ..just_prompt.atoms.shared.data_types import ModelProviders
from ..just_prompt.atoms.shared.utils import split_provider_and_model


@dataclass
class AgentResponse:
    """Response from an LLM agent."""
    content: str
    model_used: str
    provider: str
    tokens_used: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    execution_time: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass 
class MultiAgentResponse:
    """Response from multiple agents working together."""
    responses: List[AgentResponse]
    consensus: Optional[str] = None
    confidence_score: float = 0.0
    decision_reasoning: List[str] = None
    execution_time: float = 0.0


class EnhancedAgentFactory:
    """
    Enhanced agent factory that provides unified access to multiple LLM providers
    with advanced features like CEO/board decision making, parallel processing,
    and intelligent model selection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_models = self._load_default_models()
        self.model_router = ModelRouter()
        
        # Agent specializations
        self.agent_specializations = {
            'reasoning': ['anthropic:claude-3-7-sonnet-20250219:4k', 'openai:o3:high'],
            'coding': ['openai:gpt-4o', 'anthropic:claude-3-5-sonnet-20241022', 'deepseek:deepseek-coder'],
            'analysis': ['anthropic:claude-3-7-sonnet-20250219:8k', 'gemini:gemini-2.5-pro-preview-03-25'],
            'creative': ['openai:gpt-4o', 'gemini:gemini-2.5-flash-preview-04-17:4k'],
            'fast': ['openai:gpt-4o-mini', 'anthropic:claude-3-5-haiku-20241022', 'groq:llama-3.1-70b-versatile'],
            'decision_making': ['openai:o3:high', 'anthropic:claude-3-7-sonnet-20250219:4k', 'gemini:gemini-2.5-pro-preview-03-25']
        }
        
        # CEO model for final decisions
        self.ceo_model = 'openai:o3:high'
        
    def _load_default_models(self) -> List[str]:
        """Load default models from config or use sensible defaults."""
        default_models = self.config.get('default_models', [
            'openai:o3:high',
            'openai:gpt-4o-mini', 
            'anthropic:claude-3-7-sonnet-20250219:4k',
            'gemini:gemini-2.5-pro-preview-03-25',
            'deepseek:deepseek-coder'
        ])
        return default_models
    
    async def initialize(self) -> bool:
        """Initialize the enhanced agent factory."""
        try:
            logger.info("🤖 Initializing Enhanced Agent Factory with just-prompt...")
            
            # Test available providers
            available_providers = await self._test_provider_availability()
            logger.info(f"Available LLM providers: {', '.join(available_providers)}")
            
            if not available_providers:
                logger.error("❌ No LLM providers available")
                return False
            
            logger.success("✅ Enhanced Agent Factory initialized with just-prompt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Enhanced Agent Factory initialization failed: {e}")
            return False
    
    async def _test_provider_availability(self) -> List[str]:
        """Test which LLM providers are available based on API keys."""
        available = []
        
        # Check for API keys
        if os.getenv('OPENAI_API_KEY'):
            available.append('openai')
        if os.getenv('ANTHROPIC_API_KEY'):
            available.append('anthropic')
        if os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY'):
            available.append('gemini')
        if os.getenv('GROQ_API_KEY'):
            available.append('groq')
        if os.getenv('DEEPSEEK_API_KEY'):
            available.append('deepseek')
        if os.getenv('OLLAMA_HOST'):
            available.append('ollama')
            
        return available
    
    async def get_agent(self, agent_type: str = 'reasoning', model: Optional[str] = None) -> 'EnhancedAgent':
        """
        Get an enhanced agent for a specific purpose.
        
        Args:
            agent_type: Type of agent needed (reasoning, coding, analysis, creative, fast, decision_making)
            model: Specific model to use (optional)
        
        Returns:
            Enhanced agent instance
        """
        if model:
            selected_model = model
        else:
            # Select best model for agent type
            available_models = self.agent_specializations.get(agent_type, self.default_models)
            selected_model = await self._select_best_available_model(available_models)
        
        return EnhancedAgent(selected_model, self.model_router)
    
    async def get_multi_agent_consensus(self, 
                                      prompt: str, 
                                      agent_types: List[str] = None,
                                      num_agents: int = 3) -> MultiAgentResponse:
        """
        Get consensus from multiple agents (board of directors approach).
        
        Args:
            prompt: The prompt to send to all agents
            agent_types: Types of agents to use
            num_agents: Number of agents if agent_types not specified
        
        Returns:
            Multi-agent response with consensus
        """
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Select agents
            if agent_types:
                agents = [await self.get_agent(agent_type) for agent_type in agent_types]
            else:
                # Use diverse agent types for better consensus
                diverse_types = ['reasoning', 'analysis', 'fast'][:num_agents]
                agents = [await self.get_agent(agent_type) for agent_type in diverse_types]
            
            # Get responses from all agents in parallel
            tasks = [agent.process_message(prompt) for agent in agents]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful responses
            valid_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.warning(f"Agent {i} failed: {response}")
                    continue
                valid_responses.append(response)
            
            if not valid_responses:
                return MultiAgentResponse(
                    responses=[],
                    consensus="No valid responses received",
                    confidence_score=0.0,
                    execution_time=asyncio.get_event_loop().time() - start_time
                )
            
            # Get CEO decision based on board responses
            consensus, confidence, reasoning = await self._get_ceo_decision(prompt, valid_responses)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return MultiAgentResponse(
                responses=valid_responses,
                consensus=consensus,
                confidence_score=confidence,
                decision_reasoning=reasoning,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Multi-agent consensus failed: {e}")
            return MultiAgentResponse(
                responses=[],
                consensus=f"Error: {e}",
                confidence_score=0.0,
                execution_time=0.0
            )
    
    async def _get_ceo_decision(self, 
                              original_prompt: str, 
                              board_responses: List[AgentResponse]) -> tuple[str, float, List[str]]:
        """Get final decision from CEO model based on board responses."""
        try:
            # Create CEO agent
            ceo_agent = EnhancedAgent(self.ceo_model, self.model_router)
            
            # Prepare board summary for CEO
            board_summary = "\n\n".join([
                f"Board Member {i+1} ({resp.model_used}):\n{resp.content}"
                for i, resp in enumerate(board_responses)
            ])
            
            ceo_prompt = f"""
            As the CEO, I need to make a final decision based on the board's input.
            
            ORIGINAL QUESTION:
            {original_prompt}
            
            BOARD RESPONSES:
            {board_summary}
            
            Please provide:
            1. DECISION: Your final decision/answer
            2. CONFIDENCE: A confidence score from 0.0 to 1.0
            3. REASONING: 3-5 bullet points explaining your reasoning
            
            Format your response as:
            DECISION: [your decision]
            CONFIDENCE: [0.0-1.0]
            REASONING:
            - [point 1]
            - [point 2]
            - [point 3]
            """
            
            ceo_response = await ceo_agent.process_message(ceo_prompt)
            
            # Parse CEO response
            decision, confidence, reasoning = self._parse_ceo_response(ceo_response.content)
            
            return decision, confidence, reasoning
            
        except Exception as e:
            logger.error(f"CEO decision failed: {e}")
            # Fallback to simple majority
            if board_responses:
                return board_responses[0].content, 0.5, ["Fallback to first response due to CEO error"]
            return "No decision possible", 0.0, ["All systems failed"]
    
    def _parse_ceo_response(self, response: str) -> tuple[str, float, List[str]]:
        """Parse CEO response to extract decision, confidence, and reasoning."""
        lines = response.split('\n')
        
        decision = "No clear decision"
        confidence = 0.5
        reasoning = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('DECISION:'):
                decision = line.replace('DECISION:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = float(line.replace('CONFIDENCE:', '').strip())
                except:
                    confidence = 0.5
            elif line.startswith('REASONING:'):
                current_section = 'reasoning'
            elif current_section == 'reasoning' and line.startswith('-'):
                reasoning.append(line[1:].strip())
        
        return decision, confidence, reasoning
    
    async def _select_best_available_model(self, candidate_models: List[str]) -> str:
        """Select the best available model from candidates."""
        available_providers = await self._test_provider_availability()
        
        for model in candidate_models:
            try:
                provider_prefix, _ = split_provider_and_model(model)
                provider = ModelProviders.from_name(provider_prefix)
                if provider and provider.full_name in available_providers:
                    return model
            except:
                continue
        
        # Fallback to first default model
        return self.default_models[0] if self.default_models else 'openai:gpt-4o-mini'
    
    async def execute_parallel_tasks(self, 
                                   tasks: List[Dict[str, Any]], 
                                   agent_type: str = 'fast') -> List[AgentResponse]:
        """
        Execute multiple tasks in parallel using fast agents.
        
        Args:
            tasks: List of task dictionaries with 'prompt' key
            agent_type: Type of agent to use for all tasks
        
        Returns:
            List of agent responses
        """
        try:
            # Create agents for parallel execution
            agents = [await self.get_agent(agent_type) for _ in tasks]
            
            # Execute all tasks in parallel
            parallel_tasks = [
                agent.process_message(task['prompt']) 
                for agent, task in zip(agents, tasks)
            ]
            
            responses = await asyncio.gather(*parallel_tasks, return_exceptions=True)
            
            # Filter and return valid responses
            valid_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.warning(f"Parallel task {i} failed: {response}")
                    valid_responses.append(AgentResponse(
                        content=f"Task failed: {response}",
                        model_used="error",
                        provider="error",
                        success=False,
                        error=str(response)
                    ))
                else:
                    valid_responses.append(response)
            
            return valid_responses
            
        except Exception as e:
            logger.error(f"Parallel task execution failed: {e}")
            return []


class EnhancedAgent:
    """Individual enhanced agent using just-prompt's unified interface."""
    
    def __init__(self, model: str, model_router: ModelRouter):
        self.model = model
        self.model_router = model_router
        self.provider_prefix, self.model_name = split_provider_and_model(model)
        self.provider = ModelProviders.from_name(self.provider_prefix)
    
    async def process_message(self, prompt: str, **kwargs) -> AgentResponse:
        """
        Process a message using the agent's model.
        
        Args:
            prompt: The prompt to process
            **kwargs: Additional parameters
        
        Returns:
            Agent response
        """
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Route the prompt through just-prompt's system
            response_content = await asyncio.to_thread(
                self.model_router.route_prompt,
                self.model,
                prompt
            )
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return AgentResponse(
                content=response_content,
                model_used=self.model_name,
                provider=self.provider.full_name if self.provider else self.provider_prefix,
                execution_time=execution_time,
                success=True,
                metadata={'prompt_length': len(prompt)}
            )
            
        except Exception as e:
            logger.error(f"Agent processing failed for {self.model}: {e}")
            return AgentResponse(
                content=f"Processing failed: {e}",
                model_used=self.model_name,
                provider=self.provider.full_name if self.provider else self.provider_prefix,
                success=False,
                error=str(e)
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about this agent's model."""
        return {
            'model': self.model,
            'model_name': self.model_name,
            'provider': self.provider.full_name if self.provider else self.provider_prefix,
            'provider_prefix': self.provider_prefix
        }


def create_enhanced_agent_factory(config: Dict[str, Any]) -> EnhancedAgentFactory:
    """Create an enhanced agent factory instance."""
    return EnhancedAgentFactory(config)