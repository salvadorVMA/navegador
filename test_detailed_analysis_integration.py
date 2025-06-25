"""
Test the integrated detailed analysis workflow.

This test validates the complete pipeline from variable selection to 
detailed report generation using the logic extracted from nav_py13_reporte1.ipynb.
"""

import os
import sys
from unittest.mock import patch, MagicMock

# Add the project root to Python path
sys.path.append('/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador')

def test_detailed_analysis_import():
    """Test that the detailed analysis module can be imported"""
    try:
        from detailed_analysis import run_detailed_analysis, format_detailed_report
        print("✅ Successfully imported detailed analysis modules")
        return True
    except ImportError as e:
        print(f"❌ Failed to import detailed analysis: {e}")
        return False

def test_run_analysis_import():
    """Test that the updated run_analysis module can be imported"""
    try:
        from run_analysis import run_analysis, execute_analysis
        print("✅ Successfully imported updated run_analysis modules")
        return True
    except ImportError as e:
        print(f"❌ Failed to import run_analysis: {e}")
        return False

def test_detailed_analysis_basic_flow():
    """Test the basic flow of detailed analysis with mock data"""
    try:
        from detailed_analysis import run_detailed_analysis
        
        # Mock selected variables and query
        selected_variables = ["p1|ABC", "p2|DEF", "p3|GHI"]
        user_query = "What are the main patterns in Mexican identity?"
        
        # Test with basic parameters
        with patch('detailed_analysis.environment_setup') as mock_env, \
             patch('detailed_analysis.embedding_fun_openai') as mock_embed:
            
            # Mock environment setup
            mock_db = MagicMock()
            mock_db.get.return_value = {'ids': [], 'documents': []}
            mock_env.return_value = (MagicMock(), mock_db)
            mock_embed.return_value = [[0.1, 0.2, 0.3]]
            
            result = run_detailed_analysis(
                selected_variables=selected_variables,
                user_query=user_query
            )
            
            print(f"✅ Basic analysis flow completed")
            print(f"   Success: {result.get('success', False)}")
            print(f"   Analysis type: {result.get('analysis_type', 'unknown')}")
            print(f"   Report sections: {list(result.get('report_sections', {}).keys())}")
            
            # Validate structure
            assert 'success' in result
            assert 'analysis_type' in result
            assert 'report_sections' in result
            
            return True
            
    except Exception as e:
        print(f"❌ Basic analysis flow failed: {e}")
        return False

def test_run_analysis_integration():
    """Test the updated run_analysis function"""
    try:
        from run_analysis import run_analysis
        
        # Test detailed report analysis
        result = run_analysis(
            analysis_type="detailed_report",
            selected_variables=["p1|ABC", "p2|DEF"],
            user_query="Test query for analysis"
        )
        
        print(f"✅ Run analysis integration test completed")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Has formatted report: {'formatted_report' in result}")
        
        # Validate structure
        assert 'success' in result
        assert 'analysis_type' in result
        assert 'formatted_report' in result
        
        return True
        
    except Exception as e:
        print(f"❌ Run analysis integration failed: {e}")
        return False

def test_format_detailed_report():
    """Test the report formatting function"""
    try:
        from detailed_analysis import format_detailed_report
        
        # Mock analysis results
        mock_results = {
            'success': True,
            'query': 'Test query',
            'analysis_type': 'detailed_report',
            'selected_variables': ['p1|ABC', 'p2|DEF'],
            'report_sections': {
                'query_answer': 'This is a test answer to the query.',
                'topic_summary': 'This is a test summary of the analysis.',
                'topic_summaries': {
                    'IDENTITY': 'Mexican identity is complex...',
                    'VALUES': 'Core values include family and tradition...'
                },
                'expert_replies': [
                    'Expert insight 1 about the patterns found.',
                    'Expert insight 2 about cultural implications.'
                ]
            }
        }
        
        report = format_detailed_report(mock_results)
        
        print(f"✅ Report formatting test completed")
        print(f"   Report length: {len(report)} characters")
        print(f"   Contains query: {'Test query' in report}")
        print(f"   Contains sections: {'## Topic Analysis' in report}")
        
        # Validate report content
        assert len(report) > 100
        assert 'Test query' in report
        assert 'IDENTITY' in report
        assert 'Expert insight' in report
        
        return True
        
    except Exception as e:
        print(f"❌ Report formatting failed: {e}")
        return False

def test_agent_integration():
    """Test that the agent can use the new analysis system"""
    try:
        from agent import create_agent
        
        print("✅ Agent integration test - checking imports and structure")
        
        # Create agent without persistence (for testing)
        agent = create_agent(enable_persistence=False)
        
        print(f"   Agent created successfully")
        print(f"   Agent type: {type(agent)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent integration failed: {e}")
        return False

def test_error_handling():
    """Test error handling in the analysis pipeline"""
    try:
        from run_analysis import run_analysis
        
        # Test with invalid analysis type
        result = run_analysis(
            analysis_type="invalid_type",
            selected_variables=["p1|ABC"],
            user_query="Test query"
        )
        
        print(f"✅ Error handling test completed")
        print(f"   Success (should be False): {result.get('success', True)}")
        print(f"   Error message: {result.get('error', 'No error')}")
        
        assert result.get('success', True) == False
        assert 'error' in result
        
        # Test unimplemented analysis types
        result2 = run_analysis(
            analysis_type="comparative_analysis",
            selected_variables=["p1|ABC"],
            user_query="Test query"
        )
        
        print(f"   Unimplemented type handled: {not result2.get('success', True)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("🧪 Testing Detailed Analysis Integration")
    print("=" * 50)
    
    tests = [
        ("Import detailed analysis", test_detailed_analysis_import),
        ("Import run_analysis", test_run_analysis_import),
        ("Basic analysis flow", test_detailed_analysis_basic_flow),
        ("Run analysis integration", test_run_analysis_integration),
        ("Report formatting", test_format_detailed_report),
        ("Agent integration", test_agent_integration),
        ("Error handling", test_error_handling),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 Running: {name}")
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Detailed analysis integration is working.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()
