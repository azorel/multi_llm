#!/usr/bin/env python3
"""
Build Real-Time Autonomous System Monitoring Page
Creates actual working monitoring dashboard to see what the autonomous system is doing.
"""

import os
import sqlite3
from datetime import datetime

def add_monitoring_route():
    """Add the monitoring route to web_server.py"""
    
    # Read current web_server.py
    with open('web_server.py', 'r') as f:
        content = f.read()
    
    # Add the new route before the last route
    monitoring_route = '''
@app.route('/autonomous-monitor')
def autonomous_monitor():
    """Real-time monitoring of autonomous system activity."""
    import sqlite3
    import json
    from datetime import datetime, timedelta
    
    monitor_data = {
        'actions': [],
        'solutions': [],
        'stats': {},
        'recent_activity': []
    }
    
    # Connect to autonomous learning database
    try:
        conn = sqlite3.connect('autonomous_learning.db')
        cursor = conn.cursor()
        
        # Get recent actions (last 50)
        cursor.execute("""
            SELECT session_id, action_type, action_details, success, timestamp 
            FROM actions_taken 
            ORDER BY timestamp DESC 
            LIMIT 50
        """)
        actions = cursor.fetchall()
        
        for action in actions:
            try:
                details = json.loads(action[2]) if action[2] else {}
            except:
                details = {}
            
            monitor_data['actions'].append({
                'session_id': action[0],
                'action_type': action[1], 
                'details': details,
                'success': action[3],
                'timestamp': action[4],
                'time_ago': get_time_ago(action[4])
            })
        
        # Get learned solutions
        cursor.execute("SELECT * FROM learned_solutions ORDER BY timestamp DESC")
        solutions = cursor.fetchall()
        monitor_data['solutions'] = solutions
        
        # Calculate statistics
        cursor.execute("SELECT COUNT(*) FROM actions_taken")
        total_actions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM actions_taken WHERE success = 1")
        successful_actions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM actions_taken")
        total_sessions = cursor.fetchone()[0]
        
        success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0
        
        monitor_data['stats'] = {
            'total_actions': total_actions,
            'successful_actions': successful_actions,
            'success_rate': round(success_rate, 2),
            'total_sessions': total_sessions,
            'learned_solutions': len(solutions)
        }
        
        # Get recent activity by hour
        cursor.execute("""
            SELECT 
                strftime('%H:00', timestamp) as hour,
                COUNT(*) as count,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
            FROM actions_taken 
            WHERE datetime(timestamp) > datetime('now', '-24 hours')
            GROUP BY strftime('%H', timestamp)
            ORDER BY hour
        """)
        hourly_activity = cursor.fetchall()
        monitor_data['recent_activity'] = hourly_activity
        
        conn.close()
        
    except Exception as e:
        monitor_data['error'] = str(e)
    
    return render_template('autonomous_monitor.html', data=monitor_data)

def get_time_ago(timestamp_str):
    """Calculate time ago from timestamp string"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timestamp.tzinfo)
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "just now"
    except:
        return "unknown"

'''
    
    # Insert the route before the last route definition
    last_route_pos = content.rfind('@app.route')
    if last_route_pos > 0:
        # Find the end of the previous route
        insert_pos = content.rfind('\n\n', 0, last_route_pos)
        if insert_pos > 0:
            new_content = content[:insert_pos] + monitoring_route + content[insert_pos:]
        else:
            new_content = content + monitoring_route
    else:
        new_content = content + monitoring_route
    
    # Write back to file
    with open('web_server.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Added monitoring route to web_server.py")

def create_monitoring_template():
    """Create the autonomous monitoring HTML template"""
    
    template_content = '''{% extends "base.html" %}

{% block title %}Autonomous System Monitor - LifeOS{% endblock %}

{% block content %}
<div class="page-header">
    <h1 class="page-title">🤖 Autonomous System Monitor</h1>
    <p class="page-subtitle">
        Real-time monitoring of autonomous learning and self-healing activities.
# NOTION_REMOVED:         <span style="float: right; color: var(--notion-text-light); font-size: 12px;">
            Last updated: {{ now.strftime('%H:%M:%S') }}
# NOTION_REMOVED:             <button onclick="location.reload()" style="margin-left: 8px; background: var(--notion-blue); color: white; border: none; padding: 2px 6px; border-radius: 3px; font-size: 11px; cursor: pointer;">
                🔄 Refresh
            </button>
        </span>
    </p>
</div>

<!-- Auto-refresh script -->
<script>
    // Auto-refresh every 5 seconds
    setTimeout(function() {
        location.reload();
    }, 5000);
</script>

<!-- System Statistics -->
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px;">
# NOTION_REMOVED:     <div class="notion-card">
        <div class="card-title">📊 Total Actions</div>
        <div class="card-content">
# NOTION_REMOVED:             <div style="font-size: 32px; font-weight: 600; color: var(--notion-blue);">{{ data.stats.total_actions or 0 }}</div>
# NOTION_REMOVED:             <div style="font-size: 12px; color: var(--notion-text-light);">All autonomous actions</div>
        </div>
    </div>
    
# NOTION_REMOVED:     <div class="notion-card">
        <div class="card-title">✅ Success Rate</div>
        <div class="card-content">
# NOTION_REMOVED:             <div style="font-size: 32px; font-weight: 600; color: var(--notion-green);">{{ data.stats.success_rate or 0 }}%</div>
# NOTION_REMOVED:             <div style="font-size: 12px; color: var(--notion-text-light);">{{ data.stats.successful_actions or 0 }} successful</div>
        </div>
    </div>
    
# NOTION_REMOVED:     <div class="notion-card">
        <div class="card-title">🔄 Fix Sessions</div>
        <div class="card-content">
# NOTION_REMOVED:             <div style="font-size: 32px; font-weight: 600; color: var(--notion-purple);">{{ data.stats.total_sessions or 0 }}</div>
# NOTION_REMOVED:             <div style="font-size: 12px; color: var(--notion-text-light);">Autonomous fix attempts</div>
        </div>
    </div>
    
# NOTION_REMOVED:     <div class="notion-card">
        <div class="card-title">🧠 Solutions Learned</div>
        <div class="card-content">
# NOTION_REMOVED:             <div style="font-size: 32px; font-weight: 600; color: var(--notion-orange);">{{ data.stats.learned_solutions or 0 }}</div>
# NOTION_REMOVED:             <div style="font-size: 12px; color: var(--notion-text-light);">Knowledge acquired</div>
        </div>
    </div>
</div>

<!-- Real-time Activity Feed -->
# NOTION_REMOVED: <div class="notion-card" style="margin-bottom: 24px;">
    <div class="card-title">📡 Live Activity Feed</div>
    <div class="card-content">
        {% if data.error %}
# NOTION_REMOVED:             <div style="color: var(--notion-red); padding: 16px; background: rgba(255, 59, 48, 0.1); border-radius: 6px;">
                ❌ Database Error: {{ data.error }}
            </div>
        {% else %}
            <div style="max-height: 400px; overflow-y: auto; background: #1a1a1a; border-radius: 6px; padding: 16px; font-family: 'Monaco', 'Menlo', monospace; font-size: 13px;">
                {% for action in data.actions %}
                <div style="margin-bottom: 8px; color: {{ '#4CAF50' if action.success else '#FF5722' }};">
                    <span style="color: #888;">[{{ action.time_ago }}]</span>
                    <span style="color: #2196F3;">{{ action.session_id }}</span>
                    <span style="color: {{ '#4CAF50' if action.success else '#FF5722' }};">
                        {{ '✅' if action.success else '❌' }} {{ action.action_type }}
                    </span>
                    {% if action.details.step %}
                        <span style="color: #FFC107;">Step {{ action.details.step }}</span>
                    {% endif %}
                    {% if action.details.command %}
                        <div style="margin-left: 20px; color: #9E9E9E; font-size: 11px;">
                            > {{ action.details.command[:80] }}{% if action.details.command|length > 80 %}...{% endif %}
                        </div>
                    {% endif %}
                </div>
                {% endfor %}
                
                {% if data.actions|length == 0 %}
                <div style="color: #888; text-align: center; padding: 20px;">
                    No autonomous activity recorded yet
                </div>
                {% endif %}
            </div>
        {% endif %}
    </div>
</div>

<!-- Recent Activity Chart -->
{% if data.recent_activity %}
# NOTION_REMOVED: <div class="notion-card" style="margin-bottom: 24px;">
    <div class="card-title">📈 24-Hour Activity</div>
    <div class="card-content">
        <div style="display: flex; align-items: end; height: 100px; gap: 4px;">
            {% for hour_data in data.recent_activity %}
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center;">
# NOTION_REMOVED:                 <div style="background: var(--notion-blue); height: {{ (hour_data[1] / 10 * 80) or 2 }}px; width: 100%; margin-bottom: 4px; border-radius: 2px;"></div>
# NOTION_REMOVED:                 <div style="font-size: 10px; color: var(--notion-text-light);">{{ hour_data[0] }}</div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
{% endif %}

<!-- Learned Solutions -->
{% if data.solutions %}
# NOTION_REMOVED: <div class="notion-card">
    <div class="card-title">🧠 Learned Solutions</div>
    <div class="card-content">
        {% for solution in data.solutions %}
# NOTION_REMOVED:         <div style="border-left: 3px solid var(--notion-green); padding-left: 12px; margin-bottom: 16px;">
            <div style="font-weight: 600;">{{ solution[1] }}</div>
# NOTION_REMOVED:             <div style="font-size: 13px; color: var(--notion-text-light); margin-top: 4px;">
                {{ solution[2] }}
            </div>
# NOTION_REMOVED:             <div style="font-size: 11px; color: var(--notion-text-light); margin-top: 4px;">
                Success Rate: {{ (solution[3] * 100)|round(1) }}% | {{ solution[5] }}
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}

{% endblock %}'''

    # Write template file
    with open('templates/autonomous_monitor.html', 'w') as f:
        f.write(template_content)
    
    print("✅ Created autonomous_monitor.html template")

def update_navigation():
    """Add monitoring page to navigation"""
    # This would update the base template or navigation to include the new page
    print("✅ Navigation can be updated manually")

def main():
    """Build the complete monitoring system"""
    print("🚀 BUILDING AUTONOMOUS SYSTEM MONITORING PAGE")
    print("=" * 50)
    
    try:
        # Add route to web server
        add_monitoring_route()
        
        # Create template
        create_monitoring_template()
        
        # Update navigation
        update_navigation()
        
        print("\n✅ MONITORING PAGE BUILT SUCCESSFULLY!")
        print("🔍 Access it at: http://localhost:5000/autonomous-monitor")
        print("🔄 Auto-refreshes every 5 seconds")
        print("📊 Shows real-time autonomous system activity")
        
    except Exception as e:
        print(f"❌ Build failed: {e}")

if __name__ == "__main__":
    main()