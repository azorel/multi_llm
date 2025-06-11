#!/usr/bin/env python3
"""
Multi-Agent Orchestrator System
===============================

Based on Disler patterns for real-time agent coordination and task distribution.
This is the live orchestration engine that coordinates specialized agents.
"""

import asyncio
import json
import time
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import logging
import sys
import os

# Standalone orchestrator - no external dependencies

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    ACTIVE = "active"
    STANDBY = "standby"
    QUEUED = "queued"
    ERROR = "error"
    COMPLETED = "completed"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Task:
    id: str
    name: str
    description: str
    agent_type: str
    priority: TaskPriority
    status: AgentStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    result: Optional[str] = None
    error: Optional[str] = None
    estimated_duration: Optional[int] = None
    tokens_used: int = 0
    cost: float = 0.0

@dataclass
class Agent:
    id: str
    name: str
    type: str
    capabilities: List[str]
    status: AgentStatus
    current_task: Optional[Task] = None
    total_tasks: int = 0
    success_rate: float = 100.0
    avg_response_time: float = 0.0
    last_active: Optional[datetime] = None
    health_score: float = 100.0

class AgentOrchestrator:
    """Real-time multi-agent orchestration system based on Disler patterns."""
    
    def __init__(self, db_path: str = "agent_orchestrator.db"):
        self.db_path = db_path
        self.agents: Dict[str, Agent] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.running = False
        self.orchestrator_thread = None
        self.user_messages: List[Dict] = []
        self.init_database()
        self.register_default_agents()
        self.populate_default_prompts()
        
    def init_database(self):
        """Initialize SQLite database for persistence."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                agent_type TEXT,
                priority TEXT,
                status TEXT,
                created_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                progress INTEGER DEFAULT 0,
                result TEXT,
                error TEXT,
                estimated_duration INTEGER,
                tokens_used INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0
            )
        ''')
        
        # User messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_messages (
                id TEXT PRIMARY KEY,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Prompt library table for storing and versioning prompts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_library (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                prompt_text TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                success_rate REAL DEFAULT 0.0,
                total_uses INTEGER DEFAULT 0,
                successful_uses INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                agent_type TEXT,
                description TEXT,
                tags TEXT
            )
        ''')
        
        # Multi-LLM test results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS llm_test_results (
                id TEXT PRIMARY KEY,
                prompt_id TEXT,
                llm_provider TEXT,
                model_name TEXT,
                input_prompt TEXT,
                response_text TEXT,
                response_quality INTEGER DEFAULT 0,
                response_time_ms INTEGER,
                tokens_used INTEGER,
                cost REAL,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                test_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prompt_id) REFERENCES prompt_library (id)
            )
        ''')
        
        # Agent deployment coordination table (for infinite loop patterns)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_deployments (
                id TEXT PRIMARY KEY,
                deployment_name TEXT NOT NULL,
                specification TEXT,
                target_iterations INTEGER DEFAULT 1,
                current_iteration INTEGER DEFAULT 0,
                agents_deployed INTEGER DEFAULT 0,
                status TEXT DEFAULT 'planned',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                success_rate REAL DEFAULT 0.0
            )
        ''')
        
        # System metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                timestamp TIMESTAMP PRIMARY KEY,
                active_agents INTEGER,
                queued_tasks INTEGER,
                completed_tasks INTEGER,
                success_rate REAL,
                avg_response_time REAL,
                total_cost REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def register_default_agents(self):
        """Register the specialized agents based on Disler patterns."""
        agents_config = [
            {
                'id': 'research_agent',
                'name': 'Research Specialist',
                'type': 'SFA',
                'capabilities': ['web_search', 'document_analysis', 'summarization', 'data_extraction']
            },
            {
                'id': 'code_agent', 
                'name': 'Code Specialist',
                'type': 'SFA',
                'capabilities': ['code_generation', 'refactoring', 'testing', 'debugging', 'documentation']
            },
            {
                'id': 'monitoring_agent',
                'name': 'Monitoring Specialist', 
                'type': 'Pipeline',
                'capabilities': ['system_monitoring', 'log_analysis', 'alerting', 'performance_tracking']
            },
            {
                'id': 'database_agent',
                'name': 'Database Specialist',
                'type': 'Tool', 
                'capabilities': ['data_management', 'schema_updates', 'optimization', 'backup']
            },
            {
                'id': 'content_agent',
                'name': 'Content Processor',
                'type': 'SFA',
                'capabilities': ['content_analysis', 'extraction', 'categorization', 'transcription']
            },
            {
                'id': 'workflow_agent',
                'name': 'Workflow Manager',
                'type': 'Orchestrator', 
                'capabilities': ['task_scheduling', 'dependency_management', 'coordination', 'automation']
            }
        ]
        
        for config in agents_config:
            agent = Agent(
                id=config['id'],
                name=config['name'],
                type=config['type'],
                capabilities=config['capabilities'],
                status=AgentStatus.STANDBY,
                health_score=100.0,
                success_rate=100.0
            )
            self.agents[agent.id] = agent
    
    def populate_default_prompts(self):
        """Populate the prompt library with useful default prompts."""
        default_prompts = [
            {
                'name': 'Code Review',
                'category': 'Development',
                'prompt_text': 'Review this code for bugs, security issues, and best practices. Provide specific recommendations for improvement.',
                'agent_type': 'code',
                'description': 'Comprehensive code review prompt',
                'tags': 'review,security,best-practices'
            },
            {
                'name': 'Research Summary',
                'category': 'Research',
                'prompt_text': 'Research [TOPIC] and provide a comprehensive summary including key findings, sources, and actionable insights.',
                'agent_type': 'research',
                'description': 'Template for research tasks',
                'tags': 'research,summary,analysis'
            },
            {
                'name': 'UI Component Creation',
                'category': 'Development',
                'prompt_text': 'Create a themed UI component that combines [FUNCTIONALITY] with [THEME] design language. Include HTML, CSS, and JavaScript.',
                'agent_type': 'code',
                'description': 'Disler-style UI component generation',
                'tags': 'ui,component,theme,disler'
            },
            {
                'name': 'Multi-Agent Coordination',
                'category': 'Orchestration',
                'prompt_text': 'Coordinate multiple specialized agents to work on [TASK]. Break down into subtasks and assign appropriate agent types.',
                'agent_type': 'workflow',
                'description': 'Orchestrator coordination prompt',
                'tags': 'orchestration,coordination,multi-agent'
            },
            {
                'name': 'Content Processing',
                'category': 'Content',
                'prompt_text': 'Process and analyze this content for key insights, categorize by importance, and extract actionable items.',
                'agent_type': 'content',
                'description': 'Content analysis and processing',
                'tags': 'content,analysis,processing'
            },
            {
                'name': 'System Monitoring',
                'category': 'Operations',
                'prompt_text': 'Monitor system health, identify potential issues, and recommend preventive actions based on current metrics.',
                'agent_type': 'monitoring',
                'description': 'System health monitoring',
                'tags': 'monitoring,health,operations'
            }
        ]
        
        # Check if prompts already exist
        existing_prompts = self.search_prompts()
        existing_names = {p['name'] for p in existing_prompts}
        
        for prompt_data in default_prompts:
            if prompt_data['name'] not in existing_names:
                self.add_prompt(**prompt_data)
                
        logger.info(f"Initialized prompt library with {len(default_prompts)} default prompts")
            
    def add_task(self, name: str, description: str, agent_type: str, 
                 priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        """Add a new task to the queue."""
        task = Task(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            agent_type=agent_type,
            priority=priority,
            status=AgentStatus.QUEUED,
            created_at=datetime.now()
        )
        
        # Insert into priority queue
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: (t.priority.value, t.created_at))
        
        # Persist to database
        self.save_task(task)
        
        logger.info(f"Added task {task.id}: {task.name}")
        return task.id
        
    def save_task(self, task: Task):
        """Save task to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.id, task.name, task.description, task.agent_type,
            task.priority.value, task.status.value,
            task.created_at, task.started_at, task.completed_at,
            task.progress, task.result, task.error,
            task.estimated_duration, task.tokens_used, task.cost
        ))
        
        conn.commit()
        conn.close()
        
    def find_available_agent(self, agent_type: str, capabilities: List[str] = None) -> Optional[Agent]:
        """Find an available agent that matches requirements."""
        for agent in self.agents.values():
            if (agent.type == agent_type or agent_type == 'any') and agent.status == AgentStatus.STANDBY:
                if capabilities:
                    if all(cap in agent.capabilities for cap in capabilities):
                        return agent
                else:
                    return agent
        return None
        
    def assign_task(self, task: Task, agent: Agent) -> bool:
        """Assign a task to an agent."""
        try:
            agent.current_task = task
            agent.status = AgentStatus.ACTIVE
            agent.last_active = datetime.now()
            
            task.status = AgentStatus.ACTIVE
            task.started_at = datetime.now()
            
            self.save_task(task)
            
            # Start task execution in background
            threading.Thread(target=self.execute_task, args=(task, agent), daemon=True).start()
            
            logger.info(f"Assigned task {task.id} to agent {agent.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to assign task {task.id} to agent {agent.id}: {e}")
            return False
            
    def execute_task(self, task: Task, agent: Agent):
        """Execute a task (this is where real agent work would happen)."""
        try:
            # Simulate task execution with real logic
            if task.agent_type == 'research':
                self.execute_research_task(task, agent)
            elif task.agent_type == 'code':
                self.execute_code_task(task, agent)
            elif task.agent_type == 'content':
                self.execute_content_task(task, agent)
            elif task.agent_type == 'monitoring':
                self.execute_monitoring_task(task, agent)
            elif task.agent_type == 'llm_test':
                self.execute_llm_test_task(task, agent)
            elif task.agent_type == 'parallel_executor':
                self.execute_parallel_task(task, agent)
            else:
                self.execute_generic_task(task, agent)
                
        except Exception as e:
            self.handle_task_error(task, agent, str(e))
            
    def execute_research_task(self, task: Task, agent: Agent):
        """Execute research-specific tasks."""
        # Real implementation would use web search, document analysis etc.
        import time
        import random
        
        # Simulate research work
        steps = [
            "Initializing research parameters",
            "Searching web sources", 
            "Analyzing documents",
            "Extracting key information",
            "Synthesizing findings",
            "Generating report"
        ]
        
        for i, step in enumerate(steps):
            time.sleep(2)  # Simulate work time
            task.progress = int((i + 1) / len(steps) * 100)
            self.save_task(task)
            logger.info(f"Research task {task.id}: {step} ({task.progress}%)")
            
        # Complete task
        task.result = f"Research completed: {task.description}. Found {random.randint(3, 15)} relevant sources."
        task.tokens_used = random.randint(800, 2000)
        task.cost = task.tokens_used * 0.00005
        self.complete_task(task, agent)
        
    def execute_code_task(self, task: Task, agent: Agent):
        """Execute code-specific tasks."""
        import time
        import random
        
        steps = [
            "Analyzing requirements",
            "Designing solution",
            "Writing code",
            "Testing implementation", 
            "Optimizing performance",
            "Generating documentation"
        ]
        
        for i, step in enumerate(steps):
            time.sleep(3)  # Code tasks take longer
            task.progress = int((i + 1) / len(steps) * 100)
            self.save_task(task)
            logger.info(f"Code task {task.id}: {step} ({task.progress}%)")
            
        task.result = f"Code task completed: {task.description}. Generated {random.randint(50, 300)} lines of code."
        task.tokens_used = random.randint(1200, 3000)
        task.cost = task.tokens_used * 0.00005
        self.complete_task(task, agent)
        
    def execute_content_task(self, task: Task, agent: Agent):
        """Execute content processing tasks."""
        import time
        import random
        
        steps = [
            "Loading content",
            "Preprocessing data",
            "Extracting features",
            "Analyzing content",
            "Categorizing information", 
            "Generating summary"
        ]
        
        for i, step in enumerate(steps):
            time.sleep(1.5)
            task.progress = int((i + 1) / len(steps) * 100)
            self.save_task(task)
            logger.info(f"Content task {task.id}: {step} ({task.progress}%)")
            
        task.result = f"Content processed: {task.description}. Analyzed {random.randint(5, 25)} items."
        task.tokens_used = random.randint(600, 1500)
        task.cost = task.tokens_used * 0.00005
        self.complete_task(task, agent)
        
    def execute_monitoring_task(self, task: Task, agent: Agent):
        """Execute monitoring tasks."""
        import time
        import random
        
        # Monitoring tasks are often continuous
        for i in range(10):
            time.sleep(1)
            task.progress = min(100, (i + 1) * 10)
            self.save_task(task)
            logger.info(f"Monitoring task {task.id}: Checking systems ({task.progress}%)")
            
        task.result = f"Monitoring completed: {task.description}. All systems healthy."
        task.tokens_used = random.randint(200, 800)
        task.cost = task.tokens_used * 0.00005
        self.complete_task(task, agent)
        
    def execute_generic_task(self, task: Task, agent: Agent):
        """Execute generic tasks."""
        import time
        import random
        
        # Simple generic execution
        for i in range(5):
            time.sleep(2)
            task.progress = int((i + 1) / 5 * 100)
            self.save_task(task)
            
        task.result = f"Task completed: {task.description}"
        task.tokens_used = random.randint(400, 1000)
        task.cost = task.tokens_used * 0.00005
        self.complete_task(task, agent)
    
    def execute_llm_test_task(self, task: Task, agent: Agent):
        """Execute LLM testing tasks."""
        import time
        import random
        
        # Simulate multi-LLM testing
        steps = [
            "Loading LLM configuration",
            "Sending prompt to API",
            "Receiving response", 
            "Analyzing response quality",
            "Recording metrics",
            "Comparing with other models"
        ]
        
        for i, step in enumerate(steps):
            time.sleep(1.5)  # LLM API calls take time
            task.progress = int((i + 1) / len(steps) * 100)
            self.save_task(task)
            logger.info(f"LLM test task {task.id}: {step} ({task.progress}%)")
            
        # Simulate recording test results
        response_quality = random.randint(6, 10)  # Rating out of 10
        response_time = random.randint(800, 3000)  # ms
        
        task.result = f"LLM test completed. Quality: {response_quality}/10, Response time: {response_time}ms"
        task.tokens_used = random.randint(500, 1500)
        task.cost = task.tokens_used * 0.00008  # Slightly higher cost for testing
        
        # Record the test result (simulated)
        self.record_llm_test_result(
            prompt_id="test_prompt",
            llm_provider="Simulated",
            model_name="test-model",
            input_prompt=task.description,
            response_text=f"Simulated response for: {task.description[:50]}...",
            response_time_ms=response_time,
            tokens_used=task.tokens_used,
            cost=task.cost,
            response_quality=response_quality
        )
        
        self.complete_task(task, agent)
    
    def execute_parallel_task(self, task: Task, agent: Agent):
        """Execute parallel agent tasks (Disler infinite pattern)."""
        import time
        import random
        
        # Simulate parallel execution with unique variations
        steps = [
            "Analyzing specification",
            "Generating unique approach",
            "Creating iteration variant",
            "Applying creative direction",
            "Validating output",
            "Preparing results"
        ]
        
        for i, step in enumerate(steps):
            time.sleep(random.uniform(1.0, 2.5))  # Variable timing for uniqueness
            task.progress = int((i + 1) / len(steps) * 100)
            self.save_task(task)
            logger.info(f"Parallel task {task.id}: {step} ({task.progress}%)")
            
        # Generate unique result based on iteration number
        iteration = random.randint(1, 10)
        task.result = f"Parallel iteration {iteration} completed with unique variant: {task.description[:50]}..."
        task.tokens_used = random.randint(1000, 2500)
        task.cost = task.tokens_used * 0.00005
        
        self.complete_task(task, agent)
        
    def complete_task(self, task: Task, agent: Agent):
        """Mark task as completed and free up agent."""
        task.status = AgentStatus.COMPLETED
        task.completed_at = datetime.now()
        task.progress = 100
        
        # Update agent stats
        agent.current_task = None
        agent.status = AgentStatus.STANDBY
        agent.total_tasks += 1
        
        # Calculate response time
        if task.started_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            agent.avg_response_time = (agent.avg_response_time * (agent.total_tasks - 1) + duration) / agent.total_tasks
            
        self.save_task(task)
        self.completed_tasks.append(task)
        
        # Remove from queue
        self.task_queue = [t for t in self.task_queue if t.id != task.id]
        
        logger.info(f"Completed task {task.id} with agent {agent.id}")
        
    def handle_task_error(self, task: Task, agent: Agent, error: str):
        """Handle task execution errors."""
        task.status = AgentStatus.ERROR
        task.error = error
        task.completed_at = datetime.now()
        
        agent.current_task = None
        agent.status = AgentStatus.STANDBY
        agent.health_score = max(0, agent.health_score - 10)
        
        self.save_task(task)
        logger.error(f"Task {task.id} failed: {error}")
        
    def process_user_message(self, message: str) -> str:
        """Process user message and generate response."""
        msg_id = str(uuid.uuid4())
        
        # Store message
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_messages (id, message) VALUES (?, ?)",
            (msg_id, message)
        )
        conn.commit()
        conn.close()
        
        # Process message and generate response
        response = self.generate_response(message)
        
        # Update with response
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_messages SET response = ?, status = 'completed' WHERE id = ?",
            (response, msg_id)
        )
        conn.commit()
        conn.close()
        
        return response
        
    def generate_response(self, message: str) -> str:
        """Generate intelligent response to user message."""
        message_lower = message.lower()
        
        # Task creation commands
        if any(word in message_lower for word in ['create', 'add', 'start', 'run']):
            if 'research' in message_lower:
                task_id = self.add_task(
                    name="User Research Request",
                    description=message,
                    agent_type='research',
                    priority=TaskPriority.HIGH
                )
                return f"✅ Created research task {task_id[:8]}... I'll have the Research Specialist handle this immediately."
                
            elif 'code' in message_lower or 'implement' in message_lower:
                task_id = self.add_task(
                    name="User Code Request", 
                    description=message,
                    agent_type='code',
                    priority=TaskPriority.HIGH
                )
                return f"✅ Created coding task {task_id[:8]}... The Code Specialist will implement this right away."
                
            elif 'content' in message_lower or 'process' in message_lower:
                task_id = self.add_task(
                    name="User Content Request",
                    description=message,
                    agent_type='content', 
                    priority=TaskPriority.HIGH
                )
                return f"✅ Created content task {task_id[:8]}... Content Processor will handle this immediately."
                
        # Status queries
        elif any(word in message_lower for word in ['status', 'how', 'what']):
            active_count = len([a for a in self.agents.values() if a.status == AgentStatus.ACTIVE])
            queue_count = len(self.task_queue)
            return f"🎯 System Status: {active_count} agents active, {queue_count} tasks queued. All systems operational!"
            
        # Agent queries
        elif 'agent' in message_lower:
            if 'stop' in message_lower or 'pause' in message_lower:
                return "⏸️ I can pause specific agents. Which agent would you like to pause? (research, code, content, monitoring, database, workflow)"
            else:
                agent_list = "\n".join([f"• {agent.name} ({agent.status.value})" for agent in self.agents.values()])
                return f"🤖 Current Agents:\n{agent_list}"
                
        # Generic response
        else:
            return f"💭 I understand you want: '{message}'. I can help with research, coding, content processing, monitoring, and more. Just tell me what you need!"
            
    def start_orchestration(self):
        """Start the orchestration loop."""
        self.running = True
        self.orchestrator_thread = threading.Thread(target=self.orchestration_loop, daemon=True)
        self.orchestrator_thread.start()
        logger.info("🎯 Orchestrator started - managing multi-agent system")
        
    def stop_orchestration(self):
        """Stop the orchestration loop."""
        self.running = False
        logger.info("🛑 Orchestrator stopped")
        
    def orchestration_loop(self):
        """Main orchestration loop that assigns tasks to agents."""
        while self.running:
            try:
                # Process task queue
                for task in self.task_queue[:]:  # Copy to avoid modification during iteration
                    if task.status == AgentStatus.QUEUED:
                        agent = self.find_available_agent(task.agent_type)
                        if agent:
                            self.assign_task(task, agent)
                            
                # Record metrics
                self.record_metrics()
                            
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Orchestration error: {e}")
                time.sleep(5)  # Wait longer on error
                
    def record_metrics(self):
        """Record system metrics to database."""
        try:
            active_agents = len([a for a in self.agents.values() if a.status == AgentStatus.ACTIVE])
            queued_tasks = len(self.task_queue)
            completed_tasks = len(self.completed_tasks)
            
            if completed_tasks > 0:
                success_rate = len([t for t in self.completed_tasks if t.status == AgentStatus.COMPLETED]) / completed_tasks * 100
                avg_response_time = sum([a.avg_response_time for a in self.agents.values()]) / len(self.agents)
                total_cost = sum([t.cost for t in self.completed_tasks])
            else:
                success_rate = 100.0
                avg_response_time = 0.0
                total_cost = 0.0
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO system_metrics 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                active_agents,
                queued_tasks, 
                completed_tasks,
                success_rate,
                avg_response_time,
                total_cost
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
    
    # === PROMPT LIBRARY MANAGEMENT ===
    def add_prompt(self, name: str, prompt_text: str, category: str = None, 
                   agent_type: str = None, description: str = None, tags: str = None) -> str:
        """Add a new prompt to the library."""
        prompt_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO prompt_library 
            (id, name, category, prompt_text, agent_type, description, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (prompt_id, name, category, prompt_text, agent_type, description, tags))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added prompt to library: {name} ({prompt_id})")
        return prompt_id
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        """Get a prompt from the library."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM prompt_library WHERE id = ?', (prompt_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def search_prompts(self, category: str = None, agent_type: str = None, 
                      tags: str = None, min_success_rate: float = None) -> List[Dict]:
        """Search prompts in the library."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM prompt_library WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        if agent_type:
            query += " AND agent_type = ?"
            params.append(agent_type)
        if tags:
            query += " AND tags LIKE ?"
            params.append(f"%{tags}%")
        if min_success_rate is not None:
            query += " AND success_rate >= ?"
            params.append(min_success_rate)
            
        query += " ORDER BY success_rate DESC, total_uses DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_prompt_success(self, prompt_id: str, success: bool):
        """Update prompt success rate based on usage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE prompt_library 
            SET total_uses = total_uses + 1,
                successful_uses = successful_uses + ?,
                success_rate = CAST(successful_uses AS REAL) / total_uses,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (1 if success else 0, prompt_id))
        
        conn.commit()
        conn.close()
    
    # === MULTI-LLM TESTING ===
    def test_prompt_across_llms(self, prompt_text: str, llm_configs: List[Dict]) -> str:
        """Test a prompt across multiple LLM providers."""
        test_id = str(uuid.uuid4())
        
        # Create a deployment for coordinated testing
        deployment_id = self.create_agent_deployment(
            f"LLM Test {test_id[:8]}", 
            f"Multi-LLM prompt testing: {prompt_text[:100]}...",
            len(llm_configs)
        )
        
        # Deploy test agents for each LLM
        for llm_config in llm_configs:
            task_id = self.add_task(
                name=f"LLM Test: {llm_config['provider']} {llm_config['model']}",
                description=f"Test prompt on {llm_config['provider']} {llm_config['model']}: {prompt_text}",
                agent_type='llm_test',
                priority=TaskPriority.HIGH
            )
            
            # Store test configuration for the task
            self.store_llm_test_config(task_id, prompt_text, llm_config)
        
        logger.info(f"Started multi-LLM test deployment {deployment_id} with {len(llm_configs)} providers")
        return deployment_id
    
    def store_llm_test_config(self, task_id: str, prompt_text: str, llm_config: Dict):
        """Store LLM test configuration for a task."""
        # In a real implementation, this would store the config for the task execution
        # For now, we'll simulate by logging
        logger.info(f"Task {task_id}: Testing {llm_config['provider']} {llm_config['model']}")
    
    def record_llm_test_result(self, prompt_id: str, llm_provider: str, model_name: str,
                              input_prompt: str, response_text: str, response_time_ms: int,
                              tokens_used: int = 0, cost: float = 0.0, success: bool = True,
                              response_quality: int = 0, error_message: str = None) -> str:
        """Record the result of an LLM test."""
        result_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO llm_test_results 
            (id, prompt_id, llm_provider, model_name, input_prompt, response_text,
             response_quality, response_time_ms, tokens_used, cost, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (result_id, prompt_id, llm_provider, model_name, input_prompt, response_text,
              response_quality, response_time_ms, tokens_used, cost, success, error_message))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded LLM test result: {llm_provider} {model_name} - Success: {success}")
        return result_id
    
    # === INFINITE AGENT DEPLOYMENT (Disler Pattern) ===
    def create_agent_deployment(self, name: str, specification: str, target_iterations: int = 5) -> str:
        """Create a new agent deployment for parallel execution."""
        deployment_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO agent_deployments 
            (id, deployment_name, specification, target_iterations, status)
            VALUES (?, ?, ?, ?, 'planned')
        ''', (deployment_id, name, specification, target_iterations))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created agent deployment: {name} ({deployment_id})")
        return deployment_id
    
    def deploy_parallel_agents(self, deployment_id: str, agent_count: int = 5) -> List[str]:
        """Deploy multiple agents in parallel for a specification (Disler infinite pattern)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get deployment details
        cursor.execute('SELECT * FROM agent_deployments WHERE id = ?', (deployment_id,))
        deployment = cursor.fetchone()
        
        if not deployment:
            conn.close()
            return []
        
        # Create parallel tasks
        task_ids = []
        for i in range(agent_count):
            task_id = self.add_task(
                name=f"Parallel Agent {i+1}: {deployment[1]}",
                description=f"Iteration {i+1} of parallel deployment: {deployment[2]}",
                agent_type='parallel_executor',
                priority=TaskPriority.HIGH
            )
            task_ids.append(task_id)
        
        # Update deployment status
        cursor.execute('''
            UPDATE agent_deployments 
            SET agents_deployed = ?, status = 'executing'
            WHERE id = ?
        ''', (agent_count, deployment_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Deployed {agent_count} parallel agents for deployment {deployment_id}")
        return task_ids
    
    def get_deployment_status(self, deployment_id: str) -> Dict:
        """Get status of an agent deployment."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM agent_deployments WHERE id = ?', (deployment_id,))
        deployment = cursor.fetchone()
        
        if deployment:
            # Get related tasks
            cursor.execute('''
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM tasks WHERE description LIKE ?
            ''', (f"%{deployment['deployment_name']}%",))
            
            task_stats = cursor.fetchone()
            
            result = dict(deployment)
            result['tasks_total'] = task_stats['total'] if task_stats else 0
            result['tasks_completed'] = task_stats['completed'] if task_stats else 0
            
            conn.close()
            return result
        
        conn.close()
        return {}
    
    # === ENHANCED RESPONSE GENERATION ===        
    def generate_response(self, message: str) -> str:
        """Generate intelligent response to user message with enhanced capabilities."""
        message_lower = message.lower()
        
        # Prompt library commands
        if 'prompt library' in message_lower or 'add prompt' in message_lower:
            if 'add' in message_lower:
                return "✨ I can help you add prompts to the library! Use: 'add prompt: [name] | [category] | [prompt text]' or I can extract prompts from successful conversations."
            else:
                prompts = self.search_prompts()
                prompt_count = len(prompts)
                return f"📚 Prompt Library: {prompt_count} prompts stored. Top performers: {', '.join([p['name'] for p in prompts[:3]])}"
        
        # Multi-LLM testing commands
        elif 'test llm' in message_lower or 'compare' in message_lower:
            if 'test' in message_lower:
                # Start a multi-LLM comparison
                test_prompt = message.replace('test llm', '').replace('test', '').strip()
                if test_prompt:
                    llm_configs = [
                        {'provider': 'OpenAI', 'model': 'gpt-4'},
                        {'provider': 'Anthropic', 'model': 'claude-3-sonnet'},
                        {'provider': 'Google', 'model': 'gemini-pro'}
                    ]
                    deployment_id = self.test_prompt_across_llms(test_prompt, llm_configs)
                    return f"🧪 Started multi-LLM test {deployment_id[:8]}... Testing across OpenAI, Anthropic, and Google models."
                else:
                    return "🧪 Multi-LLM Testing: Provide a prompt to test. Example: 'test llm: Write a Python function to calculate fibonacci'"
        
        # Infinite agent deployment (Disler pattern)
        elif 'deploy' in message_lower and ('parallel' in message_lower or 'infinite' in message_lower):
            if 'parallel' in message_lower:
                # Extract specification from message
                spec = message.replace('deploy parallel', '').replace('deploy', '').strip()
                if spec:
                    deployment_id = self.create_agent_deployment(
                        f"Parallel Deploy {datetime.now().strftime('%H:%M')}",
                        spec,
                        5  # Default 5 iterations
                    )
                    task_ids = self.deploy_parallel_agents(deployment_id, 5)
                    return f"🚀 Deployed 5 parallel agents for: '{spec[:50]}...' Deployment ID: {deployment_id[:8]}"
                else:
                    return "🚀 Parallel Deployment: Specify what you want agents to work on. Example: 'deploy parallel: create UI components with different themes'"
        
        # Deployment status queries
        elif 'deployment' in message_lower and 'status' in message_lower:
            # Get recent deployments
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, deployment_name, status, agents_deployed FROM agent_deployments ORDER BY created_at DESC LIMIT 3')
            deployments = cursor.fetchall()
            conn.close()
            
            if deployments:
                status_list = []
                for dep in deployments:
                    status_list.append(f"• {dep[1]} ({dep[0][:8]}): {dep[2]} - {dep[3]} agents")
                return f"📊 Recent Deployments:\n" + "\n".join(status_list)
            else:
                return "📊 No active deployments. Use 'deploy parallel: [specification]' to start."
        
        # Task creation commands
        elif any(word in message_lower for word in ['create', 'add', 'start', 'run']):
            if 'research' in message_lower:
                task_id = self.add_task(
                    name="User Research Request",
                    description=message,
                    agent_type='research',
                    priority=TaskPriority.HIGH
                )
                return f"✅ Created research task {task_id[:8]}... I'll have the Research Specialist handle this immediately."
                
            elif 'code' in message_lower or 'implement' in message_lower:
                task_id = self.add_task(
                    name="User Code Request", 
                    description=message,
                    agent_type='code',
                    priority=TaskPriority.HIGH
                )
                return f"✅ Created coding task {task_id[:8]}... The Code Specialist will implement this right away."
                
            elif 'content' in message_lower or 'process' in message_lower:
                task_id = self.add_task(
                    name="User Content Request",
                    description=message,
                    agent_type='content', 
                    priority=TaskPriority.HIGH
                )
                return f"✅ Created content task {task_id[:8]}... Content Processor will handle this immediately."
                
        # Status queries
        elif any(word in message_lower for word in ['status', 'how', 'what']):
            active_count = len([a for a in self.agents.values() if a.status == AgentStatus.ACTIVE])
            queue_count = len(self.task_queue)
            prompt_count = len(self.search_prompts())
            return f"🎯 System Status: {active_count} agents active, {queue_count} tasks queued, {prompt_count} prompts in library. All systems operational!"
            
        # Agent queries
        elif 'agent' in message_lower:
            if 'stop' in message_lower or 'pause' in message_lower:
                return "⏸️ I can pause specific agents. Which agent would you like to pause? (research, code, content, monitoring, database, workflow)"
            else:
                agent_list = "\n".join([f"• {agent.name} ({agent.status.value})" for agent in self.agents.values()])
                return f"🤖 Current Agents:\n{agent_list}"
                
        # Generic response
        else:
            return f"💭 I understand you want: '{message}'. I can help with research, coding, content processing, monitoring, prompt management, multi-LLM testing, and parallel agent deployment. What would you like to explore?"
            
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status for web dashboard."""
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'orchestrator': {
                'status': 'active' if self.running else 'stopped',
                'name': 'Claude Orchestrator',
                'role': 'Multi-Agent Coordinator',
                'tasks_completed': len(self.completed_tasks),
                'agents_managed': len(self.agents),
                'health': 'excellent' if self.running else 'stopped'
            },
            'active_agents': [
                {
                    'id': agent.id,
                    'name': agent.name,
                    'type': agent.type,
                    'status': agent.status.value,
                    'current_task': agent.current_task.name if agent.current_task else None,
                    'capabilities': agent.capabilities,
                    'progress': agent.current_task.progress if agent.current_task else 0,
                    'start_time': agent.current_task.started_at.strftime('%H:%M:%S') if agent.current_task and agent.current_task.started_at else None,
                    'tokens_used': agent.current_task.tokens_used if agent.current_task else 0,
                    'cost': agent.current_task.cost if agent.current_task else 0.0,
                    'total_tasks': agent.total_tasks,
                    'success_rate': agent.success_rate,
                    'health': agent.health_score
                }
                for agent in self.agents.values()
                if agent.status in [AgentStatus.ACTIVE, AgentStatus.STANDBY]
            ],
            'agent_queue': [
                {
                    'id': task.id,
                    'name': task.name,
                    'agent_type': task.agent_type,
                    'priority': task.priority.value,
                    'queue_position': i + 1,
                    'created_at': task.created_at.strftime('%H:%M:%S')
                }
                for i, task in enumerate(self.task_queue)
                if task.status == AgentStatus.QUEUED
            ],
            'completed_tasks': [
                {
                    'agent': next((a.name for a in self.agents.values() if a.id == task.agent_type), 'Unknown'),
                    'task': task.name,
                    'description': task.description,
                    'completed_at': task.completed_at.strftime('%H:%M:%S') if task.completed_at else '',
                    'duration': str(task.completed_at - task.started_at).split('.')[0] if task.completed_at and task.started_at else '',
                    'success': task.status == AgentStatus.COMPLETED,
                    'tokens': task.tokens_used,
                    'cost': task.cost
                }
                for task in self.completed_tasks[-10:]  # Last 10 tasks
            ],
            'system_metrics': {
                'total_agents': len(self.agents),
                'active_agents': len([a for a in self.agents.values() if a.status == AgentStatus.ACTIVE]),
                'queued_tasks': len(self.task_queue),
                'completed_today': len(self.completed_tasks),
                'success_rate': (len([t for t in self.completed_tasks if t.status == AgentStatus.COMPLETED]) / len(self.completed_tasks) * 100) if self.completed_tasks else 100.0,
                'avg_response_time': sum([a.avg_response_time for a in self.agents.values()]) / len(self.agents) if self.agents else 0.0
            }
        }

# Global orchestrator instance
orchestrator = AgentOrchestrator()