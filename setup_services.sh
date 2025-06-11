#!/bin/bash
"""
LifeOS Service Setup Script
===========================

Sets up systemd services to run LifeOS automatically on Ubuntu startup.
"""

set -e

echo "🚀 Setting up LifeOS Services for Auto-Start"
echo "=============================================="

# Get the current directory
LIFEOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 LifeOS Directory: $LIFEOS_DIR"

# Check if running as root for systemd operations
if [[ $EUID -eq 0 ]]; then
    echo "❌ Don't run this script as root. Run as your user account."
    echo "   The script will use sudo when needed."
    exit 1
fi

echo ""
echo "📋 Step 1: Installing systemd service files..."

# Copy service files to systemd directory
sudo cp "$LIFEOS_DIR/lifeos-web.service" /etc/systemd/system/
sudo cp "$LIFEOS_DIR/lifeos-agent.service" /etc/systemd/system/

echo "✅ Service files installed to /etc/systemd/system/"

echo ""
echo "📋 Step 2: Setting correct permissions..."

# Set correct ownership and permissions
sudo chown root:root /etc/systemd/system/lifeos-web.service
sudo chown root:root /etc/systemd/system/lifeos-agent.service
sudo chmod 644 /etc/systemd/system/lifeos-web.service
sudo chmod 644 /etc/systemd/system/lifeos-agent.service

echo "✅ Permissions set correctly"

echo ""
echo "📋 Step 3: Reloading systemd daemon..."

# Reload systemd to recognize new services
sudo systemctl daemon-reload

echo "✅ Systemd daemon reloaded"

echo ""
echo "📋 Step 4: Enabling services for auto-start..."

# Enable services to start automatically on boot
sudo systemctl enable lifeos-web.service
sudo systemctl enable lifeos-agent.service

echo "✅ Services enabled for auto-start on boot"

echo ""
echo "📋 Step 5: Starting services now..."

# Start the services immediately
sudo systemctl start lifeos-web.service
sleep 5  # Give web server time to start

sudo systemctl start lifeos-agent.service
sleep 3

echo "✅ Services started"

echo ""
echo "📋 Step 6: Checking service status..."

# Check service status
echo "🌐 LifeOS Web Server Status:"
sudo systemctl status lifeos-web.service --no-pager -l

echo ""
echo "🤖 LifeOS Agent System Status:"
sudo systemctl status lifeos-agent.service --no-pager -l

echo ""
echo "🎉 SETUP COMPLETE!"
echo "=================="
echo ""
echo "✅ Your LifeOS system is now configured to start automatically on Ubuntu boot!"
echo ""
echo "📊 Service Information:"
echo "   🌐 Web Server: http://localhost:5000"
echo "   🤖 Autonomous Agent: Running in background"
echo ""
echo "🔧 Service Management Commands:"
echo "   sudo systemctl status lifeos-web     # Check web server status"
echo "   sudo systemctl status lifeos-agent   # Check agent status"
echo "   sudo systemctl restart lifeos-web    # Restart web server"
echo "   sudo systemctl restart lifeos-agent  # Restart agents"
echo "   sudo systemctl stop lifeos-web       # Stop web server"
echo "   sudo systemctl stop lifeos-agent     # Stop agents"
echo ""
echo "📋 View Logs:"
echo "   sudo journalctl -u lifeos-web -f     # Web server logs"
echo "   sudo journalctl -u lifeos-agent -f   # Agent system logs"
echo ""
echo "🔄 The services will automatically start whenever Ubuntu boots up!"