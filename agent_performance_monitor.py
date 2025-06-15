#!/usr/bin/env python3
"""
Agent Performance Monitoring and Analytics System
=================================================

A comprehensive system that monitors real agent task execution metrics,
tracks success/failure rates, costs, and provides analytics dashboard.

Integrates with the real agent orchestrator to provide actionable insights.
"""

import asyncio
import json
import sqlite3
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict, deque
import statistics

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class MetricType(Enum):
    TASK_COMPLETION = "task_completion"
    RESPONSE_TIME = "response_time"
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    ERROR_RATE = "error_rate"
    PROVIDER_HEALTH = "provider_health"

@dataclass
class PerformanceMetric:
    metric_id: str
    agent_id: str
    agent_type: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    task_id: Optional[str] = None
    provider: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Alert:
    alert_id: str
    level: AlertLevel
    title: str
    description: str
    metric_type: MetricType
    threshold_value: float
    actual_value: float
    agent_id: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class PerformanceTracker:
    """Tracks and analyzes agent performance metrics in real-time"""
    
    def __init__(self, db_path: str = "agent_analytics.db"):
        self.db_path = db_path
        self.metrics_buffer = deque(maxlen=1000)  # Recent metrics cache
        self.agent_stats = defaultdict(lambda: {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_cost': 0.0,
            'total_tokens': 0,
            'avg_response_time': 0.0,
            'response_times': deque(maxlen=100),
            'last_active': None,
            'hourly_stats': defaultdict(int),
            'provider_usage': defaultdict(int)
        })
        self.provider_stats = defaultdict(lambda: {
            'requests': 0,
            'errors': 0,
            'total_cost': 0.0,
            'avg_response_time': 0.0,
            'response_times': deque(maxlen=100)
        })
        self.alerts = []
        self.alert_thresholds = {
            'error_rate': 30.0,  # Percentage
            'response_time': 30000.0,  # Milliseconds
            'cost_spike': 5.0,  # Dollar amount spike
            'token_spike': 10000  # Token usage spike
        }
        
        self._init_database()
        self._start_background_processing()
    
    def _init_database(self):
        """Initialize analytics database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_id TEXT UNIQUE NOT NULL,
                agent_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                task_id TEXT,
                provider TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Agent performance summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_performance_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT UNIQUE NOT NULL,
                agent_type TEXT NOT NULL,
                total_tasks INTEGER DEFAULT 0,
                successful_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                total_tokens INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0.0,
                last_active DATETIME,
                success_rate REAL DEFAULT 0.0,
                cost_per_task REAL DEFAULT 0.0,
                tokens_per_task REAL DEFAULT 0.0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Provider performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provider_performance (
                provider TEXT NOT NULL,
                date DATE NOT NULL,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                avg_response_time REAL DEFAULT 0.0,
                success_rate REAL DEFAULT 0.0,
                PRIMARY KEY (provider, date)
            ) WITHOUT ROWID
        """)
        
        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                level TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                threshold_value REAL NOT NULL,
                actual_value REAL NOT NULL,
                agent_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Task execution timeline table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_execution_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                task_name TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at DATETIME,
                completed_at DATETIME,
                duration_ms INTEGER,
                tokens_used INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                provider TEXT,
                success BOOLEAN DEFAULT FALSE,
                error_message TEXT,
                files_created INTEGER DEFAULT 0,
                files_modified INTEGER DEFAULT 0
            )
        """)
        
        # Hourly performance aggregates
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hourly_performance (
                hour_timestamp DATETIME NOT NULL,
                agent_type TEXT NOT NULL,
                tasks_completed INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                avg_response_time REAL DEFAULT 0.0,
                total_cost REAL DEFAULT 0.0,
                total_tokens INTEGER DEFAULT 0,
                PRIMARY KEY (hour_timestamp, agent_type)
            ) WITHOUT ROWID
        """)
        
        conn.commit()
        conn.close()
        logger.info("✅ Agent analytics database initialized")
    
    def record_task_execution(self, task_data: Dict[str, Any]):
        """Record a completed task execution for analytics"""
        try:
            agent_id = task_data.get('agent_id', 'unknown')
            agent_type = task_data.get('agent_type', 'unknown')
            task_id = task_data.get('task_id', f'task_{int(time.time() * 1000)}')
            success = task_data.get('success', False)
            
            # Calculate metrics
            duration_ms = task_data.get('duration_ms', 0)
            tokens_used = task_data.get('tokens_used', 0)
            cost = task_data.get('cost', 0.0)
            provider = task_data.get('provider', 'unknown')
            
            # Record individual metrics
            timestamp = datetime.now(timezone.utc)
            
            metrics = [
                PerformanceMetric(
                    metric_id=f"{task_id}_completion",
                    agent_id=agent_id,
                    agent_type=agent_type,
                    metric_type=MetricType.TASK_COMPLETION,
                    value=1.0 if success else 0.0,
                    unit="boolean",
                    timestamp=timestamp,
                    task_id=task_id,
                    provider=provider
                ),
                PerformanceMetric(
                    metric_id=f"{task_id}_response_time",
                    agent_id=agent_id,
                    agent_type=agent_type,
                    metric_type=MetricType.RESPONSE_TIME,
                    value=duration_ms,
                    unit="milliseconds",
                    timestamp=timestamp,
                    task_id=task_id,
                    provider=provider
                ),
                PerformanceMetric(
                    metric_id=f"{task_id}_tokens",
                    agent_id=agent_id,
                    agent_type=agent_type,
                    metric_type=MetricType.TOKEN_USAGE,
                    value=tokens_used,
                    unit="tokens",
                    timestamp=timestamp,
                    task_id=task_id,
                    provider=provider
                ),
                PerformanceMetric(
                    metric_id=f"{task_id}_cost",
                    agent_id=agent_id,
                    agent_type=agent_type,
                    metric_type=MetricType.COST,
                    value=cost,
                    unit="dollars",
                    timestamp=timestamp,
                    task_id=task_id,
                    provider=provider
                )
            ]
            
            # Store metrics
            for metric in metrics:
                self.record_metric(metric)
            
            # Update agent stats
            self._update_agent_stats(agent_id, agent_type, success, duration_ms, tokens_used, cost, provider)
            
            # Update provider stats
            self._update_provider_stats(provider, success, duration_ms, cost)
            
            # Record task execution timeline
            self._record_task_timeline(task_data)
            
            # Check for alerts
            self._check_performance_alerts(agent_id, agent_type, duration_ms, cost, tokens_used)
            
            logger.info(f"📊 Recorded performance metrics for task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to record task execution: {e}")
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a single performance metric"""
        try:
            # Add to buffer for real-time access
            self.metrics_buffer.append(metric)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO performance_metrics 
                (metric_id, agent_id, agent_type, metric_type, value, unit, timestamp, task_id, provider, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.metric_id,
                metric.agent_id,
                metric.agent_type,
                metric.metric_type.value,
                metric.value,
                metric.unit,
                metric.timestamp,
                metric.task_id,
                metric.provider,
                json.dumps(metric.metadata) if metric.metadata else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
    
    def _update_agent_stats(self, agent_id: str, agent_type: str, success: bool, 
                           duration_ms: float, tokens_used: int, cost: float, provider: str):
        """Update agent statistics"""
        stats = self.agent_stats[agent_id]
        
        stats['total_tasks'] += 1
        if success:
            stats['successful_tasks'] += 1
        else:
            stats['failed_tasks'] += 1
        
        stats['total_cost'] += cost
        stats['total_tokens'] += tokens_used
        stats['last_active'] = datetime.now(timezone.utc)
        
        # Update response times
        stats['response_times'].append(duration_ms)
        if stats['response_times']:
            stats['avg_response_time'] = statistics.mean(stats['response_times'])
        
        # Track hourly activity
        hour_key = datetime.now().strftime('%Y-%m-%d %H:00:00')
        stats['hourly_stats'][hour_key] += 1
        
        # Track provider usage
        stats['provider_usage'][provider] += 1
        
        # Update database summary
        self._update_agent_summary_db(agent_id, agent_type, stats)
    
    def _update_provider_stats(self, provider: str, success: bool, duration_ms: float, cost: float):
        """Update provider statistics"""
        stats = self.provider_stats[provider]
        
        stats['requests'] += 1
        if not success:
            stats['errors'] += 1
        
        stats['total_cost'] += cost
        stats['response_times'].append(duration_ms)
        
        if stats['response_times']:
            stats['avg_response_time'] = statistics.mean(stats['response_times'])
    
    def _record_task_timeline(self, task_data: Dict[str, Any]):
        """Record task execution in timeline table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO task_execution_timeline 
                (task_id, agent_id, agent_type, task_name, status, started_at, completed_at, 
                 duration_ms, tokens_used, cost, provider, success, error_message, 
                 files_created, files_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_data.get('task_id'),
                task_data.get('agent_id'),
                task_data.get('agent_type'),
                task_data.get('task_name', 'Unknown Task'),
                task_data.get('status', 'completed'),
                task_data.get('started_at'),
                task_data.get('completed_at'),
                task_data.get('duration_ms', 0),
                task_data.get('tokens_used', 0),
                task_data.get('cost', 0.0),
                task_data.get('provider'),
                task_data.get('success', False),
                task_data.get('error_message'),
                len(task_data.get('files_created', [])),
                len(task_data.get('files_modified', []))
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to record task timeline: {e}")
    
    def _update_agent_summary_db(self, agent_id: str, agent_type: str, stats: Dict[str, Any]):
        """Update agent performance summary in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            success_rate = (stats['successful_tasks'] / max(stats['total_tasks'], 1)) * 100
            cost_per_task = stats['total_cost'] / max(stats['total_tasks'], 1)
            tokens_per_task = stats['total_tokens'] / max(stats['total_tasks'], 1)
            
            cursor.execute("""
                INSERT OR REPLACE INTO agent_performance_summary 
                (agent_id, agent_type, total_tasks, successful_tasks, failed_tasks, 
                 total_cost, total_tokens, avg_response_time, last_active, success_rate, 
                 cost_per_task, tokens_per_task, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id, agent_type, stats['total_tasks'], stats['successful_tasks'],
                stats['failed_tasks'], stats['total_cost'], stats['total_tokens'],
                stats['avg_response_time'], stats['last_active'], success_rate,
                cost_per_task, tokens_per_task, datetime.now(timezone.utc)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update agent summary: {e}")
    
    def _check_performance_alerts(self, agent_id: str, agent_type: str, 
                                 duration_ms: float, cost: float, tokens_used: int):
        """Check for performance issues and create alerts"""
        try:
            # Check response time threshold
            if duration_ms > self.alert_thresholds['response_time']:
                alert = Alert(
                    alert_id=f"response_time_{agent_id}_{int(time.time())}",
                    level=AlertLevel.WARNING,
                    title="High Response Time",
                    description=f"Agent {agent_id} took {duration_ms}ms to complete task",
                    metric_type=MetricType.RESPONSE_TIME,
                    threshold_value=self.alert_thresholds['response_time'],
                    actual_value=duration_ms,
                    agent_id=agent_id,
                    timestamp=datetime.now(timezone.utc)
                )
                self._create_alert(alert)
            
            # Check cost spike
            agent_stats = self.agent_stats[agent_id]
            if agent_stats['total_tasks'] > 5:  # Need some history
                avg_cost_per_task = agent_stats['total_cost'] / agent_stats['total_tasks']
                if cost > avg_cost_per_task * 3:  # 3x average cost
                    alert = Alert(
                        alert_id=f"cost_spike_{agent_id}_{int(time.time())}",
                        level=AlertLevel.WARNING,
                        title="Cost Spike Detected",
                        description=f"Agent {agent_id} task cost ${cost:.3f} is 3x higher than average ${avg_cost_per_task:.3f}",
                        metric_type=MetricType.COST,
                        threshold_value=avg_cost_per_task * 3,
                        actual_value=cost,
                        agent_id=agent_id,
                        timestamp=datetime.now(timezone.utc)
                    )
                    self._create_alert(alert)
            
            # Check error rate
            if agent_stats['total_tasks'] >= 10:  # Need sufficient data
                error_rate = (agent_stats['failed_tasks'] / agent_stats['total_tasks']) * 100
                if error_rate > self.alert_thresholds['error_rate']:
                    alert = Alert(
                        alert_id=f"error_rate_{agent_id}_{int(time.time())}",
                        level=AlertLevel.CRITICAL,
                        title="High Error Rate",
                        description=f"Agent {agent_id} has {error_rate:.1f}% error rate",
                        metric_type=MetricType.ERROR_RATE,
                        threshold_value=self.alert_thresholds['error_rate'],
                        actual_value=error_rate,
                        agent_id=agent_id,
                        timestamp=datetime.now(timezone.utc)
                    )
                    self._create_alert(alert)
            
        except Exception as e:
            logger.error(f"Failed to check performance alerts: {e}")
    
    def _create_alert(self, alert: Alert):
        """Create and store a performance alert"""
        try:
            self.alerts.append(alert)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO alerts 
                (alert_id, level, title, description, metric_type, threshold_value, 
                 actual_value, agent_id, timestamp, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id, alert.level.value, alert.title, alert.description,
                alert.metric_type.value, alert.threshold_value, alert.actual_value,
                alert.agent_id, alert.timestamp, alert.resolved
            ))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"🚨 {alert.level.value.upper()}: {alert.title} - {alert.description}")
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
    
    def get_agent_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive agent performance summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get overall stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_agents,
                    SUM(total_tasks) as total_tasks,
                    SUM(successful_tasks) as successful_tasks,
                    SUM(failed_tasks) as failed_tasks,
                    SUM(total_cost) as total_cost,
                    AVG(success_rate) as avg_success_rate,
                    AVG(avg_response_time) as avg_response_time
                FROM agent_performance_summary
            """)
            
            overall_stats = cursor.fetchone()
            
            # Get per-agent stats
            cursor.execute("""
                SELECT * FROM agent_performance_summary 
                ORDER BY total_tasks DESC
            """)
            
            agent_stats = []
            for row in cursor.fetchall():
                agent_stats.append({
                    'agent_id': row[1],
                    'agent_type': row[2],
                    'total_tasks': row[3],
                    'successful_tasks': row[4],
                    'failed_tasks': row[5],
                    'total_cost': row[6],
                    'total_tokens': row[7],
                    'avg_response_time': row[8],
                    'success_rate': row[10],
                    'cost_per_task': row[11],
                    'tokens_per_task': row[12],
                    'last_active': row[9]
                })
            
            # Get recent alerts
            cursor.execute("""
                SELECT * FROM alerts 
                WHERE resolved = FALSE 
                ORDER BY timestamp DESC 
                LIMIT 10
            """)
            
            active_alerts = []
            for row in cursor.fetchall():
                active_alerts.append({
                    'alert_id': row[1],
                    'level': row[2],
                    'title': row[3],
                    'description': row[4],
                    'agent_id': row[8],
                    'timestamp': row[9]
                })
            
            conn.close()
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'overall_stats': {
                    'total_agents': overall_stats[0] or 0,
                    'total_tasks': overall_stats[1] or 0,
                    'successful_tasks': overall_stats[2] or 0,
                    'failed_tasks': overall_stats[3] or 0,
                    'total_cost': overall_stats[4] or 0.0,
                    'avg_success_rate': overall_stats[5] or 0.0,
                    'avg_response_time': overall_stats[6] or 0.0
                },
                'agent_stats': agent_stats,
                'active_alerts': active_alerts,
                'provider_stats': dict(self.provider_stats)
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {'error': str(e)}
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over time"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get hourly task completion trends
            since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m-%d %H:00:00', completed_at) as hour,
                    COUNT(*) as tasks_completed,
                    AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                    AVG(duration_ms) as avg_duration,
                    SUM(cost) as total_cost,
                    SUM(tokens_used) as total_tokens
                FROM task_execution_timeline 
                WHERE completed_at >= ? 
                GROUP BY hour 
                ORDER BY hour
            """, (since_time,))
            
            hourly_trends = []
            for row in cursor.fetchall():
                hourly_trends.append({
                    'hour': row[0],
                    'tasks_completed': row[1],
                    'success_rate': row[2] or 0.0,
                    'avg_duration': row[3] or 0.0,
                    'total_cost': row[4] or 0.0,
                    'total_tokens': row[5] or 0
                })
            
            # Get agent type performance comparison
            cursor.execute("""
                SELECT 
                    agent_type,
                    COUNT(*) as total_tasks,
                    AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                    AVG(duration_ms) as avg_duration,
                    SUM(cost) as total_cost
                FROM task_execution_timeline 
                WHERE completed_at >= ? 
                GROUP BY agent_type 
                ORDER BY total_tasks DESC
            """, (since_time,))
            
            agent_type_performance = []
            for row in cursor.fetchall():
                agent_type_performance.append({
                    'agent_type': row[0],
                    'total_tasks': row[1],
                    'success_rate': row[2] or 0.0,
                    'avg_duration': row[3] or 0.0,
                    'total_cost': row[4] or 0.0
                })
            
            conn.close()
            
            return {
                'time_range_hours': hours,
                'hourly_trends': hourly_trends,
                'agent_type_performance': agent_type_performance
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance trends: {e}")
            return {'error': str(e)}
    
    def _start_background_processing(self):
        """Start background thread for periodic data aggregation"""
        def background_worker():
            while True:
                try:
                    # Aggregate hourly data every hour
                    self._aggregate_hourly_data()
                    # Clean old metrics (keep 30 days)
                    self._cleanup_old_data()
                    time.sleep(3600)  # Run every hour
                except Exception as e:
                    logger.error(f"Background processing error: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()
        logger.info("📊 Background analytics processing started")
    
    def _aggregate_hourly_data(self):
        """Aggregate performance data by hour"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the last hour that was aggregated
            cursor.execute("SELECT MAX(hour_timestamp) FROM hourly_performance")
            last_aggregated = cursor.fetchone()[0]
            
            if last_aggregated:
                start_time = datetime.fromisoformat(last_aggregated) + timedelta(hours=1)
            else:
                start_time = datetime.now(timezone.utc) - timedelta(days=1)
            
            end_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
            
            # Aggregate data for each hour
            current_hour = start_time
            while current_hour < end_time:
                next_hour = current_hour + timedelta(hours=1)
                
                cursor.execute("""
                    SELECT 
                        agent_type,
                        COUNT(*) as tasks_completed,
                        AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                        AVG(duration_ms) as avg_response_time,
                        SUM(cost) as total_cost,
                        SUM(tokens_used) as total_tokens
                    FROM task_execution_timeline 
                    WHERE completed_at >= ? AND completed_at < ?
                    GROUP BY agent_type
                """, (current_hour, next_hour))
                
                for row in cursor.fetchall():
                    cursor.execute("""
                        INSERT OR REPLACE INTO hourly_performance 
                        (hour_timestamp, agent_type, tasks_completed, success_rate, 
                         avg_response_time, total_cost, total_tokens)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (current_hour, row[0], row[1], row[2], row[3], row[4], row[5]))
                
                current_hour = next_hour
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to aggregate hourly data: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old performance data to prevent database bloat"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Keep only 30 days of detailed metrics
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            cursor.execute("DELETE FROM performance_metrics WHERE timestamp < ?", (cutoff_date,))
            cursor.execute("DELETE FROM task_execution_timeline WHERE completed_at < ?", (cutoff_date,))
            cursor.execute("DELETE FROM alerts WHERE timestamp < ? AND resolved = 1", (cutoff_date,))
            
            conn.commit()
            conn.close()
            
            logger.info("🧹 Cleaned up old performance data")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")

# Global performance tracker instance
performance_tracker = PerformanceTracker()

def integrate_with_orchestrator():
    """Integration function to connect with the real agent orchestrator"""
    try:
        from real_agent_orchestrator import real_orchestrator
        
        # Monkey patch the orchestrator to report performance metrics
        original_execute_task = real_orchestrator._execute_task_with_agent
        
        async def enhanced_execute_task(task, agent):
            start_time = time.time()
            
            try:
                result = await original_execute_task(task, agent)
                
                # Calculate performance metrics
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                # Extract provider from task metadata
                provider = getattr(task, 'metadata', {}).get('provider_used', 'unknown')
                if hasattr(task, 'metadata') and task.metadata and 'provider_used' in task.metadata:
                    provider = task.metadata['provider_used']
                
                # Report performance metrics
                performance_data = {
                    'task_id': task.id,
                    'agent_id': agent.agent_id,
                    'agent_type': agent.agent_type.value,
                    'task_name': task.name,
                    'success': result.get('success', False),
                    'duration_ms': duration_ms,
                    'tokens_used': task.tokens_used,
                    'cost': task.cost,
                    'provider': provider,
                    'started_at': task.started_at,
                    'completed_at': task.completed_at,
                    'status': task.status.value,
                    'error_message': task.error,
                    'files_created': task.files_created or [],
                    'files_modified': task.files_modified or []
                }
                
                performance_tracker.record_task_execution(performance_data)
                
                return result
                
            except Exception as e:
                # Record failed task
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                performance_data = {
                    'task_id': task.id,
                    'agent_id': agent.agent_id,
                    'agent_type': agent.agent_type.value,
                    'task_name': task.name,
                    'success': False,
                    'duration_ms': duration_ms,
                    'tokens_used': 0,
                    'cost': 0.0,
                    'provider': 'unknown',
                    'started_at': task.started_at,
                    'completed_at': datetime.now(timezone.utc),
                    'status': 'failed',
                    'error_message': str(e),
                    'files_created': [],
                    'files_modified': []
                }
                
                performance_tracker.record_task_execution(performance_data)
                raise e
        
        # Replace the method
        real_orchestrator._execute_task_with_agent = enhanced_execute_task
        
        logger.info("✅ Agent performance monitoring integrated with orchestrator")
        
    except ImportError:
        logger.warning("❌ Could not integrate with orchestrator - module not found")
    except Exception as e:
        logger.error(f"Failed to integrate with orchestrator: {e}")

if __name__ == "__main__":
    # Test the performance tracker
    print("🚀 Agent Performance Monitor Test")
    
    # Simulate some task executions
    test_tasks = [
        {
            'task_id': 'test_001',
            'agent_id': 'code_dev_01',
            'agent_type': 'code_developer',
            'task_name': 'Build API Integration',
            'success': True,
            'duration_ms': 15000,
            'tokens_used': 2500,
            'cost': 0.125,
            'provider': 'anthropic',
            'started_at': datetime.now(timezone.utc) - timedelta(seconds=15),
            'completed_at': datetime.now(timezone.utc),
            'status': 'completed',
            'files_created': ['api_client.py'],
            'files_modified': ['main.py']
        },
        {
            'task_id': 'test_002',
            'agent_id': 'sys_analyst_01',
            'agent_type': 'system_analyst',
            'task_name': 'System Analysis',
            'success': True,
            'duration_ms': 8000,
            'tokens_used': 1800,
            'cost': 0.089,
            'provider': 'anthropic',
            'started_at': datetime.now(timezone.utc) - timedelta(seconds=8),
            'completed_at': datetime.now(timezone.utc),
            'status': 'completed',
            'files_created': [],
            'files_modified': []
        }
    ]
    
    for task_data in test_tasks:
        performance_tracker.record_task_execution(task_data)
    
    # Get performance summary
    summary = performance_tracker.get_agent_performance_summary()
    print("\n📊 Performance Summary:")
    print(json.dumps(summary, indent=2, default=str))
    
    print("\n✅ Performance monitoring system tested successfully!")