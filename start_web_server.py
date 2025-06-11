#!/usr/bin/env python3
"""
LifeOS Web Server Launcher
==========================

Launch the local Notion-like web application that replaces your Notion workspace.
"""

import os
import sys
from pathlib import Path

def main():
    """Launch the LifeOS web server."""
    print("🚀 Starting LifeOS - Local Notion Replacement")
    print("=" * 60)
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check if virtual environment exists
    venv_path = project_root / "venv"
    if not venv_path.exists():
        print("❌ Virtual environment not found. Creating one...")
        os.system("python3 -m venv venv")
        print("✅ Virtual environment created")
    
    # Import and run the web server
    try:
        from web_server import run_server
        print("✅ All dependencies loaded successfully")
        print("")
        run_server()
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💾 Installing required packages...")
        os.system("source venv/bin/activate && pip install flask flask-socketio python-dotenv python-socketio eventlet")
        print("✅ Dependencies installed. Please run again.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()