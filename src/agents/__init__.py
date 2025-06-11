"""
Agents package for autonomous multi-LLM agent system.

This package contains implementations of different LLM agents and
the factory for creating and managing them.
"""

from .gpt_agent import GPTAgent
from .claude_agent import ClaudeAgent
from .gemini_agent import GeminiAgent
from .agent_factory import (
    AgentFactory, 
    AgentRegistry, 
    get_agent_factory,
    create_agent,
    create_default_pool
)

__all__ = [
    "GPTAgent",
    "ClaudeAgent", 
    "GeminiAgent",
    "AgentFactory",
    "AgentRegistry",
    "get_agent_factory",
    "create_agent",
    "create_default_pool"
]