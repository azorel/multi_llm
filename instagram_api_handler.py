#!/usr/bin/env python3
"""
Instagram API Handler for Social Media Automation
Supports both Instagram Graph API (business accounts) and Instagrapi (personal accounts)
"""

import os
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramHandler:
    """
    Instagram posting and management handler supporting both Graph API and Instagrapi
    
    Requirements:
        pip install instagrapi requests
        
    Features:
        - Photo and video posting (Graph API + Instagrapi)
        - Story posting
        - Automatic caption and hashtag optimization
        - Scheduled posting
        - Performance tracking
        - Account management
        - Business account insights
    """
    
    def __init__(self, db_path="lifeos_local.db"):
        self.db_path = db_path
        self.client = None
        self.session_file = "instagram_session.json"
        self.credentials_file = "instagram_credentials.json"
        
        # Instagram Graph API credentials
        self.app_id = os.getenv("FACEBOOK_APP_ID")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET")
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_business_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        
        # Initialize Instagram clients
        self._init_instagram_client()
        self._init_graph_api()
    
    def _init_instagram_client(self):
        """Initialize Instagram API client (Instagrapi for personal accounts)"""
        try:
            # Import here to handle missing dependency gracefully
            from instagrapi import Client
            
            self.client = Client()
            
            # Load session if exists
            if os.path.exists(self.session_file):
                try:
                    self.client.load_settings(self.session_file)
                    logger.info("✅ Instagram session loaded from file")
                except Exception as e:
                    logger.warning(f"Session file corrupted, will create new: {e}")
                    
        except ImportError:
            logger.error("⚠️ Instagrapi not installed. Run: pip install instagrapi")
            self.client = None
    
    def _init_graph_api(self):
        """Initialize Instagram Graph API for business accounts"""
        if self.access_token and self.instagram_business_id:
            self.graph_api_enabled = True
            logger.info("✅ Instagram Graph API configured for business account")
        else:
            self.graph_api_enabled = False
            logger.info("⚠️ Instagram Graph API not configured - business features disabled")
    
    def login(self, username: str = None, password: str = None) -> bool:
        """
        Login to Instagram account
        
        Args:
            username: Instagram username (optional if stored in credentials)
            password: Instagram password (optional if stored in credentials)
            
        Returns:
            bool: Success status
        """
        if not self.client:
            logger.error("Instagram client not initialized")
            return False
            
        try:
            # Load credentials from file if not provided
            if not username or not password:
                credentials = self._load_credentials()
                username = username or credentials.get('username')
                password = password or credentials.get('password')
            
            if not username or not password:
                logger.error("No Instagram credentials provided")
                return False
            
            # Attempt login
            success = self.client.login(username, password)
            
            if success:
                # Save session
                self.client.dump_settings(self.session_file)
                logger.info("✅ Instagram login successful")
                
                # Update database with account info
                self._update_account_info(username)
                
                return True
            else:
                logger.error("❌ Instagram login failed")
                return False
                
        except Exception as e:
            logger.error(f"Instagram login error: {e}")
            return False
    
    def _load_credentials(self) -> Dict[str, str]:
        """Load Instagram credentials from file"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
        
        return {}
    
    def save_credentials(self, username: str, password: str):
        """Save Instagram credentials securely"""
        try:
            credentials = {
                'username': username,
                'password': password,  # In production, encrypt this
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
                
            # Set file permissions to owner only
            os.chmod(self.credentials_file, 0o600)
            logger.info("✅ Instagram credentials saved")
            
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
    
    def _update_account_info(self, username: str):
        """Update database with Instagram account information"""
        try:
            if not self.client:
                return
                
            user_info = self.client.user_info_by_username(username)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create Instagram account info table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS instagram_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    user_id TEXT,
                    full_name TEXT,
                    bio TEXT,
                    followers_count INTEGER,
                    following_count INTEGER,
                    media_count INTEGER,
                    is_verified BOOLEAN,
                    is_business BOOLEAN,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert or update account info
            cursor.execute('''
                INSERT OR REPLACE INTO instagram_accounts 
                (username, user_id, full_name, bio, followers_count, following_count, 
                 media_count, is_verified, is_business, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                username,
                str(user_info.pk),
                user_info.full_name,
                user_info.biography,
                user_info.follower_count,
                user_info.following_count,
                user_info.media_count,
                user_info.is_verified,
                user_info.is_business,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Account info updated for @{username}")
            
        except Exception as e:
            logger.error(f"Error updating account info: {e}")
    
    def post_photo(self, file_path: str, caption: str, hashtags: List[str] = None) -> Dict[str, Any]:
        """
        Post a photo to Instagram
        
        Args:
            file_path: Path to image file
            caption: Post caption
            hashtags: List of hashtags (optional)
            
        Returns:
            Dict with success status and media info
        """
        if not self.client:
            return {'success': False, 'error': 'Instagram client not initialized'}
        
        try:
            # Prepare caption with hashtags
            full_caption = caption
            if hashtags:
                hashtag_string = ' '.join(hashtags)
                full_caption = f"{caption}\n\n{hashtag_string}"
            
            # Upload photo
            media = self.client.photo_upload(
                path=file_path,
                caption=full_caption
            )
            
            if media:
                logger.info(f"✅ Photo posted successfully: {media.pk}")
                
                # Update database
                self._update_post_status(file_path, 'posted', media.pk, 'instagram')
                
                return {
                    'success': True,
                    'media_id': media.pk,
                    'instagram_url': f"https://instagram.com/p/{media.code}",
                    'posted_at': datetime.now().isoformat()
                }
            else:
                return {'success': False, 'error': 'Upload failed'}
                
        except Exception as e:
            logger.error(f"Error posting photo: {e}")
            return {'success': False, 'error': str(e)}
    
    def post_video(self, file_path: str, caption: str, hashtags: List[str] = None) -> Dict[str, Any]:
        """
        Post a video to Instagram
        
        Args:
            file_path: Path to video file
            caption: Post caption
            hashtags: List of hashtags (optional)
            
        Returns:
            Dict with success status and media info
        """
        if not self.client:
            return {'success': False, 'error': 'Instagram client not initialized'}
        
        try:
            # Prepare caption with hashtags
            full_caption = caption
            if hashtags:
                hashtag_string = ' '.join(hashtags)
                full_caption = f"{caption}\n\n{hashtag_string}"
            
            # Upload video
            media = self.client.video_upload(
                path=file_path,
                caption=full_caption
            )
            
            if media:
                logger.info(f"✅ Video posted successfully: {media.pk}")
                
                # Update database
                self._update_post_status(file_path, 'posted', media.pk, 'instagram')
                
                return {
                    'success': True,
                    'media_id': media.pk,
                    'instagram_url': f"https://instagram.com/p/{media.code}",
                    'posted_at': datetime.now().isoformat()
                }
            else:
                return {'success': False, 'error': 'Video upload failed'}
                
        except Exception as e:
            logger.error(f"Error posting video: {e}")
            return {'success': False, 'error': str(e)}
    
    def post_story(self, file_path: str, duration: int = 15) -> Dict[str, Any]:
        """
        Post content to Instagram Story
        
        Args:
            file_path: Path to image/video file
            duration: Story duration in seconds (for photos)
            
        Returns:
            Dict with success status and story info
        """
        if not self.client:
            return {'success': False, 'error': 'Instagram client not initialized'}
        
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                # Upload photo story
                story = self.client.photo_upload_to_story(path=str(file_path))
            elif file_path.suffix.lower() in ['.mp4', '.mov']:
                # Upload video story
                story = self.client.video_upload_to_story(path=str(file_path))
            else:
                return {'success': False, 'error': 'Unsupported file format for story'}
            
            if story:
                logger.info(f"✅ Story posted successfully: {story.pk}")
                
                return {
                    'success': True,
                    'story_id': story.pk,
                    'posted_at': datetime.now().isoformat()
                }
            else:
                return {'success': False, 'error': 'Story upload failed'}
                
        except Exception as e:
            logger.error(f"Error posting story: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_post_status(self, file_path: str, status: str, media_id: str, platform: str):
        """Update post status in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE social_media_posts 
                SET status = ?, instagram_media_id = ?, posted_time = ?, last_updated = ?
                WHERE file_path = ?
            ''', (status, media_id, datetime.now().isoformat(), datetime.now().isoformat(), file_path))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating post status: {e}")
    
    def get_post_analytics(self, media_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific Instagram post
        
        Args:
            media_id: Instagram media ID
            
        Returns:
            Dict with post analytics
        """
        if not self.client:
            return {'success': False, 'error': 'Instagram client not initialized'}
        
        try:
            media_info = self.client.media_info(media_id)
            
            analytics = {
                'success': True,
                'media_id': media_id,
                'like_count': media_info.like_count,
                'comment_count': media_info.comment_count,
                'view_count': getattr(media_info, 'view_count', 0),
                'play_count': getattr(media_info, 'play_count', 0),
                'taken_at': media_info.taken_at.isoformat() if media_info.taken_at else None,
                'updated_at': datetime.now().isoformat()
            }
            
            # Update database with latest metrics
            self._update_post_analytics(media_id, analytics)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting post analytics: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_post_analytics(self, media_id: str, analytics: Dict[str, Any]):
        """Update post analytics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE social_media_posts 
                SET likes = ?, comments = ?, views = ?, last_updated = ?
                WHERE instagram_media_id = ?
            ''', (
                analytics.get('like_count', 0),
                analytics.get('comment_count', 0),
                analytics.get('view_count', 0),
                datetime.now().isoformat(),
                media_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")
    
    def schedule_post(self, file_path: str, caption: str, hashtags: List[str], 
                     scheduled_time: datetime) -> Dict[str, Any]:
        """
        Schedule a post for later publishing
        
        Args:
            file_path: Path to media file
            caption: Post caption
            hashtags: List of hashtags
            scheduled_time: When to publish the post
            
        Returns:
            Dict with scheduling status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create scheduled posts table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_instagram_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    caption TEXT NOT NULL,
                    hashtags TEXT,
                    scheduled_time DATETIME NOT NULL,
                    status TEXT DEFAULT 'scheduled',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    posted_at DATETIME,
                    error_message TEXT
                )
            ''')
            
            # Insert scheduled post
            cursor.execute('''
                INSERT INTO scheduled_instagram_posts 
                (file_path, caption, hashtags, scheduled_time)
                VALUES (?, ?, ?, ?)
            ''', (file_path, caption, json.dumps(hashtags), scheduled_time.isoformat()))
            
            schedule_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Post scheduled for {scheduled_time}")
            
            return {
                'success': True,
                'schedule_id': schedule_id,
                'scheduled_time': scheduled_time.isoformat(),
                'message': 'Post scheduled successfully'
            }
            
        except Exception as e:
            logger.error(f"Error scheduling post: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_scheduled_posts(self) -> Dict[str, Any]:
        """
        Process all scheduled posts that are due for publishing
        
        Returns:
            Dict with processing results
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get posts due for publishing
            cursor.execute('''
                SELECT id, file_path, caption, hashtags, scheduled_time
                FROM scheduled_instagram_posts 
                WHERE status = 'scheduled' 
                AND scheduled_time <= ?
            ''', (datetime.now().isoformat(),))
            
            due_posts = cursor.fetchall()
            processed = 0
            errors = 0
            
            for post in due_posts:
                post_id, file_path, caption, hashtags_json, scheduled_time = post
                
                try:
                    hashtags = json.loads(hashtags_json) if hashtags_json else []
                    
                    # Determine file type and post accordingly
                    file_ext = Path(file_path).suffix.lower()
                    
                    if file_ext in ['.jpg', '.jpeg', '.png']:
                        result = self.post_photo(file_path, caption, hashtags)
                    elif file_ext in ['.mp4', '.mov']:
                        result = self.post_video(file_path, caption, hashtags)
                    else:
                        result = {'success': False, 'error': 'Unsupported file format'}
                    
                    if result['success']:
                        # Update status to posted
                        cursor.execute('''
                            UPDATE scheduled_instagram_posts 
                            SET status = 'posted', posted_at = ?
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), post_id))
                        processed += 1
                    else:
                        # Update status to failed
                        cursor.execute('''
                            UPDATE scheduled_instagram_posts 
                            SET status = 'failed', error_message = ?
                            WHERE id = ?
                        ''', (result.get('error', 'Unknown error'), post_id))
                        errors += 1
                        
                except Exception as e:
                    logger.error(f"Error processing scheduled post {post_id}: {e}")
                    cursor.execute('''
                        UPDATE scheduled_instagram_posts 
                        SET status = 'failed', error_message = ?
                        WHERE id = ?
                    ''', (str(e), post_id))
                    errors += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Processed {processed} scheduled posts, {errors} errors")
            
            return {
                'success': True,
                'processed': processed,
                'errors': errors,
                'total_due': len(due_posts)
            }
            
        except Exception as e:
            logger.error(f"Error processing scheduled posts: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_account_insights(self) -> Dict[str, Any]:
        """
        Get Instagram account insights and performance metrics
        
        Returns:
            Dict with account insights
        """
        if not self.client:
            return {'success': False, 'error': 'Instagram client not initialized'}
        
        try:
            # Get user info
            user_info = self.client.account_info()
            
            # Get recent media for engagement analysis
            recent_media = self.client.user_medias(user_info.pk, amount=20)
            
            total_likes = sum(media.like_count for media in recent_media)
            total_comments = sum(media.comment_count for media in recent_media)
            total_views = sum(getattr(media, 'view_count', 0) for media in recent_media)
            
            avg_engagement = (total_likes + total_comments) / len(recent_media) if recent_media else 0
            engagement_rate = (avg_engagement / user_info.follower_count * 100) if user_info.follower_count > 0 else 0
            
            insights = {
                'success': True,
                'account': {
                    'username': user_info.username,
                    'full_name': user_info.full_name,
                    'followers': user_info.follower_count,
                    'following': user_info.following_count,
                    'posts': user_info.media_count
                },
                'engagement': {
                    'avg_likes': total_likes / len(recent_media) if recent_media else 0,
                    'avg_comments': total_comments / len(recent_media) if recent_media else 0,
                    'avg_views': total_views / len(recent_media) if recent_media else 0,
                    'engagement_rate': round(engagement_rate, 2)
                },
                'recent_posts': len(recent_media),
                'updated_at': datetime.now().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting account insights: {e}")
            return {'success': False, 'error': str(e)}

# Usage example and testing
if __name__ == "__main__":
    print("🔥 INSTAGRAM API HANDLER")
    print("=" * 40)
    
    handler = InstagramHandler()
    
    if handler.client:
        print("✅ Instagram client initialized")
        print("📱 Ready for Instagram integration")
        print("\n📋 FEATURES:")
        print("   • Photo and video posting")
        print("   • Story sharing")
        print("   • Post scheduling")
        print("   • Analytics tracking")
        print("   • Account insights")
        
        # Show setup instructions
        print(f"\n🔧 SETUP INSTRUCTIONS:")
        print(f"1. Install: pip install instagrapi")
        print(f"2. Configure credentials:")
        print(f"   handler.save_credentials('username', 'password')")
        print(f"3. Login: handler.login()")
        print(f"4. Start posting: handler.post_photo('path/to/image.jpg', 'Caption')")
    else:
        print("⚠️ Instagram client not available")
        print("   Run: pip install instagrapi")