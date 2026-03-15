"""
Phase 2 — WVS SVS: LLM construct clustering for WVS Wave 7 variables.

Reads wvs_variable_inventory.json (Phase 1) and runs a 3-step LLM pipeline
per domain to produce wvs_svs_v1.json — same schema as semantic_variable_selection_v4.json.

Steps per domain:
  1. Cluster items into latent constructs (name + description + items)
  2. Research review (coherence check, cross-reference validated indices)
  3. Variable strategy (construct_type, gateway_items, reverse_coded_items)

Output:
  data/results/wvs_svs_v1.json      — draft SVS (review before running build_wvs_constructs.py)
  data/results/build_wvs_svs.log    — per-domain LLM output for audit

Run:
  conda run -n nvg_py13_env python scripts/debug/build_wvs_svs.py
  conda run -n nvg_py13_env python scripts/debug/build_wvs_svs.py --domains E F  # subset
  conda run -n nvg_py13_env python scripts/debug/build_wvs_svs.py --no-resume     # re-run all
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

INVENTORY_PATH = ROOT / "data" / "results" / "wvs_variable_inventory.json"
OUT_SVS  = ROOT / "data" / "results" / "wvs_svs_v1.json"
OUT_LOG  = ROOT / "data" / "results" / "build_wvs_svs.log"
CACHE_DIR = ROOT / "data" / "results" / ".wvs_svs_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "claude-opus-4-6"  # full model for construct architecture decisions

# Minimum N_valid to include an item in clustering
MIN_N_VALID_PCT = 15.0

# ---------------------------------------------------------------------------
# LLM factory
# ---------------------------------------------------------------------------

def _make_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model=MODEL,
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        max_tokens=4096,
        temperature=0,
    )

# ---------------------------------------------------------------------------
# Item formatter for LLM prompts
# ---------------------------------------------------------------------------

def _format_item(item: dict) -> str:
    title = item["title_es"] or item["title_en"]
    scale = item.get("scale_text", "")
    n = item["n_valid"]
    validated = "; ".join(item["validated_indices"]) if item["validated_indices"] else ""
    waves = ",".join(str(w) for w in item["wave_coverage"])
    parts = [f"  {item['qcode']} [{item['acode']}] (N={n}, waves={waves}): {title}"]
    if scale:
        parts.append(f"    Scale: {scale[:120]}")
    if validated:
        parts.append(f"    [Validated index: {validated}]")
    return "\n".join(parts)

# ---------------------------------------------------------------------------
# Step 1: Cluster items into constructs
# ---------------------------------------------------------------------------

_STEP1_SYSTEM = textwrap.dedent("""
You are a cross-national survey methodologist designing a measurement model
for the World Values Survey applied to Mexico. Your goal is to identify
**latent constructs** — underlying psychological or sociological dimensions
that multiple survey items jointly measure.

RULES:
1. Each item belongs to AT MOST ONE construct. If an item does not clearly
   fit any construct, leave it as standalone (single_item_tier2).
2. Constructs need at least 2 items to be a scale. Standalone items are valid.
3. Construct names must be snake_case, descriptive, and domain-specific.
4. Include ALL items in your output — none may be silently dropped.
5. Flag items as reverse-coded (higher code = LESS of the construct) with [R].
6. For items marked [Validated index:...], note which validated scale they belong to.

OUTPUT: Valid JSON only — no prose, no markdown fences.
Schema:
{
  "constructs": [
    {
      "name": "snake_case_name",
      "description": "One sentence describing the latent construct.",
      "items": ["Q1", "Q2", "Q3"],
      "reverse_coded_items": ["Q2"],
      "validated_index": "Name of WVS validated index this maps to, or null"
    }
  ],
  "standalone_items": ["Q42", "Q99"]
}
""").strip()


def _step1_cluster(domain: str, domain_label: str, items: List[dict], llm) -> dict:
    item_block = "\n".join(_format_item(x) for x in items)
    prompt = f"""Domain: {domain} — {domain_label}

Items to cluster ({len(items)} total):
{item_block}

Group these items into latent constructs following the rules above.
"""
    response = llm.invoke([HumanMessage(content=f"{_STEP1_SYSTEM}\n\n---\n\n{prompt}")])
    text = response.content.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    return json.loads(text)


# ---------------------------------------------------------------------------
# Step 2: Research review
# ---------------------------------------------------------------------------

_STEP2_SYSTEM = textwrap.dedent("""
You are a social science methodologist reviewing a draft measurement model
for Mexico using World Values Survey data.

For each proposed construct:
1. Assess semantic coherence: do all items measure the same underlying concept?
2. Check alignment with known WVS validated indices (noted in the data).
3. Flag constructs where the items span multiple distinct dimensions (multi-dimensional).
4. Suggest dropping specific items if they are off-target.

OUTPUT: Valid JSON only.
Schema:
{
  "review": [
    {
      "construct_name": "...",
      "coherence": "good" | "acceptable" | "poor",
      "notes": "Brief notes. Max 2 sentences.",
      "items_to_drop": ["Q_X"],
      "validated_index_match": "exact" | "partial" | "none"
    }
  ]
}
""").strip()


def _step2_review(constructs: list, llm) -> dict:
    const_block = json.dumps({"constructs": constructs}, ensure_ascii=False, indent=2)
    prompt = f"Review these draft constructs:\n\n{const_block}"
    response = llm.invoke([HumanMessage(content=f"{_STEP2_SYSTEM}\n\n---\n\n{prompt}")])
    text = response.content.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    return json.loads(text)


# ---------------------------------------------------------------------------
# Step 3: Variable strategy
# ---------------------------------------------------------------------------

_STEP3_SYSTEM = textwrap.dedent("""
You are a psychometrician finalizing a measurement strategy for WVS constructs.

For each construct, determine:
1. construct_type:
   - "reflective_scale"  — items are interchangeable reflections of a latent trait (use mean + alpha)
   - "formative_index"   — items combine additively to form a composite (e.g. count of memberships)
   - "single_item_tier2" — only one item remains after review
2. gateway_items: items that act as routing filters (e.g. "Do you belong to a religion?")
   that gate access to sub-batteries. These should NOT be averaged into the scale but noted.
3. Confirm reverse_coded_items: items where high score = low construct level.

OUTPUT: Valid JSON only.
Schema:
{
  "final_constructs": [
    {
      "name": "snake_case_name",
      "description": "...",
      "construct_type": "reflective_scale" | "formative_index" | "single_item_tier2",
      "question_cluster": ["Q1", "Q2"],
      "reverse_coded_items": ["Q2"],
      "gateway_items": [],
      "validated_index": "...",
      "notes": "..."
    }
  ]
}
""").strip()


def _step3_strategy(constructs_step2: list, review: list, llm) -> dict:
    combined = []
    review_by_name = {r["construct_name"]: r for r in review}
    for c in constructs_step2:
        r = review_by_name.get(c["name"], {})
        items = [i for i in c["items"] if i not in r.get("items_to_drop", [])]
        combined.append({
            "name": c["name"],
            "description": c["description"],
            "items": items,
            "reverse_coded_items": c.get("reverse_coded_items", []),
            "validated_index": c.get("validated_index"),
            "coherence": r.get("coherence", "?"),
        })

    prompt = f"Finalize variable strategy for these constructs:\n\n{json.dumps({'constructs': combined}, ensure_ascii=False, indent=2)}"
    response = llm.invoke([HumanMessage(content=f"{_STEP3_SYSTEM}\n\n---\n\n{prompt}")])
    text = response.content.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    return json.loads(text)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _cache_path(domain: str, step: int) -> Path:
    return CACHE_DIR / f"{domain}_step{step}.json"


def _load_cache(domain: str, step: int):
    p = _cache_path(domain, step)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return None


def _save_cache(domain: str, step: int, data: dict) -> None:
    with open(_cache_path(domain, step), "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Per-domain pipeline
# ---------------------------------------------------------------------------

def _process_domain(
    domain_prefix: str,
    domain_label: str,
    items: List[dict],
    llm,
    resume: bool,
    log_lines: List[str],
) -> dict:
    # Filter low-N items
    filtered = [x for x in items if x["n_pct_valid"] >= MIN_N_VALID_PCT]
    excluded_low_n = [x["qcode"] for x in items if x["n_pct_valid"] < MIN_N_VALID_PCT]
    if excluded_low_n:
        log_lines.append(f"  [{domain_prefix}] Low-N excluded: {excluded_low_n}")

    if len(filtered) < 2:
        log_lines.append(f"  [{domain_prefix}] Skipped — fewer than 2 items after filtering")
        return {"constructs": [], "standalone_items": [x["qcode"] for x in filtered]}

    print(f"  {domain_prefix} ({domain_label[:30]}): {len(filtered)} items")

    # Step 1: Cluster
    s1 = _load_cache(domain_prefix, 1) if resume else None
    if s1 is None:
        print(f"    Step 1: clustering...")
        s1 = _step1_cluster(domain_prefix, domain_label, filtered, llm)
        _save_cache(domain_prefix, 1, s1)
    else:
        print(f"    Step 1: from cache")
    log_lines.append(f"\n[{domain_prefix}] Step 1:\n{json.dumps(s1, indent=2, ensure_ascii=False)}")

    # Step 2: Review
    s2 = _load_cache(domain_prefix, 2) if resume else None
    if s2 is None:
        print(f"    Step 2: research review...")
        s2 = _step2_review(s1.get("constructs", []), llm)
        _save_cache(domain_prefix, 2, s2)
    else:
        print(f"    Step 2: from cache")
    log_lines.append(f"\n[{domain_prefix}] Step 2:\n{json.dumps(s2, indent=2, ensure_ascii=False)}")

    # Step 3: Strategy
    s3 = _load_cache(domain_prefix, 3) if resume else None
    if s3 is None:
        print(f"    Step 3: variable strategy...")
        s3 = _step3_strategy(s1.get("constructs", []), s2.get("review", []), llm)
        _save_cache(domain_prefix, 3, s3)
    else:
        print(f"    Step 3: from cache")
    log_lines.append(f"\n[{domain_prefix}] Step 3:\n{json.dumps(s3, indent=2, ensure_ascii=False)}")

    return s3


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domains", nargs="*", help="Domain prefixes to process (e.g. A E F)")
    parser.add_argument("--no-resume", action="store_true", help="Ignore cache, re-run all")
    args = parser.parse_args()
    resume = not args.no_resume

    # Load inventory
    if not INVENTORY_PATH.exists():
        print(f"ERROR: {INVENTORY_PATH} not found. Run wvs_variable_inventory.py first.")
        sys.exit(1)

    with open(INVENTORY_PATH) as f:
        inventory = json.load(f)

    llm = _make_llm()
    log_lines: list[str] = []
    svs_domains: dict[str, Any] = {}

    for domain_prefix, dom_data in sorted(inventory["domains"].items()):
        if args.domains and domain_prefix not in args.domains:
            continue

        domain_label = dom_data["label"]
        items = dom_data["items"]

        try:
            result = _process_domain(
                domain_prefix, domain_label, items, llm, resume, log_lines
            )
        except Exception as e:
            print(f"  ERROR in {domain_prefix}: {e}")
            log_lines.append(f"\n[{domain_prefix}] ERROR: {e}")
            result = {"final_constructs": []}

        svs_domains[f"WVS_{domain_prefix}"] = {
            "survey_name": domain_label,
            "construct_clusters": result.get("final_constructs", []),
        }

    # Build final SVS JSON (same schema as semantic_variable_selection_v4.json)
    svs = {
        "version": "wvs_v1",
        "source": "WVS Wave 7 — Mexico (2018)",
        "model": MODEL,
        "domains": svs_domains,
    }

    with open(OUT_SVS, "w", encoding="utf-8") as f:
        json.dump(svs, f, ensure_ascii=False, indent=2)
    print(f"\nSVS: {OUT_SVS}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print(f"Log: {OUT_LOG}")

    # Summary
    n_constructs = sum(
        len(d.get("construct_clusters", []))
        for d in svs_domains.values()
    )
    print(f"\nTotal constructs: {n_constructs} across {len(svs_domains)} domains")
    print(f"\nReview {OUT_SVS} before running build_wvs_constructs.py")


if __name__ == "__main__":
    main()
