#!/usr/bin/env python3
"""
Test GitHub Token Validity
"""

import os
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_github_token():
    """Test if the GitHub token is valid"""
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("❌ No GITHUB_TOKEN found in environment")
        return False
    
    print(f"🔑 Testing GitHub token: {token[:10]}...")
    
    # Test API call
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Test-Script'
    }
    
    try:
        response = requests.get('https://api.github.com/user', headers=headers)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Token valid! Authenticated as: {user_data.get('login', 'Unknown')}")
            print(f"Rate limit remaining: {response.headers.get('X-RateLimit-Remaining', 'Unknown')}")
            return True
        elif response.status_code == 401:
            print("❌ Token invalid or expired")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False

def test_unauthenticated():
    """Test unauthenticated GitHub API"""
    print("\n🔍 Testing unauthenticated GitHub API...")
    
    try:
        response = requests.get('https://api.github.com/rate_limit')
        
        if response.status_code == 200:
            rate_data = response.json()
            print(f"✅ Unauthenticated API working")
            print(f"Rate limit: {rate_data['rate']['remaining']}/{rate_data['rate']['limit']}")
            return True
        else:
            print(f"❌ Unauthenticated API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing unauthenticated API: {e}")
        return False

if __name__ == "__main__":
    print("🧪 GITHUB TOKEN TEST")
    print("=" * 40)
    
    token_valid = test_github_token()
    unauth_works = test_unauthenticated()
    
    print("\n📋 RESULTS:")
    print(f"Token authentication: {'✅ Working' if token_valid else '❌ Failed'}")
    print(f"Unauthenticated API: {'✅ Working' if unauth_works else '❌ Failed'}")
    
    if not token_valid:
        print("\n🔧 SOLUTION:")
        print("1. Generate a new GitHub Personal Access Token at:")
        print("   https://github.com/settings/tokens")
        print("2. Select scopes: 'repo', 'user', 'read:org'")
        print("3. Update GITHUB_TOKEN in .env file")
        print("4. Token should start with 'ghp_', 'gho_', or 'github_pat_'")