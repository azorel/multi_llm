#!/usr/bin/env python3
"""
TDD (Test-Driven Development) Routes
Provides web interface and API for the TDD system
"""

from flask import Blueprint, render_template, request, jsonify
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Import TDD system
try:
    from tdd_system import tdd_system
    tdd_available = True
    logger.info("✅ TDD system imported successfully")
except ImportError as e:
    tdd_available = False
    tdd_system = None
    logger.error(f"❌ TDD system not available: {e}")

tdd_bp = Blueprint('tdd', __name__)

@tdd_bp.route('/tdd-dashboard')
def tdd_dashboard():
    """TDD Dashboard - main interface"""
    if not tdd_available:
        return render_template('error.html', 
                             error_title="TDD System Unavailable",
                             error_message="The TDD system is not available.")
    
    return render_template('tdd_dashboard.html')

@tdd_bp.route('/api/tdd/cycles', methods=['GET'])
def get_all_cycles():
    """Get all TDD cycles"""
    if not tdd_available:
        return jsonify({'success': False, 'error': 'TDD system not available'})
    
    try:
        result = tdd_system.list_all_cycles()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting cycles: {e}")
        return jsonify({'success': False, 'error': str(e)})

@tdd_bp.route('/api/tdd/cycles', methods=['POST'])
def create_cycle():
    """Create a new TDD cycle"""
    if not tdd_available:
        return jsonify({'success': False, 'error': 'TDD system not available'})
    
    try:
        data = request.json
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Cycle name is required'})
        
        cycle_id = tdd_system.create_tdd_cycle(name, description)
        
        if cycle_id > 0:
            return jsonify({
                'success': True,
                'cycle_id': cycle_id,
                'message': f'TDD cycle "{name}" created successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create cycle'})
            
    except Exception as e:
        logger.error(f"Error creating cycle: {e}")
        return jsonify({'success': False, 'error': str(e)})

@tdd_bp.route('/api/tdd/cycles/<int:cycle_id>')
def get_cycle_status(cycle_id):
    """Get status of a specific TDD cycle"""
    if not tdd_available:
        return jsonify({'success': False, 'error': 'TDD system not available'})
    
    try:
        result = tdd_system.get_cycle_status(cycle_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting cycle status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@tdd_bp.route('/api/tdd/cycles/<int:cycle_id>/generate-tests', methods=['POST'])
def generate_tests(cycle_id):
    """Generate tests for a cycle from specification"""
    if not tdd_available:
        return jsonify({'success': False, 'error': 'TDD system not available'})
    
    try:
        data = request.json
        specification = data.get('specification', '').strip()
        
        if not specification:
            return jsonify({'success': False, 'error': 'Specification is required'})
        
        result = tdd_system.generate_test_from_specification(cycle_id, specification)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating tests: {e}")
        return jsonify({'success': False, 'error': str(e)})

@tdd_bp.route('/api/tdd/cycles/<int:cycle_id>/run-tests', methods=['POST'])
def run_tests(cycle_id):
    """Run tests for a cycle"""
    if not tdd_available:
        return jsonify({'success': False, 'error': 'TDD system not available'})
    
    try:
        result = tdd_system.run_tests(cycle_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return jsonify({'success': False, 'error': str(e)})

@tdd_bp.route('/api/tdd/test-cases/<int:test_case_id>/implement', methods=['POST'])
def implement_test(test_case_id):
    """Generate implementation for a failing test"""
    if not tdd_available:
        return jsonify({'success': False, 'error': 'TDD system not available'})
    
    try:
        result = tdd_system.implement_failing_test(test_case_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error implementing test: {e}")
        return jsonify({'success': False, 'error': str(e)})

@tdd_bp.route('/api/tdd/implementations/<int:implementation_id>/refactor', methods=['POST'])
def refactor_implementation(implementation_id):
    """Refactor an implementation"""
    if not tdd_available:
        return jsonify({'success': False, 'error': 'TDD system not available'})
    
    try:
        result = tdd_system.refactor_code(implementation_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error refactoring implementation: {e}")
        return jsonify({'success': False, 'error': str(e)})

@tdd_bp.route('/api/tdd/cycles/<int:cycle_id>/complete', methods=['POST'])
def complete_full_cycle(cycle_id):
    """Complete a full TDD cycle (Red-Green-Refactor)"""
    if not tdd_available:
        return jsonify({'success': False, 'error': 'TDD system not available'})
    
    try:
        data = request.json
        specification = data.get('specification', '').strip()
        
        if not specification:
            return jsonify({'success': False, 'error': 'Specification is required'})
        
        result = tdd_system.complete_tdd_cycle(cycle_id, specification)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error completing TDD cycle: {e}")
        return jsonify({'success': False, 'error': str(e)})

@tdd_bp.route('/api/tdd/health')
def tdd_health():
    """TDD system health check"""
    try:
        health_data = {
            'tdd_available': tdd_available,
            'timestamp': datetime.now().isoformat(),
            'system_status': 'operational' if tdd_available else 'unavailable'
        }
        
        if tdd_available:
            cycles_result = tdd_system.list_all_cycles()
            if cycles_result['success']:
                health_data.update({
                    'total_cycles': cycles_result['total_cycles'],
                    'active_cycles': cycles_result['active_cycles'],
                    'completed_cycles': cycles_result['completed_cycles']
                })
        
        return jsonify({'success': True, 'health': health_data})
        
    except Exception as e:
        logger.error(f"Error in TDD health check: {e}")
        return jsonify({'success': False, 'error': str(e)})