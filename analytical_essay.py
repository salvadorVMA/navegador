"""
Analytical Essay Generator for Navegador

Receives a structured quantitative report from the quantitative engine and
produces a dialectical analytical essay via a single LLM call.

The essay structure enforces nuance:
- Summary: finding + caveat
- Introduction: scope and framing
- Prevailing view: consensus evidence
- Counterargument: divergence evidence (must be >= prevailing view in length)
- Implications: >=2 alternative interpretations

No ChromaDB, no implications retrieval. The LLM interprets quantitative
results directly.
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
# PYDANTIC OUTPUT MODEL
# =============================================================================

class AnalyticalEssay(BaseModel):
    """Structured output for the dialectical analytical essay."""
    summary: str = Field(
        description="2-3 sentences: main finding plus key caveat or counterpoint"
    )
    introduction: str = Field(
        description="One paragraph: scope of the data, variables analyzed, and framing"
    )
    prevailing_view: str = Field(
        description="Evidence-grounded paragraph(s) presenting the dominant patterns "
                    "with exact percentages from the quantitative report"
    )
    counterargument: str = Field(
        description="Paragraph(s) of equal or greater length than prevailing_view, "
                    "presenting divergence, polarization, and minority opinions"
    )
    implications: str = Field(
        description="At least 2 alternative interpretations or decisions "
                    "that follow from the tension between prevailing view and counterargument"
    )


# =============================================================================
# PROMPTS
# =============================================================================

ESSAY_SYSTEM_PROMPT = """You are an expert analyst writing for an audience of social scientists and policy makers.
You are fully bilingual in English and Spanish. You write your essay in the same language as the QUERY.
You produce evidence-driven analytical essays with a dialectical structure that foregrounds divergence and nuance.

ABSOLUTE RULES:
1. Every percentage you cite MUST appear in the QUANTITATIVE REPORT below. Do NOT invent, round differently, or extrapolate numbers.
2. The COUNTERARGUMENT section must be AT LEAST as long as the PREVAILING VIEW section. If they are unequal, the counterargument must be longer.
3. Variables classified as "polarized" or "dispersed" must receive MORE attention than "consensus" variables.
4. Any minority opinion (>15%) mentioned in the quantitative report must be explicitly discussed; it must NEVER be dismissed or minimized.
5. The IMPLICATIONS section must contain at least 2 genuinely different interpretations or policy directions — not restatements of the same idea.
6. Do NOT use the word "overall" to paper over genuine disagreement in the data.
7. If the data shows polarization, say so directly; do not soften it."""


def create_essay_prompt(
    user_query: str,
    quantitative_report_text: str,
    format_instructions: str
) -> str:
    """
    Build the full prompt for the analytical essay LLM call.

    Args:
        user_query: The user's original query
        quantitative_report_text: Formatted quantitative report string
        format_instructions: Pydantic parser format instructions

    Returns:
        Complete prompt string
    """
    return f"""QUERY: {user_query}

QUANTITATIVE REPORT:
{quantitative_report_text}

YOUR TASK:
Write a structured analytical essay based EXCLUSIVELY on the quantitative report above.
The essay must address the QUERY using the evidence in the report.

STRUCTURE (each key must be a non-empty string):

1. "summary": 2-3 sentences. State the single most important finding, then immediately state the most significant caveat or counterpoint. This is the executive summary.

2. "introduction": One paragraph. Describe the scope: how many variables were analyzed, which surveys they come from, and what the distribution shapes tell us about the level of consensus vs. fragmentation in public opinion. Set up the dialectical tension.

3. "prevailing_view": Present the dominant patterns across the variables. Which responses command pluralities or majorities? Cite exact percentages and variable IDs (e.g., "38.3% chose Orgullo (p5_1|IDE)"). Group consensus and lean variables together. Build the case for what "most people" think.

4. "counterargument": THIS SECTION MUST BE AT LEAST AS LONG AS prevailing_view. Present ALL evidence of divergence:
   - Polarized variables where opinion is split
   - Dispersed variables where no single view dominates
   - Minority opinions (>15%) that represent significant dissent
   - The MARGIN between first and second place when it is small (< 15 percentage points)
   Treat each of these seriously. Explain WHY the disagreement matters. Do not use hedging language.

5. "implications": At least 2 distinct implications or alternative interpretations. These should be genuinely different directions, not variations of the same point. Consider: What would a policymaker emphasizing the prevailing view decide? What would one emphasizing the counterargument decide? How does the level of polarization affect the reliability of simple majority readings?

{format_instructions}

IMPORTANT: Return valid JSON only. No markdown formatting, no code blocks, no extra text."""


# =============================================================================
# ESSAY GENERATION
# =============================================================================

# Initialize parser
essay_parser = PydanticOutputParser(pydantic_object=AnalyticalEssay)
essay_format_instructions = essay_parser.get_format_instructions()


def generate_analytical_essay(
    selected_variables: List[str],
    user_query: str,
    model_name: str = 'gpt-4.1-mini-2025-04-14',
    temperature: float = 0.4,
) -> dict:
    """
    Main entry point: build quantitative report, then generate essay.

    Args:
        selected_variables: List of variable IDs
        user_query: The user's original query
        model_name: LLM model to use
        temperature: LLM temperature (lower for factual accuracy)

    Returns:
        dict with keys: success, essay, quantitative_report,
        formatted_report, report_sections
    """
    print(f"[analytical_essay] Starting for query: {user_query}")
    print(f"[analytical_essay] Variables: {selected_variables}")

    try:
        # Phase 1: Quantitative engine (pure computation, no LLM)
        print("[analytical_essay] Building quantitative report...")
        quant_report = build_quantitative_report(selected_variables)

        if quant_report.variable_count == 0:
            return _error_result(
                user_query, selected_variables,
                "No valid variables found in df_tables for the selected variable IDs."
            )

        quant_text = format_quantitative_report_for_llm(quant_report)
        print(f"[analytical_essay] Quantitative report: {quant_report.variable_count} variables, "
              f"divergence index: {quant_report.divergence_index:.1%}")

        # Phase 2: LLM essay generation (single call)
        print("[analytical_essay] Generating essay...")
        prompt = create_essay_prompt(user_query, quant_text, essay_format_instructions)

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
        formatted = format_analytical_essay_report(essay_dict, user_query, quant_report, metadata)

        return {
            'query': user_query,
            'selected_variables': selected_variables,
            'analysis_type': 'analytical_essay',
            'success': True,
            'essay': essay_dict,
            'quantitative_report': quant_report.model_dump(),
            'formatted_report': formatted,
            'report_sections': {
                'query_answer': essay_dict.get('summary', ''),
                'topic_summary': essay_dict.get('introduction', ''),
                'prevailing_view': essay_dict.get('prevailing_view', ''),
                'counterargument': essay_dict.get('counterargument', ''),
                'implications': essay_dict.get('implications', ''),
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
            'prevailing_view': '',
            'counterargument': '',
            'implications': '',
        },
    }


# =============================================================================
# REPORT FORMATTING
# =============================================================================

def format_analytical_essay_report(
    essay_dict: dict,
    user_query: str,
    quant_report: QuantitativeReport,
    metadata: dict,
) -> str:
    """
    Format the analytical essay and quantitative data into a readable markdown report.

    Args:
        essay_dict: The parsed essay dictionary
        user_query: Original user query
        quant_report: The quantitative report model
        metadata: Analysis metadata dict

    Returns:
        Formatted markdown string
    """
    report = f"""# Analytical Essay

**Query:** {user_query}

## Summary
{essay_dict.get('summary', 'No summary available.')}

## Introduction
{essay_dict.get('introduction', 'No introduction available.')}

## Prevailing View
{essay_dict.get('prevailing_view', 'No prevailing view available.')}

## Counterargument
{essay_dict.get('counterargument', 'No counterargument available.')}

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

    # Per-variable detail
    if quant_report and quant_report.variables:
        report += "\n### Variable Details\n"
        for v in quant_report.variables:
            report += f"\n**{v.var_id}** ({v.shape})\n"
            report += f"- Question: {v.question_text[:150]}\n"
            report += f"- Mode: {v.modal_response} ({v.modal_percentage:.1f}%)\n"
            report += f"- Runner-up: {v.runner_up_response} ({v.runner_up_percentage:.1f}%), margin: {v.margin:.1f}pp\n"
            report += f"- HHI: {v.hhi:.0f}\n"
            if v.minority_opinions:
                minorities = ", ".join(
                    f"{label} ({pct:.1f}%)" for label, pct in v.minority_opinions.items()
                )
                report += f"- Minority opinions: {minorities}\n"

    polarized = metadata.get('polarized_variables', [])
    dispersed = metadata.get('dispersed_variables', [])
    report += f"""
### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** {', '.join(polarized) or 'None'}
- **Dispersed Variables:** {', '.join(dispersed) or 'None'}
"""

    return report
