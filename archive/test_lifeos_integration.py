#!/usr/bin/env python3
"""
LifeOS Integration Test Script - Phase 1 Foundation Setup

This script tests the basic LifeOS integration capabilities as outlined
in the implementation guide. It verifies connections to all core databases
and performs basic read/write operations.

Based on comprehensive workspace discovery with 44 databases.
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from integrations.notion_mcp_client 
async def test_basic_connection():
    """Test basic MCP connection to Notion."""
    print("🔌 Testing basic Notion MCP connection...")
    
    if not api_token:
        return False
    
    try:
# NOTION_REMOVED:         client = NotionMCPClient(api_token)
        connected = await client.test_connection()
        
        if connected:
            print("✅ Basic connection successful")
            return True
        else:
            print("❌ Connection failed")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

async def test_knowledge_hub_access():
    """Test Knowledge Hub database access."""
    print("\n🧠 Testing Knowledge Hub - AI Enhanced access...")
    
# NOTION_REMOVED:     knowledge_hub_id = os.getenv('NOTION_KNOWLEDGE_HUB_DB_ID')
    
    if not knowledge_hub_id:
        print("❌ NOTION_KNOWLEDGE_HUB_DB_ID not found in environment")
        return False
    
    try:
        # Query Knowledge Hub with limit
        entries = await client.query_database(knowledge_hub_id, page_size=5)
        
        print(f"✅ Found {len(entries)} knowledge entries")
        
# DEMO CODE REMOVED: # Show sample entries
        for i, entry in enumerate(entries[:3], 1):
            title = "Unknown"
            content_type = "Unknown"
            
            # Extract title and type from properties
            if 'properties' in entry:
                props = entry['properties']
                
                # Get title (usually the first title property)
                if 'Name' in props and props['Name'].get('title'):
                    title = props['Name']['title'][0]['text']['content']
                elif 'Title' in props and props['Title'].get('title'):
                    title = props['Title']['title'][0]['text']['content']
                
                # Get type
                if 'Type' in props and props['Type'].get('select'):
                    content_type = props['Type']['select']['name']
            
            print(f"   {i}. {title} ({content_type})")
        
        return True
        
    except Exception as e:
        print(f"❌ Knowledge Hub access failed: {e}")
        return False

async def test_youtube_channels_access():
    """Test YouTube Channels database access."""
    print("\n🎥 Testing YouTube Channels access...")
    
# NOTION_REMOVED:     channels_id = os.getenv('NOTION_YOUTUBE_CHANNELS_DB_ID')
    
    if not channels_id:
        print("❌ NOTION_YOUTUBE_CHANNELS_DB_ID not found in environment")
        return False
    
    try:
        channels = await client.query_database(channels_id, page_size=5)
        
        print(f"✅ Found {len(channels)} YouTube channels")
        
# DEMO CODE REMOVED: # Show sample channels
        for i, channel in enumerate(channels[:3], 1):
            channel_name = "Unknown"
            
            if 'properties' in channel:
                props = channel['properties']
                
                # Get channel name
                if 'Name' in props and props['Name'].get('title'):
                    channel_name = props['Name']['title'][0]['text']['content']
                elif 'Channel' in props and props['Channel'].get('title'):
                    channel_name = props['Channel']['title'][0]['text']['content']
            
            print(f"   {i}. {channel_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ YouTube Channels access failed: {e}")
        return False

async def test_rc_garage_access():
    """Test Home Garage (RC management) database access."""
    print("\n🏎️ Testing Home Garage (RC management) access...")
    
# NOTION_REMOVED:     garage_id = os.getenv('NOTION_HOME_GARAGE_DB_ID')
    
    if not garage_id:
        print("❌ NOTION_HOME_GARAGE_DB_ID not found in environment")
        return False
    
    try:
        garage_items = await client.query_database(garage_id, page_size=5)
        
        print(f"✅ Found {len(garage_items)} garage items")
        
# DEMO CODE REMOVED: # Show sample items
        for i, item in enumerate(garage_items[:3], 1):
            item_name = "Unknown"
            
            if 'properties' in item:
                props = item['properties']
                
                # Get item name
                if 'Name' in props and props['Name'].get('title'):
                    item_name = props['Name']['title'][0]['text']['content']
                elif 'Item' in props and props['Item'].get('title'):
                    item_name = props['Item']['title'][0]['text']['content']
            
            print(f"   {i}. {item_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Home Garage access failed: {e}")
        return False

async def test_maintenance_schedule_access():
    """Test Maintenance Schedule database access."""
    print("\n🔧 Testing Maintenance Schedule access...")
    
# NOTION_REMOVED:     maintenance_id = os.getenv('NOTION_MAINTENANCE_SCHEDULE_DB_ID')
    
    if not maintenance_id:
        print("❌ NOTION_MAINTENANCE_SCHEDULE_DB_ID not found in environment")
        return False
    
    try:
        maintenance_items = await client.query_database(maintenance_id, page_size=5)
        
        print(f"✅ Found {len(maintenance_items)} maintenance items")
        
# DEMO CODE REMOVED: # Show sample items
        for i, item in enumerate(maintenance_items[:3], 1):
            item_name = "Unknown"
            
            if 'properties' in item:
                props = item['properties']
                
                # Get maintenance item name
                if 'Name' in props and props['Name'].get('title'):
                    item_name = props['Name']['title'][0]['text']['content']
                elif 'Task' in props and props['Task'].get('title'):
                    item_name = props['Task']['title'][0]['text']['content']
            
            print(f"   {i}. {item_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Maintenance Schedule access failed: {e}")
        return False

async def test_financial_access():
    """Test Spending Log database access."""
    print("\n💰 Testing Spending Log access...")
    
# NOTION_REMOVED:     spending_id = os.getenv('NOTION_SPENDING_LOG_DB_ID')
    
    if not spending_id:
        print("❌ NOTION_SPENDING_LOG_DB_ID not found in environment")
        return False
    
    try:
        spending_items = await client.query_database(spending_id, page_size=5)
        
        print(f"✅ Found {len(spending_items)} spending entries")
        
# DEMO CODE REMOVED: # Show sample entries
        for i, item in enumerate(spending_items[:3], 1):
            description = "Unknown"
            amount = "Unknown"
            
            if 'properties' in item:
                props = item['properties']
                
                # Get description
                if 'Description' in props and props['Description'].get('title'):
                    description = props['Description']['title'][0]['text']['content']
                elif 'Name' in props and props['Name'].get('title'):
                    description = props['Name']['title'][0]['text']['content']
                
                # Get amount
                if 'Amount' in props and props['Amount'].get('number'):
                    amount = f"${props['Amount']['number']}"
            
            print(f"   {i}. {description} - {amount}")
        
        return True
        
    except Exception as e:
        print(f"❌ Spending Log access failed: {e}")
        return False

async def test_lifelog_write():
    """Test writing to Lifelog database for system logging."""
    print("\n📝 Testing Lifelog database write capability...")
    
# NOTION_REMOVED:     lifelog_id = os.getenv('NOTION_LIFELOG_DB_ID')
    
    if not lifelog_id:
        print("❌ NOTION_LIFELOG_DB_ID not found in environment")
        return False
    
    try:
        # Create a test log entry
        test_entry = {
            "Name": {
                "title": [{"text": {"content": f"LifeOS Integration Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}}]
            },
            "Status": {
                "select": {"name": "Success"}
            },
            "Notes": {
                "rich_text": [{"text": {"content": "LifeOS Phase 1 foundation test completed successfully. All core database connections verified."}}]
            }
        }
        
        # Create the page
        result = await client.create_database_page(lifelog_id, test_entry)
        
        if result:
            print("✅ Successfully created test log entry")
            return True
        else:
            print("❌ Failed to create test log entry")
            return False
        
    except Exception as e:
        print(f"❌ Lifelog write failed: {e}")
        return False

async def test_all_core_databases():
    """Test access to all core LifeOS databases."""
    print("\n🔍 Testing all core LifeOS database connections...")
    
    core_databases = {
        "Knowledge Hub": "NOTION_KNOWLEDGE_HUB_DB_ID",
        "YouTube Channels": "NOTION_YOUTUBE_CHANNELS_DB_ID", 
        "Home Garage": "NOTION_HOME_GARAGE_DB_ID",
        "Maintenance Schedule": "NOTION_MAINTENANCE_SCHEDULE_DB_ID",
        "Spending Log": "NOTION_SPENDING_LOG_DB_ID",
        "Lifelog": "NOTION_LIFELOG_DB_ID",
        "Habits": "NOTION_HABITS_DB_ID",
        "Events": "NOTION_EVENTS_DB_ID"
    }
    
    results = {}
    
    for db_name, env_var in core_databases.items():
        db_id = os.getenv(env_var)
        
        if not db_id:
            print(f"   ❌ {db_name}: Environment variable {env_var} not found")
            results[db_name] = False
            continue
        
        try:
            entries = await client.query_database(db_id, page_size=1)
            print(f"   ✅ {db_name}: {len(entries)} entries accessible")
            results[db_name] = True
        except Exception as e:
            print(f"   ❌ {db_name}: Access failed - {str(e)[:50]}...")
            results[db_name] = False
    
    # Summary
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"\n📊 Database Access Summary: {successful}/{total} databases accessible")
    
    return successful == total

async def run_full_integration_test():
    """Run complete LifeOS Phase 1 integration test."""
    print("🚀 LIFEOS INTEGRATION TEST - PHASE 1 FOUNDATION SETUP")
    print("=" * 60)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Test 1: Basic connection
    test_results.append(await test_basic_connection())
    
    # Test 2: Knowledge Hub access
    test_results.append(await test_knowledge_hub_access())
    
    # Test 3: YouTube Channels access  
    test_results.append(await test_youtube_channels_access())
    
    # Test 4: RC Garage access
    test_results.append(await test_rc_garage_access())
    
    # Test 5: Maintenance Schedule access
    test_results.append(await test_maintenance_schedule_access())
    
    # Test 6: Financial access
    test_results.append(await test_financial_access())
    
    # Test 7: Lifelog write capability
    test_results.append(await test_lifelog_write())
    
    # Test 8: All core databases
    test_results.append(await test_all_core_databases())
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 LIFEOS INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"Tests passed: {passed_tests}/{total_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! LifeOS Phase 1 foundation is ready.")
        print("✅ Basic integration operational")
        print("✅ Core databases accessible")
        print("✅ Logging capability verified")
        print("\n🚀 Ready to proceed with Phase 2: Core Automation")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed. Please review configuration.")
        print("❌ Integration not ready for Phase 2")
        
        # Suggest next steps
        print("\n🔧 Suggested fixes:")
        print("2. Check database IDs in .env file")
        print("3. Ensure Notion integration has database permissions")
        print("4. Review Notion workspace structure")
    
    print(f"\nTest completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed_tests == total_tests

async def main():
    """Main test execution."""
    success = await run_full_integration_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())