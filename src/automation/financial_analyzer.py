#!/usr/bin/env python3
"""
Financial Analyzer - Spending Pattern Analysis for LifeOS
Uses direct Notion API instead of MCP
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
from loguru import logger

# import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from integrations.notion_client 

@dataclass
class SpendingPattern:
    category: str
    total_spent: float
    transaction_count: int
    average_transaction: float
    trend: str  # increasing/stable/decreasing
    monthly_average: float


class FinancialAnalyzer:
    """Analyzes spending patterns from Notion financial databases."""
    
        
        # Database IDs
# NOTION_REMOVED:         self.spending_log_db_id = os.getenv('NOTION_SPENDING_LOG_DB_ID')
# NOTION_REMOVED:         self.income_db_id = os.getenv('NOTION_INCOME_DB_ID')
# NOTION_REMOVED:         self.expenses_db_id = os.getenv('NOTION_EXPENSES_DB_ID')
        
    async def analyze_spending_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Analyze spending patterns for the specified period."""
        logger.info(f"💰 Analyzing spending patterns for last {days} days...")
        
        try:
            # Get spending data
            spending_data = await self._get_spending_data(days)
            
            # Analyze by category
            category_analysis = self._analyze_by_category(spending_data)
            
            # Calculate trends
            trends = self._calculate_trends(spending_data)
            
            # Generate insights
            insights = self._generate_insights(category_analysis, trends)
            
            # Create summary
            summary = {
                "period": f"Last {days} days",
                "total_spent": sum(item.get('amount', 0) for item in spending_data),
                "transaction_count": len(spending_data),
                "daily_average": sum(item.get('amount', 0) for item in spending_data) / days,
                "top_categories": self._get_top_categories(category_analysis, 5),
                "trends": trends,
                "insights": insights,
                "recommendations": self._generate_recommendations(category_analysis, trends)
            }
            
            logger.info(f"Analysis complete: ${summary['total_spent']:.2f} spent in {summary['transaction_count']} transactions")
            return summary
            
        except Exception as e:
            logger.error(f"Error analyzing spending patterns: {e}")
            return {}
    
    async def _get_spending_data(self, days: int) -> List[Dict[str, Any]]:
        """Retrieve spending data from Notion."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        filter_params = {
            "filter": {
                "property": "Date",
                "date": {
                    "after": cutoff_date
                }
            },
            "sorts": [
                {
                    "property": "Date",
                    "direction": "descending"
                }
            ]
        }
        
# NOTION_REMOVED:         results = await self.notion.query_database(self.spending_log_db_id, **filter_params)
        
        # Parse results
        spending_data = []
        for page in results:
            props = page.get('properties', {})
            
            # Extract data
            amount = self._extract_number(props, 'Amount')
            category = self._extract_select(props, 'Category')
            date = self._extract_date(props, 'Date')
            description = self._extract_text(props, 'Description')
            
            if amount and date:
                spending_data.append({
                    'amount': amount,
                    'category': category or 'Uncategorized',
                    'date': date,
                    'description': description or ''
                })
        
        return spending_data
    
    def _analyze_by_category(self, spending_data: List[Dict[str, Any]]) -> Dict[str, SpendingPattern]:
        """Analyze spending by category."""
        categories = {}
        
        for item in spending_data:
            cat = item['category']
            if cat not in categories:
                categories[cat] = {
                    'total': 0,
                    'count': 0,
                    'amounts': []
                }
            
            categories[cat]['total'] += item['amount']
            categories[cat]['count'] += 1
            categories[cat]['amounts'].append(item['amount'])
        
        # Create SpendingPattern objects
        patterns = {}
        for cat, data in categories.items():
            patterns[cat] = SpendingPattern(
                category=cat,
                total_spent=data['total'],
                transaction_count=data['count'],
                average_transaction=data['total'] / data['count'],
                trend='stable',  # Will be calculated separately
                monthly_average=data['total'] * 30 / len(spending_data) if spending_data else 0
            )
        
        return patterns
    
    def _calculate_trends(self, spending_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Calculate spending trends."""
        # Simple trend calculation - compare first half vs second half
        if len(spending_data) < 4:
            return {"overall": "insufficient_data"}
        
        mid_point = len(spending_data) // 2
        first_half = sum(item['amount'] for item in spending_data[:mid_point])
        second_half = sum(item['amount'] for item in spending_data[mid_point:])
        
        if second_half > first_half * 1.1:
            trend = "increasing"
        elif second_half < first_half * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {"overall": trend, "confidence": "medium"}
    
    def _generate_insights(self, patterns: Dict[str, SpendingPattern], trends: Dict[str, str]) -> List[str]:
        """Generate actionable insights."""
        insights = []
        
        # Find highest spending category
        if patterns:
            top_cat = max(patterns.values(), key=lambda x: x.total_spent)
            insights.append(f"Highest spending in {top_cat.category}: ${top_cat.total_spent:.2f}")
        
        # Trend insight
        if trends.get('overall') == 'increasing':
            insights.append("⚠️ Spending is trending upward")
        elif trends.get('overall') == 'decreasing':
            insights.append("✅ Spending is trending downward")
        
        return insights[:5]
    
    def _generate_recommendations(self, patterns: Dict[str, SpendingPattern], trends: Dict[str, str]) -> List[str]:
        """Generate financial recommendations."""
        recs = []
        
        # High spending categories
        for cat, pattern in patterns.items():
            if pattern.monthly_average > 500:  # Threshold
                recs.append(f"Consider budgeting for {cat} (${pattern.monthly_average:.0f}/month)")
        
        # Trend-based recommendations
        if trends.get('overall') == 'increasing':
            recs.append("Review recent expenses to identify areas for reduction")
        
        return recs[:3]
    
    def _get_top_categories(self, patterns: Dict[str, SpendingPattern], limit: int) -> List[Dict[str, Any]]:
        """Get top spending categories."""
        sorted_patterns = sorted(patterns.values(), key=lambda x: x.total_spent, reverse=True)
        
        return [
            {
                "category": p.category,
                "total_spent": p.total_spent,
                "transaction_count": p.transaction_count,
                "average": p.average_transaction
            }
            for p in sorted_patterns[:limit]
        ]
    
    # Utility methods
    def _extract_number(self, props: Dict[str, Any], key: str) -> Optional[float]:
        """Extract number from Notion properties."""
        if key in props and props[key].get('number') is not None:
            return props[key]['number']
        return None
    
    def _extract_select(self, props: Dict[str, Any], key: str) -> Optional[str]:
        """Extract select value from Notion properties."""
        if key in props and props[key].get('select'):
            return props[key]['select'].get('name')
        return None
    
    def _extract_date(self, props: Dict[str, Any], key: str) -> Optional[str]:
        """Extract date from Notion properties."""
        if key in props and props[key].get('date'):
            return props[key]['date'].get('start')
        return None
    
    def _extract_text(self, props: Dict[str, Any], key: str) -> Optional[str]:
        """Extract text from Notion properties."""
        if key in props:
            if props[key].get('title'):
                return props[key]['title'][0]['text']['content'] if props[key]['title'] else None
            elif props[key].get('rich_text'):
                return props[key]['rich_text'][0]['text']['content'] if props[key]['rich_text'] else None
        return None


async def main():
    """Test the financial analyzer."""
    from dotenv import load_dotenv
    load_dotenv()
    
    if not token:
        return
    
    analyzer = FinancialAnalyzer(token)
    
    print("💰 FINANCIAL ANALYZER TEST")
    print("=" * 50)
    
    # Analyze last 30 days
    analysis = await analyzer.analyze_spending_patterns(30)
    
    if analysis:
        print(f"📊 Period: {analysis['period']}")
        print(f"💵 Total Spent: ${analysis['total_spent']:.2f}")
        print(f"📈 Daily Average: ${analysis['daily_average']:.2f}")
        print(f"🎯 Trend: {analysis['trends'].get('overall', 'unknown')}")
        
        if analysis['insights']:
            print("\n💡 Insights:")
            for insight in analysis['insights']:
                print(f"   • {insight}")
    else:
        print("❌ Analysis failed")


if __name__ == "__main__":
    asyncio.run(main())