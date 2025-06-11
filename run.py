#!/usr/bin/env python3
"""
LifeOS Autonomous System - Simple Runner
========================================

Simple script to run the LifeOS autonomous system with proper environment setup.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run the LifeOS autonomous system."""
    print("🚀 LifeOS Autonomous System Launcher")
    print("=" * 40)
    
    # Check if we're in a virtual environment
    venv_path = Path("venv")
    if venv_path.exists():
        # Use virtual environment
        if os.name == 'nt':  # Windows
            python_cmd = str(venv_path / "Scripts" / "python.exe")
        else:  # Unix/Linux/macOS
            python_cmd = str(venv_path / "bin" / "python")
        
        print(f"✅ Using virtual environment: {python_cmd}")
    else:
        # Use system Python
        python_cmd = "python3"
        print(f"⚠️ Using system Python: {python_cmd}")
    
    # Check for .env file
    if not Path(".env").exists():
        print("❌ .env file not found!")
        print("📋 Please copy .env.example to .env and configure your tokens")
        return False
    
    print("✅ Configuration file found")
    
    try:
        print("🎯 Starting LifeOS Autonomous System...")
        print("🛑 Press Ctrl+C to stop")
        print("-" * 40)
        
        # Run the main application
        subprocess.run([python_cmd, "main.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n👋 System stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ System error: {e}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Python interpreter not found: {python_cmd}")
        print("💡 Try: python3 run.py")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)