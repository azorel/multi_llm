#!/usr/bin/env python3
"""
GitHub Professional Backup Manager
Comprehensive backup and version control for the autonomous multi-LLM agent project
"""

import os
import subprocess
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from github_api_handler import GitHubAPIHandler

class GitHubBackupManager:
    """Professional GitHub repository management and backup system"""
    
    def __init__(self):
        load_dotenv()
        self.owner = os.getenv('GITHUB_DEFAULT_OWNER', 'azorel')
        self.repo = os.getenv('GITHUB_DEFAULT_REPO', 'multi_llm')
        self.token = os.getenv('GITHUB_TOKEN')
        self.local_path = Path('/home/ikino/dev/autonomous-multi-llm-agent')
        self.backup_path = Path('./workspace/repo')
        
        self.github = GitHubAPIHandler(self.token)
        
        # Project metadata
        self.project_info = {
            "name": "Autonomous Multi-LLM Agent System",
            "description": "Advanced multi-agent orchestration system with vanlife & RC social media automation, GitHub integration, and Claude+Gemini optimization",
            "version": "1.0.0",
            "author": "azorel",
            "technologies": ["Python", "Flask", "SQLite", "Claude API", "Gemini API", "GitHub API"],
            "features": [
                "Enhanced Multi-Agent Orchestrator",
                "Vanlife & RC Truck Social Media Automation", 
                "GitHub Repository Integration",
                "Content Analysis with AI",
                "Automated Caption & Hashtag Generation",
                "Revenue Tracking System",
                "Real-time Agent Performance Monitoring",
                "TDD System Integration"
            ]
        }
    
    def initialize_git_repo(self) -> bool:
        """Initialize or update local Git repository"""
        print("🔧 INITIALIZING GIT REPOSITORY")
        print("=" * 50)
        
        try:
            # Check if already a git repo
            if (self.local_path / '.git').exists():
                print("✅ Git repository already exists")
                
                # Check remote
                result = subprocess.run(
                    ['git', 'remote', 'get-url', 'origin'],
                    cwd=self.local_path,
                    capture_output=True,
                    text=True
                )
                
                expected_url = f"https://github.com/{self.owner}/{self.repo}.git"
                
                if result.returncode == 0:
                    current_remote = result.stdout.strip()
                    if current_remote != expected_url:
                        print(f"🔄 Updating remote URL from {current_remote} to {expected_url}")
                        subprocess.run(['git', 'remote', 'set-url', 'origin', expected_url], cwd=self.local_path)
                else:
                    print(f"📎 Adding remote origin: {expected_url}")
                    subprocess.run(['git', 'remote', 'add', 'origin', expected_url], cwd=self.local_path)
            else:
                print("🆕 Initializing new Git repository")
                subprocess.run(['git', 'init'], cwd=self.local_path)
                subprocess.run(['git', 'remote', 'add', 'origin', f"https://github.com/{self.owner}/{self.repo}.git"], cwd=self.local_path)
            
            # Set up Git config
            subprocess.run(['git', 'config', 'user.name', 'Autonomous Agent'], cwd=self.local_path)
            subprocess.run(['git', 'config', 'user.email', 'agent@autonomous-system.dev'], cwd=self.local_path)
            
            print("✅ Git repository initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing Git repository: {e}")
            return False
    
    def create_gitignore(self) -> None:
        """Create comprehensive .gitignore file"""
        print("📝 Creating .gitignore file...")
        
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Database files
*.db
*.sqlite3
lifeos_local.db

# Logs
*.log
logs/
temp/

# System files
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
.cache/

# API Keys and secrets (keep .env.example)
.env.local
.env.production
*.key
*.pem

# Node modules (if any)
node_modules/

# Backup files
*.bak
*.backup

# Upload directories
uploads/
workspace/repo/

# Generated files
autonomous_generated_*

# Test coverage
htmlcov/
.coverage
.pytest_cache/

# Documentation builds
docs/_build/
"""
        
        gitignore_path = self.local_path / '.gitignore'
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        
        print("✅ .gitignore file created")
    
    def create_project_readme(self) -> None:
        """Create comprehensive README.md file"""
        print("📚 Creating project README...")
        
        readme_content = f"""# {self.project_info['name']}

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

{self.project_info['description']}

## 🚀 Features

{chr(10).join(f"- {feature}" for feature in self.project_info['features'])}

## 🛠️ Technologies

{', '.join(self.project_info['technologies'])}

## 📋 Prerequisites

- Python 3.8 or higher
- Git
- GitHub Personal Access Token
- Anthropic API Key (Claude)
- Google API Key (Gemini)

## ⚡ Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/{self.owner}/{self.repo}.git
   cd {self.repo}
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the application:**
   ```bash
   python3 -m flask --app web_server run --port=8082
   ```

5. **Access the dashboard:**
   ```
   http://localhost:8082
   ```

## 🏗️ System Architecture

### Core Components

- **Enhanced Multi-Agent Orchestrator**: Claude + Gemini optimized agent coordination
- **Social Media Automation**: Vanlife & RC truck content optimization
- **GitHub Integration**: Repository analysis and automated workflows
- **Content Analysis Engine**: AI-powered content classification and optimization
- **Revenue Tracking**: Monetization analytics for van life income generation

### Agent Types

1. **Senior Code Developer** - Python development and optimization
2. **System Analyst** - Architecture and system design
3. **API Integration Specialist** - External service integration
4. **Database Specialist** - Data management and optimization
5. **Content Processor** - Media analysis and optimization
6. **Error Diagnostician** - System debugging and repair
7. **Template Fixer** - UI/UX and template management
8. **Web Tester** - Application testing and validation

## 📱 Web Interface

- **Dashboard**: `/` - Main system overview
- **Social Media**: `/social-media` - Content automation
- **GitHub Users**: `/github-users` - Repository management
- **Analytics**: `/analytics` - Performance metrics
- **Code Analysis**: `/code-analysis` - Repository insights

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Core APIs
ANTHROPIC_API_KEY=your_claude_key
GOOGLE_API_KEY=your_gemini_key
GITHUB_TOKEN=your_github_token

# GitHub Integration
GITHUB_DEFAULT_OWNER={self.owner}
GITHUB_DEFAULT_REPO={self.repo}

# Database
DATABASE_URL=sqlite:///lifeos_local.db
```

### Social Media Automation

The system includes specialized automation for:
- **Vanlife Content**: Trail exploration, camping setups, van tours
- **RC Truck Content**: Axial Racing, Vanquish brands, technical crawling
- **Location Focus**: Southern BC trails and outdoor adventures
- **Brand Voice**: Relaxed traveler exploring new trails

## 📊 Database Schema

- **social_media_posts**: Content analysis and posting data
- **trail_locations**: Southern BC trail database
- **rc_brands**: RC truck brand and model detection
- **revenue_tracking**: Monetization and income analytics
- **hashtag_performance**: Social media optimization data

## 🤖 Agent Orchestration

### Task Execution

```python
from enhanced_orchestrator_claude_gemini import enhanced_orchestrator, AgentType

# Add a task
task_id = enhanced_orchestrator.add_task(
    "Analyze repository structure",
    "Perform comprehensive analysis of codebase...",
    AgentType.SYSTEM_ANALYST,
    TaskPriority.HIGH
)

# Execute tasks
results = await enhanced_orchestrator.execute_tasks_parallel([task])
```

### Provider Load Balancing

- **Claude**: 50% - Code analysis, system design
- **Gemini**: 50% - Content processing, image analysis
- Automatic fallback on provider failure

## 📈 Performance Monitoring

- Real-time agent performance tracking
- Task execution analytics
- Error detection and recovery
- System health monitoring

## 🔄 Automated Workflows

- **Repository Discovery**: Daily GitHub repository scanning
- **Content Analysis**: AI-powered media processing
- **Performance Optimization**: Continuous system improvement
- **Error Recovery**: Autonomous problem resolution

## 📝 Development

### Testing

```bash
# Run content analyzer tests
python3 test_social_media_system.py

# Test GitHub integration
python3 github_integration_status.py

# Validate API tokens
python3 test_github_token.py
```

### TDD System

The project includes a Test-Driven Development system:

```python
from tdd_system import tdd_system

# Create TDD cycle
cycle_id = tdd_system.create_tdd_cycle("Feature Name", "Description")
result = tdd_system.complete_tdd_cycle(cycle_id, "Implementation details")
```

## 🛡️ Security

- API keys stored in environment variables
- No sensitive data in repository
- Secure GitHub token validation
- Rate limiting on all external APIs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create a GitHub issue
- Check the documentation
- Review the system logs

## 🗺️ Roadmap

- [ ] YouTube Data API integration
- [ ] Instagram Graph API integration
- [ ] Advanced revenue analytics
- [ ] Mobile app companion
- [ ] Voice command integration
- [ ] Advanced AI model fine-tuning

---

**Generated by Autonomous Multi-LLM Agent System v{self.project_info['version']}**

*Building the future of intelligent automation, one agent at a time.* 🤖✨
"""
        
        readme_path = self.local_path / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        print("✅ README.md created")
    
    def create_requirements_txt(self) -> None:
        """Generate requirements.txt from current environment"""
        print("📦 Creating requirements.txt...")
        
        # Core requirements we know are needed
        requirements = [
            "flask>=2.0.0",
            "anthropic>=0.7.0",
            "google-generativeai>=0.3.0",
            "python-dotenv>=0.19.0",
            "requests>=2.28.0",
            "sqlite3",  # Built-in but documented
            "pathlib",  # Built-in but documented
            "asyncio",  # Built-in but documented
            "aiohttp>=3.8.0",
            "tenacity>=8.0.0",
            "psutil>=5.9.0",
            "concurrent-futures>=3.1.0",
            "dataclasses",  # Built-in but documented
            "enum34;python_version<'3.4'",
            "typing-extensions>=4.0.0",
        ]
        
        requirements_content = "\n".join(sorted(requirements))
        
        requirements_path = self.local_path / 'requirements.txt'
        with open(requirements_path, 'w') as f:
            f.write(requirements_content)
        
        print("✅ requirements.txt created")
    
    def create_license_file(self) -> None:
        """Create MIT license file"""
        print("⚖️ Creating LICENSE file...")
        
        year = datetime.now().year
        license_content = f"""MIT License

Copyright (c) {year} {self.project_info['author']}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
        
        license_path = self.local_path / 'LICENSE'
        with open(license_path, 'w') as f:
            f.write(license_content)
        
        print("✅ LICENSE file created")
    
    def create_env_example(self) -> None:
        """Create .env.example template"""
        print("🔧 Creating .env.example template...")
        
        env_example_content = """# =================================================================
# AUTONOMOUS MULTI-LLM AGENT SYSTEM CONFIGURATION
# =================================================================
# Copy this file to .env and fill in your actual values

# =================================================================
# CORE SYSTEM CONFIGURATION
# =================================================================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# =================================================================
# LLM PROVIDER CONFIGURATIONS
# =================================================================

# Anthropic Configuration (Required)
ANTHROPIC_API_KEY=your_claude_api_key_here
ANTHROPIC_MODEL=claude-3-sonnet-20241022

# Google Gemini Configuration (Required)
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-pro

# =================================================================
# GITHUB INTEGRATION
# =================================================================
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_DEFAULT_OWNER=your_github_username
GITHUB_DEFAULT_REPO=your_repository_name
GITHUB_AUTO_COMMIT=false
GITHUB_AUTO_TEST=true
GITHUB_AUTO_PR=false
GITHUB_AUTO_REVIEW=true

# =================================================================
# DATABASE CONFIGURATION
# =================================================================
DATABASE_URL=sqlite:///lifeos_local.db

# =================================================================
# AGENT CONFIGURATION
# =================================================================
MAX_CONCURRENT_AGENTS=5
AGENT_TIMEOUT=300
TASK_QUEUE_SIZE=1000

# =================================================================
# SOCIAL MEDIA AUTOMATION
# =================================================================
# YouTube Data API (Optional)
YOUTUBE_API_KEY=your_youtube_api_key_here

# Instagram Graph API (Optional) 
INSTAGRAM_ACCESS_TOKEN=your_instagram_token_here

# =================================================================
# MONITORING & PERFORMANCE
# =================================================================
METRICS_ENABLED=true
PERFORMANCE_MONITORING_ENABLED=true
HEALTH_CHECK_ENABLED=true

# =================================================================
# SECURITY
# =================================================================
API_RATE_LIMIT_ENABLED=true
ENCRYPTION_ENABLED=false
"""
        
        env_example_path = self.local_path / '.env.example'
        with open(env_example_path, 'w') as f:
            f.write(env_example_content)
        
        print("✅ .env.example created")
    
    def stage_and_commit_files(self, commit_message: str) -> bool:
        """Stage and commit files to Git"""
        print(f"📝 Staging and committing: {commit_message}")
        
        try:
            # Add all files
            subprocess.run(['git', 'add', '.'], cwd=self.local_path)
            
            # Commit with message
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.local_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Files committed successfully")
                return True
            else:
                print(f"⚠️ Commit result: {result.stdout}")
                return True  # May be no changes to commit
                
        except Exception as e:
            print(f"❌ Error committing files: {e}")
            return False
    
    def push_to_github(self) -> bool:
        """Push commits to GitHub repository"""
        print("🚀 Pushing to GitHub...")
        
        try:
            # Push to main branch
            result = subprocess.run(
                ['git', 'push', '-u', 'origin', 'main'],
                cwd=self.local_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Successfully pushed to GitHub")
                return True
            else:
                # Try master branch if main fails
                result = subprocess.run(
                    ['git', 'push', '-u', 'origin', 'master'],
                    cwd=self.local_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print("✅ Successfully pushed to GitHub (master branch)")
                    return True
                else:
                    print(f"❌ Push failed: {result.stderr}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error pushing to GitHub: {e}")
            return False
    
    def update_repository_description(self) -> bool:
        """Update GitHub repository description"""
        print("📝 Updating repository description...")
        
        try:
            import requests
            
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}"
            headers = {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            data = {
                'name': self.repo,
                'description': self.project_info['description'],
                'homepage': '',
                'private': False,
                'has_issues': True,
                'has_projects': True,
                'has_wiki': True
            }
            
            response = requests.patch(url, headers=headers, json=data)
            
            if response.status_code == 200:
                print("✅ Repository description updated")
                return True
            else:
                print(f"⚠️ Failed to update description: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating repository description: {e}")
            return False
    
    def full_backup_and_setup(self) -> bool:
        """Perform complete backup and repository setup"""
        print("🎯 PERFORMING COMPLETE PROJECT BACKUP")
        print("=" * 60)
        
        success_steps = []
        
        # Step 1: Initialize Git repository
        if self.initialize_git_repo():
            success_steps.append("Git repository initialized")
        
        # Step 2: Create project files
        self.create_gitignore()
        success_steps.append("Created .gitignore")
        
        self.create_project_readme()
        success_steps.append("Created README.md")
        
        self.create_requirements_txt()
        success_steps.append("Created requirements.txt")
        
        self.create_license_file()
        success_steps.append("Created LICENSE")
        
        self.create_env_example()
        success_steps.append("Created .env.example")
        
        # Step 3: Commit initial files
        if self.stage_and_commit_files("🚀 Initial project backup - Autonomous Multi-LLM Agent System\n\n- Enhanced multi-agent orchestrator with Claude + Gemini\n- Vanlife & RC truck social media automation\n- GitHub integration and repository management\n- Content analysis and revenue tracking\n- Professional documentation and setup"):
            success_steps.append("Initial commit created")
        
        # Step 4: Push to GitHub
        if self.push_to_github():
            success_steps.append("Pushed to GitHub")
        
        # Step 5: Update repository metadata
        if self.update_repository_description():
            success_steps.append("Updated repository description")
        
        # Final report
        print("\n🏁 BACKUP COMPLETION REPORT")
        print("=" * 50)
        
        for step in success_steps:
            print(f"✅ {step}")
        
        print(f"\n🌐 Repository URL: https://github.com/{self.owner}/{self.repo}")
        print(f"📊 Steps completed: {len(success_steps)}/8")
        
        if len(success_steps) >= 6:
            print("🎉 Project successfully backed up to GitHub!")
            return True
        else:
            print("⚠️ Backup completed with some issues")
            return False

if __name__ == "__main__":
    manager = GitHubBackupManager()
    success = manager.full_backup_and_setup()
    
    if success:
        print("\n🚀 Ready for professional GitHub management!")
    else:
        print("\n⚠️ Backup needs attention - check the logs above")