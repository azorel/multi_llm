#!/usr/bin/env python3
"""
Direct Notion API Workspace Mapper
===================================

Uses direct HTTP requests to the Notion API to map workspace structure.
No MCP server dependencies required.
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime


class DirectNotionClient:
    """Direct Notion API client."""
    
    def __init__(self, token: str):
        """Initialize the client."""
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    async def search_databases(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """Search for all databases in the workspace."""
        async with aiohttp.ClientSession() as session:
            search_data = {
                "filter": {
                    "value": "database",
                    "property": "object"
                },
                "page_size": page_size
            }
            
            async with session.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json=search_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("results", [])
                else:
                    error_text = await response.text()
                    print(f"Error searching databases: {response.status} - {error_text}")
                    return []
    
    async def get_database(self, database_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a database."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/databases/{database_id}",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    print(f"Error getting database {database_id}: {response.status} - {error_text}")
                    return None
    
    async def query_database(self, database_id: str, page_size: int = 3) -> List[Dict[str, Any]]:
        """Query database pages."""
        async with aiohttp.ClientSession() as session:
            query_data = {
                "page_size": page_size
            }
            
            async with session.post(
                f"{self.base_url}/databases/{database_id}/query",
                headers=self.headers,
                json=query_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("results", [])
                else:
                    error_text = await response.text()
                    print(f"Error querying database {database_id}: {response.status} - {error_text}")
                    return []


class DirectWorkspaceMapper:
    """Direct workspace mapper using Notion API."""
    
        """Initialize mapper."""
        self.mapping = {
            "workspace_name": "LifeOS Comprehensive Workspace",
            "discovery_date": datetime.now().isoformat(),
            "databases": [],
            "checkbox_automation_candidates": [],
            "property_type_summary": {},
            "automation_recommendations": [],
            "database_relationships": {},
            "total_databases": 0,
            "total_pages": 0
        }
    
    async def discover_databases(self) -> List[Dict[str, Any]]:
        """Discover all databases."""
        print("🔍 Discovering databases...")
        
        try:
# NOTION_REMOVED:             databases = await self.notion.search_databases()
            print(f"📊 Found {len(databases)} databases")
            return databases
        except Exception as e:
            print(f"Error discovering databases: {e}")
            return []
    
    async def analyze_database(self, database: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single database."""
        db_id = database.get("id", "")
        title = ""
        
        # Extract title safely
        try:
            title_obj = database.get("title", [])
            if title_obj and len(title_obj) > 0:
                title = title_obj[0].get("plain_text", "Unknown")
            if not title:
                title = f"Database {db_id[:8]}"
        except:
            title = f"Database {db_id[:8]}"
        
        print(f"🔬 Analyzing: {title}")
        
        # Get detailed database info
# NOTION_REMOVED:         detailed_db = await self.notion.get_database(db_id)
        if not detailed_db:
            print(f"  ⚠️  Could not get detailed info for {title}")
            return None
        
        properties = detailed_db.get("properties", {})
        
        # Analyze properties
        property_analysis = []
        checkbox_properties = []
        relation_properties = []
        formula_properties = []
        rollup_properties = []
        property_types = {}
        
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type", "unknown")
            property_types[prop_type] = property_types.get(prop_type, 0) + 1
            
            prop_info = {
                "name": prop_name,
                "type": prop_type,
                "id": prop_data.get("id", "")
            }
            
            # Handle different property types
            if prop_type == "select":
                options = [opt.get("name", "") for opt in prop_data.get("select", {}).get("options", [])]
                prop_info["options"] = options
                prop_info["configuration"] = prop_data.get("select", {})
            elif prop_type == "multi_select":
                options = [opt.get("name", "") for opt in prop_data.get("multi_select", {}).get("options", [])]
                prop_info["options"] = options
                prop_info["configuration"] = prop_data.get("multi_select", {})
            elif prop_type == "formula":
                formula = prop_data.get("formula", {}).get("expression", "")
                prop_info["formula"] = formula
                prop_info["configuration"] = prop_data.get("formula", {})
                formula_properties.append(prop_name)
            elif prop_type == "relation":
                relation_db = prop_data.get("relation", {}).get("database_id", "")
                prop_info["relation_database"] = relation_db
                prop_info["configuration"] = prop_data.get("relation", {})
                relation_properties.append(prop_name)
            elif prop_type == "rollup":
                rollup_prop = prop_data.get("rollup", {}).get("rollup_property_name", "")
                relation_prop_id = prop_data.get("rollup", {}).get("relation_property_id", "")
                prop_info["rollup_property"] = rollup_prop
                prop_info["relation_property_id"] = relation_prop_id
                prop_info["configuration"] = prop_data.get("rollup", {})
                rollup_properties.append(prop_name)
            elif prop_type == "checkbox":
                checkbox_properties.append(prop_name)
                prop_info["configuration"] = prop_data.get("checkbox", {})
            else:
                prop_info["configuration"] = prop_data.get(prop_type, {})
            
            property_analysis.append(prop_info)
        
# DEMO CODE REMOVED: # Get sample pages
# DEMO CODE REMOVED: sample_pages = await self.get_sample_pages(db_id, 3)
        
        # Update global property type summary
        for prop_type, count in property_types.items():
            self.mapping["property_type_summary"][prop_type] = (
                self.mapping["property_type_summary"].get(prop_type, 0) + count
            )
        
        # Track database relationships
        if relation_properties:
            self.mapping["database_relationships"][db_id] = {
                "database_title": title,
                "relations": relation_properties
            }
        
        # Track checkbox automation candidates
        for checkbox_prop in checkbox_properties:
            self.mapping["checkbox_automation_candidates"].append({
                "database_id": db_id,
                "database_title": title,
                "property_name": checkbox_prop,
                "automation_potential": "high",
                "description": f"Automate {checkbox_prop} checkbox in {title} database"
            })
        
        database_info = {
            "id": db_id,
            "title": title,
            "url": detailed_db.get("url", ""),
            "properties": property_analysis,
            "property_count": len(properties),
            "checkbox_properties": checkbox_properties,
            "relation_properties": relation_properties,
            "formula_properties": formula_properties,
            "rollup_properties": rollup_properties,
# DEMO CODE REMOVED: "sample_pages": sample_pages,
# DEMO CODE REMOVED: "sample_page_count": len(sample_pages),
            "created_time": detailed_db.get("created_time", ""),
            "last_edited_time": detailed_db.get("last_edited_time", ""),
            "parent": detailed_db.get("parent", {}),
            "is_inline": detailed_db.get("is_inline", False),
            "description": detailed_db.get("description", []),
            "cover": detailed_db.get("cover"),
            "icon": detailed_db.get("icon")
        }
        
        return database_info
    
# DEMO CODE REMOVED: async def get_sample_pages(self, database_id: str, limit: int = 3) -> List[Dict[str, Any]]:
# DEMO CODE REMOVED: """Get sample pages from database."""
        try:
# NOTION_REMOVED:             pages = await self.notion.query_database(database_id, limit)
            return pages
        except Exception as e:
# DEMO CODE REMOVED: print(f"  ⚠️  Error getting sample pages: {e}")
            return []
    
    def generate_automation_recommendations(self):
        """Generate automation recommendations."""
        recommendations = []
        
        # Checkbox automation - highest priority
        for candidate in self.mapping["checkbox_automation_candidates"]:
            recommendations.append({
                "type": "checkbox_automation",
                "priority": "high",
                "database_id": candidate["database_id"],
                "database_title": candidate["database_title"],
                "property_name": candidate["property_name"],
                "description": candidate["description"],
                "implementation": f"Create webhook listener for {candidate['property_name']} checkbox changes",
                "estimated_effort": "low",
                "business_value": "high"
            })
        
        # Relationship synchronization
        for db_id, rel_info in self.mapping["database_relationships"].items():
            for relation in rel_info["relations"]:
                recommendations.append({
                    "type": "relationship_sync",
                    "priority": "medium",
                    "database_id": db_id,
                    "database_title": rel_info["database_title"],
                    "property_name": relation,
                    "description": f"Auto-sync {relation} relationships in {rel_info['database_title']}",
                    "implementation": "Monitor relationship changes and maintain data consistency",
                    "estimated_effort": "medium",
                    "business_value": "medium"
                })
        
        # Complex database optimization
        for db in self.mapping["databases"]:
            if db["property_count"] > 15:
                recommendations.append({
                    "type": "complex_database_optimization",
                    "priority": "low",
                    "database_id": db["id"],
                    "database_title": db["title"],
                    "description": f"Optimize complex database: {db['title']} ({db['property_count']} properties)",
                    "implementation": "Create templates, validation rules, and automated workflows",
                    "estimated_effort": "high",
                    "business_value": "medium"
                })
        
        # Formula performance monitoring
        for db in self.mapping["databases"]:
            if db["formula_properties"]:
                for formula_prop in db["formula_properties"]:
                    recommendations.append({
                        "type": "formula_optimization",
                        "priority": "low",
                        "database_id": db["id"],
                        "database_title": db["title"],
                        "property_name": formula_prop,
                        "description": f"Monitor formula performance: {formula_prop} in {db['title']}",
                        "implementation": "Cache formula results or optimize expressions",
                        "estimated_effort": "medium",
                        "business_value": "low"
                    })
        
        self.mapping["automation_recommendations"] = recommendations
    
    async def run_comprehensive_mapping(self):
        """Run the complete mapping process."""
        print("🗺️ Starting comprehensive workspace mapping...")
        
        # Test connection first
        print("🔌 Testing Notion API connection...")
        try:
# NOTION_REMOVED:             test_search = await self.notion.search_databases(page_size=1)
            print("✅ Notion API connection successful")
        except Exception as e:
            print(f"❌ Notion API connection failed: {e}")
            return
        
        # Discover all databases
        databases = await self.discover_databases()
        
        if not databases:
            print("❌ No databases found. Check your Notion integration permissions.")
            return
        
        # Analyze each database
        successful_analyses = 0
        for database in databases:
            try:
                db_info = await self.analyze_database(database)
                if db_info:
                    self.mapping["databases"].append(db_info)
                    successful_analyses += 1
                await asyncio.sleep(0.2)  # Be respectful to API rate limits
            except Exception as e:
                print(f"Error analyzing database: {e}")
                continue
        
        # Update totals
        self.mapping["total_databases"] = len(self.mapping["databases"])
# DEMO CODE REMOVED: self.mapping["total_pages"] = sum(db["sample_page_count"] for db in self.mapping["databases"])
        
        # Generate recommendations
        self.generate_automation_recommendations()
        
        print(f"✅ Mapping complete: {successful_analyses}/{len(databases)} databases analyzed")
        print(f"📊 Found {len(self.mapping['checkbox_automation_candidates'])} checkbox automation candidates")
        print(f"🔗 Found {len(self.mapping['database_relationships'])} databases with relationships")
    
    def save_mapping(self, filename: str = "workspace_mapping.json"):
        """Save mapping to file."""
        print(f"💾 Saving mapping to {filename}...")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.mapping, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Mapping saved to {filename}")
    
    def print_summary(self):
        """Print summary of discovered workspace."""
        print("\n" + "="*100)
        print("📊 NOTION WORKSPACE COMPREHENSIVE MAPPING SUMMARY")
        print("="*100)
        print(f"Discovery Date: {self.mapping['discovery_date']}")
        print(f"Total Databases: {self.mapping['total_databases']}")
# DEMO CODE REMOVED: print(f"Sample Pages Analyzed: {self.mapping['total_pages']}")
        print(f"Checkbox Automation Opportunities: {len(self.mapping['checkbox_automation_candidates'])}")
        print(f"Database Relationships: {len(self.mapping['database_relationships'])}")
        print()
        
        print("📋 DATABASE INVENTORY:")
        print("-" * 80)
        for i, db in enumerate(self.mapping["databases"], 1):
            print(f"{i:2}. {db['title']} ({db['property_count']} properties)")
            if db['checkbox_properties']:
                print(f"     ✅ Checkboxes: {', '.join(db['checkbox_properties'])}")
            if db['relation_properties']:
                print(f"     🔗 Relations: {', '.join(db['relation_properties'])}")
            if db['formula_properties']:
                print(f"     🧮 Formulas: {', '.join(db['formula_properties'])}")
        print()
        
        print("🔲 CHECKBOX AUTOMATION OPPORTUNITIES (HIGH PRIORITY):")
        print("-" * 80)
        for i, candidate in enumerate(self.mapping["checkbox_automation_candidates"], 1):
            print(f"{i:2}. {candidate['database_title']} → {candidate['property_name']}")
        print()
        
        print("📊 PROPERTY TYPE DISTRIBUTION:")
        print("-" * 80)
        total_props = sum(self.mapping["property_type_summary"].values())
        for prop_type, count in sorted(self.mapping["property_type_summary"].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_props * 100) if total_props > 0 else 0
            print(f"• {prop_type:<20} {count:>3} ({percentage:>5.1f}%)")
        print()
        
        print("🤖 AUTOMATION RECOMMENDATIONS BY PRIORITY:")
        print("-" * 80)
        
        # Group by priority
        high_priority = [r for r in self.mapping["automation_recommendations"] if r["priority"] == "high"]
        medium_priority = [r for r in self.mapping["automation_recommendations"] if r["priority"] == "medium"]
        low_priority = [r for r in self.mapping["automation_recommendations"] if r["priority"] == "low"]
        
        if high_priority:
            print("🔴 HIGH PRIORITY:")
            for rec in high_priority[:5]:
                print(f"   • {rec['description']}")
            if len(high_priority) > 5:
                print(f"   ... and {len(high_priority) - 5} more high priority items")
        
        if medium_priority:
            print("🟡 MEDIUM PRIORITY:")
            for rec in medium_priority[:3]:
                print(f"   • {rec['description']}")
            if len(medium_priority) > 3:
                print(f"   ... and {len(medium_priority) - 3} more medium priority items")
        
        if low_priority:
            print("🟢 LOW PRIORITY:")
            for rec in low_priority[:2]:
                print(f"   • {rec['description']}")
            if len(low_priority) > 2:
                print(f"   ... and {len(low_priority) - 2} more low priority items")
        
        print(f"\nTotal Recommendations: {len(self.mapping['automation_recommendations'])}")
        print("\n" + "="*100)


def load_env_file():
    """Load environment variables from .env file."""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    except FileNotFoundError:
        pass
    return env_vars


async def main():
    """Main function."""
    print("🚀 Starting Direct Notion Workspace Mapping...")
    
    # Load from .env file
    env_vars = load_env_file()
    
        print("Please ensure your Notion API token is set in the .env file")
        return
    
    try:
        await mapper.run_comprehensive_mapping()
        mapper.save_mapping()
        mapper.print_summary()
        
        print("\n✅ Comprehensive workspace mapping completed successfully!")
        print("📄 Detailed mapping saved to: workspace_mapping.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())