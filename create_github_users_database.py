#!/usr/bin/env python3
"""Create GitHub Users Database in Notion automatically"""

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

async def create_github_users_database():
    """Create the GitHub Users database in Notion automatically."""
    
        return None
    
    headers = {
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    print("🚀 CREATING GITHUB USERS DATABASE")
    print("=" * 40)
    
    # First, let's find a suitable parent page by searching for existing databases
    print("🔍 Finding suitable parent page...")
    
    # Try to find the workspace or use search to find existing databases
    try:
        async with aiohttp.ClientSession() as session:
            # Search for existing databases to find workspace structure
            search_data = {
                "query": "database",
                "filter": {"property": "object", "value": "database"}
            }
            
            async with session.post(
                headers=headers,
                json=search_data,
                timeout=10
            ) as response:
                if response.status == 200:
                    search_results = await response.json()
                    databases = search_results.get('results', [])
                    
                    if databases:
                        # Use the parent of the first database we find
                        first_db = databases[0]
                        if first_db.get('parent', {}).get('type') == 'page_id':
                            parent_page_id = first_db['parent']['page_id']
                            print(f"✅ Found parent page ID: {parent_page_id}")
                        else:
                            # If no page parent, we'll need to create it differently
                            print("⚠️ No page parent found, will create as workspace database")
                            parent_page_id = None
                    else:
                        print("⚠️ No existing databases found")
                        parent_page_id = None
                else:
                    print(f"⚠️ Search failed: {response.status}")
                    parent_page_id = None
    
    except Exception as e:
        print(f"⚠️ Error searching for parent: {e}")
        parent_page_id = None
    
    # Database schema
    database_data = {
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
                "number": {
                    "format": "number"
                }
            },
            "Followers": {
                "number": {
                    "format": "number"
                }
            },
            "Following": {
                "number": {
                    "format": "number"
                }
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
                "number": {
                    "format": "number"
                }
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
    
    # Add parent if we found one
    if parent_page_id:
        database_data["parent"] = {
            "type": "page_id",
            "page_id": parent_page_id
        }
    else:
        # Create as workspace database (this might not work in all workspaces)
        database_data["parent"] = {
            "type": "workspace",
            "workspace": True
        }
    
    print("📝 Creating GitHub Users database...")
    
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
                    print()
                    
                    # Add to .env file automatically
                    await update_env_file(database_id)
                    
# DEMO CODE REMOVED: # Add sample users
# DEMO CODE REMOVED: await add_sample_users(database_id, headers)
                    
                    return database_id
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create database: {response.status}")
                    print(f"Error: {error_text}")
                    
                    # If workspace creation failed, let's try a different approach
                    if "parent" in error_text.lower():
                        print("\n🔄 Trying alternative creation method...")
                        return await create_database_alternative_method(headers)
                    
                    return None
                    
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return None

async def create_database_alternative_method(headers):
    """Alternative method: Create database in user's root workspace."""
    print("📝 Attempting to create database in workspace root...")
    
    # Simplified database creation without explicit parent
    database_data = {
        "title": [{"type": "text", "text": {"content": "GitHub Users"}}],
        "properties": {
            "Name": {"title": {}},
            "Username": {"rich_text": {}},
            "Profile URL": {"url": {}},
            "Process User": {"checkbox": {}},
            "Processing Status": {
                "select": {
                    "options": [
                        {"name": "Pending", "color": "yellow"},
                        {"name": "Processing", "color": "blue"},
                        {"name": "Completed", "color": "green"},
                        {"name": "Failed", "color": "red"}
                    ]
                }
            },
            "Primary Language": {
                "select": {
                    "options": [
                        {"name": "Python", "color": "blue"},
                        {"name": "JavaScript", "color": "yellow"},
                        {"name": "TypeScript", "color": "purple"},
                        {"name": "Other", "color": "gray"}
                    ]
                }
            },
            "Notes": {"rich_text": {}}
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
                    
                    print("✅ Simplified GitHub Users Database created!")
                    print(f"📋 Database ID: {database_id}")
                    
                    await update_env_file(database_id)
                    return database_id
                else:
                    error_text = await response.text()
                    print(f"❌ Alternative creation also failed: {response.status}")
                    print(f"Error: {error_text}")
                    print()
                    print("📋 Manual Setup Required:")
                    print("Please create the database manually in Notion and copy the ID")
                    return None
                    
    except Exception as e:
        print(f"❌ Alternative creation error: {e}")
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
            "account_type": "User",
            "priority": "High"
        },
        {
            "name": "Dan Abramov", 
            "username": "gaearon",
            "bio": "Co-author of Redux, Create React App. Working on React at Meta.",
            "primary_language": "JavaScript",
            "account_type": "User",
            "priority": "High"
        },
        {
            "name": "Microsoft",
            "username": "microsoft",
# DEMO CODE REMOVED: "bio": "Open source projects and samples from Microsoft",
            "primary_language": "TypeScript",
            "account_type": "Organization",
            "priority": "Medium"
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
                    "Primary Language": {
                        "select": {"name": user["primary_language"]}
                    },
                    "Account Type": {
                        "select": {"name": user["account_type"]}
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
                        "rich_text": [{"text": {"content": f"{user['bio']} - Check 'Process User' to import repositories"}}]
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
                        print(f"⚠️ Failed to add: {user['name']}")
                        
        except Exception as e:
            print(f"⚠️ Error adding {user['name']}: {e}")
    
    print()
    print("🎉 GitHub Users Database setup complete!")
    print()
    print("📋 Next Steps:")
    print("1. Go to your Notion workspace and find the 'GitHub Users' database")
    print("2. Check the 'Process User' checkbox for any user you want to process")
    print("3. Run your main app and it will automatically import their repositories")
    print("4. Test with: python test_github_users.py")

async def main():
    """Main function."""
    database_id = await create_github_users_database()
    
    if database_id:
        print(f"\n🚀 Database created successfully: {database_id}")
        print("Your autonomous system can now process GitHub users!")
    else:
        print("\n❌ Database creation failed")
        print("Please create the database manually using the GITHUB_USERS_DATABASE_GUIDE.md")

if __name__ == "__main__":
    asyncio.run(main())