"""
Analytical Essay Generator for Navegador

Receives a structured quantitative report from the quantitative engine and
produces a data-driven analytical essay via LLM calls.

Pipeline:
1. Quantitative engine: compute statistics per variable (pure computation)
2. Relevance gate: filter variables by query relevance (ChromaDB + expert grading)
3. Reasoning outline: LLM maps variables AND variable pairs to query,
   builds evidence hierarchy with bivariate associations prioritized
4. Essay generation: LLM produces data-driven essay grounded in reasoning

Essay structure (data-driven, not dialectical):
- Summary: finding + evidence quality
- Data landscape: variables analyzed, coverage, distributions
- Evidence: bivariate associations first, then supporting univariate patterns
- Complications: demographic moderation, minority views, simulation limitations
- Implications: policy / understanding directions
"""

import json
import traceback
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
try:
    from langchain.output_parsers import PydanticOutputParser
except ImportError:
    from langchain_core.output_parsers import PydanticOutputParser

from utility_functions import get_answer, clean_llm_json_output
from quantitative_engine import (
    QuantitativeReport,
    build_quantitative_report,
    format_quantitative_report_for_llm,
)


# =============================================================================
# PYDANTIC OUTPUT MODELS
# =============================================================================

class ReasoningOutline(BaseModel):
    """Intermediate reasoning between data and essay."""
    variable_relevance: Dict[str, str] = Field(
        description="For each variable ID, explain HOW it relates to the query "
                    "and what aspect of the question it addresses"
    )
    variable_pairs: List[Dict[str, str]] = Field(
        description="For each pair of variables from different surveys, provide: "
                    "'var_a', 'var_b', 'expected_relationship' (what relationship "
                    "would we expect given the query?), 'actual_evidence' (what do "
                    "the cross-tab profiles and bivariate statistics show — how do "
                    "response distributions shift across conditioning categories, "
                    "what is the key contrast, V value, p-value, strength?). "
                    "If no bivariate data exists for a pair, note that."
    )
    evidence_hierarchy: str = Field(
        description="2-3 sentences: rank the available evidence from strongest "
                    "to weakest. Cross-dataset bivariate estimates with significant "
                    "p-values are primary. Demographic fault lines are secondary. "
                    "Univariate patterns are supporting context."
    )
    key_limitations: List[str] = Field(
        description="List of 2-4 methodological limitations or caveats about "
                    "the evidence (e.g., simulation-based estimates, small number "
                    "of cross-survey pairs, weak effect sizes)"
    )


class AnalyticalEssay(BaseModel):
    """Structured output for the data-driven analytical essay."""
    summary: str = Field(
        description="2-3 sentences: the single most important finding about the "
                    "relationship (or lack thereof) between the queried topics, "
                    "stated in plain language using actual data patterns (e.g., "
                    "'studying rates double among those with high tech access'). "
                    "Include a brief statement of evidence quality."
    )
    data_landscape: str = Field(
        description="One paragraph: how many variables were analyzed, which "
                    "surveys they come from, what proportion show consensus vs. "
                    "polarization vs. dispersion, and what the overall divergence "
                    "index tells us about agreement levels"
    )
    evidence: str = Field(
        description="The core analytical section. MUST lead with substantive "
                    "descriptions of cross-tab patterns — how response "
                    "distributions shift across conditioning categories. Use the "
                    "conditional profiles to state what the data LOOKS LIKE in "
                    "plain language (e.g., '25% vs 12%'). Cite V and p "
                    "parenthetically as supporting evidence: (V=0.18, p<0.001). "
                    "Demographic fault lines should describe concrete subgroup "
                    "differences. Univariate distributions are supporting context."
    )
    complications: str = Field(
        description="Paragraph(s) discussing: demographic moderation effects "
                    "(which SES dimensions show the strongest V values and what "
                    "subgroup differences mean), minority views that challenge "
                    "the main finding, simulation limitations (SES-bridge "
                    "assumptions, sample sizes), and any variables where the "
                    "relationship is absent or opposite to expectation"
    )
    implications: str = Field(
        description="At least 2 genuinely different interpretations or policy "
                    "directions that follow from the evidence. These should "
                    "account for the evidence quality and complications described "
                    "above, not just restate the findings."
    )


# =============================================================================
# PROMPTS
# =============================================================================

ESSAY_SYSTEM_PROMPT = """You are an expert analyst writing for an audience of social scientists and policy makers.
You are fully bilingual in English and Spanish. You write your essay in the same language as the QUERY.
You produce substantive analytical essays that answer the user's question using data patterns, not statistics recitation.

ABSOLUTE RULES:
1. Every percentage and V value you cite MUST appear in the QUANTITATIVE REPORT below. Do NOT invent, round differently, or extrapolate numbers.
2. RELATIONSHIP QUERIES: When the query asks how X relates to Y, the EVIDENCE section MUST open with substantive descriptions of HOW the relationship manifests in the data. Use the conditional distribution profiles ("How Y responses shift across X categories") to describe what the relationship LOOKS LIKE in plain language. For example: "Among those who perceive 'mucho' technology access, 25% are currently studying vs only 12% among those who perceive 'poco' access." Cite Cramér's V and p-values in PARENTHESES as supporting evidence, NOT as the lead sentence. If the association is weak or absent, describe the uniformity: "Regardless of X level, Y responses remain virtually identical (~Z% across all groups)."
3. Variables classified as "polarized" or "dispersed" must receive attention proportional to their relevance to the query.
4. Any minority opinion (>15%) mentioned in the quantitative report must be explicitly discussed; it must NEVER be dismissed or minimized.
5. The IMPLICATIONS section must contain at least 2 genuinely different interpretations or policy directions — not restatements of the same idea.
6. Do NOT use the word "overall" to paper over genuine disagreement in the data.
7. If the data shows polarization, say so directly; do not soften it.
8. Only discuss data points that are LOGICALLY CONNECTED to the query. Follow the REASONING OUTLINE to maintain analytical coherence.
9. DEMOGRAPHIC FAULT LINES: Describe concrete subgroup differences in the COMPLICATIONS section: "Women are 15 points more likely than men to say X." Do not just cite V values — state what the actual difference IS, using the demographic breakdowns provided per variable.
10. NON-SIGNIFICANT RESULTS: If cross-dataset bivariate estimates show p >= 0.05 or V < 0.05, these must be reported as evidence of a weak or absent relationship. Do not omit them.
11. CROSS-TAB PROFILES: When the report includes "How Y responses shift across X categories" data, you MUST use these conditional distributions to build your narrative. The "Key contrast" line identifies the most variable response category — lead with that pattern. Translate data into substantive sentences about people's views, not into statistics reports.
12. DATA TABLES IN TEXT: For EVERY variable whose distribution you discuss in the EVIDENCE or COMPLICATIONS sections, you MUST include a markdown table immediately after the prose. No exceptions — prose-only summaries with numbers in parentheses are forbidden.
    - Tables go INSIDE the string value of the relevant field (evidence, complications), embedded as inline markdown — do NOT add extra JSON keys for tables.
    - For a univariate distribution, use a frequency table: bold caption line with variable ID above the table, then | Response | % | rows. The variable ID (e.g. "p2|EDU") MUST appear only in the bold caption line — NEVER inside a table cell. Example:
      **p3|SOC** — Technology access perception:\n| Response | % |\n|---|---|\n| Mucho | 47.1% |\n| Poco | 35.2% |
    - For a cross-tabulation, include the conditional distribution table showing how the key response varies across groups.
    - Use ONLY data from the QUANTITATIVE REPORT — do not invent numbers."""


REASONING_SYSTEM_PROMPT = """You are an expert survey research methodologist.
You are fully bilingual in English and Spanish.
Your task is to evaluate how survey variables relate to a research question
and build an evidence hierarchy BEFORE writing the essay.

Be rigorous: if a variable does not logically connect to the query,
say so explicitly. Do not force connections that don't exist.
When bivariate estimates are available, these are stronger evidence
about relationships than comparing individual variable distributions."""


def create_reasoning_prompt(
    user_query: str,
    quantitative_report_text: str,
    format_instructions: str,
) -> str:
    """
    Build the prompt for the intermediate reasoning step.

    This step maps each variable to the query, identifies variable pairs
    and their bivariate evidence, and builds an evidence hierarchy.
    """
    return f"""QUERY: {user_query}

QUANTITATIVE REPORT:
{quantitative_report_text}

YOUR TASK:
Before writing an analytical essay, reason about the evidence structure.

Step 1 — Variable relevance:
For each variable, explain specifically HOW it addresses the QUERY.
If a variable has a weak or tangential connection, say so explicitly.

Step 2 — Variable pairs and bivariate evidence:
For every pair of variables from DIFFERENT surveys (different three-letter codes
after the pipe), identify:
- What relationship would we EXPECT between them given the query?
- What does the cross-dataset bivariate estimate ACTUALLY show (V value, p-value)?
- Is the relationship statistically significant (p < 0.05)?
If no bivariate estimate exists for a pair, note that gap.

Step 3 — Evidence hierarchy:
Rank the available evidence. Cross-dataset bivariate estimates with significant
p-values are the strongest evidence about relationships between topics.
Demographic fault lines are the next tier. Univariate distributions are
supporting context only — comparing two marginal distributions side by side
does NOT demonstrate a relationship.

Step 4 — Limitations:
List methodological caveats: simulation-based estimates, sample sizes,
number of variables analyzed, relevance of available variables to the query.

{format_instructions}

IMPORTANT: Return valid JSON only. No markdown formatting, no code blocks, no extra text."""


def create_essay_prompt(
    user_query: str,
    quantitative_report_text: str,
    reasoning_text: str,
    format_instructions: str,
) -> str:
    """
    Build the full prompt for the analytical essay LLM call.

    Includes the reasoning outline to ground the essay in evidence hierarchy.
    """
    return f"""QUERY: {user_query}

QUANTITATIVE REPORT:
{quantitative_report_text}

REASONING OUTLINE (follow this evidence hierarchy):
{reasoning_text}

YOUR TASK:
Write a structured analytical essay based EXCLUSIVELY on the quantitative report above.
The essay must address the QUERY using the evidence in the report.
Follow the REASONING OUTLINE to ensure you respect the evidence hierarchy:
bivariate associations first, then demographic patterns, then univariate distributions.

STRUCTURE (each key must be a non-empty string):

1. "summary": 2-3 sentences. State the single most important finding about the
   relationship between the queried topics. Then state the evidence quality:
   how many bivariate pairs were estimated, whether associations are significant,
   and what the overall confidence level is.

2. "data_landscape": One paragraph. Describe the scope: how many variables were
   analyzed, which surveys they come from, and what the distribution shapes
   (consensus/lean/polarized/dispersed) and divergence index tell us about the
   level of agreement in public opinion on these topics.

3. "evidence": This is the core section. STRUCTURE IT AS FOLLOWS:
   A) SUBSTANTIVE CROSS-TAB PATTERNS FIRST: For each cross-dataset variable pair,
      describe WHAT the relationship looks like using the conditional distribution
      profiles ("How Y responses shift across X categories"). Lead with the
      "Key contrast" category — how its prevalence shifts across conditioning
      categories. For example: "The proportion currently studying ranges from 12%
      among those perceiving 'poco' technology access to 25% among those perceiving
      'mucho' access (V=0.178, p<0.001)."
      If V < 0.1, describe the uniformity: "Regardless of X category, Y responses
      remain virtually identical (~Z% across all groups), confirming no meaningful
      association (V=0.05, p=0.32)."
      A weak or absent relationship IS a finding — describe the uniformity.
      IMPORTANT: After describing each cross-tab relationship, include the
      conditional distribution as a markdown table:
        | [var_b] category | [key var_a response] % |
        |---|---|
        | CategoryA | X% |
        | CategoryB | Y% |
   B) DEMOGRAPHIC MODERATION: Describe how responses differ across SES groups using
      the expanded demographic breakdowns. Do not just cite V values — state what
      the difference IS: "Women are 15 points more likely than men to say X (V=0.14)."
      Use the top-2 response categories shown per group.
   C) SUPPORTING UNIVARIATE PATTERNS: For each variable discussed, include its
      frequency table as a markdown table. The variable ID is a CAPTION that goes
      on its own line ABOVE the table header — it must NEVER appear inside a table
      cell. Use this exact format:

      **[variable_id]** — [brief question description]:
      | Response | % |
      |---|---|
      | OptionA | X% |
      | OptionB | Y% |

      The Response column contains only the response label (e.g. "Sí", "No",
      "Mucho"). The variable ID (e.g. "p2|EDU") belongs only in the bold caption
      line above the table, never in the Response column.
      Use only data from the QUANTITATIVE REPORT. Group by distribution shape.

4. "complications": Discuss factors that complicate the main findings:
   - Which SES dimensions moderate responses most strongly (exact V values)?
   - Minority views (>15%) that run counter to the dominant pattern
   - Simulation limitations: SES-bridge assumptions, sample sizes
   - Variables where the evidence is absent or contradictory
   Do not soften or hedge. If the relationship is weak, say so.

5. "implications": At least 2 distinct policy implications or interpretations.
   These must account for the evidence quality and complications above.
   Consider: what does a strong bivariate association suggest vs. a weak one?
   What would different levels of confidence in the data lead to?

{format_instructions}

IMPORTANT: Return valid JSON only. No markdown formatting around the JSON, no code blocks, no extra text. The JSON must contain EXACTLY the fields defined in the schema — do NOT add extra keys for tables or any other content."""


# =============================================================================
# ESSAY GENERATION
# =============================================================================

# Initialize parsers
essay_parser = PydanticOutputParser(pydantic_object=AnalyticalEssay)
essay_format_instructions = essay_parser.get_format_instructions()

reasoning_parser = PydanticOutputParser(pydantic_object=ReasoningOutline)
reasoning_format_instructions = reasoning_parser.get_format_instructions()


def generate_reasoning_outline(
    user_query: str,
    quant_text: str,
    model_name: str = 'gpt-4.1-mini-2025-04-14',
    temperature: float = 0.2,
) -> dict:
    """
    Generate an intermediate reasoning outline that maps variables to the query.

    This step ensures the essay has logical coherence by:
    1. Articulating HOW each variable relates to the question
    2. Identifying variable pairs and their bivariate evidence
    3. Building an evidence hierarchy

    Args:
        user_query: The user's original query
        quant_text: Formatted quantitative report string
        model_name: LLM model to use
        temperature: Low temperature for analytical precision

    Returns:
        dict with reasoning outline fields
    """
    print("[analytical_essay] Generating reasoning outline...")

    prompt = create_reasoning_prompt(
        user_query, quant_text, reasoning_format_instructions
    )

    response = get_answer(
        prompt=prompt,
        system_prompt=REASONING_SYSTEM_PROMPT,
        model=model_name,
        temperature=temperature,
    )

    if response is None:
        return {
            'variable_relevance': {},
            'variable_pairs': [],
            'evidence_hierarchy': 'Reasoning step failed — proceed with direct analysis.',
            'key_limitations': [],
        }

    try:
        cleaned = clean_llm_json_output(response)
        reasoning = reasoning_parser.parse(cleaned)
        result = reasoning.model_dump()
        print(f"[analytical_essay] Reasoning: {len(result.get('variable_relevance', {}))} variables mapped, "
              f"{len(result.get('variable_pairs', []))} pairs identified")
        return result
    except Exception as e:
        print(f"[analytical_essay] Reasoning parse error (non-fatal): {e}")
        return {
            'variable_relevance': {},
            'variable_pairs': [],
            'evidence_hierarchy': 'Reasoning step failed — proceed with direct analysis.',
            'key_limitations': [],
        }


def format_reasoning_for_essay(reasoning_dict: dict) -> str:
    """Format the reasoning outline as text for inclusion in the essay prompt."""
    parts = []

    var_rel = reasoning_dict.get('variable_relevance', {})
    if var_rel:
        parts.append("VARIABLE-QUERY MAPPING:")
        for var_id, explanation in var_rel.items():
            parts.append(f"  - {var_id}: {explanation}")

    var_pairs = reasoning_dict.get('variable_pairs', [])
    if var_pairs:
        parts.append("\nVARIABLE PAIRS AND BIVARIATE EVIDENCE:")
        for pair in var_pairs:
            var_a = pair.get('var_a', '?')
            var_b = pair.get('var_b', '?')
            expected = pair.get('expected_relationship', '?')
            actual = pair.get('actual_evidence', '?')
            parts.append(f"  - {var_a} x {var_b}:")
            parts.append(f"    Expected: {expected}")
            parts.append(f"    Actual: {actual}")

    hierarchy = reasoning_dict.get('evidence_hierarchy', '')
    if hierarchy:
        parts.append(f"\nEVIDENCE HIERARCHY: {hierarchy}")

    limitations = reasoning_dict.get('key_limitations', [])
    if limitations:
        parts.append("\nKEY LIMITATIONS:")
        for i, lim in enumerate(limitations, 1):
            parts.append(f"  {i}. {lim}")

    return '\n'.join(parts) if parts else "No reasoning outline available."


def generate_analytical_essay(
    selected_variables: List[str],
    user_query: str,
    model_name: str = 'gpt-4.1-mini-2025-04-14',
    temperature: float = 0.4,
) -> dict:
    """
    Main entry point: relevance filter → quantitative report → reasoning → essay.

    Pipeline:
    1. Build quantitative report with relevance gate (filters irrelevant variables)
    2. Generate reasoning outline (maps variables and pairs to query)
    3. Generate essay grounded in evidence hierarchy

    Args:
        selected_variables: List of variable IDs
        user_query: The user's original query
        model_name: LLM model to use
        temperature: LLM temperature (lower for factual accuracy)

    Returns:
        dict with keys: success, essay, quantitative_report,
        formatted_report, report_sections, reasoning
    """
    print(f"[analytical_essay] Starting for query: {user_query}")
    print(f"[analytical_essay] Variables: {selected_variables}")

    try:
        # Phase 1: Quantitative engine with relevance gate
        # (auto-correction constrained to same survey code,
        #  relevance filter using ChromaDB + expert grading)
        print("[analytical_essay] Building quantitative report (with relevance gate)...")
        quant_report = build_quantitative_report(
            selected_variables,
            user_query=user_query,
            relevance_filter=True,
        )

        if quant_report.variable_count == 0:
            return _error_result(
                user_query, selected_variables,
                "No valid or relevant variables found for the selected variable IDs."
            )

        quant_text = format_quantitative_report_for_llm(quant_report)
        print(f"[analytical_essay] Quantitative report: {quant_report.variable_count} variables, "
              f"divergence index: {quant_report.divergence_index:.1%}")

        # Phase 2: Intermediate reasoning step
        reasoning_dict = generate_reasoning_outline(
            user_query, quant_text, model_name, temperature=0.2
        )
        reasoning_text = format_reasoning_for_essay(reasoning_dict)

        # Phase 3: LLM essay generation (grounded in reasoning)
        print("[analytical_essay] Generating essay...")
        prompt = create_essay_prompt(
            user_query, quant_text, reasoning_text, essay_format_instructions
        )

        response = get_answer(
            prompt=prompt,
            system_prompt=ESSAY_SYSTEM_PROMPT,
            model=model_name,
            temperature=temperature
        )

        if response is None:
            return _error_result(user_query, selected_variables, "No response from LLM")

        # Parse response
        cleaned = clean_llm_json_output(response)
        essay = essay_parser.parse(cleaned)
        essay_dict = essay.model_dump()

        # Build metadata from quantitative report
        metadata = {
            'variable_count': quant_report.variable_count,
            'shape_counts': quant_report.shape_summary,
            'divergence_index': quant_report.divergence_index,
            'polarized_variables': [
                v.var_id for v in quant_report.variables if v.shape == 'polarized'
            ],
            'dispersed_variables': [
                v.var_id for v in quant_report.variables if v.shape == 'dispersed'
            ],
        }

        # Format as markdown
        formatted = format_analytical_essay_report(
            essay_dict, user_query, quant_report, metadata, reasoning_dict
        )

        return {
            'query': user_query,
            'selected_variables': selected_variables,
            'analysis_type': 'analytical_essay',
            'success': True,
            'essay': essay_dict,
            'reasoning': reasoning_dict,
            'quantitative_report': quant_report.model_dump(),
            'formatted_report': formatted,
            'report_sections': {
                'query_answer': essay_dict.get('summary', ''),
                'topic_summary': essay_dict.get('data_landscape', ''),
                'evidence': essay_dict.get('evidence', ''),
                'complications': essay_dict.get('complications', ''),
                'implications': essay_dict.get('implications', ''),
                # Backward compat for dashboard/debug scripts
                'prevailing_view': essay_dict.get('evidence', ''),
                'counterargument': essay_dict.get('complications', ''),
            },
            'metadata': metadata,
        }

    except Exception as e:
        print(f"[analytical_essay] Error: {e}")
        traceback.print_exc()
        return _error_result(user_query, selected_variables, str(e))


def _error_result(user_query: str, selected_variables: list, error_msg: str) -> dict:
    """Build standardized error result dict."""
    return {
        'query': user_query,
        'selected_variables': selected_variables,
        'analysis_type': 'analytical_essay',
        'success': False,
        'error': error_msg,
        'formatted_report': f'Error generating analytical essay: {error_msg}',
        'report_sections': {
            'query_answer': f'Error: {error_msg}',
            'topic_summary': '',
            'evidence': '',
            'complications': '',
            'implications': '',
            'prevailing_view': '',
            'counterargument': '',
        },
    }


# =============================================================================
# REPORT FORMATTING — HELPERS
# =============================================================================

def _format_variable_details(quant_report: Optional[QuantitativeReport]) -> str:
    """Render the per-variable statistics block for the appendix."""
    if not quant_report or not quant_report.variables:
        return ""
    lines = ["\n### Variable Details\n"]
    for v in quant_report.variables:
        lines.append(f"\n**{v.var_id}** ({v.shape})")
        lines.append(f"- Question: {v.question_text[:150]}")
        lines.append(f"- Mode: {v.modal_response} ({v.modal_percentage:.1f}%)")
        lines.append(
            f"- Runner-up: {v.runner_up_response} ({v.runner_up_percentage:.1f}%), "
            f"margin: {v.margin:.1f}pp"
        )
        lines.append(f"- HHI: {v.hhi:.0f}")
        if v.minority_opinions:
            minorities = ", ".join(
                f"{label} ({pct:.1f}%)" for label, pct in v.minority_opinions.items()
            )
            lines.append(f"- Minority opinions: {minorities}")
        # Full marginal frequency table
        if v.frequencies:
            lines.append("\n| Response | % |")
            lines.append("|----------|---|")
            for label, pct in sorted(
                v.frequencies.items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"| {label} | {pct:.1f}% |")
    return "\n".join(lines) + "\n"


def _cramers_v_strength(v: float) -> str:
    """Label a Cramér's V value as weak / moderate / strong."""
    if v < 0.1:
        return 'weak'
    if v < 0.3:
        return 'moderate'
    return 'strong'


def _format_bivariate_variable_block(variables) -> str:
    """Render the per-variable demographic breakdown detail lines."""
    lines = ["\n**Variable-Level Demographic Detail:**"]
    for v in variables:
        if not v.bivariate_stats:
            continue
        lines.append(f"\n*{v.var_id}*")
        for ses_var, biv in sorted(
            v.bivariate_stats.items(),
            key=lambda x: x[1].get('cramers_v') or 0,
            reverse=True,
        ):
            cv = biv.get('cramers_v') or 0
            p = biv.get('p_value') or 1.0
            top_groups = [
                f"{g}: {info['first']['category']} ({info['first']['proportion']*100:.0f}%)"
                for g, info in list(biv.get('leaders', {}).items())[:3]
                if 'first' in info
            ]
            suffix = (" — " + "; ".join(top_groups)) if top_groups else ""
            lines.append(f"- {ses_var}: V={cv:.3f} (p={p:.3f}){suffix}")
    return "\n".join(lines)


def _format_demographic_fault_lines(
    fault_lines: dict,
    quant_report: Optional[QuantitativeReport],
) -> str:
    """Render the demographic fault lines table and per-variable breakdowns."""
    lines = [
        "\n### Demographic Fault Lines\n",
        "| Dimension | Mean Cramér's V | Max Cramér's V | Variables |",
        "|-----------|----------------|----------------|----------|",
    ]
    for ses_var, info in fault_lines.items():
        strength = _cramers_v_strength(info['mean_cramers_v'])
        lines.append(
            f"| {ses_var} | {info['mean_cramers_v']:.3f} ({strength}) "
            f"| {info['max_cramers_v']:.3f} | {info['n_significant']} |"
        )

    if quant_report and any(v.bivariate_stats for v in quant_report.variables):
        lines.append(_format_bivariate_variable_block(quant_report.variables))

    return "\n".join(lines) + "\n"


def _format_cross_dataset_bivariate(cross_dataset_bivariate: dict) -> str:
    """Render simulation-based cross-dataset bivariate estimates as a markdown table."""
    # Check if any estimate has top_contrasts to decide on column
    has_patterns = any(
        est.get('top_contrasts') for est in cross_dataset_bivariate.values()
    )
    if has_patterns:
        lines = [
            "\n### Cross-Dataset Bivariate Estimates (Simulation-Based)\n",
            "| Variable Pair | Cramér's V | p-value | Key Pattern | n sim |",
            "|---------------|------------|---------|-------------|-------|",
        ]
    else:
        lines = [
            "\n### Cross-Dataset Bivariate Estimates (Simulation-Based)\n",
            "| Variable Pair | Cramér's V | p-value | Strength | n simulated |",
            "|---------------|------------|---------|----------|-------------|",
        ]
    for est in cross_dataset_bivariate.values():
        cv = est.get('cramers_v', 0)
        pv = est.get('p_value', 1)
        strength = _cramers_v_strength(cv)
        top_contrasts = est.get('top_contrasts')
        if has_patterns and top_contrasts:
            # Show the top contrast category's range
            top_cat = next(iter(top_contrasts))
            tc = top_contrasts[top_cat]
            pattern = (
                f"\"{top_cat}\": {tc['min_pct']*100:.0f}% "
                f"(\"{tc['min_when']}\") → {tc['max_pct']*100:.0f}% "
                f"(\"{tc['max_when']}\")"
            )
            lines.append(
                f"| {est.get('var_a')} × {est.get('var_b')} "
                f"| {cv:.3f} ({strength}) | {pv:.3f} "
                f"| {pattern} | {est.get('n_simulated')} |"
            )
        elif has_patterns:
            lines.append(
                f"| {est.get('var_a')} × {est.get('var_b')} "
                f"| {cv:.3f} ({strength}) | {pv:.3f} "
                f"| — | {est.get('n_simulated')} |"
            )
        else:
            lines.append(
                f"| {est.get('var_a')} × {est.get('var_b')} "
                f"| {cv:.3f} | {pv:.3f} | {strength} | {est.get('n_simulated')} |"
            )
    lines.append("\n*Estimates derived from SES-bridge regression simulation.*\n")

    # Conditional distribution sub-tables for each pair
    for pair_key, est in cross_dataset_bivariate.items():
        col_profiles = est.get('column_profiles')
        if not col_profiles:
            continue
        var_a = est.get('var_a', '?')
        var_b = est.get('var_b', '?')
        lines.append(
            f"\n**{var_a} × {var_b}** — "
            f"How {var_a} distributes given {var_b}:\n"
        )
        lines.append(f"| {var_b} (conditioning) | Top {var_a} responses |")
        lines.append("|---|---|")
        for cond_cat, profile in list(col_profiles.items())[:8]:
            top = sorted(profile.items(), key=lambda x: x[1], reverse=True)[:3]
            parts = [f"{cat}: {pct * 100:.0f}%" for cat, pct in top]
            lines.append(f"| {cond_cat} | {', '.join(parts)} |")

    return "\n".join(lines)


def _format_bridge_diagnostics(cross_dataset_bivariate: dict) -> str:
    """Render SES bridge model diagnostics as a markdown appendix.

    De-duplicates by variable: if var_a appears in multiple pairs it is shown
    once (first occurrence wins — model is fit on the same data each time so
    diagnostics are deterministic).

    Includes:
      - Summary table: one row per variable (pseudo-R², LLR p, dominant SES, quality)
      - Per-variable coefficient detail: top SES predictors by |t-stat|
      - Footer: mean R², overall dominant SES, warning if weak bridges present

    This section is appended AFTER the LLM has produced its essay so it never
    enters the prompt context.  It is purely for human inspection.
    """
    # Collect per-variable diagnostics, keyed by var_id, first-occurrence wins
    var_diags: dict = {}
    for est in cross_dataset_bivariate.values():
        for diag_key, var_key in (
            ('model_a_diagnostics', 'var_a'),
            ('model_b_diagnostics', 'var_b'),
        ):
            diag = est.get(diag_key)
            var_id = est.get(var_key)
            if diag and var_id and var_id not in var_diags:
                var_diags[var_id] = diag

    if not var_diags:
        return ""

    def _fmt(v) -> str:
        return f"{v:.3f}" if v == v else "n/a"   # NaN != NaN

    def _quality(r2, llr_p) -> str:
        if r2 != r2:           # NaN
            return "?"
        if r2 >= 0.05 and llr_p < 0.05:
            return "good"
        if r2 >= 0.02 and llr_p < 0.10:
            return "fair"
        return "weak"

    lines = [
        "\n### Bridge Model Diagnostics\n",
        "> For human inspection only — not passed to the LLM.\n",
        "#### Summary\n",
        "| Variable | Model | Pseudo-R² | LLR p | Dominant SES | Quality |",
        "|----------|-------|-----------|-------|--------------|---------|",
    ]

    r2_vals = []
    dominant_counts: dict = {}

    for var_id in sorted(var_diags):
        d = var_diags[var_id]
        r2    = d.get('pseudo_r2', float('nan'))
        llr_p = d.get('llr_pvalue', float('nan'))
        mtype = d.get('model_type', '?')
        dom   = d.get('dominant_ses_group') or '?'
        qual  = _quality(r2, llr_p)

        lines.append(
            f"| {var_id} | {mtype} | {_fmt(r2)} | {_fmt(llr_p)} | {dom} | {qual} |"
        )
        if r2 == r2:           # not NaN
            r2_vals.append(r2)
        dominant_counts[dom] = dominant_counts.get(dom, 0) + 1

    # Summary footer
    if r2_vals:
        mean_r2 = sum(r2_vals) / len(r2_vals)
        overall_dom = max(dominant_counts, key=dominant_counts.get)
        n_weak = sum(
            1 for d in var_diags.values()
            if _quality(d.get('pseudo_r2', float('nan')),
                        d.get('llr_pvalue', float('nan'))) == 'weak'
        )
        lines.append(
            f"\n**Mean pseudo-R²:** {mean_r2:.3f} &ensp;|&ensp; "
            f"**Overall dominant SES dimension:** {overall_dom}"
        )
        if n_weak:
            lines.append(
                f"\n> ⚠ {n_weak}/{len(var_diags)} bridge models are weak "
                f"(R²<0.02 or LLR p≥0.10). "
                f"Simulated Cramér's V for those variables may underestimate the true association."
            )

    # --- Per-variable coefficient breakdown ---
    lines.append("\n#### Per-Variable SES Predictor Detail\n")
    lines.append(
        "Top predictors by |t|-statistic — answers: which SES variable is doing the work?\n"
    )

    for var_id in sorted(var_diags):
        d = var_diags[var_id]
        r2         = d.get('pseudo_r2', float('nan'))
        llr_p      = d.get('llr_pvalue', float('nan'))
        mtype      = d.get('model_type', '?')
        coef_table = d.get('coef_table', [])
        qual       = _quality(r2, llr_p)

        lines.append(
            f"**{var_id}** ({mtype}, R²={_fmt(r2)}, LLR p={_fmt(llr_p)}, quality={qual})"
        )

        if coef_table:
            lines.append("| SES Predictor | Coef | Std Err | t-stat | p-value |")
            lines.append("|---------------|------|---------|--------|---------|")
            for row in coef_table[:6]:   # top 6 by |t|, covers all main SES groups
                feat  = row.get('feature', '?')
                coef  = row.get('coef', float('nan'))
                se    = row.get('std_err', float('nan'))
                tstat = row.get('t_stat', float('nan'))
                pval  = row.get('p_value', float('nan'))
                lines.append(
                    f"| {feat} | {_fmt(coef)} | {_fmt(se)} | {_fmt(tstat)} | {_fmt(pval)} |"
                )
        else:
            lines.append("*(coefficient table unavailable)*")
        lines.append("")   # blank line between variables

    lines.append(
        "*Pseudo-R² = McFadden's. "
        "Low values mean SES explains little variance in that variable — "
        "the bridge simulation still produces an estimate, but its precision is reduced.*\n"
    )
    return "\n".join(lines)


def _format_reasoning_section(reasoning_dict: Optional[dict]) -> str:
    """Render the reasoning outline block."""
    if not reasoning_dict or not reasoning_dict.get('evidence_hierarchy'):
        return ""
    lines = [
        "\n### Reasoning Outline\n",
        f"**Evidence Hierarchy:** {reasoning_dict['evidence_hierarchy']}",
    ]
    limitations = reasoning_dict.get('key_limitations', [])
    if limitations:
        lines.append("\n**Key Limitations:**")
        lines.extend(f"- {lim}" for lim in limitations)
    return "\n".join(lines) + "\n"


# =============================================================================
# REPORT FORMATTING
# =============================================================================

def format_analytical_essay_report(
    essay_dict: dict,
    user_query: str,
    quant_report: QuantitativeReport,
    metadata: dict,
    reasoning_dict: Optional[dict] = None,
) -> str:
    """
    Format the analytical essay and quantitative data into a readable markdown report.
    """
    report = f"""# Analytical Essay

**Query:** {user_query}

## Summary
{essay_dict.get('summary', 'No summary available.')}

## Data Landscape
{essay_dict.get('data_landscape', 'No data landscape available.')}

## Evidence
{essay_dict.get('evidence', 'No evidence section available.')}

## Complications
{essay_dict.get('complications', 'No complications section available.')}

## Implications
{essay_dict.get('implications', 'No implications available.')}

---

## Quantitative Appendix

| Metric | Value |
|--------|-------|
| Variables Analyzed | {metadata.get('variable_count', 'N/A')} |
| Divergence Index | {metadata.get('divergence_index', 0):.1%} |
| Consensus Variables | {metadata.get('shape_counts', {}).get('consensus', 0)} |
| Lean Variables | {metadata.get('shape_counts', {}).get('lean', 0)} |
| Polarized Variables | {metadata.get('shape_counts', {}).get('polarized', 0)} |
| Dispersed Variables | {metadata.get('shape_counts', {}).get('dispersed', 0)} |
"""

    report += _format_variable_details(quant_report)
    fault_lines = quant_report.demographic_fault_lines if quant_report else None
    if fault_lines:
        report += _format_demographic_fault_lines(fault_lines, quant_report)
    cross_biv = quant_report.cross_dataset_bivariate if quant_report else None
    if cross_biv:
        report += _format_cross_dataset_bivariate(cross_biv)
        report += _format_bridge_diagnostics(cross_biv)
    report += _format_reasoning_section(reasoning_dict)

    polarized = metadata.get('polarized_variables', [])
    dispersed = metadata.get('dispersed_variables', [])
    report += f"""
### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** {', '.join(polarized) or 'None'}
- **Dispersed Variables:** {', '.join(dispersed) or 'None'}
"""

    return report
