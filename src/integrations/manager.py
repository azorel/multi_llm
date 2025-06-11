"""
Unified integration manager for coordinating all external service integrations.

This module provides a centralized interface for managing Notion, GitHub, and other
external integrations with unified error handling, retry logic, and configuration management.
"""

import asyncio
import json
import time
import uuid
import os
from typing import Dict, List, Any, Optional, Union, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import sqlite3
from pathlib import Path
from loguru import logger
import threading


class IntegrationStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    OFFLINE = "offline"
    ERROR = "error"
    INITIALIZING = "initializing"


class IntegrationType(Enum):
# NOTION_REMOVED:     NOTION = "notion"
    GITHUB = "github"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    SEQUENTIAL_THINKING = "sequential_thinking"


class OperationType(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SYNC = "sync"
    HEALTH_CHECK = "health_check"


class RetryPolicy(Enum):
    IMMEDIATE = "immediate"
    LINEAR_BACKOFF = "linear_backoff"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class IntegrationConfig:
    """Configuration for a specific integration."""
    name: str
    enabled: bool
    priority: int  # 1-10, higher is more important
    timeout: float
    max_retries: int
    retry_policy: RetryPolicy
    health_check_interval: float
    circuit_breaker_threshold: int
    circuit_breaker_timeout: float
    authentication: Dict[str, Any]
    specific_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationResult:
    """Result of an integration operation."""
    operation_id: str
    integration_name: str
    operation_type: OperationType
    success: bool
    result_data: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class IntegrationHealth:
    """Health status of an integration."""
    integration_name: str
    status: IntegrationStatus
    last_successful_operation: Optional[datetime]
    last_error: Optional[str]
    success_rate: float
    average_response_time: float
    circuit_breaker_state: str
    total_operations: int
    failed_operations: int
    uptime_percentage: float


@dataclass
class ExternalService:
    """Represents an external service integration."""
    service_type: IntegrationType
    name: str
    config: IntegrationConfig
    health: IntegrationHealth
    last_health_check: Optional[datetime] = None
    
    
@dataclass
class ServiceHealth:
    """Overall health status of external services."""
    total_services: int
    healthy_services: int
    degraded_services: int
    offline_services: int
    error_services: int
    overall_status: IntegrationStatus
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class CircuitBreakerState:
    """Circuit breaker state for an integration."""
    is_open: bool = False
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    next_retry_time: Optional[datetime] = None
    total_failures: int = 0


class IntegrationManager:
    """Unified manager for all external integrations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.integrations: Dict[str, Any] = {}
        self.integration_configs: Dict[str, IntegrationConfig] = {}
        self.operation_history: deque = deque(maxlen=10000)
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.health_status: Dict[str, IntegrationHealth] = {}
        
        # Database for persistence
        self.db_path = config.get('database_path', 'integration_manager.db')
        
        # Monitoring and statistics
        self.statistics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.last_health_check: Dict[str, datetime] = {}
        
        # Threading and async
        self.manager_lock = threading.RLock()
        self.health_check_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Initialize database and load configurations
        self._initialize_database()
        self._load_integration_configs()
        
        logger.info("IntegrationManager initialized")
    
    def _initialize_database(self):
        """Initialize SQLite database for integration management."""
        conn = sqlite3.connect(self.db_path)
        
        # Operations history table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS operations (
                operation_id TEXT PRIMARY KEY,
                integration_name TEXT,
                operation_type TEXT,
                success INTEGER,
                result_data TEXT,
                error_message TEXT,
                execution_time REAL,
                retry_count INTEGER,
                timestamp TEXT
            )
        ''')
        
        # Health status table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS health_status (
                integration_name TEXT PRIMARY KEY,
                status TEXT,
                last_successful_operation TEXT,
                last_error TEXT,
                success_rate REAL,
                average_response_time REAL,
                circuit_breaker_state TEXT,
                total_operations INTEGER,
                failed_operations INTEGER,
                uptime_percentage REAL,
                updated_at TEXT
            )
        ''')
        
        # Configuration history table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS config_history (
                config_id TEXT PRIMARY KEY,
                integration_name TEXT,
                config_data TEXT,
                applied_at TEXT,
                applied_by TEXT
            )
        ''')
        
        # Sync operations queue
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sync_queue (
                sync_id TEXT PRIMARY KEY,
                integration_name TEXT,
                operation_data TEXT,
                priority INTEGER,
                scheduled_at TEXT,
                attempts INTEGER,
                status TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_integration_configs(self):
        """Load integration configurations from config."""
        integrations_config = self.config.get('integrations', {})
        
        for integration_name, config_data in integrations_config.items():
            try:
                integration_config = IntegrationConfig(
                    name=integration_name,
                    enabled=config_data.get('enabled', True),
                    priority=config_data.get('priority', 5),
                    timeout=config_data.get('timeout', 30.0),
                    max_retries=config_data.get('max_retries', 3),
                    retry_policy=RetryPolicy(config_data.get('retry_policy', 'exponential_backoff')),
                    health_check_interval=config_data.get('health_check_interval', 300.0),
                    circuit_breaker_threshold=config_data.get('circuit_breaker_threshold', 5),
                    circuit_breaker_timeout=config_data.get('circuit_breaker_timeout', 300.0),
                    authentication=config_data.get('authentication', {}),
                    specific_config=config_data.get('config', {})
                )
                
                self.integration_configs[integration_name] = integration_config
                self.circuit_breakers[integration_name] = CircuitBreakerState()
                
                # Initialize health status
                self.health_status[integration_name] = IntegrationHealth(
                    integration_name=integration_name,
                    status=IntegrationStatus.INITIALIZING,
                    last_successful_operation=None,
                    last_error=None,
                    success_rate=1.0,
                    average_response_time=0.0,
                    circuit_breaker_state="closed",
                    total_operations=0,
                    failed_operations=0,
                    uptime_percentage=100.0
                )
                
                logger.info(f"Loaded configuration for integration: {integration_name}")
                
            except Exception as e:
                logger.error(f"Failed to load config for {integration_name}: {e}")
    
    async def start(self):
        """Start the integration manager."""
        with self.manager_lock:
            if self.is_running:
                logger.warning("IntegrationManager already running")
                return
            
            self.is_running = True
            
            # Initialize all configured integrations
            await self._initialize_integrations()
            
            # Start health check monitoring
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info("IntegrationManager started successfully")
    
    async def stop(self):
        """Stop the integration manager."""
        with self.manager_lock:
            if not self.is_running:
                return
            
            self.is_running = False
            
            # Cancel health check task
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Cleanup all integrations
            await self._cleanup_integrations()
            
            logger.info("IntegrationManager stopped")
    
    async def _initialize_integrations(self):
        """Initialize all configured integrations."""
        for integration_name, config in self.integration_configs.items():
            if not config.enabled:
                logger.info(f"Skipping disabled integration: {integration_name}")
                continue
            
            try:
                await self._initialize_integration(integration_name, config)
            except Exception as e:
                logger.error(f"Failed to initialize {integration_name}: {e}")
                self.health_status[integration_name].status = IntegrationStatus.ERROR
                self.health_status[integration_name].last_error = str(e)
    
    async def _initialize_integration(self, integration_name: str, config: IntegrationConfig):
        """Initialize a specific integration."""
        try:
# NOTION_REMOVED:             if integration_name == 'notion':
# NOTION_REMOVED:                 integration = create_notion_client(api_key, config.specific_config)
                
            elif integration_name == 'github':
                from .github_client import GitHubIntegration
                integration = GitHubIntegration(config.specific_config)
                
            elif integration_name == 'sequential_thinking':
                from .sequential_thinking_client import SequentialThinkingClient
                server_path = config.specific_config.get('server_path')
                integration = SequentialThinkingClient(server_path)
                
            else:
                raise ValueError(f"Unknown integration type: {integration_name}")
            
            self.integrations[integration_name] = integration
            self.health_status[integration_name].status = IntegrationStatus.HEALTHY
            
            logger.success(f"Initialized {integration_name} integration")
            
        except Exception as e:
            logger.error(f"Failed to initialize {integration_name}: {e}")
            self.health_status[integration_name].status = IntegrationStatus.ERROR
            self.health_status[integration_name].last_error = str(e)
            raise
    
    async def _cleanup_integrations(self):
        """Cleanup all integrations."""
        for integration_name, integration in self.integrations.items():
            try:
                if hasattr(integration, 'cleanup'):
                    await integration.cleanup()
                logger.debug(f"Cleaned up {integration_name}")
            except Exception as e:
                logger.error(f"Error cleaning up {integration_name}: {e}")
        
        self.integrations.clear()
    
    async def execute_operation(self, integration_name: str, operation_type: OperationType,
                              operation_method: str, *args, **kwargs) -> OperationResult:
        """Execute an operation on a specific integration with error handling and retry logic."""
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Check if integration exists and is healthy
        if not await self._validate_integration(integration_name):
            return OperationResult(
                operation_id=operation_id,
                integration_name=integration_name,
                operation_type=operation_type,
                success=False,
                error_message=f"Integration {integration_name} not available"
            )
        
        # Check circuit breaker
        if self._is_circuit_breaker_open(integration_name):
            return OperationResult(
                operation_id=operation_id,
                integration_name=integration_name,
                operation_type=operation_type,
                success=False,
                error_message=f"Circuit breaker open for {integration_name}"
            )
        
        config = self.integration_configs[integration_name]
        integration = self.integrations[integration_name]
        
        retry_count = 0
        last_error = None
        
        while retry_count <= config.max_retries:
            try:
                # Execute the operation
                if hasattr(integration, operation_method):
                    method = getattr(integration, operation_method)
                    
                    # Apply timeout
                    result = await asyncio.wait_for(
                        method(*args, **kwargs),
                        timeout=config.timeout
                    )
                    
                    execution_time = time.time() - start_time
                    
                    # Record successful operation
                    operation_result = OperationResult(
                        operation_id=operation_id,
                        integration_name=integration_name,
                        operation_type=operation_type,
                        success=True,
                        result_data=result,
                        execution_time=execution_time,
                        retry_count=retry_count
                    )
                    
                    await self._record_operation_success(integration_name, operation_result)
                    return operation_result
                    
                else:
                    raise AttributeError(f"Method {operation_method} not found in {integration_name}")
                    
            except Exception as e:
                last_error = e
                retry_count += 1
                
                logger.warning(f"Operation failed on {integration_name} (attempt {retry_count}): {e}")
                
                if retry_count <= config.max_retries:
                    # Apply retry policy
                    delay = self._calculate_retry_delay(config.retry_policy, retry_count)
                    await asyncio.sleep(delay)
                else:
                    # Max retries exceeded
                    await self._record_operation_failure(integration_name, str(e))
                    break
        
        execution_time = time.time() - start_time
        
        # Return failure result
        operation_result = OperationResult(
            operation_id=operation_id,
            integration_name=integration_name,
            operation_type=operation_type,
            success=False,
            error_message=str(last_error),
            execution_time=execution_time,
            retry_count=retry_count
        )
        
        return operation_result
    
    async def _validate_integration(self, integration_name: str) -> bool:
        """Validate that an integration is available and healthy."""
        if integration_name not in self.integration_configs:
            logger.error(f"Integration {integration_name} not configured")
            return False
        
        if not self.integration_configs[integration_name].enabled:
            logger.warning(f"Integration {integration_name} is disabled")
            return False
        
        if integration_name not in self.integrations:
            logger.warning(f"Integration {integration_name} not initialized")
            return False
        
        health = self.health_status.get(integration_name)
        if health and health.status == IntegrationStatus.OFFLINE:
            logger.warning(f"Integration {integration_name} is offline")
            return False
        
        return True
    
    def _is_circuit_breaker_open(self, integration_name: str) -> bool:
        """Check if circuit breaker is open for an integration."""
        breaker = self.circuit_breakers.get(integration_name)
        if not breaker:
            return False
        
        if not breaker.is_open:
            return False
        
        # Check if timeout has passed
        if breaker.next_retry_time and datetime.now() >= breaker.next_retry_time:
            # Reset circuit breaker to half-open
            breaker.is_open = False
            breaker.next_retry_time = None
            logger.info(f"Circuit breaker reset for {integration_name}")
            return False
        
        return True
    
    def _calculate_retry_delay(self, retry_policy: RetryPolicy, attempt: int) -> float:
        """Calculate retry delay based on policy."""
        if retry_policy == RetryPolicy.IMMEDIATE:
            return 0.0
        elif retry_policy == RetryPolicy.LINEAR_BACKOFF:
            return attempt * 1.0
        elif retry_policy == RetryPolicy.EXPONENTIAL_BACKOFF:
            return min(2 ** attempt, 60.0)  # Cap at 60 seconds
        else:
            return 1.0
    
    async def _record_operation_success(self, integration_name: str, result: OperationResult):
        """Record a successful operation."""
        with self.manager_lock:
            # Update circuit breaker
            breaker = self.circuit_breakers[integration_name]
            breaker.failure_count = 0
            breaker.is_open = False
            
            # Update health status
            health = self.health_status[integration_name]
            health.last_successful_operation = datetime.now()
            health.total_operations += 1
            
            # Update statistics
            self._update_statistics(integration_name, result)
            
            # Store in database
            await self._store_operation_result(result)
    
    async def _record_operation_failure(self, integration_name: str, error_message: str):
        """Record a failed operation."""
        with self.manager_lock:
            config = self.integration_configs[integration_name]
            breaker = self.circuit_breakers[integration_name]
            health = self.health_status[integration_name]
            
            # Update circuit breaker
            breaker.failure_count += 1
            breaker.total_failures += 1
            breaker.last_failure_time = datetime.now()
            
            if breaker.failure_count >= config.circuit_breaker_threshold:
                # Open circuit breaker
                breaker.is_open = True
                breaker.next_retry_time = datetime.now() + timedelta(seconds=config.circuit_breaker_timeout)
                logger.warning(f"Circuit breaker opened for {integration_name}")
            
            # Update health status
            health.last_error = error_message
            health.total_operations += 1
            health.failed_operations += 1
            
            if health.failed_operations / health.total_operations > 0.5:
                health.status = IntegrationStatus.DEGRADED
            
            # Update statistics
            self._update_failure_statistics(integration_name, error_message)
    
    def _update_statistics(self, integration_name: str, result: OperationResult):
        """Update performance statistics."""
        stats = self.statistics[integration_name]
        
        # Response time tracking
        response_times = stats.get('response_times', [])
        response_times.append(result.execution_time)
        if len(response_times) > 100:  # Keep last 100 measurements
            response_times.pop(0)
        stats['response_times'] = response_times
        
        # Success rate tracking
        successes = stats.get('successes', 0) + 1
        total = stats.get('total_operations', 0) + 1
        stats['successes'] = successes
        stats['total_operations'] = total
        stats['success_rate'] = successes / total
        
        # Update health status
        health = self.health_status[integration_name]
        health.success_rate = stats['success_rate']
        health.average_response_time = sum(response_times) / len(response_times)
    
    def _update_failure_statistics(self, integration_name: str, error_message: str):
        """Update failure statistics."""
        stats = self.statistics[integration_name]
        
        # Track total operations
        total = stats.get('total_operations', 0) + 1
        stats['total_operations'] = total
        
        # Track failures
        failures = stats.get('failures', 0) + 1
        stats['failures'] = failures
        
        # Track error types
        error_types = stats.get('error_types', {})
        error_type = type(error_message).__name__
        error_types[error_type] = error_types.get(error_type, 0) + 1
        stats['error_types'] = error_types
        
        # Update success rate
        successes = stats.get('successes', 0)
        stats['success_rate'] = successes / total if total > 0 else 0.0
    
    async def _store_operation_result(self, result: OperationResult):
        """Store operation result in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO operations
                (operation_id, integration_name, operation_type, success, result_data,
                 error_message, execution_time, retry_count, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.operation_id,
                result.integration_name,
                result.operation_type.value,
                1 if result.success else 0,
                json.dumps(result.result_data) if result.result_data else None,
                result.error_message,
                result.execution_time,
                result.retry_count,
                result.timestamp.isoformat()
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store operation result: {e}")
    
    async def _health_check_loop(self):
        """Continuous health check loop."""
        while self.is_running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(60)  # Run every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(30)  # Shorter retry on error
    
    async def _perform_health_checks(self):
        """Perform health checks on all integrations."""
        for integration_name, config in self.integration_configs.items():
            if not config.enabled:
                continue
            
            last_check = self.last_health_check.get(integration_name)
            if last_check and (datetime.now() - last_check).total_seconds() < config.health_check_interval:
                continue
            
            await self._check_integration_health(integration_name)
            self.last_health_check[integration_name] = datetime.now()
    
    async def _check_integration_health(self, integration_name: str):
        """Check health of a specific integration."""
        try:
            if integration_name not in self.integrations:
                self.health_status[integration_name].status = IntegrationStatus.OFFLINE
                return
            
            integration = self.integrations[integration_name]
            
            # Perform basic health check
            if hasattr(integration, 'health_check'):
                health_result = await integration.health_check()
                if health_result:
                    self.health_status[integration_name].status = IntegrationStatus.HEALTHY
                else:
                    self.health_status[integration_name].status = IntegrationStatus.DEGRADED
            else:
                # Default health check - just verify the object exists
                self.health_status[integration_name].status = IntegrationStatus.HEALTHY
            
            # Update uptime percentage
            self._update_uptime_percentage(integration_name)
            
        except Exception as e:
            logger.error(f"Health check failed for {integration_name}: {e}")
            self.health_status[integration_name].status = IntegrationStatus.ERROR
            self.health_status[integration_name].last_error = str(e)
    
    def _update_uptime_percentage(self, integration_name: str):
        """Update uptime percentage for an integration."""
        health = self.health_status[integration_name]
        
        if health.total_operations == 0:
            health.uptime_percentage = 100.0
        else:
            successful_ops = health.total_operations - health.failed_operations
            health.uptime_percentage = (successful_ops / health.total_operations) * 100.0
    
    # Public API methods
    
# NOTION_REMOVED:     async def create_notion_task(self, title: str, description: str, **kwargs) -> OperationResult:
        """Create a task in Notion."""
        return await self.execute_operation(
            'notion', OperationType.CREATE, 'create_task',
            title, description, **kwargs
        )
    
# NOTION_REMOVED:     async def update_notion_task_status(self, task_id: str, status) -> OperationResult:
        """Update Notion task status."""
        return await self.execute_operation(
            'notion', OperationType.UPDATE, 'update_task_status',
            task_id, status
        )
    
# NOTION_REMOVED:     async def create_notion_knowledge_entry(self, title: str, content: Dict[str, Any], 
                                          tags: List[str], **kwargs) -> OperationResult:
        """Create a knowledge entry in Notion."""
        return await self.execute_operation(
            'notion', OperationType.CREATE, 'create_knowledge_entry',
            title, content, tags, **kwargs
        )
    
# NOTION_REMOVED:     async def sync_notion_data(self, force: bool = False) -> OperationResult:
        """Sync data with Notion."""
        return await self.execute_operation(
            'notion', OperationType.SYNC, 'sync_with_notion',
            force
        )
    
    async def commit_github_code(self, files: List[Dict[str, Any]], message: str, 
                                branch: Optional[str] = None) -> OperationResult:
        """Commit code to GitHub."""
        return await self.execute_operation(
            'github', OperationType.CREATE, 'commit_code',
            files, message, branch
        )
    
    async def create_github_pull_request(self, title: str, description: str,
                                       head_branch: str, base_branch: str = "main",
                                       **kwargs) -> OperationResult:
        """Create a GitHub pull request."""
        return await self.execute_operation(
            'github', OperationType.CREATE, 'create_pull_request',
            title, description, head_branch, base_branch, **kwargs
        )
    
    async def create_github_issue(self, title: str, description: str, **kwargs) -> OperationResult:
        """Create a GitHub issue."""
        return await self.execute_operation(
            'github', OperationType.CREATE, 'create_issue',
            title, description, **kwargs
        )
    
    async def run_github_tests(self, branch: Optional[str] = None) -> OperationResult:
        """Run tests on GitHub."""
        return await self.execute_operation(
            'github', OperationType.READ, 'run_tests',
            branch
        )
    
    def get_integration_status(self, integration_name: str) -> Optional[IntegrationHealth]:
        """Get status of a specific integration."""
        return self.health_status.get(integration_name)
    
    def get_all_integration_status(self) -> Dict[str, IntegrationHealth]:
        """Get status of all integrations."""
        return self.health_status.copy()
    
    def get_integration_statistics(self, integration_name: str) -> Dict[str, Any]:
        """Get statistics for a specific integration."""
        return self.statistics.get(integration_name, {})
    
    async def get_operation_history(self, integration_name: Optional[str] = None,
                                  limit: int = 100) -> List[Dict[str, Any]]:
        """Get operation history."""
        conn = sqlite3.connect(self.db_path)
        
        if integration_name:
            cursor = conn.execute('''
                SELECT * FROM operations 
                WHERE integration_name = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (integration_name, limit))
        else:
            cursor = conn.execute('''
                SELECT * FROM operations 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'operation_id': row[0],
                'integration_name': row[1],
                'operation_type': row[2],
                'success': bool(row[3]),
                'result_data': json.loads(row[4]) if row[4] else None,
                'error_message': row[5],
                'execution_time': row[6],
                'retry_count': row[7],
                'timestamp': row[8]
            })
        
        conn.close()
        return results
    
    async def reset_circuit_breaker(self, integration_name: str) -> bool:
        """Manually reset circuit breaker for an integration."""
        if integration_name not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[integration_name]
        breaker.is_open = False
        breaker.failure_count = 0
        breaker.next_retry_time = None
        
        logger.info(f"Circuit breaker manually reset for {integration_name}")
        return True
    
    async def enable_integration(self, integration_name: str) -> bool:
        """Enable an integration."""
        if integration_name not in self.integration_configs:
            return False
        
        config = self.integration_configs[integration_name]
        config.enabled = True
        
        # Try to initialize if not already done
        if integration_name not in self.integrations:
            try:
                await self._initialize_integration(integration_name, config)
            except Exception as e:
                logger.error(f"Failed to enable {integration_name}: {e}")
                return False
        
        logger.info(f"Enabled integration: {integration_name}")
        return True
    
    async def disable_integration(self, integration_name: str) -> bool:
        """Disable an integration."""
        if integration_name not in self.integration_configs:
            return False
        
        config = self.integration_configs[integration_name]
        config.enabled = False
        
        # Update health status
        self.health_status[integration_name].status = IntegrationStatus.OFFLINE
        
        logger.info(f"Disabled integration: {integration_name}")
        return True
    
    def get_manager_status(self) -> Dict[str, Any]:
        """Get overall manager status."""
        total_integrations = len(self.integration_configs)
        healthy_integrations = sum(
            1 for health in self.health_status.values()
            if health.status == IntegrationStatus.HEALTHY
        )
        
        return {
            'is_running': self.is_running,
            'total_integrations': total_integrations,
            'healthy_integrations': healthy_integrations,
            'degraded_integrations': sum(
                1 for health in self.health_status.values()
                if health.status == IntegrationStatus.DEGRADED
            ),
            'offline_integrations': sum(
                1 for health in self.health_status.values()
                if health.status == IntegrationStatus.OFFLINE
            ),
            'overall_health': healthy_integrations / total_integrations if total_integrations > 0 else 0.0,
            'uptime': datetime.now().isoformat(),  # Manager start time would be tracked separately
            'total_operations': sum(
                health.total_operations for health in self.health_status.values()
            ),
            'circuit_breakers_open': sum(
                1 for breaker in self.circuit_breakers.values() if breaker.is_open
            )
        }
    
    # Sequential Thinking Integration Methods
    
    async def start_thinking_session(self, problem_description: str) -> OperationResult:
        """Start a new sequential thinking session."""
        return await self.execute_operation(
            'sequential_thinking', OperationType.CREATE, 'start_thinking_session',
            problem_description
        )
    
    async def add_thought_step(self, session_id: str, thought: str, thought_number: int,
                             total_thoughts: int, next_thought_needed: bool, **kwargs) -> OperationResult:
        """Add a thought step to a thinking session."""
        return await self.execute_operation(
            'sequential_thinking', OperationType.CREATE, 'add_thought_step',
            session_id, thought, thought_number, total_thoughts, next_thought_needed, **kwargs
        )
    
    async def complete_thinking_session(self, session_id: str, final_solution: str) -> OperationResult:
        """Complete a thinking session with a final solution."""
        return await self.execute_operation(
            'sequential_thinking', OperationType.UPDATE, 'complete_thinking_session',
            session_id, final_solution
        )
    
    async def solve_problem_step_by_step(self, problem_description: str, 
                                       initial_thought_estimate: int = 5,
                                       max_thoughts: int = 20) -> OperationResult:
        """Solve a problem using structured step-by-step thinking."""
        return await self.execute_operation(
            'sequential_thinking', OperationType.CREATE, 'solve_problem_step_by_step',
            problem_description, initial_thought_estimate, max_thoughts
        )
    
    async def revise_thought(self, session_id: str, original_thought_number: int,
                           revised_thought: str, new_total_thoughts: Optional[int] = None) -> OperationResult:
        """Revise a previous thought in the thinking process."""
        return await self.execute_operation(
            'sequential_thinking', OperationType.UPDATE, 'revise_thought',
            session_id, original_thought_number, revised_thought, new_total_thoughts
        )
    
    async def create_thought_branch(self, session_id: str, branch_from_thought_number: int,
                                  branch_thought: str, branch_id: Optional[str] = None) -> OperationResult:
        """Create a new branch in the thinking process."""
        return await self.execute_operation(
            'sequential_thinking', OperationType.CREATE, 'create_thought_branch',
            session_id, branch_from_thought_number, branch_thought, branch_id
        )
    
    async def get_thinking_session_summary(self, session_id: str) -> OperationResult:
        """Get a summary of a thinking session."""
        return await self.execute_operation(
            'sequential_thinking', OperationType.READ, 'get_session_summary',
            session_id
        )

    async def cleanup(self):
        """Cleanup the integration manager."""
        logger.info("Cleaning up IntegrationManager")
        await self.stop()


# Global instance management
_integration_manager_instance = None
_integration_manager_lock = threading.Lock()

def get_integration_manager() -> IntegrationManager:
    """Get the global integration manager instance."""
    global _integration_manager_instance
    
    if _integration_manager_instance is None:
        with _integration_manager_lock:
            if _integration_manager_instance is None:
                _integration_manager_instance = IntegrationManager()
    
    return _integration_manager_instance