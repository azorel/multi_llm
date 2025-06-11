import asyncio
import json
import os
import re
import tempfile
import uuid
import time
import traceback
import signal
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, AsyncGenerator, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import psutil
import docker
from loguru import logger
import ast
import resource


class ExecutionLanguage(Enum):
    PYTHON = "python"
    NODEJS = "nodejs"
    BASH = "bash"
    SHELL = "shell"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    KILLED = "killed"


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class ResourceLimits:
    max_memory_mb: int = 256
    max_cpu_percent: float = 50.0
    max_execution_time: int = 30
    max_disk_mb: int = 100
    max_network_bandwidth: Optional[int] = None  # KB/s
    max_processes: int = 10
    max_file_descriptors: int = 100


@dataclass
class ExecutionEnvironment:
    language: ExecutionLanguage
    working_directory: str
    environment_variables: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    virtual_env: Optional[str] = None
    docker_image: Optional[str] = None
    network_isolated: bool = True


@dataclass
class ExecutionResult:
    execution_id: str
    status: ExecutionStatus
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    memory_peak_mb: float
    cpu_usage_percent: float
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    network_activity: Dict[str, Any] = field(default_factory=dict)
    error_analysis: Optional[Dict[str, Any]] = None
    performance_profile: Optional[Dict[str, Any]] = None


@dataclass
class CodeValidationResult:
    is_safe: bool
    risk_level: str
    detected_patterns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class DangerousPatternDetector:
    """Detect dangerous patterns in code before execution."""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.MEDIUM):
        self.security_level = security_level
        
        # Dangerous patterns by category
        self.patterns = {
            'system_calls': [
                r'os\.system\s*\(',
                r'subprocess\.(run|call|Popen|check_output)',
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__\s*\(',
                r'compile\s*\(',
                r'open\s*\([^)]*["\'][rwa]',
            ],
            'network_operations': [
                r'socket\.',
                r'urllib\.',
                r'requests\.',
                r'http\.',
                r'ftp\.',
                r'smtp\.',
                r'ssh\.',
                r'telnet\.',
            ],
            'file_operations': [
                r'shutil\.(rmtree|move|copy)',
                r'os\.(remove|unlink|rmdir|rename)',
                r'pathlib.*\.unlink\(',
                r'open\s*\([^)]*["\'][wa]',
            ],
            'privilege_escalation': [
                r'sudo\s+',
                r'su\s+',
                r'chmod\s+',
                r'chown\s+',
                r'setuid\s*\(',
                r'setgid\s*\(',
            ],
            'environment_manipulation': [
                r'os\.environ',
                r'sys\.path',
                r'importlib\.',
                r'__builtins__',
                r'globals\s*\(',
                r'locals\s*\(',
            ],
            'process_manipulation': [
                r'threading\.',
                r'multiprocessing\.',
                r'concurrent\.futures',
                r'asyncio\.create_subprocess',
                r'signal\.',
            ]
        }
        
        # Compile patterns for efficiency
        self.compiled_patterns = {}
        for category, patterns in self.patterns.items():
            self.compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    def validate_code(self, code: str, language: ExecutionLanguage) -> CodeValidationResult:
        """Validate code for dangerous patterns."""
        detected_patterns = []
        risk_level = "low"
        
        if language == ExecutionLanguage.PYTHON:
            detected_patterns.extend(self._validate_python_code(code))
        elif language in [ExecutionLanguage.BASH, ExecutionLanguage.SHELL]:
            detected_patterns.extend(self._validate_shell_code(code))
        elif language in [ExecutionLanguage.NODEJS, ExecutionLanguage.JAVASCRIPT]:
            detected_patterns.extend(self._validate_javascript_code(code))
        
        # Determine risk level
        if detected_patterns:
            if any('system_calls' in p or 'privilege_escalation' in p for p in detected_patterns):
                risk_level = "critical"
            elif any('network_operations' in p or 'file_operations' in p for p in detected_patterns):
                risk_level = "high"
            else:
                risk_level = "medium"
        
        # Security level filtering
        is_safe = self._assess_safety(detected_patterns, risk_level)
        
        recommendations = self._generate_recommendations(detected_patterns)
        
        return CodeValidationResult(
            is_safe=is_safe,
            risk_level=risk_level,
            detected_patterns=detected_patterns,
            recommendations=recommendations
        )

    def _validate_python_code(self, code: str) -> List[str]:
        """Validate Python code specifically."""
        detected = []
        
        # Try to parse AST for deeper analysis
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', 'compile', '__import__']:
                            detected.append(f"system_calls: {node.func.id}")
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['system', 'popen']:
                            detected.append(f"system_calls: {node.func.attr}")
        except SyntaxError:
            detected.append("syntax_error: Invalid Python syntax")
        
        # Pattern-based detection
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(code):
                    detected.append(f"{category}: {pattern.pattern}")
        
        return detected

    def _validate_shell_code(self, code: str) -> List[str]:
        """Validate shell code."""
        detected = []
        
        dangerous_commands = [
            'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs',
            'sudo', 'su', 'chmod', 'chown',
            'wget', 'curl', 'nc', 'netcat', 'ssh', 'scp',
            'iptables', 'ufw', 'firewall-cmd',
            'crontab', 'at', 'systemctl', 'service'
        ]
        
        for cmd in dangerous_commands:
            if re.search(rf'\b{cmd}\b', code, re.IGNORECASE):
                detected.append(f"dangerous_command: {cmd}")
        
        # Check for command chaining and redirection
        if re.search(r'[;&|]', code):
            detected.append("command_chaining: Potential command injection")
        
        if re.search(r'[<>]', code):
            detected.append("redirection: File redirection detected")
        
        return detected

    def _validate_javascript_code(self, code: str) -> List[str]:
        """Validate JavaScript/Node.js code."""
        detected = []
        
        js_patterns = [
            r'require\s*\(\s*["\']fs["\']',
            r'require\s*\(\s*["\']child_process["\']',
            r'require\s*\(\s*["\']os["\']',
            r'eval\s*\(',
            r'Function\s*\(',
            r'process\.exit',
            r'process\.env',
            r'global\.',
            r'Buffer\.',
        ]
        
        for pattern in js_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                detected.append(f"javascript_risk: {pattern}")
        
        return detected

    def _assess_safety(self, detected_patterns: List[str], risk_level: str) -> bool:
        """Assess if code is safe based on security level."""
        if self.security_level == SecurityLevel.LOW:
            return risk_level != "critical"
        elif self.security_level == SecurityLevel.MEDIUM:
            return risk_level not in ["critical", "high"]
        elif self.security_level == SecurityLevel.HIGH:
            return risk_level == "low"
        else:  # MAXIMUM
            return len(detected_patterns) == 0

    def _generate_recommendations(self, detected_patterns: List[str]) -> List[str]:
        """Generate security recommendations."""
        recommendations = []
        
        if any('system_calls' in p for p in detected_patterns):
            recommendations.append("Remove or replace system calls with safer alternatives")
        
        if any('network_operations' in p for p in detected_patterns):
            recommendations.append("Network operations should be reviewed and potentially sandboxed")
        
        if any('file_operations' in p for p in detected_patterns):
            recommendations.append("File operations should be restricted to designated directories")
        
        if any('privilege_escalation' in p for p in detected_patterns):
            recommendations.append("Remove privilege escalation attempts")
        
        return recommendations


class CodeExecutor:
    """Safe code execution with Docker isolation and comprehensive monitoring."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Docker configuration
        self.use_docker = config.get("use_docker", True)
        self.docker_client = None
        
        # WSL-specific configuration
        self.is_wsl = self._detect_wsl()
        self.docker_host = config.get("docker_host")
        
        if self.use_docker:
            try:
                # WSL Docker setup
                if self.is_wsl and not self.docker_host:
                    # Try to connect to Docker Desktop on Windows from WSL
                    import platform
                    if "microsoft" in platform.uname().release.lower():
                        # WSL2 with Docker Desktop
                        self.docker_client = docker.from_env()
                    else:
                        # Try alternative Docker connection methods
                        self.docker_client = self._setup_wsl_docker()
                else:
                    self.docker_client = docker.from_env()
                
                # Test Docker connection
                self.docker_client.ping()
                logger.info(f"Docker client initialized successfully (WSL: {self.is_wsl})")
            except Exception as e:
                logger.warning(f"Docker not available: {e}")
                if self.is_wsl:
                    logger.info("WSL detected. Consider installing Docker Desktop for Windows or configuring Docker daemon.")
                self.use_docker = False
        
        # Security configuration
        self.security_level = SecurityLevel(config.get("security_level", "medium"))
        self.pattern_detector = DangerousPatternDetector(self.security_level)
        
        # Resource limits
        self.default_limits = ResourceLimits(
            max_memory_mb=config.get("max_memory_mb", 256),
            max_cpu_percent=config.get("max_cpu_percent", 50.0),
            max_execution_time=config.get("max_execution_time", 30),
            max_disk_mb=config.get("max_disk_mb", 100),
            max_processes=config.get("max_processes", 10),
            max_file_descriptors=config.get("max_file_descriptors", 100)
        )
        
        # Execution tracking
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.execution_history: List[ExecutionResult] = []
        self.max_history = config.get("max_execution_history", 1000)
        
        # Working directories
        self.base_workdir = Path(config.get("workdir", tempfile.gettempdir())) / "code_executor"
        self.base_workdir.mkdir(parents=True, exist_ok=True)
        
        # Language configurations
        self.language_configs = {
            ExecutionLanguage.PYTHON: {
                "docker_image": "python:3.11-slim",
                "command": ["python", "-c"],
                "file_extension": ".py"
            },
            ExecutionLanguage.NODEJS: {
                "docker_image": "node:18-slim",
                "command": ["node", "-e"],
                "file_extension": ".js"
            },
            ExecutionLanguage.BASH: {
                "docker_image": "ubuntu:22.04",
                "command": ["bash", "-c"],
                "file_extension": ".sh"
            }
        }
        
        logger.info(f"CodeExecutor initialized with security level: {self.security_level.value}")
    
    def _detect_wsl(self) -> bool:
        """Detect if running in WSL environment."""
        try:
            import platform
            import os
            
            # Check for WSL indicators
            if "microsoft" in platform.uname().release.lower():
                return True
            
            # Check for WSL environment variables
            if os.getenv("WSL_DISTRO_NAME") or os.getenv("WSLENV"):
                return True
            
            # Check for /proc/version content
            try:
                with open("/proc/version", "r") as f:
                    version_info = f.read().lower()
                    if "microsoft" in version_info or "wsl" in version_info:
                        return True
            except (FileNotFoundError, PermissionError):
                pass
            
            return False
        except Exception:
            return False
    
    def _setup_wsl_docker(self):
        """Setup Docker client for WSL environment."""
        import os
        
        # Try different Docker socket locations for WSL
        socket_paths = [
            "unix:///var/run/docker.sock",
            "tcp://localhost:2375",
            "tcp://localhost:2376",
            "npipe:////./pipe/docker_engine"  # Windows named pipe
        ]
        
        for socket_path in socket_paths:
            try:
                if socket_path.startswith("unix://"):
                    if os.path.exists(socket_path[7:]):
                        return docker.DockerClient(base_url=socket_path)
                elif socket_path.startswith("tcp://"):
                    return docker.DockerClient(base_url=socket_path)
                elif socket_path.startswith("npipe://"):
                    return docker.DockerClient(base_url=socket_path)
            except Exception as e:
                logger.debug(f"Failed to connect to Docker at {socket_path}: {e}")
                continue
        
        # If all else fails, try default
        return docker.from_env()
    
    def _convert_wsl_path(self, linux_path: str) -> str:
        """Convert WSL Linux path to Windows path if needed."""
        if not self.is_wsl:
            return linux_path
        
        try:
            # Use wslpath utility to convert if available
            result = subprocess.run(
                ['wslpath', '-w', linux_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                windows_path = result.stdout.strip()
                logger.debug(f"Converted WSL path: {linux_path} -> {windows_path}")
                return windows_path
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback: simple conversion for common patterns
        if linux_path.startswith("/mnt/c/"):
            return linux_path.replace("/mnt/c/", "C:\\").replace("/", "\\")
        elif linux_path.startswith("/mnt/"):
            drive = linux_path[5:6].upper()
            return f"{drive}:" + linux_path[6:].replace("/", "\\")
        
        return linux_path

    async def execute_python(self, code: str, args: Optional[List[str]] = None,
                           env: Optional[Dict[str, str]] = None,
                           limits: Optional[ResourceLimits] = None) -> ExecutionResult:
        """Execute Python code with safety checks."""
        execution_env = ExecutionEnvironment(
            language=ExecutionLanguage.PYTHON,
            working_directory=str(self.base_workdir),
            environment_variables=env or {},
            dependencies=[],
            network_isolated=True
        )
        
        return await self._execute_code(code, execution_env, args, limits)

    async def execute_shell(self, commands: Union[str, List[str]], 
                          shell: str = 'bash',
                          limits: Optional[ResourceLimits] = None) -> ExecutionResult:
        """Execute shell commands with safety checks."""
        if isinstance(commands, list):
            code = '\n'.join(commands)
        else:
            code = commands
        
        execution_env = ExecutionEnvironment(
            language=ExecutionLanguage.BASH,
            working_directory=str(self.base_workdir),
            network_isolated=True
        )
        
        return await self._execute_code(code, execution_env, None, limits)

    async def execute_nodejs(self, code: str, 
                           limits: Optional[ResourceLimits] = None) -> ExecutionResult:
        """Execute Node.js code with safety checks."""
        execution_env = ExecutionEnvironment(
            language=ExecutionLanguage.NODEJS,
            working_directory=str(self.base_workdir),
            network_isolated=True
        )
        
        return await self._execute_code(code, execution_env, None, limits)

    async def execute_in_container(self, image: str, code: str, 
                                 language: ExecutionLanguage,
                                 limits: Optional[ResourceLimits] = None) -> ExecutionResult:
        """Execute code in a specific Docker container."""
        execution_env = ExecutionEnvironment(
            language=language,
            working_directory=str(self.base_workdir),
            docker_image=image,
            network_isolated=True
        )
        
        return await self._execute_code(code, execution_env, None, limits)

    async def batch_execute(self, tasks: List[Dict[str, Any]]) -> List[ExecutionResult]:
        """Execute multiple code tasks in parallel."""
        execution_tasks = []
        
        for task in tasks:
            code = task['code']
            language = ExecutionLanguage(task.get('language', 'python'))
            limits = task.get('limits')
            
            execution_env = ExecutionEnvironment(
                language=language,
                working_directory=str(self.base_workdir),
                network_isolated=task.get('network_isolated', True)
            )
            
            task_coroutine = self._execute_code(code, execution_env, None, limits)
            execution_tasks.append(task_coroutine)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                error_result = ExecutionResult(
                    execution_id=str(uuid.uuid4()),
                    status=ExecutionStatus.FAILED,
                    exit_code=-1,
                    stdout="",
                    stderr=str(result),
                    execution_time=0.0,
                    memory_peak_mb=0.0,
                    cpu_usage_percent=0.0
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results

    async def _execute_code(self, code: str, env: ExecutionEnvironment,
                          args: Optional[List[str]] = None,
                          limits: Optional[ResourceLimits] = None) -> ExecutionResult:
        """Core code execution method with comprehensive safety and monitoring."""
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Use provided limits or defaults
        resource_limits = limits or self.default_limits
        
        logger.info(f"Starting execution {execution_id} for {env.language.value}")
        
        try:
            # Pre-execution validation
            validation_result = self.pattern_detector.validate_code(code, env.language)
            
            if not validation_result.is_safe:
                logger.warning(f"Code validation failed for {execution_id}: {validation_result.detected_patterns}")
                
                if self.security_level in [SecurityLevel.HIGH, SecurityLevel.MAXIMUM]:
                    raise ValueError(f"Code rejected by security validation: {validation_result.detected_patterns}")
            
            # Choose execution method
            if self.use_docker and self.docker_client:
                result = await self._execute_in_docker(execution_id, code, env, resource_limits)
            else:
                result = await self._execute_local(execution_id, code, env, resource_limits)
            
            # Post-execution analysis
            result.error_analysis = await self._analyze_errors(result)
            result.performance_profile = await self._profile_performance(result)
            
            # Store in history
            self._store_execution_result(result)
            
            logger.info(f"Execution {execution_id} completed with status: {result.status}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            error_result = ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                memory_peak_mb=0.0,
                cpu_usage_percent=0.0
            )
            
            self._store_execution_result(error_result)
            logger.error(f"Execution {execution_id} failed: {e}")
            return error_result

    async def _execute_in_docker(self, execution_id: str, code: str,
                               env: ExecutionEnvironment,
                               limits: ResourceLimits) -> ExecutionResult:
        """Execute code in Docker container with full isolation."""
        # Get language configuration
        lang_config = self.language_configs.get(env.language)
        if not lang_config:
            raise ValueError(f"Unsupported language: {env.language}")
        
        # Use custom image if provided
        image = env.docker_image or lang_config["docker_image"]
        
        # Create temporary directory for this execution
        exec_workdir = self.base_workdir / execution_id
        exec_workdir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Write code to file
            code_file = exec_workdir / f"code{lang_config['file_extension']}"
            with open(code_file, 'w') as f:
                f.write(code)
            
            # Container configuration
            container_config = {
                'image': image,
                'command': lang_config['command'] + [code],
                'working_dir': '/workspace',
                'volumes': {str(exec_workdir): {'bind': '/workspace', 'mode': 'rw'}},
                'mem_limit': f"{limits.max_memory_mb}m",
                'memswap_limit': f"{limits.max_memory_mb}m",
                'cpu_quota': int(limits.max_cpu_percent * 1000),
                'cpu_period': 100000,
                'network_disabled': env.network_isolated,
                'remove': True,
                'detach': False,
                'stdout': True,
                'stderr': True,
                'environment': env.environment_variables,
                'user': 'nobody',  # Run as non-root for security
                'read_only': False,  # Allow writing to workspace
                'tmpfs': {'/tmp': ''}  # Provide temporary filesystem
            }
            
            # WSL-specific adjustments
            if self.is_wsl:
                # Adjust volume mount for WSL path translation
                wsl_path = self._convert_wsl_path(str(exec_workdir))
                if wsl_path != str(exec_workdir):
                    container_config['volumes'] = {wsl_path: {'bind': '/workspace', 'mode': 'rw'}}
                
                # Set platform for cross-platform compatibility
                container_config['platform'] = 'linux/amd64'
            
            # Set up resource monitoring
            start_time = time.time()
            memory_peak = 0.0
            cpu_usage = 0.0
            
            # Execute with timeout
            try:
                container = self.docker_client.containers.run(**container_config)
                execution_time = time.time() - start_time
                
                # Parse container output
                output = container.decode('utf-8') if isinstance(container, bytes) else str(container)
                stdout = output
                stderr = ""
                exit_code = 0
                status = ExecutionStatus.COMPLETED
                
            except docker.errors.ContainerError as e:
                execution_time = time.time() - start_time
                stdout = e.stdout.decode('utf-8') if e.stdout else ""
                stderr = e.stderr.decode('utf-8') if e.stderr else str(e)
                exit_code = e.exit_status
                status = ExecutionStatus.FAILED
                
            except Exception as e:
                execution_time = time.time() - start_time
                stdout = ""
                stderr = str(e)
                exit_code = -1
                status = ExecutionStatus.FAILED
            
            # Check for created/modified files
            files_created, files_modified = await self._scan_file_changes(exec_workdir)
            
            return ExecutionResult(
                execution_id=execution_id,
                status=status,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                memory_peak_mb=memory_peak,
                cpu_usage_percent=cpu_usage,
                files_created=files_created,
                files_modified=files_modified
            )
            
        finally:
            # Cleanup
            shutil.rmtree(exec_workdir, ignore_errors=True)

    async def _execute_local(self, execution_id: str, code: str,
                           env: ExecutionEnvironment,
                           limits: ResourceLimits) -> ExecutionResult:
        """Execute code locally with process isolation."""
        # Get language configuration
        lang_config = self.language_configs.get(env.language)
        if not lang_config:
            raise ValueError(f"Unsupported language: {env.language}")
        
        # Create temporary directory
        exec_workdir = self.base_workdir / execution_id
        exec_workdir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Write code to file
            code_file = exec_workdir / f"code{lang_config['file_extension']}"
            with open(code_file, 'w') as f:
                f.write(code)
            
            # Prepare command
            if env.language == ExecutionLanguage.PYTHON:
                cmd = ['python', str(code_file)]
            elif env.language == ExecutionLanguage.NODEJS:
                cmd = ['node', str(code_file)]
            elif env.language == ExecutionLanguage.BASH:
                cmd = ['bash', str(code_file)]
            else:
                raise ValueError(f"Local execution not supported for {env.language}")
            
            # Set resource limits
            def set_limits():
                # Memory limit
                resource.setrlimit(resource.RLIMIT_AS, (limits.max_memory_mb * 1024 * 1024, -1))
                # CPU time limit
                resource.setrlimit(resource.RLIMIT_CPU, (limits.max_execution_time, -1))
                # Process limit
                resource.setrlimit(resource.RLIMIT_NPROC, (limits.max_processes, -1))
                # File descriptor limit
                resource.setrlimit(resource.RLIMIT_NOFILE, (limits.max_file_descriptors, -1))
            
            # Execute process
            start_time = time.time()
            
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=exec_workdir,
                    env={**os.environ, **env.environment_variables},
                    preexec_fn=set_limits
                )
                
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=limits.max_execution_time
                )
                
                execution_time = time.time() - start_time
                exit_code = process.returncode
                status = ExecutionStatus.COMPLETED if exit_code == 0 else ExecutionStatus.FAILED
                
            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                if process:
                    process.kill()
                    await process.wait()
                
                stdout = b""
                stderr = b"Execution timeout"
                exit_code = -1
                status = ExecutionStatus.TIMEOUT
            
            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            # Monitor resource usage (simplified)
            memory_peak = 0.0
            cpu_usage = 0.0
            
            # Check for file changes
            files_created, files_modified = await self._scan_file_changes(exec_workdir)
            
            return ExecutionResult(
                execution_id=execution_id,
                status=status,
                exit_code=exit_code,
                stdout=stdout_str,
                stderr=stderr_str,
                execution_time=execution_time,
                memory_peak_mb=memory_peak,
                cpu_usage_percent=cpu_usage,
                files_created=files_created,
                files_modified=files_modified
            )
            
        finally:
            # Cleanup
            shutil.rmtree(exec_workdir, ignore_errors=True)

    async def _scan_file_changes(self, workdir: Path) -> Tuple[List[str], List[str]]:
        """Scan for created and modified files in working directory."""
        created_files = []
        modified_files = []
        
        try:
            for file_path in workdir.rglob('*'):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(workdir))
                    
                    # Skip code files we created
                    if not relative_path.startswith('code.'):
                        created_files.append(relative_path)
        
        except Exception as e:
            logger.warning(f"Failed to scan file changes: {e}")
        
        return created_files, modified_files

    async def _analyze_errors(self, result: ExecutionResult) -> Optional[Dict[str, Any]]:
        """Analyze execution errors and provide insights."""
        if result.status == ExecutionStatus.COMPLETED:
            return None
        
        error_analysis = {
            'error_type': 'unknown',
            'likely_cause': 'Unknown error',
            'suggestions': [],
            'severity': 'medium'
        }
        
        stderr = result.stderr.lower()
        
        # Common error patterns
        if 'syntaxerror' in stderr or 'syntax error' in stderr:
            error_analysis.update({
                'error_type': 'syntax_error',
                'likely_cause': 'Code contains syntax errors',
                'suggestions': ['Check code syntax', 'Validate parentheses and brackets'],
                'severity': 'low'
            })
        
        elif 'nameerror' in stderr or 'name error' in stderr:
            error_analysis.update({
                'error_type': 'name_error',
                'likely_cause': 'Undefined variable or function',
                'suggestions': ['Check variable names', 'Ensure all imports are present'],
                'severity': 'medium'
            })
        
        elif 'importerror' in stderr or 'modulenotfounderror' in stderr:
            error_analysis.update({
                'error_type': 'import_error',
                'likely_cause': 'Missing module or package',
                'suggestions': ['Install required packages', 'Check import statements'],
                'severity': 'medium'
            })
        
        elif 'permissionerror' in stderr or 'permission denied' in stderr:
            error_analysis.update({
                'error_type': 'permission_error',
                'likely_cause': 'Insufficient permissions for file/directory access',
                'suggestions': ['Check file permissions', 'Ensure proper access rights'],
                'severity': 'high'
            })
        
        elif result.status == ExecutionStatus.TIMEOUT:
            error_analysis.update({
                'error_type': 'timeout',
                'likely_cause': 'Execution exceeded time limit',
                'suggestions': ['Optimize code performance', 'Increase timeout limit'],
                'severity': 'medium'
            })
        
        return error_analysis

    async def _profile_performance(self, result: ExecutionResult) -> Dict[str, Any]:
        """Generate performance profile for execution."""
        profile = {
            'execution_time_category': 'normal',
            'memory_usage_category': 'normal',
            'efficiency_score': 0.5,
            'bottlenecks': [],
            'optimizations': []
        }
        
        # Categorize execution time
        if result.execution_time < 1.0:
            profile['execution_time_category'] = 'fast'
        elif result.execution_time > 10.0:
            profile['execution_time_category'] = 'slow'
            profile['bottlenecks'].append('Long execution time')
            profile['optimizations'].append('Consider algorithm optimization')
        
        # Categorize memory usage
        if result.memory_peak_mb < 50:
            profile['memory_usage_category'] = 'light'
        elif result.memory_peak_mb > 200:
            profile['memory_usage_category'] = 'heavy'
            profile['bottlenecks'].append('High memory usage')
            profile['optimizations'].append('Consider memory optimization')
        
        # Calculate efficiency score
        time_score = max(0, 1 - (result.execution_time / 30))  # 30s max
        memory_score = max(0, 1 - (result.memory_peak_mb / 256))  # 256MB max
        success_score = 1.0 if result.status == ExecutionStatus.COMPLETED else 0.0
        
        profile['efficiency_score'] = (time_score + memory_score + success_score) / 3
        
        return profile

    def _store_execution_result(self, result: ExecutionResult):
        """Store execution result in history."""
        self.execution_history.append(result)
        
        # Trim history if it gets too long
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]

    # Management and monitoring methods
    
    def get_active_executions(self) -> List[str]:
        """Get list of currently active execution IDs."""
        return list(self.active_executions.keys())

    def kill_execution(self, execution_id: str) -> bool:
        """Kill an active execution."""
        if execution_id in self.active_executions:
            task = self.active_executions[execution_id]
            task.cancel()
            del self.active_executions[execution_id]
            logger.info(f"Killed execution: {execution_id}")
            return True
        return False

    def get_execution_history(self, limit: int = 50) -> List[ExecutionResult]:
        """Get recent execution history."""
        return self.execution_history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'average_memory_usage': 0.0
            }
        
        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.status == ExecutionStatus.COMPLETED)
        
        avg_time = sum(r.execution_time for r in self.execution_history) / total
        avg_memory = sum(r.memory_peak_mb for r in self.execution_history) / total
        
        return {
            'total_executions': total,
            'success_rate': successful / total,
            'average_execution_time': avg_time,
            'average_memory_usage': avg_memory,
            'active_executions': len(self.active_executions),
            'docker_available': self.use_docker
        }

    async def cleanup_old_executions(self, max_age_hours: int = 24) -> int:
        """Clean up old execution data."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Clean up temporary directories
        cleanup_count = 0
        try:
            for item in self.base_workdir.iterdir():
                if item.is_dir():
                    try:
                        # Check if directory is old enough
                        creation_time = datetime.fromtimestamp(item.stat().st_ctime)
                        if creation_time < cutoff_time:
                            shutil.rmtree(item, ignore_errors=True)
                            cleanup_count += 1
                    except (OSError, ValueError):
                        continue
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
        
        logger.info(f"Cleaned up {cleanup_count} old execution directories")
        return cleanup_count

    async def install_dependencies(self, language: ExecutionLanguage, 
                                 dependencies: List[str]) -> bool:
        """Install dependencies in execution environment."""
        if not self.use_docker:
            logger.warning("Dependency installation requires Docker")
            return False
        
        try:
            if language == ExecutionLanguage.PYTHON:
                install_cmd = ["pip", "install"] + dependencies
            elif language == ExecutionLanguage.NODEJS:
                install_cmd = ["npm", "install"] + dependencies
            else:
                logger.warning(f"Dependency installation not supported for {language}")
                return False
            
            # Run installation in container
            image = self.language_configs[language]["docker_image"]
            
            container = self.docker_client.containers.run(
                image=image,
                command=install_cmd,
                remove=True,
                detach=False
            )
            
            logger.info(f"Installed dependencies for {language}: {dependencies}")
            return True
            
        except Exception as e:
            logger.error(f"Dependency installation failed: {e}")
            return False

    @asynccontextmanager
    async def execution_context(self, limits: Optional[ResourceLimits] = None):
        """Context manager for grouped executions with shared resources."""
        context_id = str(uuid.uuid4())
        context_workdir = self.base_workdir / f"context_{context_id}"
        context_workdir.mkdir(parents=True, exist_ok=True)
        
        old_workdir = self.base_workdir
        self.base_workdir = context_workdir
        
        try:
            yield context_id
        finally:
            self.base_workdir = old_workdir
            # Cleanup context directory
            shutil.rmtree(context_workdir, ignore_errors=True)

    def validate_code_safety(self, code: str, 
                           language: ExecutionLanguage) -> CodeValidationResult:
        """Public method to validate code safety without execution."""
        return self.pattern_detector.validate_code(code, language)