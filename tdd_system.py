#!/usr/bin/env python3
"""
Test-Driven Development (TDD) System
Provides automated test generation, execution, and code development following TDD principles
"""

import os
import sys
import ast
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
from database import NotionLikeDatabase

logger = logging.getLogger(__name__)

# Import testing modules with fallback
try:
    import pytest
    pytest_available = True
except ImportError:
    pytest_available = False
    logger.warning("pytest not available - some TDD features will be limited")

try:
    import coverage
    coverage_available = True
except ImportError:
    coverage_available = False
    logger.warning("coverage not available - coverage reports will be disabled")

class TDDSystem:
    """Complete Test-Driven Development system for automated code development"""
    
    def __init__(self):
        self.db = NotionLikeDatabase()
        self.test_dir = Path("tests")
        self.test_dir.mkdir(exist_ok=True)
        self.src_dir = Path("src")
        self.src_dir.mkdir(exist_ok=True)
        self.coverage_dir = Path("coverage_reports")
        self.coverage_dir.mkdir(exist_ok=True)
        self.tdd_cycles = []
        
        # Initialize TDD database tables
        self._init_tdd_database()
        
    def _init_tdd_database(self):
        """Initialize TDD-specific database tables"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # TDD Cycles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tdd_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    created_date TEXT,
                    completed_date TEXT,
                    test_files TEXT,
                    source_files TEXT,
                    coverage_percentage REAL,
                    total_tests INTEGER DEFAULT 0,
                    passing_tests INTEGER DEFAULT 0,
                    failing_tests INTEGER DEFAULT 0
                )
            ''')
            
            # Test Cases table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    test_code TEXT,
                    status TEXT DEFAULT 'red',
                    execution_time REAL,
                    error_message TEXT,
                    created_date TEXT,
                    last_run_date TEXT,
                    FOREIGN KEY (cycle_id) REFERENCES tdd_cycles (id)
                )
            ''')
            
            # Code Implementations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS code_implementations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_id INTEGER,
                    test_case_id INTEGER,
                    file_path TEXT,
                    function_name TEXT,
                    code_content TEXT,
                    iteration INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'draft',
                    created_date TEXT,
                    FOREIGN KEY (cycle_id) REFERENCES tdd_cycles (id),
                    FOREIGN KEY (test_case_id) REFERENCES test_cases (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ TDD database tables initialized")
            
        except Exception as e:
            logger.error(f"Error initializing TDD database: {e}")
    
    def create_tdd_cycle(self, name: str, description: str = "") -> int:
        """Create a new TDD cycle"""
        try:
            cycle_id = self.db.add_record('tdd_cycles', {
                'name': name,
                'description': description,
                'status': 'active',
                'created_date': datetime.now().isoformat(),
                'test_files': '[]',
                'source_files': '[]'
            })
            
            logger.info(f"🔄 Created TDD cycle: {name} (ID: {cycle_id})")
            return cycle_id
            
        except Exception as e:
            logger.error(f"Error creating TDD cycle: {e}")
            return -1
    
    def generate_test_from_specification(self, cycle_id: int, spec: str) -> Dict[str, Any]:
        """Generate test code from a specification using AI"""
        try:
            # Import the real orchestrator for AI assistance
            from real_agent_orchestrator import real_orchestrator, AgentType, TaskPriority
            
            # Create a task for the Code Developer agent to generate tests
            task_id = real_orchestrator.add_task(
                name=f"Generate TDD Tests - Cycle {cycle_id}",
                description=f"""
Generate comprehensive pytest test cases for the following specification:

{spec}

Requirements:
1. Follow TDD best practices (Red-Green-Refactor)
2. Create pytest-compatible test functions
3. Include edge cases and error conditions
4. Use descriptive test names and docstrings
5. Include setup and teardown if needed
6. Generate actual Python test code that can be executed

The tests should be designed to FAIL initially (Red phase) and guide the implementation.
                """,
                agent_type=AgentType.CODE_DEVELOPER,
                priority=TaskPriority.HIGH
            )
            
            # Get the task and agent
            task = next(t for t in real_orchestrator.task_queue if t.id == task_id)
            agent = next(a for a in real_orchestrator.agents.values() 
                        if a.agent_type == AgentType.CODE_DEVELOPER)
            
            # Execute the task synchronously
            import asyncio
            result = asyncio.run(agent.execute_task(task))
            
            if result['success']:
                test_code = result.get('result', '')
                
                # Save test case to database
                test_case_id = self.db.add_record('test_cases', {
                    'cycle_id': cycle_id,
                    'name': f"Generated Test for Cycle {cycle_id}",
                    'description': spec[:200] + "..." if len(spec) > 200 else spec,
                    'test_code': test_code,
                    'status': 'red',
                    'created_date': datetime.now().isoformat()
                })
                
                # Write test file
                test_file = self.test_dir / f"test_cycle_{cycle_id}_{test_case_id}.py"
                test_file.write_text(test_code)
                
                return {
                    'success': True,
                    'test_case_id': test_case_id,
                    'test_file': str(test_file),
                    'test_code': test_code,
                    'cost': result.get('cost', 0),
                    'tokens_used': result.get('tokens_used', 0)
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error in test generation')
                }
                
        except Exception as e:
            logger.error(f"Error generating test from specification: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_tests(self, cycle_id: int) -> Dict[str, Any]:
        """Run all tests for a TDD cycle"""
        try:
            # Get all test cases for this cycle
            test_cases = [tc for tc in self.db.get_table_data('test_cases') 
                         if tc.get('cycle_id') == cycle_id]
            
            if not test_cases:
                return {'success': False, 'error': 'No test cases found for this cycle'}
            
            # Initialize coverage if available
            cov = None
            if coverage_available:
                cov = coverage.Coverage()
                cov.start()
            
            results = {
                'total_tests': 0,
                'passing_tests': 0,
                'failing_tests': 0,
                'test_results': [],
                'coverage_percentage': 0.0
            }
            
            for test_case in test_cases:
                test_file = self.test_dir / f"test_cycle_{cycle_id}_{test_case['id']}.py"
                
                if test_file.exists():
                    # Run pytest on this specific test file if available, otherwise use python directly
                    if pytest_available:
                        cmd = ['python', '-m', 'pytest', str(test_file), '-v', '--tb=short']
                    else:
                        # Fallback to running Python directly (limited functionality)
                        cmd = ['python', str(test_file)]
                    
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        
                        test_result = {
                            'test_case_id': test_case['id'],
                            'test_name': test_case['name'],
                            'passed': result.returncode == 0,
                            'output': result.stdout,
                            'error': result.stderr if result.stderr else None,
                            'execution_time': 0  # Could be extracted from pytest output
                        }
                        
                        # Update test case status
                        status = 'green' if result.returncode == 0 else 'red'
                        self.db.update_record('test_cases', test_case['id'], {
                            'status': status,
                            'last_run_date': datetime.now().isoformat(),
                            'error_message': result.stderr if result.stderr else None
                        })
                        
                        results['test_results'].append(test_result)
                        results['total_tests'] += 1
                        
                        if result.returncode == 0:
                            results['passing_tests'] += 1
                        else:
                            results['failing_tests'] += 1
                            
                    except subprocess.TimeoutExpired:
                        results['test_results'].append({
                            'test_case_id': test_case['id'],
                            'test_name': test_case['name'],
                            'passed': False,
                            'output': '',
                            'error': 'Test execution timed out',
                            'execution_time': 30.0
                        })
                        results['total_tests'] += 1
                        results['failing_tests'] += 1
            
            # Stop coverage and get results if available
            if cov and coverage_available:
                try:
                    cov.stop()
                    cov.save()
                    
                    # Generate coverage report
                    coverage_data = cov.get_data()
                    measured_files = coverage_data.measured_files()
                    if measured_files:
                        results['coverage_percentage'] = cov.report()
                    else:
                        results['coverage_percentage'] = 0.0
                except:
                    results['coverage_percentage'] = 0.0
            else:
                results['coverage_percentage'] = 0.0
            
            # Update cycle with results
            self.db.update_record('tdd_cycles', cycle_id, {
                'total_tests': results['total_tests'],
                'passing_tests': results['passing_tests'],
                'failing_tests': results['failing_tests'],
                'coverage_percentage': results['coverage_percentage']
            })
            
            return {'success': True, **results}
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return {'success': False, 'error': str(e)}
    
    def implement_failing_test(self, test_case_id: int) -> Dict[str, Any]:
        """Generate implementation code to make a failing test pass"""
        try:
            # Get test case details
            test_case = self.db.get_record('test_cases', test_case_id)
            if not test_case:
                return {'success': False, 'error': 'Test case not found'}
            
            cycle_id = test_case['cycle_id']
            test_code = test_case['test_code']
            
            # Import the real orchestrator for AI assistance
            from real_agent_orchestrator import real_orchestrator, AgentType, TaskPriority
            
            # Create a task for the Code Developer agent to implement the code
            task_id = real_orchestrator.add_task(
                name=f"Implement Code for Test {test_case_id}",
                description=f"""
Analyze the following failing test and implement the minimal code needed to make it pass:

TEST CODE:
{test_code}

Requirements:
1. Write only the minimal code needed to make the test pass
2. Follow the Green phase of TDD (make tests pass with simplest solution)
3. Create proper Python modules/functions/classes as needed
4. Ensure the code is clean and follows Python best practices
5. Include proper error handling if tests expect it
6. Generate actual executable Python code

Focus on making the test pass, not on perfect implementation (that comes in Refactor phase).
                """,
                agent_type=AgentType.CODE_DEVELOPER,
                priority=TaskPriority.HIGH
            )
            
            # Get the task and agent
            task = next(t for t in real_orchestrator.task_queue if t.id == task_id)
            agent = next(a for a in real_orchestrator.agents.values() 
                        if a.agent_type == AgentType.CODE_DEVELOPER)
            
            # Execute the task synchronously
            import asyncio
            result = asyncio.run(agent.execute_task(task))
            
            if result['success']:
                implementation_code = result.get('result', '')
                
                # Save implementation to database
                impl_id = self.db.add_record('code_implementations', {
                    'cycle_id': cycle_id,
                    'test_case_id': test_case_id,
                    'file_path': f"src/implementation_{test_case_id}.py",
                    'function_name': f"implementation_{test_case_id}",
                    'code_content': implementation_code,
                    'iteration': 1,
                    'status': 'draft',
                    'created_date': datetime.now().isoformat()
                })
                
                # Write implementation file
                impl_file = self.src_dir / f"implementation_{test_case_id}.py"
                impl_file.write_text(implementation_code)
                
                return {
                    'success': True,
                    'implementation_id': impl_id,
                    'implementation_file': str(impl_file),
                    'implementation_code': implementation_code,
                    'cost': result.get('cost', 0),
                    'tokens_used': result.get('tokens_used', 0)
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error in code implementation')
                }
                
        except Exception as e:
            logger.error(f"Error implementing failing test: {e}")
            return {'success': False, 'error': str(e)}
    
    def refactor_code(self, implementation_id: int) -> Dict[str, Any]:
        """Refactor implementation code while keeping tests passing"""
        try:
            # Get implementation details
            implementation = self.db.get_record('code_implementations', implementation_id)
            if not implementation:
                return {'success': False, 'error': 'Implementation not found'}
            
            current_code = implementation['code_content']
            test_case_id = implementation['test_case_id']
            
            # Get the related test
            test_case = self.db.get_record('test_cases', test_case_id)
            test_code = test_case['test_code'] if test_case else ""
            
            # Import the real orchestrator for AI assistance
            from real_agent_orchestrator import real_orchestrator, AgentType, TaskPriority
            
            # Create a task for refactoring
            task_id = real_orchestrator.add_task(
                name=f"Refactor Implementation {implementation_id}",
                description=f"""
Refactor the following code while ensuring all tests continue to pass:

CURRENT IMPLEMENTATION:
{current_code}

RELATED TEST:
{test_code}

Requirements:
1. Improve code quality, readability, and maintainability
2. Remove duplication and follow DRY principles
3. Apply appropriate design patterns if beneficial
4. Ensure all existing tests still pass
5. Add proper documentation and comments
6. Optimize performance where possible
7. Follow Python best practices and PEP 8

The refactored code should be functionally equivalent but better structured.
                """,
                agent_type=AgentType.CODE_DEVELOPER,
                priority=TaskPriority.MEDIUM
            )
            
            # Get the task and agent
            task = next(t for t in real_orchestrator.task_queue if t.id == task_id)
            agent = next(a for a in real_orchestrator.agents.values() 
                        if a.agent_type == AgentType.CODE_DEVELOPER)
            
            # Execute the task synchronously
            import asyncio
            result = asyncio.run(agent.execute_task(task))
            
            if result['success']:
                refactored_code = result.get('result', '')
                
                # Save new iteration
                new_iteration = implementation.get('iteration', 1) + 1
                refactor_id = self.db.add_record('code_implementations', {
                    'cycle_id': implementation['cycle_id'],
                    'test_case_id': test_case_id,
                    'file_path': implementation['file_path'],
                    'function_name': implementation['function_name'],
                    'code_content': refactored_code,
                    'iteration': new_iteration,
                    'status': 'refactored',
                    'created_date': datetime.now().isoformat()
                })
                
                # Update implementation file
                impl_file = Path(implementation['file_path'])
                impl_file.write_text(refactored_code)
                
                return {
                    'success': True,
                    'refactor_id': refactor_id,
                    'refactored_code': refactored_code,
                    'iteration': new_iteration,
                    'cost': result.get('cost', 0),
                    'tokens_used': result.get('tokens_used', 0)
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error in code refactoring')
                }
                
        except Exception as e:
            logger.error(f"Error refactoring code: {e}")
            return {'success': False, 'error': str(e)}
    
    def complete_tdd_cycle(self, cycle_id: int, specification: str) -> Dict[str, Any]:
        """Complete a full TDD cycle: Red -> Green -> Refactor"""
        try:
            results = {
                'cycle_id': cycle_id,
                'phases': {},
                'total_cost': 0.0,
                'total_tokens': 0,
                'success': True
            }
            
            # RED Phase: Generate failing tests
            logger.info(f"🔴 RED Phase: Generating tests for cycle {cycle_id}")
            test_result = self.generate_test_from_specification(cycle_id, specification)
            results['phases']['red'] = test_result
            
            if not test_result['success']:
                results['success'] = False
                return results
            
            results['total_cost'] += test_result.get('cost', 0)
            results['total_tokens'] += test_result.get('tokens_used', 0)
            
            # Run tests to confirm they fail
            test_run = self.run_tests(cycle_id)
            results['phases']['red_test_run'] = test_run
            
            if test_run['success'] and test_run['failing_tests'] > 0:
                logger.info(f"✅ RED Phase complete: {test_run['failing_tests']} failing tests")
                
                # GREEN Phase: Implement code to make tests pass
                logger.info(f"🟢 GREEN Phase: Implementing code for cycle {cycle_id}")
                
                test_case_id = test_result['test_case_id']
                impl_result = self.implement_failing_test(test_case_id)
                results['phases']['green'] = impl_result
                
                if impl_result['success']:
                    results['total_cost'] += impl_result.get('cost', 0)
                    results['total_tokens'] += impl_result.get('tokens_used', 0)
                    
                    # Run tests again to confirm they pass
                    green_test_run = self.run_tests(cycle_id)
                    results['phases']['green_test_run'] = green_test_run
                    
                    if green_test_run['success'] and green_test_run['passing_tests'] > 0:
                        logger.info(f"✅ GREEN Phase complete: {green_test_run['passing_tests']} passing tests")
                        
                        # REFACTOR Phase: Improve code quality
                        logger.info(f"🔵 REFACTOR Phase: Refactoring code for cycle {cycle_id}")
                        
                        implementation_id = impl_result['implementation_id']
                        refactor_result = self.refactor_code(implementation_id)
                        results['phases']['refactor'] = refactor_result
                        
                        if refactor_result['success']:
                            results['total_cost'] += refactor_result.get('cost', 0)
                            results['total_tokens'] += refactor_result.get('tokens_used', 0)
                            
                            # Final test run to ensure refactoring didn't break anything
                            final_test_run = self.run_tests(cycle_id)
                            results['phases']['refactor_test_run'] = final_test_run
                            
                            if final_test_run['success'] and final_test_run['passing_tests'] > 0:
                                logger.info(f"✅ REFACTOR Phase complete: All tests still passing")
                                
                                # Mark cycle as completed
                                self.db.update_record('tdd_cycles', cycle_id, {
                                    'status': 'completed',
                                    'completed_date': datetime.now().isoformat()
                                })
                            else:
                                results['success'] = False
                        else:
                            results['success'] = False
                    else:
                        results['success'] = False
                else:
                    results['success'] = False
            else:
                results['success'] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Error completing TDD cycle: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_cycle_status(self, cycle_id: int) -> Dict[str, Any]:
        """Get comprehensive status of a TDD cycle"""
        try:
            cycle = self.db.get_record('tdd_cycles', cycle_id)
            if not cycle:
                return {'success': False, 'error': 'Cycle not found'}
            
            test_cases = [tc for tc in self.db.get_table_data('test_cases') 
                         if tc.get('cycle_id') == cycle_id]
            
            implementations = [impl for impl in self.db.get_table_data('code_implementations') 
                             if impl.get('cycle_id') == cycle_id]
            
            return {
                'success': True,
                'cycle': cycle,
                'test_cases': test_cases,
                'implementations': implementations,
                'metrics': {
                    'total_tests': cycle.get('total_tests', 0),
                    'passing_tests': cycle.get('passing_tests', 0),
                    'failing_tests': cycle.get('failing_tests', 0),
                    'coverage_percentage': cycle.get('coverage_percentage', 0.0),
                    'implementation_iterations': len(set(impl.get('test_case_id') for impl in implementations))
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting cycle status: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_all_cycles(self) -> Dict[str, Any]:
        """List all TDD cycles with summary information"""
        try:
            cycles = self.db.get_table_data('tdd_cycles')
            
            cycle_summaries = []
            for cycle in cycles:
                cycle_summaries.append({
                    'id': cycle['id'],
                    'name': cycle['name'],
                    'status': cycle['status'],
                    'created_date': cycle['created_date'],
                    'completed_date': cycle.get('completed_date'),
                    'total_tests': cycle.get('total_tests', 0),
                    'passing_tests': cycle.get('passing_tests', 0),
                    'coverage_percentage': cycle.get('coverage_percentage', 0.0)
                })
            
            return {
                'success': True,
                'cycles': cycle_summaries,
                'total_cycles': len(cycles),
                'active_cycles': len([c for c in cycles if c['status'] == 'active']),
                'completed_cycles': len([c for c in cycles if c['status'] == 'completed'])
            }
            
        except Exception as e:
            logger.error(f"Error listing cycles: {e}")
            return {'success': False, 'error': str(e)}

# Initialize global TDD system
tdd_system = TDDSystem()