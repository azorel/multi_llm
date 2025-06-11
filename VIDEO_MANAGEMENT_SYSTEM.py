#!/usr/bin/env python3
"""
VIDEO MANAGEMENT SYSTEM
=======================

Web interface for managing processed videos:
- Mark for delete, edit, integration
- View AI analysis results
- Manage auto-check settings
- Integration workflow management
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json
from datetime import datetime
import os

class VideoManagementSystem:
    """Video management web interface."""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.db_path = 'autonomous_learning.db'
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/video_management')
        def video_management():
            """Main video management page."""
            videos = self.get_all_videos()
            return render_template('video_management.html', videos=videos)
        
        @self.app.route('/video/<int:video_id>')
        def video_detail(video_id):
            """Detailed video view."""
            video = self.get_video_details(video_id)
            if not video:
                return "Video not found", 404
            return render_template('video_detail.html', video=video)
        
        @self.app.route('/api/mark_video', methods=['POST'])
        def mark_video():
            """Mark video for action."""
            data = request.json
            video_id = data.get('video_id')
            action = data.get('action')  # 'delete', 'edit', 'integration'
            notes = data.get('notes', '')
            
            success = self.mark_video_for_action(video_id, action, notes)
            return jsonify({'success': success})
        
        @self.app.route('/api/update_auto_check', methods=['POST'])
        def update_auto_check():
            """Update auto-check settings."""
            data = request.json
            video_id = data.get('video_id')
            enabled = data.get('enabled')
            
            success = self.update_auto_check_setting(video_id, enabled)
            return jsonify({'success': success})
        
        @self.app.route('/api/integration_workflow', methods=['POST'])
        def integration_workflow():
            """Process integration workflow."""
            data = request.json
            video_id = data.get('video_id')
            action = data.get('action')  # 'approve', 'reject', 'modify'
            
            result = self.process_integration(video_id, action, data)
            return jsonify(result)
        
        @self.app.route('/api/bulk_action', methods=['POST'])
        def bulk_action():
            """Perform bulk actions on videos."""
            data = request.json
            video_ids = data.get('video_ids', [])
            action = data.get('action')
            
            results = self.perform_bulk_action(video_ids, action)
            return jsonify(results)
        
        @self.app.route('/api/search_videos', methods=['GET'])
        def search_videos():
            """Search videos by various criteria."""
            query = request.args.get('q', '')
            filter_type = request.args.get('filter', 'all')
            
            videos = self.search_videos(query, filter_type)
            return jsonify(videos)
    
    def get_all_videos(self):
        """Get all videos with management info."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, url, channel, duration_seconds, view_count, 
                       quality_score, relevance_score, technical_complexity,
                       mark_for_delete, mark_for_edit, mark_for_integration,
                       auto_check_enabled, processing_status, created_at,
                       ai_context, thumbnail_url
                FROM knowledge_hub 
                ORDER BY created_at DESC
            """)
            
            videos = []
            for row in cursor.fetchall():
                videos.append({
                    'id': row[0],
                    'name': row[1],
                    'url': row[2],
                    'channel': row[3],
                    'duration_seconds': row[4],
                    'view_count': row[5],
                    'quality_score': row[6],
                    'relevance_score': row[7],
                    'technical_complexity': row[8],
                    'mark_for_delete': bool(row[9]),
                    'mark_for_edit': bool(row[10]),
                    'mark_for_integration': bool(row[11]),
                    'auto_check_enabled': bool(row[12]),
                    'processing_status': row[13],
                    'created_at': row[14],
                    'ai_context': row[15],
                    'thumbnail_url': row[16],
                    'duration_formatted': self.format_duration(row[4])
                })
            
            conn.close()
            return videos
            
        except Exception as e:
            print(f"❌ Error getting videos: {e}")
            return []
    
    def get_video_details(self, video_id: int):
        """Get detailed video information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM knowledge_hub WHERE id = ?", (video_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            video = dict(zip(columns, row))
            
            # Parse JSON fields
            json_fields = ['tags', 'hashtags', 'ai_extracted_hashtags', 'ai_key_insights', 
                          'chapters', 'automatic_captions', 'subtitles']
            
            for field in json_fields:
                if video.get(field):
                    try:
                        video[field] = json.loads(video[field])
                    except:
                        video[field] = []
            
            video['duration_formatted'] = self.format_duration(video.get('duration_seconds'))
            
            conn.close()
            return video
            
        except Exception as e:
            print(f"❌ Error getting video details: {e}")
            return None
    
    def mark_video_for_action(self, video_id: int, action: str, notes: str = '') -> bool:
        """Mark video for specific action."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Reset all marks first
            cursor.execute("""
                UPDATE knowledge_hub 
                SET mark_for_delete = 0, mark_for_edit = 0, mark_for_integration = 0,
                    integration_notes = ?
                WHERE id = ?
            """, (notes, video_id))
            
            # Set specific mark
            if action == 'delete':
                cursor.execute("UPDATE knowledge_hub SET mark_for_delete = 1 WHERE id = ?", (video_id,))
            elif action == 'edit':
                cursor.execute("UPDATE knowledge_hub SET mark_for_edit = 1 WHERE id = ?", (video_id,))
            elif action == 'integration':
                cursor.execute("UPDATE knowledge_hub SET mark_for_integration = 1 WHERE id = ?", (video_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error marking video: {e}")
            return False
    
    def update_auto_check_setting(self, video_id: int, enabled: bool) -> bool:
        """Update auto-check setting for video."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE knowledge_hub 
                SET auto_check_enabled = ?
                WHERE id = ?
            """, (enabled, video_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error updating auto-check: {e}")
            return False
    
    def process_integration(self, video_id: int, action: str, data: dict) -> dict:
        """Process integration workflow."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if action == 'approve':
                # Mark as integrated
                cursor.execute("""
                    UPDATE knowledge_hub 
                    SET mark_for_integration = 0, 
                        status = 'Integrated',
                        integration_notes = 'Approved for integration'
                    WHERE id = ?
                """, (video_id,))
                
                result = {'success': True, 'message': 'Video approved for integration'}
                
            elif action == 'reject':
                # Mark as rejected
                cursor.execute("""
                    UPDATE knowledge_hub 
                    SET mark_for_integration = 0,
                        integration_notes = ?
                    WHERE id = ?
                """, (data.get('reason', 'Rejected'), video_id))
                
                result = {'success': True, 'message': 'Video integration rejected'}
                
            elif action == 'modify':
                # Update integration notes
                cursor.execute("""
                    UPDATE knowledge_hub 
                    SET integration_notes = ?
                    WHERE id = ?
                """, (data.get('modifications', ''), video_id))
                
                result = {'success': True, 'message': 'Integration notes updated'}
            
            else:
                result = {'success': False, 'message': 'Invalid action'}
            
            conn.commit()
            conn.close()
            return result
            
        except Exception as e:
            print(f"❌ Error processing integration: {e}")
            return {'success': False, 'message': str(e)}
    
    def perform_bulk_action(self, video_ids: list, action: str) -> dict:
        """Perform bulk actions on multiple videos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            success_count = 0
            
            for video_id in video_ids:
                try:
                    if action == 'delete_marked':
                        cursor.execute("DELETE FROM knowledge_hub WHERE id = ? AND mark_for_delete = 1", (video_id,))
                    elif action == 'enable_auto_check':
                        cursor.execute("UPDATE knowledge_hub SET auto_check_enabled = 1 WHERE id = ?", (video_id,))
                    elif action == 'disable_auto_check':
                        cursor.execute("UPDATE knowledge_hub SET auto_check_enabled = 0 WHERE id = ?", (video_id,))
                    elif action == 'clear_marks':
                        cursor.execute("""
                            UPDATE knowledge_hub 
                            SET mark_for_delete = 0, mark_for_edit = 0, mark_for_integration = 0
                            WHERE id = ?
                        """, (video_id,))
                    
                    success_count += 1
                    
                except Exception as e:
                    print(f"❌ Bulk action failed for video {video_id}: {e}")
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'Action completed on {success_count}/{len(video_ids)} videos'
            }
            
        except Exception as e:
            print(f"❌ Bulk action failed: {e}")
            return {'success': False, 'message': str(e)}
    
    def search_videos(self, query: str, filter_type: str) -> list:
        """Search videos by various criteria."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            base_query = """
                SELECT id, name, channel, ai_context, quality_score, 
                       mark_for_delete, mark_for_edit, mark_for_integration
                FROM knowledge_hub
            """
            
            where_conditions = []
            params = []
            
            # Text search
            if query:
                where_conditions.append("(name LIKE ? OR ai_context LIKE ? OR channel LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            
            # Filter by type
            if filter_type == 'marked_delete':
                where_conditions.append("mark_for_delete = 1")
            elif filter_type == 'marked_edit':
                where_conditions.append("mark_for_edit = 1")
            elif filter_type == 'marked_integration':
                where_conditions.append("mark_for_integration = 1")
            elif filter_type == 'high_quality':
                where_conditions.append("quality_score > 0.7")
            elif filter_type == 'auto_check':
                where_conditions.append("auto_check_enabled = 1")
            
            # Build final query
            if where_conditions:
                final_query = base_query + " WHERE " + " AND ".join(where_conditions)
            else:
                final_query = base_query
            
            final_query += " ORDER BY created_at DESC LIMIT 50"
            
            cursor.execute(final_query, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'channel': row[2],
                    'ai_context': row[3],
                    'quality_score': row[4],
                    'mark_for_delete': bool(row[5]),
                    'mark_for_edit': bool(row[6]),
                    'mark_for_integration': bool(row[7])
                })
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def format_duration(self, seconds):
        """Format duration in human readable format."""
        if not seconds:
            return "Unknown"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def run(self, host='0.0.0.0', port=5001):
        """Run the video management system."""
        print(f"🎥 Video Management System starting on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=True)

if __name__ == "__main__":
    management_system = VideoManagementSystem()
    management_system.run()