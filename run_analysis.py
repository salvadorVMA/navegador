"""
Analysis execution module for the Navegador project.

This module handles the execution of different types of analysis based on user requests.
Currently supports detailed reports with plans for comparative analysis and quick insights.
"""

from detailed_analysis import (
    run_detailed_analysis, 
    format_detailed_report,
    run_quick_insights_analysis,
    format_quick_insights_report,
    run_plots_only_analysis,
    format_plots_only_report
)
# Import optimized analysis functions
from detailed_analysis_optimized import run_detailed_analysis_optimized, benchmark_analysis_performance
from performance_optimization import get_cache_stats, clear_cache, reset_performance_metrics


def run_analysis(analysis_type: str, selected_variables: list, user_query: str, **kwargs) -> dict:
    """
    Run analysis based on the specified type and parameters.
    
    Args:
        analysis_type (str): Type of analysis to run ('detailed_report', 'comparative_analysis', 'quick_insights', 'plots_only')
        selected_variables (list): List of variable IDs selected for analysis
        user_query (str): The user's query
        **kwargs: Additional parameters specific to each analysis type
        
    Returns:
        dict: Analysis results including success status, data, and formatted report
    """
    print(f"Running {analysis_type} analysis...")
    print(f"Variables: {selected_variables}")
    print(f"Query: {user_query}")
    
    if analysis_type == "detailed_report":
        return _run_detailed_report(selected_variables, user_query, **kwargs)
    elif analysis_type == "comparative_analysis":
        return _run_comparative_analysis(selected_variables, user_query, **kwargs)
    elif analysis_type == "quick_insights":
        return _run_quick_insights(selected_variables, user_query, **kwargs)
    elif analysis_type == "plots_only":
        return _run_plots_only(selected_variables, user_query, **kwargs)
    # Optimized analysis types
    elif analysis_type == "detailed_report_optimized":
        return _run_detailed_report_optimized(selected_variables, user_query, **kwargs)
    elif analysis_type == "benchmark":
        return _run_benchmark_analysis(selected_variables, user_query, **kwargs)
    elif analysis_type == "performance_stats":
        return _get_performance_stats(**kwargs)
    else:
        return {
            'success': False,
            'error': f'Unknown analysis type: {analysis_type}',
            'analysis_type': analysis_type,
            'results': {},
            'formatted_report': f'Error: Analysis type "{analysis_type}" is not supported.'
        }


def _run_detailed_report(selected_variables: list, user_query: str, **kwargs) -> dict:
    """
    Run detailed report analysis using the integrated notebook logic.
    
    Args:
        selected_variables (list): List of variable IDs selected for analysis
        user_query (str): The user's query
        **kwargs: Additional parameters
        
    Returns:
        dict: Detailed analysis results
    """
    try:
        # Use the integrated detailed analysis from the notebook
        analysis_results = run_detailed_analysis(
            selected_variables=selected_variables,
            user_query=user_query,
            analysis_params=kwargs.get('analysis_params')
        )
        
        # Format the report
        formatted_report = format_detailed_report(analysis_results)
        
        return {
            'success': analysis_results.get('success', False),
            'analysis_type': 'detailed_report',
            'results': analysis_results,
            'formatted_report': formatted_report,
            'error': analysis_results.get('error') if not analysis_results.get('success', False) else None
        }
        
    except Exception as e:
        print(f"Error in detailed report analysis: {e}")
        return {
            'success': False,
            'error': str(e),
            'analysis_type': 'detailed_report',
            'results': {},
            'formatted_report': f'Error generating detailed report: {str(e)}'
        }


def _run_comparative_analysis(selected_variables: list, user_query: str, **kwargs) -> dict:
    """
    Run comparative analysis (placeholder for future implementation).
    
    Args:
        selected_variables (list): List of variable IDs selected for analysis  
        user_query (str): The user's query
        **kwargs: Additional parameters
        
    Returns:
        dict: Comparative analysis results
    """
    return {
        'success': False,
        'error': 'Comparative analysis not yet implemented',
        'analysis_type': 'comparative_analysis',
        'results': {
            'message': 'This analysis type will be implemented in future versions.'
        },
        'formatted_report': '''
# Comparative Analysis (Coming Soon)

This analysis type is not yet implemented. It will provide:
- Cross-variable comparisons
- Statistical correlations
- Trend analysis across different demographics

Please use the detailed report analysis for now.
'''
    }


def _run_quick_insights(selected_variables: list, user_query: str, **kwargs) -> dict:
    """
    Run quick insights analysis that summarizes variable descriptions and includes plots.
    
    Args:
        selected_variables (list): List of variable IDs selected for analysis
        user_query (str): The user's query
        **kwargs: Additional parameters
        
    Returns:
        dict: Quick insights results
    """
    try:
        # Use the new quick insights analysis
        analysis_results = run_quick_insights_analysis(
            selected_variables=selected_variables,
            user_query=user_query,
            analysis_params=kwargs.get('analysis_params')
        )
        
        # Format the report
        formatted_report = format_quick_insights_report(analysis_results)
        
        return {
            'success': analysis_results.get('success', False),
            'analysis_type': 'quick_insights',
            'results': analysis_results,
            'formatted_report': formatted_report,
            'error': analysis_results.get('error') if not analysis_results.get('success', False) else None
        }
        
    except Exception as e:
        print(f"Error in quick insights analysis: {e}")
        return {
            'success': False,
            'error': str(e),
            'analysis_type': 'quick_insights',
            'results': {},
            'formatted_report': f'Error generating quick insights: {str(e)}'
        }


def _run_plots_only(selected_variables: list, user_query: str, **kwargs) -> dict:
    """
    Run plots-only analysis that returns only the plots for selected variables.
    
    Args:
        selected_variables (list): List of variable IDs selected for analysis
        user_query (str): The user's query
        **kwargs: Additional parameters
        
    Returns:
        dict: Plots-only analysis results
    """
    try:
        # Use the new plots-only analysis
        analysis_results = run_plots_only_analysis(
            selected_variables=selected_variables,
            user_query=user_query,
            analysis_params=kwargs.get('analysis_params')
        )
        
        # Format the report
        formatted_report = format_plots_only_report(analysis_results)
        
        return {
            'success': analysis_results.get('success', False),
            'analysis_type': 'plots_only',
            'results': analysis_results,
            'formatted_report': formatted_report,
            'error': analysis_results.get('error') if not analysis_results.get('success', False) else None
        }
        
    except Exception as e:
        print(f"Error in plots-only analysis: {e}")
        return {
            'success': False,
            'error': str(e),
            'analysis_type': 'plots_only',
            'results': {},
            'formatted_report': f'Error generating plots: {str(e)}'
        }


def _run_detailed_report_optimized(selected_variables: list, user_query: str, **kwargs) -> dict:
    """
    Run optimized detailed report analysis.
    
    Args:
        selected_variables (list): List of variable IDs selected for analysis
        user_query (str): The user's query
        **kwargs: Additional parameters
        
    Returns:
        dict: Optimized detailed analysis results
    """
    try:
        # Use the optimized detailed analysis
        analysis_results = run_detailed_analysis_optimized(
            selected_variables=selected_variables,
            user_query=user_query,
            analysis_params=kwargs.get('analysis_params')
        )
        
        # Format the report using the original formatter
        formatted_report = format_detailed_report(analysis_results)
        
        return {
            'success': analysis_results.get('success', False),
            'analysis_type': 'detailed_report_optimized',
            'results': analysis_results,
            'formatted_report': formatted_report,
            'error': analysis_results.get('error') if not analysis_results.get('success', False) else None
        }
        
    except Exception as e:
        print(f"Error in optimized detailed report analysis: {e}")
        return {
            'success': False,
            'error': str(e),
            'analysis_type': 'detailed_report_optimized',
            'results': {},
            'formatted_report': f'Error generating optimized detailed report: {str(e)}'
        }


def _run_benchmark_analysis(selected_variables: list, user_query: str, **kwargs) -> dict:
    """
    Run benchmark comparison between original and optimized analysis.
    
    Args:
        selected_variables (list): List of variable IDs selected for analysis
        user_query (str): The user's query
        **kwargs: Additional parameters
        
    Returns:
        dict: Benchmark results
    """
    try:
        iterations = kwargs.get('iterations', 2)  # Default to 2 iterations for faster testing
        
        benchmark_results = benchmark_analysis_performance(
            selected_variables=selected_variables,
            user_query=user_query,
            iterations=iterations
        )
        
        # Format benchmark report
        if 'error' not in benchmark_results:
            formatted_report = f"""
# Performance Benchmark Report

**Query:** {user_query}
**Variables:** {selected_variables}
**Iterations:** {benchmark_results['iterations']}

## Results

| Metric | Original | Optimized | Improvement |
|--------|----------|-----------|-------------|
| Average Time | {benchmark_results['average_original']}s | {benchmark_results['average_optimized']}s | {benchmark_results['improvement_percentage']}% |
| Best Time | {min(benchmark_results['original_times']):.2f}s | {min(benchmark_results['optimized_times']):.2f}s | - |
| Worst Time | {max(benchmark_results['original_times']):.2f}s | {max(benchmark_results['optimized_times']):.2f}s | - |

## Performance Improvement
The optimized version is **{benchmark_results['improvement_percentage']:.1f}% faster** than the original implementation.

## Individual Run Times
- **Original:** {[f'{t:.2f}s' for t in benchmark_results['original_times']]}
- **Optimized:** {[f'{t:.2f}s' for t in benchmark_results['optimized_times']]}
"""
        else:
            formatted_report = f"Benchmark failed: {benchmark_results['error']}"
        
        return {
            'success': 'error' not in benchmark_results,
            'analysis_type': 'benchmark',
            'results': benchmark_results,
            'formatted_report': formatted_report,
            'error': benchmark_results.get('error')
        }
        
    except Exception as e:
        print(f"Error in benchmark analysis: {e}")
        return {
            'success': False,
            'error': str(e),
            'analysis_type': 'benchmark',
            'results': {},
            'formatted_report': f'Error running benchmark: {str(e)}'
        }


def _get_performance_stats(**kwargs) -> dict:
    """
    Get current performance statistics.
    
    Returns:
        dict: Performance statistics
    """
    try:
        stats = get_cache_stats()
        
        formatted_report = f"""
# Performance Statistics

## Cache Performance
- **Total LLM Calls:** {stats['llm_calls']}
- **Cache Hit Rate:** {stats['cache_hit_rate']}%
- **Total Analysis Time:** {stats['total_analysis_time']}s

## Average Times by Analysis Type
"""
        
        for analysis_type, avg_time in stats['average_times_by_type'].items():
            formatted_report += f"- **{analysis_type.replace('_', ' ').title()}:** {avg_time}s\n"
        
        formatted_report += f"""
## Cache Statistics
- **Cache Entries:** {stats['cache_stats']['total_entries']}
- **Cache Hits:** {stats['cache_stats']['total_hits']}
- **Max Cache Size:** {stats['cache_stats']['max_size']}
- **TTL:** {stats['cache_stats']['ttl_seconds']}s
"""
        
        return {
            'success': True,
            'analysis_type': 'performance_stats',
            'results': stats,
            'formatted_report': formatted_report
        }
        
    except Exception as e:
        print(f"Error getting performance stats: {e}")
        return {
            'success': False,
            'error': str(e),
            'analysis_type': 'performance_stats',
            'results': {},
            'formatted_report': f'Error getting performance statistics: {str(e)}'
        }


# Legacy function for backward compatibility
def execute_analysis(dataset_name: str, variables: list) -> dict:
    """
    Legacy function maintained for backward compatibility.
    
    Args:
        dataset_name: Name of the dataset to analyze  
        variables: List of variables to include in the analysis
        
    Returns:
        Dictionary containing analysis results
    """
    print(f"Legacy execute_analysis called with dataset: {dataset_name}, variables: {variables}")
    
    # Redirect to new analysis system
    return run_analysis(
        analysis_type="detailed_report",
        selected_variables=variables,
        user_query=f"Analysis of {dataset_name} dataset"
    )
