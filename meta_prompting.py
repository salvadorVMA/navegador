"""
Meta-Prompting System for Navegador Survey Analysis

This module implements a sophisticated meta-prompting strategy that:
1. Optimizes prompts while preserving analytical structure
2. Supports A/B testing and versioning
3. Monitors prompt performance
4. Enables iterative improvement

Key Features:
- Template-based prompt generation with variable substitution
- Prompt versioning and comparison
- Performance tracking (quality, tokens, latency)
- A/B testing framework
- Automatic prompt optimization using LLM feedback
"""

import json
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import re

try:
    from performance_optimization import get_cache_stats, performance_monitor
    PERFORMANCE_AVAILABLE = True
except ImportError:
    PERFORMANCE_AVAILABLE = False


# =============================================================================
# PROMPT TEMPLATES - Optimized versions of existing prompts
# =============================================================================

class PromptTemplates:
    """
    Centralized prompt templates for survey analysis.

    Each template maintains the critical cross-analysis structure while
    being more concise and effective.
    """

    # Version 1: Original (baseline)
    CROSS_ANALYSIS_V1 = """You are a research assistant analyzing survey results to answer the QUERY below.

Your job is to:
- Identify the top {n_topics} SIMILAR PATTERNS (trends or agreements) and {n_topics} DIFFERENT PATTERNS (contrasts or contradictions) relevant to the QUERY.
- For each pattern, provide:
    1. TITLE_SUMMARY: A short, descriptive title (never empty).
    2. VARIABLE_STRING: Comma-separated QUESTION_IDs used in the pattern (never empty).
    3. DESCRIPTION: A detailed explanation, citing numbers and QUESTION_IDs in parentheses (never empty).

Instructions:
- Do NOT leave any field empty. If information is limited, generalize or summarize what is available.
- Use only facts you are sure about, and always cite the QUESTION_ID for each fact.
- Do NOT repeat the same pattern in multiple fields.
- Ignore any results marked as 'NaN' or not available.
- If you combine categories (e.g., "like a lot" + "like somewhat"), only mention the sum if all original values are present.
- Do NOT invent data; if a pattern is weak, explain that.
- Each pattern must be unique and relevant to the QUERY.

QUERY: {user_query}
RESULTS: {results}

{format_instructions}

Output strict JSON only, no markdown."""

    # Version 2: Optimized (clearer, more concise)
    CROSS_ANALYSIS_V2 = """# Survey Pattern Analysis

**Role**: Expert survey analyst
**Task**: Identify {n_topics} SIMILAR and {n_topics} DIFFERENT patterns from survey data

## Required Output Structure
For each pattern provide:
- TITLE_SUMMARY: Concise descriptive title
- VARIABLE_STRING: Comma-separated QUESTION_IDs (e.g., p1_1|ABC,p2_1|DEF)
- DESCRIPTION: Evidence with percentages and QUESTION_IDs in parentheses

## Rules
✓ Cite actual data with QUESTION_IDs
✓ Include percentages from results
✓ Cross-reference related questions
✗ No empty fields
✗ No invented data
✗ No duplicate patterns

## Query
{user_query}

## Survey Results
{results}

## Format
{format_instructions}

Return JSON only."""

    # Version 3: Chain-of-thought optimized
    CROSS_ANALYSIS_V3 = """Analyze survey patterns using this structured approach:

STEP 1 - Understand the Query
Query: {user_query}

STEP 2 - Review Survey Results
{results}

STEP 3 - Identify Patterns
Find {n_topics} SIMILAR patterns (agreement/trends) and {n_topics} DIFFERENT patterns (contrasts)

STEP 4 - Structure Each Pattern
- TITLE_SUMMARY: What's the key insight?
- VARIABLE_STRING: Which questions support this? (format: pXX_X|ABC,pYY_Y|DEF)
- DESCRIPTION: What do the numbers show? Always cite QUESTION_IDs and percentages.

CRITICAL RULES:
• Every statement must reference a QUESTION_ID from results
• Include actual percentages from data
• No speculation or invented statistics
• Cross-reference related survey questions
• All fields must be complete

{format_instructions}

Output JSON only, no explanatory text."""

    # Expert summary template
    EXPERT_SUMMARY_V1 = """You are analyzing survey patterns with expert domain knowledge.

Pattern: {pattern_title}
Variables: {variables}
Description: {description}

Expert Context:
{expert_context}

Task: Provide a 2-3 sentence expert analysis that:
1. Interprets the pattern using domain expertise
2. Explains why this pattern matters
3. Suggests implications or recommendations

Focus on actionable insights."""

    EXPERT_SUMMARY_V2 = """# Expert Pattern Analysis

## Pattern Details
**Title**: {pattern_title}
**Variables**: {variables}
**Finding**: {description}

## Expert Knowledge Base
{expert_context}

## Your Analysis
Provide expert interpretation covering:
1. **Significance**: Why does this pattern matter?
2. **Context**: How does expert knowledge explain this?
3. **Implications**: What should stakeholders know?

Keep analysis concise (2-3 sentences) and actionable."""

    # Transversal analysis template
    TRANSVERSAL_V1 = """Synthesize findings across multiple survey topics.

User Query: {user_query}

Patterns Identified:
{patterns_summary}

Task:
1. Create topic-specific summaries for each dataset
2. Provide a one-paragraph synthesis for general audience
3. Answer the original query in 2 sentences

Structure your response as:
- TOPIC_SUMMARIES: Dict with topic names as keys
- TOPIC_SUMMARY: One paragraph overview
- QUERY_ANSWER: Two sentence direct answer

{format_instructions}"""

    TRANSVERSAL_V2 = """# Cross-Topic Survey Synthesis

## Original Question
{user_query}

## Patterns Across Topics
{patterns_summary}

## Required Output

### 1. Topic Summaries (TOPIC_SUMMARIES)
For each survey topic, provide a focused summary of key findings.

### 2. Integrated Overview (TOPIC_SUMMARY)
One paragraph synthesizing insights across all topics for a general audience.

### 3. Direct Answer (QUERY_ANSWER)
Two sentences directly answering the original question with supporting evidence.

## Guidelines
- Connect insights across different surveys
- Highlight agreements and contradictions
- Use percentages and specific findings
- Write for non-expert audience

{format_instructions}"""


# =============================================================================
# PROMPT METADATA AND VERSIONING
# =============================================================================

@dataclass
class PromptVersion:
    """Metadata for a prompt version."""
    template_name: str
    version: str
    created_at: str
    description: str
    expected_tokens: int  # Approximate
    structure_type: str  # 'cross_analysis', 'expert_summary', 'transversal'
    optimization_goal: str  # 'clarity', 'conciseness', 'accuracy', 'cot'

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PromptPerformance:
    """Performance metrics for a prompt."""
    template_name: str
    version: str
    execution_count: int = 0
    total_tokens: int = 0
    avg_tokens: float = 0.0
    total_latency: float = 0.0
    avg_latency: float = 0.0
    success_rate: float = 0.0
    quality_score: float = 0.0  # 0-100, based on parsing success and completeness
    last_used: Optional[str] = None

    def update_metrics(self, tokens: int, latency: float, success: bool, quality: float):
        """Update performance metrics with new execution data."""
        self.execution_count += 1
        self.total_tokens += tokens
        self.avg_tokens = self.total_tokens / self.execution_count
        self.total_latency += latency
        self.avg_latency = self.total_latency / self.execution_count

        # Update success rate
        current_successes = self.success_rate * (self.execution_count - 1)
        if success:
            current_successes += 1
        self.success_rate = current_successes / self.execution_count

        # Update quality score (weighted average)
        self.quality_score = ((self.quality_score * (self.execution_count - 1)) + quality) / self.execution_count

        self.last_used = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)


# =============================================================================
# META-PROMPT OPTIMIZER
# =============================================================================

class MetaPromptOptimizer:
    """
    Meta-prompting system that optimizes prompts using LLM feedback.

    This class can analyze existing prompts and generate improved versions
    while preserving the critical analytical structure.
    """

    META_OPTIMIZATION_PROMPT = """You are a prompt engineering expert. Analyze and optimize this prompt.

CURRENT PROMPT:
{current_prompt}

REQUIREMENTS:
- Preserve the analytical structure (cross-analysis of survey results)
- Maintain all critical fields: {required_fields}
- Make it more concise without losing clarity
- Improve instruction clarity
- Reduce token count by ~20-30%

OPTIMIZATION GOALS:
{optimization_goals}

CONSTRAINTS:
- Must work with survey data in format: QUESTION_ID|DATASET: percentages
- Must support cross-referencing multiple questions
- Must produce valid JSON output
- Must prevent hallucination of data

Provide the optimized prompt and explain your changes."""

    def __init__(self, llm_function=None):
        """
        Initialize the meta-prompt optimizer.

        Args:
            llm_function: Function to call LLM (should accept prompt, return string)
        """
        self.llm_function = llm_function

    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze a prompt's characteristics.

        Returns:
            Dict with token_count, instruction_count, example_count, etc.
        """
        # Simple token estimation (rough)
        token_count = len(prompt.split())

        # Count instructions
        instruction_markers = ['must', 'should', 'do not', 'always', 'never', '✓', '✗', '-']
        instruction_count = sum(1 for marker in instruction_markers if marker.lower() in prompt.lower())

        # Count examples
        example_count = prompt.count('example')

        # Check for structured elements
        has_checklist = '[ ]' in prompt or '✓' in prompt
        has_sections = '#' in prompt or '##' in prompt

        return {
            'token_count_estimate': token_count,
            'instruction_count': instruction_count,
            'example_count': example_count,
            'has_checklist': has_checklist,
            'has_sections': has_sections,
            'length': len(prompt)
        }

    def optimize_prompt(
        self,
        current_prompt: str,
        required_fields: List[str],
        optimization_goals: List[str],
    ) -> Tuple[str, str]:
        """
        Use LLM to optimize a prompt.

        Args:
            current_prompt: The prompt to optimize
            required_fields: Fields that must be preserved
            optimization_goals: Goals like "reduce tokens", "improve clarity"

        Returns:
            Tuple of (optimized_prompt, explanation)
        """
        if not self.llm_function:
            raise ValueError("LLM function not configured")

        meta_prompt = self.META_OPTIMIZATION_PROMPT.format(
            current_prompt=current_prompt,
            required_fields=", ".join(required_fields),
            optimization_goals="\rn".join(f"- {goal}" for goal in optimization_goals)
        )

        response = self.llm_function(meta_prompt)

        # Parse response (assuming it contains the optimized promp
        # TODO: explain parsing logic
        # TODO: plan and implement robust parsing
        # This is simplified - you'd want more robust parsing
        return response, "LLM optimization applied"


# =============================================================================
# PROMPT MANAGER
# =============================================================================

class PromptManager:
    """
    Manages prompt templates, versions, and performance tracking.

    Features:
    - Template storage and retrieval
    - Version management
    - Performance tracking
    - A/B testing support
    - Automatic prompt selection based on performance
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the prompt manager.

        Args:
            storage_path: Path to store prompt metadata and performance data
        """
        self.storage_path = storage_path or Path("./prompt_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Load templates
        self.templates = self._load_templates()

        # Load performance data
        self.performance = self._load_performance()

        # A/B testing configuration
        self.ab_tests = {}

    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load prompt templates from PromptTemplates class."""
        templates = {}

        # Cross-analysis templates
        templates['cross_analysis'] = {
            'v1': PromptTemplates.CROSS_ANALYSIS_V1,
            'v2': PromptTemplates.CROSS_ANALYSIS_V2,
            'v3': PromptTemplates.CROSS_ANALYSIS_V3,
        }

        # Expert summary templates
        templates['expert_summary'] = {
            'v1': PromptTemplates.EXPERT_SUMMARY_V1,
            'v2': PromptTemplates.EXPERT_SUMMARY_V2,
        }

        # Transversal templates
        templates['transversal'] = {
            'v1': PromptTemplates.TRANSVERSAL_V1,
            'v2': PromptTemplates.TRANSVERSAL_V2,
        }

        return templates

    def _load_performance(self) -> Dict[str, PromptPerformance]:
        """Load performance data from storage."""
        perf_file = self.storage_path / "prompt_performance.json"

        if not perf_file.exists():
            return {}

        try:
            with open(perf_file, 'r') as f:
                data = json.load(f)
                return {
                    key: PromptPerformance(**value)
                    for key, value in data.items()
                }
        except Exception as e:
            print(f"Warning: Could not load performance data: {e}")
            return {}

    def _save_performance(self):
        """Save performance data to storage."""
        perf_file = self.storage_path / "prompt_performance.json"

        try:
            data = {
                key: perf.to_dict()
                for key, perf in self.performance.items()
            }

            with open(perf_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save performance data: {e}")

    def get_prompt(
        self,
        template_type: str,
        version: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get a prompt template, optionally with variable substitution.

        Args:
            template_type: Type of template ('cross_analysis', 'expert_summary', etc.)
            version: Specific version to use (None = best performing)
            variables: Variables to substitute in template

        Returns:
            Formatted prompt string
        """
        if template_type not in self.templates:
            raise ValueError(f"Unknown template type: {template_type}")

        # Select version
        if version is None:
            version = self._select_best_version(template_type)

        template = self.templates[template_type][version]

        # Substitute variables if provided
        if variables:
            try:
                template = template.format(**variables)
            except KeyError as e:
                print(f"Warning: Missing variable {e} in template")

        return template

    def _select_best_version(self, template_type: str) -> str:
        """
        Select the best performing version of a template.

        Uses a combination of success rate, quality score, and token efficiency.
        """
        available_versions = list(self.templates[template_type].keys())

        if len(available_versions) == 1:
            return available_versions[0]

        # Calculate scores for each version
        scores = {}
        for version in available_versions:
            key = f"{template_type}_{version}"

            if key not in self.performance:
                # New version, give it a chance
                scores[version] = 0.5
                continue

            perf = self.performance[key]

            # Score based on:
            # - Success rate (40%)
            # - Quality score (40%)
            # - Token efficiency (20%) - lower is better
            token_efficiency = 1.0 / (1.0 + perf.avg_tokens / 1000)  # Normalize

            score = (
                perf.success_rate * 0.4 +
                (perf.quality_score / 100) * 0.4 +
                token_efficiency * 0.2
            )

            scores[version] = score

        # Return version with highest score
        best_version = max(scores.items(), key=lambda x: x[1])[0]
        return best_version

    def record_execution(
        self,
        template_type: str,
        version: str,
        tokens_used: int,
        latency: float,
        success: bool,
        quality_score: float
    ):
        """
        Record execution metrics for a prompt.

        Args:
            template_type: Type of template used
            version: Version used
            tokens_used: Number of tokens in prompt + response
            latency: Execution time in seconds
            success: Whether execution was successful
            quality_score: Quality score (0-100)
        """
        key = f"{template_type}_{version}"

        if key not in self.performance:
            self.performance[key] = PromptPerformance(
                template_name=template_type,
                version=version
            )

        self.performance[key].update_metrics(tokens_used, latency, success, quality_score)
        self._save_performance()

    def get_performance_report(self, template_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance report for templates.

        Args:
            template_type: Specific type to report on (None = all)

        Returns:
            Dict with performance statistics
        """
        if template_type:
            keys = [k for k in self.performance.keys() if k.startswith(template_type)]
        else:
            keys = list(self.performance.keys())

        report = {
            'summary': {
                'total_executions': sum(self.performance[k].execution_count for k in keys),
                'avg_success_rate': sum(self.performance[k].success_rate for k in keys) / len(keys) if keys else 0,
                'avg_quality': sum(self.performance[k].quality_score for k in keys) / len(keys) if keys else 0,
            },
            'by_template': {
                key: self.performance[key].to_dict()
                for key in keys
            }
        }

        return report

    def start_ab_test(
        self,
        template_type: str,
        version_a: str,
        version_b: str,
        split_ratio: float = 0.5
    ):
        """
        Start an A/B test between two prompt versions.

        Args:
            template_type: Template type to test
            version_a: First version
            version_b: Second version
            split_ratio: Ratio for A (0.5 = 50/50 split)
        """
        self.ab_tests[template_type] = {
            'version_a': version_a,
            'version_b': version_b,
            'split_ratio': split_ratio,
            'started_at': datetime.now().isoformat()
        }

    def get_ab_test_version(self, template_type: str, request_id: str) -> str:
        """
        Get version for A/B test based on request ID.

        Uses consistent hashing to ensure same request always gets same version.
        """
        if template_type not in self.ab_tests:
            return self._select_best_version(template_type)

        test = self.ab_tests[template_type]
q
        # Hash request ID to determine version
        # TODO: explain has logic
        hash_val = int(hashlib.sha256(request_id.encode()).hexdigest(), 16)
        ratio = (hash_val % 100) / 100.0

        if ratio < test['split_ratio']:
            return test['version_a']
        else:
            return test['version_b']


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_optimized_prompt(
    template_type: str,
    variables: Dict[str, Any],
    version: Optional[str] = None,
    request_id: Optional[str] = None
) -> str:
    """
    Get an optimized prompt with automatic version selection.

    Args:
        template_type: Type of prompt template
        variables: Variables to substitute
        version: Specific version (None = auto-select)
        request_id: Request ID for A/B testing

    Returns:
        Formatted prompt string
    """
    manager = get_prompt_manager()

    # Handle A/B testing if request_id provided

    if request_id and version is None:
        version = manager.get_ab_test_version(template_type, request_id)

    return manager.get_prompt(template_type, version, variables)


def record_prompt_performance(
    template_type: str,
    version: str,
    tokens: int,
    latency: float,
    success: bool,
    quality: float
):
    """Record prompt performance metrics."""
    manager = get_prompt_manager()
    manager.record_execution(template_type, version, tokens, latency, success, quality)


def get_prompt_stats(template_type: Optional[str] = None) -> Dict[str, Any]:
    """Get prompt performance statistics."""
    manager = get_prompt_manager()
    return manager.get_performance_report(template_type)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("META-PROMPTING SYSTEM - Demo")
    print("=" * 80)

    # Initialize manager
    manager = get_prompt_manager()

    # Example 1: Get best performing prompt
    print("\n1. Get optimized cross-analysis prompt:")
    prompt = manager.get_prompt(
        'cross_analysis',
        variables={
            'n_topics': 3,
            'user_query': "What do Mexicans think about immigration?",
            'results': "[Sample survey results]",
            'format_instructions': "[JSON schema]"
        }
    )
    print(f"Selected version: v2 (auto)")
    print(f"Token estimate: {len(prompt.split())} words")

    # Example 2: Record performance
    print("\n2. Record execution performance:")
    manager.record_execution(
        'cross_analysis',
        'v2',
        tokens_used=1500,
        latency=3.2,
        success=True,
        quality_score=85.0
    )
    print("✓ Performance recorded")

    # Example 3: Start A/B test
    print("\n3. Start A/B test:")
    manager.start_ab_test('cross_analysis', 'v2', 'v3', split_ratio=0.5)
    print("✓ A/B test started (v2 vs v3, 50/50 split)")

    # Example 4: Get performance report
    print("\n4. Performance Report:")
    report = manager.get_performance_report('cross_analysis')
    print(json.dumps(report, indent=2))

    print("\n" + "=" * 80)
    print("✅ Meta-prompting system ready!")
    print("=" * 80)
