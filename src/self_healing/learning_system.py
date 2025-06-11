import asyncio
import json
import pickle
import numpy as np
import sqlite3
import hashlib
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from pathlib import Path
import statistics
from sklearn.cluster import DBSCAN, KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from loguru import logger
import threading
import copy


class ExperienceType(Enum):
    TASK_EXECUTION = "task_execution"
    ERROR_RECOVERY = "error_recovery"
    VALIDATION = "validation"
    COLLABORATION = "collaboration"
    OPTIMIZATION = "optimization"


class PatternType(Enum):
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    EFFICIENCY_PATTERN = "efficiency_pattern"
    COLLABORATION_PATTERN = "collaboration_pattern"
    ANTI_PATTERN = "anti_pattern"


class LearningObjective(Enum):
    ACCURACY = "accuracy"
    EFFICIENCY = "efficiency"
    RELIABILITY = "reliability"
    SAFETY = "safety"
    COLLABORATION = "collaboration"


@dataclass
class Experience:
    experience_id: str
    timestamp: datetime
    experience_type: ExperienceType
    agent_id: str
    task_context: Dict[str, Any]
    actions_taken: List[Dict[str, Any]]
    outcomes: Dict[str, Any]
    metrics: Dict[str, float]
    success: bool
    execution_time: float
    resource_usage: Dict[str, float]
    error_info: Optional[Dict[str, Any]] = None
    recovery_actions: List[Dict[str, Any]] = field(default_factory=list)
    collaboration_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Pattern:
    pattern_id: str
    pattern_type: PatternType
    pattern_name: str
    description: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    expected_outcomes: Dict[str, Any]
    confidence_score: float
    usage_count: int
    success_rate: float
    avg_execution_time: float
    resource_efficiency: float
    discovered_date: datetime
    last_updated: datetime
    supporting_experiences: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)


@dataclass
class StrategyUpdate:
    strategy_id: str
    update_type: str
    old_parameters: Dict[str, Any]
    new_parameters: Dict[str, Any]
    expected_improvement: float
    confidence: float
    reasoning: str
    validation_required: bool


@dataclass
class KnowledgeEntry:
    entry_id: str
    category: str
    content: Dict[str, Any]
    relevance_score: float
    evidence_strength: float
    created_date: datetime
    updated_date: datetime
    source_experiences: List[str]
    applicability_contexts: List[str]


@dataclass
class LearningMetrics:
    total_experiences: int = 0
    patterns_discovered: int = 0
    strategies_optimized: int = 0
    knowledge_entries: int = 0
    avg_learning_rate: float = 0.0
    improvement_score: float = 0.0
    adaptation_efficiency: float = 0.0
    cross_agent_transfers: int = 0
    last_learning_session: Optional[datetime] = None


class ExperienceProcessor:
    """Process and analyze experiences for pattern extraction."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.feature_scaler = StandardScaler()
# DEMO CODE REMOVED: self.clustering_model = DBSCAN(eps=0.3, min_samples=3)
        self.success_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
        self.efficiency_predictor = GradientBoostingRegressor(n_estimators=100, random_state=42)
    
    def extract_features(self, experiences: List[Experience]) -> np.ndarray:
        """Extract numerical features from experiences."""
        features = []
        
        for exp in experiences:
            feature_vector = [
                exp.execution_time,
                exp.metrics.get('accuracy', 0.0),
                exp.metrics.get('efficiency', 0.0),
                exp.resource_usage.get('memory_mb', 0.0),
                exp.resource_usage.get('cpu_percent', 0.0),
                len(exp.actions_taken),
                len(exp.recovery_actions),
                1 if exp.success else 0,
                exp.metrics.get('complexity', 0.0),
                exp.metrics.get('confidence', 0.0)
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def cluster_experiences(self, experiences: List[Experience]) -> Dict[int, List[Experience]]:
        """Cluster similar experiences together."""
        if len(experiences) < 3:
            return {0: experiences}
        
        features = self.extract_features(experiences)
        features_scaled = self.feature_scaler.fit_transform(features)
        
        cluster_labels = self.clustering_model.fit_predict(features_scaled)
        
        clusters = defaultdict(list)
        for i, label in enumerate(cluster_labels):
            clusters[label].append(experiences[i])
        
        return dict(clusters)
    
    def identify_success_patterns(self, experiences: List[Experience]) -> List[Pattern]:
        """Identify patterns that lead to success."""
        successful_experiences = [exp for exp in experiences if exp.success]
        
        if len(successful_experiences) < 2:
            return []
        
        clusters = self.cluster_experiences(successful_experiences)
        patterns = []
        
        for cluster_id, cluster_experiences in clusters.items():
            if len(cluster_experiences) < 2:
                continue
            
            pattern = self._create_pattern_from_cluster(
                cluster_experiences, 
                PatternType.SUCCESS_PATTERN,
                f"Success Pattern {cluster_id}"
            )
            patterns.append(pattern)
        
        return patterns
    
    def identify_failure_patterns(self, experiences: List[Experience]) -> List[Pattern]:
        """Identify patterns that lead to failure."""
        failed_experiences = [exp for exp in experiences if not exp.success]
        
        if len(failed_experiences) < 2:
            return []
        
        clusters = self.cluster_experiences(failed_experiences)
        patterns = []
        
        for cluster_id, cluster_experiences in clusters.items():
            if len(cluster_experiences) < 2:
                continue
            
            pattern = self._create_pattern_from_cluster(
                cluster_experiences, 
                PatternType.FAILURE_PATTERN,
                f"Failure Pattern {cluster_id}"
            )
            patterns.append(pattern)
        
        return patterns
    
    def identify_efficiency_patterns(self, experiences: List[Experience]) -> List[Pattern]:
        """Identify patterns that lead to high efficiency."""
        # Sort by efficiency metrics
        efficient_experiences = sorted(
            experiences, 
            key=lambda x: x.metrics.get('efficiency', 0.0), 
            reverse=True
        )[:len(experiences)//3]  # Top 33% most efficient
        
        if len(efficient_experiences) < 2:
            return []
        
        clusters = self.cluster_experiences(efficient_experiences)
        patterns = []
        
        for cluster_id, cluster_experiences in clusters.items():
            if len(cluster_experiences) < 2:
                continue
            
            pattern = self._create_pattern_from_cluster(
                cluster_experiences, 
                PatternType.EFFICIENCY_PATTERN,
                f"Efficiency Pattern {cluster_id}"
            )
            patterns.append(pattern)
        
        return patterns
    
    def _create_pattern_from_cluster(self, experiences: List[Experience], 
                                   pattern_type: PatternType, name: str) -> Pattern:
        """Create a pattern from a cluster of similar experiences."""
        # Extract common conditions
        conditions = self._extract_common_conditions(experiences)
        
        # Extract common actions
        actions = self._extract_common_actions(experiences)
        
        # Calculate metrics
        success_rate = sum(1 for exp in experiences if exp.success) / len(experiences)
        avg_execution_time = statistics.mean(exp.execution_time for exp in experiences)
        avg_efficiency = statistics.mean(exp.metrics.get('efficiency', 0.0) for exp in experiences)
        
        # Calculate confidence based on cluster size and consistency
        confidence_score = min(0.9, len(experiences) / 10.0 + success_rate * 0.3)
        
        pattern = Pattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type=pattern_type,
            pattern_name=name,
            description=f"Pattern identified from {len(experiences)} similar experiences",
            conditions=conditions,
            actions=actions,
            expected_outcomes=self._extract_expected_outcomes(experiences),
            confidence_score=confidence_score,
            usage_count=0,
            success_rate=success_rate,
            avg_execution_time=avg_execution_time,
            resource_efficiency=avg_efficiency,
            discovered_date=datetime.now(),
            last_updated=datetime.now(),
            supporting_experiences=[exp.experience_id for exp in experiences],
            tags=self._extract_tags(experiences)
        )
        
        return pattern
    
    def _extract_common_conditions(self, experiences: List[Experience]) -> Dict[str, Any]:
        """Extract common conditions from experiences."""
        all_conditions = []
        
        for exp in experiences:
            context_conditions = {
                'task_type': exp.task_context.get('task_type'),
                'complexity': exp.task_context.get('complexity'),
                'resource_constraints': exp.task_context.get('resource_constraints'),
                'collaboration_mode': exp.task_context.get('collaboration_mode'),
                'time_pressure': exp.task_context.get('time_pressure')
            }
            all_conditions.append(context_conditions)
        
        # Find most common values for each condition
        common_conditions = {}
        for key in all_conditions[0].keys():
            values = [cond.get(key) for cond in all_conditions if cond.get(key) is not None]
            if values:
                # Use most common value
                value_counts = defaultdict(int)
                for value in values:
                    value_counts[value] += 1
                common_conditions[key] = max(value_counts.items(), key=lambda x: x[1])[0]
        
        return common_conditions
    
    def _extract_common_actions(self, experiences: List[Experience]) -> List[Dict[str, Any]]:
        """Extract common action patterns from experiences."""
        action_sequences = []
        
        for exp in experiences:
            sequence = []
            for action in exp.actions_taken:
                sequence.append({
                    'type': action.get('type'),
                    'parameters': action.get('parameters', {}),
                    'timing': action.get('timing')
                })
            action_sequences.append(sequence)
        
        # Find common action patterns (simplified)
        if not action_sequences:
            return []
        
        # Use the most common sequence length as reference
        lengths = [len(seq) for seq in action_sequences]
        common_length = max(set(lengths), key=lengths.count)
        
        # Extract actions at each position
        common_actions = []
        for i in range(common_length):
            actions_at_position = []
            for seq in action_sequences:
                if i < len(seq):
                    actions_at_position.append(seq[i])
            
            if actions_at_position:
                # Use most common action type at this position
                action_types = [action.get('type') for action in actions_at_position]
                most_common_type = max(set(action_types), key=action_types.count)
                
                common_actions.append({
                    'type': most_common_type,
                    'position': i,
                    'frequency': action_types.count(most_common_type) / len(action_types)
                })
        
        return common_actions
    
    def _extract_expected_outcomes(self, experiences: List[Experience]) -> Dict[str, Any]:
        """Extract expected outcomes from experiences."""
        outcomes = {
            'success_probability': sum(1 for exp in experiences if exp.success) / len(experiences),
            'avg_execution_time': statistics.mean(exp.execution_time for exp in experiences),
            'avg_accuracy': statistics.mean(exp.metrics.get('accuracy', 0.0) for exp in experiences),
            'avg_efficiency': statistics.mean(exp.metrics.get('efficiency', 0.0) for exp in experiences),
            'resource_usage': {
                'memory_mb': statistics.mean(exp.resource_usage.get('memory_mb', 0.0) for exp in experiences),
                'cpu_percent': statistics.mean(exp.resource_usage.get('cpu_percent', 0.0) for exp in experiences)
            }
        }
        
        return outcomes
    
    def _extract_tags(self, experiences: List[Experience]) -> Set[str]:
        """Extract relevant tags from experiences."""
        tags = set()
        
        for exp in experiences:
            # Add tags based on experience characteristics
            if exp.success:
                tags.add('successful')
            else:
                tags.add('failed')
            
            if exp.execution_time < 1.0:
                tags.add('fast')
            elif exp.execution_time > 10.0:
                tags.add('slow')
            
            if exp.metrics.get('efficiency', 0.0) > 0.8:
                tags.add('efficient')
            
            if exp.resource_usage.get('memory_mb', 0.0) > 100:
                tags.add('memory_intensive')
            
            if len(exp.recovery_actions) > 0:
                tags.add('recovery_needed')
            
            # Add context-based tags
            task_type = exp.task_context.get('task_type')
            if task_type:
                tags.add(f'task_{task_type}')
        
        return tags


class StrategyOptimizer:
    """Optimize strategies based on learned patterns."""
    
    def __init__(self):
        self.optimization_history = []
        self.strategy_performance = defaultdict(list)
    
    def optimize_prompt_strategies(self, patterns: List[Pattern]) -> List[StrategyUpdate]:
        """Optimize prompt strategies based on successful patterns."""
        updates = []
        
        success_patterns = [p for p in patterns if p.pattern_type == PatternType.SUCCESS_PATTERN]
        
        for pattern in success_patterns:
            if pattern.confidence_score > 0.7 and pattern.success_rate > 0.8:
                # Generate prompt optimization
                update = StrategyUpdate(
                    strategy_id=f"prompt_optimization_{pattern.pattern_id}",
                    update_type="prompt_template",
                    old_parameters={},  # Would contain current prompt parameters
                    new_parameters=self._generate_prompt_parameters(pattern),
                    expected_improvement=pattern.success_rate - 0.5,  # Baseline improvement
                    confidence=pattern.confidence_score,
                    reasoning=f"Based on pattern with {pattern.success_rate:.2f} success rate",
                    validation_required=True
                )
                updates.append(update)
        
        return updates
    
    def optimize_parameter_strategies(self, patterns: List[Pattern]) -> List[StrategyUpdate]:
        """Optimize execution parameters based on efficiency patterns."""
        updates = []
        
        efficiency_patterns = [p for p in patterns if p.pattern_type == PatternType.EFFICIENCY_PATTERN]
        
        for pattern in efficiency_patterns:
            if pattern.resource_efficiency > 0.8:
                # Generate parameter optimization
                update = StrategyUpdate(
                    strategy_id=f"parameter_optimization_{pattern.pattern_id}",
                    update_type="execution_parameters",
                    old_parameters={},  # Current parameters
                    new_parameters=self._generate_execution_parameters(pattern),
                    expected_improvement=pattern.resource_efficiency - 0.5,
                    confidence=pattern.confidence_score,
                    reasoning=f"Based on efficient pattern with {pattern.resource_efficiency:.2f} efficiency",
                    validation_required=True
                )
                updates.append(update)
        
        return updates
    
    def optimize_resource_allocation(self, patterns: List[Pattern]) -> List[StrategyUpdate]:
        """Optimize resource allocation strategies."""
        updates = []
        
        # Analyze resource usage patterns
        for pattern in patterns:
            if pattern.pattern_type in [PatternType.SUCCESS_PATTERN, PatternType.EFFICIENCY_PATTERN]:
                resource_params = pattern.expected_outcomes.get('resource_usage', {})
                
                if resource_params:
                    update = StrategyUpdate(
                        strategy_id=f"resource_optimization_{pattern.pattern_id}",
                        update_type="resource_allocation",
                        old_parameters={},
                        new_parameters={
                            'memory_limit': resource_params.get('memory_mb', 256),
                            'cpu_limit': resource_params.get('cpu_percent', 50),
                            'timeout': pattern.avg_execution_time * 1.2  # Add 20% buffer
                        },
                        expected_improvement=0.1,  # Modest improvement expected
                        confidence=pattern.confidence_score * 0.8,  # Slightly lower confidence
                        reasoning=f"Optimized based on resource usage pattern",
                        validation_required=True
                    )
                    updates.append(update)
        
        return updates
    
    def _generate_prompt_parameters(self, pattern: Pattern) -> Dict[str, Any]:
        """Generate optimized prompt parameters based on pattern."""
        # Extract prompt-related information from pattern
        conditions = pattern.conditions
        
        parameters = {
            'temperature': 0.7,  # Default, could be optimized based on pattern
            'max_tokens': 1000,
            'top_p': 0.9,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0
        }
        
        # Adjust based on pattern characteristics
        if 'creativity' in pattern.tags:
            parameters['temperature'] = 0.9
        elif 'precision' in pattern.tags:
            parameters['temperature'] = 0.3
        
        if 'complex' in pattern.tags:
            parameters['max_tokens'] = 2000
        
        return parameters
    
    def _generate_execution_parameters(self, pattern: Pattern) -> Dict[str, Any]:
        """Generate optimized execution parameters based on pattern."""
        expected_outcomes = pattern.expected_outcomes
        
        parameters = {
            'timeout': pattern.avg_execution_time * 1.1,  # 10% buffer
            'retry_attempts': 3,
            'backoff_factor': 1.5,
            'parallel_execution': True if pattern.resource_efficiency > 0.7 else False
        }
        
        # Adjust based on pattern characteristics
        if 'fast' in pattern.tags:
            parameters['timeout'] = min(parameters['timeout'], 5.0)
        elif 'slow' in pattern.tags:
            parameters['timeout'] = max(parameters['timeout'], 30.0)
        
        return parameters


class KnowledgeManager:
    """Manage knowledge base and cross-agent learning."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.knowledge_entries: Dict[str, KnowledgeEntry] = {}
        self.best_practices: Dict[str, List[str]] = defaultdict(list)
        self.anti_patterns: Dict[str, List[str]] = defaultdict(list)
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize knowledge database."""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                entry_id TEXT PRIMARY KEY,
                category TEXT,
                content TEXT,
                relevance_score REAL,
                evidence_strength REAL,
                created_date TEXT,
                updated_date TEXT,
                source_experiences TEXT,
                applicability_contexts TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS best_practices (
                practice_id TEXT PRIMARY KEY,
                category TEXT,
                description TEXT,
                success_rate REAL,
                evidence_count INTEGER,
                created_date TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS anti_patterns (
                anti_pattern_id TEXT PRIMARY KEY,
                category TEXT,
                description TEXT,
                failure_rate REAL,
                evidence_count INTEGER,
                created_date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_knowledge_entry(self, entry: KnowledgeEntry):
        """Add new knowledge entry."""
        self.knowledge_entries[entry.entry_id] = entry
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT OR REPLACE INTO knowledge_entries
            (entry_id, category, content, relevance_score, evidence_strength,
             created_date, updated_date, source_experiences, applicability_contexts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.entry_id,
            entry.category,
            json.dumps(entry.content),
            entry.relevance_score,
            entry.evidence_strength,
            entry.created_date.isoformat(),
            entry.updated_date.isoformat(),
            json.dumps(entry.source_experiences),
            json.dumps(entry.applicability_contexts)
        ))
        conn.commit()
        conn.close()
    
    def add_best_practice(self, category: str, description: str, 
                         success_rate: float, evidence_count: int):
        """Add a best practice."""
        practice_id = str(uuid.uuid4())
        
        self.best_practices[category].append(description)
        
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO best_practices
            (practice_id, category, description, success_rate, evidence_count, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            practice_id,
            category,
            description,
            success_rate,
            evidence_count,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def add_anti_pattern(self, category: str, description: str, 
                        failure_rate: float, evidence_count: int):
        """Add an anti-pattern."""
        anti_pattern_id = str(uuid.uuid4())
        
        self.anti_patterns[category].append(description)
        
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO anti_patterns
            (anti_pattern_id, category, description, failure_rate, evidence_count, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            anti_pattern_id,
            category,
            description,
            failure_rate,
            evidence_count,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def get_relevant_knowledge(self, context: Dict[str, Any], limit: int = 10) -> List[KnowledgeEntry]:
        """Get knowledge entries relevant to the given context."""
        relevant_entries = []
        
        context_str = json.dumps(context, sort_keys=True)
        
        for entry in self.knowledge_entries.values():
            # Calculate relevance based on context similarity
            relevance = self._calculate_context_relevance(entry, context)
            
            if relevance > 0.3:  # Threshold for relevance
                entry_copy = copy.deepcopy(entry)
                entry_copy.relevance_score = relevance
                relevant_entries.append(entry_copy)
        
        # Sort by relevance and return top entries
        relevant_entries.sort(key=lambda x: x.relevance_score, reverse=True)
        return relevant_entries[:limit]
    
    def _calculate_context_relevance(self, entry: KnowledgeEntry, context: Dict[str, Any]) -> float:
        """Calculate how relevant a knowledge entry is to the given context."""
        relevance_score = 0.0
        
        # Check applicability contexts
        for applicable_context in entry.applicability_contexts:
            if applicable_context in str(context):
                relevance_score += 0.3
        
        # Check content similarity
        context_keywords = set(str(context).lower().split())
        entry_keywords = set(str(entry.content).lower().split())
        
        if context_keywords and entry_keywords:
            intersection = context_keywords.intersection(entry_keywords)
            union = context_keywords.union(entry_keywords)
            jaccard_similarity = len(intersection) / len(union)
            relevance_score += jaccard_similarity * 0.4
        
        # Factor in evidence strength
        relevance_score *= entry.evidence_strength
        
        return min(relevance_score, 1.0)
    
    def transfer_knowledge_to_agent(self, agent_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Transfer relevant knowledge to another agent."""
        relevant_knowledge = self.get_relevant_knowledge(context)
        
        transfer_package = {
            'agent_id': agent_id,
            'transfer_time': datetime.now().isoformat(),
            'knowledge_entries': [asdict(entry) for entry in relevant_knowledge],
            'best_practices': {
                category: practices for category, practices in self.best_practices.items()
                if any(keyword in str(context).lower() for keyword in category.lower().split())
            },
            'anti_patterns': {
                category: patterns for category, patterns in self.anti_patterns.items()
                if any(keyword in str(context).lower() for keyword in category.lower().split())
            }
        }
        
        return transfer_package


class LearningSystem:
    """Comprehensive learning system for autonomous multi-LLM agents."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_id = config.get('agent_id', str(uuid.uuid4()))
        
        # Core components
        self.experience_processor = ExperienceProcessor()
        self.strategy_optimizer = StrategyOptimizer()
        self.knowledge_manager = KnowledgeManager(
            config.get('knowledge_db_path', 'knowledge_base.db')
        )
        
        # Storage
        self.experiences: Dict[str, Experience] = {}
        self.patterns: Dict[str, Pattern] = {}
        self.strategy_updates: List[StrategyUpdate] = []
        
        # Metrics and monitoring
        self.metrics = LearningMetrics()
        self.learning_history = deque(maxlen=1000)
        
        # Configuration
        self.max_experiences = config.get('max_experiences', 10000)
        self.learning_frequency = config.get('learning_frequency', 100)  # Learn every N experiences
        self.min_pattern_support = config.get('min_pattern_support', 3)
        
        # Database for persistence
        self.db_path = config.get('learning_db_path', 'learning_system.db')
        self._initialize_database()
        
        # Thread safety
        self.learning_lock = threading.RLock()
        
        logger.info(f"LearningSystem initialized for agent {self.agent_id}")
    
    def _initialize_database(self):
        """Initialize learning database."""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS experiences (
                experience_id TEXT PRIMARY KEY,
                timestamp TEXT,
                experience_type TEXT,
                agent_id TEXT,
                task_context TEXT,
                actions_taken TEXT,
                outcomes TEXT,
                metrics TEXT,
                success INTEGER,
                execution_time REAL,
                resource_usage TEXT,
                error_info TEXT,
                recovery_actions TEXT,
                collaboration_data TEXT,
                metadata TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT,
                pattern_name TEXT,
                description TEXT,
                conditions TEXT,
                actions TEXT,
                expected_outcomes TEXT,
                confidence_score REAL,
                usage_count INTEGER,
                success_rate REAL,
                avg_execution_time REAL,
                resource_efficiency REAL,
                discovered_date TEXT,
                last_updated TEXT,
                supporting_experiences TEXT,
                tags TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS strategy_updates (
                strategy_id TEXT PRIMARY KEY,
                update_type TEXT,
                old_parameters TEXT,
                new_parameters TEXT,
                expected_improvement REAL,
                confidence REAL,
                reasoning TEXT,
                validation_required INTEGER,
                created_date TEXT,
                applied_date TEXT,
                actual_improvement REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def record_experience(self, execution_result: Dict[str, Any]) -> None:
        """Record a new execution experience for learning."""
        try:
            with self.learning_lock:
                # Create experience from execution result
                experience = Experience(
                    experience_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    experience_type=ExperienceType(execution_result.get('type', 'task_execution')),
                    agent_id=self.agent_id,
                    task_context=execution_result.get('task_context', {}),
                    actions_taken=execution_result.get('actions', []),
                    outcomes=execution_result.get('outcomes', {}),
                    metrics=execution_result.get('metrics', {}),
                    success=execution_result.get('success', False),
                    execution_time=execution_result.get('execution_time', 0.0),
                    resource_usage=execution_result.get('resource_usage', {}),
                    error_info=execution_result.get('error_info'),
                    recovery_actions=execution_result.get('recovery_actions', []),
                    collaboration_data=execution_result.get('collaboration_data'),
                    metadata=execution_result.get('metadata', {})
                )
                
                # Store experience
                self.experiences[experience.experience_id] = experience
                self.metrics.total_experiences += 1
                
                # Store in database
                await self._store_experience(experience)
                
                # Trigger learning if we have enough new experiences
                if self.metrics.total_experiences % self.learning_frequency == 0:
                    await self._trigger_learning_session()
                
                logger.debug(f"Recorded experience: {experience.experience_id}")
                
        except Exception as e:
            logger.error(f"Failed to record experience: {e}")
    
    async def extract_patterns(self) -> List[Pattern]:
        """Extract learning patterns from recorded experiences."""
        try:
            with self.learning_lock:
                experiences_list = list(self.experiences.values())
                
                if len(experiences_list) < self.min_pattern_support:
                    return []
                
                # Extract different types of patterns
                success_patterns = self.experience_processor.identify_success_patterns(experiences_list)
                failure_patterns = self.experience_processor.identify_failure_patterns(experiences_list)
                efficiency_patterns = self.experience_processor.identify_efficiency_patterns(experiences_list)
                
                all_patterns = success_patterns + failure_patterns + efficiency_patterns
                
                # Store new patterns
                new_patterns = []
                for pattern in all_patterns:
                    if pattern.pattern_id not in self.patterns:
                        self.patterns[pattern.pattern_id] = pattern
                        await self._store_pattern(pattern)
                        new_patterns.append(pattern)
                        self.metrics.patterns_discovered += 1
                
                logger.info(f"Extracted {len(new_patterns)} new patterns")
                return new_patterns
                
        except Exception as e:
            logger.error(f"Failed to extract patterns: {e}")
            return []
    
    async def optimize_strategies(self) -> StrategyUpdate:
        """Optimize strategies based on learned patterns."""
        try:
            with self.learning_lock:
                patterns_list = list(self.patterns.values())
                
                if not patterns_list:
                    return StrategyUpdate(
                        strategy_id="no_optimization",
                        update_type="none",
                        old_parameters={},
                        new_parameters={},
                        expected_improvement=0.0,
                        confidence=0.0,
                        reasoning="No patterns available for optimization",
                        validation_required=False
                    )
                
                # Generate strategy updates
                prompt_updates = self.strategy_optimizer.optimize_prompt_strategies(patterns_list)
                parameter_updates = self.strategy_optimizer.optimize_parameter_strategies(patterns_list)
                resource_updates = self.strategy_optimizer.optimize_resource_allocation(patterns_list)
                
                all_updates = prompt_updates + parameter_updates + resource_updates
                
                # Select best update
                if all_updates:
                    best_update = max(all_updates, key=lambda x: x.expected_improvement * x.confidence)
                    
                    # Store update
                    self.strategy_updates.append(best_update)
                    await self._store_strategy_update(best_update)
                    self.metrics.strategies_optimized += 1
                    
                    logger.info(f"Generated strategy optimization: {best_update.strategy_id}")
                    return best_update
                
                return StrategyUpdate(
                    strategy_id="no_optimization",
                    update_type="none",
                    old_parameters={},
                    new_parameters={},
                    expected_improvement=0.0,
                    confidence=0.0,
                    reasoning="No beneficial optimizations found",
                    validation_required=False
                )
                
        except Exception as e:
            logger.error(f"Failed to optimize strategies: {e}")
            return StrategyUpdate(
                strategy_id="error",
                update_type="error",
                old_parameters={},
                new_parameters={},
                expected_improvement=0.0,
                confidence=0.0,
                reasoning=f"Optimization failed: {e}",
                validation_required=False
            )
    
    async def update_knowledge_base(self) -> None:
        """Update knowledge base with new insights."""
        try:
            with self.learning_lock:
                # Extract knowledge from successful patterns
                successful_patterns = [
                    p for p in self.patterns.values() 
                    if p.pattern_type == PatternType.SUCCESS_PATTERN and p.confidence_score > 0.7
                ]
                
                for pattern in successful_patterns:
                    # Create knowledge entry
                    knowledge_entry = KnowledgeEntry(
                        entry_id=str(uuid.uuid4()),
                        category=f"pattern_{pattern.pattern_type.value}",
                        content={
                            'pattern_id': pattern.pattern_id,
                            'description': pattern.description,
                            'conditions': pattern.conditions,
                            'actions': pattern.actions,
                            'outcomes': pattern.expected_outcomes
                        },
                        relevance_score=pattern.confidence_score,
                        evidence_strength=min(pattern.usage_count / 10.0, 1.0),
                        created_date=pattern.discovered_date,
                        updated_date=datetime.now(),
                        source_experiences=pattern.supporting_experiences,
                        applicability_contexts=list(pattern.tags)
                    )
                    
                    self.knowledge_manager.add_knowledge_entry(knowledge_entry)
                    self.metrics.knowledge_entries += 1
                
                # Extract best practices
                for pattern in successful_patterns:
                    if pattern.success_rate > 0.9:
                        self.knowledge_manager.add_best_practice(
                            category=pattern.pattern_name,
                            description=f"Apply pattern: {pattern.description}",
                            success_rate=pattern.success_rate,
                            evidence_count=len(pattern.supporting_experiences)
                        )
                
                # Extract anti-patterns from failures
                failure_patterns = [
                    p for p in self.patterns.values() 
                    if p.pattern_type == PatternType.FAILURE_PATTERN and p.confidence_score > 0.7
                ]
                
                for pattern in failure_patterns:
                    self.knowledge_manager.add_anti_pattern(
                        category=pattern.pattern_name,
                        description=f"Avoid pattern: {pattern.description}",
                        failure_rate=1.0 - pattern.success_rate,
                        evidence_count=len(pattern.supporting_experiences)
                    )
                
                logger.info("Updated knowledge base with new insights")
                
        except Exception as e:
            logger.error(f"Failed to update knowledge base: {e}")
    
    async def share_learning(self, other_agents: List[str]) -> None:
        """Share learning with other agents."""
        try:
            with self.learning_lock:
                for agent_id in other_agents:
                    # Create transfer package
                    transfer_package = {
                        'source_agent': self.agent_id,
                        'target_agent': agent_id,
                        'transfer_time': datetime.now().isoformat(),
                        'patterns': [asdict(pattern) for pattern in self.patterns.values()],
                        'successful_strategies': [
                            asdict(update) for update in self.strategy_updates 
                            if update.expected_improvement > 0.1
                        ],
                        'knowledge_summary': self._create_knowledge_summary()
                    }
                    
                    # In a real implementation, this would send the package to the other agent
                    logger.info(f"Prepared knowledge transfer package for agent {agent_id}")
                    self.metrics.cross_agent_transfers += 1
                
        except Exception as e:
            logger.error(f"Failed to share learning: {e}")
    
    async def _trigger_learning_session(self):
        """Trigger a comprehensive learning session."""
        try:
            session_start = time.time()
            
            # Extract new patterns
            new_patterns = await self.extract_patterns()
            
            # Optimize strategies
            strategy_update = await self.optimize_strategies()
            
            # Update knowledge base
            await self.update_knowledge_base()
            
            # Update metrics
            session_time = time.time() - session_start
            self.metrics.last_learning_session = datetime.now()
            self.metrics.avg_learning_rate = self._calculate_learning_rate()
            self.metrics.improvement_score = self._calculate_improvement_score()
            self.metrics.adaptation_efficiency = self._calculate_adaptation_efficiency()
            
            # Log learning session
            self.learning_history.append({
                'timestamp': datetime.now().isoformat(),
                'patterns_discovered': len(new_patterns),
                'strategies_updated': 1 if strategy_update.strategy_id != "no_optimization" else 0,
                'session_time': session_time,
                'total_experiences': self.metrics.total_experiences
            })
            
            logger.info(f"Learning session completed in {session_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Learning session failed: {e}")
    
    def _calculate_learning_rate(self) -> float:
        """Calculate the current learning rate."""
        if len(self.learning_history) < 2:
            return 0.0
        
        recent_sessions = list(self.learning_history)[-10:]  # Last 10 sessions
        patterns_per_session = [session['patterns_discovered'] for session in recent_sessions]
        
        if patterns_per_session:
            return statistics.mean(patterns_per_session)
        
        return 0.0
    
    def _calculate_improvement_score(self) -> float:
        """Calculate overall improvement score."""
        if not self.experiences:
            return 0.0
        
        # Compare recent performance to historical performance
        experiences_list = list(self.experiences.values())
        experiences_list.sort(key=lambda x: x.timestamp)
        
        if len(experiences_list) < 20:
            return 0.0
        
        # Split into historical and recent
        split_point = len(experiences_list) // 2
        historical = experiences_list[:split_point]
        recent = experiences_list[split_point:]
        
        # Calculate success rates
        historical_success = sum(1 for exp in historical if exp.success) / len(historical)
        recent_success = sum(1 for exp in recent if exp.success) / len(recent)
        
        # Calculate efficiency improvements
        historical_efficiency = statistics.mean(exp.metrics.get('efficiency', 0.0) for exp in historical)
        recent_efficiency = statistics.mean(exp.metrics.get('efficiency', 0.0) for exp in recent)
        
        # Combined improvement score
        success_improvement = recent_success - historical_success
        efficiency_improvement = recent_efficiency - historical_efficiency
        
        return (success_improvement + efficiency_improvement) / 2
    
    def _calculate_adaptation_efficiency(self) -> float:
        """Calculate how efficiently the system adapts."""
        if len(self.learning_history) < 5:
            return 0.0
        
        # Measure learning speed: patterns discovered per unit time
        recent_sessions = list(self.learning_history)[-5:]
        total_patterns = sum(session['patterns_discovered'] for session in recent_sessions)
        total_time = sum(session['session_time'] for session in recent_sessions)
        
        if total_time > 0:
            return total_patterns / total_time
        
        return 0.0
    
    def _create_knowledge_summary(self) -> Dict[str, Any]:
        """Create a summary of current knowledge."""
        return {
            'total_patterns': len(self.patterns),
            'success_patterns': len([p for p in self.patterns.values() 
                                   if p.pattern_type == PatternType.SUCCESS_PATTERN]),
            'failure_patterns': len([p for p in self.patterns.values() 
                                   if p.pattern_type == PatternType.FAILURE_PATTERN]),
            'efficiency_patterns': len([p for p in self.patterns.values() 
                                      if p.pattern_type == PatternType.EFFICIENCY_PATTERN]),
            'best_practices_count': sum(len(practices) for practices in self.knowledge_manager.best_practices.values()),
            'anti_patterns_count': sum(len(patterns) for patterns in self.knowledge_manager.anti_patterns.values()),
            'learning_metrics': asdict(self.metrics)
        }
    
    # Database storage methods
    async def _store_experience(self, experience: Experience):
        """Store experience in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO experiences
                (experience_id, timestamp, experience_type, agent_id, task_context,
                 actions_taken, outcomes, metrics, success, execution_time,
                 resource_usage, error_info, recovery_actions, collaboration_data, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                experience.experience_id,
                experience.timestamp.isoformat(),
                experience.experience_type.value,
                experience.agent_id,
                json.dumps(experience.task_context),
                json.dumps(experience.actions_taken),
                json.dumps(experience.outcomes),
                json.dumps(experience.metrics),
                1 if experience.success else 0,
                experience.execution_time,
                json.dumps(experience.resource_usage),
                json.dumps(experience.error_info) if experience.error_info else None,
                json.dumps(experience.recovery_actions),
                json.dumps(experience.collaboration_data) if experience.collaboration_data else None,
                json.dumps(experience.metadata)
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store experience: {e}")
    
    async def _store_pattern(self, pattern: Pattern):
        """Store pattern in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO patterns
                (pattern_id, pattern_type, pattern_name, description, conditions,
                 actions, expected_outcomes, confidence_score, usage_count,
                 success_rate, avg_execution_time, resource_efficiency,
                 discovered_date, last_updated, supporting_experiences, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.pattern_id,
                pattern.pattern_type.value,
                pattern.pattern_name,
                pattern.description,
                json.dumps(pattern.conditions),
                json.dumps(pattern.actions),
                json.dumps(pattern.expected_outcomes),
                pattern.confidence_score,
                pattern.usage_count,
                pattern.success_rate,
                pattern.avg_execution_time,
                pattern.resource_efficiency,
                pattern.discovered_date.isoformat(),
                pattern.last_updated.isoformat(),
                json.dumps(pattern.supporting_experiences),
                json.dumps(list(pattern.tags))
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store pattern: {e}")
    
    async def _store_strategy_update(self, update: StrategyUpdate):
        """Store strategy update in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO strategy_updates
                (strategy_id, update_type, old_parameters, new_parameters,
                 expected_improvement, confidence, reasoning, validation_required, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                update.strategy_id,
                update.update_type,
                json.dumps(update.old_parameters),
                json.dumps(update.new_parameters),
                update.expected_improvement,
                update.confidence,
                update.reasoning,
                1 if update.validation_required else 0,
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store strategy update: {e}")
    
    # Public utility methods
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        return {
            'metrics': asdict(self.metrics),
            'recent_learning_history': list(self.learning_history)[-10:],
            'pattern_distribution': self._get_pattern_distribution(),
            'knowledge_summary': self._create_knowledge_summary(),
            'adaptation_trends': self._get_adaptation_trends()
        }
    
    def _get_pattern_distribution(self) -> Dict[str, int]:
        """Get distribution of pattern types."""
        distribution = defaultdict(int)
        for pattern in self.patterns.values():
            distribution[pattern.pattern_type.value] += 1
        return dict(distribution)
    
    def _get_adaptation_trends(self) -> Dict[str, Any]:
        """Get trends in adaptation and learning."""
        if len(self.learning_history) < 3:
            return {'trend': 'insufficient_data'}
        
        recent_sessions = list(self.learning_history)[-5:]
        patterns_trend = [session['patterns_discovered'] for session in recent_sessions]
        
        if len(patterns_trend) > 1:
            trend_direction = 'increasing' if patterns_trend[-1] > patterns_trend[0] else 'decreasing'
        else:
            trend_direction = 'stable'
        
        return {
            'pattern_discovery_trend': trend_direction,
            'avg_patterns_per_session': statistics.mean(patterns_trend),
            'learning_velocity': self.metrics.avg_learning_rate,
            'improvement_trajectory': self.metrics.improvement_score
        }
    
    async def cleanup(self):
        """Cleanup learning system resources."""
        logger.info("Cleaning up LearningSystem")
        
        # Save final state
        for pattern in self.patterns.values():
            await self._store_pattern(pattern)
        
        # Final metrics update
        self.metrics.last_learning_session = datetime.now()