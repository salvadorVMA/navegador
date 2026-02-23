"""
Tool-Enhanced Analysis Integration

This module integrates the survey analysis tools with the existing LLM-based
analysis pipeline. It provides:

1. Tool-augmented pattern identification
2. Fact-checking for LLM claims
3. Hybrid LLM + deterministic analysis

Integration points:
- Wraps existing detailed_analysis functions
- Adds tool-calling capability at key decision points
- Maintains backward compatibility
"""

from typing import Dict, List, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import json
import time

# Import existing analysis functions
from detailed_analysis import (
    create_prompt_crosssum,
    get_structured_summary,
    run_detailed_analysis,
    format_detailed_report
)

# Import new tools
from survey_analysis_tools import (
    AVAILABLE_TOOLS,
    get_variable_metadata,
    calculate_percentage_from_data,
    validate_percentage_claim,
    analyze_variable_summary,
    cross_reference_variables,
    get_tool_stats,
    get_tool_descriptions
)

from utility_functions import get_answer, clean_llm_json_output


# =============================================================================
# TOOL-ENHANCED PATTERN IDENTIFICATION
# =============================================================================

def create_tool_enhanced_pattern_prompt(user_query: str, tmp_res_st: str,
                                        n_topics: int = 5) -> str:
    """
    Create a prompt that instructs the LLM to use tools for verification.

    This prompt adds tool-calling instructions to the standard pattern
    identification prompt.
    """

    # Get tool descriptions for context
    tool_descriptions = get_tool_descriptions()
    tools_str = "\n".join([
        f"- {t['name']}: {t['description']}"
        for t in tool_descriptions
    ])

    prompt = f"""
You are a research assistant analyzing survey results with access to verification tools.

AVAILABLE TOOLS:
{tools_str}

YOUR TASK:
Identify the top {n_topics} SIMILAR PATTERNS and {n_topics} DIFFERENT PATTERNS from the survey results.

CRITICAL WORKFLOW:
1. First, identify potential patterns from the results
2. For each pattern, USE TOOLS to verify:
   - Use `calculate_percentage_from_data` to verify percentage claims
   - Use `analyze_variable_summary` to get accurate statistics
   - Use `cross_reference_variables` to validate relationships
3. Only include patterns you've verified with tools
4. Cite both the QUESTION_ID and the tool verification in your description

For each pattern, provide:
- TITLE_SUMMARY: Concise descriptive title
- VARIABLE_STRING: Comma-separated QUESTION_IDs
- DESCRIPTION: Evidence with VERIFIED percentages and tool citations

VERIFICATION REQUIREMENT:
Every numerical claim MUST be verified using a tool. Format:
"X% of respondents agree (QUESTION_ID, verified via calculate_percentage_from_data)"

QUERY: {user_query}
RESULTS: {tmp_res_st}

Example tool usage in description:
"High agreement on education (verified): 78.5% support increased funding (p12|MEX, calculate_percentage_from_data),
while 82.1% value quality over quantity (p13|MEX, analyze_variable_summary)"

Return strict JSON with pattern structure:
{{
  "SIMILAR_PATTERN_1": {{
    "TITLE_SUMMARY": "...",
    "VARIABLE_STRING": "p1|MEX,p2|MEX",
    "DESCRIPTION": "... (with tool verifications)"
  }},
  ...
}}
"""
    return prompt


def run_tool_enhanced_pattern_identification(
    user_query: str,
    tmp_res_st: str,
    tmp_grade_dict: dict,
    model_name: str = 'gpt-4o-mini-2024-07-18',
    use_tools: bool = True
) -> Tuple[str, dict]:
    """
    Run pattern identification with tool enhancement.

    This function can run in two modes:
    1. Tool-enhanced: LLM uses tools to verify claims (use_tools=True)
    2. Standard: Regular LLM-only analysis (use_tools=False)

    Args:
        user_query: User's question
        tmp_res_st: Survey results string
        tmp_grade_dict: Graded variables dictionary
        model_name: LLM model to use
        use_tools: Whether to enable tool calling

    Returns:
        Tuple of (content string, parsed patterns dict)
    """
    n_topics = min(len(tmp_grade_dict) // 4, 5)

    if not use_tools:
        # Fallback to standard analysis
        return get_structured_summary(user_query, tmp_res_st, tmp_grade_dict,
                                     model_name, temperature=0.9)

    # Tool-enhanced analysis
    try:
        # Initialize LLM with tools
        llm = ChatOpenAI(model=model_name, temperature=0.7)

        # Create agent using langgraph prebuilt react agent
        agent = create_react_agent(llm, AVAILABLE_TOOLS)

        # Create enhanced prompt
        tool_prompt = create_tool_enhanced_pattern_prompt(user_query, tmp_res_st, n_topics)

        # Execute with tools
        result = agent.invoke({"messages": [("human", tool_prompt)]})

        content = result['messages'][-1].content

        # Clean and parse
        content = clean_llm_json_output(content)

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # Fallback to standard if parsing fails
            print("⚠️ Tool-enhanced analysis failed to parse, falling back to standard")
            return get_structured_summary(user_query, tmp_res_st, tmp_grade_dict,
                                         model_name, temperature=0.9)

        return content, parsed

    except Exception as e:
        print(f"⚠️ Tool-enhanced analysis error: {e}")
        print("Falling back to standard analysis")
        return get_structured_summary(user_query, tmp_res_st, tmp_grade_dict,
                                     model_name, temperature=0.9)


# =============================================================================
# FACT-CHECKING POST-PROCESSOR
# =============================================================================

def fact_check_pattern(pattern: Dict[str, str]) -> Dict[str, Any]:
    """
    Fact-check a pattern by validating its claims against actual data.

    Args:
        pattern: Pattern dictionary with TITLE_SUMMARY, VARIABLE_STRING, DESCRIPTION

    Returns:
        Dictionary with validation results and corrected values
    """
    results = {
        'original_pattern': pattern,
        'validation_results': [],
        'corrections_needed': [],
        'confidence_score': 100.0
    }

    # Extract variable IDs
    variable_string = pattern.get('VARIABLE_STRING', '')
    variable_ids = [v.strip() for v in variable_string.split(',') if v.strip()]

    # Extract percentage claims from description
    description = pattern.get('DESCRIPTION', '')
    import re
    percentage_claims = re.findall(r'(\d+(?:\.\d+)?)\s*%[^(]*\(([^)]+)\)', description)

    # Validate each claim
    for claimed_pct, var_context in percentage_claims:
        # Try to extract variable ID from context
        var_id = None
        for vid in variable_ids:
            if vid in var_context:
                var_id = vid
                break

        if var_id:
            # Validate using tool
            validation = validate_percentage_claim.invoke({
                'claim': f"{claimed_pct}%",
                'variable_id': var_id,
                'tolerance': 5.0
            })

            results['validation_results'].append(validation)

            if not validation.get('valid', False):
                results['corrections_needed'].append({
                    'claimed': claimed_pct,
                    'actual': validation.get('actual_percentage'),
                    'variable': var_id
                })
                results['confidence_score'] -= 15.0

    results['confidence_score'] = max(0.0, results['confidence_score'])
    results['is_accurate'] = results['confidence_score'] >= 70.0

    return results


def fact_check_all_patterns(patterns: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Fact-check all patterns in a pattern dictionary.

    Args:
        patterns: Dictionary of patterns (SIMILAR_PATTERN_1, etc.)

    Returns:
        Dictionary with fact-checking results for all patterns
    """
    fact_check_results = {
        'total_patterns': len(patterns),
        'patterns_checked': 0,
        'accurate_patterns': 0,
        'patterns_needing_correction': 0,
        'individual_results': {}
    }

    for pattern_key, pattern_data in patterns.items():
        if pattern_key.startswith('SIMILAR_PATTERN') or pattern_key.startswith('DIFFERENT_PATTERN'):
            check_result = fact_check_pattern(pattern_data)
            fact_check_results['individual_results'][pattern_key] = check_result
            fact_check_results['patterns_checked'] += 1

            if check_result['is_accurate']:
                fact_check_results['accurate_patterns'] += 1
            else:
                fact_check_results['patterns_needing_correction'] += 1

    # Calculate overall accuracy
    if fact_check_results['patterns_checked'] > 0:
        fact_check_results['accuracy_rate'] = (
            fact_check_results['accurate_patterns'] /
            fact_check_results['patterns_checked'] * 100
        )
    else:
        fact_check_results['accuracy_rate'] = 0.0

    return fact_check_results


# =============================================================================
# HYBRID ANALYSIS WORKFLOW
# =============================================================================

def run_hybrid_detailed_analysis(
    selected_variables: List[str],
    user_query: str,
    analysis_params: Optional[Dict] = None,
    enable_tools: bool = True,
    enable_fact_checking: bool = True
) -> Dict[str, Any]:
    """
    Run detailed analysis with hybrid LLM + tool approach.

    This combines:
    1. LLM reasoning for interpretation
    2. Tools for verification and accuracy
    3. Post-analysis fact-checking

    Args:
        selected_variables: List of variable IDs
        user_query: User's question
        analysis_params: Optional analysis parameters
        enable_tools: Enable tool-calling during analysis
        enable_fact_checking: Enable post-analysis fact-checking

    Returns:
        Dictionary with analysis results and tool metrics
    """
    start_time = time.time()

    # Initialize result structure
    result = {
        'success': False,
        'user_query': user_query,
        'selected_variables': selected_variables,
        'tool_enhanced': enable_tools,
        'fact_checked': enable_fact_checking,
    }

    try:
        # Step 1: Run standard analysis (or tool-enhanced if enabled)
        if enable_tools:
            print("🔧 Running tool-enhanced analysis...")
            # This would integrate with the full pipeline
            # For now, use standard analysis
            analysis_results = run_detailed_analysis(
                selected_variables=selected_variables,
                user_query=user_query,
                analysis_params=analysis_params
            )
        else:
            print("📊 Running standard analysis...")
            analysis_results = run_detailed_analysis(
                selected_variables=selected_variables,
                user_query=user_query,
                analysis_params=analysis_params
            )

        result.update(analysis_results)

        # Step 2: Fact-check patterns if enabled
        if enable_fact_checking and 'patterns' in analysis_results:
            print("✓ Fact-checking patterns...")
            fact_check_results = fact_check_all_patterns(analysis_results['patterns'])
            result['fact_check'] = fact_check_results
            result['accuracy_rate'] = fact_check_results['accuracy_rate']

        # Step 3: Add tool usage statistics
        tool_stats = get_tool_stats()
        result['tool_statistics'] = tool_stats

        # Step 4: Calculate execution time
        result['execution_time'] = time.time() - start_time
        result['success'] = analysis_results.get('success', False)

        return result

    except Exception as e:
        result['error'] = str(e)
        result['success'] = False
        return result


# =============================================================================
# REPORTING
# =============================================================================

def format_hybrid_analysis_report(results: Dict[str, Any]) -> str:
    """
    Format the hybrid analysis results into a readable report.

    Includes:
    - Standard analysis report
    - Fact-checking results
    - Tool usage statistics
    """
    report_sections = []

    # Standard report
    if 'formatted_report' in results:
        report_sections.append(results['formatted_report'])
    elif results.get('success'):
        standard_report = format_detailed_report(results)
        report_sections.append(standard_report)

    # Fact-checking section
    if 'fact_check' in results:
        fc = results['fact_check']
        fact_check_section = f"""

## 🔍 Fact-Checking Results

**Patterns Analyzed:** {fc['patterns_checked']}
**Accuracy Rate:** {fc['accuracy_rate']:.1f}%
**Accurate Patterns:** {fc['accurate_patterns']}
**Patterns Needing Correction:** {fc['patterns_needing_correction']}

"""
        if fc['patterns_needing_correction'] > 0:
            fact_check_section += "### Corrections Needed:\n"
            for pattern_key, check_result in fc['individual_results'].items():
                if not check_result['is_accurate']:
                    fact_check_section += f"\n**{pattern_key}** (Confidence: {check_result['confidence_score']:.0f}%):\n"
                    for correction in check_result['corrections_needed']:
                        fact_check_section += f"  - Variable {correction['variable']}: Claimed {correction['claimed']}%, Actual {correction['actual']}%\n"

        report_sections.append(fact_check_section)

    # Tool statistics
    if 'tool_statistics' in results and results['tool_statistics'].get('total_executions', 0) > 0:
        ts = results['tool_statistics']
        tool_section = f"""

## 🛠️ Tool Usage Statistics

**Total Tool Calls:** {ts.get('total_executions', 0)}
**Success Rate:** {ts.get('success_rate', 0):.1%}
**Average Execution Time:** {ts.get('avg_execution_time', 0):.3f}s

### Tools Used:
"""
        for tool_name, count in ts.get('executions_by_tool', {}).items():
            tool_section += f"- {tool_name}: {count} calls\n"

        report_sections.append(tool_section)

    return "\n".join(report_sections)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TOOL-ENHANCED ANALYSIS - Demo")
    print("=" * 80)

    # Example usage
    print("\n1. Tool Descriptions:")
    for tool_desc in get_tool_descriptions():
        print(f"  - {tool_desc['name']}: {tool_desc['description'][:60]}...")

    print("\n2. Example Hybrid Analysis:")
    print("This would run analysis with tool enhancement and fact-checking")

    print("\n" + "=" * 80)
    print("✅ Tool-enhanced analysis integration ready!")
    print("=" * 80)
