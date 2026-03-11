"""Construct Validation Diagnostic.

Three-phase validation of all construct clusters in semantic_variable_selection.json:
  Phase A — Per-construct LLM audit (name accuracy, description, question fit)
  Phase B — Per-domain cross-construct misassignment detection
  Phase C — Statistical diagnostics (Cronbach α, inter-item r, PCA variance)

Outputs: data/results/construct_validation_report.json

Usage:
  python scripts/debug/validate_constructs.py                    # full run
  python scripts/debug/validate_constructs.py --domains IDE SOC  # subset
  python scripts/debug/validate_constructs.py --resume           # resume interrupted
  python scripts/debug/validate_constructs.py --stats-only       # skip LLM, stats only
"""
from __future__ import annotations

import argparse
import json
import re
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', message='.*ConstantInputWarning.*')

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

SVS_PATH = ROOT / 'data' / 'results' / 'semantic_variable_selection.json'
CACHE_DIR = ROOT / 'data' / 'results' / '.semantic_selection_cache'
OUTPUT_PATH = ROOT / 'data' / 'results' / 'construct_validation_report.json'

MODEL_VALIDATOR = 'claude-sonnet-4-6'
LLM_TIMEOUT = 90  # seconds per call
MAX_TOKENS = 4096


def _set_model(model: str) -> None:
    global MODEL_VALIDATOR
    MODEL_VALIDATOR = model


# ── Anthropic helpers (from select_bridge_variables_semantic.py) ──

def _call_claude(prompt: str, model: str, max_tokens: int = MAX_TOKENS,
                 temperature: float = 0.2) -> str:
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model, max_tokens=max_tokens, temperature=temperature,
        messages=[{'role': 'user', 'content': prompt}],
    )
    return msg.content[0].text


def _parse_json_response(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r'```(?:json)?\s*([\s\S]+?)```', text, re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    for pattern in (r'(\[[\s\S]+\])', r'(\{[\s\S]+\})'):
        m = re.search(pattern, text)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    raise ValueError(f'Could not parse JSON from response:\n{text[:500]}')


# ── Atomic checkpoint ──

def _save_checkpoint(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def _load_checkpoint(path: Path) -> Optional[dict]:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


# ═══════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════

def load_pregs_dict() -> dict:
    """Load question text mapping via dataset_knowledge (handles pkl/json paths)."""
    from dataset_knowledge import pregs_dict
    return pregs_dict


def load_svs() -> dict:
    """Load semantic_variable_selection.json."""
    with open(SVS_PATH) as f:
        return json.load(f)


def load_step0_summaries() -> Dict[str, dict]:
    """Load all cached step0 summary files. Returns {domain: {qid: {summary, ...}}}."""
    summaries = {}
    for p in sorted(CACHE_DIR.glob('*_step0_summaries.json')):
        domain = p.stem.split('_step0')[0]
        with open(p) as f:
            summaries[domain] = json.load(f)
    return summaries


def build_construct_records(svs: dict, step0: dict,
                            pregs_dict: dict) -> List[dict]:
    """Assemble complete records for each construct with question text."""
    records = []
    for domain_id, domain_data in svs.get('domains', {}).items():
        survey_title = domain_data.get('survey_title', domain_id)
        step0_dom = step0.get(domain_id, {})

        for cluster in domain_data.get('construct_clusters', []):
            name = cluster['name']
            desc = cluster.get('description', '')
            qids_raw = cluster.get('question_cluster', [])

            questions = []
            for qid_raw in qids_raw:
                # Strip domain suffix if present (v2 stores 'p2|COR', v1 stores 'p2')
                qid_bare = qid_raw.split('|')[0] if '|' in qid_raw else qid_raw
                qid_full = f'{qid_bare}|{domain_id}'
                # Get Spanish text from pregs_dict
                raw_entry = pregs_dict.get(qid_full, '')
                spanish = raw_entry.split('|', 1)[1] if '|' in raw_entry else raw_entry
                # Get English summary from step0
                s0 = step0_dom.get(qid_full, step0_dom.get(qid_bare, {}))
                english = s0.get('summary', '') if isinstance(s0, dict) else ''
                questions.append({
                    'qid': qid_bare,
                    'qid_full': qid_full,
                    'spanish': spanish.strip(),
                    'english_summary': english.strip(),
                })

            # Also get the variable strategy for this construct
            strategy = None
            for vs in domain_data.get('variable_strategies', []):
                if vs.get('construct_name') == name:
                    strategy = vs
                    break

            records.append({
                'domain': domain_id,
                'survey_title': survey_title,
                'construct_name': name,
                'description': desc,
                'questions': questions,
                'n_questions': len(questions),
                'requires_aggregation': cluster.get('requires_aggregation', True),
                'strategy': strategy,
            })
    return records


# ═══════════════════════════════════════════════════════════════════
# PHASE A: PER-CONSTRUCT LLM VALIDATION
# ═══════════════════════════════════════════════════════════════════

PHASE_A_PROMPT = """\
You are a survey methodology expert evaluating whether a construct label accurately \
describes the survey questions assigned to it. Be CRITICAL — flag any mismatch.

CONSTRUCT NAME: {name}
CONSTRUCT DESCRIPTION: {description}
SURVEY DOMAIN: {survey_title} ({domain})

QUESTIONS IN THIS CONSTRUCT:
{questions_block}

EVALUATE each dimension on a 1-5 scale (1=completely wrong, 3=partially correct, 5=perfect match):

1. name_accuracy: Does the construct NAME describe what these questions collectively measure?
2. description_accuracy: Does the DESCRIPTION match what the questions actually measure?
3. internal_coherence: Do ALL questions belong together as measures of one latent construct?

Also provide:
4. outlier_questions: List any questions that do NOT fit this construct. For each, explain \
what the question actually measures and why it doesn't belong.
5. suggested_name: A better name if current name is inaccurate (null if name is fine).
6. suggested_description: A better 1-2 sentence description if current is inaccurate (null if fine).
7. summary_accuracy: For each question, does the English summary accurately represent the \
original Spanish question? Flag any mistranslations or significant information loss.
8. verdict: "valid" | "needs_rename" | "needs_restructure"
9. reasoning: Brief explanation of your assessment.

Return STRICT JSON with this exact schema:
{{
  "name_accuracy": int,
  "description_accuracy": int,
  "internal_coherence": int,
  "outlier_questions": [
    {{"qid": str, "actually_measures": str, "why_doesnt_fit": str}}
  ],
  "suggested_name": str | null,
  "suggested_description": str | null,
  "summary_accuracy": [
    {{"qid": str, "accurate": bool, "issue": str | null}}
  ],
  "verdict": str,
  "reasoning": str
}}
"""


def _format_questions_block(questions: List[dict]) -> str:
    lines = []
    for q in questions:
        lines.append(f'  {q["qid"]}:')
        if q['spanish']:
            lines.append(f'    [ES] {q["spanish"]}')
        if q['english_summary']:
            lines.append(f'    [EN summary] {q["english_summary"]}')
        if not q['spanish'] and not q['english_summary']:
            lines.append(f'    [no text available]')
    return '\n'.join(lines)


def validate_construct(record: dict) -> dict:
    """Phase A: validate a single construct via LLM."""
    prompt = PHASE_A_PROMPT.format(
        name=record['construct_name'],
        description=record['description'],
        survey_title=record['survey_title'],
        domain=record['domain'],
        questions_block=_format_questions_block(record['questions']),
    )
    raw = _call_claude(prompt, MODEL_VALIDATOR)
    result = _parse_json_response(raw)
    result['composite_score'] = round(
        np.mean([result.get('name_accuracy', 3),
                 result.get('description_accuracy', 3),
                 result.get('internal_coherence', 3)]), 2)
    return result


# ═══════════════════════════════════════════════════════════════════
# PHASE B: PER-DOMAIN CROSS-CONSTRUCT MISASSIGNMENT
# ═══════════════════════════════════════════════════════════════════

PHASE_B_PROMPT = """\
You are a survey methodology expert. Given ALL constructs within a single survey domain, \
identify questions that may be assigned to the wrong construct.

DOMAIN: {survey_title} ({domain})

CONSTRUCTS:
{constructs_block}

EVALUATE:
1. misassigned_questions: Questions that would fit better in a sibling construct.
2. orphan_questions: Questions that don't fit any of the existing constructs.
3. domain_level_issues: Any structural problems with how this domain's questions are divided.

Return STRICT JSON:
{{
  "misassigned_questions": [
    {{"qid": str, "current_construct": str, "better_construct": str, "reasoning": str}}
  ],
  "orphan_questions": [
    {{"qid": str, "reasoning": str}}
  ],
  "domain_level_issues": str | null
}}
"""


def _format_constructs_block(records: List[dict]) -> str:
    parts = []
    for r in records:
        qs = ', '.join(
            f'{q["qid"]}: {q["english_summary"] or q["spanish"][:80]}'
            for q in r['questions']
        )
        parts.append(
            f'Construct "{r["construct_name"]}": {r["description"]}\n'
            f'  Questions: {qs}'
        )
    return '\n\n'.join(parts)


def review_domain(domain: str, records: List[dict]) -> dict:
    """Phase B: cross-construct misassignment check for one domain."""
    prompt = PHASE_B_PROMPT.format(
        survey_title=records[0]['survey_title'],
        domain=domain,
        constructs_block=_format_constructs_block(records),
    )
    raw = _call_claude(prompt, MODEL_VALIDATOR, max_tokens=4096)
    return _parse_json_response(raw)


# ═══════════════════════════════════════════════════════════════════
# PHASE C: STATISTICAL DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════

def _load_survey_df(survey_name: str) -> Optional[pd.DataFrame]:
    """Load a single survey DataFrame via dataset_knowledge."""
    from dataset_knowledge import enc_dict
    entry = enc_dict.get(survey_name)
    if entry is None:
        return None
    df = entry.get('dataframe')
    return df if isinstance(df, pd.DataFrame) else None


def cronbach_alpha(df_items: pd.DataFrame) -> Optional[float]:
    """Cronbach's alpha for a set of items. Returns None if < 2 items or no variance."""
    df_clean = df_items.dropna()
    k = df_clean.shape[1]
    if k < 2 or len(df_clean) < 10:
        return None
    item_vars = df_clean.var(axis=0, ddof=1)
    if item_vars.sum() == 0:
        return None
    total_var = df_clean.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return None
    alpha = (k / (k - 1)) * (1 - item_vars.sum() / total_var)
    return round(float(alpha), 4)


def mean_inter_item_correlation(df_items: pd.DataFrame) -> Optional[float]:
    """Mean pairwise Spearman correlation between items."""
    df_clean = df_items.dropna()
    k = df_clean.shape[1]
    if k < 2 or len(df_clean) < 10:
        return None
    corr = df_clean.corr(method='spearman')
    # Extract upper triangle (exclude diagonal)
    mask = np.triu(np.ones(corr.shape, dtype=bool), k=1)
    vals = corr.values[mask]
    if len(vals) == 0:
        return None
    return round(float(np.nanmean(vals)), 4)


def pca_variance_explained(df_items: pd.DataFrame) -> Optional[dict]:
    """PCA on items: variance explained by first component. Uses SVD, no sklearn."""
    df_clean = df_items.dropna()
    k = df_clean.shape[1]
    if k < 2 or len(df_clean) < 10:
        return None
    # Standardize
    X = df_clean.values.astype(float)
    X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-12)
    try:
        _, s, _ = np.linalg.svd(X, full_matrices=False)
    except np.linalg.LinAlgError:
        return None
    var_explained = s ** 2 / (s ** 2).sum()
    return {
        'pc1_variance_ratio': round(float(var_explained[0]), 4),
        'pc2_variance_ratio': round(float(var_explained[1]), 4) if k > 1 else 0.0,
        'n_components_90pct': int(np.searchsorted(np.cumsum(var_explained), 0.90) + 1),
    }


def _is_sentinel(val: float) -> bool:
    """Filter sentinel codes (>= 97 or < 0)."""
    return val >= 97 or val < 0


def compute_stats_for_construct(record: dict, df: pd.DataFrame) -> dict:
    """Phase C: statistical diagnostics for one construct."""
    qids = [q['qid'] for q in record['questions']]
    # Find matching columns in DataFrame
    cols_found = [c for c in qids if c in df.columns]
    n_found = len(cols_found)
    n_expected = len(qids)

    result = {
        'n_questions_expected': n_expected,
        'n_questions_found': n_found,
        'columns_missing': [c for c in qids if c not in df.columns],
    }

    if n_found < 2:
        result['cronbach_alpha'] = None
        result['mean_inter_item_r'] = None
        result['pca'] = None
        result['stat_verdict'] = 'too_few_items' if n_found < 2 else 'single_item'
        result['n_valid_rows'] = int(df[cols_found].dropna().shape[0]) if cols_found else 0
        return result

    # Build clean item matrix: drop sentinels, then drop NaN rows
    sub = df[cols_found].copy()
    for col in cols_found:
        sub[col] = pd.to_numeric(sub[col], errors='coerce')
        sub.loc[sub[col].apply(lambda v: _is_sentinel(v) if pd.notna(v) else False), col] = np.nan
    sub = sub.dropna()
    result['n_valid_rows'] = int(len(sub))

    if len(sub) < 10:
        result['cronbach_alpha'] = None
        result['mean_inter_item_r'] = None
        result['pca'] = None
        result['stat_verdict'] = 'insufficient_data'
        return result

    alpha = cronbach_alpha(sub)
    mean_r = mean_inter_item_correlation(sub)
    pca = pca_variance_explained(sub)

    result['cronbach_alpha'] = alpha
    result['mean_inter_item_r'] = mean_r
    result['pca'] = pca

    # Statistical verdict
    if alpha is not None and alpha >= 0.7 and mean_r is not None and mean_r >= 0.3:
        result['stat_verdict'] = 'good'
    elif alpha is not None and alpha >= 0.5:
        result['stat_verdict'] = 'questionable'
    elif alpha is not None and alpha < 0.5:
        result['stat_verdict'] = 'poor'
    else:
        result['stat_verdict'] = 'indeterminate'

    # Per-item diagnostics: item-total correlation (drop each item, check if alpha improves)
    item_analysis = []
    for col in cols_found:
        others = [c for c in cols_found if c != col]
        if len(others) < 2:
            continue
        total_others = sub[others].sum(axis=1)
        r_item_total = sub[col].corr(total_others, method='spearman')
        alpha_without = cronbach_alpha(sub[others])
        item_analysis.append({
            'qid': col,
            'item_total_r': round(float(r_item_total), 4) if pd.notna(r_item_total) else None,
            'alpha_if_dropped': alpha_without,
            'improves_alpha': (alpha_without is not None and alpha is not None
                               and alpha_without > alpha + 0.02),
        })
    result['item_analysis'] = item_analysis

    return result


# ═══════════════════════════════════════════════════════════════════
# ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════

def run_phase_a(records: List[dict], report: dict,
                workers: int = 3) -> dict:
    """Run Phase A (per-construct LLM validation) with checkpointing."""
    constructs = report.setdefault('constructs', {})
    pending = [r for r in records
               if f'{r["domain"]}|{r["construct_name"]}' not in constructs
               or 'name_accuracy' not in constructs[f'{r["domain"]}|{r["construct_name"]}']]

    if not pending:
        print(f'  Phase A: all {len(records)} constructs already validated')
        return report

    print(f'  Phase A: {len(pending)} constructs to validate ({len(records) - len(pending)} cached)')
    t0 = time.time()
    completed = 0

    def _run_one(rec: dict) -> Tuple[str, dict]:
        key = f'{rec["domain"]}|{rec["construct_name"]}'
        try:
            result = validate_construct(rec)
        except Exception as exc:
            result = {'error': str(exc), 'verdict': 'error', 'composite_score': 0}
        return key, result

    if workers <= 1:
        for rec in pending:
            key, result = _run_one(rec)
            constructs[key] = {**constructs.get(key, {}), **result}
            completed += 1
            elapsed = time.time() - t0
            print(f'    [{completed}/{len(pending)}] {key}: '
                  f'verdict={result.get("verdict", "?")} '
                  f'score={result.get("composite_score", "?")} '
                  f'({elapsed:.0f}s)', flush=True)
            _save_checkpoint(report, OUTPUT_PATH)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(_run_one, r): r for r in pending}
            for fut in as_completed(futs):
                key, result = fut.result()
                constructs[key] = {**constructs.get(key, {}), **result}
                completed += 1
                elapsed = time.time() - t0
                print(f'    [{completed}/{len(pending)}] {key}: '
                      f'verdict={result.get("verdict", "?")} '
                      f'score={result.get("composite_score", "?")} '
                      f'({elapsed:.0f}s)', flush=True)
                _save_checkpoint(report, OUTPUT_PATH)

    return report


def run_phase_b(records: List[dict], report: dict,
                workers: int = 2) -> dict:
    """Run Phase B (per-domain cross-construct review) with checkpointing."""
    domain_reviews = report.setdefault('domain_reviews', {})
    # Group records by domain
    by_domain: Dict[str, List[dict]] = {}
    for r in records:
        by_domain.setdefault(r['domain'], []).append(r)

    pending = [d for d in by_domain if d not in domain_reviews
               or 'misassigned_questions' not in domain_reviews[d]]

    if not pending:
        print(f'  Phase B: all {len(by_domain)} domains already reviewed')
        return report

    print(f'  Phase B: {len(pending)} domains to review ({len(by_domain) - len(pending)} cached)')
    t0 = time.time()
    completed = 0

    def _run_one(dom: str) -> Tuple[str, dict]:
        try:
            result = review_domain(dom, by_domain[dom])
        except Exception as exc:
            result = {'error': str(exc)}
        return dom, result

    if workers <= 1:
        for dom in pending:
            key, result = _run_one(dom)
            domain_reviews[key] = result
            completed += 1
            n_mis = len(result.get('misassigned_questions', []))
            print(f'    [{completed}/{len(pending)}] {key}: '
                  f'{n_mis} misassigned ({time.time() - t0:.0f}s)', flush=True)
            _save_checkpoint(report, OUTPUT_PATH)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(_run_one, d): d for d in pending}
            for fut in as_completed(futs):
                key, result = fut.result()
                domain_reviews[key] = result
                completed += 1
                n_mis = len(result.get('misassigned_questions', []))
                print(f'    [{completed}/{len(pending)}] {key}: '
                      f'{n_mis} misassigned ({time.time() - t0:.0f}s)', flush=True)
                _save_checkpoint(report, OUTPUT_PATH)

    return report


def run_phase_c(records: List[dict], report: dict) -> dict:
    """Run Phase C (statistical diagnostics) — local computation, no LLM."""
    constructs = report.setdefault('constructs', {})

    # Check which constructs need stats
    pending = [r for r in records
               if 'cronbach_alpha' not in constructs.get(
                   f'{r["domain"]}|{r["construct_name"]}', {})]

    if not pending:
        print(f'  Phase C: all {len(records)} constructs have stats')
        return report

    print(f'  Phase C: computing stats for {len(pending)} constructs...')

    # Load DataFrames by survey (cache to avoid reloading)
    from dataset_knowledge import enc_dict, enc_nom_dict
    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    df_cache: Dict[str, pd.DataFrame] = {}
    t0 = time.time()

    for i, rec in enumerate(pending):
        key = f'{rec["domain"]}|{rec["construct_name"]}'
        survey_name = enc_nom_dict_rev.get(rec['domain'])
        if survey_name is None:
            constructs.setdefault(key, {}).update({
                'cronbach_alpha': None, 'mean_inter_item_r': None,
                'pca': None, 'stat_verdict': 'no_survey_data',
                'n_valid_rows': 0, 'item_analysis': [],
            })
            continue

        if survey_name not in df_cache:
            entry = enc_dict.get(survey_name)
            if entry and isinstance(entry.get('dataframe'), pd.DataFrame):
                df_cache[survey_name] = entry['dataframe']
            else:
                constructs.setdefault(key, {}).update({
                    'cronbach_alpha': None, 'mean_inter_item_r': None,
                    'pca': None, 'stat_verdict': 'no_dataframe',
                    'n_valid_rows': 0, 'item_analysis': [],
                })
                continue

        df = df_cache[survey_name]
        stats = compute_stats_for_construct(rec, df)
        constructs.setdefault(key, {}).update(stats)

        if (i + 1) % 10 == 0:
            print(f'    [{i + 1}/{len(pending)}] ({time.time() - t0:.0f}s)', flush=True)

    _save_checkpoint(report, OUTPUT_PATH)
    print(f'  Phase C: done ({time.time() - t0:.0f}s)')
    return report


def build_summary(report: dict) -> dict:
    """Aggregate metrics across all phases."""
    constructs = report.get('constructs', {})
    domain_reviews = report.get('domain_reviews', {})

    # Phase A summary
    verdicts = [c.get('verdict', 'unknown') for c in constructs.values()]
    scores = [c.get('composite_score', 0) for c in constructs.values()
              if c.get('composite_score') is not None]
    n_outliers = sum(len(c.get('outlier_questions', [])) for c in constructs.values())
    bad_summaries = sum(
        1 for c in constructs.values()
        for sa in c.get('summary_accuracy', [])
        if isinstance(sa, dict) and not sa.get('accurate', True)
    )

    # Phase B summary
    total_misassigned = sum(
        len(d.get('misassigned_questions', []))
        for d in domain_reviews.values()
    )

    # Phase C summary
    alphas = [c['cronbach_alpha'] for c in constructs.values()
              if c.get('cronbach_alpha') is not None]
    stat_verdicts = [c.get('stat_verdict', 'unknown') for c in constructs.values()]

    # Worst constructs (lowest composite score)
    ranked = sorted(constructs.items(), key=lambda kv: kv[1].get('composite_score', 5))
    worst_10 = [
        {'key': k, 'composite_score': v.get('composite_score'),
         'verdict': v.get('verdict'), 'stat_verdict': v.get('stat_verdict'),
         'cronbach_alpha': v.get('cronbach_alpha'),
         'suggested_name': v.get('suggested_name')}
        for k, v in ranked[:10]
    ]

    # Constructs that are semantically valid but statistically poor
    semantic_ok_stat_bad = [
        k for k, v in constructs.items()
        if v.get('composite_score', 0) >= 3.5
        and v.get('stat_verdict') == 'poor'
    ]
    # Constructs that are statistically valid but semantically bad
    stat_ok_semantic_bad = [
        k for k, v in constructs.items()
        if v.get('cronbach_alpha') is not None and v['cronbach_alpha'] >= 0.7
        and v.get('composite_score', 5) < 3.0
    ]

    summary = {
        'n_constructs': len(constructs),
        'phase_a': {
            'n_valid': verdicts.count('valid'),
            'n_needs_rename': verdicts.count('needs_rename'),
            'n_needs_restructure': verdicts.count('needs_restructure'),
            'n_errors': verdicts.count('error'),
            'mean_composite_score': round(np.mean(scores), 2) if scores else None,
            'n_outlier_questions': n_outliers,
            'n_bad_summaries': bad_summaries,
        },
        'phase_b': {
            'n_domains_reviewed': len(domain_reviews),
            'total_misassigned': total_misassigned,
            'domains_with_issues': [
                d for d, v in domain_reviews.items()
                if len(v.get('misassigned_questions', [])) > 0
            ],
        },
        'phase_c': {
            'mean_cronbach_alpha': round(np.mean(alphas), 3) if alphas else None,
            'median_cronbach_alpha': round(float(np.median(alphas)), 3) if alphas else None,
            'n_good': stat_verdicts.count('good'),
            'n_questionable': stat_verdicts.count('questionable'),
            'n_poor': stat_verdicts.count('poor'),
            'n_too_few_items': stat_verdicts.count('too_few_items'),
        },
        'cross_phase': {
            'semantic_ok_stat_bad': semantic_ok_stat_bad,
            'stat_ok_semantic_bad': stat_ok_semantic_bad,
        },
        'worst_constructs': worst_10,
    }
    return summary


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Construct Validation Diagnostic')
    parser.add_argument('--domains', nargs='*', default=None,
                        help='Domain codes to validate (default: all)')
    parser.add_argument('--workers', type=int, default=3,
                        help='Parallel LLM workers (default: 3)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from existing checkpoint')
    parser.add_argument('--stats-only', action='store_true',
                        help='Skip LLM phases, run only Phase C stats')
    parser.add_argument('--model', default=MODEL_VALIDATOR,
                        help=f'LLM model (default: {MODEL_VALIDATOR})')
    args = parser.parse_args()

    _set_model(args.model)

    # Load or resume report
    report = _load_checkpoint(OUTPUT_PATH) if args.resume else None
    if report is None:
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'model': args.model,
                'script': 'validate_constructs.py',
            },
            'constructs': {},
            'domain_reviews': {},
        }

    # Load data sources
    print('Loading data sources...', flush=True)
    pregs_dict = load_pregs_dict()
    print(f'  pregs_dict: {len(pregs_dict)} entries')
    svs = load_svs()
    step0 = load_step0_summaries()
    print(f'  step0 summaries: {len(step0)} domains')

    # Build records
    records = build_construct_records(svs, step0, pregs_dict)
    if args.domains:
        records = [r for r in records if r['domain'] in args.domains]
    print(f'  {len(records)} constructs across '
          f'{len(set(r["domain"] for r in records))} domains')

    if not args.stats_only:
        # Phase A
        print('\n── Phase A: Per-construct LLM validation ──', flush=True)
        report = run_phase_a(records, report, workers=args.workers)

        # Phase B
        print('\n── Phase B: Cross-construct misassignment ──', flush=True)
        report = run_phase_b(records, report, workers=min(args.workers, 3))

    # Phase C (always runs — it's local computation)
    print('\n── Phase C: Statistical diagnostics ──', flush=True)
    report = run_phase_c(records, report)

    # Build summary
    print('\n── Building summary ──', flush=True)
    report['summary'] = build_summary(report)
    report['metadata']['completed_at'] = datetime.now().isoformat()
    _save_checkpoint(report, OUTPUT_PATH)

    # Print summary
    s = report['summary']
    print(f'\n{"=" * 60}')
    print(f'VALIDATION COMPLETE: {s["n_constructs"]} constructs')
    print(f'{"=" * 60}')

    pa = s.get('phase_a', {})
    if pa:
        print(f'\nPhase A (Semantic):')
        print(f'  Valid: {pa.get("n_valid", "?")}  |  '
              f'Needs rename: {pa.get("n_needs_rename", "?")}  |  '
              f'Needs restructure: {pa.get("n_needs_restructure", "?")}')
        print(f'  Mean composite score: {pa.get("mean_composite_score", "?")}')
        print(f'  Outlier questions: {pa.get("n_outlier_questions", "?")}')
        print(f'  Bad summaries (Step 0): {pa.get("n_bad_summaries", "?")}')

    pb = s.get('phase_b', {})
    if pb:
        print(f'\nPhase B (Cross-construct):')
        print(f'  Total misassigned: {pb.get("total_misassigned", "?")}')
        if pb.get('domains_with_issues'):
            print(f'  Domains with issues: {", ".join(pb["domains_with_issues"])}')

    pc = s.get('phase_c', {})
    if pc:
        print(f'\nPhase C (Statistical):')
        print(f'  Mean α: {pc.get("mean_cronbach_alpha", "?")}  |  '
              f'Median α: {pc.get("median_cronbach_alpha", "?")}')
        print(f'  Good: {pc.get("n_good", "?")}  |  '
              f'Questionable: {pc.get("n_questionable", "?")}  |  '
              f'Poor: {pc.get("n_poor", "?")}  |  '
              f'Too few items: {pc.get("n_too_few_items", "?")}')

    cx = s.get('cross_phase', {})
    if cx:
        if cx.get('semantic_ok_stat_bad'):
            print(f'\nSemantic OK but stat poor ({len(cx["semantic_ok_stat_bad"])}):')
            for k in cx['semantic_ok_stat_bad']:
                print(f'  - {k}')
        if cx.get('stat_ok_semantic_bad'):
            print(f'\nStat OK but semantic bad ({len(cx["stat_ok_semantic_bad"])}):')
            for k in cx['stat_ok_semantic_bad']:
                print(f'  - {k}')

    print(f'\nWorst 10 constructs:')
    for w in s.get('worst_constructs', []):
        print(f'  {w["key"]}: score={w["composite_score"]} '
              f'verdict={w["verdict"]} α={w["cronbach_alpha"]} '
              f'stat={w["stat_verdict"]}')

    print(f'\nReport saved: {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
