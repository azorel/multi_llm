#!/usr/bin/env python3
"""
Enhanced Real Agent Orchestrator - Claude + Gemini Optimized
TDD-driven implementation with advanced multi-agent coordination
"""

import asyncio
import json
import sqlite3
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import anthropic
import google.generativeai as genai
from pathlib import Path
import traceback
import subprocess
import time
import concurrent.futures
import random

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class AgentType(Enum):
    CODE_DEVELOPER = "code_developer"
    SYSTEM_ANALYST = "system_analyst"
    CONTENT_PROCESSOR = "content_processor"
    DATABASE_SPECIALIST = "database_specialist"
    API_INTEGRATOR = "api_integrator"
    ERROR_DIAGNOSTICIAN = "error_diagnostician"
    TEMPLATE_FIXER = "template_fixer"
    WEB_TESTER = "web_tester"

@dataclass
class Task:
    id: str
    name: str
    description: str
    agent_type: AgentType
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    tokens_used: int = 0
    cost: float = 0.0
    files_created: List[str] = None
    files_modified: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.files_created is None:
            self.files_created = []
        if self.files_modified is None:
            self.files_modified = []
        if self.metadata is None:
            self.metadata = {}

class ProviderLoadBalancer:
    """Enhanced load balancer for Claude + Gemini optimization"""
    
    def __init__(self):
        # Claude + Gemini only configuration
        self.providers = {
            "anthropic": {"weight": 0.5, "requests": 0, "errors": 0, "cost": 0.0, "response_times": []},
            "gemini": {"weight": 0.5, "requests": 0, "errors": 0, "cost": 0.0, "response_times": []}
        }
        self.current_index = 0
        
    def get_next_provider(self) -> str:
        """Get next provider based on enhanced weighted selection"""
        # Calculate availability scores
        available_providers = []
        for name, data in self.providers.items():
            error_rate = data["errors"] / max(data["requests"], 1)
            avg_response_time = sum(data["response_times"][-10:]) / max(len(data["response_times"][-10:]), 1)
            
            # Score based on error rate and response time
            availability_score = (1 - error_rate) * (1 / max(avg_response_time, 0.1))
            available_providers.append((name, data, availability_score))
        
        if not available_providers:
            return "anthropic"  # Fallback to Claude
            
        # Weight by availability score
        total_score = sum(score for _, _, score in available_providers)
        if total_score == 0:
            return "anthropic"
        
        # Select based on weighted probability
        r = random.random() * total_score
        cumulative = 0
        for name, data, score in available_providers:
            cumulative += score
            if r <= cumulative:
                return name
                
        return "anthropic"
    
    def record_request(self, provider: str, success: bool, cost: float = 0.0, response_time: float = 0.0):
        """Record request outcome with enhanced metrics"""
        if provider in self.providers:
            self.providers[provider]["requests"] += 1
            self.providers[provider]["cost"] += cost
            self.providers[provider]["response_times"].append(response_time)
            
            # Keep only last 100 response times
            if len(self.providers[provider]["response_times"]) > 100:
                self.providers[provider]["response_times"] = self.providers[provider]["response_times"][-100:]
            
            if not success:
                self.providers[provider]["errors"] += 1
                
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get comprehensive provider statistics"""
        stats = {}
        for provider, data in self.providers.items():
            error_rate = data["errors"] / max(data["requests"], 1)
            avg_response_time = sum(data["response_times"][-10:]) / max(len(data["response_times"][-10:]), 1)
            
            stats[provider] = {
                **data,
                "error_rate": error_rate,
                "avg_response_time": avg_response_time,
                "availability_score": (1 - error_rate) * (1 / max(avg_response_time, 0.1))
            }
        return stats
    
    def get_cost_optimal_provider(self) -> str:
        """Get provider with best cost efficiency"""
        min_cost = float('inf')
        optimal_provider = "anthropic"
        
        for provider, data in self.providers.items():
            if data["requests"] > 0:
                cost_per_request = data["cost"] / data["requests"]
                if cost_per_request < min_cost:
                    min_cost = cost_per_request
                    optimal_provider = provider
        
        return optimal_provider

class EnhancedRealAgent:
    """Enhanced real agent with Claude + Gemini specialization"""
    
    def __init__(self, agent_id: str, name: str, agent_type: AgentType, load_balancer: ProviderLoadBalancer = None):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.load_balancer = load_balancer or ProviderLoadBalancer()
        self.current_task: Optional[Task] = None
        self.status = "standby"
        self.created_at = datetime.now(timezone.utc)
        self.tasks_completed = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.learned_lessons = []
        self.provider_clients = {}
        self.provider_preferences = {}
        
        # Initialize LLM clients (Claude + Gemini only)
        self._init_all_llm_clients()
        self._setup_agent_specialization()
    
    def _init_all_llm_clients(self):
        """Initialize Claude and Gemini clients only"""
        # Initialize Anthropic (Claude)
        try:
            if os.getenv("ANTHROPIC_API_KEY"):
                self.provider_clients["anthropic"] = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                logger.info(f"Claude client initialized for {self.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize Claude client for {self.name}: {e}")
            
        # Initialize Gemini
        try:
            if os.getenv("GOOGLE_API_KEY"):
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                self.provider_clients["gemini"] = genai.GenerativeModel('gemini-1.5-pro')
                logger.info(f"Gemini client initialized for {self.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client for {self.name}: {e}")
            
        if not self.provider_clients:
            logger.error(f"No LLM clients could be initialized for {self.name}")
    
    def _setup_agent_specialization(self):
        """Setup provider preferences based on agent type"""
        # Define agent-specific provider preferences
        preferences = {
            AgentType.CODE_DEVELOPER: {"anthropic": 0.7, "gemini": 0.3},
            AgentType.SYSTEM_ANALYST: {"anthropic": 0.4, "gemini": 0.6},
            AgentType.CONTENT_PROCESSOR: {"anthropic": 0.5, "gemini": 0.5},
            AgentType.DATABASE_SPECIALIST: {"anthropic": 0.6, "gemini": 0.4},
            AgentType.API_INTEGRATOR: {"anthropic": 0.7, "gemini": 0.3},
            AgentType.ERROR_DIAGNOSTICIAN: {"anthropic": 0.8, "gemini": 0.2},
            AgentType.TEMPLATE_FIXER: {"anthropic": 0.6, "gemini": 0.4},
            AgentType.WEB_TESTER: {"anthropic": 0.5, "gemini": 0.5}
        }
        
        self.provider_preferences = preferences.get(self.agent_type, {"anthropic": 0.5, "gemini": 0.5})
    
    def get_preferred_provider_for_task(self, task_type: str) -> str:
        """Get preferred provider based on task type and learning"""
        # Task-specific preferences
        task_preferences = {
            "code_generation": "anthropic",
            "data_analysis": "gemini",
            "text_processing": "gemini",
            "debugging": "anthropic",
            "optimization": "anthropic",
            "research": "gemini"
        }
        
        # Check learned preferences first
        for lesson in self.learned_lessons:
            if lesson.get("task_type") == task_type and lesson.get("success"):
                return lesson.get("provider_used", "anthropic")
        
        # Use task-specific or agent-specific preferences
        if task_type in task_preferences:
            return task_preferences[task_type]
        
        # Use agent-specific preference
        return max(self.provider_preferences, key=self.provider_preferences.get)
    
    def learn_from_task(self, lesson: Dict[str, Any]):
        """Learn from task execution outcomes"""
        lesson["timestamp"] = datetime.now().isoformat()
        self.learned_lessons.append(lesson)
        
        # Keep only recent lessons (last 100)
        if len(self.learned_lessons) > 100:
            self.learned_lessons = self.learned_lessons[-100:]
        
        logger.info(f"{self.name} learned: {lesson.get('lesson', 'New insight')}")
    
    def estimate_tokens(self, provider: str, prompt: str) -> int:
        """Estimate token usage for a prompt"""
        # Rough estimation: ~4 characters per token
        base_tokens = len(prompt) // 4
        
        # Provider-specific adjustments
        if provider == "anthropic":
            return int(base_tokens * 1.1)  # Claude uses slightly more tokens
        elif provider == "gemini":
            return int(base_tokens * 0.9)   # Gemini typically uses fewer tokens
        
        return base_tokens
    
    def track_response_time(self, provider: str, response_time: float):
        """Track response times for performance optimization"""
        self.load_balancer.record_request(provider, True, 0.0, response_time)
    
    def get_fastest_provider(self) -> str:
        """Get the fastest responding provider"""
        stats = self.load_balancer.get_provider_stats()
        
        fastest_provider = "anthropic"
        min_response_time = float('inf')
        
        for provider, data in stats.items():
            if data["avg_response_time"] < min_response_time:
                min_response_time = data["avg_response_time"]
                fastest_provider = provider
        
        return fastest_provider
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute task with enhanced provider selection and learning"""
        start_time = time.time()
        self.current_task = task
        self.status = "working"
        
        try:
            # Determine optimal provider
            task_type = self._classify_task_type(task.description)
            preferred_provider = self.get_preferred_provider_for_task(task_type)
            
            # Fallback to load balancer if preferred provider unavailable
            if preferred_provider not in self.provider_clients:
                preferred_provider = self.load_balancer.get_next_provider()
            
            # Execute with primary provider
            try:
                result = await self._execute_with_provider(task, preferred_provider)
                execution_time = time.time() - start_time
                
                # Record success
                self.load_balancer.record_request(preferred_provider, True, result.get("cost", 0), execution_time)
                
                # Learn from successful execution
                self.learn_from_task({
                    "task_type": task_type,
                    "provider_used": preferred_provider,
                    "success": True,
                    "execution_time": execution_time,
                    "tokens_used": result.get("tokens_used", 0),
                    "lesson": f"{preferred_provider} worked well for {task_type} tasks"
                })
                
                return result
                
            except Exception as e:
                # Try fallback provider
                fallback_providers = [p for p in self.provider_clients.keys() if p != preferred_provider]
                
                for fallback_provider in fallback_providers:
                    try:
                        logger.warning(f"Retrying task {task.name} with {fallback_provider}")
                        result = await self._execute_with_provider(task, fallback_provider)
                        execution_time = time.time() - start_time
                        
                        # Record fallback success
                        self.load_balancer.record_request(fallback_provider, True, result.get("cost", 0), execution_time)
                        
                        return result
                    except Exception as fallback_error:
                        logger.error(f"Fallback provider {fallback_provider} also failed: {fallback_error}")
                        continue
                
                # All providers failed
                raise e
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"Task execution failed for {self.name}: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time,
                "agent": self.name,
                "task_id": task.id
            }
        finally:
            self.current_task = None
            self.status = "standby"
    
    def _classify_task_type(self, description: str) -> str:
        """Classify task type based on description"""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["code", "function", "class", "implement", "programming"]):
            return "code_generation"
        elif any(keyword in description_lower for keyword in ["analyze", "analysis", "data", "metrics"]):
            return "data_analysis"
        elif any(keyword in description_lower for keyword in ["process", "text", "content", "parse"]):
            return "text_processing"
        elif any(keyword in description_lower for keyword in ["debug", "error", "fix", "issue"]):
            return "debugging"
        elif any(keyword in description_lower for keyword in ["optimize", "improve", "performance"]):
            return "optimization"
        elif any(keyword in description_lower for keyword in ["research", "find", "search", "investigate"]):
            return "research"
        else:
            return "general"
    
    async def _execute_with_provider(self, task: Task, provider: str) -> Dict[str, Any]:
        """Execute task with specific provider"""
        if provider not in self.provider_clients:
            raise ValueError(f"Provider {provider} not available")
        
        # Estimate tokens
        estimated_tokens = self.estimate_tokens(provider, task.description)
        
        # Execute with provider
        if provider == "anthropic":
            return await self._execute_with_claude(task, estimated_tokens)
        elif provider == "gemini":
            return await self._execute_with_gemini(task, estimated_tokens)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _execute_with_claude(self, task: Task, estimated_tokens: int) -> Dict[str, Any]:
        """Execute task with Claude (Anthropic)"""
        client = self.provider_clients["anthropic"]
        
        try:
            response = client.messages.create(
                model="claude-3-sonnet-20241022",
                max_tokens=4000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": f"""
You are {self.name}, a {self.agent_type.value.replace('_', ' ').title()}.

Task: {task.name}
Description: {task.description}

Please provide a comprehensive solution with:
1. Clear reasoning
2. Implementation details
3. Any code or files needed
4. Verification steps

Focus on delivering high-quality, production-ready results.
"""
                    }
                ]
            )
            
            result_text = response.content[0].text
            tokens_used = estimated_tokens  # Claude doesn't provide exact token count
            cost = self._estimate_cost("anthropic", tokens_used)
            
            self.tasks_completed += 1
            self.total_tokens_used += tokens_used
            self.total_cost += cost
            
            return {
                "success": True,
                "result": result_text,
                "provider": "anthropic",
                "tokens_used": tokens_used,
                "cost": cost,
                "agent": self.name,
                "task_id": task.id
            }
            
        except Exception as e:
            raise Exception(f"Claude execution error: {str(e)}")
    
    async def _execute_with_gemini(self, task: Task, estimated_tokens: int) -> Dict[str, Any]:
        """Execute task with Gemini"""
        model = self.provider_clients["gemini"]
        
        try:
            prompt = f"""
You are {self.name}, a {self.agent_type.value.replace('_', ' ').title()}.

Task: {task.name}
Description: {task.description}

Please provide a comprehensive solution with:
1. Clear reasoning
2. Implementation details  
3. Any code or files needed
4. Verification steps

Focus on delivering high-quality, production-ready results.
"""
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=4000
                )
            )
            
            result_text = response.text
            tokens_used = estimated_tokens
            cost = self._estimate_cost("gemini", tokens_used)
            
            self.tasks_completed += 1
            self.total_tokens_used += tokens_used
            self.total_cost += cost
            
            return {
                "success": True,
                "result": result_text,
                "provider": "gemini",
                "tokens_used": tokens_used,
                "cost": cost,
                "agent": self.name,
                "task_id": task.id
            }
            
        except Exception as e:
            raise Exception(f"Gemini execution error: {str(e)}")
    
    def _estimate_cost(self, provider: str, tokens: int) -> float:
        """Estimate cost based on provider and tokens"""
        # Rough cost estimates (per 1000 tokens)
        costs = {
            "anthropic": 0.01,  # Claude Sonnet
            "gemini": 0.0005    # Gemini 1.5 Pro
        }
        
        return (tokens / 1000) * costs.get(provider, 0.01)

class EnhancedRealAgentOrchestrator:
    """Enhanced orchestrator with advanced multi-agent coordination"""
    
    def __init__(self):
        self.agents: Dict[str, EnhancedRealAgent] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.load_balancer = ProviderLoadBalancer()
        self.db_path = "enhanced_orchestrator.db"
        
        # Initialize database
        self._init_database()
        
        # Create enhanced agent team
        self._create_enhanced_agents()
        
        logger.info("Enhanced Real Agent Orchestrator initialized with Claude + Gemini optimization")
    
    def _init_database(self):
        """Initialize enhanced database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enhanced tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enhanced_tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    agent_type TEXT,
                    priority INTEGER,
                    status TEXT,
                    assigned_agent TEXT,
                    result TEXT,
                    error TEXT,
                    created_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    progress INTEGER,
                    tokens_used INTEGER,
                    cost REAL,
                    provider_used TEXT,
                    execution_time REAL,
                    metadata TEXT
                )
            ''')
            
            # Agent performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    agent_type TEXT,
                    task_id TEXT,
                    provider_used TEXT,
                    execution_time REAL,
                    tokens_used INTEGER,
                    cost REAL,
                    success BOOLEAN,
                    timestamp TEXT
                )
            ''')
            
            # Learning system table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_system (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    task_type TEXT,
                    provider_used TEXT,
                    success BOOLEAN,
                    execution_time REAL,
                    tokens_used INTEGER,
                    lesson TEXT,
                    timestamp TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Enhanced database schema initialized")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def _create_enhanced_agents(self):
        """Create enhanced agent team with specializations"""
        agent_configs = [
            ("senior_code_dev", "Senior Code Developer", AgentType.CODE_DEVELOPER),
            ("system_analyst", "System Analyst", AgentType.SYSTEM_ANALYST),
            ("api_specialist", "API Integration Specialist", AgentType.API_INTEGRATOR),
            ("db_specialist", "Database Specialist", AgentType.DATABASE_SPECIALIST),
            ("content_processor", "Content Processor", AgentType.CONTENT_PROCESSOR),
            ("error_diagnostician", "Error Diagnostician", AgentType.ERROR_DIAGNOSTICIAN),
            ("template_fixer", "Template Fixer", AgentType.TEMPLATE_FIXER),
            ("web_tester", "Web Tester", AgentType.WEB_TESTER)
        ]
        
        for agent_id, name, agent_type in agent_configs:
            agent = EnhancedRealAgent(agent_id, name, agent_type, self.load_balancer)
            self.agents[agent_id] = agent
            logger.info(f"Created enhanced agent: {name} ({agent_type.value})")
    
    def add_task(self, name: str, description: str, agent_type: AgentType, priority: TaskPriority) -> str:
        """Add task to queue with enhanced tracking"""
        task_id = f"task_{int(time.time() * 1000)}"
        task = Task(
            id=task_id,
            name=name,
            description=description,
            agent_type=agent_type,
            priority=priority
        )
        
        self.task_queue.append(task)
        
        # Store in database
        self._store_task_in_db(task)
        
        logger.info(f"Added enhanced task: {name} (Priority: {priority.name})")
        return task_id
    
    def get_optimal_agent_for_task(self, task: Task) -> EnhancedRealAgent:
        """Get optimal agent for task based on specialization and performance"""
        # Filter agents by type
        suitable_agents = [agent for agent in self.agents.values() 
                          if agent.agent_type == task.agent_type]
        
        if not suitable_agents:
            # Fallback to any available agent
            suitable_agents = list(self.agents.values())
        
        if not suitable_agents:
            raise ValueError("No agents available")
        
        # Select best agent based on performance metrics
        best_agent = min(suitable_agents, key=lambda a: (
            a.total_cost / max(a.tasks_completed, 1),  # Cost efficiency
            len([l for l in a.learned_lessons if not l.get("success", True)])  # Error rate
        ))
        
        return best_agent
    
    def decompose_complex_task(self, task: Task) -> List[Task]:
        """Decompose complex task into subtasks"""
        subtasks = []
        task_description = task.description.lower()
        
        # Analyze task complexity and create subtasks
        if "build" in task_description and "test" in task_description:
            # Development + Testing task
            subtasks.extend([
                Task(
                    id=f"{task.id}_dev",
                    name=f"Development: {task.name}",
                    description=f"Implement core functionality: {task.description}",
                    agent_type=AgentType.CODE_DEVELOPER,
                    priority=task.priority
                ),
                Task(
                    id=f"{task.id}_test",
                    name=f"Testing: {task.name}",
                    description=f"Create and run tests for: {task.description}",
                    agent_type=AgentType.WEB_TESTER,
                    priority=task.priority
                )
            ])
        
        elif "api" in task_description:
            # API-related task
            subtasks.extend([
                Task(
                    id=f"{task.id}_design",
                    name=f"API Design: {task.name}",
                    description=f"Design API structure: {task.description}",
                    agent_type=AgentType.SYSTEM_ANALYST,
                    priority=task.priority
                ),
                Task(
                    id=f"{task.id}_implement",
                    name=f"API Implementation: {task.name}",
                    description=f"Implement API endpoints: {task.description}",
                    agent_type=AgentType.API_INTEGRATOR,
                    priority=task.priority
                )
            ])
        
        return subtasks if subtasks else [task]
    
    async def execute_tasks_parallel(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """Execute multiple tasks in parallel"""
        async def execute_single_task(task):
            agent = self.get_optimal_agent_for_task(task)
            return await agent.execute_task(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*[execute_single_task(task) for task in tasks], 
                                     return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "task_id": tasks[i].id
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def scale_agents_for_load(self, high_load: bool = False):
        """Dynamically scale agent pool based on load"""
        if high_load:
            # Create additional specialized agents
            additional_agents = [
                ("code_dev_2", "Senior Code Developer 2", AgentType.CODE_DEVELOPER),
                ("analyst_2", "System Analyst 2", AgentType.SYSTEM_ANALYST),
            ]
            
            for agent_id, name, agent_type in additional_agents:
                if agent_id not in self.agents:
                    agent = EnhancedRealAgent(agent_id, name, agent_type, self.load_balancer)
                    self.agents[agent_id] = agent
                    logger.info(f"Scaled up: Added {name}")
    
    def route_task_intelligently(self, task: Task) -> EnhancedRealAgent:
        """Intelligent task routing based on agent capabilities and current load"""
        # Get suitable agents
        suitable_agents = [agent for agent in self.agents.values() 
                          if agent.agent_type == task.agent_type and agent.status == "standby"]
        
        if not suitable_agents:
            # Get any available agent of the right type
            suitable_agents = [agent for agent in self.agents.values() 
                              if agent.agent_type == task.agent_type]
        
        if not suitable_agents:
            raise ValueError(f"No suitable agents found for {task.agent_type}")
        
        # Route to best agent based on multiple factors
        best_agent = min(suitable_agents, key=lambda a: (
            0 if a.status == "standby" else 1,  # Prefer available agents
            a.total_cost / max(a.tasks_completed, 1),  # Cost efficiency
            len(a.learned_lessons)  # Experience (more lessons = more experienced)
        ))
        
        return best_agent
    
    def learn_from_task_outcome(self, task_result: Dict[str, Any]):
        """Learn from task execution outcomes"""
        try:
            # Store learning data
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO learning_system 
                (agent_id, task_type, provider_used, success, execution_time, tokens_used, lesson, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_result.get("agent_id", "unknown"),
                task_result.get("task_type", "general"),
                task_result.get("provider_used", "unknown"),
                task_result.get("success", False),
                task_result.get("execution_time", 0.0),
                task_result.get("tokens_used", 0),
                f"Task quality score: {task_result.get('quality_score', 0)}",
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Learned from task outcome: {task_result.get('task_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Learning system error: {e}")
    
    def get_learned_lessons(self) -> List[Dict[str, Any]]:
        """Get all learned lessons from the system"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM learning_system ORDER BY timestamp DESC LIMIT 100')
            lessons = []
            
            for row in cursor.fetchall():
                lessons.append({
                    "id": row[0],
                    "agent_id": row[1],
                    "task_type": row[2],
                    "provider_used": row[3],
                    "success": bool(row[4]),
                    "execution_time": row[5],
                    "tokens_used": row[6],
                    "lesson": row[7],
                    "timestamp": row[8]
                })
            
            conn.close()
            return lessons
            
        except Exception as e:
            logger.error(f"Error retrieving lessons: {e}")
            return []
    
    def _store_task_in_db(self, task: Task):
        """Store task in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO enhanced_tasks VALUES 
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id, task.name, task.description, task.agent_type.value,
                task.priority.value, task.status.value, task.assigned_agent,
                task.result, task.error, 
                task.created_at.isoformat() if task.created_at else None,
                task.started_at.isoformat() if task.started_at else None,
                task.completed_at.isoformat() if task.completed_at else None,
                task.progress, task.tokens_used, task.cost, None, None,
                json.dumps(task.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database storage error: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        agent_stats = {}
        total_tokens = 0
        total_cost = 0.0
        
        for agent_id, agent in self.agents.items():
            agent_stats[agent_id] = {
                "name": agent.name,
                "type": agent.agent_type.value,
                "status": agent.status,
                "tasks_completed": agent.tasks_completed,
                "total_tokens": agent.total_tokens_used,
                "total_cost": agent.total_cost,
                "provider_preferences": agent.provider_preferences,
                "lessons_learned": len(agent.learned_lessons)
            }
            total_tokens += agent.total_tokens_used
            total_cost += agent.total_cost
        
        return {
            "total_agents": len(self.agents),
            "active_agents": len([a for a in self.agents.values() if a.status != "standby"]),
            "pending_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "total_tokens_used": total_tokens,
            "total_cost": total_cost,
            "provider_stats": self.load_balancer.get_provider_stats(),
            "agent_details": agent_stats,
            "learning_system_entries": len(self.get_learned_lessons())
        }

# Initialize enhanced orchestrator
enhanced_orchestrator = EnhancedRealAgentOrchestrator()

if __name__ == "__main__":
    print("🚀 Enhanced Real Agent Orchestrator - Claude + Gemini Optimized")
    print(f"✅ {len(enhanced_orchestrator.agents)} agents initialized")
    print("🎯 Ready for advanced multi-agent coordination")
    
    # Example usage
    import asyncio
    
    async def demo():
        # Add test task
        task_id = enhanced_orchestrator.add_task(
            "Demo Task",
            "Create a simple Python function to calculate fibonacci numbers",
            AgentType.CODE_DEVELOPER,
            TaskPriority.HIGH
        )
        
        # Get optimal agent and execute
        task = enhanced_orchestrator.task_queue[-1]
        agent = enhanced_orchestrator.get_optimal_agent_for_task(task)
        
        print(f"🎯 Executing demo task with {agent.name}")
        result = await agent.execute_task(task)
        
        print(f"✅ Demo completed: {result.get('success', False)}")
        print(f"💰 Cost: ${result.get('cost', 0):.4f}")
        print(f"🔤 Tokens: {result.get('tokens_used', 0)}")
    
    # Run demo if script is executed directly
    # asyncio.run(demo())