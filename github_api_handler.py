#!/usr/bin/env python3
"""
GitHub API Handler
Real GitHub API integration for fetching user repositories
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import json
from pathlib import Path
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class GitHubAPIHandler:
    """Enhanced GitHub API handler with batch processing and automation"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.token_valid = False
        
        # Set headers
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'LifeOS-Knowledge-Hub'
        })
        
        if self.token:
            # Validate token before using it
            if self._validate_token():
                self.session.headers['Authorization'] = f'token {self.token}'
                self.token_valid = True
                logger.info("🔑 GitHub API token configured and validated")
            else:
                logger.warning("⚠️ GitHub token invalid - using unauthenticated API (limited rate)")
                self.token = None
        else:
            logger.warning("⚠️ No GitHub token - using unauthenticated API (limited rate)")
        
        # Enhanced features
        self.processing_queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.rate_limit_info = {}
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.monitoring_enabled = False
        self.processing_callbacks = []
        self.batch_size = 5
        self.retry_attempts = 3
        self.retry_delay = 1
    
    def _validate_token(self) -> bool:
        """Validate GitHub token by making a test API call"""
        if not self.token:
            return False
        
        try:
            # Test token with a simple API call
            headers = {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'LifeOS-Knowledge-Hub'
            }
            
            response = requests.get(f"{self.base_url}/user", headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"✅ GitHub token valid - authenticated as: {user_data.get('login', 'Unknown')}")
                return True
            elif response.status_code == 401:
                logger.error("❌ GitHub token invalid or expired")
                return False
            else:
                logger.warning(f"⚠️ GitHub token validation failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error validating GitHub token: {e}")
            return False
    
    def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get GitHub user information"""
        try:
            url = f"{self.base_url}/users/{username}"
            response = self.session.get(url)
            
            if response.status_code == 404:
                return {"success": False, "error": f"User '{username}' not found"}
            elif response.status_code == 401:
                return {"success": False, "error": "GitHub authentication failed. Please check your token."}
            elif response.status_code == 403:
                error_msg = "Rate limit exceeded."
                if not self.token_valid:
                    error_msg += " Add a valid GitHub token for higher limits."
                return {"success": False, "error": error_msg}
            elif response.status_code != 200:
                return {"success": False, "error": f"GitHub API error: {response.status_code}"}
            
            data = response.json()
            return {
                "success": True,
                "user": {
                    "username": data.get("login"),
                    "name": data.get("name"),
                    "avatar_url": data.get("avatar_url"),
                    "bio": data.get("bio"),
                    "company": data.get("company"),
                    "location": data.get("location"),
                    "public_repos": data.get("public_repos", 0),
                    "followers": data.get("followers", 0),
                    "following": data.get("following", 0),
                    "created_at": data.get("created_at"),
                    "github_url": data.get("html_url")
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching user info for {username}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_repositories(self, username: str, max_repos: int = 100) -> Dict[str, Any]:
        """Get all repositories for a GitHub user"""
        try:
            logger.info(f"📦 Fetching repositories for {username}")
            
            repositories = []
            page = 1
            per_page = 30  # GitHub API limit
            
            while len(repositories) < max_repos:
                url = f"{self.base_url}/users/{username}/repos"
                params = {
                    'page': page,
                    'per_page': per_page,
                    'sort': 'updated',
                    'type': 'all'
                }
                
                response = self.session.get(url, params=params)
                
                if response.status_code == 404:
                    return {"success": False, "error": f"User '{username}' not found"}
                elif response.status_code == 403:
                    return {"success": False, "error": "Rate limit exceeded"}
                elif response.status_code != 200:
                    return {"success": False, "error": f"GitHub API error: {response.status_code}"}
                
                repos_data = response.json()
                
                if not repos_data:  # No more repositories
                    break
                
                for repo in repos_data:
                    if len(repositories) >= max_repos:
                        break
                        
                    repo_info = {
                        "name": repo.get("name"),
                        "full_name": repo.get("full_name"),
                        "description": repo.get("description", ""),
                        "language": repo.get("language", "Unknown"),
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "size": repo.get("size", 0),
                        "created_at": repo.get("created_at"),
                        "updated_at": repo.get("updated_at"),
                        "pushed_at": repo.get("pushed_at"),
                        "clone_url": repo.get("clone_url"),
                        "html_url": repo.get("html_url"),
                        "private": repo.get("private", False),
                        "fork": repo.get("fork", False),
                        "archived": repo.get("archived", False),
                        "topics": repo.get("topics", []),
                        "license": repo.get("license", {}).get("name") if repo.get("license") else None
                    }
                    repositories.append(repo_info)
                
                page += 1
                
                # Rate limiting - be nice to GitHub API
                time.sleep(0.1)
            
            logger.info(f"✅ Found {len(repositories)} repositories for {username}")
            
            return {
                "success": True,
                "username": username,
                "repositories": repositories,
                "total_found": len(repositories)
            }
            
        except Exception as e:
            logger.error(f"Error fetching repositories for {username}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_repository_details(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific repository"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo_name}"
            response = self.session.get(url)
            
            if response.status_code == 404:
                return {"success": False, "error": f"Repository '{owner}/{repo_name}' not found"}
            elif response.status_code != 200:
                return {"success": False, "error": f"GitHub API error: {response.status_code}"}
            
            data = response.json()
            
            # Get README content
            readme_content = self._get_readme(owner, repo_name)
            
            # Get languages
            languages = self._get_languages(owner, repo_name)
            
            return {
                "success": True,
                "repository": {
                    "name": data.get("name"),
                    "full_name": data.get("full_name"),
                    "description": data.get("description", ""),
                    "language": data.get("language"),
                    "languages": languages,
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "issues": data.get("open_issues_count", 0),
                    "size": data.get("size", 0),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "pushed_at": data.get("pushed_at"),
                    "clone_url": data.get("clone_url"),
                    "html_url": data.get("html_url"),
                    "topics": data.get("topics", []),
                    "license": data.get("license", {}).get("name") if data.get("license") else None,
                    "readme": readme_content,
                    "default_branch": data.get("default_branch", "main")
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching repository details for {owner}/{repo_name}: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_readme(self, owner: str, repo_name: str) -> str:
        """Get README content for a repository"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo_name}/readme"
            response = self.session.get(url)
            
            if response.status_code == 200:
                readme_data = response.json()
                import base64
                content = base64.b64decode(readme_data.get("content", "")).decode('utf-8')
                return content[:5000]  # Limit to first 5000 chars
            
            return ""
            
        except Exception as e:
            logger.debug(f"Could not fetch README for {owner}/{repo_name}: {e}")
            return ""
    
    def _get_languages(self, owner: str, repo_name: str) -> Dict[str, int]:
        """Get programming languages used in a repository"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo_name}/languages"
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            
            return {}
            
        except Exception as e:
            logger.debug(f"Could not fetch languages for {owner}/{repo_name}: {e}")
            return {}
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Check current rate limit status with caching"""
        try:
            # Check cache first
            cache_key = "rate_limit"
            if self._is_cached(cache_key):
                return self.cache[cache_key]['data']
            
            url = f"{self.base_url}/rate_limit"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    "success": True,
                    "core": data.get("resources", {}).get("core", {}),
                    "search": data.get("resources", {}).get("search", {}),
                    "graphql": data.get("resources", {}).get("graphql", {}),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Cache the result
                self._cache_result(cache_key, result)
                self.rate_limit_info = result
                return result
            
            return {"success": False, "error": "Could not fetch rate limit"}
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return {"success": False, "error": str(e)}
    
    def batch_process_users(self, usernames: List[str], callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process multiple GitHub users in batches"""
        logger.info(f"🔄 Starting batch processing of {len(usernames)} users")
        
        results = {
            "success": True,
            "total_users": len(usernames),
            "processed": 0,
            "failed": 0,
            "results": [],
            "errors": []
        }
        
        # Process in batches
        for i in range(0, len(usernames), self.batch_size):
            batch = usernames[i:i + self.batch_size]
            logger.info(f"📦 Processing batch {i//self.batch_size + 1}: {batch}")
            
            # Check rate limits before processing
            rate_status = self.get_rate_limit_status()
            if rate_status["success"]:
                remaining = rate_status.get("core", {}).get("remaining", 0)
                if remaining < len(batch) * 2:  # Need at least 2 calls per user
                    reset_time = rate_status.get("core", {}).get("reset", time.time())
                    wait_time = max(0, reset_time - time.time())
                    logger.warning(f"⏳ Rate limit low, waiting {wait_time:.0f} seconds")
                    time.sleep(wait_time + 1)
            
            # Process batch
            batch_results = self._process_user_batch(batch)
            
            for result in batch_results:
                if result["success"]:
                    results["processed"] += 1
                    results["results"].append(result)
                    
                    # Call callback if provided
                    if callback:
                        try:
                            callback(result)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")
                else:
                    results["failed"] += 1
                    results["errors"].append(result)
            
            # Rate limiting between batches
            if i + self.batch_size < len(usernames):
                time.sleep(1)
        
        logger.info(f"✅ Batch processing complete: {results['processed']} processed, {results['failed']} failed")
        return results
    
    def _process_user_batch(self, usernames: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of users concurrently"""
        results = []
        
        # Use thread pool for concurrent processing
        with ThreadPoolExecutor(max_workers=min(3, len(usernames))) as executor:
            futures = []
            
            for username in usernames:
                future = executor.submit(self._process_single_user_with_retry, username)
                futures.append((username, future))
            
            # Collect results
            for username, future in futures:
                try:
                    result = future.result(timeout=30)  # 30 second timeout
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing user {username}: {e}")
                    results.append({
                        "success": False,
                        "username": username,
                        "error": str(e)
                    })
        
        return results
    
    def _process_single_user_with_retry(self, username: str) -> Dict[str, Any]:
        """Process a single user with retry logic"""
        for attempt in range(self.retry_attempts):
            try:
                # Get user info
                user_result = self.get_user_info(username)
                if not user_result["success"]:
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    return user_result
                
                # Get repositories
                repos_result = self.get_user_repositories(username)
                if not repos_result["success"]:
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    return repos_result
                
                return {
                    "success": True,
                    "username": username,
                    "user_info": user_result["user"],
                    "repositories": repos_result["repositories"],
                    "total_repos": len(repos_result["repositories"]),
                    "processed_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    logger.warning(f"Attempt {attempt + 1} failed for {username}: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    logger.error(f"All attempts failed for {username}: {e}")
                    return {
                        "success": False,
                        "username": username,
                        "error": str(e)
                    }
        
        return {
            "success": False,
            "username": username,
            "error": "Max retry attempts exceeded"
        }
    
    def monitor_repository_updates(self, repositories: List[Dict[str, str]], 
                                 callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Monitor repositories for updates"""
        logger.info(f"👀 Starting repository monitoring for {len(repositories)} repos")
        
        updates_found = []
        errors = []
        
        for repo in repositories:
            try:
                owner = repo.get('owner', '')
                name = repo.get('name', '')
                last_checked = repo.get('last_checked', '')
                
                if not owner or not name:
                    continue
                
                # Get current repository info
                current_info = self.get_repository_details(owner, name)
                
                if current_info["success"]:
                    repo_data = current_info["repository"]
                    last_push = repo_data.get('pushed_at', '')
                    
                    # Check if updated since last check
                    if last_checked and last_push > last_checked:
                        update_info = {
                            "owner": owner,
                            "name": name,
                            "last_push": last_push,
                            "previous_check": last_checked,
                            "repository_data": repo_data
                        }
                        updates_found.append(update_info)
                        
                        if callback:
                            try:
                                callback(update_info)
                            except Exception as e:
                                logger.error(f"Monitoring callback error: {e}")
                
                time.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error monitoring {repo}: {e}")
                errors.append({"repository": repo, "error": str(e)})
        
        result = {
            "success": True,
            "monitored": len(repositories),
            "updates_found": len(updates_found),
            "updates": updates_found,
            "errors": errors,
            "checked_at": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Repository monitoring complete: {len(updates_found)} updates found")
        return result
    
    def health_check_repositories(self, repositories: List[Dict[str, str]]) -> Dict[str, Any]:
        """Perform health checks on repositories"""
        logger.info(f"🔍 Running health checks on {len(repositories)} repositories")
        
        healthy = []
        unhealthy = []
        errors = []
        
        for repo in repositories:
            try:
                owner = repo.get('owner', '')
                name = repo.get('name', '')
                
                if not owner or not name:
                    continue
                
                # Get repository details
                repo_info = self.get_repository_details(owner, name)
                
                if repo_info["success"]:
                    repo_data = repo_info["repository"]
                    
                    # Determine health status
                    health_score = self._calculate_repo_health(repo_data)
                    
                    health_info = {
                        "owner": owner,
                        "name": name,
                        "health_score": health_score,
                        "last_updated": repo_data.get('updated_at'),
                        "size": repo_data.get('size', 0),
                        "stars": repo_data.get('stars', 0),
                        "issues": repo_data.get('issues', 0),
                        "has_readme": bool(repo_data.get('readme', ''))
                    }
                    
                    if health_score >= 0.7:
                        healthy.append(health_info)
                    else:
                        unhealthy.append(health_info)
                else:
                    errors.append({"repository": f"{owner}/{name}", "error": repo_info.get("error", "Unknown error")})
                
                time.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error checking health of {repo}: {e}")
                errors.append({"repository": repo, "error": str(e)})
        
        result = {
            "success": True,
            "total_checked": len(repositories),
            "healthy": len(healthy),
            "unhealthy": len(unhealthy),
            "healthy_repos": healthy,
            "unhealthy_repos": unhealthy,
            "errors": errors,
            "checked_at": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Health check complete: {len(healthy)} healthy, {len(unhealthy)} unhealthy")
        return result
    
    def _calculate_repo_health(self, repo_data: Dict[str, Any]) -> float:
        """Calculate repository health score (0-1)"""
        score = 0.0
        max_score = 0.0
        
        # Has README (20%)
        max_score += 0.2
        if repo_data.get('readme', ''):
            score += 0.2
        
        # Recent activity (30%)
        max_score += 0.3
        pushed_at = repo_data.get('pushed_at', '')
        if pushed_at:
            try:
                push_date = datetime.fromisoformat(pushed_at.replace('Z', '+00:00'))
                days_since_push = (datetime.now(push_date.tzinfo) - push_date).days
                if days_since_push <= 30:
                    score += 0.3
                elif days_since_push <= 90:
                    score += 0.2
                elif days_since_push <= 180:
                    score += 0.1
            except:
                pass
        
        # Stars and engagement (20%)
        max_score += 0.2
        stars = repo_data.get('stars', 0)
        if stars >= 100:
            score += 0.2
        elif stars >= 10:
            score += 0.15
        elif stars >= 1:
            score += 0.1
        
        # Size and content (15%)
        max_score += 0.15
        size = repo_data.get('size', 0)
        if size > 1000:  # KB
            score += 0.15
        elif size > 100:
            score += 0.1
        elif size > 0:
            score += 0.05
        
        # License (15%)
        max_score += 0.15
        if repo_data.get('license'):
            score += 0.15
        
        return score / max_score if max_score > 0 else 0.0
    
    def _is_cached(self, key: str) -> bool:
        """Check if result is cached and still valid"""
        if key not in self.cache:
            return False
        
        cached_time = self.cache[key]['timestamp']
        return (time.time() - cached_time) < self.cache_ttl
    
    def _cache_result(self, key: str, data: Any):
        """Cache a result with timestamp"""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def add_processing_callback(self, callback: Callable):
        """Add a callback for processing events"""
        self.processing_callbacks.append(callback)
    
    def enable_monitoring(self):
        """Enable continuous monitoring"""
        self.monitoring_enabled = True
        logger.info("📡 GitHub monitoring enabled")
    
    def disable_monitoring(self):
        """Disable continuous monitoring"""
        self.monitoring_enabled = False
        logger.info("📡 GitHub monitoring disabled")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "cache_size": len(self.cache),
            "rate_limit_info": self.rate_limit_info,
            "monitoring_enabled": self.monitoring_enabled,
            "batch_size": self.batch_size,
            "retry_attempts": self.retry_attempts,
            "callbacks_registered": len(self.processing_callbacks)
        }

# Global instance with environment token
load_dotenv()
github_token = os.getenv('GITHUB_TOKEN')
github_api = GitHubAPIHandler(github_token)

def set_github_token(token: str):
    """Set GitHub API token"""
    global github_api
    github_api = GitHubAPIHandler(token)
    logger.info("🔑 GitHub API token updated")

def setup_automated_processing():
    """Setup automated processing workflows"""
    github_api.enable_monitoring()
    logger.info("🤖 Automated GitHub processing setup complete")