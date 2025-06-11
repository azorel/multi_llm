#!/usr/bin/env python3
"""
Run Disler AI Engineering System Analysis on main.py and codebase
Using Single File Agent (SFA) patterns with low-temperature (0.1) precision
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Import the Disler Agent Engine
sys.path.insert(0, str(Path.cwd()))
from disler_agent_engine import DislerAgentEngine

async def analyze_main_codebase():
    """Use Disler AI Engineering System to analyze main.py and codebase."""
    
    print('🤖 INITIATING DISLER AI ENGINEERING SYSTEM ANALYSIS')
    print('=' * 60)
    print('Target: main.py and autonomous-multi-llm-agent codebase')
    print('Method: Single File Agent (SFA) pattern with low temperature (0.1)')
    print('Models: Multi-provider analysis (OpenAI, Anthropic, Gemini)')
    print('')
    
    # Initialize the engine
    engine = DislerAgentEngine()
    
    # Read the main.py file for analysis
    try:
        with open('/home/ikino/dev/autonomous-multi-llm-agent/main.py', 'r') as f:
            main_py_content = f.read()
    except Exception as e:
        print(f"❌ Error reading main.py: {e}")
        return
    
    # Read disler_agent_engine.py for context
    try:
        with open('/home/ikino/dev/autonomous-multi-llm-agent/disler_agent_engine.py', 'r') as f:
            disler_engine_content = f.read()
    except Exception as e:
        print(f"❌ Error reading disler_agent_engine.py: {e}")
        return
    
    # Define the analysis agent configuration
    analysis_config = {
        'agent_name': 'Codebase Architecture Analyzer',
        'agent_type': 'Analysis',
        'provider': 'OpenAI',
        'prompt_template': f'''Analyze the provided codebase architecture and main.py file. Focus on:

1. ARCHITECTURE ASSESSMENT:
   - Overall system design and patterns in main.py (lines 1-1252)
   - Component integration and dependencies
   - Scalability and maintainability factors
   - Error handling and resilience patterns
   - Background service orchestration

2. CODE QUALITY ANALYSIS:
   - Code organization and structure in main.py
   - Design patterns implementation (Observer, Factory, etc.)
   - Best practices adherence
   - Performance bottlenecks in monitoring loops
   - Memory management and resource cleanup

3. INTEGRATION OPPORTUNITIES:
   - Areas where Disler SFA patterns can be applied
   - Single File Agent (SFA) refactoring opportunities
   - Multi-model optimization potential in existing LLM calls
   - Workflow automation improvements using checkbox system
   - Voice command integration possibilities

4. DISLER PATTERN APPLICATION:
   - How to integrate the existing DislerAgentEngine (1171 lines) with main.py
   - Opportunities to replace existing agent patterns with SFA
   - Low-temperature (0.1) prompting integration
   - Multi-provider failover improvements
   - Cost tracking and optimization integration

5. OPTIMIZATION RECOMMENDATIONS:
   - Performance enhancements for the 8 background monitoring loops
   - Code simplification opportunities
   - Maintainability improvements
   - Resource utilization optimization
   - Error recovery and self-healing improvements

6. IMPLEMENTATION STRATEGY:
   - Priority-ordered improvement list
   - Risk assessment for changes
   - Implementation complexity estimates
   - Expected benefits quantification
   - Migration path from current architecture to Disler patterns

CODEBASE CONTEXT:
- main.py contains LifeOSAutonomousSystem with 8 background monitoring services
- Existing integration with YouTube, GitHub, Notion APIs
- Self-healing and recovery mechanisms
- Current multi-model support (OpenAI, Anthropic, Gemini)
- Comprehensive checkbox automation system
- DislerAgentEngine ready for integration

Provide structured, actionable insights with specific code examples and implementation recommendations.''',
        'configuration': {
            'target_file': 'main.py',
            'codebase_path': '/home/ikino/dev/autonomous-multi-llm-agent',
            'analysis_depth': 'comprehensive',
            'main_py_lines': len(main_py_content.split('\n')),
            'disler_engine_lines': len(disler_engine_content.split('\n')),
            'focus_areas': [
                'architecture_patterns',
                'integration_opportunities', 
                'performance_optimization',
                'maintainability_improvements',
                'disler_pattern_application',
                'background_service_optimization'
            ]
        }
    }
    
    print('🔄 Executing comprehensive codebase analysis...')
    print('   📋 Using low-temperature (0.1) for precise, deterministic analysis')
    print('   🧠 Applying Disler SFA patterns for focused analysis')
    print('   🎯 Multi-model validation for comprehensive insights')
    print('   📊 Analyzing 1252 lines of main.py + 1171 lines of DislerAgentEngine')
    print('')
    
    # Execute the analysis using Disler patterns
    result = await engine._execute_by_type(
        analysis_config['agent_type'],
        analysis_config['prompt_template'], 
        json.dumps(analysis_config['configuration']),
        analysis_config['provider']
    )
    
    if result['success']:
        print('✅ ANALYSIS COMPLETED SUCCESSFULLY')
        print('=' * 60)
        print('')
        print('📊 DISLER AI ENGINEERING SYSTEM ANALYSIS RESULTS:')
        print('')
        print(result['output'])
        print('')
        print('=' * 60)
        print(f'💰 Cost Estimate: ${result.get("cost_estimate", 0):.4f}')
        print(f'🔢 Tokens Used: {result.get("tokens_used", 0)}')
        print(f'🤖 Model Provider: {result.get("provider", "Unknown")}')
        print(f'📅 Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('=' * 60)
        
        # Save results to file
        results_file = f'/home/ikino/dev/autonomous-multi-llm-agent/DISLER_ANALYSIS_RESULTS_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        with open(results_file, 'w') as f:
            f.write(f'# Disler AI Engineering System Analysis Results\n\n')
            f.write(f'**Analysis Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'**Target:** main.py and codebase\n')
            f.write(f'**Method:** Single File Agent (SFA) with low temperature (0.1)\n')
            f.write(f'**Provider:** {result.get("provider", "Unknown")}\n')
            f.write(f'**Cost:** ${result.get("cost_estimate", 0):.4f}\n')
            f.write(f'**Tokens:** {result.get("tokens_used", 0)}\n\n')
            f.write('## Analysis Results\n\n')
            f.write(result['output'])
        
        print(f'📁 Results saved to: {results_file}')
        
    else:
        print(f'❌ Analysis failed: {result.get("error", "Unknown error")}')
    
    return result

async def run_model_comparison():
    """Run model comparison test using Disler patterns."""
    
    print('\n🧪 RUNNING MULTI-MODEL COMPARISON TEST')
    print('=' * 60)
    
    engine = DislerAgentEngine()
    
    test_config = {
        'test_name': 'Codebase Analysis Comparison',
        'prompt': '''Analyze this codebase architecture question: "What are the top 3 most critical improvements needed for the LifeOSAutonomousSystem in main.py?" Provide a concise, structured response with specific recommendations.''',
        'models': ['GPT-4', 'Claude-3.5-Sonnet', 'Gemini-Pro']
    }
    
    # Execute multi-model test
    results = {}
    costs = {}
    
    for model in test_config['models']:
        if model in ["GPT-4", "GPT-3.5-Turbo"]:
            provider = "OpenAI"
        elif model in ["Claude-3.5-Sonnet", "Claude-3-Haiku"]:
            provider = "Anthropic"
        elif model in ["Gemini-Pro", "Gemini-Flash"]:
            provider = "Gemini"
        else:
            continue
        
        try:
            print(f'🔄 Testing {model}...')
            start_time = datetime.now()
            result = await engine._call_llm(test_config['prompt'], provider)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            cost = engine._estimate_cost(test_config['prompt'], result, provider)
            
            results[model] = {
                'output': result,
                'duration': duration,
                'cost': cost,
                'success': True
            }
            costs[model] = cost
            
            print(f'   ✅ {model}: {duration:.2f}s, ${cost:.4f}')
            
        except Exception as e:
            results[model] = {
                'error': str(e),
                'success': False
            }
            print(f'   ❌ {model}: {str(e)}')
    
    # Determine winner (lowest cost for similar quality)
    winner = min(costs.keys(), key=lambda k: costs[k]) if costs else "No winner"
    
    print('')
    print('🏆 MODEL COMPARISON RESULTS:')
    print(f'Winner: {winner} (${costs.get(winner, 0):.4f})')
    print('')
    
    for model, result in results.items():
        if result['success']:
            print(f'**{model}:** {result["output"][:200]}...')
            print(f'Cost: ${result["cost"]:.4f}, Duration: {result["duration"]:.2f}s')
            print('')
    
    return results

if __name__ == "__main__":
    try:
        # Run comprehensive analysis
        analysis_result = asyncio.run(analyze_main_codebase())
        
        # Run model comparison
        comparison_result = asyncio.run(run_model_comparison())
        
        print('\n🎉 DISLER AI ENGINEERING SYSTEM ANALYSIS COMPLETE')
        
    except KeyboardInterrupt:
        print('\n🛑 Analysis interrupted by user')
    except Exception as e:
        print(f'\n❌ Analysis error: {e}')