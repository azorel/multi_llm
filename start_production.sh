#!/bin/bash
# Production startup script for autonomous multi-LLM agent system

echo "🚀 Starting Autonomous Multi-LLM Agent System"
echo "============================================"

# Change to project directory
cd /home/ikino/dev/autonomous-multi-llm-agent

# Check for virtual environment
if [ -d "venv" ]; then
    echo "✅ Using virtual environment"
    source venv/bin/activate
else
    echo "⚠️ No virtual environment found"
fi

# Export API keys if .env exists
if [ -f ".env" ]; then
    echo "✅ Loading environment variables"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check critical API keys
echo "🔑 Checking API keys..."
[ -n "$NOTION_API_KEY" ] && echo "  ✅ Notion API key found" || echo "  ⚠️ Notion API key missing"
[ -n "$OPENAI_API_KEY" ] && echo "  ✅ OpenAI API key found" || echo "  ⚠️ OpenAI API key missing"
[ -n "$ANTHROPIC_API_KEY" ] && echo "  ✅ Anthropic API key found" || echo "  ⚠️ Anthropic API key missing"

# Start the system
echo ""
echo "🔄 Starting autonomous system..."
echo "Press Ctrl+C to stop"
echo ""

# Run with proper error handling
python run.py --mode autonomous --environment development 2>&1 | tee -a system_startup.log