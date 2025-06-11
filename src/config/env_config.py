"""
Enhanced environment configuration manager for the autonomous multi-LLM agent system.

This module provides improved configuration management with support for:
- Environment variables with type conversion
- Configuration validation and schema enforcement
- Secrets management and secure handling
- Dynamic configuration updates
- Environment-specific overrides
"""

import os
import json
import yaml
from typing import Dict, List, Any, Optional, Union, Type, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re
from loguru import logger
import subprocess
import tempfile
import shutil


class ConfigType(Enum):
    """Configuration value types for validation."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    PATH = "path"
    URL = "url"
    EMAIL = "email"
    SECRET = "secret"


@dataclass
class ConfigField:
    """Configuration field definition with validation."""
    name: str
    type: ConfigType
    default: Any = None
    required: bool = False
    description: str = ""
    choices: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    secret: bool = False
    env_var: Optional[str] = None


class EnvironmentConfigManager:
    """Enhanced environment configuration manager."""
    
    def __init__(self):
        self.config_fields: Dict[str, ConfigField] = {}
        self.config_values: Dict[str, Any] = {}
        self.validation_errors: List[str] = []
        self._setup_default_fields()
        
    def _setup_default_fields(self):
        """Set up default configuration fields for the agent system."""
        
        # Core system configuration
        self.register_field(ConfigField(
            name="ENVIRONMENT",
            type=ConfigType.STRING,
            default="development",
            required=True,
            description="Deployment environment",
            choices=["development", "testing", "staging", "production"],
            env_var="ENVIRONMENT"
        ))
        
        self.register_field(ConfigField(
            name="DEBUG",
            type=ConfigType.BOOLEAN,
            default=True,
            description="Enable debug mode",
            env_var="DEBUG"
        ))
        
        self.register_field(ConfigField(
            name="LOG_LEVEL",
            type=ConfigType.STRING,
            default="INFO",
            description="Logging level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            env_var="LOG_LEVEL"
        ))
        
        # Database configuration
        self.register_field(ConfigField(
            name="DATABASE_URL",
            type=ConfigType.STRING,
            default="sqlite:///data/main.db",
            required=True,
            description="Main database connection URL",
            env_var="DATABASE_URL"
        ))
        
        # LLM API configurations
        self.register_field(ConfigField(
            name="OPENAI_API_KEY",
            type=ConfigType.SECRET,
            required=False,
            description="OpenAI API key",
            env_var="OPENAI_API_KEY",
            secret=True
        ))
        
        self.register_field(ConfigField(
            name="ANTHROPIC_API_KEY",
            type=ConfigType.SECRET,
            required=False,
            description="Anthropic API key",
            env_var="ANTHROPIC_API_KEY",
            secret=True
        ))
        
        self.register_field(ConfigField(
            name="GOOGLE_API_KEY",
            type=ConfigType.SECRET,
            required=False,
            description="Google API key",
            env_var="GOOGLE_API_KEY",
            secret=True
        ))
        
        # Integration configurations
        self.register_field(ConfigField(
            type=ConfigType.SECRET,
            required=False,
# NOTION_REMOVED:             description="Notion API token",
            secret=True
        ))
        
        self.register_field(ConfigField(
            name="GITHUB_TOKEN",
            type=ConfigType.SECRET,
            required=False,
            description="GitHub personal access token",
            env_var="GITHUB_TOKEN",
            secret=True
        ))
        
        # Agent configuration
        self.register_field(ConfigField(
            name="MAX_CONCURRENT_AGENTS",
            type=ConfigType.INTEGER,
            default=5,
            description="Maximum number of concurrent agents",
            min_value=1,
            max_value=50,
            env_var="MAX_CONCURRENT_AGENTS"
        ))
        
        self.register_field(ConfigField(
            name="AGENT_TIMEOUT",
            type=ConfigType.INTEGER,
            default=300,
            description="Agent execution timeout in seconds",
            min_value=10,
            max_value=3600,
            env_var="AGENT_TIMEOUT"
        ))
        
        # Resource limits
        self.register_field(ConfigField(
            name="MAX_MEMORY_USAGE",
            type=ConfigType.STRING,
            default="4GB",
            description="Maximum memory usage",
            pattern=r"^\d+[KMGT]B$",
            env_var="MAX_MEMORY_USAGE"
        ))
        
        self.register_field(ConfigField(
            name="MAX_CPU_USAGE",
            type=ConfigType.INTEGER,
            default=80,
            description="Maximum CPU usage percentage",
            min_value=10,
            max_value=100,
            env_var="MAX_CPU_USAGE"
        ))
        
        # Self-healing configuration
        self.register_field(ConfigField(
            name="HEALING_ENABLED",
            type=ConfigType.BOOLEAN,
            default=True,
            description="Enable self-healing system",
            env_var="HEALING_LOOP_ENABLED"
        ))
        
        self.register_field(ConfigField(
            name="RECOVERY_MAX_ATTEMPTS",
            type=ConfigType.INTEGER,
            default=5,
            description="Maximum recovery attempts",
            min_value=1,
            max_value=20,
            env_var="RECOVERY_MAX_ATTEMPTS"
        ))
        
        # Monitoring configuration
        self.register_field(ConfigField(
            name="METRICS_ENABLED",
            type=ConfigType.BOOLEAN,
            default=True,
            description="Enable metrics collection",
            env_var="METRICS_ENABLED"
        ))
        
        self.register_field(ConfigField(
            name="HEALTH_CHECK_INTERVAL",
            type=ConfigType.INTEGER,
            default=60,
            description="Health check interval in seconds",
            min_value=10,
            max_value=300,
            env_var="HEALTH_CHECK_INTERVAL"
        ))
        
        # Network configuration
        self.register_field(ConfigField(
            name="HTTP_PORT",
            type=ConfigType.INTEGER,
            default=8000,
            description="HTTP server port",
            min_value=1024,
            max_value=65535,
            env_var="HTTP_PORT"
        ))
        
        self.register_field(ConfigField(
            name="WS_PORT",
            type=ConfigType.INTEGER,
            default=8765,
            description="WebSocket server port",
            min_value=1024,
            max_value=65535,
            env_var="WS_PORT"
        ))
        
        # Security configuration
        self.register_field(ConfigField(
            name="API_KEY_REQUIRED",
            type=ConfigType.BOOLEAN,
            default=False,
            description="Require API key for access",
            env_var="API_KEY_REQUIRED"
        ))
        
        self.register_field(ConfigField(
            name="ENCRYPTION_ENABLED",
            type=ConfigType.BOOLEAN,
            default=False,
            description="Enable data encryption",
            env_var="ENCRYPTION_ENABLED"
        ))
        
        # File system paths
        self.register_field(ConfigField(
            name="DATA_DIR",
            type=ConfigType.PATH,
            default="./data",
            description="Data directory path",
            env_var="DATA_DIR"
        ))
        
        self.register_field(ConfigField(
            name="LOGS_DIR",
            type=ConfigType.PATH,
            default="./logs",
            description="Logs directory path",
            env_var="LOGS_DIR"
        ))
        
        self.register_field(ConfigField(
            name="WORKSPACE_DIR",
            type=ConfigType.PATH,
            default="./workspace",
            description="Workspace directory path",
            env_var="WORKSPACE_DIR"
        ))
    
    def register_field(self, field: ConfigField):
        """Register a configuration field."""
        self.config_fields[field.name] = field
        if field.env_var:
            self.config_fields[field.env_var] = field
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        self.config_values.clear()
        self.validation_errors.clear()
        
        for field_name, field in self.config_fields.items():
            # Skip duplicate entries (env_var mappings)
            if field.name != field_name:
                continue
                
            value = self._get_field_value(field)
            if value is not None:
                self.config_values[field.name] = value
        
        # Validate configuration
        self._validate_configuration()
        
        if self.validation_errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(self.validation_errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Loaded {len(self.config_values)} configuration values")
        return self.config_values.copy()
    
    def _get_field_value(self, field: ConfigField) -> Any:
        """Get value for a configuration field."""
        # Try environment variable first
        env_value = None
        if field.env_var:
            env_value = os.getenv(field.env_var)
        
        # Fall back to field name as env var
        if env_value is None:
            env_value = os.getenv(field.name)
        
        # Use default if no env value
        if env_value is None:
            if field.required:
                self.validation_errors.append(f"Required field {field.name} not set")
            return field.default
        
        # Convert value based on type
        try:
            return self._convert_value(env_value, field)
        except Exception as e:
            self.validation_errors.append(f"Invalid value for {field.name}: {e}")
            return field.default
    
    def _convert_value(self, value: str, field: ConfigField) -> Any:
        """Convert string value to appropriate type."""
        if field.type == ConfigType.STRING or field.type == ConfigType.SECRET:
            return value
        
        elif field.type == ConfigType.INTEGER:
            return int(value)
        
        elif field.type == ConfigType.FLOAT:
            return float(value)
        
        elif field.type == ConfigType.BOOLEAN:
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
        
        elif field.type == ConfigType.LIST:
            return [item.strip() for item in value.split(',') if item.strip()]
        
        elif field.type == ConfigType.DICT:
            return json.loads(value)
        
        elif field.type == ConfigType.PATH:
            return Path(value)
        
        elif field.type == ConfigType.URL:
            # Basic URL validation
            if not (value.startswith('http://') or value.startswith('https://')):
                raise ValueError(f"Invalid URL: {value}")
            return value
        
        elif field.type == ConfigType.EMAIL:
            # Basic email validation
            if '@' not in value or '.' not in value:
                raise ValueError(f"Invalid email: {value}")
            return value
        
        else:
            return value
    
    def _validate_configuration(self):
        """Validate loaded configuration."""
        for field_name, field in self.config_fields.items():
            # Skip duplicate entries
            if field.name != field_name:
                continue
            
            value = self.config_values.get(field.name)
            if value is None:
                continue
            
            # Check choices
            if field.choices and value not in field.choices:
                self.validation_errors.append(
                    f"{field.name} must be one of {field.choices}, got: {value}"
                )
            
            # Check numeric ranges
            if field.type in (ConfigType.INTEGER, ConfigType.FLOAT):
                if field.min_value is not None and value < field.min_value:
                    self.validation_errors.append(
                        f"{field.name} must be >= {field.min_value}, got: {value}"
                    )
                if field.max_value is not None and value > field.max_value:
                    self.validation_errors.append(
                        f"{field.name} must be <= {field.max_value}, got: {value}"
                    )
            
            # Check pattern
            if field.pattern and isinstance(value, str):
                if not re.match(field.pattern, value):
                    self.validation_errors.append(
                        f"{field.name} does not match pattern {field.pattern}: {value}"
                    )
    
    def get(self, name: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config_values.get(name, default)
    
    def get_int(self, name: str, default: int = 0) -> int:
        """Get integer configuration value."""
        value = self.get(name, default)
        return int(value) if value is not None else default
    
    def get_float(self, name: str, default: float = 0.0) -> float:
        """Get float configuration value."""
        value = self.get(name, default)
        return float(value) if value is not None else default
    
    def get_bool(self, name: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        value = self.get(name, default)
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
        else:
            return bool(value) if value is not None else default
    
    def get_list(self, name: str, default: List[Any] = None) -> List[Any]:
        """Get list configuration value."""
        value = self.get(name, default or [])
        if isinstance(value, list):
            return value
        elif isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        else:
            return default or []
    
    def get_dict(self, name: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get dictionary configuration value."""
        value = self.get(name, default or {})
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default or {}
        else:
            return default or {}
    
    def get_path(self, name: str, default: str = "") -> Path:
        """Get path configuration value."""
        value = self.get(name, default)
        return Path(value) if value else Path(default)
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.get("ENVIRONMENT") == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.get("ENVIRONMENT") == "development"
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.get("ENVIRONMENT") == "testing"
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            'url': self.get("DATABASE_URL"),
            'pool_size': self.get_int("DATABASE_POOL_SIZE", 10),
            'timeout': self.get_int("DATABASE_TIMEOUT", 30)
        }
    
    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        """Get LLM provider configuration."""
        provider_upper = provider.upper()
        
        config = {
            'api_key': self.get(f"{provider_upper}_API_KEY"),
            'model': self.get(f"{provider_upper}_MODEL"),
            'temperature': self.get_float(f"{provider_upper}_TEMPERATURE", 0.7),
            'max_tokens': self.get_int(f"{provider_upper}_MAX_TOKENS", 4000),
            'timeout': self.get_int(f"{provider_upper}_TIMEOUT", 60)
        }
        
        # Add provider-specific configs
        if provider.lower() == 'ollama':
            config['base_url'] = self.get("OLLAMA_BASE_URL", "http://localhost:11434")
        
        return config
    
    def get_integration_config(self, integration: str) -> Dict[str, Any]:
        """Get external integration configuration."""
        integration_upper = integration.upper()
        
# NOTION_REMOVED:         if integration.lower() == 'notion':
            return {
                'version': self.get("NOTION_VERSION", "2022-06-28"),
                'tasks_database_id': self.get("NOTION_TASKS_DATABASE_ID"),
                'knowledge_database_id': self.get("NOTION_KNOWLEDGE_DATABASE_ID"),
                'local_db_path': self.get_path("NOTION_DB_PATH", "data/notion_integration.db"),
                'sync_enabled': self.get_bool("NOTION_SYNC_ENABLED", True)
            }
        
        elif integration.lower() == 'github':
            return {
                'token': self.get("GITHUB_TOKEN"),
                'default_owner': self.get("GITHUB_DEFAULT_OWNER"),
                'default_repo': self.get("GITHUB_DEFAULT_REPO"),
                'local_repo_path': self.get_path("GITHUB_LOCAL_REPO_PATH", "./workspace/repo"),
                'auto_commit': self.get_bool("GITHUB_AUTO_COMMIT", False),
                'auto_test': self.get_bool("GITHUB_AUTO_TEST", True)
            }
        
        return {}
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return {
            'max_concurrent': self.get_int("MAX_CONCURRENT_AGENTS", 5),
            'timeout': self.get_int("AGENT_TIMEOUT", 300),
            'heartbeat_interval': self.get_int("AGENT_HEARTBEAT_INTERVAL", 30),
            'cleanup_interval': self.get_int("AGENT_CLEANUP_INTERVAL", 60)
        }
    
    def get_healing_config(self) -> Dict[str, Any]:
        """Get self-healing configuration."""
        return {
            'enabled': self.get_bool("HEALING_ENABLED", True),
            'monitoring_interval': self.get_float("HEALING_MONITORING_INTERVAL", 10.0),
            'health_check_interval': self.get_float("HEALING_HEALTH_CHECK_INTERVAL", 30.0),
            'recovery_max_attempts': self.get_int("RECOVERY_MAX_ATTEMPTS", 5),
            'auto_intervention': self.get_bool("RECOVERY_AUTO_INTERVENTION", True),
            'performance_optimization': self.get_bool("HEALING_PERFORMANCE_OPTIMIZATION", True)
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return {
            'metrics_enabled': self.get_bool("METRICS_ENABLED", True),
            'collection_interval': self.get_int("METRICS_COLLECTION_INTERVAL", 10),
            'health_check_enabled': self.get_bool("HEALTH_CHECK_ENABLED", True),
            'health_check_interval': self.get_int("HEALTH_CHECK_INTERVAL", 60),
            'performance_monitoring': self.get_bool("PERFORMANCE_MONITORING_ENABLED", True)
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            'api_key_required': self.get_bool("API_KEY_REQUIRED", False),
            'encryption_enabled': self.get_bool("ENCRYPTION_ENABLED", False),
            'auth_enabled': self.get_bool("AUTH_ENABLED", False),
            'rate_limit_enabled': self.get_bool("API_RATE_LIMIT_ENABLED", True),
            'rate_limit_requests': self.get_int("API_RATE_LIMIT_REQUESTS", 100),
            'rate_limit_window': self.get_int("API_RATE_LIMIT_WINDOW", 60)
        }
    
    def get_resource_limits(self) -> Dict[str, Any]:
        """Get resource limit configuration."""
        return {
            'max_memory': self.get("MAX_MEMORY_USAGE", "4GB"),
            'max_memory_per_agent': self.get("MAX_MEMORY_PER_AGENT", "512MB"),
            'max_cpu_usage': self.get_int("MAX_CPU_USAGE", 80),
            'memory_warning_threshold': self.get_int("MEMORY_WARNING_THRESHOLD", 80),
            'cpu_warning_threshold': self.get_int("CPU_WARNING_THRESHOLD", 70)
        }
    
    def get_network_config(self) -> Dict[str, Any]:
        """Get network configuration."""
        return {
            'http_host': self.get("HTTP_HOST", "0.0.0.0"),
            'http_port': self.get_int("HTTP_PORT", 8000),
            'ws_host': self.get("WS_HOST", "0.0.0.0"),
            'ws_port': self.get_int("WS_PORT", 8765),
            'http_timeout': self.get_int("HTTP_TIMEOUT", 30),
            'max_connections': self.get_int("HTTP_MAX_CONNECTIONS", 1000)
        }
    
    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        config = {}
        
        for name, value in self.config_values.items():
            field = self.config_fields.get(name)
            
            # Skip secrets unless explicitly requested
            if field and field.secret and not include_secrets:
                config[name] = "***HIDDEN***"
            else:
                config[name] = value
        
        return config
    
    def validate_required_fields(self) -> List[str]:
        """Check for missing required fields."""
        missing = []
        
        for field_name, field in self.config_fields.items():
            if field.name != field_name:  # Skip duplicates
                continue
                
            if field.required and field.name not in self.config_values:
                missing.append(field.name)
        
        return missing
    
    def generate_env_template(self, output_path: Optional[str] = None) -> str:
        """Generate .env template file."""
        template_lines = [
            "# =================================================================",
            "# AUTONOMOUS MULTI-LLM AGENT SYSTEM CONFIGURATION",
            "# =================================================================",
            "# This file contains environment variable templates",
            "# Copy this file to .env and set your actual values",
            "",
        ]
        
        # Group fields by category
        categories = {
            "Core System": ["ENVIRONMENT", "DEBUG", "LOG_LEVEL"],
            "Database": ["DATABASE_URL"],
            "LLM APIs": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"],
            "Agent Configuration": ["MAX_CONCURRENT_AGENTS", "AGENT_TIMEOUT"],
            "Resource Limits": ["MAX_MEMORY_USAGE", "MAX_CPU_USAGE"],
            "Monitoring": ["METRICS_ENABLED", "HEALTH_CHECK_INTERVAL"],
            "Network": ["HTTP_PORT", "WS_PORT"],
            "Security": ["API_KEY_REQUIRED", "ENCRYPTION_ENABLED"],
            "File System": ["DATA_DIR", "LOGS_DIR", "WORKSPACE_DIR"]
        }
        
        for category, field_names in categories.items():
            template_lines.extend([
                f"# {category}",
                "# " + "=" * (len(category) + 2),
            ])
            
            for field_name in field_names:
                field = self.config_fields.get(field_name)
                if field:
                    template_lines.append(f"# {field.description}")
                    if field.choices:
                        template_lines.append(f"# Choices: {', '.join(map(str, field.choices))}")
                    if field.secret:
                        template_lines.append(f"{field.name}=your_{field.name.lower()}_here")
                    else:
                        template_lines.append(f"{field.name}={field.default or ''}")
                    template_lines.append("")
            
            template_lines.append("")
        
        template_content = "\n".join(template_lines)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(template_content)
            logger.info(f"Environment template written to {output_path}")
        
        return template_content


# Global instance
_env_config: Optional[EnvironmentConfigManager] = None


def get_env_config() -> EnvironmentConfigManager:
    """Get the global environment configuration manager."""
    global _env_config
    if _env_config is None:
        _env_config = EnvironmentConfigManager()
        _env_config.load_configuration()
    return _env_config


def initialize_env_config() -> EnvironmentConfigManager:
    """Initialize the global environment configuration manager."""
    global _env_config
    _env_config = EnvironmentConfigManager()
    _env_config.load_configuration()
    return _env_config