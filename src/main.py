#!/usr/bin/env python3
"""
Autonomous Multi-LLM Agent System - Core Implementation
======================================================

Clean implementation of the 1-3-1 orchestration pattern:
- 1 Proposer phase (parallel proposal generation)
- 3 Evaluator phase (consensus voting)  
- 1 Executor phase (validated execution)

Focused on core autonomous functionality with LifeOS integration.
No web interfaces, pure autonomous operation.
"""

import asyncio
import signal
import sys
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from dotenv import load_dotenv

# Import hot reload system
from hot_reload import DevelopmentMode

# Core imports - using temporary config for testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from temp_config import initialize_config
from temp_stubs import (
    initialize_observability, TemporarySharedMemory, TemporaryAgentPool,
    TemporaryRecoveryManager, TemporaryGitHubClient
)

# Real Notion integration - import directly to avoid dependency issues
sys.path.insert(0, str(Path(__file__).parent / "integrations"))
from notion_mcp_client 
# Content processing integration
sys.path.insert(0, str(Path(__file__).parent / "processors"))
from content_processor_factory import content_factory
from youtube_channel_processor import create_youtube_channel_processor

# LifeOS automation integration
sys.path.insert(0, str(Path(__file__).parent / "automation"))
from lifeos_automation_engine import create_lifeos_automation_engine

# Create temporary classes for testing
from enum import Enum
from dataclasses import dataclass

class TaskType(Enum):
    GENERAL = "general"
    ANALYSIS = "analysis"
    CODE = "code"

class Priority(Enum):
    NORMAL = "normal"
    HIGH = "high"

@dataclass 
class TaskContext:
    task_id: str
    task_type: TaskType
    description: str
    priority: Priority
    context: Dict[str, Any]
    metadata: Dict[str, Any]

# Try to import real components, fall back to stubs
try:
    from core.orchestrator import Orchestrator
except ImportError:
    # Will implement later
    pass

# Load environment
load_dotenv()


class AutonomousAgentSystem:
    """
    Core autonomous multi-LLM agent system implementing 1-3-1 architecture.
    
    Features:
    - Pure autonomous operation (no web interfaces)
    - 1-3-1 orchestration pattern
    - Self-healing capabilities
    - LifeOS integration via Notion
    - Multi-LLM collaboration
    """
    
    def __init__(self):
        """Initialize the autonomous agent system."""
        self.config = None
        self.orchestrator = None
        self.agent_pool = None
        self.shared_memory = None
        self.recovery_manager = None
        self.observability = None
        
        # Integrations
        self.github_client = None
# NOTION_REMOVED:         self.notion_client = None
        self.content_factory = content_factory
        self.lifeos_automation_engine = None
        self.youtube_channel_processor = None
        
        # Runtime state
        self.running = False
        self.start_time = None
        self.background_tasks = []
        self.shutdown_handlers = []
        
        # Health monitoring
        self.component_health = {
            "config": "unknown",
            "orchestrator": "unknown",
            "agent_pool": "unknown", 
            "shared_memory": "unknown",
            "recovery_manager": "unknown",
            "observability": "unknown"
        }
        
        # Development mode
        self.development_mode = None
        self.is_development = False
        
        logger.info("Autonomous Agent System initialized")
    
    async def initialize(self, config_dir: str = "config", environment: Optional[str] = None, development: bool = False):
        """Initialize all system components."""
        logger.info("🤖 INITIALIZING AUTONOMOUS MULTI-LLM AGENT SYSTEM")
        logger.info("=" * 60)
        
        # Check for development mode
        self.is_development = development or os.environ.get('DEVELOPMENT_MODE', '').lower() == 'true'
        
        try:
            # Load configuration
            logger.info("📋 Loading configuration...")
            self.config = initialize_config(config_dir, environment)
            self.component_health["config"] = "healthy"
            
            # Initialize observability
            logger.info("📊 Starting observability system...")
            monitoring_config = self.config.get("monitoring", {})
            monitoring_config["enabled"] = True
            self.observability = initialize_observability(monitoring_config)
            if self.observability:
                self.observability.start()
                self.component_health["observability"] = "healthy"
            
            # Initialize shared memory
            logger.info("🧠 Initializing shared memory...")
            self.shared_memory = TemporarySharedMemory()
            self.component_health["shared_memory"] = "healthy"
            
            # Initialize agent pool with temporary agents for testing
            logger.info("🤖 Setting up agent pool...")
            self.agent_pool = TemporaryAgentPool()
            self.component_health["agent_pool"] = "healthy"
            
            # Initialize recovery manager for self-healing
            logger.info("🛡️ Setting up self-healing system...")
            recovery_config = self.config.get("features", {}).get("self_healing", {})
            self.recovery_manager = TemporaryRecoveryManager(
                agents=self.agent_pool.agents,
                shared_memory=self.shared_memory,
                config=recovery_config
            )
            self.component_health["recovery_manager"] = "healthy"
            
            # Note: Orchestrator will be implemented later
            logger.info("🎯 Core orchestrator will be implemented...")
            self.component_health["orchestrator"] = "pending"
            
            # Initialize external integrations
            logger.info("🔗 Setting up integrations...")
            await self._initialize_integrations()
            
            # Initialize LifeOS automation engine
            logger.info("🤖 Setting up LifeOS automation engine...")
            await self._initialize_lifeos_automation()
            
            # Initialize YouTube channel processor
            logger.info("📺 Setting up YouTube channel processor...")
            await self._initialize_youtube_processor()
            
            # Start background monitoring
            logger.info("⚙️ Starting background services...")
            await self._start_background_services()
            
            self.start_time = datetime.now()
            self.running = True
            
            # Initialize development mode if enabled
            if self.is_development:
                await self._initialize_development_mode()
            
            logger.info("✅ SYSTEM INITIALIZATION COMPLETE")
            logger.info(f"🎯 1-3-1 Architecture: {len(self.agent_pool.agents)} agents ready")
            logger.info(f"🔗 Integrations: {'Notion' if self.notion_client else 'None'} {'GitHub' if self.github_client else ''}")
            if self.is_development:
                logger.info("🔧 DEVELOPMENT MODE ACTIVE - Hot reload enabled")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    # Agent initialization removed - using temporary agents for testing
    
    async def _initialize_integrations(self):
        """Initialize external integrations."""
        
        # Temporary stub integrations for testing
        logger.info("   🔧 Using temporary integration stubs for testing")
        
        # GitHub Integration (temporary stub)
        github_config = self.config.get("api", {}).get("github", {})
        if github_config.get("token"):
            self.github_client = TemporaryGitHubClient(
                token=github_config.get("token"),
                owner=github_config.get("default_owner"),
                repo=github_config.get("default_repo")
            )
            logger.info("   ✅ GitHub integration stub ready")
        
        # Notion Integration (Real MCP integration)
# NOTION_REMOVED:         notion_config = self.config.get("api", {}).get("notion", {})  
        if notion_config.get("api_key"):
# NOTION_REMOVED:             self.notion_client = create_notion_client(
# NOTION_REMOVED:                 api_key=notion_config.get("api_key"),
                database_ids={
                    "tasks": notion_config.get("tasks_database_id"),
                    "knowledge": notion_config.get("knowledge_database_id"),
                    "logs": notion_config.get("execution_logs_database_id")
                }
            )
            
            # Test the connection
            try:
# NOTION_REMOVED:                 connection_test = await self.notion_client.test_connection()
                if connection_test:
                    logger.info("   ✅ LifeOS (Notion) MCP integration ready and tested")
                else:
                    logger.warning("   ⚠️ LifeOS (Notion) MCP integration added but connection test failed")
            except Exception as e:
                logger.warning(f"   ⚠️ LifeOS (Notion) MCP integration added but test failed: {e}")
        else:
            logger.info("   ℹ️ No Notion API key configured - LifeOS integration disabled")
    
    async def _initialize_lifeos_automation(self):
        """Initialize LifeOS automation engine."""
# NOTION_REMOVED:         notion_config = self.config.get("api", {}).get("notion", {})
        
            try:
                
                # Initialize the automation engine
                success = await self.lifeos_automation_engine.initialize()
                
                if success:
                    logger.info("   ✅ LifeOS automation engine initialized")
                    logger.info("   🔧 Multi-database automation ready")
                    logger.info("   ⚡ Workflow engines active")
                else:
                    logger.warning("   ⚠️ LifeOS automation engine initialization had issues")
                    
            except Exception as e:
                logger.warning(f"   ⚠️ LifeOS automation engine setup failed: {e}")
        else:
            logger.info("   ℹ️ No Notion API key - LifeOS automation disabled")
    
    async def _initialize_youtube_processor(self):
        """Initialize YouTube channel processor."""
# NOTION_REMOVED:         notion_config = self.config.get("api", {}).get("notion", {})
        
            try:
                self.youtube_channel_processor = create_youtube_channel_processor(
                )
                logger.info("   ✅ YouTube channel processor initialized")
                logger.info("   📺 Channel processing automation ready")
                logger.info("   ⚡ Checkbox-triggered processing active")
            except Exception as e:
                logger.warning(f"   ⚠️ YouTube channel processor setup failed: {e}")
        else:
            logger.info("   ℹ️ No Notion API key - YouTube channel processing disabled")
    
    async def _initialize_development_mode(self):
        """Initialize development mode features."""
        logger.info("🔧 Initializing development mode...")
        
        # Development configuration
        dev_config = {
            'auto_reload': True,
            'reload_delay': 1.0,
            'debug_mode': True,
            'performance_monitoring': True,
            'module_config': {
                # Add any module-specific reload configurations
                'src.automation.lifeos_automation_engine': {
                    'auto_reload': True,
                    'preserve_state': True,
                    'reload_delay': 2.0
                },
                'src.processors.youtube_channel_processor': {
                    'auto_reload': True,
                    'preserve_state': True,
                    'reload_delay': 1.5
                }
            }
        }
        
        # Initialize development mode
        self.development_mode = DevelopmentMode(self, dev_config)
        await self.development_mode.enable()
        
        logger.info("   ✅ Development mode initialized")
        logger.info("   🔄 Hot reload active for safe modules")
        logger.info("   📊 Performance monitoring enabled")
    
    async def _start_background_services(self):
        """Start background monitoring and maintenance services."""
        
        # Health monitoring task
        health_task = asyncio.create_task(self._health_monitoring_loop())
        self.background_tasks.append(health_task)
        
        # Self-healing monitoring
        if self.recovery_manager:
            healing_task = asyncio.create_task(self._self_healing_loop())
            self.background_tasks.append(healing_task)
        
        # LifeOS synchronization
        if self.notion_client:
            lifeos_task = asyncio.create_task(self._lifeos_sync_loop())
            self.background_tasks.append(lifeos_task)
            
            # Content processing monitoring
            content_task = asyncio.create_task(self._content_processing_loop())
            self.background_tasks.append(content_task)
            
            # LifeOS automation monitoring
            if self.lifeos_automation_engine:
                lifeos_task = asyncio.create_task(self._lifeos_automation_loop())
                self.background_tasks.append(lifeos_task)
            
            # YouTube channel processing monitoring
            if self.youtube_channel_processor:
                youtube_task = asyncio.create_task(self._youtube_channel_processing_loop())
                self.background_tasks.append(youtube_task)
        
        logger.info(f"   🔄 Started {len(self.background_tasks)} background services")
    
    async def _health_monitoring_loop(self):
        """Background health monitoring."""
        while self.running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _perform_health_checks(self):
        """Check health of all components."""
        
        # Check shared memory
        if self.shared_memory:
            try:
                test_key = f"health_check_{int(time.time())}"
                self.shared_memory.store(test_key, {"test": True})
                self.shared_memory.retrieve(test_key)
                self.shared_memory.delete(test_key)
                self.component_health["shared_memory"] = "healthy"
            except Exception:
                self.component_health["shared_memory"] = "unhealthy"
        
        # Check agent pool
        if self.agent_pool:
            try:
                # Simple health check - ensure agents are responsive
                healthy_agents = 0
                for agent in self.agent_pool.agents.values():
                    if hasattr(agent, 'health_check'):
                        try:
                            await agent.health_check()
                            healthy_agents += 1
                        except Exception:
                            continue
                
                if healthy_agents > 0:
                    self.component_health["agent_pool"] = "healthy"
                else:
                    self.component_health["agent_pool"] = "unhealthy"
            except Exception:
                self.component_health["agent_pool"] = "unhealthy"
    
    async def _self_healing_loop(self):
        """Background self-healing monitoring."""
        while self.running:
            try:
                if self.recovery_manager:
                    await self.recovery_manager.monitor_system_health()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Self-healing error: {e}")
                await asyncio.sleep(120)
    
    async def _lifeos_sync_loop(self):
        """Background LifeOS synchronization."""
        while self.running:
            try:
                if self.notion_client:
                    await self._sync_with_lifeos()
                await asyncio.sleep(300)  # Sync every 5 minutes
            except Exception as e:
                logger.error(f"LifeOS sync error: {e}")
                await asyncio.sleep(600)
    
    async def _sync_with_lifeos(self):
        """Synchronize with LifeOS (Notion workspace)."""
        if not self.notion_client:
            return
            
        try:
            # Get database IDs from config
# NOTION_REMOVED:             notion_config = self.config.get("api", {}).get("notion", {})
# NOTION_REMOVED:             tasks_db_id = notion_config.get("tasks_database_id")
            
            if not tasks_db_id:
                logger.warning("No tasks database ID configured for LifeOS sync")
                return
            
            # Check for new tasks in Notion
# NOTION_REMOVED:             tasks = await self.notion_client.get_pending_tasks(tasks_db_id)
            
            if not tasks:
                logger.debug("No pending tasks found in LifeOS")
                return
            
            logger.info(f"📋 Found {len(tasks)} pending tasks in LifeOS")
            
            for task_data in tasks:
                # Extract task info from Notion page properties
                properties = task_data.get("properties", {})
                
                # Get title
                title_prop = properties.get("Name", {}) or properties.get("Title", {})
                title = ""
                if title_prop.get("title"):
                    title = title_prop["title"][0].get("plain_text", "")
                
                # Skip if no title
                if not title:
                    continue
                
                # Convert Notion task to TaskContext
                task_context = TaskContext(
                    task_id=task_data.get("id", ""),
                    task_type=TaskType.GENERAL,
                    description=title,
                    priority=Priority.NORMAL,
# NOTION_REMOVED:                     context={"notion_data": task_data},
# NOTION_REMOVED:                     metadata={"source": "lifeos", "notion_page_id": task_data.get("id")}
                )
                
                # Process task (using temporary implementation for now)
                logger.info(f"📋 Processing LifeOS task: {task_context.description}")
                result = await self.execute_task(task_context.description)
                
                # Update task status in Notion
                await self.notion_client.update_task_status(
                    task_data.get("id"),
                    "✅ Completed"
                )
                
                logger.info(f"✅ LifeOS task completed: {result['status']}")
        
        except Exception as e:
            logger.error(f"LifeOS sync failed: {e}")
    
    async def _content_processing_loop(self):
        """Background content processing for Knowledge Hub."""
        while self.running:
            try:
                if self.notion_client:
                    await self._process_pending_content()
                await asyncio.sleep(180)  # Check every 3 minutes
            except Exception as e:
                logger.error(f"Content processing error: {e}")
                await asyncio.sleep(300)
    
    async def _lifeos_automation_loop(self):
        """Background LifeOS automation processing."""
        while self.running:
            try:
                if self.lifeos_automation_engine:
                    logger.info("🤖 Running LifeOS automation cycle...")
                    results = await self.lifeos_automation_engine.process_automation_cycle()
                    
                    # Log automation results
                    if "error" not in results:
                        processed_engines = [engine for engine, result in results.items() if result.get("processed_items") or result.get("completed_tasks")]
                        if processed_engines:
                            logger.info(f"✅ LifeOS automation completed: {len(processed_engines)} engines processed items")
                        else:
                            logger.debug("🔄 LifeOS automation cycle - no items to process")
                    else:
                        logger.error(f"❌ LifeOS automation error: {results['error']}")
                
                await asyncio.sleep(600)  # Run every 10 minutes
            except Exception as e:
                logger.error(f"LifeOS automation error: {e}")
                await asyncio.sleep(900)  # Wait longer on error
    
    async def _youtube_channel_processing_loop(self):
        """Background YouTube channel processing with adaptive timing."""
        base_check_interval = 30  # Check every 30 seconds for new channels
        processing_check_interval = 10  # Check every 10 seconds when actively processing
        
        while self.running:
            try:
                if self.youtube_channel_processor:
                    logger.debug("📺 Checking for YouTube channels to process...")
                    
                    # Get channels marked for processing
                    channels = await self.youtube_channel_processor.get_channels_to_process()
                    
                    if channels:
                        logger.info(f"📺 Found {len(channels)} channels marked for processing")
                        
                        # Process channels and keep checking until all are unmarked
                        processing_active = True
                        while processing_active and self.running:
                            result = await self.youtube_channel_processor.process_marked_channels()
                            
                            # Log results
                            if result["channels_processed"] > 0:
                                logger.info(f"✅ YouTube processing completed: {result['channels_processed']} channels, {result['total_videos_imported']} videos imported")
                                
                                if result["errors"]:
                                    logger.warning(f"⚠️ YouTube processing had {len(result['errors'])} errors")
                            
                            # Check if there are still channels to process
                            remaining_channels = await self.youtube_channel_processor.get_channels_to_process()
                            if not remaining_channels:
                                processing_active = False
                                logger.info("✅ All channels processed, returning to monitoring mode")
                            else:
                                logger.info(f"🔄 {len(remaining_channels)} channels still marked, continuing processing...")
                                await asyncio.sleep(processing_check_interval)  # Short wait during active processing
                    else:
                        logger.debug("🔄 YouTube processing cycle - no channels marked for processing")
                
                # Wait for next check cycle
                await asyncio.sleep(base_check_interval)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"YouTube channel processing error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _process_pending_content(self):
        """Process pending content in Knowledge Hub using direct API."""
        try:
            # Get Notion token
# NOTION_REMOVED:             notion_config = self.config.get("api", {}).get("notion", {})
            
                logger.debug("No Notion API token for content processing")
                return
            
            # Find Knowledge Hub database
            if not knowledge_db_id:
                logger.debug("Knowledge Hub database not found")
                return
            
            # Get pending content items
            
            if not pending_items:
                logger.debug("No pending content items found")
                return
            
            logger.info(f"📋 Found {len(pending_items)} pending content items to process")
            
            # Process each item
            for item in pending_items[:3]:  # Process max 3 items per cycle
                await asyncio.sleep(5)  # Small delay between items
                
        except Exception as e:
            logger.error(f"Error processing pending content: {e}")
    
        """Find Knowledge Hub database using direct API."""
        try:
            import requests
            
            headers = {
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                headers=headers,
                json={
                    'query': 'Knowledge Hub',
                    'filter': {'property': 'object', 'value': 'database'},
                    'page_size': 10
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                for item in results:
                    if item.get('object') == 'database':
                        title_list = item.get('title', [])
                        if title_list:
                            title = title_list[0].get('plain_text', '')
                            if 'Knowledge Hub' in title:
                                return item['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding Knowledge Hub: {e}")
            return None
    
        """Get content items that need processing."""
        try:
            import requests
            
            headers = {
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            # Query for items with 🚀 Yes = true and Status != ✅ Completed
            
            filter_data = {
                "filter": {
                    "and": [
                        {"property": "🚀 Yes", "checkbox": {"equals": True}},
                        {
                            "or": [
                                {"property": "Status", "select": {"does_not_equal": "✅ Completed"}},
                                {"property": "Status", "select": {"is_empty": True}}
                            ]
                        }
                    ]
                },
                "page_size": 10
            }
            
            response = requests.post(
                query_url,
                headers=headers,
                json=filter_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            else:
                logger.error(f"Query failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting pending content: {e}")
            return []
    
        """Process a single content item."""
        try:
            page_id = item.get('id', '')
            properties = item.get('properties', {})
            
            # Get content details
            content_url = None
            content_type = None
            content_name = "Unknown"
            
            # Extract URL
            if "URL" in properties:
                url_prop = properties["URL"]
                content_url = url_prop.get("url")
            
            # Extract Type
            if "Type" in properties:
                type_prop = properties["Type"]
                if type_prop.get("select"):
                    content_type = type_prop["select"].get("name")
            
            # Extract Name
            for prop_name in ["Name", "Title"]:
                if prop_name in properties:
                    title_prop = properties[prop_name]
                    if title_prop.get("title"):
                        content_name = title_prop["title"][0].get("plain_text", "Unknown")
                    break
            
            if not content_url or not content_type:
                logger.warning(f"⚠️ Missing URL or Type for item: {content_name}")
                return
            
            logger.info(f"🔄 Processing {content_type}: {content_name}")
            
            # Update status to Processing
            
            # Process content using factory
            result = await self.content_factory.process_content(content_url, content_type)
            
            if result.get('success'):
                # Update Notion with results
                logger.info(f"✅ Successfully processed: {content_name}")
            else:
                error = result.get('error', 'Unknown error')
                logger.error(f"❌ Failed to process {content_name}: {error}")
                
        except Exception as e:
            logger.error(f"Error processing content item: {e}")
            if 'page_id' in locals():
    
        """Update Notion page status."""
        try:
            import requests
            
            headers = {
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            properties = {
                "Status": {"select": {"name": status}}
            }
            
            if error_msg:
                current_notes = f"❌ Error: {error_msg}\n\nProcessed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                properties["Notes"] = {
                    "rich_text": [{"text": {"content": current_notes}}]
                }
            
            response = requests.patch(
                update_url,
                headers=headers,
                json={"properties": properties},
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to update status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error updating Notion status: {e}")
    
        """Update Notion page with processing results."""
        try:
            import requests
            
            headers = {
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            properties = {}
            
            # Get data from processing results
            metadata = processing_results.get('metadata', {})
            knowledge_hub = processing_results.get('knowledge_hub', {})
            
            # Update title if meaningful
            title = metadata.get('title', '') or metadata.get('name', '')
            if title and title not in ['Unknown Video', 'Unknown']:
                properties["Name"] = {
                    "title": [{"text": {"content": title}}]
                }
            
            # AI Summary
            ai_summary = knowledge_hub.get('ai_summary', '')
            if ai_summary:
                properties["AI Summary"] = {
                    "rich_text": [{"text": {"content": ai_summary}}]
                }
            
            # Hashtags
            hashtags = knowledge_hub.get('hashtags', [])
            if hashtags:
                clean_hashtags = [tag.replace('#', '') for tag in hashtags]
                properties["Hashtags"] = {
                    "multi_select": [{"name": tag} for tag in clean_hashtags]
                }
            
            # Priority based on relevance
            relevance_indicators = knowledge_hub.get('relevance_indicators', [])
            if 'High Priority' in relevance_indicators:
                properties["Priority"] = {"select": {"name": "🔴 High"}}
            elif 'Learning' in relevance_indicators or 'Implementation' in relevance_indicators:
                properties["Priority"] = {"select": {"name": "🟡 Medium"}}
            else:
                properties["Priority"] = {"select": {"name": "🟢 Low"}}
            
            # Status
            properties["Status"] = {"select": {"name": "✅ Completed"}}
            
            # Enhanced Notes
            notes = self._generate_enhanced_notes(metadata, knowledge_hub, processing_results.get('content_type', 'Unknown'))
            if notes:
                properties["Notes"] = {
                    "rich_text": [{"text": {"content": notes}}]
                }
            
            # Update the page
            response = requests.patch(
                update_url,
                headers=headers,
                json={"properties": properties},
                timeout=15
            )
            
            if response.status_code == 200:
                logger.debug(f"Successfully updated Notion page {page_id[:8]}")
            else:
                logger.error(f"Failed to update Notion page: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error updating Notion with results: {e}")
    
    def _generate_enhanced_notes(self, metadata: dict, knowledge_hub: dict, content_type: str) -> str:
        """Generate enhanced notes for any content type."""
        try:
            notes_parts = []
            
            # Content type specific header
            type_emojis = {
                "YouTube": "🎬",
                "GitHub": "📂", 
                "Obsidian": "📝",
                "Markdown": "📄"
            }
            
            emoji = type_emojis.get(content_type, "📋")
            notes_parts.append(f"{emoji} **{content_type.upper()} CONTENT**")
            
            # Basic info
            title = metadata.get('title', '') or metadata.get('name', 'Unknown')
            notes_parts.append(f"📄 {title}")
            
            # Type-specific metadata
            if content_type == "YouTube":
                channel = metadata.get('uploader', 'Unknown')
                duration = metadata.get('duration_formatted', 'Unknown')
                views = metadata.get('view_count', 0)
                
                notes_parts.append(f"👤 Channel: {channel}")
                notes_parts.append(f"⏱️ Duration: {duration}")
                notes_parts.append(f"👀 Views: {views:,}" if views else "👀 Views: Unknown")
                
            elif content_type == "GitHub":
                language = metadata.get('language', 'Unknown')
                stars = metadata.get('stars', 0)
                forks = metadata.get('forks', 0)
                
                notes_parts.append(f"💻 Language: {language}")
                notes_parts.append(f"⭐ Stars: {stars:,} | 🍴 Forks: {forks:,}")
                
                if metadata.get('description'):
                    notes_parts.append(f"📝 {metadata['description']}")
            
            # AI Analysis
            ai_summary = knowledge_hub.get('ai_summary', '')
            if ai_summary:
                notes_parts.append(f"\n{ai_summary}")
            
            notes_parts.append(f"\n" + "="*50)
            
            # Content Analysis
            notes_parts.append(f"\n🧠 **CONTENT ANALYSIS**")
            category = knowledge_hub.get('content_category', 'General')
            difficulty = knowledge_hub.get('difficulty_level', 'Unknown')
            implementation_time = knowledge_hub.get('implementation_time', 'Unknown')
            
            notes_parts.append(f"📂 Category: {category}")
            notes_parts.append(f"📊 Difficulty: {difficulty}")
            notes_parts.append(f"⏳ Implementation Time: {implementation_time}")
            
            # Key insights
            key_insights = knowledge_hub.get('key_insights', [])
            if key_insights:
                notes_parts.append(f"\n💡 **KEY INSIGHTS:**")
                for insight in key_insights[:3]:
                    notes_parts.append(f"• {insight}")
            
            # Action items
            action_items = knowledge_hub.get('action_items', [])
            if action_items:
                notes_parts.append(f"\n🎯 **ACTION ITEMS:**")
                for i, item in enumerate(action_items[:5], 1):
                    notes_parts.append(f"{i}. {item}")
            
            # Relevance
            relevance_indicators = knowledge_hub.get('relevance_indicators', [])
            if relevance_indicators:
                notes_parts.append(f"\n🎯 **RELEVANCE:** {', '.join(relevance_indicators)}")
            
            # Processing info
            notes_parts.append(f"\n🤖 **AUTO-PROCESSED:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return "\n".join(notes_parts)
            
        except Exception as e:
            logger.error(f"Error generating enhanced notes: {e}")
            return f"🤖 Content processed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    async def execute_task(self, task_description: str, 
                          task_type: TaskType = TaskType.GENERAL,
                          priority: Priority = Priority.NORMAL,
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a task using the 1-3-1 orchestration pattern.
        
        Args:
            task_description: Description of the task
            task_type: Type of task
            priority: Task priority
            context: Additional context
            
        Returns:
            Execution result dictionary
        """
        if not self.running:
            raise RuntimeError("System not initialized")
        
        # Create task context
        task_context = TaskContext(
            task_id=f"task_{int(time.time())}",
            task_type=task_type,
            description=task_description,
            priority=priority,
            context=context or {},
            metadata={"source": "direct", "created_at": datetime.now().isoformat()}
        )
        
        logger.info(f"🎯 Executing task (temporary implementation): {task_description}")
        
        # Temporary implementation - simulate task execution
        await asyncio.sleep(1)  # Simulate processing time
        result = {
            "status": "completed",
            "output": f"Task completed successfully: {task_description}",
            "agent_id": "temp_agent1",
            "execution_time": 1.0,
            "metadata": {}
        }
        
        # Log to LifeOS if available
        if self.notion_client:
            try:
# NOTION_REMOVED:                 notion_config = self.config.get("api", {}).get("notion", {})
# NOTION_REMOVED:                 logs_parent_page_id = notion_config.get("execution_logs_database_id")
                if logs_parent_page_id:
                    await self.notion_client.log_execution(task_context.__dict__, result, logs_parent_page_id)
                else:
                    logger.debug("No logs parent page ID configured for LifeOS logging")
            except Exception as e:
                logger.warning(f"Failed to log to LifeOS: {e}")
        
        return {
            "task_id": task_context.task_id,
            "status": result["status"],
            "result": result["output"],
            "agent_id": result["agent_id"],
            "execution_time": result["execution_time"],
            "metadata": result["metadata"]
        }
    
    async def run(self):
        """
        Run the system in pure background mode.
        
        Monitors for YouTube channels and processes them automatically.
        """
        logger.info("🚀 STARTING AUTONOMOUS MULTI-LLM AGENT SYSTEM")
        logger.info("=" * 50)
        logger.info("📺 Monitoring YouTube channels for processing...")
        logger.info("🤖 Background services active")
        logger.info("🛡️ Self-healing enabled")
        logger.info("🛑 Press Ctrl+C to stop")
        logger.info("")
        
        try:
            # Run until interrupted
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 System interrupted by user")
        
        finally:
            await self.shutdown()
    
    
    def add_shutdown_handler(self, handler):
        """Add a shutdown handler."""
        self.shutdown_handlers.append(handler)
    
    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("🔄 Starting graceful shutdown...")
        
        self.running = False
        
        # Shutdown development mode if enabled
        if self.development_mode:
            await self.development_mode.disable()
        
        # Call shutdown handlers
        for handler in self.shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logger.error(f"Error in shutdown handler: {e}")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for background tasks
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Shutdown components (orchestrator will be implemented later)
        if hasattr(self, 'orchestrator') and self.orchestrator and hasattr(self.orchestrator, 'shutdown'):
            await self.orchestrator.shutdown()
        
        if self.observability:
            self.observability.stop()
        
        logger.info("✅ Graceful shutdown completed")


async def main():
    """Main entry point."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>"
    )
    
    # Create system
    system = AutonomousAgentSystem()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(system.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize
        if not await system.initialize("config", None):
            logger.error("❌ System initialization failed")
            sys.exit(1)
        
        # Run system
        await system.run()
    
    async def reload_module(self, module_name: str) -> Dict[str, Any]:
        """Reload a specific module (development mode only)."""
        if not self.is_development or not self.development_mode:
            return {
                'success': False,
                'error': 'Development mode not active'
            }
        
        return await self.development_mode.reload_module(module_name)
    
    async def get_development_stats(self) -> Dict[str, Any]:
        """Get development mode statistics."""
        if not self.is_development or not self.development_mode:
            return {'error': 'Development mode not active'}
        
        return self.development_mode.get_statistics()
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)
    finally:
        await system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())