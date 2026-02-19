"""
Analytical Essay Generator v2 — Thematic Architecture

Diagnosis of v1 problems:
- The quantitative report primes the LLM with distribution taxonomy (lean/polarized/dispersed)
  BEFORE it reasons about content, so the essay organizes around distribution shapes, not topics.
- The COUNTERARGUMENT section is structurally defined as "minority opinions + dispersed variables",
  so it fills mechanically with percentage lists even when there is no genuine counter-narrative.

V2 design principles:
- Keep the quantitative engine (stage 3): HHI, shape, minority opinions are analytically sound.
- Suppress shape labels in the LLM-facing report: the LLM sees percentages and margins,
  not taxonomy labels. Shape data is available to the reasoning step but not lead-positioned.
- Replace reasoning outline with THEMATIC SYNTHESIS: the LLM groups variables into 3-4 named
  content themes BEFORE writing. Themes organize around what the variables are about, not how
  their distributions look.
- Replace essay structure with THEMATIC ESSAY: overview → [Theme 1] → [Theme 2] → [Theme 3]
  → synthesis. Each theme is a substantive analytical paragraph that cites data as evidence.
  Statistical polarization/dispersion is mentioned only when it substantively matters.
- No mechanical length rules: essay quality comes from argument depth, not section symmetry.

Pipeline:
1. build_quantitative_report()        — pure computation (unchanged from v1)
2. format_for_thematic_llm()          — suppresses shape labels from per-variable blocks
3. fetch_variable_implications()      — retrieves ChromaDB implications for enriched context
4. generate_thematic_synthesis()      — LLM step 1: content themes + overall argument
5. generate_thematic_essay()          — LLM step 2: structured thematic essay
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

class ThemeCluster(BaseModel):
    """One substantive theme grouping several variables."""
    title: str = Field(description="Short descriptive title for this theme (the subject matter, not a statistical label)")
    variable_ids: List[str] = Field(description="List of variable IDs that belong to this theme")
    finding: str = Field(
        description="1-2 sentences: what do these variables together reveal about the query? "
                    "State the substantive conclusion, not the distribution pattern."
    )
    nuance: str = Field(
        description="1 sentence: the most important qualification, tension, or caveat for this theme. "
                    "Only mention polarization or dispersion if it changes the interpretation."
    )


class ThematicSynthesis(BaseModel):
    """Intermediate thematic outline before essay generation."""
    themes: List[ThemeCluster] = Field(
        description="3 to 4 substantive content themes that organize the variables to answer the query"
    )
    overall_argument: str = Field(
        description="2-3 sentences: what does the data as a whole say about the query? "
                    "State the main finding and its most important complication."
    )
    variables_to_flag: List[str] = Field(
        description="Variable IDs where the level of disagreement or dispersion is substantively "
                    "important enough that it should be explicitly discussed in the essay. "
                    "Leave empty if distribution patterns don't change the substantive interpretation."
    )


class ThematicEssay(BaseModel):
    """Structured output for the thematic analytical essay."""
    overview: str = Field(
        description="2-3 sentences: main finding and how the thematic sections fit together. "
                    "State what the data reveals, not what the survey covers."
    )
    theme_sections: List[Dict[str, str]] = Field(
        description="List of dicts, each with 'title' (str) and 'text' (str). "
                    "3-4 thematic sections. Each 'text' is a substantive analytical paragraph "
                    "that cites exact percentages and variable IDs as evidence."
    )
    synthesis: str = Field(
        description="1-2 paragraphs: what the themes together reveal about the query. "
                    "Include implications: what would a policymaker or researcher do with these findings? "
                    "Discuss tensions in the data only where they affect interpretation."
    )


# =============================================================================
# PROMPTS
# =============================================================================

THEMATIC_SYSTEM_PROMPT = """You are an expert analyst writing for an audience of social scientists and policy makers.
You are fully bilingual in English and Spanish. You write your essay in the same language as the QUERY.
You produce thematic analytical essays grounded in survey data.

ABSOLUTE RULES:
1. Every percentage you cite MUST appear in the QUANTITATIVE REPORT. Do NOT invent, round differently, or extrapolate numbers.
2. Organize your essay around CONTENT THEMES — what the data is about — not around statistical distribution types.
3. Cite percentages as evidence for substantive claims. The claim comes first; the data supports it.
4. Mention polarization or fragmentation only when it is SUBSTANTIVELY IMPORTANT — when the level of disagreement changes what a reader or policymaker should conclude. Do not mention it to pad a section.
5. Each thematic section must make an argument. Not: "X% said A and Y% said B." Instead: "Mexicans broadly support X, as shown by N% agreeing that..."
6. The essay should read as a coherent argument from overview to synthesis, not as a sequential report of variables."""


SYNTHESIS_SYSTEM_PROMPT = """You are an expert survey research methodologist.
You are fully bilingual in English and Spanish.
Your task is to read quantitative survey data and organize it into substantive content themes
that answer a research question.

Be rigorous: organize by CONTENT (what the variables are about), not by statistical pattern.
A "lean" distribution and a "dispersed" distribution about the same topic belong in the same theme."""


def create_synthesis_prompt(
    user_query: str,
    quant_text: str,
    implications_text: str,
    format_instructions: str,
) -> str:
    """
    Build the thematic synthesis prompt.

    The LLM sees the full quantitative data plus ChromaDB expert implications,
    and must group variables into content themes before any essay is written.
    """
    impl_section = f"\nEXPERT CONTEXT (domain implications per variable):\n{implications_text}\n" if implications_text else ""

    return f"""QUERY: {user_query}

QUANTITATIVE REPORT:
{quant_text}
{impl_section}
YOUR TASK:
Before writing an essay, organize the survey variables into 3-4 content themes that together answer the QUERY.

INSTRUCTIONS:
1. Group variables by what they are ABOUT, not by how their distributions look.
   - Variables about the same substantive topic belong in the same theme even if one is "lean" and another "dispersed".
2. For each theme, identify what the data REVEALS (a finding), and the most important qualification.
3. Only flag a variable in "variables_to_flag" if its level of disagreement or dispersion is large enough
   that a reader would draw a different conclusion without knowing about it.
4. In "overall_argument", state the main substantive answer to the query in 2-3 sentences.

{format_instructions}

IMPORTANT: Return valid JSON only. No markdown, no code blocks, no extra text."""


def create_essay_prompt(
    user_query: str,
    quant_text: str,
    synthesis: ThematicSynthesis,
    format_instructions: str,
) -> str:
    """
    Build the essay prompt using the thematic synthesis as organizing structure.
    """
    # Serialize synthesis for the prompt
    themes_text = ""
    for i, t in enumerate(synthesis.themes, 1):
        themes_text += f"\nTheme {i}: {t.title}\n"
        themes_text += f"  Variables: {', '.join(t.variable_ids)}\n"
        themes_text += f"  Finding: {t.finding}\n"
        themes_text += f"  Nuance: {t.nuance}\n"

    flagged = ", ".join(synthesis.variables_to_flag) if synthesis.variables_to_flag else "None"

    return f"""QUERY: {user_query}

QUANTITATIVE REPORT:
{quant_text}

THEMATIC OUTLINE (follow this structure):
Overall argument: {synthesis.overall_argument}

Themes:
{themes_text}
Variables where disagreement level is substantively important: {flagged}

YOUR TASK:
Write a structured analytical essay that answers the QUERY using the evidence in the quantitative report.
Follow the thematic outline above — each theme becomes one section of the essay.

STRUCTURE:

1. "overview": 2-3 sentences. State the main substantive finding and how the sections fit together.
   Do NOT describe the dataset or number of variables. Start with what the data reveals.

2. "theme_sections": A list of 3-4 dicts, each with "title" (str) and "text" (str).
   Each section corresponds to one theme from the outline.
   Each "text" must:
   - Open with a clear analytical claim about the theme (not "X% said...")
   - Use specific percentages and variable IDs as evidence (e.g., "75.6% of respondents, p41|MED")
   - Discuss the flagged variables' disagreement level if they appear in this theme — but only
     because it changes what the finding means, not to fulfill a structural requirement
   - Be 2-4 sentences of substantive analysis

3. "synthesis": 1-2 paragraphs. Pull the themes together to answer the query.
   What does the combined evidence mean for researchers or policymakers?
   What is the most important tension or limitation in the data?
   Do not repeat individual percentages already cited in the theme sections.

{format_instructions}

IMPORTANT: Return valid JSON only. No markdown, no code blocks, no extra text."""


# =============================================================================
# CHROMADB IMPLICATIONS RETRIEVAL
# =============================================================================

def fetch_variable_implications(variable_ids: List[str]) -> str:
    """
    Fetch pre-generated expert implications from ChromaDB for each variable.

    These are richer than the raw quant stats — they contain domain expert
    analysis of what the variable results mean. Used to enrich the thematic
    synthesis step (not the essay step, which works from quant data only).

    Returns a formatted string of implications, or empty string if unavailable.
    """
    try:
        from utility_functions import environment_setup, embedding_fun_openai
        _, db_f1 = environment_setup(embedding_fun_openai)

        impl_ids = [f"{vid}__implications" for vid in variable_ids]
        result = db_f1.get(ids=impl_ids)

        if not result or not result.get('ids'):
            return ""

        parts = []
        for doc_id, doc in zip(result['ids'], result['documents']):
            if doc:
                var_id = doc_id.replace('__implications', '')
                parts.append(f"[{var_id}] {doc}")

        return "\n\n".join(parts)
    except Exception as e:
        print(f"[essay_v2] Could not fetch implications (non-fatal): {e}")
        return ""


# =============================================================================
# THEMATIC SYNTHESIS
# =============================================================================

synthesis_parser = PydanticOutputParser(pydantic_object=ThematicSynthesis)
synthesis_format_instructions = synthesis_parser.get_format_instructions()

essay_parser = PydanticOutputParser(pydantic_object=ThematicEssay)
essay_format_instructions = essay_parser.get_format_instructions()


def generate_thematic_synthesis(
    user_query: str,
    quant_text: str,
    implications_text: str,
    model_name: str = 'gpt-4.1-mini-2025-04-14',
    temperature: float = 0.2,
) -> ThematicSynthesis:
    """
    Generate thematic clustering of variables before essay writing.

    Unlike v1 reasoning (variable → query mapping), this step groups
    variables by substantive content and identifies what each group reveals.
    """
    print("[essay_v2] Generating thematic synthesis...")

    prompt = create_synthesis_prompt(
        user_query, quant_text, implications_text, synthesis_format_instructions
    )

    response = get_answer(
        prompt=prompt,
        system_prompt=SYNTHESIS_SYSTEM_PROMPT,
        model=model_name,
        temperature=temperature,
    )

    if response is None:
        # Fallback: single theme with all variables
        return ThematicSynthesis(
            themes=[ThemeCluster(
                title="Survey findings",
                variable_ids=[],
                finding="Thematic synthesis unavailable.",
                nuance="",
            )],
            overall_argument="Synthesis step failed — proceeding with direct analysis.",
            variables_to_flag=[],
        )

    try:
        cleaned = clean_llm_json_output(response)
        result = synthesis_parser.parse(cleaned)
        n_themes = len(result.themes)
        flagged = len(result.variables_to_flag)
        print(f"[essay_v2] Synthesis: {n_themes} themes, {flagged} variables flagged for disagreement")
        return result
    except Exception as e:
        print(f"[essay_v2] Synthesis parse error (non-fatal): {e}")
        return ThematicSynthesis(
            themes=[ThemeCluster(
                title="Survey findings",
                variable_ids=[],
                finding="Parse failed — proceeding with direct analysis.",
                nuance="",
            )],
            overall_argument="Synthesis step failed.",
            variables_to_flag=[],
        )


# =============================================================================
# ESSAY GENERATION
# =============================================================================

def generate_thematic_essay(
    selected_variables: List[str],
    user_query: str,
    model_name: str = 'gpt-4.1-mini-2025-04-14',
    temperature: float = 0.4,
) -> dict:
    """
    Main entry point for v2 pipeline:
    quant report → implications → thematic synthesis → thematic essay.

    Returns:
        dict with keys: success, essay, quantitative_report,
        formatted_report, report_sections, synthesis
    """
    print(f"[essay_v2] Starting for query: {user_query}")

    try:
        # Stage 3: Quantitative engine (unchanged)
        print("[essay_v2] Building quantitative report...")
        quant_report = build_quantitative_report(
            selected_variables,
            user_query=user_query,
        )

        if quant_report.variable_count == 0:
            return _error_result(user_query, selected_variables,
                                 "No valid variables found.")

        quant_text = format_quantitative_report_for_llm(quant_report)
        print(f"[essay_v2] Quant report: {quant_report.variable_count} variables, "
              f"divergence: {quant_report.divergence_index:.0%}")

        # Stage 3b: Fetch ChromaDB implications for synthesis enrichment
        implications_text = fetch_variable_implications(
            [v.var_id for v in quant_report.variables]
        )

        # Stage 4: Thematic synthesis
        synthesis = generate_thematic_synthesis(
            user_query, quant_text, implications_text, model_name, temperature=0.2
        )

        # Stage 5: Essay generation
        print("[essay_v2] Generating thematic essay...")
        prompt = create_essay_prompt(
            user_query, quant_text, synthesis, essay_format_instructions
        )

        response = get_answer(
            prompt=prompt,
            system_prompt=THEMATIC_SYSTEM_PROMPT,
            model=model_name,
            temperature=temperature,
        )

        if response is None:
            return _error_result(user_query, selected_variables, "No response from LLM")

        cleaned = clean_llm_json_output(response)
        essay = essay_parser.parse(cleaned)
        essay_dict = essay.model_dump()

        # Metadata
        metadata = {
            'variable_count': quant_report.variable_count,
            'shape_counts': quant_report.shape_summary,
            'divergence_index': quant_report.divergence_index,
            'n_themes': len(synthesis.themes),
            'flagged_variables': synthesis.variables_to_flag,
            'polarized_variables': [v.var_id for v in quant_report.variables if v.shape == 'polarized'],
            'dispersed_variables': [v.var_id for v in quant_report.variables if v.shape == 'dispersed'],
        }

        formatted = format_thematic_essay_report(essay_dict, user_query, quant_report, metadata, synthesis)

        # Flatten theme_sections for report_sections compatibility
        theme_texts = {t['title']: t['text'] for t in essay_dict.get('theme_sections', [])}

        return {
            'query': user_query,
            'selected_variables': selected_variables,
            'analysis_type': 'thematic_essay',
            'success': True,
            'essay': essay_dict,
            'synthesis': synthesis.model_dump(),
            'quantitative_report': quant_report.model_dump(),
            'formatted_report': formatted,
            'report_sections': {
                'query_answer': essay_dict.get('overview', ''),
                'topic_summary': essay_dict.get('synthesis', ''),
                'topic_summaries': theme_texts,
                'expert_replies': [],
            },
            'metadata': metadata,
        }

    except Exception as e:
        print(f"[essay_v2] Error: {e}")
        traceback.print_exc()
        return _error_result(user_query, selected_variables, str(e))


def _error_result(user_query: str, selected_variables: list, error_msg: str) -> dict:
    return {
        'query': user_query,
        'selected_variables': selected_variables,
        'analysis_type': 'thematic_essay',
        'success': False,
        'error': error_msg,
        'formatted_report': f'Error generating thematic essay: {error_msg}',
        'report_sections': {
            'query_answer': f'Error: {error_msg}',
            'topic_summary': '',
            'topic_summaries': {},
            'expert_replies': [],
        },
    }


# =============================================================================
# REPORT FORMATTING
# =============================================================================

def format_thematic_essay_report(
    essay_dict: dict,
    user_query: str,
    quant_report: QuantitativeReport,
    metadata: dict,
    synthesis: Optional[ThematicSynthesis] = None,
) -> str:
    """Format the thematic essay as markdown."""

    report = f"""# Analytical Essay (v2 — Thematic)

**Query:** {user_query}

## Overview
{essay_dict.get('overview', '')}

"""

    # Theme sections
    for section in essay_dict.get('theme_sections', []):
        title = section.get('title', 'Theme')
        text = section.get('text', '')
        report += f"## {title}\n{text}\n\n"

    # Synthesis
    report += f"## Synthesis\n{essay_dict.get('synthesis', '')}\n"

    # Quantitative appendix
    report += f"""
---

## Quantitative Appendix

| Metric | Value |
|--------|-------|
| Variables Analyzed | {metadata.get('variable_count', 'N/A')} |
| Themes Identified | {metadata.get('n_themes', 'N/A')} |
| Divergence Index | {metadata.get('divergence_index', 0):.1%} |
| Consensus Variables | {metadata.get('shape_counts', {}).get('consensus', 0)} |
| Lean Variables | {metadata.get('shape_counts', {}).get('lean', 0)} |
| Polarized Variables | {metadata.get('shape_counts', {}).get('polarized', 0)} |
| Dispersed Variables | {metadata.get('shape_counts', {}).get('dispersed', 0)} |
| Flagged for disagreement | {', '.join(metadata.get('flagged_variables', [])) or 'None'} |
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

    # Thematic synthesis summary
    if synthesis:
        report += "\n### Thematic Outline\n"
        report += f"**Overall argument:** {synthesis.overall_argument}\n\n"
        for t in synthesis.themes:
            report += f"**{t.title}** — {', '.join(t.variable_ids)}\n"
            report += f"  Finding: {t.finding}\n"
            if t.nuance:
                report += f"  Nuance: {t.nuance}\n"

    report += f"""
### Analysis Metadata
- **Analysis Type:** Thematic Essay v2
- **Flagged Variables:** {', '.join(metadata.get('flagged_variables', [])) or 'None'}
- **Polarized Variables:** {', '.join(metadata.get('polarized_variables', [])) or 'None'}
- **Dispersed Variables:** {', '.join(metadata.get('dispersed_variables', [])) or 'None'}
"""

    return report
