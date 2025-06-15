#!/usr/bin/env python3
"""
Analytics Routes
================

Flask routes for the agent performance analytics dashboard.
Provides API endpoints and web interface for performance monitoring.
"""

from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timezone, timedelta
import json
from typing import Dict, Any
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__)

# Import the performance tracker
try:
    from agent_performance_monitor import performance_tracker
    PERFORMANCE_TRACKING_AVAILABLE = True
except ImportError:
    logger.warning("Performance tracking not available")
    PERFORMANCE_TRACKING_AVAILABLE = False

@analytics_bp.route('/analytics-dashboard')
def analytics_dashboard():
    """Main analytics dashboard page"""
    return render_template('analytics_dashboard.html')

@analytics_bp.route('/api/analytics/overview')
def analytics_overview():
    """Get overall analytics overview"""
    try:
        if not PERFORMANCE_TRACKING_AVAILABLE:
            return jsonify({
                'error': 'Performance tracking not available',
                'message': 'The performance monitoring system is not initialized'
            }), 503
        
        # Get performance summary
        summary = performance_tracker.get_agent_performance_summary()
        
        # Get recent trends
        trends = performance_tracker.get_performance_trends(hours=24)
        
        return jsonify({
            'success': True,
            'summary': summary,
            'trends': trends,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get analytics overview: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/agents')
def analytics_agents():
    """Get detailed agent performance data"""
    try:
        if not PERFORMANCE_TRACKING_AVAILABLE:
            return jsonify({
                'error': 'Performance tracking not available'
            }), 503
        
        summary = performance_tracker.get_agent_performance_summary()
        
        # Format agent data for the dashboard
        agents_data = []
        for agent in summary.get('agent_stats', []):
            agents_data.append({
                'id': agent['agent_id'],
                'name': agent['agent_id'].replace('_', ' ').title(),
                'type': agent['agent_type'],
                'status': 'active' if agent['last_active'] else 'inactive',
                'total_tasks': agent['total_tasks'],
                'success_rate': agent['success_rate'],
                'avg_response_time': agent['avg_response_time'],
                'total_cost': agent['total_cost'],
                'cost_per_task': agent['cost_per_task'],
                'tokens_per_task': agent['tokens_per_task'],
                'last_active': agent['last_active']
            })
        
        return jsonify({
            'success': True,
            'agents': agents_data,
            'total_agents': len(agents_data),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get agent analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/providers')
def analytics_providers():
    """Get provider performance and load balancing data"""
    try:
        if not PERFORMANCE_TRACKING_AVAILABLE:
            return jsonify({
                'error': 'Performance tracking not available'
            }), 503
        
        summary = performance_tracker.get_agent_performance_summary()
        provider_stats = summary.get('provider_stats', {})
        
        # Format provider data
        providers_data = []
        for provider, stats in provider_stats.items():
            error_rate = (stats['errors'] / max(stats['requests'], 1)) * 100
            success_rate = 100 - error_rate
            
            providers_data.append({
                'name': provider,
                'requests': stats['requests'],
                'errors': stats['errors'],
                'success_rate': success_rate,
                'error_rate': error_rate,
                'total_cost': stats['total_cost'],
                'avg_response_time': stats['avg_response_time'],
                'status': 'healthy' if error_rate < 10 else 'warning' if error_rate < 30 else 'critical'
            })
        
        return jsonify({
            'success': True,
            'providers': providers_data,
            'total_providers': len(providers_data),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get provider analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/alerts')
def analytics_alerts():
    """Get current alerts and notifications"""
    try:
        if not PERFORMANCE_TRACKING_AVAILABLE:
            return jsonify({
                'error': 'Performance tracking not available'
            }), 503
        
        summary = performance_tracker.get_agent_performance_summary()
        active_alerts = summary.get('active_alerts', [])
        
        # Format alerts
        alerts_data = []
        for alert in active_alerts:
            alerts_data.append({
                'id': alert['alert_id'],
                'level': alert['level'],
                'title': alert['title'],
                'description': alert['description'],
                'agent_id': alert['agent_id'],
                'timestamp': alert['timestamp'],
                'status': 'active'
            })
        
        # Count alerts by level
        alert_counts = {
            'critical': sum(1 for a in alerts_data if a['level'] == 'critical'),
            'warning': sum(1 for a in alerts_data if a['level'] == 'warning'),
            'info': sum(1 for a in alerts_data if a['level'] == 'info')
        }
        
        return jsonify({
            'success': True,
            'alerts': alerts_data,
            'alert_counts': alert_counts,
            'total_alerts': len(alerts_data),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/trends')
def analytics_trends():
    """Get performance trends over time"""
    try:
        if not PERFORMANCE_TRACKING_AVAILABLE:
            return jsonify({
                'error': 'Performance tracking not available'
            }), 503
        
        # Get time range from query params
        hours = int(request.args.get('hours', 24))
        hours = min(hours, 168)  # Max 1 week
        
        trends = performance_tracker.get_performance_trends(hours=hours)
        
        return jsonify({
            'success': True,
            'trends': trends,
            'time_range_hours': hours,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get trends: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/metrics')
def analytics_metrics():
    """Get real-time metrics data"""
    try:
        if not PERFORMANCE_TRACKING_AVAILABLE:
            return jsonify({
                'error': 'Performance tracking not available'
            }), 503
        
        # Get recent metrics from buffer
        recent_metrics = list(performance_tracker.metrics_buffer)[-50:]  # Last 50 metrics
        
        metrics_data = []
        for metric in recent_metrics:
            metrics_data.append({
                'metric_id': metric.metric_id,
                'agent_id': metric.agent_id,
                'agent_type': metric.agent_type,
                'metric_type': metric.metric_type.value,
                'value': metric.value,
                'unit': metric.unit,
                'timestamp': metric.timestamp.isoformat(),
                'provider': metric.provider
            })
        
        return jsonify({
            'success': True,
            'metrics': metrics_data,
            'total_metrics': len(metrics_data),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/tasks')
def analytics_tasks():
    """Get task execution timeline"""
    try:
        if not PERFORMANCE_TRACKING_AVAILABLE:
            return jsonify({
                'error': 'Performance tracking not available'
            }), 503
        
        # Get limit from query params
        limit = int(request.args.get('limit', 50))
        limit = min(limit, 200)  # Max 200 tasks
        
        # Query task execution timeline
        import sqlite3
        conn = sqlite3.connect(performance_tracker.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                task_id, agent_id, agent_type, task_name, status,
                started_at, completed_at, duration_ms, tokens_used,
                cost, provider, success, error_message,
                files_created, files_modified
            FROM task_execution_timeline 
            ORDER BY completed_at DESC 
            LIMIT ?
        """, (limit,))
        
        tasks_data = []
        for row in cursor.fetchall():
            tasks_data.append({
                'task_id': row[0],
                'agent_id': row[1],
                'agent_type': row[2],
                'task_name': row[3],
                'status': row[4],
                'started_at': row[5],
                'completed_at': row[6],
                'duration_ms': row[7],
                'tokens_used': row[8],
                'cost': row[9],
                'provider': row[10],
                'success': row[11],
                'error_message': row[12],
                'files_created': row[13],
                'files_modified': row[14]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'tasks': tasks_data,
            'total_tasks': len(tasks_data),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get task timeline: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/dashboard-data')
def dashboard_data():
    """Get all dashboard data in one request"""
    try:
        if not PERFORMANCE_TRACKING_AVAILABLE:
            return jsonify({
                'error': 'Performance tracking not available',
                'mock_data': True,
                'overview': {
                    'total_agents': 8,
                    'active_agents': 6,
                    'total_tasks': 156,
                    'success_rate': 94.2,
                    'avg_response_time': 8500,
                    'total_cost': 12.45,
                    'active_alerts': 2
                },
                'agents': [
                    {
                        'id': 'code_dev_01',
                        'name': 'Code Developer 01',
                        'type': 'code_developer',
                        'status': 'active',
                        'total_tasks': 45,
                        'success_rate': 96.7,
                        'avg_response_time': 12000,
                        'total_cost': 4.32
                    },
                    {
                        'id': 'sys_analyst_01',
                        'name': 'System Analyst 01',
                        'type': 'system_analyst',
                        'status': 'active',
                        'total_tasks': 32,
                        'success_rate': 91.2,
                        'avg_response_time': 8500,
                        'total_cost': 2.87
                    }
                ],
                'providers': [
                    {
                        'name': 'anthropic',
                        'requests': 98,
                        'success_rate': 96.9,
                        'avg_response_time': 9200,
                        'total_cost': 8.45,
                        'status': 'healthy'
                    },
                    {
                        'name': 'openai',
                        'requests': 58,
                        'success_rate': 93.1,
                        'avg_response_time': 7800,
                        'total_cost': 4.00,
                        'status': 'healthy'
                    }
                ],
                'alerts': [
                    {
                        'id': 'alert_001',
                        'level': 'warning',
                        'title': 'High Response Time',
                        'description': 'Agent code_dev_01 response time above threshold',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                ]
            })
        
        # Get all data from the performance tracker
        summary = performance_tracker.get_agent_performance_summary()
        trends = performance_tracker.get_performance_trends(hours=24)
        
        # Format overview data
        overall_stats = summary.get('overall_stats', {})
        overview = {
            'total_agents': overall_stats.get('total_agents', 0),
            'active_agents': len([a for a in summary.get('agent_stats', []) if a.get('last_active')]),
            'total_tasks': overall_stats.get('total_tasks', 0),
            'success_rate': overall_stats.get('avg_success_rate', 0),
            'avg_response_time': overall_stats.get('avg_response_time', 0),
            'total_cost': overall_stats.get('total_cost', 0),
            'active_alerts': len(summary.get('active_alerts', []))
        }
        
        # Format agent data
        agents = []
        for agent in summary.get('agent_stats', [])[:10]:  # Top 10 agents
            agents.append({
                'id': agent['agent_id'],
                'name': agent['agent_id'].replace('_', ' ').title(),
                'type': agent['agent_type'],
                'status': 'active' if agent['last_active'] else 'inactive',
                'total_tasks': agent['total_tasks'],
                'success_rate': agent['success_rate'],
                'avg_response_time': agent['avg_response_time'],
                'total_cost': agent['total_cost']
            })
        
        # Format provider data
        providers = []
        provider_stats = summary.get('provider_stats', {})
        for provider, stats in provider_stats.items():
            error_rate = (stats['errors'] / max(stats['requests'], 1)) * 100
            providers.append({
                'name': provider,
                'requests': stats['requests'],
                'success_rate': 100 - error_rate,
                'avg_response_time': stats['avg_response_time'],
                'total_cost': stats['total_cost'],
                'status': 'healthy' if error_rate < 10 else 'warning' if error_rate < 30 else 'critical'
            })
        
        # Format alerts
        alerts = []
        for alert in summary.get('active_alerts', [])[:5]:  # Top 5 alerts
            alerts.append({
                'id': alert['alert_id'],
                'level': alert['level'],
                'title': alert['title'],
                'description': alert['description'],
                'timestamp': alert['timestamp']
            })
        
        return jsonify({
            'success': True,
            'overview': overview,
            'agents': agents,
            'providers': providers,
            'alerts': alerts,
            'trends': trends,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/test-data')
def test_analytics_data():
    """Generate test data for the analytics system"""
    try:
        if not PERFORMANCE_TRACKING_AVAILABLE:
            return jsonify({
                'error': 'Performance tracking not available'
            }), 503
        
        # Generate some test task executions
        import random
        from datetime import datetime, timezone, timedelta
        
        agent_types = ['code_developer', 'system_analyst', 'api_integrator', 'database_specialist']
        providers = ['anthropic', 'openai', 'gemini']
        
        test_tasks = []
        
        for i in range(20):
            agent_type = random.choice(agent_types)
            provider = random.choice(providers)
            success = random.random() > 0.1  # 90% success rate
            
            task_data = {
                'task_id': f'test_task_{i:03d}',
                'agent_id': f'{agent_type}_01',
                'agent_type': agent_type,
                'task_name': f'Test Task {i+1}',
                'success': success,
                'duration_ms': random.randint(2000, 25000),
                'tokens_used': random.randint(500, 5000),
                'cost': random.uniform(0.01, 0.5),
                'provider': provider,
                'started_at': datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 60)),
                'completed_at': datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
                'status': 'completed' if success else 'failed',
                'error_message': None if success else 'Test error message',
                'files_created': ['test_file.py'] if success and random.random() > 0.5 else [],
                'files_modified': ['existing_file.py'] if success and random.random() > 0.7 else []
            }
            
            performance_tracker.record_task_execution(task_data)
            test_tasks.append(task_data)
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(test_tasks)} test task executions',
            'test_tasks': len(test_tasks),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to generate test data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/health')
def analytics_health():
    """Get analytics system health status"""
    try:
        health_status = {
            'performance_tracking': PERFORMANCE_TRACKING_AVAILABLE,
            'database_connection': False,
            'metrics_buffer_size': 0,
            'alerts_count': 0,
            'uptime': 'unknown'
        }
        
        if PERFORMANCE_TRACKING_AVAILABLE:
            try:
                import sqlite3
                conn = sqlite3.connect(performance_tracker.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM performance_metrics")
                metrics_count = cursor.fetchone()[0]
                conn.close()
                
                health_status.update({
                    'database_connection': True,
                    'metrics_buffer_size': len(performance_tracker.metrics_buffer),
                    'alerts_count': len(performance_tracker.alerts),
                    'total_metrics': metrics_count
                })
                
            except Exception as e:
                health_status['database_error'] = str(e)
        
        return jsonify({
            'success': True,
            'health': health_status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/insights')
def analytics_insights():
    """Get comprehensive system insights and optimization recommendations"""
    try:
        # Try to get insights from orchestration monitor
        try:
            from agent_orchestrator_integration import get_system_insights
            insights = get_system_insights()
        except ImportError:
            insights = {
                'monitoring_status': False,
                'optimization_recommendations': ['Enhanced monitoring not available'],
                'provider_performance': {},
                'agent_health': {},
                'error': 'Enhanced monitoring system not initialized'
            }
        
        return jsonify({
            'success': True,
            'insights': insights,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get system insights: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/optimize')
def analytics_optimize():
    """Trigger optimization recommendations"""
    try:
        # Get current insights
        from agent_orchestrator_integration import get_system_insights
        insights = get_system_insights()
        
        optimization_actions = []
        
        # Check if we can perform optimizations
        recommendations = insights.get('optimization_recommendations', [])
        
        if not recommendations:
            optimization_actions.append("System is already optimized")
        else:
            for rec in recommendations:
                optimization_actions.append(f"Recommendation: {rec}")
        
        return jsonify({
            'success': True,
            'optimization_actions': optimization_actions,
            'recommendations_count': len(recommendations),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to trigger optimization: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500