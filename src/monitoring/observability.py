import asyncio
import json
import time
import threading
import traceback
import psutil
import statistics
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from pathlib import Path
import logging
import uuid

# Prometheus and monitoring imports
try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
    from prometheus_client.exposition import start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("Warning: prometheus_client not available. Install with: pip install prometheus_client")

# Grafana and alerting imports
try:
    import requests
    import numpy as np
    from scipy import stats
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests/numpy/scipy not available for advanced features")

from loguru import logger


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertStatus(Enum):
    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class MetricDefinition:
    name: str
    metric_type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None


@dataclass
class Alert:
    id: str
    name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    threshold: float
    current_value: float
    metric_name: str
    condition: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    escalation_level: int = 0
    notification_channels: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    name: str
    metric_name: str
    condition: str  # e.g., "gt", "lt", "eq", "anomaly"
    threshold: float
    severity: AlertSeverity
    duration: int  # seconds
    description: str
    enabled: bool = True
    notification_channels: List[str] = field(default_factory=list)
    escalation_rules: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TaskMetrics:
    task_id: str
    agent_id: str
    task_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: Optional[bool] = None
    duration_ms: Optional[float] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMetrics:
    agent_id: str
    agent_type: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_response_time_ms: float = 0.0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    last_activity: Optional[datetime] = None
    performance_score: float = 0.0
    resource_usage: Dict[str, float] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_io: Dict[str, int] = field(default_factory=dict)
    active_tasks: int = 0
    active_agents: int = 0
    queue_depth: int = 0


@dataclass
class TraceEvent:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "success"  # success, error, timeout


@dataclass
class ExecutionSnapshot:
    snapshot_id: str
    timestamp: datetime
    task_id: str
    agent_id: str
    state: Dict[str, Any]
    call_stack: List[str]
    variables: Dict[str, Any]
    memory_state: Dict[str, Any]
    decisions: List[Dict[str, Any]]


class AnomalyDetector:
    """Statistical anomaly detection for metrics."""
    
    def __init__(self, window_size: int = 100, threshold_factor: float = 3.0):
        self.window_size = window_size
        self.threshold_factor = threshold_factor
        self.metric_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
    
    def add_value(self, metric_name: str, value: float):
        """Add a new value to the metric window."""
        self.metric_windows[metric_name].append(value)
    
    def is_anomaly(self, metric_name: str, value: float) -> bool:
        """Detect if a value is anomalous using statistical methods."""
        window = self.metric_windows[metric_name]
        
        if len(window) < 10:  # Need minimum data points
            return False
        
        try:
            if REQUESTS_AVAILABLE:
                # Use z-score method
                mean = np.mean(window)
                std = np.std(window)
                z_score = abs((value - mean) / std) if std > 0 else 0
                return z_score > self.threshold_factor
            else:
                # Fallback to simple statistical method
                mean = statistics.mean(window)
                stdev = statistics.stdev(window) if len(window) > 1 else 0
                z_score = abs((value - mean) / stdev) if stdev > 0 else 0
                return z_score > self.threshold_factor
        except:
            return False
    
    def get_statistics(self, metric_name: str) -> Dict[str, float]:
        """Get statistical summary of a metric."""
        window = self.metric_windows[metric_name]
        
        if not window:
            return {}
        
        try:
            if REQUESTS_AVAILABLE:
                return {
                    "mean": float(np.mean(window)),
                    "std": float(np.std(window)),
                    "min": float(np.min(window)),
                    "max": float(np.max(window)),
                    "median": float(np.median(window))
                }
            else:
                return {
                    "mean": statistics.mean(window),
                    "min": min(window),
                    "max": max(window),
                    "median": statistics.median(window)
                }
        except:
            return {}


class NotificationChannel:
    """Base class for notification channels."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send notification for an alert."""
        raise NotImplementedError


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel."""
    
    async def send_notification(self, alert: Alert) -> bool:
        if not REQUESTS_AVAILABLE or not self.enabled:
            return False
        
        try:
            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                return False
            
            payload = {
                "alert_id": alert.id,
                "name": alert.name,
                "description": alert.description,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "metric_name": alert.metric_name,
                "current_value": alert.current_value,
                "threshold": alert.threshold,
                "created_at": alert.created_at.isoformat(),
                "metadata": alert.metadata
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=self.config.get("timeout", 10),
                headers={"Content-Type": "application/json"}
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel with SMTP integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_server = config.get("smtp_server", "localhost")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_username = config.get("smtp_username")
        self.smtp_password = config.get("smtp_password")
        self.sender_email = config.get("sender_email", "alerts@autonomous-agents.com")
        self.recipient_emails = config.get("recipient_emails", [])
        self.use_tls = config.get("use_tls", True)
    
    async def send_notification(self, alert: Alert) -> bool:
        if not self.enabled or not self.recipient_emails:
            logger.warning("Email notifications disabled or no recipients configured")
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.utils import formatdate
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipient_emails)
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = f"[{alert.severity.upper()}] {alert.name}"
            
            # Email body
            body = f"""
Alert: {alert.name}
Severity: {alert.severity}
Component: {alert.component}
Time: {alert.timestamp}

Description:
{alert.description}

Metrics:
{chr(10).join(f'- {k}: {v}' for k, v in alert.metrics.items())}

Additional Info:
{chr(10).join(f'- {k}: {v}' for k, v in alert.additional_info.items())}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent for alert: {alert.name}")
            return True
            
        except ImportError:
            logger.warning("Email functionality requires smtplib (not available)")
            return False
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel."""
    
    async def send_notification(self, alert: Alert) -> bool:
        if not REQUESTS_AVAILABLE or not self.enabled:
            return False
        
        try:
            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                return False
            
            color_map = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff9900",
                AlertSeverity.CRITICAL: "#ff0000",
                AlertSeverity.EMERGENCY: "#8B0000"
            }
            
            payload = {
                "attachments": [{
                    "color": color_map.get(alert.severity, "#36a64f"),
                    "title": f"🚨 {alert.name}",
                    "text": alert.description,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                        {"title": "Metric", "value": alert.metric_name, "short": True},
                        {"title": "Current Value", "value": str(alert.current_value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold), "short": True}
                    ],
                    "timestamp": alert.created_at.timestamp()
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class PrometheusExporter:
    """Prometheus metrics exporter."""
    
    def __init__(self, port: int = 8000):
        self.port = port
        self.registry = CollectorRegistry()
        self.metrics: Dict[str, Any] = {}
        self.server_started = False
        
        if PROMETHEUS_AVAILABLE:
            self._initialize_default_metrics()
    
    def _initialize_default_metrics(self):
        """Initialize default Prometheus metrics."""
        # Task metrics
        self.metrics["task_total"] = Counter(
            "autonomous_agent_tasks_total",
            "Total number of tasks",
            ["agent_id", "task_type", "status"],
            registry=self.registry
        )
        
        self.metrics["task_duration"] = Histogram(
            "autonomous_agent_task_duration_seconds",
            "Task execution duration",
            ["agent_id", "task_type"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 300.0],
            registry=self.registry
        )
        
        self.metrics["task_cost"] = Summary(
            "autonomous_agent_task_cost_usd",
            "Task execution cost in USD",
            ["agent_id", "task_type"],
            registry=self.registry
        )
        
        # Agent metrics
        self.metrics["agent_performance"] = Gauge(
            "autonomous_agent_performance_score",
            "Agent performance score",
            ["agent_id", "agent_type"],
            registry=self.registry
        )
        
        self.metrics["agent_tokens"] = Counter(
            "autonomous_agent_tokens_total",
            "Total tokens used by agent",
            ["agent_id", "agent_type"],
            registry=self.registry
        )
        
        # System metrics
        self.metrics["system_cpu"] = Gauge(
            "autonomous_agent_cpu_percent",
            "CPU usage percentage",
            registry=self.registry
        )
        
        self.metrics["system_memory"] = Gauge(
            "autonomous_agent_memory_percent",
            "Memory usage percentage",
            registry=self.registry
        )
        
        self.metrics["system_active_tasks"] = Gauge(
            "autonomous_agent_active_tasks",
            "Number of active tasks",
            registry=self.registry
        )
        
        # Error metrics
        self.metrics["errors_total"] = Counter(
            "autonomous_agent_errors_total",
            "Total number of errors",
            ["error_type", "component"],
            registry=self.registry
        )
    
    def start_server(self):
        """Start Prometheus metrics server."""
        if not PROMETHEUS_AVAILABLE or self.server_started:
            return
        
        try:
            start_http_server(self.port, registry=self.registry)
            self.server_started = True
            logger.info(f"Prometheus metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
    
    def record_task_metric(self, task_metrics: TaskMetrics):
        """Record task metrics to Prometheus."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        status = "success" if task_metrics.success else "failed"
        
        self.metrics["task_total"].labels(
            agent_id=task_metrics.agent_id,
            task_type=task_metrics.task_type,
            status=status
        ).inc()
        
        if task_metrics.duration_ms:
            self.metrics["task_duration"].labels(
                agent_id=task_metrics.agent_id,
                task_type=task_metrics.task_type
            ).observe(task_metrics.duration_ms / 1000)
        
        if task_metrics.cost_usd > 0:
            self.metrics["task_cost"].labels(
                agent_id=task_metrics.agent_id,
                task_type=task_metrics.task_type
            ).observe(task_metrics.cost_usd)
        
        if task_metrics.tokens_used > 0:
            # Note: We need agent_type for this metric
            # This would need to be passed in or looked up
            pass
    
    def record_agent_metric(self, agent_metrics: AgentMetrics):
        """Record agent metrics to Prometheus."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.metrics["agent_performance"].labels(
            agent_id=agent_metrics.agent_id,
            agent_type=agent_metrics.agent_type
        ).set(agent_metrics.performance_score)
        
        self.metrics["agent_tokens"].labels(
            agent_id=agent_metrics.agent_id,
            agent_type=agent_metrics.agent_type
        ).inc(agent_metrics.total_tokens_used)
    
    def record_system_metric(self, system_metrics: SystemMetrics):
        """Record system metrics to Prometheus."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.metrics["system_cpu"].set(system_metrics.cpu_percent)
        self.metrics["system_memory"].set(system_metrics.memory_percent)
        self.metrics["system_active_tasks"].set(system_metrics.active_tasks)
    
    def record_error(self, error_type: str, component: str):
        """Record error metric."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.metrics["errors_total"].labels(
            error_type=error_type,
            component=component
        ).inc()


class TraceCollector:
    """Distributed tracing collector."""
    
    def __init__(self, max_traces: int = 10000):
        self.max_traces = max_traces
        self.traces: Dict[str, List[TraceEvent]] = {}
        self.active_spans: Dict[str, TraceEvent] = {}
        self.lock = threading.RLock()
    
    def start_span(self, operation_name: str, parent_span_id: Optional[str] = None, 
                   trace_id: Optional[str] = None, tags: Optional[Dict[str, Any]] = None) -> str:
        """Start a new trace span."""
        span_id = str(uuid.uuid4())
        trace_id = trace_id or str(uuid.uuid4())
        
        span = TraceEvent(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.now(),
            end_time=None,
            duration_ms=None,
            tags=tags or {},
            logs=[]
        )
        
        with self.lock:
            self.active_spans[span_id] = span
            
            if trace_id not in self.traces:
                self.traces[trace_id] = []
            
            # Limit traces to prevent memory issues
            if len(self.traces) > self.max_traces:
                oldest_trace = min(self.traces.keys())
                del self.traces[oldest_trace]
        
        return span_id
    
    def finish_span(self, span_id: str, status: str = "success", tags: Optional[Dict[str, Any]] = None):
        """Finish a trace span."""
        with self.lock:
            if span_id not in self.active_spans:
                return
            
            span = self.active_spans.pop(span_id)
            span.end_time = datetime.now()
            span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
            span.status = status
            
            if tags:
                span.tags.update(tags)
            
            self.traces[span.trace_id].append(span)
    
    def add_log(self, span_id: str, message: str, level: str = "info", **kwargs):
        """Add a log entry to a span."""
        with self.lock:
            if span_id in self.active_spans:
                self.active_spans[span_id].logs.append({
                    "timestamp": datetime.now().isoformat(),
                    "level": level,
                    "message": message,
                    **kwargs
                })
    
    def get_trace(self, trace_id: str) -> List[TraceEvent]:
        """Get all spans for a trace."""
        return self.traces.get(trace_id, [])
    
    def get_active_spans(self) -> List[TraceEvent]:
        """Get all currently active spans."""
        with self.lock:
            return list(self.active_spans.values())


class ExecutionRecorder:
    """Records execution states for debugging and replay."""
    
    def __init__(self, max_snapshots: int = 1000):
        self.max_snapshots = max_snapshots
        self.snapshots: Dict[str, List[ExecutionSnapshot]] = defaultdict(list)
        self.lock = threading.RLock()
    
    def record_snapshot(self, task_id: str, agent_id: str, state: Dict[str, Any],
                       call_stack: List[str], variables: Dict[str, Any],
                       memory_state: Dict[str, Any], decisions: List[Dict[str, Any]]):
        """Record an execution snapshot."""
        snapshot = ExecutionSnapshot(
            snapshot_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            task_id=task_id,
            agent_id=agent_id,
            state=state.copy(),
            call_stack=call_stack.copy(),
            variables=variables.copy(),
            memory_state=memory_state.copy(),
            decisions=decisions.copy()
        )
        
        with self.lock:
            self.snapshots[task_id].append(snapshot)
            
            # Limit snapshots per task
            if len(self.snapshots[task_id]) > self.max_snapshots:
                self.snapshots[task_id].pop(0)
    
    def get_snapshots(self, task_id: str) -> List[ExecutionSnapshot]:
        """Get all snapshots for a task."""
        return self.snapshots.get(task_id, [])
    
    def replay_execution(self, task_id: str, snapshot_id: Optional[str] = None) -> Optional[ExecutionSnapshot]:
        """Get a specific snapshot for replay."""
        snapshots = self.snapshots.get(task_id, [])
        
        if not snapshots:
            return None
        
        if snapshot_id:
            for snapshot in snapshots:
                if snapshot.snapshot_id == snapshot_id:
                    return snapshot
        
        # Return latest snapshot if no specific ID requested
        return snapshots[-1]


class DashboardGenerator:
    """Generates monitoring dashboards."""
    
    def __init__(self):
        self.panels = []
    
    def generate_grafana_dashboard(self) -> Dict[str, Any]:
        """Generate a Grafana dashboard configuration."""
        return {
            "dashboard": {
                "id": None,
                "title": "Autonomous Multi-LLM Agent Monitoring",
                "description": "Comprehensive monitoring dashboard for the autonomous agent system",
                "tags": ["autonomous", "llm", "agent", "monitoring"],
                "timezone": "browser",
                "refresh": "5s",
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "panels": [
                    {
                        "id": 1,
                        "title": "Task Completion Rate",
                        "type": "stat",
                        "targets": [{
                            "expr": "rate(autonomous_agent_tasks_total{status=\"success\"}[5m]) / rate(autonomous_agent_tasks_total[5m]) * 100",
                            "legendFormat": "Success Rate %"
                        }],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Agent Performance Scores",
                        "type": "timeseries",
                        "targets": [{
                            "expr": "autonomous_agent_performance_score",
                            "legendFormat": "{{agent_id}}"
                        }],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "System Resource Usage",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "autonomous_agent_cpu_percent",
                                "legendFormat": "CPU %"
                            },
                            {
                                "expr": "autonomous_agent_memory_percent",
                                "legendFormat": "Memory %"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
                    },
                    {
                        "id": 4,
                        "title": "Task Duration Distribution",
                        "type": "histogram",
                        "targets": [{
                            "expr": "autonomous_agent_task_duration_seconds",
                            "legendFormat": "{{agent_id}}"
                        }],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
                    },
                    {
                        "id": 5,
                        "title": "Error Rate by Component",
                        "type": "timeseries",
                        "targets": [{
                            "expr": "rate(autonomous_agent_errors_total[5m])",
                            "legendFormat": "{{component}} - {{error_type}}"
                        }],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
                    },
                    {
                        "id": 6,
                        "title": "Cost Tracking",
                        "type": "stat",
                        "targets": [{
                            "expr": "increase(autonomous_agent_task_cost_usd_sum[1h])",
                            "legendFormat": "Hourly Cost USD"
                        }],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 24}
                    }
                ]
            }
        }


class ObservabilitySystem:
    """Comprehensive observability system for autonomous multi-LLM agents."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", True)
        
        # Core components
        self.prometheus_exporter = PrometheusExporter(config.get("prometheus_port", 8000))
        self.anomaly_detector = AnomalyDetector(
            window_size=config.get("anomaly_window_size", 100),
            threshold_factor=config.get("anomaly_threshold", 3.0)
        )
        self.trace_collector = TraceCollector(config.get("max_traces", 10000))
        self.execution_recorder = ExecutionRecorder(config.get("max_snapshots", 1000))
        self.dashboard_generator = DashboardGenerator()
        
        # Metrics storage
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.system_metrics_history: deque = deque(maxlen=1000)
        
        # Alerting
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        
        # Background tasks
        self.running = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.alert_thread: Optional[threading.Thread] = None
        
        # Locks
        self.metrics_lock = threading.RLock()
        self.alerts_lock = threading.RLock()
        
        self._initialize_notification_channels()
        self._load_default_alert_rules()
        
        logger.info("ObservabilitySystem initialized")
    
    def _initialize_notification_channels(self):
        """Initialize notification channels from config."""
        channels_config = self.config.get("notification_channels", {})
        
        for channel_name, channel_config in channels_config.items():
            channel_type = channel_config.get("type", "webhook")
            
            if channel_type == "webhook":
                self.notification_channels[channel_name] = WebhookNotificationChannel(channel_name, channel_config)
            elif channel_type == "slack":
                self.notification_channels[channel_name] = SlackNotificationChannel(channel_name, channel_config)
            elif channel_type == "email":
                self.notification_channels[channel_name] = EmailNotificationChannel(channel_name, channel_config)
    
    def _load_default_alert_rules(self):
        """Load default alert rules."""
        default_rules = [
            AlertRule(
                name="High Task Failure Rate",
                metric_name="task_failure_rate",
                condition="gt",
                threshold=0.2,  # 20% failure rate
                severity=AlertSeverity.WARNING,
                duration=300,  # 5 minutes
                description="Task failure rate is above 20%",
                notification_channels=["default"]
            ),
            AlertRule(
                name="High CPU Usage",
                metric_name="cpu_percent",
                condition="gt",
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                duration=300,
                description="CPU usage is above 80%",
                notification_channels=["default"]
            ),
            AlertRule(
                name="High Memory Usage",
                metric_name="memory_percent",
                condition="gt",
                threshold=90.0,
                severity=AlertSeverity.CRITICAL,
                duration=180,
                description="Memory usage is above 90%",
                notification_channels=["default"]
            ),
            AlertRule(
                name="Agent Performance Drop",
                metric_name="agent_performance",
                condition="lt",
                threshold=0.5,
                severity=AlertSeverity.WARNING,
                duration=600,
                description="Agent performance score dropped below 0.5",
                notification_channels=["default"]
            ),
            AlertRule(
                name="Anomalous Response Time",
                metric_name="task_duration",
                condition="anomaly",
                threshold=0.0,  # Not used for anomaly detection
                severity=AlertSeverity.INFO,
                duration=0,
                description="Detected anomalous task response times",
                notification_channels=["default"]
            )
        ]
        
        self.alert_rules.extend(default_rules)
    
    def start(self):
        """Start the observability system."""
        if not self.enabled or self.running:
            return
        
        self.running = True
        
        # Start Prometheus server
        self.prometheus_exporter.start_server()
        
        # Start monitoring threads
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.alert_thread = threading.Thread(target=self._alerting_loop, daemon=True)
        self.alert_thread.start()
        
        logger.info("ObservabilitySystem started")
    
    def stop(self):
        """Stop the observability system."""
        self.running = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if self.alert_thread:
            self.alert_thread.join(timeout=5)
        
        logger.info("ObservabilitySystem stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        while self.running:
            try:
                self._collect_system_metrics()
                self._update_agent_performance_scores()
                time.sleep(self.config.get("monitoring_interval", 30))
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def _alerting_loop(self):
        """Background alerting loop."""
        while self.running:
            try:
                self._evaluate_alert_rules()
                self._process_alerts()
                time.sleep(self.config.get("alert_evaluation_interval", 10))
            except Exception as e:
                logger.error(f"Error in alerting loop: {e}")
                time.sleep(5)
    
    def _collect_system_metrics(self):
        """Collect system resource metrics."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            system_metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                disk_usage_percent=disk.percent,
                network_io={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv
                },
                active_tasks=len(self.task_metrics),
                active_agents=len(self.agent_metrics),
                queue_depth=0  # Would need to integrate with task queue
            )
            
            with self.metrics_lock:
                self.system_metrics_history.append(system_metrics)
            
            # Record to Prometheus
            self.prometheus_exporter.record_system_metric(system_metrics)
            
            # Add to anomaly detection
            self.anomaly_detector.add_value("cpu_percent", cpu_percent)
            self.anomaly_detector.add_value("memory_percent", memory.percent)
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def _update_agent_performance_scores(self):
        """Update agent performance scores."""
        with self.metrics_lock:
            for agent_id, metrics in self.agent_metrics.items():
                if metrics.total_tasks > 0:
                    success_rate = metrics.successful_tasks / metrics.total_tasks
                    
                    # Simple performance score calculation
                    # In practice, this would be more sophisticated
                    performance_score = success_rate * 0.7 + \
                                      (1 / max(metrics.avg_response_time_ms / 1000, 1)) * 0.3
                    
                    metrics.performance_score = min(performance_score, 1.0)
                    
                    # Record to Prometheus
                    self.prometheus_exporter.record_agent_metric(metrics)
    
    def _evaluate_alert_rules(self):
        """Evaluate alert rules against current metrics."""
        current_time = datetime.now()
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            try:
                should_alert = False
                current_value = 0.0
                
                if rule.condition == "anomaly":
                    # Special handling for anomaly detection
                    should_alert = self._check_anomaly_condition(rule)
                else:
                    current_value = self._get_metric_value(rule.metric_name)
                    should_alert = self._evaluate_condition(rule.condition, current_value, rule.threshold)
                
                alert_id = f"{rule.name}_{rule.metric_name}"
                
                if should_alert:
                    if alert_id not in self.active_alerts:
                        # Create new alert
                        alert = Alert(
                            id=alert_id,
                            name=rule.name,
                            description=rule.description,
                            severity=rule.severity,
                            status=AlertStatus.PENDING,
                            threshold=rule.threshold,
                            current_value=current_value,
                            metric_name=rule.metric_name,
                            condition=rule.condition,
                            created_at=current_time,
                            updated_at=current_time,
                            notification_channels=rule.notification_channels
                        )
                        
                        with self.alerts_lock:
                            self.active_alerts[alert_id] = alert
                        
                        logger.warning(f"Alert triggered: {rule.name}")
                    else:
                        # Update existing alert
                        alert = self.active_alerts[alert_id]
                        alert.current_value = current_value
                        alert.updated_at = current_time
                        
                        # Check if alert should fire (duration threshold met)
                        if alert.status == AlertStatus.PENDING:
                            duration = (current_time - alert.created_at).total_seconds()
                            if duration >= rule.duration:
                                alert.status = AlertStatus.FIRING
                                logger.error(f"Alert firing: {rule.name}")
                else:
                    # Resolve alert if it exists
                    if alert_id in self.active_alerts:
                        alert = self.active_alerts[alert_id]
                        if alert.status in [AlertStatus.PENDING, AlertStatus.FIRING]:
                            alert.status = AlertStatus.RESOLVED
                            alert.resolved_at = current_time
                            alert.updated_at = current_time
                            logger.info(f"Alert resolved: {rule.name}")
            
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule.name}: {e}")
    
    def _check_anomaly_condition(self, rule: AlertRule) -> bool:
        """Check if metric shows anomalous behavior."""
        if rule.metric_name == "task_duration":
            # Check recent task durations for anomalies
            recent_tasks = [
                metrics for metrics in self.task_metrics.values()
                if metrics.end_time and 
                   (datetime.now() - metrics.end_time).total_seconds() < 300 and
                   metrics.duration_ms is not None
            ]
            
            for task in recent_tasks:
                if self.anomaly_detector.is_anomaly("task_duration", task.duration_ms):
                    return True
        
        return False
    
    def _get_metric_value(self, metric_name: str) -> float:
        """Get current value for a metric."""
        if metric_name == "task_failure_rate":
            with self.metrics_lock:
                if not self.task_metrics:
                    return 0.0
                
                recent_tasks = [
                    metrics for metrics in self.task_metrics.values()
                    if metrics.end_time and 
                       (datetime.now() - metrics.end_time).total_seconds() < 300
                ]
                
                if not recent_tasks:
                    return 0.0
                
                failed_tasks = sum(1 for task in recent_tasks if not task.success)
                return failed_tasks / len(recent_tasks)
        
        elif metric_name == "cpu_percent":
            if self.system_metrics_history:
                return self.system_metrics_history[-1].cpu_percent
        
        elif metric_name == "memory_percent":
            if self.system_metrics_history:
                return self.system_metrics_history[-1].memory_percent
        
        elif metric_name == "agent_performance":
            with self.metrics_lock:
                if not self.agent_metrics:
                    return 1.0
                
                # Return minimum performance score
                return min(metrics.performance_score for metrics in self.agent_metrics.values())
        
        return 0.0
    
    def _evaluate_condition(self, condition: str, current_value: float, threshold: float) -> bool:
        """Evaluate alert condition."""
        if condition == "gt":
            return current_value > threshold
        elif condition == "lt":
            return current_value < threshold
        elif condition == "eq":
            return abs(current_value - threshold) < 0.001
        elif condition == "gte":
            return current_value >= threshold
        elif condition == "lte":
            return current_value <= threshold
        else:
            return False
    
    async def _process_alerts(self):
        """Process and send notifications for active alerts."""
        with self.alerts_lock:
            for alert in self.active_alerts.values():
                if alert.status == AlertStatus.FIRING:
                    await self._send_alert_notifications(alert)
    
    async def _send_alert_notifications(self, alert: Alert):
        """Send notifications for an alert."""
        for channel_name in alert.notification_channels:
            if channel_name in self.notification_channels:
                try:
                    success = await self.notification_channels[channel_name].send_notification(alert)
                    if success:
                        logger.info(f"Alert notification sent via {channel_name}: {alert.name}")
                    else:
                        logger.warning(f"Failed to send alert notification via {channel_name}: {alert.name}")
                except Exception as e:
                    logger.error(f"Error sending alert notification via {channel_name}: {e}")
    
    # Public API methods
    
    def record_task_start(self, task_id: str, agent_id: str, task_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record the start of a task."""
        span_id = self.trace_collector.start_span(
            f"task_{task_type}",
            tags={"task_id": task_id, "agent_id": agent_id, "task_type": task_type}
        )
        
        task_metrics = TaskMetrics(
            task_id=task_id,
            agent_id=agent_id,
            task_type=task_type,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        with self.metrics_lock:
            self.task_metrics[task_id] = task_metrics
            
            # Initialize agent metrics if not exists
            if agent_id not in self.agent_metrics:
                # We'd need agent_type from somewhere - defaulting to "unknown"
                self.agent_metrics[agent_id] = AgentMetrics(
                    agent_id=agent_id,
                    agent_type="unknown"
                )
        
        return span_id
    
    def record_task_end(self, task_id: str, span_id: str, success: bool, 
                       tokens_used: int = 0, cost_usd: float = 0.0,
                       error_type: Optional[str] = None, error_message: Optional[str] = None,
                       retry_count: int = 0):
        """Record the end of a task."""
        with self.metrics_lock:
            if task_id not in self.task_metrics:
                logger.warning(f"Task {task_id} not found in metrics")
                return
            
            task_metrics = self.task_metrics[task_id]
            task_metrics.end_time = datetime.now()
            task_metrics.success = success
            task_metrics.duration_ms = (task_metrics.end_time - task_metrics.start_time).total_seconds() * 1000
            task_metrics.tokens_used = tokens_used
            task_metrics.cost_usd = cost_usd
            task_metrics.error_type = error_type
            task_metrics.error_message = error_message
            task_metrics.retry_count = retry_count
            
            # Update agent metrics
            agent_metrics = self.agent_metrics.get(task_metrics.agent_id)
            if agent_metrics:
                agent_metrics.total_tasks += 1
                agent_metrics.total_tokens_used += tokens_used
                agent_metrics.total_cost_usd += cost_usd
                agent_metrics.last_activity = task_metrics.end_time
                
                if success:
                    agent_metrics.successful_tasks += 1
                else:
                    agent_metrics.failed_tasks += 1
                
                # Update average response time
                if agent_metrics.total_tasks > 0:
                    # Simple moving average - in practice might use exponential moving average
                    old_avg = agent_metrics.avg_response_time_ms
                    new_avg = (old_avg * (agent_metrics.total_tasks - 1) + task_metrics.duration_ms) / agent_metrics.total_tasks
                    agent_metrics.avg_response_time_ms = new_avg
        
        # Finish trace span
        status = "success" if success else "error"
        tags = {}
        if error_type:
            tags["error_type"] = error_type
        
        self.trace_collector.finish_span(span_id, status, tags)
        
        # Record to Prometheus
        self.prometheus_exporter.record_task_metric(task_metrics)
        
        # Record error if applicable
        if not success and error_type:
            self.prometheus_exporter.record_error(error_type, "task_execution")
    
    def record_agent_decision(self, agent_id: str, task_id: str, decision: Dict[str, Any]):
        """Record an agent decision for debugging."""
        # This would be called from agent code to track decision-making
        pass
    
    def record_execution_snapshot(self, task_id: str, agent_id: str, state: Dict[str, Any],
                                 call_stack: List[str], variables: Dict[str, Any],
                                 memory_state: Dict[str, Any], decisions: List[Dict[str, Any]]):
        """Record an execution snapshot for debugging."""
        self.execution_recorder.record_snapshot(
            task_id, agent_id, state, call_stack, variables, memory_state, decisions
        )
    
    def get_task_metrics(self, task_id: Optional[str] = None) -> Union[TaskMetrics, List[TaskMetrics]]:
        """Get task metrics."""
        with self.metrics_lock:
            if task_id:
                return self.task_metrics.get(task_id)
            else:
                return list(self.task_metrics.values())
    
    def get_agent_metrics(self, agent_id: Optional[str] = None) -> Union[AgentMetrics, List[AgentMetrics]]:
        """Get agent metrics."""
        with self.metrics_lock:
            if agent_id:
                return self.agent_metrics.get(agent_id)
            else:
                return list(self.agent_metrics.values())
    
    def get_system_metrics(self, limit: int = 100) -> List[SystemMetrics]:
        """Get recent system metrics."""
        return list(self.system_metrics_history)[-limit:]
    
    def get_trace(self, trace_id: str) -> List[TraceEvent]:
        """Get trace by ID."""
        return self.trace_collector.get_trace(trace_id)
    
    def get_execution_snapshots(self, task_id: str) -> List[ExecutionSnapshot]:
        """Get execution snapshots for a task."""
        return self.execution_recorder.get_snapshots(task_id)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        with self.alerts_lock:
            return [alert for alert in self.active_alerts.values() 
                   if alert.status in [AlertStatus.PENDING, AlertStatus.FIRING]]
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        with self.alerts_lock:
            return sorted(self.active_alerts.values(), 
                         key=lambda a: a.created_at, reverse=True)[:limit]
    
    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule."""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule."""
        self.alert_rules = [rule for rule in self.alert_rules if rule.name != rule_name]
        logger.info(f"Removed alert rule: {rule_name}")
    
    def generate_dashboard_config(self) -> Dict[str, Any]:
        """Generate dashboard configuration."""
        return self.dashboard_generator.generate_grafana_dashboard()
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in various formats."""
        if format == "json":
            with self.metrics_lock:
                return json.dumps({
                    "task_metrics": [asdict(m) for m in self.task_metrics.values()],
                    "agent_metrics": [asdict(m) for m in self.agent_metrics.values()],
                    "system_metrics": [asdict(m) for m in self.system_metrics_history],
                    "alerts": [asdict(a) for a in self.active_alerts.values()]
                }, default=str, indent=2)
        elif format == "prometheus" and PROMETHEUS_AVAILABLE:
            return generate_latest(self.prometheus_exporter.registry)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        with self.metrics_lock:
            total_tasks = len(self.task_metrics)
            successful_tasks = sum(1 for t in self.task_metrics.values() if t.success)
            
            success_rate = successful_tasks / total_tasks if total_tasks > 0 else 1.0
            
            # Get latest system metrics
            latest_system = self.system_metrics_history[-1] if self.system_metrics_history else None
            
            # Count active alerts by severity
            active_alerts = self.get_active_alerts()
            alert_counts = {
                "info": sum(1 for a in active_alerts if a.severity == AlertSeverity.INFO),
                "warning": sum(1 for a in active_alerts if a.severity == AlertSeverity.WARNING),
                "critical": sum(1 for a in active_alerts if a.severity == AlertSeverity.CRITICAL),
                "emergency": sum(1 for a in active_alerts if a.severity == AlertSeverity.EMERGENCY)
            }
            
            # Determine overall health
            if alert_counts["emergency"] > 0:
                health_status = "emergency"
            elif alert_counts["critical"] > 0:
                health_status = "critical"
            elif alert_counts["warning"] > 0:
                health_status = "warning"
            elif success_rate < 0.9:
                health_status = "degraded"
            else:
                health_status = "healthy"
            
            return {
                "status": health_status,
                "success_rate": success_rate,
                "total_tasks": total_tasks,
                "active_agents": len(self.agent_metrics),
                "active_alerts": len(active_alerts),
                "alert_counts": alert_counts,
                "system_metrics": {
                    "cpu_percent": latest_system.cpu_percent if latest_system else 0,
                    "memory_percent": latest_system.memory_percent if latest_system else 0,
                    "active_tasks": latest_system.active_tasks if latest_system else 0
                } if latest_system else {},
                "timestamp": datetime.now().isoformat()
            }


# Global observability instance
_observability_system: Optional[ObservabilitySystem] = None

def get_observability_system() -> Optional[ObservabilitySystem]:
    """Get the global observability system instance."""
    return _observability_system

def initialize_observability(config: Dict[str, Any]) -> ObservabilitySystem:
    """Initialize the global observability system."""
    global _observability_system
    _observability_system = ObservabilitySystem(config)
    return _observability_system