#!/usr/bin/env python3
"""
Agent Orchestrator Integration
=============================

Enhanced integration between the agent performance monitor and real orchestrator.
Provides real-time monitoring, alert system, and performance optimization.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import threading
import json

# Setup logging
logger = logging.getLogger(__name__)

class EnhancedOrchestrationMonitor:
    """Enhanced monitoring for the agent orchestration system"""
    
    def __init__(self):
        self.monitoring_active = False
        self.performance_tracker = None
        self.orchestrator = None
        self.alert_callbacks = []
        self.monitoring_thread = None
        
        # Performance thresholds for automatic optimization
        self.optimization_thresholds = {
            'high_error_rate': 25.0,  # Percentage
            'slow_response_time': 20000.0,  # Milliseconds
            'high_cost_per_task': 1.0,  # Dollars
            'provider_failure_rate': 40.0  # Percentage
        }
        
        # Load balancing weights
        self.provider_weights = {
            'anthropic': 1.0,
            'openai': 1.0,
            'gemini': 1.0
        }
        
        self.init_integration()
    
    def init_integration(self):
        """Initialize integration with orchestrator and performance tracker"""
        try:
            from agent_performance_monitor import performance_tracker
            self.performance_tracker = performance_tracker
            logger.info("✅ Performance tracker integrated")
            
            from real_agent_orchestrator import real_orchestrator
            self.orchestrator = real_orchestrator
            logger.info("✅ Real orchestrator integrated")
            
            # Start monitoring
            self.start_enhanced_monitoring()
            
        except ImportError as e:
            logger.warning(f"⚠️ Could not integrate components: {e}")
    
    def start_enhanced_monitoring(self):
        """Start enhanced monitoring in background thread"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("🔍 Enhanced orchestration monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("⏹️ Enhanced monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Check system performance
                self._check_system_health()
                
                # Optimize load balancing
                self._optimize_load_balancing()
                
                # Check for performance issues
                self._check_performance_issues()
                
                # Auto-scale based on load
                self._auto_scale_monitoring()
                
                # Sleep for monitoring interval
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Wait 30 seconds on error
    
    def _check_system_health(self):
        """Check overall system health"""
        if not self.performance_tracker:
            return
        
        try:
            summary = self.performance_tracker.get_agent_performance_summary()
            overall_stats = summary.get('overall_stats', {})
            
            # Check overall success rate
            success_rate = overall_stats.get('avg_success_rate', 0)
            if success_rate < 80.0:
                self._trigger_alert(
                    level='warning',
                    title='Low System Success Rate',
                    description=f'Overall system success rate is {success_rate:.1f}%',
                    metric_type='system_health'
                )
            
            # Check average response time
            avg_response_time = overall_stats.get('avg_response_time', 0)
            if avg_response_time > 15000:  # 15 seconds
                self._trigger_alert(
                    level='warning',
                    title='High System Response Time',
                    description=f'Average response time is {avg_response_time:.0f}ms',
                    metric_type='system_performance'
                )
            
            # Check cost trends
            total_cost = overall_stats.get('total_cost', 0)
            if total_cost > 50.0:  # Alert if costs exceed $50
                self._trigger_alert(
                    level='info',
                    title='High Cost Alert',
                    description=f'Total system cost is ${total_cost:.2f}',
                    metric_type='cost_monitoring'
                )
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
    
    def _optimize_load_balancing(self):
        """Dynamically optimize load balancing based on performance"""
        if not self.performance_tracker or not self.orchestrator:
            return
        
        try:
            summary = self.performance_tracker.get_agent_performance_summary()
            provider_stats = summary.get('provider_stats', {})
            
            # Calculate provider performance scores
            provider_scores = {}
            for provider, stats in provider_stats.items():
                if stats['requests'] > 0:
                    error_rate = (stats['errors'] / stats['requests']) * 100
                    avg_response_time = stats['avg_response_time']
                    
                    # Score based on success rate and response time
                    success_rate = 100 - error_rate
                    speed_score = max(0, 100 - (avg_response_time / 100))  # Normalize response time
                    
                    overall_score = (success_rate * 0.7) + (speed_score * 0.3)
                    provider_scores[provider] = max(0.1, overall_score / 100)  # Min weight 0.1
                else:
                    provider_scores[provider] = 1.0  # Default for new providers
            
            # Update orchestrator load balancer weights
            if hasattr(self.orchestrator, 'load_balancer'):
                for provider, score in provider_scores.items():
                    if provider in self.orchestrator.load_balancer.providers:
                        self.orchestrator.load_balancer.providers[provider]['weight'] = score
                
                logger.info(f"📊 Updated provider weights: {provider_scores}")
            
        except Exception as e:
            logger.error(f"Error optimizing load balancing: {e}")
    
    def _check_performance_issues(self):
        """Check for specific performance issues and auto-remediate"""
        if not self.performance_tracker:
            return
        
        try:
            summary = self.performance_tracker.get_agent_performance_summary()
            
            # Check individual agents for issues
            for agent in summary.get('agent_stats', []):
                agent_id = agent['agent_id']
                
                # High error rate
                if agent['total_tasks'] > 5 and agent['success_rate'] < 70:
                    self._trigger_agent_remediation(agent_id, 'high_error_rate', agent['success_rate'])
                
                # Slow response time
                if agent['avg_response_time'] > self.optimization_thresholds['slow_response_time']:
                    self._trigger_agent_remediation(agent_id, 'slow_response', agent['avg_response_time'])
                
                # High cost per task
                if agent['cost_per_task'] > self.optimization_thresholds['high_cost_per_task']:
                    self._trigger_agent_remediation(agent_id, 'high_cost', agent['cost_per_task'])
            
        except Exception as e:
            logger.error(f"Error checking performance issues: {e}")
    
    def _trigger_agent_remediation(self, agent_id: str, issue_type: str, value: float):
        """Trigger automatic remediation for agent issues"""
        remediation_actions = {
            'high_error_rate': lambda: self._remediate_high_error_rate(agent_id, value),
            'slow_response': lambda: self._remediate_slow_response(agent_id, value),
            'high_cost': lambda: self._remediate_high_cost(agent_id, value)
        }
        
        if issue_type in remediation_actions:
            try:
                remediation_actions[issue_type]()
                logger.info(f"🔧 Applied remediation for {agent_id}: {issue_type}")
            except Exception as e:
                logger.error(f"Failed to remediate {issue_type} for {agent_id}: {e}")
    
    def _remediate_high_error_rate(self, agent_id: str, error_rate: float):
        """Remediate high error rate issues"""
        # Switch agent to most reliable provider
        if self.orchestrator and hasattr(self.orchestrator, 'agents'):
            agent = self.orchestrator.agents.get(agent_id)
            if agent:
                # Find most reliable provider
                best_provider = self._get_most_reliable_provider()
                if best_provider and best_provider != agent.llm_provider:
                    agent.llm_provider = best_provider
                    logger.info(f"🔄 Switched {agent_id} to {best_provider} due to high error rate")
    
    def _remediate_slow_response(self, agent_id: str, response_time: float):
        """Remediate slow response time issues"""
        # Switch agent to fastest provider
        if self.orchestrator and hasattr(self.orchestrator, 'agents'):
            agent = self.orchestrator.agents.get(agent_id)
            if agent:
                fastest_provider = self._get_fastest_provider()
                if fastest_provider and fastest_provider != agent.llm_provider:
                    agent.llm_provider = fastest_provider
                    logger.info(f"⚡ Switched {agent_id} to {fastest_provider} for better speed")
    
    def _remediate_high_cost(self, agent_id: str, cost_per_task: float):
        """Remediate high cost issues"""
        # Switch agent to most cost-effective provider
        if self.orchestrator and hasattr(self.orchestrator, 'agents'):
            agent = self.orchestrator.agents.get(agent_id)
            if agent:
                cheapest_provider = self._get_most_cost_effective_provider()
                if cheapest_provider and cheapest_provider != agent.llm_provider:
                    agent.llm_provider = cheapest_provider
                    logger.info(f"💰 Switched {agent_id} to {cheapest_provider} for cost optimization")
    
    def _get_most_reliable_provider(self) -> Optional[str]:
        """Get the most reliable provider based on success rate"""
        if not self.performance_tracker:
            return None
        
        summary = self.performance_tracker.get_agent_performance_summary()
        provider_stats = summary.get('provider_stats', {})
        
        best_provider = None
        best_success_rate = 0
        
        for provider, stats in provider_stats.items():
            if stats['requests'] > 0:
                success_rate = (stats['requests'] - stats['errors']) / stats['requests']
                if success_rate > best_success_rate:
                    best_success_rate = success_rate
                    best_provider = provider
        
        return best_provider
    
    def _get_fastest_provider(self) -> Optional[str]:
        """Get the fastest provider based on response time"""
        if not self.performance_tracker:
            return None
        
        summary = self.performance_tracker.get_agent_performance_summary()
        provider_stats = summary.get('provider_stats', {})
        
        fastest_provider = None
        best_response_time = float('inf')
        
        for provider, stats in provider_stats.items():
            if stats['requests'] > 0:
                avg_response_time = stats['avg_response_time']
                if avg_response_time < best_response_time:
                    best_response_time = avg_response_time
                    fastest_provider = provider
        
        return fastest_provider
    
    def _get_most_cost_effective_provider(self) -> Optional[str]:
        """Get the most cost-effective provider"""
        if not self.performance_tracker:
            return None
        
        summary = self.performance_tracker.get_agent_performance_summary()
        provider_stats = summary.get('provider_stats', {})
        
        cheapest_provider = None
        best_cost_ratio = float('inf')
        
        for provider, stats in provider_stats.items():
            if stats['requests'] > 0:
                cost_per_request = stats['total_cost'] / stats['requests']
                if cost_per_request < best_cost_ratio:
                    best_cost_ratio = cost_per_request
                    cheapest_provider = provider
        
        return cheapest_provider
    
    def _auto_scale_monitoring(self):
        """Auto-scale monitoring based on system load"""
        if not self.orchestrator:
            return
        
        try:
            # Check task queue length
            pending_tasks = len([t for t in self.orchestrator.task_queue 
                               if hasattr(t, 'status') and t.status.value == 'pending'])
            
            # Check active agents
            active_agents = len([a for a in self.orchestrator.agents.values() 
                               if hasattr(a, 'status') and a.status == 'working'])
            
            # Auto-scaling logic
            if pending_tasks > 10 and active_agents == 0:
                logger.warning(f"⚠️ High task queue ({pending_tasks} pending) with no active agents")
                self._trigger_alert(
                    level='critical',
                    title='Task Queue Backlog',
                    description=f'{pending_tasks} tasks pending with no active agents',
                    metric_type='queue_management'
                )
            
        except Exception as e:
            logger.error(f"Error in auto-scaling check: {e}")
    
    def _trigger_alert(self, level: str, title: str, description: str, metric_type: str):
        """Trigger a system alert"""
        alert_data = {
            'level': level,
            'title': title,
            'description': description,
            'metric_type': metric_type,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'orchestration_monitor'
        }
        
        # Log the alert
        logger.warning(f"🚨 ALERT [{level.upper()}]: {title} - {description}")
        
        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def add_alert_callback(self, callback):
        """Add a callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def get_system_insights(self) -> Dict[str, Any]:
        """Get comprehensive system insights"""
        insights = {
            'monitoring_status': self.monitoring_active,
            'optimization_recommendations': [],
            'provider_performance': {},
            'agent_health': {},
            'cost_optimization': {},
            'performance_trends': {}
        }
        
        if not self.performance_tracker:
            return insights
        
        try:
            summary = self.performance_tracker.get_agent_performance_summary()
            
            # Analyze provider performance
            provider_stats = summary.get('provider_stats', {})
            for provider, stats in provider_stats.items():
                if stats['requests'] > 0:
                    success_rate = (stats['requests'] - stats['errors']) / stats['requests'] * 100
                    insights['provider_performance'][provider] = {
                        'success_rate': success_rate,
                        'avg_response_time': stats['avg_response_time'],
                        'cost_per_request': stats['total_cost'] / stats['requests'],
                        'total_requests': stats['requests'],
                        'recommendation': self._get_provider_recommendation(success_rate, stats['avg_response_time'])
                    }
            
            # Analyze agent health
            for agent in summary.get('agent_stats', []):
                agent_id = agent['agent_id']
                insights['agent_health'][agent_id] = {
                    'success_rate': agent['success_rate'],
                    'avg_response_time': agent['avg_response_time'],
                    'cost_per_task': agent['cost_per_task'],
                    'total_tasks': agent['total_tasks'],
                    'status': 'healthy' if agent['success_rate'] > 80 else 'attention_needed'
                }
            
            # Generate optimization recommendations
            insights['optimization_recommendations'] = self._generate_optimization_recommendations(summary)
            
        except Exception as e:
            logger.error(f"Error generating system insights: {e}")
            insights['error'] = str(e)
        
        return insights
    
    def _get_provider_recommendation(self, success_rate: float, avg_response_time: float) -> str:
        """Get recommendation for provider optimization"""
        if success_rate < 90:
            return "Consider reducing load on this provider"
        elif avg_response_time > 10000:
            return "High response time - may need optimization"
        elif success_rate > 95 and avg_response_time < 5000:
            return "Excellent performance - consider increasing load"
        else:
            return "Performing well"
    
    def _generate_optimization_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate system optimization recommendations"""
        recommendations = []
        
        overall_stats = summary.get('overall_stats', {})
        
        # Overall system recommendations
        if overall_stats.get('avg_success_rate', 0) < 85:
            recommendations.append("System success rate is below 85% - investigate failing agents")
        
        if overall_stats.get('avg_response_time', 0) > 12000:
            recommendations.append("Average response time is high - consider load balancing optimization")
        
        if overall_stats.get('total_cost', 0) > 25:
            recommendations.append("System costs are high - consider cost optimization strategies")
        
        # Agent-specific recommendations
        agent_stats = summary.get('agent_stats', [])
        failing_agents = [a for a in agent_stats if a['success_rate'] < 80]
        if failing_agents:
            recommendations.append(f"{len(failing_agents)} agents have success rates below 80%")
        
        slow_agents = [a for a in agent_stats if a['avg_response_time'] > 15000]
        if slow_agents:
            recommendations.append(f"{len(slow_agents)} agents have slow response times")
        
        # Provider recommendations
        provider_stats = summary.get('provider_stats', {})
        for provider, stats in provider_stats.items():
            if stats['requests'] > 0:
                error_rate = (stats['errors'] / stats['requests']) * 100
                if error_rate > 20:
                    recommendations.append(f"Provider {provider} has high error rate ({error_rate:.1f}%)")
        
        return recommendations

# Global monitor instance
orchestration_monitor = EnhancedOrchestrationMonitor()

def get_system_insights() -> Dict[str, Any]:
    """Get system insights from the orchestration monitor"""
    return orchestration_monitor.get_system_insights()

def add_performance_alert_callback(callback):
    """Add a callback for performance alerts"""
    orchestration_monitor.add_alert_callback(callback)

if __name__ == "__main__":
    # Test the orchestration monitor
    print("🚀 Enhanced Orchestration Monitor Test")
    
    # Add a test alert callback
    def test_alert_callback(alert_data):
        print(f"📢 ALERT: {alert_data['title']} - {alert_data['description']}")
    
    orchestration_monitor.add_alert_callback(test_alert_callback)
    
    # Get system insights
    insights = orchestration_monitor.get_system_insights()
    print("\n📊 System Insights:")
    print(json.dumps(insights, indent=2, default=str))
    
    print("\n✅ Enhanced orchestration monitoring system tested successfully!")