"""
Example Hot Reload Module
=========================

A simple module for testing hot reload functionality.
Modify the functions in this file to test hot reloading.
"""

from datetime import datetime
from loguru import logger


class ExampleProcessor:
    """Example processor class for testing hot reload."""
    
    def __init__(self):
        """Initialize the processor."""
        self.version = "1.0.0"
        self.created_at = datetime.now()
        self.process_count = 0
        logger.info(f"ExampleProcessor initialized - version {self.version}")
    
    def process_data(self, data: str) -> str:
        """
        Process some data.
        
        Try changing this function and saving the file to test hot reload!
        """
        self.process_count += 1
        
        # Modify this return statement to test hot reload
        result = f"[v{self.version}] Processed: {data.upper()} (count: {self.process_count})"
        
        logger.info(f"Processing data: {data} -> {result}")
        return result
    
    def preserve_state(self) -> dict:
        """Preserve state during hot reload."""
        return {
            'process_count': self.process_count,
            'created_at': self.created_at.isoformat()
        }
    
    def restore_state(self, state: dict):
        """Restore state after hot reload."""
        self.process_count = state.get('process_count', 0)
        if 'created_at' in state:
            self.created_at = datetime.fromisoformat(state['created_at'])
        logger.info(f"State restored - process_count: {self.process_count}")


def simple_function(message: str) -> str:
    """
    A simple function for testing hot reload.
    
    Try modifying this function and saving the file!
    """
    # Change this message to test hot reload
    return f"Hello from hot reload! Message: {message}"


def get_current_time() -> str:
    """Get current time - modify this to test hot reload."""
    # Try changing the format string
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Global variable for testing state preservation
GLOBAL_COUNTER = 0

def increment_counter() -> int:
    """Increment and return global counter."""
    global GLOBAL_COUNTER
    GLOBAL_COUNTER += 1
    return GLOBAL_COUNTER


# Example configuration
CONFIG = {
    "name": "Example Hot Reload Module",
    "version": "1.0.0",
    "features": ["hot_reload", "state_preservation", "testing"]
}

logger.info(f"Module loaded: {CONFIG['name']} v{CONFIG['version']}")