#!/usr/bin/env python3
"""
Refactored Local Notion-like Web Application
===========================================

A complete web application that looks and feels like Notion.
Includes all your databases, Today's CC, and automation features.

GitHub and OpenAI functionality has been disabled.
"""

import os
import sys
import logging
from flask import Flask
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Import database
from database import NotionLikeDatabase

# Import blueprints
from routes.teams import teams_bp
from routes.dashboard import dashboard_bp
from routes.business import business_bp
from routes.code_analysis import code_analysis_bp
from routes.analytics import analytics_bp
from routes.social_media import social_media_bp

# Import automation routes
try:
    from routes.automation import automation_bp, automation_dashboard_bp
    automation_available = True
    logger.info("✅ Automation routes imported")
except ImportError as e:
    automation_available = False
    automation_dashboard_bp = None
    logger.warning(f"⚠️ Automation routes not available: {e}")

# Import TDD routes
try:
    from routes.tdd import tdd_bp
    tdd_available = True
    logger.info("✅ TDD routes imported")
except ImportError as e:
    tdd_available = False
    tdd_bp = None
    logger.warning(f"⚠️ TDD routes not available: {e}")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize database
db = NotionLikeDatabase()
logger.info("✅ Database initialized")

# Initialize agent performance monitoring
try:
    from agent_performance_monitor import performance_tracker, integrate_with_orchestrator
    integrate_with_orchestrator()
    logger.info("✅ Agent performance monitoring initialized")
except Exception as e:
    logger.warning(f"⚠️ Agent performance monitoring not available: {e}")

# Register blueprints
app.register_blueprint(teams_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(business_bp)
app.register_blueprint(code_analysis_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(social_media_bp)

# Register automation blueprints if available
if automation_available:
    app.register_blueprint(automation_bp)
    app.register_blueprint(automation_dashboard_bp)
    logger.info("✅ Automation blueprints registered")

# Register TDD blueprint if available
if tdd_available:
    app.register_blueprint(tdd_bp)
    logger.info("✅ TDD blueprint registered")

logger.info("✅ All blueprints registered")

# Note: GitHub functionality has been disabled
# The following routes have been removed:
# - /github-users
# - /github-repos  
# - /add-github-repo
# - /process-github-user
# GitHub processing imports have been removed

# Note: OpenAI functionality has been disabled
# OpenAI provider references have been removed from the database
# and replaced with Anthropic/Local alternatives

def main():
    """Run the web server."""
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 Starting web server on port {port}")
    logger.info("📝 GitHub functionality: DISABLED")
    logger.info("🤖 OpenAI functionality: DISABLED")
    logger.info(f"🤖 Automation API: {'ENABLED' if automation_available else 'DISABLED'}")
    logger.info(f"🐛 Debug mode: {debug}")
    
    # Start the server
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=debug
    )

if __name__ == '__main__':
    main()