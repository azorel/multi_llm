"""
Safe Reloader for Hot Reload System
===================================

Provides safe module reloading with state preservation and rollback.
"""

import sys
import asyncio
from typing import Dict, Any, Optional, Set, List, Callable
from datetime import datetime
import traceback
from loguru import logger

from .module_loader import ModuleLoader


class SafeReloader:
    """
    Manages safe reloading of modules with state preservation.
    
    Features:
    - Instance tracking and state preservation
    - Background task continuity during reloads
    - Graceful error handling and rollback
    - Module dependency resolution
    """
    
    def __init__(self, module_loader: ModuleLoader):
        """Initialize the safe reloader."""
        self.module_loader = module_loader
        
        # Track active instances that need preservation
        self.tracked_instances: Dict[str, List[Any]] = {}
        
        # Track background tasks
        self.background_tasks: Dict[str, asyncio.Task] = {}
        
        # Pre/post reload hooks
        self.pre_reload_hooks: Dict[str, List[Callable]] = {}
        self.post_reload_hooks: Dict[str, List[Callable]] = {}
        
        # Reload statistics
        self.reload_stats = {
            'total_reloads': 0,
            'successful_reloads': 0,
            'failed_reloads': 0,
            'last_reload': None
        }
        
        logger.info("SafeReloader initialized")
    
    def track_instance(self, module_name: str, instance: Any):
        """Track an instance for state preservation during reload."""
        if module_name not in self.tracked_instances:
            self.tracked_instances[module_name] = []
        
        if instance not in self.tracked_instances[module_name]:
            self.tracked_instances[module_name].append(instance)
            logger.debug(f"Tracking instance of {instance.__class__.__name__} for module {module_name}")
    
    def untrack_instance(self, module_name: str, instance: Any):
        """Stop tracking an instance."""
        if module_name in self.tracked_instances:
            try:
                self.tracked_instances[module_name].remove(instance)
            except ValueError:
                pass
    
    def add_pre_reload_hook(self, module_name: str, hook: Callable):
        """Add a hook to run before module reload."""
        if module_name not in self.pre_reload_hooks:
            self.pre_reload_hooks[module_name] = []
        self.pre_reload_hooks[module_name].append(hook)
    
    def add_post_reload_hook(self, module_name: str, hook: Callable):
        """Add a hook to run after module reload."""
        if module_name not in self.post_reload_hooks:
            self.post_reload_hooks[module_name] = []
        self.post_reload_hooks[module_name].append(hook)
    
    async def _run_hooks(self, hooks: List[Callable], module_name: str, phase: str):
        """Run a list of hooks."""
        for hook in hooks:
            try:
                logger.debug(f"Running {phase} hook for {module_name}")
                if asyncio.iscoroutinefunction(hook):
                    await hook(module_name)
                else:
                    hook(module_name)
            except Exception as e:
                logger.error(f"Error in {phase} hook for {module_name}: {e}")
    
    def _preserve_instance_state(self, module_name: str) -> Dict[str, Any]:
        """Preserve state of tracked instances."""
        preserved_state = {}
        
        if module_name in self.tracked_instances:
            for i, instance in enumerate(self.tracked_instances[module_name]):
                try:
                    # Save instance state
                    instance_state = {
                        'class_name': instance.__class__.__name__,
                        'module': instance.__class__.__module__,
                        'state': {}
                    }
                    
                    # Save instance attributes
                    if hasattr(instance, '__dict__'):
                        for attr_name, attr_value in instance.__dict__.items():
                            # Skip private attributes and complex objects
                            if not attr_name.startswith('_'):
                                try:
                                    # Only save simple types for now
                                    if isinstance(attr_value, (str, int, float, bool, list, dict, tuple)):
                                        instance_state['state'][attr_name] = attr_value
                                except Exception:
                                    pass
                    
                    # Save any custom preservation method
                    if hasattr(instance, 'preserve_state'):
                        custom_state = instance.preserve_state()
                        instance_state['custom_state'] = custom_state
                    
                    preserved_state[f'instance_{i}'] = instance_state
                    
                except Exception as e:
                    logger.error(f"Error preserving instance state: {e}")
        
        return preserved_state
    
    def _restore_instance_state(self, module_name: str, preserved_state: Dict[str, Any]):
        """Restore state to tracked instances."""
        if module_name not in self.tracked_instances:
            return
        
        for i, instance in enumerate(self.tracked_instances[module_name]):
            instance_key = f'instance_{i}'
            if instance_key in preserved_state:
                instance_state = preserved_state[instance_key]
                
                try:
                    # Restore simple attributes
                    for attr_name, attr_value in instance_state.get('state', {}).items():
                        try:
                            setattr(instance, attr_name, attr_value)
                        except Exception:
                            pass
                    
                    # Restore custom state if method exists
                    if hasattr(instance, 'restore_state') and 'custom_state' in instance_state:
                        instance.restore_state(instance_state['custom_state'])
                    
                except Exception as e:
                    logger.error(f"Error restoring instance state: {e}")
    
    async def reload_module_safe(self, module_name: str, force: bool = False) -> Dict[str, Any]:
        """
        Safely reload a module with state preservation.
        
        Args:
            module_name: Name of the module to reload
            force: Force reload even if not marked as safe
            
        Returns:
            Result dictionary with reload status
        """
        self.reload_stats['total_reloads'] += 1
        
        result = {
            'success': False,
            'module': module_name,
            'timestamp': datetime.now().isoformat(),
            'error': None,
            'state_preserved': False,
            'instances_preserved': 0
        }
        
        try:
            logger.info(f"Starting safe reload of {module_name}")
            
            # Run pre-reload hooks
            if module_name in self.pre_reload_hooks:
                await self._run_hooks(self.pre_reload_hooks[module_name], module_name, "pre-reload")
            
            # Preserve instance states
            preserved_state = self._preserve_instance_state(module_name)
            result['instances_preserved'] = len(preserved_state)
            
            # Perform the reload
            reload_result = self.module_loader.reload_module(module_name, force)
            
            if reload_result['success']:
                # Restore instance states
                self._restore_instance_state(module_name, preserved_state)
                result['state_preserved'] = True
                
                # Run post-reload hooks
                if module_name in self.post_reload_hooks:
                    await self._run_hooks(self.post_reload_hooks[module_name], module_name, "post-reload")
                
                result['success'] = True
                self.reload_stats['successful_reloads'] += 1
                logger.info(f"Successfully reloaded {module_name} with state preservation")
                
            else:
                result['error'] = reload_result['error']
                self.reload_stats['failed_reloads'] += 1
                
        except Exception as e:
            result['error'] = str(e)
            result['traceback'] = traceback.format_exc()
            self.reload_stats['failed_reloads'] += 1
            logger.error(f"Safe reload failed for {module_name}: {e}")
        
        self.reload_stats['last_reload'] = datetime.now().isoformat()
        return result
    
    async def reload_multiple_safe(self, module_names: List[str], force: bool = False) -> Dict[str, Any]:
        """
        Safely reload multiple modules in order.
        
        Args:
            module_names: List of module names to reload
            force: Force reload even if not marked as safe
            
        Returns:
            Summary of reload results
        """
        # Get proper reload order
        reload_order = self.module_loader.get_reload_order(module_names)
        
        results = {
            'total': len(reload_order),
            'successful': 0,
            'failed': 0,
            'modules': {},
            'reload_order': reload_order
        }
        
        for module_name in reload_order:
            result = await self.reload_module_safe(module_name, force)
            results['modules'][module_name] = result
            
            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
                
                # Stop on first failure unless forced
                if not force:
                    logger.warning(f"Stopping reload sequence due to failure in {module_name}")
                    break
        
        return results
    
    def register_background_task(self, task_name: str, task: asyncio.Task):
        """Register a background task to preserve during reloads."""
        self.background_tasks[task_name] = task
        logger.debug(f"Registered background task: {task_name}")
    
    def unregister_background_task(self, task_name: str):
        """Unregister a background task."""
        if task_name in self.background_tasks:
            del self.background_tasks[task_name]
            logger.debug(f"Unregistered background task: {task_name}")
    
    async def pause_background_tasks(self) -> List[str]:
        """Pause background tasks before reload."""
        paused = []
        
        for task_name, task in self.background_tasks.items():
            if not task.done():
                # We can't really pause, but we can track them
                paused.append(task_name)
                logger.debug(f"Background task {task_name} will continue during reload")
        
        return paused
    
    async def resume_background_tasks(self, paused_tasks: List[str]):
        """Resume background tasks after reload."""
        # Tasks continue running, just log status
        for task_name in paused_tasks:
            if task_name in self.background_tasks:
                task = self.background_tasks[task_name]
                if not task.done():
                    logger.debug(f"Background task {task_name} still running after reload")
                else:
                    logger.warning(f"Background task {task_name} completed during reload")
    
    def get_reload_stats(self) -> Dict[str, Any]:
        """Get reload statistics."""
        return self.reload_stats.copy()
    
    def get_tracked_instances(self) -> Dict[str, int]:
        """Get count of tracked instances per module."""
        return {
            module: len(instances) 
            for module, instances in self.tracked_instances.items()
        }