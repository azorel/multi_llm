#!/usr/bin/env python3
"""
Intelligent Task Generator
==========================

Analyzes user interactions, patterns, and system state to automatically
generate relevant tasks and suggestions for the LifeOS system.

Features:
- Pattern recognition from user behavior
- Context-aware task suggestions
- Inventory-based automation
- Competition preparation workflows
- Routine optimization recommendations
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from loguru import logger

from ..integrations.notion_mcp_client 

@dataclass
class TaskSuggestion:
    """Represents an intelligent task suggestion."""
    title: str
    action: str
    priority: str  # High, Medium, Low
    details: str
    category: str  # inventory, routine, rc, general
    trigger_reason: str
    estimated_effort: str  # Quick, Medium, Long
    deadline: Optional[datetime] = None
    dependencies: List[str] = None


class IntelligentTaskGenerator:
    """
    Generates intelligent tasks based on system analysis and user patterns.
    """
    
# NOTION_REMOVED:     def __init__(self, notion_client: NotionMCPClient, db_ids: Dict[str, str]):
        """Initialize the task generator."""
# NOTION_REMOVED:         self.notion_client = notion_client
        self.db_ids = db_ids
        
        # Task generation rules
        self.inventory_rules = {
            'coffee_low': {
                'threshold': 3,
                'task_template': {
                    'title': 'Restock Coffee Supply',
                    'action': 'CompleteShoppingTrip',
                    'priority': 'High',
                    'category': 'inventory',
                    'estimated_effort': 'Medium'
                }
            },
            'milk_out': {
                'threshold': 0,
                'task_template': {
                    'title': 'Emergency Milk Run',
                    'action': 'CompleteShoppingTrip', 
                    'priority': 'High',
                    'category': 'inventory',
                    'estimated_effort': 'Quick'
                }
            }
        }
        
        self.routine_patterns = {
            'morning_coffee_usage': {
                'pattern': 'daily_7am',
                'generates': 'coffee_inventory_check'
            },
            'rc_session_prep': {
                'pattern': 'weekend_prep',
                'generates': 'battery_charge_reminder'
            }
        }
        
        self.rc_workflows = {
            'competition_approaching': {
                'trigger_days': 7,
                'generates_tasks': [
                    'vehicle_inspection',
                    'battery_prep',
                    'spare_parts_check',
                    'practice_session_schedule'
                ]
            }
        }

    async def analyze_and_generate_tasks(self) -> List[TaskSuggestion]:
        """
        Analyze current system state and generate intelligent task suggestions.
        
        Returns:
            List of suggested tasks
        """
        suggestions = []
        
        try:
            # Analyze inventory state
            inventory_tasks = await self._analyze_inventory_needs()
            suggestions.extend(inventory_tasks)
            
            # Analyze routine patterns
            routine_tasks = await self._analyze_routine_patterns()
            suggestions.extend(routine_tasks)
            
            # Analyze RC hobby needs
            rc_tasks = await self._analyze_rc_needs()
            suggestions.extend(rc_tasks)
            
            # Analyze upcoming events
            event_tasks = await self._analyze_upcoming_events()
            suggestions.extend(event_tasks)
            
            # Remove duplicates and prioritize
            suggestions = self._prioritize_and_deduplicate(suggestions)
            
            logger.info(f"🧠 Generated {len(suggestions)} intelligent task suggestions")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating intelligent tasks: {e}")
            return []

    async def _analyze_inventory_needs(self) -> List[TaskSuggestion]:
        """Analyze inventory and generate restocking tasks."""
        suggestions = []
        
        try:
            # Get food items
# NOTION_REMOVED:             food_items = await self.notion_client.query_database(
                self.db_ids['food_onhand'],
                filter_conditions={
                    'property': 'Current Stock',
                    'number': {'less_than': 5}
                }
            )
            
            # Get drink items  
# NOTION_REMOVED:             drink_items = await self.notion_client.query_database(
                self.db_ids['drinks'],
                filter_conditions={
                    'property': 'Current Stock', 
                    'number': {'less_than': 3}
                }
            )
            
            # Generate shopping tasks
            low_stock_items = []
            
            for item in food_items.get('results', []):
                item_name = self._extract_title(item)
                current_stock = self._extract_number(item, 'Current Stock')
                low_stock_items.append(f"{item_name} ({current_stock} remaining)")
            
            for item in drink_items.get('results', []):
                item_name = self._extract_title(item)
                current_stock = self._extract_number(item, 'Current Stock')
                low_stock_items.append(f"{item_name} ({current_stock} remaining)")
            
            if low_stock_items:
                suggestions.append(TaskSuggestion(
                    title=f"Shopping Trip - {len(low_stock_items)} Items Low",
                    action="CompleteShoppingTrip",
                    priority="Medium" if len(low_stock_items) < 3 else "High",
                    details=f"Restock: {', '.join(low_stock_items[:3])}{'...' if len(low_stock_items) > 3 else ''}",
                    category="inventory",
                    trigger_reason=f"{len(low_stock_items)} items below threshold",
                    estimated_effort="Medium",
                    deadline=datetime.now() + timedelta(days=2)
                ))
            
            # Check for critical items (stock = 0)
            critical_items = [item for item in low_stock_items if "0 remaining" in item]
            if critical_items:
                suggestions.append(TaskSuggestion(
                    title="Emergency Restock - Critical Items",
                    action="CompleteShoppingTrip",
                    priority="High",
                    details=f"Critical: {', '.join(critical_items)}",
                    category="inventory",
                    trigger_reason="Items completely out of stock",
                    estimated_effort="Quick",
                    deadline=datetime.now() + timedelta(hours=4)
                ))
                
        except Exception as e:
            logger.error(f"Error analyzing inventory: {e}")
            
        return suggestions

    async def _analyze_routine_patterns(self) -> List[TaskSuggestion]:
        """Analyze routine completions and suggest optimizations."""
        suggestions = []
        
        try:
            # Get recent habit completions
            week_ago = datetime.now() - timedelta(days=7)
            
# NOTION_REMOVED:             habits_data = await self.notion_client.query_database(
                self.db_ids['habits'],
                filter_conditions={
                    'property': 'Date',
                    'date': {'after': week_ago.isoformat()}
                }
            )
            
            # Analyze completion patterns
            completion_counts = {}
            for habit in habits_data.get('results', []):
                habit_name = self._extract_title(habit)
                completion_counts[habit_name] = completion_counts.get(habit_name, 0) + 1
            
            # Suggest routine improvements
            for habit_name, count in completion_counts.items():
                completion_rate = count / 7  # Weekly rate
                
                if completion_rate < 0.5:  # Less than 50% completion
                    suggestions.append(TaskSuggestion(
                        title=f"Optimize {habit_name} Routine",
                        action="CompleteRoutine",
                        priority="Medium",
                        details=f"Only {completion_rate:.1%} completion rate this week - consider adjustments",
                        category="routine",
                        trigger_reason=f"Low completion rate: {completion_rate:.1%}",
                        estimated_effort="Medium"
                    ))
                    
        except Exception as e:
            logger.error(f"Error analyzing routines: {e}")
            
        return suggestions

    async def _analyze_rc_needs(self) -> List[TaskSuggestion]:
        """Analyze RC hobby needs and generate maintenance tasks."""
        suggestions = []
        
        try:
            # Get vehicle data
# NOTION_REMOVED:             vehicles = await self.notion_client.query_database(self.db_ids['home_garage'])
            
            for vehicle_data in vehicles.get('results', []):
                vehicle_name = self._extract_title(vehicle_data)
                status = self._extract_select(vehicle_data, 'Status')
                last_used = self._extract_date(vehicle_data, 'Last Used')
                
                # Check for maintenance needs
                if status == "Needs Repair":
                    suggestions.append(TaskSuggestion(
                        title=f"Repair {vehicle_name}",
                        action="RC Repair",
                        priority="High",
                        details=f"Vehicle marked as needing repair",
                        category="rc",
                        trigger_reason="Vehicle status indicates repair needed",
                        estimated_effort="Long"
                    ))
                
                # Check for inactive vehicles
                if last_used:
                    days_since_use = (datetime.now() - last_used).days
                    if days_since_use > 14:  # More than 2 weeks
                        suggestions.append(TaskSuggestion(
                            title=f"Check {vehicle_name} Condition",
                            action="RC Maintenance",
                            priority="Low",
                            details=f"Vehicle unused for {days_since_use} days - check condition",
                            category="rc",
                            trigger_reason=f"Inactive for {days_since_use} days",
                            estimated_effort="Quick"
                        ))
                        
        except Exception as e:
            logger.error(f"Error analyzing RC needs: {e}")
            
        return suggestions

    async def _analyze_upcoming_events(self) -> List[TaskSuggestion]:
        """Analyze upcoming events and generate preparation tasks."""
        suggestions = []
        
        try:
            # Get upcoming events
            future_date = datetime.now() + timedelta(days=30)
            
# NOTION_REMOVED:             events = await self.notion_client.query_database(
                self.db_ids['event_records'],
                filter_conditions={
                    'property': 'Date',
                    'date': {'after': datetime.now().isoformat()}
                }
            )
            
            for event_data in events.get('results', []):
                event_name = self._extract_title(event_data)
                event_date = self._extract_date(event_data, 'Date')
                
                if event_date:
                    days_until = (event_date - datetime.now()).days
                    
                    # Generate prep tasks based on timeline
                    if 1 <= days_until <= 7:  # Within a week
                        suggestions.append(TaskSuggestion(
                            title=f"Final Prep for {event_name}",
                            action="Generate Comp Prep",
                            priority="High",
                            details=f"Event in {days_until} days - final preparations needed",
                            category="rc",
                            trigger_reason=f"Event approaching in {days_until} days",
                            estimated_effort="Medium",
                            deadline=event_date - timedelta(days=1)
                        ))
                    
                    elif 8 <= days_until <= 14:  # 1-2 weeks out
                        suggestions.append(TaskSuggestion(
                            title=f"Prepare for {event_name}",
                            action="Generate Comp Prep",
                            priority="Medium",
                            details=f"Event in {days_until} days - start preparations",
                            category="rc",
                            trigger_reason=f"Event scheduled in {days_until} days",
                            estimated_effort="Long",
                            deadline=event_date - timedelta(days=3)
                        ))
                        
        except Exception as e:
            logger.error(f"Error analyzing upcoming events: {e}")
            
        return suggestions

    def _prioritize_and_deduplicate(self, suggestions: List[TaskSuggestion]) -> List[TaskSuggestion]:
        """Remove duplicates and sort by priority."""
        # Remove duplicates based on title
        seen_titles = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            if suggestion.title not in seen_titles:
                seen_titles.add(suggestion.title)
                unique_suggestions.append(suggestion)
        
        # Sort by priority and deadline
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        
        def sort_key(task):
            priority_val = priority_order.get(task.priority, 3)
            deadline_val = task.deadline.timestamp() if task.deadline else float('inf')
            return (priority_val, deadline_val)
        
        return sorted(unique_suggestions, key=sort_key)

    async def create_suggested_tasks(self, suggestions: List[TaskSuggestion]) -> int:
        """
        Create the suggested tasks in the chores database.
        
        Returns:
            Number of tasks created
        """
        created_count = 0
        
        try:
            for suggestion in suggestions:
                # Create task in chores database
                task_data = {
                    "Name": {"title": [{"text": {"content": suggestion.title}}]},
                    "Action": {"rich_text": [{"text": {"content": suggestion.action}}]},
                    "Priority": {"select": {"name": suggestion.priority}},
                    "Details": {"rich_text": [{"text": {"content": suggestion.details}}]},
                    "Category": {"select": {"name": suggestion.category}},
                    "Created": {"date": {"start": datetime.now().isoformat()}},
                    "AI Generated": {"checkbox": True}
                }
                
                if suggestion.deadline:
                    task_data["Deadline"] = {"date": {"start": suggestion.deadline.isoformat()}}
                
# NOTION_REMOVED:                 result = await self.notion_client.create_page(
                    parent_database_id=self.db_ids['chores'],
                    properties=task_data
                )
                
                if result:
                    created_count += 1
                    logger.info(f"✅ Created task: {suggestion.title}")
                    
        except Exception as e:
            logger.error(f"Error creating suggested tasks: {e}")
            
        return created_count

    # Helper methods for data extraction
    def _extract_title(self, page_data: Dict[str, Any]) -> str:
        """Extract title from page data."""
        try:
            title_prop = page_data.get('properties', {}).get('Name', {})
            if 'title' in title_prop:
                return title_prop['title'][0]['text']['content'] if title_prop['title'] else ""
            return ""
        except:
            return ""

    def _extract_number(self, page_data: Dict[str, Any], prop_name: str) -> int:
        """Extract number property."""
        try:
            prop = page_data.get('properties', {}).get(prop_name, {})
            return prop.get('number', 0) or 0
        except:
            return 0

    def _extract_select(self, page_data: Dict[str, Any], prop_name: str) -> str:
        """Extract select property."""
        try:
            prop = page_data.get('properties', {}).get(prop_name, {})
            select_val = prop.get('select')
            return select_val.get('name', '') if select_val else ''
        except:
            return ""

    def _extract_date(self, page_data: Dict[str, Any], prop_name: str) -> Optional[datetime]:
        """Extract date property."""
        try:
            prop = page_data.get('properties', {}).get(prop_name, {})
            date_val = prop.get('date')
            if date_val and date_val.get('start'):
                return datetime.fromisoformat(date_val['start'].replace('Z', '+00:00'))
            return None
        except:
            return None


# Factory function
# NOTION_REMOVED: def create_intelligent_task_generator(notion_client: NotionMCPClient, db_ids: Dict[str, str]) -> IntelligentTaskGenerator:
    """Create and return an intelligent task generator instance."""
    return IntelligentTaskGenerator(notion_client, db_ids)