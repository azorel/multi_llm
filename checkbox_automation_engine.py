#!/usr/bin/env python3
"""
LifeOS Checkbox Automation Engine
Comprehensive automation system for all checkbox fields across the workspace
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Load environment
env_path = Path('.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                if '#' in value:
                    value = value.split('#')[0].strip()
                os.environ[key] = value

class CheckboxAutomationEngine:
    """Central engine for processing all checkbox automations across LifeOS workspace."""
    
    def __init__(self):
        self.headers = {
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        # Database IDs from workspace mapping
        self.database_ids = {
            'knowledge_hub': '20bec31c-9de2-814e-80db-d13d0c27d869',
            'youtube_channels': '203ec31c-9de2-8079-ae4e-ed754d474888',
            'github_users': '20dec31c-9de2-81f3-be69-e656966b28f8',
            'maintenance_schedule': '203ec31c-9de2-8176-a4b2-f02415f950da',
            'habits': '203ec31c-9de2-816f-a8a6-ec5969b3f4bc',
            'things_bought': '205ec31c-9de2-809b-8676-e5686fc02c52',
            'recurring': '203ec31c-9de2-8142-a0a1-de4b49fbace7',
            'weekly': '1fdec31c-9de2-8126-bc1c-f8233192d910',
            'books': '203ec31c-9de2-812f-aaba-efe3f9b21e98',
            'meals': '1ffec31c-9de2-818b-8569-ddbc74a1e754'
        }
        
        # Checkbox automation configurations
        self.automation_configs = self._load_automation_configs()
        
        # Track processed items to prevent loops
        self.processed_items = set()
        
        print("🤖 Checkbox Automation Engine initialized")
        print(f"📊 Configured automations: {len(self.automation_configs)}")
    
    def _load_automation_configs(self) -> Dict[str, Dict]:
        """Load automation configurations for each checkbox field."""
        return {
            # YouTube Channel Automations
            'youtube_channels.Auto Process': {
                'database_id': self.database_ids['youtube_channels'],
                'checkbox_field': 'Auto Process',
                'handler': self._handle_youtube_auto_process,
                'description': 'Automatically process marked channels continuously'
            },
            'youtube_channels.Process Channel': {
                'database_id': self.database_ids['youtube_channels'],
                'checkbox_field': 'Process Channel',
                'handler': self._handle_youtube_process_channel,
                'description': 'One-time channel processing trigger'
            },
            
            # Knowledge Hub Automations
            'knowledge_hub.Decision Made': {
                'database_id': self.database_ids['knowledge_hub'],
                'checkbox_field': 'Decision Made',
                'handler': self._handle_knowledge_decision_made,
                'description': 'Process finalized decisions into action items'
            },
            'knowledge_hub.📁 Pass': {
                'database_id': self.database_ids['knowledge_hub'],
                'checkbox_field': '📁 Pass',
                'handler': self._handle_knowledge_pass,
                'description': 'Archive approved content for sharing'
            },
            'knowledge_hub.🚀 Yes': {
                'database_id': self.database_ids['knowledge_hub'],
                'checkbox_field': '🚀 Yes',
                'handler': self._handle_knowledge_implementation,
                'description': 'Trigger implementation workflows'
            },
            
            # Maintenance Automations
            'maintenance_schedule.Completed': {
                'database_id': self.database_ids['maintenance_schedule'],
                'checkbox_field': 'Completed',
                'handler': self._handle_maintenance_completed,
                'description': 'Process completed maintenance and schedule next'
            },
            
            # Habit Tracking Automations
            'habits.MON': {
                'database_id': self.database_ids['habits'],
                'checkbox_field': 'MON',
                'handler': lambda item: self._handle_habit_completion(item, 'Monday'),
                'description': 'Track Monday habit completion'
            },
            'habits.TUE': {
                'database_id': self.database_ids['habits'],
                'checkbox_field': 'TUE',
                'handler': lambda item: self._handle_habit_completion(item, 'Tuesday'),
                'description': 'Track Tuesday habit completion'
            },
            'habits.WED': {
                'database_id': self.database_ids['habits'],
                'checkbox_field': 'WED',
                'handler': lambda item: self._handle_habit_completion(item, 'Wednesday'),
                'description': 'Track Wednesday habit completion'
            },
            'habits.THU': {
                'database_id': self.database_ids['habits'],
                'checkbox_field': 'THU',
                'handler': lambda item: self._handle_habit_completion(item, 'Thursday'),
                'description': 'Track Thursday habit completion'
            },
            'habits.FRI': {
                'database_id': self.database_ids['habits'],
                'checkbox_field': 'FRI',
                'handler': lambda item: self._handle_habit_completion(item, 'Friday'),
                'description': 'Track Friday habit completion'
            },
            'habits.SAT': {
                'database_id': self.database_ids['habits'],
                'checkbox_field': 'SAT',
                'handler': lambda item: self._handle_habit_completion(item, 'Saturday'),
                'description': 'Track Saturday habit completion'
            },
            'habits.SUN': {
                'database_id': self.database_ids['habits'],
                'checkbox_field': 'SUN',
                'handler': lambda item: self._handle_habit_completion(item, 'Sunday'),
                'description': 'Track Sunday habit completion'
            },
            
            # Purchase & Planning Automations
            'things_bought.Buy': {
                'database_id': self.database_ids['things_bought'],
                'checkbox_field': 'Buy',
                'handler': self._handle_purchase_decision,
                'description': 'Process purchase decisions and create tracking'
            },
            'recurring.active': {
                'database_id': self.database_ids['recurring'],
                'checkbox_field': 'active',
                'handler': self._handle_recurring_activation,
                'description': 'Activate recurring task automation'
            },
            'weekly.this week?': {
                'database_id': self.database_ids['weekly'],
                'checkbox_field': 'this week?',
                'handler': self._handle_weekly_planning,
                'description': 'Add to current week planning'
            }
        }
    
    async def monitor_all_checkboxes(self):
        """Main monitoring loop for all checkbox automations."""
        print("🔄 Starting checkbox automation monitoring...")
        
        while True:
            try:
                await self._single_automation_cycle()
                # Wait before next check cycle
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"❌ Critical error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Longer wait on critical errors
    
    async def _single_automation_cycle(self):
        """Run a single automation cycle across all checkboxes."""
        try:
            # Check each automation configuration
            for automation_key, config in self.automation_configs.items():
                try:
                    await self._check_and_process_checkbox(automation_key, config)
                except Exception as e:
                    print(f"❌ Error processing {automation_key}: {e}")
        except Exception as e:
            print(f"❌ Error in automation cycle: {e}")
    
    async def _check_and_process_checkbox(self, automation_key: str, config: Dict):
        """Check a specific checkbox field and process if marked."""
        try:
            database_id = config['database_id']
            checkbox_field = config['checkbox_field']
            handler = config['handler']
            
            # Query for items with checkbox marked true
            query_data = {
                "filter": {
                    "property": checkbox_field,
                    "checkbox": {"equals": True}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    headers=self.headers,
                    json=query_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('results', [])
                        
                        for item in items:
                            item_id = item['id']
                            
                            # Skip if already processed recently
                            if item_id in self.processed_items:
                                continue
                            
                            print(f"📋 Processing {automation_key}: {item_id}")
                            
                            # Call the specific handler
                            try:
                                await handler(item)
                                
                                # Mark as processed
                                self.processed_items.add(item_id)
                                
                                # Uncheck the checkbox (for one-time actions)
                                if automation_key not in ['habits.MON', 'habits.TUE', 'habits.WED', 
                                                        'habits.THU', 'habits.FRI', 'habits.SAT', 'habits.SUN']:
                                    await self._uncheck_checkbox(item_id, checkbox_field)
                                
                                print(f"✅ Completed {automation_key} for {item_id}")
                                
                            except Exception as e:
                                print(f"❌ Handler error for {automation_key}: {e}")
                    
        except Exception as e:
            print(f"❌ Error checking {automation_key}: {e}")
    
    async def _uncheck_checkbox(self, page_id: str, checkbox_field: str):
        """Uncheck a checkbox after processing."""
        try:
            update_data = {
                "properties": {
                    checkbox_field: {
                        "checkbox": False
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    headers=self.headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        print(f"📋 Unchecked {checkbox_field} for {page_id}")
                    
        except Exception as e:
            print(f"⚠️ Error unchecking {checkbox_field}: {e}")
    
    def get_property_value(self, props: Dict[str, Any], prop_name: str, prop_type: str) -> str:
        """Extract property value from Notion properties."""
        try:
            prop = props.get(prop_name, {})
            
            if prop_type == 'title' and prop.get('title'):
                return prop['title'][0].get('plain_text', '')
            elif prop_type == 'rich_text' and prop.get('rich_text'):
                return prop['rich_text'][0].get('plain_text', '')
            elif prop_type == 'url':
                return prop.get('url', '')
            elif prop_type == 'select' and prop.get('select'):
                return prop['select'].get('name', '')
            
            return ''
        except Exception:
            return ''
    
    # ========================================
    # SPECIFIC AUTOMATION HANDLERS
    # ========================================
    
    async def _handle_youtube_auto_process(self, item: Dict[str, Any]):
        """Handle YouTube Auto Process checkbox."""
        props = item.get('properties', {})
        channel_name = self.get_property_value(props, 'Channel Name', 'title')
        
        print(f"🎥 Auto processing YouTube channel: {channel_name}")
        
        # Import and run enhanced video processor
        try:
            from simple_video_processor import process_videos_with_ai
            await process_videos_with_ai()
            print(f"✅ Auto processed videos for: {channel_name}")
        except Exception as e:
            print(f"❌ Auto processing failed for {channel_name}: {e}")
    
    async def _handle_youtube_process_channel(self, item: Dict[str, Any]):
        """Handle YouTube Process Channel checkbox (existing working automation)."""
        props = item.get('properties', {})
        channel_name = self.get_property_value(props, 'Channel Name', 'title')
        
        print(f"🎥 Processing YouTube channel: {channel_name}")
        
        # This is already handled by the existing system
        # Just log for monitoring
        print(f"✅ YouTube channel processing triggered for: {channel_name}")
    
    async def _handle_knowledge_decision_made(self, item: Dict[str, Any]):
        """Handle Knowledge Hub Decision Made checkbox."""
        props = item.get('properties', {})
        title = self.get_property_value(props, 'Name', 'title')
        
        print(f"🧠 Processing decision: {title}")
        
        # Update status to Decision Made
        update_data = {
            "properties": {
                "Processing Status": {
                    "select": {"name": "Decision Made"}
                },
                "Last Processed": {
                    "date": {"start": datetime.now().isoformat()}
                }
            }
        }
        
        await self._update_page(item['id'], update_data)
        print(f"✅ Decision processed: {title}")
    
    async def _handle_knowledge_pass(self, item: Dict[str, Any]):
        """Handle Knowledge Hub Pass checkbox."""
        props = item.get('properties', {})
        title = self.get_property_value(props, 'Name', 'title')
        
        print(f"📁 Archiving approved content: {title}")
        
        # Update status to Archived
        update_data = {
            "properties": {
                "Processing Status": {
                    "select": {"name": "Archived"}
                },
                "Archive Date": {
                    "date": {"start": datetime.now().isoformat()}
                }
            }
        }
        
        await self._update_page(item['id'], update_data)
        print(f"✅ Content archived: {title}")
    
    async def _handle_knowledge_implementation(self, item: Dict[str, Any]):
        """Handle Knowledge Hub Implementation checkbox."""
        props = item.get('properties', {})
        title = self.get_property_value(props, 'Name', 'title')
        
        print(f"🚀 Triggering implementation: {title}")
        
        # Update status to Implementation
        update_data = {
            "properties": {
                "Processing Status": {
                    "select": {"name": "Implementation"}
                },
                "Implementation Date": {
                    "date": {"start": datetime.now().isoformat()}
                }
            }
        }
        
        await self._update_page(item['id'], update_data)
        print(f"✅ Implementation triggered: {title}")
    
    async def _handle_maintenance_completed(self, item: Dict[str, Any]):
        """Handle Maintenance Completed checkbox."""
        props = item.get('properties', {})
        maintenance_type = self.get_property_value(props, 'Type', 'select')
        
        print(f"🔧 Maintenance completed: {maintenance_type}")
        
        # Update completion date and status
        update_data = {
            "properties": {
                "Completion Date": {
                    "date": {"start": datetime.now().isoformat()}
                },
                "Status": {
                    "select": {"name": "Completed"}
                },
                "Notes": {
                    "rich_text": [{
                        "text": {"content": f"Completed on {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
                    }]
                }
            }
        }
        
        await self._update_page(item['id'], update_data)
        print(f"✅ Maintenance recorded: {maintenance_type}")
    
    async def _handle_habit_completion(self, item: Dict[str, Any], day: str):
        """Handle daily habit completion."""
        props = item.get('properties', {})
        habit_name = self.get_property_value(props, 'Habit', 'title')
        
        print(f"✅ {day} habit completed: {habit_name}")
        
        # Update last completion date
        update_data = {
            "properties": {
                "Last Completed": {
                    "date": {"start": datetime.now().isoformat()}
                },
                "Streak Count": {
                    "number": self._calculate_habit_streak(item, day)
                }
            }
        }
        
        await self._update_page(item['id'], update_data)
        print(f"🎯 Habit streak updated: {habit_name}")
    
    def _calculate_habit_streak(self, item: Dict[str, Any], day: str) -> int:
        """Calculate habit streak (simplified implementation)."""
        # In a full implementation, this would analyze completion history
        # For now, just increment current streak
        props = item.get('properties', {})
        current_streak = props.get('Streak Count', {}).get('number', 0) or 0
        return current_streak + 1
    
    async def _handle_purchase_decision(self, item: Dict[str, Any]):
        """Handle Things Bought purchase decision."""
        props = item.get('properties', {})
        item_name = self.get_property_value(props, 'Name', 'title')
        
        print(f"💰 Purchase decision made: {item_name}")
        
        # Update purchase status and date
        update_data = {
            "properties": {
                "Purchase Status": {
                    "select": {"name": "Approved"}
                },
                "Decision Date": {
                    "date": {"start": datetime.now().isoformat()}
                }
            }
        }
        
        await self._update_page(item['id'], update_data)
        print(f"✅ Purchase approved: {item_name}")
    
    async def _handle_recurring_activation(self, item: Dict[str, Any]):
        """Handle recurring task activation."""
        props = item.get('properties', {})
        task_name = self.get_property_value(props, 'Name', 'title')
        
        print(f"🔄 Activating recurring task: {task_name}")
        
        # Update activation status
        update_data = {
            "properties": {
                "Status": {
                    "select": {"name": "Active"}
                },
                "Activation Date": {
                    "date": {"start": datetime.now().isoformat()}
                },
                "Next Due": {
                    "date": {"start": (datetime.now() + timedelta(days=1)).isoformat()}
                }
            }
        }
        
        await self._update_page(item['id'], update_data)
        print(f"✅ Recurring task activated: {task_name}")
    
    async def _handle_weekly_planning(self, item: Dict[str, Any]):
        """Handle weekly planning checkbox."""
        props = item.get('properties', {})
        task_name = self.get_property_value(props, 'Name', 'title')
        
        print(f"📅 Adding to this week: {task_name}")
        
        # Update week assignment
        update_data = {
            "properties": {
                "Week Status": {
                    "select": {"name": "This Week"}
                },
                "Assigned Date": {
                    "date": {"start": datetime.now().isoformat()}
                },
                "Priority": {
                    "select": {"name": "High"}
                }
            }
        }
        
        await self._update_page(item['id'], update_data)
        print(f"✅ Added to this week: {task_name}")
    
    async def _update_page(self, page_id: str, update_data: Dict):
        """Update a Notion page with new properties."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    headers=self.headers,
                    json=update_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        print(f"⚠️ Update failed: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Error updating page: {e}")
            return False

async def main():
    """Main function to run checkbox automation engine."""
    engine = CheckboxAutomationEngine()
    
    print("🚀 Starting LifeOS Checkbox Automation Engine")
    print("=" * 50)
    
    try:
        await engine.monitor_all_checkboxes()
    except KeyboardInterrupt:
        print("\n🛑 Automation engine stopped by user")
    except Exception as e:
        print(f"\n❌ Engine error: {e}")

if __name__ == "__main__":
    asyncio.run(main())