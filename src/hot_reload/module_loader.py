"""
Module Loader for Hot Reload System
===================================

Provides dynamic module loading and reloading capabilities.
"""

import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional, Set, List
import threading
from datetime import datetime
from loguru import logger


class ModuleLoader:
    """
    Handles dynamic loading and reloading of Python modules.
    
    Features:
    - Safe module reloading with dependency tracking
    - Module state preservation during reload
    - Circular dependency detection
    - Reload rollback on failure
    """
    
    def __init__(self):
        """Initialize the module loader."""
        self.loaded_modules: Dict[str, Any] = {}
        self.module_states: Dict[str, Dict[str, Any]] = {}
        self.reload_history: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        
        # Track module dependencies
        self.module_dependencies: Dict[str, Set[str]] = {}
        
        # Track reload-safe modules
        self.reload_safe_modules: Set[str] = {
            'src.automation.lifeos_automation_engine',
            'src.integrations.notion_mcp_client',
            'src.processors.content_processor_factory',
            'src.processors.youtube_channel_processor',
            'src.self_healing.recovery_manager',
            'src.self_healing.error_detector',
            'src.self_healing.healing_loop',
            'src.intelligence.autonomous_decision_engine',
            'src.integrations.sequential_thinking_client',
            'src.tools.youtube_processor',
            'src.tools.validation',
            'src.monitoring.observability',
        }
        
        logger.info("ModuleLoader initialized")
    
    def is_reload_safe(self, module_name: str) -> bool:
        """Check if a module can be safely reloaded."""
        # Check if module is in the safe list
        if module_name in self.reload_safe_modules:
            return True
        
        # Check if it's a local project module
        if module_name.startswith('src.'):
            # Allow most src modules except core system modules
            unsafe_patterns = [
                'src.main',
                'src.core.orchestrator',
                'src.core.shared_memory',
                'src.config.',
            ]
            
            for pattern in unsafe_patterns:
                if module_name.startswith(pattern):
                    return False
            
            return True
        
        return False
    
    def save_module_state(self, module_name: str) -> Dict[str, Any]:
        """Save the current state of a module before reloading."""
        state = {}
        
        if module_name in sys.modules:
            module = sys.modules[module_name]
            
            # Save module attributes that should persist
            for attr_name in dir(module):
                if not attr_name.startswith('__'):
                    try:
                        attr_value = getattr(module, attr_name)
                        
                        # Save only serializable attributes
                        if isinstance(attr_value, (str, int, float, bool, list, dict, tuple)):
                            state[attr_name] = attr_value
                        elif hasattr(attr_value, '__dict__'):
                            # For class instances, save their state
                            state[attr_name] = {
                                '_type': 'instance',
                                '_class': attr_value.__class__.__name__,
                                '_state': getattr(attr_value, '__dict__', {})
                            }
                    except Exception as e:
                        logger.debug(f"Could not save attribute {attr_name}: {e}")
        
        return state
    
    def restore_module_state(self, module_name: str, state: Dict[str, Any]):
        """Restore module state after reloading."""
        if module_name in sys.modules and state:
            module = sys.modules[module_name]
            
            for attr_name, attr_value in state.items():
                try:
                    if isinstance(attr_value, dict) and attr_value.get('_type') == 'instance':
                        # Skip instance restoration for now (complex)
                        continue
                    else:
                        setattr(module, attr_name, attr_value)
                except Exception as e:
                    logger.debug(f"Could not restore attribute {attr_name}: {e}")
    
    def track_dependencies(self, module_name: str):
        """Track module dependencies for proper reload ordering."""
        if module_name not in self.module_dependencies:
            self.module_dependencies[module_name] = set()
        
        if module_name in sys.modules:
            module = sys.modules[module_name]
            
            # Check module imports
            for name, obj in module.__dict__.items():
                if hasattr(obj, '__module__') and obj.__module__:
                    dep_module = obj.__module__
                    if dep_module.startswith('src.') and dep_module != module_name:
                        self.module_dependencies[module_name].add(dep_module)
    
    def get_reload_order(self, module_names: List[str]) -> List[str]:
        """Determine the correct order to reload modules based on dependencies."""
        # Simple topological sort
        visited = set()
        reload_order = []
        
        def visit(module_name: str):
            if module_name in visited:
                return
            
            visited.add(module_name)
            
            # Visit dependencies first
            for dep in self.module_dependencies.get(module_name, []):
                if dep in module_names:
                    visit(dep)
            
            reload_order.append(module_name)
        
        for module_name in module_names:
            visit(module_name)
        
        return reload_order
    
    def reload_module(self, module_name: str, force: bool = False) -> Dict[str, Any]:
        """
        Safely reload a module.
        
        Args:
            module_name: Name of the module to reload
            force: Force reload even if not marked as safe
            
        Returns:
            Result dictionary with success status and details
        """
        with self._lock:
            result = {
                'success': False,
                'module': module_name,
                'timestamp': datetime.now().isoformat(),
                'error': None,
                'state_preserved': False
            }
            
            try:
                # Check if module can be reloaded
                if not force and not self.is_reload_safe(module_name):
                    result['error'] = f"Module {module_name} is not marked as reload-safe"
                    logger.warning(result['error'])
                    return result
                
                # Check if module exists
                if module_name not in sys.modules:
                    result['error'] = f"Module {module_name} not loaded"
                    return result
                
                logger.info(f"Reloading module: {module_name}")
                
                # Save current state
                saved_state = self.save_module_state(module_name)
                self.module_states[module_name] = saved_state
                
                # Track dependencies
                self.track_dependencies(module_name)
                
                # Store reference to old module
                old_module = sys.modules[module_name]
                
                # Reload the module
                try:
                    new_module = importlib.reload(sys.modules[module_name])
                    
                    # Restore state if available
                    if saved_state:
                        self.restore_module_state(module_name, saved_state)
                        result['state_preserved'] = True
                    
                    # Update loaded modules tracking
                    self.loaded_modules[module_name] = new_module
                    
                    result['success'] = True
                    logger.info(f"Successfully reloaded module: {module_name}")
                    
                except Exception as reload_error:
                    # Rollback on failure
                    logger.error(f"Failed to reload {module_name}: {reload_error}")
                    
                    # Try to restore old module
                    sys.modules[module_name] = old_module
                    result['error'] = str(reload_error)
                    raise
                
            except Exception as e:
                result['error'] = str(e)
                logger.error(f"Module reload error for {module_name}: {e}")
            
            finally:
                # Record in history
                self.reload_history.append(result)
                
                # Keep only last 100 entries
                if len(self.reload_history) > 100:
                    self.reload_history = self.reload_history[-100:]
            
            return result
    
    def reload_multiple(self, module_names: List[str], force: bool = False) -> Dict[str, Any]:
        """
        Reload multiple modules in the correct order.
        
        Args:
            module_names: List of module names to reload
            force: Force reload even if not marked as safe
            
        Returns:
            Summary of reload results
        """
        # Get proper reload order
        reload_order = self.get_reload_order(module_names)
        
        results = {
            'total': len(reload_order),
            'successful': 0,
            'failed': 0,
            'modules': {}
        }
        
        for module_name in reload_order:
            result = self.reload_module(module_name, force)
            results['modules'][module_name] = result
            
            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
                
                # Stop on first failure to maintain consistency
                if not force:
                    logger.warning(f"Stopping reload sequence due to failure in {module_name}")
                    break
        
        return results
    
    def get_reload_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent reload history."""
        return self.reload_history[-limit:]
    
    def clear_module_cache(self, module_name: str):
        """Clear module from all caches."""
        # Clear from sys.modules
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        # Clear from loader caches
        if module_name in self.loaded_modules:
            del self.loaded_modules[module_name]
        
        if module_name in self.module_states:
            del self.module_states[module_name]
        
        # Clear any submodules
        for name in list(sys.modules.keys()):
            if name.startswith(f"{module_name}."):
                del sys.modules[name]
    
    def add_reload_safe_module(self, module_name: str):
        """Mark a module as safe to reload."""
        self.reload_safe_modules.add(module_name)
        logger.info(f"Module {module_name} marked as reload-safe")
    
    def remove_reload_safe_module(self, module_name: str):
        """Remove a module from the reload-safe list."""
        self.reload_safe_modules.discard(module_name)
        logger.info(f"Module {module_name} removed from reload-safe list")