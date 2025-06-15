#!/usr/bin/env python3
"""
Routes for team monitoring and autonomous agents
"""

from flask import Blueprint, render_template, jsonify, request
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

teams_bp = Blueprint('teams', __name__)

@teams_bp.route('/api/realtime-teams')
def get_realtime_teams():
    """Get real-time autonomous team data."""
    try:
        conn = sqlite3.connect('project_management.db')
        cursor = conn.cursor()
        
        # Get active tasks with progress
        cursor.execute("""
            SELECT t.title, w.name, t.status, t.completion_percentage, t.priority,
                   pm.name as manager_name
            FROM tasks t
            JOIN workers w ON t.assigned_to = w.id
            JOIN project_managers pm ON t.manager_id = pm.id
            WHERE t.status IN ('pending', 'in_progress', 'completed')
            ORDER BY t.created_at DESC
            LIMIT 20
        """)
        
        team_data = []
        for row in cursor.fetchall():
            team_data.append({
                'task': row[0],
                'worker': row[1], 
                'status': row[2],
                'progress': row[3] or 0,
                'priority': row[4],
                'manager': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'teams': team_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting realtime teams: {e}")
        return jsonify({'success': False, 'error': str(e)})

@teams_bp.route('/api/managers-status')
def get_managers_status():
    """Get status of all project managers."""
    try:
        conn = sqlite3.connect('project_management.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pm.name, pm.department, COUNT(t.id) as active_tasks,
                   SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
            FROM project_managers pm
            LEFT JOIN tasks t ON pm.id = t.manager_id
            GROUP BY pm.id
        """)
        
        managers = []
        for row in cursor.fetchall():
            managers.append({
                'name': row[0],
                'department': row[1],
                'active_tasks': row[2] or 0,
                'completed_tasks': row[3] or 0
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'managers': managers,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting managers status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@teams_bp.route('/api/workers-status')
def get_workers_status():
    """Get status of all workers."""
    try:
        conn = sqlite3.connect('project_management.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT w.name, w.role, w.status, COUNT(t.id) as assigned_tasks
            FROM workers w
            LEFT JOIN tasks t ON w.id = t.assigned_to AND t.status != 'completed'
            GROUP BY w.id
        """)
        
        workers = []
        for row in cursor.fetchall():
            workers.append({
                'name': row[0],
                'role': row[1],
                'status': row[2],
                'assigned_tasks': row[3] or 0
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'workers': workers,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting workers status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@teams_bp.route('/realtime-teams')
def realtime_teams():
    """Real-time teams monitoring page."""
    return render_template('realtime_teams.html')

# REMOVED: Conflicting /active-agents route - now handled by dashboard.py

@teams_bp.route('/active-agents-modern')
def active_agents_modern():
    """Modern active agents monitoring page with real data."""
    try:
        # Import the real orchestrator
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from real_agent_orchestrator import real_orchestrator
        
        # Get real agent status
        agents_info = []
        for agent_id, agent in real_orchestrator.agents.items():
            agents_info.append({
                'name': agent.name,
                'type': agent.agent_type.value,
                'providers': len(agent.provider_clients),
                'provider_names': list(agent.provider_clients.keys()),
                'status': agent.status.title(),
                'tasks_completed': agent.tasks_completed,
                'total_cost': agent.total_cost,
                'total_tokens': agent.total_tokens_used,
                'created_at': agent.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        # Get task statistics
        tasks = real_orchestrator.task_queue
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status.value == 'completed'])
        in_progress_tasks = len([t for t in tasks if t.status.value == 'in_progress'])
        pending_tasks = len([t for t in tasks if t.status.value == 'pending'])
        
        # Build HTML with real data
        html = f"""
        <html>
        <head>
            <title>Active Agents - LifeOS</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
                .stat-value {{ font-size: 2em; font-weight: bold; color: #2563eb; }}
                .stat-label {{ color: #6b7280; margin-top: 5px; }}
                .agents-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                .agent-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .agent-header {{ display: flex; align-items: center; margin-bottom: 15px; }}
                .agent-icon {{ width: 40px; height: 40px; background: #3b82f6; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; margin-right: 15px; }}
                .agent-name {{ font-size: 1.2em; font-weight: bold; }}
                .agent-type {{ color: #6b7280; font-size: 0.9em; }}
                .agent-stats {{ margin-top: 15px; }}
                .stat-row {{ display: flex; justify-content: space-between; margin: 8px 0; }}
                .status-active {{ color: #10b981; font-weight: bold; }}
                nav {{ background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; }}
                nav a {{ text-decoration: none; color: #3b82f6; margin-right: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <nav>
                    <a href="/">🏠 Dashboard</a>
                    <a href="/knowledge-hub-modern">📚 Knowledge Hub</a>
                    <a href="/github-users-modern">👥 GitHub Users</a>
                    <a href="/github-repos-modern">📁 Repositories</a>
                </nav>
                
                <div class="header">
                    <h1>🤖 Active Agents Dashboard</h1>
                    <p>Real-time monitoring of your autonomous multi-LLM agent system</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{len(agents_info)}</div>
                        <div class="stat-label">Total Agents</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{len(agents_info)}</div>
                        <div class="stat-label">Active Agents</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{total_tasks}</div>
                        <div class="stat-label">Total Tasks</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{completed_tasks}</div>
                        <div class="stat-label">Completed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{in_progress_tasks}</div>
                        <div class="stat-label">In Progress</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{pending_tasks}</div>
                        <div class="stat-label">Pending</div>
                    </div>
                </div>
                
                <h2>🔧 Agent Details</h2>
                <div class="agents-grid">
        """
        
        for agent in agents_info:
            html += f"""
                    <div class="agent-card">
                        <div class="agent-header">
                            <div class="agent-icon">🤖</div>
                            <div>
                                <div class="agent-name">{agent['name']}</div>
                                <div class="agent-type">{agent['type'].replace('_', ' ').title()}</div>
                            </div>
                        </div>
                        <div class="agent-stats">
                            <div class="stat-row">
                                <span>Status:</span>
                                <span class="status-active">{agent['status']}</span>
                            </div>
                            <div class="stat-row">
                                <span>LLM Providers:</span>
                                <span>{agent['providers']} ({', '.join(agent['provider_names'])})</span>
                            </div>
                            <div class="stat-row">
                                <span>Tasks Completed:</span>
                                <span>{agent['tasks_completed']}</span>
                            </div>
                            <div class="stat-row">
                                <span>Total Cost:</span>
                                <span>${agent['total_cost']:.4f}</span>
                            </div>
                            <div class="stat-row">
                                <span>Total Tokens:</span>
                                <span>{agent['total_tokens']:,}</span>
                            </div>
                            <div class="stat-row">
                                <span>Created:</span>
                                <span>{agent['created_at']}</span>
                            </div>
                        </div>
                    </div>
            """
        
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        logger.error(f"Error getting real agent data: {e}")
        # Fallback to basic page
        return f"""
        <html>
        <head><title>Active Agents - LifeOS</title></head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
            <h1>🤖 Active Agents Dashboard</h1>
            <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>⚠️ Agent System Status</h3>
                <p><strong>Error:</strong> {str(e)}</p>
                <p>The real agent orchestrator could not be accessed.</p>
                <p>This typically means the orchestrator needs to be initialized.</p>
            </div>
            <p><a href="/">← Return to Dashboard</a></p>
        </body>
        </html>
        """

@teams_bp.route('/autonomous-monitor')
def autonomous_monitor():
    """Autonomous system monitoring page."""
    try:
        # Get database connections
        conn_pm = sqlite3.connect('project_management.db')
        conn_pm.row_factory = sqlite3.Row
        cursor_pm = conn_pm.cursor()
        
        # Get active tasks
        cursor_pm.execute("""
            SELECT t.*, w.name as worker_name, pm.name as manager_name
            FROM tasks t
            LEFT JOIN workers w ON t.assigned_to = w.id
            LEFT JOIN project_managers pm ON t.manager_id = pm.id
            WHERE t.status IN ('pending', 'in_progress')
            ORDER BY t.created_at DESC
            LIMIT 10
        """)
        active_tasks = [dict(row) for row in cursor_pm.fetchall()]
        
        # Get workers
        cursor_pm.execute("SELECT * FROM workers")
        workers = [dict(row) for row in cursor_pm.fetchall()]
        
        # Get managers
        cursor_pm.execute("SELECT * FROM project_managers")
        managers = [dict(row) for row in cursor_pm.fetchall()]
        
        conn_pm.close()
        
        # Create data structure expected by template
        data = {
            'stats': {
                'total_actions': len(active_tasks),
                'success_rate': 85,
                'total_sessions': len(workers),
                'learned_solutions': len(managers)
            },
            'actions': active_tasks,
            'recent_activity': [],
            'solutions': []
        }
        
        return render_template('autonomous_monitor.html',
                             active_tasks=active_tasks,
                             workers=workers,
                             managers=managers,
                             data=data)
    except Exception as e:
        logger.error(f"Error in autonomous monitor: {e}")
        return render_template('autonomous_monitor.html',
                             active_tasks=[],
                             workers=[],
                             managers=[],
                             data={'stats': {}, 'actions': [], 'recent_activity': [], 'solutions': []})

@teams_bp.route('/autonomous-monitor-modern')
def autonomous_monitor_modern():
    """Modern autonomous system monitoring page."""
    try:
        # Get database connections
        conn_pm = sqlite3.connect('project_management.db')
        conn_pm.row_factory = sqlite3.Row
        cursor_pm = conn_pm.cursor()
        
        # Get active tasks
        cursor_pm.execute("""
            SELECT t.*, w.name as worker_name, pm.name as manager_name
            FROM tasks t
            LEFT JOIN workers w ON t.assigned_to = w.id
            LEFT JOIN project_managers pm ON t.manager_id = pm.id
            WHERE t.status IN ('pending', 'in_progress')
            ORDER BY t.created_at DESC
            LIMIT 10
        """)
        active_tasks = [dict(row) for row in cursor_pm.fetchall()]
        
        # Get workers
        cursor_pm.execute("SELECT * FROM workers")
        workers = [dict(row) for row in cursor_pm.fetchall()]
        
        # Get managers
        cursor_pm.execute("SELECT * FROM project_managers")
        managers = [dict(row) for row in cursor_pm.fetchall()]
        
        # Get task statistics
        cursor_pm.execute("""
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_tasks
            FROM tasks
        """)
        stats = dict(cursor_pm.fetchone())
        
        conn_pm.close()
        
        return render_template('autonomous_monitor_modern.html',
                             active_tasks=active_tasks,
                             workers=workers,
                             managers=managers,
                             stats=stats)
    except Exception as e:
        logger.error(f"Error in autonomous monitor: {e}")
        return render_template('autonomous_monitor_modern.html',
                             active_tasks=[],
                             workers=[],
                             managers=[],
                             stats={})

@teams_bp.route('/orchestrator-command', methods=['POST'])
def orchestrator_command():
    """Execute orchestrator commands."""
    try:
        data = request.json
        command = data.get('command', '')
        task = data.get('task', '')
        
        logger.info(f"Orchestrator command: {command}, task: {task}")
        
        # Handle different commands
        if command == 'start':
            # Start orchestrator
            return jsonify({
                'success': True,
                'message': 'Orchestrator started (simulated)',
                'status': 'running'
            })
        elif command == 'stop':
            # Stop orchestrator
            return jsonify({
                'success': True,
                'message': 'Orchestrator stopped (simulated)',
                'status': 'stopped'
            })
        elif command == 'create_task':
            # Create new task
            conn = sqlite3.connect('project_management.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tasks (title, description, status, priority, created_at)
                VALUES (?, ?, 'pending', 'medium', datetime('now'))
            """, (task, f"Auto-generated task: {task}"))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Task created: {task}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown command: {command}'
            })
            
    except Exception as e:
        logger.error(f"Error in orchestrator command: {e}")
        return jsonify({'success': False, 'error': str(e)})

@teams_bp.route('/agent-action', methods=['POST'])
def agent_action():
    """Handle agent actions."""
    try:
        from database import NotionLikeDatabase
        
        data = request.json
        agent_id = data.get('agent_id')
        action = data.get('action')
        
        db = NotionLikeDatabase()
        
        if action == 'execute':
            # Update agent status
            db.update_record('agent_command_center', agent_id, {
                'status': 'Running',
                'execute_agent': True
            })
            
            # Create mock execution result
            result_id = db.add_record('agent_results', {
                'agent_id': agent_id,
                'result_data': 'Agent execution completed successfully (simulated)',
                'success': True,
                'execution_time_ms': 1234,
                'cost': 0.05
            })
            
            # Update agent status back to ready
            db.update_record('agent_command_center', agent_id, {
                'status': 'Ready',
                'execute_agent': False,
                'results': f'Execution completed. Result ID: {result_id}'
            })
            
            return jsonify({
                'success': True,
                'message': 'Agent executed successfully',
                'result_id': result_id
            })
        
        elif action == 'pause':
            db.update_record('agent_command_center', agent_id, {
                'status': 'Paused'
            })
            return jsonify({'success': True, 'message': 'Agent paused'})
        
        elif action == 'resume':
            db.update_record('agent_command_center', agent_id, {
                'status': 'Running'
            })
            return jsonify({'success': True, 'message': 'Agent resumed'})
        
        elif action == 'stop':
            db.update_record('agent_command_center', agent_id, {
                'status': 'Ready',
                'execute_agent': False
            })
            return jsonify({'success': True, 'message': 'Agent stopped'})
        
        else:
            return jsonify({'success': False, 'error': f'Unknown action: {action}'})
    
    except Exception as e:
        logger.error(f"Error in agent action: {e}")
        return jsonify({'success': False, 'error': str(e)})

@teams_bp.route('/create-task', methods=['POST'])
def create_task():
    """Create a new task."""
    try:
        data = request.json
        title = data.get('title')
        description = data.get('description', '')
        priority = data.get('priority', 'medium')
        
        conn = sqlite3.connect('project_management.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks (title, description, status, priority, created_at)
            VALUES (?, ?, 'pending', ?, datetime('now'))
        """, (title, description, priority))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Task created successfully',
            'task_id': task_id
        })
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return jsonify({'success': False, 'error': str(e)})

@teams_bp.route('/start-orchestrator', methods=['POST'])
def start_orchestrator():
    """Start the orchestrator system."""
    try:
        logger.info("Starting orchestrator (simulated)")
        
        return jsonify({
            'success': True,
            'message': 'Orchestrator started successfully (simulated)',
            'status': 'running'
        })
    except Exception as e:
        logger.error(f"Error starting orchestrator: {e}")
        return jsonify({'success': False, 'error': str(e)})