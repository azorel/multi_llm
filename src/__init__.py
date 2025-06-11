"""
Autonomous Multi-LLM Agent System

A comprehensive framework for orchestrating multiple LLM agents with self-healing,
monitoring, and collaborative capabilities.
"""

from .core import (
    BaseAgent,
    Orchestrator, 
    SharedMemory,
    WorkflowResult,
    ExecutionStatus
)

from .agents import (
    GPTAgent,
    ClaudeAgent,
    GeminiAgent,
    AgentFactory,
    create_agent,
    create_default_pool
)

from .config import (
    ConfigurationManager,
    EnvironmentConfigManager,
    get_config,
    load_config,
    validate_config
)

from .monitoring import (
    ObservabilitySystem,
    get_observability_system,
    initialize_observability
)

from .self_healing import (
    ErrorDetector,
    RecoveryManager,
    HealingLoop,
    LearningSystem
)

from .tools import (
    SecureFileSystemManager,
    CodeExecutor,
    ValidationFramework,
    ToolRegistry,
    get_tool_registry
)

from .models import (
    Proposal,
    Vote,
    Action,
    ExecutionResult,
    TaskContext
)

__version__ = "1.0.0"
__author__ = "Autonomous Agent System"

__all__ = [
    # Core components
    "BaseAgent",
    "Orchestrator",
    "SharedMemory", 
    "WorkflowResult",
    "ExecutionStatus",
    
    # Agents
    "GPTAgent",
    "ClaudeAgent",
    "GeminiAgent", 
    "AgentFactory",
    "create_agent",
    "create_default_pool",
    
    # Configuration
    "ConfigurationManager",
    "EnvironmentConfigManager",
    "get_config",
    "load_config", 
    "validate_config",
    
    # Monitoring
    "ObservabilitySystem",
    "get_observability_system",
    "initialize_observability",
    
    # Self-healing
    "ErrorDetector",
    "RecoveryManager", 
    "HealingLoop",
    "LearningSystem",
    
    # Tools
    "SecureFileSystemManager",
    "CodeExecutor",
    "ValidationFramework",
    "ToolRegistry",
    "get_tool_registry",
    
    # Models
    "Proposal",
    "Vote",
    "Action", 
    "ExecutionResult",
    "TaskContext"
]