#!/usr/bin/env python3
"""
GitHub Token Setup and Validation Tool
Helps fix GitHub authentication issues
"""

import os
import requests
from dotenv import load_dotenv
from github_api_handler import GitHubAPIHandler

def check_current_token():
    """Check current GitHub token status"""
    print("🔍 CHECKING CURRENT GITHUB TOKEN")
    print("=" * 50)
    
    load_dotenv()
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("❌ No GITHUB_TOKEN found in .env file")
        return False
    
    print(f"Token found: {token[:10]}...{token[-4:]} (length: {len(token)})")
    
    # Test token
    try:
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Token-Validator'
        }
        
        response = requests.get('https://api.github.com/user', headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Token valid - authenticated as: {user_data.get('login')}")
            print(f"📊 Rate limit: {response.headers.get('X-RateLimit-Remaining')}/{response.headers.get('X-RateLimit-Limit')}")
            return True
        elif response.status_code == 401:
            print("❌ Token invalid or expired")
            print("Response:", response.json().get('message', 'Unknown error'))
            return False
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False

def test_github_api_handler():
    """Test our GitHub API handler with current token"""
    print("\n🧪 TESTING GITHUB API HANDLER")
    print("=" * 50)
    
    try:
        # Create new handler (will validate token)
        handler = GitHubAPIHandler()
        
        print(f"Token valid: {handler.token_valid}")
        print(f"Has token: {bool(handler.token)}")
        
        # Test user info fetch
        print("\nTesting user info fetch...")
        result = handler.get_user_info('octocat')
        
        if result['success']:
            print("✅ User info fetch successful")
            user = result['user']
            print(f"   Username: {user['username']}")
            print(f"   Name: {user['name']}")
            print(f"   Public repos: {user['public_repos']}")
        else:
            print(f"❌ User info fetch failed: {result['error']}")
        
        return handler.token_valid
        
    except Exception as e:
        print(f"❌ Error testing GitHub API handler: {e}")
        return False

def generate_token_instructions():
    """Generate instructions for creating a new GitHub token"""
    print("\n📝 GITHUB TOKEN SETUP INSTRUCTIONS")
    print("=" * 50)
    
    print("""
1. Go to GitHub Personal Access Tokens page:
   https://github.com/settings/tokens

2. Click "Generate new token" → "Generate new token (classic)"

3. Give it a descriptive name like: "Autonomous Multi-LLM Agent"

4. Set expiration: 90 days (or longer)

5. Select the following scopes:
   ✅ repo (Full control of private repositories)
   ✅ user (Read user profile information)  
   ✅ read:org (Read org membership)
   ✅ notifications (Access notifications)

6. Click "Generate token"

7. Copy the token (starts with 'ghp_' or 'github_pat_')

8. Update your .env file:
   GITHUB_TOKEN=your_new_token_here

9. Restart the application

""")

def suggest_token_format():
    """Suggest correct token format"""
    print("🔧 EXPECTED TOKEN FORMAT")
    print("=" * 50)
    
    print("""
Valid GitHub token formats:
• Classic tokens: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
• Fine-grained tokens: github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
• OAuth tokens: gho_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

Your current token format appears invalid.
Please generate a new token following the instructions above.
""")

def fix_env_file():
    """Offer to help fix .env file"""
    print("\n🛠️ .ENV FILE HELPER")
    print("=" * 50)
    
    env_path = ".env"
    if not os.path.exists(env_path):
        print("❌ .env file not found")
        return
    
    print("Current .env file contains:")
    
    # Read current file
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    github_token_line = None
    for i, line in enumerate(lines):
        if line.strip().startswith('GITHUB_TOKEN='):
            github_token_line = i
            current_token = line.split('=', 1)[1].strip()
            print(f"Line {i+1}: GITHUB_TOKEN={current_token[:10]}...{current_token[-4:] if len(current_token) > 14 else current_token}")
            break
    
    if github_token_line is not None:
        print(f"\n⚠️ Found GITHUB_TOKEN on line {github_token_line + 1}")
        print("Please replace the current token with a new valid token.")
    else:
        print("❌ No GITHUB_TOKEN line found in .env file")
        print("Please add: GITHUB_TOKEN=your_token_here")

def main():
    """Main function to diagnose and fix GitHub token issues"""
    print("🔧 GITHUB TOKEN FIX UTILITY")
    print("=" * 60)
    
    # Step 1: Check current token
    token_valid = check_current_token()
    
    # Step 2: Test API handler
    handler_working = test_github_api_handler()
    
    # Step 3: Provide guidance
    if token_valid and handler_working:
        print("\n🎉 SUCCESS! GitHub integration is working correctly.")
        print("No action needed.")
    else:
        suggest_token_format()
        generate_token_instructions()
        fix_env_file()
        
        print("\n🔄 NEXT STEPS:")
        print("1. Generate a new GitHub token using the instructions above")
        print("2. Update GITHUB_TOKEN in your .env file")
        print("3. Run this script again to verify")
        print("4. Restart your Flask application")

if __name__ == "__main__":
    main()