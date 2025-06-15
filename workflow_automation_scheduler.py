#!/usr/bin/env python3
"""
Workflow Automation and Scheduling System
Handles automated workflows, scheduled tasks, and repository discovery workflows
"""

import asyncio
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
try:
    import croniter
except ImportError:
    # Mock croniter if not available
    class croniter:
        def __init__(self, cron_expr, start_time):
            self.start_time = start_time
        
        def get_next(self, ret_type):
            # Return next hour as a fallback
            return self.start_time + timedelta(hours=1)
        
        @staticmethod
        def croniter(cron_expr):
            # Basic validation - just check if it has the right number of parts
            parts = cron_expr.split()
            if len(parts) != 5:
                raise ValueError("Invalid cron expression")
            return True

from pathlib import Path
import sqlite3

from background_processing_service import background_service, JobPriority, BackgroundJob
from automated_repository_processor import automated_processor
from github_api_handler import github_api
from database import NotionLikeDatabase

logger = logging.getLogger(__name__)

class WorkflowTrigger(Enum):
    """Workflow trigger types"""
    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"
    CONDITION = "condition"
    DEPENDENCY = "dependency"

class WorkflowStatus(Enum):
    """Workflow execution status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""
    step_id: str
    step_type: str  # 'job', 'condition', 'parallel', 'delay'
    title: str
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    timeout: Optional[int] = None  # seconds
    retry_count: int = 0
    max_retries: int = 3
    condition: Optional[str] = None  # Python expression for conditional execution
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class Workflow:
    """Represents a complete workflow"""
    workflow_id: str
    name: str
    description: str
    trigger: WorkflowTrigger
    trigger_config: Dict[str, Any]  # Schedule expression, event config, etc.
    steps: List[WorkflowStep]
    status: WorkflowStatus = WorkflowStatus.INACTIVE
    created_at: datetime = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    tags: List[str] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums to strings
        data['trigger'] = self.trigger.value
        data['status'] = self.status.value
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'last_run', 'next_run']:
            if data[field]:
                data[field] = data[field].isoformat()
        return data

@dataclass
class WorkflowExecution:
    """Represents a workflow execution instance"""
    execution_id: str
    workflow_id: str
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: Optional[str] = None
    step_results: Dict[str, Any] = None
    error: str = ""
    trigger_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.step_results is None:
            self.step_results = {}
        if self.trigger_data is None:
            self.trigger_data = {}

class WorkflowAutomationScheduler:
    """
    Comprehensive workflow automation and scheduling system
    Handles repository discovery, processing workflows, and scheduled tasks
    """
    
    def __init__(self):
        self.db = NotionLikeDatabase()
        
        # Workflow management
        self.workflows: Dict[str, Workflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        
        # Scheduling
        self.scheduler_thread = None
        self.is_running = False
        self.check_interval = 60  # Check every minute
        
        # Step handlers
        self.step_handlers = {}
        
        # Event system
        self.event_listeners = {}
        
        # Statistics
        self.stats = {
            'workflows_created': 0,
            'workflows_executed': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'start_time': None
        }
        
        # Initialize storage
        self._init_workflow_storage()
        
        # Register built-in step handlers
        self._register_builtin_handlers()
        
        # Create default workflows
        self._create_default_workflows()
        
        logger.info("⏰ Workflow Automation Scheduler initialized")
    
    def start_scheduler(self) -> Dict[str, Any]:
        """Start the workflow scheduler"""
        if self.is_running:
            return {"success": False, "error": "Scheduler already running"}
        
        try:
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            
            # Load existing workflows
            self._load_workflows()
            
            # Start scheduler thread
            self.scheduler_thread = threading.Thread(target=self._scheduler_worker, daemon=True)
            self.scheduler_thread.start()
            
            # Calculate next runs for scheduled workflows
            self._calculate_next_runs()
            
            logger.info("🚀 Workflow Scheduler started")
            return {
                "success": True,
                "message": "Workflow scheduler started",
                "active_workflows": len([w for w in self.workflows.values() if w.enabled]),
                "scheduled_workflows": len([w for w in self.workflows.values() if w.trigger == WorkflowTrigger.SCHEDULE and w.enabled])
            }
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            self.is_running = False
            return {"success": False, "error": str(e)}
    
    def stop_scheduler(self) -> Dict[str, Any]:
        """Stop the workflow scheduler"""
        if not self.is_running:
            return {"success": False, "error": "Scheduler not running"}
        
        try:
            self.is_running = False
            
            # Wait for scheduler thread
            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=30)
            
            # Save workflows
            self._save_workflows()
            
            logger.info("🛑 Workflow Scheduler stopped")
            return {
                "success": True,
                "message": "Workflow scheduler stopped",
                "final_stats": self.get_scheduler_stats()
            }
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            return {"success": False, "error": str(e)}
    
    def create_workflow(self, name: str, description: str, trigger: WorkflowTrigger,
                       trigger_config: Dict[str, Any], steps: List[Dict[str, Any]],
                       tags: List[str] = None) -> Dict[str, Any]:
        """Create a new workflow"""
        try:
            workflow_id = str(uuid.uuid4())
            
            # Convert step dictionaries to WorkflowStep objects
            workflow_steps = []
            for step_data in steps:
                step = WorkflowStep(
                    step_id=step_data.get('step_id', str(uuid.uuid4())),
                    step_type=step_data['step_type'],
                    title=step_data['title'],
                    parameters=step_data.get('parameters', {}),
                    dependencies=step_data.get('dependencies', []),
                    timeout=step_data.get('timeout'),
                    max_retries=step_data.get('max_retries', 3),
                    condition=step_data.get('condition')
                )
                workflow_steps.append(step)
            
            # Validate trigger configuration
            if trigger == WorkflowTrigger.SCHEDULE:
                if 'cron' not in trigger_config:
                    return {"success": False, "error": "Schedule trigger requires 'cron' in trigger_config"}
                # Validate cron expression
                try:
                    croniter.croniter(trigger_config['cron'])
                except Exception as e:
                    return {"success": False, "error": f"Invalid cron expression: {e}"}
            
            workflow = Workflow(
                workflow_id=workflow_id,
                name=name,
                description=description,
                trigger=trigger,
                trigger_config=trigger_config,
                steps=workflow_steps,
                tags=tags or []
            )
            
            # Calculate next run if scheduled
            if trigger == WorkflowTrigger.SCHEDULE:
                workflow.next_run = self._calculate_next_run(trigger_config['cron'])
            
            self.workflows[workflow_id] = workflow
            self.stats['workflows_created'] += 1
            
            # Save workflow
            self._save_workflow(workflow)
            
            logger.info(f"📋 Workflow created: {name} ({workflow_id})")
            return {
                "success": True,
                "workflow_id": workflow_id,
                "message": f"Workflow '{name}' created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_workflow(self, workflow_id: str, trigger_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a workflow manually"""
        if workflow_id not in self.workflows:
            return {"success": False, "error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        
        if not workflow.enabled:
            return {"success": False, "error": "Workflow is disabled"}
        
        try:
            execution_id = str(uuid.uuid4())
            
            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_id=workflow_id,
                trigger_data=trigger_data or {}
            )
            
            self.executions[execution_id] = execution
            
            # Submit execution as background job
            job_result = background_service.submit_job(
                job_type="workflow_execution",
                title=f"Execute Workflow: {workflow.name}",
                description=f"Execute workflow {workflow.name} ({workflow_id})",
                parameters={
                    'execution_id': execution_id,
                    'workflow_id': workflow_id,
                    'trigger_data': trigger_data or {}
                },
                priority=JobPriority.NORMAL,
                tags=['workflow', 'automation']
            )
            
            if not job_result['success']:
                return job_result
            
            execution.status = "queued"
            workflow.run_count += 1
            
            logger.info(f"🏃 Workflow execution queued: {workflow.name} ({execution_id})")
            return {
                "success": True,
                "execution_id": execution_id,
                "job_id": job_result['job_id'],
                "message": f"Workflow execution queued"
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return {"success": False, "error": str(e)}
    
    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow details"""
        if workflow_id not in self.workflows:
            return {"success": False, "error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        return {
            "success": True,
            "workflow": workflow.to_dict()
        }
    
    def get_all_workflows(self, include_disabled: bool = True) -> Dict[str, Any]:
        """Get all workflows"""
        workflows = list(self.workflows.values())
        
        if not include_disabled:
            workflows = [w for w in workflows if w.enabled]
        
        return {
            "success": True,
            "workflows": [w.to_dict() for w in workflows],
            "total": len(workflows)
        }
    
    def enable_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Enable a workflow"""
        if workflow_id not in self.workflows:
            return {"success": False, "error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        workflow.enabled = True
        workflow.status = WorkflowStatus.ACTIVE
        
        # Calculate next run if scheduled
        if workflow.trigger == WorkflowTrigger.SCHEDULE:
            workflow.next_run = self._calculate_next_run(workflow.trigger_config['cron'])
        
        self._save_workflow(workflow)
        
        logger.info(f"✅ Workflow enabled: {workflow.name}")
        return {"success": True, "message": "Workflow enabled"}
    
    def disable_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Disable a workflow"""
        if workflow_id not in self.workflows:
            return {"success": False, "error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        workflow.enabled = False
        workflow.status = WorkflowStatus.INACTIVE
        workflow.next_run = None
        
        self._save_workflow(workflow)
        
        logger.info(f"❌ Workflow disabled: {workflow.name}")
        return {"success": True, "message": "Workflow disabled"}
    
    def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete a workflow"""
        if workflow_id not in self.workflows:
            return {"success": False, "error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        
        # Remove from database
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM workflows WHERE workflow_id = ?', (workflow_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error deleting workflow from database: {e}")
        
        # Remove from memory
        del self.workflows[workflow_id]
        
        logger.info(f"🗑️ Workflow deleted: {workflow.name}")
        return {"success": True, "message": "Workflow deleted"}
    
    def get_workflow_executions(self, workflow_id: str = None, limit: int = 50) -> Dict[str, Any]:
        """Get workflow execution history"""
        executions = list(self.executions.values())
        
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        
        # Sort by start time desc
        executions.sort(key=lambda x: x.started_at or datetime.min, reverse=True)
        executions = executions[:limit]
        
        return {
            "success": True,
            "executions": [asdict(e) for e in executions],
            "total": len(executions)
        }
    
    def register_step_handler(self, step_type: str, handler: Callable):
        """Register a handler for a specific step type"""
        self.step_handlers[step_type] = handler
        logger.info(f"📝 Registered step handler for: {step_type}")
    
    def add_event_listener(self, event_type: str, callback: Callable):
        """Add an event listener"""
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        self.event_listeners[event_type].append(callback)
        logger.info(f"👂 Added event listener for: {event_type}")
    
    def trigger_event(self, event_type: str, event_data: Dict[str, Any]):
        """Trigger an event that may start workflows"""
        logger.info(f"🔔 Event triggered: {event_type}")
        
        # Find workflows triggered by this event
        for workflow in self.workflows.values():
            if (workflow.enabled and 
                workflow.trigger == WorkflowTrigger.EVENT and 
                workflow.trigger_config.get('event_type') == event_type):
                
                # Check event conditions if specified
                conditions = workflow.trigger_config.get('conditions', {})
                if self._check_event_conditions(event_data, conditions):
                    logger.info(f"🏃 Triggering workflow: {workflow.name}")
                    self.execute_workflow(workflow.workflow_id, {'event_type': event_type, 'event_data': event_data})
        
        # Call event listeners
        if event_type in self.event_listeners:
            for callback in self.event_listeners[event_type]:
                try:
                    callback(event_data)
                except Exception as e:
                    logger.error(f"Event listener error: {e}")
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        stats = self.stats.copy()
        
        # Add current state
        stats.update({
            'is_running': self.is_running,
            'total_workflows': len(self.workflows),
            'enabled_workflows': len([w for w in self.workflows.values() if w.enabled]),
            'scheduled_workflows': len([w for w in self.workflows.values() if w.trigger == WorkflowTrigger.SCHEDULE and w.enabled]),
            'active_executions': len([e for e in self.executions.values() if e.status in ['pending', 'running']]),
            'total_executions': len(self.executions)
        })
        
        # Runtime
        if stats['start_time']:
            runtime = datetime.now() - stats['start_time']
            stats['runtime_seconds'] = runtime.total_seconds()
            stats['runtime_formatted'] = str(runtime).split('.')[0]
        
        # Next scheduled workflows
        scheduled_workflows = []
        for workflow in self.workflows.values():
            if workflow.enabled and workflow.next_run:
                scheduled_workflows.append({
                    'workflow_id': workflow.workflow_id,
                    'name': workflow.name,
                    'next_run': workflow.next_run.isoformat()
                })
        
        # Sort by next run time
        scheduled_workflows.sort(key=lambda x: x['next_run'])
        stats['next_scheduled'] = scheduled_workflows[:10]  # Next 10
        
        return stats
    
    def _scheduler_worker(self):
        """Main scheduler worker thread"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check for workflows that need to run
                for workflow in self.workflows.values():
                    if (workflow.enabled and 
                        workflow.trigger == WorkflowTrigger.SCHEDULE and 
                        workflow.next_run and 
                        workflow.next_run <= current_time):
                        
                        # Execute the workflow
                        logger.info(f"⏰ Scheduled execution: {workflow.name}")
                        result = self.execute_workflow(workflow.workflow_id)
                        
                        if result['success']:
                            # Calculate next run
                            workflow.next_run = self._calculate_next_run(workflow.trigger_config['cron'])
                            workflow.last_run = current_time
                            self._save_workflow(workflow)
                        else:
                            logger.error(f"Failed to execute scheduled workflow: {result.get('error', 'Unknown error')}")
                
                # Sleep for check interval
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Scheduler worker error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _calculate_next_run(self, cron_expression: str) -> datetime:
        """Calculate next run time from cron expression"""
        try:
            cron = croniter.croniter(cron_expression, datetime.now())
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"Error calculating next run: {e}")
            # Default to 1 hour from now
            return datetime.now() + timedelta(hours=1)
    
    def _calculate_next_runs(self):
        """Calculate next run times for all scheduled workflows"""
        for workflow in self.workflows.values():
            if (workflow.enabled and 
                workflow.trigger == WorkflowTrigger.SCHEDULE and 
                'cron' in workflow.trigger_config):
                workflow.next_run = self._calculate_next_run(workflow.trigger_config['cron'])
    
    def _check_event_conditions(self, event_data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """Check if event data meets workflow trigger conditions"""
        try:
            for key, expected_value in conditions.items():
                if key not in event_data:
                    return False
                if event_data[key] != expected_value:
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking event conditions: {e}")
            return False
    
    def _register_builtin_handlers(self):
        """Register built-in step handlers"""
        
        # Workflow execution handler
        def workflow_execution_handler(parameters, progress_callback):
            execution_id = parameters['execution_id']
            workflow_id = parameters['workflow_id']
            
            if execution_id not in self.executions:
                raise Exception("Execution not found")
            
            if workflow_id not in self.workflows:
                raise Exception("Workflow not found")
            
            execution = self.executions[execution_id]
            workflow = self.workflows[workflow_id]
            
            try:
                execution.status = "running"
                execution.started_at = datetime.now()
                
                progress_callback(0, len(workflow.steps), "Starting workflow execution")
                
                # Execute steps in order
                for i, step in enumerate(workflow.steps):
                    progress_callback(i, len(workflow.steps), f"Executing step: {step.title}")
                    
                    # Check dependencies
                    if not self._check_step_dependencies(step, execution.step_results):
                        continue
                    
                    # Check condition
                    if step.condition and not self._evaluate_condition(step.condition, execution.step_results):
                        execution.step_results[step.step_id] = {"skipped": True, "reason": "Condition not met"}
                        continue
                    
                    # Execute step
                    step_result = self._execute_step(step, execution.step_results)
                    execution.step_results[step.step_id] = step_result
                    
                    if not step_result.get('success', False):
                        raise Exception(f"Step {step.title} failed: {step_result.get('error', 'Unknown error')}")
                
                # Workflow completed successfully
                execution.status = "completed"
                execution.completed_at = datetime.now()
                workflow.success_count += 1
                
                progress_callback(len(workflow.steps), len(workflow.steps), "Workflow completed successfully")
                
                return {
                    "success": True,
                    "execution_id": execution_id,
                    "results": execution.step_results
                }
                
            except Exception as e:
                execution.status = "failed"
                execution.error = str(e)
                execution.completed_at = datetime.now()
                workflow.failure_count += 1
                
                logger.error(f"Workflow execution failed: {e}")
                raise e
        
        background_service.register_job_handler("workflow_execution", workflow_execution_handler)
        
        # Repository discovery step
        def repository_discovery_step(parameters, progress_callback):
            progress_callback(0, 100, "Starting repository discovery")
            
            source = parameters.get('source', 'database')
            result = automated_processor.discover_repositories(source)
            
            progress_callback(100, 100, "Repository discovery completed")
            return result
        
        self.register_step_handler("repository_discovery", repository_discovery_step)
        
        # Repository processing step
        def repository_processing_step(parameters, progress_callback):
            progress_callback(0, 100, "Starting repository processing")
            
            repo_filter = parameters.get('filter', {})
            batch_size = parameters.get('batch_size', 5)
            
            # Get repositories to process
            repos = self.db.get_table_data('knowledge_hub')
            github_repos = [r for r in repos if r.get('category', '').lower().find('repository') != -1]
            
            # Apply filters
            if 'language' in repo_filter:
                github_repos = [r for r in github_repos if r.get('github_language', '').lower() == repo_filter['language'].lower()]
            
            if 'min_stars' in repo_filter:
                github_repos = [r for r in github_repos if r.get('github_stars', 0) >= repo_filter['min_stars']]
            
            # Process repositories
            processed = 0
            for i, repo in enumerate(github_repos[:batch_size]):
                progress_callback(i, min(len(github_repos), batch_size), f"Processing {repo.get('title', 'Unknown')}")
                
                # Convert to repository format
                repository = {
                    'username': repo.get('github_owner', ''),
                    'repo_name': repo.get('github_repo', ''),
                    'full_name': f"{repo.get('github_owner', '')}/{repo.get('github_repo', '')}",
                    'description': repo.get('content', ''),
                    'language': repo.get('github_language', ''),
                    'stars': repo.get('github_stars', 0)
                }
                
                result = automated_processor.process_repository_automated(repository)
                if result.get('success', False):
                    processed += 1
            
            progress_callback(batch_size, batch_size, f"Repository processing completed: {processed} processed")
            return {"success": True, "processed": processed, "total": len(github_repos)}
        
        self.register_step_handler("repository_processing", repository_processing_step)
        
        # GitHub monitoring step
        def github_monitoring_step(parameters, progress_callback):
            progress_callback(0, 100, "Starting GitHub monitoring")
            
            # Get repositories to monitor
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
            
            # Monitor for updates
            result = github_api.monitor_repository_updates(github_repos)
            
            progress_callback(100, 100, f"GitHub monitoring completed: {result.get('updates_found', 0)} updates found")
            return result
        
        self.register_step_handler("github_monitoring", github_monitoring_step)
        
        # Health check step
        def health_check_step(parameters, progress_callback):
            progress_callback(0, 100, "Running health checks")
            
            # Get repositories for health check
            repos = self.db.get_table_data('knowledge_hub')
            github_repos = []
            
            for repo in repos:
                if (repo.get('category', '').lower().find('repository') != -1 and 
                    repo.get('github_owner') and repo.get('github_repo')):
                    github_repos.append({
                        'owner': repo['github_owner'],
                        'name': repo['github_repo']
                    })
            
            # Perform health checks
            result = github_api.health_check_repositories(github_repos)
            
            progress_callback(100, 100, f"Health checks completed: {result.get('healthy', 0)} healthy repos")
            return result
        
        self.register_step_handler("health_check", health_check_step)
    
    def _execute_step(self, step: WorkflowStep, previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        if step.step_type not in self.step_handlers:
            return {"success": False, "error": f"Unknown step type: {step.step_type}"}
        
        try:
            handler = self.step_handlers[step.step_type]
            
            # Prepare parameters with context
            parameters = step.parameters.copy()
            parameters['previous_results'] = previous_results
            parameters['step_id'] = step.step_id
            
            # Execute with timeout if specified
            if step.timeout:
                # TODO: Implement timeout handling
                pass
            
            # Simple progress callback for steps
            def step_progress(current, total, message):
                logger.debug(f"Step {step.title}: {message} ({current}/{total})")
            
            result = handler(parameters, step_progress)
            
            return {
                "success": True,
                "result": result,
                "step_id": step.step_id,
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "step_id": step.step_id
            }
    
    def _check_step_dependencies(self, step: WorkflowStep, results: Dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied"""
        for dep_id in step.dependencies:
            if dep_id not in results:
                return False
            if not results[dep_id].get('success', False):
                return False
        return True
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition expression"""
        try:
            # Simple condition evaluation (could be enhanced with a proper expression evaluator)
            # For now, just check basic conditions
            return True  # TODO: Implement proper condition evaluation
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    def _create_default_workflows(self):
        """Create default automation workflows"""
        
        # Daily repository discovery workflow
        discovery_workflow = {
            "name": "Daily Repository Discovery",
            "description": "Automatically discover new repositories from GitHub users daily",
            "trigger": WorkflowTrigger.SCHEDULE,
            "trigger_config": {"cron": "0 9 * * *"},  # Daily at 9 AM
            "steps": [
                {
                    "step_type": "repository_discovery",
                    "title": "Discover New Repositories",
                    "parameters": {"source": "database"}
                },
                {
                    "step_type": "repository_processing",
                    "title": "Process New Repositories",
                    "parameters": {"batch_size": 5, "filter": {"min_stars": 1}},
                    "dependencies": ["repository_discovery"]
                }
            ],
            "tags": ["daily", "discovery", "automation"]
        }
        
        try:
            result = self.create_workflow(**discovery_workflow)
            if result['success']:
                logger.info("✅ Created default discovery workflow")
        except Exception as e:
            logger.error(f"Error creating default discovery workflow: {e}")
        
        # Weekly repository monitoring workflow
        monitoring_workflow = {
            "name": "Weekly Repository Monitoring",
            "description": "Monitor all repositories for updates and health weekly",
            "trigger": WorkflowTrigger.SCHEDULE,
            "trigger_config": {"cron": "0 10 * * 1"},  # Weekly on Monday at 10 AM
            "steps": [
                {
                    "step_type": "github_monitoring",
                    "title": "Monitor Repository Updates",
                    "parameters": {}
                },
                {
                    "step_type": "health_check",
                    "title": "Repository Health Check",
                    "parameters": {},
                    "dependencies": ["github_monitoring"]
                }
            ],
            "tags": ["weekly", "monitoring", "health"]
        }
        
        try:
            result = self.create_workflow(**monitoring_workflow)
            if result['success']:
                logger.info("✅ Created default monitoring workflow")
        except Exception as e:
            logger.error(f"Error creating default monitoring workflow: {e}")
    
    def _init_workflow_storage(self):
        """Initialize workflow storage in database"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id TEXT PRIMARY KEY,
                    workflow_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    execution_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    execution_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows (workflow_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("📊 Workflow storage initialized")
            
        except Exception as e:
            logger.error(f"Error initializing workflow storage: {e}")
    
    def _save_workflow(self, workflow: Workflow):
        """Save workflow to persistent storage"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            workflow_data = json.dumps(workflow.to_dict())
            
            cursor.execute('''
                INSERT OR REPLACE INTO workflows (workflow_id, workflow_data, updated_at)
                VALUES (?, ?, ?)
            ''', (workflow.workflow_id, workflow_data, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving workflow {workflow.workflow_id}: {e}")
    
    def _save_workflows(self):
        """Save all workflows to persistent storage"""
        for workflow in self.workflows.values():
            self._save_workflow(workflow)
    
    def _load_workflows(self):
        """Load workflows from persistent storage"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT workflow_data FROM workflows')
            rows = cursor.fetchall()
            
            for (workflow_data,) in rows:
                data = json.loads(workflow_data)
                
                # Convert back to enums and objects
                workflow = Workflow(
                    workflow_id=data['workflow_id'],
                    name=data['name'],
                    description=data['description'],
                    trigger=WorkflowTrigger(data['trigger']),
                    trigger_config=data['trigger_config'],
                    steps=[],  # Will be populated below
                    status=WorkflowStatus(data['status']),
                    run_count=data.get('run_count', 0),
                    success_count=data.get('success_count', 0),
                    failure_count=data.get('failure_count', 0),
                    tags=data.get('tags', []),
                    enabled=data.get('enabled', True)
                )
                
                # Convert datetime fields
                for field in ['created_at', 'last_run', 'next_run']:
                    if data.get(field):
                        setattr(workflow, field, datetime.fromisoformat(data[field]))
                
                # Convert steps
                for step_data in data.get('steps', []):
                    step = WorkflowStep(
                        step_id=step_data['step_id'],
                        step_type=step_data['step_type'],
                        title=step_data['title'],
                        parameters=step_data['parameters'],
                        dependencies=step_data.get('dependencies', []),
                        timeout=step_data.get('timeout'),
                        max_retries=step_data.get('max_retries', 3),
                        condition=step_data.get('condition')
                    )
                    workflow.steps.append(step)
                
                self.workflows[workflow.workflow_id] = workflow
            
            conn.close()
            logger.info(f"📥 Loaded {len(rows)} workflows from storage")
            
        except Exception as e:
            logger.error(f"Error loading workflows: {e}")

# Global instance
workflow_scheduler = WorkflowAutomationScheduler()