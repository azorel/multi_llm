# Agent Performance Analytics System

## Overview

A comprehensive agent performance monitoring and analytics system for the autonomous multi-LLM agent system. This system provides real-time monitoring, performance tracking, alerting, and optimization recommendations for all agent operations.

## Features

### 🔍 Performance Tracking Engine
- **Real-time metrics collection** - Monitors task execution, response times, costs, and success rates
- **Multi-provider tracking** - Tracks performance across Anthropic, OpenAI, and Gemini providers
- **Automatic integration** - Seamlessly integrates with the real agent orchestrator
- **Historical data** - Maintains 30 days of detailed performance history

### 📊 Analytics Dashboard
- **Web-based interface** - Modern, responsive dashboard at `/analytics-dashboard`
- **Real-time charts** - Live performance trends and provider distribution charts
- **Agent performance table** - Detailed view of individual agent metrics
- **Provider health monitoring** - Real-time status of all LLM providers

### 🚨 Alert System
- **Automatic alerts** - Detects performance issues and cost spikes
- **Configurable thresholds** - Customizable alert levels for different metrics
- **Smart remediation** - Automatic load balancing and provider switching
- **Real-time notifications** - Immediate alerts for critical issues

### 🎯 Optimization Engine
- **Load balancing** - Dynamic provider weight adjustment based on performance
- **Cost optimization** - Automatic switching to cost-effective providers
- **Performance tuning** - Agent reassignment based on success rates
- **Intelligent recommendations** - AI-powered optimization suggestions

## Database Schema

The system creates the following analytics tables:

### Performance Metrics
```sql
performance_metrics (
    metric_id TEXT UNIQUE,
    agent_id TEXT,
    agent_type TEXT,
    metric_type TEXT,
    value REAL,
    timestamp DATETIME,
    provider TEXT
)
```

### Agent Performance Summary
```sql
agent_performance_summary (
    agent_id TEXT UNIQUE,
    total_tasks INTEGER,
    successful_tasks INTEGER,
    success_rate REAL,
    avg_response_time REAL,
    total_cost REAL
)
```

### Task Execution Timeline
```sql
task_execution_timeline (
    task_id TEXT,
    agent_id TEXT,
    duration_ms INTEGER,
    tokens_used INTEGER,
    cost REAL,
    success BOOLEAN
)
```

### Alerts
```sql
alerts (
    alert_id TEXT UNIQUE,
    level TEXT,
    title TEXT,
    description TEXT,
    agent_id TEXT,
    timestamp DATETIME
)
```

## API Endpoints

### Dashboard Data
```
GET /api/analytics/dashboard-data
```
Returns comprehensive dashboard data including metrics, agents, providers, and alerts.

### Performance Overview
```
GET /api/analytics/overview
```
Returns system-wide performance summary and trends.

### Agent Details
```
GET /api/analytics/agents
```
Returns detailed performance data for all agents.

### Provider Health
```
GET /api/analytics/providers
```
Returns provider performance and load balancing statistics.

### System Insights
```
GET /api/analytics/insights
```
Returns AI-powered optimization recommendations and system insights.

### Generate Test Data
```
GET /api/analytics/test-data
```
Generates sample performance data for testing (development only).

### Health Check
```
GET /api/analytics/health
```
Returns system health status and connectivity information.

## Key Components

### 1. PerformanceTracker (`agent_performance_monitor.py`)
- Core tracking engine
- Database operations
- Metric collection and storage
- Alert generation

### 2. EnhancedOrchestrationMonitor (`agent_orchestrator_integration.py`)
- Real-time monitoring
- Load balancing optimization
- Automatic remediation
- System insights generation

### 3. Analytics Routes (`routes/analytics.py`)
- Flask API endpoints
- Data formatting and serialization
- Error handling

### 4. Analytics Dashboard (`templates/analytics_dashboard.html`)
- Modern web interface
- Interactive charts (Chart.js)
- Real-time data updates
- Responsive design

## Performance Metrics Tracked

### Agent Metrics
- **Task Completion Rate** - Percentage of successfully completed tasks
- **Response Time** - Average time to complete tasks (milliseconds)
- **Token Usage** - Total tokens consumed per task
- **Cost** - Dollar cost per task and total cost
- **Error Rate** - Percentage of failed tasks
- **Files Created/Modified** - Number of files affected by tasks

### Provider Metrics
- **Request Distribution** - Load balancing across providers
- **Success Rate** - Provider reliability metrics
- **Average Response Time** - Provider speed comparison
- **Cost Analysis** - Cost per request by provider
- **Error Tracking** - Provider-specific error rates

### System Metrics
- **Overall Success Rate** - System-wide task success percentage
- **Total Cost** - Cumulative system costs
- **Active Agents** - Number of currently working agents
- **Queue Length** - Pending tasks in the system
- **Throughput** - Tasks completed per hour

## Alert Types

### Warning Alerts
- **High Response Time** - Agent taking longer than 30 seconds
- **Cost Spike** - Task cost 3x higher than average
- **Provider Issues** - Provider error rate above 20%

### Critical Alerts
- **High Error Rate** - Agent success rate below 70%
- **Queue Backlog** - Many pending tasks with no active agents
- **System Cost Threshold** - Total costs exceeding $50

### Info Alerts
- **Performance Improvements** - Agents performing better than baseline
- **Optimization Opportunities** - Recommendations for efficiency gains

## Optimization Features

### Automatic Load Balancing
- Dynamic provider weight adjustment
- Performance-based routing
- Failover handling
- Cost optimization

### Smart Agent Management
- Agent reassignment based on performance
- Provider switching for failing agents
- Workload distribution optimization

### Cost Control
- Real-time cost tracking
- Budget alerts and warnings
- Cost-effective provider recommendations
- Token usage optimization

## Installation and Setup

### 1. Dependencies
The system requires:
- Flask (web framework)
- SQLite3 (database)
- Chart.js (frontend charts)
- Font Awesome (icons)

### 2. Integration
The analytics system automatically integrates when the web server starts:
```python
from agent_performance_monitor import performance_tracker, integrate_with_orchestrator
integrate_with_orchestrator()
```

### 3. Access the Dashboard
Navigate to `http://localhost:8081/analytics-dashboard` to view the analytics interface.

## Configuration

### Alert Thresholds
```python
alert_thresholds = {
    'error_rate': 30.0,           # Percentage
    'response_time': 30000.0,     # Milliseconds
    'cost_spike': 5.0,            # Dollar amount spike
    'token_spike': 10000          # Token usage spike
}
```

### Optimization Settings
```python
optimization_thresholds = {
    'high_error_rate': 25.0,      # Percentage
    'slow_response_time': 20000.0, # Milliseconds
    'high_cost_per_task': 1.0,    # Dollars
    'provider_failure_rate': 40.0 # Percentage
}
```

## Usage Examples

### Generate Test Data
```bash
curl http://localhost:8081/api/analytics/test-data
```

### Get Dashboard Data
```bash
curl http://localhost:8081/api/analytics/dashboard-data
```

### Check System Health
```bash
curl http://localhost:8081/api/analytics/health
```

### Get Optimization Insights
```bash
curl http://localhost:8081/api/analytics/insights
```

## Monitoring and Maintenance

### Background Processes
- **Hourly Aggregation** - Summarizes performance data every hour
- **Data Cleanup** - Removes data older than 30 days
- **Alert Processing** - Continuously monitors for performance issues
- **Load Balancing** - Adjusts provider weights every minute

### Database Maintenance
- Automatic index optimization
- Periodic data compression
- Performance metric cleanup
- Alert history management

## Security Considerations

- All API endpoints validate input data
- Database operations use parameterized queries
- No sensitive data is logged or exposed
- Provider API keys are not tracked in analytics

## Performance Impact

The analytics system is designed to have minimal impact on agent performance:
- **Async processing** - Metrics collection doesn't block agent execution
- **Efficient storage** - Optimized database schema and indexes
- **Background aggregation** - Heavy processing done in background threads
- **Caching** - Frequently accessed data is cached in memory

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check if SQLite database file is writable
   - Verify disk space availability

2. **Missing Metrics**
   - Ensure orchestrator integration is active
   - Check that agents are properly initialized

3. **Dashboard Not Loading**
   - Verify Flask server is running
   - Check browser console for JavaScript errors

4. **Alert System Not Working**
   - Confirm alert thresholds are properly configured
   - Check background monitoring thread status

### Debug Commands
```bash
# Test performance tracker
python3 agent_performance_monitor.py

# Test orchestration integration
python3 agent_orchestrator_integration.py

# Check database tables
sqlite3 agent_analytics.db ".tables"

# View recent metrics
sqlite3 agent_analytics.db "SELECT * FROM performance_metrics ORDER BY timestamp DESC LIMIT 10;"
```

## Future Enhancements

### Planned Features
- **Machine Learning** - Predictive performance modeling
- **Advanced Alerting** - Slack/email notifications
- **Custom Dashboards** - User-configurable views
- **API Rate Limiting** - Provider usage optimization
- **Performance Benchmarking** - Agent comparison tools

### Integration Opportunities
- **Monitoring Tools** - Prometheus/Grafana integration
- **Cloud Providers** - AWS CloudWatch integration
- **CI/CD Pipelines** - Performance regression detection
- **Business Intelligence** - Data export capabilities

## Support

For issues or questions about the analytics system:
1. Check the troubleshooting section above
2. Review system logs for error messages
3. Test individual components with provided debug commands
4. Verify all dependencies are properly installed

The analytics system provides comprehensive insights into agent performance and automatically optimizes the system for better efficiency, cost-effectiveness, and reliability.