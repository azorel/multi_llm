# GitHub Users Database Setup Guide

## Overview

This guide will help you set up a **GitHub Users** database in Notion that works exactly like your YouTube Channels database. You'll be able to:

- Add GitHub users/organizations you want to track
- Use a **"Process User"** checkbox to trigger repository imports
- Automatically import selected repositories to your Knowledge database
- Track processing status and statistics

## Database Schema

Create a new database in Notion called **"GitHub Users"** with these properties:

### Core Properties
| Property Name | Type | Description |
|---------------|------|-------------|
| **Name** | Title | Display name (e.g., "Linus Torvalds") |
| **Username** | Text | GitHub username (e.g., "torvalds") |
| **Profile URL** | URL | GitHub profile link |
| **Public Repos** | Number | Number of public repositories |
| **Followers** | Number | Follower count |
| **Following** | Number | Following count |

### Profile Information
| Property Name | Type | Description |
|---------------|------|-------------|
| **Bio** | Text | User's GitHub bio |
| **Company** | Text | Company/organization |
| **Location** | Text | Location |
| **Website** | URL | Personal website |

### Classification
| Property Name | Type | Options |
|---------------|------|---------|
| **Primary Language** | Select | Python, JavaScript, TypeScript, Java, C++, Go, Rust, C#, PHP, Ruby, Other |
| **Account Type** | Select | User, Organization, Bot |
| **Tags** | Multi-select | AI/ML, Web Development, Open Source, Framework Author, Company, Influencer, Tutorial Creator, DevOps, Mobile Development, Game Development |

### Processing Control
| Property Name | Type | Description |
|---------------|------|-------------|
| **Process User** | Checkbox | ✅ Check this to import repositories |
| **Last Processed** | Date | When repositories were last imported |
| **Repos Imported** | Number | Count of imported repositories |
| **Processing Status** | Select | Pending, Processing, Completed, Failed, Skipped |
| **Priority** | Select | High, Medium, Low |
| **Notes** | Text | Additional notes |

## Quick Setup Steps

### 1. Create the Database

1. **Go to your Notion workspace**
2. **Create a new database** called "GitHub Users"
3. **Add all properties** from the schema above
4. **Configure select options** as specified

### 2. Get Database ID

1. **Open the database** in Notion
2. **Copy the database ID** from the URL:
   ```
   https://notion.so/your-workspace/database-id?v=view-id
                                   ↑ This part
   ```

### 3. Update Configuration

Add to your `.env` file:
```bash
NOTION_GITHUB_USERS_DATABASE_ID=your_database_id_here
```

### 4. Add GitHub Users

Add users you want to track. Here are some popular ones to start with:

#### Framework/Library Authors
- **Linus Torvalds** (`torvalds`) - Linux, Git
- **Dan Abramov** (`gaearon`) - React, Redux
- **Evan You** (`yyx990803`) - Vue.js
- **TJ Holowaychuk** (`tj`) - Express.js
- **Rich Harris** (`Rich-Harris`) - Svelte

#### Open Source Contributors
- **Sindre Sorhus** (`sindresorhus`) - Popular npm packages
- **Kent C. Dodds** (`kentcdodds`) - Testing utilities
- **Addy Osmani** (`addyosmani`) - Google Chrome team

#### Organizations
- **Microsoft** (`microsoft`) - .NET, TypeScript, VSCode
- **Google** (`google`) - Angular, Go, TensorFlow
- **Facebook** (`facebook`) - React, React Native
- **Vercel** (`vercel`) - Next.js, hosting
- **Netflix** (`Netflix`) - Microservices tools

#### AI/ML
- **OpenAI** (`openai`) - GPT, AI tools
- **Hugging Face** (`huggingface`) - Transformers
- **Anthropic** (`anthropics`) - Claude

## Usage Workflow

### 1. Add Users
1. **Create new entries** in your GitHub Users database
2. **Fill in basic info**: Name, Username, Profile URL
3. **Set tags and priority** based on your interests
4. **Add notes** about why you want to track them

### 2. Process Repositories
1. **Check "Process User"** for users you want to import
2. **Your autonomous system** will automatically:
   - Fetch their repositories
   - Analyze each repository
   - Import selected repos to Knowledge database
   - Update processing status

### 3. Monitor Progress
- **Processing Status** shows current state
- **Repos Imported** counts successful imports
- **Last Processed** tracks when it was done

## Integration with Main App

### Configuration

Update your main app configuration to include the GitHub Users processor:

```python
# In main.py configuration
'github_users_db_id': os.getenv('NOTION_GITHUB_USERS_DATABASE_ID'),
```

### Automatic Processing

The system will:
1. **Monitor the checkbox** "Process User"
2. **Fetch user's repositories** when checked
3. **Display repository list** for selection
4. **Import selected repositories** to Knowledge database
5. **Uncheck the box** and update status when complete

## Sample Database Entries

Here's how to set up some sample entries:

### Linus Torvalds
- **Name**: Linus Torvalds
- **Username**: torvalds
- **Profile URL**: https://github.com/torvalds
- **Primary Language**: C++
- **Account Type**: User
- **Tags**: Open Source, Framework Author
- **Priority**: High
- **Notes**: Creator of Linux kernel and Git

### Microsoft
- **Name**: Microsoft
- **Username**: microsoft
- **Profile URL**: https://github.com/microsoft
- **Primary Language**: C#
- **Account Type**: Organization
- **Tags**: Company, Open Source
- **Priority**: Medium
- **Notes**: Official Microsoft open source projects

## Advanced Features

### Batch Processing
- Set multiple users to "Process User"
- System processes them in priority order
- High priority users processed first

### Smart Repository Selection
- System shows repository list with descriptions
- You select which ones to import
- Focuses on most popular/recent repositories

### Automatic Categorization
- Repositories categorized by language and type
- AI-powered summaries and analysis
- Proper tagging for easy discovery

### Progress Tracking
- Real-time status updates
- Error handling and retry logic
- Statistics on import success rates

## Maintenance

### Regular Updates
- **Review processing status** weekly
- **Add new interesting users** as you discover them
- **Update priorities** based on your current interests

### Database Cleanup
- **Archive completed entries** older than 6 months
- **Remove users** you're no longer interested in
- **Update tags** as your focus areas change

## Troubleshooting

### Common Issues

**User not processing**
- Check "Process User" is checked
- Verify username is correct
- Ensure GitHub user exists and has public repos

**No repositories imported**
- User might have no public repositories
- Check GitHub API rate limits
- Verify Notion database permissions

**Processing stuck**
- Check system logs for errors
- Restart the autonomous system
- Verify all API tokens are valid

### Debug Mode

Enable detailed logging in your processor:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

1. **Set up the database** with the schema above
2. **Add your first users** (start with 3-5 interesting ones)
3. **Test the processing** by checking one user's box
4. **Monitor the results** in your Knowledge database
5. **Scale up** by adding more users over time

This gives you a powerful way to systematically discover and import interesting code repositories from developers you follow!