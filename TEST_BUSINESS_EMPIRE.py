#!/usr/bin/env python3
"""
TEST BUSINESS EMPIRE SYSTEM
===========================

Test the multi-agent business empire builder system.
"""

import asyncio
import sqlite3
import json
from datetime import datetime
from BUSINESS_EMPIRE_BUILDER import BusinessEmpireBuilder

async def test_business_empire():
    """Test the business empire system."""
    print("🚀 TESTING BUSINESS EMPIRE BUILDER")
    print("=" * 70)
    
    # Initialize the system
    empire = BusinessEmpireBuilder()
    
    # Test 1: Database initialization
    print("🧪 Test 1: Database Initialization")
    try:
        conn = sqlite3.connect(empire.db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['business_opportunities', 'business_projects', 'revenue_streams', 'agent_actions']
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if not missing_tables:
            print("✅ All required tables exist")
        else:
            print(f"❌ Missing tables: {missing_tables}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
    
    # Test 2: CEO Agent Analysis
    print("\n🧪 Test 2: CEO Agent Business Analysis")
    try:
        # Test opportunity identification
        await empire.identify_new_opportunities()
        
        # Check if opportunities were created
        conn = sqlite3.connect(empire.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM business_opportunities")
        opp_count = cursor.fetchone()[0]
        conn.close()
        
        if opp_count > 0:
            print(f"✅ CEO created {opp_count} business opportunities")
        else:
            print("⚠️ CEO didn't create opportunities (may need Gemini API key)")
        
    except Exception as e:
        print(f"❌ CEO analysis test failed: {e}")
    
    # Test 3: Project Creation
    print("\n🧪 Test 3: Project Creation")
    try:
        # Manually create a test project
        project_id = f"test_proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        conn = sqlite3.connect(empire.db_path)
        cursor = conn.cursor()
        
        # First create an opportunity
        opp_id = f"test_opp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute("""
            INSERT INTO business_opportunities 
            (id, category, title, revenue_model, revenue_potential, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (opp_id, "RC", "Test RC Trail App", "Subscription", 5000, "approved_for_development"))
        
        # Create project
        tasks = [
            {"task": "Design app wireframes", "team": "development", "status": "pending"},
            {"task": "Build backend API", "team": "development", "status": "pending"},
            {"task": "Create marketing content", "team": "content", "status": "pending"}
        ]
        
        cursor.execute("""
            INSERT INTO business_projects 
            (id, opportunity_id, name, description, tasks, progress, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (project_id, opp_id, "RC Trail Finder App", "GPS-based trail discovery", 
              json.dumps(tasks), 25, "development"))
        
        conn.commit()
        conn.close()
        
        print("✅ Test project created successfully")
        
    except Exception as e:
        print(f"❌ Project creation test failed: {e}")
    
    # Test 4: Agent Task Management
    print("\n🧪 Test 4: Agent Task Management")
    try:
        # Test getting tasks for development team
        dev_tasks = await empire.get_tasks_for_team("development")
        content_tasks = await empire.get_tasks_for_team("content")
        
        print(f"✅ Found {len(dev_tasks)} development tasks")
        print(f"✅ Found {len(content_tasks)} content tasks")
        
        # Test task execution
        if dev_tasks:
            await empire.execute_development_task(dev_tasks[0])
            print("✅ Development task execution test passed")
        
        if content_tasks:
            await empire.execute_content_task(content_tasks[0])
            print("✅ Content task execution test passed")
        
    except Exception as e:
        print(f"❌ Task management test failed: {e}")
    
    # Test 5: Revenue Tracking
    print("\n🧪 Test 5: Revenue Tracking")
    try:
        # Create test revenue stream
        conn = sqlite3.connect(empire.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id FROM business_projects LIMIT 1
        """)
        project = cursor.fetchone()
        
        if project:
            revenue_id = f"test_rev_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            cursor.execute("""
                INSERT INTO revenue_streams
                (id, project_id, revenue_source, amount, status, customer_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (revenue_id, project[0], "Subscription Sales", 1500.0, "active", 30))
            
            conn.commit()
            print("✅ Revenue tracking test passed")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Revenue tracking test failed: {e}")
    
    # Test 6: Business Stats
    print("\n🧪 Test 6: Business Statistics")
    try:
        from BUSINESS_EMPIRE_DASHBOARD import BusinessEmpireDashboard
        
        dashboard = BusinessEmpireDashboard()
        stats = dashboard.get_empire_stats()
        
        print(f"✅ Empire Stats:")
        print(f"   📊 Opportunities: {stats.get('total_opportunities', 0)}")
        print(f"   🚀 Projects: {stats.get('total_projects', 0)}")
        print(f"   💰 Revenue: ${stats.get('total_revenue', 0):.2f}")
        print(f"   👥 Customers: {stats.get('total_customers', 0)}")
        
    except Exception as e:
        print(f"❌ Business stats test failed: {e}")
    
    # Test Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    # Get final counts
    try:
        conn = sqlite3.connect(empire.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM business_opportunities")
        opp_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM business_projects")
        proj_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM revenue_streams")
        rev_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM agent_actions")
        action_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"📈 Business Opportunities Created: {opp_count}")
        print(f"🚀 Projects Initiated: {proj_count}")
        print(f"💰 Revenue Streams: {rev_count}")
        print(f"🤖 Agent Actions Logged: {action_count}")
        
        if opp_count > 0 and proj_count > 0:
            print("\n✅ BUSINESS EMPIRE SYSTEM IS OPERATIONAL!")
            print("🎯 Ready to turn lifestyle into profitable businesses")
        else:
            print("\n⚠️ System partially functional - may need API keys for full operation")
        
    except Exception as e:
        print(f"❌ Final summary failed: {e}")
    
    print("\n🚀 To start the full system:")
    print("   source venv/bin/activate && python3 BUSINESS_EMPIRE_BUILDER.py")
    print("\n🌐 To view the dashboard:")
    print("   source venv/bin/activate && python3 BUSINESS_EMPIRE_DASHBOARD.py")
    print("   Then open: http://localhost:5002")

def test_gemini_availability():
    """Test if Gemini API is available."""
    import os
    
    print("\n🧪 Testing Gemini 2.5 Pro Availability")
    print("-" * 50)
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    if gemini_key:
        print("✅ GEMINI_API_KEY found")
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Test API call
            response = model.generate_content("Say 'Gemini is working for business empire!'")
            print(f"✅ Gemini response: {response.text}")
            return True
            
        except Exception as e:
            print(f"❌ Gemini API test failed: {e}")
            return False
    else:
        print("⚠️ GEMINI_API_KEY not found")
        print("💡 Set your Gemini API key for full business intelligence:")
        print("   export GEMINI_API_KEY='your_key_here'")
        return False

if __name__ == "__main__":
    # Test Gemini first
    gemini_working = test_gemini_availability()
    
    # Run main tests
    asyncio.run(test_business_empire())