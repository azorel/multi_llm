#!/usr/bin/env python3
"""
Social Media Routes for Vanlife & RC Truck Automation
Handles upload, analysis, and posting workflow
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import sqlite3
from pathlib import Path

# Import our content analyzer
from content_analyzer import VanlifeRCContentAnalyzer
from social_media_database_extension import extend_database_for_social_media, get_social_media_stats

social_media_bp = Blueprint('social_media', __name__)

# Configuration
UPLOAD_FOLDER = 'uploads/social_media'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi', 'mkv'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@social_media_bp.route('/social-media')
def dashboard():
    """Main social media dashboard"""
    try:
        # Get system stats
        stats = get_social_media_stats()
        
        # Get recent posts
        conn = sqlite3.connect('lifeos_local.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, original_filename, content_type, caption, status, created_date, views, likes
            FROM social_media_posts 
            ORDER BY created_date DESC 
            LIMIT 10
        ''')
        recent_posts = cursor.fetchall()
        
        # Get revenue summary
        cursor.execute('''
            SELECT SUM(revenue_generated) as total_revenue,
                   COUNT(*) as total_posts,
                   AVG(views) as avg_views
            FROM social_media_posts
        ''')
        revenue_data = cursor.fetchone()
        
        conn.close()
        
        return render_template('social_media_dashboard.html',
                             stats=stats,
                             recent_posts=recent_posts,
                             revenue_data=revenue_data)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('social_media_dashboard.html', 
                             stats={}, recent_posts=[], revenue_data=None)

@social_media_bp.route('/social-media/upload')
def upload_interface():
    """Upload interface for photos and videos"""
    return render_template('social_media_upload.html')

@social_media_bp.route('/social-media/upload', methods=['POST'])
def handle_upload():
    """Handle file upload and analysis"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'})
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'success': False, 'error': 'File too large (max 100MB)'})
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Analyze content
        analyzer = VanlifeRCContentAnalyzer()
        analysis_result = analyzer.analyze_content(file_path)
        
        if analysis_result['success']:
            # Save to database
            post_id = analyzer.save_analysis_to_db(file_path, analysis_result)
            
            # Return analysis results
            return jsonify({
                'success': True,
                'post_id': post_id,
                'file_path': file_path,
                'content_type': analysis_result['content_type'],
                'caption': analysis_result['caption'],
                'hashtags': analysis_result['hashtags'],
                'posting_recommendations': analysis_result['posting_recommendations'],
                'file_info': analysis_result['file_info']
            })
        else:
            # Clean up file on analysis failure
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'success': False, 'error': analysis_result.get('error', 'Analysis failed')})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@social_media_bp.route('/social-media/preview/<int:post_id>')
def preview_post(post_id):
    """Preview post before publishing"""
    try:
        conn = sqlite3.connect('lifeos_local.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, file_path, original_filename, content_type, caption, 
                   hashtags, analysis_data, created_date
            FROM social_media_posts 
            WHERE id = ?
        ''', (post_id,))
        
        post_data = cursor.fetchone()
        conn.close()
        
        if not post_data:
            flash('Post not found', 'error')
            return redirect(url_for('social_media.dashboard'))
        
        # Parse hashtags
        hashtags = json.loads(post_data[5]) if post_data[5] else []
        analysis_data = json.loads(post_data[6]) if post_data[6] else {}
        
        post = {
            'id': post_data[0],
            'file_path': post_data[1],
            'filename': post_data[2],
            'content_type': post_data[3],
            'caption': post_data[4],
            'hashtags': hashtags,
            'analysis': analysis_data,
            'created_date': post_data[7]
        }
        
        return render_template('social_media_preview.html', post=post)
        
    except Exception as e:
        flash(f'Error loading preview: {str(e)}', 'error')
        return redirect(url_for('social_media.dashboard'))

@social_media_bp.route('/social-media/edit/<int:post_id>', methods=['POST'])
def edit_post(post_id):
    """Edit caption and hashtags before posting"""
    try:
        data = request.get_json()
        caption = data.get('caption', '').strip()
        hashtags = data.get('hashtags', [])
        
        if not caption:
            return jsonify({'success': False, 'error': 'Caption cannot be empty'})
        
        # Update database
        conn = sqlite3.connect('lifeos_local.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE social_media_posts 
            SET caption = ?, hashtags = ?, last_updated = ?
            WHERE id = ?
        ''', (caption, json.dumps(hashtags), datetime.now().isoformat(), post_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Post updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@social_media_bp.route('/social-media/schedule/<int:post_id>', methods=['POST'])
def schedule_post(post_id):
    """Schedule post for publishing"""
    try:
        data = request.get_json()
        platforms = data.get('platforms', [])
        scheduled_time = data.get('scheduled_time')
        
        if not platforms:
            return jsonify({'success': False, 'error': 'Please select at least one platform'})
        
        # Update database
        conn = sqlite3.connect('lifeos_local.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE social_media_posts 
            SET platforms = ?, scheduled_time = ?, status = ?, last_updated = ?
            WHERE id = ?
        ''', (json.dumps(platforms), scheduled_time, 'scheduled', datetime.now().isoformat(), post_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Post scheduled successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@social_media_bp.route('/social-media/analytics')
def analytics():
    """Analytics and revenue tracking"""
    try:
        conn = sqlite3.connect('lifeos_local.db')
        cursor = conn.cursor()
        
        # Get posting performance by content type
        cursor.execute('''
            SELECT content_type, 
                   COUNT(*) as post_count,
                   AVG(views) as avg_views,
                   AVG(likes) as avg_likes,
                   SUM(revenue_generated) as total_revenue
            FROM social_media_posts 
            WHERE status = 'posted'
            GROUP BY content_type
        ''')
        content_performance = cursor.fetchall()
        
        # Get hashtag performance
        cursor.execute('''
            SELECT hashtag, niche, avg_engagement, trending_score
            FROM hashtag_performance 
            ORDER BY trending_score DESC 
            LIMIT 20
        ''')
        hashtag_performance = cursor.fetchall()
        
        # Get revenue tracking
        cursor.execute('''
            SELECT revenue_source, SUM(amount) as total, COUNT(*) as count
            FROM revenue_tracking 
            GROUP BY revenue_source
            ORDER BY total DESC
        ''')
        revenue_sources = cursor.fetchall()
        
        conn.close()
        
        return render_template('social_media_analytics.html',
                             content_performance=content_performance,
                             hashtag_performance=hashtag_performance,
                             revenue_sources=revenue_sources)
        
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return render_template('social_media_analytics.html',
                             content_performance=[], hashtag_performance=[], revenue_sources=[])

@social_media_bp.route('/social-media/api/stats')
def api_stats():
    """API endpoint for dashboard stats"""
    try:
        stats = get_social_media_stats()
        
        # Add performance metrics
        conn = sqlite3.connect('lifeos_local.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_posts,
                SUM(views) as total_views,
                SUM(likes) as total_likes,
                SUM(revenue_generated) as total_revenue
            FROM social_media_posts
        ''')
        performance = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'database_stats': stats,
            'performance': {
                'total_posts': performance[0] or 0,
                'total_views': performance[1] or 0,
                'total_likes': performance[2] or 0,
                'total_revenue': performance[3] or 0.0
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@social_media_bp.route('/social-media/delete/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Delete a post and its associated file"""
    try:
        conn = sqlite3.connect('lifeos_local.db')
        cursor = conn.cursor()
        
        # Get file path before deletion
        cursor.execute('SELECT file_path FROM social_media_posts WHERE id = ?', (post_id,))
        result = cursor.fetchone()
        
        if result:
            file_path = result[0]
            
            # Delete from database
            cursor.execute('DELETE FROM social_media_posts WHERE id = ?', (post_id,))
            cursor.execute('DELETE FROM revenue_tracking WHERE post_id = ?', (post_id,))
            
            conn.commit()
            conn.close()
            
            # Delete file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'success': True, 'message': 'Post deleted successfully'})
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'Post not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Initialize database on import
try:
    extend_database_for_social_media()
    print("✅ Social media database initialized")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")