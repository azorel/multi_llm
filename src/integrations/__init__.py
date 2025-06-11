"""
External service integrations for autonomous multi-LLM agents.

This module provides integrations with external services and platforms including:
- GitHub integration for repository management
- Notion integration for knowledge management
- Unified integration manager for orchestrating external services
"""

from .github_client import (
    GitHubIntegration,
    GitHubRepository,
    GitHubPullRequest,
    GitHubIssue,
    GitHubAPIClient
)

    NotionIntegration,
    NotionTask,
    NotionKnowledgeEntry,
    NotionDashboard,
    NotionPropertyBuilder,
    NotionBlockBuilder
)

from .manager import (
    IntegrationManager,
    IntegrationType,
    IntegrationStatus,
    IntegrationConfig,
    ExternalService,
    ServiceHealth,
    get_integration_manager
)

__all__ = [
    # GitHub integration
    "GitHubIntegration",
    "GitHubRepository",
    "GitHubPullRequest", 
    "GitHubIssue",
    "GitHubAPIClient",
    
    # Notion integration
    "NotionIntegration",
    "NotionTask",
    "NotionKnowledgeEntry",
    "NotionDashboard",
    "NotionPropertyBuilder",
    "NotionBlockBuilder",
    
    # Integration manager
    "IntegrationManager",
    "IntegrationType",
    "IntegrationStatus",
    "IntegrationConfig",
    "ExternalService",
    "ServiceHealth",
    "get_integration_manager"
]