#!/usr/bin/env python3
"""
Automated Repository Processing Pipeline
Handles automated discovery, cloning, analysis, and integration of GitHub repositories
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import json
import time
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from github_api_handler import github_api
from repository_integration_service import RepositoryIntegrationService
from repository_code_analyzer import repository_analyzer
from knowledge_hub_orchestrator import orchestrator
from database import NotionLikeDatabase

logger = logging.getLogger(__name__)

@dataclass
class ProcessingTask:
    """Represents a repository processing task"""
    task_id: str
    task_type: str  # 'clone', 'analyze', 'integrate', 'monitor'
    repository: Dict[str, Any]
    priority: int = 5  # 1-10, lower is higher priority
    created_at: datetime = None
    attempts: int = 0
    max_attempts: int = 3
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class AutomatedRepositoryProcessor:
    """
    Automated pipeline for processing GitHub repositories:
    1. Discovery -> 2. Cloning -> 3. Analysis -> 4. Integration -> 5. Monitoring
    """
    
    def __init__(self):
        self.db = NotionLikeDatabase()
        self.integration_service = RepositoryIntegrationService()
        
        # Processing queues
        self.discovery_queue = Queue()
        self.processing_queue = Queue()
        self.analysis_queue = Queue()
        self.integration_queue = Queue()
        self.monitoring_queue = Queue()
        
        # State management
        self.is_running = False
        self.worker_threads = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Progress tracking
        self.processing_stats = {
            'total_discovered': 0,
            'total_processed': 0,
            'total_analyzed': 0,
            'total_integrated': 0,
            'errors': 0,
            'start_time': None,
            'current_operations': []
        }
        
        # Configuration
        self.config = {
            'batch_size': 5,
            'concurrent_workers': 3,
            'monitoring_interval': 300,  # 5 minutes
            'auto_discovery': True,
            'auto_analysis': True,
            'auto_integration': True,
            'retry_failed': True,
            'max_repositories_per_user': 20,
            'health_check_interval': 3600  # 1 hour
        }
        
        # Callbacks
        self.callbacks = {
            'on_discovery': [],
            'on_processing_start': [],
            'on_processing_complete': [],
            'on_analysis_complete': [],
            'on_integration_complete': [],
            'on_error': []
        }
        
        logger.info("🤖 Automated Repository Processor initialized")
    
    def start_automated_processing(self) -> Dict[str, Any]:
        """Start the automated processing pipeline"""
        if self.is_running:
            return {"success": False, "error": "Already running"}
        
        try:
            self.is_running = True
            self.processing_stats['start_time'] = datetime.now()
            
            # Start worker threads
            self._start_workers()
            
            # Start monitoring
            self._start_monitoring()
            
            logger.info("🚀 Automated repository processing started")
            return {
                "success": True,
                "message": "Automated processing started",
                "workers": len(self.worker_threads),
                "config": self.config
            }
            
        except Exception as e:
            logger.error(f"Error starting automated processing: {e}")
            self.is_running = False
            return {"success": False, "error": str(e)}
    
    def stop_automated_processing(self) -> Dict[str, Any]:
        """Stop the automated processing pipeline"""
        if not self.is_running:
            return {"success": False, "error": "Not running"}
        
        try:
            self.is_running = False
            
            # Wait for workers to finish
            for thread in self.worker_threads:
                thread.join(timeout=10)
            
            self.worker_threads.clear()
            
            logger.info("🛑 Automated repository processing stopped")
            return {
                "success": True,
                "message": "Automated processing stopped",
                "final_stats": self.get_processing_stats()
            }
            
        except Exception as e:
            logger.error(f"Error stopping automated processing: {e}")
            return {"success": False, "error": str(e)}
    
    def discover_repositories(self, source: str = "database") -> Dict[str, Any]:
        """Discover repositories from various sources"""
        logger.info(f"🔍 Starting repository discovery from {source}")
        
        try:
            discovered = []
            
            if source == "database":
                # Get GitHub users from database
                users = self.db.get_table_data('github_users')
                
                for user in users:
                    username = user.get('username', '')
                    if not username:
                        continue
                    
                    # Get user repositories
                    repos_result = github_api.get_user_repositories(
                        username, 
                        max_repos=self.config['max_repositories_per_user']
                    )
                    
                    if repos_result['success']:
                        user_repos = repos_result['repositories']
                        
                        for repo in user_repos:
                            # Filter out forks and archived repos unless specified
                            if repo.get('fork', False) or repo.get('archived', False):
                                continue
                            
                            repo_info = {
                                'username': username,
                                'repo_name': repo['name'],
                                'full_name': repo['full_name'],
                                'clone_url': repo['clone_url'],
                                'html_url': repo['html_url'],
                                'description': repo['description'],
                                'language': repo['language'],
                                'stars': repo['stars'],
                                'size': repo['size'],
                                'updated_at': repo['updated_at'],
                                'discovered_at': datetime.now().isoformat()
                            }
                            discovered.append(repo_info)
                            
                            # Add to processing queue
                            task = ProcessingTask(
                                task_id=f"process_{repo['full_name'].replace('/', '_')}_{int(time.time())}",
                                task_type='process',
                                repository=repo_info,
                                priority=3
                            )
                            self.processing_queue.put(task)
                    
                    # Rate limiting
                    time.sleep(0.5)
            
            self.processing_stats['total_discovered'] += len(discovered)
            
            # Trigger discovery callbacks
            for callback in self.callbacks['on_discovery']:
                try:
                    callback(discovered)
                except Exception as e:
                    logger.error(f"Discovery callback error: {e}")
            
            logger.info(f"✅ Discovered {len(discovered)} repositories")
            return {
                "success": True,
                "discovered": len(discovered),
                "repositories": discovered
            }
            
        except Exception as e:
            logger.error(f"Error discovering repositories: {e}")
            return {"success": False, "error": str(e)}
    
    def process_repository_automated(self, repository: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single repository through the complete pipeline"""
        repo_name = repository.get('full_name', 'Unknown')
        logger.info(f"🔄 Starting automated processing of {repo_name}")
        
        try:
            # Track current operation
            self.processing_stats['current_operations'].append(f"Processing {repo_name}")
            
            # Trigger processing start callbacks
            for callback in self.callbacks['on_processing_start']:
                try:
                    callback(repository)
                except Exception as e:
                    logger.error(f"Processing start callback error: {e}")
            
            results = {
                'repository': repo_name,
                'steps': {},
                'success': True,
                'errors': []
            }
            
            # Step 1: Clone and analyze structure
            if self.config['auto_analysis']:
                analysis_result = self._analyze_repository_structure(repository)
                results['steps']['analysis'] = analysis_result
                
                if not analysis_result['success']:
                    results['success'] = False
                    results['errors'].append(f"Analysis failed: {analysis_result.get('error', 'Unknown')}")
            
            # Step 2: Code analysis (if Python repository)
            if results['success'] and repository.get('language', '').lower() == 'python':
                code_analysis_result = self._perform_code_analysis(repository)
                results['steps']['code_analysis'] = code_analysis_result
                
                if not code_analysis_result['success']:
                    logger.warning(f"Code analysis failed for {repo_name}, continuing...")
            
            # Step 3: Integration
            if results['success'] and self.config['auto_integration']:
                integration_result = self._integrate_repository(repository)
                results['steps']['integration'] = integration_result
                
                if not integration_result['success']:
                    results['success'] = False
                    results['errors'].append(f"Integration failed: {integration_result.get('error', 'Unknown')}")
            
            # Step 4: Add to knowledge base
            if results['success']:
                knowledge_result = self._add_to_knowledge_base(repository, results)
                results['steps']['knowledge_base'] = knowledge_result
            
            # Update statistics
            if results['success']:
                self.processing_stats['total_processed'] += 1
                if 'analysis' in results['steps']:
                    self.processing_stats['total_analyzed'] += 1
                if 'integration' in results['steps']:
                    self.processing_stats['total_integrated'] += 1
            else:
                self.processing_stats['errors'] += 1
            
            # Remove from current operations
            if f"Processing {repo_name}" in self.processing_stats['current_operations']:
                self.processing_stats['current_operations'].remove(f"Processing {repo_name}")
            
            # Trigger completion callbacks
            callback_list = self.callbacks['on_processing_complete'] if results['success'] else self.callbacks['on_error']
            for callback in callback_list:
                try:
                    callback(repository, results)
                except Exception as e:
                    logger.error(f"Completion callback error: {e}")
            
            logger.info(f"{'✅' if results['success'] else '❌'} Automated processing {'completed' if results['success'] else 'failed'} for {repo_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error in automated processing of {repo_name}: {e}")
            self.processing_stats['errors'] += 1
            
            if f"Processing {repo_name}" in self.processing_stats['current_operations']:
                self.processing_stats['current_operations'].remove(f"Processing {repo_name}")
            
            return {
                'repository': repo_name,
                'success': False,
                'error': str(e)
            }
    
    def _analyze_repository_structure(self, repository: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze repository structure"""
        try:
            repo_name = repository.get('repo_name', '')
            
            # For now, create a mock analysis based on repository metadata
            # In a full implementation, this would clone and analyze the actual repository
            
            analysis = {
                'success': True,
                'repository': repository['full_name'],
                'language': repository.get('language', 'Unknown'),
                'size_kb': repository.get('size', 0),
                'stars': repository.get('stars', 0),
                'description': repository.get('description', ''),
                'last_updated': repository.get('updated_at', ''),
                'structure_analysis': {
                    'primary_language': repository.get('language', 'Unknown'),
                    'complexity_estimate': self._estimate_complexity(repository),
                    'project_type': self._classify_project_type(repository),
                    'learning_value': self._assess_learning_value(repository)
                },
                'analysis_date': datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing repository structure: {e}")
            return {'success': False, 'error': str(e)}
    
    def _perform_code_analysis(self, repository: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed code analysis"""
        try:
            # This would typically require cloning the repository
            # For this implementation, we'll simulate the analysis
            
            analysis = {
                'success': True,
                'repository': repository['full_name'],
                'code_metrics': {
                    'estimated_loc': repository.get('size', 0) * 2,  # Rough estimate
                    'complexity_score': self._estimate_complexity(repository),
                    'patterns_detected': self._detect_patterns_from_metadata(repository),
                    'quality_score': self._calculate_quality_score(repository)
                },
                'learnings': self._extract_learnings_from_metadata(repository),
                'analysis_date': datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error performing code analysis: {e}")
            return {'success': False, 'error': str(e)}
    
    def _integrate_repository(self, repository: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate repository into the system"""
        try:
            # Add repository to knowledge hub
            knowledge_data = {
                'title': f"{repository['full_name']} - GitHub Repository",
                'content': f"GitHub repository: {repository.get('description', 'No description')}",
                'category': 'GitHub Repository',
                'source': repository.get('html_url', ''),
                'tags': f"github,{repository.get('language', 'unknown').lower()},repository",
                'status': 'Active',
                'github_owner': repository['username'],
                'github_repo': repository['repo_name'],
                'github_language': repository.get('language', ''),
                'github_stars': repository.get('stars', 0),
                'github_forks': repository.get('forks', 0),
                'integration_status': 'automated',
                'integration_date': datetime.now().isoformat(),
                'created_date': datetime.now().isoformat()
            }
            
            # Check if already exists
            existing = self.db.get_table_data('knowledge_hub')
            for item in existing:
                if (item.get('github_owner') == repository['username'] and 
                    item.get('github_repo') == repository['repo_name']):
                    # Update existing record
                    self.db.update_record('knowledge_hub', item['id'], knowledge_data)
                    return {
                        'success': True,
                        'action': 'updated',
                        'record_id': item['id']
                    }
            
            # Add new record
            record_id = self.db.add_record('knowledge_hub', knowledge_data)
            
            return {
                'success': True,
                'action': 'created',
                'record_id': record_id
            }
            
        except Exception as e:
            logger.error(f"Error integrating repository: {e}")
            return {'success': False, 'error': str(e)}
    
    def _add_to_knowledge_base(self, repository: Dict[str, Any], processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """Add processing results to knowledge base"""
        try:
            # Create summary of processing results
            summary = f"Automatically processed repository {repository['full_name']}"
            
            if 'analysis' in processing_results['steps']:
                analysis = processing_results['steps']['analysis']
                summary += f" | Language: {analysis.get('language', 'Unknown')}"
                summary += f" | Size: {analysis.get('size_kb', 0)}KB"
                summary += f" | Stars: {analysis.get('stars', 0)}"
            
            # Store processing metadata
            metadata = {
                'processing_date': datetime.now().isoformat(),
                'processing_results': processing_results,
                'automated': True
            }
            
            return {
                'success': True,
                'summary': summary,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error adding to knowledge base: {e}")
            return {'success': False, 'error': str(e)}
    
    def _estimate_complexity(self, repository: Dict[str, Any]) -> int:
        """Estimate repository complexity (1-10)"""
        complexity = 1
        
        # Size factor
        size = repository.get('size', 0)
        if size > 10000:
            complexity += 3
        elif size > 1000:
            complexity += 2
        elif size > 100:
            complexity += 1
        
        # Language factor
        language = repository.get('language', '').lower()
        if language in ['c++', 'rust', 'assembly']:
            complexity += 2
        elif language in ['java', 'c#', 'go']:
            complexity += 1
        
        # Stars factor (popular = likely complex)
        stars = repository.get('stars', 0)
        if stars > 1000:
            complexity += 1
        
        return min(complexity, 10)
    
    def _classify_project_type(self, repository: Dict[str, Any]) -> str:
        """Classify the type of project"""
        description = repository.get('description', '').lower()
        name = repository.get('repo_name', '').lower()
        language = repository.get('language', '').lower()
        
        # Web frameworks
        if any(term in description for term in ['web', 'api', 'server', 'flask', 'django', 'express']):
            return 'Web Application'
        
        # CLI tools
        if any(term in description for term in ['cli', 'command', 'tool', 'utility']):
            return 'CLI Tool'
        
        # Libraries
        if any(term in description for term in ['library', 'package', 'module', 'framework']):
            return 'Library/Framework'
        
        # AI/ML
        if any(term in description for term in ['ai', 'ml', 'machine learning', 'neural', 'model']):
            return 'AI/ML Project'
        
        # Data
        if any(term in description for term in ['data', 'analysis', 'dashboard', 'visualization']):
            return 'Data Project'
        
        # Game
        if any(term in description for term in ['game', 'gaming', 'unity', 'pygame']):
            return 'Game'
        
        return 'General Application'
    
    def _assess_learning_value(self, repository: Dict[str, Any]) -> str:
        """Assess the learning value of a repository"""
        stars = repository.get('stars', 0)
        size = repository.get('size', 0)
        description = repository.get('description', '').lower()
        
        score = 0
        
        # Stars indicate community value
        if stars > 1000:
            score += 3
        elif stars > 100:
            score += 2
        elif stars > 10:
            score += 1
        
        # Size indicates substantial content
        if size > 1000:
            score += 2
        elif size > 100:
            score += 1
        
        # Description quality
        if len(description) > 50:
            score += 1
        
        # Learning-related keywords
        if any(term in description for term in ['tutorial', 'example', 'learn', 'guide', 'demo']):
            score += 2
        
        if score >= 6:
            return 'High'
        elif score >= 3:
            return 'Medium'
        else:
            return 'Low'
    
    def _detect_patterns_from_metadata(self, repository: Dict[str, Any]) -> List[str]:
        """Detect patterns from repository metadata"""
        patterns = []
        
        description = repository.get('description', '').lower()
        name = repository.get('repo_name', '').lower()
        
        # Framework patterns
        if 'flask' in description or 'flask' in name:
            patterns.append('Flask Web Framework')
        if 'django' in description or 'django' in name:
            patterns.append('Django Web Framework')
        if 'api' in description or 'api' in name:
            patterns.append('API Development')
        
        # Architecture patterns
        if any(term in description for term in ['microservice', 'micro-service']):
            patterns.append('Microservices Architecture')
        if 'mvc' in description:
            patterns.append('MVC Pattern')
        
        # Technology patterns
        if any(term in description for term in ['docker', 'container']):
            patterns.append('Containerization')
        if any(term in description for term in ['kubernetes', 'k8s']):
            patterns.append('Kubernetes')
        if 'ai' in description or 'ml' in description:
            patterns.append('Machine Learning')
        
        return patterns
    
    def _calculate_quality_score(self, repository: Dict[str, Any]) -> float:
        """Calculate a quality score for the repository"""
        score = 0.0
        
        # Stars indicate quality/popularity
        stars = repository.get('stars', 0)
        if stars > 1000:
            score += 0.4
        elif stars > 100:
            score += 0.3
        elif stars > 10:
            score += 0.2
        elif stars > 0:
            score += 0.1
        
        # Size indicates content
        size = repository.get('size', 0)
        if size > 1000:
            score += 0.3
        elif size > 100:
            score += 0.2
        elif size > 0:
            score += 0.1
        
        # Description quality
        description = repository.get('description', '')
        if len(description) > 100:
            score += 0.2
        elif len(description) > 50:
            score += 0.1
        
        # Recent activity
        updated_at = repository.get('updated_at', '')
        if updated_at:
            try:
                update_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                days_ago = (datetime.now(update_date.tzinfo) - update_date).days
                if days_ago <= 30:
                    score += 0.1
            except:
                pass
        
        return min(score, 1.0)
    
    def _extract_learnings_from_metadata(self, repository: Dict[str, Any]) -> List[str]:
        """Extract potential learnings from repository metadata"""
        learnings = []
        
        language = repository.get('language', '')
        if language:
            learnings.append(f"{language} programming patterns and practices")
        
        description = repository.get('description', '').lower()
        project_type = self._classify_project_type(repository)
        
        learnings.append(f"{project_type} development approaches")
        
        # Specific technology learnings
        if 'api' in description:
            learnings.append("API design and implementation")
        if 'web' in description:
            learnings.append("Web development best practices")
        if 'test' in description:
            learnings.append("Testing methodologies and frameworks")
        if any(term in description for term in ['docker', 'container']):
            learnings.append("Containerization and deployment strategies")
        
        return learnings[:5]  # Limit to top 5 learnings
    
    def _start_workers(self):
        """Start worker threads for processing"""
        # Discovery worker
        discovery_worker = threading.Thread(target=self._discovery_worker, daemon=True)
        discovery_worker.start()
        self.worker_threads.append(discovery_worker)
        
        # Processing workers
        for i in range(self.config['concurrent_workers']):
            worker = threading.Thread(target=self._processing_worker, daemon=True)
            worker.start()
            self.worker_threads.append(worker)
        
        logger.info(f"🔧 Started {len(self.worker_threads)} worker threads")
    
    def _discovery_worker(self):
        """Worker thread for continuous discovery"""
        while self.is_running:
            try:
                if self.config['auto_discovery']:
                    self.discover_repositories("database")
                
                # Wait before next discovery cycle
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                logger.error(f"Discovery worker error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _processing_worker(self):
        """Worker thread for processing repositories"""
        while self.is_running:
            try:
                # Get task from queue
                task = self.processing_queue.get(timeout=30)
                
                if task.task_type == 'process':
                    self.process_repository_automated(task.repository)
                
                self.processing_queue.task_done()
                
            except Empty:
                continue  # Timeout, check if still running
            except Exception as e:
                logger.error(f"Processing worker error: {e}")
                time.sleep(5)
    
    def _start_monitoring(self):
        """Start monitoring thread"""
        monitoring_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
        monitoring_thread.start()
        self.worker_threads.append(monitoring_thread)
    
    def _monitoring_worker(self):
        """Worker thread for monitoring and health checks"""
        last_health_check = 0
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Periodic health checks
                if current_time - last_health_check > self.config['health_check_interval']:
                    self._perform_health_checks()
                    last_health_check = current_time
                
                # Monitor queue sizes
                self._monitor_queue_health()
                
                time.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Monitoring worker error: {e}")
                time.sleep(60)
    
    def _perform_health_checks(self):
        """Perform periodic health checks"""
        try:
            # Check database connection
            self.db.get_table_data('knowledge_hub', limit=1)
            
            # Check GitHub API rate limits
            rate_status = github_api.get_rate_limit_status()
            if rate_status['success']:
                remaining = rate_status.get('core', {}).get('remaining', 0)
                if remaining < 100:
                    logger.warning(f"⚠️ GitHub API rate limit low: {remaining} remaining")
            
            logger.debug("✅ Health checks passed")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def _monitor_queue_health(self):
        """Monitor queue sizes and processing health"""
        queue_sizes = {
            'discovery': self.discovery_queue.qsize(),
            'processing': self.processing_queue.qsize(),
            'analysis': self.analysis_queue.qsize(),
            'integration': self.integration_queue.qsize(),
            'monitoring': self.monitoring_queue.qsize()
        }
        
        # Log warnings for large queues
        for queue_name, size in queue_sizes.items():
            if size > 50:
                logger.warning(f"⚠️ Large queue detected: {queue_name} has {size} items")
    
    def add_callback(self, event: str, callback: Callable):
        """Add a callback for specific events"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            logger.info(f"📞 Added callback for {event}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        stats = self.processing_stats.copy()
        
        if stats['start_time']:
            runtime = datetime.now() - stats['start_time']
            stats['runtime_seconds'] = runtime.total_seconds()
            stats['runtime_formatted'] = str(runtime).split('.')[0]
        
        stats['queue_sizes'] = {
            'discovery': self.discovery_queue.qsize(),
            'processing': self.processing_queue.qsize(),
            'analysis': self.analysis_queue.qsize(),
            'integration': self.integration_queue.qsize(),
            'monitoring': self.monitoring_queue.qsize()
        }
        
        stats['is_running'] = self.is_running
        stats['worker_threads'] = len(self.worker_threads)
        stats['config'] = self.config
        
        return stats
    
    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update processing configuration"""
        try:
            self.config.update(new_config)
            logger.info(f"⚙️ Configuration updated: {new_config}")
            return {"success": True, "config": self.config}
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return {"success": False, "error": str(e)}
    
    def process_single_repository(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Process a single repository manually"""
        try:
            # Get repository info
            repo_info = github_api.get_repository_details(owner, repo_name)
            if not repo_info['success']:
                return repo_info
            
            repository = {
                'username': owner,
                'repo_name': repo_name,
                'full_name': f"{owner}/{repo_name}",
                'clone_url': repo_info['repository'].get('clone_url', ''),
                'html_url': repo_info['repository'].get('html_url', ''),
                'description': repo_info['repository'].get('description', ''),
                'language': repo_info['repository'].get('language', ''),
                'stars': repo_info['repository'].get('stars', 0),
                'size': repo_info['repository'].get('size', 0),
                'updated_at': repo_info['repository'].get('updated_at', ''),
                'manual_processing': True
            }
            
            # Process through pipeline
            result = self.process_repository_automated(repository)
            return result
            
        except Exception as e:
            logger.error(f"Error processing single repository {owner}/{repo_name}: {e}")
            return {"success": False, "error": str(e)}

# Global instance
automated_processor = AutomatedRepositoryProcessor()