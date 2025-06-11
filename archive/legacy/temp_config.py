"""
Temporary configuration manager for testing the system.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


def initialize_config(config_dir: str = "config", environment: Optional[str] = None) -> Dict[str, Any]:
    """
    Simple configuration loader for testing.
    
    Returns a basic configuration dictionary with defaults.
    """
    config = {
        "app": {
            "name": "Autonomous Multi-LLM Agent System",
            "version": "1.0.0",
            "environment": environment or os.getenv("ENVIRONMENT", "development")
        },
        "features": {
            "orchestration": {
                "min_votes": 3,
                "consensus_threshold": 0.6,
                "max_retries": 3,
                "proposal_timeout": 120,
                "voting_timeout": 60,
                "execution_timeout": 300,
                "enable_rollback": True
            },
            "self_healing": {
                "enabled": True,
                "monitoring_interval": 10.0,
                "health_check_interval": 30.0,
                "recovery_max_attempts": 5,
                "auto_intervention": True
            },
            "integrations": {
                "github_integration": False,
                "notion_sync": False
            }
        },
        "api": {
            "enabled": False,  # Disabled for pure autonomous mode
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": "gpt-4-turbo-preview"
            },
            "anthropic": {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "model": "claude-3-sonnet-20240229"
            },
            "google": {
                "api_key": os.getenv("GOOGLE_API_KEY"),
                "model": "gemini-1.5-pro"
            },
            "github": {
                "token": os.getenv("GITHUB_TOKEN"),
                "default_owner": os.getenv("GITHUB_DEFAULT_OWNER"),
                "default_repo": os.getenv("GITHUB_DEFAULT_REPO")
            },
            "notion": {
                "tasks_database_id": os.getenv("NOTION_TASKS_DATABASE_ID"),
                "knowledge_database_id": os.getenv("NOTION_KNOWLEDGE_DATABASE_ID"),
                "execution_logs_database_id": os.getenv("NOTION_LOGS_DATABASE_ID")
            }
        },
        "monitoring": {
            "enabled": True,
            "health_checks": {
                "interval_seconds": 30
            },
            "metrics": {
                "collection_interval": 60
            }
        },
        "performance": {
            "concurrency": {
                "worker_threads": 4
            }
        },
        "resources": {
            "rate_limits": {
                "requests_per_minute": 60
            }
        },
        "security": {
            "api_security": {
                "allowed_origins": ["*"]
            }
        }
    }
    
    return config