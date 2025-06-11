"""
Centralized configuration management for the autonomous multi-LLM agent system.

This module provides unified configuration loading and management across all
components of the agent system, combining environment variables, YAML files,
and runtime configuration with proper validation and type safety.
"""

import os
import json
import yaml
from typing import Dict, List, Any, Optional, Union, Type
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger
import threading
from contextlib import contextmanager

from .env_config import EnvironmentConfigManager, get_env_config


@dataclass
class ConfigurationState:
    """Current configuration state."""
    environment: str
    loaded_at: datetime
    config_sources: List[str]
    validation_errors: List[str]
    values: Dict[str, Any]


class ConfigurationManager:
    """Centralized configuration management system."""
    
    def __init__(self, config_dir: str = "config", auto_reload: bool = False):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
            auto_reload: Whether to automatically reload config on file changes
        """
        self.config_dir = Path(config_dir)
        self.auto_reload = auto_reload
        self._config_cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._env_config = get_env_config()
        self._state: Optional[ConfigurationState] = None
        
        # Initialize configuration
        self.reload_configuration()
    
    def reload_configuration(self) -> ConfigurationState:
        """Reload configuration from all sources."""
        with self._lock:
            logger.info("Reloading configuration...")
            
            # Clear cache
            self._config_cache.clear()
            
            # Determine environment
            environment = self._env_config.get("ENVIRONMENT", "development")
            
            # Load configuration in order of precedence
            config_sources = []
            merged_config = {}
            validation_errors = []
            
            try:
                # 1. Load environment variables (highest precedence)
                env_config = self._env_config.export_config(include_secrets=True)
                merged_config.update({"env": env_config})
                config_sources.append("environment_variables")
                
                # 2. Load environment-specific YAML file
                env_yaml_path = self.config_dir / f"{environment}.yaml"
                if env_yaml_path.exists():
                    with open(env_yaml_path, 'r', encoding='utf-8') as f:
                        env_yaml_config = yaml.safe_load(f) or {}
                    merged_config.update(env_yaml_config)
                    config_sources.append(f"{environment}.yaml")
                    logger.info(f"Loaded {environment}.yaml configuration")
                else:
                    logger.warning(f"Environment config file not found: {env_yaml_path}")
                
                # 3. Load base configuration if it exists
                base_config_path = self.config_dir / "config.yaml"
                if base_config_path.exists():
                    with open(base_config_path, 'r', encoding='utf-8') as f:
                        base_config = yaml.safe_load(f) or {}
                    # Merge base config first, then override with env-specific
                    final_config = self._deep_merge(base_config, merged_config)
                    merged_config = final_config
                    config_sources.append("config.yaml")
                    logger.info("Loaded base config.yaml configuration")
                
                # Store in cache
                self._config_cache = merged_config
                
                # Create state
                self._state = ConfigurationState(
                    environment=environment,
                    loaded_at=datetime.now(),
                    config_sources=config_sources,
                    validation_errors=validation_errors,
                    values=merged_config.copy()
                )
                
                logger.info(f"Configuration loaded successfully from {len(config_sources)} sources")
                return self._state
                
            except Exception as e:
                error_msg = f"Failed to load configuration: {e}"
                logger.error(error_msg)
                validation_errors.append(error_msg)
                
                # Create error state
                self._state = ConfigurationState(
                    environment=environment,
                    loaded_at=datetime.now(),
                    config_sources=config_sources,
                    validation_errors=validation_errors,
                    values=merged_config
                )
                
                raise RuntimeError(error_msg) from e
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None, section: Optional[str] = None) -> Any:
        """
        Get configuration value with dot notation support.
        
        Args:
            key: Configuration key (supports dot notation like 'api.openai.model')
            default: Default value if key not found
            section: Optional section to search in first
            
        Returns:
            Configuration value or default
        """
        with self._lock:
            try:
                # Try environment variables first for certain keys
                if key.upper() in self._env_config.config_values:
                    return self._env_config.get(key.upper(), default)
                
                # Navigate through nested dictionary
                current = self._config_cache
                
                # If section specified, start there
                if section and section in current:
                    current = current[section]
                
                # Split key by dots and navigate
                keys = key.split('.')
                for k in keys:
                    if isinstance(current, dict) and k in current:
                        current = current[k]
                    else:
                        return default
                
                return current
                
            except Exception as e:
                logger.warning(f"Error accessing config key '{key}': {e}")
                return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        with self._lock:
            return self._config_cache.get(section, {})
    
    def get_int(self, key: str, default: int = 0, section: Optional[str] = None) -> int:
        """Get integer configuration value."""
        value = self.get(key, default, section)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0, section: Optional[str] = None) -> float:
        """Get float configuration value."""
        value = self.get(key, default, section)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False, section: Optional[str] = None) -> bool:
        """Get boolean configuration value."""
        value = self.get(key, default, section)
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
        else:
            return bool(value) if value is not None else default
    
    def get_list(self, key: str, default: List[Any] = None, section: Optional[str] = None) -> List[Any]:
        """Get list configuration value."""
        value = self.get(key, default or [], section)
        if isinstance(value, list):
            return value
        elif isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        else:
            return default or []
    
    def get_dict(self, key: str, default: Dict[str, Any] = None, section: Optional[str] = None) -> Dict[str, Any]:
        """Get dictionary configuration value."""
        value = self.get(key, default or {}, section)
        if isinstance(value, dict):
            return value
        else:
            return default or {}
    
    def get_path(self, key: str, default: str = "", section: Optional[str] = None) -> Path:
        """Get path configuration value."""
        value = self.get(key, default, section)
        return Path(value) if value else Path(default)
    
    # Environment helpers
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.get("environment", section="app") == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.get("environment", section="app") == "development"
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.get("environment", section="app") == "testing"
    
    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self.get_bool("debug", section="app")
    
    # Configuration sections
    def get_api_config(self, provider: str) -> Dict[str, Any]:
        """Get API configuration for a specific provider."""
        api_section = self.get_section("api")
        provider_config = api_section.get(provider, {})
        
        # Merge with environment variables
        env_config = self._env_config.get_llm_config(provider)
        return {**provider_config, **env_config}
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        db_config = self.get_section("database")
        
        # Add environment-specific database URL
        env_db_config = self._env_config.get_database_config()
        return {**db_config, **env_db_config}
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get_section("logging")
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        security_config = self.get_section("security")
        env_security_config = self._env_config.get_security_config()
        return {**security_config, **env_security_config}
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.get_section("performance")
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        monitoring_config = self.get_section("monitoring")
        env_monitoring_config = self._env_config.get_monitoring_config()
        return {**monitoring_config, **env_monitoring_config}
    
    def get_features_config(self) -> Dict[str, Any]:
        """Get features configuration."""
        return self.get_section("features")
    
    def get_retry_config(self, service: Optional[str] = None) -> Dict[str, Any]:
        """Get retry configuration for a service or global."""
        retry_config = self.get_section("retry")
        
        if service:
            # Return service-specific retry config with global fallback
            service_config = retry_config.get("services", {}).get(service, {})
            global_config = retry_config.get("global", {})
            return {**global_config, **service_config}
        
        return retry_config.get("global", {})
    
    def get_resource_limits(self) -> Dict[str, Any]:
        """Get resource limits configuration."""
        resources_config = self.get_section("resources")
        env_resources_config = self._env_config.get_resource_limits()
        return {**resources_config, **env_resources_config}
    
    def get_integration_config(self, integration: str) -> Dict[str, Any]:
        """Get integration configuration."""
        # Get from YAML config
        integrations_section = self.get_section("integrations") 
        integration_config = integrations_section.get(integration, {})
        
        # Merge with environment config
        env_integration_config = self._env_config.get_integration_config(integration)
        return {**integration_config, **env_integration_config}
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        agent_config = self.get_section("agents")
        env_agent_config = self._env_config.get_agent_config()
        return {**agent_config, **env_agent_config}
    
    def get_healing_config(self) -> Dict[str, Any]:
        """Get self-healing configuration."""
        healing_config = self.get_section("self_healing")
        env_healing_config = self._env_config.get_healing_config()
        return {**healing_config, **env_healing_config}
    
    def get_network_config(self) -> Dict[str, Any]:
        """Get network configuration."""
        network_config = self.get_section("network")
        env_network_config = self._env_config.get_network_config()
        return {**network_config, **env_network_config}
    
    # Validation and state
    def validate_configuration(self) -> List[str]:
        """Validate current configuration and return any errors."""
        errors = []
        
        # Validate required environment variables
        missing_required = self._env_config.validate_required_fields()
        if missing_required:
            errors.extend([f"Missing required environment variable: {var}" for var in missing_required])
        
        # Validate API configurations
        api_config = self.get_section("api")
        for provider in ["openai", "anthropic", "google"]:
            provider_config = api_config.get(provider, {})
            if provider_config and not provider_config.get("model"):
                errors.append(f"Missing model configuration for {provider}")
        
        # Validate database configuration
        db_config = self.get_database_config()
        if not db_config.get("url"):
            errors.append("Missing database URL configuration")
        
        # Validate security settings for production
        if self.is_production():
            security_config = self.get_security_config()
            if not security_config.get("api_key_required"):
                errors.append("API key authentication should be required in production")
            if not security_config.get("encryption_enabled"):
                errors.append("Data encryption should be enabled in production")
        
        return errors
    
    def get_state(self) -> Optional[ConfigurationState]:
        """Get current configuration state."""
        return self._state
    
    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export current configuration."""
        with self._lock:
            config = self._config_cache.copy()
            
            if not include_secrets:
                # Mask sensitive values
                self._mask_secrets(config)
            
            return config
    
    def _mask_secrets(self, config: Dict[str, Any]) -> None:
        """Recursively mask secret values in configuration."""
        secret_keys = ["key", "token", "secret", "password", "credential"]
        
        for key, value in config.items():
            if isinstance(value, dict):
                self._mask_secrets(value)
            elif isinstance(value, str) and any(secret_key in key.lower() for secret_key in secret_keys):
                config[key] = "***MASKED***"
    
    @contextmanager
    def override_config(self, overrides: Dict[str, Any]):
        """Temporarily override configuration values."""
        with self._lock:
            original_cache = self._config_cache.copy()
            try:
                # Apply overrides
                self._config_cache = self._deep_merge(self._config_cache, overrides)
                yield
            finally:
                # Restore original configuration
                self._config_cache = original_cache


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config() -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def initialize_config(config_dir: str = "config", auto_reload: bool = False) -> ConfigurationManager:
    """Initialize the global configuration manager."""
    global _config_manager
    _config_manager = ConfigurationManager(config_dir=config_dir, auto_reload=auto_reload)
    return _config_manager


# Convenience functions for common config access patterns
def get_environment() -> str:
    """Get current environment."""
    return get_config().get("environment", "development", section="app")


def is_production() -> bool:
    """Check if running in production."""
    return get_config().is_production()


def is_development() -> bool:
    """Check if running in development."""
    return get_config().is_development()


def is_testing() -> bool:
    """Check if running in testing."""
    return get_config().is_testing()


def get_api_config(provider: str) -> Dict[str, Any]:
    """Get API configuration for provider."""
    return get_config().get_api_config(provider)


def get_database_config() -> Dict[str, Any]:
    """Get database configuration."""
    return get_config().get_database_config()


def reload_config() -> ConfigurationState:
    """Reload configuration from all sources."""
    return get_config().reload_configuration()