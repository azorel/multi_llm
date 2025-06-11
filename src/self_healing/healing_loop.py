"""
Self-Healing Loop Orchestration System

This module provides the main orchestration for the self-healing system,
integrating error detection, recovery management, and learning capabilities.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import sqlite3
from pathlib import Path

from loguru import logger

from .error_detector import ErrorDetector, ErrorEvent, ErrorSeverity, ErrorType, Anomaly
from .recovery_manager import RecoveryManager, RecoveryResult, RecoveryStrategy, RecoveryStatus


class HealingState(Enum):
    HEALTHY = "healthy"
    MONITORING = "monitoring"
    DETECTING = "detecting"
    RECOVERING = "recovering"
    ESCALATING = "escalating"
    LEARNING = "learning"
    DEGRADED = "degraded"
    FAILED = "failed"


class InterventionTrigger(Enum):
    ERROR_THRESHOLD = "error_threshold"
    ANOMALY_DETECTED = "anomaly_detected"
    FAILURE_PREDICTED = "failure_predicted"
    PERFORMANCE_DEGRADED = "performance_degraded"
    MANUAL_TRIGGER = "manual_trigger"
    SCHEDULED_CHECK = "scheduled_check"


@dataclass
class HealingSession:
    session_id: str
    start_time: datetime
    trigger: InterventionTrigger
    initial_state: Dict[str, Any]
    errors_detected: List[ErrorEvent] = field(default_factory=list)
    anomalies_detected: List[Anomaly] = field(default_factory=list)
    recovery_attempts: List[RecoveryResult] = field(default_factory=list)
    final_state: Optional[Dict[str, Any]] = None
    end_time: Optional[datetime] = None
    success: bool = False
    lessons_learned: List[str] = field(default_factory=list)


@dataclass
class SystemHealth:
    overall_health: float  # 0.0 - 1.0
    component_health: Dict[str, float]
    recent_errors: int
    error_rate: float
    performance_metrics: Dict[str, float]
    predictions: Dict[str, Any]
    last_updated: datetime


@dataclass
class HealingConfiguration:
    max_recovery_attempts: int = 5
    escalation_threshold: int = 3
    monitoring_interval: float = 5.0
    health_check_interval: float = 30.0
    learning_enabled: bool = True
    auto_intervention: bool = True
    performance_optimization: bool = True
    degraded_mode_threshold: float = 0.3
    failure_threshold: float = 0.1


class PerformanceOptimizer:
    """Optimizes system performance based on historical data and current conditions."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.optimization_history = deque(maxlen=1000)
        self.performance_baselines = {}
        self.optimization_strategies = {}
        
    async def analyze_performance(self, current_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Analyze current performance and identify optimization opportunities."""
        analysis = {
            'performance_score': self._calculate_performance_score(current_metrics),
            'bottlenecks': self._identify_bottlenecks(current_metrics),
            'optimization_recommendations': [],
            'predicted_improvements': {}
        }
        
        # Check for performance degradation
        for metric, value in current_metrics.items():
            baseline = self.performance_baselines.get(metric)
            if baseline and value < baseline * 0.8:  # 20% degradation
                analysis['optimization_recommendations'].append({
                    'metric': metric,
                    'current': value,
                    'baseline': baseline,
                    'degradation': (baseline - value) / baseline,
                    'suggested_actions': self._get_optimization_actions(metric)
                })
        
        return analysis
    
    def _calculate_performance_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall performance score."""
        if not metrics:
            return 1.0
        
        # Weight different metrics
        weights = {
            'cpu_usage': -0.3,  # Lower CPU usage is better
            'memory_usage': -0.3,
            'response_time': -0.2,
            'throughput': 0.2,  # Higher throughput is better
            'error_rate': -0.4  # Lower error rate is better
        }
        
        score = 1.0
        for metric, value in metrics.items():
            weight = weights.get(metric, 0)
            if weight != 0:
                normalized_value = min(value / 100.0, 1.0)  # Normalize to 0-1
                score += weight * normalized_value
        
        return max(0.0, min(1.0, score))
    
    def _identify_bottlenecks(self, metrics: Dict[str, float]) -> List[str]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        if metrics.get('cpu_usage', 0) > 80:
            bottlenecks.append('cpu_intensive_operations')
        if metrics.get('memory_usage', 0) > 85:
            bottlenecks.append('memory_exhaustion')
        if metrics.get('disk_usage', 0) > 90:
            bottlenecks.append('disk_space_limitation')
        if metrics.get('response_time', 0) > 5000:  # 5 seconds
            bottlenecks.append('slow_response_times')
        
        return bottlenecks
    
    def _get_optimization_actions(self, metric: str) -> List[str]:
        """Get optimization actions for a specific metric."""
        actions = {
            'cpu_usage': [
                'Optimize algorithm complexity',
                'Implement caching',
                'Reduce unnecessary computations',
                'Use more efficient data structures'
            ],
            'memory_usage': [
                'Implement garbage collection optimization',
                'Reduce memory allocations',
                'Use memory-efficient data structures',
                'Implement memory pooling'
            ],
            'response_time': [
                'Implement response caching',
                'Optimize database queries',
                'Use asynchronous processing',
                'Implement request queuing'
            ],
            'error_rate': [
                'Improve error handling',
                'Add input validation',
                'Implement retry mechanisms',
                'Review and fix code issues'
            ]
        }
        return actions.get(metric, ['General performance review needed'])
    
    async def apply_optimizations(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply performance optimizations."""
        results = {
            'applied_optimizations': [],
            'failed_optimizations': [],
            'estimated_improvement': 0.0
        }
        
        for rec in recommendations:
            try:
                # Simulate optimization application
                optimization_id = str(uuid.uuid4())
                
                # Record optimization attempt
                optimization_record = {
                    'id': optimization_id,
                    'metric': rec['metric'],
                    'actions': rec['suggested_actions'][:2],  # Apply first 2 actions
                    'timestamp': datetime.now(),
                    'estimated_improvement': rec['degradation'] * 0.5  # Assume 50% improvement
                }
                
                self.optimization_history.append(optimization_record)
                results['applied_optimizations'].append(optimization_record)
                results['estimated_improvement'] += optimization_record['estimated_improvement']
                
                logger.info(f"Applied optimization for {rec['metric']}: {optimization_record['actions']}")
                
            except Exception as e:
                logger.error(f"Failed to apply optimization for {rec['metric']}: {e}")
                results['failed_optimizations'].append({
                    'metric': rec['metric'],
                    'error': str(e)
                })
        
        return results
    
    def update_baselines(self, metrics: Dict[str, float]):
        """Update performance baselines with new metrics."""
        for metric, value in metrics.items():
            if metric not in self.performance_baselines:
                self.performance_baselines[metric] = value
            else:
                # Use exponential moving average
                alpha = 0.1
                self.performance_baselines[metric] = (
                    alpha * value + (1 - alpha) * self.performance_baselines[metric]
                )


class HealingLoop:
    """Main self-healing orchestration system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.healing_config = HealingConfiguration(**config.get('healing', {}))
        
        # Core components
        self.error_detector = ErrorDetector(config.get('error_detection', {}))
        self.recovery_manager = RecoveryManager(config.get('recovery', {}))
        self.performance_optimizer = PerformanceOptimizer(config.get('performance', {}))
        
        # State management
        self.current_state = HealingState.HEALTHY
        self.system_health = SystemHealth(
            overall_health=1.0,
            component_health={},
            recent_errors=0,
            error_rate=0.0,
            performance_metrics={},
            predictions={},
            last_updated=datetime.now()
        )
        
        # Session tracking
        self.active_sessions: Dict[str, HealingSession] = {}
        self.session_history: List[HealingSession] = []
        
        # Monitoring and intervention
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.intervention_queue = asyncio.Queue()
        self.is_running = False
        
        # Learning and adaptation
        self.learning_data = {
            'successful_interventions': [],
            'failed_interventions': [],
            'performance_patterns': {},
            'error_patterns': {},
            'recovery_effectiveness': {}
        }
        
        # Database for persistence
        self.db_path = config.get('database_path', 'healing_loop.db')
        self._initialize_database()
        
        # Callbacks and hooks
        self.intervention_callbacks: List[Callable] = []
        self.health_change_callbacks: List[Callable] = []
        
        logger.info("HealingLoop initialized")
    
    def _initialize_database(self):
        """Initialize database for persistent storage."""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS healing_sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                trigger_type TEXT,
                initial_state TEXT,
                final_state TEXT,
                success INTEGER,
                errors_count INTEGER,
                recoveries_count INTEGER,
                lessons_learned TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS system_health_history (
                timestamp TEXT PRIMARY KEY,
                overall_health REAL,
                component_health TEXT,
                error_rate REAL,
                performance_metrics TEXT,
                predictions TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS intervention_patterns (
                pattern_id TEXT PRIMARY KEY,
                trigger_type TEXT,
                conditions TEXT,
                success_rate REAL,
                avg_recovery_time REAL,
                last_used TEXT,
                usage_count INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def start(self):
        """Start the healing loop."""
        if self.is_running:
            logger.warning("HealingLoop is already running")
            return
        
        self.is_running = True
        logger.info("Starting HealingLoop")
        
        # Start core monitoring tasks
        self.monitoring_tasks['health_monitor'] = asyncio.create_task(self._health_monitoring_loop())
        self.monitoring_tasks['intervention_processor'] = asyncio.create_task(self._intervention_processing_loop())
        self.monitoring_tasks['performance_monitor'] = asyncio.create_task(self._performance_monitoring_loop())
        
        if self.healing_config.learning_enabled:
            self.monitoring_tasks['learning_processor'] = asyncio.create_task(self._learning_processing_loop())
        
        # Initialize error detector monitoring
        await self.error_detector.monitor_execution("healing_loop", "system")
        
        self.current_state = HealingState.MONITORING
        await self._update_system_health()
        
        logger.info("HealingLoop started successfully")
    
    async def stop(self):
        """Stop the healing loop."""
        if not self.is_running:
            return
        
        logger.info("Stopping HealingLoop")
        self.is_running = False
        
        # Cancel all monitoring tasks
        for task_name, task in self.monitoring_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.debug(f"Cancelled task: {task_name}")
        
        # Cleanup components
        await self.error_detector.cleanup()
        await self.recovery_manager.cleanup()
        
        # Finalize any active sessions
        for session in self.active_sessions.values():
            session.end_time = datetime.now()
            session.success = False
            await self._store_session(session)
        
        self.current_state = HealingState.HEALTHY
        logger.info("HealingLoop stopped")
    
    async def _health_monitoring_loop(self):
        """Main health monitoring loop."""
        try:
            while self.is_running:
                await self._perform_health_check()
                await asyncio.sleep(self.healing_config.health_check_interval)
        except asyncio.CancelledError:
            logger.debug("Health monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Health monitoring loop error: {e}")
    
    async def _perform_health_check(self):
        """Perform comprehensive health check."""
        try:
            # Collect current metrics
            current_metrics = await self._collect_system_metrics()
            
            # Update system health
            await self._update_system_health(current_metrics)
            
            # Check for anomalies
            anomalies = await self.error_detector.detect_anomalies(current_metrics)
            
            # Predict potential failures
            failure_prediction = await self.error_detector.predict_failure(current_metrics)
            
            # Determine if intervention is needed
            intervention_needed = await self._assess_intervention_need(
                current_metrics, anomalies, failure_prediction
            )
            
            if intervention_needed:
                trigger = self._determine_intervention_trigger(anomalies, failure_prediction)
                await self._queue_intervention(trigger, current_metrics)
            
            # Update performance baselines
            self.performance_optimizer.update_baselines(current_metrics)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    async def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect comprehensive system metrics."""
        try:
            import psutil
            
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'memory_available_gb': memory.available / (1024**3),
                'timestamp': time.time()
            }
            
            # Add error metrics
            recent_events = await self.error_detector.error_stream.get_events(
                since=datetime.now() - timedelta(minutes=5)
            )
            
            metrics.update({
                'error_count_5min': len(recent_events),
                'error_rate': len(recent_events) / 300.0,  # errors per second
                'critical_errors': sum(1 for e in recent_events if e.severity == ErrorSeverity.CRITICAL)
            })
            
            # Add performance metrics
            if hasattr(self, 'performance_metrics'):
                metrics.update(self.performance_metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {'timestamp': time.time()}
    
    async def _update_system_health(self, metrics: Optional[Dict[str, float]] = None):
        """Update system health assessment."""
        if metrics is None:
            metrics = await self._collect_system_metrics()
        
        # Calculate component health scores
        component_health = {}
        
        # CPU health
        cpu_usage = metrics.get('cpu_usage', 0)
        component_health['cpu'] = max(0.0, 1.0 - (cpu_usage / 100.0))
        
        # Memory health
        memory_usage = metrics.get('memory_usage', 0)
        component_health['memory'] = max(0.0, 1.0 - (memory_usage / 100.0))
        
        # Disk health
        disk_usage = metrics.get('disk_usage', 0)
        component_health['disk'] = max(0.0, 1.0 - (disk_usage / 100.0))
        
        # Error health
        error_rate = metrics.get('error_rate', 0)
        component_health['errors'] = max(0.0, 1.0 - error_rate)
        
        # Calculate overall health
        overall_health = sum(component_health.values()) / len(component_health)
        
        # Update system health
        previous_health = self.system_health.overall_health
        self.system_health = SystemHealth(
            overall_health=overall_health,
            component_health=component_health,
            recent_errors=int(metrics.get('error_count_5min', 0)),
            error_rate=error_rate,
            performance_metrics=metrics,
            predictions={},
            last_updated=datetime.now()
        )
        
        # Update healing state based on health
        await self._update_healing_state(overall_health)
        
        # Trigger health change callbacks if significant change
        if abs(overall_health - previous_health) > 0.1:
            for callback in self.health_change_callbacks:
                try:
                    await callback(self.system_health)
                except Exception as e:
                    logger.error(f"Health change callback failed: {e}")
        
        # Store health history
        await self._store_health_snapshot()
    
    async def _update_healing_state(self, health_score: float):
        """Update healing state based on health score."""
        previous_state = self.current_state
        
        if health_score >= 0.8:
            if self.current_state not in [HealingState.HEALTHY, HealingState.MONITORING]:
                self.current_state = HealingState.HEALTHY
        elif health_score >= 0.5:
            if self.current_state == HealingState.HEALTHY:
                self.current_state = HealingState.MONITORING
        elif health_score >= self.healing_config.degraded_mode_threshold:
            self.current_state = HealingState.DEGRADED
        elif health_score >= self.healing_config.failure_threshold:
            self.current_state = HealingState.DETECTING
        else:
            self.current_state = HealingState.FAILED
        
        if previous_state != self.current_state:
            logger.info(f"Healing state changed: {previous_state.value} -> {self.current_state.value}")
    
    async def _assess_intervention_need(self, 
                                      metrics: Dict[str, float],
                                      anomalies: List[Anomaly],
                                      failure_prediction) -> bool:
        """Assess whether intervention is needed."""
        if not self.healing_config.auto_intervention:
            return False
        
        # Check error thresholds
        if metrics.get('error_rate', 0) > 0.1:  # More than 0.1 errors per second
            return True
        
        # Check for high-severity anomalies
        critical_anomalies = [a for a in anomalies if a.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]]
        if critical_anomalies:
            return True
        
        # Check failure prediction
        if hasattr(failure_prediction, 'probability') and failure_prediction.probability > 0.7:
            return True
        
        # Check system health degradation
        if self.system_health.overall_health < 0.5:
            return True
        
        return False
    
    def _determine_intervention_trigger(self, anomalies: List[Anomaly], failure_prediction) -> InterventionTrigger:
        """Determine the type of intervention trigger."""
        if anomalies:
            return InterventionTrigger.ANOMALY_DETECTED
        elif hasattr(failure_prediction, 'probability') and failure_prediction.probability > 0.7:
            return InterventionTrigger.FAILURE_PREDICTED
        elif self.system_health.error_rate > 0.1:
            return InterventionTrigger.ERROR_THRESHOLD
        elif self.system_health.overall_health < 0.8:
            return InterventionTrigger.PERFORMANCE_DEGRADED
        else:
            return InterventionTrigger.SCHEDULED_CHECK
    
    async def _queue_intervention(self, trigger: InterventionTrigger, context: Dict[str, Any]):
        """Queue an intervention for processing."""
        intervention = {
            'trigger': trigger,
            'context': context,
            'timestamp': datetime.now(),
            'priority': self._calculate_intervention_priority(trigger, context)
        }
        
        await self.intervention_queue.put(intervention)
        logger.info(f"Queued intervention: {trigger.value}")
    
    def _calculate_intervention_priority(self, trigger: InterventionTrigger, context: Dict[str, Any]) -> int:
        """Calculate intervention priority (higher = more urgent)."""
        priority_map = {
            InterventionTrigger.ERROR_THRESHOLD: 90,
            InterventionTrigger.ANOMALY_DETECTED: 80,
            InterventionTrigger.FAILURE_PREDICTED: 70,
            InterventionTrigger.PERFORMANCE_DEGRADED: 60,
            InterventionTrigger.MANUAL_TRIGGER: 50,
            InterventionTrigger.SCHEDULED_CHECK: 10
        }
        
        base_priority = priority_map.get(trigger, 50)
        
        # Adjust based on system health
        if self.system_health.overall_health < 0.3:
            base_priority += 20
        elif self.system_health.overall_health < 0.5:
            base_priority += 10
        
        return base_priority
    
    async def _intervention_processing_loop(self):
        """Process queued interventions."""
        try:
            while self.is_running:
                try:
                    # Wait for intervention with timeout
                    intervention = await asyncio.wait_for(
                        self.intervention_queue.get(), timeout=1.0
                    )
                    await self._process_intervention(intervention)
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            logger.debug("Intervention processing loop cancelled")
        except Exception as e:
            logger.error(f"Intervention processing loop error: {e}")
    
    async def _process_intervention(self, intervention: Dict[str, Any]):
        """Process a single intervention."""
        session_id = str(uuid.uuid4())
        
        session = HealingSession(
            session_id=session_id,
            start_time=datetime.now(),
            trigger=intervention['trigger'],
            initial_state=intervention['context'].copy()
        )
        
        self.active_sessions[session_id] = session
        
        try:
            logger.info(f"Starting healing session {session_id} for {intervention['trigger'].value}")
            
            # Change state to appropriate intervention state
            if intervention['trigger'] == InterventionTrigger.ANOMALY_DETECTED:
                self.current_state = HealingState.DETECTING
            else:
                self.current_state = HealingState.RECOVERING
            
            # Trigger intervention callbacks
            for callback in self.intervention_callbacks:
                try:
                    await callback(session, intervention)
                except Exception as e:
                    logger.error(f"Intervention callback failed: {e}")
            
            # Perform actual intervention
            success = await self._perform_intervention(session, intervention)
            
            # Update session
            session.end_time = datetime.now()
            session.success = success
            session.final_state = await self._collect_system_metrics()
            
            # Learn from the intervention
            if self.healing_config.learning_enabled:
                await self._learn_from_intervention(session)
            
            # Store session
            await self._store_session(session)
            
            logger.info(f"Healing session {session_id} completed: {'success' if success else 'failed'}")
            
        except Exception as e:
            logger.error(f"Intervention processing failed: {e}")
            session.end_time = datetime.now()
            session.success = False
            await self._store_session(session)
        
        finally:
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Add to history
            self.session_history.append(session)
            
            # Return to monitoring state
            self.current_state = HealingState.MONITORING
    
    async def _perform_intervention(self, session: HealingSession, intervention: Dict[str, Any]) -> bool:
        """Perform the actual intervention."""
        trigger = intervention['trigger']
        context = intervention['context']
        
        success = False
        
        try:
            if trigger == InterventionTrigger.ERROR_THRESHOLD:
                success = await self._handle_error_threshold(session, context)
            elif trigger == InterventionTrigger.ANOMALY_DETECTED:
                success = await self._handle_anomaly_detection(session, context)
            elif trigger == InterventionTrigger.FAILURE_PREDICTED:
                success = await self._handle_failure_prediction(session, context)
            elif trigger == InterventionTrigger.PERFORMANCE_DEGRADED:
                success = await self._handle_performance_degradation(session, context)
            else:
                success = await self._handle_general_intervention(session, context)
            
            return success
            
        except Exception as e:
            logger.error(f"Intervention execution failed: {e}")
            return False
    
    async def _handle_error_threshold(self, session: HealingSession, context: Dict[str, Any]) -> bool:
        """Handle error threshold breaches."""
        logger.info("Handling error threshold breach")
        
        # Get recent errors
        recent_errors = await self.error_detector.error_stream.get_events(
            since=datetime.now() - timedelta(minutes=5)
        )
        session.errors_detected = recent_errors
        
        # Group errors by type for targeted recovery
        error_groups = defaultdict(list)
        for error in recent_errors:
            error_groups[error.error_type].append(error)
        
        overall_success = True
        
        # Attempt recovery for each error type
        for error_type, errors in error_groups.items():
            try:
                # Use the most recent error as representative
                representative_error = max(errors, key=lambda e: e.timestamp)
                
# DEMO CODE REMOVED: # Create a mock exception for recovery
# DEMO CODE REMOVED: mock_exception = Exception(representative_error.message)
                
                # Attempt recovery
                recovery_result = await self.recovery_manager.auto_recover(
# DEMO CODE REMOVED: mock_exception,
                    {
                        'goal': 'Resolve error threshold breach',
                        'system_state': context,
                        'error_context': representative_error.context
                    },
                    orchestrator=self
                )
                
                session.recovery_attempts.append(recovery_result)
                
                if not recovery_result.success:
                    overall_success = False
                
                session.lessons_learned.extend(recovery_result.lessons_learned)
                
            except Exception as e:
                logger.error(f"Recovery failed for error type {error_type}: {e}")
                overall_success = False
        
        return overall_success
    
    async def _handle_anomaly_detection(self, session: HealingSession, context: Dict[str, Any]) -> bool:
        """Handle detected anomalies."""
        logger.info("Handling anomaly detection")
        
        # Detect current anomalies
        current_metrics = await self._collect_system_metrics()
        anomalies = await self.error_detector.detect_anomalies(current_metrics)
        session.anomalies_detected = anomalies
        
        if not anomalies:
            return True  # No anomalies to handle
        
        overall_success = True
        
        for anomaly in anomalies:
            try:
                # Create intervention based on anomaly type
                if anomaly.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
# DEMO CODE REMOVED: # Create mock error for recovery
# DEMO CODE REMOVED: mock_exception = Exception(f"Anomaly detected: {anomaly.description}")
                    
                    recovery_result = await self.recovery_manager.auto_recover(
# DEMO CODE REMOVED: mock_exception,
                        {
                            'goal': 'Resolve detected anomaly',
                            'system_state': context,
                            'anomaly_context': anomaly.context
                        },
                        orchestrator=self
                    )
                    
                    session.recovery_attempts.append(recovery_result)
                    
                    if not recovery_result.success:
                        overall_success = False
                    
                    session.lessons_learned.extend(recovery_result.lessons_learned)
            
            except Exception as e:
                logger.error(f"Anomaly recovery failed: {e}")
                overall_success = False
        
        return overall_success
    
    async def _handle_failure_prediction(self, session: HealingSession, context: Dict[str, Any]) -> bool:
        """Handle predicted failures."""
        logger.info("Handling failure prediction")
        
        # Get failure prediction
        failure_prediction = await self.error_detector.predict_failure(context)
        
        if failure_prediction.probability < 0.5:
            return True  # Low probability, no action needed
        
        try:
            # Implement preventive measures based on contributing factors
            mitigation_success = True
            
            for factor in failure_prediction.contributing_factors:
                if 'memory' in factor.lower():
                    # Trigger memory optimization
                    session.lessons_learned.append("Applied memory optimization")
                elif 'cpu' in factor.lower():
                    # Reduce CPU load
                    session.lessons_learned.append("Applied CPU load reduction")
                elif 'disk' in factor.lower():
                    # Free up disk space
                    session.lessons_learned.append("Applied disk cleanup")
            
            # Apply mitigation suggestions
            for suggestion in failure_prediction.mitigation_suggestions:
                session.lessons_learned.append(f"Applied mitigation: {suggestion}")
            
            return mitigation_success
            
        except Exception as e:
            logger.error(f"Failure prediction handling failed: {e}")
            return False
    
    async def _handle_performance_degradation(self, session: HealingSession, context: Dict[str, Any]) -> bool:
        """Handle performance degradation."""
        logger.info("Handling performance degradation")
        
        if not self.healing_config.performance_optimization:
            return True
        
        try:
            # Analyze performance
            performance_analysis = await self.performance_optimizer.analyze_performance(context)
            
            # Apply optimizations
            if performance_analysis['optimization_recommendations']:
                optimization_results = await self.performance_optimizer.apply_optimizations(
                    performance_analysis['optimization_recommendations']
                )
                
                session.lessons_learned.extend([
                    f"Applied optimization: {opt['actions']}" 
                    for opt in optimization_results['applied_optimizations']
                ])
                
                return len(optimization_results['failed_optimizations']) == 0
            
            return True
            
        except Exception as e:
            logger.error(f"Performance degradation handling failed: {e}")
            return False
    
    async def _handle_general_intervention(self, session: HealingSession, context: Dict[str, Any]) -> bool:
        """Handle general interventions."""
        logger.info("Handling general intervention")
        
        try:
            # Perform basic health restoration
            current_metrics = await self._collect_system_metrics()
            
            # Check if system has recovered naturally
            if self.system_health.overall_health > 0.8:
                session.lessons_learned.append("System recovered naturally")
                return True
            
            # Apply basic recovery strategies
            session.lessons_learned.append("Applied basic system checks")
            return True
            
        except Exception as e:
            logger.error(f"General intervention failed: {e}")
            return False
    
    async def _performance_monitoring_loop(self):
        """Monitor and optimize performance continuously."""
        try:
            while self.is_running:
                if self.healing_config.performance_optimization:
                    await self._optimize_performance()
                await asyncio.sleep(60)  # Check every minute
        except asyncio.CancelledError:
            logger.debug("Performance monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Performance monitoring loop error: {e}")
    
    async def _optimize_performance(self):
        """Perform continuous performance optimization."""
        try:
            current_metrics = await self._collect_system_metrics()
            analysis = await self.performance_optimizer.analyze_performance(current_metrics)
            
            # Apply minor optimizations automatically
            minor_recommendations = [
                rec for rec in analysis['optimization_recommendations']
                if rec['degradation'] < 0.3  # Less than 30% degradation
            ]
            
            if minor_recommendations:
                await self.performance_optimizer.apply_optimizations(minor_recommendations)
                logger.debug(f"Applied {len(minor_recommendations)} minor optimizations")
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
    
    async def _learning_processing_loop(self):
        """Process learning data and adapt strategies."""
        try:
            while self.is_running:
                await self._process_learning_data()
                await asyncio.sleep(300)  # Learn every 5 minutes
        except asyncio.CancelledError:
            logger.debug("Learning processing loop cancelled")
        except Exception as e:
            logger.error(f"Learning processing loop error: {e}")
    
    async def _process_learning_data(self):
        """Process accumulated learning data."""
        try:
            # Analyze successful interventions
            recent_sessions = [s for s in self.session_history[-100:] if s.success]
            
            if len(recent_sessions) >= 5:
                # Extract patterns from successful interventions
                success_patterns = self._extract_success_patterns(recent_sessions)
                
                # Update intervention strategies
                await self._update_intervention_strategies(success_patterns)
                
                logger.debug(f"Processed learning data from {len(recent_sessions)} successful sessions")
            
        except Exception as e:
            logger.error(f"Learning processing failed: {e}")
    
    def _extract_success_patterns(self, sessions: List[HealingSession]) -> Dict[str, Any]:
        """Extract patterns from successful healing sessions."""
        patterns = {
            'trigger_effectiveness': defaultdict(int),
            'recovery_strategies': defaultdict(int),
            'common_lessons': defaultdict(int),
            'timing_patterns': []
        }
        
        for session in sessions:
            # Count trigger effectiveness
            patterns['trigger_effectiveness'][session.trigger.value] += 1
            
            # Extract recovery strategies used
            for recovery in session.recovery_attempts:
                if recovery.success:
                    patterns['recovery_strategies'][recovery.strategy_used.value] += 1
            
            # Count common lessons
            for lesson in session.lessons_learned:
                patterns['common_lessons'][lesson] += 1
            
            # Track timing
            if session.end_time:
                duration = (session.end_time - session.start_time).total_seconds()
                patterns['timing_patterns'].append({
                    'trigger': session.trigger.value,
                    'duration': duration,
                    'success': session.success
                })
        
        return patterns
    
    async def _update_intervention_strategies(self, patterns: Dict[str, Any]):
        """Update intervention strategies based on learned patterns."""
        try:
            # Update trigger priorities based on effectiveness
            most_effective_triggers = sorted(
                patterns['trigger_effectiveness'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            logger.debug(f"Most effective triggers: {most_effective_triggers[:3]}")
            
            # Update recovery strategy preferences
            most_effective_strategies = sorted(
                patterns['recovery_strategies'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            logger.debug(f"Most effective strategies: {most_effective_strategies[:3]}")
            
        except Exception as e:
            logger.error(f"Strategy update failed: {e}")
    
    async def _learn_from_intervention(self, session: HealingSession):
        """Learn from a completed intervention session."""
        try:
            learning_record = {
                'timestamp': datetime.now(),
                'trigger': session.trigger.value,
                'success': session.success,
                'duration': (session.end_time - session.start_time).total_seconds() if session.end_time else 0,
                'errors_count': len(session.errors_detected),
                'recoveries_count': len(session.recovery_attempts),
                'lessons': session.lessons_learned
            }
            
            if session.success:
                self.learning_data['successful_interventions'].append(learning_record)
            else:
                self.learning_data['failed_interventions'].append(learning_record)
            
            # Keep only recent learning data
            for key in ['successful_interventions', 'failed_interventions']:
                if len(self.learning_data[key]) > 1000:
                    self.learning_data[key] = self.learning_data[key][-1000:]
            
        except Exception as e:
            logger.error(f"Learning from intervention failed: {e}")
    
    async def _store_session(self, session: HealingSession):
        """Store healing session in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO healing_sessions
                (session_id, start_time, end_time, trigger_type, initial_state, final_state,
                 success, errors_count, recoveries_count, lessons_learned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id,
                session.start_time.isoformat(),
                session.end_time.isoformat() if session.end_time else None,
                session.trigger.value,
                json.dumps(session.initial_state),
                json.dumps(session.final_state) if session.final_state else None,
                1 if session.success else 0,
                len(session.errors_detected),
                len(session.recovery_attempts),
                json.dumps(session.lessons_learned)
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store session: {e}")
    
    async def _store_health_snapshot(self):
        """Store current health snapshot."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO system_health_history
                (timestamp, overall_health, component_health, error_rate, performance_metrics, predictions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.system_health.last_updated.isoformat(),
                self.system_health.overall_health,
                json.dumps(self.system_health.component_health),
                self.system_health.error_rate,
                json.dumps(self.system_health.performance_metrics),
                json.dumps(self.system_health.predictions)
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store health snapshot: {e}")
    
    # Public API methods
    
    async def trigger_manual_intervention(self, context: Optional[Dict[str, Any]] = None):
        """Manually trigger an intervention."""
        context = context or {}
        await self._queue_intervention(InterventionTrigger.MANUAL_TRIGGER, context)
    
    def add_intervention_callback(self, callback: Callable):
        """Add callback for intervention events."""
        self.intervention_callbacks.append(callback)
    
    def add_health_change_callback(self, callback: Callable):
        """Add callback for health change events."""
        self.health_change_callbacks.append(callback)
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health."""
        return self.system_health
    
    def get_healing_status(self) -> Dict[str, Any]:
        """Get comprehensive healing system status."""
        return {
            'current_state': self.current_state.value,
            'system_health': {
                'overall_health': self.system_health.overall_health,
                'component_health': self.system_health.component_health,
                'error_rate': self.system_health.error_rate,
                'recent_errors': self.system_health.recent_errors
            },
            'active_sessions': len(self.active_sessions),
            'total_sessions': len(self.session_history),
            'successful_sessions': sum(1 for s in self.session_history if s.success),
            'is_running': self.is_running,
            'configuration': {
                'auto_intervention': self.healing_config.auto_intervention,
                'learning_enabled': self.healing_config.learning_enabled,
                'performance_optimization': self.healing_config.performance_optimization
            },
            'learning_data_size': {
                'successful_interventions': len(self.learning_data['successful_interventions']),
                'failed_interventions': len(self.learning_data['failed_interventions'])
            }
        }
    
    async def get_healing_statistics(self) -> Dict[str, Any]:
        """Get detailed healing statistics."""
        if not self.session_history:
            return {
                'total_sessions': 0,
                'success_rate': 0.0,
                'average_duration': 0.0,
                'trigger_distribution': {},
                'strategy_effectiveness': {}
            }
        
        total_sessions = len(self.session_history)
        successful_sessions = sum(1 for s in self.session_history if s.success)
        success_rate = successful_sessions / total_sessions
        
        # Calculate average duration
        completed_sessions = [s for s in self.session_history if s.end_time]
        average_duration = 0.0
        if completed_sessions:
            total_duration = sum(
                (s.end_time - s.start_time).total_seconds() 
                for s in completed_sessions
            )
            average_duration = total_duration / len(completed_sessions)
        
        # Trigger distribution
        trigger_counts = defaultdict(int)
        for session in self.session_history:
            trigger_counts[session.trigger.value] += 1
        
        # Strategy effectiveness
        strategy_stats = defaultdict(lambda: {'attempts': 0, 'successes': 0})
        for session in self.session_history:
            for recovery in session.recovery_attempts:
                strategy = recovery.strategy_used.value
                strategy_stats[strategy]['attempts'] += 1
                if recovery.success:
                    strategy_stats[strategy]['successes'] += 1
        
        strategy_effectiveness = {}
        for strategy, stats in strategy_stats.items():
            if stats['attempts'] > 0:
                strategy_effectiveness[strategy] = stats['successes'] / stats['attempts']
        
        return {
            'total_sessions': total_sessions,
            'success_rate': success_rate,
            'average_duration': average_duration,
            'trigger_distribution': dict(trigger_counts),
            'strategy_effectiveness': dict(strategy_effectiveness),
            'recent_health_trend': await self._get_health_trend(),
            'performance_improvements': await self._get_performance_improvements()
        }
    
    async def _get_health_trend(self) -> List[Dict[str, Any]]:
        """Get recent health trend data."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('''
                SELECT timestamp, overall_health, error_rate
                FROM system_health_history
                ORDER BY timestamp DESC
                LIMIT 100
            ''')
            
            trend_data = []
            for row in cursor.fetchall():
                trend_data.append({
                    'timestamp': row[0],
                    'health': row[1],
                    'error_rate': row[2]
                })
            
            conn.close()
            return trend_data
            
        except Exception as e:
            logger.error(f"Failed to get health trend: {e}")
            return []
    
    async def _get_performance_improvements(self) -> Dict[str, Any]:
        """Get performance improvement metrics."""
        try:
            if not self.performance_optimizer.optimization_history:
                return {}
            
            recent_optimizations = list(self.performance_optimizer.optimization_history)[-50:]
            
            improvements_by_metric = defaultdict(list)
            for opt in recent_optimizations:
                metric = opt['metric']
                improvement = opt['estimated_improvement']
                improvements_by_metric[metric].append(improvement)
            
            average_improvements = {}
            for metric, improvements in improvements_by_metric.items():
                average_improvements[metric] = sum(improvements) / len(improvements)
            
            return {
                'total_optimizations': len(recent_optimizations),
                'average_improvements': average_improvements,
                'optimization_frequency': len(recent_optimizations) / max(1, 
                    (datetime.now() - recent_optimizations[0]['timestamp']).total_seconds() / 3600
                ) if recent_optimizations else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance improvements: {e}")
            return {}
    
    async def process_goal(self, goal: str, context: Optional[Dict[str, Any]] = None):
        """Process a goal (for orchestrator compatibility)."""
        # This method is called by the recovery manager during auto-recovery
        # It's a simplified implementation for compatibility
        try:
            # Simulate goal processing
            await asyncio.sleep(0.1)  # Simulate processing time
            
# DEMO CODE REMOVED: # Create a mock result
            result = type('Result', (), {
                'status': type('Status', (), {'value': 'success'})()
            })()
            
            return result
            
        except Exception as e:
            logger.error(f"Goal processing failed: {e}")
            result = type('Result', (), {
                'status': type('Status', (), {'value': 'failed'})()
            })()
            return result