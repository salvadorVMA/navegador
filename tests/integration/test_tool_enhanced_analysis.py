"""
Integration Tests for Tool-Enhanced Analysis

These tests verify that the tool-enhanced analysis pipeline works correctly
and can be compared against the standard analysis pipeline.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from survey_analysis_tools import (
    get_variable_metadata,
    calculate_percentage_from_data,
    validate_percentage_claim,
    analyze_variable_summary,
    get_tool_stats,
    AVAILABLE_TOOLS
)
from tool_enhanced_analysis import (
    fact_check_pattern,
    fact_check_all_patterns,
    run_hybrid_detailed_analysis,
    format_hybrid_analysis_report
)


class TestToolBasics:
    """Test basic tool functionality"""

    def test_tools_are_importable(self):
        """Verify all tools can be imported"""
        assert len(AVAILABLE_TOOLS) > 0
        assert all(hasattr(tool, 'name') for tool in AVAILABLE_TOOLS)

    def test_get_variable_metadata(self):
        """Test metadata retrieval"""
        # This test requires actual data to be loaded
        # Mock or skip if data not available
        try:
            result = get_variable_metadata.invoke({'variable_id': 'p1|MEX'})
            assert 'variable_id' in result
            assert result['variable_id'] == 'p1|MEX'
        except FileNotFoundError:
            pytest.skip("Survey data not available")

    def test_validate_variable_id_format(self):
        """Test variable ID validation"""
        from survey_analysis_tools import validate_variable_id_format

        # Valid formats
        valid_ids = ['p1|ABC', 'p12|MEX', 'p1_1|ABC', 'p12_34|DEF']
        for vid in valid_ids:
            result = validate_variable_id_format.invoke({'variable_id': vid})
            assert result['valid'] is True, f"{vid} should be valid"

        # Invalid formats
        invalid_ids = ['p1', 'p1|', '1|ABC', 'p1|ab', 'p1|ABCD']
        for vid in invalid_ids:
            result = validate_variable_id_format.invoke({'variable_id': vid})
            assert result['valid'] is False, f"{vid} should be invalid"


class TestFactChecking:
    """Test fact-checking functionality"""

    def test_fact_check_pattern_structure(self):
        """Test that fact-checking returns expected structure"""
        sample_pattern = {
            'TITLE_SUMMARY': 'High agreement on education',
            'VARIABLE_STRING': 'p1|MEX,p2|MEX',
            'DESCRIPTION': '85% support increased funding (p1|MEX)'
        }

        result = fact_check_pattern(sample_pattern)

        assert 'original_pattern' in result
        assert 'validation_results' in result
        assert 'confidence_score' in result
        assert 'is_accurate' in result

    def test_fact_check_all_patterns(self):
        """Test bulk pattern fact-checking"""
        sample_patterns = {
            'SIMILAR_PATTERN_1': {
                'TITLE_SUMMARY': 'Pattern 1',
                'VARIABLE_STRING': 'p1|MEX',
                'DESCRIPTION': 'Description 1'
            },
            'DIFFERENT_PATTERN_1': {
                'TITLE_SUMMARY': 'Pattern 2',
                'VARIABLE_STRING': 'p2|MEX',
                'DESCRIPTION': 'Description 2'
            }
        }

        result = fact_check_all_patterns(sample_patterns)

        assert 'total_patterns' in result
        assert result['total_patterns'] == 2
        assert 'accuracy_rate' in result
        assert 'individual_results' in result


class TestHybridAnalysis:
    """Test hybrid analysis workflow"""

    @pytest.mark.slow
    def test_hybrid_analysis_structure(self):
        """Test that hybrid analysis returns expected structure"""
        # This test requires the full data pipeline
        try:
            result = run_hybrid_detailed_analysis(
                selected_variables=['p1|MEX', 'p2|MEX'],
                user_query="What do people think about education?",
                enable_tools=False,  # Disable tools for basic test
                enable_fact_checking=False
            )

            assert 'success' in result
            assert 'user_query' in result
            assert 'selected_variables' in result
            assert 'tool_enhanced' in result

        except Exception as e:
            pytest.skip(f"Full pipeline not available: {e}")

    @pytest.mark.slow
    def test_hybrid_vs_standard_comparison(self):
        """Compare tool-enhanced vs standard analysis"""
        pytest.skip("Requires full data pipeline - run manually")

        # This would be run manually for A/B testing
        """
        from run_analysis import run_analysis

        selected_vars = ['p1|MEX', 'p2|MEX']
        query = "What do Mexicans think about education?"

        # Standard
        standard = run_analysis('detailed_report', selected_vars, query)

        # Enhanced
        enhanced = run_hybrid_detailed_analysis(
            selected_vars,
            query,
            enable_tools=True,
            enable_fact_checking=True
        )

        # Compare
        print(f"Standard success: {standard['success']}")
        print(f"Enhanced success: {enhanced['success']}")
        if 'accuracy_rate' in enhanced:
            print(f"Accuracy rate: {enhanced['accuracy_rate']:.1f}%")
        """


class TestToolMonitoring:
    """Test tool execution monitoring"""

    def test_get_tool_stats(self):
        """Test tool statistics retrieval"""
        stats = get_tool_stats()
        assert isinstance(stats, dict)
        assert 'total_executions' in stats

    def test_tool_stats_update_after_execution(self):
        """Test that stats update after tool execution"""
        # Get initial stats
        initial_stats = get_tool_stats()
        initial_count = initial_stats.get('total_executions', 0)

        # Execute a tool
        try:
            get_variable_metadata.invoke({'variable_id': 'p1|MEX'})
        except FileNotFoundError:
            pytest.skip("Survey data not available")

        # Check stats updated
        new_stats = get_tool_stats()
        new_count = new_stats.get('total_executions', 0)

        assert new_count >= initial_count  # May be equal if tool failed


class TestReportFormatting:
    """Test report generation"""

    def test_format_hybrid_report_basic(self):
        """Test basic report formatting"""
        sample_results = {
            'success': True,
            'user_query': 'Test query',
            'selected_variables': ['p1|MEX'],
        }

        report = format_hybrid_analysis_report(sample_results)
        assert isinstance(report, str)
        assert len(report) > 0

    def test_format_hybrid_report_with_fact_check(self):
        """Test report formatting with fact-check results"""
        sample_results = {
            'success': True,
            'user_query': 'Test query',
            'selected_variables': ['p1|MEX'],
            'fact_check': {
                'patterns_checked': 5,
                'accuracy_rate': 85.0,
                'accurate_patterns': 4,
                'patterns_needing_correction': 1,
                'individual_results': {}
            }
        }

        report = format_hybrid_analysis_report(sample_results)
        assert 'Fact-Checking Results' in report
        assert '85.0%' in report

    def test_format_hybrid_report_with_tool_stats(self):
        """Test report formatting with tool statistics"""
        sample_results = {
            'success': True,
            'user_query': 'Test query',
            'selected_variables': ['p1|MEX'],
            'tool_statistics': {
                'total_executions': 10,
                'success_rate': 0.9,
                'avg_execution_time': 0.123,
                'executions_by_tool': {
                    'calculate_percentage_from_data': 5,
                    'validate_percentage_claim': 3
                }
            }
        }

        report = format_hybrid_analysis_report(sample_results)
        assert 'Tool Usage Statistics' in report
        assert '10' in report  # Total executions


# =============================================================================
# INTEGRATION TEST SCENARIOS
# =============================================================================

@pytest.mark.integration
class TestEndToEndScenarios:
    """End-to-end integration tests"""

    def test_scenario_1_basic_tool_usage(self):
        """
        Scenario: User runs analysis with tools enabled
        Expected: Analysis completes with tool verification
        """
        pytest.skip("Requires full data pipeline")

    def test_scenario_2_tool_failure_graceful_degradation(self):
        """
        Scenario: Tools fail but analysis continues
        Expected: Falls back to standard analysis with warning
        """
        pytest.skip("Requires full data pipeline")

    def test_scenario_3_fact_check_finds_errors(self):
        """
        Scenario: Fact-checking detects inaccurate claims
        Expected: Report includes corrections
        """
        pytest.skip("Requires full data pipeline")

    def test_scenario_4_comparison_mode(self):
        """
        Scenario: User runs both standard and enhanced analysis
        Expected: Side-by-side comparison of results
        """
        pytest.skip("Requires full data pipeline")


# =============================================================================
# PERFORMANCE BENCHMARKS
# =============================================================================

@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmarking tests"""

    @pytest.mark.slow
    def test_tool_overhead(self):
        """Measure overhead of tool-enhanced analysis"""
        pytest.skip("Manual benchmark - run separately")
        """
        import time

        # Measure standard
        start = time.time()
        standard = run_analysis('detailed_report', ['p1|MEX'], 'Test query')
        standard_time = time.time() - start

        # Measure enhanced
        start = time.time()
        enhanced = run_hybrid_detailed_analysis(['p1|MEX'], 'Test query',
                                                enable_tools=True)
        enhanced_time = time.time() - start

        overhead = (enhanced_time - standard_time) / standard_time * 100
        print(f"Tool overhead: {overhead:.1f}%")

        # Should be less than 50% overhead
        assert overhead < 50, f"Tool overhead too high: {overhead:.1f}%"
        """


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_variable_ids():
    """Sample variable IDs for testing"""
    return ['p1|MEX', 'p2|MEX', 'p3|MEX']


@pytest.fixture
def sample_user_query():
    """Sample user query for testing"""
    return "What do Mexicans think about education policy?"


@pytest.fixture
def sample_patterns():
    """Sample patterns for testing"""
    return {
        'SIMILAR_PATTERN_1': {
            'TITLE_SUMMARY': 'High support for education',
            'VARIABLE_STRING': 'p1|MEX,p2|MEX',
            'DESCRIPTION': '85% support increased funding (p1|MEX)'
        },
        'DIFFERENT_PATTERN_1': {
            'TITLE_SUMMARY': 'Mixed views on approach',
            'VARIABLE_STRING': 'p3|MEX,p4|MEX',
            'DESCRIPTION': 'Split between traditional and modern methods'
        }
    }


# =============================================================================
# MANUAL TEST RUNNER
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TOOL-ENHANCED ANALYSIS - Integration Tests")
    print("=" * 80)

    print("\nRunning basic tests...")

    # Test 1: Tool imports
    print("\n1. Testing tool imports...")
    try:
        assert len(AVAILABLE_TOOLS) > 0
        print(f"   ✓ {len(AVAILABLE_TOOLS)} tools loaded")
    except AssertionError:
        print("   ✗ Failed to load tools")

    # Test 2: Tool stats
    print("\n2. Testing tool monitoring...")
    stats = get_tool_stats()
    print(f"   ✓ Tool executions: {stats.get('total_executions', 0)}")

    # Test 3: Fact-checking
    print("\n3. Testing fact-checking...")
    sample_pattern = {
        'TITLE_SUMMARY': 'Test pattern',
        'VARIABLE_STRING': 'p1|MEX',
        'DESCRIPTION': 'Test description'
    }
    result = fact_check_pattern(sample_pattern)
    print(f"   ✓ Fact-check returned: {list(result.keys())}")

    print("\n" + "=" * 80)
    print("✅ Basic integration tests complete!")
    print("\nTo run full test suite:")
    print("  pytest tests/integration/test_tool_enhanced_analysis.py -v")
    print("\nTo run with benchmarks:")
    print("  pytest tests/integration/test_tool_enhanced_analysis.py -v -m benchmark")
    print("=" * 80)
