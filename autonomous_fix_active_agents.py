#!/usr/bin/env python3
"""
Autonomous Template Fixer Agent - Fix active-agents page error
"""

import os
import shutil
import time
import re

def autonomous_template_fixer():
    """
    Fix the active-agents template error: 'dict object' has no attribute 'system_metrics'
    
    Error: The template is trying to access agents.system_metrics.total_agents
    but the agents object is a dict without a system_metrics attribute.
    
    Solution: Fix the template to use the correct data structure or provide default values.
    """
    
    print("🔧 Autonomous Template Fixer Agent: Active Agents Error")
    print("Error: 'dict object' has no attribute 'system_metrics'")
    print("Location: templates/active_agents.html line 91")
    
    template_path = "templates/active_agents.html"
    
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False
    
    # Create backup
    backup_path = f"{template_path}.backup_autonomous_{int(time.time())}"
    shutil.copy2(template_path, backup_path)
    print(f"💾 Created backup: {backup_path}")
    
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📖 Template file read: {len(content)} characters")
    
    # Apply fixes
    fixed_content = content
    fixes_applied = []
    
    # Fix system_metrics references - replace with default values or conditional checks
    system_metrics_patterns = [
        (r'{{ agents\.system_metrics\.total_agents }}', '{{ agents.get("system_metrics", {}).get("total_agents", 0) }}'),
        (r'{{ agents\.system_metrics\.active_agents }}', '{{ agents.get("system_metrics", {}).get("active_agents", 0) }}'),
        (r'{{ agents\.system_metrics\.queued_tasks }}', '{{ agents.get("system_metrics", {}).get("queued_tasks", 0) }}'),
        (r'{{ agents\.system_metrics\.completed_today }}', '{{ agents.get("system_metrics", {}).get("completed_today", 0) }}'),
        (r'{{ "%.1f"\|format\(agents\.system_metrics\.success_rate\) }}', '{{ "%.1f"|format(agents.get("system_metrics", {}).get("success_rate", 0)) }}'),
        (r'{{ agents\.system_metrics\.avg_response_time }}', '{{ agents.get("system_metrics", {}).get("avg_response_time", 0) }}'),
    ]
    
    for pattern, replacement in system_metrics_patterns:
        if re.search(pattern, fixed_content):
            fixed_content = re.sub(pattern, replacement, fixed_content)
            fixes_applied.append(f"Fixed system_metrics access: {pattern}")
    
    # Also fix the references in the template that expect agents.active_agents to be a list
    # but it might be empty or have a different structure
    active_agents_fixes = [
        (r'{% if agents\.active_agents %}', '{% if agents.get("active_agents") %}'),
        (r'{{ agents\.active_agents\|length }}', '{{ agents.get("active_agents", [])|length }}'),
        (r'{% for agent in agents\.active_agents %}', '{% for agent in agents.get("active_agents", []) %}'),
        (r'{{ agents\.agent_queue\|length }}', '{{ agents.get("agent_queue", [])|length }}'),
        (r'{% for agent in agents\.agent_queue %}', '{% for agent in agents.get("agent_queue", []) %}'),
        (r'{% if agents\.agent_queue %}', '{% if agents.get("agent_queue") %}'),
        (r'{% for agent in agents\.active_agents \+ agents\.agent_queue %}', '{% for agent in (agents.get("active_agents", []) + agents.get("agent_queue", [])) %}'),
        (r'{% for task in agents\.completed_tasks %}', '{% for task in agents.get("completed_tasks", []) %}'),
    ]
    
    for pattern, replacement in active_agents_fixes:
        if re.search(pattern, fixed_content):
            fixed_content = re.sub(pattern, replacement, fixed_content)
            fixes_applied.append(f"Fixed agents access: {pattern}")
    
    # Write the fixed template
    if fixes_applied:
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("✅ Template fixed successfully!")
        for fix in fixes_applied:
            print(f"  - {fix}")
        print(f"💾 Backup saved: {backup_path}")
        return True
    else:
        print("ℹ️ No system_metrics issues found to fix")
        return False

def verify_fix():
    """Verify the fix by testing the page"""
    import requests
    try:
        response = requests.get("http://localhost:5000/active-agents", timeout=5)
        if response.status_code == 200:
            print("✅ Verification: Page is now working!")
            return True
        else:
            print(f"❌ Verification failed: Status {response.status_code}")
            print(response.text[:200])
            return False
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    print("🤖 AUTONOMOUS TEMPLATE FIXING SYSTEM")
    print("=" * 50)
    
    # Fix the template
    success = autonomous_template_fixer()
    
    if success:
        print("\n🔍 Verifying fix...")
        verify_fix()
    
    print("\n🎉 Autonomous fixing completed!")