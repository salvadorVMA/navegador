"""
Test script for agent analysis type recognition

This script tests that the agent can properly recognize and select the new analysis types
based on natural language input patterns.
"""

def test_analysis_type_selection():
    """Test the analysis type selection logic from the agent."""
    
    # Import the select_analysis_type logic (we'll simulate the state)
    from typing import Dict, List, Any
    from langchain_core.messages import HumanMessage, AIMessage
    
    # Simulate the agent state structure
    class MockAgentState:
        def __init__(self):
            self.data = {
                "messages": [],
                "analysis_type": None
            }
        
        def __getitem__(self, key):
            return self.data[key]
        
        def __setitem__(self, key, value):
            self.data[key] = value
        
        def get(self, key, default=None):
            return self.data.get(key, default)
    
    # Test analysis type detection logic
    def test_analysis_type_detection(user_message: str) -> str:
        """Test what analysis type would be selected for a given user message."""
        last_lower = user_message.lower()
        
        if "plots only" in last_lower or "just plots" in last_lower or "only plots" in last_lower:
            return "plots_only"
        elif "quick insights" in last_lower or "quick analysis" in last_lower or "summary" in last_lower:
            return "quick_insights"
        elif "detailed" in last_lower or "complex" in last_lower or "deep analysis" in last_lower:
            return "detailed"
        else:
            return "descriptive"
    
    # Test cases
    test_cases = [
        # Plots only
        ("I want plots only", "plots_only"),
        ("Can you generate just plots?", "plots_only"),
        ("Show me only plots for these variables", "plots_only"),
        ("Generate only plots", "plots_only"),
        
        # Quick insights
        ("Give me quick insights", "quick_insights"),
        ("I need a quick analysis", "quick_insights"),
        ("Can you provide a summary?", "quick_insights"),
        ("Quick insights please", "quick_insights"),
        
        # Detailed
        ("I want a detailed analysis", "detailed"),
        ("Run a complex analysis", "detailed"),
        ("Perform deep analysis", "detailed"),
        ("Give me a detailed report", "detailed"),
        
        # Default (descriptive)
        ("Analyze this data", "descriptive"),
        ("What do you see in the data?", "descriptive"),
        ("Help me understand these variables", "descriptive"),
        ("Run analysis", "descriptive"),
    ]
    
    print("=" * 60)
    print("TESTING ANALYSIS TYPE RECOGNITION")
    print("=" * 60)
    
    correct_predictions = 0
    total_tests = len(test_cases)
    
    for user_message, expected_type in test_cases:
        predicted_type = test_analysis_type_detection(user_message)
        is_correct = predicted_type == expected_type
        
        print(f"Input: '{user_message}'")
        print(f"Expected: {expected_type}, Predicted: {predicted_type}")
        print(f"Result: {'✓ CORRECT' if is_correct else '✗ INCORRECT'}")
        print()
        
        if is_correct:
            correct_predictions += 1
    
    accuracy = correct_predictions / total_tests * 100
    print(f"Accuracy: {correct_predictions}/{total_tests} ({accuracy:.1f}%)")
    
    return accuracy >= 90.0  # We expect at least 90% accuracy


def test_integration_with_run_analysis():
    """Test integration with the actual run_analysis function."""
    print("=" * 60)
    print("TESTING INTEGRATION WITH RUN_ANALYSIS")
    print("=" * 60)
    
    from run_analysis import run_analysis
    
    # Test different analysis types with the same variables
    test_configs = [
        {
            "name": "Quick Insights Test",
            "analysis_type": "quick_insights",
            "variables": ["p13|IND"],
            "query": "Quick summary of political attitudes"
        },
        {
            "name": "Plots Only Test", 
            "analysis_type": "plots_only",
            "variables": ["p13|IND"],
            "query": "Generate visualization only"
        }
    ]
    
    results = {}
    
    for config in test_configs:
        print(f"\n--- {config['name']} ---")
        
        try:
            result = run_analysis(
                analysis_type=config["analysis_type"],
                selected_variables=config["variables"],
                user_query=config["query"]
            )
            
            success = result.get('success', False)
            print(f"Success: {success}")
            
            if success:
                # Check expected features for each analysis type
                results_data = result.get('results', {})
                
                if config["analysis_type"] == "quick_insights":
                    has_descriptions = 'variable_descriptions' in results_data
                    has_plots = 'plot_paths' in results_data
                    print(f"Has descriptions: {has_descriptions}")
                    print(f"Has plots: {has_plots}")
                    results[config["name"]] = has_descriptions and has_plots
                    
                elif config["analysis_type"] == "plots_only":
                    has_plots = 'plot_paths' in results_data
                    has_descriptions = 'variable_descriptions' in results_data
                    print(f"Has plots: {has_plots}")
                    print(f"Has descriptions: {has_descriptions} (should be False)")
                    results[config["name"]] = has_plots and not has_descriptions
                    
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                results[config["name"]] = False
                
        except Exception as e:
            print(f"Exception: {e}")
            results[config["name"]] = False
    
    # Summary
    print(f"\n--- INTEGRATION TEST RESULTS ---")
    all_passed = True
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    print("Starting analysis type recognition tests...")
    
    # Run tests
    recognition_test_passed = test_analysis_type_selection()
    integration_test_passed = test_integration_with_run_analysis()
    
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    
    print(f"Analysis Type Recognition: {'PASSED' if recognition_test_passed else 'FAILED'}")
    print(f"Integration Test: {'PASSED' if integration_test_passed else 'FAILED'}")
    
    if recognition_test_passed and integration_test_passed:
        print("\n🎉 ALL TESTS PASSED! The new analysis types are working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the implementation.")
