#!/usr/bin/env python3
"""GitHub Repository Processor for Knowledge Database Import"""

import os
import asyncio
import aiohttp
import json
import re
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

class GitHubRepoProcessor:
    """Process GitHub repositories and import selected ones to Knowledge database."""
    
        self.knowledge_db_id = knowledge_db_id
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        
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
    
    async def get_user_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Fetch all repositories for a GitHub user."""
        try:
            repos = []
            page = 1
            per_page = 100
            
            print(f"🔍 Fetching repositories for user: {username}")
            
            async with aiohttp.ClientSession() as session:
                while True:
                    url = f"https://api.github.com/users/{username}/repos"
                    params = {
                        'page': page,
                        'per_page': per_page,
                        'sort': 'updated',
                        'direction': 'desc'
                    }
                    
                    async with session.get(url, headers=self.github_headers, params=params) as response:
                        if response.status == 200:
                            page_repos = await response.json()
                            
                            if not page_repos:  # No more repos
                                break
                                
                            repos.extend(page_repos)
                            print(f"📋 Fetched page {page}: {len(page_repos)} repositories")
                            page += 1
                            
                            if len(page_repos) < per_page:  # Last page
                                break
                        else:
                            error_text = await response.text()
                            print(f"❌ GitHub API error: {response.status} - {error_text}")
                            break
            
            print(f"✅ Found {len(repos)} total repositories for {username}")
            return repos
            
        except Exception as e:
            print(f"❌ Error fetching repositories: {e}")
            return []
    
    def display_repositories(self, repos: List[Dict[str, Any]]) -> None:
        """Display repositories in a selectable format."""
        print(f"\n📚 AVAILABLE REPOSITORIES")
        print("=" * 60)
        
        for i, repo in enumerate(repos, 1):
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
            
            print(f"{i:3d}. {name}")
            print(f"     📝 {description[:70]}{'...' if len(description) > 70 else ''}")
            print(f"     💻 {language} | ⭐ {stars} | 📅 {updated_str}")
            print()
    
    def get_user_selection(self, repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get user selection of repositories to import."""
        try:
            print("📋 SELECT REPOSITORIES TO IMPORT")
            print("Enter repository numbers separated by commas (e.g., 1,3,5-8,12)")
            print("Or type 'all' to select all repositories")
            print("Or type 'quit' to cancel")
            
            selection = input("\nYour selection: ").strip()
            
            if selection.lower() == 'quit':
                return []
            
            if selection.lower() == 'all':
                return repos
            
            # Parse selection
            selected_indices = set()
            parts = selection.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Range selection (e.g., 5-8)
                    start, end = part.split('-')
                    start_idx = int(start.strip()) - 1
                    end_idx = int(end.strip()) - 1
                    selected_indices.update(range(start_idx, end_idx + 1))
                else:
                    # Single selection
                    selected_indices.add(int(part) - 1)
            
            # Filter selected repositories
            selected_repos = []
            for idx in selected_indices:
                if 0 <= idx < len(repos):
                    selected_repos.append(repos[idx])
            
            print(f"✅ Selected {len(selected_repos)} repositories for import")
            return selected_repos
            
        except Exception as e:
            print(f"❌ Error parsing selection: {e}")
            return []
    
    async def analyze_repository(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a repository and extract key information."""
        try:
            name = repo['name']
            description = repo.get('description', '')
            language = repo.get('language', 'Unknown')
            topics = repo.get('topics', [])
            
            print(f"🔍 Analyzing repository: {name}")
            
            # Get repository contents to understand structure
            contents = await self.get_repo_contents(repo['full_name'])
            
            # Analyze the codebase
            analysis = {
                'name': name,
                'full_name': repo['full_name'],
                'description': description,
                'language': language,
                'topics': topics,
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'size': repo.get('size', 0),
                'updated_at': repo.get('updated_at', ''),
                'clone_url': repo.get('clone_url', ''),
                'html_url': repo.get('html_url', ''),
                'contents': contents,
                'project_type': self.determine_project_type(contents, language, topics),
                'key_files': self.identify_key_files(contents),
                'complexity': self.assess_complexity(contents, repo.get('size', 0)),
                'frameworks': self.detect_frameworks(contents, language)
            }
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing repository {repo['name']}: {e}")
            return {}
    
    async def get_repo_contents(self, full_name: str, path: str = "") -> List[Dict[str, Any]]:
        """Get repository contents from GitHub API."""
        try:
            url = f"https://api.github.com/repos/{full_name}/contents/{path}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.github_headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return []
                        
        except Exception as e:
            print(f"⚠️ Error getting contents for {full_name}: {e}")
            return []
    
    def determine_project_type(self, contents: List[Dict], language: str, topics: List[str]) -> str:
        """Determine the type of project based on contents and metadata."""
        file_names = [item['name'].lower() for item in contents if item['type'] == 'file']
        
        # Check for specific project types
        if 'package.json' in file_names:
            return 'Node.js/JavaScript Project'
        elif 'requirements.txt' in file_names or 'pyproject.toml' in file_names:
            return 'Python Project'
        elif 'cargo.toml' in file_names:
            return 'Rust Project'
        elif 'go.mod' in file_names:
            return 'Go Project'
        elif 'pom.xml' in file_names or 'build.gradle' in file_names:
            return 'Java Project'
        elif 'dockerfile' in file_names or 'docker-compose.yml' in file_names:
            return 'Docker/Containerized Project'
        elif any(topic in ['ai', 'machine-learning', 'ml', 'artificial-intelligence'] for topic in topics):
            return 'AI/ML Project'
        elif any(topic in ['web', 'webapp', 'website'] for topic in topics):
            return 'Web Application'
        elif any(topic in ['api', 'rest-api', 'graphql'] for topic in topics):
            return 'API Project'
        elif language:
            return f'{language} Project'
        else:
            return 'General Project'
    
    def identify_key_files(self, contents: List[Dict]) -> List[str]:
        """Identify key files in the repository."""
        key_files = []
        important_files = [
            'readme.md', 'readme.txt', 'readme.rst',
            'package.json', 'requirements.txt', 'cargo.toml', 'go.mod',
            'dockerfile', 'docker-compose.yml', 'makefile',
            'license', 'license.md', 'license.txt',
            '.gitignore', '.env.example'
        ]
        
        for item in contents:
            if item['type'] == 'file' and item['name'].lower() in important_files:
                key_files.append(item['name'])
        
        return key_files
    
    def assess_complexity(self, contents: List[Dict], size_kb: int) -> str:
        """Assess the complexity of the project."""
        file_count = len([item for item in contents if item['type'] == 'file'])
        dir_count = len([item for item in contents if item['type'] == 'dir'])
        
        if size_kb > 10000 or file_count > 50 or dir_count > 10:
            return 'High'
        elif size_kb > 1000 or file_count > 20 or dir_count > 5:
            return 'Medium'
        else:
            return 'Low'
    
    def detect_frameworks(self, contents: List[Dict], language: str) -> List[str]:
        """Detect frameworks and libraries used in the project."""
        frameworks = []
        file_names = [item['name'].lower() for item in contents if item['type'] == 'file']
        
        # Framework detection patterns
        framework_indicators = {
            'React': ['package.json'],  # Would need to check package.json contents
            'Vue.js': ['vue.config.js', 'nuxt.config.js'],
            'Angular': ['angular.json'],
            'Django': ['manage.py', 'settings.py'],
            'Flask': ['app.py', 'wsgi.py'],
            'FastAPI': ['main.py'],  # Would need content analysis
            'Express.js': ['package.json'],  # Would need package.json analysis
            'Docker': ['dockerfile', 'docker-compose.yml'],
            'Kubernetes': ['deployment.yaml', 'service.yaml'],
            'Terraform': ['.tf'],
        }
        
        for framework, indicators in framework_indicators.items():
            if any(indicator in file_names for indicator in indicators):
                frameworks.append(framework)
        
        return frameworks
    
    async def         """        try:
            print(f"📝 Importing {analysis['name']} to Knowledge database...")
            
            # Create comprehensive analysis summary
            summary = self.create_repository_summary(analysis)
            
            # Prepare Notion page data
            page_data = {
                "parent": {"database_id": self.knowledge_db_id},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": analysis['name']}}]
                    },
                    "URL": {
                        "url": analysis['html_url']
                    },
                    "Type": {
                        "select": {"name": "Repository"}
                    },
                    "Content Type": {
                        "select": {"name": "GitHub"}
                    },
                    "AI Summary": {
                        "rich_text": [{"text": {"content": summary['ai_summary']}}]
                    },
                    "Hashtags": {
                        "multi_select": [{"name": tag} for tag in summary['hashtags']]
                    },
                    "Content Summary": {
                        "rich_text": [{"text": {"content": summary['content_summary']}}]
                    },
                    "Channel": {
                        "rich_text": [{"text": {"content": f"GitHub/{analysis['full_name'].split('/')[0]}"}}]
                    },
                    "Processing Status": {
                        "select": {"name": "Completed"}
                    },
                    "Status": {
                        "select": {"name": "Ready"}
                    },
                    "Priority": {
                        "select": {"name": "Medium"}
                    },
                    "Complexity Level": {
                        "select": {"name": analysis['complexity']}
                    },
                    "Key Points": {
                        "rich_text": [{"text": {"content": summary['key_points']}}]
                    },
                    "Notes": {
                        "rich_text": [{"text": {"content": summary['notes']}}]
                    },
                    "Action Items": {
                        "rich_text": [{"text": {"content": summary['action_items']}}]
                    },
                    "Assistant Prompt": {
                        "rich_text": [{"text": {"content": summary['assistant_prompt']}}]
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=page_data,
                    timeout=15
                ) as response:
                    if response.status == 200:
                        print(f"✅ Successfully imported: {analysis['name']}")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Import failed: {response.status} - {error_text[:200]}")
                        return False
                        
        except Exception as e:
            print(f"❌ Error importing repository: {e}")
            return False
    
    def create_repository_summary(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Create comprehensive summary for the repository."""
        name = analysis['name']
        description = analysis.get('description', '')
        language = analysis['language']
        project_type = analysis['project_type']
        frameworks = analysis.get('frameworks', [])
        topics = analysis.get('topics', [])
        
        # AI Summary
        ai_summary = f"{project_type} written in {language}. "
        if description:
            ai_summary += f"{description[:100]}{'...' if len(description) > 100 else ''}"
        else:
            ai_summary += f"Repository containing {language} code with {len(analysis.get('contents', []))} files."
        
        # Content Summary
        content_summary = f"GitHub repository: {name}. {project_type}"
        if frameworks:
            content_summary += f" using {', '.join(frameworks[:3])}"
        content_summary += f". Stars: {analysis.get('stars', 0)}, Language: {language}."
        
        # Hashtags
        hashtags = [language.lower().replace(' ', '-')] if language != 'Unknown' else []
        hashtags.extend([topic.lower() for topic in topics[:4]])
        hashtags.extend([fw.lower().replace('.', '').replace(' ', '-') for fw in frameworks[:3]])
        hashtags.extend(['github', 'repository', 'code'])
        hashtags = list(set(hashtags))[:8]
        
        # Key Points
        key_points = []
        key_points.append(f"Repository type: {project_type}")
        key_points.append(f"Primary language: {language}")
        if frameworks:
            key_points.append(f"Frameworks/Tools: {', '.join(frameworks[:3])}")
        key_points.append(f"Complexity: {analysis['complexity']}")
        if analysis.get('key_files'):
            key_points.append(f"Key files: {', '.join(analysis['key_files'][:3])}")
        
        key_points_text = '\n'.join([f"• {point}" for point in key_points[:5]])
        
        # Action Items
        action_items = []
        action_items.append(f"Review {name} repository structure and codebase")
        action_items.append(f"Understand the {project_type.lower()} implementation patterns")
        if frameworks:
            action_items.append(f"Study {frameworks[0]} framework usage and best practices")
        else:
            action_items.append(f"Analyze {language} coding techniques and architecture")
        
        action_items_text = '\n'.join([f"• {item}" for item in action_items[:3]])
        
        # Assistant Prompt
        assistant_prompt = f"If instructed, analyze the {name} repository, study its {language} codebase"
        if frameworks:
            assistant_prompt += f", learn the {frameworks[0]} implementation patterns"
        assistant_prompt += f", and understand the {project_type.lower()} architecture and design decisions."
        
        # Notes
        notes = f"GitHub repository: {analysis['full_name']}. "
        notes += f"Last updated: {analysis.get('updated_at', 'Unknown')[:10]}. "
        notes += f"Size: {analysis.get('size', 0)} KB. "
        notes += f"Stars: {analysis.get('stars', 0)}, Forks: {analysis.get('forks', 0)}. "
        if description:
            notes += f"Description: {description}. "
        notes += f"Clone URL: {analysis.get('clone_url', '')}"
        
        return {
            'ai_summary': ai_summary,
            'content_summary': content_summary,
            'hashtags': hashtags,
            'key_points': key_points_text,
            'action_items': action_items_text,
            'assistant_prompt': assistant_prompt,
            'notes': notes
        }

async def main():
    """Main function to process GitHub repositories."""
    print("🚀 GITHUB REPOSITORY PROCESSOR")
    print("=" * 50)
    
    # Configuration
# NOTION_REMOVED:     knowledge_db_id = os.getenv('NOTION_KNOWLEDGE_DATABASE_ID', '20bec31c-9de2-814e-80db-d13d0c27d869')
    
        return
    
    # Get GitHub username
    print("Enter GitHub username or organization name:")
    username = input("Username: ").strip()
    
    if not username:
        print("❌ No username provided")
        return
    
    # Initialize processor
    
    # Fetch repositories
    repos = await processor.get_user_repositories(username)
    
    if not repos:
        print("❌ No repositories found or error fetching repositories")
        return
    
    # Display repositories
    processor.display_repositories(repos)
    
    # Get user selection
    selected_repos = processor.get_user_selection(repos)
    
    if not selected_repos:
        print("❌ No repositories selected")
        return
    
    # Process selected repositories
    print(f"\n🔄 Processing {len(selected_repos)} selected repositories...")
    
    imported_count = 0
    for repo in selected_repos:
        try:
            # Analyze repository
            analysis = await processor.analyze_repository(repo)
            
            if analysis:
                #                 success = await processor.                if success:
                    imported_count += 1
                
                # Rate limiting
                await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Error processing {repo['name']}: {e}")
    
    print(f"\n✅ Import completed: {imported_count}/{len(selected_repos)} repositories imported successfully")

if __name__ == "__main__":
    asyncio.run(main())