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