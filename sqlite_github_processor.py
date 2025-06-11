#!/usr/bin/env python3
"""
SQLite GitHub Processor
Monitors lifeos_local.db for GitHub users marked for processing,
fetches their repositories, analyzes them, and stores results.
"""

import asyncio
import aiohttp
import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager
import os
import sys
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('github_processor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Repository:
    """Repository data structure"""
    name: str
    full_name: str
    description: str
    url: str
    language: str
    stars: int
    forks: int
    topics: List[str]
    created_at: str
    updated_at: str
    owner: str
    is_fork: bool
    size: int
    default_branch: str
    has_issues: bool
    has_wiki: bool
    archived: bool
    disabled: bool

@dataclass
class ProcessingResult:
    """Result of processing a GitHub user"""
    user: str
    success: bool
    repo_count: int
    error: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = None

class SQLiteGitHubProcessor:
    """Processes GitHub users from SQLite database"""
    
    def __init__(self, db_path: str = "lifeos_local.db", github_token: Optional[str] = None):
        self.db_path = db_path
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.api_base = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "LifeOS-GitHub-Processor"
        }
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
        
        # Rate limiting
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0
        
        # Ensure database exists and has proper schema
        self._ensure_database_schema()
    
    def _ensure_database_schema(self):
        """Ensure database tables exist with proper schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Add missing columns to existing tables if needed
            try:
                # Add missing columns to github_users
                cursor.execute("ALTER TABLE github_users ADD COLUMN processing_status TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE github_users ADD COLUMN repo_count INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                # Add missing columns to knowledge_hub
                cursor.execute("ALTER TABLE knowledge_hub ADD COLUMN source_url TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE knowledge_hub ADD COLUMN author TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE knowledge_hub ADD COLUMN subcategory TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE knowledge_hub ADD COLUMN metadata TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE knowledge_hub ADD COLUMN is_processed BOOLEAN DEFAULT FALSE")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE knowledge_hub ADD COLUMN processing_notes TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Create indexes for performance (only if they don't exist)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_users_process ON github_users(process_user)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_hub_source ON knowledge_hub(source)")
            
            conn.commit()
    
    def get_users_to_process(self) -> List[Tuple[int, str]]:
        """Get list of users marked for processing"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username 
                FROM github_users 
                WHERE process_user = 1
                ORDER BY id ASC
            """)
            return cursor.fetchall()
    
    async def check_rate_limit(self, session: aiohttp.ClientSession):
        """Check GitHub API rate limit"""
        async with session.get(f"{self.api_base}/rate_limit", headers=self.headers) as response:
            if response.status == 200:
                data = await response.json()
                self.rate_limit_remaining = data['rate']['remaining']
                self.rate_limit_reset = data['rate']['reset']
                logger.info(f"Rate limit: {self.rate_limit_remaining} remaining")
    
    async def wait_for_rate_limit(self):
        """Wait if rate limit is exceeded"""
        if self.rate_limit_remaining < 10:
            wait_time = max(0, self.rate_limit_reset - time.time()) + 1
            logger.warning(f"Rate limit low. Waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)
    
    @asynccontextmanager
    async def get_session(self):
        """Get aiohttp session with proper headers"""
        async with aiohttp.ClientSession() as session:
            yield session
    
    async def fetch_user_repos(self, session: aiohttp.ClientSession, username: str) -> List[Repository]:
        """Fetch all repositories for a user or organization"""
        repos = []
        page = 1
        per_page = 100
        
        # First, determine if it's a user or organization
        user_type = await self._get_user_type(session, username)
        
        while True:
            await self.wait_for_rate_limit()
            
            url = f"{self.api_base}/{'users' if user_type == 'User' else 'orgs'}/{username}/repos"
            params = {
                'page': page,
                'per_page': per_page,
                'type': 'all' if user_type == 'User' else 'all',
                'sort': 'updated',
                'direction': 'desc'
            }
            
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 5000))
                    self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))
                    
                    if response.status == 404:
                        logger.warning(f"User/Org not found: {username}")
                        break
                    elif response.status != 200:
                        logger.error(f"Error fetching repos for {username}: {response.status}")
                        break
                    
                    data = await response.json()
                    if not data:
                        break
                    
                    for repo_data in data:
                        repo = Repository(
                            name=repo_data['name'],
                            full_name=repo_data['full_name'],
                            description=repo_data.get('description', ''),
                            url=repo_data['html_url'],
                            language=repo_data.get('language', 'Unknown'),
                            stars=repo_data['stargazers_count'],
                            forks=repo_data['forks_count'],
                            topics=repo_data.get('topics', []),
                            created_at=repo_data['created_at'],
                            updated_at=repo_data['updated_at'],
                            owner=username,
                            is_fork=repo_data['fork'],
                            size=repo_data['size'],
                            default_branch=repo_data.get('default_branch', 'main'),
                            has_issues=repo_data['has_issues'],
                            has_wiki=repo_data['has_wiki'],
                            archived=repo_data['archived'],
                            disabled=repo_data['disabled']
                        )
                        repos.append(repo)
                    
                    page += 1
                    
            except Exception as e:
                logger.error(f"Exception fetching repos for {username}: {e}")
                break
        
        return repos
    
    async def _get_user_type(self, session: aiohttp.ClientSession, username: str) -> str:
        """Determine if username is a user or organization"""
        await self.wait_for_rate_limit()
        
        try:
            async with session.get(f"{self.api_base}/users/{username}", headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('type', 'User')
        except Exception as e:
            logger.error(f"Error determining user type for {username}: {e}")
        
        return 'User'  # Default to User
    
    def analyze_repository(self, repo: Repository) -> Dict[str, Any]:
        """Analyze a repository and generate insights"""
        # Determine category based on repository characteristics
        category = "Development"
        subcategory = "Open Source"
        
        if repo.language:
            subcategory = f"{repo.language} Projects"
        
        if any(topic in ['machine-learning', 'ai', 'deep-learning', 'ml'] for topic in repo.topics):
            category = "AI/ML"
            subcategory = "Machine Learning Projects"
        elif any(topic in ['web', 'frontend', 'backend', 'fullstack'] for topic in repo.topics):
            category = "Web Development"
            subcategory = "Web Applications"
        elif any(topic in ['data', 'analytics', 'database'] for topic in repo.topics):
            category = "Data Engineering"
            subcategory = "Data Projects"
        
        # Generate tags
        tags = []
        if repo.language:
            tags.append(repo.language.lower())
        tags.extend(repo.topics[:10])  # Limit to 10 topics
        if repo.stars > 100:
            tags.append("popular")
        if repo.stars > 1000:
            tags.append("trending")
        if repo.is_fork:
            tags.append("fork")
        if repo.archived:
            tags.append("archived")
        
        # Create content summary
        content_parts = [
            f"# {repo.name}",
            f"\n{repo.description or 'No description available.'}\n",
            f"**Language:** {repo.language or 'Not specified'}",
            f"**Stars:** {repo.stars}",
            f"**Forks:** {repo.forks}",
            f"**Size:** {repo.size} KB",
            f"**Created:** {repo.created_at}",
            f"**Updated:** {repo.updated_at}",
            f"**Default Branch:** {repo.default_branch}",
        ]
        
        if repo.topics:
            content_parts.append(f"**Topics:** {', '.join(repo.topics)}")
        
        if repo.archived:
            content_parts.append("\n⚠️ This repository is archived")
        
        content = "\n".join(content_parts)
        
        return {
            'title': repo.name,
            'content': content,
            'category': category,
            'subcategory': subcategory,
            'tags': tags,
            'metadata': {
                'stars': repo.stars,
                'forks': repo.forks,
                'language': repo.language,
                'size': repo.size,
                'is_fork': repo.is_fork,
                'archived': repo.archived,
                'topics': repo.topics,
                'created_at': repo.created_at,
                'updated_at': repo.updated_at
            }
        }
    
    def store_repository_in_knowledge_hub(self, repo: Repository, user_id: int):
        """Store repository information in knowledge_hub table"""
        analysis = self.analyze_repository(repo)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if repository already exists
            cursor.execute("""
                SELECT id FROM knowledge_hub 
                WHERE source = 'GitHub' AND source_url = ?
            """, (repo.url,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing entry
                cursor.execute("""
                    UPDATE knowledge_hub 
                    SET title = ?, content = ?, author = ?, category = ?, 
                        subcategory = ?, tags = ?, metadata = ?, 
                        updated_at = CURRENT_TIMESTAMP, is_processed = 1
                    WHERE id = ?
                """, (
                    analysis['title'],
                    analysis['content'],
                    repo.owner,
                    analysis['category'],
                    analysis['subcategory'],
                    json.dumps(analysis['tags']),
                    json.dumps(analysis['metadata']),
                    existing[0]
                ))
                logger.info(f"Updated repository: {repo.full_name}")
            else:
                # Insert new entry
                cursor.execute("""
                    INSERT INTO knowledge_hub 
                    (title, content, source, source_url, author, category, 
                     subcategory, tags, metadata, is_processed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    analysis['title'],
                    analysis['content'],
                    'GitHub',
                    repo.url,
                    repo.owner,
                    analysis['category'],
                    analysis['subcategory'],
                    json.dumps(analysis['tags']),
                    json.dumps(analysis['metadata'])
                ))
                logger.info(f"Stored new repository: {repo.full_name}")
            
            conn.commit()
    
    def update_user_processing_status(self, user_id: int, username: str, result: ProcessingResult):
        """Update user processing status in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if result.success:
                cursor.execute("""
                    UPDATE github_users 
                    SET process_user = 0, 
                        last_processed = CURRENT_TIMESTAMP,
                        processing_status = 'completed',
                        repos_analyzed = ?,
                        status = 'Completed'
                    WHERE id = ?
                """, (result.repo_count, user_id))
                logger.info(f"Successfully processed {username}: {result.repo_count} repositories")
            else:
                cursor.execute("""
                    UPDATE github_users 
                    SET process_user = 0,
                        last_processed = CURRENT_TIMESTAMP,
                        processing_status = ?,
                        status = 'Failed'
                    WHERE id = ?
                """, (f"error: {result.error}", user_id))
                logger.error(f"Failed to process {username}: {result.error}")
            
            conn.commit()
    
    async def process_user(self, session: aiohttp.ClientSession, user_id: int, username: str) -> ProcessingResult:
        """Process a single GitHub user"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing GitHub user: {username}")
            
            # Fetch repositories
            repos = await self.fetch_user_repos(session, username)
            
            if not repos:
                return ProcessingResult(
                    user=username,
                    success=True,
                    repo_count=0,
                    processing_time=time.time() - start_time,
                    metadata={'message': 'No repositories found'}
                )
            
            # Store each repository
            for repo in repos:
                if not repo.archived or True:  # Process archived repos too
                    self.store_repository_in_knowledge_hub(repo, user_id)
            
            # Calculate statistics
            total_stars = sum(r.stars for r in repos)
            total_forks = sum(r.forks for r in repos)
            languages = set(r.language for r in repos if r.language)
            
            return ProcessingResult(
                user=username,
                success=True,
                repo_count=len(repos),
                processing_time=time.time() - start_time,
                metadata={
                    'total_stars': total_stars,
                    'total_forks': total_forks,
                    'languages': list(languages),
                    'archived_count': sum(1 for r in repos if r.archived)
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing user {username}: {e}")
            return ProcessingResult(
                user=username,
                success=False,
                repo_count=0,
                error=str(e),
                processing_time=time.time() - start_time
            )
    
    async def process_all_marked_users(self):
        """Process all users marked for processing"""
        users = self.get_users_to_process()
        
        if not users:
            logger.info("No users marked for processing")
            return
        
        logger.info(f"Found {len(users)} users to process")
        
        async with self.get_session() as session:
            # Check rate limit before starting
            await self.check_rate_limit(session)
            
            for user_id, username in users:
                result = await self.process_user(session, user_id, username)
                self.update_user_processing_status(user_id, username, result)
                
                # Brief pause between users to be respectful
                await asyncio.sleep(1)
    
    async def monitor_and_process(self, interval: int = 60):
        """Continuously monitor for users to process"""
        logger.info(f"Starting GitHub processor monitor (checking every {interval} seconds)")
        
        while True:
            try:
                await self.process_all_marked_users()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            await asyncio.sleep(interval)

def main():
    """Main entry point"""
    # Check for GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.warning("No GITHUB_TOKEN found. API rate limits will be restrictive.")
    
    # Create processor
    processor = SQLiteGitHubProcessor(github_token=github_token)
    
    # Run processor
    try:
        # Process once
        asyncio.run(processor.process_all_marked_users())
        
        # Or run continuous monitoring (uncomment below)
        # asyncio.run(processor.monitor_and_process(interval=300))  # Check every 5 minutes
        
    except KeyboardInterrupt:
        logger.info("Processor stopped by user")
    except Exception as e:
        logger.error(f"Processor error: {e}")
        raise

if __name__ == "__main__":
    main()