#!/usr/bin/env python3
"""
Extract and analyze all checkbox fields from the LifeOS workspace databases.
This script provides deep contextual analysis for automation implementation.
"""

import json
import sys
from pathlib import Path

def extract_checkbox_fields(databases_file):
    """Extract all checkbox fields from databases with their context."""
    
    with open(databases_file, 'r') as f:
        databases = json.load(f)
    
    checkbox_analysis = {
        "total_databases": len(databases),
        "databases_with_checkboxes": [],
        "checkbox_fields": [],
        "summary_stats": {
            "total_checkboxes": 0,
            "databases_with_checkboxes": 0
        }
    }
    
    for db in databases:
        db_checkboxes = []
        
        for prop_name, prop_data in db.get("properties", {}).items():
            if prop_data.get("type") == "checkbox":
                checkbox_info = {
                    "database_id": db["id"],
                    "database_title": db["title"],
                    "field_name": prop_name,
                    "field_id": prop_data["id"],
                    "database_url": db["url"],
                    "database_created": db["created_time"],
                    "database_updated": db["last_edited_time"]
                }
                
                db_checkboxes.append(checkbox_info)
                checkbox_analysis["checkbox_fields"].append(checkbox_info)
        
        if db_checkboxes:
            checkbox_analysis["databases_with_checkboxes"].append({
                "id": db["id"],
                "title": db["title"],
                "url": db["url"],
                "checkbox_count": len(db_checkboxes),
                "checkboxes": db_checkboxes
            })
    
    checkbox_analysis["summary_stats"]["total_checkboxes"] = len(checkbox_analysis["checkbox_fields"])
    checkbox_analysis["summary_stats"]["databases_with_checkboxes"] = len(checkbox_analysis["databases_with_checkboxes"])
    
    return checkbox_analysis

def analyze_database_properties(databases_file):
    """Analyze all database properties for automation opportunities."""
    
    with open(databases_file, 'r') as f:
        databases = json.load(f)
    
    property_analysis = {
        "property_types": {},
        "automation_opportunities": [],
        "database_analysis": []
    }
    
    for db in databases:
        db_analysis = {
            "id": db["id"],
            "title": db["title"],
            "url": db["url"],
            "property_count": len(db.get("properties", {})),
            "property_types": {},
            "automation_potential": []
        }
        
        for prop_name, prop_data in db.get("properties", {}).items():
            prop_type = prop_data.get("type", "unknown")
            
            # Track property types globally
            if prop_type not in property_analysis["property_types"]:
                property_analysis["property_types"][prop_type] = 0
            property_analysis["property_types"][prop_type] += 1
            
            # Track property types per database
            if prop_type not in db_analysis["property_types"]:
                db_analysis["property_types"][prop_type] = 0
            db_analysis["property_types"][prop_type] += 1
            
            # Identify automation opportunities
            if prop_type == "checkbox":
                db_analysis["automation_potential"].append({
                    "type": "checkbox_automation",
                    "field": prop_name,
                    "opportunity": f"Automate actions when '{prop_name}' checkbox is toggled"
                })
            
            elif prop_type == "select" and "status" in prop_name.lower():
                db_analysis["automation_potential"].append({
                    "type": "status_workflow",
                    "field": prop_name,
                    "opportunity": f"Automate workflow transitions based on '{prop_name}' changes"
                })
            
            elif prop_type == "date" and any(keyword in prop_name.lower() for keyword in ["due", "deadline", "schedule"]):
                db_analysis["automation_potential"].append({
                    "type": "date_automation",
                    "field": prop_name,
                    "opportunity": f"Set reminders and notifications for '{prop_name}'"
                })
        
        property_analysis["database_analysis"].append(db_analysis)
        
        if db_analysis["automation_potential"]:
            property_analysis["automation_opportunities"].extend([
                {**opp, "database_id": db["id"], "database_title": db["title"]}
                for opp in db_analysis["automation_potential"]
            ])
    
    return property_analysis

def main():
    databases_file = "/home/ikino/dev/autonomous-multi-llm-agent/lifeos_discovery_results/discovered_databases.json"
    
    print("🔍 Extracting checkbox fields...")
    checkbox_analysis = extract_checkbox_fields(databases_file)
    
    print("📊 Analyzing database properties...")
    property_analysis = analyze_database_properties(databases_file)
    
    # Save checkbox analysis
    checkbox_output = "/home/ikino/dev/autonomous-multi-llm-agent/lifeos_checkbox_analysis.json"
    with open(checkbox_output, 'w') as f:
        json.dump(checkbox_analysis, f, indent=2)
    
    # Save property analysis
    property_output = "/home/ikino/dev/autonomous-multi-llm-agent/lifeos_property_analysis.json"
    with open(property_output, 'w') as f:
        json.dump(property_analysis, f, indent=2)
    
    print(f"\n✅ Analysis Results:")
    print(f"   📁 Total databases: {checkbox_analysis['total_databases']}")
    print(f"   ☑️  Databases with checkboxes: {checkbox_analysis['summary_stats']['databases_with_checkboxes']}")
    print(f"   🔲 Total checkbox fields: {checkbox_analysis['summary_stats']['total_checkboxes']}")
    print(f"   🤖 Automation opportunities: {len(property_analysis['automation_opportunities'])}")
    
    print(f"\n📄 Files created:")
    print(f"   {checkbox_output}")
    print(f"   {property_output}")
    
    # Display top checkbox fields
    print(f"\n🔍 Top Checkbox Fields Found:")
    for i, cb in enumerate(checkbox_analysis["checkbox_fields"][:10]):
        print(f"   {i+1}. '{cb['field_name']}' in '{cb['database_title']}'")
    
    if len(checkbox_analysis["checkbox_fields"]) > 10:
        print(f"   ... and {len(checkbox_analysis['checkbox_fields']) - 10} more")

if __name__ == "__main__":
    main()