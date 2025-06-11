#!/usr/bin/env python3
"""
LifeOS Mapper
=============

Comprehensive discovery and mapping of Mike's LifeOS Notion workspace.
Maps all databases, pages, and relationships to understand automation opportunities.
"""

import asyncio
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger


class LifeOSMapper:
    """
    Maps and analyzes the complete LifeOS Notion workspace structure.
    """
    
        self.headers = {
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        # Discovery results
        self.workspace_map = {
            "databases": {},
            "pages": {},
            "relationships": {},
            "automation_opportunities": {},
            "discovered_at": datetime.now().isoformat()
        }
    
    async def discover_complete_workspace(self) -> Dict[str, Any]:
        """
        Discover and map the complete LifeOS workspace.
        """
        logger.info("🔍 STARTING LIFEOS WORKSPACE DISCOVERY")
        logger.info("=" * 50)
        
        try:
            # Step 1: Discover all accessible content
            logger.info("📋 Step 1: Discovering all accessible content...")
            all_content = await self._discover_all_content()
            
            # Step 2: Analyze databases in detail
            logger.info("🗄️ Step 2: Analyzing database structures...")
            await self._analyze_databases(all_content['databases'])
            
            # Step 3: Analyze pages and their connections
            logger.info("📄 Step 3: Analyzing pages and connections...")
            await self._analyze_pages(all_content['pages'])
            
            # Step 4: Map relationships between components
            logger.info("🔗 Step 4: Mapping relationships...")
            await self._map_relationships()
            
            # Step 5: Identify automation opportunities
            logger.info("🤖 Step 5: Identifying automation opportunities...")
            await self._identify_automation_opportunities()
            
            # Step 6: Generate comprehensive report
            logger.info("📊 Step 6: Generating workspace analysis...")
            report = await self._generate_workspace_report()
            
            logger.info("✅ LifeOS workspace discovery completed!")
            return report
            
        except Exception as e:
            logger.error(f"❌ Discovery failed: {e}")
            return {"error": str(e)}
    
    async def _discover_all_content(self) -> Dict[str, List]:
        """
        Discover all accessible databases and pages.
        """
        try:
            databases = []
            pages = []
            
            # Search for databases
            db_response = requests.post(
                headers=self.headers,
                json={
                    'filter': {'property': 'object', 'value': 'database'},
                    'page_size': 100
                },
                timeout=15
            )
            
            if db_response.status_code == 200:
                db_data = db_response.json()
                databases = db_data.get('results', [])
                logger.info(f"   📊 Found {len(databases)} databases")
            
            # Search for pages
            page_response = requests.post(
                headers=self.headers,
                json={
                    'filter': {'property': 'object', 'value': 'page'},
                    'page_size': 100
                },
                timeout=15
            )
            
            if page_response.status_code == 200:
                page_data = page_response.json()
                pages = page_data.get('results', [])
                logger.info(f"   📄 Found {len(pages)} pages")
            
            return {"databases": databases, "pages": pages}
            
        except Exception as e:
            logger.error(f"Error discovering content: {e}")
            return {"databases": [], "pages": []}
    
    async def _analyze_databases(self, databases: List[Dict]) -> None:
        """
        Analyze each database structure in detail.
        """
        try:
            for db in databases:
                db_id = db.get('id', '')
                title_list = db.get('title', [])
                db_title = title_list[0].get('plain_text', 'Untitled') if title_list else 'Untitled'
                
                logger.info(f"   🔍 Analyzing database: {db_title}")
                
                # Get detailed database schema
                schema_response = requests.get(
                    headers=self.headers,
                    timeout=10
                )
                
                if schema_response.status_code == 200:
                    schema_data = schema_response.json()
                    
                    # Analyze properties
                    properties = schema_data.get('properties', {})
                    property_analysis = {}
                    
                    for prop_name, prop_data in properties.items():
                        prop_type = prop_data.get('type', 'unknown')
                        
                        analysis = {
                            "type": prop_type,
                            "config": {}
                        }
                        
                        # Extract type-specific configuration
                        if prop_type == 'select':
                            options = prop_data.get('select', {}).get('options', [])
                            analysis["config"]["options"] = [opt.get('name', '') for opt in options]
                        elif prop_type == 'multi_select':
                            options = prop_data.get('multi_select', {}).get('options', [])
                            analysis["config"]["options"] = [opt.get('name', '') for opt in options]
                        elif prop_type == 'relation':
                            analysis["config"]["database_id"] = prop_data.get('relation', {}).get('database_id', '')
                        elif prop_type == 'formula':
                            analysis["config"]["expression"] = prop_data.get('formula', {}).get('expression', '')
                        
                        property_analysis[prop_name] = analysis
                    
# DEMO CODE REMOVED: # Sample some entries to understand usage patterns
# DEMO CODE REMOVED: sample_entries = await self._sample_database_entries(db_id, 5)
                    
                    # Analyze automation potential
                    automation_analysis = await self._analyze_database_automation_potential(
# DEMO CODE REMOVED: db_title, property_analysis, sample_entries
                    )
                    
                    self.workspace_map["databases"][db_id] = {
                        "title": db_title,
                        "properties": property_analysis,
# DEMO CODE REMOVED: "sample_entries": sample_entries,
                        "automation_potential": automation_analysis,
                        "created_time": schema_data.get('created_time', ''),
                        "last_edited_time": schema_data.get('last_edited_time', '')
                    }
                
                await asyncio.sleep(1)  # Rate limiting
                
        except Exception as e:
            logger.error(f"Error analyzing databases: {e}")
    
# DEMO CODE REMOVED: async def _sample_database_entries(self, db_id: str, limit: int = 5) -> List[Dict]:
        """
# DEMO CODE REMOVED: Sample entries from a database to understand data patterns.
        """
        try:
            response = requests.post(
                headers=self.headers,
                json={'page_size': limit},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                entries = data.get('results', [])
                
                # Extract meaningful data from entries
                processed_entries = []
                for entry in entries:
                    processed_entry = {
                        "id": entry.get('id', ''),
                        "created_time": entry.get('created_time', ''),
                        "last_edited_time": entry.get('last_edited_time', ''),
                        "property_values": {}
                    }
                    
                    properties = entry.get('properties', {})
                    for prop_name, prop_value in properties.items():
                        processed_entry["property_values"][prop_name] = self._extract_property_value(prop_value)
                    
                    processed_entries.append(processed_entry)
                
                return processed_entries
            
            return []
            
        except Exception as e:
            logger.error(f"Error sampling database entries: {e}")
            return []
    
    def _extract_property_value(self, prop_value: Dict) -> Any:
        """
        Extract readable value from Notion property.
        """
        prop_type = prop_value.get('type', 'unknown')
        
        try:
            if prop_type == 'title':
                title_list = prop_value.get('title', [])
                return title_list[0].get('plain_text', '') if title_list else ''
            elif prop_type == 'rich_text':
                text_list = prop_value.get('rich_text', [])
                return text_list[0].get('plain_text', '') if text_list else ''
            elif prop_type == 'select':
                select_data = prop_value.get('select')
                return select_data.get('name', '') if select_data else ''
            elif prop_type == 'multi_select':
                options = prop_value.get('multi_select', [])
                return [opt.get('name', '') for opt in options]
            elif prop_type == 'number':
                return prop_value.get('number')
            elif prop_type == 'checkbox':
                return prop_value.get('checkbox', False)
            elif prop_type == 'url':
                return prop_value.get('url', '')
            elif prop_type == 'email':
                return prop_value.get('email', '')
            elif prop_type == 'phone_number':
                return prop_value.get('phone_number', '')
            elif prop_type == 'date':
                date_data = prop_value.get('date')
                return date_data.get('start', '') if date_data else ''
            elif prop_type == 'people':
                people = prop_value.get('people', [])
                return [person.get('name', '') for person in people]
            elif prop_type == 'files':
                files = prop_value.get('files', [])
                return [file.get('name', '') for file in files]
            elif prop_type == 'relation':
                relations = prop_value.get('relation', [])
                return [rel.get('id', '') for rel in relations]
            elif prop_type == 'formula':
                formula_result = prop_value.get('formula', {})
                formula_type = formula_result.get('type', '')
                if formula_type == 'string':
                    return formula_result.get('string', '')
                elif formula_type == 'number':
                    return formula_result.get('number')
                elif formula_type == 'boolean':
                    return formula_result.get('boolean', False)
            
            return str(prop_value)  # Fallback
            
        except Exception:
            return 'extraction_error'
    
# DEMO CODE REMOVED: async def _analyze_database_automation_potential(self, title: str, properties: Dict, samples: List) -> Dict:
        """
        Analyze automation potential for a database.
        """
        automation_opportunities = {
            "workflow_triggers": [],
            "auto_updates": [],
            "data_flows": [],
            "content_processing": [],
            "notifications": [],
            "integrations": []
        }
        
        try:
            # Analyze triggers based on properties
            for prop_name, prop_info in properties.items():
                prop_type = prop_info["type"]
                
                # Checkbox triggers
                if prop_type == "checkbox":
                    automation_opportunities["workflow_triggers"].append({
                        "type": "checkbox_trigger",
                        "property": prop_name,
                        "description": f"Trigger workflows when {prop_name} is checked"
                    })
                
                # Status-based workflows
                if prop_type == "select" and any(keyword in prop_name.lower() for keyword in ["status", "stage", "phase"]):
                    options = prop_info.get("config", {}).get("options", [])
                    automation_opportunities["workflow_triggers"].append({
                        "type": "status_change_trigger",
                        "property": prop_name,
                        "options": options,
                        "description": f"Trigger actions based on {prop_name} changes"
                    })
                
                # URL-based content processing
                if prop_type == "url":
                    automation_opportunities["content_processing"].append({
                        "type": "url_processing",
                        "property": prop_name,
                        "description": f"Auto-process content from URLs in {prop_name}"
                    })
                
                # Date-based automation
                if prop_type == "date":
                    automation_opportunities["notifications"].append({
                        "type": "date_reminder",
                        "property": prop_name,
                        "description": f"Send reminders based on {prop_name}"
                    })
                
                # Relation-based data flows
                if prop_type == "relation":
                    related_db = prop_info.get("config", {}).get("database_id", "")
                    automation_opportunities["data_flows"].append({
                        "type": "relation_sync",
                        "property": prop_name,
                        "related_database": related_db,
                        "description": f"Sync data between databases via {prop_name}"
                    })
            
            # Analyze based on database title/purpose
            title_lower = title.lower()
            
            if "task" in title_lower or "todo" in title_lower:
                automation_opportunities["integrations"].extend([
                    {"type": "task_management", "description": "Auto-create tasks from various sources"},
                    {"type": "deadline_tracking", "description": "Monitor and alert on task deadlines"},
                    {"type": "progress_reporting", "description": "Generate progress reports"}
                ])
            
            if "knowledge" in title_lower or "hub" in title_lower:
                automation_opportunities["integrations"].extend([
                    {"type": "content_curation", "description": "Auto-categorize and tag content"},
                    {"type": "ai_summarization", "description": "Generate AI summaries for content"},
                    {"type": "learning_tracking", "description": "Track learning progress and insights"}
                ])
            
            if "project" in title_lower:
                automation_opportunities["integrations"].extend([
                    {"type": "project_tracking", "description": "Monitor project milestones and health"},
                    {"type": "resource_allocation", "description": "Track and optimize resource usage"},
                    {"type": "stakeholder_updates", "description": "Auto-generate project updates"}
                ])
            
            if "calendar" in title_lower or "schedule" in title_lower:
                automation_opportunities["integrations"].extend([
                    {"type": "calendar_sync", "description": "Sync with external calendars"},
                    {"type": "meeting_automation", "description": "Auto-schedule and prepare meetings"},
                    {"type": "time_blocking", "description": "Optimize time allocation"}
                ])
            
            return automation_opportunities
            
        except Exception as e:
            logger.error(f"Error analyzing automation potential: {e}")
            return automation_opportunities
    
    async def _analyze_pages(self, pages: List[Dict]) -> None:
        """
        Analyze pages and their potential for automation.
        """
        try:
            for page in pages[:20]:  # Limit to first 20 pages
                page_id = page.get('id', '')
                
                # Get page title
                title = "Untitled"
                properties = page.get('properties', {})
                for prop_name, prop_data in properties.items():
                    if prop_data.get('type') == 'title':
                        title_list = prop_data.get('title', [])
                        if title_list:
                            title = title_list[0].get('plain_text', 'Untitled')
                        break
                
                logger.info(f"   📄 Analyzing page: {title}")
                
                # Analyze page for automation opportunities
                page_analysis = {
                    "title": title,
                    "created_time": page.get('created_time', ''),
                    "last_edited_time": page.get('last_edited_time', ''),
                    "automation_potential": await self._analyze_page_automation_potential(page_id, title)
                }
                
                self.workspace_map["pages"][page_id] = page_analysis
                
                await asyncio.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            logger.error(f"Error analyzing pages: {e}")
    
    async def _analyze_page_automation_potential(self, page_id: str, title: str) -> Dict:
        """
        Analyze automation potential for a specific page.
        """
        opportunities = {
            "content_automation": [],
            "workflow_integration": [],
            "data_sync": []
        }
        
        try:
            title_lower = title.lower()
            
            # Dashboard pages
            if "dashboard" in title_lower:
                opportunities["content_automation"].extend([
                    {"type": "dashboard_updates", "description": "Auto-refresh dashboard metrics"},
                    {"type": "kpi_tracking", "description": "Track and visualize KPIs"},
                    {"type": "alert_system", "description": "Send alerts based on dashboard data"}
                ])
            
            # Template pages
            if "template" in title_lower:
                opportunities["workflow_integration"].append({
                    "type": "template_instantiation", 
                    "description": "Auto-create instances from templates"
                })
            
            # Index/Hub pages
            if any(keyword in title_lower for keyword in ["index", "hub", "overview"]):
                opportunities["content_automation"].append({
                    "type": "content_aggregation", 
                    "description": "Auto-aggregate related content"
                })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error analyzing page automation: {e}")
            return opportunities
    
    async def _map_relationships(self) -> None:
        """
        Map relationships between databases and pages.
        """
        try:
            relationships = {
                "database_relations": {},
                "page_database_connections": {},
                "data_flow_patterns": []
            }
            
            # Analyze database relationships through relation properties
            for db_id, db_info in self.workspace_map["databases"].items():
                db_title = db_info["title"]
                properties = db_info["properties"]
                
                for prop_name, prop_info in properties.items():
                    if prop_info["type"] == "relation":
                        related_db_id = prop_info.get("config", {}).get("database_id", "")
                        if related_db_id in self.workspace_map["databases"]:
                            related_db_title = self.workspace_map["databases"][related_db_id]["title"]
                            
                            relationship_key = f"{db_id}->{related_db_id}"
                            relationships["database_relations"][relationship_key] = {
                                "source_db": db_title,
                                "target_db": related_db_title,
                                "relation_property": prop_name,
                                "automation_potential": "bidirectional_sync"
                            }
            
            self.workspace_map["relationships"] = relationships
            
        except Exception as e:
            logger.error(f"Error mapping relationships: {e}")
    
    async def _identify_automation_opportunities(self) -> None:
        """
        Identify comprehensive automation opportunities across the workspace.
        """
        try:
            opportunities = {
                "workflow_automation": [],
                "content_processing": [],
                "data_synchronization": [],
                "notification_systems": [],
                "ai_enhancement": [],
                "integration_points": []
            }
            
            # Aggregate opportunities from all databases
            for db_id, db_info in self.workspace_map["databases"].items():
                db_title = db_info["title"]
                db_automation = db_info.get("automation_potential", {})
                
                # Workflow automation
                for trigger in db_automation.get("workflow_triggers", []):
                    opportunities["workflow_automation"].append({
                        "database": db_title,
                        "database_id": db_id,
                        **trigger
                    })
                
                # Content processing
                for content_op in db_automation.get("content_processing", []):
                    opportunities["content_processing"].append({
                        "database": db_title,
                        "database_id": db_id,
                        **content_op
                    })
                
                # Integration points
                for integration in db_automation.get("integrations", []):
                    opportunities["integration_points"].append({
                        "database": db_title,
                        "database_id": db_id,
                        **integration
                    })
            
            # Cross-database automation opportunities
            if len(self.workspace_map["databases"]) > 1:
                opportunities["data_synchronization"].append({
                    "type": "cross_database_sync",
                    "description": "Sync data between related databases",
                    "priority": "high"
                })
                
                opportunities["ai_enhancement"].append({
                    "type": "workspace_intelligence",
                    "description": "AI-powered insights across all databases",
                    "priority": "high"
                })
            
            # Global notification system
            opportunities["notification_systems"].append({
                "type": "unified_notifications",
                "description": "Centralized notification system for all workspace activities",
                "priority": "medium"
            })
            
            self.workspace_map["automation_opportunities"] = opportunities
            
        except Exception as e:
            logger.error(f"Error identifying automation opportunities: {e}")
    
    async def _generate_workspace_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive workspace analysis report.
        """
        try:
            report = {
                "workspace_summary": {
                    "total_databases": len(self.workspace_map["databases"]),
                    "total_pages": len(self.workspace_map["pages"]),
                    "total_relationships": len(self.workspace_map["relationships"].get("database_relations", {})),
                    "automation_potential": "high"
                },
                "database_analysis": {},
                "automation_roadmap": {},
                "implementation_priority": [],
                "full_workspace_map": self.workspace_map
            }
            
            # Database analysis summary
            for db_id, db_info in self.workspace_map["databases"].items():
                db_title = db_info["title"]
                properties_count = len(db_info["properties"])
                
                report["database_analysis"][db_title] = {
                    "id": db_id,
                    "properties_count": properties_count,
# DEMO CODE REMOVED: "sample_entries_count": len(db_info["sample_entries"]),
                    "automation_opportunities": len([
                        item for sublist in db_info.get("automation_potential", {}).values() 
                        if isinstance(sublist, list) for item in sublist
                    ])
                }
            
            # Automation roadmap
            automation_ops = self.workspace_map.get("automation_opportunities", {})
            
            report["automation_roadmap"] = {
                "phase_1_immediate": {
                    "workflow_triggers": len(automation_ops.get("workflow_automation", [])),
                    "content_processing": len(automation_ops.get("content_processing", [])),
                    "description": "Implement checkbox triggers and content processing"
                },
                "phase_2_integration": {
                    "data_sync": len(automation_ops.get("data_synchronization", [])),
                    "notifications": len(automation_ops.get("notification_systems", [])),
                    "description": "Cross-database sync and notification systems"
                },
                "phase_3_intelligence": {
                    "ai_enhancement": len(automation_ops.get("ai_enhancement", [])),
                    "advanced_integrations": len(automation_ops.get("integration_points", [])),
                    "description": "AI-powered insights and advanced automations"
                }
            }
            
            # Implementation priority
            priority_items = []
            
            # High priority: Knowledge Hub and Task management
            for db_title, db_analysis in report["database_analysis"].items():
                if any(keyword in db_title.lower() for keyword in ["knowledge", "task", "hub"]):
                    priority_items.append({
                        "type": "database_automation",
                        "target": db_title,
                        "priority": "high",
                        "reason": "Core productivity system"
                    })
            
            # Medium priority: Project and calendar systems
            for db_title, db_analysis in report["database_analysis"].items():
                if any(keyword in db_title.lower() for keyword in ["project", "calendar", "schedule"]):
                    priority_items.append({
                        "type": "database_automation",
                        "target": db_title,
                        "priority": "medium",
                        "reason": "Project and time management"
                    })
            
            report["implementation_priority"] = priority_items
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {"error": str(e)}


# Factory function
    """Create a LifeOS mapper instance."""