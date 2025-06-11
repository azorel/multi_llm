#!/usr/bin/env python3
"""Setup GitHub Users Database in Notion"""

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
    """Create the GitHub Users database in Notion."""
    
        return
    
    headers = {
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    # Database schema
    database_data = {
        "parent": {
            "type": "page_id",
            "page_id": "your_parent_page_id_here"  # You'll need to replace this
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
            },
            "Created Date": {
                "created_time": {}
            },
            "Last Modified": {
                "last_edited_time": {}
            }
        }
    }
    
    print("🐙 Creating GitHub Users Database in Notion...")
    print("=" * 50)
    
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
                    print("🔧 Next Steps:")
                    print("1. Add this to your .env file:")
# NOTION_REMOVED:                     print(f"   NOTION_GITHUB_USERS_DATABASE_ID={database_id}")
                    print()
                    print("2. Update your main.py configuration to use this database")
                    print("3. Start adding GitHub users with the 'Process User' checkbox")
                    
                    return database_id
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create database: {response.status}")
                    print(f"Error: {error_text}")
                    return None
                    
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return None

# DEMO CODE REMOVED: async def add_sample_users(database_id: str):
# DEMO CODE REMOVED: """Add some sample GitHub users to the database."""
    
    headers = {
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
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
            "tags": ["Web Development", "Framework Author", "Tutorial Creator"],
            "priority": "High"
        },
        {
            "name": "Sindre Sorhus",
            "username": "sindresorhus",
            "bio": "Full-Time Open-Sourcerer",
            "primary_language": "JavaScript",
            "tags": ["Open Source", "Web Development"],
            "priority": "Medium"
        },
        {
            "name": "TJ Holowaychuk",
            "username": "tj",
            "bio": "Founder of Apex, creator of Express.js",
            "primary_language": "Go",
            "tags": ["Web Development", "Framework Author"],
            "priority": "High"
        },
        {
            "name": "Microsoft",
            "username": "microsoft",
# DEMO CODE REMOVED: "bio": "Open source projects and samples from Microsoft",
            "primary_language": "C#",
            "tags": ["Company", "Open Source"],
            "priority": "Medium"
        }
    ]
    
# DEMO CODE REMOVED: print("👥 Adding sample GitHub users...")
    
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
                        "select": {"name": "User" if user["username"] != "microsoft" else "Organization"}
                    },
                    "Tags": {
                        "multi_select": [{"name": tag} for tag in user["tags"]]
                    },
                    "Priority": {
                        "select": {"name": user["priority"]}
                    },
                    "Process User": {
                        "checkbox": False  # Set to True when you want to process
                    },
                    "Processing Status": {
                        "select": {"name": "Pending"}
                    },
                    "Notes": {
# DEMO CODE REMOVED: "rich_text": [{"text": {"content": f"Sample user entry for {user['name']} - check 'Process User' to import repositories"}}]
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
                        print(f"❌ Failed to add: {user['name']}")
                        
        except Exception as e:
            print(f"❌ Error adding {user['name']}: {e}")

async def main():
    """Main setup function."""
    print("🚀 GITHUB USERS DATABASE SETUP")
    print("=" * 40)
    print()
    print("This will create a new 'GitHub Users' database in your Notion workspace.")
    print("⚠️  You need to specify a parent page ID in the script.")
    print()
    
    # Check if we should proceed
    proceed = input("Do you want to create the database? (y/N): ").strip().lower()
    if proceed != 'y':
        print("❌ Setup cancelled")
        return
    
    # Get parent page ID
    print()
    print("📋 You need a parent page ID where the database will be created.")
    print("Find this in your Notion page URL: notion.so/your-page-id")
    parent_page_id = input("Enter parent page ID: ").strip()
    
    if not parent_page_id:
        print("❌ No parent page ID provided")
        return
    
    # Update the database data with the parent page ID
    # (This is a bit hacky, but works for this setup script)
    print(f"📝 Using parent page ID: {parent_page_id}")
    
    # For now, let's create a simpler version that can be manually configured
    print()
    print("📋 Manual Setup Instructions:")
    print("=" * 30)
    print()
    print("1. Go to your Notion workspace")
    print("2. Create a new database called 'GitHub Users'")
    print("3. Add these properties:")
    print()
    
    properties = [
        ("Name", "Title"),
        ("Username", "Text"),
        ("Profile URL", "URL"),
        ("Public Repos", "Number"),
        ("Followers", "Number"),
        ("Following", "Number"),
        ("Bio", "Text"),
        ("Company", "Text"),
        ("Location", "Text"),
        ("Website", "URL"),
        ("Primary Language", "Select"),
        ("Account Type", "Select"),
        ("Process User", "Checkbox"),
        ("Last Processed", "Date"),
        ("Repos Imported", "Number"),
        ("Processing Status", "Select"),
        ("Priority", "Select"),
        ("Tags", "Multi-select"),
        ("Notes", "Text")
    ]
    
    for prop_name, prop_type in properties:
        print(f"   • {prop_name} ({prop_type})")
    
    print()
    print("4. Copy the database ID from the URL")
# NOTION_REMOVED:     print("5. Add to .env: NOTION_GITHUB_USERS_DATABASE_ID=your_database_id")
    print()
    print("📚 See GITHUB_USERS_DATABASE_GUIDE.md for complete setup instructions")

if __name__ == "__main__":
    asyncio.run(main())