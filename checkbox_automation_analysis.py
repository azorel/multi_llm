#!/usr/bin/env python3
"""
Comprehensive Checkbox Automation Analysis and Testing
=====================================================

This script discovers all checkbox fields across the LifeOS workspace and tests
which ones have working automation backends vs which need to be built.
"""

import asyncio
import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

# Database mappings from our discovery
DATABASE_MAPPINGS = {
    # Knowledge Management
    "knowledge_hub": "20bec31c-9de2-814e-80db-d13d0c27d869",
    "notes": "1fdec31c-9de2-814b-8231-e715f51bb81d",
    "books": "1fdec31c-9de2-81a4-9413-c6ae516847c3",
    "journals": "1fdec31c-9de2-8191-a702-fbd24c8bc8f3",
    
    # Content Management
    "youtube_channels": "203ec31c-9de2-8079-ae4e-ed754d474888",
    
    # RC/Hobby Management
    "home_garage": "1feec31c-9de2-8156-82ed-d5a045492ac9",
    "maintenance_schedule": "203ec31c-9de2-8176-a4b2-f02415f950da",
    "maintenance_records": "1feec31c-9de2-81cb-9b31-e32055d36f69",
    "event_records": "1feec31c-9de2-81aa-ae5f-c6a03e8fdf27",
    
    # Vehicle Management
    "fuel_log": "203ec31c-9de2-8117-a2d0-fe342ad051ff",
    "vehicle_todos": "1feec31c-9de2-81bf-b92d-d18d2f5c3e8e",
    
    # Financial Management
    "spending_log": "203ec31c-9de2-81d4-90c6-ca4eea0106fc",
    "recurring": "1fdec31c-9de2-815b-ab44-f416ead6bd65",
    "accounts": "1fdec31c-9de2-8184-a168-fa38482ce0fd",
    
    # Household Management
    "things_bought": "205ec31c-9de2-809b-8676-e5686fc02c52",
    "food_onhand": "200ec31c-9de2-80e2-817f-dfbc151b7946",
    "chores": "1fdec31c-9de2-81dd-80d4-d07072888283",
    "meals": "1fdec31c-9de2-810a-8195-dce2c5bb51b5",
    
    # Habits & Goals
    "habits": "1fdec31c-9de2-8161-96e4-cbf394be6204",
    "weekly": "1fdec31c-9de2-8126-bc1c-f8233192d910",
    "goal_records": "1fdec31c-9de2-8102-9edf-f24c409b8059",
    
    # Events
    "events": "1fdec31c-9de2-81dd-813b-fdaaf622277d"
}


class CheckboxAutomationAnalyzer:
    """Analyzes checkbox fields and their automation status across LifeOS workspace."""
    
        self.headers = {
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        # Track discovered checkbox fields
        self.checkbox_fields = {}
        
        # Track automation status
        self.automation_status = {}
        
        # Known working automations from code analysis
        self.known_automations = {
            "youtube_channels": {
                "Process Channel": {
                    "status": "WORKING",
                    "backend": "YouTubeChannelProcessor",
                    "function": "get_channels_to_process()",
                    "description": "Processes all videos from marked channels"
                }
            },
            "knowledge_hub": {
                "🚀 Yes": {
                    "status": "WORKING", 
                    "backend": "ContentProcessingEngine",
                    "function": "_get_pending_content_items()",
                    "description": "Triggers AI processing of content items"
                },
                "Decision Made": {
                    "status": "PASSIVE",
                    "backend": "YouTubeChannelProcessor",
                    "function": "_has_user_checkbox_choices()",
                    "description": "Tracks user decisions but no automation"
                },
                "📁 Pass": {
                    "status": "PASSIVE",
                    "backend": "YouTubeChannelProcessor", 
                    "function": "_has_user_checkbox_choices()",
                    "description": "Tracks user pass decisions but no automation"
                }
            }
        }
    
    async def discover_all_checkbox_fields(self) -> Dict[str, List[str]]:
        """Discover all checkbox fields across all databases."""
        logger.info("🔍 Starting comprehensive checkbox field discovery...")
        
        for db_name, db_id in DATABASE_MAPPINGS.items():
            try:
                logger.info(f"   📊 Analyzing database: {db_name}")
                checkboxes = await self._get_database_checkbox_fields(db_id, db_name)
                if checkboxes:
                    self.checkbox_fields[db_name] = checkboxes
                    logger.info(f"      ✅ Found {len(checkboxes)} checkbox fields")
                else:
                    logger.info(f"      ℹ️ No checkbox fields found")
                    
                # Small delay to avoid rate limits
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"   ❌ Error analyzing {db_name}: {e}")
                continue
        
        logger.info(f"🎯 Discovery complete! Found checkboxes in {len(self.checkbox_fields)} databases")
        return self.checkbox_fields
    
    async def _get_database_checkbox_fields(self, db_id: str, db_name: str) -> List[str]:
        """Get all checkbox fields from a specific database."""
        try:
            response = requests.get(
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to access {db_name}: {response.status_code}")
                return []
            
            database_info = response.json()
            properties = database_info.get('properties', {})
            
            checkbox_fields = []
            for prop_name, prop_info in properties.items():
                if prop_info.get('type') == 'checkbox':
                    checkbox_fields.append(prop_name)
            
            return checkbox_fields
            
        except Exception as e:
            logger.error(f"Error getting checkbox fields for {db_name}: {e}")
            return []
    
    async def test_existing_automations(self) -> Dict[str, Dict]:
        """Test all known automations to verify they're working."""
        logger.info("🧪 Testing existing checkbox automations...")
        
        test_results = {}
        
        # Test YouTube Channel Processing
        logger.info("   📺 Testing YouTube Channel Processing...")
        youtube_test = await self._test_youtube_channel_automation()
        test_results["youtube_channels"] = youtube_test
        
        # Test Knowledge Hub Processing  
        logger.info("   🧠 Testing Knowledge Hub Processing...")
        knowledge_test = await self._test_knowledge_hub_automation()
        test_results["knowledge_hub"] = knowledge_test
        
        # Test LifeOS Automation Engine
        logger.info("   🤖 Testing LifeOS Automation Engine...")
        lifeos_test = await self._test_lifeos_automation_engine()
        test_results["lifeos_engine"] = lifeos_test
        
        return test_results
    
    async def _test_youtube_channel_automation(self) -> Dict:
        """Test YouTube channel processing automation."""
        try:
            # Check if we have channels database access
            channels_db_id = DATABASE_MAPPINGS.get("youtube_channels")
            if not channels_db_id:
                return {"status": "ERROR", "error": "No YouTube channels database ID"}
            
            # Query for channels with "Process Channel" checkbox set
            query_data = {
                "filter": {
                    "property": "Process Channel",
                    "checkbox": {"equals": True}
                }
            }
            
            response = requests.post(
                headers=self.headers,
                json=query_data,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                return {
                    "status": "WORKING",
                    "channels_marked": len(results),
                    "description": "Can query channels marked for processing",
                    "automation_active": len(results) > 0
                }
            else:
                return {
                    "status": "ERROR", 
                    "error": f"Query failed: {response.status_code}",
                    "description": "Cannot query YouTube channels database"
                }
                
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    async def _test_knowledge_hub_automation(self) -> Dict:
        """Test Knowledge Hub content processing automation."""
        try:
            # Check if we have knowledge hub database access
            knowledge_db_id = DATABASE_MAPPINGS.get("knowledge_hub")
            if not knowledge_db_id:
                return {"status": "ERROR", "error": "No Knowledge Hub database ID"}
            
            # Query for items with "🚀 Yes" checkbox set
            query_data = {
                "filter": {
                    "property": "🚀 Yes",
                    "checkbox": {"equals": True}
                }
            }
            
            response = requests.post(
                headers=self.headers,
                json=query_data,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                return {
                    "status": "WORKING",
                    "items_marked": len(results),
                    "description": "Can query items marked for processing",
                    "automation_active": len(results) > 0
                }
            else:
                return {
                    "status": "ERROR",
                    "error": f"Query failed: {response.status_code}",
                    "description": "Cannot query Knowledge Hub database"
                }
                
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    async def _test_lifeos_automation_engine(self) -> Dict:
        """Test LifeOS automation engine functionality."""
        try:
            # Check if automation engine is configured and can be imported
            try:
                sys.path.insert(0, str(Path(__file__).parent / "src" / "automation"))
                from lifeos_automation_engine import create_lifeos_automation_engine
                
                # Try to create engine instance
                
                return {
                    "status": "WORKING",
                    "description": "LifeOS automation engine can be instantiated",
                    "engines_available": list(engine.engines.keys()) if hasattr(engine, 'engines') else []
                }
                
            except ImportError as e:
                return {
                    "status": "PARTIAL",
                    "error": f"Import error: {e}",
                    "description": "LifeOS automation engine not properly configured"
                }
                
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    async def analyze_automation_gaps(self) -> Dict[str, Any]:
        """Analyze gaps between discovered checkboxes and implemented automations."""
        logger.info("📊 Analyzing automation gaps...")
        
        gaps = {
            "implemented": {},
            "missing": {},
            "partial": {},
            "unknown": {}
        }
        
        total_checkboxes = 0
        implemented_count = 0
        
        for db_name, checkboxes in self.checkbox_fields.items():
            total_checkboxes += len(checkboxes)
            
            db_gaps = {
                "implemented": [],
                "missing": [],
                "partial": [],
                "unknown": []
            }
            
            for checkbox in checkboxes:
                # Check if we have known automation for this checkbox
                known_automation = self.known_automations.get(db_name, {}).get(checkbox)
                
                if known_automation:
                    status = known_automation.get("status", "UNKNOWN")
                    if status == "WORKING":
                        db_gaps["implemented"].append({
                            "field": checkbox,
                            "backend": known_automation.get("backend"),
                            "function": known_automation.get("function"),
                            "description": known_automation.get("description")
                        })
                        implemented_count += 1
                    elif status == "PASSIVE":
                        db_gaps["partial"].append({
                            "field": checkbox,
                            "backend": known_automation.get("backend"),
                            "description": known_automation.get("description"),
                            "needs": "Active automation"
                        })
                    else:
                        db_gaps["unknown"].append({
                            "field": checkbox,
                            "status": status
                        })
                else:
                    db_gaps["missing"].append({
                        "field": checkbox,
                        "needs": "Complete automation implementation"
                    })
            
            if any(db_gaps.values()):  # Only add if there are gaps to report
                gaps[db_name] = db_gaps
        
        # Add summary statistics
        gaps["summary"] = {
            "total_checkboxes": total_checkboxes,
            "implemented_automations": implemented_count,
            "missing_automations": total_checkboxes - implemented_count,
            "automation_coverage": f"{(implemented_count/total_checkboxes*100):.1f}%" if total_checkboxes > 0 else "0%"
        }
        
        return gaps
    
    async def create_test_scenarios(self) -> Dict[str, List[Dict]]:
        """Create comprehensive test scenarios for each checkbox automation."""
        logger.info("🎯 Creating test scenarios for checkbox automations...")
        
        scenarios = {}
        
        for db_name, checkboxes in self.checkbox_fields.items():
            db_scenarios = []
            
            for checkbox in checkboxes:
                # Create test scenario based on database type and checkbox name
                scenario = self._generate_test_scenario(db_name, checkbox)
                if scenario:
                    db_scenarios.append(scenario)
            
            if db_scenarios:
                scenarios[db_name] = db_scenarios
        
        return scenarios
    
    def _generate_test_scenario(self, db_name: str, checkbox_name: str) -> Optional[Dict]:
        """Generate a test scenario for a specific checkbox."""
        # Define test scenarios based on database type and checkbox patterns
        scenario_templates = {
            "process": {
                "action": "Mark checkbox as true",
                "expected": "System should detect and process the marked item",
                "verification": "Check logs for processing activity",
                "cleanup": "Unmark checkbox after test"
            },
            "status": {
                "action": "Mark checkbox to indicate status change", 
                "expected": "System should update related fields or trigger workflows",
                "verification": "Check for status updates in related databases",
                "cleanup": "Reset status if needed"
            },
            "decision": {
                "action": "Mark checkbox to indicate decision made",
                "expected": "System should record decision and potentially trigger actions",
                "verification": "Check decision is recorded and any followup actions occur",
                "cleanup": "Reset decision if test item"
            },
            "trigger": {
                "action": "Mark checkbox to trigger automation",
                "expected": "System should execute automation workflow",
                "verification": "Check automation results and completion status",
                "cleanup": "Unmark trigger checkbox"
            }
        }
        
        # Determine scenario type based on checkbox name patterns
        checkbox_lower = checkbox_name.lower()
        
        if any(word in checkbox_lower for word in ["process", "🚀", "yes"]):
            template = scenario_templates["process"]
        elif any(word in checkbox_lower for word in ["done", "complete", "finished"]):
            template = scenario_templates["status"]
        elif any(word in checkbox_lower for word in ["decision", "decide", "pass"]):
            template = scenario_templates["decision"] 
        else:
            template = scenario_templates["trigger"]
        
        return {
            "checkbox": checkbox_name,
            "database": db_name,
            "scenario_type": template,
            "test_steps": [
                f"1. {template['action']} for '{checkbox_name}' in {db_name}",
                f"2. {template['expected']}",
                f"3. {template['verification']}",
                f"4. {template['cleanup']}"
            ]
        }
    
    async def create_implementation_roadmap(self) -> Dict[str, Any]:
        """Create priority matrix and implementation roadmap for missing automations."""
        logger.info("🗺️ Creating implementation roadmap...")
        
        gaps = await self.analyze_automation_gaps()
        
        # Define priority scoring
        priority_matrix = {
            "youtube_channels": {"score": 10, "reason": "Content processing - high value, daily use"},
            "knowledge_hub": {"score": 10, "reason": "AI processing - core functionality"},
            "maintenance_schedule": {"score": 9, "reason": "RC maintenance - critical for hobby"},
            "home_garage": {"score": 8, "reason": "Inventory management - prevents issues"},
            "chores": {"score": 7, "reason": "Household automation - quality of life"},
            "habits": {"score": 7, "reason": "Personal development - long-term value"},
            "fuel_log": {"score": 6, "reason": "Vehicle tracking - useful but not critical"},
            "spending_log": {"score": 6, "reason": "Financial tracking - good visibility"},
            "events": {"score": 5, "reason": "Event management - periodic value"},
            "things_bought": {"score": 4, "reason": "Purchase tracking - nice to have"},
            "food_onhand": {"score": 4, "reason": "Kitchen management - convenience"},
            "meals": {"score": 3, "reason": "Meal planning - optional"},
            "books": {"score": 3, "reason": "Reading tracking - low automation value"},
            "notes": {"score": 2, "reason": "Note management - minimal automation needs"}
        }
        
        # Create implementation phases
        roadmap = {
            "phase_1_immediate": {"databases": [], "effort": "Low", "timeline": "This week"},
            "phase_2_high_value": {"databases": [], "effort": "Medium", "timeline": "Next 2 weeks"},
            "phase_3_enhancement": {"databases": [], "effort": "High", "timeline": "Next month"},
            "phase_4_nice_to_have": {"databases": [], "effort": "Variable", "timeline": "Future"}
        }
        
        # Categorize databases by priority and missing automations
        for db_name in gaps.keys():
            if db_name == "summary":
                continue
                
            priority = priority_matrix.get(db_name, {"score": 1, "reason": "Unknown value"})
            missing_count = len(gaps.get(db_name, {}).get("missing", []))
            
            if missing_count == 0:
                continue  # Skip databases with no missing automations
            
            db_info = {
                "database": db_name,
                "priority_score": priority["score"],
                "priority_reason": priority["reason"],
                "missing_automations": missing_count,
                "missing_fields": [item["field"] for item in gaps.get(db_name, {}).get("missing", [])]
            }
            
            # Assign to phase based on priority score
            if priority["score"] >= 9:
                roadmap["phase_1_immediate"]["databases"].append(db_info)
            elif priority["score"] >= 7:
                roadmap["phase_2_high_value"]["databases"].append(db_info)
            elif priority["score"] >= 5:
                roadmap["phase_3_enhancement"]["databases"].append(db_info)
            else:
                roadmap["phase_4_nice_to_have"]["databases"].append(db_info)
        
        # Add implementation estimates
        roadmap["implementation_estimates"] = {
            "phase_1_immediate": "2-4 hours per database",
            "phase_2_high_value": "4-8 hours per database", 
            "phase_3_enhancement": "8-16 hours per database",
            "phase_4_nice_to_have": "Variable based on complexity"
        }
        
        return roadmap
    
    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        logger.info("📋 Generating comprehensive checkbox automation report...")
        
        # Gather all analysis data
        checkbox_fields = await self.discover_all_checkbox_fields()
        test_results = await self.test_existing_automations()
        gaps = await self.analyze_automation_gaps()
        scenarios = await self.create_test_scenarios()
        roadmap = await self.create_implementation_roadmap()
        
        report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "checkbox_discovery": {
                "total_databases_analyzed": len(DATABASE_MAPPINGS),
                "databases_with_checkboxes": len(checkbox_fields),
                "checkbox_fields_by_database": checkbox_fields,
                "total_checkbox_fields": sum(len(fields) for fields in checkbox_fields.values())
            },
            "automation_testing": test_results,
            "gap_analysis": gaps,
            "test_scenarios": scenarios,
            "implementation_roadmap": roadmap,
            "recommendations": {
                "immediate_actions": [
                    "Complete testing of existing YouTube channel automation",
                    "Verify Knowledge Hub processing is working correctly",
                    "Implement missing automations for maintenance_schedule database",
                    "Set up monitoring for home_garage inventory levels"
                ],
                "next_steps": [
                    "Implement chores automation for household task management",
                    "Add habits tracking automation for personal development",
                    "Create fuel_log automation for vehicle efficiency monitoring",
                    "Set up spending_log automation for financial insights"
                ],
                "long_term_goals": [
                    "Achieve 90%+ automation coverage across all databases",
                    "Implement predictive intelligence for maintenance and inventory",
                    "Create cross-database workflows for event preparation",
                    "Build natural language interface for checkbox automation"
                ]
            }
        }
        
        return report
    
    async def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save comprehensive report to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"checkbox_automation_analysis_{timestamp}.json"
        
        filepath = Path(__file__).parent / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Comprehensive report saved to: {filepath}")
        return filepath


async def main():
    """Main function to run comprehensive checkbox automation analysis."""
    # Setup logging
    logger.info("🚀 Starting Comprehensive Checkbox Automation Analysis")
    logger.info("=" * 60)
    
    # Get Notion token
        return
    
    # Create analyzer
    
    try:
        # Run comprehensive analysis
        report = await analyzer.generate_comprehensive_report()
        
        # Save report
        report_file = await analyzer.save_report(report)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 ANALYSIS SUMMARY")
        logger.info("=" * 60)
        
        discovery = report["checkbox_discovery"]
        gaps = report["gap_analysis"]["summary"]
        
        logger.info(f"📋 Total databases analyzed: {discovery['total_databases_analyzed']}")
        logger.info(f"📋 Databases with checkboxes: {discovery['databases_with_checkboxes']}")
        logger.info(f"☑️ Total checkbox fields found: {discovery['total_checkbox_fields']}")
        logger.info(f"✅ Implemented automations: {gaps['implemented_automations']}")
        logger.info(f"❌ Missing automations: {gaps['missing_automations']}")
        logger.info(f"📈 Automation coverage: {gaps['automation_coverage']}")
        
        logger.info(f"\n📄 Full report saved to: {report_file}")
        logger.info("\n🎯 Next steps:")
        for action in report["recommendations"]["immediate_actions"]:
            logger.info(f"   • {action}")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())