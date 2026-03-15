"""
Phase 4 — WVS Semantic Coherence Review

LLM-assisted semantic coherence review for all WVS constructs (multi-item only).
Adapted from semantic_coherence_review.py for WVS:
  - Uses Spanish question text from wvs_variable_inventory.json
  - Falls back to English title from column_names_to_labels
  - Same output schema: COHERENT / MIXED / INCOHERENT per construct, FLAG/OK per item

Outputs:
  data/results/wvs_semantic_coherence_v1.md
  data/results/wvs_semantic_coherence_v1.json

Run:
  conda run -n nvg_py13_env python scripts/debug/wvs_semantic_coherence_review.py
  conda run -n nvg_py13_env python scripts/debug/wvs_semantic_coherence_review.py --domains WVS_E WVS_F
  conda run -n nvg_py13_env python scripts/debug/wvs_semantic_coherence_review.py --no-resume
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

SVS_PATH       = ROOT / "data" / "results" / "wvs_svs_v1.json"
INVENTORY_PATH = ROOT / "data" / "results" / "wvs_variable_inventory.json"
MANIFEST_PATH  = ROOT / "data" / "results" / "wvs_construct_manifest.json"
OVERRIDES_PATH = ROOT / "data" / "results" / "wvs_construct_overrides.json"
CACHE_DIR      = ROOT / "data" / "results" / ".wvs_coherence_cache"
OUTPUT_MD      = ROOT / "data" / "results" / "wvs_semantic_coherence_v1.md"
OUTPUT_JSON    = ROOT / "data" / "results" / "wvs_semantic_coherence_v1.json"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "claude-haiku-4-5-20251001"

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

def _make_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model=MODEL,
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        max_tokens=1024,
        temperature=0,
    )


# ---------------------------------------------------------------------------
# Item text helpers
# ---------------------------------------------------------------------------

def _build_item_lookup(inventory: dict) -> dict[str, dict]:
    """Build {qcode: item_dict} from inventory for fast lookup."""
    lookup: dict[str, dict] = {}
    for dom_data in inventory["domains"].values():
        for item in dom_data["items"]:
            lookup[item["qcode"]] = item
    return lookup


def _item_text(qcode: str, item_lookup: dict) -> str:
    """Return best available question text (Spanish if available, else English)."""
    entry = item_lookup.get(qcode, {})
    es = entry.get("title_es", "").strip()
    en = entry.get("title_en", qcode).strip()
    return es if es and len(es) > 5 else en


def _value_summary(qcode: str, item_lookup: dict) -> str:
    """Return scale text from inventory."""
    entry = item_lookup.get(qcode, {})
    scale = entry.get("scale_text", "").strip()
    return scale[:150] if scale else ""


# ---------------------------------------------------------------------------
# LLM prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = textwrap.dedent("""
You are a social science survey methodologist reviewing construct validity
for World Values Survey items applied to Mexico.

You will receive a construct name, its description, and items with Spanish
(or English) question text and answer scales.

Your task:
1. Assess whether each item semantically measures the same underlying construct.
   An item is OFF-TARGET if it measures a different, unrelated, or only tangentially
   related concept.
2. Pay attention to items that are merely correlated with the construct but measure
   something substantively distinct (behavioral outcome vs. attitudinal construct, etc.).
3. Be conservative: flag only items with clear semantic problems.

Respond ONLY with valid JSON — no markdown, no prose outside the JSON:
{
  "construct_verdict": "COHERENT" | "MIXED" | "INCOHERENT",
  "construct_verdict_reason": "<one sentence>",
  "items": [
    {
      "item": "<Q-code>",
      "verdict": "OK" | "FLAG",
      "reason": "<one sentence when FLAG>"
    }
  ]
}
""").strip()


def _build_prompt(key: str, description: str, items: List[str], item_lookup: dict) -> str:
    lines = [
        f"Construct: {key}",
        f"Description: {description}",
        "",
        "Items:",
    ]
    for qcode in items:
        text = _item_text(qcode, item_lookup)
        scale = _value_summary(qcode, item_lookup)
        lines.append(f"  {qcode}: {text}")
        if scale:
            lines.append(f"    Scale: {scale}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _cache_path(key: str) -> Path:
    safe = key.replace("|", "_").replace(" ", "_")
    return CACHE_DIR / f"{safe}.json"


def _load_cached(key: str) -> Optional[dict]:
    p = _cache_path(key)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return None


def _save_cache(key: str, result: dict) -> None:
    with open(_cache_path(key), "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Per-construct review
# ---------------------------------------------------------------------------

def _review_construct(
    key: str, description: str, items: List[str],
    item_lookup: dict, llm, resume: bool
) -> dict:
    if resume:
        cached = _load_cached(key)
        if cached is not None:
            return cached

    prompt = _build_prompt(key, description, items, item_lookup)
    try:
        response = llm.invoke([HumanMessage(content=f"{_SYSTEM_PROMPT}\n\n---\n\n{prompt}")])
        text = response.content.strip()
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


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def _render_markdown(results: List[dict], path: Path) -> None:
    flagged_constructs = [r for r in results if r.get("construct_verdict") != "COHERENT"]
    flagged_items_total = sum(
        1 for r in results for i in r.get("items", []) if i.get("verdict") == "FLAG"
    )
    items_to_drop: dict[str, list] = {}
    for r in results:
        drops = [i["item"] for i in r.get("items", []) if i.get("verdict") == "FLAG"]
        if drops:
            items_to_drop[r["_key"]] = drops

    lines = [
        "# WVS Construct Semantic Coherence Review — V1",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Model: {MODEL}",
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
        f"| Constructs with ≥1 flagged item | {len(items_to_drop)} |",
        "",
    ]

    if items_to_drop:
        lines += [
            "## Suggested items_to_drop for wvs_construct_overrides.json",
            "",
            "```json",
        ]
        for key, drops in sorted(items_to_drop.items()):
            lines.append(f'  "{key}": {json.dumps(drops)},')
        lines += ["```", ""]

    lines += [
        "## All Constructs",
        "",
        "| Key | Verdict | Flagged items | Reason |",
        "|-----|---------|---------------|--------|",
    ]
    for r in results:
        verdict = r.get("construct_verdict", "?")
        reason = r.get("construct_verdict_reason", "")[:80]
        flags = [i["item"] for i in r.get("items", []) if i.get("verdict") == "FLAG"]
        flag_str = ", ".join(f"`{i}`" for i in flags) if flags else "—"
        lines.append(f"| `{r['_key']}` | {verdict} | {flag_str} | {reason} |")

    lines += ["", "## Flagged Constructs", ""]

    for r in results:
        if r.get("construct_verdict") == "COHERENT" and not any(
            i.get("verdict") == "FLAG" for i in r.get("items", [])
        ):
            continue
        lines += [
            f"### `{r['_key']}`",
            "",
            f"**Verdict**: {r.get('construct_verdict')} — {r.get('construct_verdict_reason', '')}",
            "",
            "| Item | Verdict | Reason |",
            "|------|---------|--------|",
        ]
        for ir in r.get("items", []):
            lines.append(f"| `{ir['item']}` | {ir.get('verdict','?')} | {ir.get('reason','')} |")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domains", nargs="*", help="Filter to these WVS domains (e.g. WVS_E WVS_F)")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts, no LLM calls")
    args = parser.parse_args()
    resume = not args.no_resume

    for path, name in [(SVS_PATH, "SVS"), (INVENTORY_PATH, "inventory"), (MANIFEST_PATH, "manifest")]:
        if not path.exists():
            print(f"ERROR: {path} not found. Run earlier phases first.")
            sys.exit(1)

    with open(SVS_PATH) as f:
        svs = json.load(f)
    with open(INVENTORY_PATH) as f:
        inventory = json.load(f)
    with open(MANIFEST_PATH) as f:
        manifest_list = json.load(f)

    item_lookup = _build_item_lookup(inventory)
    manifest = {m["key"]: m for m in manifest_list if m.get("key")}

    # Filter to multi-item built constructs
    skip_types = {"single_item_tier2", "formative_index", "excluded", "missing_items"}
    to_review = [
        m for m in manifest_list
        if m.get("column") and m.get("type") not in skip_types and m.get("n_items", 0) >= 2
    ]

    if args.domains:
        to_review = [m for m in to_review if any(m["key"].startswith(d) for d in args.domains)]

    print(f"Constructs to review: {len(to_review)}")

    if not args.dry_run:
        llm = _make_llm()
    else:
        llm = None

    all_results: List[dict] = []
    for idx, m in enumerate(to_review, 1):
        key = m["key"]
        items = m.get("items", [])
        if not items:
            continue

        # Find description from SVS
        wvs_domain = "WVS_" + key.split("|")[0].replace("WVS_", "")
        cname = key.split("|")[1] if "|" in key else ""
        description = ""
        for cl in svs.get("domains", {}).get(wvs_domain, {}).get("construct_clusters", []):
            if cl.get("name") == cname:
                description = cl.get("description", "")
                break

        if args.dry_run:
            print(f"\n[{idx}/{len(to_review)}] {key}")
            print(_build_prompt(key, description, items, item_lookup))
            print("---")
            continue

        print(f"[{idx}/{len(to_review)}] {key} ({len(items)} items)...", end=" ", flush=True)
        result = _review_construct(key, description, items, item_lookup, llm, resume)
        verdict = result.get("construct_verdict", "?")
        n_flags = sum(1 for i in result.get("items", []) if i.get("verdict") == "FLAG")
        print(f"{verdict} ({n_flags} flagged)")
        all_results.append(result)

    if args.dry_run:
        return

    with open(OUTPUT_JSON, "w") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nJSON: {OUTPUT_JSON}")

    _render_markdown(all_results, OUTPUT_MD)

    n_c = sum(1 for r in all_results if r.get("construct_verdict") == "COHERENT")
    n_m = sum(1 for r in all_results if r.get("construct_verdict") == "MIXED")
    n_i = sum(1 for r in all_results if r.get("construct_verdict") == "INCOHERENT")
    n_f = sum(1 for r in all_results for i in r.get("items", []) if i.get("verdict") == "FLAG")
    print(f"\nComplete: {len(all_results)} constructs — COHERENT={n_c} MIXED={n_m} INCOHERENT={n_i} items_flagged={n_f}")


if __name__ == "__main__":
    main()
