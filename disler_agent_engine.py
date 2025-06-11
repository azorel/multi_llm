#!/usr/bin/env python3
"""
Disler Agent Engine - Powers the AI Engineering System
Implements patterns from all 8 disler repositories with low-temperature, powerful prompts
"""

import asyncio
import aiohttp
import json
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Load environment
env_path = Path('.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                if '#' in value:
                    value = value.split('#')[0].strip()
                os.environ[key] = value

class DislerAgentEngine:
    """
    Central engine implementing disler's patterns:
    - Single File Agents (SFA)
    - Multi-model support with low temperature
    - Prompt testing and optimization
    - Voice command processing
    - Infinite agentic loops
    - Cost tracking and optimization
    """
    
    def __init__(self):
        # API configurations
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        
        # Database IDs
        self.databases = {
            'agent_command_center': os.getenv('DISLER_AGENT_COMMAND_CENTER_ID'),
            'prompt_library': os.getenv('DISLER_PROMPT_LIBRARY_ID'),
            'model_testing': os.getenv('DISLER_MODEL_TESTING_DASHBOARD_ID'),
            'voice_commands': os.getenv('DISLER_VOICE_COMMANDS_ID'),
            'workflow_templates': os.getenv('DISLER_WORKFLOW_TEMPLATES_ID'),
            'agent_results': os.getenv('DISLER_AGENT_RESULTS_ID'),
            'cost_tracking': os.getenv('DISLER_COST_TRACKING_ID')
        }
        
# NOTION_REMOVED:         self.notion_headers = {
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        # Agent execution tracking
        self.active_executions = {}
        self.execution_history = []
        
        # Low temperature for precise, powerful responses
        self.model_configs = {
            'openai': {
                'temperature': 0.1,
                'max_tokens': 4000,
                'top_p': 0.95
            },
            'anthropic': {
                'temperature': 0.1,
                'max_tokens': 4000,
                'top_p': 0.95
            },
            'gemini': {
                'temperature': 0.1,
                'max_output_tokens': 4000,
                'top_p': 0.95
            }
        }
        
        print("🤖 Disler Agent Engine initialized")
        print(f"📊 Connected to {len([db for db in self.databases.values() if db])} databases")
    
    async def monitor_all_systems(self):
        """Main monitoring loop for all Disler systems."""
        print("🔄 Starting Disler Agent Engine monitoring...")
        
        while True:
            try:
                # Monitor Agent Command Center
                await self._monitor_agent_executions()
                
                # Monitor Model Testing
                await self._monitor_model_tests()
                
                # Monitor Voice Commands
                await self._monitor_voice_commands()
                
                # Monitor Workflow Executions
                await self._monitor_workflow_executions()
                
                # Update cost tracking
                await self._update_cost_tracking()
                
                # Wait before next cycle
                await asyncio.sleep(15)  # Check every 15 seconds for responsiveness
                
            except Exception as e:
                print(f"❌ Critical error in monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _single_monitoring_cycle(self):
        """Run a single monitoring cycle across all systems."""
        try:
            # Monitor Agent Command Center
            await self._monitor_agent_executions()
            
            # Monitor Model Testing
            await self._monitor_model_tests()
            
            # Monitor Voice Commands
            await self._monitor_voice_commands()
            
            # Monitor Workflow Executions
            await self._monitor_workflow_executions()
            
            # Update cost tracking (less frequent)
            # await self._update_cost_tracking()
            
        except Exception as e:
            print(f"❌ Error in single monitoring cycle: {e}")
    
    async def _monitor_agent_executions(self):
        """Monitor Agent Command Center for execution requests."""
        try:
            # Query for agents marked for execution
            query_data = {
                "filter": {
                    "property": "Execute Agent",
                    "checkbox": {"equals": True}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=query_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        agents = data.get('results', [])
                        
                        for agent in agents:
                            await self._execute_agent(agent)
                            
        except Exception as e:
            print(f"❌ Error monitoring agent executions: {e}")
    
    async def _execute_agent(self, agent: Dict[str, Any]):
        """Execute a single agent using SFA patterns from disler."""
        agent_id = agent['id']
        props = agent.get('properties', {})
        
        try:
            # Extract agent details
            agent_name = self._get_property_value(props, 'Agent Name', 'title')
            agent_type = self._get_property_value(props, 'Agent Type', 'select')
            providers = self._get_property_value(props, 'Provider', 'multi_select')
            prompt_template = self._get_property_value(props, 'Prompt Template', 'rich_text')
            configuration = self._get_property_value(props, 'Configuration', 'rich_text')
            
            print(f"🚀 Executing agent: {agent_name} ({agent_type})")
            
            # Update status to Running
            await self._update_agent_status(agent_id, "Running")
            
            # Choose provider (prefer order: OpenAI, Anthropic, Gemini)
            provider = self._select_best_provider(providers)
            
            # Execute based on agent type
            result = await self._execute_by_type(agent_type, prompt_template, configuration, provider)
            
            # Update agent with results
            await self._update_agent_results(agent_id, result, provider)
            
            # Record execution in results database
            await self._record_agent_execution(agent_name, agent_type, result, provider)
            
            # Uncheck the execution checkbox
            await self._uncheck_agent_execution(agent_id)
            
            print(f"✅ Agent execution completed: {agent_name}")
            
        except Exception as e:
            print(f"❌ Error executing agent {agent_id}: {e}")
            await self._update_agent_status(agent_id, "Failed", str(e))
            await self._uncheck_agent_execution(agent_id)
    
    async def _execute_by_type(self, agent_type: str, prompt_template: str, configuration: str, provider: str) -> Dict[str, Any]:
        """Execute agent based on type using appropriate SFA pattern."""
        
        # Parse configuration if provided
        config = {}
        if configuration:
            try:
                config = json.loads(configuration)
            except:
                # Treat as plain text input
                config = {'input': configuration}
        
        # Build enhanced prompt with disler's patterns
        enhanced_prompt = self._build_enhanced_prompt(agent_type, prompt_template, config)
        
        # Execute with selected provider
        if agent_type == "Data Query":
            return await self._execute_data_query_agent(enhanced_prompt, config, provider)
        elif agent_type == "Web Scraping":
            return await self._execute_web_scraping_agent(enhanced_prompt, config, provider)
        elif agent_type == "File Operations":
            return await self._execute_file_operations_agent(enhanced_prompt, config, provider)
        elif agent_type == "Content Generation":
            return await self._execute_content_generation_agent(enhanced_prompt, config, provider)
        elif agent_type == "Code Generation":
            return await self._execute_code_generation_agent(enhanced_prompt, config, provider)
        elif agent_type == "Analysis":
            return await self._execute_analysis_agent(enhanced_prompt, config, provider)
        else:
            return await self._execute_custom_agent(enhanced_prompt, config, provider)
    
    def _build_enhanced_prompt(self, agent_type: str, template: str, config: Dict) -> str:
        """Build enhanced prompt using disler's prompt engineering patterns."""
        
        # Base structure from disler's repositories
        base_prompt = f"""You are a {agent_type} specialist AI agent. You are precise, efficient, and follow instructions exactly.

CORE INSTRUCTIONS:
{template}

EXECUTION CONTEXT:
- Agent Type: {agent_type}
- Temperature: 0.1 (precise, deterministic responses)
- Focus: High-quality, actionable results
- Format: Structured, clear output

INPUT DATA:
{json.dumps(config, indent=2) if config else "No specific input provided"}

RESPONSE REQUIREMENTS:
1. Provide precise, actionable results
2. Include reasoning for decisions made
3. Format output clearly and consistently
4. Include error handling for any issues
5. Optimize for accuracy over creativity

Execute the task following these requirements exactly."""

        return base_prompt
    
    async def _execute_data_query_agent(self, prompt: str, config: Dict, provider: str) -> Dict[str, Any]:
        """Execute data query agent using DuckDB pattern from single-file-agents."""
        try:
            # Simulate DuckDB operation (in real implementation, would use actual DuckDB)
            result = await self._call_llm(prompt, provider)
            
            return {
                'success': True,
                'output': result,
                'type': 'data_query',
                'provider': provider,
                'tokens_used': len(prompt.split()) + len(result.split()),
                'cost_estimate': self._estimate_cost(prompt, result, provider)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'type': 'data_query',
                'provider': provider
            }
    
    async def _execute_web_scraping_agent(self, prompt: str, config: Dict, provider: str) -> Dict[str, Any]:
        """Execute web scraping agent with AI filtering."""
        try:
            # Enhanced prompt for web scraping
            scraping_prompt = f"""{prompt}

WEB SCRAPING INSTRUCTIONS:
- Extract relevant information from the specified URL or content
- Apply intelligent filtering to remove noise
- Summarize key findings in structured format
- Validate extracted data for accuracy

URL/Content to process: {config.get('url', config.get('content', 'Not specified'))}"""
            
            result = await self._call_llm(scraping_prompt, provider)
            
            return {
                'success': True,
                'output': result,
                'type': 'web_scraping',
                'provider': provider,
                'tokens_used': len(scraping_prompt.split()) + len(result.split()),
                'cost_estimate': self._estimate_cost(scraping_prompt, result, provider)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'type': 'web_scraping',
                'provider': provider
            }
    
    async def _execute_file_operations_agent(self, prompt: str, config: Dict, provider: str) -> Dict[str, Any]:
        """Execute file operations agent using bash/file patterns."""
        try:
            # Enhanced prompt for file operations
            file_prompt = f"""{prompt}

FILE OPERATION INSTRUCTIONS:
- Perform the requested file operation safely
- Validate file paths and permissions
- Provide clear status updates
- Handle errors gracefully

Operation: {config.get('operation', 'Not specified')}
Target: {config.get('target', 'Not specified')}"""
            
            result = await self._call_llm(file_prompt, provider)
            
            return {
                'success': True,
                'output': result,
                'type': 'file_operations',
                'provider': provider,
                'tokens_used': len(file_prompt.split()) + len(result.split()),
                'cost_estimate': self._estimate_cost(file_prompt, result, provider)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'type': 'file_operations',
                'provider': provider
            }
    
    async def _execute_content_generation_agent(self, prompt: str, config: Dict, provider: str) -> Dict[str, Any]:
        """Execute content generation agent with structured output."""
        try:
            # Enhanced prompt for content generation
            content_prompt = f"""{prompt}

CONTENT GENERATION INSTRUCTIONS:
- Create high-quality, relevant content
- Follow specified format and style guidelines
- Ensure accuracy and factual correctness
- Optimize for the intended audience

Topic: {config.get('topic', 'Not specified')}
Format: {config.get('format', 'Not specified')}
Length: {config.get('length', 'Not specified')}"""
            
            result = await self._call_llm(content_prompt, provider)
            
            return {
                'success': True,
                'output': result,
                'type': 'content_generation',
                'provider': provider,
                'tokens_used': len(content_prompt.split()) + len(result.split()),
                'cost_estimate': self._estimate_cost(content_prompt, result, provider)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'type': 'content_generation',
                'provider': provider
            }
    
    async def _execute_code_generation_agent(self, prompt: str, config: Dict, provider: str) -> Dict[str, Any]:
        """Execute code generation agent with best practices."""
        try:
            # Enhanced prompt for code generation
            code_prompt = f"""{prompt}

CODE GENERATION INSTRUCTIONS:
- Generate clean, efficient, well-documented code
- Follow language-specific best practices
- Include error handling and edge cases
- Optimize for readability and performance

Language: {config.get('language', 'Not specified')}
Task: {config.get('task', 'Not specified')}
Requirements: {config.get('requirements', 'Not specified')}"""
            
            result = await self._call_llm(code_prompt, provider)
            
            return {
                'success': True,
                'output': result,
                'type': 'code_generation',
                'provider': provider,
                'tokens_used': len(code_prompt.split()) + len(result.split()),
                'cost_estimate': self._estimate_cost(code_prompt, result, provider)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'type': 'code_generation',
                'provider': provider
            }
    
    async def _execute_analysis_agent(self, prompt: str, config: Dict, provider: str) -> Dict[str, Any]:
        """Execute analysis agent with structured insights."""
        try:
            # Enhanced prompt for analysis
            analysis_prompt = f"""{prompt}

ANALYSIS INSTRUCTIONS:
- Provide comprehensive, structured analysis
- Include key insights and recommendations
- Support conclusions with evidence
- Present findings in clear, actionable format

Data to analyze: {config.get('data', 'Not specified')}
Analysis type: {config.get('analysis_type', 'General')}
Focus areas: {config.get('focus_areas', 'Not specified')}"""
            
            result = await self._call_llm(analysis_prompt, provider)
            
            return {
                'success': True,
                'output': result,
                'type': 'analysis',
                'provider': provider,
                'tokens_used': len(analysis_prompt.split()) + len(result.split()),
                'cost_estimate': self._estimate_cost(analysis_prompt, result, provider)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'type': 'analysis',
                'provider': provider
            }
    
    async def _execute_custom_agent(self, prompt: str, config: Dict, provider: str) -> Dict[str, Any]:
        """Execute custom agent with flexible configuration."""
        try:
            result = await self._call_llm(prompt, provider)
            
            return {
                'success': True,
                'output': result,
                'type': 'custom',
                'provider': provider,
                'tokens_used': len(prompt.split()) + len(result.split()),
                'cost_estimate': self._estimate_cost(prompt, result, provider)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'type': 'custom',
                'provider': provider
            }
    
    async def _call_llm(self, prompt: str, provider: str) -> str:
        """Call the appropriate LLM with low temperature settings."""
        
        if provider == "OpenAI" and self.openai_key:
            return await self._call_openai(prompt)
        elif provider == "Anthropic" and self.anthropic_key:
            return await self._call_anthropic(prompt)
        elif provider == "Gemini" and self.gemini_key:
            return await self._call_gemini(prompt)
        else:
            # Fallback to available provider
            if self.openai_key:
                return await self._call_openai(prompt)
            elif self.anthropic_key:
                return await self._call_anthropic(prompt)
            elif self.gemini_key:
                return await self._call_gemini(prompt)
            else:
                raise Exception("No API keys available")
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API with low temperature for precision."""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.openai_key)
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=self.model_configs['openai']['temperature'],
                max_tokens=self.model_configs['openai']['max_tokens'],
                top_p=self.model_configs['openai']['top_p']
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"OpenAI API error: {str(e)}"
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API with low temperature for precision."""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)
            
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=self.model_configs['anthropic']['max_tokens'],
                temperature=self.model_configs['anthropic']['temperature'],
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"Anthropic API error: {str(e)}"
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API with low temperature for precision."""
        try:
            # Simplified Gemini call (would need proper SDK integration)
            async with aiohttp.ClientSession() as session:
                url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={self.gemini_key}"
                
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": self.model_configs['gemini']['temperature'],
                        "maxOutputTokens": self.model_configs['gemini']['max_output_tokens'],
                        "topP": self.model_configs['gemini']['top_p']
                    }
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['candidates'][0]['content']['parts'][0]['text']
                    else:
                        return f"Gemini API error: {response.status}"
                        
        except Exception as e:
            return f"Gemini API error: {str(e)}"
    
    def _select_best_provider(self, providers: List[str]) -> str:
        """Select the best available provider based on preference and API availability."""
        preference_order = ["OpenAI", "Anthropic", "Gemini"]
        
        # Check available providers in preference order
        for preferred in preference_order:
            if preferred in providers:
                if preferred == "OpenAI" and self.openai_key:
                    return "OpenAI"
                elif preferred == "Anthropic" and self.anthropic_key:
                    return "Anthropic"
                elif preferred == "Gemini" and self.gemini_key:
                    return "Gemini"
        
        # Fallback to any available
        if self.openai_key:
            return "OpenAI"
        elif self.anthropic_key:
            return "Anthropic"
        elif self.gemini_key:
            return "Gemini"
        
        return "None"
    
    def _estimate_cost(self, prompt: str, response: str, provider: str) -> float:
        """Estimate API cost based on token usage."""
        # Simplified cost estimation (tokens * rate)
        prompt_tokens = len(prompt.split())
        response_tokens = len(response.split())
        total_tokens = prompt_tokens + response_tokens
        
        # Rough cost estimates per 1K tokens
        rates = {
            "OpenAI": 0.03,  # GPT-4
            "Anthropic": 0.015,  # Claude-3.5-Sonnet
            "Gemini": 0.0075  # Gemini Pro
        }
        
        rate = rates.get(provider, 0.02)
        return (total_tokens / 1000) * rate
    
    def _get_property_value(self, props: Dict[str, Any], prop_name: str, prop_type: str) -> Any:
        """Extract property value from Notion properties."""
        try:
            prop = props.get(prop_name, {})
            
            if prop_type == 'title' and prop.get('title'):
                return prop['title'][0].get('plain_text', '')
            elif prop_type == 'rich_text' and prop.get('rich_text'):
                return prop['rich_text'][0].get('plain_text', '')
            elif prop_type == 'select' and prop.get('select'):
                return prop['select'].get('name', '')
            elif prop_type == 'multi_select' and prop.get('multi_select'):
                return [item.get('name', '') for item in prop['multi_select']]
            elif prop_type == 'checkbox':
                return prop.get('checkbox', False)
            elif prop_type == 'number':
                return prop.get('number', 0)
            elif prop_type == 'date' and prop.get('date'):
                return prop['date'].get('start', '')
            
            return ''
        except Exception:
            return ''
    
    async def _update_agent_status(self, agent_id: str, status: str, error: str = None):
        """Update agent status in Notion."""
        try:
            update_data = {
                "properties": {
                    "Status": {"select": {"name": status}},
                    "Last Run": {"date": {"start": datetime.now().isoformat()}}
                }
            }
            
            if error:
                update_data["properties"]["Results"] = {
                    "rich_text": [{"text": {"content": f"Error: {error}"}}]
                }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Error updating agent status: {e}")
            return False
    
    async def _update_agent_results(self, agent_id: str, result: Dict, provider: str):
        """Update agent with execution results."""
        try:
            if result['success']:
                status = "Completed"
                results_text = result['output'][:2000]  # Truncate if too long
                cost = result.get('cost_estimate', 0)
                execution_time = result.get('tokens_used', 0) / 100  # Rough estimate
            else:
                status = "Failed"
                results_text = f"Error: {result.get('error', 'Unknown error')}"
                cost = 0
                execution_time = 0
            
            update_data = {
                "properties": {
                    "Status": {"select": {"name": status}},
                    "Results": {"rich_text": [{"text": {"content": results_text}}]},
                    "Cost Estimate": {"number": cost},
                    "Execution Time": {"number": execution_time},
                    "Last Run": {"date": {"start": datetime.now().isoformat()}}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Error updating agent results: {e}")
            return False
    
    async def _uncheck_agent_execution(self, agent_id: str):
        """Uncheck the Execute Agent checkbox."""
        try:
            update_data = {
                "properties": {
                    "Execute Agent": {"checkbox": False}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Error unchecking agent execution: {e}")
            return False
    
    async def _record_agent_execution(self, agent_name: str, agent_type: str, result: Dict, provider: str):
        """Record execution in Agent Results database."""
        try:
            if not self.databases['agent_results']:
                return
            
            execution_id = f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            page_data = {
                "parent": {"database_id": self.databases['agent_results']},
                "properties": {
                    "Execution ID": {"title": [{"text": {"content": execution_id}}]},
                    "Agent Name": {"rich_text": [{"text": {"content": agent_name}}]},
                    "Execution Time": {"date": {"start": datetime.now().isoformat()}},
                    "Duration": {"number": result.get('tokens_used', 0) / 100},
                    "Status": {"select": {"name": "Success" if result['success'] else "Failed"}},
                    "Output": {"rich_text": [{"text": {"content": result.get('output', result.get('error', ''))[:2000]}}]},
                    "Cost": {"number": result.get('cost_estimate', 0)},
                    "Tokens Used": {"number": result.get('tokens_used', 0)},
                    "Model Used": {"rich_text": [{"text": {"content": provider}}]}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=page_data,
                    timeout=10
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Error recording execution: {e}")
            return False
    
    async def _monitor_model_tests(self):
        """Monitor Model Testing Dashboard for test requests."""
        try:
            if not self.databases['model_testing']:
                return
            
            query_data = {
                "filter": {
                    "property": "Run Test",
                    "checkbox": {"equals": True}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=query_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        tests = data.get('results', [])
                        
                        for test in tests:
                            await self._execute_model_test(test)
                            
        except Exception as e:
            print(f"❌ Error monitoring model tests: {e}")
    
    async def _execute_model_test(self, test: Dict[str, Any]):
        """Execute model comparison test using promptfoo patterns."""
        test_id = test['id']
        props = test.get('properties', {})
        
        try:
            test_name = self._get_property_value(props, 'Test Name', 'title')
            prompt = self._get_property_value(props, 'Prompt', 'rich_text')
            models = self._get_property_value(props, 'Models Tested', 'multi_select')
            
            print(f"🧪 Running model test: {test_name}")
            
            # Execute test with each model
            results = {}
            costs = {}
            
            for model in models:
                if model in ["GPT-4", "GPT-3.5-Turbo"]:
                    provider = "OpenAI"
                elif model in ["Claude-3.5-Sonnet", "Claude-3-Haiku"]:
                    provider = "Anthropic"
                elif model in ["Gemini-Pro", "Gemini-Flash"]:
                    provider = "Gemini"
                else:
                    continue
                
                try:
                    start_time = datetime.now()
                    result = await self._call_llm(prompt, provider)
                    end_time = datetime.now()
                    
                    duration = (end_time - start_time).total_seconds()
                    cost = self._estimate_cost(prompt, result, provider)
                    
                    results[model] = {
                        'output': result,
                        'duration': duration,
                        'cost': cost,
                        'success': True
                    }
                    costs[model] = cost
                    
                except Exception as e:
                    results[model] = {
                        'error': str(e),
                        'success': False
                    }
            
            # Determine winner (lowest cost for similar quality)
            winner = min(costs.keys(), key=lambda k: costs[k]) if costs else "No winner"
            
            # Update test results
            await self._update_test_results(test_id, results, winner)
            
            print(f"✅ Model test completed: {test_name}")
            
        except Exception as e:
            print(f"❌ Error executing model test: {e}")
            await self._update_test_status(test_id, "Failed", str(e))
    
    async def _update_test_results(self, test_id: str, results: Dict, winner: str):
        """Update model test results."""
        try:
            results_text = json.dumps(results, indent=2)[:2000]
            
            update_data = {
                "properties": {
                    "Status": {"select": {"name": "Completed"}},
                    "Results": {"rich_text": [{"text": {"content": results_text}}]},
                    "Winner": {"select": {"name": winner}},
                    "Test Date": {"date": {"start": datetime.now().isoformat()}},
                    "Run Test": {"checkbox": False}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Error updating test results: {e}")
            return False
    
    async def _update_test_status(self, test_id: str, status: str, error: str = None):
        """Update test status."""
        try:
            update_data = {
                "properties": {
                    "Status": {"select": {"name": status}},
                    "Test Date": {"date": {"start": datetime.now().isoformat()}},
                    "Run Test": {"checkbox": False}
                }
            }
            
            if error:
                update_data["properties"]["Results"] = {
                    "rich_text": [{"text": {"content": f"Error: {error}"}}]
                }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Error updating test status: {e}")
            return False
    
    async def _monitor_voice_commands(self):
        """Monitor Voice Commands for execution requests."""
        try:
            if not self.databases['voice_commands']:
                return
            
            query_data = {
                "filter": {
                    "property": "Execute Command",
                    "checkbox": {"equals": True}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=query_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        commands = data.get('results', [])
                        
                        for command in commands:
                            await self._execute_voice_command(command)
                            
        except Exception as e:
            print(f"❌ Error monitoring voice commands: {e}")
    
    async def _execute_voice_command(self, command: Dict[str, Any]):
        """Execute voice command using claude-code-is-programmable patterns."""
        command_id = command['id']
        props = command.get('properties', {})
        
        try:
            command_name = self._get_property_value(props, 'Command', 'title')
            voice_trigger = self._get_property_value(props, 'Voice Trigger', 'rich_text')
            agent_type = self._get_property_value(props, 'Agent Type', 'select')
            parameters = self._get_property_value(props, 'Parameters', 'rich_text')
            
            print(f"🎤 Executing voice command: {command_name}")
            
            # Parse parameters
            config = {}
            if parameters:
                try:
                    config = json.loads(parameters)
                except:
                    config = {'input': parameters}
            
            # Execute based on agent type
            result = await self._execute_by_type(agent_type, voice_trigger, json.dumps(config), "OpenAI")
            
            # Update command results
            await self._update_voice_command_results(command_id, result)
            
            print(f"✅ Voice command completed: {command_name}")
            
        except Exception as e:
            print(f"❌ Error executing voice command: {e}")
            await self._uncheck_voice_command(command_id)
    
    async def _update_voice_command_results(self, command_id: str, result: Dict):
        """Update voice command results."""
        try:
            update_data = {
                "properties": {
                    "Last Executed": {"date": {"start": datetime.now().isoformat()}},
                    "Execute Command": {"checkbox": False}
                }
            }
            
            # Update usage count (simplified)
            current_count = 1  # Would need to fetch current value in real implementation
            update_data["properties"]["Usage Count"] = {"number": current_count}
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Error updating voice command: {e}")
            return False
    
    async def _uncheck_voice_command(self, command_id: str):
        """Uncheck voice command execution."""
        try:
            update_data = {
                "properties": {
                    "Execute Command": {"checkbox": False}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Error unchecking voice command: {e}")
            return False
    
    async def _monitor_workflow_executions(self):
        """Monitor Workflow Templates for execution requests."""
        try:
            if not self.databases['workflow_templates']:
                return
            
            query_data = {
                "filter": {
                    "property": "Execute Workflow",
                    "checkbox": {"equals": True}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=query_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        workflows = data.get('results', [])
                        
                        for workflow in workflows:
                            await self._execute_workflow(workflow)
                            
        except Exception as e:
            print(f"❌ Error monitoring workflows: {e}")
    
    async def _execute_workflow(self, workflow: Dict[str, Any]):
        """Execute workflow using infinite-agentic-loop patterns."""
        workflow_id = workflow['id']
        props = workflow.get('properties', {})
        
        try:
            workflow_name = self._get_property_value(props, 'Workflow Name', 'title')
            description = self._get_property_value(props, 'Description', 'rich_text')
            agent_pipeline = self._get_property_value(props, 'Agent Pipeline', 'rich_text')
            
            print(f"🔄 Executing workflow: {workflow_name}")
            
            # Parse agent pipeline
            steps = []
            if agent_pipeline:
                # Simple parsing - in real implementation would be more sophisticated
                steps = agent_pipeline.split('\n')
            
            # Execute workflow steps
            results = []
            for i, step in enumerate(steps):
                if step.strip():
                    step_result = await self._execute_workflow_step(step, i + 1)
                    results.append(step_result)
            
            # Update workflow results
            await self._update_workflow_results(workflow_id, results)
            
            print(f"✅ Workflow completed: {workflow_name}")
            
        except Exception as e:
            print(f"❌ Error executing workflow: {e}")
            await self._uncheck_workflow_execution(workflow_id)
    
    async def _execute_workflow_step(self, step: str, step_number: int) -> Dict:
        """Execute individual workflow step."""
        try:
            # Simple step execution - would be more sophisticated in real implementation
            prompt = f"Execute workflow step {step_number}: {step}"
            result = await self._call_llm(prompt, "OpenAI")
            
            return {
                'step': step_number,
                'description': step,
                'result': result,
                'success': True
            }
        except Exception as e:
            return {
                'step': step_number,
                'description': step,
                'error': str(e),
                'success': False
            }
    
    async def _update_workflow_results(self, workflow_id: str, results: List[Dict]):
        """Update workflow execution results."""
        try:
            results_text = json.dumps(results, indent=2)[:2000]
            
            update_data = {
                "properties": {
                    "Status": {"select": {"name": "Completed"}},
                    "Last Run": {"date": {"start": datetime.now().isoformat()}},
                    "Execute Workflow": {"checkbox": False}
                }
            }
            
            # Update usage count (simplified)
            current_count = 1  # Would fetch current value in real implementation
            update_data["properties"]["Usage Count"] = {"number": current_count}
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Error updating workflow: {e}")
            return False
    
    async def _uncheck_workflow_execution(self, workflow_id: str):
        """Uncheck workflow execution."""
        try:
            update_data = {
                "properties": {
                    "Execute Workflow": {"checkbox": False}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
# NOTION_REMOVED:                     headers=self.notion_headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Error unchecking workflow: {e}")
            return False
    
    async def _update_cost_tracking(self):
        """Update cost tracking with daily usage."""
        try:
            if not self.databases['cost_tracking']:
                return
            
            # This would aggregate actual costs from API usage
            # For now, creating a simple daily entry
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Check if today's entry exists
            # If not, create it with estimated costs
            # This is a simplified implementation
            
        except Exception as e:
            print(f"❌ Error updating cost tracking: {e}")

async def main():
    """Main function to run the Disler Agent Engine."""
    engine = DislerAgentEngine()
    
    print("🚀 Starting Disler Agent Engine")
    print("=" * 50)
    print("Monitoring all systems for checkbox executions...")
    print("🔲 Agent Command Center - Execute agents")
    print("🧪 Model Testing Dashboard - Run model comparisons")
    print("🎤 Voice Commands - Execute voice-controlled agents")
    print("🔄 Workflow Templates - Execute multi-agent workflows")
    print("💰 Cost Tracking - Monitor API usage")
    
    try:
        await engine.monitor_all_systems()
    except KeyboardInterrupt:
        print("\n🛑 Disler Agent Engine stopped by user")
    except Exception as e:
        print(f"\n❌ Engine error: {e}")

if __name__ == "__main__":
    asyncio.run(main())