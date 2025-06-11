#!/usr/bin/env python3
"""Simple script to import GitHub repositories to Knowledge database"""

import asyncio
import sys
from github_repo_processor import GitHubRepoProcessor
import os
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

async def import_github_repos():
    """Interactive GitHub repository import."""
    
    print("🐙 GITHUB REPOSITORY IMPORTER")
    print("=" * 40)
    print("Import GitHub repositories to your Knowledge database")
    print()
    
    # Check configuration
# NOTION_REMOVED:     knowledge_db_id = os.getenv('NOTION_KNOWLEDGE_DATABASE_ID', '20bec31c-9de2-814e-80db-d13d0c27d869')
    
        print("Please add your Notion API token to the .env file")
        return
    
    print("✅ Notion integration ready")
    print("✅ Knowledge database configured")
    print()
    
    # Get GitHub input
    print("📋 Enter GitHub user or organization:")
    print("Examples: 'torvalds', 'microsoft', 'openai', etc.")
    username = input("GitHub username: ").strip()
    
    if not username:
        print("❌ No username provided")
        return
    
    # Process repositories
    try:
        
        # Fetch repositories
        print(f"\n🔍 Fetching repositories for '{username}'...")
        repos = await processor.get_user_repositories(username)
        
        if not repos:
            print(f"❌ No repositories found for user '{username}'")
            return
        
        # Display and select
        processor.display_repositories(repos)
        selected_repos = processor.get_user_selection(repos)
        
        if not selected_repos:
            print("❌ No repositories selected for import")
            return
        
        # Import repositories
        print(f"\n🚀 Importing {len(selected_repos)} repositories...")
        imported_count = 0
        
        for i, repo in enumerate(selected_repos, 1):
            print(f"\n📦 Processing {i}/{len(selected_repos)}: {repo['name']}")
            
            try:
                analysis = await processor.analyze_repository(repo)
                
                if analysis:
                    success = await processor.                    if success:
                        imported_count += 1
                        print(f"   ✅ Imported successfully")
                    else:
                        print(f"   ❌ Import failed")
                else:
                    print(f"   ❌ Analysis failed")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n🎉 IMPORT COMPLETE")
        print(f"✅ Successfully imported: {imported_count}/{len(selected_repos)} repositories")
        print(f"📚 Check your Knowledge database in Notion for the imported repositories")
        
    except Exception as e:
        print(f"❌ Error during import process: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(import_github_repos())
    except KeyboardInterrupt:
        print("\n👋 Import cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")