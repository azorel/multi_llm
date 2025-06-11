#!/bin/bash

echo "🚀 Setting up LifeOS Services for Auto-Start"
echo "=============================================="

LIFEOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 LifeOS Directory: $LIFEOS_DIR"

echo ""
echo "📋 Installing systemd service files..."

# Copy service files to systemd directory
sudo cp "$LIFEOS_DIR/lifeos-web.service" /etc/systemd/system/
sudo cp "$LIFEOS_DIR/lifeos-agent.service" /etc/systemd/system/

echo "✅ Service files installed"

echo ""
echo "📋 Setting permissions..."

sudo chown root:root /etc/systemd/system/lifeos-web.service
sudo chown root:root /etc/systemd/system/lifeos-agent.service
sudo chmod 644 /etc/systemd/system/lifeos-web.service
sudo chmod 644 /etc/systemd/system/lifeos-agent.service

echo "✅ Permissions set"

echo ""
echo "📋 Reloading systemd..."

sudo systemctl daemon-reload

echo "✅ Systemd reloaded"

echo ""
echo "📋 Enabling auto-start..."

sudo systemctl enable lifeos-web.service
sudo systemctl enable lifeos-agent.service

echo "✅ Auto-start enabled"

echo ""
echo "🎉 SETUP COMPLETE!"
echo "=================="
echo ""
echo "✅ LifeOS will now start automatically when Ubuntu boots!"
echo ""
echo "🔧 To start services now:"
echo "   ./service_manager.sh start"
echo ""
echo "📊 To check status:"
echo "   ./service_manager.sh status"