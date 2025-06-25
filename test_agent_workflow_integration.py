"""
Test script for agent workflow with new analysis types

This script tests the complete agent workflow including the new analysis types:
- quick_insights: summarizes variable descriptions and adds plots
- plots_only: returns only plots for selected variables

The agent should properly recognize requests for these analysis types and
route them to the correct analysis functions.
"""

import os
import sys
from run_analysis import run_analysis


def test_agent_workflow_quick_insights():
    """Test the agent workflow for quick insights analysis type."""
    print("=" * 60)
    print("TESTING AGENT WORKFLOW - QUICK INSIGHTS")
    print("=" * 60)
    
    try:
        # Test direct run_analysis call
        result = run_analysis(
            analysis_type="quick_insights",
            selected_variables=["p13|IND", "p14|IND"],
            user_query="What are the main insights about political attitudes and indigenous issues?"
        )
        
        print(f"Analysis completed!")
        print(f"Success: {result.get('success', False)}")
        print(f"Analysis type: {result.get('analysis_type', 'Unknown')}")
        
        if result.get('success', False):
            print("\n--- QUICK INSIGHTS WORKFLOW TEST RESULTS ---")
            results_data = result.get('results', {})
            
            # Check variable descriptions
            variable_descriptions = results_data.get('variable_descriptions', {})
            print(f"Variable descriptions generated: {len(variable_descriptions)}")
            
            # Check plots
            plot_paths = results_data.get('plot_paths', {})
            print(f"Plots generated: {len(plot_paths)}")
            
            # Check insights summary
            insights_summary = results_data.get('insights_summary', {})
            key_findings = insights_summary.get('key_findings', [])
            print(f"Key findings identified: {len(key_findings)}")
            
            # Show formatted report excerpt
            formatted_report = result.get('formatted_report', '')
            if formatted_report:
                lines = formatted_report.split('\n')
                print(f"\nReport preview (first 15 lines):")
                for line in lines[:15]:
                    print(f"  {line}")
                print("  ...")
                
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Exception during quick insights test: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def test_agent_workflow_plots_only():
    """Test the agent workflow for plots-only analysis type."""
    print("=" * 60)
    print("TESTING AGENT WORKFLOW - PLOTS ONLY")
    print("=" * 60)
    
    try:
        # Test direct run_analysis call
        result = run_analysis(
            analysis_type="plots_only",
            selected_variables=["p13|IND", "p14|IND"],
            user_query="Generate plots for political and indigenous variables"
        )
        
        print(f"Analysis completed!")
        print(f"Success: {result.get('success', False)}")
        print(f"Analysis type: {result.get('analysis_type', 'Unknown')}")
        
        if result.get('success', False):
            print("\n--- PLOTS ONLY WORKFLOW TEST RESULTS ---")
            results_data = result.get('results', {})
            
            # Check plots
            plot_paths = results_data.get('plot_paths', {})
            print(f"Plots generated: {len(plot_paths)}")
            
            for var_id, path in plot_paths.items():
                print(f"  - {var_id}: {path}")
            
            # Check report sections
            report_sections = results_data.get('report_sections', {})
            plot_count = report_sections.get('plot_count', 0)
            print(f"Plot count in report: {plot_count}")
            
            # Show formatted report
            formatted_report = result.get('formatted_report', '')
            if formatted_report:
                lines = formatted_report.split('\n')
                print(f"\nReport preview (first 10 lines):")
                for line in lines[:10]:
                    print(f"  {line}")
                print("  ...")
                
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Exception during plots-only test: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def test_analysis_type_comparison():
    """Test comparison between all analysis types."""
    print("=" * 60)
    print("TESTING ANALYSIS TYPE COMPARISON")
    print("=" * 60)
    
    selected_variables = ["p13|IND"]
    user_query = "Analysis of political attitudes"
    
    analysis_types = ["detailed_report", "quick_insights", "plots_only"]
    results_summary = {}
    
    for analysis_type in analysis_types:
        print(f"\n--- Testing {analysis_type.replace('_', ' ').title()} ---")
        
        try:
            result = run_analysis(
                analysis_type=analysis_type,
                selected_variables=selected_variables,
                user_query=user_query
            )
            
            success = result.get('success', False)
            print(f"Success: {success}")
            
            if success:
                results_data = result.get('results', {})
                report_sections = results_data.get('report_sections', {})
                
                # Count different elements
                summary = {
                    'success': True,
                    'report_sections': len(report_sections),
                    'has_plots': 'plot_paths' in results_data,
                    'plot_count': len(results_data.get('plot_paths', {})),
                    'has_descriptions': 'variable_descriptions' in results_data,
                    'description_count': len(results_data.get('variable_descriptions', {})),
                    'report_length': len(result.get('formatted_report', ''))
                }
                
                print(f"  Report sections: {summary['report_sections']}")
                print(f"  Has plots: {summary['has_plots']}")
                print(f"  Plot count: {summary['plot_count']}")
                print(f"  Has descriptions: {summary['has_descriptions']}")
                print(f"  Description count: {summary['description_count']}")
                print(f"  Report length: {summary['report_length']} characters")
                
                results_summary[analysis_type] = summary
                
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
                results_summary[analysis_type] = {'success': False, 'error': result.get('error')}
                
        except Exception as e:
            print(f"  Exception: {e}")
            results_summary[analysis_type] = {'success': False, 'error': str(e)}
    
    print("\n--- COMPARISON SUMMARY ---")
    for analysis_type, summary in results_summary.items():
        if summary.get('success', False):
            print(f"{analysis_type}:")
            print(f"  ✓ Plots: {summary.get('plot_count', 0)}")
            print(f"  ✓ Descriptions: {summary.get('description_count', 0)}")
            print(f"  ✓ Report length: {summary.get('report_length', 0)}")
        else:
            print(f"{analysis_type}: FAILED - {summary.get('error', 'Unknown')}")
    
    print()


def test_plot_file_generation():
    """Test that plot files are actually being generated."""
    print("=" * 60)
    print("TESTING PLOT FILE GENERATION")
    print("=" * 60)
    
    plot_dir = "plot_images"
    
    # Get initial file count
    initial_files = set()
    if os.path.exists(plot_dir):
        initial_files = set(f for f in os.listdir(plot_dir) if f.endswith('.png'))
    
    print(f"Initial PNG files in {plot_dir}: {len(initial_files)}")
    
    # Run plots-only analysis
    try:
        result = run_analysis(
            analysis_type="plots_only",
            selected_variables=["p13|IND"],
            user_query="Test plot generation"
        )
        
        if result.get('success', False):
            print("Plots-only analysis completed successfully")
            
            # Check for new files
            if os.path.exists(plot_dir):
                current_files = set(f for f in os.listdir(plot_dir) if f.endswith('.png'))
                new_files = current_files - initial_files
                
                print(f"Current PNG files: {len(current_files)}")
                print(f"New files generated: {len(new_files)}")
                
                if new_files:
                    print("New plot files:")
                    for file in sorted(new_files):
                        path = os.path.join(plot_dir, file)
                        size = os.path.getsize(path)
                        print(f"  - {file} ({size} bytes)")
                else:
                    print("No new files were generated (files may have been overwritten)")
            else:
                print(f"Plot directory {plot_dir} does not exist")
                
        else:
            print(f"Plots-only analysis failed: {result.get('error')}")
            
    except Exception as e:
        print(f"Exception during plot generation test: {e}")
    
    print()


if __name__ == "__main__":
    print("Starting comprehensive agent workflow tests...")
    print("=" * 60)
    
    # Run all tests
    test_agent_workflow_quick_insights()
    test_agent_workflow_plots_only()
    test_analysis_type_comparison()
    test_plot_file_generation()
    
    print("=" * 60)
    print("All agent workflow tests completed!")
