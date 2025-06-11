import os
import json
import yaml
import asyncio
import hashlib
import threading
import time
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import re
from loguru import logger
try:
    import jsonschema
except ImportError:
    jsonschema = None
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = None
import copy

class ConfigEnvironment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

class ConfigChangeType(Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"

@dataclass
class ConfigChange:
    path: str
    change_type: ConfigChangeType
    old_value: Any
    new_value: Any
    timestamp: datetime
    source: str

@dataclass
class ConfigValidationError:
    path: str
    message: str
    severity: str  # error, warning, info
    code: str

@dataclass
class ABTestVariant:
    name: str
    weight: float
    config_overrides: Dict[str, Any]
    enabled: bool = True

@dataclass
class ABTest:
    name: str
    enabled: bool
    traffic_split: float
    variants: Dict[str, ABTestVariant]
    selection_key: str = "user_id"

@dataclass
class FeatureFlag:
    name: str
    enabled: bool
    rollout_percentage: float
    conditions: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class ConfigWatcher(FileSystemEventHandler):
    """File system watcher for configuration changes."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml', '.json')):
            logger.info(f"Configuration file changed: {event.src_path}")
            asyncio.create_task(self.config_manager._handle_file_change(event.src_path))

class SecretManager:
    """Manages secrets and environment variable substitution."""
    
    def __init__(self):
        self.secrets_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_refresh = {}
    
    def resolve_secret(self, value: str) -> str:
        """Resolve environment variable or secret references."""
        if not isinstance(value, str):
            return value
        
        # Pattern: ${VAR_NAME} or ${VAR_NAME:default_value}
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
        
        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ''
            
            # Check cache first
            cache_key = f"env_{var_name}"
            if cache_key in self.secrets_cache:
                cache_time = self.last_refresh.get(cache_key, 0)
                if time.time() - cache_time < self.cache_ttl:
                    return self.secrets_cache[cache_key]
            
            # Get from environment
            env_value = os.getenv(var_name, default_value)
            
            # Cache the value
            self.secrets_cache[cache_key] = env_value
            self.last_refresh[cache_key] = time.time()
            
            return env_value
        
        return re.sub(pattern, replace_var, value)
    
    def resolve_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolve all secrets in configuration."""
        if isinstance(config, dict):
            return {k: self.resolve_config(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self.resolve_config(item) for item in config]
        elif isinstance(config, str):
            return self.resolve_secret(config)
        else:
            return config

class ConfigSchema:
    """Configuration schema validation."""
    
    def __init__(self):
        self.schema = {
            "type": "object",
            "properties": {
                "app": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "environment": {"type": "string", "enum": ["development", "testing", "production"]},
                        "debug": {"type": "boolean"},
                        "maintenance_mode": {"type": "boolean"}
                    },
                    "required": ["name", "version", "environment"]
                },
                "api": {
                    "type": "object",
                    "properties": {
                        "openai": {"$ref": "#/definitions/api_config"},
                        "anthropic": {"$ref": "#/definitions/api_config"},
                        "google": {"$ref": "#/definitions/api_config"}
                    }
                },
                "resources": {
                    "type": "object",
                    "properties": {
                        "memory": {
                            "type": "object",
                            "properties": {
                                "max_memory_mb": {"type": "integer", "minimum": 128},
                                "warning_threshold_mb": {"type": "integer"},
                                "cleanup_threshold_mb": {"type": "integer"}
                            }
                        },
                        "cpu": {
                            "type": "object",
                            "properties": {
                                "max_cpu_percent": {"type": "integer", "minimum": 1, "maximum": 100},
                                "max_concurrent_tasks": {"type": "integer", "minimum": 1}
                            }
                        }
                    }
                },
                "logging": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
                        "format": {"type": "string", "enum": ["simple", "detailed", "structured", "json"]}
                    }
                }
            },
            "definitions": {
                "api_config": {
                    "type": "object",
                    "properties": {
                        "base_url": {"type": "string", "format": "uri"},
                        "api_key": {"type": "string"},
                        "model": {"type": "string"},
                        "max_tokens": {"type": "integer", "minimum": 1},
                        "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                        "timeout": {"type": "integer", "minimum": 1},
                        "max_retries": {"type": "integer", "minimum": 0}
                    },
                    "required": ["base_url", "api_key", "model"]
                }
            },
            "required": ["app"]
        }
    
    def validate(self, config: Dict[str, Any]) -> List[ConfigValidationError]:
        """Validate configuration against schema."""
        errors = []
        
        try:
            jsonschema.validate(config, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(ConfigValidationError(
                path=".".join(str(p) for p in e.path),
                message=e.message,
                severity="error",
                code="schema_validation"
            ))
        except jsonschema.SchemaError as e:
            errors.append(ConfigValidationError(
                path="schema",
                message=f"Schema error: {e.message}",
                severity="error",
                code="schema_error"
            ))
        
        # Additional custom validations
        errors.extend(self._validate_resource_consistency(config))
        errors.extend(self._validate_api_configuration(config))
        
        return errors
    
    def _validate_resource_consistency(self, config: Dict[str, Any]) -> List[ConfigValidationError]:
        """Validate resource configuration consistency."""
        errors = []
        
        if "resources" in config and "memory" in config["resources"]:
            memory_config = config["resources"]["memory"]
            max_memory = memory_config.get("max_memory_mb", 0)
            warning_threshold = memory_config.get("warning_threshold_mb", 0)
            cleanup_threshold = memory_config.get("cleanup_threshold_mb", 0)
            
            if warning_threshold > max_memory:
                errors.append(ConfigValidationError(
                    path="resources.memory.warning_threshold_mb",
                    message="Warning threshold cannot exceed max memory",
                    severity="error",
                    code="resource_consistency"
                ))
            
            if cleanup_threshold > max_memory:
                errors.append(ConfigValidationError(
                    path="resources.memory.cleanup_threshold_mb",
                    message="Cleanup threshold cannot exceed max memory",
                    severity="error",
                    code="resource_consistency"
                ))
        
        return errors
    
    def _validate_api_configuration(self, config: Dict[str, Any]) -> List[ConfigValidationError]:
        """Validate API configuration."""
        errors = []
        
        if "api" in config:
            for api_name, api_config in config["api"].items():
                if isinstance(api_config, dict):
                    # Check if API key is set
                    api_key = api_config.get("api_key", "")
                    if api_key.startswith("${") and api_key.endswith("}"):
                        # This is an environment variable reference, check if it's set
                        var_name = api_key[2:-1].split(":")[0]
                        if not os.getenv(var_name):
                            errors.append(ConfigValidationError(
                                path=f"api.{api_name}.api_key",
                                message=f"Environment variable {var_name} is not set",
                                severity="warning",
                                code="missing_env_var"
                            ))
        
        return errors

class ConfigManager:
    """Comprehensive configuration management system."""
    
    def __init__(self, config_dir: str = "config", environment: Optional[str] = None):
        self.config_dir = Path(config_dir)
        self.environment = ConfigEnvironment(environment or os.getenv("ENVIRONMENT", "development"))
        
        # Core components
        self.secret_manager = SecretManager()
        self.schema = ConfigSchema()
        
        # Configuration state
        self.config: Dict[str, Any] = {}
        self.raw_config: Dict[str, Any] = {}
        self.config_hash = ""
        self.last_modified = {}
        
        # Change tracking
        self.change_history: List[ConfigChange] = []
        self.max_history = 1000
        self.change_listeners: List[Callable] = []
        
        # Hot reloading
        self.hot_reload_enabled = False
        self.file_watcher = None
        self.observer = None
        
        # A/B testing
        self.ab_tests: Dict[str, ABTest] = {}
        self.user_variants: Dict[str, Dict[str, str]] = {}
        
        # Feature flags
        self.feature_flags: Dict[str, FeatureFlag] = {}
        
        # Threading
        self.config_lock = threading.RLock()
        
        # Load initial configuration
        self.load_config()
        
        logger.info(f"ConfigManager initialized for environment: {self.environment.value}")
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from files."""
        with self.config_lock:
            # Load base configuration
            base_config = self._load_config_file("config.yaml")
            
            # Load environment-specific overrides
            env_config = self._load_config_file(f"{self.environment.value}.yaml")
            
            # Merge configurations
            merged_config = self._merge_configs(base_config, env_config)
            
            # Store raw config before secret resolution
            self.raw_config = copy.deepcopy(merged_config)
            
            # Resolve secrets
            resolved_config = self.secret_manager.resolve_config(merged_config)
            
            # Validate configuration
            validation_errors = self.schema.validate(resolved_config)
            if validation_errors:
                error_messages = [f"{error.path}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    raise ValueError(f"Configuration validation failed: {'; '.join(error_messages)}")
                else:
                    # Log warnings
                    for error in validation_errors:
                        if error.severity == "warning":
                            logger.warning(f"Config warning at {error.path}: {error.message}")
            
            # Calculate config hash
            config_str = json.dumps(resolved_config, sort_keys=True)
            new_hash = hashlib.md5(config_str.encode()).hexdigest()
            
            # Check if config changed
            if new_hash != self.config_hash:
                old_config = self.config.copy()
                self.config = resolved_config
                self.config_hash = new_hash
                
                # Track changes
                self._track_config_changes(old_config, resolved_config)
                
                # Notify listeners
                self._notify_change_listeners()
                
                logger.info("Configuration loaded and validated successfully")
            
            return self.config
    
    def _load_config_file(self, filename: str) -> Dict[str, Any]:
        """Load a single configuration file."""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            logger.warning(f"Configuration file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if filename.endswith('.json'):
                    config = json.load(f)
                else:
                    config = yaml.safe_load(f)
            
            # Update last modified time
            self.last_modified[str(file_path)] = file_path.stat().st_mtime
            
            logger.debug(f"Loaded configuration file: {file_path}")
            return config or {}
            
        except Exception as e:
            logger.error(f"Failed to load configuration file {file_path}: {e}")
            return {}
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries."""
        result = copy.deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        
        return result
    
    def _track_config_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """Track configuration changes."""
        changes = self._find_config_differences(old_config, new_config)
        
        for change in changes:
            self.change_history.append(change)
        
        # Trim history if needed
        if len(self.change_history) > self.max_history:
            self.change_history = self.change_history[-self.max_history:]
    
    def _find_config_differences(self, old: Dict[str, Any], new: Dict[str, Any], path: str = "") -> List[ConfigChange]:
        """Find differences between two configuration dictionaries."""
        changes = []
        
        # Check for modified and new keys
        for key, new_value in new.items():
            current_path = f"{path}.{key}" if path else key
            
            if key not in old:
                changes.append(ConfigChange(
                    path=current_path,
                    change_type=ConfigChangeType.CREATED,
                    old_value=None,
                    new_value=new_value,
                    timestamp=datetime.now(),
                    source="config_file"
                ))
            elif old[key] != new_value:
                if isinstance(old[key], dict) and isinstance(new_value, dict):
                    changes.extend(self._find_config_differences(old[key], new_value, current_path))
                else:
                    changes.append(ConfigChange(
                        path=current_path,
                        change_type=ConfigChangeType.MODIFIED,
                        old_value=old[key],
                        new_value=new_value,
                        timestamp=datetime.now(),
                        source="config_file"
                    ))
        
        # Check for deleted keys
        for key, old_value in old.items():
            if key not in new:
                current_path = f"{path}.{key}" if path else key
                changes.append(ConfigChange(
                    path=current_path,
                    change_type=ConfigChangeType.DELETED,
                    old_value=old_value,
                    new_value=None,
                    timestamp=datetime.now(),
                    source="config_file"
                ))
        
        return changes
    
    def _notify_change_listeners(self):
        """Notify all change listeners."""
        for listener in self.change_listeners:
            try:
                listener(self.config)
            except Exception as e:
                logger.error(f"Error notifying config change listener: {e}")
    
    async def _handle_file_change(self, file_path: str):
        """Handle file system change event."""
        if not self.hot_reload_enabled:
            return
        
        try:
            # Check if file was actually modified
            file_stat = Path(file_path).stat()
            last_modified = self.last_modified.get(file_path, 0)
            
            if file_stat.st_mtime > last_modified:
                logger.info(f"Reloading configuration due to file change: {file_path}")
                await asyncio.sleep(0.1)  # Debounce
                self.load_config()
        except Exception as e:
            logger.error(f"Error handling file change {file_path}: {e}")
    
    # Public API methods
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path."""
        with self.config_lock:
            keys = path.split('.')
            value = self.config
            
            try:
                for key in keys:
                    value = value[key]
                return value
            except (KeyError, TypeError):
                return default
    
    def set(self, path: str, value: Any, source: str = "runtime"):
        """Set configuration value by dot-separated path."""
        with self.config_lock:
            keys = path.split('.')
            config = self.config
            
            # Navigate to parent
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set value
            old_value = config.get(keys[-1])
            config[keys[-1]] = value
            
            # Track change
            change = ConfigChange(
                path=path,
                change_type=ConfigChangeType.MODIFIED if old_value is not None else ConfigChangeType.CREATED,
                old_value=old_value,
                new_value=value,
                timestamp=datetime.now(),
                source=source
            )
            self.change_history.append(change)
            
            # Update config hash
            config_str = json.dumps(self.config, sort_keys=True)
            self.config_hash = hashlib.md5(config_str.encode()).hexdigest()
            
            # Notify listeners
            self._notify_change_listeners()
            
            logger.info(f"Configuration updated: {path} = {value}")
    
    def has(self, path: str) -> bool:
        """Check if configuration path exists."""
        return self.get(path) is not None
    
    def enable_hot_reload(self):
        """Enable hot reloading of configuration files."""
        if self.hot_reload_enabled:
            return
        
        self.hot_reload_enabled = True
        self.file_watcher = ConfigWatcher(self)
        self.observer = Observer()
        self.observer.schedule(self.file_watcher, str(self.config_dir), recursive=False)
        self.observer.start()
        
        logger.info("Hot reload enabled for configuration files")
    
    def disable_hot_reload(self):
        """Disable hot reloading."""
        if not self.hot_reload_enabled:
            return
        
        self.hot_reload_enabled = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self.file_watcher = None
        
        logger.info("Hot reload disabled")
    
    def add_change_listener(self, listener: Callable[[Dict[str, Any]], None]):
        """Add a configuration change listener."""
        self.change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[Dict[str, Any]], None]):
        """Remove a configuration change listener."""
        if listener in self.change_listeners:
            self.change_listeners.remove(listener)
    
    # A/B Testing methods
    
    def register_ab_test(self, test: ABTest):
        """Register an A/B test."""
        self.ab_tests[test.name] = test
        logger.info(f"Registered A/B test: {test.name}")
    
    def get_ab_variant(self, test_name: str, user_id: str) -> Optional[str]:
        """Get A/B test variant for a user."""
        if test_name not in self.ab_tests:
            return None
        
        test = self.ab_tests[test_name]
        if not test.enabled:
            return None
        
        # Check if user already has a variant
        if user_id in self.user_variants.get(test_name, {}):
            return self.user_variants[test_name][user_id]
        
        # Assign variant based on hash
        user_hash = hashlib.md5(f"{test_name}:{user_id}".encode()).hexdigest()
        hash_value = int(user_hash[:8], 16) / 0xffffffff
        
        if hash_value > test.traffic_split:
            return None  # User not in test
        
        # Select variant
        cumulative_weight = 0
        variant_hash = hash_value / test.traffic_split
        
        for variant_name, variant in test.variants.items():
            if not variant.enabled:
                continue
            
            cumulative_weight += variant.weight
            if variant_hash <= cumulative_weight:
                # Store user variant
                if test_name not in self.user_variants:
                    self.user_variants[test_name] = {}
                self.user_variants[test_name][user_id] = variant_name
                
                return variant_name
        
        return None
    
    def get_ab_config(self, test_name: str, user_id: str) -> Dict[str, Any]:
        """Get configuration with A/B test overrides."""
        variant = self.get_ab_variant(test_name, user_id)
        if not variant or test_name not in self.ab_tests:
            return self.config
        
        test = self.ab_tests[test_name]
        if variant not in test.variants:
            return self.config
        
        # Apply variant overrides
        config_copy = copy.deepcopy(self.config)
        overrides = test.variants[variant].config_overrides
        
        return self._merge_configs(config_copy, overrides)
    
    # Feature Flags methods
    
    def register_feature_flag(self, flag: FeatureFlag):
        """Register a feature flag."""
        self.feature_flags[flag.name] = flag
        logger.info(f"Registered feature flag: {flag.name}")
    
    def is_feature_enabled(self, flag_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if a feature flag is enabled."""
        if flag_name not in self.feature_flags:
            return False
        
        flag = self.feature_flags[flag_name]
        if not flag.enabled:
            return False
        
        # Check rollout percentage
        if flag.rollout_percentage < 100:
            context_hash = hashlib.md5(f"{flag_name}:{context}".encode()).hexdigest()
            hash_value = int(context_hash[:8], 16) / 0xffffffff * 100
            if hash_value > flag.rollout_percentage:
                return False
        
        # Check conditions
        if flag.conditions and context:
            for condition_key, condition_value in flag.conditions.items():
                if context.get(condition_key) != condition_value:
                    return False
        
        return True
    
    # Utility methods
    
    def get_change_history(self, limit: int = 100) -> List[ConfigChange]:
        """Get recent configuration changes."""
        return self.change_history[-limit:]
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration metadata."""
        return {
            "environment": self.environment.value,
            "config_hash": self.config_hash,
            "hot_reload_enabled": self.hot_reload_enabled,
            "last_loaded": max(self.last_modified.values()) if self.last_modified else None,
            "change_count": len(self.change_history),
            "ab_tests_count": len(self.ab_tests),
            "feature_flags_count": len(self.feature_flags)
        }
    
    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export current configuration."""
        if include_secrets:
            return copy.deepcopy(self.config)
        else:
            return copy.deepcopy(self.raw_config)
    
    def validate_config(self, config: Optional[Dict[str, Any]] = None) -> List[ConfigValidationError]:
        """Validate configuration."""
        target_config = config if config is not None else self.config
        return self.schema.validate(target_config)
    
    def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up ConfigManager")
        self.disable_hot_reload()

# Global configuration instance
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def initialize_config(config_dir: str = "config", environment: Optional[str] = None) -> ConfigManager:
    """Initialize the global configuration manager."""
    global _config_manager
    _config_manager = ConfigManager(config_dir, environment)
    return _config_manager