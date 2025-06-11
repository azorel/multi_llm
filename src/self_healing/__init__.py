"""
Self-healing system for autonomous multi-LLM agents.

This module provides comprehensive self-healing capabilities including:
- Error detection and anomaly monitoring
- Automated recovery strategies and code fixes
- Continuous healing loops and system monitoring
- Machine learning-based pattern recognition and adaptation
"""

from .error_detector import (
    ErrorDetector,
    ErrorEvent,
    ErrorSeverity,
    ErrorType,
    Anomaly,
    AnomalyType,
    ErrorStream,
    PatternRecognizer,
    AnomalyDetector,
    FailurePredictor,
    RootCauseAnalyzer,
    FailureProbability,
    RootCause
)

from .recovery_manager import (
    RecoveryManager,
    RecoveryStrategy,
    RecoveryStatus,
    RecoveryResult,
    RecoveryContext,
    CodeFix,
    FixType,
    AlternativeApproach,
    RecoveryPattern
)

from .healing_loop import (
    HealingLoop,
    HealingState,
    InterventionTrigger,
    HealingSession,
    SystemHealth,
    HealingConfiguration,
    PerformanceOptimizer
)

from .learning_system import (
    LearningSystem,
    Experience,
    ExperienceType,
    Pattern,
    PatternType,
    StrategyUpdate,
    KnowledgeEntry,
    LearningMetrics,
    LearningObjective
)

__all__ = [
    # Error detection
    "ErrorDetector",
    "ErrorEvent",
    "ErrorSeverity", 
    "ErrorType",
    "Anomaly",
    "AnomalyType",
    "ErrorStream",
    "PatternRecognizer",
    "AnomalyDetector",
    "FailurePredictor",
    "RootCauseAnalyzer",
    "FailureProbability",
    "RootCause",
    
    # Recovery management
    "RecoveryManager",
    "RecoveryStrategy",
    "RecoveryStatus",
    "RecoveryResult",
    "RecoveryContext",
    "CodeFix",
    "FixType",
    "AlternativeApproach", 
    "RecoveryPattern",
    
    # Healing loop
    "HealingLoop",
    "HealingState",
    "InterventionTrigger",
    "HealingSession",
    "SystemHealth",
    "HealingConfiguration",
    "PerformanceOptimizer",
    
    # Learning system
    "LearningSystem",
    "Experience",
    "ExperienceType",
    "Pattern", 
    "PatternType",
    "StrategyUpdate",
    "KnowledgeEntry",
    "LearningMetrics",
    "LearningObjective"
]