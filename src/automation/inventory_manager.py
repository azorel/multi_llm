#!/usr/bin/env python3
"""
Inventory Manager - Automated Household & RC Inventory Monitoring
================================================================

This module provides comprehensive inventory management for the Home Garage database
and other household inventory systems. It integrates with the discovered LifeOS 
Notion workspace to provide:

- Automated stock level monitoring with smart alerts
- Predictive reordering based on usage patterns
- Cost optimization and budget integration
- Automated shopping list generation
- Supplier and price tracking
- Consumption analytics and trend analysis

Based on comprehensive Notion workspace discovery:
- Home Garage (13 props) - Primary inventory database
- Things Bought (7 props) - Purchase history tracking  
- Food Onhand (4 props) - Kitchen inventory
- Spending Log (9 props) - Financial integration
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import statistics
from loguru import logger

# import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from integrations.notion_mcp_client 

class InventoryStatus(Enum):
    CRITICAL = "critical"           # Out of stock or emergency low
    LOW = "low"                    # Below minimum threshold
    REORDER = "reorder"            # Hit reorder point
    ADEQUATE = "adequate"          # Normal stock levels
    OVERSTOCKED = "overstocked"    # Above maximum recommended
    UNKNOWN = "unknown"            # Cannot determine status


class AlertPriority(Enum):
    EMERGENCY = "emergency"        # Immediate action required
    HIGH = "high"                 # Action needed this week
    MEDIUM = "medium"             # Action needed soon
    LOW = "low"                   # Monitor only
    INFO = "info"                 # Informational


class ConsumptionTrend(Enum):
    INCREASING = "increasing"      # Usage going up
    STABLE = "stable"             # Consistent usage
    DECREASING = "decreasing"      # Usage going down
    SEASONAL = "seasonal"          # Seasonal patterns detected
    UNPREDICTABLE = "unpredictable" # No clear pattern


@dataclass
class InventoryItem:
    """Represents an inventory item with all relevant data."""
    name: str
    category: str
    current_stock: float
    minimum_stock: float
    maximum_stock: Optional[float]
    reorder_point: float
    reorder_quantity: float
    unit_cost: float
    supplier: str
    last_updated: datetime
    location: str
    status: InventoryStatus
    page_id: str


@dataclass
class InventoryAlert:
    """Represents an inventory alert requiring action."""
    item: InventoryItem
    priority: AlertPriority
    message: str
    recommended_action: str
    estimated_cost: float
    days_until_stockout: Optional[int]
    consumption_rate: Optional[float]


@dataclass
class ShoppingListItem:
    """Represents an item for the shopping list."""
    name: str
    category: str
    quantity: float
    unit: str
    estimated_cost: float
    supplier: str
    priority: AlertPriority
    reason: str


@dataclass
class ConsumptionAnalysis:
    """Analysis of consumption patterns for an item."""
    item_name: str
    daily_usage_rate: float
    weekly_usage_rate: float
    trend: ConsumptionTrend
    confidence: float
    predicted_stockout_date: Optional[datetime]
    recommended_reorder_point: float
    recommended_reorder_quantity: float


class InventoryManager:
    """
    Comprehensive inventory management system for LifeOS.
    
    Provides intelligent monitoring, alerts, and optimization for all household
    and RC inventory across multiple Notion databases.
    """
    
        """Initialize the inventory manager."""
        
        # Database IDs from LifeOS discovery
# NOTION_REMOVED:         self.home_garage_db_id = os.getenv('NOTION_HOME_GARAGE_DB_ID')
# NOTION_REMOVED:         self.things_bought_db_id = os.getenv('NOTION_THINGS_BOUGHT_DB_ID')
# NOTION_REMOVED:         self.food_onhand_db_id = os.getenv('NOTION_FOOD_ONHAND_DB_ID')
# NOTION_REMOVED:         self.spending_log_db_id = os.getenv('NOTION_SPENDING_LOG_DB_ID')
# NOTION_REMOVED:         self.lifelog_db_id = os.getenv('NOTION_LIFELOG_DB_ID')
        
        # Configuration
        self.critical_threshold = 0.1    # 10% of minimum stock
        self.low_threshold = 1.0         # At minimum stock
        self.reorder_multiplier = 1.5    # 150% of minimum = reorder point
        self.overstock_multiplier = 3.0  # 300% of minimum = overstocked
        self.analysis_days = 90          # Days to analyze for trends
        
    async def monitor_all_inventory(self) -> Dict[str, Any]:
        """Monitor all inventory across all databases and generate comprehensive report."""
        logger.info("📦 Starting comprehensive inventory monitoring...")
        
        try:
            # Get inventory from all sources
            home_garage_items = await self._get_home_garage_inventory()
            food_items = await self._get_food_inventory()
            
            # Combine all inventory
            all_items = home_garage_items + food_items
            
            # Generate alerts
            alerts = await self._generate_inventory_alerts(all_items)
            
            # Analyze consumption patterns
            consumption_analysis = await self._analyze_consumption_patterns(all_items)
            
            # Generate shopping list
            shopping_list = await self._generate_shopping_list(alerts, consumption_analysis)
            
            # Calculate financial impact
            financial_impact = self._calculate_financial_impact(alerts, shopping_list)
            
            # Generate comprehensive report
            report = {
                "timestamp": datetime.now().isoformat(),
                "inventory_summary": {
                    "total_items": len(all_items),
                    "critical_items": len([a for a in alerts if a.priority == AlertPriority.EMERGENCY]),
                    "low_stock_items": len([a for a in alerts if a.priority == AlertPriority.HIGH]),
                    "reorder_needed": len([a for a in alerts if a.priority in [AlertPriority.EMERGENCY, AlertPriority.HIGH]]),
                    "total_value": sum(item.current_stock * item.unit_cost for item in all_items),
                    "categories": self._analyze_categories(all_items)
                },
                "alerts": {
                    "critical": [self._alert_to_dict(a) for a in alerts if a.priority == AlertPriority.EMERGENCY],
                    "high_priority": [self._alert_to_dict(a) for a in alerts if a.priority == AlertPriority.HIGH],
                    "medium_priority": [self._alert_to_dict(a) for a in alerts if a.priority == AlertPriority.MEDIUM][:5],
                    "total_alerts": len(alerts)
                },
                "shopping_list": {
                    "urgent_items": [self._shopping_item_to_dict(item) for item in shopping_list if item.priority == AlertPriority.EMERGENCY],
                    "high_priority_items": [self._shopping_item_to_dict(item) for item in shopping_list if item.priority == AlertPriority.HIGH],
                    "total_items": len(shopping_list),
                    "estimated_cost": sum(item.estimated_cost for item in shopping_list)
                },
                "consumption_analysis": {
                    "items_analyzed": len(consumption_analysis),
                    "increasing_consumption": len([a for a in consumption_analysis if a.trend == ConsumptionTrend.INCREASING]),
                    "stable_consumption": len([a for a in consumption_analysis if a.trend == ConsumptionTrend.STABLE]),
                    "decreasing_consumption": len([a for a in consumption_analysis if a.trend == ConsumptionTrend.DECREASING]),
                    "top_consumed": sorted(consumption_analysis, key=lambda x: x.daily_usage_rate, reverse=True)[:5]
                },
                "financial_impact": financial_impact,
                "recommendations": self._generate_recommendations(alerts, consumption_analysis, financial_impact)
            }
            
            # Log to Lifelog database
            await self._log_inventory_report(report)
            
            logger.info(f"Generated inventory report with {len(alerts)} alerts and {len(shopping_list)} shopping items")
            return report
            
        except Exception as e:
            logger.error(f"Error monitoring inventory: {e}")
            return {}
    
    async def _get_home_garage_inventory(self) -> List[InventoryItem]:
        """Get inventory items from Home Garage database."""
        logger.info("🔧 Analyzing Home Garage inventory...")
        
        items = []
        
        try:
# NOTION_REMOVED:             garage_items = await self.notion.query_database(
                self.home_garage_db_id,
                page_size=100
            )
            
            for item_data in garage_items:
                item = await self._parse_garage_item(item_data)
                if item:
                    items.append(item)
            
            logger.info(f"Found {len(items)} items in Home Garage")
            return items
            
        except Exception as e:
            logger.error(f"Error getting home garage inventory: {e}")
            return []
    
    async def _get_food_inventory(self) -> List[InventoryItem]:
        """Get inventory items from Food Onhand database."""
        logger.info("🍽️ Analyzing food inventory...")
        
        items = []
        
        try:
# NOTION_REMOVED:             food_items = await self.notion.query_database(
                self.food_onhand_db_id,
                page_size=100
            )
            
            for item_data in food_items:
                item = await self._parse_food_item(item_data)
                if item:
                    items.append(item)
            
            logger.info(f"Found {len(items)} food items")
            return items
            
        except Exception as e:
            logger.error(f"Error getting food inventory: {e}")
            return []
    
    async def _parse_garage_item(self, item_data: Dict[str, Any]) -> Optional[InventoryItem]:
        """Parse a Home Garage item into InventoryItem."""
        try:
            props = item_data.get('properties', {})
            
            # Extract required fields
            name = self._extract_title(props, ['Name', 'Item', 'Part'])
            if not name:
                return None
            
            current_stock = self._extract_number(props, ['Stock', 'Quantity', 'Current Stock', 'Qty'])
            if current_stock is None:
                current_stock = 0
            
            # Extract optional fields with defaults
            category = self._extract_select(props, ['Category', 'Type', 'Classification']) or "General"
            minimum_stock = self._extract_number(props, ['Minimum Stock', 'Min Qty', 'Min']) or 1
            maximum_stock = self._extract_number(props, ['Maximum Stock', 'Max Qty', 'Max'])
            unit_cost = self._extract_number(props, ['Cost', 'Price', 'Unit Cost']) or 0
            supplier = self._extract_select(props, ['Supplier', 'Vendor', 'Source']) or "Unknown"
            location = self._extract_select(props, ['Location', 'Storage', 'Shelf']) or "Garage"
            
            # Calculate derived values
            reorder_point = minimum_stock * self.reorder_multiplier
            reorder_quantity = minimum_stock * 2  # Default reorder quantity
            
            # Determine status
            status = self._determine_status(current_stock, minimum_stock, maximum_stock)
            
            return InventoryItem(
                name=name,
                category=category,
                current_stock=current_stock,
                minimum_stock=minimum_stock,
                maximum_stock=maximum_stock,
                reorder_point=reorder_point,
                reorder_quantity=reorder_quantity,
                unit_cost=unit_cost,
                supplier=supplier,
                last_updated=datetime.now(),
                location=location,
                status=status,
                page_id=item_data['id']
            )
            
        except Exception as e:
            logger.error(f"Error parsing garage item: {e}")
            return None
    
    async def _parse_food_item(self, item_data: Dict[str, Any]) -> Optional[InventoryItem]:
        """Parse a Food Onhand item into InventoryItem."""
        try:
            props = item_data.get('properties', {})
            
            # Extract required fields
            name = self._extract_title(props, ['Name', 'Food', 'Item'])
            if not name:
                return None
            
            current_stock = self._extract_number(props, ['Quantity', 'Amount', 'Stock']) or 0
            
            # Food-specific defaults
            category = "Food"
            minimum_stock = 1  # Default minimum for food items
            maximum_stock = None
            unit_cost = self._extract_number(props, ['Cost', 'Price']) or 0
            supplier = "Grocery Store"
            location = "Kitchen"
            
            # Calculate derived values
            reorder_point = minimum_stock * self.reorder_multiplier
            reorder_quantity = minimum_stock * 2
            
            # Determine status
            status = self._determine_status(current_stock, minimum_stock, maximum_stock)
            
            return InventoryItem(
                name=name,
                category=category,
                current_stock=current_stock,
                minimum_stock=minimum_stock,
                maximum_stock=maximum_stock,
                reorder_point=reorder_point,
                reorder_quantity=reorder_quantity,
                unit_cost=unit_cost,
                supplier=supplier,
                last_updated=datetime.now(),
                location=location,
                status=status,
                page_id=item_data['id']
            )
            
        except Exception as e:
            logger.error(f"Error parsing food item: {e}")
            return None
    
    def _determine_status(self, current: float, minimum: float, maximum: Optional[float]) -> InventoryStatus:
        """Determine inventory status based on stock levels."""
        if current <= 0:
            return InventoryStatus.CRITICAL
        elif current <= minimum * self.critical_threshold:
            return InventoryStatus.CRITICAL
        elif current <= minimum:
            return InventoryStatus.LOW
        elif current <= minimum * self.reorder_multiplier:
            return InventoryStatus.REORDER
        elif maximum and current >= maximum:
            return InventoryStatus.OVERSTOCKED
        elif current >= minimum * self.overstock_multiplier:
            return InventoryStatus.OVERSTOCKED
        else:
            return InventoryStatus.ADEQUATE
    
    async def _generate_inventory_alerts(self, items: List[InventoryItem]) -> List[InventoryAlert]:
        """Generate alerts for inventory items that need attention."""
        alerts = []
        
        for item in items:
            if item.status in [InventoryStatus.CRITICAL, InventoryStatus.LOW, InventoryStatus.REORDER]:
                alert = self._create_alert(item)
                if alert:
                    alerts.append(alert)
        
        # Sort by priority
        priority_order = {
            AlertPriority.EMERGENCY: 0,
            AlertPriority.HIGH: 1,
            AlertPriority.MEDIUM: 2,
            AlertPriority.LOW: 3,
            AlertPriority.INFO: 4
        }
        
        alerts.sort(key=lambda x: priority_order[x.priority])
        return alerts
    
    def _create_alert(self, item: InventoryItem) -> Optional[InventoryAlert]:
        """Create an alert for an inventory item."""
        try:
            # Determine priority and message based on status
            if item.status == InventoryStatus.CRITICAL:
                priority = AlertPriority.EMERGENCY
                message = f"CRITICAL: {item.name} is out of stock or critically low ({item.current_stock} remaining)"
                action = f"ORDER IMMEDIATELY: {item.reorder_quantity} units"
            elif item.status == InventoryStatus.LOW:
                priority = AlertPriority.HIGH
                message = f"LOW STOCK: {item.name} is below minimum threshold ({item.current_stock}/{item.minimum_stock})"
                action = f"Reorder soon: {item.reorder_quantity} units"
            elif item.status == InventoryStatus.REORDER:
                priority = AlertPriority.MEDIUM
                message = f"REORDER POINT: {item.name} has reached reorder point ({item.current_stock} remaining)"
                action = f"Schedule reorder: {item.reorder_quantity} units"
            else:
                return None
            
            # Calculate financial impact
            estimated_cost = item.reorder_quantity * item.unit_cost
            
            # Estimate days until stockout (simplified)
            days_until_stockout = None
            consumption_rate = None
            if item.current_stock > 0:
                # Simple estimate: assume 30-day consumption cycle
                estimated_monthly_usage = max(item.minimum_stock, 1)
                daily_usage = estimated_monthly_usage / 30
                if daily_usage > 0:
                    days_until_stockout = int(item.current_stock / daily_usage)
                    consumption_rate = daily_usage
            
            return InventoryAlert(
                item=item,
                priority=priority,
                message=message,
                recommended_action=action,
                estimated_cost=estimated_cost,
                days_until_stockout=days_until_stockout,
                consumption_rate=consumption_rate
            )
            
        except Exception as e:
            logger.error(f"Error creating alert for {item.name}: {e}")
            return None
    
    async def _analyze_consumption_patterns(self, items: List[InventoryItem]) -> List[ConsumptionAnalysis]:
        """Analyze consumption patterns for inventory optimization."""
        logger.info("📊 Analyzing consumption patterns...")
        
        # This is a simplified analysis - in a full implementation,
        # you would analyze historical purchase and usage data
        analyses = []
        
        for item in items:
            try:
                # Simple consumption analysis based on current stock vs minimum
                if item.minimum_stock > 0:
                    usage_ratio = item.current_stock / item.minimum_stock
                    
                    # Estimate daily usage (simplified)
                    estimated_monthly_usage = item.minimum_stock
                    daily_usage = estimated_monthly_usage / 30
                    weekly_usage = daily_usage * 7
                    
                    # Determine trend (simplified - would need historical data)
                    if usage_ratio < 0.5:
                        trend = ConsumptionTrend.INCREASING
                        confidence = 0.6
                    elif usage_ratio > 2.0:
                        trend = ConsumptionTrend.DECREASING
                        confidence = 0.6
                    else:
                        trend = ConsumptionTrend.STABLE
                        confidence = 0.8
                    
                    # Predict stockout date
                    stockout_date = None
                    if daily_usage > 0:
                        days_remaining = item.current_stock / daily_usage
                        stockout_date = datetime.now() + timedelta(days=days_remaining)
                    
                    # Recommend optimized reorder point and quantity
                    recommended_reorder_point = daily_usage * 14  # 2-week buffer
                    recommended_reorder_quantity = daily_usage * 30  # 1-month supply
                    
                    analysis = ConsumptionAnalysis(
                        item_name=item.name,
                        daily_usage_rate=daily_usage,
                        weekly_usage_rate=weekly_usage,
                        trend=trend,
                        confidence=confidence,
                        predicted_stockout_date=stockout_date,
                        recommended_reorder_point=recommended_reorder_point,
                        recommended_reorder_quantity=recommended_reorder_quantity
                    )
                    
                    analyses.append(analysis)
                
            except Exception as e:
                logger.error(f"Error analyzing consumption for {item.name}: {e}")
        
        logger.info(f"Analyzed consumption patterns for {len(analyses)} items")
        return analyses
    
    async def _generate_shopping_list(self, alerts: List[InventoryAlert], analyses: List[ConsumptionAnalysis]) -> List[ShoppingListItem]:
        """Generate optimized shopping list based on alerts and consumption analysis."""
        shopping_items = []
        
        for alert in alerts:
            if alert.priority in [AlertPriority.EMERGENCY, AlertPriority.HIGH, AlertPriority.MEDIUM]:
                # Find consumption analysis for this item
                analysis = next((a for a in analyses if a.item_name == alert.item.name), None)
                
                # Use analysis to optimize quantity if available
                quantity = alert.item.reorder_quantity
                if analysis and analysis.recommended_reorder_quantity > 0:
                    quantity = analysis.recommended_reorder_quantity
                
                shopping_item = ShoppingListItem(
                    name=alert.item.name,
                    category=alert.item.category,
                    quantity=quantity,
                    unit="units",  # Would be more specific in real implementation
                    estimated_cost=quantity * alert.item.unit_cost,
                    supplier=alert.item.supplier,
                    priority=alert.priority,
                    reason=alert.message
                )
                
                shopping_items.append(shopping_item)
        
        return shopping_items
    
    def _calculate_financial_impact(self, alerts: List[InventoryAlert], shopping_list: List[ShoppingListItem]) -> Dict[str, Any]:
        """Calculate financial impact of inventory needs."""
        immediate_cost = sum(item.estimated_cost for item in shopping_list if item.priority == AlertPriority.EMERGENCY)
        urgent_cost = sum(item.estimated_cost for item in shopping_list if item.priority == AlertPriority.HIGH)
        total_cost = sum(item.estimated_cost for item in shopping_list)
        
        # Calculate potential savings from consumption optimization
        potential_savings = 0
        for alert in alerts:
            if alert.item.status == InventoryStatus.OVERSTOCKED:
                excess = alert.item.current_stock - alert.item.minimum_stock * 2
                if excess > 0:
                    potential_savings += excess * alert.item.unit_cost
        
        return {
            "immediate_purchases_needed": immediate_cost,
            "urgent_purchases_needed": urgent_cost,
            "total_shopping_cost": total_cost,
            "potential_savings": potential_savings,
            "number_of_suppliers": len(set(item.supplier for item in shopping_list)),
            "categories_affected": len(set(item.category for item in shopping_list))
        }
    
    def _analyze_categories(self, items: List[InventoryItem]) -> Dict[str, Any]:
        """Analyze inventory by categories."""
        categories = {}
        
        for item in items:
            if item.category not in categories:
                categories[item.category] = {
                    "total_items": 0,
                    "total_value": 0,
                    "critical_items": 0,
                    "low_items": 0,
                    "adequate_items": 0
                }
            
            cat = categories[item.category]
            cat["total_items"] += 1
            cat["total_value"] += item.current_stock * item.unit_cost
            
            if item.status == InventoryStatus.CRITICAL:
                cat["critical_items"] += 1
            elif item.status == InventoryStatus.LOW:
                cat["low_items"] += 1
            elif item.status == InventoryStatus.ADEQUATE:
                cat["adequate_items"] += 1
        
        return categories
    
    def _generate_recommendations(self, alerts: List[InventoryAlert], analyses: List[ConsumptionAnalysis], financial: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Critical items
        critical_alerts = [a for a in alerts if a.priority == AlertPriority.EMERGENCY]
        if critical_alerts:
            recommendations.append(f"🚨 URGENT: {len(critical_alerts)} items are critically low - order immediately")
        
        # High priority items
        high_alerts = [a for a in alerts if a.priority == AlertPriority.HIGH]
        if high_alerts:
            recommendations.append(f"⚠️ HIGH: {len(high_alerts)} items need reordering this week")
        
        # Financial optimization
        if financial["immediate_purchases_needed"] > 100:
            recommendations.append(f"💰 Budget impact: ${financial['immediate_purchases_needed']:.2f} needed for immediate purchases")
        
        # Consumption trends
        increasing_items = [a for a in analyses if a.trend == ConsumptionTrend.INCREASING]
        if increasing_items:
            recommendations.append(f"📈 {len(increasing_items)} items showing increased consumption - consider adjusting reorder points")
        
        # Supplier optimization
        if financial["number_of_suppliers"] > 3:
            recommendations.append("🏪 Consider consolidating orders from multiple suppliers to reduce costs")
        
        return recommendations[:5]
    
    async def _log_inventory_report(self, report: Dict[str, Any]) -> None:
        """Log inventory report to Lifelog database."""
        try:
            if not self.lifelog_db_id:
                return
            
            summary = f"Inventory Summary: {report['inventory_summary']['total_items']} items tracked, " \
                     f"{report['alerts']['total_alerts']} alerts, " \
                     f"${report['financial_impact']['total_shopping_cost']:.2f} shopping needed"
            
            log_entry = {
                "Name": {
                    "title": [{"text": {"content": f"Inventory Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]
                },
                "Type": {
                    "select": {"name": "Inventory Management"}
                },
                "Status": {
                    "select": {"name": "Completed"}
                },
                "Details": {
                    "rich_text": [{"text": {"content": summary}}]
                }
            }
            
            await self.notion.create_database_page(self.lifelog_db_id, log_entry)
            
        except Exception as e:
            logger.error(f"Error logging inventory report: {e}")
    
    # Utility methods for data extraction
    def _extract_title(self, props: Dict[str, Any], possible_keys: List[str]) -> Optional[str]:
        """Extract title text from properties."""
        for key in possible_keys:
            if key in props and props[key].get('title'):
                return props[key]['title'][0]['text']['content']
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
    
    def _alert_to_dict(self, alert: InventoryAlert) -> Dict[str, Any]:
        """Convert inventory alert to dictionary."""
        return {
            "item_name": alert.item.name,
            "category": alert.item.category,
            "current_stock": alert.item.current_stock,
            "minimum_stock": alert.item.minimum_stock,
            "priority": alert.priority.value,
            "message": alert.message,
            "recommended_action": alert.recommended_action,
            "estimated_cost": alert.estimated_cost,
            "days_until_stockout": alert.days_until_stockout,
            "supplier": alert.item.supplier
        }
    
    def _shopping_item_to_dict(self, item: ShoppingListItem) -> Dict[str, Any]:
        """Convert shopping list item to dictionary."""
        return {
            "name": item.name,
            "category": item.category,
            "quantity": item.quantity,
            "estimated_cost": item.estimated_cost,
            "supplier": item.supplier,
            "priority": item.priority.value,
            "reason": item.reason
        }


async def main():
    """Test the inventory manager."""
    from dotenv import load_dotenv
    
    load_dotenv()
    
        return
    
    
    print("📦 INVENTORY MANAGER TEST")
    print("=" * 50)
    
    # Generate comprehensive inventory report
    report = await inventory_manager.monitor_all_inventory()
    
    if report:
        print(f"✅ Total Items: {report['inventory_summary']['total_items']}")
        print(f"🚨 Critical Items: {report['inventory_summary']['critical_items']}")
        print(f"⚠️ Low Stock Items: {report['inventory_summary']['low_stock_items']}")
        print(f"🛒 Shopping List Items: {report['shopping_list']['total_items']}")
        print(f"💰 Shopping Cost: ${report['shopping_list']['estimated_cost']:.2f}")
        
        if report['recommendations']:
            print("\n🔧 Top Recommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"   {i}. {rec}")
    else:
        print("❌ Failed to generate inventory report")


if __name__ == "__main__":
    asyncio.run(main())