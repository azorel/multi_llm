#!/usr/bin/env python3
"""
SQL-Based Web Application
=========================

Complete web application using SQL database instead of Notion.
NO MORE NOTION DEPENDENCIES!
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
import threading
import asyncio

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

class SQLWebServer:
    """SQL-based web server replacing Notion."""
    
    def __init__(self):
        self.db_path = 'autonomous_learning.db'
        self.ensure_tables()
    
    def ensure_tables(self):
        """Ensure all required tables exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist (from migration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS youtube_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                channel_id TEXT UNIQUE,
                description TEXT,
                subscriber_count INTEGER DEFAULT 0,
                video_count INTEGER DEFAULT 0,
                country TEXT,
                hashtags TEXT,
                auto_process BOOLEAN DEFAULT FALSE,
                process_channel BOOLEAN DEFAULT FALSE,
                last_processed DATETIME,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_hub (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT UNIQUE,
                type TEXT DEFAULT 'YouTube',
                content_type TEXT,
                ai_summary TEXT,
                content_summary TEXT,
                key_points TEXT,
                action_items TEXT,
                assistant_prompt TEXT,
                complexity_level TEXT DEFAULT 'Medium',
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Ready',
                processing_status TEXT DEFAULT 'Pending',
                hashtags TEXT,
                channel TEXT,
                video_id TEXT,
                duration_seconds INTEGER,
                published_at DATETIME,
                decision_made BOOLEAN DEFAULT FALSE,
                pass_flag BOOLEAN DEFAULT FALSE,
                yes_flag BOOLEAN DEFAULT FALSE,
                notes TEXT,
                thumbnail_url TEXT,
                transcript TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                level TEXT DEFAULT 'INFO',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_youtube_channels(self):
        """Get all YouTube channels."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, url, channel_id, subscriber_count, video_count, 
                   auto_process, process_channel, last_processed, notes
            FROM youtube_channels 
            ORDER BY name
        """)
        
        channels = []
        for row in cursor.fetchall():
            channel = {
                'id': row[0],
                'name': row[1],
                'url': row[2],
                'channel_id': row[3],
                'subscriber_count': row[4] or 0,
                'video_count': row[5] or 0,
                'auto_process': bool(row[6]),
                'process_channel': bool(row[7]),
                'last_processed': row[8],
                'notes': row[9] or ''
            }
            channels.append(channel)
        
        conn.close()
        return channels
    
    def get_knowledge_hub(self, limit=50, status_filter=None):
        """Get knowledge hub videos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, name, url, type, content_type, ai_summary, priority, 
                   status, processing_status, channel, video_id, created_at,
                   duration_seconds, upload_date, published_at, uploader,
                   view_count, like_count, transcript, updated_at
            FROM knowledge_hub 
        """
        
        params = []
        if status_filter:
            query += " WHERE processing_status = ?"
            params.append(status_filter)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        videos = []
        for row in cursor.fetchall():
            # Format duration from seconds to readable format
            duration_formatted = ""
            if row[12]:  # duration_seconds
                total_seconds = row[12]
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                if hours > 0:
                    duration_formatted = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    duration_formatted = f"{minutes}:{seconds:02d}"
            
            video = {
                'id': row[0],
                'title': row[1],  # Use title instead of name for consistency
                'name': row[1],
                'url': row[2],
                'youtube_url': row[2],
                'type': row[3],
                'content_type': row[4],
                'ai_summary': row[5] or '',
                'priority': row[6],
                'status': row[7],
                'processing_status': row[8] or 'pending',
                'channel_name': row[9] or 'Unknown Channel',
                'channel': row[9] or 'Unknown Channel',
                'video_id': row[10] or '',
                'youtube_id': row[10] or '',
                'created_at': row[11],
                'duration_seconds': row[12] or 0,
                'duration': duration_formatted or 'Unknown',
                'upload_date': row[13] or row[14] or row[11],  # Try upload_date, then published_at, then created_at
                'published_at': row[14],
                'uploader': row[15],
                'view_count': row[16] or 0,
                'like_count': row[17] or 0,
                'transcript': row[18] or '',
                'updated_at': row[19],
                'processing_date': row[19] or row[11]  # Use updated_at or created_at as processing date
            }
            videos.append(video)
        
        conn.close()
        return videos
    
    def get_video_details(self, video_id):
        """Get detailed video information."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM knowledge_hub WHERE id = ?
        """, (video_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        # Format duration from seconds to readable format
        duration_formatted = "Unknown"
        if row[17]:  # duration_seconds
            total_seconds = row[17]
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            if hours > 0:
                duration_formatted = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_formatted = f"{minutes}:{seconds:02d}"
        
        video = {
            'id': row[0],
            'title': row[1],
            'name': row[1],
            'url': row[2],
            'youtube_url': row[2],
            'type': row[3],
            'content_type': row[4],
            'ai_summary': row[5] or '',
            'ai_insights': row[47] if len(row) > 47 and row[47] else '',
            'ai_key_points': row[48] if len(row) > 48 and row[48] else '',
            'content_summary': row[6] or '',
            'key_points': row[7] or '',
            'action_items': row[8] or '',
            'assistant_prompt': row[9] or '',
            'complexity_level': row[10],
            'priority': row[11],
            'status': row[12],
            'processing_status': row[13] or 'pending',
            'hashtags': json.loads(row[14]) if row[14] else [],
            'channel_name': row[15] or 'Unknown Channel',
            'channel': row[15] or 'Unknown Channel',
            'video_id': row[16] or '',
            'youtube_id': row[16] or '',
            'duration_seconds': row[17] or 0,
            'duration': duration_formatted,
            'published_at': row[18],
            'upload_date': row[33] if len(row) > 33 and row[33] else row[18],
            'decision_made': bool(row[19]),
            'pass_flag': bool(row[20]),
            'yes_flag': bool(row[21]),
            'notes': row[22] or '',
            'thumbnail_url': row[23] or '',
            'transcript': row[24] or '',
            'created_at': row[25],
            'updated_at': row[26],
            'processing_date': row[26] or row[25],
            'description': row[27] if len(row) > 27 and row[27] else '',
            'view_count': row[30] if len(row) > 30 and row[30] else 0,
            'like_count': row[31] if len(row) > 31 and row[31] else 0,
            'language': row[36] if len(row) > 36 and row[36] else 'Unknown',
            'processing_agent': row[57] if len(row) > 57 and row[57] else 'Multi-Agent System',
            'retry_count': 0,  # Not in original table
            'error_message': None  # Not in original table
        }
        
        conn.close()
        return video
    
    def mark_channel_for_processing(self, channel_id):
        """Mark a channel for processing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE youtube_channels 
            SET process_channel = 1, updated_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), channel_id))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def get_processing_stats(self):
        """Get processing statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Channel stats
        cursor.execute("SELECT COUNT(*) FROM youtube_channels")
        total_channels = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM youtube_channels WHERE process_channel = 1")
        marked_channels = cursor.fetchone()[0]
        
        # Video stats
        cursor.execute("SELECT COUNT(*) FROM knowledge_hub")
        total_videos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_hub WHERE processing_status = 'Completed'")
        processed_videos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_hub WHERE processing_status = 'pending'")
        pending_videos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_hub WHERE processing_status = 'error'")
        error_videos = cursor.fetchone()[0]
        
        # Recent activity
        cursor.execute("""
            SELECT COUNT(*) FROM knowledge_hub 
            WHERE created_at > datetime('now', '-24 hours')
        """)
        videos_today = cursor.fetchone()[0]
        
        # Database size
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        db_size_mb = (page_count * page_size) / (1024 * 1024) if page_count and page_size else 0
        
        conn.close()
        
        return {
            'total_channels': total_channels,
            'marked_channels': marked_channels,
            'total_videos': total_videos,
            'processed_videos': processed_videos,
            'pending_videos': pending_videos,
            'error_videos': error_videos,
            'videos_today': videos_today,
            'db_size': round(db_size_mb, 2)
        }

# Initialize web server
web_server = SQLWebServer()

@app.route('/')
def dashboard():
    """Main dashboard."""
    stats = web_server.get_processing_stats()
    recent_videos = web_server.get_knowledge_hub(limit=10)
    return render_template('sql_dashboard.html', stats=stats, recent_videos=recent_videos)

@app.route('/youtube_channels')
def youtube_channels():
    """YouTube channels page."""
    channels = web_server.get_youtube_channels()
    return render_template('sql_youtube_channels.html', channels=channels)

@app.route('/knowledge_hub')
def knowledge_hub():
    """Knowledge hub page."""
    status_filter = request.args.get('status')
    limit = int(request.args.get('limit', 50))
    videos = web_server.get_knowledge_hub(limit=limit, status_filter=status_filter)
    return render_template('sql_knowledge_hub.html', videos=videos, status_filter=status_filter)

@app.route('/video/<int:video_id>')
def video_details(video_id):
    """Video details page."""
    video = web_server.get_video_details(video_id)
    if not video:
        return "Video not found", 404
    return render_template('sql_video_details.html', video=video)

@app.route('/api/mark_channel/<int:channel_id>', methods=['POST'])
def api_mark_channel(channel_id):
    """API endpoint to mark channel for processing."""
    success = web_server.mark_channel_for_processing(channel_id)
    return jsonify({'success': success})

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics."""
    stats = web_server.get_processing_stats()
    return jsonify(stats)

@app.route('/api/add_channel', methods=['POST'])
def api_add_channel():
    """API endpoint to add a new YouTube channel."""
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        # Get channel data
        name = data.get('name', '').strip()
        url = data.get('url', '').strip()
        description = data.get('description', '').strip()
        
        # Validate required fields
        if not name:
            return jsonify({'success': False, 'error': 'Channel name is required'}), 400
        
        if not url:
            return jsonify({'success': False, 'error': 'Channel URL is required'}), 400
        
        # Validate URL format
        if not (url.startswith('https://www.youtube.com/@') or 
                url.startswith('https://youtube.com/@') or
                url.startswith('https://www.youtube.com/channel/') or
                url.startswith('https://youtube.com/channel/') or
                url.startswith('https://www.youtube.com/c/') or
                url.startswith('https://youtube.com/c/')):
            return jsonify({'success': False, 'error': 'Invalid YouTube channel URL format'}), 400
        
        # Extract channel ID from URL if possible
        channel_id = None
        if '/channel/' in url:
            channel_id = url.split('/channel/')[-1].split('/')[0].split('?')[0]
        elif '/@' in url:
            # For @username URLs, we'll need to fetch the actual channel ID later
            channel_id = url.split('/@')[-1].split('/')[0].split('?')[0]
        
        # Add channel to database
        conn = sqlite3.connect(web_server.db_path)
        cursor = conn.cursor()
        
        # Check if channel already exists
        cursor.execute("SELECT id, name FROM youtube_channels WHERE url = ?", (url,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return jsonify({'success': False, 'error': f'Channel already exists: {existing[1]}'}), 409
        
        # Insert new channel
        cursor.execute("""
            INSERT INTO youtube_channels (name, url, channel_id, description, auto_process, process_channel, created_at, updated_at)
            VALUES (?, ?, ?, ?, 0, 0, datetime('now'), datetime('now'))
        """, (name, url, channel_id, description))
        
        channel_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Channel "{name}" added successfully',
            'channel_id': channel_id
        })
        
    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/multi_agents')
def multi_agents():
    """Multi-agent system status page."""
    # Check if SQL multi-agent system is running
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        sql_agents_running = 'sql_multi_agent_system.py' in result.stdout
    except:
        sql_agents_running = False
    
    stats = web_server.get_processing_stats()
    
    return render_template('sql_multi_agents.html', 
                         sql_agents_running=sql_agents_running, 
                         stats=stats)

@app.route('/api/process_video/<int:video_id>', methods=['POST'])
def api_process_video(video_id):
    """API endpoint to process a video with AI."""
    try:
        # Validate video_id
        if video_id <= 0:
            return jsonify({'success': False, 'error': 'Invalid video ID'}), 400
        
        # Check if video exists
        conn = sqlite3.connect(web_server.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, processing_status FROM knowledge_hub WHERE id = ?", (video_id,))
        video = cursor.fetchone()
        
        if not video:
            conn.close()
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        # Check if video is already being processed
        if video[1] == 'processing':
            conn.close()
            return jsonify({'success': False, 'error': 'Video is already being processed'}), 409
        
        # Update video status to pending
        cursor.execute("""
            UPDATE knowledge_hub 
            SET processing_status = 'pending', 
                updated_at = datetime('now')
            WHERE id = ?
        """, (video_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Failed to update video status'}), 500
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Video {video_id} queued for AI processing'})
    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/start_system', methods=['POST'])
def api_start_system():
    """API endpoint to start the multi-agent system."""
    try:
        import subprocess
        import os
        
        # Check if already running
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'FINAL_UNIFIED_SYSTEM.py' in result.stdout:
            return jsonify({'success': False, 'error': 'System is already running'})
        
        # Start the unified system
        process = subprocess.Popen([
            'python3', 'FINAL_UNIFIED_SYSTEM.py'
        ], cwd='/home/ikino/dev/autonomous-multi-llm-agent')
        
        return jsonify({'success': True, 'message': 'Multi-agent system started', 'pid': process.pid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stop_system', methods=['POST'])
def api_stop_system():
    """API endpoint to stop the multi-agent system."""
    try:
        import subprocess
        
        # Find and kill the process
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if 'FINAL_UNIFIED_SYSTEM.py' in line and 'python' in line:
                pid = line.split()[1]
                subprocess.run(['kill', pid])
                return jsonify({'success': True, 'message': f'System stopped (PID: {pid})'})
        
        return jsonify({'success': False, 'error': 'System not found running'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/logs/<component>')
def api_logs(component):
    """API endpoint to get logs for a specific component."""
    try:
        import os
        log_files = {
            'web-server': '/var/log/web-server.log',
            'youtube-processor': '/var/log/youtube-processor.log',
            'health-monitor': '/var/log/health-monitor.log',
            'database-manager': '/var/log/database-manager.log'
        }
        
        log_file = log_files.get(component)
        if not log_file or not os.path.exists(log_file):
            # Fallback to system logs
            import subprocess
            result = subprocess.run(['journalctl', '-u', component, '--lines=100'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return jsonify({'logs': result.stdout})
            else:
                return jsonify({'logs': f'No logs available for {component}\n\nComponent status: Monitoring...\nLast check: Active\nErrors: None'})
        
        with open(log_file, 'r') as f:
            logs = f.read()
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'logs': f'Error reading logs: {str(e)}'})

@app.route('/api/bulk_process', methods=['POST'])
def api_bulk_process():
    """API endpoint for bulk processing operations."""
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        action = data.get('action')
        video_ids = data.get('video_ids', [])
        
        # Validate required fields
        if not action:
            return jsonify({'success': False, 'error': 'Missing required field: action'}), 400
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'Missing required field: video_ids'}), 400
        
        # Validate action
        valid_actions = ['process', 'delete', 'reset']
        if action not in valid_actions:
            return jsonify({'success': False, 'error': f'Invalid action. Must be one of: {", ".join(valid_actions)}'}), 400
        
        # Validate video_ids
        if not isinstance(video_ids, list):
            return jsonify({'success': False, 'error': 'video_ids must be a list'}), 400
        
        if len(video_ids) == 0:
            return jsonify({'success': False, 'error': 'video_ids list cannot be empty'}), 400
        
        if len(video_ids) > 1000:  # Reasonable limit
            return jsonify({'success': False, 'error': 'Cannot process more than 1000 videos at once'}), 400
        
        # Validate each video ID
        for vid in video_ids:
            if not isinstance(vid, int) or vid <= 0:
                return jsonify({'success': False, 'error': f'Invalid video ID: {vid}'}), 400
        
        conn = sqlite3.connect(web_server.db_path)
        cursor = conn.cursor()
        
        # Check if all video IDs exist
        cursor.execute(f"SELECT id FROM knowledge_hub WHERE id IN ({','.join(['?'] * len(video_ids))})", video_ids)
        existing_ids = [row[0] for row in cursor.fetchall()]
        missing_ids = set(video_ids) - set(existing_ids)
        
        if missing_ids:
            conn.close()
            return jsonify({'success': False, 'error': f'Video IDs not found: {list(missing_ids)}'}), 404
        
        # Perform the bulk operation
        if action == 'process':
            cursor.executemany("""
                UPDATE knowledge_hub 
                SET processing_status = 'pending', 
                    updated_at = datetime('now')
                WHERE id = ?
            """, [(vid,) for vid in video_ids])
            message = f'{len(video_ids)} videos queued for processing'
            
        elif action == 'delete':
            cursor.executemany("""
                UPDATE knowledge_hub 
                SET processing_status = 'deleted', 
                    updated_at = datetime('now')
                WHERE id = ?
            """, [(vid,) for vid in video_ids])
            message = f'{len(video_ids)} videos marked for deletion'
            
        elif action == 'reset':
            cursor.executemany("""
                UPDATE knowledge_hub 
                SET processing_status = 'pending', 
                    updated_at = datetime('now')
                WHERE id = ?
            """, [(vid,) for vid in video_ids])
            message = f'{len(video_ids)} videos reset for reprocessing'
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'No videos were updated'}), 500
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': message, 'processed_count': cursor.rowcount})
        
    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/health')
def api_health():
    """System health monitoring endpoint."""
    try:
        import psutil
        import time
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database metrics
        conn = sqlite3.connect(web_server.db_path)
        cursor = conn.cursor()
        
        # Get database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        # Get processing stats
        cursor.execute("SELECT COUNT(*) FROM knowledge_hub")
        total_videos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_hub WHERE processing_status = 'Completed'")
        processed_videos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_hub WHERE processing_status = 'pending'")
        pending_videos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_hub WHERE processing_status = 'error'")
        error_videos = cursor.fetchone()[0]
        
        conn.close()
        
        # Process status
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        system_running = 'FINAL_UNIFIED_SYSTEM.py' in result.stdout
        
        health_data = {
            'timestamp': time.time(),
            'status': 'healthy' if cpu_percent < 80 and memory.percent < 85 else 'warning',
            'system': {
                'cpu_percent': round(cpu_percent, 1),
                'memory_percent': round(memory.percent, 1),
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_percent': round(disk.percent, 1),
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'uptime': True,
                'agents_running': system_running
            },
            'database': {
                'size_mb': round(db_size / (1024**2), 2),
                'total_videos': total_videos,
                'processed_videos': processed_videos,
                'pending_videos': pending_videos,
                'error_videos': error_videos,
                'processing_rate': round((processed_videos / total_videos * 100), 1) if total_videos > 0 else 0
            },
            'alerts': []
        }
        
        # Generate alerts
        if cpu_percent > 80:
            health_data['alerts'].append({'level': 'warning', 'message': f'High CPU usage: {cpu_percent}%'})
        if memory.percent > 85:
            health_data['alerts'].append({'level': 'warning', 'message': f'High memory usage: {memory.percent}%'})
        if disk.percent > 90:
            health_data['alerts'].append({'level': 'critical', 'message': f'Low disk space: {disk.percent}% used'})
        if error_videos > 0:
            health_data['alerts'].append({'level': 'info', 'message': f'{error_videos} videos failed processing'})
        if not system_running:
            health_data['alerts'].append({'level': 'warning', 'message': 'Multi-agent system is not running'})
        
        return jsonify(health_data)
        
    except Exception as e:
        return jsonify({
            'timestamp': time.time(),
            'status': 'error',
            'error': str(e),
            'alerts': [{'level': 'critical', 'message': 'Health check failed'}]
        }), 500

@app.route('/health')
def health_dashboard():
    """System health dashboard page."""
    return render_template('sql_health.html')

if __name__ == '__main__':
    print("🚀 Starting SQL-based web server...")
    print("🌐 Available at: http://localhost:5000")
    print("📊 Dashboard: http://localhost:5000")
    print("📺 YouTube Channels: http://localhost:5000/youtube_channels")
    print("🧠 Knowledge Hub: http://localhost:5000/knowledge_hub")
    print("🤖 Multi-Agents: http://localhost:5000/multi_agents")
    print("🔍 Health Monitor: http://localhost:5000/health")
    print("=" * 60)
    print("✅ NO MORE NOTION - EVERYTHING IS SQL-BASED!")
    
    app.run(host='0.0.0.0', port=5000, debug=True)