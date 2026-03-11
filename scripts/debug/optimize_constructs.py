"""Construct Optimization: Item Pruning + LLM Re-exploration.

Two-strategy optimization for poor constructs (α < 0.5):

  Strategy 1 — Iterative item pruning: Drop worst-fitting items until α improves
               or minimum item count (3) is reached. Free, instant.
  Strategy 2 — LLM re-exploration: For constructs that remain poor after pruning,
               send unused domain questions to LLM to find better replacements.

Reads:  data/results/construct_validation_report.json (Phase C stats)
        data/results/semantic_variable_selection.json (current constructs)
        data/results/.semantic_selection_cache/*_step0_summaries.json

Writes: data/results/semantic_variable_selection_v3.json (optimized constructs)
        data/results/construct_optimization_log.json (detailed log)

Usage:
    python scripts/debug/optimize_constructs.py                     # both strategies
    python scripts/debug/optimize_constructs.py --prune-only        # strategy 1 only
    python scripts/debug/optimize_constructs.py --reexplore-only    # strategy 2 only
    python scripts/debug/optimize_constructs.py --domains REL SAL   # subset
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

REPORT_PATH = ROOT / "data" / "results" / "construct_validation_report.json"
SVS_PATH = ROOT / "data" / "results" / "semantic_variable_selection.json"
CACHE_DIR = ROOT / "data" / "results" / ".semantic_selection_cache"
OUTPUT_SVS = ROOT / "data" / "results" / "semantic_variable_selection_v3.json"
OUTPUT_LOG = ROOT / "data" / "results" / "construct_optimization_log.json"

MIN_ITEMS = 3          # minimum items after pruning
ALPHA_TARGET = 0.5     # target α for pruning to stop
MODEL_REEXPLORE = "claude-sonnet-4-6"


# ── Helpers ──

def _is_sentinel(val: float) -> bool:
    return val >= 97 or val < 0


def _cronbach_alpha(df_items: pd.DataFrame) -> Optional[float]:
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
    return float((k / (k - 1)) * (1 - item_vars.sum() / total_var))


def _clean_item_matrix(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Build clean numeric item matrix: sentinel → NaN, then dropna."""
    sub = df[cols].copy()
    for col in cols:
        sub[col] = pd.to_numeric(sub[col], errors="coerce")
        sub.loc[sub[col].apply(
            lambda v: _is_sentinel(v) if pd.notna(v) else False
        ), col] = np.nan
    return sub.dropna()


def _save_atomic(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def _call_claude(prompt: str, model: str, max_tokens: int = 4096,
                 temperature: float = 0.3) -> str:
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model, max_tokens=max_tokens, temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _parse_json_response(text: str) -> Any:
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


# ═══════════════════════════════════════════════════════════════════
# STRATEGY 1: ITERATIVE ITEM PRUNING
# ═══════════════════════════════════════════════════════════════════

def prune_construct(
    construct_key: str,
    qids: List[str],
    df: pd.DataFrame,
    min_items: int = MIN_ITEMS,
    alpha_target: float = ALPHA_TARGET,
) -> dict:
    """
    Iteratively drop the worst-fitting item until:
      - α >= alpha_target, OR
      - only min_items remain, OR
      - no drop improves α

    Returns dict with original_alpha, final_alpha, dropped_items, remaining_items.
    """
    cols = [q for q in qids if q in df.columns]
    if len(cols) < min_items:
        return {
            "action": "skip",
            "reason": "too_few_items",
            "original_items": qids,
            "remaining_items": qids,
            "dropped_items": [],
            "original_alpha": None,
            "final_alpha": None,
        }

    sub = _clean_item_matrix(df, cols)
    original_alpha = _cronbach_alpha(sub)

    if original_alpha is None:
        return {
            "action": "skip",
            "reason": "cannot_compute_alpha",
            "original_items": qids,
            "remaining_items": qids,
            "dropped_items": [],
            "original_alpha": None,
            "final_alpha": None,
        }

    if original_alpha >= alpha_target:
        return {
            "action": "no_change",
            "reason": "already_above_target",
            "original_items": qids,
            "remaining_items": qids,
            "dropped_items": [],
            "original_alpha": round(original_alpha, 4),
            "final_alpha": round(original_alpha, 4),
        }

    current_cols = list(cols)
    dropped = []
    current_alpha = original_alpha

    while len(current_cols) > min_items:
        # Try dropping each item, find best improvement
        best_col = None
        best_alpha = current_alpha

        for col in current_cols:
            remaining = [c for c in current_cols if c != col]
            if len(remaining) < 2:
                continue
            sub_try = _clean_item_matrix(df, remaining)
            a = _cronbach_alpha(sub_try)
            if a is not None and a > best_alpha:
                best_alpha = a
                best_col = col

        if best_col is None:
            # No improvement possible
            break

        current_cols.remove(best_col)
        dropped.append(best_col)
        current_alpha = best_alpha

        if current_alpha >= alpha_target:
            break

    action = "pruned" if dropped else "no_improvement"
    return {
        "action": action,
        "reason": f"alpha {original_alpha:.3f} → {current_alpha:.3f}",
        "original_items": qids,
        "remaining_items": current_cols,
        "dropped_items": dropped,
        "original_alpha": round(original_alpha, 4),
        "final_alpha": round(current_alpha, 4),
        "reached_target": current_alpha >= alpha_target,
    }


def run_strategy1(
    svs: dict, report: dict, df_cache: dict, enc_nom_dict_rev: dict,
    target_domains: Optional[List[str]] = None,
) -> Tuple[dict, List[dict]]:
    """
    Run Strategy 1 on all poor constructs.
    Returns (updated svs, list of prune logs).
    """
    print("\n══ Strategy 1: Iterative Item Pruning ══")
    constructs_report = report.get("constructs", {})
    logs = []

    # Find poor constructs
    poor_keys = [
        k for k, v in constructs_report.items()
        if v.get("stat_verdict") == "poor"
        and (target_domains is None or k.split("|")[0] in target_domains)
    ]
    print(f"  {len(poor_keys)} poor constructs to process")

    pruned_count = 0
    improved_count = 0

    for key in poor_keys:
        domain, cname = key.split("|", 1)
        survey_name = enc_nom_dict_rev.get(domain)
        if survey_name is None or survey_name not in df_cache:
            logs.append({"key": key, "action": "skip", "reason": "no_dataframe"})
            continue

        df = df_cache[survey_name]

        # Find the cluster in svs
        dom_data = svs["domains"].get(domain)
        if dom_data is None:
            continue
        cluster = None
        for c in dom_data.get("construct_clusters", []):
            if c["name"] == cname:
                cluster = c
                break
        if cluster is None:
            continue

        qids_raw = cluster.get("question_cluster", [])
        qids_bare = [q.split("|")[0] if "|" in q else q for q in qids_raw]

        result = prune_construct(key, qids_bare, df)
        logs.append({"key": key, **result})

        if result["action"] == "pruned" and result["dropped_items"]:
            pruned_count += 1
            if result.get("reached_target"):
                improved_count += 1
            # Update the cluster in svs
            kept_bare = set(result["remaining_items"])
            cluster["question_cluster"] = [
                q for q in qids_raw
                if (q.split("|")[0] if "|" in q else q) in kept_bare
            ]
            cluster["pruning_applied"] = True
            cluster["items_dropped"] = result["dropped_items"]
            cluster["alpha_before_pruning"] = result["original_alpha"]
            cluster["alpha_after_pruning"] = result["final_alpha"]

            print(f"  ✓ {key}: α {result['original_alpha']:.3f} → "
                  f"{result['final_alpha']:.3f} "
                  f"(dropped {len(result['dropped_items'])} items"
                  f"{', TARGET REACHED' if result.get('reached_target') else ''})")

    print(f"\n  Summary: {pruned_count} pruned, {improved_count} reached α≥{ALPHA_TARGET}")
    return svs, logs


# ═══════════════════════════════════════════════════════════════════
# STRATEGY 2: LLM RE-EXPLORATION OF UNUSED QUESTIONS
# ═══════════════════════════════════════════════════════════════════

REEXPLORE_PROMPT = """\
You are a survey methodology expert. A construct cluster has poor internal \
consistency (Cronbach's α < 0.5 even after item pruning). Your task: find \
REPLACEMENT or ADDITIONAL questions from unused survey items that would form \
a more coherent measurement of the same underlying dimension.

DOMAIN: {survey_title} ({domain})

CURRENT CONSTRUCT:
  Name: {construct_name}
  Description: {description}
  Current items (α = {alpha:.3f}):
{current_items_block}

UNUSED QUESTIONS IN THIS DOMAIN (not assigned to any construct):
{unused_items_block}

INSTRUCTIONS:
1. Review each unused question carefully (use the SPANISH original for meaning).
2. Identify questions that measure the SAME underlying dimension as the construct.
3. Also flag any current items that are clearly misfit and should be REPLACED.
4. The goal is a coherent cluster with α ≥ 0.5 (ideally ≥ 0.7).
5. Prefer keeping the cluster size between 3-8 items.
6. If no unused questions fit this construct, say so honestly.

Return STRICT JSON:
{{
  "verdict": "improved" | "replaced" | "no_improvement",
  "reasoning": "Brief explanation of changes",
  "add_questions": ["qid1", "qid2"],
  "remove_questions": ["qid3"],
  "suggested_name": "new_name_if_changed" | null,
  "suggested_description": "new description if changed" | null,
  "confidence": "high" | "medium" | "low"
}}
"""


def _format_items_block(qids: List[str], pregs_dict: dict, step0: dict,
                        domain: str) -> str:
    """Format question items with Spanish text and English summary."""
    lines = []
    for qid in qids:
        qid_full = f"{qid}|{domain}"
        raw = pregs_dict.get(qid_full, "")
        spanish = raw.split("|", 1)[1] if "|" in raw else raw
        s0 = step0.get(qid_full, step0.get(qid, {}))
        english = s0.get("summary", "") if isinstance(s0, dict) else ""
        lines.append(f"    {qid}:")
        if spanish:
            lines.append(f"      [ES] {spanish.strip()}")
        if english:
            lines.append(f"      [EN] {english.strip()}")
        if not spanish and not english:
            lines.append(f"      [no text available]")
    return "\n".join(lines)


def run_strategy2(
    svs: dict, report: dict, prune_logs: List[dict],
    df_cache: dict, enc_nom_dict_rev: dict,
    pregs_dict: dict, step0_all: dict,
    target_domains: Optional[List[str]] = None,
    model: str = MODEL_REEXPLORE,
) -> Tuple[dict, List[dict]]:
    """
    Run Strategy 2 on constructs still poor after pruning.
    Returns (updated svs, list of reexplore logs).
    """
    print("\n══ Strategy 2: LLM Re-exploration of Unused Questions ══")

    # Identify constructs still poor after Strategy 1
    prune_results = {log["key"]: log for log in prune_logs if "key" in log}
    constructs_report = report.get("constructs", {})

    still_poor = []
    for key, v in constructs_report.items():
        if v.get("stat_verdict") != "poor":
            continue
        domain = key.split("|")[0]
        if target_domains and domain not in target_domains:
            continue
        # Check if pruning already rescued it
        prune = prune_results.get(key, {})
        if prune.get("reached_target"):
            continue
        still_poor.append(key)

    print(f"  {len(still_poor)} constructs still poor after pruning")
    if not still_poor:
        return svs, []

    # Build used-question sets per domain
    used_per_domain: Dict[str, set] = {}
    for dom_id, dom_data in svs["domains"].items():
        used = set()
        for c in dom_data.get("construct_clusters", []):
            for q in c.get("question_cluster", []):
                qid = q.split("|")[0] if "|" in q else q
                used.add(qid)
        used_per_domain[dom_id] = used

    logs = []
    improved = 0
    t0 = time.time()

    for i, key in enumerate(still_poor):
        domain, cname = key.split("|", 1)
        dom_data = svs["domains"].get(domain)
        if dom_data is None:
            continue

        # Find current cluster
        cluster = None
        for c in dom_data.get("construct_clusters", []):
            if c["name"] == cname:
                cluster = c
                break
        if cluster is None:
            continue

        # Get step0 summaries for this domain
        step0_dom = step0_all.get(domain, {})
        if not step0_dom:
            logs.append({"key": key, "verdict": "skip", "reason": "no_step0"})
            continue

        # Find unused questions
        all_qids = set(k.split("|")[0] for k in step0_dom.keys())
        used = used_per_domain.get(domain, set())
        unused_qids = sorted(all_qids - used)

        if not unused_qids:
            logs.append({"key": key, "verdict": "skip", "reason": "no_unused_questions"})
            continue

        # Current items
        current_qids = [
            q.split("|")[0] if "|" in q else q
            for q in cluster.get("question_cluster", [])
        ]
        alpha = constructs_report.get(key, {}).get("cronbach_alpha", 0.0) or 0.0
        # Use post-pruning alpha if available
        prune = prune_results.get(key, {})
        if prune.get("final_alpha") is not None:
            alpha = prune["final_alpha"]

        # Build prompt
        prompt = REEXPLORE_PROMPT.format(
            survey_title=dom_data.get("survey_title", domain),
            domain=domain,
            construct_name=cname,
            description=cluster.get("description", ""),
            alpha=alpha,
            current_items_block=_format_items_block(
                current_qids, pregs_dict, step0_dom, domain),
            unused_items_block=_format_items_block(
                unused_qids, pregs_dict, step0_dom, domain),
        )

        try:
            raw = _call_claude(prompt, model)
            result = _parse_json_response(raw)
        except Exception as exc:
            logs.append({"key": key, "verdict": "error", "error": str(exc)})
            print(f"  ✗ [{i+1}/{len(still_poor)}] {key}: ERROR {exc}")
            continue

        # Apply changes if LLM suggests improvements
        add_qs = result.get("add_questions", [])
        remove_qs = result.get("remove_questions", [])
        verdict = result.get("verdict", "no_improvement")

        log_entry = {"key": key, **result}

        if verdict in ("improved", "replaced") and (add_qs or remove_qs):
            # Validate: check added questions exist in DataFrame
            survey_name = enc_nom_dict_rev.get(domain)
            df = df_cache.get(survey_name)

            # Build new question list
            new_qids = [q for q in current_qids if q not in remove_qs]
            for q in add_qs:
                if q not in new_qids:
                    new_qids.append(q)

            # Verify α improvement
            if df is not None and len(new_qids) >= 2:
                valid_cols = [q for q in new_qids if q in df.columns]
                if len(valid_cols) >= 2:
                    sub = _clean_item_matrix(df, valid_cols)
                    new_alpha = _cronbach_alpha(sub)

                    if new_alpha is not None and new_alpha > alpha:
                        # Apply the change
                        cluster["question_cluster"] = [
                            f"{q}|{domain}" for q in new_qids
                        ]
                        cluster["reexplored"] = True
                        cluster["items_added"] = add_qs
                        cluster["items_removed"] = remove_qs
                        cluster["alpha_before_reexplore"] = round(alpha, 4)
                        cluster["alpha_after_reexplore"] = round(new_alpha, 4)

                        if result.get("suggested_name"):
                            cluster["name_before_reexplore"] = cname
                            cluster["name"] = result["suggested_name"]
                        if result.get("suggested_description"):
                            cluster["description"] = result["suggested_description"]

                        # Update used set
                        for q in add_qs:
                            used_per_domain[domain].add(q)

                        log_entry["verified_alpha"] = round(new_alpha, 4)
                        log_entry["applied"] = True
                        improved += 1
                        print(f"  ✓ [{i+1}/{len(still_poor)}] {key}: "
                              f"α {alpha:.3f} → {new_alpha:.3f} "
                              f"(+{len(add_qs)} -{len(remove_qs)} items) "
                              f"[{result.get('confidence', '?')}]")
                    else:
                        log_entry["verified_alpha"] = round(new_alpha, 4) if new_alpha else None
                        log_entry["applied"] = False
                        log_entry["reason"] = "no_alpha_improvement_after_verification"
                        print(f"  ~ [{i+1}/{len(still_poor)}] {key}: "
                              f"LLM suggested changes but α didn't improve "
                              f"({alpha:.3f} → {new_alpha if new_alpha else 'None'})")
                else:
                    log_entry["applied"] = False
                    log_entry["reason"] = f"only {len(valid_cols)} valid columns"
                    print(f"  ~ [{i+1}/{len(still_poor)}] {key}: "
                          f"added items not found in DataFrame")
            else:
                log_entry["applied"] = False
                log_entry["reason"] = "no_dataframe"
        else:
            log_entry["applied"] = False
            print(f"  - [{i+1}/{len(still_poor)}] {key}: no improvement found "
                  f"[{result.get('confidence', '?')}]")

        logs.append(log_entry)
        elapsed = time.time() - t0
        if (i + 1) % 5 == 0:
            print(f"    ... {i+1}/{len(still_poor)} processed ({elapsed:.0f}s)")

    print(f"\n  Summary: {improved}/{len(still_poor)} improved by re-exploration")
    return svs, logs


# ═══════════════════════════════════════════════════════════════════
# RE-COMPUTE STATS (mini Phase C for changed constructs)
# ═══════════════════════════════════════════════════════════════════

def recompute_stats(svs: dict, df_cache: dict, enc_nom_dict_rev: dict) -> dict:
    """Recompute Cronbach α for all constructs in the (possibly modified) svs."""
    print("\n══ Recomputing Statistics ══")
    stats = {}
    for dom_id, dom_data in svs["domains"].items():
        survey_name = enc_nom_dict_rev.get(dom_id)
        df = df_cache.get(survey_name) if survey_name else None
        if df is None:
            continue

        for cluster in dom_data.get("construct_clusters", []):
            key = f"{dom_id}|{cluster['name']}"
            qids = [
                q.split("|")[0] if "|" in q else q
                for q in cluster.get("question_cluster", [])
            ]
            cols = [q for q in qids if q in df.columns]
            if len(cols) < 2:
                stats[key] = {"alpha": None, "n_items": len(cols), "verdict": "too_few"}
                continue
            sub = _clean_item_matrix(df, cols)
            alpha = _cronbach_alpha(sub)
            verdict = "good" if alpha and alpha >= 0.7 else (
                "questionable" if alpha and alpha >= 0.5 else "poor"
            )
            stats[key] = {
                "alpha": round(alpha, 4) if alpha else None,
                "n_items": len(cols),
                "n_valid_rows": len(sub),
                "verdict": verdict,
            }
    return stats


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Construct Optimization")
    parser.add_argument("--domains", nargs="*", default=None)
    parser.add_argument("--prune-only", action="store_true",
                        help="Only run Strategy 1 (item pruning)")
    parser.add_argument("--reexplore-only", action="store_true",
                        help="Only run Strategy 2 (LLM re-exploration)")
    parser.add_argument("--model", default=MODEL_REEXPLORE,
                        help=f"LLM model for Strategy 2 (default: {MODEL_REEXPLORE})")
    parser.add_argument("--alpha-target", type=float, default=ALPHA_TARGET,
                        help=f"Target α for pruning (default: {ALPHA_TARGET})")
    args = parser.parse_args()

    # Load inputs
    print("Loading data...", flush=True)

    with open(REPORT_PATH) as f:
        report = json.load(f)
    print(f"  Validation report: {len(report.get('constructs', {}))} constructs")

    with open(SVS_PATH) as f:
        svs = json.load(f)
    print(f"  SVS: {len(svs.get('domains', {}))} domains")

    # Load step0 summaries
    step0_all = {}
    for p in sorted(CACHE_DIR.glob("*_step0_summaries.json")):
        domain = p.stem.split("_step0")[0]
        with open(p) as f:
            step0_all[domain] = json.load(f)
    print(f"  Step0 summaries: {len(step0_all)} domains")

    # Load survey DataFrames
    from dataset_knowledge import enc_dict, enc_nom_dict, pregs_dict
    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    df_cache: Dict[str, pd.DataFrame] = {}
    for survey_name, entry in enc_dict.items():
        if isinstance(entry.get("dataframe"), pd.DataFrame):
            df_cache[survey_name] = entry["dataframe"]
    print(f"  DataFrames: {len(df_cache)} surveys loaded")

    # ── Strategy 1: Item Pruning ──
    prune_logs = []
    if not args.reexplore_only:
        svs, prune_logs = run_strategy1(
            svs, report, df_cache, enc_nom_dict_rev,
            target_domains=args.domains,
        )

    # ── Strategy 2: LLM Re-exploration ──
    reexplore_logs = []
    if not args.prune_only:
        svs, reexplore_logs = run_strategy2(
            svs, report, prune_logs,
            df_cache, enc_nom_dict_rev,
            pregs_dict, step0_all,
            target_domains=args.domains,
            model=args.model,
        )

    # ── Recompute final stats ──
    final_stats = recompute_stats(svs, df_cache, enc_nom_dict_rev)

    # ── Compare v2 vs v3 ──
    print("\n══ Comparison: v2 → v3 ══")
    v2_verdicts = {"good": 0, "questionable": 0, "poor": 0, "too_few": 0}
    v3_verdicts = {"good": 0, "questionable": 0, "poor": 0, "too_few": 0}

    for key, v in report.get("constructs", {}).items():
        sv = v.get("stat_verdict", "poor")
        if sv in v2_verdicts:
            v2_verdicts[sv] += 1

    for key, v in final_stats.items():
        sv = v.get("verdict", "poor")
        if sv in v3_verdicts:
            v3_verdicts[sv] += 1

    v2_alphas = [v.get("cronbach_alpha") for v in report["constructs"].values()
                 if v.get("cronbach_alpha") is not None]
    v3_alphas = [v["alpha"] for v in final_stats.values()
                 if v.get("alpha") is not None]

    print(f"  v2: good={v2_verdicts['good']}, questionable={v2_verdicts['questionable']}, "
          f"poor={v2_verdicts['poor']}  |  mean α={np.mean(v2_alphas):.3f}, "
          f"median α={np.median(v2_alphas):.3f}")
    print(f"  v3: good={v3_verdicts['good']}, questionable={v3_verdicts['questionable']}, "
          f"poor={v3_verdicts['poor']}  |  mean α={np.mean(v3_alphas):.3f}, "
          f"median α={np.median(v3_alphas):.3f}")

    # Individual changes
    changes = []
    for key in final_stats:
        v2_a = report["constructs"].get(key, {}).get("cronbach_alpha")
        v3_a = final_stats[key].get("alpha")
        if v2_a is not None and v3_a is not None and abs(v3_a - v2_a) > 0.01:
            changes.append((key, v2_a, v3_a, v3_a - v2_a))
    changes.sort(key=lambda x: -x[3])

    if changes:
        print(f"\n  Top improvements:")
        for key, v2_a, v3_a, delta in changes[:15]:
            print(f"    {key}: {v2_a:.3f} → {v3_a:.3f} ({delta:+.3f})")
        degraded = [c for c in changes if c[3] < -0.01]
        if degraded:
            print(f"\n  Degradations ({len(degraded)}):")
            for key, v2_a, v3_a, delta in degraded:
                print(f"    {key}: {v2_a:.3f} → {v3_a:.3f} ({delta:+.3f})")

    # ── Save outputs ──
    svs["metadata"]["optimized_at"] = datetime.now().isoformat()
    svs["metadata"]["optimization_strategies"] = [
        "item_pruning" if not args.reexplore_only else None,
        "llm_reexploration" if not args.prune_only else None,
    ]
    _save_atomic(svs, OUTPUT_SVS)
    print(f"\n  Saved optimized SVS → {OUTPUT_SVS.name}")

    optimization_log = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "alpha_target": args.alpha_target,
            "model": args.model,
        },
        "strategy1_prune": prune_logs,
        "strategy2_reexplore": reexplore_logs,
        "final_stats": final_stats,
        "comparison": {
            "v2": v2_verdicts,
            "v3": v3_verdicts,
            "v2_mean_alpha": round(float(np.mean(v2_alphas)), 4),
            "v3_mean_alpha": round(float(np.mean(v3_alphas)), 4),
            "v2_median_alpha": round(float(np.median(v2_alphas)), 4),
            "v3_median_alpha": round(float(np.median(v3_alphas)), 4),
            "individual_changes": [
                {"key": k, "v2_alpha": v2, "v3_alpha": v3, "delta": round(d, 4)}
                for k, v2, v3, d in changes
            ],
        },
    }
    _save_atomic(optimization_log, OUTPUT_LOG)
    print(f"  Saved optimization log → {OUTPUT_LOG.name}")


if __name__ == "__main__":
    main()
