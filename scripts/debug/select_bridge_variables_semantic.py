"""
select_bridge_variables_semantic.py — Semantic variable selection for bridge sweep.

Replaces naive max-entropy selection with a 5-step LLM pipeline:

  Step 0: Summarize all questions per domain + semantic dedup (claude-haiku)
  Step 1: Propose n≥5 construct clusters of questions + minimal descriptions (claude-sonnet)
  Step 2: Research review per construct: sources, causal roles, data availability (claude-opus)
  Step 3: Variable strategy per construct: aggregate vs single, with justification (claude-sonnet)
  Step 4: Build variables — create aggregated columns or select singles (local)

All intermediate outputs saved to data/results/.semantic_selection_cache/{DOMAIN}_step{N}_*.json
for human review.

Usage:
    python scripts/debug/select_bridge_variables_semantic.py
    python scripts/debug/select_bridge_variables_semantic.py --domains REL COR --workers 1
    python scripts/debug/select_bridge_variables_semantic.py \\
        --n-constructs 5 --k-final 5 --workers 4
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

OUTPUT_PATH = ROOT / "data" / "results" / "semantic_variable_selection.json"
CACHE_DIR = ROOT / "data" / "results" / ".semantic_selection_cache"

EXCLUDE_DOMAINS = {"JUE", "CON"}
MAX_ORDINAL_CATEGORIES = 15
DEDUPE_PREFIX_LEN = 40


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ConstructCluster:
    """Step 1 output: a cluster of questions measuring one construct."""
    name: str
    description: str              # minimal — just enough for research review
    question_cluster: List[str]   # qids in this cluster
    requires_aggregation: bool    # True if multiple questions needed to measure it


@dataclass
class ResearchReview:
    """Step 2 output: academic validation of a construct."""
    construct_name: str
    sources: List[Dict]           # [{citation, relevance, key_finding}]
    causal_relationships: List[Dict]  # [{role, related_construct, measurable_in_data, data_source}]
    gap_justification: Optional[str]  # detailed justification if no/few sources
    importance_rating: int        # 1-5 how important for cross-domain analysis


@dataclass
class VariableStrategy:
    """Step 3 output: how to operationalize a construct for the bridge."""
    construct_name: str
    strategy: str                 # 'aggregate' | 'single_max_entropy' | 'single_best_match'
    selected_qids: List[str]      # qids used (1 for single, multiple for aggregate)
    aggregation_method: Optional[str]  # 'sum_score' | 'mean_score' | 'pca_first_component' | null
    justification: str
    bridge_column: str            # final column name for the sweep


@dataclass
class DomainSelection:
    """Complete selection output for one domain."""
    domain: str
    survey_title: str
    construct_clusters: List[ConstructCluster]
    research_reviews: List[ResearchReview]
    variable_strategies: List[VariableStrategy]
    selected_variables: List[str]  # final bridge columns
    fallback_used: bool = False


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

def _call_claude(
    prompt: str,
    model: str,
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> str:
    """Call Anthropic API and return text content."""
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _parse_json_response(text: str) -> Any:
    """Extract JSON from a response that may wrap it in a code fence."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text, re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    for pattern in (r"(\[[\s\S]+\])", r"(\{[\s\S]+\})"):
        m = re.search(pattern, text)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    raise ValueError(f"Could not parse JSON from response:\n{text[:500]}")


def _save_cache(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _load_cache(path: Path) -> Any:
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Variable eligibility + pre-filter
# ---------------------------------------------------------------------------

def _eligible_qids(domain: str, df: pd.DataFrame, all_qids: List[str]) -> List[str]:
    eligible = []
    for qid in all_qids:
        col = qid.split("|")[0]
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty or series.nunique() > MAX_ORDINAL_CATEGORIES:
            continue
        eligible.append(qid)
    return eligible


def _fast_dedupe(
    qids: List[str], pregs_dict: dict, df: pd.DataFrame,
    prefix_len: int = DEDUPE_PREFIX_LEN,
) -> List[str]:
    groups: Dict[str, str] = {}
    for qid in qids:
        raw = pregs_dict.get(qid, "")
        text = raw.split("|", 1)[1] if "|" in raw else raw
        prefix = text.strip().lower()[:prefix_len]
        if prefix not in groups:
            groups[prefix] = qid
        else:
            existing = groups[prefix]
            ec = existing.split("|")[0]
            nc = qid.split("|")[0]
            if (nc in df.columns and df[nc].nunique()) > (ec in df.columns and df[ec].nunique()):
                groups[prefix] = qid
    return list(groups.values())


def _shannon_entropy(series: pd.Series) -> float:
    counts = series.dropna().value_counts(normalize=True)
    counts = counts[counts > 0]
    return float(-np.sum(counts * np.log2(counts)))


# ---------------------------------------------------------------------------
# Step 0: Question summarization + semantic deduplication
# ---------------------------------------------------------------------------

def _step0_summarize(
    domain: str, survey_title: str, qids: List[str],
    pregs_dict: dict, model: str, cache_path: Path,
) -> Dict[str, Dict]:
    if cache_path.exists():
        print(f"  [{domain}] Step 0: cached ({cache_path.name})")
        return _load_cache(cache_path)

    lines = []
    for qid in qids:
        raw = pregs_dict.get(qid, "")
        text = raw.split("|", 1)[1].strip() if "|" in raw else raw.strip()
        lines.append(f'"{qid}": {text}')
    questions_block = "\n".join(lines)

    prompt = f"""You are a survey methodologist reviewing questions from a Mexican public opinion survey.

Survey: {survey_title}
Domain: {domain}

Your tasks:
1. For each question, write a 1-sentence English summary of what it measures. Include the specific topic — e.g. "Trust in the Army to fight corruption (0-10 scale)" not just "Trust in an institution".
2. Identify near-duplicate questions — same concept with slightly different wording or response coding (e.g., main question vs alternate coding, follow-up recoding of the same item).
3. For each duplicate group, mark ONE question as canonical (keep=true) — prefer the version with more response categories. All others get keep=false and duplicate_of pointing to the canonical qid.

QUESTIONS:
{questions_block}

Return ONLY a JSON object (no commentary):
{{
  "qid": {{
    "summary": "one-sentence English summary",
    "duplicate_of": null,
    "keep": true
  }},
  ...
}}
"""

    print(f"  [{domain}] Step 0: Summarizing {len(qids)} questions...")
    raw_resp = _call_claude(prompt, model=model, max_tokens=16384, temperature=0.2)
    result = _parse_json_response(raw_resp)
    for qid in qids:
        if qid not in result:
            result[qid] = {"summary": pregs_dict.get(qid, qid), "duplicate_of": None, "keep": True}
    _save_cache(result, cache_path)
    n_kept = sum(1 for v in result.values() if v.get("keep", True))
    print(f"  [{domain}] Step 0: {n_kept}/{len(qids)} kept, saved {cache_path.name}")
    return result


# ---------------------------------------------------------------------------
# Step 1: Construct cluster proposal
# ---------------------------------------------------------------------------

def _step1_construct_clusters(
    domain: str, survey_title: str, domain_label: str,
    summaries: Dict[str, str], n_constructs: int,
    model: str, cache_path: Path,
) -> List[Dict]:
    """
    Propose n≥5 construct clusters. Each cluster is a group of questions
    that together or separately measure a meaningful construct.
    """
    if cache_path.exists():
        print(f"  [{domain}] Step 1: cached ({cache_path.name})")
        return _load_cache(cache_path)

    q_lines = "\n".join(f'  {qid}: {s}' for qid, s in summaries.items())

    prompt = f"""You are a social science researcher with expertise in Mexican public opinion surveys.

Survey: {survey_title}
Domain: {domain_label}

Below are the available questions (deduplicated, summarized in English):

{q_lines}

Your task: Propose exactly {n_constructs} meaningful CONSTRUCT CLUSTERS. Each cluster is a group
of questions from this survey that together or separately measure a relevant theoretical construct.

Guidelines:
- A construct is a latent variable (e.g., "institutional trust", "perceived discrimination",
  "political efficacy") — not a survey topic or section header.
- Each cluster should contain 2-8 questions that jointly measure the construct.
- Some constructs may be measurable by a single question; others require aggregating several.
- Questions should NOT appear in multiple clusters (assign each to its best fit).
- Choose constructs that are important for understanding Mexican public opinion AND that can
  potentially relate to other survey domains (cross-domain relevance).
- Avoid creating clusters around response format (e.g., "all 0-10 scale questions") — cluster
  by substantive content.

For each construct provide:
  - name: short snake_case label (e.g., "institutional_trust", "civic_participation")
  - description: 1-2 sentences describing what this construct measures. Keep it minimal but
    precise enough that a researcher could evaluate it.
  - question_cluster: list of qids that belong to this cluster
  - requires_aggregation: true if the construct is best measured by combining multiple
    questions into a composite score; false if a single representative question suffices

Return ONLY a JSON array:
[
  {{
    "name": "...",
    "description": "...",
    "question_cluster": ["qid1", "qid2", ...],
    "requires_aggregation": true
  }},
  ...
]
"""

    print(f"  [{domain}] Step 1: Proposing {n_constructs} construct clusters...")
    raw_resp = _call_claude(prompt, model=model, max_tokens=4096, temperature=0.4)
    result = _parse_json_response(raw_resp)
    if not isinstance(result, list):
        raise ValueError(f"Step 1 returned {type(result)}, expected list")
    _save_cache(result, cache_path)
    print(f"  [{domain}] Step 1: {len(result)} clusters, saved {cache_path.name}")
    return result


# ---------------------------------------------------------------------------
# Step 2: Research review per construct
# ---------------------------------------------------------------------------

def _step2_research_review(
    domain: str, survey_title: str, domain_label: str,
    clusters: List[Dict], summaries: Dict[str, str],
    model: str, cache_path: Path,
) -> List[Dict]:
    """
    For each construct: academic validation, causal relationships,
    data availability assessment.
    """
    if cache_path.exists():
        print(f"  [{domain}] Step 2: cached ({cache_path.name})")
        return _load_cache(cache_path)

    # Build construct descriptions with their questions for context
    cluster_descriptions = []
    for c in clusters:
        q_details = []
        for qid in c.get("question_cluster", []):
            q_details.append(f"    {qid}: {summaries.get(qid, '?')}")
        cluster_descriptions.append(
            f"Construct: {c['name']}\n"
            f"  Description: {c['description']}\n"
            f"  Questions:\n" + "\n".join(q_details)
        )
    all_constructs_block = "\n\n".join(cluster_descriptions)

    # Also list all 24 survey domains so the LLM can assess cross-domain measurability
    domain_list = ("CIE (Science & Technology), COR (Corruption), CUL (Political Culture), "
                   "DEP (Culture/Sports), DER (Human Rights), ECO (Economy/Employment), "
                   "EDU (Education), ENV (Aging), FAM (Family), FED (Federalism), "
                   "GEN (Gender), GLO (Globalization), HAB (Housing), IDE (Identity/Values), "
                   "IND (Indigenous), JUS (Justice), MED (Environment), MIG (Migration), "
                   "NIN (Children/Youth), POB (Poverty), REL (Religion/Secularization), "
                   "SAL (Health), SEG (Public Security), SOC (Information Society)")

    prompt = f"""You are a social science researcher conducting a literature review to validate
construct definitions for a cross-domain survey analysis of Mexican public opinion.

Survey: {survey_title}
Domain: {domain_label}

The following constructs have been proposed for this domain:

{all_constructs_block}

For EACH construct, provide a research review with:

1. **sources**: 2-5 academic references that discuss this construct, its measurement, or its
   importance. For each source provide:
   - citation: APA format (author, year, title, journal/book)
   - relevance: how it relates to this construct
   - key_finding: one sentence on the main finding or contribution

2. **causal_relationships**: Known causal, correlational, or moderating relationships this
   construct has with other variables. For each:
   - role: "cause" | "effect" | "moderator" | "correlate"
   - related_construct: what it relates to (e.g., "educational attainment", "voter turnout")
   - measurable_in_data: can we measure the related construct with the available surveys?
     Consider all 24 domains: {domain_list}
   - data_source: if measurable, which domain(s) likely contain relevant questions

3. **gap_justification**: If few or no academic sources exist for this construct, provide a
   DETAILED justification (3-5 sentences) explaining:
   - Why this construct is important to measure despite limited literature
   - What gap in knowledge it fills
   - How it contributes to understanding Mexican public opinion
   Set to null if adequate sources were found.

4. **importance_rating**: 1-5 scale for cross-domain analysis importance:
   5 = Essential, highly connected to other domains
   4 = Very important, clear cross-domain relevance
   3 = Moderately important
   2 = Somewhat important, mostly domain-specific
   1 = Low cross-domain relevance

Return ONLY a JSON array:
[
  {{
    "construct_name": "...",
    "sources": [
      {{"citation": "...", "relevance": "...", "key_finding": "..."}},
      ...
    ],
    "causal_relationships": [
      {{
        "role": "cause|effect|moderator|correlate",
        "related_construct": "...",
        "measurable_in_data": true,
        "data_source": "EDU, POB"
      }},
      ...
    ],
    "gap_justification": null,
    "importance_rating": 4
  }},
  ...
]
"""

    print(f"  [{domain}] Step 2: Research review for {len(clusters)} constructs...")
    raw_resp = _call_claude(prompt, model=model, max_tokens=8192, temperature=0.4)
    result = _parse_json_response(raw_resp)
    if not isinstance(result, list):
        raise ValueError(f"Step 2 returned {type(result)}, expected list")
    _save_cache(result, cache_path)
    print(f"  [{domain}] Step 2: Saved {cache_path.name}")
    return result


# ---------------------------------------------------------------------------
# Step 3: Variable strategy per construct
# ---------------------------------------------------------------------------

def _step3_variable_strategy(
    domain: str, survey_title: str,
    clusters: List[Dict], reviews: List[Dict],
    summaries: Dict[str, str], df: pd.DataFrame,
    model: str, cache_path: Path,
) -> List[Dict]:
    """
    For each construct, decide: aggregate multiple questions, or select a single one.
    Also specify the aggregation method and justify the choice.
    """
    if cache_path.exists():
        print(f"  [{domain}] Step 3: cached ({cache_path.name})")
        return _load_cache(cache_path)

    # Add data quality info: number of response categories and entropy per question
    q_info_lines = []
    for c in clusters:
        lines = [f"\nConstruct: {c['name']} (requires_aggregation={c.get('requires_aggregation', False)})"]
        for qid in c.get("question_cluster", []):
            col = qid.split("|")[0]
            if col in df.columns:
                s = df[col].dropna()
                n_cat = s.nunique()
                ent = _shannon_entropy(s)
                lines.append(f"  {qid}: {summaries.get(qid, '?')}  [K={n_cat}, H={ent:.2f}]")
            else:
                lines.append(f"  {qid}: {summaries.get(qid, '?')}  [NOT IN DATA]")
        q_info_lines.append("\n".join(lines))
    constructs_block = "\n".join(q_info_lines)

    # Include importance ratings from reviews
    importance_map = {r.get("construct_name", ""): r.get("importance_rating", 3) for r in reviews}
    importance_info = ", ".join(f"{k}: {v}/5" for k, v in importance_map.items())

    prompt = f"""You are a quantitative social scientist designing bridge variables for a cross-survey
analysis. Each construct will become a variable passed through a statistical bridge that links
different surveys via shared SES demographics.

Survey: {survey_title}
Domain: {domain}
Construct importance ratings: {importance_info}

For each construct below, you must decide HOW to operationalize it as a single variable for
the bridge regression. The bridge model (MNLogit/OrderedModel) requires an ordinal or
categorical target with ≤15 categories.

Available constructs with their questions (K=number of categories, H=Shannon entropy in bits):
{constructs_block}

For each construct, choose ONE strategy:

1. **aggregate**: Combine 2+ questions into a composite score. Use when:
   - The construct is multi-dimensional and no single question captures it fully
   - Questions use compatible scales (all 0-10, or all Likert-5)
   - Aggregation reduces measurement error
   Methods: "sum_score" (sum, then bin to ≤5 categories), "mean_score" (mean, then bin),
   "pca_first_component" (first PC, then bin to 5 quantiles)

2. **single_max_entropy**: Pick the one question with highest Shannon entropy (H). Use when:
   - One question clearly dominates the cluster in content validity
   - Questions use incompatible scales (mixing 0-10 with categorical)
   - The construct is simple and well-captured by one item

3. **single_best_match**: Pick the most face-valid question regardless of entropy. Use when:
   - A specific question is the gold-standard measure of this construct
   - Higher entropy alternatives are less content-valid

For each construct return:
  - construct_name: must match the cluster name
  - strategy: "aggregate" | "single_max_entropy" | "single_best_match"
  - selected_qids: list of qids to use (1 for single, 2+ for aggregate)
  - aggregation_method: "sum_score" | "mean_score" | "pca_first_component" | null (if single)
  - justification: 2-3 sentences explaining the choice, addressing:
    (a) why this strategy is appropriate for this construct
    (b) for aggregation: why the questions are combinable (scale compatibility, face validity)
    (c) for single: why this one question is sufficient

Return ONLY a JSON array:
[
  {{
    "construct_name": "...",
    "strategy": "aggregate",
    "selected_qids": ["qid1", "qid2", "qid3"],
    "aggregation_method": "sum_score",
    "justification": "..."
  }},
  ...
]
"""

    print(f"  [{domain}] Step 3: Variable strategy for {len(clusters)} constructs...")
    raw_resp = _call_claude(prompt, model=model, max_tokens=4096, temperature=0.3)
    result = _parse_json_response(raw_resp)
    if not isinstance(result, list):
        raise ValueError(f"Step 3 returned {type(result)}, expected list")
    _save_cache(result, cache_path)
    print(f"  [{domain}] Step 3: Saved {cache_path.name}")
    return result


# ---------------------------------------------------------------------------
# Step 4: Build bridge variables (local computation)
# ---------------------------------------------------------------------------

def _step4_build_variables(
    domain: str,
    strategies: List[Dict],
    df: pd.DataFrame,
    max_bins: int = 5,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Build bridge variables: create aggregated columns or select singles.
    Returns (modified_df, list_of_bridge_column_names).
    """
    bridge_cols: List[str] = []
    df = df.copy()

    for strat in strategies:
        cname = strat["construct_name"]
        strategy = strat["strategy"]
        qids = strat.get("selected_qids", [])
        agg_method = strat.get("aggregation_method")

        if not qids:
            continue

        # Get column names (strip domain suffix)
        cols = [q.split("|")[0] for q in qids]
        cols = [c for c in cols if c in df.columns]
        if not cols:
            continue

        if strategy == "aggregate" and len(cols) >= 2 and agg_method:
            # Create aggregated column
            agg_col = f"agg_{cname}|{domain}"
            sub = df[cols].dropna()

            if agg_method == "sum_score":
                raw_scores = sub.sum(axis=1)
            elif agg_method == "mean_score":
                raw_scores = sub.mean(axis=1)
            elif agg_method == "pca_first_component":
                # Simple PCA: standardize then take first PC
                standardized = (sub - sub.mean()) / sub.std().replace(0, 1)
                # SVD-based first component
                try:
                    U, S, Vt = np.linalg.svd(standardized.values, full_matrices=False)
                    raw_scores = pd.Series(U[:, 0] * S[0], index=sub.index)
                except Exception:
                    raw_scores = sub.mean(axis=1)  # fallback
            else:
                raw_scores = sub.mean(axis=1)

            # Scale to [1, 10] — preserves ordinal variation, avoids sentinel
            # filter (_SENTINEL_LOW=0), does NOT bin (no ties from qcut).
            lo, hi = raw_scores.min(), raw_scores.max()
            if hi > lo:
                normalised = 1.0 + 9.0 * (raw_scores - lo) / (hi - lo)
            else:
                normalised = raw_scores * 0.0 + 5.0  # constant → all ties, edge case

            df.loc[normalised.index, agg_col] = normalised
            bridge_cols.append(agg_col)
            print(f"    [{domain}] Built aggregate: {agg_col} from {cols} ({agg_method})")

        else:
            # Single variable: pick best column
            if strategy == "single_max_entropy":
                best = max(cols, key=lambda c: _shannon_entropy(df[c].dropna()) if c in df.columns else 0)
            else:
                best = cols[0]  # single_best_match: first in list is LLM's pick

            bridge_col = f"{best}|{domain}"
            bridge_cols.append(bridge_col)
            print(f"    [{domain}] Single variable: {bridge_col}")

    return df, bridge_cols


# ---------------------------------------------------------------------------
# Main selector class
# ---------------------------------------------------------------------------

class SemanticVariableSelector:
    """
    5-step LLM pipeline for construct-based variable selection.

    Parameters
    ----------
    n_constructs : int
        Number of construct clusters to propose per domain (≥5 recommended).
    k_final : int
        Maximum constructs to include in the final bridge sweep.
        Set equal to n_constructs to use all, or lower to select top-importance.
    model_summarizer : str
        Anthropic model for Step 0 (haiku — cheap, fast).
    model_cluster : str
        Anthropic model for Step 1 (sonnet — good at clustering).
    model_reviewer : str
        Anthropic model for Step 2 (opus — best at literature review).
    model_strategist : str
        Anthropic model for Step 3 (sonnet — good at operational decisions).
    cache_dir : str or Path
        Directory for per-domain intermediate JSON outputs.
    """

    def __init__(
        self,
        n_constructs: int = 5,
        k_final: int = 5,
        model_summarizer: str = "claude-haiku-4-5-20251001",
        model_cluster: str = "claude-sonnet-4-6",
        model_reviewer: str = "claude-opus-4-6",
        model_strategist: str = "claude-sonnet-4-6",
        cache_dir: str | Path = CACHE_DIR,
        max_ordinal_categories: int = MAX_ORDINAL_CATEGORIES,
        max_aggregate_bins: int = 5,
    ) -> None:
        self.n_constructs = n_constructs
        self.k_final = k_final
        self.model_summarizer = model_summarizer
        self.model_cluster = model_cluster
        self.model_reviewer = model_reviewer
        self.model_strategist = model_strategist
        self.cache_dir = Path(cache_dir)
        self.max_ordinal_categories = max_ordinal_categories
        self.max_aggregate_bins = max_aggregate_bins

    def select_for_domain(
        self,
        domain: str,
        survey_title: str,
        domain_label: str,
        df: pd.DataFrame,
        all_qids: List[str],
        pregs_dict: dict,
    ) -> DomainSelection:
        """Run the full 5-step pipeline for one domain."""
        t0 = time.time()
        print(f"\n{'='*60}")
        print(f"[{domain}] Starting selection ({len(all_qids)} questions)")
        print(f"{'='*60}")

        # Eligibility filter
        qids = _eligible_qids(domain, df, all_qids)
        print(f"  [{domain}] Eligible (≤{self.max_ordinal_categories} categories): {len(qids)}")
        qids = _fast_dedupe(qids, pregs_dict, df, DEDUPE_PREFIX_LEN)
        print(f"  [{domain}] After prefix dedup: {len(qids)}")

        try:
            # --- Step 0: Summarize + semantic dedup ---
            step0_result = _step0_summarize(
                domain, survey_title, qids, pregs_dict,
                self.model_summarizer, self.cache_dir / f"{domain}_step0_summaries.json",
            )
            kept_qids = [q for q, v in step0_result.items() if v.get("keep", True)]
            summaries = {q: step0_result[q]["summary"] for q in kept_qids}
            print(f"  [{domain}] After semantic dedup: {len(summaries)} questions")

            # --- Step 1: Construct cluster proposal ---
            clusters_raw = _step1_construct_clusters(
                domain, survey_title, domain_label, summaries,
                self.n_constructs, self.model_cluster,
                self.cache_dir / f"{domain}_step1_construct_clusters.json",
            )

            # --- Step 2: Research review ---
            reviews_raw = _step2_research_review(
                domain, survey_title, domain_label, clusters_raw, summaries,
                self.model_reviewer,
                self.cache_dir / f"{domain}_step2_research_review.json",
            )

            # --- Step 3: Variable strategy ---
            strategies_raw = _step3_variable_strategy(
                domain, survey_title, clusters_raw, reviews_raw,
                summaries, df, self.model_strategist,
                self.cache_dir / f"{domain}_step3_variable_strategy.json",
            )

            # --- Step 4: Build variables ---
            df_modified, bridge_cols = _step4_build_variables(
                domain, strategies_raw, df, self.max_aggregate_bins,
            )

            # If k_final < n_constructs, select top-importance constructs
            if len(bridge_cols) > self.k_final:
                importance = {r.get("construct_name", ""): r.get("importance_rating", 3)
                              for r in reviews_raw}
                # Sort strategies by importance (descending), keep top k_final
                ranked = sorted(
                    strategies_raw,
                    key=lambda s: importance.get(s["construct_name"], 3),
                    reverse=True,
                )[:self.k_final]
                ranked_names = {s["construct_name"] for s in ranked}
                bridge_cols = [c for c in bridge_cols
                               if any(s["construct_name"] in c or c.split("|")[0] in
                                      [q.split("|")[0] for q in s.get("selected_qids", [])]
                                      for s in ranked)][:self.k_final]

            # Build typed output objects
            construct_clusters = [
                ConstructCluster(
                    name=c["name"], description=c["description"],
                    question_cluster=c.get("question_cluster", []),
                    requires_aggregation=c.get("requires_aggregation", False),
                ) for c in clusters_raw
            ]
            research_reviews = [
                ResearchReview(
                    construct_name=r.get("construct_name", ""),
                    sources=r.get("sources", []),
                    causal_relationships=r.get("causal_relationships", []),
                    gap_justification=r.get("gap_justification"),
                    importance_rating=r.get("importance_rating", 3),
                ) for r in reviews_raw
            ]
            variable_strategies = [
                VariableStrategy(
                    construct_name=s["construct_name"],
                    strategy=s["strategy"],
                    selected_qids=s.get("selected_qids", []),
                    aggregation_method=s.get("aggregation_method"),
                    justification=s.get("justification", ""),
                    bridge_column=bridge_cols[i] if i < len(bridge_cols) else "",
                ) for i, s in enumerate(strategies_raw)
            ]

            elapsed = time.time() - t0
            print(f"  [{domain}] Done in {elapsed:.1f}s → {bridge_cols}")
            return DomainSelection(
                domain=domain, survey_title=survey_title,
                construct_clusters=construct_clusters,
                research_reviews=research_reviews,
                variable_strategies=variable_strategies,
                selected_variables=bridge_cols,
            )

        except Exception as exc:
            print(f"  [{domain}] ERROR: {exc} — falling back to entropy")
            import traceback; traceback.print_exc()
            scored = []
            for qid in all_qids:
                col = qid.split("|")[0]
                if col in df.columns:
                    s = df[col].dropna()
                    if s.nunique() <= self.max_ordinal_categories and len(s) > 0:
                        scored.append((qid, _shannon_entropy(s)))
            scored.sort(key=lambda x: -x[1])
            return DomainSelection(
                domain=domain, survey_title=survey_title,
                construct_clusters=[], research_reviews=[],
                variable_strategies=[],
                selected_variables=[q for q, _ in scored[:self.k_final]],
                fallback_used=True,
            )

    def select_all_domains(
        self,
        enc_dict: dict, enc_nom_dict_rev: dict,
        rev_topic_dict: dict, pregs_dict: dict,
        workers: int = 1,
        domains_filter: Optional[List[str]] = None,
    ) -> Dict[str, DomainSelection]:
        target_domains = [
            d for d in rev_topic_dict.keys()
            if d not in EXCLUDE_DOMAINS
            and (domains_filter is None or d in domains_filter)
        ]

        def _run(domain: str) -> Tuple[str, Optional[DomainSelection]]:
            survey_name = enc_nom_dict_rev.get(domain)
            if not survey_name:
                return domain, None
            df = enc_dict.get(survey_name, {}).get("dataframe")
            if not isinstance(df, pd.DataFrame):
                return domain, None
            domain_label = rev_topic_dict.get(domain, domain)
            domain_qids = [q for q in pregs_dict if q.endswith(f"|{domain}")]
            return domain, self.select_for_domain(
                domain, survey_name, domain_label, df, domain_qids, pregs_dict,
            )

        results: Dict[str, DomainSelection] = {}
        if workers == 1:
            for domain in target_domains:
                d, sel = _run(domain)
                if sel is not None:
                    results[d] = sel
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futs = {pool.submit(_run, d): d for d in target_domains}
                for fut in as_completed(futs):
                    d, sel = fut.result()
                    if sel is not None:
                        results[d] = sel
        return results

    def save(self, results: Dict[str, DomainSelection], path: Path = OUTPUT_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        out: Dict[str, Any] = {
            "metadata": {
                "n_constructs": self.n_constructs,
                "k_final": self.k_final,
                "model_summarizer": self.model_summarizer,
                "model_cluster": self.model_cluster,
                "model_reviewer": self.model_reviewer,
                "model_strategist": self.model_strategist,
                "generated_at": datetime.now().isoformat(),
            },
            "domains": {},
        }
        for domain, sel in results.items():
            out["domains"][domain] = {
                "survey_title": sel.survey_title,
                "fallback_used": sel.fallback_used,
                "construct_clusters": [asdict(c) for c in sel.construct_clusters],
                "research_reviews": [asdict(r) for r in sel.research_reviews],
                "variable_strategies": [asdict(v) for v in sel.variable_strategies],
                "selected_variables": sel.selected_variables,
            }
        with open(path, "w") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"\nSaved selection to {path}")

    @staticmethod
    def load(path: Path | str = OUTPUT_PATH) -> Dict[str, List[str]]:
        """Load selection → {domain: [bridge_col1, ...]} for sweep scripts."""
        with open(path) as f:
            data = json.load(f)
        return {
            domain: info["selected_variables"]
            for domain, info in data.get("domains", {}).items()
        }

    @staticmethod
    def build_aggregates(
        enc_dict: dict,
        enc_nom_dict_rev: dict,
        selection_path: Path | str = OUTPUT_PATH,
        cache_dir: Path | str = CACHE_DIR,
        max_bins: int = 5,
    ) -> dict:
        """
        Inject aggregated columns into enc_dict DataFrames so sweep scripts
        can use semantic variable selections.

        For each domain in the selection JSON, reads the step3 strategy cache
        to determine which qids to aggregate and how. Creates the aggregated
        columns (agg_*) directly in the DataFrames within enc_dict.

        Parameters
        ----------
        enc_dict : dict
            Survey data dict: {survey_name: {"dataframe": pd.DataFrame, ...}}.
            Modified in-place (aggregated columns added).
        enc_nom_dict_rev : dict
            {domain_code: survey_name} mapping.
        selection_path : Path
            Path to semantic_variable_selection.json.
        cache_dir : Path
            Directory containing step3 strategy caches.
        max_bins : int
            Number of quantile bins for aggregated scores.

        Returns
        -------
        dict
            The modified enc_dict (same reference, modified in-place).
        """
        selection_path = Path(selection_path)
        cache_dir = Path(cache_dir)

        with open(selection_path) as f:
            selection_data = json.load(f)

        n_built = 0
        for domain, info in selection_data.get("domains", {}).items():
            survey_name = enc_nom_dict_rev.get(domain)
            if not survey_name or survey_name not in enc_dict:
                continue
            df = enc_dict[survey_name].get("dataframe")
            if not isinstance(df, pd.DataFrame):
                continue

            # Load step3 strategies (from cache or from the selection JSON)
            step3_path = cache_dir / f"{domain}_step3_variable_strategy.json"
            if step3_path.exists():
                with open(step3_path) as f:
                    strategies = json.load(f)
            else:
                # Fall back to variable_strategies in the selection JSON
                strategies = [
                    {
                        "construct_name": vs["construct_name"],
                        "strategy": vs["strategy"],
                        "selected_qids": vs["selected_qids"],
                        "aggregation_method": vs["aggregation_method"],
                    }
                    for vs in info.get("variable_strategies", [])
                ]

            for strat in strategies:
                cname = strat["construct_name"]
                strategy = strat["strategy"]
                qids = strat.get("selected_qids", [])
                agg_method = strat.get("aggregation_method")

                if not qids:
                    continue

                cols = [q.split("|")[0] for q in qids]
                cols = [c for c in cols if c in df.columns]
                if not cols:
                    continue

                agg_col_name = f"agg_{cname}"

                if strategy == "aggregate" and len(cols) >= 2 and agg_method:
                    sub = df[cols].dropna()
                    if len(sub) < 10:
                        continue

                    if agg_method == "sum_score":
                        raw_scores = sub.sum(axis=1)
                    elif agg_method == "mean_score":
                        raw_scores = sub.mean(axis=1)
                    elif agg_method == "pca_first_component":
                        standardized = (sub - sub.mean()) / sub.std().replace(0, 1)
                        try:
                            U, S, Vt = np.linalg.svd(
                                standardized.values, full_matrices=False
                            )
                            raw_scores = pd.Series(U[:, 0] * S[0], index=sub.index)
                        except Exception:
                            raw_scores = sub.mean(axis=1)
                    else:
                        raw_scores = sub.mean(axis=1)

                    # Scale to [1, 10] — preserves ordinal variation, avoids
                    # sentinel filter (_SENTINEL_LOW=0), no binning (no qcut ties).
                    lo, hi = raw_scores.min(), raw_scores.max()
                    if hi > lo:
                        normalised = 1.0 + 9.0 * (raw_scores - lo) / (hi - lo)
                    else:
                        normalised = raw_scores * 0.0 + 5.0

                    df[agg_col_name] = np.nan
                    df.loc[normalised.index, agg_col_name] = normalised.astype(float)
                    n_built += 1

                else:
                    # Single variable — no column creation needed.
                    # The sweep uses col.split("|")[0] which maps to the
                    # original column name already in the DataFrame.
                    pass

        print(f"  build_aggregates: created {n_built} aggregated columns "
              f"across {len(selection_data.get('domains', {}))} domains")
        return enc_dict


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Semantic construct-based variable selection for bridge sweep"
    )
    parser.add_argument("--n-constructs", type=int, default=5,
                        help="Construct clusters per domain (default: 5)")
    parser.add_argument("--k-final", type=int, default=5,
                        help="Max constructs to keep per domain (default: 5)")
    parser.add_argument("--model-summarizer", default="claude-haiku-4-5-20251001")
    parser.add_argument("--model-cluster", default="claude-sonnet-4-6")
    parser.add_argument("--model-reviewer", default="claude-opus-4-6")
    parser.add_argument("--model-strategist", default="claude-sonnet-4-6")
    parser.add_argument("--workers", type=int, default=1,
                        help="Parallel workers (default: 1 — LLM rate limits)")
    parser.add_argument("--domains", nargs="*", default=None,
                        help="Specific domains to process (default: all)")
    parser.add_argument("--no-cache", action="store_true",
                        help="Clear cache and recompute from scratch")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    args = parser.parse_args()

    if args.no_cache and args.cache_dir.exists():
        import shutil
        shutil.rmtree(args.cache_dir)
        print(f"Cache cleared: {args.cache_dir}")

    print("Loading survey data...")
    from dataset_knowledge import (
        los_mex_dict, rev_topic_dict, pregs_dict, enc_nom_dict, DATA_AVAILABLE,
    )
    if not DATA_AVAILABLE:
        print("ERROR: Survey data not available.", file=sys.stderr)
        sys.exit(1)

    from ses_analysis import AnalysisConfig
    preprocessed = AnalysisConfig.preprocess_survey_data(los_mex_dict)
    enc_dict = preprocessed.get("enc_dict", los_mex_dict.get("enc_dict", {}))
    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    selector = SemanticVariableSelector(
        n_constructs=args.n_constructs,
        k_final=args.k_final,
        model_summarizer=args.model_summarizer,
        model_cluster=args.model_cluster,
        model_reviewer=args.model_reviewer,
        model_strategist=args.model_strategist,
        cache_dir=args.cache_dir,
    )

    results = selector.select_all_domains(
        enc_dict=enc_dict, enc_nom_dict_rev=enc_nom_dict_rev,
        rev_topic_dict=rev_topic_dict, pregs_dict=pregs_dict,
        workers=args.workers, domains_filter=args.domains,
    )

    selector.save(results, args.output)

    # Summary
    print(f"\n{'='*60}")
    print("SELECTION SUMMARY")
    print(f"{'='*60}")
    for domain, sel in sorted(results.items()):
        flag = " [FALLBACK]" if sel.fallback_used else ""
        n_agg = sum(1 for v in sel.variable_strategies if v.strategy == "aggregate")
        n_single = len(sel.variable_strategies) - n_agg
        print(f"  {domain}: {len(sel.selected_variables)} vars "
              f"({n_agg} aggregated, {n_single} single){flag}")
        for v in sel.variable_strategies:
            strat = f"[{v.strategy}]"
            qids = ", ".join(v.selected_qids[:3])
            if len(v.selected_qids) > 3:
                qids += f" +{len(v.selected_qids)-3} more"
            print(f"    {v.construct_name}: {strat} {qids}")

    n_fallback = sum(1 for s in results.values() if s.fallback_used)
    print(f"\n{len(results)} domains processed, {n_fallback} used fallback")


if __name__ == "__main__":
    main()
