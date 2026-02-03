"""
Test script for the new analysis types: quick_insights and plots_only

This script tests the integration of the new analysis types with the
detailed_analysis.py and run_analysis.py modules.
"""

import os
import sys
from run_analysis import run_analysis


def test_quick_insights_analysis():
    """Test the quick insights analysis type."""
    print("=" * 60)
    print("TESTING QUICK INSIGHTS ANALYSIS")
    print("=" * 60)
    
    # Test parameters
    selected_variables = ["p13|IND", "p14|IND"]  # Using some variables that should exist
    user_query = "What are the main patterns in political attitudes?"
    
    print(f"Testing with variables: {selected_variables}")
    print(f"Query: {user_query}")
    print()
    
    try:
        # Run the analysis
        result = run_analysis(
            analysis_type="quick_insights",
            selected_variables=selected_variables,
            user_query=user_query
        )
        
        print("Analysis completed!")
        print(f"Success: {result.get('success', False)}")
        print(f"Analysis type: {result.get('analysis_type', 'Unknown')}")
        
        if result.get('success', False):
            print("\n--- QUICK INSIGHTS REPORT ---")
            print(result.get('formatted_report', 'No report available'))
            
            # Check if plots were generated
            results = result.get('results', {})
            plot_paths = results.get('plot_paths', {})
            print(f"\nPlots generated: {len(plot_paths)}")
            for var_id, path in plot_paths.items():
                print(f"  - {var_id}: {path}")
                
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Exception during quick insights test: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def test_plots_only_analysis():
    """Test the plots-only analysis type."""
    print("=" * 60)
    print("TESTING PLOTS ONLY ANALYSIS")
    print("=" * 60)
    
    # Test parameters
    selected_variables = ["p13|IND", "p14|IND"]
    user_query = "Generate plots for political variables"
    
    print(f"Testing with variables: {selected_variables}")
    print(f"Query: {user_query}")
    print()
    
    try:
        # Run the analysis
        result = run_analysis(
            analysis_type="plots_only",
            selected_variables=selected_variables,
            user_query=user_query
        )
        
        print("Analysis completed!")
        print(f"Success: {result.get('success', False)}")
        print(f"Analysis type: {result.get('analysis_type', 'Unknown')}")
        
        if result.get('success', False):
            print("\n--- PLOTS ONLY REPORT ---")
            print(result.get('formatted_report', 'No report available'))
            
            # Check if plots were generated
            results = result.get('results', {})
            plot_paths = results.get('plot_paths', {})
            print(f"\nPlots generated: {len(plot_paths)}")
            for var_id, path in plot_paths.items():
                print(f"  - {var_id}: {path}")
                
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Exception during plots-only test: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def test_comparison_with_detailed_report():
    """Test comparison between the different analysis types."""
    print("=" * 60)
    print("TESTING COMPARISON WITH DETAILED REPORT")
    print("=" * 60)
    
    selected_variables = ["p13|IND"]
    user_query = "Political attitudes analysis"
    
    print(f"Testing all analysis types with variable: {selected_variables}")
    print(f"Query: {user_query}")
    print()
    
    analysis_types = ["detailed_report", "quick_insights", "plots_only"]
    
    for analysis_type in analysis_types:
        print(f"\n--- Testing {analysis_type.upper().replace('_', ' ')} ---")
        
        try:
            result = run_analysis(
                analysis_type=analysis_type,
                selected_variables=selected_variables,
                user_query=user_query
            )
            
            print(f"Success: {result.get('success', False)}")
            
            if result.get('success', False):
                # Count report sections
                results = result.get('results', {})
                report_sections = results.get('report_sections', {})
                print(f"Report sections: {len(report_sections)}")
                
                # Check for plots if applicable
                if 'plot_paths' in results:
                    plot_paths = results.get('plot_paths', {})
                    print(f"Plots generated: {len(plot_paths)}")
                    
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Exception: {e}")
    
    print()


def check_plot_files():
    """Check if plot files were actually created."""
    print("=" * 60)
    print("CHECKING PLOT FILES")
    print("=" * 60)
    
    plot_dir = "plot_images"
    if os.path.exists(plot_dir):
        files = os.listdir(plot_dir)
        plot_files = [f for f in files if f.endswith('.png')]
        
        print(f"Plot directory: {plot_dir}")
        print(f"Total PNG files: {len(plot_files)}")
        
        if plot_files:
            print("Recent plot files:")
            for file in sorted(plot_files)[-10:]:  # Show last 10 files
                path = os.path.join(plot_dir, file)
                size = os.path.getsize(path)
                print(f"  - {file} ({size} bytes)")
        else:
            print("No plot files found.")
    else:
        print(f"Plot directory '{plot_dir}' does not exist.")
    
    print()


if __name__ == "__main__":
    print("Starting tests for new analysis types...")
    print("=" * 60)
    
    # Run tests
    test_quick_insights_analysis()
    test_plots_only_analysis()
    test_comparison_with_detailed_report()
    check_plot_files()
    
    print("=" * 60)
    print("All tests completed!")
