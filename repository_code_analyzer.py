#!/usr/bin/env python3
"""
Repository Code Analysis Engine
Analyzes Python code files to extract patterns, structures, and insights
"""

import os
import ast
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class CodeMetrics:
    """Metrics for a code file"""
    lines_of_code: int
    complexity: int
    functions: int
    classes: int
    imports: int
    comments: int
    docstrings: int

@dataclass
class FunctionInfo:
    """Information about a function"""
    name: str
    args: List[str]
    returns: Optional[str]
    docstring: Optional[str]
    line_start: int
    line_end: int
    complexity: int
    is_async: bool
    decorators: List[str]

@dataclass
class ClassInfo:
    """Information about a class"""
    name: str
    bases: List[str]
    methods: List[str]
    docstring: Optional[str]
    line_start: int
    line_end: int
    decorators: List[str]

@dataclass
class ImportInfo:
    """Information about imports"""
    module: str
    alias: Optional[str]
    is_from_import: bool
    imported_names: List[str]

class CodeAnalyzer:
    """Analyzes Python code files for patterns and structure"""
    
    def __init__(self):
        self.patterns = {
            'web_frameworks': ['flask', 'django', 'fastapi', 'tornado', 'bottle'],
            'databases': ['sqlite3', 'sqlalchemy', 'pymongo', 'psycopg2', 'mysql'],
            'ai_ml': ['numpy', 'pandas', 'sklearn', 'tensorflow', 'torch', 'transformers'],
            'async_patterns': ['asyncio', 'aiohttp', 'async', 'await'],
            'testing': ['pytest', 'unittest', 'mock', 'test_', 'assert'],
            'logging': ['logging', 'logger', 'log'],
            'api_clients': ['requests', 'httpx', 'urllib'],
            'data_processing': ['json', 'csv', 'xml', 'yaml', 'pickle'],
            'cli_tools': ['argparse', 'click', 'typer', 'sys.argv'],
            'gui_frameworks': ['tkinter', 'PyQt', 'kivy', 'streamlit', 'gradio']
        }
        
        self.architecture_patterns = {
            'mvc': ['models', 'views', 'controllers'],
            'microservices': ['service', 'api', 'endpoint'],
            'observer': ['observer', 'subject', 'notify'],
            'singleton': ['singleton', '__instance'],
            'factory': ['factory', 'create_', 'builder'],
            'decorator': ['decorator', 'wrapper', '@'],
            'adapter': ['adapter', 'wrapper'],
            'strategy': ['strategy', 'algorithm']
        }
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                logger.warning(f"Syntax error in {file_path}: {e}")
                return {"error": f"Syntax error: {e}"}
            
            # Extract information
            result = {
                "file_path": file_path,
                "metrics": self._calculate_metrics(content, tree),
                "functions": self._extract_functions(tree),
                "classes": self._extract_classes(tree),
                "imports": self._extract_imports(tree),
                "patterns": self._detect_patterns(content, tree),
                "architecture": self._detect_architecture_patterns(content),
                "complexity": self._calculate_complexity(tree),
                "documentation": self._analyze_documentation(tree, content),
                "analysis_date": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {"error": str(e)}
    
    def _calculate_metrics(self, content: str, tree: ast.AST) -> CodeMetrics:
        """Calculate basic code metrics"""
        lines = content.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        functions = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
        classes = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
        imports = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])
        
        comments = len([line for line in lines if line.strip().startswith('#')])
        docstrings = len([node for node in ast.walk(tree) if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)])
        
        return CodeMetrics(
            lines_of_code=loc,
            complexity=self._calculate_complexity(tree),
            functions=functions,
            classes=classes,
            imports=imports,
            comments=comments,
            docstrings=docstrings
        )
    
    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function information"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "returns": ast.unparse(node.returns) if node.returns else None,
                    "docstring": ast.get_docstring(node),
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "is_async": False,
                    "decorators": [ast.unparse(dec) for dec in node.decorator_list],
                    "complexity": self._calculate_function_complexity(node)
                }
                functions.append(func_info)
            
            elif isinstance(node, ast.AsyncFunctionDef):
                func_info = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "returns": ast.unparse(node.returns) if node.returns else None,
                    "docstring": ast.get_docstring(node),
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "is_async": True,
                    "decorators": [ast.unparse(dec) for dec in node.decorator_list],
                    "complexity": self._calculate_function_complexity(node)
                }
                functions.append(func_info)
        
        return functions
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class information"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(item.name)
                
                class_info = {
                    "name": node.name,
                    "bases": [ast.unparse(base) for base in node.bases],
                    "methods": methods,
                    "docstring": ast.get_docstring(node),
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "decorators": [ast.unparse(dec) for dec in node.decorator_list]
                }
                classes.append(class_info)
        
        return classes
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract import information"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_info = {
                        "module": alias.name,
                        "alias": alias.asname,
                        "is_from_import": False,
                        "imported_names": [alias.name]
                    }
                    imports.append(import_info)
            
            elif isinstance(node, ast.ImportFrom):
                imported_names = [alias.name for alias in node.names]
                import_info = {
                    "module": node.module or "",
                    "alias": None,
                    "is_from_import": True,
                    "imported_names": imported_names
                }
                imports.append(import_info)
        
        return imports
    
    def _detect_patterns(self, content: str, tree: ast.AST) -> Dict[str, List[str]]:
        """Detect coding patterns and frameworks"""
        detected = defaultdict(list)
        content_lower = content.lower()
        
        # Import-based detection
        imports = self._extract_imports(tree)
        all_imports = []
        for imp in imports:
            all_imports.extend(imp['imported_names'])
            if imp['module']:
                all_imports.append(imp['module'])
        
        # Check patterns
        for pattern_type, keywords in self.patterns.items():
            for keyword in keywords:
                if any(keyword in imp.lower() for imp in all_imports):
                    detected[pattern_type].append(f"import: {keyword}")
                elif keyword in content_lower:
                    detected[pattern_type].append(f"usage: {keyword}")
        
        return dict(detected)
    
    def _detect_architecture_patterns(self, content: str) -> List[str]:
        """Detect architecture patterns"""
        detected = []
        content_lower = content.lower()
        
        for pattern, keywords in self.architecture_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                detected.append(pattern)
        
        return detected
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _calculate_function_complexity(self, func_node: ast.AST) -> int:
        """Calculate complexity for a specific function"""
        complexity = 1
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _analyze_documentation(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Analyze documentation quality"""
        lines = content.split('\n')
        
        # Count docstrings
        docstring_count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                if ast.get_docstring(node):
                    docstring_count += 1
        
        # Count comments
        comment_lines = [line for line in lines if line.strip().startswith('#')]
        
        # Calculate documentation ratio
        total_definitions = len([node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))])
        doc_ratio = docstring_count / max(total_definitions, 1)
        
        return {
            "docstring_count": docstring_count,
            "comment_lines": len(comment_lines),
            "total_definitions": total_definitions,
            "documentation_ratio": doc_ratio,
            "well_documented": doc_ratio > 0.5
        }

class RepositoryAnalyzer:
    """Analyzes entire repositories for patterns and insights"""
    
    def __init__(self):
        self.code_analyzer = CodeAnalyzer()
    
    def analyze_repository(self, repo_path: str) -> Dict[str, Any]:
        """Analyze an entire repository"""
        logger.info(f"🔍 Analyzing repository: {repo_path}")
        
        if not os.path.exists(repo_path):
            return {"error": f"Repository path does not exist: {repo_path}"}
        
        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        if not python_files:
            return {"error": "No Python files found in repository"}
        
        # Analyze each file
        file_analyses = []
        for file_path in python_files:
            analysis = self.code_analyzer.analyze_file(file_path)
            if "error" not in analysis:
                file_analyses.append(analysis)
        
        # Aggregate results
        return self._aggregate_repository_analysis(repo_path, file_analyses)
    
    def _aggregate_repository_analysis(self, repo_path: str, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate analysis results from all files"""
        if not file_analyses:
            return {"error": "No files could be analyzed"}
        
        # Aggregate metrics
        total_loc = sum(analysis["metrics"].lines_of_code for analysis in file_analyses)
        total_functions = sum(len(analysis["functions"]) for analysis in file_analyses)
        total_classes = sum(len(analysis["classes"]) for analysis in file_analyses)
        total_complexity = sum(analysis["complexity"] for analysis in file_analyses)
        
        # Aggregate patterns
        all_patterns = defaultdict(set)
        for analysis in file_analyses:
            for pattern_type, instances in analysis["patterns"].items():
                all_patterns[pattern_type].update(instances)
        
        # Aggregate architecture patterns
        all_architecture = set()
        for analysis in file_analyses:
            all_architecture.update(analysis["architecture"])
        
        # Find most common imports
        all_imports = []
        for analysis in file_analyses:
            for imp in analysis["imports"]:
                all_imports.extend(imp["imported_names"])
                if imp["module"]:
                    all_imports.append(imp["module"])
        
        common_imports = Counter(all_imports).most_common(10)
        
        # Calculate quality metrics
        total_definitions = sum(analysis["documentation"]["total_definitions"] for analysis in file_analyses)
        total_documented = sum(analysis["documentation"]["docstring_count"] for analysis in file_analyses)
        doc_ratio = total_documented / max(total_definitions, 1)
        
        # Extract key learnings
        learnings = self._extract_learnings(file_analyses, all_patterns, all_architecture)
        
        return {
            "repository_path": repo_path,
            "analysis_date": datetime.now().isoformat(),
            "files_analyzed": len(file_analyses),
            "summary": {
                "lines_of_code": total_loc,
                "functions": total_functions,
                "classes": total_classes,
                "complexity": total_complexity,
                "avg_complexity": total_complexity / max(len(file_analyses), 1)
            },
            "patterns": {k: list(v) for k, v in all_patterns.items()},
            "architecture_patterns": list(all_architecture),
            "common_imports": common_imports,
            "quality_metrics": {
                "documentation_ratio": doc_ratio,
                "well_documented": doc_ratio > 0.5,
                "total_definitions": total_definitions,
                "documented_definitions": total_documented
            },
            "learnings": learnings,
            "file_details": file_analyses
        }
    
    def _extract_learnings(self, file_analyses: List[Dict[str, Any]], patterns: Dict[str, Set], architecture: Set) -> Dict[str, Any]:
        """Extract key learnings from the repository analysis"""
        learnings = {
            "technologies": [],
            "patterns": [],
            "best_practices": [],
            "code_quality": [],
            "architecture_insights": []
        }
        
        # Technology learnings
        if "web_frameworks" in patterns:
            learnings["technologies"].append("Uses web frameworks for HTTP applications")
        if "databases" in patterns:
            learnings["technologies"].append("Implements database integration patterns")
        if "ai_ml" in patterns:
            learnings["technologies"].append("Incorporates AI/ML capabilities")
        if "async_patterns" in patterns:
            learnings["technologies"].append("Uses async programming patterns")
        
        # Pattern learnings
        if "testing" in patterns:
            learnings["patterns"].append("Implements comprehensive testing patterns")
        if "logging" in patterns:
            learnings["patterns"].append("Uses structured logging approaches")
        if "api_clients" in patterns:
            learnings["patterns"].append("Implements API client patterns")
        
        # Architecture insights
        for arch_pattern in architecture:
            learnings["architecture_insights"].append(f"Implements {arch_pattern} pattern")
        
        # Code quality insights
        avg_doc_ratio = sum(analysis["documentation"]["documentation_ratio"] for analysis in file_analyses) / len(file_analyses)
        if avg_doc_ratio > 0.7:
            learnings["best_practices"].append("Excellent documentation practices")
        elif avg_doc_ratio > 0.3:
            learnings["best_practices"].append("Good documentation practices")
        else:
            learnings["code_quality"].append("Documentation could be improved")
        
        return learnings

# Global instance
repository_analyzer = RepositoryAnalyzer()