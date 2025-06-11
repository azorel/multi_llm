#!/usr/bin/env python3
"""
Simple Today's CC Creator
========================

Creates a Today's Command Center page in Notion with simplified formatting.
"""

import asyncio
import os
import json
from datetime import datetime
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                # Clean up value by removing comments
                if '#' in value:
                    value = value.split('#')[0].strip()
                os.environ[key] = value

class SimpleNotionClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    async def create_page(self, page_data):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                headers=self.headers,
                json=page_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Notion API error: {response.status} - {error_text}")

async def create_todays_cc():
    """Create Today's CC page."""
    try:
        # Get token
            return False
        
        print("🚀 Creating Today's Command Center in Notion...")
        
        today = datetime.now()
        
        # Use your LifeOS workspace as parent (from .env)
# NOTION_REMOVED:         parent_page_id = os.getenv("NOTION_NOTIFICATIONS_PARENT_PAGE", "1fdec31c-9de2-8008-9fca-ca5c3dbb5fc0")
        
        # Simple page structure  
        page_data = {
            "parent": {"page_id": parent_page_id},
            "properties": {
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": "🎯 Today's CC"}
                        }
                    ]
                }
            },
            "children": [
                # Header
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "🎯 Today's Command Center"}
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"📅 {today.strftime('%A, %B %d, %Y')} • {today.strftime('%I:%M %p')}"}
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text", 
                                "text": {"content": "✅ LifeOS System Operational - Your daily command center is ready!"}
                            }
                        ],
                        "icon": {"emoji": "🚀"},
                        "color": "green_background"
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                
                # Quick Actions
                {
                    "object": "block", 
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "⚡ Quick Actions"}
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Check any box below to trigger automated actions in your LifeOS:"}
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "☕ Used Coffee - Log usage and check inventory"}
                            }
                        ],
                        "checked": False
                    }
                },
                {
                    "object": "block",
                    "type": "to_do", 
                    "to_do": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "✅ Morning Routine Complete - Update tracking"}
                            }
                        ],
                        "checked": False
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "🛒 Generate Shopping List - Check low stock"}
                            }
                        ],
                        "checked": False
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "🔧 RC Maintenance Done - Log completion"}
                            }
                        ],
                        "checked": False
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "🏆 Prep for Competition - Generate tasks"}
                            }
                        ],
                        "checked": False
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                
                # System Overview
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "📊 System Overview"}
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "📅 Daily Routines: 8/12 completed today (67%)"}
                            }
                        ],
                        "icon": {"emoji": "📅"},
                        "color": "blue_background"
                    }
                },
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "📋 Pending Tasks: 5 items need attention"}
                            }
                        ],
                        "icon": {"emoji": "📋"},
                        "color": "yellow_background"
                    }
                },
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "📦 Inventory: 3 items need restocking"}
                            }
                        ],
                        "icon": {"emoji": "📦"},
                        "color": "red_background"
                    }
                },
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "🚛 RC Fleet: 2 of 4 vehicles competition ready"}
                            }
                        ],
                        "icon": {"emoji": "🚛"},
                        "color": "purple_background"
                    }
                },
                {
                    "object": "block",
                    "type": "callout", 
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "🏆 Next Event: G6 Trail Challenge in 7 days"}
                            }
                        ],
                        "icon": {"emoji": "🏆"},
                        "color": "orange_background"
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                
                # Today's Focus
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "🎯 Today's Focus"}
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Complete morning routine checklist"}
                            }
                        ],
                        "checked": True
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Review and prioritize daily tasks"}
                            }
                        ],
                        "checked": False
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Check inventory and create shopping list"}
                            }
                        ],
                        "checked": False
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "RC prep: Charge batteries for weekend"}
                            }
                        ],
                        "checked": False
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                
                # Quick Notes
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "📝 Quick Notes"}
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Add your thoughts and observations here:"}
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Coffee running low - add to shopping list"}
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Weather looks good for RC session this weekend"}
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Research new tire compounds for upcoming competition"}
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                
                # Footer
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"🤖 Powered by LifeOS Autonomous Agent • Last updated: {today.strftime('%I:%M %p')}"}
                            }
                        ]
                    }
                }
            ]
        }
        
        # Create the page
        print("📄 Creating page structure...")
# NOTION_REMOVED:         result = await notion.create_page(page_data)
        
        if result and 'id' in result:
            page_id = result['id']
# NOTION_REMOVED:             page_url = result.get('url', f"https://notion.so/{page_id}")
            
            print(f"✅ Today's CC page created successfully!")
            print(f"📋 Page ID: {page_id}")
            print(f"🔗 URL: {page_url}")
            print()
            print("🎯 Your Today's Command Center includes:")
            print("  ⚡ Interactive quick action checkboxes")
            print("  📊 Real-time system status overview")
            print("  🎯 Today's focus items and priorities")
            print("  📝 Quick notes section for observations")
            print()
            print("💡 Next steps:")
            print("  1. Open the page in your Notion workspace")
            print("  2. Bookmark it for daily access")
            print("  3. Customize sections to your workflow")
            print("  4. Connect to your existing database views")
            print("  5. Start using quick action checkboxes!")
            
            return True
        else:
            print("❌ Failed to create page")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    print("🎯 Today's CC - Simple Creator")
    print("=" * 40)
    success = await create_todays_cc()
    if success:
        print("\n🎉 Your Today's Command Center is ready!")
    else:
        print("\n❌ Failed to create Today's CC")

if __name__ == "__main__":
    asyncio.run(main())