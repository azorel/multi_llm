#!/usr/bin/env python3
"""
GitHub Repository Processor for Knowledge Hub Integration
=========================================================

Processes GitHub repositories and imports them into the knowledge hub
similar to how YouTube videos are processed.
"""

import requests
import sqlite3
import logging
import json
import base64
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubRepositoryProcessor:
    def __init__(self, github_token: str = None):
        """Initialize the GitHub repository processor."""
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        if self.github_token:
            self.session.headers.update({
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            })
        else:
            logger.warning("No GitHub token provided. API requests will be rate-limited.")

    def extract_repo_info(self, repo_url: str) -> Optional[Dict]:
        """Extract repository information from GitHub URL."""
        try:
            # Parse GitHub URL to get owner and repo name
            pattern = r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
            match = re.search(pattern, repo_url)
            
            if not match:
                logger.error(f"Invalid GitHub URL format: {repo_url}")
                return None
            
            owner, repo_name = match.groups()
            
            # Get repository information
            repo_api_url = f"{self.base_url}/repos/{owner}/{repo_name}"
            response = self.session.get(repo_api_url)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch repo info: {response.status_code}")
                return None
            
            repo_data = response.json()
            
            # Get additional repository content
            readme_content = self.get_readme_content(owner, repo_name)
            languages = self.get_repository_languages(owner, repo_name)
            recent_commits = self.get_recent_commits(owner, repo_name)
            
            # Compile comprehensive repository information
            repo_info = {
                'name': repo_data.get('name'),
                'full_name': repo_data.get('full_name'),
                'description': repo_data.get('description', 'No description available'),
                'url': repo_data.get('html_url'),
                'clone_url': repo_data.get('clone_url'),
                'language': repo_data.get('language'),
                'languages': languages,
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
                'watchers': repo_data.get('watchers_count', 0),
                'open_issues': repo_data.get('open_issues_count', 0),
                'created_at': repo_data.get('created_at'),
                'updated_at': repo_data.get('updated_at'),
                'pushed_at': repo_data.get('pushed_at'),
                'size': repo_data.get('size', 0),
                'default_branch': repo_data.get('default_branch', 'main'),
                'topics': repo_data.get('topics', []),
                'license': repo_data.get('license', {}).get('name') if repo_data.get('license') else None,
                'readme_content': readme_content,
                'recent_commits': recent_commits,
                'owner': {
                    'login': repo_data.get('owner', {}).get('login'),
                    'type': repo_data.get('owner', {}).get('type'),
                    'url': repo_data.get('owner', {}).get('html_url')
                }
            }
            
            return repo_info
            
        except Exception as e:
            logger.error(f"Error extracting repo info from {repo_url}: {e}")
            return None

    def get_readme_content(self, owner: str, repo_name: str) -> str:
        """Get README content from repository."""
        try:
            readme_url = f"{self.base_url}/repos/{owner}/{repo_name}/readme"
            response = self.session.get(readme_url)
            
            if response.status_code == 200:
                readme_data = response.json()
                content = base64.b64decode(readme_data['content']).decode('utf-8')
                return content
            else:
                return "No README found"
                
        except Exception as e:
            logger.error(f"Error fetching README: {e}")
            return "Error fetching README"

    def get_repository_languages(self, owner: str, repo_name: str) -> Dict:
        """Get programming languages used in the repository."""
        try:
            languages_url = f"{self.base_url}/repos/{owner}/{repo_name}/languages"
            response = self.session.get(languages_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching languages: {e}")
            return {}

    def get_recent_commits(self, owner: str, repo_name: str, limit: int = 5) -> List[Dict]:
        """Get recent commits from the repository."""
        try:
            commits_url = f"{self.base_url}/repos/{owner}/{repo_name}/commits"
            params = {'per_page': limit}
            response = self.session.get(commits_url, params=params)
            
            if response.status_code == 200:
                commits_data = response.json()
                commits = []
                
                for commit in commits_data:
                    commits.append({
                        'sha': commit['sha'][:7],
                        'message': commit['commit']['message'].split('\n')[0],
                        'author': commit['commit']['author']['name'],
                        'date': commit['commit']['author']['date'],
                        'url': commit['html_url']
                    })
                
                return commits
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error fetching commits: {e}")
            return []

    def format_repository_content(self, repo_info: Dict) -> str:
        """Format repository information for knowledge hub storage."""
        content_parts = []
        
        # Repository Overview
        content_parts.append(f"# {repo_info['name']}")
        content_parts.append(f"**Full Name:** {repo_info['full_name']}")
        content_parts.append(f"**Description:** {repo_info['description']}")
        content_parts.append(f"**URL:** {repo_info['url']}")
        content_parts.append("")
        
        # Statistics
        content_parts.append("## Repository Statistics")
        content_parts.append(f"- ⭐ Stars: {repo_info['stars']:,}")
        content_parts.append(f"- 🍴 Forks: {repo_info['forks']:,}")
        content_parts.append(f"- 👀 Watchers: {repo_info['watchers']:,}")
        content_parts.append(f"- 🐛 Open Issues: {repo_info['open_issues']:,}")
        content_parts.append(f"- 📦 Size: {repo_info['size']:,} KB")
        content_parts.append("")
        
        # Technical Details
        content_parts.append("## Technical Information")
        content_parts.append(f"- **Primary Language:** {repo_info['language'] or 'Not specified'}")
        content_parts.append(f"- **Default Branch:** {repo_info['default_branch']}")
        content_parts.append(f"- **License:** {repo_info['license'] or 'No license specified'}")
        
        if repo_info['topics']:
            content_parts.append(f"- **Topics:** {', '.join(repo_info['topics'])}")
        
        # Languages breakdown
        if repo_info['languages']:
            content_parts.append("")
            content_parts.append("### Programming Languages")
            total_bytes = sum(repo_info['languages'].values())
            for lang, bytes_count in sorted(repo_info['languages'].items(), key=lambda x: x[1], reverse=True):
                percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                content_parts.append(f"- **{lang}:** {percentage:.1f}%")
        
        # Dates
        content_parts.append("")
        content_parts.append("## Timeline")
        content_parts.append(f"- **Created:** {repo_info['created_at']}")
        content_parts.append(f"- **Last Updated:** {repo_info['updated_at']}")
        content_parts.append(f"- **Last Push:** {repo_info['pushed_at']}")
        
        # Recent Commits
        if repo_info['recent_commits']:
            content_parts.append("")
            content_parts.append("## Recent Commits")
            for commit in repo_info['recent_commits']:
                content_parts.append(f"- **{commit['sha']}** by {commit['author']}: {commit['message']}")
        
        # Owner Information
        content_parts.append("")
        content_parts.append("## Repository Owner")
        content_parts.append(f"- **Username:** {repo_info['owner']['login']}")
        content_parts.append(f"- **Type:** {repo_info['owner']['type']}")
        content_parts.append(f"- **Profile:** {repo_info['owner']['url']}")
        
        # README Content
        if repo_info['readme_content'] and repo_info['readme_content'] != "No README found":
            content_parts.append("")
            content_parts.append("## README Content")
            content_parts.append("```")
            # Limit README content to prevent overly large entries
            readme_preview = repo_info['readme_content'][:5000]
            if len(repo_info['readme_content']) > 5000:
                readme_preview += "\n\n... (README truncated for storage)"
            content_parts.append(readme_preview)
            content_parts.append("```")
        
        return "\n".join(content_parts)

    def add_to_knowledge_hub(self, repo_info: Dict, db_path: str = 'lifeos_local.db') -> bool:
        """Add repository information to the knowledge hub database."""
        try:
            formatted_content = self.format_repository_content(repo_info)
            
            # Create tags based on repository characteristics
            tags = ['github', 'repository', 'code-analysis']
            if repo_info['language']:
                tags.append(repo_info['language'].lower())
            tags.extend([topic.lower() for topic in repo_info['topics'][:3]])  # Limit topics
            
            # Determine category based on repository characteristics
            category = 'GitHub Repository'
            if repo_info['stars'] > 1000:
                category = 'Popular GitHub Repository'
            elif repo_info['language'] in ['Python', 'JavaScript', 'TypeScript', 'Java', 'C++']:
                category = f'{repo_info["language"]} GitHub Repository'
            
            knowledge_data = {
                'title': f"{repo_info['full_name']} - GitHub Repository",
                'source': repo_info['url'],
                'content': formatted_content,
                'category': category,
                'tags': ','.join(tags),
                'created_date': datetime.now().isoformat(),
                'last_edited': datetime.now().isoformat(),
                # Additional metadata
                'github_stars': repo_info['stars'],
                'github_forks': repo_info['forks'],
                'github_language': repo_info['language'],
                'github_owner': repo_info['owner']['login']
            }
            
            # Connect to database and insert
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if repository already exists
            cursor.execute(
                "SELECT id FROM knowledge_hub WHERE source = ?",
                (repo_info['url'],)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing entry
                cursor.execute("""
                    UPDATE knowledge_hub 
                    SET content = ?, last_edited = ?, tags = ?, 
                        github_stars = ?, github_forks = ?
                    WHERE source = ?
                """, (
                    formatted_content,
                    knowledge_data['last_edited'],
                    knowledge_data['tags'],
                    repo_info['stars'],
                    repo_info['forks'],
                    repo_info['url']
                ))
                logger.info(f"Updated existing repository: {repo_info['full_name']}")
                knowledge_id = existing[0]
            else:
                # Insert new entry
                placeholders = ', '.join(['?' for _ in knowledge_data])
                columns = ', '.join(knowledge_data.keys())
                
                cursor.execute(
                    f"INSERT INTO knowledge_hub ({columns}) VALUES ({placeholders})",
                    list(knowledge_data.values())
                )
                knowledge_id = cursor.lastrowid
                logger.info(f"Added new repository: {repo_info['full_name']}")
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding repository to knowledge hub: {e}")
            return False

    def process_repository(self, repo_url: str) -> Tuple[bool, str, Optional[int]]:
        """Process a GitHub repository and add it to knowledge hub."""
        try:
            logger.info(f"Processing repository: {repo_url}")
            
            # Extract repository information
            repo_info = self.extract_repo_info(repo_url)
            if not repo_info:
                return False, "Failed to extract repository information", None
            
            # Add to knowledge hub
            success = self.add_to_knowledge_hub(repo_info)
            if not success:
                return False, "Failed to add repository to knowledge hub", None
            
            message = f"Successfully processed {repo_info['full_name']} - {repo_info['stars']} stars, {repo_info['language'] or 'No language'}"
            
            return True, message, repo_info.get('stars', 0)
            
        except Exception as e:
            logger.error(f"Error processing repository {repo_url}: {e}")
            return False, f"Error: {str(e)}", None

def main():
    """Test the GitHub repository processor."""
    processor = GitHubRepositoryProcessor()
    
    # Test with a sample repository
    test_repo = "https://github.com/microsoft/vscode"
    success, message, stars = processor.process_repository(test_repo)
    
    print(f"Success: {success}")
    print(f"Message: {message}")
    print(f"Stars: {stars}")

if __name__ == "__main__":
    main()