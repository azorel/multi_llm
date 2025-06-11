"""
File Watcher for Hot Reload System
==================================

Monitors file changes and triggers reloads.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Set, Callable, Optional, Any
from datetime import datetime
import hashlib
from loguru import logger

try:
    from watchfiles import awatch
    WATCHFILES_AVAILABLE = True
except ImportError:
    WATCHFILES_AVAILABLE = False
    logger.warning("watchfiles not available, using polling-based file watcher")


class FileWatcher:
    """
    Watches for file changes and triggers callbacks.
    
    Features:
    - Efficient file watching using watchfiles or polling
    - File filtering and ignore patterns
    - Debouncing to prevent multiple rapid reloads
    - Change event batching
    """
    
    def __init__(self, watch_paths: List[Path], ignore_patterns: Optional[List[str]] = None):
        """
        Initialize the file watcher.
        
        Args:
            watch_paths: List of paths to watch
            ignore_patterns: List of glob patterns to ignore
        """
        self.watch_paths = [Path(p) for p in watch_paths]
        self.ignore_patterns = ignore_patterns or []
        
        # Default ignore patterns
        self.ignore_patterns.extend([
            '*.pyc',
            '__pycache__',
            '*.log',
            '.git',
            '.idea',
            '.vscode',
            '*.tmp',
            '*.swp',
            '.env*',
            'venv',
            '.pytest_cache',
            '*.db',
            '*.sqlite'
        ])
        
        # File change tracking
        self.file_hashes: Dict[Path, str] = {}
        self.last_check_times: Dict[Path, float] = {}
        
        # Change callbacks
        self.change_callbacks: List[Callable] = []
        
        # Debouncing
        self.debounce_delay = 0.5  # seconds
        self.pending_changes: Set[Path] = set()
        self.debounce_task: Optional[asyncio.Task] = None
        
        # Running state
        self.running = False
        self.watch_task: Optional[asyncio.Task] = None
        
        logger.info(f"FileWatcher initialized for paths: {self.watch_paths}")
    
    def should_ignore(self, file_path: Path) -> bool:
        """Check if a file should be ignored."""
        path_str = str(file_path)
        
        for pattern in self.ignore_patterns:
            if pattern in path_str:
                return True
            
            # Check glob patterns
            if file_path.match(pattern):
                return True
        
        return False
    
    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate hash of file contents."""
        try:
            if file_path.exists() and file_path.is_file():
                return hashlib.md5(file_path.read_bytes()).hexdigest()
        except Exception as e:
            logger.debug(f"Could not hash file {file_path}: {e}")
        return None
    
    def on_change(self, callback: Callable):
        """Register a callback for file changes."""
        self.change_callbacks.append(callback)
        logger.debug(f"Registered change callback: {callback}")
    
    async def _process_changes(self, changed_files: Set[Path]):
        """Process a batch of file changes."""
        if not changed_files:
            return
        
        logger.info(f"Processing {len(changed_files)} file changes")
        
        # Filter Python files
        python_files = [f for f in changed_files if f.suffix == '.py']
        
        if python_files:
            # Convert file paths to module names
            modules_to_reload = set()
            
            for file_path in python_files:
                module_name = self._file_to_module_name(file_path)
                if module_name:
                    modules_to_reload.add(module_name)
            
            # Notify callbacks
            change_event = {
                'timestamp': datetime.now().isoformat(),
                'changed_files': [str(f) for f in changed_files],
                'python_files': [str(f) for f in python_files],
                'modules': list(modules_to_reload)
            }
            
            for callback in self.change_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(change_event)
                    else:
                        callback(change_event)
                except Exception as e:
                    logger.error(f"Error in change callback: {e}")
    
    def _file_to_module_name(self, file_path: Path) -> Optional[str]:
        """Convert a file path to a module name."""
        try:
            # Get relative path from project root
            for watch_path in self.watch_paths:
                try:
                    relative_path = file_path.relative_to(watch_path)
                    
                    # Convert to module name
                    parts = list(relative_path.parts)
                    
                    # Remove .py extension
                    if parts[-1].endswith('.py'):
                        parts[-1] = parts[-1][:-3]
                    
                    # Skip __init__ files
                    if parts[-1] == '__init__':
                        parts = parts[:-1]
                    
                    # Join with dots
                    module_name = '.'.join(parts)
                    
                    # Only return if it's a src module
                    if module_name.startswith('src.'):
                        return module_name
                    
                except ValueError:
                    continue
        except Exception as e:
            logger.debug(f"Could not convert {file_path} to module name: {e}")
        
        return None
    
    async def _debounced_process_changes(self):
        """Process changes after debounce delay."""
        await asyncio.sleep(self.debounce_delay)
        
        # Process all pending changes
        changes_to_process = self.pending_changes.copy()
        self.pending_changes.clear()
        self.debounce_task = None
        
        await self._process_changes(changes_to_process)
    
    async def _handle_file_change(self, file_path: Path):
        """Handle a single file change."""
        if self.should_ignore(file_path):
            return
        
        # Add to pending changes
        self.pending_changes.add(file_path)
        
        # Cancel existing debounce task if any
        if self.debounce_task and not self.debounce_task.done():
            self.debounce_task.cancel()
        
        # Start new debounce task
        self.debounce_task = asyncio.create_task(self._debounced_process_changes())
    
    async def _watch_with_watchfiles(self):
        """Watch files using the watchfiles library."""
        logger.info("Starting file watcher with watchfiles")
        
        async for changes in awatch(*[str(p) for p in self.watch_paths]):
            if not self.running:
                break
            
            for change_type, file_path_str in changes:
                file_path = Path(file_path_str)
                await self._handle_file_change(file_path)
    
    async def _watch_with_polling(self):
        """Watch files using polling (fallback method)."""
        logger.info("Starting file watcher with polling")
        
        poll_interval = 1.0  # seconds
        
        while self.running:
            try:
                # Scan all watch paths
                for watch_path in self.watch_paths:
                    if watch_path.is_dir():
                        for file_path in watch_path.rglob('*.py'):
                            if self.should_ignore(file_path):
                                continue
                            
                            # Check if file has changed
                            current_hash = self.calculate_file_hash(file_path)
                            previous_hash = self.file_hashes.get(file_path)
                            
                            if current_hash and current_hash != previous_hash:
                                self.file_hashes[file_path] = current_hash
                                await self._handle_file_change(file_path)
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error in polling watcher: {e}")
                await asyncio.sleep(poll_interval * 2)
    
    async def start(self):
        """Start watching for file changes."""
        if self.running:
            logger.warning("File watcher already running")
            return
        
        self.running = True
        
        # Choose watch method
        if WATCHFILES_AVAILABLE:
            self.watch_task = asyncio.create_task(self._watch_with_watchfiles())
        else:
            self.watch_task = asyncio.create_task(self._watch_with_polling())
        
        logger.info("File watcher started")
    
    async def stop(self):
        """Stop watching for file changes."""
        if not self.running:
            return
        
        logger.info("Stopping file watcher")
        self.running = False
        
        # Cancel watch task
        if self.watch_task and not self.watch_task.done():
            self.watch_task.cancel()
            try:
                await self.watch_task
            except asyncio.CancelledError:
                pass
        
        # Cancel debounce task
        if self.debounce_task and not self.debounce_task.done():
            self.debounce_task.cancel()
            try:
                await self.debounce_task
            except asyncio.CancelledError:
                pass
        
        logger.info("File watcher stopped")
    
    def get_watched_files(self) -> List[str]:
        """Get list of currently watched files."""
        watched = []
        for watch_path in self.watch_paths:
            if watch_path.is_dir():
                for file_path in watch_path.rglob('*.py'):
                    if not self.should_ignore(file_path):
                        watched.append(str(file_path))
        return watched
    
    def set_debounce_delay(self, delay: float):
        """Set the debounce delay in seconds."""
        self.debounce_delay = max(0.1, delay)
        logger.info(f"Debounce delay set to {self.debounce_delay}s")