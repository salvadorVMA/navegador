"""
Integration module for meta-prompting system with existing analysis pipeline.

This module provides:
1. Drop-in replacements for existing prompt functions
2. Automatic performance tracking
3. Quality assessment
4. Monitoring dashboard data
"""

import time
import json
from typing import Dict, Any, Tuple, Optional
from meta_prompting import get_optimized_prompt, record_prompt_performance, get_prompt_manager


# =============================================================================
# QUALITY ASSESSMENT
# =============================================================================

class PromptQualityAssessor:
    """
    Assesses the quality of LLM responses to prompts.

    Quality factors:
    - Parsing success
    - Field completeness
    - Data citation (QUESTION_IDs present)
    - No hallucination indicators
    """

    @staticmethod
    def assess_cross_analysis_quality(
        response: str,
        parsed_data: Dict,
        expected_patterns: int
    ) -> float:
        """
        Assess quality of cross-analysis response.

        Args:
            response: Raw LLM response
            parsed_data: Parsed structured data
            expected_patterns: Number of patterns expected

        Returns:
            Quality score (0-100)
        """
        score = 0.0

        # Factor 1: Parsing success (30 points)
        if parsed_data and len(parsed_data) > 0:
            score += 30

        # Factor 2: Expected number of patterns (20 points)
        actual_patterns = len([k for k in parsed_data.keys() if 'PATTERN' in k])
        if actual_patterns >= expected_patterns:
            score += 20
        elif actual_patterns > 0:
            score += 20 * (actual_patterns / expected_patterns)

        # Factor 3: Field completeness (25 points)
        complete_patterns = 0
        for key, value in parsed_data.items():
            if 'PATTERN' in key and isinstance(value, dict):
                required_fields = ['TITLE_SUMMARY', 'VARIABLE_STRING', 'DESCRIPTION']
                if all(field in value and value[field] for field in required_fields):
                    complete_patterns += 1

        if actual_patterns > 0:
            score += 25 * (complete_patterns / actual_patterns)

        # Factor 4: Data citations present (15 points)
        citation_count = response.count('|')  # Question IDs have format pXX|ABC
        if citation_count >= expected_patterns:
            score += 15
        elif citation_count > 0:
            score += 15 * min(citation_count / expected_patterns, 1.0)

        # Factor 5: No obvious hallucination markers (10 points)
        hallucination_markers = [
            'i don\'t have',
            'i cannot',
            'as an ai',
            'i apologize',
            'i\'m not sure'
        ]

        has_hallucination = any(marker in response.lower() for marker in hallucination_markers)
        if not has_hallucination:
            score += 10

        return round(score, 2)

    @staticmethod
    def assess_expert_summary_quality(
        response: str,
        parsed_data: Dict
    ) -> float:
        """
        Assess quality of expert summary response.

        Returns:
            Quality score (0-100)
        """
        score = 0.0

        # Parsing success
        if parsed_data and 'EXPERT_REPLY' in parsed_data:
            score += 40

        # Length check (should be concise, 2-3 sentences)
        reply = parsed_data.get('EXPERT_REPLY', '')
        sentences = reply.count('.') + reply.count('!') + reply.count('?')
        if 2 <= sentences <= 4:
            score += 30
        elif sentences > 0:
            score += 30 * (1.0 - abs(sentences - 3) / 5)

        # Contains actionable insights
        insight_markers = ['should', 'recommends', 'suggests', 'indicates', 'implies']
        if any(marker in reply.lower() for marker in insight_markers):
            score += 30

        return round(score, 2)


# =============================================================================
# INTEGRATED PROMPT FUNCTIONS
# =============================================================================

def create_optimized_crosssum_prompt(
    user_query: str,
    tmp_res_st: str,
    n_topics: int = 5,
    format_instructions: str = "",
    request_id: Optional[str] = None
) -> str:
    """
    Drop-in replacement for create_prompt_crosssum that uses meta-prompting.

    Args:
        user_query: User's question
        tmp_res_st: Survey results string
        n_topics: Number of patterns to find
        format_instructions: Pydantic format instructions
        request_id: Optional request ID for A/B testing

    Returns:
        Optimized prompt string
    """
    variables = {
        'user_query': user_query,
        'results': tmp_res_st,
        'n_topics': n_topics,
        'format_instructions': format_instructions
    }

    prompt = get_optimized_prompt(
        'cross_analysis',
        variables,
        request_id=request_id
    )

    return prompt


def get_structured_summary_with_tracking(
    user_query: str,
    tmp_res_st: str,
    tmp_grade_dict: dict,
    model_name: str = 'gpt-4o-mini-2024-07-18',
    temperature: float = 0.9,
    get_answer_func = None,
    request_id: Optional[str] = None
) -> Tuple[str, dict, Dict[str, Any]]:
    """
    Enhanced version of get_structured_summary with performance tracking.

    Args:
        user_query: User's question
        tmp_res_st: Survey results string
        tmp_grade_dict: Graded variables dict
        model_name: LLM model to use
        temperature: Sampling temperature
        get_answer_func: Function to call LLM
        request_id: Optional request ID

    Returns:
        Tuple of (raw_response, parsed_dict, metadata)
    """
    from utility_functions import get_answer, clean_llm_json_output
    from langchain_core.output_parsers import PydanticOutputParser
    from detailed_analysis import FlatPatternSummary, pattern_parser_simdif, pattern_simdif_format_instructions

    if get_answer_func is None:
        get_answer_func = get_answer

    # Calculate n_topics
    n_topics = min(len(tmp_grade_dict) // 4, 5)

    # Get optimized prompt
    start_time = time.time()

    prompt = create_optimized_crosssum_prompt(
        user_query=user_query,
        tmp_res_st=tmp_res_st,
        n_topics=n_topics,
        format_instructions=pattern_simdif_format_instructions,
        request_id=request_id
    )

    # Call LLM
    content = get_answer_func(prompt, model=model_name, temperature=temperature)
    latency = time.time() - start_time

    # Clean and parse
    content = clean_llm_json_output(content)

    success = False
    parsed = {}
    try:
        parsed = pattern_parser_simdif.parse(content)
        parsed = parsed.model_dump()
        success = True
    except Exception as e:
        print(f"Parsing failed: {e}")

    # Assess quality
    assessor = PromptQualityAssessor()
    quality_score = assessor.assess_cross_analysis_quality(
        content,
        parsed,
        n_topics * 2  # Similar + Different patterns
    )

    # Estimate tokens (rough)
    tokens = len(prompt.split()) + len(content.split())

    # Get version that was used
    manager = get_prompt_manager()
    version = 'v2'  # Default, would need to track which was actually used

    # Record performance
    record_prompt_performance(
        'cross_analysis',
        version,
        tokens,
        latency,
        success,
        quality_score
    )

    # Prepare metadata
    metadata = {
        'prompt_version': version,
        'tokens_used': tokens,
        'latency': latency,
        'success': success,
        'quality_score': quality_score,
        'n_topics': n_topics
    }

    return content, parsed, metadata


def create_optimized_expert_prompt(
    pattern_title: str,
    variables: str,
    description: str,
    expert_context: str,
    format_instructions: str = ""
) -> str:
    """
    Create optimized expert summary prompt.

    Args:
        pattern_title: Title of the pattern
        variables: Variable string
        description: Pattern description
        expert_context: Expert knowledge context
        format_instructions: Format instructions

    Returns:
        Optimized prompt
    """
    prompt_variables = {
        'pattern_title': pattern_title,
        'variables': variables,
        'description': description,
        'expert_context': expert_context,
        'format_instructions': format_instructions
    }

    return get_optimized_prompt('expert_summary', prompt_variables)


def create_optimized_transversal_prompt(
    user_query: str,
    patterns_summary: str,
    format_instructions: str = ""
) -> str:
    """
    Create optimized transversal analysis prompt.

    Args:
        user_query: Original user query
        patterns_summary: Summary of identified patterns
        format_instructions: Format instructions

    Returns:
        Optimized prompt
    """
    prompt_variables = {
        'user_query': user_query,
        'patterns_summary': patterns_summary,
        'format_instructions': format_instructions
    }

    return get_optimized_prompt('transversal', prompt_variables)


# =============================================================================
# MONITORING AND REPORTING
# =============================================================================

def get_prompt_performance_dashboard() -> Dict[str, Any]:
    """
    Get dashboard data for prompt performance.

    Returns:
        Dict with performance metrics suitable for display
    """
    from meta_prompting import get_prompt_stats

    stats = get_prompt_stats()

    # Format for dashboard
    dashboard_data = {
        'overview': {
            'total_prompt_executions': stats['summary']['total_executions'],
            'avg_success_rate': f"{stats['summary']['avg_success_rate'] * 100:.1f}%",
            'avg_quality': f"{stats['summary']['avg_quality']:.1f}/100",
        },
        'by_template': {}
    }

    # Process each template
    for key, perf in stats['by_template'].items():
        template_name = perf['template_name']
        version = perf['version']

        if template_name not in dashboard_data['by_template']:
            dashboard_data['by_template'][template_name] = []

        dashboard_data['by_template'][template_name].append({
            'version': version,
            'executions': perf['execution_count'],
            'avg_tokens': int(perf['avg_tokens']),
            'avg_latency': f"{perf['avg_latency']:.2f}s",
            'success_rate': f"{perf['success_rate'] * 100:.1f}%",
            'quality': f"{perf['quality_score']:.1f}/100",
            'last_used': perf['last_used']
        })

    return dashboard_data


def print_prompt_report():
    """Print a formatted prompt performance report."""
    dashboard = get_prompt_performance_dashboard()

    print("=" * 80)
    print("PROMPT PERFORMANCE REPORT")
    print("=" * 80)

    # Overview
    overview = dashboard['overview']
    print("\n📊 Overview:")
    print(f"   Total Executions: {overview['total_prompt_executions']}")
    print(f"   Avg Success Rate: {overview['avg_success_rate']}")
    print(f"   Avg Quality Score: {overview['avg_quality']}")

    # By template
    for template_name, versions in dashboard['by_template'].items():
        print(f"\n📝 {template_name.replace('_', ' ').title()}:")
        for v in versions:
            print(f"   Version {v['version']}:")
            print(f"      Executions: {v['executions']}")
            print(f"      Avg Tokens: {v['avg_tokens']}")
            print(f"      Avg Latency: {v['avg_latency']}")
            print(f"      Success Rate: {v['success_rate']}")
            print(f"      Quality: {v['quality']}")

    print("\n" + "=" * 80)


# =============================================================================
# COMPARISON TOOLS
# =============================================================================

def compare_prompt_versions(
    template_type: str,
    version_a: str,
    version_b: str
) -> Dict[str, Any]:
    """
    Compare performance of two prompt versions.

    Args:
        template_type: Type of template
        version_a: First version
        version_b: Second version

    Returns:
        Comparison dict
    """
    manager = get_prompt_manager()

    key_a = f"{template_type}_{version_a}"
    key_b = f"{template_type}_{version_b}"

    perf_a = manager.performance.get(key_a)
    perf_b = manager.performance.get(key_b)

    if not perf_a or not perf_b:
        return {'error': 'One or both versions have no performance data'}

    comparison = {
        'version_a': version_a,
        'version_b': version_b,
        'metrics': {
            'executions': {
                'a': perf_a.execution_count,
                'b': perf_b.execution_count
            },
            'tokens': {
                'a': perf_a.avg_tokens,
                'b': perf_b.avg_tokens,
                'improvement': f"{((perf_a.avg_tokens - perf_b.avg_tokens) / perf_a.avg_tokens * 100):.1f}%"
            },
            'latency': {
                'a': perf_a.avg_latency,
                'b': perf_b.avg_latency,
                'improvement': f"{((perf_a.avg_latency - perf_b.avg_latency) / perf_a.avg_latency * 100):.1f}%"
            },
            'success_rate': {
                'a': perf_a.success_rate,
                'b': perf_b.success_rate,
                'improvement': f"{((perf_b.success_rate - perf_a.success_rate) * 100):.1f}%"
            },
            'quality': {
                'a': perf_a.quality_score,
                'b': perf_b.quality_score,
                'improvement': f"{((perf_b.quality_score - perf_a.quality_score) / perf_a.quality_score * 100):.1f}%"
            }
        },
        'winner': None
    }

    # Determine winner (weighted score)
    score_a = (
        perf_a.success_rate * 0.3 +
        (perf_a.quality_score / 100) * 0.4 +
        (1.0 / (1.0 + perf_a.avg_tokens / 1000)) * 0.3
    )

    score_b = (
        perf_b.success_rate * 0.3 +
        (perf_b.quality_score / 100) * 0.4 +
        (1.0 / (1.0 + perf_b.avg_tokens / 1000)) * 0.3
    )

    comparison['winner'] = version_a if score_a > score_b else version_b
    comparison['scores'] = {'a': round(score_a, 3), 'b': round(score_b, 3)}

    return comparison


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PROMPT INTEGRATION - Demo")
    print("=" * 80)

    # Simulate usage
    print("\n1. Get optimized prompt:")
    prompt = create_optimized_crosssum_prompt(
        user_query="What do Mexicans think about healthcare?",
        tmp_res_st="[Survey results would go here]",
        n_topics=3
    )
    print(f"✓ Generated {len(prompt)} character prompt")

    # Print report
    print("\n2. Performance Report:")
    print_prompt_report()

    print("\n" + "=" * 80)
    print("✅ Integration ready!")
    print("=" * 80)
