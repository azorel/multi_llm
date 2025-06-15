#!/usr/bin/env python3
"""
Integration Pipeline Orchestrator
Connects GitHub API → Repository Processing → Code Analysis → Knowledge Base → Workflow Automation
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import json
import uuid
from pathlib import Path

from github_api_handler import github_api, setup_automated_processing
from automated_repository_processor import automated_processor
from repository_integration_service import RepositoryIntegrationService
from repository_code_analyzer import repository_analyzer
from background_processing_service import background_service, JobPriority
from workflow_automation_scheduler import workflow_scheduler, WorkflowTrigger
from knowledge_hub_orchestrator import orchestrator
from database import NotionLikeDatabase

logger = logging.getLogger(__name__)

@dataclass
class PipelineConfig:
    """Configuration for the integration pipeline"""
    github_monitoring_enabled: bool = True
    auto_repository_discovery: bool = True
    auto_code_analysis: bool = True
    auto_integration: bool = True
    batch_processing_enabled: bool = True
    workflow_automation_enabled: bool = True
    max_concurrent_operations: int = 3
    discovery_interval_hours: int = 24
    monitoring_interval_hours: int = 6
    health_check_interval_hours: int = 12
    repository_filters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.repository_filters is None:
            self.repository_filters = {
                'min_stars': 1,
                'exclude_forks': True,
                'exclude_archived': True,
                'languages': ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust']
            }

class IntegrationPipelineOrchestrator:
    """
    Master orchestrator that connects all systems in a comprehensive automation pipeline
    """
    
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.db = NotionLikeDatabase()
        self.integration_service = RepositoryIntegrationService()
        
        # Pipeline state
        self.is_running = False
        self.pipeline_threads = []
        self.operation_queue = []
        self.active_operations = {}
        
        # Statistics and monitoring
        self.pipeline_stats = {
            'start_time': None,
            'repositories_discovered': 0,
            'repositories_processed': 0,
            'repositories_analyzed': 0,
            'repositories_integrated': 0,
            'workflows_executed': 0,
            'errors_encountered': 0,
            'last_discovery': None,
            'last_monitoring': None,
            'last_health_check': None
        }
        
        # Event handlers and callbacks
        self.event_handlers = {
            'repository_discovered': [],
            'repository_processed': [],
            'repository_analyzed': [],
            'repository_integrated': [],
            'workflow_completed': [],
            'error_occurred': []
        }
        
        # Integration tracking
        self.integration_cache = {}
        self.processing_locks = set()
        
        logger.info("🔗 Integration Pipeline Orchestrator initialized")
    
    def start_pipeline(self) -> Dict[str, Any]:
        """Start the complete integration pipeline"""
        if self.is_running:
            return {"success": False, "error": "Pipeline already running"}
        
        try:
            self.is_running = True
            self.pipeline_stats['start_time'] = datetime.now()
            
            # Initialize all services
            init_results = self._initialize_services()
            if not all(result['success'] for result in init_results.values()):
                failed_services = [name for name, result in init_results.items() if not result['success']]
                return {
                    "success": False, 
                    "error": f"Failed to initialize services: {failed_services}",
                    "details": init_results
                }
            
            # Setup GitHub API automation
            setup_automated_processing()
            
            # Start pipeline workers
            self._start_pipeline_workers()
            
            # Setup event listeners
            self._setup_event_listeners()
            
            # Start initial discovery if enabled
            if self.config.auto_repository_discovery:
                self._trigger_repository_discovery()
            
            logger.info("🚀 Integration Pipeline started successfully")
            return {
                "success": True,
                "message": "Integration pipeline started",
                "services_initialized": list(init_results.keys()),
                "config": self.config.__dict__,
                "workers": len(self.pipeline_threads)
            }
            
        except Exception as e:
            logger.error(f"Error starting integration pipeline: {e}")
            self.is_running = False
            return {"success": False, "error": str(e)}
    
    def stop_pipeline(self) -> Dict[str, Any]:
        """Stop the integration pipeline"""
        if not self.is_running:
            return {"success": False, "error": "Pipeline not running"}
        
        try:
            self.is_running = False
            
            # Stop all workers
            for thread in self.pipeline_threads:
                thread.join(timeout=30)
            
            self.pipeline_threads.clear()
            
            # Stop services
            stop_results = {}
            if background_service.is_running:
                stop_results['background_service'] = background_service.stop_service()
            if workflow_scheduler.is_running:
                stop_results['workflow_scheduler'] = workflow_scheduler.stop_scheduler()
            if automated_processor.is_running:
                stop_results['automated_processor'] = automated_processor.stop_automated_processing()
            
            logger.info("🛑 Integration Pipeline stopped")
            return {
                "success": True,
                "message": "Integration pipeline stopped",
                "final_stats": self.get_pipeline_stats(),
                "stop_results": stop_results
            }
            
        except Exception as e:
            logger.error(f"Error stopping integration pipeline: {e}")
            return {"success": False, "error": str(e)}
    
    def process_github_user_complete(self, username: str) -> Dict[str, Any]:
        """Process a GitHub user through the complete pipeline"""
        try:
            operation_id = str(uuid.uuid4())
            logger.info(f"🔄 Starting complete processing for GitHub user: {username}")
            
            # Submit as background job for tracking
            job_result = background_service.submit_job(
                job_type="complete_user_processing",
                title=f"Complete Processing: {username}",
                description=f"Process GitHub user {username} through complete pipeline",
                parameters={
                    'username': username,
                    'operation_id': operation_id,
                    'config': self.config.__dict__
                },
                priority=JobPriority.HIGH,
                tags=['github', 'user', 'complete_processing']
            )
            
            if not job_result['success']:
                return job_result
            
            self.active_operations[operation_id] = {
                'type': 'user_processing',
                'username': username,
                'job_id': job_result['job_id'],
                'started_at': datetime.now(),
                'status': 'queued'
            }
            
            return {
                "success": True,
                "operation_id": operation_id,
                "job_id": job_result['job_id'],
                "message": f"Complete processing queued for {username}"
            }
            
        except Exception as e:
            logger.error(f"Error starting complete processing for {username}: {e}")
            return {"success": False, "error": str(e)}
    
    def process_repository_complete(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Process a single repository through the complete pipeline"""
        try:
            full_name = f"{owner}/{repo_name}"
            operation_id = str(uuid.uuid4())
            
            logger.info(f"🔄 Starting complete processing for repository: {full_name}")
            
            # Check if already processing
            if full_name in self.processing_locks:
                return {"success": False, "error": "Repository already being processed"}
            
            self.processing_locks.add(full_name)
            
            # Submit as background job
            job_result = background_service.submit_job(
                job_type="complete_repository_processing",
                title=f"Complete Processing: {full_name}",
                description=f"Process repository {full_name} through complete pipeline",
                parameters={
                    'owner': owner,
                    'repo_name': repo_name,
                    'operation_id': operation_id,
                    'config': self.config.__dict__
                },
                priority=JobPriority.NORMAL,
                tags=['github', 'repository', 'complete_processing']
            )
            
            if not job_result['success']:
                self.processing_locks.discard(full_name)
                return job_result
            
            self.active_operations[operation_id] = {
                'type': 'repository_processing',
                'repository': full_name,
                'job_id': job_result['job_id'],
                'started_at': datetime.now(),
                'status': 'queued'
            }
            
            return {
                "success": True,
                "operation_id": operation_id,
                "job_id": job_result['job_id'],
                "message": f"Complete processing queued for {full_name}"
            }
            
        except Exception as e:
            logger.error(f"Error starting complete processing for {owner}/{repo_name}: {e}")
            return {"success": False, "error": str(e)}
    
    def trigger_automated_discovery(self) -> Dict[str, Any]:
        """Trigger automated repository discovery"""
        try:
            logger.info("🔍 Triggering automated repository discovery")
            
            # Submit discovery job
            job_result = background_service.submit_job(
                job_type="automated_discovery",
                title="Automated Repository Discovery",
                description="Discover new repositories from all GitHub users",
                parameters={
                    'filters': self.config.repository_filters,
                    'batch_processing': self.config.batch_processing_enabled
                },
                priority=JobPriority.NORMAL,
                tags=['discovery', 'automation']
            )
            
            if job_result['success']:
                self.pipeline_stats['last_discovery'] = datetime.now()
            
            return job_result
            
        except Exception as e:
            logger.error(f"Error triggering automated discovery: {e}")
            return {"success": False, "error": str(e)}
    
    def trigger_repository_monitoring(self) -> Dict[str, Any]:
        """Trigger repository monitoring for updates"""
        try:
            logger.info("👁️ Triggering repository monitoring")
            
            # Submit monitoring job
            job_result = background_service.submit_job(
                job_type="repository_monitoring",
                title="Repository Monitoring",
                description="Monitor all repositories for updates and changes",
                parameters={
                    'auto_process_updates': True,
                    'health_checks': True
                },
                priority=JobPriority.LOW,
                tags=['monitoring', 'automation']
            )
            
            if job_result['success']:
                self.pipeline_stats['last_monitoring'] = datetime.now()
            
            return job_result
            
        except Exception as e:
            logger.error(f"Error triggering repository monitoring: {e}")
            return {"success": False, "error": str(e)}
    
    def trigger_health_checks(self) -> Dict[str, Any]:
        """Trigger comprehensive health checks"""
        try:
            logger.info("🏥 Triggering health checks")
            
            # Submit health check job
            job_result = background_service.submit_job(
                job_type="health_checks",
                title="Pipeline Health Checks",
                description="Comprehensive health checks for all pipeline components",
                parameters={
                    'check_github_api': True,
                    'check_repositories': True,
                    'check_integration_status': True,
                    'check_workflows': True
                },
                priority=JobPriority.LOW,
                tags=['health', 'monitoring']
            )
            
            if job_result['success']:
                self.pipeline_stats['last_health_check'] = datetime.now()
            
            return job_result
            
        except Exception as e:
            logger.error(f"Error triggering health checks: {e}")
            return {"success": False, "error": str(e)}
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status"""
        try:
            # Get service statuses
            service_status = {
                'github_api': {
                    'monitoring_enabled': github_api.monitoring_enabled,
                    'rate_limit': github_api.get_rate_limit_status(),
                    'stats': github_api.get_processing_stats()
                },
                'automated_processor': {
                    'running': automated_processor.is_running,
                    'stats': automated_processor.get_processing_stats()
                },
                'background_service': {
                    'running': background_service.is_running,
                    'stats': background_service.get_service_stats()
                },
                'workflow_scheduler': {
                    'running': workflow_scheduler.is_running,
                    'stats': workflow_scheduler.get_scheduler_stats()
                }
            }
            
            # Get repository statistics
            repo_stats = self._get_repository_statistics()
            
            # Get active operations
            active_ops = []
            for op_id, op_info in self.active_operations.items():
                op_info_copy = op_info.copy()
                if 'started_at' in op_info_copy:
                    op_info_copy['started_at'] = op_info_copy['started_at'].isoformat()
                active_ops.append(op_info_copy)
            
            return {
                "success": True,
                "pipeline": {
                    "running": self.is_running,
                    "config": self.config.__dict__,
                    "stats": self.pipeline_stats,
                    "active_operations": active_ops,
                    "worker_threads": len(self.pipeline_threads)
                },
                "services": service_status,
                "repositories": repo_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return {"success": False, "error": str(e)}
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        stats = self.pipeline_stats.copy()
        
        # Add runtime information
        if stats['start_time']:
            runtime = datetime.now() - stats['start_time']
            stats['runtime_seconds'] = runtime.total_seconds()
            stats['runtime_formatted'] = str(runtime).split('.')[0]
        
        # Add rates
        if stats['start_time']:
            hours_running = (datetime.now() - stats['start_time']).total_seconds() / 3600
            if hours_running > 0:
                stats['repositories_per_hour'] = stats['repositories_processed'] / hours_running
                stats['integrations_per_hour'] = stats['repositories_integrated'] / hours_running
        
        return stats
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler for pipeline events"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
            logger.info(f"📞 Added event handler for {event_type}")
    
    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update pipeline configuration"""
        try:
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            logger.info(f"⚙️ Pipeline configuration updated: {new_config}")
            return {"success": True, "config": self.config.__dict__}
            
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return {"success": False, "error": str(e)}
    
    def _initialize_services(self) -> Dict[str, Dict[str, Any]]:
        """Initialize all required services"""
        results = {}
        
        # Start background processing service
        try:
            results['background_service'] = background_service.start_service()
        except Exception as e:
            results['background_service'] = {"success": False, "error": str(e)}
        
        # Start workflow scheduler
        try:
            results['workflow_scheduler'] = workflow_scheduler.start_scheduler()
        except Exception as e:
            results['workflow_scheduler'] = {"success": False, "error": str(e)}
        
        # Start automated processor
        try:
            results['automated_processor'] = automated_processor.start_automated_processing()
        except Exception as e:
            results['automated_processor'] = {"success": False, "error": str(e)}
        
        # Register job handlers
        self._register_pipeline_job_handlers()
        
        return results
    
    def _register_pipeline_job_handlers(self):
        """Register job handlers for pipeline operations"""
        
        # Complete user processing handler
        def complete_user_processing_handler(parameters, progress_callback):
            username = parameters['username']
            operation_id = parameters['operation_id']
            
            try:
                # Update operation status
                if operation_id in self.active_operations:
                    self.active_operations[operation_id]['status'] = 'running'
                
                progress_callback(0, 100, f"Starting complete processing for user: {username}")
                
                # Step 1: Get user information and repositories
                progress_callback(10, 100, "Fetching user information and repositories")
                user_result = github_api.get_user_info(username)
                if not user_result['success']:
                    raise Exception(f"Failed to get user info: {user_result.get('error', 'Unknown error')}")
                
                repos_result = github_api.get_user_repositories(username)
                if not repos_result['success']:
                    raise Exception(f"Failed to get repositories: {repos_result.get('error', 'Unknown error')}")
                
                repositories = repos_result['repositories']
                self.pipeline_stats['repositories_discovered'] += len(repositories)
                
                # Apply filters
                filtered_repos = self._apply_repository_filters(repositories)
                progress_callback(20, 100, f"Found {len(filtered_repos)} repositories (after filtering)")
                
                # Step 2: Process each repository
                processed = 0
                for i, repo in enumerate(filtered_repos):
                    repo_progress = 20 + (60 * i / len(filtered_repos))
                    progress_callback(int(repo_progress), 100, f"Processing repository: {repo['name']}")
                    
                    # Convert to standard format
                    repository = {
                        'username': username,
                        'repo_name': repo['name'],
                        'full_name': repo['full_name'],
                        'clone_url': repo['clone_url'],
                        'html_url': repo['html_url'],
                        'description': repo['description'],
                        'language': repo['language'],
                        'stars': repo['stars'],
                        'size': repo['size'],
                        'updated_at': repo['updated_at']
                    }
                    
                    # Process through pipeline
                    result = self._process_single_repository_pipeline(repository)
                    if result.get('success', False):
                        processed += 1
                        self.pipeline_stats['repositories_processed'] += 1
                        if result.get('analyzed', False):
                            self.pipeline_stats['repositories_analyzed'] += 1
                        if result.get('integrated', False):
                            self.pipeline_stats['repositories_integrated'] += 1
                
                # Step 3: Update user record
                progress_callback(90, 100, "Updating user record")
                self._update_github_user_record(username, user_result['user'], len(repositories), processed)
                
                progress_callback(100, 100, f"Complete processing finished: {processed}/{len(filtered_repos)} repositories processed")
                
                # Trigger events
                self._trigger_event('repository_processed', {
                    'username': username,
                    'repositories_processed': processed,
                    'total_repositories': len(repositories)
                })
                
                # Update operation status
                if operation_id in self.active_operations:
                    self.active_operations[operation_id]['status'] = 'completed'
                
                return {
                    "success": True,
                    "username": username,
                    "repositories_found": len(repositories),
                    "repositories_processed": processed,
                    "user_info": user_result['user']
                }
                
            except Exception as e:
                # Update operation status
                if operation_id in self.active_operations:
                    self.active_operations[operation_id]['status'] = 'failed'
                    self.active_operations[operation_id]['error'] = str(e)
                
                self.pipeline_stats['errors_encountered'] += 1
                logger.error(f"Complete user processing failed for {username}: {e}")
                raise e
        
        background_service.register_job_handler("complete_user_processing", complete_user_processing_handler)
        
        # Complete repository processing handler
        def complete_repository_processing_handler(parameters, progress_callback):
            owner = parameters['owner']
            repo_name = parameters['repo_name']
            operation_id = parameters['operation_id']
            full_name = f"{owner}/{repo_name}"
            
            try:
                # Update operation status
                if operation_id in self.active_operations:
                    self.active_operations[operation_id]['status'] = 'running'
                
                progress_callback(0, 100, f"Starting complete processing for repository: {full_name}")
                
                # Step 1: Get repository details
                progress_callback(10, 100, "Fetching repository details")
                repo_result = github_api.get_repository_details(owner, repo_name)
                if not repo_result['success']:
                    raise Exception(f"Failed to get repository details: {repo_result.get('error', 'Unknown error')}")
                
                repo_data = repo_result['repository']
                
                # Convert to standard format
                repository = {
                    'username': owner,
                    'repo_name': repo_name,
                    'full_name': full_name,
                    'clone_url': repo_data['clone_url'],
                    'html_url': repo_data['html_url'],
                    'description': repo_data['description'],
                    'language': repo_data['language'],
                    'stars': repo_data['stars'],
                    'size': repo_data['size'],
                    'updated_at': repo_data['updated_at']
                }
                
                # Step 2: Process through complete pipeline
                progress_callback(20, 100, "Processing through pipeline")
                result = self._process_single_repository_pipeline(repository)
                
                progress_callback(100, 100, "Complete repository processing finished")
                
                # Update statistics
                self.pipeline_stats['repositories_processed'] += 1
                if result.get('analyzed', False):
                    self.pipeline_stats['repositories_analyzed'] += 1
                if result.get('integrated', False):
                    self.pipeline_stats['repositories_integrated'] += 1
                
                # Update operation status
                if operation_id in self.active_operations:
                    self.active_operations[operation_id]['status'] = 'completed'
                
                # Remove from processing locks
                self.processing_locks.discard(full_name)
                
                return result
                
            except Exception as e:
                # Update operation status
                if operation_id in self.active_operations:
                    self.active_operations[operation_id]['status'] = 'failed'
                    self.active_operations[operation_id]['error'] = str(e)
                
                # Remove from processing locks
                self.processing_locks.discard(full_name)
                
                self.pipeline_stats['errors_encountered'] += 1
                logger.error(f"Complete repository processing failed for {full_name}: {e}")
                raise e
        
        background_service.register_job_handler("complete_repository_processing", complete_repository_processing_handler)
        
        # Automated discovery handler
        def automated_discovery_handler(parameters, progress_callback):
            try:
                progress_callback(0, 100, "Starting automated discovery")
                
                # Get all GitHub users
                users = self.db.get_table_data('github_users')
                if not users:
                    return {"success": True, "message": "No GitHub users found", "discovered": 0}
                
                total_discovered = 0
                
                for i, user in enumerate(users):
                    user_progress = int((i / len(users)) * 90)
                    progress_callback(user_progress, 100, f"Processing user: {user.get('username', 'Unknown')}")
                    
                    username = user.get('username', '')
                    if not username:
                        continue
                    
                    # Use batch processing if enabled
                    if self.config.batch_processing_enabled:
                        result = github_api.batch_process_users([username])
                        if result['success'] and result['results']:
                            user_result = result['results'][0]
                            discovered = len(user_result.get('repositories', []))
                            total_discovered += discovered
                    else:
                        repos_result = github_api.get_user_repositories(username)
                        if repos_result['success']:
                            discovered = len(repos_result['repositories'])
                            total_discovered += discovered
                
                progress_callback(100, 100, f"Automated discovery completed: {total_discovered} repositories discovered")
                
                self.pipeline_stats['repositories_discovered'] += total_discovered
                
                return {
                    "success": True,
                    "discovered": total_discovered,
                    "users_processed": len(users)
                }
                
            except Exception as e:
                logger.error(f"Automated discovery failed: {e}")
                raise e
        
        background_service.register_job_handler("automated_discovery", automated_discovery_handler)
        
        # Repository monitoring handler
        def repository_monitoring_handler(parameters, progress_callback):
            try:
                progress_callback(0, 100, "Starting repository monitoring")
                
                # Get all repositories
                repos = self.db.get_table_data('knowledge_hub')
                github_repos = []
                
                for repo in repos:
                    if (repo.get('category', '').lower().find('repository') != -1 and 
                        repo.get('github_owner') and repo.get('github_repo')):
                        github_repos.append({
                            'owner': repo['github_owner'],
                            'name': repo['github_repo'],
                            'last_checked': repo.get('integration_date', '')
                        })
                
                progress_callback(20, 100, f"Monitoring {len(github_repos)} repositories")
                
                # Monitor for updates
                result = github_api.monitor_repository_updates(github_repos)
                
                # Process updates if auto-processing enabled
                if parameters.get('auto_process_updates', False) and result.get('updates_found', 0) > 0:
                    progress_callback(60, 100, f"Processing {result['updates_found']} updated repositories")
                    
                    for update in result.get('updates', []):
                        owner = update['owner']
                        name = update['name']
                        
                        # Trigger re-processing
                        self.process_repository_complete(owner, name)
                
                # Run health checks if enabled
                if parameters.get('health_checks', False):
                    progress_callback(80, 100, "Running repository health checks")
                    health_result = github_api.health_check_repositories(github_repos)
                    result['health_check'] = health_result
                
                progress_callback(100, 100, "Repository monitoring completed")
                
                return result
                
            except Exception as e:
                logger.error(f"Repository monitoring failed: {e}")
                raise e
        
        background_service.register_job_handler("repository_monitoring", repository_monitoring_handler)
        
        # Health checks handler
        def health_checks_handler(parameters, progress_callback):
            try:
                progress_callback(0, 100, "Starting comprehensive health checks")
                
                health_results = {}
                
                # GitHub API health
                if parameters.get('check_github_api', True):
                    progress_callback(20, 100, "Checking GitHub API health")
                    health_results['github_api'] = github_api.get_rate_limit_status()
                
                # Repository health
                if parameters.get('check_repositories', True):
                    progress_callback(40, 100, "Checking repository health")
                    repos = self.db.get_table_data('knowledge_hub')
                    github_repos = []
                    
                    for repo in repos:
                        if (repo.get('category', '').lower().find('repository') != -1 and 
                            repo.get('github_owner') and repo.get('github_repo')):
                            github_repos.append({
                                'owner': repo['github_owner'],
                                'name': repo['github_repo']
                            })
                    
                    health_results['repositories'] = github_api.health_check_repositories(github_repos)
                
                # Integration status
                if parameters.get('check_integration_status', True):
                    progress_callback(60, 100, "Checking integration status")
                    health_results['integration'] = self._check_integration_health()
                
                # Workflow status
                if parameters.get('check_workflows', True):
                    progress_callback(80, 100, "Checking workflow status")
                    health_results['workflows'] = workflow_scheduler.get_scheduler_stats()
                
                progress_callback(100, 100, "Health checks completed")
                
                return {
                    "success": True,
                    "health_results": health_results,
                    "overall_health": self._calculate_overall_health(health_results)
                }
                
            except Exception as e:
                logger.error(f"Health checks failed: {e}")
                raise e
        
        background_service.register_job_handler("health_checks", health_checks_handler)
    
    def _process_single_repository_pipeline(self, repository: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single repository through the complete pipeline"""
        full_name = repository['full_name']
        result = {
            'success': True,
            'repository': full_name,
            'steps_completed': [],
            'analyzed': False,
            'integrated': False
        }
        
        try:
            # Step 1: Add to knowledge hub if not already there
            existing = self._find_existing_repository(repository)
            if not existing:
                knowledge_result = self._add_repository_to_knowledge_hub(repository)
                if knowledge_result['success']:
                    result['steps_completed'].append('knowledge_hub_added')
            else:
                result['steps_completed'].append('knowledge_hub_exists')
            
            # Step 2: Code analysis (if Python repository)
            if self.config.auto_code_analysis and repository.get('language', '').lower() == 'python':
                try:
                    # For now, we'll do metadata-based analysis
                    # In a full implementation, this would clone and analyze the actual code
                    analysis_result = self._perform_metadata_analysis(repository)
                    if analysis_result['success']:
                        result['steps_completed'].append('code_analysis')
                        result['analyzed'] = True
                        result['analysis'] = analysis_result
                except Exception as e:
                    logger.warning(f"Code analysis failed for {full_name}: {e}")
            
            # Step 3: Integration (if configured)
            if self.config.auto_integration:
                try:
                    integration_result = self._integrate_repository_metadata(repository)
                    if integration_result['success']:
                        result['steps_completed'].append('integration')
                        result['integrated'] = True
                        result['integration'] = integration_result
                except Exception as e:
                    logger.warning(f"Integration failed for {full_name}: {e}")
            
            # Step 4: Trigger events
            self._trigger_event('repository_processed', {
                'repository': repository,
                'result': result
            })
            
            return result
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            return result
    
    def _apply_repository_filters(self, repositories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply repository filters based on configuration"""
        filtered = []
        filters = self.config.repository_filters
        
        for repo in repositories:
            # Skip forks if configured
            if filters.get('exclude_forks', True) and repo.get('fork', False):
                continue
            
            # Skip archived if configured
            if filters.get('exclude_archived', True) and repo.get('archived', False):
                continue
            
            # Check minimum stars
            if repo.get('stars', 0) < filters.get('min_stars', 0):
                continue
            
            # Check language filter
            languages = filters.get('languages', [])
            if languages and repo.get('language') not in languages:
                continue
            
            filtered.append(repo)
        
        return filtered
    
    def _find_existing_repository(self, repository: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find existing repository in knowledge hub"""
        try:
            repos = self.db.get_table_data('knowledge_hub')
            for repo in repos:
                if (repo.get('github_owner') == repository['username'] and 
                    repo.get('github_repo') == repository['repo_name']):
                    return repo
            return None
        except Exception as e:
            logger.error(f"Error finding existing repository: {e}")
            return None
    
    def _add_repository_to_knowledge_hub(self, repository: Dict[str, Any]) -> Dict[str, Any]:
        """Add repository to knowledge hub"""
        try:
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
                'integration_status': 'pipeline_processed',
                'integration_date': datetime.now().isoformat(),
                'created_date': datetime.now().isoformat()
            }
            
            record_id = self.db.add_record('knowledge_hub', knowledge_data)
            return {"success": True, "record_id": record_id}
            
        except Exception as e:
            logger.error(f"Error adding repository to knowledge hub: {e}")
            return {"success": False, "error": str(e)}
    
    def _perform_metadata_analysis(self, repository: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis based on repository metadata"""
        try:
            analysis = {
                'success': True,
                'repository': repository['full_name'],
                'metadata_analysis': {
                    'language': repository.get('language', 'Unknown'),
                    'size_kb': repository.get('size', 0),
                    'stars': repository.get('stars', 0),
                    'description': repository.get('description', ''),
                    'complexity_estimate': self._estimate_complexity(repository),
                    'project_type': self._classify_project_type(repository),
                    'learning_value': self._assess_learning_value(repository),
                    'patterns_detected': self._detect_patterns_from_metadata(repository)
                },
                'analysis_date': datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error performing metadata analysis: {e}")
            return {'success': False, 'error': str(e)}
    
    def _integrate_repository_metadata(self, repository: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate repository using metadata"""
        try:
            # Update existing record with integration metadata
            existing = self._find_existing_repository(repository)
            if existing:
                integration_data = {
                    'integration_status': 'metadata_integrated',
                    'integration_date': datetime.now().isoformat(),
                    'metadata_analysis': json.dumps({
                        'complexity': self._estimate_complexity(repository),
                        'project_type': self._classify_project_type(repository),
                        'learning_value': self._assess_learning_value(repository)
                    })
                }
                
                self.db.update_record('knowledge_hub', existing['id'], integration_data)
                
                return {
                    'success': True,
                    'action': 'metadata_integrated',
                    'record_id': existing['id']
                }
            
            return {'success': False, 'error': 'Repository not found in knowledge hub'}
            
        except Exception as e:
            logger.error(f"Error integrating repository metadata: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_github_user_record(self, username: str, user_info: Dict[str, Any], 
                                  total_repos: int, processed_repos: int):
        """Update GitHub user record with processing results"""
        try:
            users = self.db.get_table_data('github_users')
            for user in users:
                if user.get('username') == username:
                    update_data = {
                        'last_processed': datetime.now().isoformat(),
                        'repos_found': total_repos,
                        'repos_processed': processed_repos,
                        'status': 'Pipeline Processed',
                        'profile_data': json.dumps(user_info)
                    }
                    self.db.update_record('github_users', user['id'], update_data)
                    break
        except Exception as e:
            logger.error(f"Error updating GitHub user record: {e}")
    
    def _get_repository_statistics(self) -> Dict[str, Any]:
        """Get repository statistics"""
        try:
            repos = self.db.get_table_data('knowledge_hub')
            github_repos = [r for r in repos if r.get('category', '').lower().find('repository') != -1]
            
            stats = {
                'total_repositories': len(github_repos),
                'integrated_repositories': len([r for r in github_repos if r.get('integration_status') == 'metadata_integrated']),
                'pipeline_processed': len([r for r in github_repos if r.get('integration_status') == 'pipeline_processed']),
                'languages': {},
                'total_stars': 0,
                'average_stars': 0
            }
            
            # Language breakdown
            for repo in github_repos:
                language = repo.get('github_language', 'Unknown')
                stats['languages'][language] = stats['languages'].get(language, 0) + 1
                stats['total_stars'] += repo.get('github_stars', 0)
            
            if github_repos:
                stats['average_stars'] = stats['total_stars'] / len(github_repos)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting repository statistics: {e}")
            return {}
    
    def _check_integration_health(self) -> Dict[str, Any]:
        """Check integration system health"""
        try:
            # Check database connectivity
            self.db.get_table_data('knowledge_hub', limit=1)
            
            # Check integration service
            integrated_repos = self.integration_service.get_integrated_repositories()
            
            # Check processing locks
            stuck_operations = []
            for op_id, op_info in self.active_operations.items():
                if op_info.get('started_at'):
                    elapsed = datetime.now() - op_info['started_at']
                    if elapsed > timedelta(hours=2):  # Operations stuck for more than 2 hours
                        stuck_operations.append(op_id)
            
            return {
                "success": True,
                "database_connected": True,
                "integrated_repositories": len(integrated_repos),
                "active_operations": len(self.active_operations),
                "stuck_operations": len(stuck_operations),
                "processing_locks": len(self.processing_locks)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "database_connected": False
            }
    
    def _calculate_overall_health(self, health_results: Dict[str, Any]) -> str:
        """Calculate overall health score"""
        try:
            healthy_systems = 0
            total_systems = 0
            
            for system, result in health_results.items():
                total_systems += 1
                if isinstance(result, dict) and result.get('success', False):
                    healthy_systems += 1
            
            if total_systems == 0:
                return "unknown"
            
            health_ratio = healthy_systems / total_systems
            
            if health_ratio >= 0.9:
                return "excellent"
            elif health_ratio >= 0.7:
                return "good"
            elif health_ratio >= 0.5:
                return "fair"
            else:
                return "poor"
                
        except Exception as e:
            logger.error(f"Error calculating overall health: {e}")
            return "unknown"
    
    def _start_pipeline_workers(self):
        """Start pipeline worker threads"""
        # Discovery scheduler
        if self.config.auto_repository_discovery:
            discovery_worker = threading.Thread(target=self._discovery_scheduler_worker, daemon=True)
            discovery_worker.start()
            self.pipeline_threads.append(discovery_worker)
        
        # Monitoring scheduler
        if self.config.github_monitoring_enabled:
            monitoring_worker = threading.Thread(target=self._monitoring_scheduler_worker, daemon=True)
            monitoring_worker.start()
            self.pipeline_threads.append(monitoring_worker)
        
        # Health check scheduler
        health_worker = threading.Thread(target=self._health_check_scheduler_worker, daemon=True)
        health_worker.start()
        self.pipeline_threads.append(health_worker)
        
        logger.info(f"🔧 Started {len(self.pipeline_threads)} pipeline workers")
    
    def _discovery_scheduler_worker(self):
        """Worker for scheduled repository discovery"""
        while self.is_running:
            try:
                time.sleep(self.config.discovery_interval_hours * 3600)
                
                if self.is_running:
                    logger.info("⏰ Triggering scheduled repository discovery")
                    self.trigger_automated_discovery()
                    
            except Exception as e:
                logger.error(f"Discovery scheduler worker error: {e}")
                time.sleep(3600)  # Wait 1 hour on error
    
    def _monitoring_scheduler_worker(self):
        """Worker for scheduled repository monitoring"""
        while self.is_running:
            try:
                time.sleep(self.config.monitoring_interval_hours * 3600)
                
                if self.is_running:
                    logger.info("⏰ Triggering scheduled repository monitoring")
                    self.trigger_repository_monitoring()
                    
            except Exception as e:
                logger.error(f"Monitoring scheduler worker error: {e}")
                time.sleep(3600)  # Wait 1 hour on error
    
    def _health_check_scheduler_worker(self):
        """Worker for scheduled health checks"""
        while self.is_running:
            try:
                time.sleep(self.config.health_check_interval_hours * 3600)
                
                if self.is_running:
                    logger.info("⏰ Triggering scheduled health checks")
                    self.trigger_health_checks()
                    
            except Exception as e:
                logger.error(f"Health check scheduler worker error: {e}")
                time.sleep(3600)  # Wait 1 hour on error
    
    def _setup_event_listeners(self):
        """Setup event listeners for pipeline coordination"""
        
        # Add workflow scheduler event listeners
        workflow_scheduler.add_event_listener('repository_updated', 
                                            lambda data: self._handle_repository_updated(data))
        
        # Add automated processor callbacks
        automated_processor.add_callback('on_processing_complete', 
                                       lambda repo, result: self._handle_processing_complete(repo, result))
        
        automated_processor.add_callback('on_error', 
                                       lambda repo, error: self._handle_processing_error(repo, error))
    
    def _handle_repository_updated(self, data: Dict[str, Any]):
        """Handle repository update events"""
        try:
            owner = data.get('owner', '')
            name = data.get('name', '')
            
            if owner and name:
                logger.info(f"🔄 Repository updated, triggering re-processing: {owner}/{name}")
                self.process_repository_complete(owner, name)
                
        except Exception as e:
            logger.error(f"Error handling repository update: {e}")
    
    def _handle_processing_complete(self, repository: Dict[str, Any], result: Dict[str, Any]):
        """Handle processing completion events"""
        try:
            self._trigger_event('repository_processed', {
                'repository': repository,
                'result': result
            })
        except Exception as e:
            logger.error(f"Error handling processing complete: {e}")
    
    def _handle_processing_error(self, repository: Dict[str, Any], error: Any):
        """Handle processing error events"""
        try:
            self.pipeline_stats['errors_encountered'] += 1
            self._trigger_event('error_occurred', {
                'repository': repository,
                'error': str(error)
            })
        except Exception as e:
            logger.error(f"Error handling processing error: {e}")
    
    def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger pipeline events"""
        try:
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    handler(data)
            
            # Also trigger workflow scheduler events
            workflow_scheduler.trigger_event(event_type, data)
            
        except Exception as e:
            logger.error(f"Error triggering event {event_type}: {e}")
    
    def _trigger_repository_discovery(self):
        """Trigger initial repository discovery"""
        try:
            self.trigger_automated_discovery()
        except Exception as e:
            logger.error(f"Error triggering initial discovery: {e}")
    
    # Helper methods from automated processor for consistency
    def _estimate_complexity(self, repository: Dict[str, Any]) -> int:
        """Estimate repository complexity (1-10)"""
        complexity = 1
        
        size = repository.get('size', 0)
        if size > 10000:
            complexity += 3
        elif size > 1000:
            complexity += 2
        elif size > 100:
            complexity += 1
        
        language = repository.get('language', '').lower()
        if language in ['c++', 'rust', 'assembly']:
            complexity += 2
        elif language in ['java', 'c#', 'go']:
            complexity += 1
        
        stars = repository.get('stars', 0)
        if stars > 1000:
            complexity += 1
        
        return min(complexity, 10)
    
    def _classify_project_type(self, repository: Dict[str, Any]) -> str:
        """Classify the type of project"""
        description = repository.get('description', '').lower()
        name = repository.get('repo_name', '').lower()
        
        if any(term in description for term in ['web', 'api', 'server', 'flask', 'django', 'express']):
            return 'Web Application'
        elif any(term in description for term in ['cli', 'command', 'tool', 'utility']):
            return 'CLI Tool'
        elif any(term in description for term in ['library', 'package', 'module', 'framework']):
            return 'Library/Framework'
        elif any(term in description for term in ['ai', 'ml', 'machine learning', 'neural', 'model']):
            return 'AI/ML Project'
        elif any(term in description for term in ['data', 'analysis', 'dashboard', 'visualization']):
            return 'Data Project'
        elif any(term in description for term in ['game', 'gaming', 'unity', 'pygame']):
            return 'Game'
        else:
            return 'General Application'
    
    def _assess_learning_value(self, repository: Dict[str, Any]) -> str:
        """Assess the learning value of a repository"""
        stars = repository.get('stars', 0)
        size = repository.get('size', 0)
        description = repository.get('description', '').lower()
        
        score = 0
        
        if stars > 1000:
            score += 3
        elif stars > 100:
            score += 2
        elif stars > 10:
            score += 1
        
        if size > 1000:
            score += 2
        elif size > 100:
            score += 1
        
        if len(description) > 50:
            score += 1
        
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
        
        if 'flask' in description or 'flask' in name:
            patterns.append('Flask Web Framework')
        if 'django' in description or 'django' in name:
            patterns.append('Django Web Framework')
        if 'api' in description or 'api' in name:
            patterns.append('API Development')
        if any(term in description for term in ['microservice', 'micro-service']):
            patterns.append('Microservices Architecture')
        if 'mvc' in description:
            patterns.append('MVC Pattern')
        if any(term in description for term in ['docker', 'container']):
            patterns.append('Containerization')
        if any(term in description for term in ['kubernetes', 'k8s']):
            patterns.append('Kubernetes')
        if 'ai' in description or 'ml' in description:
            patterns.append('Machine Learning')
        
        return patterns

# Global instance
integration_orchestrator = IntegrationPipelineOrchestrator()