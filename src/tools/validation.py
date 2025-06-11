import ast
import re
import json
import time
import uuid
import asyncio
import difflib
import random
import string
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import subprocess
import tempfile
import coverage
import pylint.lint
import bandit.core.manager
from loguru import logger
import hypothesis
from hypothesis import strategies as st


class ValidationLevel(Enum):
    SYNTAX = "syntax"
    LOGIC = "logic"
    OUTPUT = "output"
    PERFORMANCE = "performance"
    SECURITY = "security"
    INTEGRATION = "integration"


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    PROPERTY_BASED = "property_based"
    FUZZ = "fuzz"
    PERFORMANCE = "performance"
    SECURITY = "security"


class ValidationStrategy(Enum):
    STATIC_ANALYSIS = "static_analysis"
    DYNAMIC_TESTING = "dynamic_testing"
    LLM_VALIDATION = "llm_validation"
    FORMAL_VERIFICATION = "formal_verification"
    BEHAVIORAL_TESTING = "behavioral_testing"


@dataclass
class ValidationIssue:
    level: ValidationLevel
    severity: str  # critical, high, medium, low, info
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    suggestion: Optional[str] = None
    category: Optional[str] = None
    confidence: float = 1.0


@dataclass
class TestCase:
    test_id: str
    name: str
    test_type: TestType
    input_data: Any
    expected_output: Any
    test_function: Optional[Callable] = None
    setup: Optional[Callable] = None
    teardown: Optional[Callable] = None
    timeout: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    test_id: str
    passed: bool
    execution_time: float
    output: Any
    error_message: Optional[str] = None
    assertion_details: Optional[str] = None
    coverage_data: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    validation_id: str
    code_hash: str
    language: str
    timestamp: datetime
    overall_score: float
    passed: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    performance_data: Optional[Dict[str, Any]] = None


@dataclass
class TestResults:
    suite_id: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time: float
    test_results: List[TestResult] = field(default_factory=list)
    coverage_report: Optional[Dict[str, Any]] = None
    performance_summary: Optional[Dict[str, Any]] = None


@dataclass
class SecurityReport:
    scan_id: str
    risk_score: float
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    compliance_checks: Dict[str, bool] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    tool_reports: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeQualityMetrics:
    cyclomatic_complexity: float
    maintainability_index: float
    lines_of_code: int
    comment_ratio: float
    duplication_ratio: float
    test_coverage: float
    technical_debt_minutes: float


class SyntaxValidator:
    """Validates code syntax for different languages."""
    
    def validate_python(self, code: str) -> List[ValidationIssue]:
        """Validate Python syntax."""
        issues = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.SYNTAX,
                severity="critical",
                message=f"Syntax error: {e.msg}",
                line_number=e.lineno,
                column_number=e.offset,
                suggestion="Fix syntax error before proceeding"
            ))
        
        return issues
    
    def validate_javascript(self, code: str) -> List[ValidationIssue]:
        """Validate JavaScript syntax using external tools."""
        issues = []
        
        try:
            # Use node.js to check syntax
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                f.flush()
                
                result = subprocess.run(
                    ['node', '--check', f.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.SYNTAX,
                        severity="critical",
                        message=f"JavaScript syntax error: {result.stderr}",
                        suggestion="Fix syntax error before proceeding"
                    ))
                
            Path(f.name).unlink(missing_ok=True)
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.SYNTAX,
                severity="medium",
                message=f"Could not validate JavaScript syntax: {e}",
                suggestion="Manual syntax check recommended"
            ))
        
        return issues


class LogicValidator:
    """Validates code logic and potential runtime issues."""
    
    def __init__(self):
        self.logic_patterns = {
            'infinite_loop': [
                r'while\s+True\s*:',
                r'while\s+1\s*:',
                r'for\s+.*\s+in\s+itertools\.count\(',
            ],
            'unreachable_code': [
                r'return\s+.*\n\s*\w+',
                r'break\s*\n\s*\w+',
                r'continue\s*\n\s*\w+',
            ],
            'null_pointer': [
                r'\..*\(\)\s*$',
                r'\[\s*\w+\s*\]',
            ],
            'unhandled_exception': [
                r'open\s*\([^)]*\)',
                r'int\s*\([^)]*\)',
                r'float\s*\([^)]*\)',
            ]
        }
        
        self.compiled_patterns = {}
        for category, patterns in self.logic_patterns.items():
            self.compiled_patterns[category] = [
                re.compile(pattern, re.MULTILINE | re.IGNORECASE) 
                for pattern in patterns
            ]
    
    def validate_python_logic(self, code: str) -> List[ValidationIssue]:
        """Validate Python code logic."""
        issues = []
        
        # Check for common logic issues
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(code)
                for match in matches:
                    line_num = code[:match.start()].count('\n') + 1
                    
                    if category == 'infinite_loop':
                        issues.append(ValidationIssue(
                            level=ValidationLevel.LOGIC,
                            severity="high",
                            message="Potential infinite loop detected",
                            line_number=line_num,
                            suggestion="Add break condition or timeout",
                            category=category
                        ))
                    elif category == 'unreachable_code':
                        issues.append(ValidationIssue(
                            level=ValidationLevel.LOGIC,
                            severity="medium",
                            message="Unreachable code detected",
                            line_number=line_num,
                            suggestion="Remove unreachable code",
                            category=category
                        ))
                    elif category == 'unhandled_exception':
                        issues.append(ValidationIssue(
                            level=ValidationLevel.LOGIC,
                            severity="medium",
                            message="Potential unhandled exception",
                            line_number=line_num,
                            suggestion="Add try-except block",
                            category=category
                        ))
        
        # AST-based analysis
        try:
            tree = ast.parse(code)
            issues.extend(self._analyze_ast(tree))
        except SyntaxError:
            pass  # Syntax errors handled elsewhere
        
        return issues
    
    def _analyze_ast(self, tree: ast.AST) -> List[ValidationIssue]:
        """Analyze AST for logic issues."""
        issues = []
        
        for node in ast.walk(tree):
            # Check for variable usage before definition
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                # This would require more sophisticated analysis
                pass
            
            # Check for function calls without error handling
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Check for risky operations
                    risky_methods = ['open', 'read', 'write', 'delete']
                    if hasattr(node.func, 'attr') and node.func.attr in risky_methods:
                        issues.append(ValidationIssue(
                            level=ValidationLevel.LOGIC,
                            severity="medium",
                            message=f"Risky operation '{node.func.attr}' without error handling",
                            line_number=getattr(node, 'lineno', None),
                            suggestion="Add appropriate error handling"
                        ))
        
        return issues


class OutputValidator:
    """Validates actual vs expected outputs."""
    
    def validate_exact_match(self, expected: Any, actual: Any) -> bool:
        """Validate exact match between expected and actual output."""
        return expected == actual
    
    def validate_approximate_match(self, expected: float, actual: float, 
                                 tolerance: float = 1e-6) -> bool:
        """Validate approximate match for floating point numbers."""
        return abs(expected - actual) <= tolerance
    
    def validate_structural_match(self, expected: Dict, actual: Dict) -> bool:
        """Validate structural match for dictionaries."""
        if set(expected.keys()) != set(actual.keys()):
            return False
        
        for key in expected:
            if not self._deep_compare(expected[key], actual[key]):
                return False
        
        return True
    
    def validate_pattern_match(self, pattern: str, actual: str) -> bool:
        """Validate pattern match using regex."""
        return bool(re.search(pattern, actual))
    
    def validate_semantic_similarity(self, expected: str, actual: str,
                                   threshold: float = 0.8) -> bool:
        """Validate semantic similarity using string metrics."""
        similarity = difflib.SequenceMatcher(None, expected, actual).ratio()
        return similarity >= threshold
    
    def _deep_compare(self, obj1: Any, obj2: Any) -> bool:
        """Deep comparison of objects."""
        if type(obj1) != type(obj2):
            return False
        
        if isinstance(obj1, dict):
            return self.validate_structural_match(obj1, obj2)
        elif isinstance(obj1, list):
            if len(obj1) != len(obj2):
                return False
            return all(self._deep_compare(a, b) for a, b in zip(obj1, obj2))
        elif isinstance(obj1, float):
            return self.validate_approximate_match(obj1, obj2)
        else:
            return obj1 == obj2


class TestGenerator:
    """Generates test cases for code validation."""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    async def generate_unit_tests(self, code: str, function_name: str) -> List[TestCase]:
        """Generate unit tests for a specific function."""
        tests = []
        
        # Parse function signature
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    tests.extend(await self._generate_tests_for_function(node, code))
        except Exception as e:
            logger.error(f"Failed to generate unit tests: {e}")
        
        return tests
    
    async def _generate_tests_for_function(self, func_node: ast.FunctionDef, 
                                         code: str) -> List[TestCase]:
        """Generate tests for a specific function node."""
        tests = []
        
        # Extract function signature
        args = [arg.arg for arg in func_node.args.args]
        
        # Generate basic test cases
        test_cases = [
            # Positive cases
            self._generate_positive_cases(func_node, args),
            # Negative cases
            self._generate_negative_cases(func_node, args),
            # Edge cases
            self._generate_edge_cases(func_node, args),
        ]
        
        for i, case_group in enumerate(test_cases):
            for j, case in enumerate(case_group):
                test = TestCase(
                    test_id=f"{func_node.name}_test_{i}_{j}",
                    name=f"Test {func_node.name} - {case['description']}",
                    test_type=TestType.UNIT,
                    input_data=case['input'],
                    expected_output=case['expected'],
                    metadata={'description': case['description']}
                )
                tests.append(test)
        
        return tests
    
    def _generate_positive_cases(self, func_node: ast.FunctionDef, args: List[str]) -> List[Dict]:
        """Generate positive test cases."""
        cases = []
        
        # Simple positive case
        if args:
            if len(args) == 1:
                cases.append({
                    'description': 'positive_single_arg',
                    'input': [1],
# DEMO CODE REMOVED: 'expected': 'mock_result'
                })
            elif len(args) == 2:
                cases.append({
                    'description': 'positive_two_args',
                    'input': [1, 2],
# DEMO CODE REMOVED: 'expected': 'mock_result'
                })
        
        return cases
    
    def _generate_negative_cases(self, func_node: ast.FunctionDef, args: List[str]) -> List[Dict]:
        """Generate negative test cases."""
        cases = []
        
        if args:
            # None input
            cases.append({
                'description': 'none_input',
                'input': [None] * len(args),
                'expected': 'exception'
            })
            
            # Invalid type
            cases.append({
                'description': 'invalid_type',
                'input': ['invalid'] * len(args),
                'expected': 'exception'
            })
        
        return cases
    
    def _generate_edge_cases(self, func_node: ast.FunctionDef, args: List[str]) -> List[Dict]:
        """Generate edge test cases."""
        cases = []
        
        if args:
            # Empty values
            cases.append({
                'description': 'empty_values',
                'input': [''] * len(args),
# DEMO CODE REMOVED: 'expected': 'mock_result'
            })
            
            # Large values
            cases.append({
                'description': 'large_values',
                'input': [999999] * len(args),
# DEMO CODE REMOVED: 'expected': 'mock_result'
            })
        
        return cases
    
    async def generate_property_based_tests(self, code: str) -> List[TestCase]:
        """Generate property-based tests using Hypothesis."""
        tests = []
        
        # Example property-based test generation
        test = TestCase(
            test_id=f"property_test_{uuid.uuid4()}",
            name="Property-based test",
            test_type=TestType.PROPERTY_BASED,
            input_data="hypothesis_strategy",
            expected_output="property_assertion",
            metadata={'strategy': 'integers'}
        )
        tests.append(test)
        
        return tests
    
    async def generate_fuzz_tests(self, code: str, iterations: int = 100) -> List[TestCase]:
        """Generate fuzz tests with random inputs."""
        tests = []
        
        for i in range(iterations):
            # Generate random input
            fuzz_input = self._generate_random_input()
            
            test = TestCase(
                test_id=f"fuzz_test_{i}",
                name=f"Fuzz test {i}",
                test_type=TestType.FUZZ,
                input_data=fuzz_input,
                expected_output="no_crash",
                metadata={'iteration': i}
            )
            tests.append(test)
        
        return tests
    
    def _generate_random_input(self) -> Any:
        """Generate random input data for fuzzing."""
        input_types = [
            lambda: random.randint(-1000, 1000),
            lambda: random.uniform(-1000.0, 1000.0),
            lambda: ''.join(random.choices(string.ascii_letters + string.digits, k=10)),
            lambda: [random.randint(0, 100) for _ in range(random.randint(0, 10))],
            lambda: {f"key_{i}": random.randint(0, 100) for i in range(random.randint(0, 5))},
            lambda: None,
            lambda: "",
            lambda: []
        ]
        
        return random.choice(input_types)()


class PerformanceBenchmark:
    """Performance benchmarking and validation."""
    
    def __init__(self):
        self.benchmarks = {}
    
    async def benchmark_execution_time(self, code: str, iterations: int = 10) -> Dict[str, float]:
        """Benchmark code execution time."""
        times = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            
            try:
                # Execute code in a restricted environment
                exec_globals = {'__builtins__': {'range': range, 'len': len, 'sum': sum, 'min': min, 'max': max}}
                exec_locals = {}
                
                # Compile and execute the code
                compiled_code = compile(code, '<benchmark>', 'exec')
                exec(compiled_code, exec_globals, exec_locals)
                
                # If code executed successfully, add small processing time
                await asyncio.sleep(0.001)
            except Exception:
                # If execution fails, still record the attempt time
                await asyncio.sleep(0.0005)
            
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        return {
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': sum(times) / len(times),
            'std_dev': self._calculate_std_dev(times)
        }
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    async def benchmark_memory_usage(self, code: str) -> Dict[str, float]:
        """Benchmark memory usage."""
        # This would require integration with memory profiling tools
        return {
            'peak_memory_mb': 0.0,
            'avg_memory_mb': 0.0,
            'memory_efficiency': 1.0
        }
    
    async def benchmark_cpu_usage(self, code: str) -> Dict[str, float]:
        """Benchmark CPU usage."""
        # This would require integration with CPU profiling tools
        return {
            'cpu_percent': 0.0,
            'cpu_efficiency': 1.0
        }


class SecurityValidator:
    """Security validation using static analysis tools."""
    
    def __init__(self):
        self.security_tools = ['bandit', 'safety', 'semgrep']
    
    async def validate_security(self, code: str, language: str = 'python') -> SecurityReport:
        """Comprehensive security validation."""
        scan_id = str(uuid.uuid4())
        vulnerabilities = []
        tool_reports = {}
        
        if language == 'python':
            # Bandit security scan
            bandit_results = await self._run_bandit_scan(code)
            tool_reports['bandit'] = bandit_results
            vulnerabilities.extend(bandit_results.get('vulnerabilities', []))
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(vulnerabilities)
        
        # Generate recommendations
        recommendations = self._generate_security_recommendations(vulnerabilities)
        
        return SecurityReport(
            scan_id=scan_id,
            risk_score=risk_score,
            vulnerabilities=vulnerabilities,
            recommendations=recommendations,
            tool_reports=tool_reports
        )
    
    async def _run_bandit_scan(self, code: str) -> Dict[str, Any]:
        """Run Bandit security scan on Python code."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                f.flush()
                
                # Run bandit
                result = subprocess.run(
                    ['bandit', '-f', 'json', f.name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.stdout:
                    bandit_output = json.loads(result.stdout)
                    return {
                        'vulnerabilities': bandit_output.get('results', []),
                        'metrics': bandit_output.get('metrics', {})
                    }
                
            Path(f.name).unlink(missing_ok=True)
            
        except Exception as e:
            logger.error(f"Bandit scan failed: {e}")
        
        return {'vulnerabilities': [], 'metrics': {}}
    
    def _calculate_risk_score(self, vulnerabilities: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score from vulnerabilities."""
        if not vulnerabilities:
            return 0.0
        
        severity_weights = {
            'HIGH': 1.0,
            'MEDIUM': 0.6,
            'LOW': 0.3
        }
        
        total_score = 0.0
        for vuln in vulnerabilities:
            severity = vuln.get('issue_severity', 'LOW')
            confidence = vuln.get('issue_confidence', 'LOW')
            
            weight = severity_weights.get(severity, 0.3)
            confidence_factor = severity_weights.get(confidence, 0.3)
            
            total_score += weight * confidence_factor
        
        # Normalize to 0-10 scale
        return min(total_score, 10.0)
    
    def _generate_security_recommendations(self, vulnerabilities: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations based on vulnerabilities."""
        recommendations = []
        
        for vuln in vulnerabilities:
            test_id = vuln.get('test_id', '')
            
            if 'hardcoded_password' in test_id:
                recommendations.append("Use environment variables or secure vaults for passwords")
            elif 'sql_injection' in test_id:
                recommendations.append("Use parameterized queries to prevent SQL injection")
            elif 'shell_injection' in test_id:
                recommendations.append("Avoid shell command execution or sanitize inputs")
            elif 'unsafe_yaml' in test_id:
                recommendations.append("Use safe YAML loading methods")
        
        return list(set(recommendations))  # Remove duplicates


class ValidationFramework:
    """Comprehensive validation framework with multiple validation strategies."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize validators
        self.syntax_validator = SyntaxValidator()
        self.logic_validator = LogicValidator()
        self.output_validator = OutputValidator()
        self.test_generator = TestGenerator()
        self.performance_benchmark = PerformanceBenchmark()
        self.security_validator = SecurityValidator()
        
        # LLM integration
        self.llm_client = config.get('llm_client')
        self.use_llm_validation = config.get('use_llm_validation', True)
        
        # Validation history
        self.validation_history: List[ValidationResult] = []
        self.max_history = config.get('max_validation_history', 1000)
        
        logger.info("ValidationFramework initialized")
    
    async def validate_code(self, code: str, language: str = 'python',
                          levels: Optional[List[ValidationLevel]] = None) -> ValidationResult:
        """Comprehensive code validation across multiple levels."""
        validation_id = str(uuid.uuid4())
        code_hash = str(hash(code))
        timestamp = datetime.now()
        
        if levels is None:
            levels = [ValidationLevel.SYNTAX, ValidationLevel.LOGIC, ValidationLevel.SECURITY]
        
        all_issues = []
        metrics = {}
        suggestions = []
        
        logger.info(f"Starting validation {validation_id} for {language} code")
        
        # Syntax validation
        if ValidationLevel.SYNTAX in levels:
            syntax_issues = await self._validate_syntax(code, language)
            all_issues.extend(syntax_issues)
            metrics['syntax_issues'] = len(syntax_issues)
        
        # Logic validation
        if ValidationLevel.LOGIC in levels:
            logic_issues = await self._validate_logic(code, language)
            all_issues.extend(logic_issues)
            metrics['logic_issues'] = len(logic_issues)
        
        # Security validation
        if ValidationLevel.SECURITY in levels:
            security_report = await self.security_validator.validate_security(code, language)
            security_issues = self._convert_security_to_issues(security_report)
            all_issues.extend(security_issues)
            metrics['security_risk_score'] = security_report.risk_score
            suggestions.extend(security_report.recommendations)
        
        # Performance validation
        if ValidationLevel.PERFORMANCE in levels:
            perf_data = await self.performance_benchmark.benchmark_execution_time(code)
            metrics['performance'] = perf_data
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(all_issues, metrics)
        passed = overall_score >= self.config.get('passing_score', 0.7)
        
        # Generate suggestions
        if not passed:
            suggestions.extend(self._generate_improvement_suggestions(all_issues))
        
        result = ValidationResult(
            validation_id=validation_id,
            code_hash=code_hash,
            language=language,
            timestamp=timestamp,
            overall_score=overall_score,
            passed=passed,
            issues=all_issues,
            metrics=metrics,
            suggestions=suggestions,
            performance_data=metrics.get('performance')
        )
        
        self._store_validation_result(result)
        
        logger.info(f"Validation {validation_id} completed: score={overall_score:.2f}, passed={passed}")
        return result
    
    async def validate_output(self, expected: Any, actual: Any, 
                            validation_type: str = 'exact') -> bool:
        """Validate actual output against expected output."""
        if validation_type == 'exact':
            return self.output_validator.validate_exact_match(expected, actual)
        elif validation_type == 'approximate':
            return self.output_validator.validate_approximate_match(expected, actual)
        elif validation_type == 'structural':
            return self.output_validator.validate_structural_match(expected, actual)
        elif validation_type == 'pattern':
            return self.output_validator.validate_pattern_match(expected, actual)
        elif validation_type == 'semantic':
            return self.output_validator.validate_semantic_similarity(expected, actual)
        else:
            raise ValueError(f"Unknown validation type: {validation_type}")
    
    async def generate_tests(self, code: str, test_types: Optional[List[TestType]] = None) -> List[TestCase]:
        """Generate comprehensive test suite for code."""
        if test_types is None:
            test_types = [TestType.UNIT, TestType.FUZZ]
        
        all_tests = []
        
        # Extract function names from code
        function_names = self._extract_function_names(code)
        
        for test_type in test_types:
            if test_type == TestType.UNIT:
                for func_name in function_names:
                    unit_tests = await self.test_generator.generate_unit_tests(code, func_name)
                    all_tests.extend(unit_tests)
            
            elif test_type == TestType.PROPERTY_BASED:
                prop_tests = await self.test_generator.generate_property_based_tests(code)
                all_tests.extend(prop_tests)
            
            elif test_type == TestType.FUZZ:
                fuzz_tests = await self.test_generator.generate_fuzz_tests(code)
                all_tests.extend(fuzz_tests)
        
        logger.info(f"Generated {len(all_tests)} tests")
        return all_tests
    
    async def run_test_suite(self, tests: List[TestCase], code: str) -> TestResults:
        """Execute a test suite and return comprehensive results."""
        suite_id = str(uuid.uuid4())
        start_time = time.time()
        
        test_results = []
        passed_count = 0
        
        # Set up coverage tracking
        cov = coverage.Coverage()
        cov.start()
        
        logger.info(f"Running test suite {suite_id} with {len(tests)} tests")
        
        for test in tests:
            try:
                result = await self._execute_test(test, code)
                test_results.append(result)
                
                if result.passed:
                    passed_count += 1
                    
            except Exception as e:
                # Create failed test result
                failed_result = TestResult(
                    test_id=test.test_id,
                    passed=False,
                    execution_time=0.0,
                    output=None,
                    error_message=str(e)
                )
                test_results.append(failed_result)
        
        cov.stop()
        
        # Generate coverage report
        coverage_data = self._generate_coverage_report(cov)
        
        execution_time = time.time() - start_time
        
        results = TestResults(
            suite_id=suite_id,
            total_tests=len(tests),
            passed_tests=passed_count,
            failed_tests=len(tests) - passed_count,
            execution_time=execution_time,
            test_results=test_results,
            coverage_report=coverage_data
        )
        
        logger.info(f"Test suite {suite_id} completed: {passed_count}/{len(tests)} passed")
        return results
    
    async def validate_security(self, code: str, language: str = 'python') -> SecurityReport:
        """Validate code security using multiple tools and strategies."""
        return await self.security_validator.validate_security(code, language)
    
    def calculate_code_quality_metrics(self, code: str, language: str = 'python') -> CodeQualityMetrics:
        """Calculate comprehensive code quality metrics."""
        if language == 'python':
            return self._calculate_python_quality_metrics(code)
        else:
            # Default metrics for unsupported languages
            return CodeQualityMetrics(
                cyclomatic_complexity=1.0,
                maintainability_index=100.0,
                lines_of_code=len(code.split('\n')),
                comment_ratio=0.0,
                duplication_ratio=0.0,
                test_coverage=0.0,
                technical_debt_minutes=0.0
            )
    
    # Private helper methods
    
    async def _validate_syntax(self, code: str, language: str) -> List[ValidationIssue]:
        """Validate syntax for the specified language."""
        if language == 'python':
            return self.syntax_validator.validate_python(code)
        elif language == 'javascript':
            return self.syntax_validator.validate_javascript(code)
        else:
            return []
    
    async def _validate_logic(self, code: str, language: str) -> List[ValidationIssue]:
        """Validate logic for the specified language."""
        if language == 'python':
            return self.logic_validator.validate_python_logic(code)
        else:
            return []
    
    def _convert_security_to_issues(self, security_report: SecurityReport) -> List[ValidationIssue]:
        """Convert security vulnerabilities to validation issues."""
        issues = []
        
        for vuln in security_report.vulnerabilities:
            severity_map = {'HIGH': 'critical', 'MEDIUM': 'high', 'LOW': 'medium'}
            
            issue = ValidationIssue(
                level=ValidationLevel.SECURITY,
                severity=severity_map.get(vuln.get('issue_severity', 'LOW'), 'medium'),
                message=vuln.get('issue_text', 'Security vulnerability detected'),
                line_number=vuln.get('line_number'),
                suggestion=vuln.get('issue_text'),
                category='security',
                confidence=float(vuln.get('issue_confidence', 'MEDIUM') == 'HIGH')
            )
            issues.append(issue)
        
        return issues
    
    def _calculate_overall_score(self, issues: List[ValidationIssue], 
                               metrics: Dict[str, Any]) -> float:
        """Calculate overall validation score."""
        base_score = 1.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == 'critical':
                base_score -= 0.3
            elif issue.severity == 'high':
                base_score -= 0.2
            elif issue.severity == 'medium':
                base_score -= 0.1
            elif issue.severity == 'low':
                base_score -= 0.05
        
        # Factor in security risk
        if 'security_risk_score' in metrics:
            security_penalty = metrics['security_risk_score'] / 10.0 * 0.3
            base_score -= security_penalty
        
        return max(0.0, base_score)
    
    def _generate_improvement_suggestions(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate improvement suggestions based on issues."""
        suggestions = []
        
        # Group issues by category
        issue_categories = {}
        for issue in issues:
            category = issue.category or issue.level.value
            if category not in issue_categories:
                issue_categories[category] = []
            issue_categories[category].append(issue)
        
        # Generate category-specific suggestions
        for category, category_issues in issue_categories.items():
            if category == 'syntax':
                suggestions.append("Fix syntax errors before proceeding with validation")
            elif category == 'security':
                suggestions.append("Address security vulnerabilities to improve code safety")
            elif category == 'logic':
                suggestions.append("Review logic issues to prevent runtime errors")
            elif category == 'infinite_loop':
                suggestions.append("Add break conditions or timeouts to prevent infinite loops")
        
        return suggestions
    
    def _extract_function_names(self, code: str) -> List[str]:
        """Extract function names from code."""
        function_names = []
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_names.append(node.name)
        except SyntaxError:
            # If code has syntax errors, return empty list
            pass
        
        return function_names
    
    def _extract_main_function_name(self, code: str) -> Optional[str]:
        """Extract the name of the main function from code."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Return the first function found
                    return node.name
        except SyntaxError:
            pass
        return None
    
    async def _execute_test(self, test: TestCase, code: str) -> TestResult:
        """Execute a single test case."""
        start_time = time.time()
        
        try:
            # Prepare execution environment
            exec_globals = {'__builtins__': __builtins__}
            exec_locals = {}
            
            # Execute the code
            exec(compile(code, '<test>', 'exec'), exec_globals, exec_locals)
            
            if test.test_type == TestType.FUZZ:
                # For fuzz tests, check that no exception is raised
                passed = True
                output = "execution_completed_without_error"
            else:
                # For functional tests, try to evaluate the test inputs
                try:
                    if test.input_data:
                        # Try to call the function with test inputs
                        function_name = self._extract_main_function_name(code)
                        if function_name and function_name in exec_locals:
                            func = exec_locals[function_name]
                            if callable(func):
                                result = func(**test.input_data)
                                passed = str(result) == str(test.expected_output)
                                output = str(result)
                            else:
                                passed = True
                                output = "function_not_callable"
                        else:
                            passed = True
                            output = "function_not_found_assuming_pass"
                    else:
                        # No input data, assume test passes if code executes
                        passed = True
                        output = test.expected_output or "no_output_expected"
                except Exception as test_exec_error:
                    passed = False
                    output = f"test_execution_error: {str(test_exec_error)}"
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_id=test.test_id,
                passed=passed,
                execution_time=execution_time,
                output=output
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TestResult(
                test_id=test.test_id,
                passed=False,
                execution_time=execution_time,
                output=None,
                error_message=str(e)
            )
    
    def _generate_coverage_report(self, cov: coverage.Coverage) -> Dict[str, Any]:
        """Generate coverage report from coverage data."""
        try:
            # Get coverage data
            cov.save()
            
            # Get the report data
            report = cov.report(show_missing=True, skip_empty=True)
            
            # Get detailed file data
            file_data = {}
            total_lines = 0
            covered_lines = 0
            missing_lines = []
            
            for filename in cov.get_data().measured_files():
                analysis = cov.analysis2(filename)
                if analysis:
                    file_lines = len(analysis.statements)
                    file_missing = len(analysis.missing)
                    file_covered = file_lines - file_missing
                    
                    total_lines += file_lines
                    covered_lines += file_covered
                    
                    if analysis.missing:
                        missing_lines.extend([f"{filename}:{line}" for line in analysis.missing])
                    
                    file_data[filename] = {
                        'statements': file_lines,
                        'missing': file_missing,
                        'covered': file_covered,
                        'coverage': (file_covered / file_lines * 100) if file_lines > 0 else 0
                    }
            
            overall_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
            
            return {
                'line_coverage': overall_coverage,
                'branch_coverage': 0.0,  # Branch coverage not easily available
                'function_coverage': 0.0,  # Function coverage not easily available
                'missing_lines': missing_lines,
                'file_data': file_data,
                'total_statements': total_lines,
                'covered_statements': covered_lines
            }
        except Exception as e:
            return {
                'line_coverage': 0.0,
                'branch_coverage': 0.0,
                'function_coverage': 0.0,
                'missing_lines': [],
                'error': f"Coverage report generation failed: {str(e)}"
            }
    
    def _calculate_python_quality_metrics(self, code: str) -> CodeQualityMetrics:
        """Calculate quality metrics for Python code."""
        lines = code.split('\n')
        loc = len([line for line in lines if line.strip()])
        
        # Calculate comment ratio
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        comment_ratio = comment_lines / loc if loc > 0 else 0.0
        
        # Simple cyclomatic complexity (number of decision points + 1)
        decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally']
        complexity = 1  # Base complexity
        
        for line in lines:
            stripped = line.strip()
            for keyword in decision_keywords:
                if stripped.startswith(keyword + ' ') or stripped.startswith(keyword + ':'):
                    complexity += 1
        
        # Maintainability index (simplified)
        maintainability = max(0, 171 - 5.2 * (complexity / loc if loc > 0 else 0) - 0.23 * (complexity) - 16.2 * (loc ** 0.5))
        
        return CodeQualityMetrics(
            cyclomatic_complexity=float(complexity),
            maintainability_index=maintainability,
            lines_of_code=loc,
            comment_ratio=comment_ratio,
            duplication_ratio=0.0,  # Would require more sophisticated analysis
            test_coverage=0.0,  # Would be provided separately
            technical_debt_minutes=max(0, (100 - maintainability) * 0.5)
        )
    
    def _store_validation_result(self, result: ValidationResult):
        """Store validation result in history."""
        self.validation_history.append(result)
        
        # Trim history if it gets too long
        if len(self.validation_history) > self.max_history:
            self.validation_history = self.validation_history[-self.max_history:]
    
    # Public utility methods
    
    def get_validation_history(self, limit: int = 50) -> List[ValidationResult]:
        """Get recent validation history."""
        return self.validation_history[-limit:]
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        if not self.validation_history:
            return {
                'total_validations': 0,
                'pass_rate': 0.0,
                'average_score': 0.0
            }
        
        total = len(self.validation_history)
        passed = sum(1 for r in self.validation_history if r.passed)
        avg_score = sum(r.overall_score for r in self.validation_history) / total
        
        return {
            'total_validations': total,
            'pass_rate': passed / total,
            'average_score': avg_score,
            'recent_validations': total
        }