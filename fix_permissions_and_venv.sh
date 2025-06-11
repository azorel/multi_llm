#!/bin/bash
# Fix Permissions and Recreate Virtual Environment
# This script fixes permission issues and recreates a clean virtual environment

set -e  # Exit on error

echo "🔧 Fixing Permissions and Virtual Environment..."
echo "================================================"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 1. Fix current user ownership of the entire project
echo ""
echo "🔐 Fixing file ownership and permissions..."
sudo chown -R $USER:$USER .
find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;

# Make scripts executable
chmod +x *.sh 2>/dev/null || true

echo "✅ Permissions fixed"

# 2. Remove and recreate virtual environment
echo ""
echo "🗑️  Removing old virtual environment..."
if [ -d "venv" ]; then
    rm -rf venv
    echo "✅ Old virtual environment removed"
fi

echo ""
echo "🐍 Creating new virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip to latest version
echo "  Upgrading pip..."
pip install --upgrade pip

# Install main requirements first
echo "  Installing main requirements..."
if [ -f "requirements-py312.txt" ]; then
    echo "  Using Python 3.12 compatible requirements..."
    pip install -r requirements-py312.txt
elif [ -f "requirements.txt" ]; then
    echo "  Trying original requirements..."
    pip install -r requirements.txt || {
        echo "  ⚠️  Some packages failed. Installing core packages individually..."
        # Install core packages that should work
        pip install fastapi uvicorn pydantic httpx requests
        pip install loguru rich click pyyaml python-dotenv
        pip install tenacity asyncio-throttle aiofiles
        pip install openai anthropic google-generativeai
        pip install notion-client
        pip install "cryptography>=42.0.0"
        pip install passlib[bcrypt] PyJWT
        pip install youtube-transcript-api yt-dlp
    }
fi

# Install dev requirements with better error handling
echo "  Installing development requirements..."

if [ -f "requirements-dev-py312.txt" ]; then
    echo "  Using Python 3.12 compatible dev requirements..."
    pip install -r requirements-dev-py312.txt || {
        echo "  ⚠️  Some dev tools failed, installing individually..."
        pip install pytest pytest-asyncio pytest-cov pytest-mock
        pip install flake8 black isort mypy
        pip install bandit "safety>=3.0.0"
    }
else
    # Essential dev tools (install these individually to avoid conflicts)
    echo "  → Installing testing tools..."
    pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-xdist

    echo "  → Installing code quality tools..."
    pip install flake8 black isort mypy

    echo "  → Installing security tools..."
    pip install bandit

    # Try to install safety with newer version
    echo "  → Installing safety scanner..."
    pip install "safety>=3.0.0" || echo "    ⚠️  Could not install safety, skipping..."

    # Install documentation tools
    echo "  → Installing documentation tools..."
    pip install sphinx sphinx-rtd-theme || echo "    ⚠️  Could not install docs tools, skipping..."

    # Install debugging tools
    echo "  → Installing debugging tools..."
    pip install ipdb debugpy || echo "    ⚠️  Could not install debug tools, skipping..."

    # Install testing utilities
    echo "  → Installing test utilities..."
    pip install httpx respx responses || echo "    ⚠️  Could not install test utilities, skipping..."

    # Install performance tools
    echo "  → Installing performance tools..."
    pip install locust memory-profiler || echo "    ⚠️  Could not install performance tools, skipping..."

    # Install pre-commit
    echo "  → Installing pre-commit..."
    pip install pre-commit || echo "    ⚠️  Could not install pre-commit, skipping..."
fi

echo ""
echo "✅ Virtual environment recreated successfully!"

# 3. Fix Node.js projects
echo ""
echo "📦 Fixing Node.js dependencies..."

# Fix notion-mcp-server
if [ -d "notion-mcp-server" ]; then
    echo "  → Fixing notion-mcp-server..."
    cd notion-mcp-server
    
    # Fix ownership and permissions
    sudo chown -R $USER:$USER .
    
    # Remove and reinstall node_modules to fix any permission issues
    if [ -d "node_modules" ]; then
        rm -rf node_modules package-lock.json
    fi
    
    # Create directories with correct permissions
    mkdir -p bin build dist
    chmod 755 bin build dist
    
    # Install dependencies
    npm install
    
    cd ..
    echo "  ✅ notion-mcp-server fixed"
fi

# Fix sequential-thinking server
if [ -d "mcp-servers/sequential-thinking" ]; then
    echo "  → Fixing sequential-thinking server..."
    cd mcp-servers/sequential-thinking
    
    # Fix ownership and permissions
    sudo chown -R $USER:$USER .
    
    # Remove and reinstall node_modules
    if [ -d "node_modules" ]; then
        rm -rf node_modules package-lock.json
    fi
    
    # Create dist directory
    mkdir -p dist
    chmod 755 dist
    
    # Install dependencies
    npm install
    
    # Try to build, but don't fail if it doesn't work
    echo "    Attempting to build..."
    npm run build || echo "    ⚠️  Build failed, but project setup is complete"
    
    cd ../..
    echo "  ✅ sequential-thinking server fixed"
fi

# 4. Test the setup
echo ""
echo "🧪 Testing the setup..."

# Test Python environment
source venv/bin/activate

echo "  → Testing Python tools..."
python -c "import pytest; print('✅ pytest works')" || echo "    ⚠️  pytest issue"
python -c "import black; print('✅ black works')" || echo "    ⚠️  black issue"
python -c "import flake8; print('✅ flake8 works')" || echo "    ⚠️  flake8 issue"
python -c "import mypy; print('✅ mypy works')" || echo "    ⚠️  mypy issue"

# Test if main application modules can be imported
echo "  → Testing main application imports..."
python -c "from src.main import *" 2>/dev/null && echo "✅ Main application imports work" || echo "    ℹ️  Some import issues (normal if dependencies missing)"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 What was fixed:"
echo "  ✅ File ownership and permissions corrected"
echo "  ✅ Virtual environment recreated cleanly"
echo "  ✅ Python development tools installed"
echo "  ✅ Node.js dependencies reinstalled"
echo "  ✅ Build directories created with proper permissions"
echo ""
echo "🚀 Next steps:"
echo "  • Run: source venv/bin/activate"
echo "  • Run: ./lint.sh (if created by fix_dev_environment.sh)"
echo "  • Run: ./test.sh (if created by fix_dev_environment.sh)"