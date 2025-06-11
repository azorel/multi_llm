#!/usr/bin/env python3
"""GitHub Users Processor - Monitors and processes GitHub users with checkbox workflow"""

import os
import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Load environment
env_path = Path('.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                if '#' in value:
                    value = value.split('#')[0].strip()
                os.environ[key] = value

class GitHubUsersProcessor:
    """Process GitHub users from database with checkbox workflow."""
    
        self.github_users_db_id = github_users_db_id
        self.knowledge_db_id = knowledge_db_id
        self.github_token = github_token
        
# NOTION_REMOVED:         self.notion_headers = {
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        self.github_headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'LifeOS-Autonomous-Agent'
        }
        
        if self.github_token:
            self.github_headers['Authorization'] = f'token {self.github_token}'
    
    async def process_marked_users(self):
        """Process users marked with 'Process User' checkbox."""
        print("🚀 STARTING GITHUB USERS PROCESSING")
        print("=" * 50)
        
        # Get marked users
        print("1️⃣ Finding users marked for processing...")
        
        users = await self.get_marked_users()
        if not users:
            print("❌ No users marked for processing")
            return
        
        print(f"✅ Found {len(users)} users to process")
        
        # Process each user
        for user in users:
            await self.process_user_repositories(user)
            
            # Unmark the user
            await self.unmark_user(user['id'])
        
        print("🎉 All users processed!")
    
    async def get_marked_users(self) -> List[Dict[str, Any]]:
        """Get users marked with 'Process User' checkbox."""
        try:
            query_data = {
                "filter": {
                    "property": "Process User",
                    "checkbox": {"equals": True}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=query_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('results', [])
                    else:
                        print(f"❌ Failed to query users: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ Error getting marked users: {e}")
            return []
    
    async def process_user_repositories(self, user: Dict[str, Any]):
        """Process repositories for a single user."""
        try:
            props = user.get('properties', {})
            
            # Get user info
            username = self.get_property_value(props, 'Username', 'rich_text')
            name = self.get_property_value(props, 'Name', 'title')
            
            if not username:
                print("❌ No username found")
                return
            
            print(f"\n👤 Processing user: {name} (@{username})")
            
            # Update status to Processing
            await self.update_user_status(user['id'], "Processing")
            
            # Get user profile info
            user_info = await self.get_github_user_info(username)
            if user_info:
                await self.update_user_profile_info(user['id'], user_info)
            
            # Get user repositories
            repos = await self.get_user_repositories(username)
            if not repos:
                print("❌ No repositories found")
                await self.update_user_status(user['id'], "Completed")
                return
            
            print(f"📚 Found {len(repos)} repositories")
            
            # Display repositories for selection
            selected_repos = self.display_and_select_repositories(repos, username)
            
            if not selected_repos:
                print("❌ No repositories selected")
                await self.update_user_status(user['id'], "Skipped")
                return
            
            # Import selected repositories
            imported_count = await self.import_repositories(selected_repos, username)
            
            # Update user record
            await self.update_user_completion(user['id'], imported_count)
            
            print(f"✅ Processed {username}: {imported_count} repositories imported")
            
        except Exception as e:
            print(f"❌ Error processing user: {e}")
            await self.update_user_status(user['id'], "Failed")
    
    def get_property_value(self, props: Dict[str, Any], prop_name: str, prop_type: str) -> str:
        """Extract property value from Notion properties."""
        try:
            prop = props.get(prop_name, {})
            
            if prop_type == 'title' and prop.get('title'):
                return prop['title'][0].get('plain_text', '')
            elif prop_type == 'rich_text' and prop.get('rich_text'):
                return prop['rich_text'][0].get('plain_text', '')
            elif prop_type == 'url':
                return prop.get('url', '')
            
            return ''
        except Exception:
            return ''
    
    async def get_github_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user profile information from GitHub API."""
        try:
            url = f"https://api.github.com/users/{username}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.github_headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"⚠️ Failed to get user info: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"⚠️ Error getting user info: {e}")
            return None
    
    async def get_user_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Get user's repositories from GitHub API."""
        try:
            repos = []
            page = 1
            
            while True:
                url = f"https://api.github.com/users/{username}/repos"
                params = {
                    'page': page,
                    'per_page': 100,
                    'sort': 'updated',
                    'direction': 'desc'
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=self.github_headers, params=params) as response:
                        if response.status == 200:
                            page_repos = await response.json()
                            
                            if not page_repos:
                                break
                                
                            repos.extend(page_repos)
                            page += 1
                            
                            if len(page_repos) < 100:
                                break
                        else:
                            print(f"⚠️ Failed to get repositories: {response.status}")
                            break
            
            return repos
            
        except Exception as e:
            print(f"❌ Error getting repositories: {e}")
            return []
    
    def display_and_select_repositories(self, repos: List[Dict[str, Any]], username: str) -> List[Dict[str, Any]]:
        """Display repositories and get user selection."""
        try:
            print(f"\n📚 REPOSITORIES FOR @{username}")
            print("=" * 50)
            
            # Sort by stars and recency
            sorted_repos = sorted(repos, key=lambda r: (r.get('stargazers_count', 0), r.get('updated_at', '')), reverse=True)
            
            # Display top repositories
            displayed_repos = sorted_repos[:20]  # Show top 20
            
            for i, repo in enumerate(displayed_repos, 1):
                name = repo['name']
                description = repo.get('description', 'No description')
                language = repo.get('language', 'Unknown')
                stars = repo.get('stargazers_count', 0)
                updated = repo.get('updated_at', '')
                
                if updated:
                    try:
                        updated_date = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                        updated_str = updated_date.strftime('%Y-%m-%d')
                    except:
                        updated_str = updated[:10]
                else:
                    updated_str = 'Unknown'
                
                print(f"{i:2d}. {name}")
                print(f"    📝 {description[:60]}{'...' if len(description) > 60 else ''}")
                print(f"    💻 {language} | ⭐ {stars} | 📅 {updated_str}")
                print()
            
            # Get selection
            print("📋 SELECT REPOSITORIES TO IMPORT")
            print("Enter numbers separated by commas (e.g., 1,3,5-8,12)")
            print("Or type 'top5' for top 5, 'top10' for top 10")
            print("Or type 'all' to select all repositories")
            print("Or type 'skip' to skip this user")
            
            selection = input(f"\nSelect repositories for @{username}: ").strip()
            
            if selection.lower() == 'skip':
                return []
            
            if selection.lower() == 'all':
                return repos
            
            if selection.lower() == 'top5':
                return displayed_repos[:5]
            
            if selection.lower() == 'top10':
                return displayed_repos[:10]
            
            # Parse number selection
            selected_indices = set()
            parts = selection.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Range selection
                    start, end = part.split('-')
                    start_idx = int(start.strip()) - 1
                    end_idx = int(end.strip()) - 1
                    selected_indices.update(range(start_idx, end_idx + 1))
                else:
                    # Single selection
                    selected_indices.add(int(part) - 1)
            
            # Get selected repositories
            selected_repos = []
            for idx in selected_indices:
                if 0 <= idx < len(displayed_repos):
                    selected_repos.append(displayed_repos[idx])
            
            print(f"✅ Selected {len(selected_repos)} repositories")
            return selected_repos
            
        except Exception as e:
            print(f"❌ Error in repository selection: {e}")
            return []
    
    async def import_repositories(self, repos: List[Dict[str, Any]], username: str) -> int:
        """Import selected repositories to Knowledge database."""
        try:
            # Import the GitHub repository processor
            from github_repo_processor import GitHubRepoProcessor
            
            processor = GitHubRepoProcessor(
                self.knowledge_db_id,
                self.github_token
            )
            
            imported_count = 0
            
            for i, repo in enumerate(repos, 1):
                try:
                    print(f"\n📦 Importing {i}/{len(repos)}: {repo['name']}")
                    
                    # Analyze repository
                    analysis = await processor.analyze_repository(repo)
                    
                    if analysis:
                        #                         success = await processor.                        if success:
                            imported_count += 1
                            print(f"   ✅ Imported successfully")
                        else:
                            print(f"   ❌ Import failed")
                    else:
                        print(f"   ❌ Analysis failed")
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"   ❌ Error importing {repo['name']}: {e}")
            
            print(f"\n✅ Import completed: {imported_count}/{len(repos)} repositories imported")
            return imported_count
            
        except Exception as e:
            print(f"❌ Error importing repositories: {e}")
            return 0
    
    async def update_user_status(self, user_id: str, status: str):
        """Update user processing status."""
        try:
            update_data = {
                "properties": {
                    "Processing Status": {
                        "select": {"name": status}
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        print(f"✅ Status updated to: {status}")
                    else:
                        print(f"⚠️ Failed to update status: {response.status}")
                        
        except Exception as e:
            print(f"⚠️ Error updating status: {e}")
    
    async def update_user_profile_info(self, user_id: str, user_info: Dict[str, Any]):
        """Update user profile information from GitHub API."""
        try:
            update_data = {
                "properties": {
                    "Public Repos": {
                        "number": user_info.get('public_repos', 0)
                    },
                    "Followers": {
                        "number": user_info.get('followers', 0)
                    },
                    "Following": {
                        "number": user_info.get('following', 0)
                    }
                }
            }
            
            # Add optional fields if available
            if user_info.get('bio'):
                update_data["properties"]["Bio"] = {
                    "rich_text": [{"text": {"content": user_info['bio'][:2000]}}]  # Limit length
                }
            
            if user_info.get('company'):
                update_data["properties"]["Company"] = {
                    "rich_text": [{"text": {"content": user_info['company']}}]
                }
            
            if user_info.get('location'):
                update_data["properties"]["Location"] = {
                    "rich_text": [{"text": {"content": user_info['location']}}]
                }
            
            if user_info.get('blog'):
                update_data["properties"]["Website"] = {
                    "url": user_info['blog']
                }
            
            # Set account type
            account_type = "Organization" if user_info.get('type') == 'Organization' else "User"
            update_data["properties"]["Account Type"] = {
                "select": {"name": account_type}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        print("✅ Profile info updated")
                    else:
                        print(f"⚠️ Failed to update profile: {response.status}")
                        
        except Exception as e:
            print(f"⚠️ Error updating profile: {e}")
    
    async def update_user_completion(self, user_id: str, imported_count: int):
        """Update user record after completion."""
        try:
            update_data = {
                "properties": {
                    "Processing Status": {
                        "select": {"name": "Completed"}
                    },
                    "Last Processed": {
                        "date": {"start": datetime.now().isoformat()}
                    },
                    "Repos Imported": {
                        "number": imported_count
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        print("✅ User record updated")
                    else:
                        print(f"⚠️ Failed to update user record: {response.status}")
                        
        except Exception as e:
            print(f"⚠️ Error updating user record: {e}")
    
    async def unmark_user(self, user_id: str):
        """Unmark the 'Process User' checkbox."""
        try:
            update_data = {
                "properties": {
                    "Process User": {
                        "checkbox": False
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        print("✅ User unmarked")
                    else:
                        print(f"⚠️ Failed to unmark user: {response.status}")
                        
        except Exception as e:
            print(f"⚠️ Error unmarking user: {e}")

async def main():
    """Main function to process GitHub users."""
    print("🚀 GITHUB USERS PROCESSOR")
    print("=" * 30)
    
    # Configuration
# NOTION_REMOVED:     github_users_db_id = os.getenv('NOTION_GITHUB_USERS_DATABASE_ID')
# NOTION_REMOVED:     knowledge_db_id = os.getenv('NOTION_KNOWLEDGE_DATABASE_ID', '20bec31c-9de2-814e-80db-d13d0c27d869')
    github_token = os.getenv('GITHUB_TOKEN')
    
        return
    
    if not github_users_db_id:
        print("❌ No NOTION_GITHUB_USERS_DATABASE_ID found in environment")
        print("Please set up the GitHub Users database first")
        return
    
    # Initialize processor
    
    # Process marked users
    await processor.process_marked_users()

if __name__ == "__main__":
    asyncio.run(main())