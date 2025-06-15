#!/usr/bin/env python3
"""
Routes for code analysis and learning functionality
"""

from flask import Blueprint, render_template, jsonify, request
import logging
import json
import asyncio
from datetime import datetime
import sys
import os

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our analysis engines
try:
    from repository_code_analyzer import repository_analyzer
    from code_learning_engine import code_learning_engine
    from database import NotionLikeDatabase
    analyzer_available = True
    logger.info("✅ Code analysis engines imported successfully")
except Exception as e:
    analyzer_available = False
    logger.error(f"❌ Failed to import analysis engines: {e}")

code_analysis_bp = Blueprint('code_analysis', __name__)
db = NotionLikeDatabase()

@code_analysis_bp.route('/code-analysis')
def code_analysis_dashboard():
    """Main code analysis dashboard"""
    return render_template('code_analysis_modern.html')

@code_analysis_bp.route('/api/repositories/analyze/<path:repo_name>')
def analyze_repository(repo_name):
    """Analyze a specific repository"""
    if not analyzer_available:
        return jsonify({
            "success": False,
            "error": "Code analysis engines not available"
        })
    
    try:
        logger.info(f"🔍 Starting analysis of repository: {repo_name}")
        
        # Get repository info from database
        repositories = db.get_table_data('integrated_repositories')
        repo_info = None
        for repo in repositories:
            if repo['repository_name'] == repo_name:
                repo_info = repo
                break
        
        if not repo_info:
            return jsonify({
                "success": False,
                "error": f"Repository '{repo_name}' not found in integrated repositories"
            })
        
        repo_path = repo_info.get('local_path', '')
        if not repo_path or not os.path.exists(repo_path):
            return jsonify({
                "success": False,
                "error": f"Repository path not found: {repo_path}"
            })
        
        # Perform analysis
        analysis_result = repository_analyzer.analyze_repository(repo_path)
        
        if "error" in analysis_result:
            return jsonify({
                "success": False,
                "error": analysis_result["error"]
            })
        
        # Store analysis results in database
        analysis_record = {
            'repository_name': repo_name,
            'repository_path': repo_path,
            'files_analyzed': analysis_result.get('files_analyzed', 0),
            'lines_of_code': analysis_result.get('summary', {}).get('lines_of_code', 0),
            'functions_count': analysis_result.get('summary', {}).get('functions', 0),
            'classes_count': analysis_result.get('summary', {}).get('classes', 0),
            'complexity_score': analysis_result.get('summary', {}).get('complexity', 0),
            'quality_score': analysis_result.get('quality_metrics', {}).get('documentation_ratio', 0),
            'patterns_detected': json.dumps(analysis_result.get('patterns', {})),
            'architecture_patterns': json.dumps(analysis_result.get('architecture_patterns', [])),
            'analysis_data': json.dumps(analysis_result, default=str),
            'status': 'completed'
        }
        
        db.add_record('code_analysis_results', analysis_record)
        
        logger.info(f"✅ Analysis completed for {repo_name}")
        
        return jsonify({
            "success": True,
            "repository": repo_name,
            "analysis": analysis_result,
            "message": f"Successfully analyzed {repo_name}"
        })
        
    except Exception as e:
        logger.error(f"Error analyzing repository {repo_name}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@code_analysis_bp.route('/api/repositories/learn/<repo_name>')
def learn_from_repository(repo_name):
    """Learn from a specific repository"""
    if not analyzer_available:
        return jsonify({
            "success": False,
            "error": "Code learning engine not available"
        })
    
    try:
        logger.info(f"🧠 Starting learning from repository: {repo_name}")
        
        # Get repository info
        repositories = db.get_table_data('integrated_repositories')
        repo_info = None
        for repo in repositories:
            if repo['repository_name'] == repo_name:
                repo_info = repo
                break
        
        if not repo_info:
            return jsonify({
                "success": False,
                "error": f"Repository '{repo_name}' not found"
            })
        
        repo_path = repo_info.get('local_path', '')
        if not repo_path or not os.path.exists(repo_path):
            return jsonify({
                "success": False,
                "error": f"Repository path not found: {repo_path}"
            })
        
        # Perform learning
        learning_result = code_learning_engine.learn_from_repository(repo_path, repo_name)
        
        if not learning_result.get('success'):
            return jsonify(learning_result)
        
        # Store patterns, insights, and snippets in database
        result_data = learning_result['learning_result']
        
        # Store patterns
        for pattern in result_data.get('patterns', []):
            pattern_record = {
                'pattern_id': pattern.get('pattern_id'),
                'pattern_name': pattern.get('name'),
                'category': pattern.get('category'),
                'description': pattern.get('description'),
                'examples': json.dumps(pattern.get('instances', [])),
                'frequency': pattern.get('frequency', 1),
                'repositories': repo_name,
                'confidence': pattern.get('confidence', 0.5)
            }
            try:
                db.add_record('code_patterns', pattern_record)
            except Exception as e:
                logger.warning(f"Pattern already exists or error storing: {e}")
        
        # Store insights
        for insight in result_data.get('insights', []):
            insight_record = {
                'insight_id': insight.get('insight_id'),
                'title': insight.get('title'),
                'description': insight.get('description'),
                'insight_type': insight.get('insight_type'),
                'examples': json.dumps(insight.get('examples', [])),
                'repositories': repo_name,
                'confidence': insight.get('confidence', 0.5),
                'actionable_advice': json.dumps(insight.get('actionable_advice', []))
            }
            try:
                db.add_record('learning_insights', insight_record)
            except Exception as e:
                logger.warning(f"Insight already exists or error storing: {e}")
        
        # Store code snippets
        for snippet in result_data.get('snippets', []):
            snippet_record = {
                'snippet_id': snippet.get('snippet_id'),
                'title': snippet.get('title'),
                'description': snippet.get('description'),
                'function_name': snippet.get('function_name'),
                'args': json.dumps(snippet.get('args', [])),
                'language': snippet.get('language', 'python'),
                'tags': json.dumps(snippet.get('tags', [])),
                'repository_source': snippet.get('repository_source'),
                'file_path': snippet.get('file_path'),
                'line_start': snippet.get('line_start', 0),
                'line_end': snippet.get('line_end', 0),
                'complexity': snippet.get('complexity', 1),
                'is_async': snippet.get('is_async', False)
            }
            try:
                db.add_record('code_snippets', snippet_record)
            except Exception as e:
                logger.warning(f"Snippet already exists or error storing: {e}")
        
        logger.info(f"✅ Learning completed for {repo_name}")
        
        return jsonify({
            "success": True,
            "repository": repo_name,
            "learning_result": result_data,
            "message": f"Successfully learned from {repo_name}"
        })
        
    except Exception as e:
        logger.error(f"Error learning from repository {repo_name}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@code_analysis_bp.route('/api/repositories/learn-all')
def learn_from_all_repositories():
    """Learn from all integrated repositories"""
    if not analyzer_available:
        return jsonify({
            "success": False,
            "error": "Code learning engine not available"
        })
    
    try:
        logger.info("🧠 Starting learning from all repositories...")
        
        # Perform learning from all repositories
        learning_result = code_learning_engine.learn_from_all_repositories()
        
        logger.info("✅ Completed learning from all repositories")
        
        return jsonify(learning_result)
        
    except Exception as e:
        logger.error(f"Error learning from all repositories: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@code_analysis_bp.route('/api/analysis-results')
def get_analysis_results():
    """Get all code analysis results"""
    try:
        results = db.get_table_data('code_analysis_results')
        
        # Parse JSON fields
        for result in results:
            try:
                result['patterns_detected'] = json.loads(result.get('patterns_detected', '{}'))
                result['architecture_patterns'] = json.loads(result.get('architecture_patterns', '[]'))
            except json.JSONDecodeError:
                result['patterns_detected'] = {}
                result['architecture_patterns'] = []
        
        return jsonify({
            "success": True,
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@code_analysis_bp.route('/api/code-patterns')
def get_code_patterns():
    """Get all learned code patterns"""
    try:
        category = request.args.get('category')
        
        if category:
            patterns = code_learning_engine.get_code_patterns(category)
        else:
            patterns = db.get_table_data('code_patterns')
            
            # Parse JSON fields
            for pattern in patterns:
                try:
                    pattern['examples'] = json.loads(pattern.get('examples', '[]'))
                except json.JSONDecodeError:
                    pattern['examples'] = []
        
        return jsonify({
            "success": True,
            "patterns": patterns
        })
        
    except Exception as e:
        logger.error(f"Error getting code patterns: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@code_analysis_bp.route('/api/learning-insights')
def get_learning_insights():
    """Get all learning insights"""
    try:
        insight_type = request.args.get('type')
        
        if insight_type:
            insights = code_learning_engine.get_learning_insights(insight_type)
        else:
            insights = db.get_table_data('learning_insights')
            
            # Parse JSON fields
            for insight in insights:
                try:
                    insight['examples'] = json.loads(insight.get('examples', '[]'))
                    insight['actionable_advice'] = json.loads(insight.get('actionable_advice', '[]'))
                except json.JSONDecodeError:
                    insight['examples'] = []
                    insight['actionable_advice'] = []
        
        return jsonify({
            "success": True,
            "insights": insights
        })
        
    except Exception as e:
        logger.error(f"Error getting learning insights: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@code_analysis_bp.route('/api/code-snippets')
def get_code_snippets():
    """Get all code snippets"""
    try:
        snippets = db.get_table_data('code_snippets')
        
        # Parse JSON fields
        for snippet in snippets:
            try:
                snippet['args'] = json.loads(snippet.get('args', '[]'))
                snippet['tags'] = json.loads(snippet.get('tags', '[]'))
            except json.JSONDecodeError:
                snippet['args'] = []
                snippet['tags'] = []
        
        return jsonify({
            "success": True,
            "snippets": snippets
        })
        
    except Exception as e:
        logger.error(f"Error getting code snippets: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@code_analysis_bp.route('/api/repositories/integrated')
def get_integrated_repositories():
    """Get all integrated repositories"""
    try:
        repositories = db.get_table_data('integrated_repositories')
        
        return jsonify({
            "success": True,
            "repositories": repositories
        })
        
    except Exception as e:
        logger.error(f"Error getting integrated repositories: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@code_analysis_bp.route('/api/analysis-summary')
def get_analysis_summary():
    """Get analysis summary statistics"""
    try:
        # Get analysis results
        analysis_results = db.get_table_data('code_analysis_results')
        patterns = db.get_table_data('code_patterns')
        insights = db.get_table_data('learning_insights')
        snippets = db.get_table_data('code_snippets')
        
        # Calculate summary statistics
        total_repos = len(analysis_results)
        total_loc = sum(result.get('lines_of_code', 0) for result in analysis_results)
        total_functions = sum(result.get('functions_count', 0) for result in analysis_results)
        total_classes = sum(result.get('classes_count', 0) for result in analysis_results)
        avg_quality = sum(result.get('quality_score', 0) for result in analysis_results) / max(total_repos, 1)
        
        # Pattern categories
        pattern_categories = {}
        for pattern in patterns:
            category = pattern.get('category', 'unknown')
            pattern_categories[category] = pattern_categories.get(category, 0) + 1
        
        # Insight types
        insight_types = {}
        for insight in insights:
            insight_type = insight.get('insight_type', 'unknown')
            insight_types[insight_type] = insight_types.get(insight_type, 0) + 1
        
        summary = {
            "repositories_analyzed": total_repos,
            "total_lines_of_code": total_loc,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "average_quality_score": round(avg_quality, 2),
            "patterns_learned": len(patterns),
            "insights_generated": len(insights),
            "code_snippets": len(snippets),
            "pattern_categories": pattern_categories,
            "insight_types": insight_types,
            "last_analysis": max([r.get('analysis_date', '') for r in analysis_results], default='Never')
        }
        
        return jsonify({
            "success": True,
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis summary: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })