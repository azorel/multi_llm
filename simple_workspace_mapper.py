#!/usr/bin/env python3
"""
Simple Notion Workspace Mapper
===============================

Simplified version that directly uses the Notion MCP client without complex imports.
Maps workspace structure and generates comprehensive JSON mapping.
"""

import os
import json
import asyncio
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime


class SimpleNotionMCPClient:
    """Simplified Notion MCP client for workspace discovery."""
    
    def __init__(self, token: str):
        """Initialize the client."""
        self.token = token
# NOTION_REMOVED:         self.mcp_command = ["npx", "-y", "@notionhq/notion-mcp-server"]
        self.mcp_env = {
            "OPENAPI_MCP_HEADERS": json.dumps({
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28"
            })
        }
    
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool and return the result."""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            process = await asyncio.create_subprocess_exec(
                *self.mcp_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, **self.mcp_env}
            )
            
            stdout, stderr = await process.communicate(
                input=json.dumps(request).encode()
            )
            
            if process.returncode != 0:
                print(f"MCP tool call failed: {stderr.decode()}")
                return {"error": f"MCP process failed: {stderr.decode()}"}
            
            response = json.loads(stdout.decode())
            
            if "error" in response:
                print(f"MCP tool error: {response['error']}")
                return {"error": response["error"]}
            
            return response.get("result", {})
            
        except Exception as e:
            print(f"Error calling MCP tool {tool_name}: {e}")
            return {"error": str(e)}


class SimpleWorkspaceMapper:
    """Simple workspace mapper."""
    
        """Initialize mapper."""
        self.mapping = {
            "workspace_name": "LifeOS Comprehensive Workspace",
            "discovery_date": datetime.now().isoformat(),
            "databases": [],
            "checkbox_automation_candidates": [],
            "property_type_summary": {},
            "automation_recommendations": [],
            "total_databases": 0,
            "total_pages": 0
        }
    
    async def discover_databases(self) -> List[Dict[str, Any]]:
        """Discover all databases."""
        print("🔍 Discovering databases...")
        
        try:
            search_params = {
                "filter": {
                    "value": "database",
                    "property": "object"
                },
                "page_size": 100
            }
            
# NOTION_REMOVED:             result = await self.notion._call_mcp_tool("API-post-search", search_params)
            
            if "error" in result:
                print(f"Error searching databases: {result['error']}")
                return []
            
            content = result.get("content", [])
            if content and isinstance(content[0], dict) and "text" in content[0]:
                search_data = json.loads(content[0]["text"])
                databases = search_data.get("results", [])
                print(f"📊 Found {len(databases)} databases")
                return databases
            
            return []
            
        except Exception as e:
            print(f"Error discovering databases: {e}")
            return []
    
    async def analyze_database(self, database: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single database."""
        db_id = database.get("id", "")
        title = ""
        
        # Extract title
        title_obj = database.get("title", [])
        if title_obj and len(title_obj) > 0:
            title = title_obj[0].get("plain_text", "Unknown")
        
        print(f"🔬 Analyzing: {title}")
        
        properties = database.get("properties", {})
        
        # Analyze properties
        property_analysis = []
        checkbox_properties = []
        relation_properties = []
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
            elif prop_type == "multi_select":
                options = [opt.get("name", "") for opt in prop_data.get("multi_select", {}).get("options", [])]
                prop_info["options"] = options
            elif prop_type == "formula":
                formula = prop_data.get("formula", {}).get("expression", "")
                prop_info["formula"] = formula
            elif prop_type == "relation":
                relation_db = prop_data.get("relation", {}).get("database_id", "")
                prop_info["relation_database"] = relation_db
                relation_properties.append(prop_name)
            elif prop_type == "checkbox":
                checkbox_properties.append(prop_name)
            
            property_analysis.append(prop_info)
        
# DEMO CODE REMOVED: # Get sample pages
# DEMO CODE REMOVED: sample_pages = await self.get_sample_pages(db_id, 3)
        
        # Update global property type summary
        for prop_type, count in property_types.items():
            self.mapping["property_type_summary"][prop_type] = (
                self.mapping["property_type_summary"].get(prop_type, 0) + count
            )
        
        # Track checkbox automation candidates
        for checkbox_prop in checkbox_properties:
            self.mapping["checkbox_automation_candidates"].append({
                "database_id": db_id,
                "database_title": title,
                "property_name": checkbox_prop,
                "automation_potential": "high"
            })
        
        database_info = {
            "id": db_id,
            "title": title,
            "url": database.get("url", ""),
            "properties": property_analysis,
            "property_count": len(properties),
            "checkbox_properties": checkbox_properties,
            "relation_properties": relation_properties,
# DEMO CODE REMOVED: "sample_pages": sample_pages,
# DEMO CODE REMOVED: "total_pages": len(sample_pages),  # Simplified count
            "created_time": database.get("created_time", ""),
            "last_edited_time": database.get("last_edited_time", "")
        }
        
        return database_info
    
# DEMO CODE REMOVED: async def get_sample_pages(self, database_id: str, limit: int = 3) -> List[Dict[str, Any]]:
# DEMO CODE REMOVED: """Get sample pages from database."""
        try:
            params = {
                "database_id": database_id,
                "page_size": limit
            }
            
# NOTION_REMOVED:             result = await self.notion._call_mcp_tool("API-post-database-query", params)
            
            if "error" in result:
                return []
            
            content = result.get("content", [])
            if content and isinstance(content[0], dict) and "text" in content[0]:
                query_data = json.loads(content[0]["text"])
                return query_data.get("results", [])
            
            return []
            
        except Exception as e:
# DEMO CODE REMOVED: print(f"Error getting sample pages: {e}")
            return []
    
    def generate_automation_recommendations(self):
        """Generate automation recommendations."""
        recommendations = []
        
        # Checkbox automation
        for candidate in self.mapping["checkbox_automation_candidates"]:
            recommendations.append({
                "type": "checkbox_automation",
                "priority": "high",
                "database_id": candidate["database_id"],
                "database_title": candidate["database_title"],
                "property_name": candidate["property_name"],
                "description": f"Automate {candidate['property_name']} checkbox in {candidate['database_title']}",
                "implementation": "Create backend trigger when checkbox is checked/unchecked"
            })
        
        # Database with many properties - potential for automation
        for db in self.mapping["databases"]:
            if db["property_count"] > 10:
                recommendations.append({
                    "type": "complex_database_automation",
                    "priority": "medium",
                    "database_id": db["id"],
                    "database_title": db["title"],
                    "description": f"Complex database with {db['property_count']} properties - good automation candidate",
                    "implementation": "Consider automated workflows for data entry and validation"
                })
        
        self.mapping["automation_recommendations"] = recommendations
    
    async def run_comprehensive_mapping(self):
        """Run the complete mapping process."""
        print("🗺️ Starting comprehensive workspace mapping...")
        
        # Discover all databases
        databases = await self.discover_databases()
        
        # Analyze each database
        for database in databases:
            try:
                db_info = await self.analyze_database(database)
                self.mapping["databases"].append(db_info)
                await asyncio.sleep(0.1)  # Be respectful to API
            except Exception as e:
                print(f"Error analyzing database: {e}")
                continue
        
        # Update totals
        self.mapping["total_databases"] = len(self.mapping["databases"])
        self.mapping["total_pages"] = sum(db["total_pages"] for db in self.mapping["databases"])
        
        # Generate recommendations
        self.generate_automation_recommendations()
        
        print(f"✅ Mapping complete: {self.mapping['total_databases']} databases")
        print(f"📊 Found {len(self.mapping['checkbox_automation_candidates'])} checkbox automation candidates")
    
    def save_mapping(self, filename: str = "workspace_mapping.json"):
        """Save mapping to file."""
        print(f"💾 Saving mapping to {filename}...")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.mapping, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Mapping saved to {filename}")
    
    def print_summary(self):
        """Print summary of discovered workspace."""
        print("\n" + "="*80)
        print("📊 NOTION WORKSPACE MAPPING SUMMARY")
        print("="*80)
        print(f"Total Databases: {self.mapping['total_databases']}")
# DEMO CODE REMOVED: print(f"Total Pages Sampled: {self.mapping['total_pages']}")
        print()
        
        print("📋 DATABASES:")
        print("-" * 40)
        for db in self.mapping["databases"]:
            print(f"• {db['title']} ({db['property_count']} properties)")
            if db['checkbox_properties']:
                print(f"  Checkboxes: {', '.join(db['checkbox_properties'])}")
            if db['relation_properties']:
                print(f"  Relations: {', '.join(db['relation_properties'])}")
        print()
        
        print("🔲 CHECKBOX AUTOMATION CANDIDATES:")
        print("-" * 40)
        for candidate in self.mapping["checkbox_automation_candidates"]:
            print(f"• {candidate['database_title']} → {candidate['property_name']}")
        print()
        
        print("📊 PROPERTY TYPES:")
        print("-" * 40)
        for prop_type, count in sorted(self.mapping["property_type_summary"].items()):
            print(f"• {prop_type}: {count}")
        print()
        
        print("🤖 AUTOMATION RECOMMENDATIONS:")
        print("-" * 40)
        for rec in self.mapping["automation_recommendations"][:5]:
            print(f"• [{rec['priority'].upper()}] {rec['description']}")
        if len(self.mapping["automation_recommendations"]) > 5:
            print(f"... and {len(self.mapping['automation_recommendations']) - 5} more")
        
        print("\n" + "="*80)


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
    print("🚀 Starting Simple Notion Workspace Mapping...")
    
    # Load from .env file
    env_vars = load_env_file()
    
        return
    
    try:
        await mapper.run_comprehensive_mapping()
        mapper.save_mapping()
        mapper.print_summary()
        
        print("\n✅ Workspace mapping completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())