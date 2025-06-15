#!/usr/bin/env python3
"""
Routes for business empire functionality
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
import sqlite3
from datetime import datetime
import logging
import random

logger = logging.getLogger(__name__)

business_bp = Blueprint('business', __name__)

@business_bp.route('/business-empire')
def business_empire():
    """Redirect to modern Business Empire page."""
    return redirect(url_for('business.business_empire_modern'))

@business_bp.route('/business-opportunities')
def business_opportunities():
    """Business opportunities page."""
    from database import NotionLikeDatabase
    db = NotionLikeDatabase()
    opportunities = db.get_table_data('business_opportunities')
    return render_template('business_opportunities_modern.html', opportunities=opportunities)

@business_bp.route('/business-projects')
def business_projects():
    """Business projects page."""
    from database import NotionLikeDatabase
    db = NotionLikeDatabase()
    projects = db.get_table_data('business_projects')
    
    # Calculate stats needed by template
    total_budget = sum(project.get('budget', 0) for project in projects)
    total_spent = sum(project.get('spent', 0) for project in projects)
    spent_percentage = round((total_spent / total_budget * 100), 1) if total_budget > 0 else 0
    
    # Calculate average progress
    progress_values = [project.get('progress', 0) for project in projects if project.get('progress') is not None]
    avg_progress = round(sum(progress_values) / len(progress_values), 1) if progress_values else 0
    
    # Status breakdown
    status_counts = {}
    for project in projects:
        status = project.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    project_status_stats = []
    total_projects = len(projects)
    for status, count in status_counts.items():
        percentage = (count / total_projects * 100) if total_projects > 0 else 0
        project_status_stats.append({
            'name': status,
            'count': count,
            'percentage': round(percentage, 1)
        })
    
    return render_template('business_projects_modern.html', 
                         projects=projects,
                         total_budget=total_budget,
                         total_spent=total_spent,
                         spent_percentage=spent_percentage,
                         avg_progress=avg_progress,
                         project_status_stats=project_status_stats)

@business_bp.route('/business-revenue')
def business_revenue():
    """Business revenue streams page."""
    from database import NotionLikeDatabase
    db = NotionLikeDatabase()
    revenue_streams = db.get_table_data('revenue_streams')
    
    # Calculate totals
    total_monthly = sum(stream.get('monthly_revenue', 0) for stream in revenue_streams)
    avg_growth = sum(stream.get('growth_rate', 0) for stream in revenue_streams) / len(revenue_streams) if revenue_streams else 0
    
    return render_template('business_revenue.html', 
                         revenue_streams=revenue_streams,
                         total_monthly=total_monthly,
                         avg_growth=avg_growth)

@business_bp.route('/business-agents')
def business_agents():
    """Business agents page."""
    from database import NotionLikeDatabase
    db = NotionLikeDatabase()
    agents = db.get_table_data('business_agents')
    
    # Calculate stats
    total_agents = len(agents)
    available_agents = sum(1 for a in agents if a.get('status') == 'Available')
    avg_performance = sum(a.get('performance_score', 0) for a in agents) / total_agents if total_agents else 0
    
    return render_template('business_agents.html', 
                         agents=agents,
                         stats={
                             'total': total_agents,
                             'available': available_agents,
                             'avg_performance': avg_performance
                         })

@business_bp.route('/api/approve_business_opportunity', methods=['POST'])
def approve_business_opportunity():
    """Approve a business opportunity and convert to project."""
    try:
        from database import NotionLikeDatabase
        
        data = request.json
        opportunity_id = data.get('opportunity_id')
        
        db = NotionLikeDatabase()
        
        # Get opportunity details
        opportunity = db.get_record('business_opportunities', opportunity_id)
        
        if opportunity:
            # Create new project from opportunity
            project_id = db.add_record('business_projects', {
                'project_name': opportunity.get('opportunity_name'),
                'description': opportunity.get('description'),
                'status': 'Planning',
                'roi_percentage': random.uniform(15, 45)  # Simulated ROI
            })
            
            # Update opportunity status
            db.update_record('business_opportunities', opportunity_id, {
                'status': 'Approved'
            })
            
            return jsonify({
                'success': True,
                'message': 'Opportunity approved and converted to project',
                'project_id': project_id
            })
        else:
            return jsonify({'success': False, 'error': 'Opportunity not found'})
    
    except Exception as e:
        logger.error(f"Error approving opportunity: {e}")
        return jsonify({'success': False, 'error': str(e)})

@business_bp.route('/api/update_business_project_status', methods=['POST'])
def update_business_project_status():
    """Update business project status."""
    try:
        from database import NotionLikeDatabase
        
        data = request.json
        project_id = data.get('project_id')
        new_status = data.get('status')
        
        db = NotionLikeDatabase()
        
        success = db.update_record('business_projects', project_id, {
            'status': new_status
        })
        
        return jsonify({'success': success})
    
    except Exception as e:
        logger.error(f"Error updating project status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@business_bp.route('/api/business_empire_stats', methods=['GET'])
def business_empire_stats():
    """Get business empire statistics."""
    try:
        from database import NotionLikeDatabase
        db = NotionLikeDatabase()
        
        # Get all data
        opportunities = db.get_table_data('business_opportunities')
        projects = db.get_table_data('business_projects')
        revenue_streams = db.get_table_data('revenue_streams')
        agents = db.get_table_data('business_agents')
        
        # Calculate stats
        stats = {
            'opportunities': {
                'total': len(opportunities),
                'evaluating': sum(1 for o in opportunities if o.get('status') == 'Evaluating'),
                'approved': sum(1 for o in opportunities if o.get('status') == 'Approved')
            },
            'projects': {
                'total': len(projects),
                'planning': sum(1 for p in projects if p.get('status') == 'Planning'),
                'in_progress': sum(1 for p in projects if p.get('status') == 'In Progress'),
                'completed': sum(1 for p in projects if p.get('status') == 'Completed')
            },
            'revenue': {
                'total_monthly': sum(r.get('monthly_revenue', 0) for r in revenue_streams),
                'active_streams': sum(1 for r in revenue_streams if r.get('status') == 'Active'),
                'avg_growth': sum(r.get('growth_rate', 0) for r in revenue_streams) / len(revenue_streams) if revenue_streams else 0
            },
            'agents': {
                'total': len(agents),
                'available': sum(1 for a in agents if a.get('status') == 'Available'),
                'avg_performance': sum(a.get('performance_score', 0) for a in agents) / len(agents) if agents else 0
            }
        }
        
        return jsonify({'success': True, 'stats': stats})
    
    except Exception as e:
        logger.error(f"Error getting business empire stats: {e}")
        return jsonify({'success': False, 'error': str(e)})

@business_bp.route('/api/business_agent_command', methods=['POST'])
def business_agent_command():
    """Execute business agent commands."""
    try:
        from database import NotionLikeDatabase
        
        data = request.json
        agent_id = data.get('agent_id')
        command = data.get('command')
        
        db = NotionLikeDatabase()
        
        if command == 'deploy':
            # Deploy agent
            db.update_record('business_agents', agent_id, {
                'status': 'Deployed'
            })
            
            # Simulate creating a new opportunity
            opportunity_id = db.add_record('business_opportunities', {
                'opportunity_name': f'AI-Generated Opportunity {random.randint(100, 999)}',
                'description': 'Autonomous agent identified market opportunity',
                'potential_value': f'${random.randint(10, 100)}k/month',
                'status': 'Evaluating'
            })
            
            return jsonify({
                'success': True,
                'message': 'Agent deployed successfully',
                'opportunity_created': opportunity_id
            })
        
        elif command == 'recall':
            # Recall agent
            db.update_record('business_agents', agent_id, {
                'status': 'Available'
            })
            
            return jsonify({
                'success': True,
                'message': 'Agent recalled successfully'
            })
        
        else:
            return jsonify({'success': False, 'error': f'Unknown command: {command}'})
    
    except Exception as e:
        logger.error(f"Error executing business agent command: {e}")
        return jsonify({'success': False, 'error': str(e)})

@business_bp.route('/business-empire-modern')
def business_empire_modern():
    """Modern Business Empire dashboard."""
    from database import NotionLikeDatabase
    db = NotionLikeDatabase()
    
    # Get all business data
    opportunities = db.get_table_data('business_opportunities', limit=5)
    projects = db.get_table_data('business_projects', limit=5)
    revenue_streams = db.get_table_data('revenue_streams', limit=5)
    agents = db.get_table_data('business_agents', limit=5)
    
    # Calculate summary stats
    total_revenue = sum(r.get('monthly_revenue', 0) for r in revenue_streams)
    active_projects = sum(1 for p in projects if p.get('status') in ['Planning', 'In Progress'])
    available_agents = sum(1 for a in agents if a.get('status') == 'Available')
    
    return render_template('business_empire_modern.html',
                         opportunities=opportunities,
                         projects=projects,
                         revenue_streams=revenue_streams,
                         agents=agents,
                         stats={
                             'total_revenue': total_revenue,
                             'active_projects': active_projects,
                             'available_agents': available_agents
                         })

@business_bp.route('/business-opportunities-modern')
def business_opportunities_modern():
    """Modern Business opportunities page."""
    from database import NotionLikeDatabase
    db = NotionLikeDatabase()
    
    opportunities = db.get_table_data('business_opportunities')
    
    # Add some sample data if empty
    if not opportunities:
        sample_opportunities = [
            {
                'opportunity_name': 'AI Content Generation Service',
                'description': 'Automated content creation for businesses',
                'potential_value': '$50k/month',
                'status': 'Evaluating'
            },
            {
                'opportunity_name': 'Autonomous Trading Bot',
                'description': 'AI-powered cryptocurrency trading system',
                'potential_value': '$100k/month',
                'status': 'Evaluating'
            },
            {
                'opportunity_name': 'SaaS Automation Platform',
                'description': 'No-code automation for small businesses',
                'potential_value': '$75k/month',
                'status': 'Approved'
            }
        ]
        
        for opp in sample_opportunities:
            db.add_record('business_opportunities', opp)
        
        opportunities = db.get_table_data('business_opportunities')
    
    return render_template('business_opportunities_modern.html', opportunities=opportunities)

@business_bp.route('/business-projects-modern')
def business_projects_modern():
    """Modern Business projects page."""
    from database import NotionLikeDatabase
    db = NotionLikeDatabase()
    
    projects = db.get_table_data('business_projects')
    
    # Add some sample data if empty
    if not projects:
        sample_projects = [
            {
                'project_name': 'AI Assistant Platform',
                'description': 'Multi-agent AI assistant service',
                'status': 'In Progress',
                'roi_percentage': 35.5
            },
            {
                'project_name': 'Automated SEO Tool',
                'description': 'AI-powered SEO optimization service',
                'status': 'Planning',
                'roi_percentage': 28.3
            }
        ]
        
        for proj in sample_projects:
            db.add_record('business_projects', proj)
        
        projects = db.get_table_data('business_projects')
    
    return render_template('business_projects_modern.html', projects=projects)