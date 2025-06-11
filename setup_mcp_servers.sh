#!/bin/bash
# Setup script for MCP servers in the autonomous agent system

set -e

echo "Setting up MCP servers for autonomous agent..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Installing Node.js..."
    
    # Install Node.js using NodeSource repository (for Ubuntu/Debian)
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"

# Navigate to the sequential thinking server directory
cd "$(dirname "$0")/mcp-servers/sequential-thinking"

echo "Installing Sequential Thinking MCP server dependencies..."
npm install

echo "Building Sequential Thinking MCP server..."
npm run build

echo "MCP servers setup completed successfully!"

# Test the server
echo "Testing Sequential Thinking MCP server..."
if [ -f "dist/index.js" ]; then
    echo "✓ Sequential Thinking MCP server built successfully"
else
    echo "✗ Sequential Thinking MCP server build failed"
    exit 1
fi

echo "All MCP servers are ready!"