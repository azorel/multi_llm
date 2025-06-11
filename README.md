# LifeOS Autonomous Agent System

A unified autonomous system that integrates YouTube channel processing, Notion-based life management, and intelligent automation into a single, powerful application.

## 🚀 Features

- **YouTube Channel Processing**: Automatically process YouTube channels marked in your Notion database
- **Today's CC Monitoring**: Real-time interaction monitoring for your daily command center
- **LifeOS Automation**: Intelligent task generation and life management automation
- **Background Services**: Continuous monitoring and automated workflows
- **Notion Integration**: Deep integration with your LifeOS Notion workspace

## 🎯 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your actual tokens and IDs
```

### 3. Run the System
```bash
python main.py
```

## ⚙️ Configuration

### Required Environment Variables
- `NOTION_API_TOKEN`: Your Notion integration token

### Optional Environment Variables
- `NOTION_CHANNELS_DATABASE_ID`: YouTube channels database ID
- `NOTION_KNOWLEDGE_DATABASE_ID`: Knowledge Hub database ID
- `TODAYS_CC_PAGE_ID`: Today's CC page ID for monitoring
- `GOOGLE_API_KEY`: Google API key for enhanced YouTube processing
- `GEMINI_API_KEY`: Gemini AI key for content analysis

## 🎛️ System Components

### YouTube Channel Processor
- Monitors Notion database for channels marked "Process Channel"
- Resolves channel IDs from URLs
- Imports recent videos to Knowledge Hub
- Supports both API and web scraping methods

### Today's CC Monitor
- Monitors checkbox interactions in your daily command center
- Processes quick actions automatically
- Logs activities and updates databases

### LifeOS Automation
- Runs periodic automation cycles
- Generates intelligent tasks
- Manages inventory and routines
- Optimizes system performance

### Background Services
- Continuous monitoring loops
- Statistics tracking
- Error handling and recovery
- System health monitoring

## 📊 System Status

The system provides real-time status including:
- Active components and features
- Processing statistics
- Uptime and performance metrics
- Error tracking and recovery

## 🛠️ Architecture

```
LifeOS Autonomous System
├── Notion Integration (Core)
├── YouTube Processor
├── Today's CC Monitor  
├── LifeOS Automation
└── Background Services
```

## 🔧 Development

### Project Structure
```
├── main.py              # Consolidated main application
├── requirements.txt     # Dependencies
├── .env.example        # Environment template
├── src/                # Legacy source code (archived)
├── archive/            # Archived utility scripts
└── README.md           # This file
```

### Adding Features
The main.py file is designed to be modular. Add new features by:
1. Creating a new component class
2. Adding initialization in `__init__`
3. Adding background monitoring if needed
4. Updating the status reporting

## 📋 Usage Examples

### Process YouTube Channels
1. Add YouTube channel URLs to your Notion channels database
2. Check "Process Channel" for any channel
3. System automatically processes and imports videos

### Use Today's CC
1. Create or update your Today's CC page
2. Check quick action boxes
3. System processes actions automatically

### Monitor System
- View logs for real-time status
- Check statistics in shutdown summary
- Monitor background service health

## 🚑 Troubleshooting

### Common Issues
1. **No Notion Token**: Set `NOTION_API_TOKEN` in .env
2. **Database Not Found**: Verify database IDs in configuration
3. **Connection Issues**: Check Notion API permissions
4. **Missing Dependencies**: Run `pip install -r requirements.txt`

### Debug Mode
Add debug logging by changing log level in main.py:
```python
logger.add(sys.stdout, level="DEBUG")
```

## 📚 Documentation

For detailed documentation on LifeOS concepts and Notion setup, see the archived documentation in the project directory.

## 🤝 Contributing

This is a personal life management system. The code is provided as-is for reference and learning purposes.

## 📄 License

Private use only. Not licensed for redistribution or commercial use.