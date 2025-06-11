#!/usr/bin/env python3
"""
LifeOS Management Classes
========================

Core management classes for the complete LifeOS system:
- InventoryManager: Household inventory and shopping automation
- RoutineTracker: Daily routine tracking and analysis
- RCHobbyManager: RC hobby and competition management
- RCCompetitionManager: Competition prep and vehicle management

Integrates with existing Notion databases and extends functionality.
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger

from ..integrations.notion_mcp_client 

class InventoryManager:
    """
    Manages household inventory, shopping lists, and restocking automation.
    
    Integrates with existing Food Onhand, Drinks, and Things Bought databases.
    Provides smart shopping list generation and usage tracking.
    """
    
# NOTION_REMOVED:     def __init__(self, notion_client: NotionMCPClient, db_ids: Dict[str, str]):
# NOTION_REMOVED:         self.notion = notion_client
        self.food_db_id = db_ids.get('food_onhand')
        self.drinks_db_id = db_ids.get('drinks')
        self.things_bought_db_id = db_ids.get('things_bought')
        self.inventory_db_id = db_ids.get('household_inventory')  # New consolidated DB
        
        # Inventory thresholds
        self.default_thresholds = {
            'coffee_packets': {'min': 3, 'restock': 18},
            'milk': {'min': 0, 'restock': 2},
            'bread': {'min': 1, 'restock': 2},
            'eggs': {'min': 6, 'restock': 12},
            'toilet_paper': {'min': 2, 'restock': 12}
        }

    async def process_item_usage(self, item_name: str, quantity_used: int, notes: str = "") -> Dict[str, Any]:
        """
        Process usage of an inventory item.
        
        Args:
            item_name: Name of the item used
            quantity_used: Amount consumed
            notes: Optional usage notes
            
        Returns:
            Result dict with status and actions taken
        """
        try:
            result = {
                'item': item_name,
                'quantity_used': quantity_used,
                'current_stock': 0,
                'needs_shopping': False,
                'shopping_task_created': False,
                'error': None
            }
            
            # Find the item in inventory
            item_data = await self._find_inventory_item(item_name)
            
            if not item_data:
                # Create new inventory item if it doesn't exist
                item_data = await self._create_inventory_item(item_name, quantity_used)
                result['error'] = f"Item '{item_name}' not found in inventory, created new entry"
            
            # Update current stock
            new_stock = max(0, item_data.get('current_stock', 0) - quantity_used)
            await self._update_item_stock(item_data['id'], new_stock)
            result['current_stock'] = new_stock
            
            # Check if item needs restocking
            min_threshold = item_data.get('min_threshold', 1)
            if new_stock <= min_threshold:
                result['needs_shopping'] = True
                
                # Create shopping task
                shopping_task = await self._create_shopping_task(item_data)
                if shopping_task:
                    result['shopping_task_created'] = True
                    logger.info(f"📦 Shopping task created for {item_name} (stock: {new_stock})")
            
            # Log usage
            await self._log_item_usage(item_name, quantity_used, new_stock, notes)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing item usage for {item_name}: {e}")
            return {'error': str(e), 'item': item_name}

    async def get_low_stock_items(self) -> List[Dict[str, Any]]:
        """Get all items that need restocking."""
        try:
            # Query inventory for items below threshold
            low_stock_items = []
            
            # This would query your inventory databases
# DEMO CODE REMOVED: # For now, return sample data
# DEMO CODE REMOVED: sample_items = [
                {
                    'name': 'Coffee Packets',
                    'current_stock': 2,
                    'min_threshold': 3,
                    'restock_amount': 18,
                    'primary_store': 'Walmart',
                    'estimated_price': 8.99
                },
                {
                    'name': 'Milk',
                    'current_stock': 0,
                    'min_threshold': 0,
                    'restock_amount': 2,
                    'primary_store': 'Walmart',
                    'estimated_price': 3.49
                }
            ]
            
# DEMO CODE REMOVED: return sample_items
            
        except Exception as e:
            logger.error(f"Error getting low stock items: {e}")
            return []

    async def restock_item(self, item_name: str, new_amount: int, store: str = "", price: float = 0.0) -> bool:
        """
        Update inventory after shopping/restocking.
        
        Args:
            item_name: Name of item restocked
            new_amount: New quantity added
            store: Store where purchased
            price: Price paid
            
        Returns:
            Success status
        """
        try:
            # Find and update inventory item
            item_data = await self._find_inventory_item(item_name)
            if not item_data:
                logger.error(f"Item '{item_name}' not found for restocking")
                return False
            
            # Update stock
            current_stock = item_data.get('current_stock', 0)
            new_stock = current_stock + new_amount
            await self._update_item_stock(item_data['id'], new_stock)
            
            # Log purchase in Things Bought database
            if price > 0:
                await self._log_purchase(item_name, new_amount, store, price)
            
            # Update last restocked date
            await self._update_last_restocked(item_data['id'])
            
            logger.info(f"📦 Restocked {item_name}: {current_stock} → {new_stock}")
            return True
            
        except Exception as e:
            logger.error(f"Error restocking {item_name}: {e}")
            return False

    async def morning_inventory_analysis(self) -> Dict[str, Any]:
        """
        Run morning inventory analysis and create shopping tasks.
        
        Returns:
            Analysis results with actions taken
        """
        try:
            result = {
                'low_stock_items': [],
                'shopping_tasks_created': 0,
                'total_estimated_cost': 0.0,
                'recommended_stores': [],
                'analysis_time': datetime.now().isoformat()
            }
            
            # Get low stock items
            low_stock = await self.get_low_stock_items()
            result['low_stock_items'] = low_stock
            
            if low_stock:
                # Group by store for efficient shopping
                stores = {}
                for item in low_stock:
                    store = item.get('primary_store', 'Unknown')
                    if store not in stores:
                        stores[store] = []
                    stores[store].append(item)
                    result['total_estimated_cost'] += item.get('estimated_price', 0)
                
                result['recommended_stores'] = list(stores.keys())
                
                # Create shopping tasks for each store
                for store, items in stores.items():
                    task_created = await self._create_store_shopping_task(store, items)
                    if task_created:
                        result['shopping_tasks_created'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error in morning inventory analysis: {e}")
            return {'error': str(e)}

    # Private helper methods
    async def _find_inventory_item(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Find an item in the inventory database."""
        # This would query your Notion databases
        # Implementation depends on your specific database structure
        return None

    async def _create_inventory_item(self, item_name: str, initial_stock: int) -> Dict[str, Any]:
        """Create a new inventory item."""
        # Implementation would create new database entry
        return {'id': 'new_item_id', 'current_stock': initial_stock}

    async def _update_item_stock(self, item_id: str, new_stock: int) -> bool:
        """Update the stock level of an item."""
        # Implementation would update Notion database
        return True

    async def _create_shopping_task(self, item_data: Dict[str, Any]) -> bool:
        """Create a shopping task for an item."""
        # Implementation would create task in chores database
        return True

    async def _log_item_usage(self, item_name: str, quantity: int, remaining: int, notes: str) -> bool:
        """Log item usage for tracking."""
        # Implementation would log to lifelog database
        return True

    async def _log_purchase(self, item_name: str, quantity: int, store: str, price: float) -> bool:
        """Log purchase in Things Bought database."""
        # Implementation would add to things_bought database
        return True

    async def _update_last_restocked(self, item_id: str) -> bool:
        """Update last restocked date."""
        # Implementation would update database
        return True

    async def _create_store_shopping_task(self, store: str, items: List[Dict[str, Any]]) -> bool:
        """Create a shopping task for a specific store."""
        # Implementation would create comprehensive shopping task
        return True


class RoutineTracker:
    """
    Tracks daily routine completion and provides analytics.
    
    Integrates with existing habits database and creates routine templates.
    Provides completion tracking and routine optimization insights.
    """
    
# NOTION_REMOVED:     def __init__(self, notion_client: NotionMCPClient, db_ids: Dict[str, str]):
# NOTION_REMOVED:         self.notion = notion_client
        self.habits_db_id = db_ids.get('habits')
        self.routine_templates_db_id = db_ids.get('routine_templates')
        self.routine_tracking_db_id = db_ids.get('routine_tracking')

    async def complete_routine_activity(self, activity_name: str, notes: str = "", duration: int = 0) -> Dict[str, Any]:
        """
        Mark a routine activity as completed.
        
        Args:
            activity_name: Name of the routine activity
            notes: Optional completion notes
            duration: Time taken in minutes
            
        Returns:
            Completion result with analytics
        """
        try:
            result = {
                'activity': activity_name,
                'completed_at': datetime.now().isoformat(),
                'streak_count': 0,
                'weekly_completion_rate': 0.0,
                'next_activity': None,
                'error': None
            }
            
            # Log completion in routine tracking database
            completion_logged = await self._log_routine_completion(
                activity_name, notes, duration
            )
            
            if completion_logged:
                # Calculate streak and completion rate
                result['streak_count'] = await self._calculate_streak(activity_name)
                result['weekly_completion_rate'] = await self._calculate_completion_rate(
                    activity_name, days=7
                )
                
                # Get next routine activity
                result['next_activity'] = await self._get_next_routine_activity()
                
                logger.info(f"✅ Routine completed: {activity_name}")
            else:
                result['error'] = "Failed to log completion"
            
            return result
            
        except Exception as e:
            logger.error(f"Error completing routine {activity_name}: {e}")
            return {'error': str(e), 'activity': activity_name}

    async def get_todays_completions(self) -> List[Dict[str, Any]]:
        """Get all routine completions for today."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Query routine tracking database for today's completions
            completions = []
            
# DEMO CODE REMOVED: # Sample data - would come from actual database
# DEMO CODE REMOVED: sample_completions = [
                {
                    'activity': 'Wake Up',
                    'completed_at': '07:00',
                    'duration': 5,
                    'notes': 'Feeling good today'
                },
                {
                    'activity': 'Coffee & Email',
                    'completed_at': '07:30',
                    'duration': 20,
                    'notes': 'Caught up on overnight emails'
                }
            ]
            
# DEMO CODE REMOVED: return sample_completions
            
        except Exception as e:
            logger.error(f"Error getting today's completions: {e}")
            return []

    async def get_routine_stats(self, activity_name: str, days_back: int = 7) -> Dict[str, Any]:
        """
        Get completion statistics for a routine activity.
        
        Args:
            activity_name: Name of the activity
            days_back: Number of days to analyze
            
        Returns:
            Statistics dict with completion data
        """
        try:
            stats = {
                'activity': activity_name,
                'days_analyzed': days_back,
                'total_completions': 0,
                'completion_rate': 0.0,
                'current_streak': 0,
                'longest_streak': 0,
                'average_duration': 0,
                'best_time': None,
                'completion_pattern': []
            }
            
            # Query database for completion history
            # Implementation would analyze actual data
            
# DEMO CODE REMOVED: # Sample stats
            stats.update({
                'total_completions': 5,
                'completion_rate': 71.4,  # 5/7 days
                'current_streak': 3,
                'longest_streak': 5,
                'average_duration': 15,
                'best_time': '07:30'
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting routine stats for {activity_name}: {e}")
            return {'error': str(e)}

    # Private helper methods
    async def _log_routine_completion(self, activity: str, notes: str, duration: int) -> bool:
        """Log routine completion to database."""
        # Implementation would add to routine_tracking database
        return True

    async def _calculate_streak(self, activity_name: str) -> int:
        """Calculate current completion streak."""
        # Implementation would count consecutive completions
# DEMO CODE REMOVED: return 3  # Sample

    async def _calculate_completion_rate(self, activity_name: str, days: int) -> float:
        """Calculate completion rate over specified days."""
        # Implementation would calculate percentage
# DEMO CODE REMOVED: return 71.4  # Sample

    async def _get_next_routine_activity(self) -> Optional[str]:
        """Get the next scheduled routine activity."""
        # Implementation would check routine templates
# DEMO CODE REMOVED: return "Lunch Break"  # Sample


class RCCompetitionManager:
    """
    Manages RC competitions, prep tasks, and vehicle readiness.
    
    Integrates with existing Event Records and Home Garage databases.
    Provides automated competition prep task generation.
    """
    
# NOTION_REMOVED:     def __init__(self, notion_client: NotionMCPClient, db_ids: Dict[str, str]):
# NOTION_REMOVED:         self.notion = notion_client
        self.competitions_db_id = db_ids.get('event_records')
        self.vehicles_db_id = db_ids.get('home_garage')
        self.issues_db_id = db_ids.get('vehicle_issues')
        self.tasks_db_id = db_ids.get('chores')

    async def generate_comp_prep_tasks(self, competition_id: str) -> Dict[str, Any]:
        """
        Generate preparation tasks for a competition.
        
        Args:
            competition_id: ID of the competition
            
        Returns:
            Result with tasks created
        """
        try:
            result = {
                'competition_id': competition_id,
                'tasks_created': 0,
                'vehicle_checks': [],
                'prep_timeline': [],
                'estimated_prep_time': 0,
                'error': None
            }
            
            # Get competition details
            comp_data = await self._get_competition_details(competition_id)
            if not comp_data:
                result['error'] = "Competition not found"
                return result
            
            # Get vehicle for competition
            vehicle = comp_data.get('vehicle_planned')
            if not vehicle:
                result['error'] = "No vehicle assigned to competition"
                return result
            
            # Generate standard prep tasks
            prep_tasks = [
                {
                    'title': f"Battery Check - {vehicle}",
                    'action': 'RC Maintenance',
                    'priority': 'High',
                    'due_date': comp_data['event_date'] - timedelta(days=2),
                    'details': 'Check battery voltage and charge level'
                },
                {
                    'title': f"Tire Inspection - {vehicle}",
                    'action': 'RC Maintenance', 
                    'priority': 'High',
                    'due_date': comp_data['event_date'] - timedelta(days=2),
                    'details': 'Check tire wear and compound selection'
                },
                {
                    'title': f"Diff Oil Check - {vehicle}",
                    'action': 'RC Maintenance',
                    'priority': 'Medium',
                    'due_date': comp_data['event_date'] - timedelta(days=3),
                    'details': 'Check differential oil levels and consistency'
                },
                {
                    'title': f"Spare Parts Kit - {comp_data['name']}",
                    'action': 'RC Comp Prep',
                    'priority': 'Medium',
                    'due_date': comp_data['event_date'] - timedelta(days=1),
                    'details': 'Pack spare parts: axles, drive shafts, steering links'
                },
                {
                    'title': f"Load Vehicle - {comp_data['name']}",
                    'action': 'RC Comp Prep',
                    'priority': 'High',
                    'due_date': comp_data['event_date'],
                    'details': 'Load vehicle and gear for competition'
                }
            ]
            
            # Create tasks in database
            for task in prep_tasks:
                task_created = await self._create_prep_task(task, competition_id)
                if task_created:
                    result['tasks_created'] += 1
                    result['prep_timeline'].append({
                        'date': task['due_date'].strftime('%Y-%m-%d'),
                        'task': task['title'],
                        'priority': task['priority']
                    })
            
            # Calculate estimated prep time
            result['estimated_prep_time'] = len(prep_tasks) * 30  # 30 min average per task
            
            # Mark competition as having prep tasks generated
            await self._mark_prep_tasks_generated(competition_id)
            
            logger.info(f"🏆 Generated {result['tasks_created']} prep tasks for {comp_data['name']}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating comp prep tasks: {e}")
            return {'error': str(e)}

    async def create_vehicle_issue(self, vehicle_name: str, issue_title: str, 
                                 description: str, severity: str, event_name: str = "") -> str:
        """
        Create a vehicle issue/repair entry.
        
        Args:
            vehicle_name: Name of the vehicle
            issue_title: Brief issue description
            description: Detailed description
            severity: Issue severity (Critical, High, Medium, Low)
            event_name: Event where issue occurred (optional)
            
        Returns:
            Issue ID if created successfully
        """
        try:
            issue_data = {
                'title': issue_title,
                'vehicle': vehicle_name,
                'description': description,
                'severity': severity,
                'status': 'Open',
                'issue_date': datetime.now().isoformat(),
                'caused_by_event': event_name,
                'blocks_driving': severity in ['Critical', 'High']
            }
            
            # Create issue in database
            issue_id = await self._create_vehicle_issue(issue_data)
            
            if issue_id:
                # Update vehicle status if critical issue
                if severity == 'Critical':
                    await self._update_vehicle_status(vehicle_name, 'Needs Repair')
                
                # Create repair task
                await self._create_repair_task(issue_id, issue_data)
                
                logger.info(f"🔧 Created {severity} issue for {vehicle_name}: {issue_title}")
            
            return issue_id
            
        except Exception as e:
            logger.error(f"Error creating vehicle issue: {e}")
            return ""

    async def complete_vehicle_repair(self, issue_id: str, repair_notes: str, 
                                    parts_used: List[str] = None, cost: float = 0.0) -> bool:
        """
        Mark a vehicle repair as complete.
        
        Args:
            issue_id: ID of the issue being repaired
            repair_notes: Notes about the repair
            parts_used: List of parts used in repair
            cost: Cost of repair
            
        Returns:
            Success status
        """
        try:
            # Update issue status
            repair_data = {
                'status': 'Fixed',
                'fixed_date': datetime.now().isoformat(),
                'repair_notes': repair_notes,
                'actual_cost': cost
            }
            
            if parts_used:
                repair_data['parts_used'] = parts_used
            
            # Update issue in database
            updated = await self._update_vehicle_issue(issue_id, repair_data)
            
            if updated:
                # Get issue details to update vehicle status
                issue_data = await self._get_issue_details(issue_id)
                vehicle_name = issue_data.get('vehicle')
                
                # Check if vehicle has any remaining critical issues
                remaining_issues = await self._get_vehicle_critical_issues(vehicle_name)
                
                if not remaining_issues:
                    # Mark vehicle as ready if no critical issues remain
                    await self._update_vehicle_status(vehicle_name, 'Ready to Run')
                
                logger.info(f"✅ Completed repair for issue {issue_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error completing vehicle repair: {e}")
            return False

    # Private helper methods
    async def _get_competition_details(self, comp_id: str) -> Optional[Dict[str, Any]]:
        """Get competition details from database."""
        # Implementation would query event_records database
        return {
            'name': 'G6 Trail Challenge',
            'event_date': datetime.now() + timedelta(days=7),
            'vehicle_planned': 'TRX-4 Defender'
        }

    async def _create_prep_task(self, task_data: Dict[str, Any], comp_id: str) -> bool:
        """Create a prep task in the tasks database."""
        # Implementation would add to chores database
        return True

    async def _mark_prep_tasks_generated(self, comp_id: str) -> bool:
        """Mark competition as having prep tasks generated."""
        # Implementation would update event_records database
        return True

    async def _create_vehicle_issue(self, issue_data: Dict[str, Any]) -> str:
        """Create vehicle issue in database."""
        # Implementation would add to vehicle_issues database
        return "issue_123"

    async def _update_vehicle_status(self, vehicle_name: str, status: str) -> bool:
        """Update vehicle status in garage database."""
        # Implementation would update home_garage database
        return True

    async def _create_repair_task(self, issue_id: str, issue_data: Dict[str, Any]) -> bool:
        """Create repair task in tasks database."""
        # Implementation would add to chores database
        return True

    async def _update_vehicle_issue(self, issue_id: str, repair_data: Dict[str, Any]) -> bool:
        """Update vehicle issue with repair information."""
        # Implementation would update vehicle_issues database
        return True

    async def _get_issue_details(self, issue_id: str) -> Dict[str, Any]:
        """Get issue details from database."""
        # Implementation would query vehicle_issues database
        return {'vehicle': 'TRX-4 Defender'}

    async def _get_vehicle_critical_issues(self, vehicle_name: str) -> List[Dict[str, Any]]:
        """Get remaining critical issues for a vehicle."""
        # Implementation would query vehicle_issues database
        return []


class RCHobbyManager:
    """
    Comprehensive RC hobby management system.
    
    Integrates all RC-related functionality: vehicles, parts, competitions, projects.
    Provides high-level hobby management operations.
    """
    
# NOTION_REMOVED:     def __init__(self, notion_client: NotionMCPClient, db_ids: Dict[str, str]):
# NOTION_REMOVED:         self.notion = notion_client
        self.db_ids = db_ids
# NOTION_REMOVED:         self.competition_manager = RCCompetitionManager(notion_client, db_ids)
        
        # RC-specific database IDs
        self.manufacturers_db_id = db_ids.get('rc_manufacturers')
        self.vehicles_db_id = db_ids.get('home_garage')
        self.parts_db_id = db_ids.get('rc_parts')
        self.projects_db_id = db_ids.get('rc_projects')

    async def add_rc_part(self, part_name: str, manufacturer_name: str, 
                         part_number: str = "", quantity: int = 1, price: float = 0.0) -> Dict[str, Any]:
        """
        Add a new RC part to inventory.
        
        Args:
            part_name: Name of the part
            manufacturer_name: Manufacturer name
            part_number: Part number (optional)
            quantity: Quantity to add
            price: Price paid
            
        Returns:
            Result dict with part information
        """
        try:
            result = {
                'part_name': part_name,
                'manufacturer': manufacturer_name,
                'quantity_added': quantity,
                'total_inventory': 0,
                'part_id': None,
                'error': None
            }
            
            # Check if part already exists
            existing_part = await self._find_rc_part(part_name, manufacturer_name)
            
            if existing_part:
                # Update existing part quantity
                new_quantity = existing_part.get('quantity', 0) + quantity
                await self._update_part_quantity(existing_part['id'], new_quantity)
                result['part_id'] = existing_part['id']
                result['total_inventory'] = new_quantity
            else:
                # Create new part entry
                part_data = {
                    'name': part_name,
                    'manufacturer': manufacturer_name,
                    'part_number': part_number,
                    'quantity': quantity,
                    'price_paid': price,
                    'purchase_date': datetime.now().isoformat(),
                    'status': 'In Stock'
                }
                
                part_id = await self._create_rc_part(part_data)
                result['part_id'] = part_id
                result['total_inventory'] = quantity
            
            logger.info(f"🔧 Added RC part: {part_name} (qty: {quantity})")
            return result
            
        except Exception as e:
            logger.error(f"Error adding RC part {part_name}: {e}")
            return {'error': str(e), 'part_name': part_name}

    async def get_parts_needing_order(self) -> List[Dict[str, Any]]:
        """Get RC parts that need to be ordered."""
        try:
            # Query parts database for low stock items
            low_stock_parts = []
            
# DEMO CODE REMOVED: # Sample data - would come from actual database query
# DEMO CODE REMOVED: sample_parts = [
                {
                    'name': '12mm Hex Adapters',
                    'manufacturer': 'Yeah Racing',
                    'current_quantity': 0,
                    'min_stock': 2,
                    'estimated_price': 15.99,
                    'last_supplier': 'AMain Hobbies'
                },
                {
                    'name': 'Differential Oil 10k',
                    'manufacturer': 'Traxxas',
                    'current_quantity': 1,
                    'min_stock': 2,
                    'estimated_price': 8.99,
                    'last_supplier': 'Local Hobby Shop'
                }
            ]
            
# DEMO CODE REMOVED: return sample_parts
            
        except Exception as e:
            logger.error(f"Error getting parts needing order: {e}")
            return []

    async def charge_batteries_for_vehicle(self, vehicle_name: str) -> Dict[str, Any]:
        """
        Mark batteries as charged for a specific vehicle.
        
        Args:
            vehicle_name: Name of the vehicle
            
        Returns:
            Result dict with battery status
        """
        try:
            result = {
                'vehicle': vehicle_name,
                'batteries_charged': 0,
                'charge_time': datetime.now().isoformat(),
                'estimated_runtime': 0,
                'error': None
            }
            
            # Get vehicle details
            vehicle_data = await self._get_vehicle_details(vehicle_name)
            if not vehicle_data:
                result['error'] = f"Vehicle '{vehicle_name}' not found"
                return result
            
            # Update battery status
            await self._update_vehicle_battery_status(vehicle_data['id'], 'Charged')
            
# DEMO CODE REMOVED: # Sample battery info
            result['batteries_charged'] = 2  # Number of batteries
            result['estimated_runtime'] = 45  # Minutes of runtime
            
            logger.info(f"🔋 Batteries charged for {vehicle_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error charging batteries for {vehicle_name}: {e}")
            return {'error': str(e), 'vehicle': vehicle_name}

    async def get_vehicles_needing_repair(self) -> List[Dict[str, Any]]:
        """Get vehicles that have open repair issues."""
        try:
            # Query for vehicles with open issues
            vehicles_needing_repair = []
            
# DEMO CODE REMOVED: # Sample data - would come from actual database query
# DEMO CODE REMOVED: sample_vehicles = [
                {
                    'name': 'TRX-4 Defender',
                    'critical_issues': 1,
                    'high_issues': 0,
                    'total_issues': 2,
                    'status': 'Needs Repair',
                    'last_driven': '2025-06-01',
                    'next_competition': 'G6 Trail Challenge'
                },
                {
                    'name': 'SCX24 Deadbolt',
                    'critical_issues': 0,
                    'high_issues': 1,
                    'total_issues': 1,
                    'status': 'Needs Maintenance',
                    'last_driven': '2025-06-05',
                    'next_competition': None
                }
            ]
            
# DEMO CODE REMOVED: return sample_vehicles
            
        except Exception as e:
            logger.error(f"Error getting vehicles needing repair: {e}")
            return []

    async def get_hobby_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive RC hobby dashboard data."""
        try:
            dashboard = {
                'vehicles': {
                    'total': 0,
                    'ready': 0,
                    'needs_repair': 0,
                    'in_progress': 0
                },
                'parts': {
                    'total_items': 0,
                    'need_ordering': 0,
                    'estimated_order_cost': 0.0
                },
                'competitions': {
                    'upcoming': 0,
                    'this_month': 0,
                    'prep_tasks_pending': 0
                },
                'projects': {
                    'active': 0,
                    'planning': 0,
                    'completed_this_month': 0
                }
            }
            
            # Get vehicle status counts
            vehicles = await self._get_all_vehicles()
            dashboard['vehicles']['total'] = len(vehicles)
            for vehicle in vehicles:
                status = vehicle.get('status', 'Unknown')
                if status == 'Ready to Run':
                    dashboard['vehicles']['ready'] += 1
                elif status in ['Needs Repair', 'Needs Maintenance']:
                    dashboard['vehicles']['needs_repair'] += 1
                elif status == 'In Progress':
                    dashboard['vehicles']['in_progress'] += 1
            
            # Get parts that need ordering
            parts_needed = await self.get_parts_needing_order()
            dashboard['parts']['need_ordering'] = len(parts_needed)
            dashboard['parts']['estimated_order_cost'] = sum(
                part.get('estimated_price', 0) for part in parts_needed
            )
            
            # Get upcoming competitions
            upcoming_comps = await self._get_upcoming_competitions()
            dashboard['competitions']['upcoming'] = len(upcoming_comps)
            dashboard['competitions']['prep_tasks_pending'] = sum(
                1 for comp in upcoming_comps if not comp.get('prep_tasks_generated', False)
            )
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error getting hobby dashboard data: {e}")
            return {'error': str(e)}

    # Private helper methods
    async def _find_rc_part(self, part_name: str, manufacturer: str) -> Optional[Dict[str, Any]]:
        """Find an RC part in the database."""
        # Implementation would query rc_parts database
        return None

    async def _update_part_quantity(self, part_id: str, new_quantity: int) -> bool:
        """Update part quantity in database."""
        # Implementation would update rc_parts database
        return True

    async def _create_rc_part(self, part_data: Dict[str, Any]) -> str:
        """Create new RC part in database."""
        # Implementation would add to rc_parts database
        return "part_123"

    async def _get_vehicle_details(self, vehicle_name: str) -> Optional[Dict[str, Any]]:
        """Get vehicle details from database."""
        # Implementation would query home_garage database
        return {'id': 'vehicle_123', 'name': vehicle_name}

    async def _update_vehicle_battery_status(self, vehicle_id: str, status: str) -> bool:
        """Update vehicle battery status."""
        # Implementation would update home_garage database
        return True

    async def _get_all_vehicles(self) -> List[Dict[str, Any]]:
        """Get all vehicles from database."""
        # Implementation would query home_garage database
        return [
            {'name': 'TRX-4 Defender', 'status': 'Ready to Run'},
            {'name': 'SCX24 Deadbolt', 'status': 'Needs Repair'},
            {'name': 'TRX-6 Mercedes', 'status': 'In Progress'},
            {'name': 'Wraith Spawn', 'status': 'Ready to Run'}
        ]

    async def _get_upcoming_competitions(self) -> List[Dict[str, Any]]:
        """Get upcoming competitions."""
        # Implementation would query event_records database
        return [
            {
                'name': 'G6 Trail Challenge',
                'date': '2025-06-15',
                'prep_tasks_generated': False
            },
            {
                'name': 'Local Club Crawl',
                'date': '2025-06-22', 
                'prep_tasks_generated': True
            }
        ]