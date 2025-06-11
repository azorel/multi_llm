#!/usr/bin/env python3
"""
# DEMO CODE REMOVED: Hot Reload Demo
===============

# DEMO CODE REMOVED: Demonstrates the hot reload system capabilities.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.hot_reload import DevelopmentMode, ReloadManager, ModuleLoader, FileWatcher


# DEMO CODE REMOVED: class DemoSystem:
# DEMO CODE REMOVED: """Demo system for testing hot reload."""
    
    def __init__(self):
# DEMO CODE REMOVED: """Initialize demo system."""
        self.config = {
            'auto_reload': True,
            'reload_delay': 1.0,
            'debug_mode': True,
            'performance_monitoring': True,
            'module_config': {
                'src.tools.example_hot_reload_module': {
                    'auto_reload': True,
                    'preserve_state': True,
                    'reload_delay': 1.0
                }
            }
        }
        
        self.development_mode = None
        self.running = False
        
        # Import the example module
        from src.tools.example_hot_reload_module import ExampleProcessor, simple_function
        self.processor = ExampleProcessor()
        
# DEMO CODE REMOVED: logger.info("Demo system initialized")
    
    async def initialize(self):
# DEMO CODE REMOVED: """Initialize the demo system."""
# DEMO CODE REMOVED: logger.info("🔧 Initializing demo system with hot reload...")
        
        # Initialize development mode
        self.development_mode = DevelopmentMode(self, self.config)
        
        # Track the example processor instance
        self.development_mode.reload_manager.safe_reloader.track_instance(
            'src.tools.example_hot_reload_module',
            self.processor
        )
        
        # Enable development mode
        await self.development_mode.enable()
        
# DEMO CODE REMOVED: logger.info("✅ Demo system initialized")
    
# DEMO CODE REMOVED: async def run_demo(self):
# DEMO CODE REMOVED: """Run the hot reload demo."""
        self.running = True
        
# DEMO CODE REMOVED: logger.info("🚀 HOT RELOAD DEMO STARTED")
        logger.info("=" * 50)
        logger.info("📝 Instructions:")
        logger.info("1. The system is watching src/tools/example_hot_reload_module.py")
        logger.info("2. Open that file in your editor")
        logger.info("3. Modify the process_data method or simple_function")
        logger.info("4. Save the file and watch the hot reload happen")
        logger.info("5. The system will continue using the updated code")
        logger.info("6. Press Ctrl+C to stop")
        logger.info("")
        
        counter = 0
        
        try:
            while self.running:
                counter += 1
                
                # Import and use the module
                from src.tools.example_hot_reload_module import simple_function, increment_counter
                
                # Test the functions
# DEMO CODE REMOVED: logger.info(f"🔄 Demo cycle {counter}")
                
                # Use the processor instance
                result = self.processor.process_data(f"test data {counter}")
                logger.info(f"Processor result: {result}")
                
                # Use the simple function
                func_result = simple_function(f"cycle {counter}")
                logger.info(f"Function result: {func_result}")
                
                # Test global state
                global_count = increment_counter()
                logger.info(f"Global counter: {global_count}")
                
                logger.info("-" * 30)
                
                # Wait before next cycle
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
# DEMO CODE REMOVED: logger.info("Demo interrupted by user")
        
        finally:
            self.running = False
            if self.development_mode:
                await self.development_mode.disable()
    
    async def show_stats(self):
        """Show hot reload statistics."""
        if not self.development_mode:
            return
        
        stats = self.development_mode.get_statistics()
        
        logger.info("📊 HOT RELOAD STATISTICS:")
        logger.info("=" * 30)
        
        if 'reload_manager_stats' in stats and stats['reload_manager_stats']:
            reload_stats = stats['reload_manager_stats']
            logger.info(f"File changes detected: {reload_stats.get('total_file_changes', 0)}")
            logger.info(f"Total reloads: {reload_stats.get('total_reloads', 0)}")
            logger.info(f"Successful reloads: {reload_stats.get('successful_reloads', 0)}")
            logger.info(f"Failed reloads: {reload_stats.get('failed_reloads', 0)}")
            
            if 'safe_reloader_stats' in reload_stats:
                safe_stats = reload_stats['safe_reloader_stats']
                logger.info(f"Last reload: {safe_stats.get('last_reload', 'Never')}")
            
            if 'tracked_instances' in reload_stats:
                tracked = reload_stats['tracked_instances']
                logger.info(f"Tracked instances: {sum(tracked.values())} across {len(tracked)} modules")


async def test_module_loader():
    """Test the module loader directly."""
    logger.info("🧪 TESTING MODULE LOADER")
    logger.info("=" * 40)
    
    loader = ModuleLoader()
    
    # Add our example module to safe list
    loader.add_reload_safe_module('src.tools.example_hot_reload_module')
    
    # Test loading the module
    try:
        import src.tools.example_hot_reload_module
        logger.info("✅ Module imported successfully")
        
        # Test reload
        result = loader.reload_module('src.tools.example_hot_reload_module')
        
        if result['success']:
            logger.info("✅ Module reloaded successfully")
            logger.info(f"State preserved: {result['state_preserved']}")
        else:
            logger.error(f"❌ Reload failed: {result['error']}")
        
        # Show reload history
        history = loader.get_reload_history(5)
        logger.info(f"📋 Recent reload history: {len(history)} entries")
        for entry in history:
            status = "✅" if entry['success'] else "❌"
            logger.info(f"   {status} {entry['module']} - {entry['timestamp']}")
    
    except Exception as e:
        logger.error(f"❌ Module loader test failed: {e}")


async def test_file_watcher():
    """Test the file watcher directly."""
    logger.info("🧪 TESTING FILE WATCHER")
    logger.info("=" * 40)
    
    project_root = Path(__file__).parent
    watch_paths = [project_root / 'src']
    
    watcher = FileWatcher(watch_paths)
    
    changes_detected = []
    
    def on_change(change_event):
        changes_detected.append(change_event)
        logger.info(f"📁 File change detected: {len(change_event['changed_files'])} files")
        for file_path in change_event['changed_files']:
            logger.info(f"   - {file_path}")
        if change_event['modules']:
            logger.info(f"   Modules to reload: {change_event['modules']}")
    
    watcher.on_change(on_change)
    
    logger.info(f"Watching {len(watch_paths)} paths for changes...")
    logger.info("Modify any .py file in src/ to test file watching")
    logger.info("Will watch for 30 seconds...")
    
    await watcher.start()
    
    try:
        await asyncio.sleep(30)
    except KeyboardInterrupt:
        logger.info("File watcher test interrupted")
    finally:
        await watcher.stop()
    
    logger.info(f"📊 Total changes detected: {len(changes_detected)}")


async def main():
    """Main entry point."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>"
    )
    
    import argparse
    
# DEMO CODE REMOVED: parser = argparse.ArgumentParser(description='Hot reload demo')
    parser.add_argument('--test-loader', action='store_true', help='Test module loader')
    parser.add_argument('--test-watcher', action='store_true', help='Test file watcher')
# DEMO CODE REMOVED: parser.add_argument('--full-demo', action='store_true', help='Run full demo (default)')
    
    args = parser.parse_args()
    
    if args.test_loader:
        await test_module_loader()
    elif args.test_watcher:
        await test_file_watcher()
    else:
# DEMO CODE REMOVED: # Run full demo
# DEMO CODE REMOVED: demo = DemoSystem()
# DEMO CODE REMOVED: await demo.initialize()
        
        try:
# DEMO CODE REMOVED: await demo.run_demo()
        finally:
# DEMO CODE REMOVED: await demo.show_stats()


if __name__ == "__main__":
    asyncio.run(main())