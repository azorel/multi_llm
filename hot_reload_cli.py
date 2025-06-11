#!/usr/bin/env python3
"""
Hot Reload CLI Tool
===================

Command-line interface for managing hot reload during development.
"""

import asyncio
import sys
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.hot_reload import ModuleLoader, ReloadManager


class HotReloadCLI:
    """CLI for hot reload management."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.project_root = Path(__file__).parent
        self.module_loader = ModuleLoader()
        self.reload_manager = ReloadManager(self.project_root)
    
    async def list_safe_modules(self):
        """List all modules marked as safe for reload."""
        safe_modules = list(self.module_loader.reload_safe_modules)
        
        print(f"📋 Safe Reload Modules ({len(safe_modules)}):")
        print("=" * 50)
        
        if not safe_modules:
            print("No modules marked as safe for reload.")
            return
        
        for i, module in enumerate(sorted(safe_modules), 1):
            print(f"{i:2}. {module}")
    
    async def reload_module(self, module_name: str, force: bool = False):
        """Reload a specific module."""
        print(f"🔄 Reloading module: {module_name}")
        print("-" * 40)
        
        result = self.module_loader.reload_module(module_name, force)
        
        if result['success']:
            print("✅ Module reloaded successfully")
            print(f"   State preserved: {result['state_preserved']}")
            print(f"   Timestamp: {result['timestamp']}")
        else:
            print("❌ Module reload failed")
            print(f"   Error: {result['error']}")
    
    async def reload_all_safe(self):
        """Reload all safe modules."""
        safe_modules = list(self.module_loader.reload_safe_modules)
        
        if not safe_modules:
            print("No safe modules to reload.")
            return
        
        print(f"🔄 Reloading {len(safe_modules)} safe modules...")
        print("=" * 50)
        
        results = self.module_loader.reload_multiple(safe_modules)
        
        print(f"📊 Reload Summary:")
        print(f"   Total: {results['total']}")
        print(f"   Successful: {results['successful']}")
        print(f"   Failed: {results['failed']}")
        
        if results['failed'] > 0:
            print("\n❌ Failed modules:")
            for module, result in results['modules'].items():
                if not result['success']:
                    print(f"   - {module}: {result['error']}")
    
    async def show_reload_history(self, limit: int = 10):
        """Show recent reload history."""
        history = self.module_loader.get_reload_history(limit)
        
        print(f"📋 Recent Reload History (last {limit}):")
        print("=" * 60)
        
        if not history:
            print("No reload history available.")
            return
        
        for entry in history:
            status = "✅" if entry['success'] else "❌"
            timestamp = entry['timestamp'][:19]  # Remove microseconds
            
            print(f"{status} {timestamp} - {entry['module']}")
            if not entry['success']:
                print(f"    Error: {entry['error']}")
            elif entry['state_preserved']:
                print(f"    State preserved")
    
    async def add_safe_module(self, module_name: str):
        """Add a module to the safe reload list."""
        self.module_loader.add_reload_safe_module(module_name)
        print(f"✅ Added {module_name} to safe reload list")
    
    async def watch_files(self, duration: int = 60):
        """Watch for file changes for a specified duration."""
        print(f"👀 Watching for file changes for {duration} seconds...")
        print("Modify any .py file in src/ to test")
        print("-" * 40)
        
        from src.hot_reload import FileWatcher
        
        watch_paths = [self.project_root / 'src']
        watcher = FileWatcher(watch_paths)
        
        changes_count = 0
        
        def on_change(change_event):
            nonlocal changes_count
            changes_count += 1
            
            print(f"📁 Change #{changes_count} detected:")
            for file_path in change_event['changed_files']:
                print(f"   - {Path(file_path).name}")
            
            if change_event['modules']:
                print(f"   Modules: {', '.join(change_event['modules'])}")
        
        watcher.on_change(on_change)
        
        await watcher.start()
        
        try:
            await asyncio.sleep(duration)
        except KeyboardInterrupt:
            print("\nWatching interrupted")
        finally:
            await watcher.stop()
        
        print(f"\n📊 Total changes detected: {changes_count}")
    
    async def clear_module_cache(self, module_name: str):
        """Clear module from all caches."""
        self.module_loader.clear_module_cache(module_name)
        print(f"🗑️ Cleared cache for {module_name}")
    
    async def show_module_info(self, module_name: str):
        """Show information about a module."""
        print(f"📄 Module Information: {module_name}")
        print("=" * 50)
        
        # Check if module is loaded
        loaded = module_name in sys.modules
        print(f"Loaded: {'Yes' if loaded else 'No'}")
        
        # Check if safe for reload
        safe = self.module_loader.is_reload_safe(module_name)
        print(f"Safe for reload: {'Yes' if safe else 'No'}")
        
        # Check if has saved state
        has_state = module_name in self.module_loader.module_states
        print(f"Has saved state: {'Yes' if has_state else 'No'}")
        
        # Check dependencies
        deps = self.module_loader.module_dependencies.get(module_name, set())
        print(f"Dependencies: {len(deps)}")
        for dep in sorted(deps):
            print(f"   - {dep}")


async def main():
    """Main CLI entry point."""
    # Configure logging
    logger.remove()
    
    parser = argparse.ArgumentParser(description='Hot Reload CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List safe modules
    subparsers.add_parser('list', help='List safe reload modules')
    
    # Reload module
    reload_parser = subparsers.add_parser('reload', help='Reload a specific module')
    reload_parser.add_argument('module', help='Module name to reload')
    reload_parser.add_argument('--force', action='store_true', help='Force reload even if not safe')
    
    # Reload all safe modules
    subparsers.add_parser('reload-all', help='Reload all safe modules')
    
    # Show reload history
    history_parser = subparsers.add_parser('history', help='Show reload history')
    history_parser.add_argument('--limit', type=int, default=10, help='Number of entries to show')
    
    # Add safe module
    add_parser = subparsers.add_parser('add-safe', help='Add module to safe reload list')
    add_parser.add_argument('module', help='Module name to add')
    
    # Watch files
    watch_parser = subparsers.add_parser('watch', help='Watch for file changes')
    watch_parser.add_argument('--duration', type=int, default=60, help='Watch duration in seconds')
    
    # Clear cache
    clear_parser = subparsers.add_parser('clear-cache', help='Clear module cache')
    clear_parser.add_argument('module', help='Module name to clear')
    
    # Module info
    info_parser = subparsers.add_parser('info', help='Show module information')
    info_parser.add_argument('module', help='Module name to inspect')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = HotReloadCLI()
    
    try:
        if args.command == 'list':
            await cli.list_safe_modules()
        elif args.command == 'reload':
            await cli.reload_module(args.module, args.force)
        elif args.command == 'reload-all':
            await cli.reload_all_safe()
        elif args.command == 'history':
            await cli.show_reload_history(args.limit)
        elif args.command == 'add-safe':
            await cli.add_safe_module(args.module)
        elif args.command == 'watch':
            await cli.watch_files(args.duration)
        elif args.command == 'clear-cache':
            await cli.clear_module_cache(args.module)
        elif args.command == 'info':
            await cli.show_module_info(args.module)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())