import asyncio
import json
import re
import time
import uuid
import sqlite3
import pickle
import hashlib
from typing import Dict, List, Any, Optional, Union, AsyncGenerator, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from pathlib import Path
import numpy as np
import psutil
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from loguru import logger
import threading
import queue


class ErrorSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorType(Enum):
    SYNTAX_ERROR = "syntax_error"
    LOGIC_ERROR = "logic_error"
    RUNTIME_ERROR = "runtime_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    SECURITY_VIOLATION = "security_violation"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    NETWORK_ERROR = "network_error"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class AnomalyType(Enum):
    STATISTICAL = "statistical"
    PATTERN_BASED = "pattern_based"
    THRESHOLD_BREACH = "threshold_breach"
    CORRELATION_ANOMALY = "correlation_anomaly"
    SEQUENCE_ANOMALY = "sequence_anomaly"


@dataclass
class ErrorEvent:
    event_id: str
    timestamp: datetime
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    process_id: Optional[str] = None
    agent_id: Optional[str] = None
    code_snippet: Optional[str] = None
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    resource_usage: Optional[Dict[str, float]] = None


@dataclass
class Anomaly:
    anomaly_id: str
    timestamp: datetime
    anomaly_type: AnomalyType
    severity: ErrorSeverity
    description: str
    affected_metrics: List[str]
    confidence_score: float
    deviation_score: float
    context: Dict[str, Any] = field(default_factory=dict)
    predicted_impact: Optional[str] = None


@dataclass
class FailureProbability:
    probability: float
    time_to_failure: Optional[timedelta]
    contributing_factors: List[str]
    confidence: float
    mitigation_suggestions: List[str]
    risk_level: ErrorSeverity


@dataclass
class RootCause:
    cause_id: str
    primary_cause: str
    contributing_factors: List[str]
    evidence: List[str]
    confidence_score: float
    suggested_fixes: List[str]
    similar_incidents: List[str]


@dataclass
class ErrorPattern:
    pattern_id: str
    pattern_type: str
    signature: str
    frequency: int
    last_seen: datetime
    error_types: List[ErrorType]
    contexts: List[Dict[str, Any]]
    resolution_success_rate: float


class ErrorStream:
    """Real-time error stream for monitoring execution."""
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.events = deque(maxlen=buffer_size)
        self.subscribers = []
        self.running = False
        self._lock = asyncio.Lock()
    
    async def add_event(self, event: ErrorEvent):
        """Add an error event to the stream."""
        async with self._lock:
            self.events.append(event)
            
            # Notify subscribers
            for callback in self.subscribers:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in stream subscriber: {e}")
    
    def subscribe(self, callback: Callable[[ErrorEvent], None]):
        """Subscribe to error events."""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[ErrorEvent], None]):
        """Unsubscribe from error events."""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    async def get_events(self, since: Optional[datetime] = None) -> List[ErrorEvent]:
        """Get events since a specific time."""
        async with self._lock:
            if since is None:
                return list(self.events)
            
            return [event for event in self.events if event.timestamp >= since]
    
    async def clear(self):
        """Clear the event buffer."""
        async with self._lock:
            self.events.clear()


class PatternRecognizer:
    """Recognizes patterns in error sequences and contexts."""
    
    def __init__(self):
        self.patterns = {}
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.pattern_db = {}
        self.sequence_patterns = defaultdict(list)
    
    def extract_error_signature(self, error: ErrorEvent) -> str:
        """Extract a signature from an error for pattern matching."""
        signature_parts = [
            error.error_type.value,
            self._normalize_message(error.message),
            str(error.line_number) if error.line_number else "unknown_line"
        ]
        
        # Add context information
        if error.context:
            context_str = "_".join(sorted(error.context.keys()))
            signature_parts.append(context_str)
        
        return "|".join(signature_parts)
    
    def _normalize_message(self, message: str) -> str:
        """Normalize error message for pattern matching."""
        # Remove specific details like file paths, line numbers, variable names
        normalized = re.sub(r'\b\d+\b', 'NUM', message)  # Replace numbers
        normalized = re.sub(r'/[^\s]+', 'PATH', normalized)  # Replace paths
        normalized = re.sub(r"'[^']*'", 'VAR', normalized)  # Replace quoted strings
        normalized = re.sub(r'"[^"]*"', 'VAR', normalized)  # Replace quoted strings
        normalized = re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', 'VAR', normalized)  # Replace identifiers
        
        return normalized.lower().strip()
    
    def learn_pattern(self, errors: List[ErrorEvent]) -> Optional[ErrorPattern]:
        """Learn a new pattern from a sequence of errors."""
        if not errors:
            return None
        
        # Extract common signature
        signatures = [self.extract_error_signature(error) for error in errors]
        common_signature = self._find_common_signature(signatures)
        
        # Determine pattern type
        pattern_type = self._classify_pattern_type(errors)
        
        # Calculate frequency and metadata
        pattern_id = hashlib.md5(common_signature.encode()).hexdigest()[:8]
        
        pattern = ErrorPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            signature=common_signature,
            frequency=len(errors),
            last_seen=max(error.timestamp for error in errors),
            error_types=list(set(error.error_type for error in errors)),
            contexts=[error.context for error in errors],
            resolution_success_rate=0.0  # Will be updated as resolutions are tracked
        )
        
        self.patterns[pattern_id] = pattern
        return pattern
    
    def _find_common_signature(self, signatures: List[str]) -> str:
        """Find common elements in signatures."""
        if len(signatures) == 1:
            return signatures[0]
        
        # Split signatures and find common parts
        signature_parts = [sig.split('|') for sig in signatures]
        common_parts = []
        
        for i in range(min(len(parts) for parts in signature_parts)):
            part_values = [parts[i] for parts in signature_parts]
            if len(set(part_values)) == 1:
                common_parts.append(part_values[0])
            else:
                common_parts.append('*')  # Wildcard for variable parts
        
        return '|'.join(common_parts)
    
    def _classify_pattern_type(self, errors: List[ErrorEvent]) -> str:
        """Classify the type of pattern based on error characteristics."""
        error_types = [error.error_type for error in errors]
        
        if len(set(error_types)) == 1:
            return "homogeneous"
        elif len(errors) > 1 and all(e1.timestamp < e2.timestamp for e1, e2 in zip(errors[:-1], errors[1:])):
            return "sequential"
        else:
            return "mixed"
    
    def match_pattern(self, error: ErrorEvent) -> Optional[ErrorPattern]:
        """Match an error against known patterns."""
        error_signature = self.extract_error_signature(error)
        
        for pattern in self.patterns.values():
            if self._signature_matches(error_signature, pattern.signature):
                return pattern
        
        return None
    
    def _signature_matches(self, error_sig: str, pattern_sig: str) -> bool:
        """Check if an error signature matches a pattern signature."""
        error_parts = error_sig.split('|')
        pattern_parts = pattern_sig.split('|')
        
        if len(error_parts) != len(pattern_parts):
            return False
        
        for error_part, pattern_part in zip(error_parts, pattern_parts):
            if pattern_part != '*' and error_part != pattern_part:
                return False
        
        return True


class AnomalyDetector:
    """Detects anomalies in system metrics and behavior."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # ML models for anomaly detection
        self.isolation_forest = IsolationForest(
            contamination=config.get('contamination', 0.1),
            random_state=42
        )
        
# DEMO CODE REMOVED: self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        self.scaler = StandardScaler()
        
        # Statistical thresholds
        self.thresholds = {
            'cpu_usage': config.get('cpu_threshold', 80.0),
            'memory_usage': config.get('memory_threshold', 80.0),
            'error_rate': config.get('error_rate_threshold', 0.1),
            'response_time': config.get('response_time_threshold', 5.0)
        }
        
        # Historical data for training
        self.historical_metrics = deque(maxlen=10000)
        self.is_trained = False
    
    def add_metrics(self, metrics: Dict[str, float], timestamp: datetime):
        """Add metrics data point for analysis."""
        metrics_with_time = {**metrics, 'timestamp': timestamp.timestamp()}
        self.historical_metrics.append(metrics_with_time)
        
        # Retrain periodically
        if len(self.historical_metrics) % 100 == 0:
            asyncio.create_task(self._retrain_models())
    
    async def detect_anomalies(self, current_metrics: Dict[str, float]) -> List[Anomaly]:
        """Detect anomalies in current metrics."""
        anomalies = []
        
        # Statistical anomaly detection
        stat_anomalies = self._detect_statistical_anomalies(current_metrics)
        anomalies.extend(stat_anomalies)
        
        # Threshold-based detection
        threshold_anomalies = self._detect_threshold_breaches(current_metrics)
        anomalies.extend(threshold_anomalies)
        
        # ML-based detection
        if self.is_trained:
            ml_anomalies = self._detect_ml_anomalies(current_metrics)
            anomalies.extend(ml_anomalies)
        
        # Correlation anomalies
        correlation_anomalies = self._detect_correlation_anomalies(current_metrics)
        anomalies.extend(correlation_anomalies)
        
        return anomalies
    
    def _detect_statistical_anomalies(self, metrics: Dict[str, float]) -> List[Anomaly]:
        """Detect anomalies using statistical methods."""
        anomalies = []
        
        if len(self.historical_metrics) < 30:
            return anomalies  # Need more data
        
        # Calculate z-scores for each metric
        for metric_name, current_value in metrics.items():
            if metric_name == 'timestamp':
                continue
            
            historical_values = [m.get(metric_name, 0) for m in self.historical_metrics if metric_name in m]
            
            if len(historical_values) < 10:
                continue
            
            mean_val = np.mean(historical_values)
            std_val = np.std(historical_values)
            
            if std_val > 0:
                z_score = abs((current_value - mean_val) / std_val)
                
                if z_score > 3:  # 3-sigma rule
                    anomaly = Anomaly(
                        anomaly_id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        anomaly_type=AnomalyType.STATISTICAL,
                        severity=ErrorSeverity.HIGH if z_score > 4 else ErrorSeverity.MEDIUM,
                        description=f"Statistical anomaly in {metric_name}: z-score={z_score:.2f}",
                        affected_metrics=[metric_name],
                        confidence_score=min(z_score / 4.0, 1.0),
                        deviation_score=z_score,
                        context={'z_score': z_score, 'mean': mean_val, 'std': std_val}
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_threshold_breaches(self, metrics: Dict[str, float]) -> List[Anomaly]:
        """Detect threshold breaches."""
        anomalies = []
        
        for metric_name, threshold in self.thresholds.items():
            if metric_name in metrics:
                current_value = metrics[metric_name]
                
                if current_value > threshold:
                    severity = ErrorSeverity.CRITICAL if current_value > threshold * 1.5 else ErrorSeverity.HIGH
                    
                    anomaly = Anomaly(
                        anomaly_id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        anomaly_type=AnomalyType.THRESHOLD_BREACH,
                        severity=severity,
                        description=f"Threshold breach: {metric_name}={current_value} > {threshold}",
                        affected_metrics=[metric_name],
                        confidence_score=1.0,
                        deviation_score=current_value / threshold,
                        context={'threshold': threshold, 'current_value': current_value}
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_ml_anomalies(self, metrics: Dict[str, float]) -> List[Anomaly]:
        """Detect anomalies using machine learning models."""
        anomalies = []
        
        try:
            # Prepare feature vector
            feature_names = [k for k in metrics.keys() if k != 'timestamp']
            features = np.array([[metrics.get(k, 0) for k in feature_names]])
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Isolation Forest prediction
            anomaly_score = self.isolation_forest.decision_function(features_scaled)[0]
            is_anomaly = self.isolation_forest.predict(features_scaled)[0] == -1
            
            if is_anomaly:
                anomaly = Anomaly(
                    anomaly_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    anomaly_type=AnomalyType.PATTERN_BASED,
                    severity=ErrorSeverity.MEDIUM,
                    description=f"ML-detected anomaly: score={anomaly_score:.3f}",
                    affected_metrics=feature_names,
                    confidence_score=abs(anomaly_score),
                    deviation_score=abs(anomaly_score),
                    context={'ml_score': anomaly_score}
                )
                anomalies.append(anomaly)
        
        except Exception as e:
            logger.error(f"ML anomaly detection failed: {e}")
        
        return anomalies
    
    def _detect_correlation_anomalies(self, metrics: Dict[str, float]) -> List[Anomaly]:
        """Detect anomalies in metric correlations."""
        anomalies = []
        
        # Check for unexpected correlations (e.g., high CPU but low memory usage)
        if 'cpu_usage' in metrics and 'memory_usage' in metrics:
            cpu = metrics['cpu_usage']
            memory = metrics['memory_usage']
            
            # Expect CPU and memory to be somewhat correlated under load
            if cpu > 70 and memory < 30:
                anomaly = Anomaly(
                    anomaly_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    anomaly_type=AnomalyType.CORRELATION_ANOMALY,
                    severity=ErrorSeverity.MEDIUM,
                    description=f"Unusual correlation: high CPU ({cpu}%) but low memory ({memory}%)",
                    affected_metrics=['cpu_usage', 'memory_usage'],
                    confidence_score=0.7,
                    deviation_score=abs(cpu - memory) / 100.0,
                    context={'cpu_usage': cpu, 'memory_usage': memory}
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    async def _retrain_models(self):
        """Retrain ML models with historical data."""
        try:
            if len(self.historical_metrics) < 100:
                return
            
            # Prepare training data
            feature_names = set()
            for metrics in self.historical_metrics:
                feature_names.update(k for k in metrics.keys() if k != 'timestamp')
            
            feature_names = sorted(list(feature_names))
            
            training_data = []
            for metrics in self.historical_metrics:
                features = [metrics.get(k, 0) for k in feature_names]
                training_data.append(features)
            
            training_data = np.array(training_data)
            
            # Fit scaler and models
            training_data_scaled = self.scaler.fit_transform(training_data)
            self.isolation_forest.fit(training_data_scaled)
            
            self.is_trained = True
            logger.info("Anomaly detection models retrained")
            
        except Exception as e:
            logger.error(f"Model retraining failed: {e}")


class FailurePredictor:
    """Predicts potential failures based on current system state."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        self.feature_names = []
        self.failure_patterns = {}
    
    async def predict_failure(self, current_state: Dict[str, Any]) -> FailureProbability:
        """Predict probability of failure based on current state."""
        
        # Rule-based predictions
        rule_based_prediction = self._rule_based_prediction(current_state)
        
        # ML-based predictions (if trained)
        ml_prediction = None
        if self.is_trained:
            ml_prediction = self._ml_based_prediction(current_state)
        
        # Combine predictions
        if ml_prediction:
            probability = (rule_based_prediction.probability + ml_prediction.probability) / 2
            contributing_factors = list(set(rule_based_prediction.contributing_factors + ml_prediction.contributing_factors))
            confidence = (rule_based_prediction.confidence + ml_prediction.confidence) / 2
        else:
            probability = rule_based_prediction.probability
            contributing_factors = rule_based_prediction.contributing_factors
            confidence = rule_based_prediction.confidence
        
        # Determine risk level
        if probability > 0.8:
            risk_level = ErrorSeverity.CRITICAL
        elif probability > 0.6:
            risk_level = ErrorSeverity.HIGH
        elif probability > 0.4:
            risk_level = ErrorSeverity.MEDIUM
        else:
            risk_level = ErrorSeverity.LOW
        
        # Estimate time to failure
        time_to_failure = self._estimate_time_to_failure(current_state, probability)
        
        # Generate mitigation suggestions
        mitigation_suggestions = self._generate_mitigation_suggestions(contributing_factors)
        
        return FailureProbability(
            probability=probability,
            time_to_failure=time_to_failure,
            contributing_factors=contributing_factors,
            confidence=confidence,
            mitigation_suggestions=mitigation_suggestions,
            risk_level=risk_level
        )
    
    def _rule_based_prediction(self, state: Dict[str, Any]) -> FailureProbability:
        """Rule-based failure prediction."""
        probability = 0.0
        contributing_factors = []
        
        # Resource exhaustion indicators
        if state.get('memory_usage', 0) > 90:
            probability += 0.3
            contributing_factors.append("High memory usage")
        
        if state.get('cpu_usage', 0) > 95:
            probability += 0.3
            contributing_factors.append("High CPU usage")
        
        if state.get('disk_usage', 0) > 95:
            probability += 0.4
            contributing_factors.append("High disk usage")
        
        # Error rate indicators
        error_rate = state.get('error_rate', 0)
        if error_rate > 0.1:
            probability += 0.2
            contributing_factors.append("High error rate")
        
        # Network issues
        if state.get('network_latency', 0) > 1000:  # ms
            probability += 0.15
            contributing_factors.append("High network latency")
        
        # Process count
        if state.get('process_count', 0) > 500:
            probability += 0.1
            contributing_factors.append("High process count")
        
        probability = min(probability, 1.0)
        
        return FailureProbability(
            probability=probability,
            time_to_failure=None,
            contributing_factors=contributing_factors,
            confidence=0.8,
            mitigation_suggestions=[],
            risk_level=ErrorSeverity.LOW
        )
    
    def _ml_based_prediction(self, state: Dict[str, Any]) -> Optional[FailureProbability]:
        """ML-based failure prediction."""
        try:
            # Prepare features
            features = [state.get(name, 0) for name in self.feature_names]
            features_array = np.array([features])
            
            # Predict
            probability = self.model.predict_proba(features_array)[0][1]  # Probability of failure
            
            # Get feature importance for contributing factors
            feature_importance = self.model.feature_importances_
            important_features = sorted(
                zip(self.feature_names, feature_importance),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            contributing_factors = [f"ML: {name}" for name, _ in important_features if _ > 0.1]
            
            return FailureProbability(
                probability=probability,
                time_to_failure=None,
                contributing_factors=contributing_factors,
                confidence=0.9,
                mitigation_suggestions=[],
                risk_level=ErrorSeverity.LOW
            )
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return None
    
    def _estimate_time_to_failure(self, state: Dict[str, Any], probability: float) -> Optional[timedelta]:
        """Estimate time until failure occurs."""
        if probability < 0.3:
            return None
        
        # Simple heuristic based on resource usage trends
        memory_usage = state.get('memory_usage', 0)
        cpu_usage = state.get('cpu_usage', 0)
        
        # Estimate based on resource exhaustion rate
        if memory_usage > 80:
            hours_to_failure = max(1, (100 - memory_usage) / 2)  # Rough estimate
            return timedelta(hours=hours_to_failure)
        
        if cpu_usage > 90:
            hours_to_failure = max(0.5, (100 - cpu_usage) / 5)
            return timedelta(hours=hours_to_failure)
        
        # Default estimate based on probability
        hours = max(1, (1 - probability) * 24)
        return timedelta(hours=hours)
    
    def _generate_mitigation_suggestions(self, factors: List[str]) -> List[str]:
        """Generate mitigation suggestions based on contributing factors."""
        suggestions = []
        
        for factor in factors:
            if "memory" in factor.lower():
                suggestions.append("Increase memory allocation or optimize memory usage")
            elif "cpu" in factor.lower():
                suggestions.append("Reduce CPU load or scale processing power")
            elif "disk" in factor.lower():
                suggestions.append("Free up disk space or add storage capacity")
            elif "error" in factor.lower():
                suggestions.append("Investigate and fix recurring errors")
            elif "network" in factor.lower():
                suggestions.append("Check network connectivity and optimize requests")
        
        return list(set(suggestions))  # Remove duplicates


class RootCauseAnalyzer:
    """Analyzes root causes of errors using multiple techniques."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.knowledge_base = {}
        self.correlation_cache = {}
    
    async def analyze_root_cause(self, error: ErrorEvent, context_events: List[ErrorEvent] = None) -> RootCause:
        """Perform comprehensive root cause analysis."""
        cause_id = str(uuid.uuid4())
        
        # Collect evidence from multiple sources
        evidence = []
        contributing_factors = []
        
        # Analyze the error itself
        primary_analysis = self._analyze_primary_error(error)
        evidence.extend(primary_analysis['evidence'])
        contributing_factors.extend(primary_analysis['factors'])
        
        # Analyze context events
        if context_events:
            context_analysis = self._analyze_context_events(error, context_events)
            evidence.extend(context_analysis['evidence'])
            contributing_factors.extend(context_analysis['factors'])
        
        # Check for known patterns
        pattern_analysis = self._analyze_error_patterns(error)
        if pattern_analysis:
            evidence.extend(pattern_analysis['evidence'])
            contributing_factors.extend(pattern_analysis['factors'])
        
        # Determine primary cause
        primary_cause = self._determine_primary_cause(error, contributing_factors)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(evidence, contributing_factors)
        
        # Generate suggested fixes
        suggested_fixes = self._generate_suggested_fixes(error, primary_cause, contributing_factors)
        
        # Find similar incidents
        similar_incidents = await self._find_similar_incidents(error)
        
        return RootCause(
            cause_id=cause_id,
            primary_cause=primary_cause,
            contributing_factors=contributing_factors,
            evidence=evidence,
            confidence_score=confidence_score,
            suggested_fixes=suggested_fixes,
            similar_incidents=similar_incidents
        )
    
    def _analyze_primary_error(self, error: ErrorEvent) -> Dict[str, List[str]]:
        """Analyze the primary error for clues."""
        evidence = []
        factors = []
        
        # Message analysis
        message = error.message.lower()
        
        if "memory" in message or "out of memory" in message:
            factors.append("Memory exhaustion")
            evidence.append(f"Error message indicates memory issue: {error.message}")
        
        if "timeout" in message or "timed out" in message:
            factors.append("Timeout/Performance issue")
            evidence.append(f"Error message indicates timeout: {error.message}")
        
        if "permission" in message or "access denied" in message:
            factors.append("Permission/Security issue")
            evidence.append(f"Error message indicates permission problem: {error.message}")
        
        if "connection" in message or "network" in message:
            factors.append("Network connectivity issue")
            evidence.append(f"Error message indicates network problem: {error.message}")
        
        # Stack trace analysis
        if error.stack_trace:
            stack_analysis = self._analyze_stack_trace(error.stack_trace)
            evidence.extend(stack_analysis['evidence'])
            factors.extend(stack_analysis['factors'])
        
        # Resource usage analysis
        if error.resource_usage:
            resource_analysis = self._analyze_resource_usage(error.resource_usage)
            evidence.extend(resource_analysis['evidence'])
            factors.extend(resource_analysis['factors'])
        
        return {'evidence': evidence, 'factors': factors}
    
    def _analyze_stack_trace(self, stack_trace: str) -> Dict[str, List[str]]:
        """Analyze stack trace for patterns."""
        evidence = []
        factors = []
        
        lines = stack_trace.split('\n')
        
        # Look for common problematic patterns
        for line in lines:
            line_lower = line.lower()
            
            if 'recursionerror' in line_lower or 'maximum recursion' in line_lower:
                factors.append("Infinite recursion")
                evidence.append(f"Stack trace shows recursion error: {line.strip()}")
            
            if 'nullpointerexception' in line_lower or 'nonetype' in line_lower:
                factors.append("Null/None reference")
                evidence.append(f"Stack trace shows null reference: {line.strip()}")
            
            if 'indexerror' in line_lower or 'list index out of range' in line_lower:
                factors.append("Array/List bounds error")
                evidence.append(f"Stack trace shows index error: {line.strip()}")
        
        return {'evidence': evidence, 'factors': factors}
    
    def _analyze_resource_usage(self, resource_usage: Dict[str, float]) -> Dict[str, List[str]]:
        """Analyze resource usage for abnormal patterns."""
        evidence = []
        factors = []
        
        cpu_usage = resource_usage.get('cpu_percent', 0)
        memory_usage = resource_usage.get('memory_percent', 0)
        disk_usage = resource_usage.get('disk_percent', 0)
        
        if cpu_usage > 95:
            factors.append("CPU exhaustion")
            evidence.append(f"CPU usage was {cpu_usage}% at time of error")
        
        if memory_usage > 90:
            factors.append("Memory pressure")
            evidence.append(f"Memory usage was {memory_usage}% at time of error")
        
        if disk_usage > 95:
            factors.append("Disk space exhaustion")
            evidence.append(f"Disk usage was {disk_usage}% at time of error")
        
        return {'evidence': evidence, 'factors': factors}
    
    def _analyze_context_events(self, error: ErrorEvent, context_events: List[ErrorEvent]) -> Dict[str, List[str]]:
        """Analyze events that occurred before the error."""
        evidence = []
        factors = []
        
        # Look for patterns in preceding events
        recent_events = [e for e in context_events if e.timestamp < error.timestamp]
        recent_events.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Check for escalating pattern
        if len(recent_events) >= 3:
            recent_severities = [e.severity for e in recent_events[:3]]
            if self._is_escalating_pattern(recent_severities):
                factors.append("Escalating error pattern")
                evidence.append("Error severity escalated in recent events")
        
        # Check for related error types
        error_types = [e.error_type for e in recent_events[:5]]
        if error.error_type in error_types:
            factors.append("Recurring error type")
            evidence.append(f"Similar {error.error_type.value} errors occurred recently")
        
        # Check for resource trends
        if recent_events:
            resource_trend = self._analyze_resource_trend(recent_events)
            if resource_trend:
                factors.extend(resource_trend['factors'])
                evidence.extend(resource_trend['evidence'])
        
        return {'evidence': evidence, 'factors': factors}
    
    def _is_escalating_pattern(self, severities: List[ErrorSeverity]) -> bool:
        """Check if error severities show escalating pattern."""
        severity_values = {
            ErrorSeverity.INFO: 1,
            ErrorSeverity.LOW: 2,
            ErrorSeverity.MEDIUM: 3,
            ErrorSeverity.HIGH: 4,
            ErrorSeverity.CRITICAL: 5
        }
        
        values = [severity_values[s] for s in severities]
        return all(values[i] >= values[i+1] for i in range(len(values)-1))
    
    def _analyze_resource_trend(self, events: List[ErrorEvent]) -> Optional[Dict[str, List[str]]]:
        """Analyze resource usage trends in recent events."""
        if not events:
            return None
        
        evidence = []
        factors = []
        
        # Extract resource usage from events that have it
        resource_events = [e for e in events if e.resource_usage]
        
        if len(resource_events) >= 2:
            # Check for increasing resource usage
            memory_values = [e.resource_usage.get('memory_percent', 0) for e in resource_events]
            cpu_values = [e.resource_usage.get('cpu_percent', 0) for e in resource_events]
            
            if len(memory_values) >= 2 and memory_values[0] - memory_values[-1] > 20:
                factors.append("Increasing memory usage trend")
                evidence.append("Memory usage increased significantly before error")
            
            if len(cpu_values) >= 2 and cpu_values[0] - cpu_values[-1] > 20:
                factors.append("Increasing CPU usage trend")
                evidence.append("CPU usage increased significantly before error")
        
        return {'evidence': evidence, 'factors': factors} if evidence else None
    
    def _analyze_error_patterns(self, error: ErrorEvent) -> Optional[Dict[str, List[str]]]:
        """Analyze against known error patterns."""
        evidence = []
        factors = []
        
        # Check if this error matches any known patterns
        error_signature = self.pattern_recognizer.extract_error_signature(error)
        matching_pattern = self.pattern_recognizer.find_matching_pattern(error_signature)
        
        if matching_pattern:
            evidence.append(f"Matches known pattern: {matching_pattern.pattern_id}")
            factors.extend(matching_pattern.recovery_strategies)
            
            # Check frequency of this pattern
            if matching_pattern.frequency > 5:
                evidence.append("High frequency pattern - system issue likely")
                factors.append("system_configuration_review_needed")
            
            # Check recency
            if matching_pattern.last_seen:
                hours_since = (time.time() - matching_pattern.last_seen) / 3600
                if hours_since < 1:
                    evidence.append("Recent pattern occurrence")
                    factors.append("immediate_attention_required")
        else:
            evidence.append("Novel error pattern - requires investigation")
            factors.append("unknown_pattern_investigation")
        
        return {
            "evidence": evidence,
            "contributing_factors": factors
        }
    
    def _determine_primary_cause(self, error: ErrorEvent, contributing_factors: List[str]) -> str:
        """Determine the most likely primary cause."""
        # Priority-based cause determination
        priority_keywords = {
            "memory": "Memory exhaustion",
            "disk": "Disk space exhaustion",
            "cpu": "CPU exhaustion",
            "network": "Network connectivity issue",
            "permission": "Permission/Security issue",
            "timeout": "Performance/Timeout issue",
            "recursion": "Logic error (infinite recursion)",
            "null": "Logic error (null reference)"
        }
        
        for keyword, cause in priority_keywords.items():
            if any(keyword in factor.lower() for factor in contributing_factors):
                return cause
        
        # Default based on error type
        error_type_causes = {
            ErrorType.RESOURCE_EXHAUSTION: "Resource exhaustion",
            ErrorType.NETWORK_ERROR: "Network connectivity issue",
            ErrorType.PERMISSION_ERROR: "Permission/Security issue",
            ErrorType.TIMEOUT_ERROR: "Performance/Timeout issue",
            ErrorType.LOGIC_ERROR: "Logic error in code",
            ErrorType.SYNTAX_ERROR: "Code syntax error"
        }
        
        return error_type_causes.get(error.error_type, "Unknown error condition")
    
    def _calculate_confidence(self, evidence: List[str], factors: List[str]) -> float:
        """Calculate confidence score for the analysis."""
        # Base confidence from amount of evidence
        evidence_score = min(len(evidence) / 10.0, 1.0)
        
        # Factor diversity score
        factor_score = min(len(set(factors)) / 5.0, 1.0)
        
        # Specific evidence quality bonus
        quality_bonus = 0.0
        if any("stack trace" in e.lower() for e in evidence):
            quality_bonus += 0.2
        if any("resource usage" in e.lower() for e in evidence):
            quality_bonus += 0.1
        
        total_confidence = (evidence_score + factor_score) / 2 + quality_bonus
        return min(total_confidence, 1.0)
    
    def _generate_suggested_fixes(self, error: ErrorEvent, primary_cause: str, 
                                factors: List[str]) -> List[str]:
        """Generate specific fix suggestions."""
        suggestions = []
        
        # Cause-specific suggestions
        cause_suggestions = {
            "Memory exhaustion": [
                "Increase memory allocation",
                "Optimize memory usage in code",
                "Add garbage collection optimization",
                "Check for memory leaks"
            ],
            "CPU exhaustion": [
                "Optimize algorithm complexity",
                "Add caching to reduce computation",
                "Scale processing power",
                "Implement rate limiting"
            ],
            "Network connectivity issue": [
                "Check network configuration",
                "Implement retry mechanisms",
                "Add connection pooling",
                "Use circuit breaker pattern"
            ],
            "Permission/Security issue": [
                "Review and update permissions",
                "Check authentication configuration",
                "Verify security policies",
                "Update access credentials"
            ]
        }
        
        suggestions.extend(cause_suggestions.get(primary_cause, []))
        
        # Factor-specific suggestions
        for factor in factors:
            if "timeout" in factor.lower():
                suggestions.append("Increase timeout values")
            elif "recursion" in factor.lower():
                suggestions.append("Add recursion depth limits")
                suggestions.append("Review recursive algorithm implementation")
            elif "null" in factor.lower():
                suggestions.append("Add null/None checks")
                suggestions.append("Initialize variables properly")
        
        return list(set(suggestions))  # Remove duplicates
    
    async def _find_similar_incidents(self, error: ErrorEvent) -> List[str]:
        """Find similar incidents from historical data."""
        # This would query historical database
# DEMO CODE REMOVED: # For now, return mock data
        return [
            f"Similar {error.error_type.value} error on {datetime.now() - timedelta(days=7)}",
            f"Related issue in {error.context.get('module', 'unknown')} module"
        ]


class ErrorDetector:
    """Main error detection system with comprehensive monitoring and analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize components
        self.error_stream = ErrorStream(config.get('stream_buffer_size', 1000))
        self.pattern_recognizer = PatternRecognizer()
        self.anomaly_detector = AnomalyDetector(config.get('anomaly_detection', {}))
        self.failure_predictor = FailurePredictor(config.get('failure_prediction', {}))
        self.root_cause_analyzer = RootCauseAnalyzer(config.get('root_cause_analysis', {}))
        
        # Monitoring state
        self.is_monitoring = False
        self.monitored_processes = {}
        self.monitoring_tasks = {}
        
        # Database for persistent storage
        self.db_path = config.get('database_path', 'error_detector.db')
        self._initialize_database()
        
        logger.info("ErrorDetector initialized")
    
    def _initialize_database(self):
        """Initialize SQLite database for persistent storage."""
        conn = sqlite3.connect(self.db_path)
        
        # Create tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS error_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT,
                error_type TEXT,
                severity TEXT,
                message TEXT,
                stack_trace TEXT,
                context TEXT,
                process_id TEXT,
                agent_id TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS anomalies (
                anomaly_id TEXT PRIMARY KEY,
                timestamp TEXT,
                anomaly_type TEXT,
                severity TEXT,
                description TEXT,
                affected_metrics TEXT,
                confidence_score REAL,
                deviation_score REAL
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS error_patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT,
                signature TEXT,
                frequency INTEGER,
                last_seen TEXT,
                resolution_success_rate REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def monitor_execution(self, process_id: str, 
                              agent_id: Optional[str] = None) -> ErrorStream:
        """Start monitoring a specific execution process."""
        logger.info(f"Starting monitoring for process {process_id}")
        
        # Create dedicated error stream for this process
        process_stream = ErrorStream()
        
        # Start monitoring task
        monitoring_task = asyncio.create_task(
            self._monitor_process_loop(process_id, agent_id, process_stream)
        )
        
        self.monitoring_tasks[process_id] = monitoring_task
        self.monitored_processes[process_id] = {
            'agent_id': agent_id,
            'stream': process_stream,
            'start_time': datetime.now()
        }
        
        return process_stream
    
    async def _monitor_process_loop(self, process_id: str, agent_id: Optional[str], 
                                  stream: ErrorStream):
        """Main monitoring loop for a process."""
        try:
            while process_id in self.monitored_processes:
                # Collect current metrics
                current_metrics = await self._collect_system_metrics(process_id)
                
                # Check for anomalies
                anomalies = await self.anomaly_detector.detect_anomalies(current_metrics)
                
                for anomaly in anomalies:
                    # Convert anomaly to error event
                    error_event = ErrorEvent(
                        event_id=str(uuid.uuid4()),
                        timestamp=anomaly.timestamp,
                        error_type=ErrorType.PERFORMANCE_DEGRADATION,
                        severity=anomaly.severity,
                        message=anomaly.description,
                        context={'anomaly_type': anomaly.anomaly_type.value},
                        process_id=process_id,
                        agent_id=agent_id,
                        resource_usage=current_metrics
                    )
                    
                    await stream.add_event(error_event)
                    await self.error_stream.add_event(error_event)
                
                # Update anomaly detector with new metrics
                self.anomaly_detector.add_metrics(current_metrics, datetime.now())
                
                # Sleep before next check
                await asyncio.sleep(self.config.get('monitoring_interval', 5))
                
        except asyncio.CancelledError:
            logger.info(f"Monitoring cancelled for process {process_id}")
        except Exception as e:
            logger.error(f"Monitoring error for process {process_id}: {e}")
    
    async def _collect_system_metrics(self, process_id: str) -> Dict[str, float]:
        """Collect system metrics for monitoring."""
        try:
            # Get system-wide metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'memory_available': memory.available / (1024**3),  # GB
                'timestamp': time.time()
            }
            
            # Try to get process-specific metrics
            try:
                if process_id.isdigit():
                    process = psutil.Process(int(process_id))
                    metrics.update({
                        'process_cpu': process.cpu_percent(),
                        'process_memory': process.memory_percent(),
                        'process_threads': process.num_threads(),
                        'process_connections': len(process.connections())
                    })
            except (psutil.NoSuchProcess, ValueError):
                pass
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return {'timestamp': time.time()}
    
    async def detect_anomalies(self, metrics: Dict[str, float]) -> List[Anomaly]:
        """Detect anomalies in provided metrics."""
        return await self.anomaly_detector.detect_anomalies(metrics)
    
    async def predict_failure(self, current_state: Dict[str, Any]) -> FailureProbability:
        """Predict potential failure based on current state."""
        return await self.failure_predictor.predict_failure(current_state)
    
    async def analyze_root_cause(self, error: ErrorEvent, 
                               lookback_minutes: int = 30) -> RootCause:
        """Analyze root cause of an error."""
        # Get context events from the lookback period
        since_time = error.timestamp - timedelta(minutes=lookback_minutes)
        context_events = await self.error_stream.get_events(since=since_time)
        
        # Filter out the current error from context
        context_events = [e for e in context_events if e.event_id != error.event_id]
        
        return await self.root_cause_analyzer.analyze_root_cause(error, context_events)
    
    def classify_error(self, error: Union[Exception, str, ErrorEvent]) -> ErrorType:
        """Classify an error into predefined categories."""
        if isinstance(error, ErrorEvent):
            return error.error_type
        
        if isinstance(error, Exception):
            error_str = str(error)
            error_type_name = type(error).__name__
        else:
            error_str = str(error)
            error_type_name = ""
        
        error_lower = error_str.lower()
        type_lower = error_type_name.lower()
        
        # Classification rules
        if 'syntaxerror' in type_lower or 'syntax error' in error_lower:
            return ErrorType.SYNTAX_ERROR
        
        if 'memory' in error_lower or 'memoryerror' in type_lower:
            return ErrorType.RESOURCE_EXHAUSTION
        
        if 'timeout' in error_lower or 'timed out' in error_lower:
            return ErrorType.TIMEOUT_ERROR
        
        if 'permission' in error_lower or 'access denied' in error_lower:
            return ErrorType.PERMISSION_ERROR
        
        if 'connection' in error_lower or 'network' in error_lower:
            return ErrorType.NETWORK_ERROR
        
        if 'security' in error_lower or 'unauthorized' in error_lower:
            return ErrorType.SECURITY_VIOLATION
        
        if any(keyword in error_lower for keyword in ['slow', 'performance', 'lag']):
            return ErrorType.PERFORMANCE_DEGRADATION
        
        if any(keyword in type_lower for keyword in ['runtime', 'value', 'type', 'attribute']):
            return ErrorType.LOGIC_ERROR
        
        return ErrorType.UNKNOWN_ERROR
    
    async def record_error(self, error: Union[Exception, str], 
                         context: Optional[Dict[str, Any]] = None,
                         process_id: Optional[str] = None,
                         agent_id: Optional[str] = None) -> ErrorEvent:
        """Record an error event."""
        
        # Create error event
        error_event = ErrorEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            error_type=self.classify_error(error),
            severity=self._determine_severity(error),
            message=str(error),
            stack_trace=self._extract_stack_trace(error) if isinstance(error, Exception) else None,
            context=context or {},
            process_id=process_id,
            agent_id=agent_id
        )
        
        # Add to streams
        await self.error_stream.add_event(error_event)
        
        # Store in database
        await self._store_error_event(error_event)
        
        # Learn pattern
        pattern = self.pattern_recognizer.learn_pattern([error_event])
        if pattern:
            await self._store_error_pattern(pattern)
        
        logger.warning(f"Recorded error: {error_event.error_type.value} - {error_event.message}")
        
        return error_event
    
    def _determine_severity(self, error: Union[Exception, str]) -> ErrorSeverity:
        """Determine error severity based on error characteristics."""
        if isinstance(error, Exception):
            error_str = str(error)
            error_type = type(error).__name__
        else:
            error_str = str(error)
            error_type = ""
        
        error_lower = error_str.lower()
        
        # Critical errors
        if any(keyword in error_lower for keyword in ['critical', 'fatal', 'crash', 'segmentation']):
            return ErrorSeverity.CRITICAL
        
        if any(keyword in error_type.lower() for keyword in ['systemexit', 'keyboardinterrupt']):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if any(keyword in error_lower for keyword in ['memory', 'disk', 'security', 'unauthorized']):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if any(keyword in error_lower for keyword in ['timeout', 'connection', 'permission']):
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        if any(keyword in error_lower for keyword in ['warning', 'deprecated']):
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM  # Default
    
    def _extract_stack_trace(self, error: Exception) -> Optional[str]:
        """Extract stack trace from exception."""
        import traceback
        return traceback.format_exc()
    
    async def _store_error_event(self, event: ErrorEvent):
        """Store error event in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO error_events 
                (event_id, timestamp, error_type, severity, message, stack_trace, 
                 context, process_id, agent_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.timestamp.isoformat(),
                event.error_type.value,
                event.severity.value,
                event.message,
                event.stack_trace,
                json.dumps(event.context),
                event.process_id,
                event.agent_id
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store error event: {e}")
    
    async def _store_error_pattern(self, pattern: ErrorPattern):
        """Store error pattern in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO error_patterns
                (pattern_id, pattern_type, signature, frequency, last_seen, resolution_success_rate)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                pattern.pattern_id,
                pattern.pattern_type,
                pattern.signature,
                pattern.frequency,
                pattern.last_seen.isoformat(),
                pattern.resolution_success_rate
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store error pattern: {e}")
    
    async def stop_monitoring(self, process_id: str):
        """Stop monitoring a specific process."""
        if process_id in self.monitoring_tasks:
            task = self.monitoring_tasks[process_id]
            task.cancel()
            del self.monitoring_tasks[process_id]
        
        if process_id in self.monitored_processes:
            del self.monitored_processes[process_id]
        
        logger.info(f"Stopped monitoring process {process_id}")
    
    async def get_detection_statistics(self) -> Dict[str, Any]:
        """Get error detection statistics."""
        recent_events = await self.error_stream.get_events(
            since=datetime.now() - timedelta(hours=24)
        )
        
        error_type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for event in recent_events:
            error_type_counts[event.error_type.value] += 1
            severity_counts[event.severity.value] += 1
        
        return {
            'total_events_24h': len(recent_events),
            'error_type_distribution': dict(error_type_counts),
            'severity_distribution': dict(severity_counts),
            'monitored_processes': len(self.monitored_processes),
            'known_patterns': len(self.pattern_recognizer.patterns),
            'anomaly_detector_trained': self.anomaly_detector.is_trained
        }
    
    async def cleanup(self):
        """Cleanup resources and stop all monitoring."""
        logger.info("Cleaning up ErrorDetector")
        
        # Stop all monitoring tasks
        for process_id in list(self.monitored_processes.keys()):
            await self.stop_monitoring(process_id)
        
        # Clear streams
        await self.error_stream.clear()