#!/bin/bash
# ================================================================
# Autonomous Multi-LLM Agent System - Dependency Installation
# ================================================================
# This script installs all required Python packages and system dependencies
# Run with: sudo bash install_dependencies.sh

set -e  # Exit on any error

echo "🤖 AUTONOMOUS MULTI-LLM AGENT SYSTEM - DEPENDENCY INSTALLER"
echo "============================================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   echo "Usage: sudo bash install_dependencies.sh"
   exit 1
fi

echo "📦 Updating system packages..."
apt update

echo ""
echo "🐍 Installing Python development tools..."
apt install -y \
    python3-full \
    python3-pip \
    python3-dev \
    python3-venv \
    build-essential \
    curl \
    wget \
    git

echo ""
echo "🌐 Installing Node.js for MCP servers..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

echo ""
echo "🔧 Installing system libraries for Python packages..."
apt install -y \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    pkg-config

echo ""
echo "🎬 Installing media processing tools..."
apt install -y \
    ffmpeg \
    youtube-dl

# Install yt-dlp (newer alternative to youtube-dl)
echo ""
echo "📹 Installing yt-dlp..."
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
chmod a+rx /usr/local/bin/yt-dlp

echo ""
echo "🐍 Installing Python packages globally..."
pip3 install --break-system-packages \
    youtube-transcript-api \
    yt-dlp \
    aiofiles \
    aiohttp \
    fastapi \
    uvicorn \
    pydantic \
    httpx \
    requests \
    asyncio-throttle \
    sqlalchemy \
    pyyaml \
    python-dotenv \
    jsonschema \
    loguru \
    prometheus-client \
    psutil \
    watchdog \
    numpy \
    scipy \
    scikit-learn \
    tenacity \
    circuitbreaker \
    python-consul \
    redis \
    aioredis \
    openai \
    anthropic \
    google-generativeai \
    PyGithub \
    notion-client \
    cryptography \
    passlib \
    click \
    rich \
    python-dateutil \
    orjson \
    Pillow \
    PyJWT \
    defusedxml \
    websockets

echo ""
echo "🔧 Setting up virtual environment with all packages..."
cd /home/ikino/dev/autonomous-multi-llm-agent

# Remove old venv if it exists
if [ -d "venv" ]; then
    echo "🗑️ Removing old virtual environment..."
    rm -rf venv
fi

# Create new venv
echo "📦 Creating new virtual environment..."
python3 -m venv venv

# Activate and install packages
echo "🔧 Installing packages in virtual environment..."
source venv/bin/activate

pip install --upgrade pip

# Install all required packages
pip install \
    youtube-transcript-api \
    yt-dlp \
    aiofiles \
    aiohttp \
    fastapi \
    uvicorn \
    pydantic \
    httpx \
    requests \
    asyncio-throttle \
    sqlalchemy \
    pyyaml \
    python-dotenv \
    jsonschema \
    loguru \
    prometheus-client \
    psutil \
    watchdog \
    numpy \
    scipy \
    scikit-learn \
    tenacity \
    circuitbreaker \
    python-consul \
    redis \
    aioredis \
    openai \
    anthropic \
    google-generativeai \
    PyGithub \
    notion-client \
    cryptography \
    passlib \
    click \
    rich \
    python-dateutil \
    orjson \
    Pillow \
    PyJWT \
    defusedxml \
    websockets

echo ""
echo "🔧 Setting proper permissions..."
chown -R ikino:ikino /home/ikino/dev/autonomous-multi-llm-agent/venv
chmod -R 755 /home/ikino/dev/autonomous-multi-llm-agent/venv

echo ""
echo "🧪 Testing installations..."
source venv/bin/activate

echo "   Testing YouTube transcript API..."
python3 -c "
from youtube_transcript_api import YouTubeTranscriptApi
print('✅ youtube-transcript-api: OK')

try:
    transcript_list = YouTubeTranscriptApi.list_transcripts('dQw4w9WgXcQ')
    transcript = transcript_list.find_transcript(['en'])
    data = transcript.fetch()
    print(f'✅ Transcript test: {len(data)} segments extracted')
except Exception as e:
    print(f'⚠️ Transcript test warning: {e}')
"

echo "   Testing other key packages..."
python3 -c "
import sys
packages = [
    'aiofiles', 'fastapi', 'pydantic', 'requests', 'loguru', 
    'openai', 'anthropic', 'google.generativeai', 'notion_client'
]

for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}: OK')
    except ImportError as e:
        print(f'❌ {pkg}: FAILED - {e}')
"

echo ""
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data
chmod 755 logs data
chown ikino:ikino logs data

echo ""
echo "🎉 INSTALLATION COMPLETE!"
echo "========================================="
echo ""
echo "✅ System packages installed"
echo "✅ Python packages installed globally and in venv"
echo "✅ YouTube processing tools ready"
echo "✅ All LLM client libraries installed"
echo "✅ Virtual environment configured"
echo ""
echo "🚀 You can now run:"
echo "   cd /home/ikino/dev/autonomous-multi-llm-agent"
echo "   source venv/bin/activate"
echo "   python src/main.py --mode autonomous"
echo ""
echo "🧪 Or test YouTube processing:"
echo "   python src/tools/youtube_processor_updated.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'"
echo ""