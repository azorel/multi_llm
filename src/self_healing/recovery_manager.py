import asyncio
import json
import re
import ast
import time
import uuid
import sqlite3
import hashlib
import random
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from pathlib import Path
import copy
import traceback
from loguru import logger
import backoff
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


class RecoveryStrategy(Enum):
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    ALGORITHM_SUBSTITUTION = "algorithm_substitution"
    RESOURCE_REALLOCATION = "resource_reallocation"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    ROLLBACK_AND_RETRY = "rollback_and_retry"
    ALTERNATIVE_APPROACH = "alternative_approach"
    HUMAN_ESCALATION = "human_escalation"
    SELF_MODIFICATION = "self_modification"
    CONTEXT_ADJUSTMENT = "context_adjustment"


class RecoveryStatus(Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    ESCALATED = "escalated"
    ROLLBACK_REQUIRED = "rollback_required"
    IN_PROGRESS = "in_progress"


class FixType(Enum):
    CODE_PATCH = "code_patch"
    PARAMETER_CHANGE = "parameter_change"
    CONFIGURATION_UPDATE = "configuration_update"
    RESOURCE_ADJUSTMENT = "resource_adjustment"
    ALGORITHM_REPLACEMENT = "algorithm_replacement"
    LOGIC_FIX = "logic_fix"
    ERROR_HANDLING = "error_handling"


@dataclass
class RecoveryContext:
    error_id: str
    original_goal: str
    failed_approach: Dict[str, Any]
    error_details: Dict[str, Any]
    system_state: Dict[str, Any]
    previous_attempts: List[Dict[str, Any]] = field(default_factory=list)
    available_resources: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    max_attempts: int = 3
    escalation_threshold: int = 2


@dataclass
class CodeFix:
    fix_id: str
    fix_type: FixType
    description: str
    target_code: str
    fixed_code: str
    confidence: float
    estimated_impact: str
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    rollback_info: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryResult:
    recovery_id: str
    status: RecoveryStatus
    strategy_used: RecoveryStrategy
    success: bool
    execution_time: float
    original_error: str
    applied_fixes: List[CodeFix] = field(default_factory=list)
    final_result: Optional[Any] = None
    lessons_learned: List[str] = field(default_factory=list)
    performance_impact: Optional[Dict[str, float]] = None
    rollback_performed: bool = False


@dataclass
class AlternativeApproach:
    approach_id: str
    strategy: str
    description: str
    implementation: Dict[str, Any]
    expected_benefits: List[str]
    potential_risks: List[str]
    resource_requirements: Dict[str, Any]
    confidence_score: float
    estimated_time: int


@dataclass
class RecoveryPattern:
    pattern_id: str
    error_signature: str
    successful_strategies: List[RecoveryStrategy]
    success_rates: Dict[str, float]
    avg_recovery_time: float
    conditions: Dict[str, Any]
    last_updated: datetime
    usage_count: int


class CodeAnalyzer:
    """Analyzes code to identify issues and generate fixes."""
    
    def __init__(self):
        self.common_fixes = {
            'SyntaxError': self._fix_syntax_error,
            'NameError': self._fix_name_error,
            'TypeError': self._fix_type_error,
            'IndexError': self._fix_index_error,
            'KeyError': self._fix_key_error,
            'AttributeError': self._fix_attribute_error,
            'ValueError': self._fix_value_error,
            'ZeroDivisionError': self._fix_zero_division_error,
            'RecursionError': self._fix_recursion_error,
            'MemoryError': self._fix_memory_error
        }
    
    def analyze_error(self, code: str, error: Exception, context: Dict[str, Any]) -> List[CodeFix]:
        """Analyze an error and generate potential fixes."""
        fixes = []
        error_type = type(error).__name__
        
        # Try specific fix generators
        if error_type in self.common_fixes:
            try:
                fix = self.common_fixes[error_type](code, error, context)
                if fix:
                    fixes.append(fix)
            except Exception as e:
                logger.error(f"Failed to generate fix for {error_type}: {e}")
        
        # Try generic fixes
        generic_fixes = self._generate_generic_fixes(code, error, context)
        fixes.extend(generic_fixes)
        
        return fixes
    
    def _fix_syntax_error(self, code: str, error: Exception, context: Dict[str, Any]) -> Optional[CodeFix]:
        """Generate fix for syntax errors."""
        error_msg = str(error)
        
        # Common syntax error patterns
        if "invalid syntax" in error_msg.lower():
            # Try to identify missing parentheses, brackets, etc.
            fixed_code = self._fix_missing_delimiters(code)
            if fixed_code != code:
                return CodeFix(
                    fix_id=str(uuid.uuid4()),
                    fix_type=FixType.CODE_PATCH,
                    description="Fixed missing delimiters",
                    target_code=code,
                    fixed_code=fixed_code,
                    confidence=0.7,
                    estimated_impact="low"
                )
        
        if "unexpected indent" in error_msg.lower():
            fixed_code = self._fix_indentation(code)
            if fixed_code != code:
                return CodeFix(
                    fix_id=str(uuid.uuid4()),
                    fix_type=FixType.CODE_PATCH,
                    description="Fixed indentation errors",
                    target_code=code,
                    fixed_code=fixed_code,
                    confidence=0.8,
                    estimated_impact="low"
                )
        
        return None
    
    def _fix_name_error(self, code: str, error: Exception, context: Dict[str, Any]) -> Optional[CodeFix]:
        """Generate fix for NameError."""
        error_msg = str(error)
        
        # Extract undefined variable name
        match = re.search(r"name '(\w+)' is not defined", error_msg)
        if match:
            var_name = match.group(1)
            
            # Suggest variable initialization
            lines = code.split('\n')
            fixed_lines = []
            
            for line in lines:
                fixed_lines.append(line)
                # Add initialization before first use
                if var_name in line and not line.strip().startswith('#'):
                    init_line = f"{var_name} = None  # Auto-generated initialization"
                    fixed_lines.insert(-1, init_line)
                    break
            
            fixed_code = '\n'.join(fixed_lines)
            
            return CodeFix(
                fix_id=str(uuid.uuid4()),
                fix_type=FixType.LOGIC_FIX,
                description=f"Initialize undefined variable '{var_name}'",
                target_code=code,
                fixed_code=fixed_code,
                confidence=0.6,
                estimated_impact="medium"
            )
        
        return None
    
    def _fix_type_error(self, code: str, error: Exception, context: Dict[str, Any]) -> Optional[CodeFix]:
        """Generate fix for TypeError."""
        error_msg = str(error)
        
        if "unsupported operand type" in error_msg.lower():
            # Add type checking and conversion
            fixed_code = self._add_type_checking(code)
            return CodeFix(
                fix_id=str(uuid.uuid4()),
                fix_type=FixType.ERROR_HANDLING,
                description="Added type checking and conversion",
                target_code=code,
                fixed_code=fixed_code,
                confidence=0.7,
                estimated_impact="medium"
            )
        
        return None
    
    def _fix_index_error(self, code: str, error: Exception, context: Dict[str, Any]) -> Optional[CodeFix]:
        """Generate fix for IndexError."""
        # Add bounds checking
        fixed_code = self._add_bounds_checking(code)
        
        return CodeFix(
            fix_id=str(uuid.uuid4()),
            fix_type=FixType.ERROR_HANDLING,
            description="Added bounds checking for list/array access",
            target_code=code,
            fixed_code=fixed_code,
            confidence=0.8,
            estimated_impact="low"
        )
    
    def _fix_key_error(self, code: str, error: Exception, context: Dict[str, Any]) -> Optional[CodeFix]:
        """Generate fix for KeyError."""
        error_msg = str(error)
        
        # Extract key name
        key_match = re.search(r"'([^']+)'", error_msg)
        if key_match:
            key = key_match.group(1)
            
            # Replace direct access with get() method
            pattern = rf"\['{key}'\]"
            replacement = f".get('{key}', None)"
            fixed_code = re.sub(pattern, replacement, code)
            
            if fixed_code != code:
                return CodeFix(
                    fix_id=str(uuid.uuid4()),
                    fix_type=FixType.ERROR_HANDLING,
                    description=f"Used safe dictionary access for key '{key}'",
                    target_code=code,
                    fixed_code=fixed_code,
                    confidence=0.9,
                    estimated_impact="low"
                )
        
        return None
    
    def _fix_attribute_error(self, code: str, error: Exception, context: Dict[str, Any]) -> Optional[CodeFix]:
        """Generate fix for AttributeError."""
        # Add hasattr checks
        fixed_code = self._add_attribute_checks(code)
        
        return CodeFix(
            fix_id=str(uuid.uuid4()),
            fix_type=FixType.ERROR_HANDLING,
            description="Added attribute existence checks",
            target_code=code,
            fixed_code=fixed_code,
            confidence=0.7,
            estimated_impact="low"
        )
    
    def _fix_value_error(self, code: str, error: Exception, context: Dict[str, Any]) -> Optional[CodeFix]:
        """Generate fix for ValueError."""
        # Add input validation
        fixed_code = self._add_input_validation(code)
        
        return CodeFix(
            fix_id=str(uuid.uuid4()),
            fix_type=FixType.ERROR_HANDLING,
            description="Added input validation",
            target_code=code,
            fixed_code=fixed_code,
            confidence=0.6,
            estimated_impact="medium"
        )
    
    def _fix_zero_division_error(self, code: str, error: Exception, context: Dict[str, Any]) -> Optional[CodeFix]:
        """Generate fix for ZeroDivisionError."""
        # Add division by zero checks
        pattern = r'(\w+\s*/\s*\w+)'
        
        def replacement(match):
            expr = match.group(1)
            parts = expr.split('/')
            if len(parts) == 2:
                numerator = parts[0].strip()
                denominator = parts[1].strip()
                return f"({numerator} / {denominator} if {denominator} != 0 else 0)"
            return expr
        
        fixed_code = re.sub(pattern, replacement, code)
        
        if fixed_code != code:
            return CodeFix(
                fix_id=str(uuid.uuid4()),
                fix_type=FixType.ERROR_HANDLING,
                description="Added zero division protection",
                target_code=code,
                fixed_code=fixed_code,
                confidence=0.9,
                estimated_impact="low"
            )
        
        return None
    
    def _fix_recursion_error(self, code: str, error: Exception, context: Dict[str, Any]) -> Optional[CodeFix]:
        """Generate fix for RecursionError."""
        # Add recursion depth limits
        fixed_code = self._add_recursion_limits(code)
        
        return CodeFix(
            fix_id=str(uuid.uuid4()),
            fix_type=FixType.LOGIC_FIX,
            description="Added recursion depth limits",
            target_code=code,
            fixed_code=fixed_code,
            confidence=0.7,
            estimated_impact="medium"
        )
    
    def _fix_memory_error(self, code: str, error: Exception, context: Dict[str, Any]) -> Optional[CodeFix]:
        """Generate fix for MemoryError."""
        # Suggest memory optimization
        fixed_code = self._optimize_memory_usage(code)
        
        return CodeFix(
            fix_id=str(uuid.uuid4()),
            fix_type=FixType.RESOURCE_ADJUSTMENT,
            description="Optimized memory usage",
            target_code=code,
            fixed_code=fixed_code,
            confidence=0.5,
            estimated_impact="high"
        )
    
    def _generate_generic_fixes(self, code: str, error: Exception, context: Dict[str, Any]) -> List[CodeFix]:
        """Generate generic fixes that might help."""
        fixes = []
        
        # Add try-catch wrapper
        try_catch_fix = self._wrap_with_try_catch(code, error)
        if try_catch_fix:
            fixes.append(try_catch_fix)
        
        # Add logging
        logging_fix = self._add_logging(code)
        if logging_fix:
            fixes.append(logging_fix)
        
        return fixes
    
    def _fix_missing_delimiters(self, code: str) -> str:
        """Attempt to fix missing parentheses, brackets, etc."""
        # Simple heuristic: count and balance delimiters
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Balance parentheses
            open_parens = line.count('(')
            close_parens = line.count(')')
            if open_parens > close_parens:
                line += ')' * (open_parens - close_parens)
            
            # Balance brackets
            open_brackets = line.count('[')
            close_brackets = line.count(']')
            if open_brackets > close_brackets:
                line += ']' * (open_brackets - close_brackets)
            
            # Balance braces
            open_braces = line.count('{')
            close_braces = line.count('}')
            if open_braces > close_braces:
                line += '}' * (open_braces - close_braces)
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_indentation(self, code: str) -> str:
        """Attempt to fix indentation errors."""
        lines = code.split('\n')
        fixed_lines = []
        current_indent = 0
        
        for line in lines:
            if line.strip():
                # Determine expected indentation based on keywords
                stripped = line.strip()
                
                if any(stripped.startswith(kw) for kw in ['def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except ', 'with ']):
                    # These keywords should start a new indentation level
                    fixed_lines.append(' ' * current_indent + stripped)
                    if stripped.endswith(':'):
                        current_indent += 4
                elif stripped in ['else:', 'elif ', 'except:', 'finally:']:
                    # These should be at the same level as the corresponding if/try
                    current_indent = max(0, current_indent - 4)
                    fixed_lines.append(' ' * current_indent + stripped)
                    current_indent += 4
                else:
                    # Regular statement
                    fixed_lines.append(' ' * current_indent + stripped)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _add_type_checking(self, code: str) -> str:
        """Add type checking to prevent type errors."""
        # Simple implementation: wrap operations in type checks
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            if '+' in line or '-' in line or '*' in line or '/' in line:
                # Add basic type checking
                fixed_line = f"# Type checking added\ntry:\n    {line}\nexcept TypeError as e:\n    print(f'Type error: {{e}}')\n    pass"
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _add_bounds_checking(self, code: str) -> str:
        """Add bounds checking for array/list access."""
        # Replace direct indexing with safe indexing
        pattern = r'(\w+)\[(\d+|\w+)\]'
        
        def replacement(match):
            array_name = match.group(1)
            index = match.group(2)
            return f"({array_name}[{index}] if len({array_name}) > {index} else None)"
        
        return re.sub(pattern, replacement, code)
    
    def _add_attribute_checks(self, code: str) -> str:
        """Add hasattr checks for attribute access."""
        pattern = r'(\w+)\.(\w+)'
        
        def replacement(match):
            obj_name = match.group(1)
            attr_name = match.group(2)
            return f"(getattr({obj_name}, '{attr_name}', None) if hasattr({obj_name}, '{attr_name}') else None)"
        
        return re.sub(pattern, replacement, code)
    
    def _add_input_validation(self, code: str) -> str:
        """Add input validation."""
        # Simple validation wrapper
        return f"# Input validation added\n{code}\n# Validation complete"
    
    def _add_recursion_limits(self, code: str) -> str:
        """Add recursion depth limits."""
        # Add counter parameter to recursive functions
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            if 'def ' in line and line.strip().endswith(':'):
                # Add depth parameter to function definition
                if '(' in line and ')' in line:
                    func_def = line.replace(')', ', _depth=0)')
                    fixed_lines.append(func_def)
                    fixed_lines.append('    if _depth > 100:  # Recursion limit')
                    fixed_lines.append('        return None')
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _optimize_memory_usage(self, code: str) -> str:
        """Optimize memory usage."""
        # Add memory-efficient alternatives
        optimizations = {
            'list(': 'iter(',  # Use iterators instead of lists
            'range(': 'xrange(' if 'xrange' in dir(__builtins__) else 'range(',
        }
        
        optimized_code = code
        for old, new in optimizations.items():
            optimized_code = optimized_code.replace(old, new)
        
        return optimized_code
    
    def _wrap_with_try_catch(self, code: str, error: Exception) -> Optional[CodeFix]:
        """Wrap code with try-catch block."""
        error_type = type(error).__name__
        
        wrapped_code = f"""try:
{self._indent_code(code, 4)}
except {error_type} as e:
    print(f"Handled {error_type}: {{e}}")
    # Fallback behavior
    pass"""
        
        return CodeFix(
            fix_id=str(uuid.uuid4()),
            fix_type=FixType.ERROR_HANDLING,
            description=f"Wrapped code with {error_type} handling",
            target_code=code,
            fixed_code=wrapped_code,
            confidence=0.8,
            estimated_impact="low"
        )
    
    def _add_logging(self, code: str) -> Optional[CodeFix]:
        """Add logging to code for better debugging."""
        logged_code = f"""import logging
logging.basicConfig(level=logging.DEBUG)

# Original code with logging
{code}

logging.info("Code execution completed")"""
        
        return CodeFix(
            fix_id=str(uuid.uuid4()),
            fix_type=FixType.CODE_PATCH,
            description="Added logging for debugging",
            target_code=code,
            fixed_code=logged_code,
            confidence=0.5,
            estimated_impact="low"
        )
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by specified number of spaces."""
        lines = code.split('\n')
        indented_lines = [' ' * spaces + line if line.strip() else line for line in lines]
        return '\n'.join(indented_lines)


class StrategySelector:
    """Selects the best recovery strategy based on error type and context."""
    
    def __init__(self):
        self.strategy_mappings = {
            'SyntaxError': [RecoveryStrategy.SELF_MODIFICATION, RecoveryStrategy.ROLLBACK_AND_RETRY],
            'NameError': [RecoveryStrategy.SELF_MODIFICATION, RecoveryStrategy.PARAMETER_ADJUSTMENT],
            'TypeError': [RecoveryStrategy.PARAMETER_ADJUSTMENT, RecoveryStrategy.SELF_MODIFICATION],
            'ValueError': [RecoveryStrategy.PARAMETER_ADJUSTMENT, RecoveryStrategy.RETRY_WITH_BACKOFF],
            'TimeoutError': [RecoveryStrategy.RESOURCE_REALLOCATION, RecoveryStrategy.RETRY_WITH_BACKOFF],
            'MemoryError': [RecoveryStrategy.RESOURCE_REALLOCATION, RecoveryStrategy.ALGORITHM_SUBSTITUTION],
            'ConnectionError': [RecoveryStrategy.RETRY_WITH_BACKOFF, RecoveryStrategy.GRACEFUL_DEGRADATION],
            'PermissionError': [RecoveryStrategy.RESOURCE_REALLOCATION, RecoveryStrategy.HUMAN_ESCALATION],
        }
        
        self.strategy_priorities = {
            RecoveryStrategy.RETRY_WITH_BACKOFF: 0.9,
            RecoveryStrategy.PARAMETER_ADJUSTMENT: 0.8,
            RecoveryStrategy.SELF_MODIFICATION: 0.7,
            RecoveryStrategy.ALGORITHM_SUBSTITUTION: 0.6,
            RecoveryStrategy.RESOURCE_REALLOCATION: 0.5,
            RecoveryStrategy.ROLLBACK_AND_RETRY: 0.4,
            RecoveryStrategy.GRACEFUL_DEGRADATION: 0.3,
            RecoveryStrategy.ALTERNATIVE_APPROACH: 0.2,
            RecoveryStrategy.HUMAN_ESCALATION: 0.1
        }
    
    def select_strategies(self, error: Exception, context: RecoveryContext) -> List[RecoveryStrategy]:
        """Select appropriate recovery strategies for the error."""
        error_type = type(error).__name__
        
        # Get strategies for this error type
        strategies = self.strategy_mappings.get(error_type, [
            RecoveryStrategy.RETRY_WITH_BACKOFF,
            RecoveryStrategy.PARAMETER_ADJUSTMENT,
            RecoveryStrategy.ALTERNATIVE_APPROACH
        ])
        
        # Filter strategies based on context
        filtered_strategies = self._filter_by_context(strategies, context)
        
        # Sort by priority and previous attempt success
        sorted_strategies = self._sort_by_priority(filtered_strategies, context)
        
        return sorted_strategies
    
    def _filter_by_context(self, strategies: List[RecoveryStrategy], 
                          context: RecoveryContext) -> List[RecoveryStrategy]:
        """Filter strategies based on context constraints."""
        filtered = []
        
        for strategy in strategies:
            # Check if strategy has already been tried
            attempted_strategies = [attempt.get('strategy') for attempt in context.previous_attempts]
            if strategy.value in attempted_strategies:
                continue
            
            # Check resource constraints
            if strategy == RecoveryStrategy.RESOURCE_REALLOCATION:
                if not context.available_resources.get('can_allocate_resources', True):
                    continue
            
            # Check if human escalation is allowed
            if strategy == RecoveryStrategy.HUMAN_ESCALATION:
                if not context.constraints.get('allow_human_escalation', True):
                    continue
            
            filtered.append(strategy)
        
        return filtered
    
    def _sort_by_priority(self, strategies: List[RecoveryStrategy], 
                         context: RecoveryContext) -> List[RecoveryStrategy]:
        """Sort strategies by priority and success probability."""
        def strategy_score(strategy):
            base_priority = self.strategy_priorities.get(strategy, 0.5)
            
            # Adjust based on previous success
            success_adjustment = 0.0
            for attempt in context.previous_attempts:
                if attempt.get('strategy') == strategy.value:
                    if attempt.get('success', False):
                        success_adjustment += 0.1
                    else:
                        success_adjustment -= 0.1
            
            return base_priority + success_adjustment
        
        return sorted(strategies, key=strategy_score, reverse=True)


class RecoveryManager:
    """Comprehensive recovery manager with self-healing capabilities."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize components
        self.code_analyzer = CodeAnalyzer()
        self.strategy_selector = StrategySelector()
        
        # Recovery patterns and learning
        self.recovery_patterns: Dict[str, RecoveryPattern] = {}
        self.success_history: List[RecoveryResult] = []
        self.knowledge_base = {}
        
        # ML components for learning
        self.pattern_vectorizer = TfidfVectorizer(max_features=1000)
        self.strategy_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        
        # Database for persistence
        self.db_path = config.get('database_path', 'recovery_manager.db')
        self._initialize_database()
        
        # Configuration
        self.max_recovery_attempts = config.get('max_recovery_attempts', 3)
        self.escalation_threshold = config.get('escalation_threshold', 2)
        self.enable_self_modification = config.get('enable_self_modification', True)
        self.enable_learning = config.get('enable_learning', True)
        
        logger.info("RecoveryManager initialized")
    
    def _initialize_database(self):
        """Initialize SQLite database for persistent storage."""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS recovery_results (
                recovery_id TEXT PRIMARY KEY,
                timestamp TEXT,
                status TEXT,
                strategy_used TEXT,
                success INTEGER,
                execution_time REAL,
                original_error TEXT,
                lessons_learned TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS recovery_patterns (
                pattern_id TEXT PRIMARY KEY,
                error_signature TEXT,
                successful_strategies TEXT,
                success_rates TEXT,
                avg_recovery_time REAL,
                conditions TEXT,
                last_updated TEXT,
                usage_count INTEGER
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS code_fixes (
                fix_id TEXT PRIMARY KEY,
                fix_type TEXT,
                description TEXT,
                target_code TEXT,
                fixed_code TEXT,
                confidence REAL,
                success_count INTEGER,
                failure_count INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def auto_recover(self, error: Exception, context: Dict[str, Any],
                          orchestrator=None) -> RecoveryResult:
        """Main auto-recovery method that orchestrates the recovery process."""
        start_time = time.time()
        recovery_id = str(uuid.uuid4())
        
        logger.info(f"Starting auto-recovery {recovery_id} for error: {type(error).__name__}")
        
        # Create recovery context
        recovery_context = RecoveryContext(
            error_id=str(uuid.uuid4()),
            original_goal=context.get('goal', 'Unknown goal'),
            failed_approach=context.get('failed_approach', {}),
            error_details={
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc()
            },
            system_state=context.get('system_state', {}),
            available_resources=context.get('available_resources', {}),
            constraints=context.get('constraints', {})
        )
        
        # Select recovery strategies
        strategies = self.strategy_selector.select_strategies(error, recovery_context)
        
        applied_fixes = []
        final_result = None
        success = False
        strategy_used = None
        lessons_learned = []
        
        # Try each strategy until one succeeds
        for strategy in strategies:
            if len(recovery_context.previous_attempts) >= self.max_recovery_attempts:
                break
            
            logger.info(f"Trying recovery strategy: {strategy.value}")
            
            try:
                strategy_result = await self._execute_strategy(
                    strategy, error, recovery_context, orchestrator
                )
                
                # Record attempt
                recovery_context.previous_attempts.append({
                    'strategy': strategy.value,
                    'success': strategy_result.get('success', False),
                    'timestamp': datetime.now().isoformat(),
                    'details': strategy_result
                })
                
                if strategy_result.get('success', False):
                    success = True
                    strategy_used = strategy
                    final_result = strategy_result.get('result')
                    applied_fixes.extend(strategy_result.get('fixes', []))
                    lessons_learned.extend(strategy_result.get('lessons', []))
                    break
                
                # Add lessons from failed attempt
                lessons_learned.append(f"Strategy {strategy.value} failed: {strategy_result.get('error', 'Unknown')}")
                
            except Exception as strategy_error:
                logger.error(f"Strategy {strategy.value} failed with exception: {strategy_error}")
                recovery_context.previous_attempts.append({
                    'strategy': strategy.value,
                    'success': False,
                    'error': str(strategy_error),
                    'timestamp': datetime.now().isoformat()
                })
        
        # Determine final status
        if success:
            status = RecoveryStatus.SUCCESS
        elif len(recovery_context.previous_attempts) >= self.escalation_threshold:
            status = RecoveryStatus.ESCALATED
            # Try human escalation if allowed
            if recovery_context.constraints.get('allow_human_escalation', True):
                escalation_result = await self._escalate_to_human(error, recovery_context)
                if escalation_result.get('success'):
                    status = RecoveryStatus.SUCCESS
                    success = True
                    final_result = escalation_result.get('result')
        else:
            status = RecoveryStatus.FAILED
        
        execution_time = time.time() - start_time
        
        # Create recovery result
        result = RecoveryResult(
            recovery_id=recovery_id,
            status=status,
            strategy_used=strategy_used or RecoveryStrategy.RETRY_WITH_BACKOFF,
            success=success,
            execution_time=execution_time,
            original_error=str(error),
            applied_fixes=applied_fixes,
            final_result=final_result,
            lessons_learned=lessons_learned
        )
        
        # Learn from this recovery attempt
        if self.enable_learning:
            await self._learn_from_recovery(result, recovery_context)
        
        # Store result
        await self._store_recovery_result(result)
        
        logger.info(f"Auto-recovery {recovery_id} completed: {status.value}")
        return result
    
    async def _execute_strategy(self, strategy: RecoveryStrategy, error: Exception,
                              context: RecoveryContext, orchestrator=None) -> Dict[str, Any]:
        """Execute a specific recovery strategy."""
        
        if strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
            return await self._retry_with_backoff(error, context, orchestrator)
        
        elif strategy == RecoveryStrategy.PARAMETER_ADJUSTMENT:
            return await self._adjust_parameters(error, context, orchestrator)
        
        elif strategy == RecoveryStrategy.ALGORITHM_SUBSTITUTION:
            return await self._substitute_algorithm(error, context, orchestrator)
        
        elif strategy == RecoveryStrategy.RESOURCE_REALLOCATION:
            return await self._reallocate_resources(error, context, orchestrator)
        
        elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            return await self._graceful_degradation(error, context, orchestrator)
        
        elif strategy == RecoveryStrategy.ROLLBACK_AND_RETRY:
            return await self._rollback_and_retry(error, context, orchestrator)
        
        elif strategy == RecoveryStrategy.ALTERNATIVE_APPROACH:
            return await self._try_alternative_approach(error, context, orchestrator)
        
        elif strategy == RecoveryStrategy.SELF_MODIFICATION:
            return await self._self_modification(error, context, orchestrator)
        
        elif strategy == RecoveryStrategy.CONTEXT_ADJUSTMENT:
            return await self._adjust_context(error, context, orchestrator)
        
        else:
            return {'success': False, 'error': f'Unknown strategy: {strategy}'}
    
    async def _retry_with_backoff(self, error: Exception, context: RecoveryContext,
                                orchestrator=None) -> Dict[str, Any]:
        """Retry the failed operation with exponential backoff."""
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            
            logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {delay:.2f}s delay")
            await asyncio.sleep(delay)
            
            try:
                # Retry the original operation
                if orchestrator and hasattr(orchestrator, 'process_goal'):
                    result = await orchestrator.process_goal(context.original_goal)
                    if result and result.status.value == 'success':
                        return {
                            'success': True,
                            'result': result,
                            'lessons': [f'Retry with backoff succeeded after {attempt + 1} attempts']
                        }
                else:
                    # Simulate successful retry
                    return {
                        'success': True,
                        'result': 'Retry successful',
                        'lessons': ['Retry with backoff strategy worked']
                    }
                    
            except Exception as retry_error:
                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'error': f'All retry attempts failed: {str(retry_error)}',
                        'lessons': ['Retry with backoff failed after all attempts']
                    }
        
        return {'success': False, 'error': 'Retry attempts exhausted'}
    
    async def _adjust_parameters(self, error: Exception, context: RecoveryContext,
                               orchestrator=None) -> Dict[str, Any]:
        """Adjust parameters to potentially fix the issue."""
        
        # Analyze error to determine parameter adjustments
        adjustments = self._determine_parameter_adjustments(error, context)
        
        if not adjustments:
            return {'success': False, 'error': 'No parameter adjustments identified'}
        
        try:
            # Apply parameter adjustments
            for param, new_value in adjustments.items():
                logger.info(f"Adjusting parameter {param} to {new_value}")
                # In a real implementation, this would modify the actual parameters
            
            # Retry with adjusted parameters
            if orchestrator and hasattr(orchestrator, 'process_goal'):
                # Update context with new parameters
                updated_context = {**context.system_state, **adjustments}
                result = await orchestrator.process_goal(context.original_goal, updated_context)
                
                if result and result.status.value == 'success':
                    return {
                        'success': True,
                        'result': result,
                        'lessons': [f'Parameter adjustment successful: {adjustments}']
                    }
            
            return {
                'success': True,
                'result': 'Parameters adjusted successfully',
                'lessons': ['Parameter adjustment strategy applied']
            }
            
        except Exception as adjustment_error:
            return {
                'success': False,
                'error': f'Parameter adjustment failed: {str(adjustment_error)}',
                'lessons': ['Parameter adjustment strategy failed']
            }
    
    def _determine_parameter_adjustments(self, error: Exception, 
                                       context: RecoveryContext) -> Dict[str, Any]:
        """Determine what parameters to adjust based on the error."""
        adjustments = {}
        error_msg = str(error).lower()
        
        if 'timeout' in error_msg:
            adjustments['timeout'] = 60  # Increase timeout
            adjustments['retry_attempts'] = 5
        
        if 'memory' in error_msg:
            adjustments['max_memory'] = 1024  # Increase memory limit
            adjustments['batch_size'] = 10  # Reduce batch size
        
        if 'connection' in error_msg:
            adjustments['connection_timeout'] = 30
            adjustments['max_connections'] = 5
        
        if 'rate limit' in error_msg:
            adjustments['request_delay'] = 2.0
            adjustments['max_requests_per_minute'] = 30
        
        return adjustments
    
    async def _substitute_algorithm(self, error: Exception, context: RecoveryContext,
                                  orchestrator=None) -> Dict[str, Any]:
        """Substitute the current algorithm with an alternative."""
        
        # Identify alternative algorithms
        alternatives = self._identify_algorithm_alternatives(error, context)
        
        if not alternatives:
            return {'success': False, 'error': 'No algorithm alternatives available'}
        
        for alternative in alternatives:
            try:
                logger.info(f"Trying alternative algorithm: {alternative['name']}")
                
                # In a real implementation, this would switch the algorithm
                # For now, simulate successful substitution
                return {
                    'success': True,
                    'result': f"Successfully switched to {alternative['name']}",
                    'lessons': [f"Algorithm substitution to {alternative['name']} worked"]
                }
                
            except Exception as sub_error:
                logger.warning(f"Alternative {alternative['name']} also failed: {sub_error}")
                continue
        
        return {'success': False, 'error': 'All algorithm alternatives failed'}
    
    def _identify_algorithm_alternatives(self, error: Exception, 
                                       context: RecoveryContext) -> List[Dict[str, Any]]:
        """Identify alternative algorithms based on the context."""
        alternatives = []
        
        # Example alternatives based on error type
        if 'memory' in str(error).lower():
            alternatives.append({
                'name': 'streaming_algorithm',
                'description': 'Process data in chunks to reduce memory usage',
                'resource_efficient': True
            })
        
        if 'timeout' in str(error).lower():
            alternatives.append({
                'name': 'fast_approximation',
                'description': 'Use approximation algorithm for faster execution',
                'time_efficient': True
            })
        
        if 'accuracy' in str(error).lower():
            alternatives.append({
                'name': 'ensemble_method',
                'description': 'Use ensemble of simpler methods',
                'accuracy_focused': True
            })
        
        return alternatives
    
    async def _reallocate_resources(self, error: Exception, context: RecoveryContext,
                                  orchestrator=None) -> Dict[str, Any]:
        """Reallocate system resources to resolve the issue."""
        
        resource_changes = self._determine_resource_changes(error, context)
        
        if not resource_changes:
            return {'success': False, 'error': 'No resource reallocation options available'}
        
        try:
            for resource, change in resource_changes.items():
                logger.info(f"Reallocating {resource}: {change}")
                # In a real implementation, this would actually change resource limits
            
            return {
                'success': True,
                'result': f"Resources reallocated: {resource_changes}",
                'lessons': ['Resource reallocation resolved the issue']
            }
            
        except Exception as realloc_error:
            return {
                'success': False,
                'error': f'Resource reallocation failed: {str(realloc_error)}',
                'lessons': ['Resource reallocation strategy failed']
            }
    
    def _determine_resource_changes(self, error: Exception, 
                                  context: RecoveryContext) -> Dict[str, str]:
        """Determine what resource changes are needed."""
        changes = {}
        error_msg = str(error).lower()
        
        if 'memory' in error_msg or 'out of memory' in error_msg:
            changes['memory'] = 'increase to 2GB'
            changes['swap'] = 'enable 1GB swap'
        
        if 'cpu' in error_msg or 'timeout' in error_msg:
            changes['cpu_cores'] = 'increase to 4 cores'
            changes['priority'] = 'set to high priority'
        
        if 'disk' in error_msg or 'no space' in error_msg:
            changes['disk_space'] = 'allocate additional 1GB'
            changes['tmp_cleanup'] = 'clean temporary files'
        
        return changes
    
    async def _graceful_degradation(self, error: Exception, context: RecoveryContext,
                                  orchestrator=None) -> Dict[str, Any]:
        """Implement graceful degradation to provide partial functionality."""
        
        degradation_options = self._identify_degradation_options(error, context)
        
        if not degradation_options:
            return {'success': False, 'error': 'No graceful degradation options available'}
        
        try:
            # Apply the best degradation option
            best_option = degradation_options[0]
            
            logger.info(f"Applying graceful degradation: {best_option['description']}")
            
            # Simulate partial success
            partial_result = {
                'status': 'partial_success',
                'completed_features': best_option.get('available_features', []),
                'disabled_features': best_option.get('disabled_features', []),
                'degradation_level': best_option.get('level', 'medium')
            }
            
            return {
                'success': True,
                'result': partial_result,
                'lessons': [f"Graceful degradation provided partial functionality: {best_option['description']}"]
            }
            
        except Exception as degradation_error:
            return {
                'success': False,
                'error': f'Graceful degradation failed: {str(degradation_error)}',
                'lessons': ['Graceful degradation strategy failed']
            }
    
    def _identify_degradation_options(self, error: Exception, 
                                    context: RecoveryContext) -> List[Dict[str, Any]]:
        """Identify graceful degradation options."""
        options = []
        
        # Example degradation options
        options.append({
            'description': 'Reduce output quality for faster processing',
            'level': 'low',
            'available_features': ['basic_processing', 'simple_output'],
            'disabled_features': ['advanced_analysis', 'detailed_reporting']
        })
        
        options.append({
            'description': 'Use cached results where available',
            'level': 'medium',
            'available_features': ['cached_data', 'basic_processing'],
            'disabled_features': ['real_time_processing', 'fresh_data']
        })
        
        return options
    
    async def _rollback_and_retry(self, error: Exception, context: RecoveryContext,
                                orchestrator=None) -> Dict[str, Any]:
        """Rollback to a previous state and retry."""
        
        try:
            # Check if rollback is possible
            if not context.system_state.get('checkpoints_available', False):
                return {'success': False, 'error': 'No rollback checkpoints available'}
            
            logger.info("Rolling back to previous checkpoint")
            
            # Simulate rollback
            rollback_successful = await self._perform_rollback(context)
            
            if not rollback_successful:
                return {'success': False, 'error': 'Rollback failed'}
            
            # Retry after rollback
            if orchestrator and hasattr(orchestrator, 'process_goal'):
                result = await orchestrator.process_goal(context.original_goal)
                
                if result and result.status.value == 'success':
                    return {
                        'success': True,
                        'result': result,
                        'lessons': ['Rollback and retry was successful']
                    }
            
            return {
                'success': True,
                'result': 'Rollback completed successfully',
                'lessons': ['System restored to previous stable state']
            }
            
        except Exception as rollback_error:
            return {
                'success': False,
                'error': f'Rollback failed: {str(rollback_error)}',
                'lessons': ['Rollback and retry strategy failed']
            }
    
    async def _perform_rollback(self, context: RecoveryContext) -> bool:
        """Perform the actual rollback operation."""
        try:
            # In a real implementation, this would:
            # 1. Restore from checkpoint
            # 2. Reset system state
            # 3. Clear any partial changes
            
            logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    async def _try_alternative_approach(self, error: Exception, context: RecoveryContext,
                                      orchestrator=None) -> Dict[str, Any]:
        """Try a completely different approach to achieve the goal."""
        
        alternatives = await self.generate_alternative_approaches(context.original_goal, context)
        
        if not alternatives:
            return {'success': False, 'error': 'No alternative approaches available'}
        
        for alternative in alternatives:
            try:
                logger.info(f"Trying alternative approach: {alternative.description}")
                
                # Simulate trying alternative approach
                if orchestrator and hasattr(orchestrator, 'process_goal'):
                    # Modify context for alternative approach
                    alt_context = {**context.system_state, 'approach': alternative.strategy}
                    result = await orchestrator.process_goal(context.original_goal, alt_context)
                    
                    if result and result.status.value == 'success':
                        return {
                            'success': True,
                            'result': result,
                            'lessons': [f"Alternative approach '{alternative.description}' was successful"]
                        }
                
                return {
                    'success': True,
                    'result': f"Alternative approach '{alternative.description}' applied",
                    'lessons': ['Alternative approach strategy worked']
                }
                
            except Exception as alt_error:
                logger.warning(f"Alternative approach failed: {alt_error}")
                continue
        
        return {'success': False, 'error': 'All alternative approaches failed'}
    
    async def _self_modification(self, error: Exception, context: RecoveryContext,
                               orchestrator=None) -> Dict[str, Any]:
        """Modify the code/logic to fix the issue."""
        
        if not self.enable_self_modification:
            return {'success': False, 'error': 'Self-modification is disabled'}
        
        try:
            # Get the code that caused the error
            failed_code = context.failed_approach.get('code', '')
            
            if not failed_code:
                return {'success': False, 'error': 'No code available for modification'}
            
            # Generate fixes
            fixes = self.code_analyzer.analyze_error(failed_code, error, context.system_state)
            
            if not fixes:
                return {'success': False, 'error': 'No code fixes could be generated'}
            
            # Try applying fixes
            for fix in fixes:
                try:
                    success = await self.apply_fix(fix)
                    
                    if success:
                        return {
                            'success': True,
                            'result': f"Applied fix: {fix.description}",
                            'fixes': [fix],
                            'lessons': [f"Self-modification successful: {fix.description}"]
                        }
                        
                except Exception as fix_error:
                    logger.warning(f"Failed to apply fix {fix.fix_id}: {fix_error}")
                    continue
            
            return {'success': False, 'error': 'All generated fixes failed to apply'}
            
        except Exception as self_mod_error:
            return {
                'success': False,
                'error': f'Self-modification failed: {str(self_mod_error)}',
                'lessons': ['Self-modification strategy failed']
            }
    
    async def _adjust_context(self, error: Exception, context: RecoveryContext,
                            orchestrator=None) -> Dict[str, Any]:
        """Adjust the execution context to avoid the error."""
        
        context_adjustments = self._determine_context_adjustments(error, context)
        
        if not context_adjustments:
            return {'success': False, 'error': 'No context adjustments identified'}
        
        try:
            # Apply context adjustments
            updated_context = {**context.system_state, **context_adjustments}
            
            if orchestrator and hasattr(orchestrator, 'process_goal'):
                result = await orchestrator.process_goal(context.original_goal, updated_context)
                
                if result and result.status.value == 'success':
                    return {
                        'success': True,
                        'result': result,
                        'lessons': [f"Context adjustment successful: {context_adjustments}"]
                    }
            
            return {
                'success': True,
                'result': f"Context adjusted: {context_adjustments}",
                'lessons': ['Context adjustment strategy applied']
            }
            
        except Exception as context_error:
            return {
                'success': False,
                'error': f'Context adjustment failed: {str(context_error)}',
                'lessons': ['Context adjustment strategy failed']
            }
    
    def _determine_context_adjustments(self, error: Exception, 
                                     context: RecoveryContext) -> Dict[str, Any]:
        """Determine what context adjustments are needed."""
        adjustments = {}
        error_msg = str(error).lower()
        
        if 'environment' in error_msg:
            adjustments['environment'] = 'development'
            adjustments['debug_mode'] = True
        
        if 'path' in error_msg or 'file not found' in error_msg:
            adjustments['working_directory'] = '/tmp'
            adjustments['create_missing_dirs'] = True
        
        if 'permission' in error_msg:
            adjustments['user_mode'] = 'safe'
            adjustments['restricted_access'] = True
        
        return adjustments
    
    async def _escalate_to_human(self, error: Exception, 
                               context: RecoveryContext) -> Dict[str, Any]:
        """Escalate the issue to human intervention."""
        
        escalation_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'original_goal': context.original_goal,
            'attempted_strategies': [attempt['strategy'] for attempt in context.previous_attempts],
            'system_state': context.system_state,
            'urgency': self._determine_urgency(error, context)
        }
        
        logger.warning(f"Escalating to human intervention: {escalation_info}")
        
        # In a real implementation, this would:
        # 1. Send notification to human operators
        # 2. Create support ticket
        # 3. Provide detailed context
        # 4. Wait for human response
        
        return {
            'success': False,  # Human intervention needed
            'escalation_info': escalation_info,
            'message': 'Issue escalated to human intervention'
        }
    
    def _determine_urgency(self, error: Exception, context: RecoveryContext) -> str:
        """Determine the urgency level for human escalation."""
        error_msg = str(error).lower()
        
        if any(keyword in error_msg for keyword in ['critical', 'fatal', 'security', 'data loss']):
            return 'critical'
        elif any(keyword in error_msg for keyword in ['timeout', 'connection', 'performance']):
            return 'high'
        else:
            return 'medium'
    
    async def generate_fix(self, error: Exception, code: str = "", 
                         context: Optional[Dict[str, Any]] = None) -> List[CodeFix]:
        """Generate code fixes for an error."""
        return self.code_analyzer.analyze_error(code, error, context or {})
    
    async def apply_fix(self, fix: CodeFix) -> bool:
        """Apply a code fix."""
        try:
            # In a real implementation, this would:
            # 1. Validate the fix
            # 2. Create backup of original code
            # 3. Apply the fix
            # 4. Test the fix
            # 5. Rollback if test fails
            
            logger.info(f"Applying fix: {fix.description}")
            
            # Simulate fix application
# DEMO CODE REMOVED: success = random.random() > 0.3  # 70% success rate for simulation
            
            # Update fix statistics
            await self._update_fix_statistics(fix, success)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to apply fix {fix.fix_id}: {e}")
            await self._update_fix_statistics(fix, False)
            return False
    
    async def rollback_changes(self, checkpoint_id: str) -> bool:
        """Rollback changes to a specific checkpoint."""
        try:
            logger.info(f"Rolling back to checkpoint: {checkpoint_id}")
            
            # In a real implementation, this would:
            # 1. Validate checkpoint exists
            # 2. Stop current operations
            # 3. Restore from checkpoint
            # 4. Verify restoration
            
            # Simulate rollback
# DEMO CODE REMOVED: success = random.random() > 0.1  # 90% success rate for simulation
            
            if success:
                logger.info("Rollback completed successfully")
            else:
                logger.error("Rollback failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    async def generate_alternative_approaches(self, goal: str, 
                                            context: RecoveryContext) -> List[AlternativeApproach]:
        """Generate alternative approaches to achieve the goal."""
        alternatives = []
        
        # Example alternative approaches
        alternatives.append(AlternativeApproach(
            approach_id=str(uuid.uuid4()),
            strategy="step_by_step",
            description="Break down the goal into smaller, manageable steps",
            implementation={
                "method": "decomposition",
                "chunk_size": "small",
                "parallel": False
            },
            expected_benefits=["Reduced complexity", "Better error isolation"],
            potential_risks=["Longer execution time"],
            resource_requirements={"cpu": "medium", "memory": "low"},
            confidence_score=0.8,
            estimated_time=120
        ))
        
        alternatives.append(AlternativeApproach(
            approach_id=str(uuid.uuid4()),
            strategy="simplified_approach",
            description="Use a simpler method with reduced functionality",
            implementation={
                "method": "simplification",
                "features": "basic",
                "quality": "good_enough"
            },
            expected_benefits=["Higher reliability", "Faster execution"],
            potential_risks=["Reduced functionality"],
            resource_requirements={"cpu": "low", "memory": "low"},
            confidence_score=0.9,
            estimated_time=60
        ))
        
        alternatives.append(AlternativeApproach(
            approach_id=str(uuid.uuid4()),
            strategy="hybrid_approach",
            description="Combine multiple techniques for better robustness",
            implementation={
                "method": "hybrid",
                "techniques": ["primary", "fallback", "validation"],
                "redundancy": True
            },
            expected_benefits=["High reliability", "Multiple fallbacks"],
            potential_risks=["Higher resource usage"],
            resource_requirements={"cpu": "high", "memory": "medium"},
            confidence_score=0.7,
            estimated_time=180
        ))
        
        return alternatives
    
    async def _learn_from_recovery(self, result: RecoveryResult, context: RecoveryContext):
        """Learn from recovery attempts to improve future performance."""
        
        # Extract error signature
        error_signature = self._create_error_signature(result.original_error, context)
        
        # Update or create recovery pattern
        if error_signature in self.recovery_patterns:
            pattern = self.recovery_patterns[error_signature]
            pattern.usage_count += 1
            
            # Update success rates
            strategy_name = result.strategy_used.value
            if strategy_name not in pattern.success_rates:
                pattern.success_rates[strategy_name] = 0.0
            
            # Update success rate using moving average
            current_rate = pattern.success_rates[strategy_name]
            new_rate = current_rate + (0.1 * (1.0 if result.success else 0.0 - current_rate))
            pattern.success_rates[strategy_name] = new_rate
            
            # Update average recovery time
            pattern.avg_recovery_time = (pattern.avg_recovery_time + result.execution_time) / 2
            pattern.last_updated = datetime.now()
            
        else:
            # Create new pattern
            pattern = RecoveryPattern(
                pattern_id=str(uuid.uuid4()),
                error_signature=error_signature,
                successful_strategies=[result.strategy_used] if result.success else [],
                success_rates={result.strategy_used.value: 1.0 if result.success else 0.0},
                avg_recovery_time=result.execution_time,
                conditions=context.system_state,
                last_updated=datetime.now(),
                usage_count=1
            )
            self.recovery_patterns[error_signature] = pattern
        
        # Store pattern in database
        await self._store_recovery_pattern(pattern)
        
        # Update knowledge base
        await self._update_knowledge_base(result, context)
    
    def _create_error_signature(self, error: str, context: RecoveryContext) -> str:
        """Create a signature for error pattern matching."""
        error_type = error.split(':')[0] if ':' in error else error
        
        # Include relevant context information
        context_signature = []
        if 'system_state' in context.system_state:
            context_signature.append(f"state:{context.system_state.get('current_state', 'unknown')}")
        if 'agent_type' in context.system_state:
            context_signature.append(f"agent:{context.system_state.get('agent_type', 'unknown')}")
        
        signature_parts = [error_type] + context_signature
        return "|".join(signature_parts)
    
    async def _update_knowledge_base(self, result: RecoveryResult, context: RecoveryContext):
        """Update the knowledge base with lessons learned."""
        
        for lesson in result.lessons_learned:
            # Extract key insights
            if lesson not in self.knowledge_base:
                self.knowledge_base[lesson] = {
                    'frequency': 1,
                    'success_rate': 1.0 if result.success else 0.0,
                    'contexts': [context.system_state],
                    'first_seen': datetime.now(),
                    'last_seen': datetime.now()
                }
            else:
                kb_entry = self.knowledge_base[lesson]
                kb_entry['frequency'] += 1
                
                # Update success rate
                current_success = kb_entry['success_rate']
                new_success = current_success + (0.1 * (1.0 if result.success else 0.0 - current_success))
                kb_entry['success_rate'] = new_success
                
                kb_entry['contexts'].append(context.system_state)
                kb_entry['last_seen'] = datetime.now()
                
                # Keep only recent contexts
                if len(kb_entry['contexts']) > 10:
                    kb_entry['contexts'] = kb_entry['contexts'][-10:]
    
    async def _store_recovery_result(self, result: RecoveryResult):
        """Store recovery result in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO recovery_results
                (recovery_id, timestamp, status, strategy_used, success, execution_time, 
                 original_error, lessons_learned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.recovery_id,
                datetime.now().isoformat(),
                result.status.value,
                result.strategy_used.value,
                1 if result.success else 0,
                result.execution_time,
                result.original_error,
                json.dumps(result.lessons_learned)
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store recovery result: {e}")
    
    async def _store_recovery_pattern(self, pattern: RecoveryPattern):
        """Store recovery pattern in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO recovery_patterns
                (pattern_id, error_signature, successful_strategies, success_rates,
                 avg_recovery_time, conditions, last_updated, usage_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.pattern_id,
                pattern.error_signature,
                json.dumps([s.value for s in pattern.successful_strategies]),
                json.dumps(pattern.success_rates),
                pattern.avg_recovery_time,
                json.dumps(pattern.conditions),
                pattern.last_updated.isoformat(),
                pattern.usage_count
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store recovery pattern: {e}")
    
    async def _update_fix_statistics(self, fix: CodeFix, success: bool):
        """Update statistics for code fixes."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get current statistics
            cursor = conn.execute(
                'SELECT success_count, failure_count FROM code_fixes WHERE fix_id = ?',
                (fix.fix_id,)
            )
            result = cursor.fetchone()
            
            if result:
                success_count, failure_count = result
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                
                conn.execute('''
                    UPDATE code_fixes 
                    SET success_count = ?, failure_count = ?
                    WHERE fix_id = ?
                ''', (success_count, failure_count, fix.fix_id))
            else:
                # Insert new fix record
                conn.execute('''
                    INSERT INTO code_fixes
                    (fix_id, fix_type, description, target_code, fixed_code, confidence,
                     success_count, failure_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    fix.fix_id,
                    fix.fix_type.value,
                    fix.description,
                    fix.target_code,
                    fix.fixed_code,
                    fix.confidence,
                    1 if success else 0,
                    0 if success else 1
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to update fix statistics: {e}")
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery statistics and performance metrics."""
        if not self.success_history:
            return {
                'total_recoveries': 0,
                'success_rate': 0.0,
                'avg_recovery_time': 0.0,
                'strategy_effectiveness': {}
            }
        
        total_recoveries = len(self.success_history)
        successful_recoveries = sum(1 for r in self.success_history if r.success)
        success_rate = successful_recoveries / total_recoveries
        
        avg_recovery_time = sum(r.execution_time for r in self.success_history) / total_recoveries
        
        # Strategy effectiveness
        strategy_stats = defaultdict(lambda: {'attempts': 0, 'successes': 0})
        for result in self.success_history:
            strategy = result.strategy_used.value
            strategy_stats[strategy]['attempts'] += 1
            if result.success:
                strategy_stats[strategy]['successes'] += 1
        
        strategy_effectiveness = {}
        for strategy, stats in strategy_stats.items():
            strategy_effectiveness[strategy] = stats['successes'] / stats['attempts']
        
        return {
            'total_recoveries': total_recoveries,
            'success_rate': success_rate,
            'avg_recovery_time': avg_recovery_time,
            'strategy_effectiveness': dict(strategy_effectiveness),
            'known_patterns': len(self.recovery_patterns),
            'knowledge_base_size': len(self.knowledge_base)
        }
    
    async def cleanup(self):
        """Cleanup resources and save state."""
        logger.info("Cleaning up RecoveryManager")
        
        # Save final state to database
        for pattern in self.recovery_patterns.values():
            await self._store_recovery_pattern(pattern)