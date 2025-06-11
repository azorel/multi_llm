"""
Agent Factory for creating and managing LLM agents.

This factory provides a centralized way to create agents with proper
configuration, registry management, and type-safe initialization.
"""

import os
from typing import Dict, List, Any, Optional, Type, Union
from datetime import datetime

from loguru import logger

from ..core.agent_base import BaseAgent
from ..models.schemas import AgentType, AgentConfig, AgentCapabilities, TaskType
from .gpt_agent import GPTAgent
from .claude_agent import ClaudeAgent
from .gemini_agent import GeminiAgent


class AgentRegistry:
    """Registry for managing agent instances and configurations."""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._agent_types: Dict[AgentType, Type[BaseAgent]] = {
            AgentType.GPT: GPTAgent,
            AgentType.CLAUDE: ClaudeAgent,
            AgentType.GEMINI: GeminiAgent
        }
        self._creation_times: Dict[str, datetime] = {}
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent instance."""
        self._agents[agent.agent_id] = agent
        self._agent_configs[agent.agent_id] = agent.config
        self._creation_times[agent.agent_id] = datetime.utcnow()
        logger.info(f"Registered agent {agent.agent_id} of type {agent.agent_type.value}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    def list_agents(self, agent_type: Optional[AgentType] = None) -> List[BaseAgent]:
        """List all agents, optionally filtered by type."""
        agents = list(self._agents.values())
        if agent_type:
            agents = [agent for agent in agents if agent.agent_type == agent_type]
        return agents
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent from registry."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            del self._agent_configs[agent_id]
            del self._creation_times[agent_id]
            logger.info(f"Removed agent {agent_id} from registry")
            return True
        return False
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an agent."""
        if agent_id not in self._agents:
            return None
        
        agent = self._agents[agent_id]
        return {
            "agent_id": agent_id,
            "agent_type": agent.agent_type.value,
            "enabled": agent.enabled,
            "healthy": agent.is_healthy,
            "health_score": agent.health_score,
            "capabilities": agent.capabilities.dict(),
            "metrics": agent.metrics,
            "created_at": self._creation_times[agent_id].isoformat(),
            "consecutive_failures": agent.consecutive_failures
        }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_agents = len(self._agents)
        healthy_agents = sum(1 for agent in self._agents.values() if agent.is_healthy)
        enabled_agents = sum(1 for agent in self._agents.values() if agent.enabled)
        
        type_counts = {}
        for agent_type in AgentType:
            type_counts[agent_type.value] = sum(
                1 for agent in self._agents.values() 
                if agent.agent_type == agent_type
            )
        
        return {
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "enabled_agents": enabled_agents,
            "health_rate": healthy_agents / max(1, total_agents),
            "agent_types": type_counts,
            "registry_size": len(self._agents)
        }


class AgentFactory:
    """Factory for creating and configuring LLM agents."""
    
    def __init__(self):
        self.registry = AgentRegistry()
        self._default_configs = self._load_default_configs()
    
    def _load_default_configs(self) -> Dict[AgentType, Dict[str, Any]]:
        """Load default configurations for each agent type."""
        return {
            AgentType.GPT: {
                "primary_model": "gpt-4",
                "fallback_model": "gpt-3.5-turbo",
                "vision_model": "gpt-4-vision-preview",
                "use_function_calling": True,
                "use_vision": True,
                "use_json_mode": True,
                "input_cost_per_token": 0.00003,
                "output_cost_per_token": 0.00006,
                "capabilities": ["text_generation", "code_generation", "analysis", "reasoning", "sequential_thinking"],
                "specializations": [TaskType.TEXT_GENERATION, TaskType.CODE_GENERATION, TaskType.ANALYSIS],
                "enable_sequential_thinking": True
            },
            AgentType.CLAUDE: {
                "primary_model": "claude-3-opus-20240229",
                "fallback_model": "claude-3-sonnet-20240229",
                "fast_model": "claude-3-haiku-20240307",
                "use_long_context": True,
                "safety_level": "high",
                "constitutional_ai": True,
                "input_cost_per_token": 0.000015,
                "output_cost_per_token": 0.000075,
                "max_context_tokens": 200000,
                "context_utilization": 0.8,
                "capabilities": ["text_generation", "analysis", "reasoning", "safety_evaluation", "sequential_thinking"],
                "specializations": [TaskType.TEXT_GENERATION, TaskType.ANALYSIS, TaskType.RESEARCH],
                "enable_sequential_thinking": True
            },
            AgentType.GEMINI: {
                "primary_model": "gemini-1.5-pro",
                "vision_model": "gemini-1.5-pro",
                "ultra_model": "gemini-1.5-pro",
                "use_vision": True,
                "use_search": False,
                "batch_processing": True,
                "enable_caching": True,
                "input_cost_per_token": 0.00000125,
                "output_cost_per_token": 0.00000375,
                "cache_ttl": 3600,
                "capabilities": ["text_generation", "multimodal_processing", "creative_tasks", "analysis", "sequential_thinking"],
                "specializations": [TaskType.TEXT_GENERATION, TaskType.CREATIVE_TASKS, TaskType.MULTIMODAL_TASKS],
                "enable_sequential_thinking": True
            }
        }
    
    def create_agent(
        self, 
        agent_type: AgentType, 
        agent_id: Optional[str] = None,
        api_key: Optional[str] = None,
        config_overrides: Optional[Dict[str, Any]] = None,
        auto_register: bool = True
    ) -> BaseAgent:
        """
        Create an agent with the specified configuration.
        
        Args:
            agent_type: Type of agent to create
            agent_id: Optional custom agent ID (auto-generated if not provided)
            api_key: API key for the agent (uses environment variable if not provided)
            config_overrides: Custom configuration to override defaults
            auto_register: Whether to automatically register the agent
            
        Returns:
            Configured agent instance
            
        Raises:
            ValueError: If agent type is not supported or configuration is invalid
        """
        if agent_type not in self.registry._agent_types:
            raise ValueError(f"Unsupported agent type: {agent_type}")
        
        # Generate agent ID if not provided
        if not agent_id:
            agent_id = f"{agent_type.value}-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Check if agent already exists
        if agent_id in self.registry._agents:
            raise ValueError(f"Agent with ID {agent_id} already exists")
        
        # Get default configuration
        default_config = self._default_configs[agent_type].copy()
        
        # Apply overrides
        if config_overrides:
            default_config.update(config_overrides)
        
        # Set API key
        if api_key:
            default_config["api_key"] = api_key
        else:
            # Try to get from environment
            env_var_map = {
                AgentType.GPT: "OPENAI_API_KEY",
                AgentType.CLAUDE: "ANTHROPIC_API_KEY",
                AgentType.GEMINI: "GOOGLE_AI_API_KEY"
            }
            env_var = env_var_map.get(agent_type)
            if env_var and os.getenv(env_var):
                default_config["api_key"] = os.getenv(env_var)
        
        # Add sequential thinking to all agents if enabled
        capabilities_list = default_config.pop("capabilities", [])
        if default_config.pop("enable_sequential_thinking", True):
            if "sequential_thinking" not in capabilities_list:
                capabilities_list.append("sequential_thinking")
        
        # Create agent capabilities
        capabilities = AgentCapabilities(
            capabilities=capabilities_list,
            specializations=default_config.pop("specializations", []),
            max_parallel_tasks=default_config.pop("max_parallel_tasks", 5),
            supported_languages=default_config.pop("supported_languages", ["en"]),
            context_window_size=default_config.pop("context_window_size", 4096)
        )
        
        # Create agent config
        config = AgentConfig(
            agent_id=agent_id,
            agent_type=agent_type,
            model=default_config.get("primary_model", f"default-{agent_type.value}"),
            api_key=default_config.get("api_key", ""),
            capabilities=capabilities.capabilities,
            specializations=capabilities.specializations,
            cost_per_token=default_config.get("input_cost_per_token", 0.001),
            max_context_length=capabilities.context_window_size,
            temperature=default_config.get("temperature", 0.7),
            timeout_seconds=default_config.get("timeout_seconds", 60),
            max_retries=default_config.get("max_retries", 3),
            metadata=default_config
        )
        
        # Create agent instance
        agent_class = self.registry._agent_types[agent_type]
        agent = agent_class(config)
        
        # Register agent if requested
        if auto_register:
            self.registry.register_agent(agent)
        
        logger.info(f"Created {agent_type.value} agent: {agent_id}")
        return agent
    
    def create_agents_from_config(self, config_dict: Dict[str, Any]) -> List[BaseAgent]:
        """
        Create multiple agents from a configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary with agent specifications
            
        Returns:
            List of created agent instances
        """
        agents = []
        
        for agent_spec in config_dict.get("agents", []):
            agent_type_str = agent_spec.get("type")
            if not agent_type_str:
                logger.warning("Agent specification missing 'type' field, skipping")
                continue
            
            try:
                agent_type = AgentType(agent_type_str)
            except ValueError:
                logger.warning(f"Unknown agent type: {agent_type_str}, skipping")
                continue
            
            agent_id = agent_spec.get("id")
            api_key = agent_spec.get("api_key")
            config_overrides = agent_spec.get("config", {})
            
            try:
                agent = self.create_agent(
                    agent_type=agent_type,
                    agent_id=agent_id,
                    api_key=api_key,
                    config_overrides=config_overrides
                )
                agents.append(agent)
            except Exception as e:
                logger.error(f"Failed to create agent {agent_id}: {e}")
        
        logger.info(f"Created {len(agents)} agents from configuration")
        return agents
    
    def create_default_agent_pool(self) -> List[BaseAgent]:
        """
        Create a default pool with one agent of each type.
        
        Returns:
            List of default agents
        """
        agents = []
        
        for agent_type in AgentType:
            try:
                agent = self.create_agent(agent_type)
                agents.append(agent)
            except Exception as e:
                logger.warning(f"Failed to create default {agent_type.value} agent: {e}")
        
        logger.info(f"Created default agent pool with {len(agents)} agents")
        return agents
    
    def create_balanced_agent_pool(self, total_agents: int = 6) -> List[BaseAgent]:
        """
        Create a balanced pool optimized for load distribution across providers.
        
        Args:
            total_agents: Total number of agents to create
            
        Returns:
            List of balanced agents across providers
        """
        agents = []
        
        # Define balanced distribution
        distribution = {
            AgentType.GPT: max(1, total_agents // 2),      # 50% GPT for general reliability
            AgentType.CLAUDE: max(1, total_agents // 3),    # 33% Claude for analysis
            AgentType.GEMINI: max(1, total_agents // 6)     # 17% Gemini for creative tasks
        }
        
        # Ensure we don't exceed total_agents
        actual_total = sum(distribution.values())
        if actual_total < total_agents:
            # Add remaining to GPT as it's most reliable
            distribution[AgentType.GPT] += (total_agents - actual_total)
        
        for agent_type, count in distribution.items():
            for i in range(count):
                try:
                    # Customize config based on agent type and role
                    config_overrides = self._get_specialized_config(agent_type, i)
                    
                    agent = self.create_agent(
                        agent_type=agent_type,
                        agent_id=f"{agent_type.value}-balanced-{i+1}",
                        config_overrides=config_overrides
                    )
                    agents.append(agent)
                    
                except Exception as e:
                    logger.warning(f"Failed to create balanced {agent_type.value} agent {i+1}: {e}")
        
        logger.info(f"Created balanced agent pool with {len(agents)} agents: {distribution}")
        return agents
    
    def _get_specialized_config(self, agent_type: AgentType, instance_num: int) -> Dict[str, Any]:
        """Get specialized configuration for load-balanced agents"""
        base_configs = {
            AgentType.GPT: {
                0: {  # Primary GPT - general purpose
                    "specializations": [TaskType.TEXT_GENERATION, TaskType.CODE_GENERATION, TaskType.ANALYSIS],
                    "primary_model": "gpt-4o-mini",  # Cost-effective for most tasks
                    "temperature": 0.7
                },
                1: {  # Secondary GPT - coding focused
                    "specializations": [TaskType.CODE_GENERATION, TaskType.DEBUGGING],
                    "primary_model": "gpt-4",  # Full model for complex coding
                    "temperature": 0.3
                },
                2: {  # Tertiary GPT - creative tasks
                    "specializations": [TaskType.CREATIVE_TASKS, TaskType.TEXT_GENERATION],
                    "primary_model": "gpt-4o-mini",
                    "temperature": 0.9
                }
            },
            AgentType.CLAUDE: {
                0: {  # Primary Claude - analysis and reasoning
                    "specializations": [TaskType.ANALYSIS, TaskType.RESEARCH, TaskType.REASONING],
                    "primary_model": "claude-3-5-sonnet-20241022",
                    "temperature": 0.1,
                    "use_long_context": True
                },
                1: {  # Secondary Claude - creative and writing
                    "specializations": [TaskType.CREATIVE_TASKS, TaskType.TEXT_GENERATION],
                    "primary_model": "claude-3-5-haiku-20241022",  # Faster for creative tasks
                    "temperature": 0.8
                }
            },
            AgentType.GEMINI: {
                0: {  # Primary Gemini - research and multimodal
                    "specializations": [TaskType.RESEARCH, TaskType.MULTIMODAL_TASKS, TaskType.CREATIVE_TASKS],
                    "primary_model": "gemini-1.5-flash",  # Cost-effective
                    "temperature": 0.6,
                    "use_vision": True
                }
            }
        }
        
        return base_configs.get(agent_type, {}).get(instance_num, {})
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID from registry."""
        return self.registry.get_agent(agent_id)
    
    def list_agents(self, agent_type: Optional[AgentType] = None) -> List[BaseAgent]:
        """List agents from registry."""
        return self.registry.list_agents(agent_type)
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent from registry."""
        return self.registry.remove_agent(agent_id)
    
    def get_factory_status(self) -> Dict[str, Any]:
        """Get factory and registry status."""
        registry_stats = self.registry.get_registry_stats()
        
        return {
            "factory_initialized": True,
            "supported_agent_types": [agent_type.value for agent_type in AgentType],
            "registry_stats": registry_stats,
            "default_configs_loaded": len(self._default_configs),
            "available_agent_classes": {
                agent_type.value: agent_class.__name__ 
                for agent_type, agent_class in self.registry._agent_types.items()
            }
        }
    
    def validate_agent_config(self, agent_type: AgentType, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate agent configuration.
        
        Args:
            agent_type: Type of agent to validate config for
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields based on agent type
        required_fields = {
            AgentType.GPT: ["api_key"],
            AgentType.CLAUDE: ["api_key"],
            AgentType.GEMINI: ["api_key"]
        }
        
        for field in required_fields.get(agent_type, []):
            if field not in config or not config[field]:
                # Check environment variables as fallback
                env_var_map = {
                    "api_key": {
                        AgentType.GPT: "OPENAI_API_KEY",
                        AgentType.CLAUDE: "ANTHROPIC_API_KEY",
                        AgentType.GEMINI: "GOOGLE_AI_API_KEY"
                    }
                }
                
                env_var = env_var_map.get(field, {}).get(agent_type)
                if not env_var or not os.getenv(env_var):
                    errors.append(f"Missing required field '{field}' and no environment variable {env_var}")
        
        # Validate model names
        valid_models = {
            AgentType.GPT: ["gpt-4", "gpt-3.5-turbo", "gpt-4-vision-preview"],
            AgentType.CLAUDE: ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            AgentType.GEMINI: ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro-latest"]
        }
        
        model = config.get("primary_model")
        if model and model not in valid_models.get(agent_type, []):
            errors.append(f"Invalid model '{model}' for agent type {agent_type.value}")
        
        # Validate cost configuration
        for cost_field in ["input_cost_per_token", "output_cost_per_token"]:
            if cost_field in config:
                try:
                    cost = float(config[cost_field])
                    if cost < 0:
                        errors.append(f"{cost_field} must be non-negative")
                except (ValueError, TypeError):
                    errors.append(f"{cost_field} must be a valid number")
        
        # Validate timeout and retry settings
        for int_field in ["timeout_seconds", "max_retries"]:
            if int_field in config:
                try:
                    value = int(config[int_field])
                    if value <= 0:
                        errors.append(f"{int_field} must be positive")
                except (ValueError, TypeError):
                    errors.append(f"{int_field} must be a valid integer")
        
        return len(errors) == 0, errors
    
    async def health_check_all_agents(self) -> Dict[str, Any]:
        """
        Perform health check on all registered agents.
        
        Returns:
            Health check results for all agents
        """
        results = {}
        
        for agent_id, agent in self.registry._agents.items():
            try:
                health_info = {
                    "agent_id": agent_id,
                    "agent_type": agent.agent_type.value,
                    "enabled": agent.enabled,
                    "healthy": agent.is_healthy,
                    "health_score": agent.health_score,
                    "consecutive_failures": agent.consecutive_failures,
                    "last_health_check": datetime.utcnow().isoformat()
                }
                
                # Try a simple health check operation
                try:
                    # This would be a simple API call to verify connectivity
                    # For now, we'll just check the agent's internal state
                    health_info["api_accessible"] = True
                    health_info["status"] = "healthy" if agent.is_healthy else "unhealthy"
                except Exception as e:
                    health_info["api_accessible"] = False
                    health_info["status"] = "error"
                    health_info["error"] = str(e)
                
                results[agent_id] = health_info
                
            except Exception as e:
                results[agent_id] = {
                    "agent_id": agent_id,
                    "status": "error",
                    "error": f"Health check failed: {str(e)}"
                }
        
        overall_status = {
            "total_agents": len(results),
            "healthy_agents": sum(1 for r in results.values() if r.get("status") == "healthy"),
            "error_agents": sum(1 for r in results.values() if r.get("status") == "error"),
            "overall_health": "good" if all(r.get("status") == "healthy" for r in results.values()) else "degraded",
            "check_timestamp": datetime.utcnow().isoformat(),
            "agent_results": results
        }
        
        return overall_status


# Global factory instance
_factory_instance: Optional[AgentFactory] = None


def get_agent_factory() -> AgentFactory:
    """Get the global agent factory instance."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = AgentFactory()
    return _factory_instance


def create_agent(
    agent_type: AgentType,
    agent_id: Optional[str] = None,
    api_key: Optional[str] = None,
    config_overrides: Optional[Dict[str, Any]] = None
) -> BaseAgent:
    """
    Convenience function to create an agent using the global factory.
    
    Args:
        agent_type: Type of agent to create
        agent_id: Optional custom agent ID
        api_key: API key for the agent
        config_overrides: Custom configuration to override defaults
        
    Returns:
        Configured agent instance
    """
    factory = get_agent_factory()
    return factory.create_agent(
        agent_type=agent_type,
        agent_id=agent_id,
        api_key=api_key,
        config_overrides=config_overrides
    )


def create_default_pool() -> List[BaseAgent]:
    """
    Convenience function to create a default agent pool.
    
    Returns:
        List of default agents (one of each type)
    """
    factory = get_agent_factory()
    return factory.create_default_agent_pool()