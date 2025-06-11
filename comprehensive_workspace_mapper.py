#!/usr/bin/env python3
"""
Comprehensive Notion Workspace Mapper
=====================================

This script performs a complete mapping of a Notion workspace to understand:
1. All databases and their properties
2. Property types, options, and configurations
3. Relationships between databases
# DEMO CODE REMOVED: 4. Sample data to understand usage patterns
5. Checkbox fields that need automation backends
6. Complete workspace structure for automation planning

Generates a detailed workspace_mapping.json file with all discovered information.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from loguru import logger
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from integrations.notion_mcp_client 

@dataclass
class PropertyInfo:
    """Information about a database property."""
    name: str
    type: str
    id: str
    configuration: Dict[str, Any]
    options: List[str] = None
    formula: str = None
    relation_database: str = None
    rollup_property: str = None


@dataclass
class DatabaseInfo:
    """Comprehensive information about a database."""
    id: str
    title: str
    url: str
    properties: List[PropertyInfo]
    created_time: str
    last_edited_time: str
    parent: Dict[str, Any]
    is_inline: bool
    description: List[Dict[str, Any]]
    cover: Dict[str, Any]
    icon: Dict[str, Any]
# DEMO CODE REMOVED: sample_pages: List[Dict[str, Any]]
    checkbox_properties: List[str]
    relation_properties: List[str]
    formula_properties: List[str]
    rollup_properties: List[str]
    total_pages: int


@dataclass
class WorkspaceMapping:
    """Complete workspace mapping."""
    workspace_name: str
    discovery_date: str
    total_databases: int
    total_pages: int
    databases: List[DatabaseInfo]
    database_relationships: Dict[str, List[str]]
    checkbox_automation_candidates: List[Dict[str, Any]]
    property_type_summary: Dict[str, int]
    automation_recommendations: List[Dict[str, Any]]


class ComprehensiveWorkspaceMapper:
    """
    Comprehensive mapper for Notion workspace discovery and analysis.
    """
    
        """Initialize the workspace mapper."""
        self.discovered_databases = []
        self.database_relationships = {}
        self.checkbox_candidates = []
        self.property_types = {}
        
        logger.info("Comprehensive Workspace Mapper initialized")
    
    async def discover_all_databases(self) -> List[Dict[str, Any]]:
        """Discover all databases in the workspace."""
        logger.info("🔍 Discovering all databases in workspace...")
        
        try:
            # Search for all databases
            all_results = []
            page_size = 100
            start_cursor = None
            
            while True:
                search_params = {
                    "filter": {
                        "value": "database",
                        "property": "object"
                    },
                    "page_size": page_size
                }
                
                if start_cursor:
                    search_params["start_cursor"] = start_cursor
                
                # Use the MCP client's search functionality
# NOTION_REMOVED:                 result = await self.notion._call_mcp_tool("API-post-search", search_params)
                
                if "error" in result:
                    logger.error(f"Error searching databases: {result['error']}")
                    break
                
                # Parse results
                content = result.get("content", [])
                if content and isinstance(content[0], dict) and "text" in content[0]:
                    search_data = json.loads(content[0]["text"])
                    results = search_data.get("results", [])
                    all_results.extend(results)
                    
                    # Check if there are more pages
                    has_more = search_data.get("has_more", False)
                    if not has_more:
                        break
                    
                    start_cursor = search_data.get("next_cursor")
                else:
                    break
            
            logger.info(f"📊 Discovered {len(all_results)} databases")
            return all_results
            
        except Exception as e:
            logger.error(f"Error discovering databases: {e}")
            return []
    
    async def analyze_database_properties(self, database: Dict[str, Any]) -> DatabaseInfo:
        """Analyze a database's properties in detail."""
        logger.info(f"🔬 Analyzing database: {database.get('title', [{}])[0].get('plain_text', 'Unknown')}")
        
        database_id = database.get("id", "")
        title = database.get("title", [{}])[0].get("plain_text", "Unknown")
        properties = database.get("properties", {})
        
        # Analyze each property
        property_infos = []
        checkbox_props = []
        relation_props = []
        formula_props = []
        rollup_props = []
        
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type", "unknown")
            prop_id = prop_data.get("id", "")
            
            # Extract configuration based on type
            configuration = {}
            options = []
            formula = None
            relation_database = None
            rollup_property = None
            
            if prop_type == "select":
                options = [opt.get("name", "") for opt in prop_data.get("select", {}).get("options", [])]
                configuration = prop_data.get("select", {})
            elif prop_type == "multi_select":
                options = [opt.get("name", "") for opt in prop_data.get("multi_select", {}).get("options", [])]
                configuration = prop_data.get("multi_select", {})
            elif prop_type == "formula":
                formula = prop_data.get("formula", {}).get("expression", "")
                configuration = prop_data.get("formula", {})
                formula_props.append(prop_name)
            elif prop_type == "relation":
                relation_database = prop_data.get("relation", {}).get("database_id", "")
                configuration = prop_data.get("relation", {})
                relation_props.append(prop_name)
            elif prop_type == "rollup":
                rollup_property = prop_data.get("rollup", {}).get("rollup_property_name", "")
                relation_database = prop_data.get("rollup", {}).get("relation_property_id", "")
                configuration = prop_data.get("rollup", {})
                rollup_props.append(prop_name)
            elif prop_type == "checkbox":
                checkbox_props.append(prop_name)
                configuration = prop_data.get("checkbox", {})
            else:
                configuration = prop_data.get(prop_type, {})
            
            property_info = PropertyInfo(
                name=prop_name,
                type=prop_type,
                id=prop_id,
                configuration=configuration,
                options=options if options else None,
                formula=formula,
                relation_database=relation_database,
                rollup_property=rollup_property
            )
            
            property_infos.append(property_info)
            
            # Track property types
            self.property_types[prop_type] = self.property_types.get(prop_type, 0) + 1
        
# DEMO CODE REMOVED: # Get sample pages from this database
# DEMO CODE REMOVED: sample_pages = await self.get_sample_pages(database_id, 5)
        
        # Count total pages
        total_pages = await self.count_database_pages(database_id)
        
        # Track relationships
        if relation_props:
            self.database_relationships[database_id] = relation_props
        
        # Track checkbox automation candidates
        for checkbox_prop in checkbox_props:
            self.checkbox_candidates.append({
                "database_id": database_id,
                "database_title": title,
                "property_name": checkbox_prop,
                "automation_potential": "high"  # All checkboxes are potential automation targets
            })
        
        database_info = DatabaseInfo(
            id=database_id,
            title=title,
            url=database.get("url", ""),
            properties=property_infos,
            created_time=database.get("created_time", ""),
            last_edited_time=database.get("last_edited_time", ""),
            parent=database.get("parent", {}),
            is_inline=database.get("is_inline", False),
            description=database.get("description", []),
            cover=database.get("cover"),
            icon=database.get("icon"),
# DEMO CODE REMOVED: sample_pages=sample_pages,
            checkbox_properties=checkbox_props,
            relation_properties=relation_props,
            formula_properties=formula_props,
            rollup_properties=rollup_props,
            total_pages=total_pages
        )
        
        return database_info
    
# DEMO CODE REMOVED: async def get_sample_pages(self, database_id: str, limit: int = 5) -> List[Dict[str, Any]]:
# DEMO CODE REMOVED: """Get sample pages from a database."""
        try:
            params = {
                "database_id": database_id,
                "page_size": limit
            }
            
# NOTION_REMOVED:             result = await self.notion._call_mcp_tool("API-post-database-query", params)
            
            if "error" in result:
# DEMO CODE REMOVED: logger.warning(f"Error getting sample pages for {database_id}: {result['error']}")
                return []
            
            content = result.get("content", [])
            if content and isinstance(content[0], dict) and "text" in content[0]:
                query_data = json.loads(content[0]["text"])
                return query_data.get("results", [])
            
            return []
            
        except Exception as e:
# DEMO CODE REMOVED: logger.warning(f"Error getting sample pages for {database_id}: {e}")
            return []
    
    async def count_database_pages(self, database_id: str) -> int:
        """Count total pages in a database."""
        try:
            # First query to get total count
            params = {
                "database_id": database_id,
                "page_size": 1
            }
            
# NOTION_REMOVED:             result = await self.notion._call_mcp_tool("API-post-database-query", params)
            
            if "error" in result:
                return 0
            
            content = result.get("content", [])
            if content and isinstance(content[0], dict) and "text" in content[0]:
                query_data = json.loads(content[0]["text"])
                
                # If has_more is True, we need to do pagination to count all
                if query_data.get("has_more", False):
                    # For now, return estimated count (we could implement full pagination)
                    return 100  # Placeholder - would need full pagination to get exact count
                else:
                    return len(query_data.get("results", []))
            
            return 0
            
        except Exception as e:
            logger.warning(f"Error counting pages for {database_id}: {e}")
            return 0
    
    def generate_automation_recommendations(self, databases: List[DatabaseInfo]) -> List[Dict[str, Any]]:
        """Generate automation recommendations based on discovered structure."""
        recommendations = []
        
        # Checkbox automation recommendations
        for candidate in self.checkbox_candidates:
            recommendations.append({
                "type": "checkbox_automation",
                "priority": "high",
                "database_id": candidate["database_id"],
                "database_title": candidate["database_title"],
                "property_name": candidate["property_name"],
                "description": f"Automate {candidate['property_name']} checkbox in {candidate['database_title']}",
                "implementation": "Create backend trigger when checkbox is checked/unchecked"
            })
        
        # Relationship-based automation
        for db_id, relations in self.database_relationships.items():
            db_title = next((db.title for db in databases if db.id == db_id), "Unknown")
            for relation in relations:
                recommendations.append({
                    "type": "relationship_sync",
                    "priority": "medium",
                    "database_id": db_id,
                    "database_title": db_title,
                    "property_name": relation,
                    "description": f"Sync related data for {relation} in {db_title}",
                    "implementation": "Monitor changes and update related records"
                })
        
        # Formula optimization recommendations
        for db in databases:
            if db.formula_properties:
                for formula_prop in db.formula_properties:
                    recommendations.append({
                        "type": "formula_optimization",
                        "priority": "low",
                        "database_id": db.id,
                        "database_title": db.title,
                        "property_name": formula_prop,
                        "description": f"Monitor and optimize formula performance for {formula_prop}",
                        "implementation": "Cache formula results or pre-compute when possible"
                    })
        
        return recommendations
    
    async def generate_comprehensive_mapping(self) -> WorkspaceMapping:
        """Generate complete workspace mapping."""
        logger.info("🗺️ Generating comprehensive workspace mapping...")
        
        # Discover all databases
        raw_databases = await self.discover_all_databases()
        
        # Analyze each database in detail
        analyzed_databases = []
        for raw_db in raw_databases:
            try:
                db_info = await self.analyze_database_properties(raw_db)
                analyzed_databases.append(db_info)
                # Small delay to be respectful to the API
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error analyzing database {raw_db.get('id', 'unknown')}: {e}")
                continue
        
        # Generate automation recommendations
        automation_recommendations = self.generate_automation_recommendations(analyzed_databases)
        
        # Create comprehensive mapping
        mapping = WorkspaceMapping(
            workspace_name="LifeOS Comprehensive Workspace",
            discovery_date=datetime.now().isoformat(),
            total_databases=len(analyzed_databases),
            total_pages=sum(db.total_pages for db in analyzed_databases),
            databases=analyzed_databases,
            database_relationships=self.database_relationships,
            checkbox_automation_candidates=self.checkbox_candidates,
            property_type_summary=self.property_types,
            automation_recommendations=automation_recommendations
        )
        
        logger.info(f"✅ Mapping complete: {mapping.total_databases} databases, {len(mapping.checkbox_automation_candidates)} checkbox automation candidates")
        
        return mapping
    
    def save_mapping_to_file(self, mapping: WorkspaceMapping, filename: str = "workspace_mapping.json"):
        """Save the mapping to a JSON file."""
        logger.info(f"💾 Saving mapping to {filename}...")
        
        # Convert to dictionary for JSON serialization
        mapping_dict = asdict(mapping)
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(mapping_dict, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"✅ Mapping saved to {filename}")
    
    def print_summary(self, mapping: WorkspaceMapping):
        """Print a summary of the workspace mapping."""
        print("\n" + "="*80)
        print("📊 NOTION WORKSPACE COMPREHENSIVE MAPPING SUMMARY")
        print("="*80)
        print(f"Workspace: {mapping.workspace_name}")
        print(f"Discovery Date: {mapping.discovery_date}")
        print(f"Total Databases: {mapping.total_databases}")
        print(f"Total Pages: {mapping.total_pages}")
        print()
        
        print("📋 DATABASE BREAKDOWN:")
        print("-" * 40)
        for db in mapping.databases:
            print(f"• {db.title}")
            print(f"  ID: {db.id}")
            print(f"  Properties: {len(db.properties)}")
            print(f"  Pages: {db.total_pages}")
            if db.checkbox_properties:
                print(f"  Checkboxes: {', '.join(db.checkbox_properties)}")
            if db.relation_properties:
                print(f"  Relations: {', '.join(db.relation_properties)}")
            print()
        
        print("🔲 CHECKBOX AUTOMATION CANDIDATES:")
        print("-" * 40)
        for candidate in mapping.checkbox_automation_candidates:
            print(f"• {candidate['database_title']} → {candidate['property_name']}")
        print()
        
        print("📊 PROPERTY TYPE SUMMARY:")
        print("-" * 40)
        for prop_type, count in sorted(mapping.property_type_summary.items()):
            print(f"• {prop_type}: {count}")
        print()
        
        print("🤖 AUTOMATION RECOMMENDATIONS:")
        print("-" * 40)
        for rec in mapping.automation_recommendations[:10]:  # Show first 10
            print(f"• [{rec['priority'].upper()}] {rec['type']}: {rec['description']}")
        if len(mapping.automation_recommendations) > 10:
            print(f"... and {len(mapping.automation_recommendations) - 10} more recommendations")
        
        print("\n" + "="*80)


async def main():
    """Main function to run the comprehensive workspace mapping."""
    print("🚀 Starting Comprehensive Notion Workspace Mapping...")
    
    # Get Notion token from environment
        print("Please set your Notion API token in the .env file")
        return
    
    try:
        # Initialize mapper
        
        # Test connection
        logger.info("🔌 Testing Notion connection...")
# NOTION_REMOVED:         connection_test = await mapper.notion.test_connection()
        if not connection_test:
            logger.error("❌ Failed to connect to Notion")
            return
        
        logger.info("✅ Notion connection successful")
        
        # Generate comprehensive mapping
        mapping = await mapper.generate_comprehensive_mapping()
        
        # Save to file
        mapper.save_mapping_to_file(mapping)
        
        # Print summary
        mapper.print_summary(mapping)
        
        print("\n✅ Comprehensive workspace mapping completed successfully!")
        print(f"📄 Detailed mapping saved to: workspace_mapping.json")
        
    except Exception as e:
        logger.error(f"❌ Error during workspace mapping: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())