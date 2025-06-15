#!/usr/bin/env python3
"""
Code Learning Engine
Extracts insights and learning patterns from analyzed code repositories
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Set, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from pathlib import Path

from repository_code_analyzer import RepositoryAnalyzer
from database import NotionLikeDatabase

logger = logging.getLogger(__name__)

@dataclass
class CodePattern:
    """Represents a learned code pattern"""
    pattern_id: str
    name: str
    description: str
    category: str
    examples: List[str]
    frequency: int
    repositories: List[str]
    confidence: float
    created_date: str

@dataclass
class LearningInsight:
    """Represents a learning insight from code analysis"""
    insight_id: str
    title: str
    description: str
    insight_type: str  # 'pattern', 'best_practice', 'anti_pattern', 'architecture'
    examples: List[str]
    repositories: List[str]
    confidence: float
    actionable_advice: List[str]
    created_date: str

@dataclass
class CodeSnippet:
    """Represents a reusable code snippet"""
    snippet_id: str
    title: str
    description: str
    code: str
    language: str
    tags: List[str]
    use_cases: List[str]
    repository_source: str
    file_path: str
    line_start: int
    line_end: int
    created_date: str

class CodeLearningEngine:
    """Engine for learning from analyzed code repositories"""
    
    def __init__(self):
        self.repository_analyzer = RepositoryAnalyzer()
        self.db = NotionLikeDatabase()
        self.learned_patterns = {}
        self.insights = {}
        self.code_snippets = {}
        
        # Initialize learning categories
        self.learning_categories = {
            'architecture_patterns': {
                'weight': 1.0,
                'keywords': ['pattern', 'architecture', 'design', 'structure']
            },
            'best_practices': {
                'weight': 0.8,
                'keywords': ['practice', 'convention', 'standard', 'quality']
            },
            'common_solutions': {
                'weight': 0.9,
                'keywords': ['solution', 'implementation', 'approach', 'method']
            },
            'optimization_techniques': {
                'weight': 0.7,
                'keywords': ['optimization', 'performance', 'efficiency', 'speed']
            },
            'error_handling': {
                'weight': 0.8,
                'keywords': ['error', 'exception', 'try', 'catch', 'handle']
            },
            'testing_patterns': {
                'weight': 0.6,
                'keywords': ['test', 'mock', 'assert', 'fixture', 'pytest']
            }
        }
    
    def learn_from_repository(self, repo_path: str, repo_name: str) -> Dict[str, Any]:
        """Learn from a single repository"""
        logger.info(f"🧠 Learning from repository: {repo_name}")
        
        # First analyze the repository
        analysis = self.repository_analyzer.analyze_repository(repo_path)
        if "error" in analysis:
            return {"success": False, "error": analysis["error"]}
        
        # Extract patterns
        patterns = self._extract_patterns(analysis, repo_name)
        
        # Generate insights
        insights = self._generate_insights(analysis, repo_name)
        
        # Extract code snippets
        snippets = self._extract_code_snippets(analysis, repo_name)
        
        # Store learning results
        learning_result = {
            "repository": repo_name,
            "analysis_date": datetime.now().isoformat(),
            "patterns_learned": len(patterns),
            "insights_generated": len(insights),
            "snippets_extracted": len(snippets),
            "patterns": patterns,
            "insights": insights,
            "snippets": snippets,
            "summary": self._generate_learning_summary(analysis, patterns, insights)
        }
        
        # Store in database
        self._store_learning_results(learning_result)
        
        return {"success": True, "learning_result": learning_result}
    
    def learn_from_all_repositories(self) -> Dict[str, Any]:
        """Learn from all integrated repositories"""
        logger.info("🧠 Learning from all integrated repositories...")
        
        # Get all integrated repositories
        repositories = self.db.get_table_data('integrated_repositories')
        if not repositories:
            return {"success": False, "error": "No integrated repositories found"}
        
        all_learnings = []
        total_patterns = 0
        total_insights = 0
        total_snippets = 0
        
        for repo in repositories:
            repo_path = repo.get('local_path', '')
            repo_name = repo.get('repository_name', 'Unknown')
            
            if not repo_path or not Path(repo_path).exists():
                logger.warning(f"Repository path not found: {repo_path}")
                continue
            
            try:
                learning = self.learn_from_repository(repo_path, repo_name)
                if learning.get('success'):
                    result = learning['learning_result']
                    all_learnings.append(result)
                    total_patterns += result['patterns_learned']
                    total_insights += result['insights_generated']
                    total_snippets += result['snippets_extracted']
                
            except Exception as e:
                logger.error(f"Error learning from {repo_name}: {e}")
                continue
        
        # Generate cross-repository insights
        cross_insights = self._generate_cross_repository_insights(all_learnings)
        
        return {
            "success": True,
            "repositories_processed": len(all_learnings),
            "total_patterns": total_patterns,
            "total_insights": total_insights,
            "total_snippets": total_snippets,
            "cross_repository_insights": cross_insights,
            "learnings": all_learnings
        }
    
    def _extract_patterns(self, analysis: Dict[str, Any], repo_name: str) -> List[Dict[str, Any]]:
        """Extract code patterns from analysis"""
        patterns = []
        pattern_id_counter = 0
        
        # Extract patterns from detected frameworks and libraries
        for pattern_type, instances in analysis.get('patterns', {}).items():
            if instances:
                pattern_id_counter += 1
                pattern = {
                    "pattern_id": f"{repo_name}_pattern_{pattern_id_counter}",
                    "name": f"{pattern_type.replace('_', ' ').title()} Usage Pattern",
                    "description": f"Implementation pattern for {pattern_type} in {repo_name}",
                    "category": pattern_type,
                    "instances": instances,
                    "frequency": len(instances),
                    "repository": repo_name,
                    "confidence": min(len(instances) / 10.0, 1.0),  # Max confidence at 10+ instances
                    "created_date": datetime.now().isoformat()
                }
                patterns.append(pattern)
        
        # Extract architectural patterns
        for arch_pattern in analysis.get('architecture_patterns', []):
            pattern_id_counter += 1
            pattern = {
                "pattern_id": f"{repo_name}_arch_{pattern_id_counter}",
                "name": f"{arch_pattern.replace('_', ' ').title()} Architecture Pattern",
                "description": f"Architectural pattern implementation in {repo_name}",
                "category": "architecture",
                "instances": [arch_pattern],
                "frequency": 1,
                "repository": repo_name,
                "confidence": 0.8,
                "created_date": datetime.now().isoformat()
            }
            patterns.append(pattern)
        
        # Extract function patterns from common implementations
        function_patterns = self._analyze_function_patterns(analysis, repo_name)
        patterns.extend(function_patterns)
        
        return patterns
    
    def _analyze_function_patterns(self, analysis: Dict[str, Any], repo_name: str) -> List[Dict[str, Any]]:
        """Analyze function patterns across files"""
        patterns = []
        function_names = []
        
        # Collect all function names
        for file_analysis in analysis.get('file_details', []):
            for func in file_analysis.get('functions', []):
                function_names.append(func['name'])
        
        # Find common function name patterns
        name_patterns = Counter()
        for name in function_names:
            # Check for common prefixes
            if name.startswith('get_'):
                name_patterns['getter_pattern'] += 1
            elif name.startswith('set_'):
                name_patterns['setter_pattern'] += 1
            elif name.startswith('is_') or name.startswith('has_'):
                name_patterns['predicate_pattern'] += 1
            elif name.startswith('_'):
                name_patterns['private_method_pattern'] += 1
            elif 'process' in name.lower():
                name_patterns['processor_pattern'] += 1
            elif 'handle' in name.lower():
                name_patterns['handler_pattern'] += 1
        
        # Create patterns for common naming conventions
        for pattern_name, count in name_patterns.items():
            if count >= 3:  # Only if pattern appears 3+ times
                pattern = {
                    "pattern_id": f"{repo_name}_func_{pattern_name}",
                    "name": f"{pattern_name.replace('_', ' ').title()}",
                    "description": f"Function naming convention pattern in {repo_name}",
                    "category": "naming_convention",
                    "instances": [pattern_name],
                    "frequency": count,
                    "repository": repo_name,
                    "confidence": min(count / 10.0, 1.0),
                    "created_date": datetime.now().isoformat()
                }
                patterns.append(pattern)
        
        return patterns
    
    def _generate_insights(self, analysis: Dict[str, Any], repo_name: str) -> List[Dict[str, Any]]:
        """Generate learning insights from analysis"""
        insights = []
        insight_id_counter = 0
        
        # Code quality insights
        quality = analysis.get('quality_metrics', {})
        doc_ratio = quality.get('documentation_ratio', 0)
        
        if doc_ratio > 0.7:
            insight_id_counter += 1
            insights.append({
                "insight_id": f"{repo_name}_insight_{insight_id_counter}",
                "title": "Excellent Documentation Practices",
                "description": f"{repo_name} demonstrates excellent documentation with {doc_ratio:.1%} of functions documented",
                "insight_type": "best_practice",
                "examples": ["High documentation ratio", "Consistent docstring usage"],
                "repository": repo_name,
                "confidence": 0.9,
                "actionable_advice": [
                    "Maintain documentation standards for all new code",
                    "Use similar docstring patterns in other projects",
                    "Consider automated documentation generation"
                ],
                "created_date": datetime.now().isoformat()
            })
        
        # Complexity insights
        avg_complexity = analysis.get('summary', {}).get('avg_complexity', 0)
        if avg_complexity < 5:
            insight_id_counter += 1
            insights.append({
                "insight_id": f"{repo_name}_insight_{insight_id_counter}",
                "title": "Well-Structured Code Complexity",
                "description": f"{repo_name} maintains low cyclomatic complexity (avg: {avg_complexity:.1f})",
                "insight_type": "best_practice",
                "examples": ["Low cyclomatic complexity", "Well-structured functions"],
                "repository": repo_name,
                "confidence": 0.8,
                "actionable_advice": [
                    "Continue breaking down complex functions",
                    "Use similar complexity management techniques",
                    "Apply SOLID principles consistently"
                ],
                "created_date": datetime.now().isoformat()
            })
        
        # Technology stack insights
        patterns = analysis.get('patterns', {})
        if 'async_patterns' in patterns and 'web_frameworks' in patterns:
            insight_id_counter += 1
            insights.append({
                "insight_id": f"{repo_name}_insight_{insight_id_counter}",
                "title": "Modern Async Web Development",
                "description": f"{repo_name} combines async programming with web frameworks for better performance",
                "insight_type": "architecture",
                "examples": patterns['async_patterns'] + patterns['web_frameworks'],
                "repository": repo_name,
                "confidence": 0.85,
                "actionable_advice": [
                    "Apply async patterns in I/O heavy operations",
                    "Use async web frameworks for scalability",
                    "Implement proper error handling in async code"
                ],
                "created_date": datetime.now().isoformat()
            })
        
        # Testing insights
        if 'testing' in patterns:
            insight_id_counter += 1
            insights.append({
                "insight_id": f"{repo_name}_insight_{insight_id_counter}",
                "title": "Comprehensive Testing Strategy",
                "description": f"{repo_name} implements testing patterns for code reliability",
                "insight_type": "best_practice",
                "examples": patterns['testing'],
                "repository": repo_name,
                "confidence": 0.8,
                "actionable_advice": [
                    "Maintain test coverage above 80%",
                    "Use similar testing patterns in other projects",
                    "Implement continuous integration testing"
                ],
                "created_date": datetime.now().isoformat()
            })
        
        return insights
    
    def _extract_code_snippets(self, analysis: Dict[str, Any], repo_name: str) -> List[Dict[str, Any]]:
        """Extract reusable code snippets"""
        snippets = []
        snippet_id_counter = 0
        
        # Extract interesting functions as snippets
        for file_analysis in analysis.get('file_details', []):
            file_path = file_analysis.get('file_path', '')
            
            for func in file_analysis.get('functions', []):
                # Focus on well-documented, non-trivial functions
                if (func.get('docstring') and 
                    len(func.get('args', [])) > 0 and 
                    func.get('complexity', 0) > 2 and 
                    func.get('complexity', 0) < 10):
                    
                    snippet_id_counter += 1
                    snippet = {
                        "snippet_id": f"{repo_name}_snippet_{snippet_id_counter}",
                        "title": f"{func['name']} - {repo_name}",
                        "description": func.get('docstring', f"Function {func['name']} from {repo_name}"),
                        "function_name": func['name'],
                        "args": func.get('args', []),
                        "is_async": func.get('is_async', False),
                        "complexity": func.get('complexity', 0),
                        "language": "python",
                        "tags": self._generate_snippet_tags(func, file_analysis),
                        "repository_source": repo_name,
                        "file_path": file_path,
                        "line_start": func.get('line_start', 0),
                        "line_end": func.get('line_end', 0),
                        "created_date": datetime.now().isoformat()
                    }
                    snippets.append(snippet)
        
        return snippets
    
    def _generate_snippet_tags(self, func: Dict[str, Any], file_analysis: Dict[str, Any]) -> List[str]:
        """Generate tags for code snippets"""
        tags = []
        
        # Function-based tags
        if func.get('is_async'):
            tags.append('async')
        if func.get('decorators'):
            tags.append('decorated')
        if 'test' in func.get('name', '').lower():
            tags.append('testing')
        
        # Pattern-based tags
        patterns = file_analysis.get('patterns', {})
        for pattern_type in patterns.keys():
            tags.append(pattern_type)
        
        # Complexity-based tags
        complexity = func.get('complexity', 0)
        if complexity <= 3:
            tags.append('simple')
        elif complexity <= 6:
            tags.append('moderate')
        else:
            tags.append('complex')
        
        return tags
    
    def _generate_learning_summary(self, analysis: Dict[str, Any], patterns: List[Dict], insights: List[Dict]) -> Dict[str, Any]:
        """Generate a summary of learning from the repository"""
        summary = analysis.get('summary', {})
        
        return {
            "code_metrics": {
                "lines_of_code": summary.get('lines_of_code', 0),
                "functions": summary.get('functions', 0),
                "classes": summary.get('classes', 0),
                "complexity": summary.get('complexity', 0)
            },
            "learning_metrics": {
                "patterns_discovered": len(patterns),
                "insights_generated": len(insights),
                "primary_technologies": list(analysis.get('patterns', {}).keys())[:5],
                "architecture_patterns": analysis.get('architecture_patterns', [])
            },
            "quality_assessment": {
                "documentation_quality": "excellent" if analysis.get('quality_metrics', {}).get('documentation_ratio', 0) > 0.7 else "good",
                "complexity_management": "excellent" if summary.get('avg_complexity', 0) < 5 else "good",
                "overall_rating": self._calculate_overall_rating(analysis)
            }
        }
    
    def _calculate_overall_rating(self, analysis: Dict[str, Any]) -> str:
        """Calculate overall code quality rating"""
        score = 0
        
        # Documentation score (0-30 points)
        doc_ratio = analysis.get('quality_metrics', {}).get('documentation_ratio', 0)
        score += min(doc_ratio * 30, 30)
        
        # Complexity score (0-25 points)
        avg_complexity = analysis.get('summary', {}).get('avg_complexity', 10)
        complexity_score = max(25 - (avg_complexity - 1) * 5, 0)
        score += complexity_score
        
        # Pattern usage score (0-25 points)
        pattern_count = len(analysis.get('patterns', {}))
        score += min(pattern_count * 3, 25)
        
        # Architecture score (0-20 points)
        arch_count = len(analysis.get('architecture_patterns', []))
        score += min(arch_count * 5, 20)
        
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "needs_improvement"
    
    def _generate_cross_repository_insights(self, all_learnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate insights across multiple repositories"""
        cross_insights = []
        
        # Analyze common patterns across repositories
        pattern_frequency = defaultdict(int)
        for learning in all_learnings:
            for pattern in learning.get('patterns', []):
                pattern_frequency[pattern['category']] += 1
        
        # Generate insights for common patterns
        for pattern_type, frequency in pattern_frequency.items():
            if frequency >= len(all_learnings) * 0.5:  # Appears in 50%+ of repos
                cross_insights.append({
                    "title": f"Common {pattern_type.replace('_', ' ').title()} Pattern",
                    "description": f"{pattern_type} appears in {frequency}/{len(all_learnings)} repositories",
                    "insight_type": "cross_repository_pattern",
                    "frequency": frequency,
                    "confidence": frequency / len(all_learnings),
                    "recommendation": f"Consider standardizing {pattern_type} usage across all projects"
                })
        
        return cross_insights
    
    def _store_learning_results(self, learning_result: Dict[str, Any]):
        """Store learning results in database"""
        try:
            # Store in knowledge hub
            self.db.add_record('knowledge_hub', {
                'title': f"Code Learning: {learning_result['repository']}",
                'content': json.dumps(learning_result, default=str),
                'category': 'Code Learning',
                'source': learning_result['repository'],
                'tags': 'code,learning,analysis,patterns',
                'status': 'Active',
                'created_date': datetime.now().isoformat()
            })
            
            logger.info(f"✅ Stored learning results for {learning_result['repository']}")
            
        except Exception as e:
            logger.error(f"Error storing learning results: {e}")
    
    def get_learning_insights(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get stored learning insights"""
        try:
            # Get from knowledge hub
            entries = self.db.get_table_data('knowledge_hub')
            learning_entries = [e for e in entries if e.get('category') == 'Code Learning']
            
            insights = []
            for entry in learning_entries:
                try:
                    content = json.loads(entry.get('content', '{}'))
                    if category:
                        # Filter by category
                        filtered_insights = [i for i in content.get('insights', []) if i.get('insight_type') == category]
                        if filtered_insights:
                            insights.extend(filtered_insights)
                    else:
                        insights.extend(content.get('insights', []))
                except json.JSONDecodeError:
                    continue
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting learning insights: {e}")
            return []
    
    def get_code_patterns(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get learned code patterns"""
        try:
            entries = self.db.get_table_data('knowledge_hub')
            learning_entries = [e for e in entries if e.get('category') == 'Code Learning']
            
            patterns = []
            for entry in learning_entries:
                try:
                    content = json.loads(entry.get('content', '{}'))
                    if category:
                        filtered_patterns = [p for p in content.get('patterns', []) if p.get('category') == category]
                        if filtered_patterns:
                            patterns.extend(filtered_patterns)
                    else:
                        patterns.extend(content.get('patterns', []))
                except json.JSONDecodeError:
                    continue
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error getting code patterns: {e}")
            return []

# Global instance
code_learning_engine = CodeLearningEngine()