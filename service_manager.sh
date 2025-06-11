#!/bin/bash
"""
LifeOS Service Manager
======================

Easy management script for LifeOS services.
"""

show_usage() {
    echo "🔧 LifeOS Service Manager"
    echo "========================"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Start both LifeOS services"
    echo "  stop      - Stop both LifeOS services"
    echo "  restart   - Restart both LifeOS services"
    echo "  status    - Show status of both services"
    echo "  logs      - Show recent logs for both services"
    echo "  web-logs  - Show web server logs (live)"
    echo "  agent-logs - Show agent system logs (live)"
    echo "  enable    - Enable auto-start on boot"
    echo "  disable   - Disable auto-start on boot"
    echo ""
    echo "Examples:"
    echo "  $0 status     # Check if services are running"
    echo "  $0 restart   # Restart all services"
    echo "  $0 logs      # View recent activity"
}

check_services() {
    WEB_STATUS=$(systemctl is-active lifeos-web.service 2>/dev/null || echo "inactive")
    AGENT_STATUS=$(systemctl is-active lifeos-agent.service 2>/dev/null || echo "inactive")
    
    echo "📊 LifeOS Service Status:"
    echo "========================="
    
    if [ "$WEB_STATUS" = "active" ]; then
        echo "🌐 Web Server:    ✅ RUNNING"
        echo "   📍 Access at: http://localhost:5000"
    else
        echo "🌐 Web Server:    ❌ STOPPED"
    fi
    
    if [ "$AGENT_STATUS" = "active" ]; then
        echo "🤖 Agent System:  ✅ RUNNING"
        echo "   🔄 All automation active"
    else
        echo "🤖 Agent System:  ❌ STOPPED"
    fi
    
    echo ""
}

case "$1" in
    "start")
        echo "🚀 Starting LifeOS services..."
        sudo systemctl start lifeos-web.service
        sleep 3
        sudo systemctl start lifeos-agent.service
        sleep 2
        check_services
        ;;
    
    "stop")
        echo "🛑 Stopping LifeOS services..."
        sudo systemctl stop lifeos-agent.service
        sudo systemctl stop lifeos-web.service
        check_services
        ;;
    
    "restart")
        echo "🔄 Restarting LifeOS services..."
        sudo systemctl restart lifeos-web.service
        sleep 3
        sudo systemctl restart lifeos-agent.service
        sleep 2
        check_services
        ;;
    
    "status")
        check_services
        echo "🔍 Detailed Status:"
        echo "==================="
        sudo systemctl status lifeos-web.service --no-pager -l
        echo ""
        sudo systemctl status lifeos-agent.service --no-pager -l
        ;;
    
    "logs")
        echo "📋 Recent LifeOS Activity:"
        echo "=========================="
        echo ""
        echo "🌐 Web Server (last 20 lines):"
        sudo journalctl -u lifeos-web.service -n 20 --no-pager
        echo ""
        echo "🤖 Agent System (last 20 lines):"
        sudo journalctl -u lifeos-agent.service -n 20 --no-pager
        ;;
    
    "web-logs")
        echo "🌐 LifeOS Web Server Logs (live):"
        echo "=================================="
        echo "Press Ctrl+C to exit"
        sudo journalctl -u lifeos-web.service -f
        ;;
    
    "agent-logs")
        echo "🤖 LifeOS Agent System Logs (live):"
        echo "===================================="
        echo "Press Ctrl+C to exit"
        sudo journalctl -u lifeos-agent.service -f
        ;;
    
    "enable")
        echo "⚡ Enabling auto-start on boot..."
        sudo systemctl enable lifeos-web.service
        sudo systemctl enable lifeos-agent.service
        echo "✅ LifeOS will now start automatically on Ubuntu boot"
        ;;
    
    "disable")
        echo "🔌 Disabling auto-start on boot..."
        sudo systemctl disable lifeos-web.service
        sudo systemctl disable lifeos-agent.service
        echo "✅ LifeOS auto-start disabled"
        ;;
    
    *)
        show_usage
        exit 1
        ;;
esac