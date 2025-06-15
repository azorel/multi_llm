#!/usr/bin/env python3
"""
Test the active-agents endpoint to isolate the issue
"""

import requests
import sys

def test_active_agents():
    """Test the active-agents endpoint."""
    try:
        response = requests.get('http://localhost:8081/active-agents', timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        print(f"Content: {response.text[:500]}...")
        
        if response.status_code == 500:
            print("\n❌ ENDPOINT IS FAILING")
            return False
        else:
            print("\n✅ ENDPOINT IS WORKING")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_active_agents()