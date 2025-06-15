#!/usr/bin/env python3
"""
Automation API Routes
Provides API endpoints for the automated GitHub processing pipeline
"""

from flask import Blueprint, request, jsonify, render_template
import logging
from datetime import datetime
from typing import Dict, Any

# Import automation services
try:
    from integration_pipeline_orchestrator import integration_orchestrator
    from background_processing_service import background_service, JobPriority, JobStatus
    from workflow_automation_scheduler import workflow_scheduler, WorkflowTrigger
    from automated_repository_processor import automated_processor
    from github_api_handler import github_api
except ImportError as e:
    logging.error(f"Failed to import automation services: {e}")
    # Create mock objects for graceful degradation
    integration_orchestrator = None
    background_service = None
    workflow_scheduler = None
    automated_processor = None
    github_api = None

logger = logging.getLogger(__name__)

# Create blueprint for API
automation_bp = Blueprint('automation', __name__, url_prefix='/api/automation')

# Create blueprint for dashboard
automation_dashboard_bp = Blueprint('automation_dashboard', __name__)

def check_services():
    """Check if automation services are available"""
    if not all([integration_orchestrator, background_service, workflow_scheduler, automated_processor, github_api]):
        return False, "Automation services not available"
    return True, "Services available"

@automation_bp.route('/status')
def get_automation_status():
    """Get overall automation system status"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        # Get comprehensive status from integration orchestrator
        status = integration_orchestrator.get_pipeline_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting automation status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/start', methods=['POST'])
def start_automation():
    """Start the complete automation pipeline"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        # Get configuration from request
        config_updates = request.json or {}
        
        # Update configuration if provided
        if config_updates:
            config_result = integration_orchestrator.update_config(config_updates)
            if not config_result['success']:
                return jsonify(config_result), 400
        
        # Start the pipeline
        result = integration_orchestrator.start_pipeline()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error starting automation: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/stop', methods=['POST'])
def stop_automation():
    """Stop the automation pipeline"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = integration_orchestrator.stop_pipeline()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error stopping automation: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/github/user/<username>/process', methods=['POST'])
def process_github_user(username):
    """Process a GitHub user through the complete pipeline"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = integration_orchestrator.process_github_user_complete(username)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error processing GitHub user {username}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/github/repository/<owner>/<repo>/process', methods=['POST'])
def process_github_repository(owner, repo):
    """Process a single GitHub repository through the complete pipeline"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = integration_orchestrator.process_repository_complete(owner, repo)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error processing repository {owner}/{repo}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/discovery/trigger', methods=['POST'])
def trigger_discovery():
    """Trigger automated repository discovery"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = integration_orchestrator.trigger_automated_discovery()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error triggering discovery: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/monitoring/trigger', methods=['POST'])
def trigger_monitoring():
    """Trigger repository monitoring"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = integration_orchestrator.trigger_repository_monitoring()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error triggering monitoring: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/health-check/trigger', methods=['POST'])
def trigger_health_check():
    """Trigger comprehensive health checks"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = integration_orchestrator.trigger_health_checks()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error triggering health check: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/jobs')
def get_background_jobs():
    """Get background job status"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        # Get query parameters
        status_filter = request.args.get('status')
        type_filter = request.args.get('type')
        limit = int(request.args.get('limit', 50))
        
        # Convert status filter
        job_status = None
        if status_filter:
            try:
                job_status = JobStatus(status_filter)
            except ValueError:
                return jsonify({"success": False, "error": f"Invalid status: {status_filter}"}), 400
        
        result = background_service.get_all_jobs(job_status, type_filter, limit)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting background jobs: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/jobs/<job_id>')
def get_job_status(job_id):
    """Get specific job status"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = background_service.get_job_status(job_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel a background job"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = background_service.cancel_job(job_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/jobs/<job_id>/retry', methods=['POST'])
def retry_job(job_id):
    """Retry a failed job"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = background_service.retry_job(job_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error retrying job {job_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/workflows')
def get_workflows():
    """Get all workflows"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        include_disabled = request.args.get('include_disabled', 'true').lower() == 'true'
        result = workflow_scheduler.get_all_workflows(include_disabled)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting workflows: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/workflows', methods=['POST'])
def create_workflow():
    """Create a new workflow"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Extract required fields
        required_fields = ['name', 'description', 'trigger', 'trigger_config', 'steps']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400
        
        # Convert trigger to enum
        try:
            trigger = WorkflowTrigger(data['trigger'])
        except ValueError:
            return jsonify({"success": False, "error": f"Invalid trigger type: {data['trigger']}"}), 400
        
        result = workflow_scheduler.create_workflow(
            name=data['name'],
            description=data['description'],
            trigger=trigger,
            trigger_config=data['trigger_config'],
            steps=data['steps'],
            tags=data.get('tags', [])
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/workflows/<workflow_id>')
def get_workflow(workflow_id):
    """Get specific workflow"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = workflow_scheduler.get_workflow(workflow_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/workflows/<workflow_id>/execute', methods=['POST'])
def execute_workflow(workflow_id):
    """Execute a workflow manually"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        trigger_data = request.json or {}
        
        result = workflow_scheduler.execute_workflow(workflow_id, trigger_data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/workflows/<workflow_id>/enable', methods=['POST'])
def enable_workflow(workflow_id):
    """Enable a workflow"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = workflow_scheduler.enable_workflow(workflow_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error enabling workflow {workflow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/workflows/<workflow_id>/disable', methods=['POST'])
def disable_workflow(workflow_id):
    """Disable a workflow"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = workflow_scheduler.disable_workflow(workflow_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error disabling workflow {workflow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/workflows/<workflow_id>/executions')
def get_workflow_executions(workflow_id):
    """Get workflow execution history"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        limit = int(request.args.get('limit', 50))
        result = workflow_scheduler.get_workflow_executions(workflow_id, limit)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting workflow executions for {workflow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/github/batch-process', methods=['POST'])
def batch_process_github_users():
    """Batch process multiple GitHub users"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        data = request.json
        if not data or 'usernames' not in data:
            return jsonify({"success": False, "error": "No usernames provided"}), 400
        
        usernames = data['usernames']
        if not isinstance(usernames, list):
            return jsonify({"success": False, "error": "Usernames must be a list"}), 400
        
        callback_url = data.get('callback_url')
        
        # Submit batch processing job
        job_result = background_service.submit_job(
            job_type="batch_github_processing",
            title=f"Batch Process {len(usernames)} GitHub Users",
            description=f"Batch process GitHub users: {', '.join(usernames[:5])}{'...' if len(usernames) > 5 else ''}",
            parameters={
                'usernames': usernames,
                'callback_url': callback_url
            },
            priority=JobPriority.NORMAL,
            tags=['github', 'batch', 'users']
        )
        
        return jsonify(job_result)
        
    except Exception as e:
        logger.error(f"Error batch processing GitHub users: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/github/api/rate-limit')
def get_github_rate_limit():
    """Get GitHub API rate limit status"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        result = github_api.get_rate_limit_status()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting GitHub rate limit: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/config')
def get_automation_config():
    """Get current automation configuration"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        config = integration_orchestrator.config.__dict__
        return jsonify({"success": True, "config": config})
        
    except Exception as e:
        logger.error(f"Error getting automation config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/config', methods=['POST'])
def update_automation_config():
    """Update automation configuration"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No configuration provided"}), 400
        
        result = integration_orchestrator.update_config(data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating automation config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/stats')
def get_automation_stats():
    """Get automation pipeline statistics"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        stats = integration_orchestrator.get_pipeline_stats()
        return jsonify({"success": True, "stats": stats})
        
    except Exception as e:
        logger.error(f"Error getting automation stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@automation_bp.route('/operations')
def get_active_operations():
    """Get active operations"""
    try:
        available, message = check_services()
        if not available:
            return jsonify({"success": False, "error": message}), 503
        
        # Get active operations from integration orchestrator
        operations = []
        for op_id, op_info in integration_orchestrator.active_operations.items():
            op_copy = op_info.copy()
            if 'started_at' in op_copy:
                op_copy['started_at'] = op_copy['started_at'].isoformat()
            op_copy['operation_id'] = op_id
            operations.append(op_copy)
        
        return jsonify({
            "success": True,
            "operations": operations,
            "total": len(operations)
        })
        
    except Exception as e:
        logger.error(f"Error getting active operations: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# Batch processing handler registration
def register_batch_processing_handler():
    """Register batch processing job handler"""
    if not background_service:
        return
    
    def batch_github_processing_handler(parameters, progress_callback):
        """Handle batch GitHub user processing"""
        usernames = parameters['usernames']
        callback_url = parameters.get('callback_url')
        
        progress_callback(0, len(usernames), "Starting batch processing")
        
        results = []
        processed = 0
        
        for i, username in enumerate(usernames):
            progress_callback(i, len(usernames), f"Processing user: {username}")
            
            try:
                # Process user through complete pipeline
                result = integration_orchestrator.process_github_user_complete(username)
                results.append({
                    'username': username,
                    'success': result.get('success', False),
                    'operation_id': result.get('operation_id'),
                    'job_id': result.get('job_id'),
                    'error': result.get('error')
                })
                
                if result.get('success', False):
                    processed += 1
                    
            except Exception as e:
                logger.error(f"Error processing user {username} in batch: {e}")
                results.append({
                    'username': username,
                    'success': False,
                    'error': str(e)
                })
        
        progress_callback(len(usernames), len(usernames), f"Batch processing completed: {processed}/{len(usernames)} successful")
        
        # TODO: Call callback URL if provided
        if callback_url:
            logger.info(f"Batch processing completed, callback URL: {callback_url}")
        
        return {
            "success": True,
            "processed": processed,
            "total": len(usernames),
            "results": results
        }
    
    try:
        background_service.register_job_handler("batch_github_processing", batch_github_processing_handler)
        logger.info("📝 Registered batch GitHub processing handler")
    except Exception as e:
        logger.error(f"Error registering batch processing handler: {e}")

# Dashboard route
@automation_dashboard_bp.route('/automation')
def automation_dashboard():
    """Serve the automation dashboard"""
    return render_template('automation_dashboard_modern.html')

# Initialize batch processing handler when module is imported
register_batch_processing_handler()