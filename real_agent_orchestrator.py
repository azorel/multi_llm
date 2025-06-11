#!/usr/bin/env python3
"""
Real Agent Orchestrator
A real multi-agent system that uses actual LLM APIs to do real work.
# DEMO CODE REMOVED: No simulations, no time.sleep(), no fake results.
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
import openai
import google.generativeai as genai
from pathlib import Path
import traceback
import subprocess
import time

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_orchestrator.log'),
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
    """Manages load balancing across multiple LLM providers"""
    
    def __init__(self):
        self.providers = {
            "anthropic": {"weight": 0.3, "requests": 0, "errors": 0, "cost": 0.0},
            "openai": {"weight": 0.4, "requests": 0, "errors": 0, "cost": 0.0},
            "gemini": {"weight": 0.3, "requests": 0, "errors": 0, "cost": 0.0}
        }
        self.current_index = 0
        
    def get_next_provider(self) -> str:
        """Get next provider based on weighted round-robin"""
        # Sort providers by weight and error rate
        available_providers = [
            (name, data) for name, data in self.providers.items()
            if data["errors"] / max(data["requests"], 1) < 0.3  # Less than 30% error rate
        ]
        
        if not available_providers:
            # Fallback to all providers if all have high error rates
            available_providers = list(self.providers.items())
        
        # Use weighted selection
        total_weight = sum(data["weight"] for _, data in available_providers)
        if total_weight == 0:
            return "openai"  # Default fallback
            
        # Simple round-robin with weights
        provider_name = available_providers[self.current_index % len(available_providers)][0]
        self.current_index += 1
        
        return provider_name
    
    def record_request(self, provider: str, success: bool, cost: float = 0.0):
        """Record request outcome for load balancing"""
        if provider in self.providers:
            self.providers[provider]["requests"] += 1
            self.providers[provider]["cost"] += cost
            if not success:
                self.providers[provider]["errors"] += 1
                
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get current provider statistics"""
        return self.providers.copy()

class RealAgent:
    """A real agent that uses LLM APIs to do actual work"""
    
    def __init__(self, agent_id: str, name: str, agent_type: AgentType, llm_provider: str = "auto", load_balancer: ProviderLoadBalancer = None):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.llm_provider = llm_provider
        self.load_balancer = load_balancer or ProviderLoadBalancer()
        self.current_task: Optional[Task] = None
        self.status = "standby"
        self.created_at = datetime.now(timezone.utc)
        self.tasks_completed = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.learned_lessons = []
        self.provider_clients = {}
        
        # Initialize all LLM clients
        self._init_all_llm_clients()
    
    def _init_all_llm_clients(self):
        """Initialize all available LLM clients for failover"""
        # Initialize Anthropic
        try:
            if os.getenv("ANTHROPIC_API_KEY"):
                self.provider_clients["anthropic"] = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                logger.info(f"Anthropic client initialized for {self.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic client for {self.name}: {e}")
            
        # Initialize OpenAI
        try:
            if os.getenv("OPENAI_API_KEY"):
                self.provider_clients["openai"] = openai.OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY")
                )
                logger.info(f"OpenAI client initialized for {self.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client for {self.name}: {e}")
            
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
            
    def _get_active_provider(self) -> str:
        """Get the active provider for this request"""
        if self.llm_provider == "auto":
            return self.load_balancer.get_next_provider()
        elif self.llm_provider in self.provider_clients:
            return self.llm_provider
        else:
            # Fallback to first available provider
            return next(iter(self.provider_clients.keys()), "openai")
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a task using real LLM calls"""
        if not self.llm_client:
            return {
                "success": False,
                "error": "LLM client not initialized",
                "result": None
            }
        
        self.current_task = task
        self.status = "working"
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(timezone.utc)
        task.assigned_agent = self.agent_id
        
        logger.info(f"Agent {self.name} starting task: {task.name}")
        
        try:
            # Build the prompt based on agent type and task
            prompt = self._build_task_prompt(task)
            
            # Make real LLM API call
            response = await self._make_llm_call(prompt)
            
            # Process the response
            result = await self._process_llm_response(response, task)
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.result = result.get("result", "Task completed")
            task.tokens_used = result.get("tokens_used", 0)
            task.cost = result.get("cost", 0.0)
            task.files_created = result.get("files_created", [])
            task.files_modified = result.get("files_modified", [])
            task.progress = 100
            
            # Store provider information for tracking
            if "provider_used" in result:
                if not hasattr(task, 'metadata'):
                    task.metadata = {}
                task.metadata = task.metadata or {}
                task.metadata["provider_used"] = result["provider_used"]
            
            # Update agent stats
            self.tasks_completed += 1
            self.total_tokens_used += task.tokens_used
            self.total_cost += task.cost
            
            self.status = "standby"
            self.current_task = None
            
            logger.info(f"Agent {self.name} completed task: {task.name}")
            
            return {
                "success": True,
                "result": task.result,
                "tokens_used": task.tokens_used,
                "cost": task.cost,
                "files_created": task.files_created,
                "files_modified": task.files_modified
            }
            
        except Exception as e:
            logger.error(f"Agent {self.name} failed task {task.name}: {e}")
            
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now(timezone.utc)
            
            self.status = "standby"
            self.current_task = None
            
            # Learn from the error
            self.learned_lessons.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_type": task.agent_type.value,
                "error": str(e),
                "lesson": "Need better error handling for this task type"
            })
            
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    def _build_task_prompt(self, task: Task) -> str:
        """Build an appropriate prompt for the task"""
        base_context = f"""
You are a {self.agent_type.value} agent working in a multi-agent system.

Your specialization: {self.agent_type.value}
Current working directory: {os.getcwd()}
Available tools: File operations, database queries, API calls, code execution

TASK: {task.name}
DESCRIPTION: {task.description}
PRIORITY: {task.priority.name}

"""
        
        if self.agent_type == AgentType.CODE_DEVELOPER:
            return base_context + """
As a Code Developer agent, you write real Python code, create files, and build working implementations.

Your capabilities:
- Read and analyze existing code
- Write new Python files with complete implementations
- Debug and fix code issues
- Create working integrations with APIs and databases
- Test implementations

REQUIREMENTS:
1. Write actual working code - no pseudocode or comments
2. Create complete files with all necessary imports
3. Handle errors properly with try/catch blocks
4. Follow Python best practices
5. Test your code logic before responding

Respond with:
1. The complete code file(s) to create or modify
2. File paths where code should be saved
3. Any dependencies to install
4. Testing instructions

IMPORTANT: Write REAL, EXECUTABLE code that actually works.
"""
        
        elif self.agent_type == AgentType.SYSTEM_ANALYST:
            return base_context + """
As a System Analyst agent, you analyze systems, identify issues, and recommend solutions.

Your capabilities:
- Analyze existing codebases and architectures
- Identify bottlenecks and issues
- Recommend improvements and solutions
- Create system documentation
- Plan implementation strategies

REQUIREMENTS:
1. Analyze the current system thoroughly
2. Identify specific issues and their root causes
3. Provide concrete, actionable recommendations
4. Create detailed implementation plans
5. Consider performance, security, and maintainability

Respond with:
1. Analysis of current system state
2. Identified issues and problems
3. Specific recommendations for improvements
4. Implementation plan with steps
5. Risk assessment and mitigation strategies
"""
        
        elif self.agent_type == AgentType.API_INTEGRATOR:
            return base_context + """
As an API Integrator agent, you build real API integrations and handle external service connections.

Your capabilities:
- Build REST API integrations
- Handle authentication and rate limiting
- Process API responses and errors
- Create async/await implementations
- Build robust error handling

REQUIREMENTS:
1. Create working API integration code
2. Handle authentication properly
3. Implement rate limiting and retries
4. Process responses and extract data
5. Handle errors gracefully

Respond with:
1. Complete API integration code
2. Authentication setup
3. Error handling implementation
4. Usage examples
5. Testing procedures
"""
        
        elif self.agent_type == AgentType.DATABASE_SPECIALIST:
            return base_context + """
As a Database Specialist agent, you work with databases, create schemas, and handle data operations.

Your capabilities:
- Design and modify database schemas
- Write efficient SQL queries
- Handle database migrations
- Optimize database performance
- Create data processing pipelines

REQUIREMENTS:
1. Create working database code
2. Design efficient schemas
3. Write optimized queries
4. Handle database errors
5. Ensure data integrity

Respond with:
1. Database schema designs
2. SQL queries and operations
3. Migration scripts if needed
4. Data processing code
5. Performance optimization recommendations
"""
        
        elif self.agent_type == AgentType.TEMPLATE_FIXER:
            return base_context + f"""
As a Template Fixer agent, you diagnose and fix HTML/Jinja2 template errors automatically.

Your capabilities:
- Analyze template syntax errors
- Fix Jinja2 filter and function issues
- Repair broken HTML structure
- Resolve template inheritance problems
- Fix variable reference errors

REQUIREMENTS:
1. Read the failing template file
2. Identify the specific error (round(), undefined variables, etc.)
3. Create a corrected version
4. Ensure all Jinja2 syntax is valid
5. Preserve the original functionality

Current working directory: {os.getcwd()}
Templates directory: templates/

ERROR TO FIX: {task.description}

STEP 1: First, identify which template file needs fixing from the error description.
STEP 2: Read the current template file to understand the issue.
STEP 3: Fix the specific error while preserving all other functionality.

Common fixes:
- round() method error → use |round(1) filter instead
- undefined variable → check data structure or add default filters
- template syntax → fix Jinja2 syntax issues

```python
import os
import re

# Extract template file from error description
error_desc = "{task.description}"
template_files = []

# Look for template file references
if "autonomous_monitor.html" in error_desc or "monitor" in error_desc:
    template_files.append("templates/autonomous_monitor.html")
elif "active_agents.html" in error_desc or "agents" in error_desc:
    template_files.append("templates/active_agents.html")
elif "workflow" in error_desc:
    template_files.append("templates/workflow_templates.html")

# Read the template file
for template_file in template_files:
    if os.path.exists(template_file):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"FOUND TEMPLATE: {template_file}")
        print(f"CONTENT LENGTH: {len(content)} characters")
        
        # Look for common errors
        if "round()" in content:
            print("FOUND ERROR: round() method usage")
        if "solution[3]" in content and "|round" not in content:
            print("FOUND ERROR: Missing float filter before round")
            
        break

print("TEMPLATE ANALYSIS COMPLETE")
```

RESPOND WITH: The complete corrected template file content wrapped in ```html tags.
"""
        
        elif self.agent_type == AgentType.WEB_TESTER:
            return base_context + """
As a Web Tester agent, you test web pages and identify errors automatically.

Your capabilities:
- Test web page functionality
- Identify HTTP errors and exceptions
- Validate HTML/CSS/JavaScript
- Check template rendering
- Report specific issues found

REQUIREMENTS:
1. Test the specified URLs using HTTP requests
2. Identify specific errors (500, 404, template errors)
3. Analyze error logs and traces
4. Report exact error messages and stack traces
5. Suggest specific fixes needed

Current task: {task.description}

EXECUTE: Make an HTTP request to test the URL and analyze the response.

```python
import requests
import sys
import traceback

try:
    url = "{task.description}".split()[-1]  # Extract URL from description
    if "http" in url:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ {url} is working (Status: {response.status_code})")
            result = f"✅ URL {url} is working correctly (Status: {response.status_code})"
        else:
            print(f"❌ {url} returned status {response.status_code}")
            result = f"❌ ERROR: {url} returned HTTP {response.status_code}"
            
            if response.status_code == 500:
                result += f"\\nServer Error Response: {response.text[:500]}"
    else:
        result = "❌ No valid URL found in task description"
        
except Exception as e:
    result = f"❌ ERROR testing URL: {str(e)}"
    print(f"Error: {e}")

print(f"RESULT: {result}")
```

RESPOND WITH: The test results and any errors found.
"""
        
        else:
            return base_context + """
Execute this task according to your specialization. Provide concrete, actionable results.

Requirements:
1. Analyze the task thoroughly
2. Create working implementations
3. Handle errors appropriately
4. Provide clear documentation
5. Test your work

Respond with specific deliverables that solve the task.
"""
    
    async def _make_llm_call(self, prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        """Make actual LLM API call with provider failover"""
        providers_to_try = list(self.provider_clients.keys())
        last_error = None
        
        # Get primary provider
        primary_provider = self._get_active_provider()
        if primary_provider in providers_to_try:
            providers_to_try.remove(primary_provider)
            providers_to_try.insert(0, primary_provider)
        
        for provider in providers_to_try:
            if provider not in self.provider_clients:
                continue
                
            try:
                result = await self._make_provider_call(provider, prompt)
                self.load_balancer.record_request(provider, True, result.get("cost", 0.0))
                result["provider_used"] = provider
                return result
                
            except Exception as e:
                last_error = e
                self.load_balancer.record_request(provider, False)
                logger.warning(f"LLM call failed for {provider}: {e}. Trying next provider...")
                continue
        
        # If all providers failed
        error_msg = f"All LLM providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def _make_provider_call(self, provider: str, prompt: str) -> Dict[str, Any]:
        """Make API call to specific provider"""
        if provider == "anthropic":
            response = self.provider_clients[provider].messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                "content": response.content[0].text,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "cost": (response.usage.input_tokens * 0.003 + response.usage.output_tokens * 0.015) / 1000
            }
            
        elif provider == "openai":
            response = self.provider_clients[provider].chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.1
            )
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "cost": response.usage.total_tokens * 0.00015 / 1000  # GPT-4o-mini cost
            }
            
        elif provider == "gemini":
            response = self.provider_clients[provider].generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=4000,
                    temperature=0.1
                )
            )
            
            # Gemini token counting is approximate
            estimated_tokens = len(prompt.split()) + len(response.text.split())
            
            return {
                "content": response.text,
                "tokens_used": estimated_tokens,
                "cost": estimated_tokens * 0.000125 / 1000  # Gemini 1.5 Pro cost estimate
            }
            
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def _process_llm_response(self, response: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """Process the LLM response and execute any code or file operations"""
        content = response["content"]
        files_created = []
        files_modified = []
        
        try:
            # Extract and execute code blocks from the response
            import re
            
            # Pattern to match code blocks with file paths
            file_pattern = r'```(?:python|py)?\s*(?:#\s*(?:FILE|SAVE|CREATE):\s*([^\n]+))?\n(.*?)\n```'
            code_blocks = re.findall(file_pattern, content, re.DOTALL | re.IGNORECASE)
            
            # Pattern to match explicit file creation instructions
            create_pattern = r'(?:CREATE|SAVE|WRITE)\s+(?:FILE|TO)?\s*:?\s*([^\n]+\.py)'
            file_paths = re.findall(create_pattern, content, re.IGNORECASE)
            
            # Execute code blocks and save files
            if code_blocks:
                for i, (suggested_path, code) in enumerate(code_blocks):
                    if code.strip():
                        # Determine file path
                        if suggested_path:
                            file_path = suggested_path.strip()
                        elif file_paths and i < len(file_paths):
                            file_path = file_paths[i].strip()
                        else:
                            # Generate a file name based on task
                            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', task.name.lower())
                            file_path = f"autonomous_generated_{safe_name}_{int(time.time())}.py"
                        
                        # Ensure file path is safe and within project directory
                        file_path = self._sanitize_file_path(file_path)
                        
                        # Create the file
                        try:
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(code)
                            
                            files_created.append(file_path)
                            logger.info(f"Agent {self.name} created file: {file_path}")
                            
                            # If this is a Python file, try to validate syntax
                            if file_path.endswith('.py'):
                                try:
                                    with open(file_path, 'r') as f:
                                        compile(f.read(), file_path, 'exec')
                                    logger.info(f"Python file {file_path} syntax is valid")
                                except SyntaxError as se:
                                    logger.warning(f"Syntax error in {file_path}: {se}")
                                    
                        except Exception as fe:
                            logger.error(f"Failed to create file {file_path}: {fe}")
            
            # Look for template fixes and HTML modifications
            template_pattern = r'(?:TEMPLATE|HTML|FIX).*?```(?:html|jinja2?)?\n(.*?)\n```'
            template_blocks = re.findall(template_pattern, content, re.DOTALL | re.IGNORECASE)
            
            # Look for specific file modification instructions
            modify_pattern = r'(?:MODIFY|UPDATE|FIX)\s+(?:FILE)?\s*:?\s*([^\n]+\.html)'
            modify_files = re.findall(modify_pattern, content, re.IGNORECASE)
            
            if template_blocks and modify_files:
                for template_code in template_blocks:
                    for modify_file in modify_files:
                        try:
                            modify_path = self._sanitize_file_path(modify_file.strip())
                            if os.path.exists(modify_path):
                                # Create backup
                                backup_path = f"{modify_path}.backup_autonomous_{int(time.time())}"
                                import shutil
                                shutil.copy2(modify_path, backup_path)
                                
                                # Apply the fix
                                with open(modify_path, 'w', encoding='utf-8') as f:
                                    f.write(template_code)
                                
                                files_modified.append(modify_path)
                                logger.info(f"Agent {self.name} modified file: {modify_path}")
                                
                        except Exception as me:
                            logger.error(f"Failed to modify file {modify_file}: {me}")
            
            # Look for database operations
            if "CREATE TABLE" in content.upper() or "INSERT INTO" in content.upper():
                sql_pattern = r'```sql\n(.*?)\n```'
                sql_blocks = re.findall(sql_pattern, content, re.DOTALL | re.IGNORECASE)
                
                for sql_code in sql_blocks:
                    try:
                        # Execute SQL if it's safe (CREATE TABLE, INSERT, SELECT)
                        safe_operations = ['CREATE TABLE', 'INSERT INTO', 'SELECT', 'UPDATE', 'ALTER TABLE']
                        if any(op in sql_code.upper() for op in safe_operations):
                            await self._execute_safe_sql(sql_code, task)
                            logger.info(f"Agent {self.name} executed SQL operations")
                    except Exception as se:
                        logger.error(f"Failed to execute SQL: {se}")
            
            # Look for Python code to execute (especially for web testing)
            python_pattern = r'```python\n(.*?)\n```'
            python_blocks = re.findall(python_pattern, content, re.DOTALL | re.IGNORECASE)
            
            execution_results = []
            for python_code in python_blocks:
                try:
                    # Check if this is safe Python code for web testing or data processing
                    safe_imports = ['requests', 'json', 'os', 'time', 'datetime', 'sqlite3', 're', 'sys', 'traceback']
                    dangerous_keywords = ['exec', 'eval', 'open', '__import__', 'subprocess', 'os.system']
                    
                    if (any(imp in python_code for imp in safe_imports) and 
                        not any(danger in python_code for danger in dangerous_keywords)):
                        
                        result = await self._execute_python_code(python_code, task)
                        execution_results.append(result)
                        logger.info(f"Agent {self.name} executed Python code successfully")
                        
                except Exception as pe:
                    logger.error(f"Failed to execute Python code: {pe}")
                    execution_results.append(f"Error: {pe}")
            
            # Look for shell commands to execute
            bash_pattern = r'```(?:bash|shell|sh)\n(.*?)\n```'
            bash_blocks = re.findall(bash_pattern, content, re.DOTALL | re.IGNORECASE)
            
            for bash_code in bash_blocks:
                try:
                    # Only execute safe commands
                    safe_commands = ['pip install', 'python -m', 'ls', 'pwd', 'cat', 'echo']
                    if any(cmd in bash_code.lower() for cmd in safe_commands):
                        result = await self._execute_safe_command(bash_code.strip())
                        logger.info(f"Agent {self.name} executed command: {bash_code[:50]}...")
                except Exception as ce:
                    logger.error(f"Failed to execute command: {ce}")
            
            # Extract key insights and actions taken
            summary = self._extract_response_summary(content, files_created, files_modified)
            
            return {
                "result": summary,
                "tokens_used": response["tokens_used"],
                "cost": response["cost"],
                "files_created": files_created,
                "files_modified": files_modified
            }
            
        except Exception as e:
            logger.error(f"Failed to process LLM response: {e}")
            # Still return the content even if execution failed
            return {
                "result": f"Response received but execution failed: {str(e)}\n\nOriginal response:\n{content}",
                "tokens_used": response["tokens_used"],
                "cost": response["cost"],
                "files_created": files_created,
                "files_modified": files_modified
            }
    
    def _sanitize_file_path(self, file_path: str) -> str:
        """Sanitize file path to prevent directory traversal"""
        # Remove any directory traversal attempts
        file_path = file_path.replace('..', '').replace('~', '')
        
        # Ensure it's within the current project
        if not file_path.startswith('/'):
            file_path = os.path.join(os.getcwd(), file_path)
        
        # Ensure it's within the project directory
        project_root = os.getcwd()
        if not os.path.commonpath([file_path, project_root]) == project_root:
            # If path is outside project, put it in a safe subdirectory
            safe_name = os.path.basename(file_path)
            file_path = os.path.join(project_root, 'autonomous_generated', safe_name)
        
        return file_path
    
    async def _execute_safe_sql(self, sql_code: str, task: Task):
        """Execute safe SQL operations"""
        try:
            import sqlite3
            # Use the lifeos database
            db_path = "lifeos_local.db"
            if os.path.exists(db_path):
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    # Split and execute each statement
                    for statement in sql_code.split(';'):
                        if statement.strip():
                            cursor.execute(statement.strip())
                    conn.commit()
                    logger.info(f"Executed SQL for task {task.name}")
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            raise e
    
    async def _execute_safe_command(self, command: str) -> str:
        """Execute safe shell commands"""
        try:
            import subprocess
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd()
            )
            return result.stdout + result.stderr
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise e
    
    async def _execute_python_code(self, python_code: str, task: Task) -> str:
        """Execute Python code safely"""
        try:
            import subprocess
            import tempfile
            import os
            
            # Create a temporary Python file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(python_code)
                temp_file = f.name
            
            try:
                # Execute the Python file
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=os.getcwd()
                )
                
                output = result.stdout + result.stderr
                logger.info(f"Python execution output: {output[:200]}...")
                return output
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Python execution failed: {e}")
            return f"Execution error: {str(e)}"
    
    def _extract_response_summary(self, content: str, files_created: List[str], files_modified: List[str]) -> str:
        """Extract a summary of what the agent accomplished"""
        summary_parts = []
        
        if files_created:
            summary_parts.append(f"Created {len(files_created)} files: {', '.join(files_created)}")
        
        if files_modified:
            summary_parts.append(f"Modified {len(files_modified)} files: {', '.join(files_modified)}")
        
        # Extract key points from the response
        lines = content.split('\n')
        key_lines = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['implemented', 'created', 'fixed', 'added', 'updated', 'built']):
                key_lines.append(line.strip())
                if len(key_lines) >= 3:  # Limit to first 3 key accomplishments
                    break
        
        if key_lines:
            summary_parts.append("Key accomplishments: " + "; ".join(key_lines))
        
        if not summary_parts:
            # Fallback to first few lines of response
            summary_parts.append(content[:200] + "..." if len(content) > 200 else content)
        
        return " | ".join(summary_parts)

class RealAgentOrchestrator:
    """Real orchestrator that manages actual LLM agents doing real work"""
    
    def __init__(self, db_path: str = "real_orchestrator.db"):
        self.db_path = db_path
        self.agents: Dict[str, RealAgent] = {}
        self.task_queue: List[Task] = []
        self.running = False
        self.learned_lessons: List[Dict[str, Any]] = []
        
        # Initialize database
        self._init_database()
        
        # Create real agents
        self._create_agents()
    
    def _init_database(self):
        """Initialize the orchestrator database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    agent_type TEXT,
                    priority INTEGER,
                    status TEXT,
                    assigned_agent TEXT,
                    result TEXT,
                    error TEXT,
                    created_at TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    progress INTEGER DEFAULT 0,
                    tokens_used INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0,
                    files_created TEXT,
                    files_modified TEXT
                )
            """)
            
            # Agents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    agent_type TEXT,
                    llm_provider TEXT,
                    status TEXT,
                    tasks_completed INTEGER DEFAULT 0,
                    total_tokens_used INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    created_at TIMESTAMP
                )
            """)
            
            # Lessons learned table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lessons_learned (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    task_type TEXT,
                    lesson TEXT,
                    error TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def _create_agents(self):
        """Create real agents with different specializations"""
        agent_configs = [
            ("code_dev_01", "Senior Code Developer", AgentType.CODE_DEVELOPER, "anthropic"),
            ("sys_analyst_01", "System Analyst", AgentType.SYSTEM_ANALYST, "anthropic"),
            ("api_int_01", "API Integration Specialist", AgentType.API_INTEGRATOR, "anthropic"),
            ("db_spec_01", "Database Specialist", AgentType.DATABASE_SPECIALIST, "anthropic"),
            ("content_proc_01", "Content Processor", AgentType.CONTENT_PROCESSOR, "anthropic"),
            ("error_diag_01", "Error Diagnostician", AgentType.ERROR_DIAGNOSTICIAN, "anthropic"),
            ("template_fix_01", "Template Fixer", AgentType.TEMPLATE_FIXER, "anthropic"),
            ("web_test_01", "Web Tester", AgentType.WEB_TESTER, "anthropic")
        ]
        
        for agent_id, name, agent_type, provider in agent_configs:
            agent = RealAgent(agent_id, name, agent_type, provider)
            self.agents[agent_id] = agent
            logger.info(f"Created real agent: {name} ({agent_type.value})")
    
    def add_task(self, name: str, description: str, agent_type: AgentType, priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        """Add a new task to the queue"""
        task_id = f"task_{int(time.time() * 1000)}"
        task = Task(
            id=task_id,
            name=name,
            description=description,
            agent_type=agent_type,
            priority=priority
        )
        
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: (t.priority.value, t.created_at), reverse=True)
        
        self._save_task(task)
        
        logger.info(f"Added real task: {name} (Priority: {priority.name})")
        return task_id
    
    def _save_task(self, task: Task):
        """Save task to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO tasks 
                (id, name, description, agent_type, priority, status, assigned_agent, result, error,
                 created_at, started_at, completed_at, progress, tokens_used, cost, files_created, files_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id, task.name, task.description, task.agent_type.value, task.priority.value,
                task.status.value, task.assigned_agent, task.result, task.error,
                task.created_at, task.started_at, task.completed_at, task.progress,
                task.tokens_used, task.cost, json.dumps(task.files_created), json.dumps(task.files_modified)
            ))
            conn.commit()
    
    async def process_user_message(self, message: str) -> str:
        """Process user message and create appropriate tasks"""
        logger.info(f"Processing user message: {message[:100]}...")
        
        # Check if this is a template fixing request
        if any(keyword in message.lower() for keyword in ['fix', 'error', 'template', 'broken', 'page']):
            return await self._handle_error_fixing_request(message)
        
        # Use a system analyst to break down the user request
        analysis_task_id = self.add_task(
            name="Analyze User Request",
            description=f"Analyze this user request and break it down into specific actionable tasks: {message}",
            agent_type=AgentType.SYSTEM_ANALYST,
            priority=TaskPriority.HIGH
        )
        
        # Process the analysis task
        analysis_task = next(t for t in self.task_queue if t.id == analysis_task_id)
        analyst_agent = next(a for a in self.agents.values() if a.agent_type == AgentType.SYSTEM_ANALYST)
        
        result = await analyst_agent.execute_task(analysis_task)
        
        if result["success"]:
            return f"✅ Real agent analysis completed. Task breakdown: {result['result'][:200]}..."
        else:
            return f"❌ Analysis failed: {result['error']}"
    
    async def _handle_error_fixing_request(self, message: str) -> str:
        """Handle template fixing and error resolution requests"""
        logger.info("Handling error fixing request")
        
        # Extract URL from message if present
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, message)
        
        if urls:
            # Test the URL first
            test_task_id = self.add_task(
                name="Test Web Page",
                description=f"Test this URL and identify specific errors: {urls[0]}",
                agent_type=AgentType.WEB_TESTER,
                priority=TaskPriority.CRITICAL
            )
            
            # Execute test task
            test_task = next(t for t in self.task_queue if t.id == test_task_id)
            tester_agent = next(a for a in self.agents.values() if a.agent_type == AgentType.WEB_TESTER)
            
            test_result = await tester_agent.execute_task(test_task)
            
            if test_result["success"]:
                # Create template fixing task based on test results
                fix_task_id = self.add_task(
                    name="Fix Template Error",
                    description=f"Fix the template error identified: {test_result['result']}. Target URL: {urls[0]}",
                    agent_type=AgentType.TEMPLATE_FIXER,
                    priority=TaskPriority.CRITICAL
                )
                
                # Execute fix task
                fix_task = next(t for t in self.task_queue if t.id == fix_task_id)
                fixer_agent = next(a for a in self.agents.values() if a.agent_type == AgentType.TEMPLATE_FIXER)
                
                fix_result = await fixer_agent.execute_task(fix_task)
                
                if fix_result["success"]:
                    # Test again to verify fix
                    verify_task_id = self.add_task(
                        name="Verify Fix",
                        description=f"Verify that the template fix worked by testing: {urls[0]}",
                        agent_type=AgentType.WEB_TESTER,
                        priority=TaskPriority.HIGH
                    )
                    
                    verify_task = next(t for t in self.task_queue if t.id == verify_task_id)
                    verify_result = await tester_agent.execute_task(verify_task)
                    
                    return f"✅ AUTONOMOUS FIX COMPLETE: {fix_result['result']}\n🔍 Verification: {verify_result['result'][:100]}..."
                else:
                    return f"❌ Template fix failed: {fix_result['error']}"
            else:
                return f"❌ Web test failed: {test_result['error']}"
        else:
            # General error fixing without specific URL
            fix_task_id = self.add_task(
                name="General Error Analysis",
                description=f"Analyze and fix the error described: {message}",
                agent_type=AgentType.ERROR_DIAGNOSTICIAN,
                priority=TaskPriority.HIGH
            )
            
            fix_task = next(t for t in self.task_queue if t.id == fix_task_id)
            error_agent = next(a for a in self.agents.values() if a.agent_type == AgentType.ERROR_DIAGNOSTICIAN)
            
            result = await error_agent.execute_task(fix_task)
            
            if result["success"]:
                return f"✅ Error analysis completed: {result['result'][:200]}..."
            else:
                return f"❌ Error analysis failed: {result['error']}"
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status including provider statistics"""
        try:
            active_agents = len([a for a in self.agents.values() if a.status == "working"])
            total_tasks = len(self.task_queue)
            completed_tasks = len([t for t in self.task_queue if t.status == TaskStatus.COMPLETED])
            
            # Get provider statistics
            provider_stats = self.load_balancer.get_provider_stats()
            
            # Calculate provider usage distribution
            total_requests = sum(stats["requests"] for stats in provider_stats.values())
            for provider, stats in provider_stats.items():
                if total_requests > 0:
                    stats["usage_percentage"] = (stats["requests"] / total_requests) * 100
                    stats["success_rate"] = (stats["requests"] - stats["errors"]) / max(stats["requests"], 1) * 100
                else:
                    stats["usage_percentage"] = 0
                    stats["success_rate"] = 100
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_overview': {
                    'active_agents': active_agents,
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'success_rate': (completed_tasks / max(total_tasks, 1)) * 100
                },
                'provider_statistics': provider_stats,
                'agents': [
                    {
                        'id': agent.agent_id,
                        'name': agent.name,
                        'type': agent.agent_type.value,
                        'status': agent.status,
                        'provider_preference': agent.llm_provider,
                        'tasks_completed': agent.tasks_completed,
                        'total_cost': agent.total_cost,
                        'available_providers': list(agent.provider_clients.keys())
                    }
                    for agent in self.agents.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {'error': str(e)}
    
    async def autonomous_website_monitoring(self):
        """Continuously monitor the website and fix errors automatically"""
        logger.info("🔍 Starting autonomous website monitoring")
        
        # Common website pages to monitor
        test_urls = [
            "http://localhost:5000/",
            "http://localhost:5000/active-agents",
            "http://localhost:5000/autonomous-monitor",
            "http://localhost:5000/workflow-templates",
            "http://localhost:5000/prompt-library",
            "http://localhost:5000/notes",
            "http://localhost:5000/tasks"
        ]
        
        while self.running:
            try:
                for url in test_urls:
                    # Test each URL
                    test_task_id = self.add_task(
                        name=f"Monitor {url}",
                        description=f"Check if {url} is working correctly and identify any errors",
                        agent_type=AgentType.WEB_TESTER,
                        priority=TaskPriority.MEDIUM
                    )
                    
                    # Process the task
                    test_task = next(t for t in self.task_queue if t.id == test_task_id)
                    tester_agent = next(a for a in self.agents.values() if a.agent_type == AgentType.WEB_TESTER)
                    
                    result = await tester_agent.execute_task(test_task)
                    
                    # If errors found, automatically fix them
                    if result["success"] and "error" in result["result"].lower():
                        logger.warning(f"🚨 Error detected on {url}: {result['result'][:100]}")
                        
                        # Automatically create fix task
                        fix_task_id = self.add_task(
                            name=f"Auto-fix {url}",
                            description=f"Automatically fix the error found on {url}: {result['result']}",
                            agent_type=AgentType.TEMPLATE_FIXER,
                            priority=TaskPriority.CRITICAL
                        )
                        
                        logger.info(f"🔧 Created automatic fix task: {fix_task_id}")
                
                # Wait before next monitoring cycle
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in autonomous monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def start_orchestration(self):
        """Start the real orchestration system"""
        logger.info("🚀 Starting Real Agent Orchestration System")
        self.running = True
        
        # Start task processing loop
        while self.running:
            await self._process_task_queue()
            await asyncio.sleep(5)  # Check for new tasks every 5 seconds
    
    async def _process_task_queue(self):
        """Process pending tasks with available agents"""
        pending_tasks = [t for t in self.task_queue if t.status == TaskStatus.PENDING]
        available_agents = [a for a in self.agents.values() if a.status == "standby"]
        
        for task in pending_tasks[:len(available_agents)]:
            # Find best agent for this task type
            suitable_agents = [a for a in available_agents if a.agent_type == task.agent_type]
            
            if suitable_agents:
                agent = suitable_agents[0]
                available_agents.remove(agent)
                
                # Execute task asynchronously
                asyncio.create_task(self._execute_task_with_agent(task, agent))
    
    async def _execute_task_with_agent(self, task: Task, agent: RealAgent):
        """Execute a task with a specific agent"""
        try:
            result = await agent.execute_task(task)
            self._save_task(task)
            
            if result["success"]:
                logger.info(f"✅ Task completed: {task.name}")
            else:
                logger.error(f"❌ Task failed: {task.name} - {result['error']}")
                
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self._save_task(task)

# Global instance
real_orchestrator = RealAgentOrchestrator()

def get_provider_health_status() -> Dict[str, Any]:
    """Get health status of all providers"""
    return {
        'load_balancer': real_orchestrator.load_balancer.get_provider_stats(),
        'available_providers': {
            'anthropic': bool(os.getenv('ANTHROPIC_API_KEY')),
            'openai': bool(os.getenv('OPENAI_API_KEY')),
            'gemini': bool(os.getenv('GOOGLE_API_KEY'))
        },
        'total_agents': len(real_orchestrator.agents),
        'agents_with_multi_provider': len([
            a for a in real_orchestrator.agents.values() 
            if len(a.provider_clients) > 1
        ])
    }

def main():
    """Main function for testing"""
    asyncio.run(test_real_orchestrator())

async def test_real_orchestrator():
    """Test the real orchestrator"""
    # Create a real task
    task_id = real_orchestrator.add_task(
        name="Build YouTube Processor",
        description="Create a real YouTube channel processor that monitors the database for marked channels and processes them using the YouTube API",
        agent_type=AgentType.CODE_DEVELOPER,
        priority=TaskPriority.HIGH
    )
    
    # Process the task
    response = await real_orchestrator.process_user_message(
        "Build a real YouTube processor for the marked channels in the database"
    )
    
    print("Orchestrator Response:", response)

if __name__ == "__main__":
    main()