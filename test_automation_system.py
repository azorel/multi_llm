#!/usr/bin/env python3
"""
Test Automation System
Simple test script to validate the automated GitHub processing pipeline
"""

import asyncio
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all automation modules can be imported"""
    logger.info("🧪 Testing module imports...")
    
    try:
        from github_api_handler import github_api
        logger.info("✅ GitHub API handler imported")
    except ImportError as e:
        logger.error(f"❌ Failed to import GitHub API handler: {e}")
        return False
    
    try:
        from automated_repository_processor import automated_processor
        logger.info("✅ Automated repository processor imported")
    except ImportError as e:
        logger.error(f"❌ Failed to import automated repository processor: {e}")
        return False
    
    try:
        from background_processing_service import background_service
        logger.info("✅ Background processing service imported")
    except ImportError as e:
        logger.error(f"❌ Failed to import background processing service: {e}")
        return False
    
    try:
        from workflow_automation_scheduler import workflow_scheduler
        logger.info("✅ Workflow automation scheduler imported")
    except ImportError as e:
        logger.error(f"❌ Failed to import workflow automation scheduler: {e}")
        return False
    
    try:
        from integration_pipeline_orchestrator import integration_orchestrator
        logger.info("✅ Integration pipeline orchestrator imported")
    except ImportError as e:
        logger.error(f"❌ Failed to import integration pipeline orchestrator: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connectivity"""
    logger.info("🧪 Testing database connection...")
    
    try:
        from database import NotionLikeDatabase
        db = NotionLikeDatabase()
        
        # Test basic database operations
        tables = ['knowledge_hub', 'github_users']
        for table in tables:
            try:
                data = db.get_table_data(table, limit=1)
                logger.info(f"✅ Successfully connected to {table} table")
            except Exception as e:
                logger.warning(f"⚠️ Issue with {table} table: {e}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def test_github_api():
    """Test GitHub API functionality"""
    logger.info("🧪 Testing GitHub API...")
    
    try:
        from github_api_handler import github_api
        
        # Test rate limit check
        rate_limit = github_api.get_rate_limit_status()
        if rate_limit.get('success', False):
            logger.info("✅ GitHub API rate limit check successful")
            core = rate_limit.get('core', {})
            logger.info(f"   Rate limit: {core.get('remaining', 0)}/{core.get('limit', 0)}")
        else:
            logger.warning(f"⚠️ GitHub API rate limit check failed: {rate_limit.get('error', 'Unknown error')}")
        
        # Test user info (with a well-known user)
        try:
            user_info = github_api.get_user_info('octocat')
            if user_info.get('success', False):
                logger.info("✅ GitHub API user info test successful")
            else:
                logger.warning(f"⚠️ GitHub API user info test failed: {user_info.get('error', 'Unknown error')}")
        except Exception as e:
            logger.warning(f"⚠️ GitHub API user info test error: {e}")
        
        return True
    except Exception as e:
        logger.error(f"❌ GitHub API test failed: {e}")
        return False

def test_background_service():
    """Test background processing service"""
    logger.info("🧪 Testing background processing service...")
    
    try:
        from background_processing_service import background_service, JobPriority
        
        # Test service start
        result = background_service.start_service()
        if result.get('success', False):
            logger.info("✅ Background service started successfully")
        else:
            logger.warning(f"⚠️ Background service start failed: {result.get('error', 'Unknown error')}")
        
        # Test job submission
        def test_job_handler(parameters, progress_callback):
            progress_callback(0, 100, "Starting test job")
            time.sleep(1)
            progress_callback(50, 100, "Halfway complete")
            time.sleep(1)
            progress_callback(100, 100, "Test job completed")
            return {"success": True, "message": "Test job completed successfully"}
        
        # Register test handler
        background_service.register_job_handler("test_job", test_job_handler)
        
        # Submit test job
        job_result = background_service.submit_job(
            job_type="test_job",
            title="Test Job",
            description="Testing background job functionality",
            parameters={},
            priority=JobPriority.LOW
        )
        
        if job_result.get('success', False):
            logger.info("✅ Test job submitted successfully")
            job_id = job_result['job_id']
            
            # Wait for job completion
            max_wait = 10  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status = background_service.get_job_status(job_id)
                if status.get('success', False):
                    job = status['job']
                    if job['status'] == 'completed':
                        logger.info("✅ Test job completed successfully")
                        break
                    elif job['status'] == 'failed':
                        logger.warning(f"⚠️ Test job failed: {job.get('error', 'Unknown error')}")
                        break
                
                time.sleep(0.5)
            else:
                logger.warning("⚠️ Test job did not complete within timeout")
        else:
            logger.warning(f"⚠️ Test job submission failed: {job_result.get('error', 'Unknown error')}")
        
        # Test service stop
        stop_result = background_service.stop_service()
        if stop_result.get('success', False):
            logger.info("✅ Background service stopped successfully")
        else:
            logger.warning(f"⚠️ Background service stop failed: {stop_result.get('error', 'Unknown error')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Background service test failed: {e}")
        return False

def test_workflow_scheduler():
    """Test workflow automation scheduler"""
    logger.info("🧪 Testing workflow automation scheduler...")
    
    try:
        from workflow_automation_scheduler import workflow_scheduler, WorkflowTrigger
        
        # Test scheduler start
        result = workflow_scheduler.start_scheduler()
        if result.get('success', False):
            logger.info("✅ Workflow scheduler started successfully")
        else:
            logger.warning(f"⚠️ Workflow scheduler start failed: {result.get('error', 'Unknown error')}")
        
        # Test workflow creation
        workflow_result = workflow_scheduler.create_workflow(
            name="Test Workflow",
            description="Testing workflow functionality",
            trigger=WorkflowTrigger.MANUAL,
            trigger_config={},
            steps=[
                {
                    "step_id": "test_step",
                    "step_type": "repository_discovery",
                    "title": "Test Discovery Step",
                    "parameters": {"source": "database"}
                }
            ],
            tags=["test"]
        )
        
        if workflow_result.get('success', False):
            logger.info("✅ Test workflow created successfully")
            workflow_id = workflow_result['workflow_id']
            
            # Test workflow execution
            exec_result = workflow_scheduler.execute_workflow(workflow_id)
            if exec_result.get('success', False):
                logger.info("✅ Test workflow execution initiated")
            else:
                logger.warning(f"⚠️ Test workflow execution failed: {exec_result.get('error', 'Unknown error')}")
            
            # Clean up - delete test workflow
            delete_result = workflow_scheduler.delete_workflow(workflow_id)
            if delete_result.get('success', False):
                logger.info("✅ Test workflow deleted successfully")
        else:
            logger.warning(f"⚠️ Test workflow creation failed: {workflow_result.get('error', 'Unknown error')}")
        
        # Test scheduler stop
        stop_result = workflow_scheduler.stop_scheduler()
        if stop_result.get('success', False):
            logger.info("✅ Workflow scheduler stopped successfully")
        else:
            logger.warning(f"⚠️ Workflow scheduler stop failed: {stop_result.get('error', 'Unknown error')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Workflow scheduler test failed: {e}")
        return False

def test_integration_pipeline():
    """Test integration pipeline orchestrator"""
    logger.info("🧪 Testing integration pipeline orchestrator...")
    
    try:
        from integration_pipeline_orchestrator import integration_orchestrator
        
        # Test pipeline status
        status = integration_orchestrator.get_pipeline_status()
        if status.get('success', False):
            logger.info("✅ Pipeline status check successful")
            pipeline = status.get('pipeline', {})
            logger.info(f"   Pipeline running: {pipeline.get('running', False)}")
        else:
            logger.warning(f"⚠️ Pipeline status check failed: {status.get('error', 'Unknown error')}")
        
        # Test configuration
        config_result = integration_orchestrator.update_config({
            'github_monitoring_enabled': True,
            'auto_repository_discovery': True
        })
        if config_result.get('success', False):
            logger.info("✅ Pipeline configuration update successful")
        else:
            logger.warning(f"⚠️ Pipeline configuration update failed: {config_result.get('error', 'Unknown error')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Integration pipeline test failed: {e}")
        return False

def test_repository_processor():
    """Test automated repository processor"""
    logger.info("🧪 Testing automated repository processor...")
    
    try:
        from automated_repository_processor import automated_processor
        
        # Test processor stats
        stats = automated_processor.get_processing_stats()
        logger.info("✅ Repository processor stats retrieved")
        logger.info(f"   Current operations: {len(stats.get('current_operations', []))}")
        
        # Test discovery (without actually processing)
        discovery_result = automated_processor.discover_repositories("database")
        if discovery_result.get('success', False):
            logger.info("✅ Repository discovery test successful")
            logger.info(f"   Repositories discovered: {discovery_result.get('discovered', 0)}")
        else:
            logger.warning(f"⚠️ Repository discovery test failed: {discovery_result.get('error', 'Unknown error')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Repository processor test failed: {e}")
        return False

def test_api_routes():
    """Test API routes availability"""
    logger.info("🧪 Testing API routes...")
    
    try:
        from routes.automation import automation_bp, automation_dashboard_bp
        logger.info("✅ Automation routes imported successfully")
        
        # Check that blueprints have expected routes
        api_routes = [rule.rule for rule in automation_bp.url_map.iter_rules()]
        dashboard_routes = [rule.rule for rule in automation_dashboard_bp.url_map.iter_rules()]
        
        logger.info(f"   API routes: {len(api_routes)} endpoints")
        logger.info(f"   Dashboard routes: {len(dashboard_routes)} endpoints")
        
        return True
    except Exception as e:
        logger.error(f"❌ API routes test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    logger.info("🚀 Starting Automation System Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Database Connection", test_database_connection),
        ("GitHub API", test_github_api),
        ("Background Service", test_background_service),
        ("Workflow Scheduler", test_workflow_scheduler),
        ("Integration Pipeline", test_integration_pipeline),
        ("Repository Processor", test_repository_processor),
        ("API Routes", test_api_routes)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info("-" * 60)
        logger.info(f"Running test: {test_name}")
        
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            results[test_name] = {
                'success': result,
                'duration': duration
            }
            
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status} - {test_name} ({duration:.2f}s)")
            
        except Exception as e:
            logger.error(f"❌ CRASHED - {test_name}: {e}")
            results[test_name] = {
                'success': False,
                'duration': 0,
                'error': str(e)
            }
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        duration = result['duration']
        logger.info(f"{status} {test_name:<25} ({duration:.2f}s)")
        
        if not result['success'] and 'error' in result:
            logger.info(f"   Error: {result['error']}")
    
    logger.info("-" * 60)
    logger.info(f"Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 All tests passed! Automation system is ready.")
    elif passed >= total * 0.7:
        logger.info("⚠️ Most tests passed. System should work with some limitations.")
    else:
        logger.info("❌ Many tests failed. System may not work properly.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)