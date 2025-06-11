# GitHub Repository Import Guide

## Overview
Your LifeOS system can now automatically import and analyze GitHub repositories into your Knowledge database. This feature allows you to:

- Import any GitHub user's repositories
- Analyze codebases automatically
- Store repository information in your Notion Knowledge database
- Get AI-powered summaries of code projects

## Quick Start

### 1. Interactive Import
Run the interactive importer:
```bash
source venv/bin/activate
python import_github_repos.py
```

### 2. Test the Feature
Test with a sample repository:
```bash
source venv/bin/activate
python test_github_import.py
```

## Usage Examples

### Import from Popular Developers
```
Username: torvalds      # Linux kernel creator
Username: gaearon       # React maintainer  
Username: tj            # Node.js libraries
Username: sindresorhus  # Popular npm packages
Username: microsoft     # Microsoft repositories
Username: google        # Google repositories
Username: openai        # OpenAI repositories
```

### Selection Examples
When selecting repositories to import:
```
1,3,5          # Import repositories 1, 3, and 5
1-10           # Import repositories 1 through 10
1,5-8,12       # Import 1, 5-8, and 12
all            # Import all repositories
quit           # Cancel import
```

## What Gets Imported

For each repository, the system analyzes and imports:

### Metadata
- Repository name and description
- Programming language and frameworks
- Stars, forks, size statistics
- Last updated date
- GitHub URL and clone URL

### Analysis
- **Project Type**: Detects if it's a web app, API, ML project, etc.
- **Complexity Level**: Low/Medium/High based on size and structure
- **Frameworks**: Automatically detects React, Django, Docker, etc.
- **Key Files**: Identifies README, package.json, requirements.txt, etc.

### AI Summary
- Comprehensive description of what the project does
- Key technical concepts and implementations
- Recommended learning approaches
- Actionable insights for developers

## Configuration

### Required Environment Variables
```bash
NOTION_API_TOKEN=your_notion_token
NOTION_KNOWLEDGE_DATABASE_ID=your_database_id
```

### Optional Environment Variables
```bash
GITHUB_TOKEN=your_github_token  # Increases rate limits
```

## Features

### Smart Analysis
- Detects programming languages and frameworks
- Identifies project types (web app, library, tool, etc.)
- Analyzes repository structure and complexity
- Extracts key technical information

### Content-Aware Import
- Creates proper hashtags based on technology stack
- Generates relevant action items for learning
- Provides context-appropriate assistant prompts
- Links to original repository for reference

### Integration with Knowledge Base
- Imports into existing Notion Knowledge database
- Uses same schema as YouTube videos for consistency
- Searchable and filterable alongside other content
- Ready for AI assistant analysis

## Rate Limits

### Without GitHub Token
- 60 requests per hour
- Suitable for small imports

### With GitHub Token
- 5,000 requests per hour
- Recommended for large imports

## Example Workflow

1. **Choose a Developer**: Pick someone whose code you want to study
2. **Run Import Script**: `python import_github_repos.py`
3. **Enter Username**: Type the GitHub username
4. **Review Repositories**: See all available repos with descriptions
5. **Select Projects**: Choose which ones to import
6. **Automatic Analysis**: System analyzes each repository
7. **Notion Import**: Repositories appear in your Knowledge database
8. **Study and Learn**: Use the imported information in your workflow

## Integration with Main App

The GitHub processor is integrated into your main autonomous system:

- **Component**: GitHub processor automatically initialized
- **Monitoring**: System health includes GitHub functionality
- **Self-Healing**: Automatic recovery on GitHub API failures
- **Logging**: All GitHub operations are logged and monitored

## Troubleshooting

### Common Issues

**No repositories found**
- Check username spelling
- Verify user has public repositories
- Check internet connection

**Import failed**
- Verify Notion API token is valid
- Check Knowledge database ID is correct
- Ensure database permissions allow page creation

**Rate limit exceeded**
- Add GitHub token to increase limits
- Wait for rate limit reset (1 hour)
- Import fewer repositories at once

### Debug Mode
Add debug logging to see detailed processing:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Usage

### Custom Analysis
Modify `github_repo_processor.py` to add custom analysis rules:
- Additional framework detection
- Custom project type classification
- Enhanced complexity assessment
- Domain-specific analysis

### Batch Processing
For large-scale imports, consider:
- Using GitHub token for higher rate limits
- Processing repositories in smaller batches
- Adding delays between imports
- Monitoring system resources

### Integration Examples
Use imported repositories for:
- Code learning and reference
- Architecture pattern analysis
- Technology stack research
- Open source project discovery
- Team knowledge sharing

## Next Steps

1. Test the feature with a few repositories
2. Import repositories from developers you follow
3. Use the imported knowledge in your AI workflows
4. Customize analysis rules for your specific needs
5. Integrate with your existing knowledge management system