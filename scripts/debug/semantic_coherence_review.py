"""
scripts/debug/semantic_coherence_review.py

LLM-assisted semantic coherence review for all V5 constructs.

For each built construct (multi-item only), loads the question text and value
labels for each item from the survey metadata, then asks an LLM whether all
items coherently measure the same underlying construct. Flags semantically
off-target items for removal.

Outputs:
  data/results/construct_semantic_coherence_v5.md  — per-construct analysis
  data/results/construct_semantic_coherence_v5.json — machine-readable results

Run:
  python scripts/debug/semantic_coherence_review.py
  python scripts/debug/semantic_coherence_review.py --domains CIE REL  # subset
  python scripts/debug/semantic_coherence_review.py --no-resume         # re-run all
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from dataset_knowledge import enc_dict, enc_nom_dict
from scripts.debug.build_construct_variables import build_v4_constructs
from scripts.debug.verify_construct_directions import _rebuild_effective_items

# ── Paths ──────────────────────────────────────────────────────────────────
SVS_V4_PATH       = ROOT / "data/results/semantic_variable_selection_v4.json"
V5_OVERRIDES_PATH = ROOT / "data/results/construct_v5_overrides.json"
MANIFEST_PATH     = ROOT / "data/results/construct_variable_manifest.json"
CACHE_DIR         = ROOT / "data/results/.semantic_coherence_cache"
OUTPUT_MD         = ROOT / "data/results/construct_semantic_coherence_v5.md"
OUTPUT_JSON       = ROOT / "data/results/construct_semantic_coherence_v5.json"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── LLM ───────────────────────────────────────────────────────────────────
MODEL = "claude-haiku-4-5-20251001"  # fast + cheap; good enough for binary item grading


def _make_llm() -> ChatAnthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    return ChatAnthropic(model=MODEL, api_key=api_key, max_tokens=1024, temperature=0)


# ── Survey metadata helpers ───────────────────────────────────────────────

def _get_survey_meta(domain: str, enc_nom_dict_rev: Dict[str, str]) -> Dict[str, Any]:
    """Return {'column_names_to_labels': {}, 'variable_value_labels': {}} for domain."""
    survey_name = enc_nom_dict_rev.get(domain)
    if survey_name and survey_name in enc_dict:
        return enc_dict[survey_name].get("metadata", {})
    return {}


def _item_text(item: str, col_labels: Dict[str, str]) -> str:
    """Return question text for item, stripping leading number."""
    raw = col_labels.get(item, "")
    if not raw:
        return item  # fallback: just the code
    # Strip leading whitespace and question number pattern like "35 " or "p35 "
    return raw.strip()


def _value_summary(item: str, val_labels: Dict[str, Any]) -> str:
    """Return compact value scale summary, e.g. '1=Sí, 2=No'."""
    vl = val_labels.get(item)
    if not vl or not isinstance(vl, dict):
        return ""
    # Exclude sentinel codes (>=97 or <0)
    entries = []
    for k, label in sorted(vl.items(), key=lambda x: float(x[0])):
        code = float(k)
        if code >= 97 or code < 0:
            continue
        entries.append(f"{int(code)}={label}")
    return ", ".join(entries)


# ── LLM prompt ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = textwrap.dedent("""
You are a social science survey methodologist reviewing construct validity.
You will be given a construct name, its description, and a list of survey
items that are currently included in it. For each item you receive the
question text and answer scale.

Your task:
1. Assess whether each item semantically measures the same underlying
   construct as described. An item is OFF-TARGET if it measures a
   different, unrelated, or only tangentially related concept.
2. Pay attention to items that are merely correlated with the construct
   domain but measure something substantively distinct (e.g. a behavioral
   outcome mixed with an attitudinal construct, or a demographic proxy
   mixed with a perception scale).
3. Be conservative: flag only items with clear semantic problems. Do NOT
   flag items just because they have a broad or general wording.

Respond ONLY with valid JSON — no markdown, no prose outside the JSON:
{
  "construct_verdict": "COHERENT" | "MIXED" | "INCOHERENT",
  "construct_verdict_reason": "<one sentence>",
  "items": [
    {
      "item": "<item code>",
      "verdict": "OK" | "FLAG",
      "reason": "<one sentence, required when FLAG>"
    }
    ...
  ]
}
""").strip()


def _build_prompt(
    key: str,
    description: str,
    items: List[str],
    col_labels: Dict[str, str],
    val_labels: Dict[str, Any],
) -> str:
    lines = [
        f"Construct: {key}",
        f"Description: {description}",
        "",
        "Items:",
    ]
    for item in items:
        text = _item_text(item, col_labels)
        values = _value_summary(item, val_labels)
        lines.append(f"  {item}: {text}")
        if values:
            lines.append(f"    Scale: {values}")
    return "\n".join(lines)


# ── Cache helpers ─────────────────────────────────────────────────────────

def _cache_path(key: str) -> Path:
    safe = key.replace("|", "_").replace(" ", "_")
    return CACHE_DIR / f"{safe}.json"


def _load_cached(key: str) -> Optional[Dict[str, Any]]:
    p = _cache_path(key)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return None


def _save_cache(key: str, result: Dict[str, Any]) -> None:
    with open(_cache_path(key), "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


# ── Per-construct review ───────────────────────────────────────────────────

def _review_construct(
    key: str,
    description: str,
    items: List[str],
    col_labels: Dict[str, str],
    val_labels: Dict[str, Any],
    llm: ChatAnthropic,
    resume: bool = True,
) -> Dict[str, Any]:
    """Call LLM to review semantic coherence. Returns parsed result dict."""
    if resume:
        cached = _load_cached(key)
        if cached is not None:
            return cached

    prompt = _build_prompt(key, description, items, col_labels, val_labels)
    try:
        response = llm.invoke([
            HumanMessage(content=f"{_SYSTEM_PROMPT}\n\n---\n\n{prompt}")
        ])
        text = response.content.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:])
        if text.endswith("```"):
            text = "\n".join(text.split("\n")[:-1])
        result = json.loads(text)
    except Exception as exc:
        result = {
            "construct_verdict": "ERROR",
            "construct_verdict_reason": str(exc),
            "items": [{"item": i, "verdict": "UNKNOWN", "reason": ""} for i in items],
        }
    result["_key"] = key
    result["_items_reviewed"] = items
    _save_cache(key, result)
    return result


# ── Description lookup ────────────────────────────────────────────────────

def _get_description(key: str, svs: Dict[str, Any], ov: Dict[str, Any]) -> str:
    domain, cname = key.split("|", 1)
    # Check new_constructs first
    for nc in ov.get("new_constructs", []):
        if nc.get("domain") == domain and nc.get("name") == cname:
            return nc.get("description", "")
    # SVS v4
    for cl in svs.get("domains", {}).get(domain, {}).get("construct_clusters", []):
        if cl["name"] == cname:
            return cl.get("description", "")
    return ""


# ── Markdown renderer ─────────────────────────────────────────────────────

def _render_markdown(results: List[Dict[str, Any]], path: Path) -> None:
    from datetime import datetime

    flagged_constructs = [r for r in results if r.get("construct_verdict") != "COHERENT"]
    flagged_items_total = sum(
        1 for r in results for i in r.get("items", []) if i.get("verdict") == "FLAG"
    )
    items_to_drop_suggestions: Dict[str, List[str]] = {}
    for r in results:
        key = r["_key"]
        drops = [i["item"] for i in r.get("items", []) if i.get("verdict") == "FLAG"]
        if drops:
            items_to_drop_suggestions[key] = drops

    lines = [
        "# Construct Semantic Coherence Review — V5",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Constructs reviewed | {len(results)} |",
        f"| COHERENT | {sum(1 for r in results if r.get('construct_verdict') == 'COHERENT')} |",
        f"| MIXED | {sum(1 for r in results if r.get('construct_verdict') == 'MIXED')} |",
        f"| INCOHERENT | {sum(1 for r in results if r.get('construct_verdict') == 'INCOHERENT')} |",
        f"| ERROR | {sum(1 for r in results if r.get('construct_verdict') == 'ERROR')} |",
        f"| Items flagged for removal | {flagged_items_total} |",
        f"| Constructs with ≥1 flagged item | {len(items_to_drop_suggestions)} |",
        "",
    ]

    if items_to_drop_suggestions:
        lines += [
            "## Suggested items_to_drop Additions",
            "",
            "Paste into `construct_v5_overrides.json` → `items_to_drop`:",
            "",
            "```json",
        ]
        for key, drops in sorted(items_to_drop_suggestions.items()):
            lines.append(f'  "{key}": {json.dumps(drops)},')
        lines += ["```", ""]

    lines += [
        "## All Constructs",
        "",
        "| Key | Verdict | Flagged items | Reason |",
        "|-----|---------|---------------|--------|",
    ]
    for r in results:
        key = r["_key"]
        verdict = r.get("construct_verdict", "?")
        reason = r.get("construct_verdict_reason", "")
        flags = [i["item"] for i in r.get("items", []) if i.get("verdict") == "FLAG"]
        flag_str = ", ".join(f"`{i}`" for i in flags) if flags else "—"
        lines.append(f"| `{key}` | {verdict} | {flag_str} | {reason} |")

    lines += ["", "## Flagged Constructs", ""]

    for r in results:
        if r.get("construct_verdict") == "COHERENT" and not any(
            i.get("verdict") == "FLAG" for i in r.get("items", [])
        ):
            continue
        key = r["_key"]
        verdict = r.get("construct_verdict", "?")
        lines += [
            f"### `{key}`",
            "",
            f"**Verdict**: {verdict} — {r.get('construct_verdict_reason', '')}",
            "",
            "| Item | Verdict | Reason |",
            "|------|---------|--------|",
        ]
        for item_result in r.get("items", []):
            iv = item_result.get("verdict", "?")
            ir = item_result.get("reason", "")
            lines.append(f"| `{item_result['item']}` | {iv} | {ir} |")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {path}")


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic coherence review for V5 constructs")
    parser.add_argument("--domains", nargs="*", help="Only review these domain codes (e.g. CIE REL)")
    parser.add_argument("--no-resume", action="store_true", help="Re-run all (ignore cache)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts, no LLM calls")
    args = parser.parse_args()

    resume = not args.no_resume

    # ── Load data ──
    print("Loading survey data...")
    with open(SVS_V4_PATH) as f:
        svs = json.load(f)
    with open(V5_OVERRIDES_PATH) as f:
        ov = json.load(f)

    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    print("Building construct variables...")
    enc_dict_built, manifest_list = build_v4_constructs(enc_dict, enc_nom_dict_rev)

    # ── Filter to multi-item built constructs ──
    excluded_keys = set(
        k for k in ov.get("excluded", {}) if not k.startswith("_")
    )
    skip_types = {"single_item_tier2", "formative_index", "excluded"}

    to_review = []
    for m in manifest_list:
        key = m.get("key", "")
        if not m.get("column"):
            continue
        if m.get("type") in skip_types:
            continue
        if key in excluded_keys:
            continue
        domain = key.split("|")[0]
        if args.domains and domain not in args.domains:
            continue
        to_review.append(m)

    print(f"Constructs to review: {len(to_review)}")

    if not args.dry_run:
        llm = _make_llm()
    else:
        llm = None

    # ── Review each construct ──
    all_results: List[Dict[str, Any]] = []
    for idx, m in enumerate(to_review, 1):
        key = m["key"]
        domain = key.split("|")[0]
        survey_name = enc_nom_dict_rev.get(domain)
        meta = enc_dict[survey_name].get("metadata", {}) if survey_name and survey_name in enc_dict else {}
        col_labels = meta.get("column_names_to_labels", {})
        val_labels = meta.get("variable_value_labels", {})

        items, _rev, _sent = _rebuild_effective_items(key, svs.get("domains", {}), ov)
        if not items:
            continue

        description = _get_description(key, svs, ov)

        if args.dry_run:
            print(f"\n[{idx}/{len(to_review)}] {key}")
            print(_build_prompt(key, description, items, col_labels, val_labels))
            print("---")
            continue

        print(f"[{idx}/{len(to_review)}] {key} ({len(items)} items)...", end=" ", flush=True)
        result = _review_construct(
            key=key,
            description=description,
            items=items,
            col_labels=col_labels,
            val_labels=val_labels,
            llm=llm,
            resume=resume,
        )
        verdict = result.get("construct_verdict", "?")
        n_flags = sum(1 for i in result.get("items", []) if i.get("verdict") == "FLAG")
        print(f"{verdict} ({n_flags} flagged)")
        all_results.append(result)

    if args.dry_run:
        return

    # ── Save JSON ──
    with open(OUTPUT_JSON, "w") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nJSON: {OUTPUT_JSON}")

    # ── Render markdown ──
    _render_markdown(all_results, OUTPUT_MD)

    # ── Summary ──
    n_coherent = sum(1 for r in all_results if r.get("construct_verdict") == "COHERENT")
    n_mixed    = sum(1 for r in all_results if r.get("construct_verdict") == "MIXED")
    n_incoh    = sum(1 for r in all_results if r.get("construct_verdict") == "INCOHERENT")
    n_error    = sum(1 for r in all_results if r.get("construct_verdict") == "ERROR")
    n_flag_items = sum(1 for r in all_results for i in r.get("items", []) if i.get("verdict") == "FLAG")
    print(
        f"\n{'='*60}\n"
        f"Review complete: {len(all_results)} constructs\n"
        f"  COHERENT={n_coherent}  MIXED={n_mixed}  INCOHERENT={n_incoh}  ERROR={n_error}\n"
        f"  Items flagged for removal: {n_flag_items}\n"
        f"Report: {OUTPUT_MD}"
    )


if __name__ == "__main__":
    main()
