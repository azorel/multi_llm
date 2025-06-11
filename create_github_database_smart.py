#!/usr/bin/env python3
"""Smart GitHub Users Database Creation - finds existing pages and creates database"""

import asyncio
import aiohttp
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

async def find_existing_page_and_create_database():
    """Find an existing page and create the GitHub Users database there."""
    
        return None
    
    headers = {
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    print("🚀 SMART GITHUB USERS DATABASE CREATION")
    print("=" * 50)
    
    # Search for any existing pages in the workspace
    print("🔍 Searching for existing pages in your workspace...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Search for pages
            search_data = {
                "query": "",
                "filter": {"property": "object", "value": "page"},
                "page_size": 10
            }
            
            async with session.post(
                headers=headers,
                json=search_data,
                timeout=10
            ) as response:
                if response.status == 200:
                    search_results = await response.json()
                    pages = search_results.get('results', [])
                    
                    print(f"📋 Found {len(pages)} pages in workspace")
                    
                    # Look for a suitable parent page
                    suitable_page = None
                    for page in pages:
                        # Skip pages that are databases themselves
                        if page.get('object') == 'page':
                            page_title = ""
                            if page.get('properties', {}).get('title', {}).get('title'):
                                page_title = page['properties']['title']['title'][0].get('plain_text', '')
                            elif page.get('properties', {}).get('Name', {}).get('title'):
                                page_title = page['properties']['Name']['title'][0].get('plain_text', '')
                            
                            print(f"📄 Found page: {page_title or 'Untitled'} (ID: {page['id'][:8]}...)")
                            
                            # Use the first suitable page
                            if not suitable_page:
                                suitable_page = page
                    
                    if suitable_page:
                        print(f"✅ Using page as parent: {page_title or 'Untitled'}")
                        return await create_database_with_parent(suitable_page['id'], headers)
                    else:
                        print("❌ No suitable parent page found")
                        return await create_page_and_database(headers)
                        
                else:
                    print(f"⚠️ Search failed: {response.status}")
                    return await create_page_and_database(headers)
                    
    except Exception as e:
        print(f"⚠️ Error searching: {e}")
        return await create_page_and_database(headers)

async def create_page_and_database(headers):
    """Create a parent page first, then create the database."""
    print("\n📝 Creating parent page for databases...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Create a parent page first
            page_data = {
                "parent": {"type": "workspace", "workspace": True},
                "properties": {
                    "title": [{"type": "text", "text": {"content": "LifeOS Databases"}}]
                },
                "children": [
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [{"type": "text", "text": {"content": "LifeOS Autonomous System Databases"}}]
                        }
                    },
                    {
                        "object": "block", 
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": "This page contains databases for the LifeOS autonomous agent system."}}]
                        }
                    }
                ]
            }
            
            async with session.post(
                headers=headers,
                json=page_data,
                timeout=15
            ) as response:
                if response.status == 200:
                    page_result = await response.json()
                    parent_page_id = page_result['id']
                    print(f"✅ Created parent page: {parent_page_id}")
                    
                    # Now create the database
                    return await create_database_with_parent(parent_page_id, headers)
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create parent page: {response.status}")
                    print(f"Error: {error_text}")
                    return None
                    
    except Exception as e:
        print(f"❌ Error creating parent page: {e}")
        return None

async def create_database_with_parent(parent_page_id, headers):
    """Create the GitHub Users database with a specific parent."""
    print(f"\n📝 Creating GitHub Users database with parent: {parent_page_id}")
    
    database_data = {
        "parent": {
            "type": "page_id",
            "page_id": parent_page_id
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "GitHub Users"
                }
            }
        ],
        "properties": {
            "Name": {
                "title": {}
            },
            "Username": {
                "rich_text": {}
            },
            "Profile URL": {
                "url": {}
            },
            "Public Repos": {
                "number": {"format": "number"}
            },
            "Followers": {
                "number": {"format": "number"}
            },
            "Following": {
                "number": {"format": "number"}
            },
            "Bio": {
                "rich_text": {}
            },
            "Company": {
                "rich_text": {}
            },
            "Location": {
                "rich_text": {}
            },
            "Website": {
                "url": {}
            },
            "Primary Language": {
                "select": {
                    "options": [
                        {"name": "Python", "color": "blue"},
                        {"name": "JavaScript", "color": "yellow"},
                        {"name": "TypeScript", "color": "purple"},
                        {"name": "Java", "color": "orange"},
                        {"name": "C++", "color": "red"},
                        {"name": "Go", "color": "green"},
                        {"name": "Rust", "color": "brown"},
                        {"name": "C#", "color": "purple"},
                        {"name": "PHP", "color": "pink"},
                        {"name": "Ruby", "color": "red"},
                        {"name": "Other", "color": "gray"}
                    ]
                }
            },
            "Account Type": {
                "select": {
                    "options": [
                        {"name": "User", "color": "blue"},
                        {"name": "Organization", "color": "green"},
                        {"name": "Bot", "color": "gray"}
                    ]
                }
            },
            "Process User": {
                "checkbox": {}
            },
            "Last Processed": {
                "date": {}
            },
            "Repos Imported": {
                "number": {"format": "number"}
            },
            "Processing Status": {
                "select": {
                    "options": [
                        {"name": "Pending", "color": "yellow"},
                        {"name": "Processing", "color": "blue"},
                        {"name": "Completed", "color": "green"},
                        {"name": "Failed", "color": "red"},
                        {"name": "Skipped", "color": "gray"}
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "High", "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "gray"}
                    ]
                }
            },
            "Tags": {
                "multi_select": {
                    "options": [
                        {"name": "AI/ML", "color": "purple"},
                        {"name": "Web Development", "color": "blue"},
                        {"name": "Open Source", "color": "green"},
                        {"name": "Framework Author", "color": "orange"},
                        {"name": "Company", "color": "red"},
                        {"name": "Influencer", "color": "yellow"},
                        {"name": "Tutorial Creator", "color": "pink"},
                        {"name": "DevOps", "color": "brown"},
                        {"name": "Mobile Development", "color": "blue"},
                        {"name": "Game Development", "color": "purple"}
                    ]
                }
            },
            "Notes": {
                "rich_text": {}
            }
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                headers=headers,
                json=database_data,
                timeout=15
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    database_id = data['id']
                    
                    print("✅ GitHub Users Database created successfully!")
                    print(f"📋 Database ID: {database_id}")
                    print(f"🔗 Database URL: https://notion.so/{database_id.replace('-', '')}")
                    
                    # Add to .env file
                    await update_env_file(database_id)
                    
# DEMO CODE REMOVED: # Add sample users
# DEMO CODE REMOVED: await add_sample_users(database_id, headers)
                    
                    return database_id
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create database: {response.status}")
                    print(f"Error: {error_text}")
                    return None
                    
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return None

async def update_env_file(database_id):
    """Add the database ID to the .env file."""
    try:
        env_path = Path('.env')
        
        # Read existing content
        existing_content = ""
        if env_path.exists():
            with open(env_path, 'r') as f:
                existing_content = f.read()
        
        # Check if the variable already exists
        if 'NOTION_GITHUB_USERS_DATABASE_ID' not in existing_content:
            # Add the new variable
            with open(env_path, 'a') as f:
                if existing_content and not existing_content.endswith('\n'):
                    f.write('\n')
# NOTION_REMOVED:                 f.write(f'NOTION_GITHUB_USERS_DATABASE_ID={database_id}\n')
            
            print("✅ Added NOTION_GITHUB_USERS_DATABASE_ID to .env file")
        else:
            print("⚠️ NOTION_GITHUB_USERS_DATABASE_ID already exists in .env file")
            print(f"   Please update it manually to: {database_id}")
            
    except Exception as e:
        print(f"⚠️ Could not update .env file: {e}")
# NOTION_REMOVED:         print(f"   Please add manually: NOTION_GITHUB_USERS_DATABASE_ID={database_id}")

# DEMO CODE REMOVED: async def add_sample_users(database_id, headers):
# DEMO CODE REMOVED: """Add sample GitHub users to the database."""
    
# DEMO CODE REMOVED: sample_users = [
        {
            "name": "Linus Torvalds",
            "username": "torvalds",
            "bio": "Creator of Linux and Git",
            "primary_language": "C++",
            "tags": ["Open Source", "Framework Author"],
            "priority": "High"
        },
        {
            "name": "Dan Abramov", 
            "username": "gaearon",
            "bio": "Co-author of Redux, Create React App. Working on React at Meta.",
            "primary_language": "JavaScript",
            "tags": ["Web Development", "Framework Author"],
            "priority": "High"
        },
        {
            "name": "Microsoft",
            "username": "microsoft",
# DEMO CODE REMOVED: "bio": "Open source projects and samples from Microsoft",
            "primary_language": "TypeScript",
            "tags": ["Company", "Open Source"],
            "priority": "Medium"
        },
        {
            "name": "OpenAI",
            "username": "openai",
            "bio": "OpenAI's official GitHub with AI tools and models",
            "primary_language": "Python",
            "tags": ["AI/ML", "Company"],
            "priority": "High"
        }
    ]
    
# DEMO CODE REMOVED: print("\n👥 Adding sample GitHub users...")
    
# DEMO CODE REMOVED: for user in sample_users:
        try:
            page_data = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": user["name"]}}]
                    },
                    "Username": {
                        "rich_text": [{"text": {"content": user["username"]}}]
                    },
                    "Profile URL": {
                        "url": f"https://github.com/{user['username']}"
                    },
                    "Bio": {
                        "rich_text": [{"text": {"content": user["bio"]}}]
                    },
                    "Primary Language": {
                        "select": {"name": user["primary_language"]}
                    },
                    "Account Type": {
                        "select": {"name": "Organization" if user["username"] in ["microsoft", "openai"] else "User"}
                    },
                    "Tags": {
                        "multi_select": [{"name": tag} for tag in user["tags"]]
                    },
                    "Process User": {
                        "checkbox": False
                    },
                    "Processing Status": {
                        "select": {"name": "Pending"}
                    },
                    "Priority": {
                        "select": {"name": user["priority"]}
                    },
                    "Notes": {
# DEMO CODE REMOVED: "rich_text": [{"text": {"content": f"Sample user: {user['bio']} - Check 'Process User' to import repositories"}}]
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    headers=headers,
                    json=page_data,
                    timeout=15
                ) as response:
                    if response.status == 200:
                        print(f"✅ Added: {user['name']} (@{user['username']})")
                    else:
                        error_text = await response.text()
                        print(f"⚠️ Failed to add {user['name']}: {error_text[:100]}")
                        
        except Exception as e:
            print(f"⚠️ Error adding {user['name']}: {e}")
    
    print()
    print("🎉 GitHub Users Database setup complete!")
    print()
    print("📋 What's Next:")
# DEMO CODE REMOVED: print("1. ✅ Database created with sample users")
    print("2. ✅ Database ID added to .env file")
    print("3. 🔍 Go to your Notion workspace and find 'GitHub Users' database")
    print("4. ☑️  Check 'Process User' for any user you want to process")
    print("5. 🚀 Run your main app - it will automatically import repositories")
    print("6. 🧪 Test first with: python test_github_users.py")

async def main():
    """Main function."""
    database_id = await find_existing_page_and_create_database()
    
    if database_id:
        print(f"\n🚀 SUCCESS! GitHub Users Database created: {database_id}")
        print("Your autonomous system is now ready to process GitHub users!")
    else:
        print("\n❌ Database creation failed")
        print("You may need to create it manually in Notion")

if __name__ == "__main__":
    asyncio.run(main())