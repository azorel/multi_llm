"""
Reload Manager for Hot Reload System
====================================

Coordinates the hot reload system components.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from loguru import logger

from .module_loader import ModuleLoader
from .file_watcher import FileWatcher
from .safe_reloader import SafeReloader


class ReloadManager:
    """
    Manages the entire hot reload system.
    
    Features:
    - Coordinates file watching and module reloading
    - Manages reload policies and rules
    - Provides reload history and statistics
    - Handles reload failures gracefully
    """
    
    def __init__(self, project_root: Path, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the reload manager.
        
        Args:
            project_root: Root directory of the project
            config: Optional configuration dictionary
        """
        self.project_root = Path(project_root)
        self.config = config or {}
        
        # Initialize components
        self.module_loader = ModuleLoader()
        self.safe_reloader = SafeReloader(self.module_loader)
        
        # Setup file watcher
        watch_paths = [self.project_root / 'src']
        ignore_patterns = self.config.get('ignore_patterns', [])
        self.file_watcher = FileWatcher(watch_paths, ignore_patterns)
        
        # Reload configuration
        self.auto_reload_enabled = self.config.get('auto_reload', True)
        self.reload_delay = self.config.get('reload_delay', 1.0)
        self.max_reload_attempts = self.config.get('max_reload_attempts', 3)
        
        # Module-specific configuration
        self.module_config: Dict[str, Dict[str, Any]] = {}
        self._load_module_config()
        
        # Reload tracking
        self.reload_queue: Set[str] = set()
        self.reload_in_progress = False
        self.reload_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'started_at': None,
            'total_file_changes': 0,
            'total_reloads': 0,
            'successful_reloads': 0,
            'failed_reloads': 0
        }
        
        # Setup file watcher callback
        self.file_watcher.on_change(self._on_file_change)
        
        logger.info(f"ReloadManager initialized for {self.project_root}")
    
    def _load_module_config(self):
        """Load module-specific configuration."""
        # Default module configurations
        self.module_config = {
            'src.automation.lifeos_automation_engine': {
                'auto_reload': True,
                'preserve_state': True,
                'reload_delay': 2.0
            },
            'src.integrations.notion_mcp_client': {
                'auto_reload': True,
                'preserve_state': True,
                'reload_delay': 1.5
            },
            'src.processors.content_processor_factory': {
                'auto_reload': True,
                'preserve_state': False,
                'reload_delay': 1.0
            },
            'src.processors.youtube_channel_processor': {
                'auto_reload': True,
                'preserve_state': True,
                'reload_delay': 1.5
            },
            'src.self_healing.recovery_manager': {
                'auto_reload': True,
                'preserve_state': True,
                'reload_delay': 2.0
            },
            'src.monitoring.observability': {
                'auto_reload': True,
                'preserve_state': True,
                'reload_delay': 1.0
            }
        }
        
        # Merge with user config
        user_module_config = self.config.get('module_config', {})
        for module, config in user_module_config.items():
            if module in self.module_config:
                self.module_config[module].update(config)
            else:
                self.module_config[module] = config
    
    def _on_file_change(self, change_event: Dict[str, Any]):
        """Handle file change event."""
        self.stats['total_file_changes'] += 1
        
        modules = change_event.get('modules', [])
        if not modules:
            return
        
        logger.info(f"File changes detected in modules: {modules}")
        
        # Filter modules based on configuration
        modules_to_reload = []
        for module in modules:
            module_cfg = self.module_config.get(module, {})
            
            # Check if auto-reload is enabled for this module
            if self.auto_reload_enabled and module_cfg.get('auto_reload', True):
                modules_to_reload.append(module)
                self.module_loader.add_reload_safe_module(module)
        
        if modules_to_reload:
            # Add to reload queue
            self.reload_queue.update(modules_to_reload)
            
            # Schedule reload
            if not self.reload_in_progress:
                if self.reload_task and not self.reload_task.done():
                    self.reload_task.cancel()
                
                self.reload_task = asyncio.create_task(self._process_reload_queue())
    
    async def _process_reload_queue(self):
        """Process queued module reloads."""
        # Wait for configured delay
        await asyncio.sleep(self.reload_delay)
        
        if not self.reload_queue:
            return
        
        self.reload_in_progress = True
        modules_to_reload = list(self.reload_queue)
        self.reload_queue.clear()
        
        try:
            logger.info(f"Processing reload queue: {modules_to_reload}")
            
            # Group modules by reload delay
            reload_groups: Dict[float, List[str]] = {}
            for module in modules_to_reload:
                delay = self.module_config.get(module, {}).get('reload_delay', self.reload_delay)
                if delay not in reload_groups:
                    reload_groups[delay] = []
                reload_groups[delay].append(module)
            
            # Process each group
            for delay, modules in sorted(reload_groups.items()):
                await asyncio.sleep(delay)
                
                # Reload modules
                result = await self.safe_reloader.reload_multiple_safe(modules)
                
                self.stats['total_reloads'] += result['total']
                self.stats['successful_reloads'] += result['successful']
                self.stats['failed_reloads'] += result['failed']
                
                # Log results
                if result['failed'] > 0:
                    logger.error(f"Reload completed with failures: {result['successful']}/{result['total']} successful")
                    
                    # Retry failed modules if configured
                    failed_modules = [
                        module for module, mod_result in result['modules'].items()
                        if not mod_result['success']
                    ]
                    
                    if failed_modules and self.max_reload_attempts > 1:
                        logger.info(f"Retrying failed modules: {failed_modules}")
                        # Add back to queue for retry
                        self.reload_queue.update(failed_modules)
                else:
                    logger.info(f"All modules reloaded successfully: {result['successful']}/{result['total']}")
        
        except Exception as e:
            logger.error(f"Error processing reload queue: {e}")
        
        finally:
            self.reload_in_progress = False
    
    async def start(self):
        """Start the reload manager."""
        logger.info("Starting ReloadManager")
        
        self.stats['started_at'] = datetime.now().isoformat()
        
        # Start file watcher
        await self.file_watcher.start()
        
        logger.info("ReloadManager started - hot reload active")
    
    async def stop(self):
        """Stop the reload manager."""
        logger.info("Stopping ReloadManager")
        
        # Cancel any pending reload
        if self.reload_task and not self.reload_task.done():
            self.reload_task.cancel()
            try:
                await self.reload_task
            except asyncio.CancelledError:
                pass
        
        # Stop file watcher
        await self.file_watcher.stop()
        
        logger.info("ReloadManager stopped")
    
    async def reload_module(self, module_name: str, force: bool = False) -> Dict[str, Any]:
        """
        Manually reload a specific module.
        
        Args:
            module_name: Name of the module to reload
            force: Force reload even if not marked as safe
            
        Returns:
            Reload result
        """
        logger.info(f"Manual reload requested for {module_name}")
        return await self.safe_reloader.reload_module_safe(module_name, force)
    
    async def reload_all_safe_modules(self) -> Dict[str, Any]:
        """Reload all modules marked as safe."""
        safe_modules = list(self.module_loader.reload_safe_modules)
        logger.info(f"Reloading all safe modules: {len(safe_modules)} modules")
        return await self.safe_reloader.reload_multiple_safe(safe_modules)
    
    def enable_auto_reload(self):
        """Enable automatic reloading on file changes."""
        self.auto_reload_enabled = True
        logger.info("Auto-reload enabled")
    
    def disable_auto_reload(self):
        """Disable automatic reloading on file changes."""
        self.auto_reload_enabled = False
        logger.info("Auto-reload disabled")
    
    def set_module_config(self, module_name: str, config: Dict[str, Any]):
        """Set configuration for a specific module."""
        self.module_config[module_name] = config
        logger.info(f"Updated configuration for module {module_name}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reload manager statistics."""
        stats = self.stats.copy()
        stats['module_loader_stats'] = self.module_loader.get_reload_history(10)
        stats['safe_reloader_stats'] = self.safe_reloader.get_reload_stats()
        stats['tracked_instances'] = self.safe_reloader.get_tracked_instances()
        stats['watched_files_count'] = len(self.file_watcher.get_watched_files())
        return stats
    
    def get_module_config(self, module_name: Optional[str] = None) -> Dict[str, Any]:
        """Get module configuration."""
        if module_name:
            return self.module_config.get(module_name, {})
        return self.module_config.copy()
    
    def add_safe_module(self, module_name: str):
        """Add a module to the safe reload list."""
        self.module_loader.add_reload_safe_module(module_name)
        
        # Add default config if not present
        if module_name not in self.module_config:
            self.module_config[module_name] = {
                'auto_reload': True,
                'preserve_state': True,
                'reload_delay': 1.0
            }