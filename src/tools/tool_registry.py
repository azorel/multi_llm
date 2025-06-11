"""
Tool Registry for dynamic tool loading and management.

This module provides a centralized registry for tools, capabilities,
and intelligent tool selection logic for autonomous agents.
"""

import asyncio
import importlib
import inspect
import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable, Type, Set, Tuple
import uuid

from loguru import logger


class ToolCategory(Enum):
    """Categories of tools available in the system."""
    FILE_SYSTEM = "file_system"
    CODE_EXECUTION = "code_execution"
    VALIDATION = "validation"
    COMMUNICATION = "communication"
    DATA_PROCESSING = "data_processing"
    ANALYSIS = "analysis"
    SECURITY = "security"
    MONITORING = "monitoring"
    INTEGRATION = "integration"
    UTILITY = "utility"


class ToolCapability(Enum):
    """Specific capabilities that tools can provide."""
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    EXECUTE_CODE = "execute_code"
    VALIDATE_CODE = "validate_code"
    GENERATE_TESTS = "generate_tests"
    ANALYZE_SECURITY = "analyze_security"
    MONITOR_PERFORMANCE = "monitor_performance"
    PROCESS_DATA = "process_data"
    COMMUNICATE_EXTERNAL = "communicate_external"
    SANDBOX_OPERATIONS = "sandbox_operations"
    TRANSACTION_SUPPORT = "transaction_support"


class ToolComplexity(Enum):
    """Complexity levels for tools."""
    SIMPLE = "simple"      # Basic operations
    MODERATE = "moderate"  # Multi-step operations
    COMPLEX = "complex"    # Advanced operations requiring coordination
    EXPERT = "expert"      # Highly specialized operations


class ToolSafety(Enum):
    """Safety levels for tool operations."""
    SAFE = "safe"           # No potential for harm
    CAUTIOUS = "cautious"   # Minimal risk with proper usage
    RISKY = "risky"         # Requires careful handling
    DANGEROUS = "dangerous" # High potential for harm


@dataclass
class ToolRequirements:
    """Requirements for using a tool."""
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    environment_vars: List[str] = field(default_factory=list)
    minimum_python_version: str = "3.8"
    external_tools: List[str] = field(default_factory=list)
    system_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolMetrics:
    """Metrics for tool usage and performance."""
    total_uses: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    average_execution_time: float = 0.0
    last_used: Optional[datetime] = None
    error_rate: float = 0.0
    performance_score: float = 1.0


@dataclass
class ToolConfiguration:
    """Configuration settings for a tool."""
    enabled: bool = True
    max_concurrent_uses: int = 10
    timeout_seconds: int = 300
    retry_attempts: int = 3
    log_level: str = "INFO"
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tool_id = str(uuid.uuid4())
        self.metrics = ToolMetrics()
        self.configuration = ToolConfiguration(**config.get('configuration', {}))
        self._initialized = False
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Tool category."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[ToolCapability]:
        """Tool capabilities."""
        pass
    
    @property
    @abstractmethod
    def complexity(self) -> ToolComplexity:
        """Tool complexity level."""
        pass
    
    @property
    @abstractmethod
    def safety_level(self) -> ToolSafety:
        """Tool safety level."""
        pass
    
    @property
    @abstractmethod
    def requirements(self) -> ToolRequirements:
        """Tool requirements."""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the tool."""
        pass
    
    @abstractmethod
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool action."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup tool resources."""
        pass
    
    def get_available_actions(self) -> List[str]:
        """Get list of available actions for this tool."""
        actions = []
        for method_name in dir(self):
            if method_name.startswith('action_') and callable(getattr(self, method_name)):
                action_name = method_name[7:]  # Remove 'action_' prefix
                actions.append(action_name)
        return actions
    
    def update_metrics(self, success: bool, execution_time: float):
        """Update tool usage metrics."""
        self.metrics.total_uses += 1
        self.metrics.last_used = datetime.now()
        
        if success:
            self.metrics.successful_uses += 1
        else:
            self.metrics.failed_uses += 1
        
        # Update average execution time
        if self.metrics.total_uses == 1:
            self.metrics.average_execution_time = execution_time
        else:
            self.metrics.average_execution_time = (
                (self.metrics.average_execution_time * (self.metrics.total_uses - 1) + execution_time) 
                / self.metrics.total_uses
            )
        
        # Update error rate
        self.metrics.error_rate = self.metrics.failed_uses / self.metrics.total_uses
        
        # Update performance score (simple calculation)
        self.metrics.performance_score = max(0.1, 1.0 - self.metrics.error_rate)


@dataclass
class ToolRegistration:
    """Registration information for a tool."""
    tool_class: Type[BaseTool]
    tool_instance: Optional[BaseTool]
    registration_time: datetime
    module_path: str
    config: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolSelector:
    """Intelligent tool selection logic."""
    
    def __init__(self):
        self.selection_history: List[Dict[str, Any]] = []
        self.capability_weights = {
            ToolCapability.READ_FILE: 1.0,
            ToolCapability.WRITE_FILE: 1.2,
            ToolCapability.DELETE_FILE: 1.5,
            ToolCapability.EXECUTE_CODE: 2.0,
            ToolCapability.VALIDATE_CODE: 1.3,
            ToolCapability.ANALYZE_SECURITY: 1.8,
            ToolCapability.SANDBOX_OPERATIONS: 1.6,
        }
    
    def select_best_tool(self, 
                        required_capabilities: List[ToolCapability],
                        available_tools: List[BaseTool],
                        preferences: Optional[Dict[str, Any]] = None) -> Optional[BaseTool]:
        """Select the best tool for the given capabilities and preferences."""
        if not available_tools:
            return None
        
        preferences = preferences or {}
        
        # Score each tool
        tool_scores = []
        for tool in available_tools:
            score = self._calculate_tool_score(tool, required_capabilities, preferences)
            tool_scores.append((tool, score))
        
        # Sort by score (descending)
        tool_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Log selection decision
        self._log_selection_decision(required_capabilities, tool_scores, preferences)
        
        # Return the best tool
        best_tool = tool_scores[0][0] if tool_scores[0][1] > 0 else None
        return best_tool
    
    def _calculate_tool_score(self, 
                            tool: BaseTool, 
                            required_capabilities: List[ToolCapability],
                            preferences: Dict[str, Any]) -> float:
        """Calculate a score for how well a tool matches the requirements."""
        score = 0.0
        
        # Check capability match
        tool_capabilities = set(tool.capabilities)
        required_capabilities_set = set(required_capabilities)
        
        # Base score from capability overlap
        capability_overlap = len(tool_capabilities.intersection(required_capabilities_set))
        if capability_overlap == 0:
            return 0.0  # Tool doesn't have any required capabilities
        
        # Capability coverage score (0-1)
        coverage_score = capability_overlap / len(required_capabilities_set)
        score += coverage_score * 10
        
        # Performance score
        score += tool.metrics.performance_score * 5
        
        # Complexity preference
        complexity_pref = preferences.get('complexity', 'moderate')
        if tool.complexity.value == complexity_pref:
            score += 3
        elif tool.complexity == ToolComplexity.SIMPLE and complexity_pref in ['simple', 'moderate']:
            score += 2
        
        # Safety preference
        safety_pref = preferences.get('safety', 'cautious')
        safety_scores = {
            ToolSafety.SAFE: 4,
            ToolSafety.CAUTIOUS: 3,
            ToolSafety.RISKY: 2,
            ToolSafety.DANGEROUS: 1
        }
        if tool.safety_level.value == safety_pref:
            score += 4
        else:
            score += safety_scores.get(tool.safety_level, 1)
        
        # Recent usage penalty (prefer less recently used tools for load balancing)
        if tool.metrics.last_used:
            hours_since_use = (datetime.now() - tool.metrics.last_used).total_seconds() / 3600
            if hours_since_use < 1:
                score -= 1  # Small penalty for very recently used tools
        
        # Error rate penalty
        if tool.metrics.error_rate > 0:
            score -= tool.metrics.error_rate * 5
        
        # Capability weight bonus
        for capability in required_capabilities:
            if capability in tool.capabilities:
                weight = self.capability_weights.get(capability, 1.0)
                score += weight
        
        return max(0.0, score)
    
    def _log_selection_decision(self, 
                              required_capabilities: List[ToolCapability],
                              tool_scores: List[Tuple[BaseTool, float]],
                              preferences: Dict[str, Any]):
        """Log the tool selection decision for analysis."""
        decision_log = {
            'timestamp': datetime.now(),
            'required_capabilities': [cap.value for cap in required_capabilities],
            'preferences': preferences,
            'tool_scores': [
                {
                    'tool_name': tool.name,
                    'score': score,
                    'capabilities': [cap.value for cap in tool.capabilities],
                    'complexity': tool.complexity.value,
                    'safety': tool.safety_level.value,
                    'performance_score': tool.metrics.performance_score,
                    'error_rate': tool.metrics.error_rate
                }
                for tool, score in tool_scores[:5]  # Top 5 tools
            ]
        }
        
        self.selection_history.append(decision_log)
        
        # Keep only recent history
        if len(self.selection_history) > 1000:
            self.selection_history = self.selection_history[-1000:]
        
        logger.debug(f"Tool selection: {tool_scores[0][0].name if tool_scores else 'None'} "
                    f"(score: {tool_scores[0][1]:.2f})" if tool_scores else "No suitable tool found")


class ToolRegistry:
    """Comprehensive registry for managing tools."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tools: Dict[str, ToolRegistration] = {}
        self.tool_instances: Dict[str, BaseTool] = {}
        self.categories: Dict[ToolCategory, List[str]] = {cat: [] for cat in ToolCategory}
        self.capabilities: Dict[ToolCapability, List[str]] = {cap: [] for cap in ToolCapability}
        
        # Tool management
        self.selector = ToolSelector()
        self.auto_load = config.get('auto_load_tools', True)
        self.tool_directories = config.get('tool_directories', [])
        
        # Performance monitoring
        self.registry_metrics = {
            'total_registrations': 0,
            'active_tools': 0,
            'failed_initializations': 0,
            'last_scan': None
        }
        
        logger.info("ToolRegistry initialized")
    
    async def initialize(self):
        """Initialize the tool registry."""
        if self.auto_load:
            await self.auto_discover_tools()
        
        # Register built-in tools
        await self._register_builtin_tools()
        
        logger.info(f"ToolRegistry initialized with {len(self.tools)} tools")
    
    async def register_tool(self, 
                           tool_class: Type[BaseTool], 
                           tool_name: str,
                           config: Optional[Dict[str, Any]] = None,
                           module_path: str = "") -> bool:
        """Register a tool class with the registry."""
        try:
            config = config or {}
            
            # Create tool instance
            tool_instance = tool_class(config)
            
            # Initialize the tool
            if await tool_instance.initialize():
                registration = ToolRegistration(
                    tool_class=tool_class,
                    tool_instance=tool_instance,
                    registration_time=datetime.now(),
                    module_path=module_path,
                    config=config
                )
                
                self.tools[tool_name] = registration
                self.tool_instances[tool_name] = tool_instance
                
                # Update category and capability mappings
                self.categories[tool_instance.category].append(tool_name)
                for capability in tool_instance.capabilities:
                    self.capabilities[capability].append(tool_name)
                
                self.registry_metrics['total_registrations'] += 1
                self.registry_metrics['active_tools'] += 1
                
                logger.info(f"Successfully registered tool: {tool_name}")
                return True
            else:
                logger.error(f"Failed to initialize tool: {tool_name}")
                self.registry_metrics['failed_initializations'] += 1
                return False
                
        except Exception as e:
            logger.error(f"Error registering tool {tool_name}: {e}")
            self.registry_metrics['failed_initializations'] += 1
            return False
    
    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool from the registry."""
        if tool_name not in self.tools:
            logger.warning(f"Tool not found for unregistration: {tool_name}")
            return False
        
        try:
            registration = self.tools[tool_name]
            tool_instance = self.tool_instances[tool_name]
            
            # Cleanup tool
            await tool_instance.cleanup()
            
            # Remove from mappings
            self.categories[tool_instance.category].remove(tool_name)
            for capability in tool_instance.capabilities:
                if tool_name in self.capabilities[capability]:
                    self.capabilities[capability].remove(tool_name)
            
            # Remove from registry
            del self.tools[tool_name]
            del self.tool_instances[tool_name]
            
            self.registry_metrics['active_tools'] -= 1
            
            logger.info(f"Successfully unregistered tool: {tool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering tool {tool_name}: {e}")
            return False
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool instance by name."""
        return self.tool_instances.get(tool_name)
    
    def get_tools_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """Get all tools in a specific category."""
        tool_names = self.categories.get(category, [])
        return [self.tool_instances[name] for name in tool_names if name in self.tool_instances]
    
    def get_tools_by_capability(self, capability: ToolCapability) -> List[BaseTool]:
        """Get all tools with a specific capability."""
        tool_names = self.capabilities.get(capability, [])
        return [self.tool_instances[name] for name in tool_names if name in self.tool_instances]
    
    def select_tool(self, 
                   required_capabilities: List[ToolCapability],
                   preferences: Optional[Dict[str, Any]] = None) -> Optional[BaseTool]:
        """Select the best tool for the given requirements."""
        # Get all tools that have at least one required capability
        candidate_tools = set()
        for capability in required_capabilities:
            candidate_tools.update(self.get_tools_by_capability(capability))
        
        if not candidate_tools:
            return None
        
        return self.selector.select_best_tool(
            required_capabilities, 
            list(candidate_tools), 
            preferences
        )
    
    async def execute_tool_action(self, 
                                tool_name: str, 
                                action: str, 
                                **kwargs) -> Dict[str, Any]:
        """Execute an action on a specific tool."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        start_time = time.time()
        success = False
        
        try:
            result = await tool.execute(action, **kwargs)
            success = True
            return result
        except Exception as e:
            logger.error(f"Tool action failed: {tool_name}.{action} - {e}")
            raise
        finally:
            execution_time = time.time() - start_time
            tool.update_metrics(success, execution_time)
    
    async def execute_with_best_tool(self, 
                                   required_capabilities: List[ToolCapability],
                                   action: str,
                                   preferences: Optional[Dict[str, Any]] = None,
                                   **kwargs) -> Dict[str, Any]:
        """Execute an action using the best available tool."""
        tool = self.select_tool(required_capabilities, preferences)
        if not tool:
            raise ValueError(f"No suitable tool found for capabilities: {required_capabilities}")
        
        return await self.execute_tool_action(tool.name, action, **kwargs)
    
    async def auto_discover_tools(self):
        """Automatically discover and load tools from configured directories."""
        discovered_count = 0
        
        # Default tool discovery in the tools package
        tools_module_path = Path(__file__).parent
        discovered_count += await self._discover_tools_in_directory(tools_module_path)
        
        # Discover in additional directories
        for directory in self.tool_directories:
            try:
                dir_path = Path(directory)
                if dir_path.exists() and dir_path.is_dir():
                    discovered_count += await self._discover_tools_in_directory(dir_path)
            except Exception as e:
                logger.warning(f"Failed to discover tools in {directory}: {e}")
        
        self.registry_metrics['last_scan'] = datetime.now()
        logger.info(f"Auto-discovery found {discovered_count} tools")
    
    async def _discover_tools_in_directory(self, directory: Path) -> int:
        """Discover tools in a specific directory."""
        discovered_count = 0
        
        for python_file in directory.glob("*.py"):
            if python_file.name.startswith("__"):
                continue
            
            try:
                # Import module
                module_name = python_file.stem
                spec = importlib.util.spec_from_file_location(module_name, python_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for tool classes
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseTool) and 
                            obj != BaseTool):
                            
                            tool_name = name.lower().replace('tool', '')
                            await self.register_tool(obj, tool_name, {}, str(python_file))
                            discovered_count += 1
                            
            except Exception as e:
                logger.warning(f"Failed to load tools from {python_file}: {e}")
        
        return discovered_count
    
    async def _register_builtin_tools(self):
        """Register built-in tools that are always available."""
        builtin_tools = [
            ('file_system', 'src.tools.file_system', 'SecureFileSystemManager'),
            ('code_executor', 'src.tools.code_executor', 'CodeExecutor'),
            ('validation', 'src.tools.validation', 'ValidationFramework')
        ]
        
        for tool_name, module_path, class_name in builtin_tools:
            try:
                module = importlib.import_module(module_path)
                tool_class = getattr(module, class_name)
                
                # Create wrapper tool class
                wrapper_class = self._create_tool_wrapper(tool_class, tool_name)
                await self.register_tool(wrapper_class, tool_name, {}, module_path)
                
            except Exception as e:
                logger.warning(f"Failed to register builtin tool {tool_name}: {e}")
    
    def _create_tool_wrapper(self, original_class: Type, tool_name: str) -> Type[BaseTool]:
        """Create a BaseTool wrapper for existing tool classes."""
        
        class ToolWrapper(BaseTool):
            def __init__(self, config: Dict[str, Any]):
                super().__init__(config)
                self.wrapped_instance = original_class(config)
                self._tool_name = tool_name
            
            @property
            def name(self) -> str:
                return self._tool_name
            
            @property
            def description(self) -> str:
                return getattr(self.wrapped_instance, '__doc__', f"{self._tool_name} tool")
            
            @property
            def category(self) -> ToolCategory:
                category_map = {
                    'file_system': ToolCategory.FILE_SYSTEM,
                    'code_executor': ToolCategory.CODE_EXECUTION,
                    'validation': ToolCategory.VALIDATION
                }
                return category_map.get(self._tool_name, ToolCategory.UTILITY)
            
            @property
            def capabilities(self) -> List[ToolCapability]:
                capability_map = {
                    'file_system': [
                        ToolCapability.READ_FILE, 
                        ToolCapability.WRITE_FILE, 
                        ToolCapability.DELETE_FILE,
                        ToolCapability.SANDBOX_OPERATIONS,
                        ToolCapability.TRANSACTION_SUPPORT
                    ],
                    'code_executor': [
                        ToolCapability.EXECUTE_CODE,
                        ToolCapability.SANDBOX_OPERATIONS,
                        ToolCapability.MONITOR_PERFORMANCE
                    ],
                    'validation': [
                        ToolCapability.VALIDATE_CODE,
                        ToolCapability.GENERATE_TESTS,
                        ToolCapability.ANALYZE_SECURITY
                    ]
                }
                return capability_map.get(self._tool_name, [])
            
            @property
            def complexity(self) -> ToolComplexity:
                complexity_map = {
                    'file_system': ToolComplexity.MODERATE,
                    'code_executor': ToolComplexity.COMPLEX,
                    'validation': ToolComplexity.COMPLEX
                }
                return complexity_map.get(self._tool_name, ToolComplexity.MODERATE)
            
            @property
            def safety_level(self) -> ToolSafety:
                safety_map = {
                    'file_system': ToolSafety.CAUTIOUS,
                    'code_executor': ToolSafety.RISKY,
                    'validation': ToolSafety.SAFE
                }
                return safety_map.get(self._tool_name, ToolSafety.CAUTIOUS)
            
            @property
            def requirements(self) -> ToolRequirements:
                requirements_map = {
                    'file_system': ToolRequirements(
                        dependencies=['aiofiles', 'magic', 'psutil'],
                        permissions=['file_system_access']
                    ),
                    'code_executor': ToolRequirements(
                        dependencies=['docker', 'psutil'],
                        external_tools=['docker'],
                        permissions=['container_access']
                    ),
                    'validation': ToolRequirements(
                        dependencies=['bandit', 'pylint', 'coverage'],
                        permissions=['code_analysis']
                    )
                }
                return requirements_map.get(self._tool_name, ToolRequirements())
            
            async def initialize(self) -> bool:
                try:
                    if hasattr(self.wrapped_instance, 'initialize'):
                        result = await self.wrapped_instance.initialize()
                        if isinstance(result, bool):
                            return result
                    return True
                except Exception as e:
                    logger.error(f"Failed to initialize {self._tool_name}: {e}")
                    return False
            
            async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
                # Map action to method call
                method_name = f"action_{action}"
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    return await method(**kwargs)
                else:
                    raise ValueError(f"Action '{action}' not supported by {self._tool_name}")
            
            async def cleanup(self):
                if hasattr(self.wrapped_instance, 'cleanup'):
                    await self.wrapped_instance.cleanup()
            
            # Action methods for file_system
            async def action_create_file(self, path: str, content: str, **kwargs) -> Dict[str, Any]:
                if self._tool_name == 'file_system':
                    result = await self.wrapped_instance.create_file(path, content, **kwargs)
                    return {'success': result, 'path': path}
                raise NotImplementedError()
            
            async def action_read_file(self, path: str, **kwargs) -> Dict[str, Any]:
                if self._tool_name == 'file_system':
                    content = await self.wrapped_instance.read_file(path, **kwargs)
                    return {'content': content, 'path': path}
                raise NotImplementedError()
            
            async def action_delete_file(self, path: str, **kwargs) -> Dict[str, Any]:
                if self._tool_name == 'file_system':
                    result = await self.wrapped_instance.delete_file(path, **kwargs)
                    return {'success': result, 'path': path}
                raise NotImplementedError()
            
            # Action methods for code_executor
            async def action_execute_python(self, code: str, **kwargs) -> Dict[str, Any]:
                if self._tool_name == 'code_executor':
                    result = await self.wrapped_instance.execute_python(code, **kwargs)
                    return {'result': result.dict() if hasattr(result, 'dict') else result}
                raise NotImplementedError()
            
            async def action_execute_shell(self, commands: str, **kwargs) -> Dict[str, Any]:
                if self._tool_name == 'code_executor':
                    result = await self.wrapped_instance.execute_shell(commands, **kwargs)
                    return {'result': result.dict() if hasattr(result, 'dict') else result}
                raise NotImplementedError()
            
            # Action methods for validation
            async def action_validate_code(self, code: str, language: str = 'python', **kwargs) -> Dict[str, Any]:
                if self._tool_name == 'validation':
                    result = await self.wrapped_instance.validate_code(code, language, **kwargs)
                    return {'result': result.dict() if hasattr(result, 'dict') else result}
                raise NotImplementedError()
            
            async def action_generate_tests(self, code: str, **kwargs) -> Dict[str, Any]:
                if self._tool_name == 'validation':
                    result = await self.wrapped_instance.generate_tests(code, **kwargs)
                    return {'tests': [test.dict() if hasattr(test, 'dict') else test for test in result]}
                raise NotImplementedError()
        
        return ToolWrapper
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get comprehensive registry status."""
        return {
            'total_tools': len(self.tools),
            'active_tools': self.registry_metrics['active_tools'],
            'categories': {
                cat.value: len(tools) for cat, tools in self.categories.items()
            },
            'capabilities': {
                cap.value: len(tools) for cap, tools in self.capabilities.items()
            },
            'metrics': self.registry_metrics,
            'tool_health': {
                name: {
                    'performance_score': tool.metrics.performance_score,
                    'error_rate': tool.metrics.error_rate,
                    'total_uses': tool.metrics.total_uses,
                    'last_used': tool.metrics.last_used.isoformat() if tool.metrics.last_used else None
                }
                for name, tool in self.tool_instances.items()
            }
        }
    
    def get_tool_recommendations(self, 
                               task_description: str,
                               context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get tool recommendations for a given task."""
        context = context or {}
        
        # Simple keyword-based capability detection
        capability_keywords = {
            ToolCapability.READ_FILE: ['read', 'load', 'get', 'fetch', 'open'],
            ToolCapability.WRITE_FILE: ['write', 'save', 'create', 'store'],
            ToolCapability.DELETE_FILE: ['delete', 'remove', 'unlink'],
            ToolCapability.EXECUTE_CODE: ['execute', 'run', 'eval', 'compile'],
            ToolCapability.VALIDATE_CODE: ['validate', 'check', 'verify', 'lint'],
            ToolCapability.GENERATE_TESTS: ['test', 'testing', 'unittest'],
            ToolCapability.ANALYZE_SECURITY: ['security', 'vulnerability', 'scan']
        }
        
        # Detect required capabilities
        task_lower = task_description.lower()
        required_capabilities = []
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                required_capabilities.append(capability)
        
        if not required_capabilities:
            # If no specific capabilities detected, return general recommendations
            return []
        
        # Get tools with required capabilities
        candidate_tools = set()
        for capability in required_capabilities:
            candidate_tools.update(self.get_tools_by_capability(capability))
        
        # Score and rank tools
        recommendations = []
        for tool in candidate_tools:
            score = self.selector._calculate_tool_score(
                tool, required_capabilities, context
            )
            
            recommendations.append({
                'tool_name': tool.name,
                'score': score,
                'capabilities': [cap.value for cap in tool.capabilities],
                'description': tool.description,
                'complexity': tool.complexity.value,
                'safety': tool.safety_level.value,
                'category': tool.category.value,
                'actions': tool.get_available_actions(),
                'requirements': tool.requirements.__dict__
            })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:5]  # Top 5 recommendations


# Global registry instance
_registry_instance: Optional[ToolRegistry] = None


async def get_tool_registry(config: Optional[Dict[str, Any]] = None) -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry_instance
    
    if _registry_instance is None:
        _registry_instance = ToolRegistry(config or {})
        await _registry_instance.initialize()
    
    return _registry_instance


async def register_tool(tool_class: Type[BaseTool], 
                       tool_name: str,
                       config: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to register a tool with the global registry."""
    registry = await get_tool_registry()
    return await registry.register_tool(tool_class, tool_name, config)


async def get_tool(tool_name: str) -> Optional[BaseTool]:
    """Convenience function to get a tool from the global registry."""
    registry = await get_tool_registry()
    return registry.get_tool(tool_name)


async def execute_tool_action(tool_name: str, action: str, **kwargs) -> Dict[str, Any]:
    """Convenience function to execute a tool action."""
    registry = await get_tool_registry()
    return await registry.execute_tool_action(tool_name, action, **kwargs)


async def find_best_tool(required_capabilities: List[ToolCapability],
                        preferences: Optional[Dict[str, Any]] = None) -> Optional[BaseTool]:
    """Convenience function to find the best tool for capabilities."""
    registry = await get_tool_registry()
    return registry.select_tool(required_capabilities, preferences)


async def get_tool_recommendations(task_description: str,
                                 context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Convenience function to get tool recommendations."""
    registry = await get_tool_registry()
    return registry.get_tool_recommendations(task_description, context)