#!/usr/bin/env python3
"""
BUSINESS EMPIRE DASHBOARD
========================

Web interface for monitoring and controlling the AI business empire.

Features:
- Business opportunity tracking
- Project progress monitoring
- Revenue analytics
- Agent activity logs
- Strategic decision interface
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json
from datetime import datetime, timedelta
import os

class BusinessEmpireDashboard:
    """Web dashboard for the business empire system."""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.db_path = 'business_empire.db'
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes for the dashboard."""
        
        @self.app.route('/')
        def empire_dashboard():
            """Main empire dashboard."""
            stats = self.get_empire_stats()
            opportunities = self.get_recent_opportunities()
            projects = self.get_active_projects()
            revenue = self.get_revenue_summary()
            
            return render_template('empire_dashboard.html', 
                                 stats=stats, 
                                 opportunities=opportunities,
                                 projects=projects,
                                 revenue=revenue)
        
        @self.app.route('/opportunities')
        def opportunities_page():
            """Business opportunities page."""
            opportunities = self.get_all_opportunities()
            return render_template('opportunities.html', opportunities=opportunities)
        
        @self.app.route('/projects')
        def projects_page():
            """Business projects page."""
            projects = self.get_all_projects()
            return render_template('projects.html', projects=projects)
        
        @self.app.route('/revenue')
        def revenue_page():
            """Revenue analytics page."""
            revenue_data = self.get_detailed_revenue()
            return render_template('revenue.html', revenue_data=revenue_data)
        
        @self.app.route('/agents')
        def agents_page():
            """Agent activity monitoring page."""
            agent_logs = self.get_agent_activity()
            return render_template('agents.html', agent_logs=agent_logs)
        
        @self.app.route('/api/approve_opportunity', methods=['POST'])
        def approve_opportunity():
            """Approve an opportunity for development."""
            data = request.json
            opp_id = data.get('opportunity_id')
            
            success = self.approve_opportunity_for_development(opp_id)
            return jsonify({'success': success})
        
        @self.app.route('/api/update_project_status', methods=['POST'])
        def update_project_status():
            """Update project status."""
            data = request.json
            project_id = data.get('project_id')
            new_status = data.get('status')
            
            success = self.update_project_status_db(project_id, new_status)
            return jsonify({'success': success})
        
        @self.app.route('/api/empire_stats', methods=['GET'])
        def api_empire_stats():
            """API endpoint for empire statistics."""
            stats = self.get_empire_stats()
            return jsonify(stats)
        
        @self.app.route('/api/agent_command', methods=['POST'])
        def agent_command():
            """Send commands to agents."""
            data = request.json
            agent_type = data.get('agent_type')
            command = data.get('command')
            
            result = self.send_agent_command(agent_type, command)
            return jsonify(result)
    
    def get_empire_stats(self):
        """Get overall empire statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Opportunities stats
            cursor.execute("SELECT COUNT(*) FROM business_opportunities")
            total_opportunities = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM business_opportunities WHERE status = 'identified'")
            new_opportunities = cursor.fetchone()[0]
            
            # Projects stats
            cursor.execute("SELECT COUNT(*) FROM business_projects")
            total_projects = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM business_projects WHERE status = 'development'")
            active_projects = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM business_projects WHERE status = 'launched'")
            launched_projects = cursor.fetchone()[0]
            
            # Revenue stats
            cursor.execute("SELECT SUM(amount) FROM revenue_streams WHERE status = 'active'")
            total_revenue = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(customer_count) FROM revenue_streams WHERE status = 'active'")
            total_customers = cursor.fetchone()[0] or 0
            
            # Agent activity (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) FROM agent_actions 
                WHERE timestamp > datetime('now', '-1 day')
            """)
            recent_actions = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_opportunities': total_opportunities,
                'new_opportunities': new_opportunities,
                'total_projects': total_projects,
                'active_projects': active_projects,
                'launched_projects': launched_projects,
                'total_revenue': total_revenue,
                'total_customers': total_customers,
                'recent_actions': recent_actions,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting empire stats: {e}")
            return {}
    
    def get_recent_opportunities(self, limit=10):
        """Get recent business opportunities."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, category, title, revenue_model, revenue_potential, status, created_at
                FROM business_opportunities
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            opportunities = []
            for row in cursor.fetchall():
                opportunities.append({
                    'id': row[0],
                    'category': row[1],
                    'title': row[2],
                    'revenue_model': row[3],
                    'revenue_potential': row[4],
                    'status': row[5],
                    'created_at': row[6]
                })
            
            conn.close()
            return opportunities
            
        except Exception as e:
            print(f"❌ Error getting recent opportunities: {e}")
            return []
    
    def get_active_projects(self):
        """Get active business projects."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.id, p.name, p.progress, p.status, p.budget, p.timeline, o.category
                FROM business_projects p
                JOIN business_opportunities o ON p.opportunity_id = o.id
                WHERE p.status IN ('planning', 'development', 'testing')
                ORDER BY p.progress DESC
            """)
            
            projects = []
            for row in cursor.fetchall():
                projects.append({
                    'id': row[0],
                    'name': row[1],
                    'progress': row[2],
                    'status': row[3],
                    'budget': row[4],
                    'timeline': row[5],
                    'category': row[6]
                })
            
            conn.close()
            return projects
            
        except Exception as e:
            print(f"❌ Error getting active projects: {e}")
            return []
    
    def get_revenue_summary(self):
        """Get revenue summary by category."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT o.category, SUM(r.amount), COUNT(r.id), SUM(r.customer_count)
                FROM revenue_streams r
                JOIN business_projects p ON r.project_id = p.id
                JOIN business_opportunities o ON p.opportunity_id = o.id
                WHERE r.status = 'active'
                GROUP BY o.category
            """)
            
            revenue_by_category = []
            for row in cursor.fetchall():
                revenue_by_category.append({
                    'category': row[0],
                    'revenue': row[1] or 0,
                    'streams': row[2] or 0,
                    'customers': row[3] or 0
                })
            
            conn.close()
            return revenue_by_category
            
        except Exception as e:
            print(f"❌ Error getting revenue summary: {e}")
            return []
    
    def get_all_opportunities(self):
        """Get all business opportunities with detailed info."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, category, title, description, revenue_model, market_size,
                       implementation_complexity, revenue_potential, status, created_at
                FROM business_opportunities
                ORDER BY revenue_potential DESC
            """)
            
            opportunities = []
            for row in cursor.fetchall():
                opportunities.append({
                    'id': row[0],
                    'category': row[1],
                    'title': row[2],
                    'description': row[3],
                    'revenue_model': row[4],
                    'market_size': row[5],
                    'complexity': row[6],
                    'revenue_potential': row[7],
                    'status': row[8],
                    'created_at': row[9]
                })
            
            conn.close()
            return opportunities
            
        except Exception as e:
            print(f"❌ Error getting all opportunities: {e}")
            return []
    
    def get_all_projects(self):
        """Get all business projects with detailed info."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.id, p.name, p.description, p.tasks, p.progress, p.status,
                       p.budget, p.timeline, o.category, o.title as opportunity_title
                FROM business_projects p
                JOIN business_opportunities o ON p.opportunity_id = o.id
                ORDER BY p.created_at DESC
            """)
            
            projects = []
            for row in cursor.fetchall():
                tasks = json.loads(row[3]) if row[3] else []
                projects.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'tasks': tasks,
                    'progress': row[4],
                    'status': row[5],
                    'budget': row[6],
                    'timeline': row[7],
                    'category': row[8],
                    'opportunity_title': row[9]
                })
            
            conn.close()
            return projects
            
        except Exception as e:
            print(f"❌ Error getting all projects: {e}")
            return []
    
    def get_detailed_revenue(self):
        """Get detailed revenue analytics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Revenue by project
            cursor.execute("""
                SELECT p.name, r.revenue_source, r.amount, r.customer_count, o.category
                FROM revenue_streams r
                JOIN business_projects p ON r.project_id = p.id
                JOIN business_opportunities o ON p.opportunity_id = o.id
                WHERE r.status = 'active'
                ORDER BY r.amount DESC
            """)
            
            revenue_streams = []
            for row in cursor.fetchall():
                revenue_streams.append({
                    'project_name': row[0],
                    'source': row[1],
                    'amount': row[2],
                    'customers': row[3],
                    'category': row[4]
                })
            
            # Monthly revenue trend (simulated for now)
            monthly_revenue = [
                {'month': 'Jan', 'revenue': 0},
                {'month': 'Feb', 'revenue': 500},
                {'month': 'Mar', 'revenue': 1200},
                {'month': 'Apr', 'revenue': 2100},
                {'month': 'May', 'revenue': 3500},
                {'month': 'Jun', 'revenue': 5200}
            ]
            
            conn.close()
            
            return {
                'revenue_streams': revenue_streams,
                'monthly_trend': monthly_revenue,
                'total_mrr': sum(stream['amount'] for stream in revenue_streams)
            }
            
        except Exception as e:
            print(f"❌ Error getting detailed revenue: {e}")
            return {'revenue_streams': [], 'monthly_trend': [], 'total_mrr': 0}
    
    def get_agent_activity(self, limit=50):
        """Get recent agent activity logs."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT agent_type, action_type, target_id, action_data, success, timestamp
                FROM agent_actions
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            activity_logs = []
            for row in cursor.fetchall():
                activity_logs.append({
                    'agent_type': row[0],
                    'action_type': row[1],
                    'target_id': row[2],
                    'action_data': row[3],
                    'success': bool(row[4]),
                    'timestamp': row[5]
                })
            
            conn.close()
            return activity_logs
            
        except Exception as e:
            print(f"❌ Error getting agent activity: {e}")
            return []
    
    def approve_opportunity_for_development(self, opp_id: str) -> bool:
        """Approve an opportunity for development."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE business_opportunities
                SET status = 'approved_for_development'
                WHERE id = ?
            """, (opp_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error approving opportunity: {e}")
            return False
    
    def update_project_status_db(self, project_id: str, new_status: str) -> bool:
        """Update project status in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE business_projects
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_status, project_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error updating project status: {e}")
            return False
    
    def send_agent_command(self, agent_type: str, command: str) -> dict:
        """Send command to specific agent (simulated for now)."""
        try:
            # In real system, this would communicate with running agents
            # For now, just log the command
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agent_actions
                (agent_type, action_type, target_id, action_data, success)
                VALUES (?, ?, ?, ?, ?)
            """, (agent_type, "manual_command", "dashboard", command, True))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f"Command '{command}' sent to {agent_type} agent"
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to send command: {e}"
            }
    
    def run(self, host='0.0.0.0', port=5002):
        """Run the business empire dashboard."""
        print(f"🏢 Business Empire Dashboard starting on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=True)

if __name__ == "__main__":
    dashboard = BusinessEmpireDashboard()
    dashboard.run()