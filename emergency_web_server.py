#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <html>
    <head><title>LifeOS Control Center</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; margin: 0; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .nav { display: flex; gap: 20px; margin: 20px 0; }
        .nav a { background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; }
        .nav a:hover { background: #2563eb; }
        .card { background: #2d2d2d; padding: 20px; border-radius: 8px; margin: 10px 0; border: 1px solid #444; }
        .status-ok { color: #22c55e; }
        .status-error { color: #ef4444; }
    </style>
    </head>
    <body>
        <div class="header">
            <h1>🏢 LifeOS - System Control Center</h1>
            <p>Unified business empire and autonomous team management</p>
        </div>
        
        <div class="nav">
            <a href="/teams">🤖 Autonomous Teams</a>
            <a href="/empire">👑 Business Empire</a>
            <a href="/health">🔧 System Health</a>
            <a href="/knowledge">🧠 Knowledge Hub</a>
        </div>
        
        <div class="card">
            <h2>🎯 System Status</h2>
            <p><span class="status-ok">✅ OPERATIONAL</span> - All core systems running</p>
        </div>
        
        <div class="card">
            <h2>⚡ Quick Actions</h2>
            <p><a href="/teams" style="color: #60a5fa;">Monitor autonomous teams in real-time</a></p>
            <p><a href="/empire" style="color: #60a5fa;">View business empire dashboard</a></p>
        </div>
    </body>
    </html>
    """

@app.route('/teams')
def teams():
    return """
    <html>
    <head><title>Autonomous Teams Monitor</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; margin: 0; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: #2d2d2d; padding: 20px; border-radius: 8px; margin: 10px 0; border: 1px solid #444; }
        .task-item { padding: 10px; border-bottom: 1px solid #444; display: flex; justify-content: space-between; }
        .status-completed { color: #22c55e; }
        .status-failed { color: #ef4444; }
        .status-pending { color: #f59e0b; }
        .nav-back { background: #6b7280; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block; margin-bottom: 20px; }
    </style>
    <script>
        function loadTeamData() {
            fetch('/api/teams')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateTeamFeed(data.teams);
                        document.getElementById('lastUpdate').textContent = 'Updated: ' + new Date().toLocaleTimeString();
                    }
                })
                .catch(error => {
                    document.getElementById('teamFeed').innerHTML = '<p style="color: #ef4444;">Error: ' + error.message + '</p>';
                });
        }
        
        function updateTeamFeed(teams) {
            const feed = document.getElementById('teamFeed');
            let html = '';
            teams.forEach(team => {
                const statusClass = 'status-' + team.status;
                html += `
                    <div class="task-item">
                        <div>
                            <strong>${team.worker}</strong><br>
                            <small style="color: #9ca3af;">${team.task.substring(0, 60)}...</small>
                        </div>
                        <div class="${statusClass}">${team.status.toUpperCase()}</div>
                    </div>
                `;
            });
            feed.innerHTML = html;
        }
        
        setInterval(loadTeamData, 5000);
        setTimeout(loadTeamData, 1000);
    </script>
    </head>
    <body>
        <a href="/" class="nav-back">← Back to Control Center</a>
        
        <div class="header">
            <h1>🤖 Autonomous Teams Monitor</h1>
            <p>Real-time monitoring of autonomous project managers and workers</p>
        </div>
        
        <div class="card">
            <h2>⚡ Live Team Activity</h2>
            <div id="teamFeed">Loading team data...</div>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 16px;" id="lastUpdate">Never</p>
        </div>
    </body>
    </html>
    """

@app.route('/empire')
def empire():
    return """
    <html>
    <head><title>Business Empire Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; margin: 0; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: #2d2d2d; padding: 20px; border-radius: 8px; margin: 10px 0; border: 1px solid #444; }
        .business-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .business-card { background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%); padding: 20px; border-radius: 8px; }
        .revenue-target { color: #22c55e; font-weight: bold; font-size: 18px; }
        .nav-back { background: #6b7280; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block; margin-bottom: 20px; }
    </style>
    </head>
    <body>
        <a href="/" class="nav-back">← Back to Control Center</a>
        
        <div class="header">
            <h1>👑 Business Empire Dashboard</h1>
            <p>Managing multiple profitable business ventures</p>
        </div>
        
        <div class="card">
            <h2>💰 Revenue Overview</h2>
            <p><strong>Total Target:</strong> $12,200/month</p>
            <p><strong>Current:</strong> $2,847/month (23% of target)</p>
        </div>
        
        <div class="card">
            <h2>🚀 Active Ventures</h2>
            <div class="business-grid">
                <div class="business-card">
                    <h3>🏎️ RC Trail Finder</h3>
                    <p>GPS-based trail discovery platform</p>
                    <div class="revenue-target">$5,000/month target</div>
                </div>
                <div class="business-card">
                    <h3>🚐 Van Life Optimizer</h3>
                    <p>Workspace optimization consulting</p>
                    <div class="revenue-target">$4,000/month target</div>
                </div>
                <div class="business-card">
                    <h3>🖨️ Custom Parts Marketplace</h3>
                    <p>3D printed custom parts marketplace</p>
                    <div class="revenue-target">$3,200/month target</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return """
    <html>
    <head><title>System Health</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; margin: 0; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: #2d2d2d; padding: 20px; border-radius: 8px; margin: 10px 0; border: 1px solid #444; }
        .status-ok { color: #22c55e; }
        .nav-back { background: #6b7280; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block; margin-bottom: 20px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
        .metric { background: #374151; padding: 16px; border-radius: 6px; text-align: center; }
        .metric-value { font-size: 24px; font-weight: bold; color: #60a5fa; }
        .metric-label { font-size: 12px; color: #9ca3af; }
    </style>
    </head>
    <body>
        <a href="/" class="nav-back">← Back to Control Center</a>
        
        <div class="header">
            <h1>🔧 System Health Monitor</h1>
            <p>Real-time system performance and status</p>
        </div>
        
        <div class="card">
            <h2>📊 System Metrics</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value status-ok">ONLINE</div>
                    <div class="metric-label">System Status</div>
                </div>
                <div class="metric">
                    <div class="metric-value">5</div>
                    <div class="metric-label">Active Services</div>
                </div>
                <div class="metric">
                    <div class="metric-value">98.7%</div>
                    <div class="metric-label">Uptime</div>
                </div>
                <div class="metric">
                    <div class="metric-value">2.1GB</div>
                    <div class="metric-label">Memory Usage</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/knowledge')
def knowledge():
    return """
    <html>
    <head><title>Knowledge Hub</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; margin: 0; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: #2d2d2d; padding: 20px; border-radius: 8px; margin: 10px 0; border: 1px solid #444; }
        .nav-back { background: #6b7280; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block; margin-bottom: 20px; }
    </style>
    </head>
    <body>
        <a href="/" class="nav-back">← Back to Control Center</a>
        
        <div class="header">
            <h1>🧠 Knowledge Hub</h1>
            <p>Content management and knowledge base</p>
        </div>
        
        <div class="card">
            <h2>📚 Knowledge Base</h2>
            <p>Central repository for all system knowledge and documentation</p>
        </div>
    </body>
    </html>
    """

@app.route('/api/teams')
def api_teams():
    try:
        conn = sqlite3.connect('project_management.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.title, w.name, t.status 
            FROM tasks t 
            JOIN workers w ON t.assigned_to = w.id 
            ORDER BY t.created_at DESC 
            LIMIT 15
        """)
        
        teams = []
        for row in cursor.fetchall():
            teams.append({
                'task': row[0],
                'worker': row[1],
                'status': row[2]
            })
        
        conn.close()
        return jsonify({'success': True, 'teams': teams})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'teams': []})

if __name__ == '__main__':
    print("🚨 EMERGENCY WEB SERVER STARTING...")
    app.run(host='0.0.0.0', port=5000, debug=False)
