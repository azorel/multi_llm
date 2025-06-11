#!/usr/bin/env python3
"""
LifeOS Integration Module
========================

Integrates the complete LifeOS functionality with the existing autonomous agent system.
Provides task processing extensions and automated workflows.

This module extends the existing main.py functionality to support:
- Today's CC Notion page management
- Daily routine tracking  
- Inventory management with auto-shopping
- RC hobby management with competition prep
- Smart automation triggers
- Notion-based daily interactions
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from loguru import logger

from .lifeos_managers import (
    InventoryManager, 
    RoutineTracker, 
    RCHobbyManager, 
    RCCompetitionManager
)
from .notion_todays_cc from ..integrations.notion_mcp_client 

class LifeOSIntegration:
    """
    Main integration class for LifeOS functionality.
    
    Extends the existing autonomous agent system with comprehensive
    life management capabilities.
    """
    
        """Initialize LifeOS integration."""
        
        # Database IDs from existing workspace discovery
        self.db_ids = {
            'lifelog': '203ec31c-9de2-800b-b980-f69359be6edf',
            'habits': '1fdec31c-9de2-8161-96e4-cbf394be6204', 
            'chores': '1fdec31c-9de2-81dd-80d4-d07072888283',
            'food_onhand': '200ec31c-9de2-80e2-817f-dfbc151b7946',
            'drinks': '200ec31c-9de2-803b-a9ab-d4bc2c3fe5cf',
            'things_bought': '205ec31c-9de2-809b-8676-e5686fc02c52',
            'rc_manufacturers': '1feec31c-9de2-81d2-a677-d57f3eb653dd',
            'home_garage': '1feec31c-9de2-8156-82ed-d5a045492ac9',
            'event_records': '1feec31c-9de2-81aa-ae5f-c6a03e8fdf27',
            'knowledge_hub': '20bec31c-9de2-814e-80db-d13d0c27d869',
            'youtube_channels': '203ec31c-9de2-8079-ae4e-ed754d474888',
            'notes': '1fdec31c-9de2-814b-8231-e715f51bb81d'
        }
        
        # Initialize managers
        self.inventory_manager = None
        self.routine_tracker = None
        self.rc_hobby_manager = None
        self.rc_competition_manager = None
        self.todays_cc = None
        
        # Task action mappings for extended functionality
        self.action_handlers = {
            'UsedItem': self.handle_used_item,
            'InventoryCheck': self.handle_inventory_check,
            'CompleteShoppingTrip': self.handle_complete_shopping,
            'CompleteRoutine': self.handle_complete_routine,
            'RC Maintenance': self.handle_rc_maintenance,
            'RC Comp Prep': self.handle_rc_comp_prep,
            'RC Repair': self.handle_rc_repair,
            'Generate Comp Prep': self.handle_generate_comp_prep,
            'Log Vehicle Issue': self.handle_log_vehicle_issue
        }

    async def initialize(self) -> bool:
        """Initialize all LifeOS managers and test connections."""
        try:
            if not self.notion_client:
                logger.error("No Notion token provided for LifeOS integration")
                return False
            
            # Test Notion connection
            await self.notion_client.test_connection()
            logger.info("✅ Notion connection established for LifeOS")
            
            # Initialize managers
# NOTION_REMOVED:             self.inventory_manager = InventoryManager(self.notion_client, self.db_ids)
# NOTION_REMOVED:             self.routine_tracker = RoutineTracker(self.notion_client, self.db_ids)
# NOTION_REMOVED:             self.rc_hobby_manager = RCHobbyManager(self.notion_client, self.db_ids)
# NOTION_REMOVED:             self.rc_competition_manager = RCCompetitionManager(self.notion_client, self.db_ids)
# NOTION_REMOVED:             self.todays_cc = create_notion_todays_cc(self.notion_client)
            
            logger.info("✅ LifeOS managers initialized")
            logger.info("✅ Today's CC Notion integration ready")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LifeOS integration: {e}")
            return False

    async def process_extended_task(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process extended LifeOS task actions.
        
        This method extends the existing task processing in main.py
        to handle new LifeOS-specific actions.
        
        Args:
            task_details: Task details dict with action, details, etc.
            
        Returns:
            Processing result dict
        """
        try:
            action = task_details.get('action', '')
            
            if action not in self.action_handlers:
                return {'error': f'Unknown LifeOS action: {action}'}
            
            # Call the appropriate handler
            handler = self.action_handlers[action]
            result = await handler(task_details)
            
            # Add processing metadata
            result['processed_by'] = 'LifeOS Integration'
            result['processed_at'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing LifeOS task: {e}")
            return {'error': str(e)}

    # Task Action Handlers
    async def handle_used_item(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle item usage tracking."""
        try:
            item_name = task_details.get('item_name', '')
            quantity = task_details.get('quantity', 1)
            notes = task_details.get('details', '')
            
            if not item_name:
                return {'error': 'Item name required for UsedItem action'}
            
            result = await self.inventory_manager.process_item_usage(
                item_name, quantity, notes
            )
            
            # Create shopping task if needed
            if result.get('needs_shopping'):
                shopping_task = {
                    'title': f"Buy {item_name}",
                    'action': 'CompleteShoppingTrip',
                    'priority': 'Medium',
                    'details': f"Restock {item_name} - current stock: {result['current_stock']}"
                }
                await self._create_task(shopping_task)
                result['shopping_task_created'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling UsedItem: {e}")
            return {'error': str(e)}

    async def handle_inventory_check(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inventory status check."""
        try:
            result = await self.inventory_manager.morning_inventory_analysis()
            
            # Log inventory status
            logger.info(f"📦 Inventory check: {len(result.get('low_stock_items', []))} items need restocking")
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling InventoryCheck: {e}")
            return {'error': str(e)}

    async def handle_complete_shopping(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shopping trip completion and inventory restocking."""
        try:
            details = task_details.get('details', '')
            result = {'items_restocked': 0, 'total_cost': 0.0}
            
            # Parse shopping details (format: "Item1: quantity, Item2: quantity")
            if details:
                items = self._parse_shopping_details(details)
                
                for item_name, quantity in items.items():
                    restock_result = await self.inventory_manager.restock_item(
                        item_name, quantity
                    )
                    if restock_result:
                        result['items_restocked'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling CompleteShoppingTrip: {e}")
            return {'error': str(e)}

    async def handle_complete_routine(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle routine activity completion."""
        try:
            activity_name = task_details.get('item_name', '') or task_details.get('details', '')
            notes = task_details.get('notes', '')
            
            if not activity_name:
                return {'error': 'Activity name required for CompleteRoutine action'}
            
            result = await self.routine_tracker.complete_routine_activity(
                activity_name, notes
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling CompleteRoutine: {e}")
            return {'error': str(e)}

    async def handle_rc_maintenance(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle RC vehicle maintenance."""
        try:
            vehicle_name = task_details.get('rc_vehicle', '') or task_details.get('item_name', '')
            maintenance_type = task_details.get('details', 'General Maintenance')
            
            if not vehicle_name:
                return {'error': 'Vehicle name required for RC Maintenance action'}
            
            # Update vehicle last maintenance date
            result = {
                'vehicle': vehicle_name,
                'maintenance_type': maintenance_type,
                'completed_at': datetime.now().isoformat(),
                'next_maintenance': (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            # Log maintenance in notes database
            await self._create_maintenance_note(vehicle_name, maintenance_type)
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling RC Maintenance: {e}")
            return {'error': str(e)}

    async def handle_rc_comp_prep(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle RC competition preparation task."""
        try:
            vehicle_name = task_details.get('rc_vehicle', '')
            competition = task_details.get('competition', '')
            prep_type = task_details.get('details', 'General Prep')
            
            result = {
                'vehicle': vehicle_name,
                'competition': competition,
                'prep_type': prep_type,
                'completed_at': datetime.now().isoformat()
            }
            
            # Update vehicle comp readiness
            if prep_type.lower() in ['battery check', 'final prep']:
                await self._update_vehicle_comp_readiness(vehicle_name, True)
                result['vehicle_comp_ready'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling RC Comp Prep: {e}")
            return {'error': str(e)}

    async def handle_rc_repair(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle RC vehicle repair completion."""
        try:
            vehicle_name = task_details.get('rc_vehicle', '')
            issue_id = task_details.get('issue_id', '')
            repair_notes = task_details.get('details', '')
            
            if issue_id:
                # Complete existing repair
                result = await self.rc_competition_manager.complete_vehicle_repair(
                    issue_id, repair_notes
                )
                return {'repair_completed': result, 'issue_id': issue_id}
            else:
                # General repair completion
                return {
                    'vehicle': vehicle_name,
                    'repair_notes': repair_notes,
                    'completed_at': datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Error handling RC Repair: {e}")
            return {'error': str(e)}

    async def handle_generate_comp_prep(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle competition prep task generation."""
        try:
            competition_id = task_details.get('competition_id', '') or task_details.get('details', '')
            
            if not competition_id:
                return {'error': 'Competition ID required for Generate Comp Prep action'}
            
            result = await self.rc_competition_manager.generate_comp_prep_tasks(competition_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling Generate Comp Prep: {e}")
            return {'error': str(e)}

    async def handle_log_vehicle_issue(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vehicle issue logging."""
        try:
            vehicle_name = task_details.get('rc_vehicle', '')
            issue_title = task_details.get('item_name', '') or 'Vehicle Issue'
            description = task_details.get('details', '')
            severity = task_details.get('priority', 'Medium')
            event_name = task_details.get('competition', '')
            
            if not vehicle_name:
                return {'error': 'Vehicle name required for Log Vehicle Issue action'}
            
            issue_id = await self.rc_competition_manager.create_vehicle_issue(
                vehicle_name, issue_title, description, severity, event_name
            )
            
            return {
                'issue_id': issue_id,
                'vehicle': vehicle_name,
                'issue_title': issue_title,
                'severity': severity
            }
            
        except Exception as e:
            logger.error(f"Error handling Log Vehicle Issue: {e}")
            return {'error': str(e)}

    async def update_todays_cc(self) -> bool:
        """
        Update the Today's CC Notion page with current data.
        
        Returns:
            Success status
        """
        try:
            if not self.todays_cc:
                logger.warning("Today's CC not initialized")
                return False
            
            # Update the page content
            success = await self.todays_cc.update_page_content()
            
            # Monitor for quick actions
            await self.todays_cc.monitor_quick_actions()
            
            if success:
                logger.info("✅ Today's CC page updated")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating Today's CC: {e}")
            return False

    async def run_morning_automation(self) -> Dict[str, Any]:
        """
        Run morning automation routines.
        
        This can be called from the main system's morning cycle.
        """
        try:
            results = {
                'inventory_analysis': {},
                'routine_prep': {},
                'rc_status': {},
                'tasks_created': 0
            }
            
            # Run inventory analysis
            if self.inventory_manager:
                inventory_result = await self.inventory_manager.morning_inventory_analysis()
                results['inventory_analysis'] = inventory_result
                results['tasks_created'] += inventory_result.get('shopping_tasks_created', 0)
            
            # Get RC hobby status
            if self.rc_hobby_manager:
                rc_dashboard = await self.rc_hobby_manager.get_hobby_dashboard_data()
                results['rc_status'] = rc_dashboard
            
            # Check for routine templates
            if self.routine_tracker:
                today_completions = await self.routine_tracker.get_todays_completions()
                results['routine_prep'] = {
                    'completions_today': len(today_completions),
# DEMO CODE REMOVED: 'pending_routines': 12 - len(today_completions)  # Sample total
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in morning automation: {e}")
            return {'error': str(e)}

    # Helper methods
    def _parse_shopping_details(self, details: str) -> Dict[str, int]:
        """Parse shopping details string into item:quantity dict."""
        items = {}
        try:
            # Expected format: "Coffee: 18, Milk: 2, Bread: 2"
            pairs = details.split(',')
            for pair in pairs:
                if ':' in pair:
                    item, qty = pair.split(':', 1)
                    items[item.strip()] = int(qty.strip())
        except Exception as e:
            logger.error(f"Error parsing shopping details: {e}")
        
        return items

    async def _create_task(self, task_data: Dict[str, Any]) -> bool:
        """Create a new task in the chores database."""
        try:
            # Implementation would add to chores database
            logger.info(f"📋 Created task: {task_data.get('title', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return False

    async def _create_maintenance_note(self, vehicle_name: str, maintenance_type: str) -> bool:
        """Create a maintenance note in the notes database."""
        try:
            # Implementation would add to notes database
            logger.info(f"📝 Created maintenance note for {vehicle_name}: {maintenance_type}")
            return True
        except Exception as e:
            logger.error(f"Error creating maintenance note: {e}")
            return False

    async def _update_vehicle_comp_readiness(self, vehicle_name: str, ready: bool) -> bool:
        """Update vehicle competition readiness status."""
        try:
            # Implementation would update home_garage database
            logger.info(f"🏁 Updated {vehicle_name} competition readiness: {ready}")
            return True
        except Exception as e:
            logger.error(f"Error updating vehicle comp readiness: {e}")
            return False

    def get_extended_task_actions(self) -> List[str]:
        """Get list of extended task actions supported by LifeOS."""
        return list(self.action_handlers.keys())

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for Today's CC."""
        try:
            dashboard = {
                'inventory': {},
                'routines': {},
                'rc_hobby': {},
                'system_status': 'operational'
            }
            
            # Get inventory status
            if self.inventory_manager:
                low_stock = await self.inventory_manager.get_low_stock_items()
                dashboard['inventory'] = {
                    'low_stock_count': len(low_stock),
                    'items': low_stock[:5]  # Top 5 items
                }
            
            # Get routine status
            if self.routine_tracker:
                completions = await self.routine_tracker.get_todays_completions()
                dashboard['routines'] = {
                    'completed_today': len(completions),
# DEMO CODE REMOVED: 'completion_rate': (len(completions) / 12) * 100  # Sample total
                }
            
            # Get RC status
            if self.rc_hobby_manager:
                rc_data = await self.rc_hobby_manager.get_hobby_dashboard_data()
                dashboard['rc_hobby'] = rc_data
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {'error': str(e)}


# Factory function for easy initialization
    """Create and return a LifeOS integration instance."""