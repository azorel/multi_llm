#!/usr/bin/env python3
"""
Disler AI Engineering System - Notion Integration Builder
Builds comprehensive AI agent system based on disler's repositories
"""

import asyncio
import aiohttp
import json
import os
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

class DislerNotionBuilder:
    """Build comprehensive AI engineering system in Notion based on disler's patterns."""
    
    def __init__(self):
        self.headers = {
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        # Track created databases
        self.created_databases = {}
        
        print("🚀 Disler AI Engineering System - Notion Builder")
        print("Building comprehensive AI agent system...")
    
    async def build_complete_system(self):
        """Build the complete AI engineering system in Notion."""
        print("\n🏗️ Building Disler AI Engineering System")
        print("=" * 50)
        
        try:
            # Create parent page for all AI engineering tools
            parent_page_id = await self._create_parent_page()
            if not parent_page_id:
                print("❌ Failed to create parent page")
                return
            
            # Build all databases
            await self._create_agent_command_center(parent_page_id)
            await self._create_prompt_library(parent_page_id)
            await self._create_model_testing_dashboard(parent_page_id)
            await self._create_voice_commands_database(parent_page_id)
            await self._create_workflow_templates(parent_page_id)
            await self._create_agent_results_database(parent_page_id)
            await self._create_cost_tracking_database(parent_page_id)
            
# DEMO CODE REMOVED: # Add sample data
# DEMO CODE REMOVED: await self._populate_sample_data()
            
            # Create integration documentation
            await self._create_integration_guide(parent_page_id)
            
            print("\n🎉 Disler AI Engineering System created successfully!")
            print("📋 Databases created:")
            for db_name, db_id in self.created_databases.items():
                print(f"  • {db_name}: {db_id}")
            
            # Update .env file with database IDs
            await self._update_env_file()
            
        except Exception as e:
            print(f"❌ Error building system: {e}")
    
    async def _create_parent_page(self) -> Optional[str]:
        """Create parent page for the AI engineering system."""
        try:
            # Search for existing pages to use as parent
            async with aiohttp.ClientSession() as session:
                search_data = {
                    "query": "",
                    "filter": {"property": "object", "value": "page"},
                    "page_size": 5
                }
                
                async with session.post(
                    headers=self.headers,
                    json=search_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        search_results = await response.json()
                        pages = search_results.get('results', [])
                        
                        if pages:
                            # Use first available page as parent
                            parent_id = pages[0]['id']
                            print(f"✅ Using existing page as parent: {parent_id}")
                            
                            # Create the AI Engineering system page
                            page_data = {
                                "parent": {"page_id": parent_id},
                                "properties": {
                                    "title": [{
                                        "type": "text",
                                        "text": {"content": "🤖 Disler AI Engineering System"}
                                    }]
                                },
                                "children": [
                                    {
                                        "object": "block",
                                        "type": "heading_1",
                                        "heading_1": {
                                            "rich_text": [{
                                                "type": "text",
                                                "text": {"content": "🤖 Disler AI Engineering System"}
                                            }]
                                        }
                                    },
                                    {
                                        "object": "block",
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [{
                                                "type": "text",
                                                "text": {
                                                    "content": "Comprehensive AI agent system based on disler's repository patterns. Features single-file agents, prompt testing, model comparison, voice interfaces, and workflow orchestration."
                                                }
                                            }]
                                        }
                                    },
                                    {
                                        "object": "block",
                                        "type": "heading_2",
                                        "heading_2": {
                                            "rich_text": [{
                                                "type": "text",
                                                "text": {"content": "🎯 Key Features"}
                                            }]
                                        }
                                    },
                                    {
                                        "object": "block",
                                        "type": "bulleted_list_item",
                                        "bulleted_list_item": {
                                            "rich_text": [{
                                                "type": "text",
                                                "text": {"content": "Single File Agents (SFA) for modular AI tasks"}
                                            }]
                                        }
                                    },
                                    {
                                        "object": "block",
                                        "type": "bulleted_list_item",
                                        "bulleted_list_item": {
                                            "rich_text": [{
                                                "type": "text",
                                                "text": {"content": "Multi-model prompt testing and optimization"}
                                            }]
                                        }
                                    },
                                    {
                                        "object": "block",
                                        "type": "bulleted_list_item",
                                        "bulleted_list_item": {
                                            "rich_text": [{
                                                "type": "text",
                                                "text": {"content": "Voice-controlled AI agent orchestration"}
                                            }]
                                        }
                                    },
                                    {
                                        "object": "block",
                                        "type": "bulleted_list_item",
                                        "bulleted_list_item": {
                                            "rich_text": [{
                                                "type": "text",
                                                "text": {"content": "Infinite agentic loops for complex workflows"}
                                            }]
                                        }
                                    },
                                    {
                                        "object": "block",
                                        "type": "bulleted_list_item",
                                        "bulleted_list_item": {
                                            "rich_text": [{
                                                "type": "text",
                                                "text": {"content": "Cost tracking and performance optimization"}
                                            }]
                                        }
                                    }
                                ]
                            }
                            
                            async with session.post(
                                headers=self.headers,
                                json=page_data,
                                timeout=15
                            ) as page_response:
                                if page_response.status == 200:
                                    page_result = await page_response.json()
                                    ai_system_page_id = page_result['id']
                                    print(f"✅ Created AI Engineering System page: {ai_system_page_id}")
                                    return ai_system_page_id
            
            return None
            
        except Exception as e:
            print(f"❌ Error creating parent page: {e}")
            return None
    
    async def _create_agent_command_center(self, parent_page_id: str):
        """Create the Agent Command Center database."""
        database_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "🤖 Agent Command Center"}}],
            "properties": {
                "Agent Name": {"title": {}},
                "Agent Type": {
                    "select": {
                        "options": [
                            {"name": "Data Query", "color": "blue"},
                            {"name": "Web Scraping", "color": "green"},
                            {"name": "File Operations", "color": "orange"},
                            {"name": "Content Generation", "color": "purple"},
                            {"name": "Code Generation", "color": "red"},
                            {"name": "Analysis", "color": "yellow"},
                            {"name": "Custom", "color": "gray"}
                        ]
                    }
                },
                "Provider": {
                    "multi_select": {
                        "options": [
                            {"name": "OpenAI", "color": "green"},
                            {"name": "Anthropic", "color": "orange"},
                            {"name": "Gemini", "color": "blue"},
                            {"name": "Local", "color": "gray"}
                        ]
                    }
                },
                "Prompt Template": {"rich_text": {}},
                "Configuration": {"rich_text": {}},
                "Execute Agent": {"checkbox": {}},
                "Last Run": {"date": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Ready", "color": "green"},
                            {"name": "Running", "color": "blue"},
                            {"name": "Completed", "color": "purple"},
                            {"name": "Failed", "color": "red"},
                            {"name": "Pending", "color": "yellow"}
                        ]
                    }
                },
                "Results": {"rich_text": {}},
                "Cost Estimate": {"number": {"format": "dollar"}},
                "Execution Time": {"number": {"format": "number"}},
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "High", "color": "red"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "Low", "color": "gray"}
                        ]
                    }
                },
                "Tags": {
                    "multi_select": {
                        "options": [
                            {"name": "SFA", "color": "blue"},
                            {"name": "Testing", "color": "green"},
                            {"name": "Production", "color": "purple"},
                            {"name": "Experimental", "color": "orange"}
                        ]
                    }
                }
            }
        }
        
        database_id = await self._create_database(database_data, "Agent Command Center")
        if database_id:
            self.created_databases["Agent Command Center"] = database_id
    
    async def _create_prompt_library(self, parent_page_id: str):
        """Create the Prompt Library database."""
        database_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "📚 Prompt Library"}}],
            "properties": {
                "Prompt Name": {"title": {}},
                "Category": {
                    "select": {
                        "options": [
                            {"name": "Data Analysis", "color": "blue"},
                            {"name": "Content Generation", "color": "green"},
                            {"name": "Code Generation", "color": "orange"},
                            {"name": "Web Scraping", "color": "purple"},
                            {"name": "File Operations", "color": "red"},
                            {"name": "Meta Prompts", "color": "yellow"},
                            {"name": "Testing", "color": "gray"}
                        ]
                    }
                },
                "Template": {"rich_text": {}},
                "Variables": {
                    "multi_select": {
                        "options": [
                            {"name": "input_data", "color": "blue"},
                            {"name": "output_format", "color": "green"},
                            {"name": "context", "color": "orange"},
                            {"name": "examples", "color": "purple"},
                            {"name": "constraints", "color": "red"}
                        ]
                    }
                },
                "Tested Models": {"rich_text": {}},
                "Success Rate": {"number": {"format": "percent"}},
                "Average Tokens": {"number": {"format": "number"}},
                "Cost Per Run": {"number": {"format": "dollar"}},
                "Examples": {"rich_text": {}},
                "Version": {"number": {"format": "number"}},
                "Created Date": {"date": {}},
                "Last Updated": {"date": {}},
                "Performance Notes": {"rich_text": {}}
            }
        }
        
        database_id = await self._create_database(database_data, "Prompt Library")
        if database_id:
            self.created_databases["Prompt Library"] = database_id
    
    async def _create_model_testing_dashboard(self, parent_page_id: str):
        """Create the Model Testing Dashboard."""
        database_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "🧪 Model Testing Dashboard"}}],
            "properties": {
                "Test Name": {"title": {}},
                "Prompt": {"rich_text": {}},
                "Models Tested": {
                    "multi_select": {
                        "options": [
                            {"name": "GPT-4", "color": "green"},
                            {"name": "GPT-3.5-Turbo", "color": "blue"},
                            {"name": "Claude-3.5-Sonnet", "color": "orange"},
                            {"name": "Claude-3-Haiku", "color": "red"},
                            {"name": "Gemini-Pro", "color": "purple"},
                            {"name": "Gemini-Flash", "color": "yellow"},
                            {"name": "Local-Model", "color": "gray"}
                        ]
                    }
                },
                "Run Test": {"checkbox": {}},
                "Test Type": {
                    "select": {
                        "options": [
                            {"name": "Performance", "color": "blue"},
                            {"name": "Cost", "color": "green"},
                            {"name": "Quality", "color": "purple"},
                            {"name": "Speed", "color": "orange"},
                            {"name": "Comparison", "color": "red"}
                        ]
                    }
                },
                "Assertions": {"rich_text": {}},
                "Results": {"rich_text": {}},
                "Winner": {
                    "select": {
                        "options": [
                            {"name": "GPT-4", "color": "green"},
                            {"name": "GPT-3.5-Turbo", "color": "blue"},
                            {"name": "Claude-3.5-Sonnet", "color": "orange"},
                            {"name": "Claude-3-Haiku", "color": "red"},
                            {"name": "Gemini-Pro", "color": "purple"},
                            {"name": "Gemini-Flash", "color": "yellow"},
                            {"name": "Tie", "color": "gray"}
                        ]
                    }
                },
                "Cost Comparison": {"rich_text": {}},
                "Performance Metrics": {"rich_text": {}},
                "Test Date": {"date": {}},
                "Duration": {"number": {"format": "number"}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Pending", "color": "yellow"},
                            {"name": "Running", "color": "blue"},
                            {"name": "Completed", "color": "green"},
                            {"name": "Failed", "color": "red"}
                        ]
                    }
                }
            }
        }
        
        database_id = await self._create_database(database_data, "Model Testing Dashboard")
        if database_id:
            self.created_databases["Model Testing Dashboard"] = database_id
    
    async def _create_voice_commands_database(self, parent_page_id: str):
        """Create Voice Commands database."""
        database_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "🎤 Voice Commands"}}],
            "properties": {
                "Command": {"title": {}},
                "Voice Trigger": {"rich_text": {}},
                "Agent Type": {
                    "select": {
                        "options": [
                            {"name": "Data Query", "color": "blue"},
                            {"name": "File Operations", "color": "orange"},
                            {"name": "Web Search", "color": "green"},
                            {"name": "Content Generation", "color": "purple"},
                            {"name": "Workflow", "color": "red"}
                        ]
                    }
                },
                "Execute Command": {"checkbox": {}},
                "Parameters": {"rich_text": {}},
                "Response Format": {
                    "select": {
                        "options": [
                            {"name": "Voice", "color": "blue"},
                            {"name": "Text", "color": "green"},
                            {"name": "Notion Page", "color": "orange"},
                            {"name": "File", "color": "purple"}
                        ]
                    }
                },
                "Last Executed": {"date": {}},
                "Success Rate": {"number": {"format": "percent"}},
                "Average Response Time": {"number": {"format": "number"}},
                "Usage Count": {"number": {"format": "number"}}
            }
        }
        
        database_id = await self._create_database(database_data, "Voice Commands")
        if database_id:
            self.created_databases["Voice Commands"] = database_id
    
    async def _create_workflow_templates(self, parent_page_id: str):
        """Create Workflow Templates database."""
        database_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "🔄 Workflow Templates"}}],
            "properties": {
                "Workflow Name": {"title": {}},
                "Description": {"rich_text": {}},
                "Category": {
                    "select": {
                        "options": [
                            {"name": "Data Processing", "color": "blue"},
                            {"name": "Content Creation", "color": "green"},
                            {"name": "Analysis", "color": "orange"},
                            {"name": "Automation", "color": "purple"},
                            {"name": "Research", "color": "red"},
                            {"name": "Testing", "color": "yellow"}
                        ]
                    }
                },
                "Execute Workflow": {"checkbox": {}},
                "Agent Pipeline": {"rich_text": {}},
                "Input Sources": {"rich_text": {}},
                "Output Destinations": {"rich_text": {}},
                "Trigger Type": {
                    "select": {
                        "options": [
                            {"name": "Manual", "color": "blue"},
                            {"name": "Scheduled", "color": "green"},
                            {"name": "Event", "color": "orange"},
                            {"name": "API", "color": "purple"}
                        ]
                    }
                },
                "Estimated Duration": {"number": {"format": "number"}},
                "Estimated Cost": {"number": {"format": "dollar"}},
                "Last Run": {"date": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Draft", "color": "gray"},
                            {"name": "Ready", "color": "green"},
                            {"name": "Running", "color": "blue"},
                            {"name": "Completed", "color": "purple"},
                            {"name": "Failed", "color": "red"}
                        ]
                    }
                },
                "Success Rate": {"number": {"format": "percent"}},
                "Usage Count": {"number": {"format": "number"}}
            }
        }
        
        database_id = await self._create_database(database_data, "Workflow Templates")
        if database_id:
            self.created_databases["Workflow Templates"] = database_id
    
    async def _create_agent_results_database(self, parent_page_id: str):
        """Create Agent Results database for execution history."""
        database_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "📊 Agent Results"}}],
            "properties": {
                "Execution ID": {"title": {}},
                "Agent Name": {"rich_text": {}},
                "Execution Time": {"date": {}},
                "Duration": {"number": {"format": "number"}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Success", "color": "green"},
                            {"name": "Failed", "color": "red"},
                            {"name": "Timeout", "color": "orange"},
                            {"name": "Cancelled", "color": "gray"}
                        ]
                    }
                },
                "Input": {"rich_text": {}},
                "Output": {"rich_text": {}},
                "Error Details": {"rich_text": {}},
                "Cost": {"number": {"format": "dollar"}},
                "Tokens Used": {"number": {"format": "number"}},
                "Model Used": {"rich_text": {}},
                "Performance Score": {"number": {"format": "number"}},
                "User Rating": {
                    "select": {
                        "options": [
                            {"name": "⭐⭐⭐⭐⭐", "color": "green"},
                            {"name": "⭐⭐⭐⭐", "color": "blue"},
                            {"name": "⭐⭐⭐", "color": "yellow"},
                            {"name": "⭐⭐", "color": "orange"},
                            {"name": "⭐", "color": "red"}
                        ]
                    }
                }
            }
        }
        
        database_id = await self._create_database(database_data, "Agent Results")
        if database_id:
            self.created_databases["Agent Results"] = database_id
    
    async def _create_cost_tracking_database(self, parent_page_id: str):
        """Create Cost Tracking database."""
        database_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "💰 Cost Tracking"}}],
            "properties": {
                "Date": {"title": {}},
                "Provider": {
                    "select": {
                        "options": [
                            {"name": "OpenAI", "color": "green"},
                            {"name": "Anthropic", "color": "orange"},
                            {"name": "Google", "color": "blue"},
                            {"name": "Total", "color": "purple"}
                        ]
                    }
                },
                "Model": {"rich_text": {}},
                "Operations": {"number": {"format": "number"}},
                "Tokens": {"number": {"format": "number"}},
                "Cost": {"number": {"format": "dollar"}},
                "Budget Remaining": {"number": {"format": "dollar"}},
                "Usage Type": {
                    "select": {
                        "options": [
                            {"name": "Agent Execution", "color": "blue"},
                            {"name": "Prompt Testing", "color": "green"},
                            {"name": "Voice Commands", "color": "orange"},
                            {"name": "Workflows", "color": "purple"}
                        ]
                    }
                },
                "Month": {"rich_text": {}},
                "Alert Threshold": {"number": {"format": "percent"}}
            }
        }
        
        database_id = await self._create_database(database_data, "Cost Tracking")
        if database_id:
            self.created_databases["Cost Tracking"] = database_id
    
    async def _create_database(self, database_data: Dict, name: str) -> Optional[str]:
        """Helper method to create a database."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    headers=self.headers,
                    json=database_data,
                    timeout=15
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        database_id = data['id']
                        print(f"✅ Created {name}: {database_id}")
                        return database_id
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to create {name}: {error_text}")
                        return None
        except Exception as e:
            print(f"❌ Error creating {name}: {e}")
            return None
    
# DEMO CODE REMOVED: async def _populate_sample_data(self):
# DEMO CODE REMOVED: """Add sample data to the databases."""
# DEMO CODE REMOVED: print("\n📝 Adding sample data...")
        
# DEMO CODE REMOVED: # Add sample agents
        if "Agent Command Center" in self.created_databases:
# DEMO CODE REMOVED: await self._add_sample_agents()
        
# DEMO CODE REMOVED: # Add sample prompts
        if "Prompt Library" in self.created_databases:
# DEMO CODE REMOVED: await self._add_sample_prompts()
        
# DEMO CODE REMOVED: # Add sample voice commands
        if "Voice Commands" in self.created_databases:
# DEMO CODE REMOVED: await self._add_sample_voice_commands()
    
# DEMO CODE REMOVED: async def _add_sample_agents(self):
# DEMO CODE REMOVED: """Add sample agents to the Agent Command Center."""
        database_id = self.created_databases["Agent Command Center"]
        
# DEMO CODE REMOVED: sample_agents = [
            {
                "Agent Name": {"title": [{"text": {"content": "DuckDB Query Agent"}}]},
                "Agent Type": {"select": {"name": "Data Query"}},
                "Provider": {"multi_select": [{"name": "OpenAI"}]},
                "Prompt Template": {"rich_text": [{"text": {"content": "You are a DuckDB expert. Analyze the provided data and execute the requested query. Return results in a clear, formatted manner."}}]},
                "Status": {"select": {"name": "Ready"}},
                "Priority": {"select": {"name": "High"}},
                "Tags": {"multi_select": [{"name": "SFA"}, {"name": "Production"}]}
            },
            {
                "Agent Name": {"title": [{"text": {"content": "Web Scraping Agent"}}]},
                "Agent Type": {"select": {"name": "Web Scraping"}},
                "Provider": {"multi_select": [{"name": "Anthropic"}]},
                "Prompt Template": {"rich_text": [{"text": {"content": "Extract relevant information from web pages using intelligent filtering and summarization."}}]},
                "Status": {"select": {"name": "Ready"}},
                "Priority": {"select": {"name": "Medium"}},
                "Tags": {"multi_select": [{"name": "SFA"}]}
            },
            {
                "Agent Name": {"title": [{"text": {"content": "Meta Prompt Generator"}}]},
                "Agent Type": {"select": {"name": "Content Generation"}},
                "Provider": {"multi_select": [{"name": "OpenAI"}, {"name": "Anthropic"}]},
                "Prompt Template": {"rich_text": [{"text": {"content": "Generate optimized prompts for specific tasks based on requirements and examples."}}]},
                "Status": {"select": {"name": "Ready"}},
                "Priority": {"select": {"name": "High"}},
                "Tags": {"multi_select": [{"name": "Testing"}, {"name": "Production"}]}
            }
        ]
        
# DEMO CODE REMOVED: for agent in sample_agents:
            await self._create_page(database_id, agent)
    
# DEMO CODE REMOVED: async def _add_sample_prompts(self):
# DEMO CODE REMOVED: """Add sample prompts to the Prompt Library."""
        database_id = self.created_databases["Prompt Library"]
        
# DEMO CODE REMOVED: sample_prompts = [
            {
                "Prompt Name": {"title": [{"text": {"content": "Data Analysis Template"}}]},
                "Category": {"select": {"name": "Data Analysis"}},
                "Template": {"rich_text": [{"text": {"content": "Analyze the following data: {input_data}\n\nProvide insights in this format: {output_format}\n\nConsider these constraints: {constraints}\n\nReturn structured analysis with key findings and recommendations."}}]},
                "Variables": {"multi_select": [{"name": "input_data"}, {"name": "output_format"}, {"name": "constraints"}]},
                "Success Rate": {"number": 95},
                "Average Tokens": {"number": 450}
            },
            {
                "Prompt Name": {"title": [{"text": {"content": "Code Generation Template"}}]},
                "Category": {"select": {"name": "Code Generation"}},
                "Template": {"rich_text": [{"text": {"content": "Generate {language} code for: {task_description}\n\nRequirements:\n- Follow best practices\n- Include error handling\n- Add clear comments\n- Optimize for performance\n\nExample format: {examples}"}}]},
                "Variables": {"multi_select": [{"name": "language"}, {"name": "task_description"}, {"name": "examples"}]},
                "Success Rate": {"number": 88},
                "Average Tokens": {"number": 320}
            }
        ]
        
# DEMO CODE REMOVED: for prompt in sample_prompts:
            await self._create_page(database_id, prompt)
    
# DEMO CODE REMOVED: async def _add_sample_voice_commands(self):
# DEMO CODE REMOVED: """Add sample voice commands."""
        database_id = self.created_databases["Voice Commands"]
        
# DEMO CODE REMOVED: sample_commands = [
            {
                "Command": {"title": [{"text": {"content": "Query Database"}}]},
                "Voice Trigger": {"rich_text": [{"text": {"content": "query database for"}}]},
                "Agent Type": {"select": {"name": "Data Query"}},
                "Response Format": {"select": {"name": "Voice"}},
                "Success Rate": {"number": 92}
            },
            {
                "Command": {"title": [{"text": {"content": "Generate Content"}}]},
                "Voice Trigger": {"rich_text": [{"text": {"content": "create content about"}}]},
                "Agent Type": {"select": {"name": "Content Generation"}},
                "Response Format": {"select": {"name": "Notion Page"}},
                "Success Rate": {"number": 87}
            }
        ]
        
# DEMO CODE REMOVED: for command in sample_commands:
            await self._create_page(database_id, command)
    
    async def _create_page(self, database_id: str, properties: Dict):
        """Create a page in a database."""
        try:
            page_data = {
                "parent": {"database_id": database_id},
                "properties": properties
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    headers=self.headers,
                    json=page_data,
                    timeout=10
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _create_integration_guide(self, parent_page_id: str):
        """Create integration guide page."""
        print("📖 Creating integration guide...")
        
        guide_data = {
            "parent": {"page_id": parent_page_id},
            "properties": {
                "title": [{"type": "text", "text": {"content": "🔧 Integration Guide & Setup"}}]
            },
            "children": [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": "🔧 Disler AI Engineering System Setup"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "This system integrates all patterns from disler's repositories into a no-code Notion interface."}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "🚀 Quick Start"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "Go to Agent Command Center database"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "Check 'Execute Agent' checkbox for any agent"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "Watch the automation process the agent and return results"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "📊 Database Overview"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "🤖 Agent Command Center - Execute and manage AI agents"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "📚 Prompt Library - Manage and test prompts"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "🧪 Model Testing Dashboard - Compare model performance"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "🎤 Voice Commands - Voice-controlled agent execution"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "🔄 Workflow Templates - Multi-agent workflows"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "📊 Agent Results - Execution history and analytics"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": "💰 Cost Tracking - Monitor API usage and costs"}}]
                    }
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    headers=self.headers,
                    json=guide_data,
                    timeout=15
                ) as response:
                    if response.status == 200:
                        print("✅ Integration guide created")
                    else:
                        print("⚠️ Failed to create integration guide")
        except Exception as e:
            print(f"❌ Error creating guide: {e}")
    
    async def _update_env_file(self):
        """Update .env file with new database IDs."""
        try:
            env_path = Path('.env')
            
            # Read existing content
            existing_content = ""
            if env_path.exists():
                with open(env_path, 'r') as f:
                    existing_content = f.read()
            
            # Add new database IDs
            new_content = existing_content
            if not new_content.endswith('\n') and new_content:
                new_content += '\n'
            
            new_content += f"\n# Disler AI Engineering System Database IDs\n"
            for db_name, db_id in self.created_databases.items():
                env_var = f"DISLER_{db_name.upper().replace(' ', '_')}_ID"
                new_content += f"{env_var}={db_id}\n"
            
            with open(env_path, 'w') as f:
                f.write(new_content)
            
            print("✅ Updated .env file with database IDs")
            
        except Exception as e:
            print(f"⚠️ Could not update .env file: {e}")

async def main():
    """Main function to build the system."""
# NOTION_REMOVED:     builder = DislerNotionBuilder()
    await builder.build_complete_system()

if __name__ == "__main__":
    asyncio.run(main())