"""
Analytical Essay Generator for Navegador

Receives a structured quantitative report from the quantitative engine and
produces a dialectical analytical essay via LLM calls.

Pipeline:
1. Quantitative engine: compute statistics per variable (pure computation)
2. Relevance gate: filter variables by query relevance (ChromaDB + expert grading)
3. Reasoning outline: LLM maps variables to query, builds argument structure
4. Essay generation: LLM produces dialectical essay grounded in data + reasoning

The essay structure enforces nuance:
- Summary: finding + caveat
- Introduction: scope and framing
- Prevailing view: consensus evidence
- Counterargument: divergence evidence (must be >= prevailing view in length)
- Implications: >=2 alternative interpretations
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
    argument_structure: str = Field(
        description="2-3 sentences: what logical argument connects these "
                    "variables to answer the query? What is the analytical chain?"
    )
    key_tensions: List[str] = Field(
        description="List of 2-4 main analytical tensions or contradictions "
                    "in the data that are relevant to answering the query"
    )


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
7. If the data shows polarization, say so directly; do not soften it.
8. Only discuss data points that are LOGICALLY CONNECTED to the query. Follow the REASONING OUTLINE to maintain analytical coherence."""


REASONING_SYSTEM_PROMPT = """You are an expert survey research methodologist.
You are fully bilingual in English and Spanish.
Your task is to evaluate how survey variables relate to a research question
and build a logical argument structure BEFORE writing the essay.

Be rigorous: if a variable does not logically connect to the query,
say so explicitly. Do not force connections that don't exist."""


def create_reasoning_prompt(
    user_query: str,
    quantitative_report_text: str,
    format_instructions: str,
) -> str:
    """
    Build the prompt for the intermediate reasoning step.

    This step maps each variable to the query and builds the logical
    argument structure BEFORE essay generation.
    """
    return f"""QUERY: {user_query}

QUANTITATIVE REPORT:
{quantitative_report_text}

YOUR TASK:
Before writing an analytical essay, you must first reason about how each variable
in the quantitative report relates to the QUERY. This reasoning will guide the essay.

For each variable:
1. Read its question text and distribution
2. Explain specifically HOW it addresses the QUERY (not just that it's "related")
3. If a variable has a weak or tangential connection to the QUERY, say so explicitly

Then identify the logical argument structure:
- What chain of reasoning connects these data points to answer the QUERY?
- What are the key tensions or contradictions in the data?

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

    Includes the reasoning outline to ground the essay in logical structure.
    """
    return f"""QUERY: {user_query}

QUANTITATIVE REPORT:
{quantitative_report_text}

REASONING OUTLINE (follow this logical structure):
{reasoning_text}

YOUR TASK:
Write a structured analytical essay based EXCLUSIVELY on the quantitative report above.
The essay must address the QUERY using the evidence in the report.
Follow the REASONING OUTLINE to ensure every data point you discuss is logically
connected to the query. Do NOT discuss data points that the reasoning identified
as tangential or weakly connected.

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
    2. Building the argument structure before writing
    3. Identifying key tensions in the data

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
            'argument_structure': 'Reasoning step failed — proceed with direct analysis.',
            'key_tensions': [],
        }

    try:
        cleaned = clean_llm_json_output(response)
        reasoning = reasoning_parser.parse(cleaned)
        result = reasoning.model_dump()
        print(f"[analytical_essay] Reasoning: {len(result.get('variable_relevance', {}))} variables mapped, "
              f"{len(result.get('key_tensions', []))} tensions identified")
        return result
    except Exception as e:
        print(f"[analytical_essay] Reasoning parse error (non-fatal): {e}")
        return {
            'variable_relevance': {},
            'argument_structure': 'Reasoning step failed — proceed with direct analysis.',
            'key_tensions': [],
        }


def format_reasoning_for_essay(reasoning_dict: dict) -> str:
    """Format the reasoning outline as text for inclusion in the essay prompt."""
    parts = []

    var_rel = reasoning_dict.get('variable_relevance', {})
    if var_rel:
        parts.append("VARIABLE-QUERY MAPPING:")
        for var_id, explanation in var_rel.items():
            parts.append(f"  - {var_id}: {explanation}")

    arg = reasoning_dict.get('argument_structure', '')
    if arg:
        parts.append(f"\nARGUMENT STRUCTURE: {arg}")

    tensions = reasoning_dict.get('key_tensions', [])
    if tensions:
        parts.append("\nKEY TENSIONS:")
        for i, t in enumerate(tensions, 1):
            parts.append(f"  {i}. {t}")

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
    2. Generate reasoning outline (maps variables to query, builds argument)
    3. Generate essay grounded in reasoning

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
        # Phase 1: Quantitative engine
        # (auto-correction constrained to same survey code)
        print("[analytical_essay] Building quantitative report...")
        quant_report = build_quantitative_report(
            selected_variables,
            user_query=user_query,
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
    reasoning_dict: Optional[dict] = None,
) -> str:
    """
    Format the analytical essay and quantitative data into a readable markdown report.
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

    # Reasoning outline (if available)
    if reasoning_dict and reasoning_dict.get('argument_structure'):
        report += "\n### Reasoning Outline\n"
        report += f"**Argument Structure:** {reasoning_dict['argument_structure']}\n"
        if reasoning_dict.get('key_tensions'):
            report += "\n**Key Tensions:**\n"
            for t in reasoning_dict['key_tensions']:
                report += f"- {t}\n"

    polarized = metadata.get('polarized_variables', [])
    dispersed = metadata.get('dispersed_variables', [])
    report += f"""
### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** {', '.join(polarized) or 'None'}
- **Dispersed Variables:** {', '.join(dispersed) or 'None'}
"""

    return report
