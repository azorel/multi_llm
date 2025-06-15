# Autonomous Multi-LLM Agent System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Advanced multi-agent orchestration system with vanlife & RC social media automation, GitHub integration, and Claude+Gemini optimization

## 🚀 Features

- Enhanced Multi-Agent Orchestrator
- Vanlife & RC Truck Social Media Automation
- GitHub Repository Integration
- Content Analysis with AI
- Automated Caption & Hashtag Generation
- Revenue Tracking System
- Real-time Agent Performance Monitoring
- TDD System Integration

## 🛠️ Technologies

Python, Flask, SQLite, Claude API, Gemini API, GitHub API

## 📋 Prerequisites

- Python 3.8 or higher
- Git
- GitHub Personal Access Token
- Anthropic API Key (Claude)
- Google API Key (Gemini)

## ⚡ Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/azorel/multi_llm.git
   cd multi_llm
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the application:**
   ```bash
   python3 -m flask --app web_server run --port=8082
   ```

5. **Access the dashboard:**
   ```
   http://localhost:8082
   ```

## 🏗️ System Architecture

### Core Components

- **Enhanced Multi-Agent Orchestrator**: Claude + Gemini optimized agent coordination
- **Social Media Automation**: Vanlife & RC truck content optimization
- **GitHub Integration**: Repository analysis and automated workflows
- **Content Analysis Engine**: AI-powered content classification and optimization
- **Revenue Tracking**: Monetization analytics for van life income generation

### Agent Types

1. **Senior Code Developer** - Python development and optimization
2. **System Analyst** - Architecture and system design
3. **API Integration Specialist** - External service integration
4. **Database Specialist** - Data management and optimization
5. **Content Processor** - Media analysis and optimization
6. **Error Diagnostician** - System debugging and repair
7. **Template Fixer** - UI/UX and template management
8. **Web Tester** - Application testing and validation

## 📱 Web Interface

- **Dashboard**: `/` - Main system overview
- **Social Media**: `/social-media` - Content automation
- **GitHub Users**: `/github-users` - Repository management
- **Analytics**: `/analytics` - Performance metrics
- **Code Analysis**: `/code-analysis` - Repository insights

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Core APIs
ANTHROPIC_API_KEY=your_claude_key
GOOGLE_API_KEY=your_gemini_key
GITHUB_TOKEN=your_github_token

# GitHub Integration
GITHUB_DEFAULT_OWNER=azorel
GITHUB_DEFAULT_REPO=multi_llm

# Database
DATABASE_URL=sqlite:///lifeos_local.db
```

### Social Media Automation

The system includes specialized automation for:
- **Vanlife Content**: Trail exploration, camping setups, van tours
- **RC Truck Content**: Axial Racing, Vanquish brands, technical crawling
- **Location Focus**: Southern BC trails and outdoor adventures
- **Brand Voice**: Relaxed traveler exploring new trails

## 📊 Database Schema

- **social_media_posts**: Content analysis and posting data
- **trail_locations**: Southern BC trail database
- **rc_brands**: RC truck brand and model detection
- **revenue_tracking**: Monetization and income analytics
- **hashtag_performance**: Social media optimization data

## 🤖 Agent Orchestration

### Task Execution

```python
from enhanced_orchestrator_claude_gemini import enhanced_orchestrator, AgentType

# Add a task
task_id = enhanced_orchestrator.add_task(
    "Analyze repository structure",
    "Perform comprehensive analysis of codebase...",
    AgentType.SYSTEM_ANALYST,
    TaskPriority.HIGH
)

# Execute tasks
results = await enhanced_orchestrator.execute_tasks_parallel([task])
```

### Provider Load Balancing

- **Claude**: 50% - Code analysis, system design
- **Gemini**: 50% - Content processing, image analysis
- Automatic fallback on provider failure

## 📈 Performance Monitoring

- Real-time agent performance tracking
- Task execution analytics
- Error detection and recovery
- System health monitoring

## 🔄 Automated Workflows

- **Repository Discovery**: Daily GitHub repository scanning
- **Content Analysis**: AI-powered media processing
- **Performance Optimization**: Continuous system improvement
- **Error Recovery**: Autonomous problem resolution

## 📝 Development

### Testing

```bash
# Run content analyzer tests
python3 test_social_media_system.py

# Test GitHub integration
python3 github_integration_status.py

# Validate API tokens
python3 test_github_token.py
```

### TDD System

The project includes a Test-Driven Development system:

```python
from tdd_system import tdd_system

# Create TDD cycle
cycle_id = tdd_system.create_tdd_cycle("Feature Name", "Description")
result = tdd_system.complete_tdd_cycle(cycle_id, "Implementation details")
```

## 🛡️ Security

- API keys stored in environment variables
- No sensitive data in repository
- Secure GitHub token validation
- Rate limiting on all external APIs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create a GitHub issue
- Check the documentation
- Review the system logs

## 🗺️ Roadmap

- [ ] YouTube Data API integration
- [ ] Instagram Graph API integration
- [ ] Advanced revenue analytics
- [ ] Mobile app companion
- [ ] Voice command integration
- [ ] Advanced AI model fine-tuning

---

**Generated by Autonomous Multi-LLM Agent System v1.0.0**

*Building the future of intelligent automation, one agent at a time.* 🤖✨
