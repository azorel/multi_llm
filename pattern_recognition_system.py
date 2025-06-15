#!/usr/bin/env python3
"""
Advanced Code Pattern Recognition System
Identifies and extracts reusable patterns from analyzed codebases
"""

import re
import ast
import json
import os
import logging
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from repository_code_analyzer import RepositoryAnalyzer
from database import NotionLikeDatabase

logger = logging.getLogger(__name__)

@dataclass
class DesignPattern:
    """Represents a detected design pattern"""
    pattern_name: str
    pattern_type: str  # creational, structural, behavioral
    confidence: float
    evidence: List[str]
    implementation_files: List[str]
    code_examples: List[str]
    benefits: List[str]
    usage_context: str

@dataclass
class ArchitecturalPattern:
    """Represents an architectural pattern"""
    pattern_name: str
    description: str
    components: List[str]
    relationships: List[str]
    implementation_evidence: List[str]
    scalability_notes: str
    trade_offs: List[str]

@dataclass
class CodingPattern:
    """Represents a coding pattern or idiom"""
    pattern_name: str
    category: str
    code_snippet: str
    use_cases: List[str]
    frequency: int
    complexity_reduction: float
    maintainability_impact: str

class PatternRecognitionSystem:
    """Advanced system for recognizing code patterns"""
    
    def __init__(self):
        self.db = NotionLikeDatabase()
        self.repository_analyzer = RepositoryAnalyzer()
        
        # Design pattern signatures
        self.design_patterns = {
            'singleton': {
                'type': 'creational',
                'indicators': ['__instance', '__new__', '_instance', 'getInstance'],
                'anti_indicators': ['__init__', 'multiple'],
                'file_patterns': ['singleton', 'instance'],
                'benefits': ['Controlled instantiation', 'Global access point', 'Lazy initialization']
            },
            'factory': {
                'type': 'creational',
                'indicators': ['factory', 'create', 'build', 'make', 'Factory'],
                'anti_indicators': [],
                'file_patterns': ['factory', 'creator', 'builder'],
                'benefits': ['Loose coupling', 'Easy to extend', 'Centralized creation logic']
            },
            'observer': {
                'type': 'behavioral',
                'indicators': ['observer', 'notify', 'subscribe', 'listener', 'signal'],
                'anti_indicators': [],
                'file_patterns': ['observer', 'listener', 'signal'],
                'benefits': ['Loose coupling', 'Dynamic relationships', 'Event-driven architecture']
            },
            'decorator': {
                'type': 'structural',
                'indicators': ['@', 'decorator', 'wrap', 'middleware'],
                'anti_indicators': [],
                'file_patterns': ['decorator', 'wrapper', 'middleware'],
                'benefits': ['Runtime behavior modification', 'Single responsibility', 'Open/closed principle']
            },
            'strategy': {
                'type': 'behavioral',
                'indicators': ['strategy', 'algorithm', 'policy', 'choose'],
                'anti_indicators': [],
                'file_patterns': ['strategy', 'algorithm', 'policy'],
                'benefits': ['Algorithm flexibility', 'Runtime switching', 'Easy testing']
            },
            'adapter': {
                'type': 'structural',
                'indicators': ['adapter', 'wrapper', 'convert', 'translate'],
                'anti_indicators': [],
                'file_patterns': ['adapter', 'wrapper', 'converter'],
                'benefits': ['Interface compatibility', 'Code reuse', 'Legacy integration']
            },
            'command': {
                'type': 'behavioral',
                'indicators': ['command', 'execute', 'undo', 'redo', 'invoke'],
                'anti_indicators': [],
                'file_patterns': ['command', 'action', 'operation'],
                'benefits': ['Undo/redo functionality', 'Queuing operations', 'Macro recording']
            }
        }
        
        # Architectural pattern signatures
        self.architectural_patterns = {
            'mvc': {
                'components': ['model', 'view', 'controller'],
                'relationships': ['controller->model', 'controller->view', 'view->model'],
                'file_structure': ['models/', 'views/', 'controllers/'],
                'trade_offs': ['Separation of concerns vs complexity', 'Testability vs overhead']
            },
            'mvp': {
                'components': ['model', 'view', 'presenter'],
                'relationships': ['presenter->model', 'presenter->view'],
                'file_structure': ['models/', 'views/', 'presenters/'],
                'trade_offs': ['Testability vs complexity', 'Loose coupling vs boilerplate']
            },
            'microservices': {
                'components': ['service', 'api', 'gateway', 'registry'],
                'relationships': ['api->service', 'gateway->api', 'service->database'],
                'file_structure': ['services/', 'api/', 'gateway/'],
                'trade_offs': ['Scalability vs complexity', 'Independence vs consistency']
            },
            'layered': {
                'components': ['presentation', 'business', 'data', 'service'],
                'relationships': ['presentation->business', 'business->data'],
                'file_structure': ['layers/', 'business/', 'data/'],
                'trade_offs': ['Organization vs rigidity', 'Maintainability vs performance']
            },
            'repository': {
                'components': ['repository', 'entity', 'database'],
                'relationships': ['service->repository', 'repository->database'],
                'file_structure': ['repositories/', 'entities/', 'models/'],
                'trade_offs': ['Data abstraction vs complexity', 'Testability vs overhead']
            }
        }
        
        # Coding patterns and idioms
        self.coding_patterns = {
            'context_manager': {
                'category': 'resource_management',
                'indicators': ['__enter__', '__exit__', 'with', 'contextlib'],
                'benefits': ['Automatic cleanup', 'Exception safety', 'Resource management']
            },
            'generator': {
                'category': 'performance',
                'indicators': ['yield', 'generator', '__iter__', '__next__'],
                'benefits': ['Memory efficiency', 'Lazy evaluation', 'Pipeline processing']
            },
            'property_decorator': {
                'category': 'encapsulation',
                'indicators': ['@property', 'getter', 'setter', '@', '.setter'],
                'benefits': ['Controlled access', 'Validation', 'Computed properties']
            },
            'error_handling': {
                'category': 'robustness',
                'indicators': ['try', 'except', 'finally', 'raise', 'Exception'],
                'benefits': ['Error recovery', 'Graceful degradation', 'User experience']
            },
            'async_pattern': {
                'category': 'concurrency',
                'indicators': ['async', 'await', 'asyncio', 'aiohttp'],
                'benefits': ['Non-blocking I/O', 'Better resource utilization', 'Scalability']
            },
            'dependency_injection': {
                'category': 'architecture',
                'indicators': ['inject', 'dependency', 'container', 'DI'],
                'benefits': ['Loose coupling', 'Testability', 'Flexibility']
            }
        }
    
    def analyze_repository_patterns(self, repo_path: str, repo_name: str) -> Dict[str, Any]:
        """Comprehensive pattern analysis of a repository"""
        logger.info(f"🔍 Analyzing patterns in repository: {repo_name}")
        
        # First get basic analysis
        basic_analysis = self.repository_analyzer.analyze_repository(repo_path)
        if "error" in basic_analysis:
            return {"error": basic_analysis["error"]}
        
        # Detect patterns
        design_patterns = self._detect_design_patterns(repo_path, basic_analysis)
        architectural_patterns = self._detect_architectural_patterns(repo_path, basic_analysis)
        coding_patterns = self._detect_coding_patterns(repo_path, basic_analysis)
        
        # Analyze pattern interactions
        pattern_interactions = self._analyze_pattern_interactions(design_patterns, architectural_patterns, coding_patterns)
        
        # Generate recommendations
        recommendations = self._generate_pattern_recommendations(design_patterns, architectural_patterns, coding_patterns)
        
        # Calculate pattern maturity score
        maturity_score = self._calculate_pattern_maturity(design_patterns, architectural_patterns, coding_patterns)
        
        return {
            "repository": repo_name,
            "analysis_date": datetime.now().isoformat(),
            "design_patterns": design_patterns,
            "architectural_patterns": architectural_patterns,
            "coding_patterns": coding_patterns,
            "pattern_interactions": pattern_interactions,
            "recommendations": recommendations,
            "maturity_score": maturity_score,
            "pattern_summary": self._generate_pattern_summary(design_patterns, architectural_patterns, coding_patterns)
        }
    
    def _detect_design_patterns(self, repo_path: str, analysis: Dict[str, Any]) -> List[DesignPattern]:
        """Detect design patterns in the repository"""
        detected_patterns = []
        
        for pattern_name, pattern_info in self.design_patterns.items():
            evidence = []
            implementation_files = []
            code_examples = []
            confidence = 0.0
            
            # Check file analysis for pattern indicators
            for file_analysis in analysis.get('file_details', []):
                file_path = file_analysis.get('file_path', '')
                file_content_indicators = 0
                
                # Check function names
                for func in file_analysis.get('functions', []):
                    func_name = func.get('name', '')
                    for indicator in pattern_info['indicators']:
                        if indicator.lower() in func_name.lower():
                            evidence.append(f"Function: {func_name}")
                            file_content_indicators += 1
                
                # Check class names
                for cls in file_analysis.get('classes', []):
                    cls_name = cls.get('name', '')
                    for indicator in pattern_info['indicators']:
                        if indicator.lower() in cls_name.lower():
                            evidence.append(f"Class: {cls_name}")
                            file_content_indicators += 1
                
                # Check file name patterns
                file_name = Path(file_path).name.lower()
                for file_pattern in pattern_info['file_patterns']:
                    if file_pattern in file_name:
                        evidence.append(f"File: {file_name}")
                        file_content_indicators += 1
                
                if file_content_indicators > 0:
                    implementation_files.append(file_path)
                    confidence += file_content_indicators * 0.2
            
            # Additional checks for specific patterns
            if pattern_name == 'singleton':
                confidence += self._check_singleton_pattern(analysis)
            elif pattern_name == 'factory':
                confidence += self._check_factory_pattern(analysis)
            elif pattern_name == 'observer':
                confidence += self._check_observer_pattern(analysis)
            elif pattern_name == 'decorator':
                confidence += self._check_decorator_pattern(analysis)
            
            # Normalize confidence
            confidence = min(confidence, 1.0)
            
            if confidence > 0.3:  # Threshold for pattern detection
                detected_patterns.append(DesignPattern(
                    pattern_name=pattern_name,
                    pattern_type=pattern_info['type'],
                    confidence=confidence,
                    evidence=evidence,
                    implementation_files=implementation_files,
                    code_examples=code_examples[:3],  # Limit examples
                    benefits=pattern_info['benefits'],
                    usage_context=self._determine_usage_context(pattern_name, evidence)
                ))
        
        return detected_patterns
    
    def _detect_architectural_patterns(self, repo_path: str, analysis: Dict[str, Any]) -> List[ArchitecturalPattern]:
        """Detect architectural patterns"""
        detected_patterns = []
        
        # Analyze directory structure
        directory_structure = self._analyze_directory_structure(repo_path)
        
        for pattern_name, pattern_info in self.architectural_patterns.items():
            evidence = []
            components_found = []
            relationships_found = []
            
            # Check for component directories
            for component in pattern_info['components']:
                for directory in directory_structure:
                    if component in directory.lower():
                        components_found.append(component)
                        evidence.append(f"Directory: {directory}")
            
            # Check for file structure patterns
            for file_pattern in pattern_info['file_structure']:
                for directory in directory_structure:
                    if file_pattern in directory:
                        evidence.append(f"Structure: {directory}")
            
            # Calculate confidence based on found components
            confidence = len(components_found) / len(pattern_info['components'])
            
            if confidence > 0.5:  # At least half the components found
                detected_patterns.append(ArchitecturalPattern(
                    pattern_name=pattern_name,
                    description=f"{pattern_name.upper()} architectural pattern",
                    components=components_found,
                    relationships=pattern_info['relationships'],
                    implementation_evidence=evidence,
                    scalability_notes=self._generate_scalability_notes(pattern_name),
                    trade_offs=pattern_info['trade_offs']
                ))
        
        return detected_patterns
    
    def _detect_coding_patterns(self, repo_path: str, analysis: Dict[str, Any]) -> List[CodingPattern]:
        """Detect coding patterns and idioms"""
        detected_patterns = []
        
        for pattern_name, pattern_info in self.coding_patterns.items():
            frequency = 0
            use_cases = []
            code_snippets = []
            
            # Analyze each file for pattern usage
            for file_analysis in analysis.get('file_details', []):
                # Check function patterns
                for func in file_analysis.get('functions', []):
                    func_name = func.get('name', '')
                    
                    for indicator in pattern_info['indicators']:
                        if indicator in func_name.lower() or indicator in str(func.get('decorators', [])):
                            frequency += 1
                            use_cases.append(f"Function: {func_name}")
                            
                            # Create code snippet for interesting patterns
                            if len(code_snippets) < 2:  # Limit snippets
                                snippet = self._create_code_snippet(func, pattern_name)
                                if snippet:
                                    code_snippets.append(snippet)
            
            if frequency > 0:
                # Calculate complexity reduction and maintainability impact
                complexity_reduction = self._calculate_complexity_reduction(pattern_name, frequency)
                maintainability_impact = self._assess_maintainability_impact(pattern_name, frequency)
                
                detected_patterns.append(CodingPattern(
                    pattern_name=pattern_name,
                    category=pattern_info['category'],
                    code_snippet=code_snippets[0] if code_snippets else "",
                    use_cases=use_cases[:5],  # Limit use cases
                    frequency=frequency,
                    complexity_reduction=complexity_reduction,
                    maintainability_impact=maintainability_impact
                ))
        
        return detected_patterns
    
    def _check_singleton_pattern(self, analysis: Dict[str, Any]) -> float:
        """Specific check for singleton pattern implementation"""
        confidence = 0.0
        
        for file_analysis in analysis.get('file_details', []):
            for cls in file_analysis.get('classes', []):
                methods = cls.get('methods', [])
                if '__new__' in methods:
                    confidence += 0.3
                if any('instance' in method.lower() for method in methods):
                    confidence += 0.2
        
        return confidence
    
    def _check_factory_pattern(self, analysis: Dict[str, Any]) -> float:
        """Specific check for factory pattern implementation"""
        confidence = 0.0
        factory_indicators = 0
        
        for file_analysis in analysis.get('file_details', []):
            for func in file_analysis.get('functions', []):
                func_name = func.get('name', '').lower()
                if 'create' in func_name or 'factory' in func_name or 'build' in func_name:
                    factory_indicators += 1
        
        confidence = min(factory_indicators * 0.2, 0.8)
        return confidence
    
    def _check_observer_pattern(self, analysis: Dict[str, Any]) -> float:
        """Specific check for observer pattern implementation"""
        confidence = 0.0
        observer_indicators = 0
        
        for file_analysis in analysis.get('file_details', []):
            for func in file_analysis.get('functions', []):
                func_name = func.get('name', '').lower()
                if any(indicator in func_name for indicator in ['notify', 'subscribe', 'observe', 'listen']):
                    observer_indicators += 1
        
        confidence = min(observer_indicators * 0.25, 0.8)
        return confidence
    
    def _check_decorator_pattern(self, analysis: Dict[str, Any]) -> float:
        """Specific check for decorator pattern implementation"""
        confidence = 0.0
        decorator_count = 0
        
        for file_analysis in analysis.get('file_details', []):
            for func in file_analysis.get('functions', []):
                decorators = func.get('decorators', [])
                if decorators:
                    decorator_count += len(decorators)
        
        confidence = min(decorator_count * 0.1, 0.8)
        return confidence
    
    def _analyze_directory_structure(self, repo_path: str) -> List[str]:
        """Analyze the directory structure of the repository"""
        directories = []
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden and common ignore directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]
                
                rel_path = os.path.relpath(root, repo_path)
                if rel_path != '.':
                    directories.append(rel_path)
        except Exception as e:
            logger.warning(f"Could not analyze directory structure: {e}")
        
        return directories
    
    def _analyze_pattern_interactions(self, design_patterns: List[DesignPattern], 
                                    architectural_patterns: List[ArchitecturalPattern], 
                                    coding_patterns: List[CodingPattern]) -> Dict[str, Any]:
        """Analyze how patterns interact with each other"""
        interactions = {
            "synergies": [],
            "conflicts": [],
            "complementary": [],
            "pattern_composition": []
        }
        
        # Check for pattern synergies
        pattern_names = [p.pattern_name for p in design_patterns] + \
                       [p.pattern_name for p in architectural_patterns] + \
                       [p.pattern_name for p in coding_patterns]
        
        # Common synergistic combinations
        synergies = {
            ('factory', 'strategy'): "Factory with Strategy allows for flexible algorithm creation",
            ('observer', 'command'): "Observer with Command enables undo/redo functionality",
            ('decorator', 'strategy'): "Decorator with Strategy provides flexible behavior modification",
            ('mvc', 'observer'): "MVC with Observer enables reactive user interfaces",
            ('repository', 'dependency_injection'): "Repository with DI improves testability"
        }
        
        for (pattern1, pattern2), description in synergies.items():
            if pattern1 in pattern_names and pattern2 in pattern_names:
                interactions["synergies"].append({
                    "patterns": [pattern1, pattern2],
                    "description": description
                })
        
        # Check for potential conflicts
        conflicts = {
            ('singleton', 'dependency_injection'): "Singleton can conflict with DI principles",
            ('microservices', 'singleton'): "Singleton doesn't scale well in microservices"
        }
        
        for (pattern1, pattern2), description in conflicts.items():
            if pattern1 in pattern_names and pattern2 in pattern_names:
                interactions["conflicts"].append({
                    "patterns": [pattern1, pattern2],
                    "description": description
                })
        
        return interactions
    
    def _generate_pattern_recommendations(self, design_patterns: List[DesignPattern], 
                                        architectural_patterns: List[ArchitecturalPattern], 
                                        coding_patterns: List[CodingPattern]) -> List[str]:
        """Generate recommendations based on detected patterns"""
        recommendations = []
        
        # Check for missing complementary patterns
        present_patterns = set([p.pattern_name for p in design_patterns])
        
        if 'factory' in present_patterns and 'strategy' not in present_patterns:
            recommendations.append("Consider implementing Strategy pattern to complement Factory pattern")
        
        if 'observer' in present_patterns and 'command' not in present_patterns:
            recommendations.append("Consider Command pattern for undo/redo functionality with Observer")
        
        # Check for architectural improvements
        arch_patterns = set([p.pattern_name for p in architectural_patterns])
        
        if not arch_patterns:
            recommendations.append("Consider implementing a clear architectural pattern (MVC, MVP, or Layered)")
        
        if 'mvc' in arch_patterns and 'observer' not in present_patterns:
            recommendations.append("Implement Observer pattern for reactive MVC updates")
        
        # Check for coding pattern improvements
        coding_pattern_names = set([p.pattern_name for p in coding_patterns])
        
        if 'error_handling' not in coding_pattern_names:
            recommendations.append("Improve error handling patterns throughout the codebase")
        
        if 'async_pattern' not in coding_pattern_names:
            recommendations.append("Consider async patterns for I/O intensive operations")
        
        return recommendations
    
    def _calculate_pattern_maturity(self, design_patterns: List[DesignPattern], 
                                  architectural_patterns: List[ArchitecturalPattern], 
                                  coding_patterns: List[CodingPattern]) -> Dict[str, Any]:
        """Calculate pattern maturity score"""
        total_patterns = len(design_patterns) + len(architectural_patterns) + len(coding_patterns)
        
        # Weight different pattern types
        design_score = sum(p.confidence for p in design_patterns) * 0.4
        arch_score = len(architectural_patterns) * 0.4
        coding_score = len(coding_patterns) * 0.2
        
        overall_score = (design_score + arch_score + coding_score) / max(total_patterns, 1)
        
        maturity_level = "Beginner"
        if overall_score > 0.7:
            maturity_level = "Advanced"
        elif overall_score > 0.4:
            maturity_level = "Intermediate"
        
        return {
            "overall_score": round(overall_score, 2),
            "maturity_level": maturity_level,
            "total_patterns": total_patterns,
            "design_patterns": len(design_patterns),
            "architectural_patterns": len(architectural_patterns),
            "coding_patterns": len(coding_patterns)
        }
    
    def _generate_pattern_summary(self, design_patterns: List[DesignPattern], 
                                architectural_patterns: List[ArchitecturalPattern], 
                                coding_patterns: List[CodingPattern]) -> Dict[str, Any]:
        """Generate a summary of all detected patterns"""
        return {
            "design_patterns": [{"name": p.pattern_name, "type": p.pattern_type, "confidence": p.confidence} for p in design_patterns],
            "architectural_patterns": [{"name": p.pattern_name, "components": len(p.components)} for p in architectural_patterns],
            "coding_patterns": [{"name": p.pattern_name, "category": p.category, "frequency": p.frequency} for p in coding_patterns],
            "most_confident_design_pattern": max(design_patterns, key=lambda x: x.confidence).pattern_name if design_patterns else None,
            "primary_architecture": architectural_patterns[0].pattern_name if architectural_patterns else None,
            "most_frequent_coding_pattern": max(coding_patterns, key=lambda x: x.frequency).pattern_name if coding_patterns else None
        }
    
    def _determine_usage_context(self, pattern_name: str, evidence: List[str]) -> str:
        """Determine the usage context for a pattern"""
        contexts = {
            'singleton': "Resource management and configuration",
            'factory': "Object creation and abstraction",
            'observer': "Event handling and notifications",
            'decorator': "Behavior modification and middleware",
            'strategy': "Algorithm selection and flexibility",
            'adapter': "Interface compatibility and integration"
        }
        return contexts.get(pattern_name, "General purpose implementation")
    
    def _generate_scalability_notes(self, pattern_name: str) -> str:
        """Generate scalability notes for architectural patterns"""
        notes = {
            'mvc': "Scales well with proper separation, but can become monolithic",
            'microservices': "Highly scalable but adds complexity and coordination overhead",
            'layered': "Good for medium-scale applications, can become bottlenecked",
            'repository': "Scales well with proper caching and query optimization"
        }
        return notes.get(pattern_name, "Scalability depends on implementation details")
    
    def _calculate_complexity_reduction(self, pattern_name: str, frequency: int) -> float:
        """Calculate how much complexity reduction a pattern provides"""
        base_reductions = {
            'context_manager': 0.3,
            'generator': 0.2,
            'property_decorator': 0.15,
            'error_handling': 0.25,
            'async_pattern': 0.35,
            'dependency_injection': 0.4
        }
        base = base_reductions.get(pattern_name, 0.1)
        return min(base * (1 + frequency * 0.05), 1.0)
    
    def _assess_maintainability_impact(self, pattern_name: str, frequency: int) -> str:
        """Assess the maintainability impact of a coding pattern"""
        impacts = {
            'context_manager': "High - Ensures proper resource cleanup",
            'generator': "Medium - Improves memory efficiency",
            'property_decorator': "High - Provides controlled access",
            'error_handling': "High - Improves robustness and debugging",
            'async_pattern': "Medium - Improves performance but adds complexity",
            'dependency_injection': "High - Greatly improves testability"
        }
        return impacts.get(pattern_name, "Medium - Depends on implementation quality")
    
    def _create_code_snippet(self, func: Dict[str, Any], pattern_name: str) -> Optional[str]:
        """Create a code snippet example for a pattern"""
        func_name = func.get('name', '')
        args = func.get('args', [])
        decorators = func.get('decorators', [])
        
        if pattern_name == 'property_decorator' and any('@property' in str(dec) for dec in decorators):
            return f"@property\ndef {func_name}(self):\n    # Property implementation\n    pass"
        elif pattern_name == 'context_manager' and ('__enter__' in func_name or '__exit__' in func_name):
            return f"def {func_name}(self, *args):\n    # Context manager implementation\n    pass"
        elif pattern_name == 'async_pattern' and func.get('is_async'):
            return f"async def {func_name}({', '.join(args)}):\n    # Async implementation\n    pass"
        
        return None

# Global instance
pattern_recognition_system = PatternRecognitionSystem()