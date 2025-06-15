#!/usr/bin/env python3
"""
Background Processing Service
Handles long-running operations with progress tracking and notifications
"""

import asyncio
import logging
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
from pathlib import Path
from queue import Queue, PriorityQueue, Empty
from concurrent.futures import ThreadPoolExecutor, Future
import sqlite3

from database import NotionLikeDatabase

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class JobPriority(Enum):
    """Job priority levels"""
    LOW = 5
    NORMAL = 3
    HIGH = 1
    URGENT = 0

@dataclass
class JobProgress:
    """Progress tracking for a job"""
    current: int = 0
    total: int = 100
    message: str = ""
    details: Dict[str, Any] = None
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    @property
    def percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100.0
    
    def update(self, current: int = None, total: int = None, message: str = None, details: Dict[str, Any] = None):
        """Update progress"""
        if current is not None:
            self.current = current
        if total is not None:
            self.total = total
        if message is not None:
            self.message = message
        if details is not None:
            self.details.update(details)
        self.updated_at = datetime.now()

@dataclass
class BackgroundJob:
    """Represents a background job"""
    job_id: str
    job_type: str
    title: str
    description: str
    parameters: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    progress: JobProgress = None
    result: Any = None
    error: str = ""
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # seconds
    max_retries: int = 3
    retry_count: int = 0
    tags: List[str] = None
    callback_url: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.progress is None:
            self.progress = JobProgress()
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.tags is None:
            self.tags = []
        if self.dependencies is None:
            self.dependencies = []
    
    @property
    def elapsed_time(self) -> Optional[timedelta]:
        """Get elapsed time since job started"""
        if self.started_at:
            end_time = self.completed_at or datetime.now()
            return end_time - self.started_at
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if job is active (running or pending)"""
        return self.status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums to strings
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'started_at', 'completed_at']:
            if data[field]:
                data[field] = data[field].isoformat()
        # Convert progress
        data['progress'] = asdict(self.progress)
        if data['progress']['started_at']:
            data['progress']['started_at'] = data['progress']['started_at'].isoformat()
        if data['progress']['updated_at']:
            data['progress']['updated_at'] = data['progress']['updated_at'].isoformat()
        return data

class BackgroundProcessingService:
    """Service for managing background jobs with progress tracking"""
    
    def __init__(self):
        self.db = NotionLikeDatabase()
        
        # Job management
        self.jobs: Dict[str, BackgroundJob] = {}
        self.job_queue = PriorityQueue()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.futures: Dict[str, Future] = {}
        
        # Service state
        self.is_running = False
        self.worker_threads = []
        self.max_concurrent_jobs = 3
        self.current_jobs = 0
        
        # Progress tracking
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        self.completion_callbacks: Dict[str, List[Callable]] = {}
        
        # Job types and handlers
        self.job_handlers = {}
        self.job_estimators = {}
        
        # Persistence
        self._init_job_storage()
        
        # Statistics
        self.stats = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'start_time': None,
            'average_job_time': 0
        }
        
        logger.info("🔄 Background Processing Service initialized")
    
    def start_service(self) -> Dict[str, Any]:
        """Start the background processing service"""
        if self.is_running:
            return {"success": False, "error": "Service already running"}
        
        try:
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            
            # Start worker threads
            for i in range(2):  # Main worker and monitor worker
                if i == 0:
                    worker = threading.Thread(target=self._job_worker, daemon=True)
                else:
                    worker = threading.Thread(target=self._monitor_worker, daemon=True)
                worker.start()
                self.worker_threads.append(worker)
            
            # Load existing jobs
            self._load_jobs()
            
            logger.info("🚀 Background Processing Service started")
            return {
                "success": True,
                "message": "Background processing service started",
                "workers": len(self.worker_threads),
                "max_concurrent": self.max_concurrent_jobs
            }
            
        except Exception as e:
            logger.error(f"Error starting background service: {e}")
            self.is_running = False
            return {"success": False, "error": str(e)}
    
    def stop_service(self) -> Dict[str, Any]:
        """Stop the background processing service"""
        if not self.is_running:
            return {"success": False, "error": "Service not running"}
        
        try:
            self.is_running = False
            
            # Cancel running jobs
            for job_id, future in self.futures.items():
                if not future.done():
                    future.cancel()
                    if job_id in self.jobs:
                        self.jobs[job_id].status = JobStatus.CANCELLED
            
            # Wait for workers to finish
            for thread in self.worker_threads:
                thread.join(timeout=10)
            
            self.worker_threads.clear()
            
            # Save job states
            self._save_jobs()
            
            logger.info("🛑 Background Processing Service stopped")
            return {
                "success": True,
                "message": "Background processing service stopped",
                "final_stats": self.get_service_stats()
            }
            
        except Exception as e:
            logger.error(f"Error stopping background service: {e}")
            return {"success": False, "error": str(e)}
    
    def submit_job(self, job_type: str, title: str, description: str, 
                   parameters: Dict[str, Any], priority: JobPriority = JobPriority.NORMAL,
                   tags: List[str] = None, dependencies: List[str] = None,
                   estimated_duration: int = None) -> Dict[str, Any]:
        """Submit a new background job"""
        try:
            job_id = str(uuid.uuid4())
            
            job = BackgroundJob(
                job_id=job_id,
                job_type=job_type,
                title=title,
                description=description,
                parameters=parameters,
                priority=priority,
                tags=tags or [],
                dependencies=dependencies or [],
                estimated_duration=estimated_duration
            )
            
            # Validate job type
            if job_type not in self.job_handlers:
                return {"success": False, "error": f"Unknown job type: {job_type}"}
            
            # Check dependencies
            if dependencies:
                for dep_id in dependencies:
                    if dep_id not in self.jobs:
                        return {"success": False, "error": f"Dependency job not found: {dep_id}"}
                    if self.jobs[dep_id].status not in [JobStatus.COMPLETED]:
                        return {"success": False, "error": f"Dependency job not completed: {dep_id}"}
            
            # Estimate duration if not provided
            if estimated_duration is None and job_type in self.job_estimators:
                job.estimated_duration = self.job_estimators[job_type](parameters)
            
            # Store job
            self.jobs[job_id] = job
            
            # Add to queue
            self.job_queue.put((priority.value, job_id))
            
            # Update stats
            self.stats['total_jobs'] += 1
            
            # Save job
            self._save_job(job)
            
            logger.info(f"📋 Job submitted: {title} ({job_id})")
            return {
                "success": True,
                "job_id": job_id,
                "message": f"Job '{title}' submitted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error submitting job: {e}")
            return {"success": False, "error": str(e)}
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a specific job"""
        if job_id not in self.jobs:
            return {"success": False, "error": "Job not found"}
        
        job = self.jobs[job_id]
        return {
            "success": True,
            "job": job.to_dict()
        }
    
    def get_all_jobs(self, status_filter: Optional[JobStatus] = None, 
                     type_filter: Optional[str] = None,
                     limit: int = 100) -> Dict[str, Any]:
        """Get all jobs with optional filtering"""
        try:
            jobs = list(self.jobs.values())
            
            # Apply filters
            if status_filter:
                jobs = [job for job in jobs if job.status == status_filter]
            
            if type_filter:
                jobs = [job for job in jobs if job.job_type == type_filter]
            
            # Sort by created_at desc
            jobs.sort(key=lambda x: x.created_at, reverse=True)
            
            # Limit results
            jobs = jobs[:limit]
            
            return {
                "success": True,
                "jobs": [job.to_dict() for job in jobs],
                "total": len(jobs)
            }
            
        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return {"success": False, "error": str(e)}
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running or pending job"""
        if job_id not in self.jobs:
            return {"success": False, "error": "Job not found"}
        
        job = self.jobs[job_id]
        
        if job.status == JobStatus.COMPLETED:
            return {"success": False, "error": "Job already completed"}
        
        if job.status == JobStatus.CANCELLED:
            return {"success": False, "error": "Job already cancelled"}
        
        try:
            # Cancel future if running
            if job_id in self.futures:
                self.futures[job_id].cancel()
            
            # Update job status
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            job.progress.message = "Job cancelled"
            
            # Save job
            self._save_job(job)
            
            logger.info(f"❌ Job cancelled: {job.title} ({job_id})")
            return {"success": True, "message": "Job cancelled successfully"}
            
        except Exception as e:
            logger.error(f"Error cancelling job: {e}")
            return {"success": False, "error": str(e)}
    
    def retry_job(self, job_id: str) -> Dict[str, Any]:
        """Retry a failed job"""
        if job_id not in self.jobs:
            return {"success": False, "error": "Job not found"}
        
        job = self.jobs[job_id]
        
        if job.status != JobStatus.FAILED:
            return {"success": False, "error": "Job is not in failed state"}
        
        if job.retry_count >= job.max_retries:
            return {"success": False, "error": "Maximum retries exceeded"}
        
        try:
            # Reset job state
            job.status = JobStatus.PENDING
            job.error = ""
            job.started_at = None
            job.completed_at = None
            job.retry_count += 1
            job.progress = JobProgress()
            
            # Re-add to queue
            self.job_queue.put((job.priority.value, job_id))
            
            # Save job
            self._save_job(job)
            
            logger.info(f"🔄 Job retry: {job.title} ({job_id}) - Attempt {job.retry_count}")
            return {"success": True, "message": f"Job retry initiated (attempt {job.retry_count})"}
            
        except Exception as e:
            logger.error(f"Error retrying job: {e}")
            return {"success": False, "error": str(e)}
    
    def register_job_handler(self, job_type: str, handler: Callable, estimator: Callable = None):
        """Register a handler for a specific job type"""
        self.job_handlers[job_type] = handler
        if estimator:
            self.job_estimators[job_type] = estimator
        logger.info(f"📝 Registered handler for job type: {job_type}")
    
    def add_progress_callback(self, job_id: str, callback: Callable):
        """Add a progress callback for a specific job"""
        if job_id not in self.progress_callbacks:
            self.progress_callbacks[job_id] = []
        self.progress_callbacks[job_id].append(callback)
    
    def add_completion_callback(self, job_id: str, callback: Callable):
        """Add a completion callback for a specific job"""
        if job_id not in self.completion_callbacks:
            self.completion_callbacks[job_id] = []
        self.completion_callbacks[job_id].append(callback)
    
    def update_job_progress(self, job_id: str, current: int = None, total: int = None, 
                           message: str = None, details: Dict[str, Any] = None):
        """Update progress for a specific job"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.progress.update(current, total, message, details)
            
            # Call progress callbacks
            if job_id in self.progress_callbacks:
                for callback in self.progress_callbacks[job_id]:
                    try:
                        callback(job)
                    except Exception as e:
                        logger.error(f"Progress callback error: {e}")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        stats = self.stats.copy()
        
        # Add current state
        stats.update({
            'is_running': self.is_running,
            'current_jobs': self.current_jobs,
            'max_concurrent': self.max_concurrent_jobs,
            'queue_size': self.job_queue.qsize(),
            'total_stored_jobs': len(self.jobs),
            'worker_threads': len(self.worker_threads)
        })
        
        # Add job status breakdown
        status_counts = {}
        for job in self.jobs.values():
            status = job.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        stats['job_status_breakdown'] = status_counts
        
        # Runtime
        if stats['start_time']:
            runtime = datetime.now() - stats['start_time']
            stats['runtime_seconds'] = runtime.total_seconds()
            stats['runtime_formatted'] = str(runtime).split('.')[0]
        
        return stats
    
    def _job_worker(self):
        """Main worker thread for executing jobs"""
        while self.is_running:
            try:
                # Get job from queue
                priority, job_id = self.job_queue.get(timeout=30)
                
                if job_id not in self.jobs:
                    continue
                
                job = self.jobs[job_id]
                
                # Check if we can run more jobs
                if self.current_jobs >= self.max_concurrent_jobs:
                    # Put job back in queue
                    self.job_queue.put((priority, job_id))
                    time.sleep(1)
                    continue
                
                # Execute job
                self._execute_job(job)
                
            except Empty:
                continue  # Timeout, check if still running
            except Exception as e:
                logger.error(f"Job worker error: {e}")
                time.sleep(5)
    
    def _execute_job(self, job: BackgroundJob):
        """Execute a specific job"""
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            job.progress.started_at = job.started_at
            job.progress.message = "Job started"
            
            self.current_jobs += 1
            
            # Get handler
            handler = self.job_handlers.get(job.job_type)
            if not handler:
                raise Exception(f"No handler found for job type: {job.job_type}")
            
            logger.info(f"🏃 Executing job: {job.title} ({job.job_id})")
            
            # Create progress updater
            def progress_updater(current, total=None, message=None, details=None):
                self.update_job_progress(job.job_id, current, total, message, details)
            
            # Execute handler
            future = self.executor.submit(handler, job.parameters, progress_updater)
            self.futures[job.job_id] = future
            
            # Wait for completion
            try:
                result = future.result()
                
                # Job completed successfully
                job.status = JobStatus.COMPLETED
                job.result = result
                job.completed_at = datetime.now()
                job.progress.current = job.progress.total
                job.progress.message = "Job completed successfully"
                
                self.stats['completed_jobs'] += 1
                
                logger.info(f"✅ Job completed: {job.title} ({job.job_id})")
                
            except Exception as e:
                # Job failed
                job.status = JobStatus.FAILED
                job.error = str(e)
                job.completed_at = datetime.now()
                job.progress.message = f"Job failed: {str(e)}"
                
                self.stats['failed_jobs'] += 1
                
                logger.error(f"❌ Job failed: {job.title} ({job.job_id}) - {e}")
                
                # Auto-retry if possible
                if job.retry_count < job.max_retries:
                    logger.info(f"🔄 Auto-retrying job: {job.title} ({job.job_id})")
                    self.retry_job(job.job_id)
            
            finally:
                # Cleanup
                self.current_jobs -= 1
                if job.job_id in self.futures:
                    del self.futures[job.job_id]
                
                # Save job
                self._save_job(job)
                
                # Call completion callbacks
                if job.job_id in self.completion_callbacks:
                    for callback in self.completion_callbacks[job.job_id]:
                        try:
                            callback(job)
                        except Exception as e:
                            logger.error(f"Completion callback error: {e}")
                
                # Update average job time
                if job.elapsed_time:
                    total_time = self.stats['average_job_time'] * self.stats['completed_jobs']
                    total_time += job.elapsed_time.total_seconds()
                    self.stats['average_job_time'] = total_time / (self.stats['completed_jobs'] + self.stats['failed_jobs'])
                
        except Exception as e:
            logger.error(f"Error executing job {job.job_id}: {e}")
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()
            self.current_jobs -= 1
    
    def _monitor_worker(self):
        """Monitor worker for cleanup and maintenance"""
        while self.is_running:
            try:
                # Clean up old completed jobs (older than 7 days)
                cutoff_date = datetime.now() - timedelta(days=7)
                jobs_to_remove = []
                
                for job_id, job in self.jobs.items():
                    if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and 
                        job.completed_at and job.completed_at < cutoff_date):
                        jobs_to_remove.append(job_id)
                
                for job_id in jobs_to_remove:
                    del self.jobs[job_id]
                    logger.debug(f"🗑️ Cleaned up old job: {job_id}")
                
                # Monitor for stuck jobs
                for job in self.jobs.values():
                    if (job.status == JobStatus.RUNNING and job.started_at and 
                        datetime.now() - job.started_at > timedelta(hours=2)):
                        logger.warning(f"⚠️ Long-running job detected: {job.title} ({job.job_id})")
                
                time.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Monitor worker error: {e}")
                time.sleep(60)
    
    def _init_job_storage(self):
        """Initialize job storage in database"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS background_jobs (
                    job_id TEXT PRIMARY KEY,
                    job_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("📊 Job storage initialized")
            
        except Exception as e:
            logger.error(f"Error initializing job storage: {e}")
    
    def _save_job(self, job: BackgroundJob):
        """Save job to persistent storage"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            job_data = json.dumps(job.to_dict())
            
            cursor.execute('''
                INSERT OR REPLACE INTO background_jobs (job_id, job_data, updated_at)
                VALUES (?, ?, ?)
            ''', (job.job_id, job_data, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving job {job.job_id}: {e}")
    
    def _load_jobs(self):
        """Load jobs from persistent storage"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT job_data FROM background_jobs')
            rows = cursor.fetchall()
            
            for (job_data,) in rows:
                data = json.loads(job_data)
                
                # Convert back to enums and datetime objects
                job = BackgroundJob(
                    job_id=data['job_id'],
                    job_type=data['job_type'],
                    title=data['title'],
                    description=data['description'],
                    parameters=data['parameters'],
                    priority=JobPriority(data['priority']),
                    status=JobStatus(data['status']),
                    result=data.get('result'),
                    error=data.get('error', ''),
                    max_retries=data.get('max_retries', 3),
                    retry_count=data.get('retry_count', 0),
                    tags=data.get('tags', []),
                    dependencies=data.get('dependencies', []),
                    estimated_duration=data.get('estimated_duration')
                )
                
                # Convert datetime fields
                for field in ['created_at', 'started_at', 'completed_at']:
                    if data.get(field):
                        setattr(job, field, datetime.fromisoformat(data[field]))
                
                # Convert progress
                if data.get('progress'):
                    progress_data = data['progress']
                    job.progress = JobProgress(
                        current=progress_data.get('current', 0),
                        total=progress_data.get('total', 100),
                        message=progress_data.get('message', ''),
                        details=progress_data.get('details', {})
                    )
                    
                    for field in ['started_at', 'updated_at']:
                        if progress_data.get(field):
                            setattr(job.progress, field, datetime.fromisoformat(progress_data[field]))
                
                self.jobs[job.job_id] = job
                
                # Re-queue pending jobs
                if job.status == JobStatus.PENDING:
                    self.job_queue.put((job.priority.value, job.job_id))
            
            conn.close()
            logger.info(f"📥 Loaded {len(rows)} jobs from storage")
            
        except Exception as e:
            logger.error(f"Error loading jobs: {e}")
    
    def _save_jobs(self):
        """Save all jobs to persistent storage"""
        for job in self.jobs.values():
            self._save_job(job)

# Global instance
background_service = BackgroundProcessingService()