#!/usr/bin/env python3
"""
Development Runner for Autonomous Agent
======================================

Runs the autonomous agent with hot reload enabled for development.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import main as run_main


async def run_development():
    """Run the agent in development mode."""
    # Set development environment variable
    os.environ['DEVELOPMENT_MODE'] = 'true'
    
    print("🚀 Starting Autonomous Agent in DEVELOPMENT MODE")
    print("🔄 Hot reload is ENABLED")
    print("📁 Watching for changes in src/")
    print("-" * 50)
    
    # Run the main application
    await run_main()


if __name__ == "__main__":
    try:
        asyncio.run(run_development())
    except KeyboardInterrupt:
        print("\n👋 Development server stopped")