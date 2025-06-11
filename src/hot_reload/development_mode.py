"""
Development Mode for Hot Reload System
=====================================

Provides development mode features for the autonomous agent.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
from loguru import logger

from .reload_manager import ReloadManager

if TYPE_CHECKING:
    from ..main import AutonomousAgentSystem


class DevelopmentMode:
    """
    Manages development mode features for the autonomous agent.
    
    Features:
    - Hot reload integration with the main system
    - Development utilities and debugging aids
    - Performance monitoring during development
    - Safe integration with production code
    """
    
    def __init__(self, agent_system: 'AutonomousAgentSystem', config: Optional[Dict[str, Any]] = None):
        """
        Initialize development mode.
        
        Args:
            agent_system: The main autonomous agent system
            config: Optional development configuration
        """
        self.agent_system = agent_system
        self.config = config or {}
        
        # Get project root
        self.project_root = Path(__file__).parent.parent.parent
        
        # Load hot reload configuration
        self._load_hot_reload_config()
        
        # Initialize reload manager
        reload_config = {
            'auto_reload': self.config.get('auto_reload', True),
            'reload_delay': self.config.get('reload_delay', 1.0),
            'max_reload_attempts': self.config.get('max_reload_attempts', 3),
            'ignore_patterns': self.config.get('ignore_patterns', []),
            'module_config': self.config.get('module_config', {})
        }
        
        self.reload_manager = ReloadManager(self.project_root, reload_config)
        
        # Development features
        self.enabled = False
        self.debug_mode = self.config.get('debug_mode', True)
        self.performance_monitoring = self.config.get('performance_monitoring', True)
        
        # Performance tracking
        self.performance_stats: Dict[str, Any] = {}
        
        logger.info("Development mode initialized")
    
    def _load_hot_reload_config(self):
        """Load hot reload configuration from file."""
        config_file = self.project_root / 'config' / 'hot_reload.yaml'
        
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r') as f:
                    hot_reload_config = yaml.safe_load(f)
                
                # Merge hot reload config with provided config
                if 'hot_reload' in hot_reload_config:
                    for key, value in hot_reload_config['hot_reload'].items():
                        if key not in self.config:
                            self.config[key] = value
                
                # Add file watcher config
                if 'file_watcher' in hot_reload_config:
                    if 'ignore_patterns' not in self.config:
                        self.config['ignore_patterns'] = []
                    self.config['ignore_patterns'].extend(
                        hot_reload_config['file_watcher'].get('ignore_patterns', [])
                    )
                
                # Add module configurations
                if 'modules' in hot_reload_config:
                    if 'module_config' not in self.config:
                        self.config['module_config'] = {}
                    
                    for module, module_cfg in hot_reload_config['modules'].items():
                        # Convert priority to reload delay
                        if 'priority' in module_cfg:
                            priority_delays = {'high': 2.0, 'medium': 1.5, 'low': 1.0}
                            if 'reload_delay' not in module_cfg:
                                module_cfg['reload_delay'] = priority_delays.get(
                                    module_cfg['priority'], 1.0
                                )
                        
                        self.config['module_config'][module] = module_cfg
                
                logger.info(f"Loaded hot reload configuration from {config_file}")
                
            except ImportError:
                logger.warning("PyYAML not available, using default configuration")
            except Exception as e:
                logger.warning(f"Failed to load hot reload config: {e}")
        else:
            logger.debug(f"Hot reload config file not found: {config_file}")
    
    async def enable(self):
        """Enable development mode."""
        if self.enabled:
            logger.warning("Development mode already enabled")
            return
        
        logger.info("Enabling development mode")
        
        # Register reload hooks for critical components
        await self._register_reload_hooks()
        
        # Track agent system instances
        await self._track_system_instances()
        
        # Start reload manager
        await self.reload_manager.start()
        
        # Enable additional logging
        if self.debug_mode:
            logger.info("Debug mode enabled - verbose logging active")
        
        self.enabled = True
        logger.info("Development mode enabled - hot reload active")
    
    async def disable(self):
        """Disable development mode."""
        if not self.enabled:
            return
        
        logger.info("Disabling development mode")
        
        # Stop reload manager
        await self.reload_manager.stop()
        
        self.enabled = False
        logger.info("Development mode disabled")
    
    async def _register_reload_hooks(self):
        """Register pre/post reload hooks for system components."""
        
        # LifeOS Automation Engine hooks
        async def pre_reload_lifeos(module_name: str):
            logger.info(f"Preparing LifeOS automation engine for reload")
            if hasattr(self.agent_system, 'lifeos_automation_engine'):
                # Could pause automation tasks here if needed
                pass
        
        async def post_reload_lifeos(module_name: str):
            logger.info(f"LifeOS automation engine reloaded")
            if hasattr(self.agent_system, 'lifeos_automation_engine'):
                # Reinitialize if needed
                try:
                    await self.agent_system._initialize_lifeos_automation()
                except Exception as e:
                    logger.error(f"Failed to reinitialize LifeOS automation: {e}")
        
        self.reload_manager.safe_reloader.add_pre_reload_hook(
            'src.automation.lifeos_automation_engine', pre_reload_lifeos
        )
        self.reload_manager.safe_reloader.add_post_reload_hook(
            'src.automation.lifeos_automation_engine', post_reload_lifeos
        )
        
        # YouTube Processor hooks
        async def pre_reload_youtube(module_name: str):
            logger.info(f"Preparing YouTube processor for reload")
        
        async def post_reload_youtube(module_name: str):
            logger.info(f"YouTube processor reloaded")
            if hasattr(self.agent_system, 'youtube_channel_processor'):
                try:
                    await self.agent_system._initialize_youtube_processor()
                except Exception as e:
                    logger.error(f"Failed to reinitialize YouTube processor: {e}")
        
        self.reload_manager.safe_reloader.add_pre_reload_hook(
            'src.processors.youtube_channel_processor', pre_reload_youtube
        )
        self.reload_manager.safe_reloader.add_post_reload_hook(
            'src.processors.youtube_channel_processor', post_reload_youtube
        )
        
        # Notion MCP Client hooks
# NOTION_REMOVED:         async def pre_reload_notion(module_name: str):
            logger.info(f"Preparing Notion MCP client for reload")
        
# NOTION_REMOVED:         async def post_reload_notion(module_name: str):
            logger.info(f"Notion MCP client reloaded")
            # Notion client typically maintains connection, just log
        
        self.reload_manager.safe_reloader.add_pre_reload_hook(
            'src.integrations.notion_mcp_client', pre_reload_notion
        )
        self.reload_manager.safe_reloader.add_post_reload_hook(
            'src.integrations.notion_mcp_client', post_reload_notion
        )
    
    async def _track_system_instances(self):
        """Track agent system instances for state preservation."""
        
        # Track main components
        if hasattr(self.agent_system, 'lifeos_automation_engine') and self.agent_system.lifeos_automation_engine:
            self.reload_manager.safe_reloader.track_instance(
                'src.automation.lifeos_automation_engine',
                self.agent_system.lifeos_automation_engine
            )
        
        if hasattr(self.agent_system, 'youtube_channel_processor') and self.agent_system.youtube_channel_processor:
            self.reload_manager.safe_reloader.track_instance(
                'src.processors.youtube_channel_processor',
                self.agent_system.youtube_channel_processor
            )
        
        if hasattr(self.agent_system, 'notion_client') and self.agent_system.notion_client:
            self.reload_manager.safe_reloader.track_instance(
                'src.integrations.notion_mcp_client',
                self.agent_system.notion_client
            )
        
        # Track background tasks
        for i, task in enumerate(self.agent_system.background_tasks):
            self.reload_manager.safe_reloader.register_background_task(
                f'system_background_task_{i}', task
            )
    
    async def reload_module(self, module_name: str, force: bool = False) -> Dict[str, Any]:
        """
        Manually reload a specific module.
        
        Args:
            module_name: Name of the module to reload
            force: Force reload even if not marked as safe
            
        Returns:
            Reload result
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Development mode not enabled'
            }
        
        return await self.reload_manager.reload_module(module_name, force)
    
    async def reload_all_safe_modules(self) -> Dict[str, Any]:
        """Reload all modules marked as safe."""
        if not self.enabled:
            return {
                'success': False,
                'error': 'Development mode not enabled'
            }
        
        return await self.reload_manager.reload_all_safe_modules()
    
    def add_safe_module(self, module_name: str):
        """Add a module to the safe reload list."""
        self.reload_manager.add_safe_module(module_name)
    
    def set_auto_reload(self, enabled: bool):
        """Enable or disable auto-reload on file changes."""
        if enabled:
            self.reload_manager.enable_auto_reload()
        else:
            self.reload_manager.disable_auto_reload()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get development mode statistics."""
        stats = {
            'enabled': self.enabled,
            'debug_mode': self.debug_mode,
            'performance_monitoring': self.performance_monitoring,
            'reload_manager_stats': self.reload_manager.get_statistics() if self.enabled else None
        }
        
        if self.performance_monitoring:
            stats['performance_stats'] = self.performance_stats
        
        return stats
    
    def log_performance(self, operation: str, duration: float, details: Optional[Dict[str, Any]] = None):
        """Log performance metrics during development."""
        if not self.performance_monitoring:
            return
        
        if operation not in self.performance_stats:
            self.performance_stats[operation] = {
                'count': 0,
                'total_duration': 0,
                'min_duration': float('inf'),
                'max_duration': 0,
                'avg_duration': 0,
                'last_recorded': None
            }
        
        stats = self.performance_stats[operation]
        stats['count'] += 1
        stats['total_duration'] += duration
        stats['min_duration'] = min(stats['min_duration'], duration)
        stats['max_duration'] = max(stats['max_duration'], duration)
        stats['avg_duration'] = stats['total_duration'] / stats['count']
        stats['last_recorded'] = datetime.now().isoformat()
        
        if details:
            stats['last_details'] = details
        
        if duration > stats['avg_duration'] * 2:
            logger.warning(f"Performance: {operation} took {duration:.2f}s (2x average)")
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run development diagnostics."""
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'development_mode': self.enabled,
            'system_health': {},
            'module_status': {},
            'background_tasks': {}
        }
        
        # Check system health
        if hasattr(self.agent_system, 'component_health'):
            diagnostics['system_health'] = self.agent_system.component_health.copy()
        
        # Check module status
        for module in self.reload_manager.module_loader.reload_safe_modules:
            diagnostics['module_status'][module] = {
                'loaded': module in self.reload_manager.module_loader.loaded_modules,
                'has_state': module in self.reload_manager.module_loader.module_states
            }
        
        # Check background tasks
        for i, task in enumerate(self.agent_system.background_tasks):
            diagnostics['background_tasks'][f'task_{i}'] = {
                'done': task.done(),
                'cancelled': task.cancelled()
            }
        
        return diagnostics