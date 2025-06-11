#!/usr/bin/env python3
"""
RC Maintenance Scheduler - Automated RC Hobby Management
========================================================

This module provides automated maintenance scheduling, inventory monitoring,
and event preparation for RC vehicles and equipment. It integrates with the
discovered LifeOS Notion workspace to provide:

- Predictive maintenance scheduling based on usage patterns
- Automated inventory monitoring with reorder alerts  
- Event preparation checklists and notifications
- Performance tracking and optimization recommendations

Based on comprehensive Notion workspace discovery with RC management databases:
- Home Garage (13 props) - Equipment inventory and status
- Maintenance Schedule (15 props) - Maintenance tracking
- Maintenance Records (8 props) - Historical maintenance data
- Event Records (8 props) - RC event participation tracking
- RC Manufacturers (6 props) - Manufacturer and part information
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from loguru import logger

# import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from integrations.notion_mcp_client 

class MaintenanceUrgency(Enum):
    OVERDUE = "overdue"
    DUE_TODAY = "due_today"  
    DUE_THIS_WEEK = "due_this_week"
    DUE_NEXT_WEEK = "due_next_week"
    UPCOMING = "upcoming"


class InventoryStatus(Enum):
    OUT_OF_STOCK = "out_of_stock"
    LOW_STOCK = "low_stock"
    REORDER_POINT = "reorder_point"
    ADEQUATE = "adequate"
    OVERSTOCKED = "overstocked"


@dataclass
class MaintenanceAlert:
    item_name: str
    urgency: MaintenanceUrgency
    due_date: Optional[datetime]
    maintenance_type: str
    last_performed: Optional[datetime]
    estimated_hours: float
    parts_needed: List[str]
    page_id: str


@dataclass
class InventoryAlert:
    item_name: str
    current_stock: int
    minimum_stock: int
    reorder_quantity: int
    status: InventoryStatus
    estimated_cost: float
    preferred_supplier: str
    page_id: str


@dataclass
class EventPreparation:
    event_name: str
    event_date: datetime
    vehicles_needed: List[str]
    equipment_checklist: List[str]
    maintenance_required: List[MaintenanceAlert]
    inventory_needed: List[str]
    preparation_status: str
    page_id: str


class RCMaintenanceScheduler:
    """
    Automated RC maintenance and inventory management system.
    
    Provides intelligent scheduling, monitoring, and alerts for RC hobby management.
    """
    
        """Initialize the RC maintenance scheduler."""
        
        # Database IDs from LifeOS discovery
# NOTION_REMOVED:         self.home_garage_db_id = os.getenv('NOTION_HOME_GARAGE_DB_ID')
# NOTION_REMOVED:         self.maintenance_schedule_db_id = os.getenv('NOTION_MAINTENANCE_SCHEDULE_DB_ID')
# NOTION_REMOVED:         self.maintenance_records_db_id = os.getenv('NOTION_MAINTENANCE_RECORDS_DB_ID')
# NOTION_REMOVED:         self.event_records_db_id = os.getenv('NOTION_EVENT_RECORDS_DB_ID')
# NOTION_REMOVED:         self.rc_manufacturers_db_id = os.getenv('NOTION_RC_MANUFACTURERS_DB_ID')
# NOTION_REMOVED:         self.lifelog_db_id = os.getenv('NOTION_LIFELOG_DB_ID')
        
        # Configuration
        self.low_stock_threshold = 3
        self.reorder_point_multiplier = 1.5
        self.maintenance_buffer_days = 7
        
    async def check_maintenance_schedule(self) -> List[MaintenanceAlert]:
        """Check all maintenance items and generate alerts for overdue/upcoming maintenance."""
        logger.info("🔧 Checking RC maintenance schedules...")
        
        alerts = []
        
        try:
            # Get all maintenance schedule items
# NOTION_REMOVED:             maintenance_items = await self.notion.query_database(
                self.maintenance_schedule_db_id,
                page_size=50
            )
            
            today = datetime.now()
            
            for item in maintenance_items:
                alert = await self._process_maintenance_item(item, today)
                if alert:
                    alerts.append(alert)
            
            # Sort by urgency
            urgency_order = {
                MaintenanceUrgency.OVERDUE: 0,
                MaintenanceUrgency.DUE_TODAY: 1,
                MaintenanceUrgency.DUE_THIS_WEEK: 2,
                MaintenanceUrgency.DUE_NEXT_WEEK: 3,
                MaintenanceUrgency.UPCOMING: 4
            }
            
            alerts.sort(key=lambda x: urgency_order[x.urgency])
            
            logger.info(f"Generated {len(alerts)} maintenance alerts")
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking maintenance schedule: {e}")
            return []
    
    async def _process_maintenance_item(self, item: Dict[str, Any], today: datetime) -> Optional[MaintenanceAlert]:
        """Process a single maintenance item and determine if an alert is needed."""
        try:
            props = item.get('properties', {})
            
            # Extract item information
            item_name = self._extract_title(props, ['Name', 'Item', 'Vehicle'])
            if not item_name:
                return None
            
            # Extract due date
            due_date = self._extract_date(props, ['Due Date', 'Next Due', 'Scheduled Date'])
            if not due_date:
                return None
            
            # Calculate urgency
            days_until_due = (due_date - today).days
            
            if days_until_due < 0:
                urgency = MaintenanceUrgency.OVERDUE
            elif days_until_due == 0:
                urgency = MaintenanceUrgency.DUE_TODAY
            elif days_until_due <= 7:
                urgency = MaintenanceUrgency.DUE_THIS_WEEK
            elif days_until_due <= 14:
                urgency = MaintenanceUrgency.DUE_NEXT_WEEK
            else:
                urgency = MaintenanceUrgency.UPCOMING
            
            # Only alert for items due within the next 2 weeks or overdue
            if days_until_due > 14:
                return None
            
            # Extract additional information
            maintenance_type = self._extract_select(props, ['Type', 'Maintenance Type', 'Category'])
            last_performed = self._extract_date(props, ['Last Performed', 'Last Done', 'Completed Date'])
            estimated_hours = self._extract_number(props, ['Estimated Hours', 'Duration', 'Time Required'])
            parts_needed = self._extract_multi_select(props, ['Parts Needed', 'Required Parts', 'Components'])
            
            return MaintenanceAlert(
                item_name=item_name,
                urgency=urgency,
                due_date=due_date,
                maintenance_type=maintenance_type or "General Maintenance",
                last_performed=last_performed,
                estimated_hours=estimated_hours or 1.0,
                parts_needed=parts_needed or [],
                page_id=item['id']
            )
            
        except Exception as e:
            logger.error(f"Error processing maintenance item: {e}")
            return None
    
    async def check_inventory_levels(self) -> List[InventoryAlert]:
        """Monitor RC inventory and generate reorder alerts."""
        logger.info("📦 Checking RC inventory levels...")
        
        alerts = []
        
        try:
            # Get all garage inventory items
# NOTION_REMOVED:             inventory_items = await self.notion.query_database(
                self.home_garage_db_id,
                page_size=100
            )
            
            for item in inventory_items:
                alert = await self._process_inventory_item(item)
                if alert:
                    alerts.append(alert)
            
            # Sort by urgency (out of stock first)
            status_order = {
                InventoryStatus.OUT_OF_STOCK: 0,
                InventoryStatus.LOW_STOCK: 1,
                InventoryStatus.REORDER_POINT: 2,
                InventoryStatus.ADEQUATE: 3,
                InventoryStatus.OVERSTOCKED: 4
            }
            
            alerts.sort(key=lambda x: status_order[x.status])
            
            logger.info(f"Generated {len(alerts)} inventory alerts")
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking inventory levels: {e}")
            return []
    
    async def _process_inventory_item(self, item: Dict[str, Any]) -> Optional[InventoryAlert]:
        """Process a single inventory item and determine if an alert is needed."""
        try:
            props = item.get('properties', {})
            
            # Extract item information
            item_name = self._extract_title(props, ['Name', 'Item', 'Part'])
            if not item_name:
                return None
            
            # Extract stock levels
            current_stock = self._extract_number(props, ['Stock', 'Quantity', 'Current Stock', 'Qty'])
            minimum_stock = self._extract_number(props, ['Minimum Stock', 'Min Qty', 'Reorder Point'])
            
            if current_stock is None:
                return None
            
            # Use default minimum if not specified
            if minimum_stock is None:
                minimum_stock = self.low_stock_threshold
            
            # Determine status
            if current_stock == 0:
                status = InventoryStatus.OUT_OF_STOCK
            elif current_stock <= minimum_stock:
                status = InventoryStatus.LOW_STOCK
            elif current_stock <= minimum_stock * self.reorder_point_multiplier:
                status = InventoryStatus.REORDER_POINT
            else:
                status = InventoryStatus.ADEQUATE
            
            # Only create alerts for items that need attention
            if status in [InventoryStatus.ADEQUATE, InventoryStatus.OVERSTOCKED]:
                return None
            
            # Extract additional information
            reorder_quantity = self._extract_number(props, ['Reorder Qty', 'Order Quantity', 'Reorder Amount'])
            estimated_cost = self._extract_number(props, ['Cost', 'Price', 'Unit Cost'])
            preferred_supplier = self._extract_select(props, ['Supplier', 'Vendor', 'Source'])
            
            # Calculate suggested reorder quantity if not specified
            if reorder_quantity is None:
                reorder_quantity = max(minimum_stock * 2, 5)
            
            return InventoryAlert(
                item_name=item_name,
                current_stock=int(current_stock),
                minimum_stock=int(minimum_stock),
                reorder_quantity=int(reorder_quantity),
                status=status,
                estimated_cost=estimated_cost or 0.0,
                preferred_supplier=preferred_supplier or "Unknown",
                page_id=item['id']
            )
            
        except Exception as e:
            logger.error(f"Error processing inventory item: {e}")
            return None
    
    async def prepare_for_upcoming_events(self) -> List[EventPreparation]:
        """Generate preparation checklists for upcoming RC events."""
        logger.info("🏁 Preparing for upcoming RC events...")
        
        preparations = []
        
        try:
            # Get upcoming events (next 30 days)
# NOTION_REMOVED:             event_items = await self.notion.query_database(
                self.event_records_db_id,
                page_size=50
            )
            
            today = datetime.now()
            cutoff_date = today + timedelta(days=30)
            
            for event in event_items:
                preparation = await self._process_event_preparation(event, today, cutoff_date)
                if preparation:
                    preparations.append(preparation)
            
            # Sort by event date
            preparations.sort(key=lambda x: x.event_date)
            
            logger.info(f"Generated {len(preparations)} event preparations")
            return preparations
            
        except Exception as e:
            logger.error(f"Error preparing for events: {e}")
            return []
    
    async def _process_event_preparation(self, event: Dict[str, Any], today: datetime, cutoff_date: datetime) -> Optional[EventPreparation]:
        """Process an event and generate preparation checklist."""
        try:
            props = event.get('properties', {})
            
            # Extract event information
            event_name = self._extract_title(props, ['Name', 'Event', 'Competition'])
            event_date = self._extract_date(props, ['Date', 'Event Date', 'Competition Date'])
            
            if not event_name or not event_date:
                return None
            
            # Only process upcoming events
            if event_date < today or event_date > cutoff_date:
                return None
            
            # Extract event details
            vehicles_needed = self._extract_multi_select(props, ['Vehicles', 'Cars', 'RC Vehicles'])
            equipment_list = self._extract_multi_select(props, ['Equipment', 'Gear', 'Required Equipment'])
            
            # Get maintenance requirements for vehicles
            maintenance_required = await self._check_vehicle_maintenance(vehicles_needed or [], event_date)
            
            # Generate inventory checklist
            inventory_needed = await self._generate_event_inventory_checklist(event_name, vehicles_needed or [])
            
            # Determine preparation status
            days_until_event = (event_date - today).days
            if days_until_event <= 3:
                prep_status = "Urgent - Event Soon"
            elif days_until_event <= 7:
                prep_status = "Active Preparation"
            else:
                prep_status = "Early Planning"
            
            return EventPreparation(
                event_name=event_name,
                event_date=event_date,
                vehicles_needed=vehicles_needed or [],
                equipment_checklist=equipment_list or [],
                maintenance_required=maintenance_required,
                inventory_needed=inventory_needed,
                preparation_status=prep_status,
                page_id=event['id']
            )
            
        except Exception as e:
            logger.error(f"Error processing event preparation: {e}")
            return None
    
    async def _check_vehicle_maintenance(self, vehicles: List[str], event_date: datetime) -> List[MaintenanceAlert]:
        """Check if vehicles need maintenance before an event."""
        maintenance_alerts = []
        
        try:
            # Get maintenance items for specified vehicles
            for vehicle in vehicles:
# NOTION_REMOVED:                 vehicle_maintenance = await self.notion.query_database(
                    self.maintenance_schedule_db_id,
                    filter_conditions={
                        "property": "Vehicle",
                        "title": {"contains": vehicle}
                    },
                    page_size=20
                )
                
                for item in vehicle_maintenance:
                    alert = await self._process_maintenance_item(item, event_date)
                    if alert and alert.due_date <= event_date:
                        maintenance_alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error checking vehicle maintenance: {e}")
        
        return maintenance_alerts
    
    async def _generate_event_inventory_checklist(self, event_name: str, vehicles: List[str]) -> List[str]:
        """Generate inventory checklist for an event."""
        checklist = []
        
        # Standard RC event items
        standard_items = [
            "Batteries (charged)",
            "Charger and cables",
            "Spare tires",
            "Tools (screwdrivers, hex keys)",
            "Spare parts",
            "Cleaning supplies",
            "Setup tools",
            "Radio batteries"
        ]
        
        checklist.extend(standard_items)
        
        # Vehicle-specific items
        for vehicle in vehicles:
            checklist.extend([
                f"{vehicle} - Pre-race inspection",
                f"{vehicle} - Backup motor/ESC",
                f"{vehicle} - Vehicle-specific spare parts"
            ])
        
        return checklist
    
    async def generate_maintenance_summary(self) -> Dict[str, Any]:
        """Generate comprehensive maintenance and inventory summary."""
        logger.info("📊 Generating RC maintenance summary...")
        
        try:
            # Get all alerts
            maintenance_alerts = await self.check_maintenance_schedule()
            inventory_alerts = await self.check_inventory_levels()
            event_preparations = await self.prepare_for_upcoming_events()
            
            # Calculate summary statistics
            overdue_maintenance = len([a for a in maintenance_alerts if a.urgency == MaintenanceUrgency.OVERDUE])
            critical_inventory = len([a for a in inventory_alerts if a.status == InventoryStatus.OUT_OF_STOCK])
            upcoming_events = len(event_preparations)
            
            summary = {
                "timestamp": datetime.now().isoformat(),
                "maintenance": {
                    "total_alerts": len(maintenance_alerts),
                    "overdue_items": overdue_maintenance,
                    "this_week": len([a for a in maintenance_alerts if a.urgency == MaintenanceUrgency.DUE_THIS_WEEK]),
                    "alerts": [self._alert_to_dict(alert) for alert in maintenance_alerts[:10]]  # Top 10
                },
                "inventory": {
                    "total_alerts": len(inventory_alerts),
                    "out_of_stock": critical_inventory,
                    "low_stock": len([a for a in inventory_alerts if a.status == InventoryStatus.LOW_STOCK]),
                    "estimated_reorder_cost": sum(a.estimated_cost * a.reorder_quantity for a in inventory_alerts),
                    "alerts": [self._inventory_to_dict(alert) for alert in inventory_alerts[:10]]  # Top 10
                },
                "events": {
                    "upcoming_count": upcoming_events,
                    "next_event": event_preparations[0].event_name if event_preparations else None,
                    "next_event_date": event_preparations[0].event_date.isoformat() if event_preparations else None,
                    "preparations": [self._event_to_dict(prep) for prep in event_preparations[:5]]  # Next 5
                },
                "overall_status": self._calculate_overall_status(overdue_maintenance, critical_inventory, upcoming_events),
                "recommendations": self._generate_recommendations(maintenance_alerts, inventory_alerts, event_preparations)
            }
            
            # Log summary to Lifelog
            await self._log_maintenance_summary(summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating maintenance summary: {e}")
            return {}
    
    def _calculate_overall_status(self, overdue_maintenance: int, critical_inventory: int, upcoming_events: int) -> str:
        """Calculate overall RC maintenance status."""
        if overdue_maintenance > 0 or critical_inventory > 0:
            return "Critical - Immediate Attention Required"
        elif upcoming_events > 0:
            return "Active - Event Preparation Needed"
        else:
            return "Good - Routine Monitoring"
    
    def _generate_recommendations(self, maintenance_alerts: List[MaintenanceAlert], 
                                inventory_alerts: List[InventoryAlert], 
                                event_preparations: List[EventPreparation]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Maintenance recommendations
        overdue = [a for a in maintenance_alerts if a.urgency == MaintenanceUrgency.OVERDUE]
        if overdue:
            recommendations.append(f"URGENT: Complete {len(overdue)} overdue maintenance tasks immediately")
        
        due_this_week = [a for a in maintenance_alerts if a.urgency == MaintenanceUrgency.DUE_THIS_WEEK]
        if due_this_week:
            recommendations.append(f"Schedule {len(due_this_week)} maintenance tasks for this week")
        
        # Inventory recommendations
        out_of_stock = [a for a in inventory_alerts if a.status == InventoryStatus.OUT_OF_STOCK]
        if out_of_stock:
            recommendations.append(f"ORDER IMMEDIATELY: {len(out_of_stock)} items are out of stock")
        
        low_stock = [a for a in inventory_alerts if a.status == InventoryStatus.LOW_STOCK]
        if low_stock:
            recommendations.append(f"Reorder {len(low_stock)} low stock items soon")
        
        # Event recommendations
        urgent_events = [e for e in event_preparations if e.preparation_status == "Urgent - Event Soon"]
        if urgent_events:
            recommendations.append(f"URGENT: Finalize preparation for {len(urgent_events)} upcoming events")
        
        return recommendations[:5]  # Top 5 recommendations
    
    async def _log_maintenance_summary(self, summary: Dict[str, Any]) -> None:
        """Log maintenance summary to Lifelog database."""
        try:
            if not self.lifelog_db_id:
                return
            
            log_entry = {
                "Name": {
                    "title": [{"text": {"content": f"RC Maintenance Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]
                },
                "Type": {
                    "select": {"name": "RC Maintenance"}
                },
                "Status": {
                    "select": {"name": summary['overall_status'].split(' - ')[0]}
                },
                "Details": {
                    "rich_text": [{"text": {"content": json.dumps(summary, indent=2)}}]
                }
            }
            
            await self.notion.create_database_page(self.lifelog_db_id, log_entry)
            
        except Exception as e:
            logger.error(f"Error logging maintenance summary: {e}")
    
    # Utility methods for extracting data from Notion properties
    def _extract_title(self, props: Dict[str, Any], possible_keys: List[str]) -> Optional[str]:
        """Extract title text from properties."""
        for key in possible_keys:
            if key in props and props[key].get('title'):
                return props[key]['title'][0]['text']['content']
        return None
    
    def _extract_date(self, props: Dict[str, Any], possible_keys: List[str]) -> Optional[datetime]:
        """Extract date from properties."""
        for key in possible_keys:
            if key in props and props[key].get('date') and props[key]['date'].get('start'):
                try:
                    return datetime.fromisoformat(props[key]['date']['start'].replace('Z', '+00:00'))
                except:
                    pass
        return None
    
    def _extract_number(self, props: Dict[str, Any], possible_keys: List[str]) -> Optional[float]:
        """Extract number from properties."""
        for key in possible_keys:
            if key in props and props[key].get('number') is not None:
                return props[key]['number']
        return None
    
    def _extract_select(self, props: Dict[str, Any], possible_keys: List[str]) -> Optional[str]:
        """Extract select value from properties."""
        for key in possible_keys:
            if key in props and props[key].get('select') and props[key]['select'].get('name'):
                return props[key]['select']['name']
        return None
    
    def _extract_multi_select(self, props: Dict[str, Any], possible_keys: List[str]) -> Optional[List[str]]:
        """Extract multi-select values from properties."""
        for key in possible_keys:
            if key in props and props[key].get('multi_select'):
                return [item['name'] for item in props[key]['multi_select']]
        return None
    
    def _alert_to_dict(self, alert: MaintenanceAlert) -> Dict[str, Any]:
        """Convert maintenance alert to dictionary."""
        return {
            "item_name": alert.item_name,
            "urgency": alert.urgency.value,
            "due_date": alert.due_date.isoformat() if alert.due_date else None,
            "maintenance_type": alert.maintenance_type,
            "estimated_hours": alert.estimated_hours,
            "parts_needed": alert.parts_needed
        }
    
    def _inventory_to_dict(self, alert: InventoryAlert) -> Dict[str, Any]:
        """Convert inventory alert to dictionary."""
        return {
            "item_name": alert.item_name,
            "current_stock": alert.current_stock,
            "minimum_stock": alert.minimum_stock,
            "status": alert.status.value,
            "reorder_quantity": alert.reorder_quantity,
            "estimated_cost": alert.estimated_cost
        }
    
    def _event_to_dict(self, prep: EventPreparation) -> Dict[str, Any]:
        """Convert event preparation to dictionary."""
        return {
            "event_name": prep.event_name,
            "event_date": prep.event_date.isoformat(),
            "vehicles_needed": prep.vehicles_needed,
            "preparation_status": prep.preparation_status,
            "maintenance_items": len(prep.maintenance_required),
            "checklist_items": len(prep.inventory_needed)
        }


async def main():
    """Test the RC maintenance scheduler."""
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    
        return
    
    
    print("🏎️ RC MAINTENANCE SCHEDULER TEST")
    print("=" * 50)
    
    # Generate comprehensive summary
    summary = await scheduler.generate_maintenance_summary()
    
    if summary:
        print(f"✅ Overall Status: {summary['overall_status']}")
        print(f"📋 Maintenance Alerts: {summary['maintenance']['total_alerts']}")
        print(f"📦 Inventory Alerts: {summary['inventory']['total_alerts']}")
        print(f"🏁 Upcoming Events: {summary['events']['upcoming_count']}")
        
        if summary['recommendations']:
            print("\n🔧 Top Recommendations:")
            for i, rec in enumerate(summary['recommendations'], 1):
                print(f"   {i}. {rec}")
    else:
        print("❌ Failed to generate maintenance summary")


if __name__ == "__main__":
    asyncio.run(main())