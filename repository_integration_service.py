#!/usr/bin/env python3
"""
Repository Integration Service
Handles cloning, analysis, and integration of GitHub repositories
"""

import os
import shutil
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import git
from database import NotionLikeDatabase

logger = logging.getLogger(__name__)

class RepositoryIntegrationService:
    """Service for integrating repositories into the main system"""
    
    def __init__(self):
        self.db = NotionLikeDatabase()
        self.integration_dir = Path("integrated_repositories")
        self.integration_dir.mkdir(exist_ok=True)
        self.analysis_cache = {}
        
    def integrate_repository(self, repository_name: str) -> Dict[str, Any]:
        """
        Main integration method that:
        1. Clones the repository
        2. Analyzes the code structure
        3. Extracts documentation
        4. Identifies key components
        5. Updates the system knowledge base
        """
        try:
            logger.info(f"🔄 Starting integration of {repository_name}")
            
            # Get repository details from knowledge hub
            repo_info = self._get_repository_info(repository_name)
            if not repo_info:
                # If not found by exact match, try to find by partial match or add it
                if repository_name.startswith('https://github.com/'):
                    # Extract repo name from URL
                    repo_parts = repository_name.replace('https://github.com/', '').split('/')
                    if len(repo_parts) >= 2:
                        owner, repo = repo_parts[0], repo_parts[1]
                        # Try to find by repo name
                        knowledge = self.db.get_table_data('knowledge_hub')
                        for item in knowledge:
                            if repo in item.get('title', '') and owner in item.get('github_owner', ''):
                                repo_info = item
                                break
                
                if not repo_info:
                    return {"success": False, "error": f"Repository {repository_name} not found in knowledge hub"}
            
            # Clone the repository
            clone_result = self._clone_repository(repo_info)
            if not clone_result['success']:
                return clone_result
            
            repo_path = clone_result['repo_path']
            
            # Analyze the repository
            analysis_result = self._analyze_repository(repo_path, repo_info)
            if not analysis_result['success']:
                return analysis_result
            
            # Extract documentation
            docs_result = self._extract_documentation(repo_path)
            
            # Identify key components
            components_result = self._identify_components(repo_path)
            
            # Update knowledge base
            integration_result = self._update_knowledge_base(
                repo_info, analysis_result, docs_result, components_result
            )
            
            # Create integration record
            integration_id = self._create_integration_record(
                repo_info, repo_path, analysis_result, docs_result, components_result
            )
            
            logger.info(f"✅ Successfully integrated {repository_name}")
            
            return {
                "success": True,
                "message": f"Repository {repository_name} successfully integrated",
                "details": {
                    "repository": repository_name,
                    "status": "integrated",
                    "integration_id": integration_id,
                    "repo_path": str(repo_path),
                    "components_found": len(components_result.get('components', [])),
                    "documentation_files": len(docs_result.get('docs', [])),
                    "analysis_complete": analysis_result['success'],
                    "languages_detected": analysis_result.get('languages', []),
                    "file_count": analysis_result.get('file_count', 0),
                    "monitoring_enabled": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error during repository integration: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_repository_info(self, repository_name: str) -> Optional[Dict[str, Any]]:
        """Get repository information from knowledge hub"""
        try:
            # Search for repository in knowledge hub
            knowledge_items = self.db.get_table_data('knowledge_hub')
            
            for item in knowledge_items:
                if (item.get('category', '').lower().find('repository') != -1 and 
                    repository_name.lower() in item.get('title', '').lower()):
                    return {
                        'id': item.get('id'),
                        'name': repository_name,
                        'title': item.get('title', ''),
                        'source': item.get('source', ''),
                        'description': item.get('content', ''),
                        'github_owner': item.get('github_owner', ''),
                        'github_repo': item.get('github_repo', ''),
                        'github_language': item.get('github_language', ''),
                        'github_stars': item.get('github_stars', 0),
                        'github_forks': item.get('github_forks', 0)
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting repository info: {e}")
            return None
    
    def _clone_repository(self, repo_info: Dict[str, Any]) -> Dict[str, Any]:
        """Clone the repository to local storage"""
        try:
            repo_url = repo_info.get('source', '')
            if not repo_url:
                return {"success": False, "error": "No repository URL found"}
            
            # Create unique directory name
            repo_name = repo_info.get('name', 'unknown')
            repo_dir = self.integration_dir / f"{repo_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"🔄 Cloning {repo_url} to {repo_dir}")
            
            # Clone the repository
            try:
                repo = git.Repo.clone_from(repo_url, repo_dir, depth=1)  # Shallow clone for speed
                logger.info(f"✅ Successfully cloned {repo_url}")
                
                return {
                    "success": True,
                    "repo_path": repo_dir,
                    "clone_url": repo_url,
                    "branch": repo.active_branch.name if repo.active_branch else "main"
                }
                
            except git.GitCommandError as e:
                logger.error(f"Git clone error: {e}")
                return {"success": False, "error": f"Failed to clone repository: {str(e)}"}
                
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_repository(self, repo_path: Path, repo_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze repository structure and content"""
        try:
            logger.info(f"🔍 Analyzing repository at {repo_path}")
            
            analysis = {
                "success": True,
                "repo_path": str(repo_path),
                "languages": [],
                "file_count": 0,
                "directory_count": 0,
                "file_types": {},
                "size_mb": 0,
                "structure": {},
                "entry_points": [],
                "config_files": [],
                "dependencies": []
            }
            
            # Get repository size
            total_size = sum(f.stat().st_size for f in repo_path.rglob('*') if f.is_file())
            analysis["size_mb"] = round(total_size / (1024 * 1024), 2)
            
            # Analyze file structure
            for item in repo_path.rglob('*'):
                if item.is_file():
                    analysis["file_count"] += 1
                    
                    # Track file types
                    suffix = item.suffix.lower()
                    if suffix:
                        analysis["file_types"][suffix] = analysis["file_types"].get(suffix, 0) + 1
                        
                        # Detect languages
                        if suffix in ['.py', '.pyx', '.pyi']:
                            if 'Python' not in analysis["languages"]:
                                analysis["languages"].append('Python')
                        elif suffix in ['.js', '.jsx', '.ts', '.tsx']:
                            if 'JavaScript/TypeScript' not in analysis["languages"]:
                                analysis["languages"].append('JavaScript/TypeScript')
                        elif suffix in ['.html', '.htm']:
                            if 'HTML' not in analysis["languages"]:
                                analysis["languages"].append('HTML')
                        elif suffix in ['.css']:
                            if 'CSS' not in analysis["languages"]:
                                analysis["languages"].append('CSS')
                        elif suffix in ['.java']:
                            if 'Java' not in analysis["languages"]:
                                analysis["languages"].append('Java')
                        elif suffix in ['.cpp', '.c', '.h']:
                            if 'C/C++' not in analysis["languages"]:
                                analysis["languages"].append('C/C++')
                        elif suffix in ['.go']:
                            if 'Go' not in analysis["languages"]:
                                analysis["languages"].append('Go')
                        elif suffix in ['.rs']:
                            if 'Rust' not in analysis["languages"]:
                                analysis["languages"].append('Rust')
                        elif suffix in ['.md', '.markdown']:
                            if 'Markdown' not in analysis["languages"]:
                                analysis["languages"].append('Markdown')
                        elif suffix in ['.json']:
                            if 'JSON' not in analysis["languages"]:
                                analysis["languages"].append('JSON')
                        elif suffix in ['.yml', '.yaml']:
                            if 'YAML' not in analysis["languages"]:
                                analysis["languages"].append('YAML')
                
                elif item.is_dir():
                    analysis["directory_count"] += 1
            
            # Find entry points
            entry_point_files = ['main.py', 'app.py', 'index.js', 'main.js', 'server.js', 'main.go', 'main.rs']
            for entry_file in entry_point_files:
                entry_path = repo_path / entry_file
                if entry_path.exists():
                    analysis["entry_points"].append(str(entry_path.relative_to(repo_path)))
            
            # Find configuration files
            config_files = ['requirements.txt', 'package.json', 'Cargo.toml', 'go.mod', 'Dockerfile', '.env.example', 'pyproject.toml', 'setup.py']
            for config_file in config_files:
                config_path = repo_path / config_file
                if config_path.exists():
                    analysis["config_files"].append(str(config_path.relative_to(repo_path)))
            
            # Extract dependencies
            analysis["dependencies"] = self._extract_dependencies(repo_path)
            
            # Create directory structure map
            analysis["structure"] = self._create_structure_map(repo_path)
            
            logger.info(f"✅ Analysis complete: {analysis['file_count']} files, {len(analysis['languages'])} languages")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_documentation(self, repo_path: Path) -> Dict[str, Any]:
        """Extract documentation files and content"""
        try:
            docs = {
                "readme": "",
                "docs": [],
                "comments": [],
                "docstrings": []
            }
            
            # Find README files
            readme_files = list(repo_path.glob("README*")) + list(repo_path.glob("readme*"))
            if readme_files:
                try:
                    with open(readme_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                        docs["readme"] = f.read()[:5000]  # Limit to 5000 chars
                except Exception as e:
                    logger.debug(f"Could not read README: {e}")
            
            # Find documentation directories and files
            doc_patterns = ['docs/', 'doc/', 'documentation/', '*.md', '*.rst', '*.txt']
            for pattern in doc_patterns:
                for doc_file in repo_path.rglob(pattern):
                    if doc_file.is_file() and doc_file.suffix.lower() in ['.md', '.rst', '.txt']:
                        try:
                            with open(doc_file, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()[:2000]  # Limit content
                                docs["docs"].append({
                                    "file": str(doc_file.relative_to(repo_path)),
                                    "content": content
                                })
                        except Exception as e:
                            logger.debug(f"Could not read doc file {doc_file}: {e}")
            
            return docs
            
        except Exception as e:
            logger.error(f"Error extracting documentation: {e}")
            return {"docs": [], "readme": ""}
    
    def _identify_components(self, repo_path: Path) -> Dict[str, Any]:
        """Identify key components and patterns in the repository"""
        try:
            components = {
                "frameworks": [],
                "patterns": [],
                "modules": [],
                "classes": [],
                "functions": []
            }
            
            # Identify frameworks based on files and dependencies
            if (repo_path / "package.json").exists():
                components["frameworks"].append("Node.js/npm")
            if (repo_path / "requirements.txt").exists() or (repo_path / "pyproject.toml").exists():
                components["frameworks"].append("Python")
            if (repo_path / "Cargo.toml").exists():
                components["frameworks"].append("Rust")
            if (repo_path / "go.mod").exists():
                components["frameworks"].append("Go")
            if (repo_path / "Dockerfile").exists():
                components["frameworks"].append("Docker")
            
            # Look for common patterns
            if any(repo_path.glob("**/models.py")):
                components["patterns"].append("MVC Pattern")
            if any(repo_path.glob("**/views.py")) or any(repo_path.glob("**/routes.py")):
                components["patterns"].append("Web Framework")
            if any(repo_path.glob("**/test_*.py")) or any(repo_path.glob("**/*_test.py")):
                components["patterns"].append("Unit Testing")
            if any(repo_path.glob("**/migrations/")):
                components["patterns"].append("Database Migrations")
            
            # Extract module/class information (simplified)
            for py_file in repo_path.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Simple regex to find classes and functions
                        import re
                        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
                        functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
                        
                        if classes:
                            components["classes"].extend(classes[:5])  # Limit to first 5
                        if functions:
                            components["functions"].extend(functions[:5])  # Limit to first 5
                            
                except Exception as e:
                    logger.debug(f"Could not analyze Python file {py_file}: {e}")
            
            return components
            
        except Exception as e:
            logger.error(f"Error identifying components: {e}")
            return {"frameworks": [], "patterns": [], "modules": [], "classes": [], "functions": []}
    
    def _extract_dependencies(self, repo_path: Path) -> List[str]:
        """Extract project dependencies"""
        dependencies = []
        
        try:
            # Python dependencies
            req_file = repo_path / "requirements.txt"
            if req_file.exists():
                with open(req_file, 'r', encoding='utf-8', errors='ignore') as f:
                    deps = [line.strip().split('==')[0].split('>=')[0].split('<=')[0] 
                           for line in f.readlines() if line.strip() and not line.startswith('#')]
                    dependencies.extend(deps[:10])  # Limit to 10
            
            # Node.js dependencies
            package_file = repo_path / "package.json"
            if package_file.exists():
                try:
                    with open(package_file, 'r', encoding='utf-8') as f:
                        package_data = json.loads(f.read())
                        deps = list(package_data.get('dependencies', {}).keys())
                        dependencies.extend(deps[:10])  # Limit to 10
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            logger.debug(f"Error extracting dependencies: {e}")
        
        return dependencies
    
    def _create_structure_map(self, repo_path: Path, max_depth: int = 3) -> Dict[str, Any]:
        """Create a simplified directory structure map"""
        try:
            structure = {}
            
            def build_tree(path: Path, current_depth: int = 0):
                if current_depth > max_depth:
                    return "..."
                
                items = {}
                try:
                    for item in path.iterdir():
                        if item.name.startswith('.'):
                            continue  # Skip hidden files/dirs
                        
                        if item.is_dir():
                            items[item.name + "/"] = build_tree(item, current_depth + 1)
                        elif current_depth < 2:  # Only show files at shallow depths
                            items[item.name] = "file"
                except PermissionError:
                    pass
                
                return items
            
            structure = build_tree(repo_path)
            return structure
            
        except Exception as e:
            logger.debug(f"Error creating structure map: {e}")
            return {}
    
    def _update_knowledge_base(self, repo_info: Dict[str, Any], analysis: Dict[str, Any], 
                             docs: Dict[str, Any], components: Dict[str, Any]) -> Dict[str, Any]:
        """Update the knowledge base with integration results"""
        try:
            # Update the original repository record
            repo_id = repo_info.get('id')
            if repo_id:
                update_data = {
                    'integration_status': 'integrated',
                    'integration_date': datetime.now().isoformat(),
                    'analysis_complete': True,
                    'file_count': analysis.get('file_count', 0),
                    'languages': ','.join(analysis.get('languages', [])),
                    'frameworks': ','.join(components.get('frameworks', [])),
                    'patterns': ','.join(components.get('patterns', [])),
                    'last_analyzed': datetime.now().isoformat()
                }
                
                self.db.update_record('knowledge_hub', repo_id, update_data)
                logger.info(f"✅ Updated knowledge hub record for repository")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error updating knowledge base: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_integration_record(self, repo_info: Dict[str, Any], repo_path: Path,
                                 analysis: Dict[str, Any], docs: Dict[str, Any], 
                                 components: Dict[str, Any]) -> int:
        """Create a detailed integration record"""
        try:
            integration_data = {
                'repository_name': repo_info.get('name', ''),
                'repository_url': repo_info.get('source', ''),
                'local_path': str(repo_path),
                'integration_date': datetime.now().isoformat(),
                'status': 'active',
                'file_count': analysis.get('file_count', 0),
                'directory_count': analysis.get('directory_count', 0),
                'size_mb': analysis.get('size_mb', 0),
                'languages': ','.join(analysis.get('languages', [])),
                'frameworks': ','.join(components.get('frameworks', [])),
                'patterns': ','.join(components.get('patterns', [])),
                'entry_points': ','.join(analysis.get('entry_points', [])),
                'config_files': ','.join(analysis.get('config_files', [])),
                'dependencies': ','.join(analysis.get('dependencies', [])),
                'has_readme': bool(docs.get('readme', '')),
                'doc_files_count': len(docs.get('docs', [])),
                'analysis_data': json.dumps({
                    'structure': analysis.get('structure', {}),
                    'file_types': analysis.get('file_types', {}),
                    'components': components
                })
            }
            
            # Create integration table if it doesn't exist
            self._ensure_integration_table_exists()
            
            # Add the integration record
            integration_id = self.db.add_record('integrated_repositories', integration_data)
            logger.info(f"✅ Created integration record with ID {integration_id}")
            
            return integration_id
            
        except Exception as e:
            logger.error(f"Error creating integration record: {e}")
            return -1
    
    def _ensure_integration_table_exists(self):
        """Ensure the integrated_repositories table exists"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS integrated_repositories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_name TEXT NOT NULL,
                    repository_url TEXT,
                    local_path TEXT,
                    integration_date DATETIME,
                    status TEXT DEFAULT 'active',
                    file_count INTEGER DEFAULT 0,
                    directory_count INTEGER DEFAULT 0,
                    size_mb REAL DEFAULT 0,
                    languages TEXT,
                    frameworks TEXT,
                    patterns TEXT,
                    entry_points TEXT,
                    config_files TEXT,
                    dependencies TEXT,
                    has_readme BOOLEAN DEFAULT FALSE,
                    doc_files_count INTEGER DEFAULT 0,
                    analysis_data TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Ensured integrated_repositories table exists")
            
        except Exception as e:
            logger.error(f"Error creating integrated_repositories table: {e}")

    def get_integrated_repositories(self) -> List[Dict[str, Any]]:
        """Get list of all integrated repositories"""
        try:
            self._ensure_integration_table_exists()
            return self.db.get_table_data('integrated_repositories')
        except Exception as e:
            logger.error(f"Error getting integrated repositories: {e}")
            return []
    
    def remove_integration(self, repository_name: str) -> Dict[str, Any]:
        """Remove repository integration"""
        try:
            # Find integration record
            integrations = self.get_integrated_repositories()
            target_integration = None
            
            for integration in integrations:
                if integration.get('repository_name') == repository_name:
                    target_integration = integration
                    break
            
            if not target_integration:
                return {"success": False, "error": "Integration not found"}
            
            # Remove local repository
            local_path = Path(target_integration.get('local_path', ''))
            if local_path.exists():
                shutil.rmtree(local_path)
                logger.info(f"🗑️ Removed local repository at {local_path}")
            
            # Remove integration record
            self.db.delete_record('integrated_repositories', target_integration['id'])
            
            # Update knowledge hub record
            knowledge_items = self.db.get_table_data('knowledge_hub')
            for item in knowledge_items:
                if (item.get('category', '').lower().find('repository') != -1 and 
                    repository_name.lower() in item.get('title', '').lower()):
                    self.db.update_record('knowledge_hub', item['id'], {
                        'integration_status': 'removed',
                        'integration_date': None,
                        'analysis_complete': False
                    })
                    break
            
            logger.info(f"✅ Successfully removed integration for {repository_name}")
            return {"success": True, "message": f"Integration for {repository_name} removed"}
            
        except Exception as e:
            logger.error(f"Error removing integration: {e}")
            return {"success": False, "error": str(e)}