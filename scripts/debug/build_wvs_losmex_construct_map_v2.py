"""
Phase 1.2 v2 — LLM-based WVS <-> los_mex construct cross-map

Replaces the v1 Jaccard-token and TF-IDF heuristics with LLM semantic grading:
  Stage 1: LLM semantic grading (0-3 scale, same as anchor discovery)
           Each WVS construct is compared against ALL los_mex constructs.
           The LLM sees full descriptions and SES fingerprints.
  Stage 2: For grade 2-3 matches, the LLM also identifies structural
           divergence risks explaining why gamma patterns may differ.

Grading scale (matches wvs_anchor_discovery.py):
  3 = near-identical concept, directly comparable
  2 = same broad concept, different operationalization or emphasis
  1 = weak thematic overlap, not interchangeable
  0 = unrelated

Output:
  data/results/wvs_losmex_construct_map_v2.json

Run:
  python scripts/debug/build_wvs_losmex_construct_map_v2.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

import anthropic

KG_PATH = ROOT / "data" / "results" / "kg_ontology_v2.json"
WVS_MANIFEST = ROOT / "data" / "results" / "wvs_construct_manifest.json"
WVS_SVS = ROOT / "data" / "results" / "wvs_svs_v1.json"
LM_SVS = ROOT / "data" / "results" / "semantic_variable_selection_v4.json"
SES_FP = ROOT / "data" / "results" / "ses_fingerprints.json"
OUTPUT = ROOT / "data" / "results" / "wvs_losmex_construct_map_v2.json"
CACHE_DIR = ROOT / "data" / "results" / ".construct_map_v2_cache"

MODEL = "claude-sonnet-4-20250514"


def _call_llm(prompt: str, max_tokens: int = 4096, temperature: float = 0.2) -> str:
    """Call Anthropic Claude API."""
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _parse_json(text: str):
    """Extract JSON from LLM response."""
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
    for pat in (r"(\[[\s\S]+\])", r"(\{[\s\S]+\})"):
        m = re.search(pat, text)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    raise ValueError(f"Could not parse JSON from response: {text[:200]}")


def _load_cache(wvs_key: str) -> list | None:
    """Load cached LLM result for a WVS construct."""
    cache_file = CACHE_DIR / f"{wvs_key.replace('|', '_')}.json"
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    return None


def _save_cache(wvs_key: str, result: list):
    """Save LLM result to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{wvs_key.replace('|', '_')}.json"
    with open(cache_file, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def _build_candidate_block(lm_constructs: list[dict], lm_descriptions: dict) -> str:
    """Build text block describing ALL los_mex constructs."""
    lines = []
    for c in lm_constructs:
        dom = c["domain"]
        cid = c["id"]
        name = cid.split("__")[1] if "__" in cid else cid
        desc = lm_descriptions.get(f"{dom}|{name}", "")
        fp = [c.get("rho_escol", 0), c.get("rho_Tam_loc", 0),
              c.get("rho_sexo", 0), c.get("rho_edad", 0)]
        mag = c.get("ses_magnitude", 0)
        lines.append(
            f"- **{cid}** (domain: {dom})\n"
            f"  {desc[:200]}\n"
            f"  SES: escol={fp[0]:.3f}, Tam_loc={fp[1]:.3f}, "
            f"sexo={fp[2]:.3f}, edad={fp[3]:.3f} (mag={mag:.3f})"
        )
    return "\n".join(lines)


def grade_construct(wvs_key: str, wvs_desc: str, wvs_items_desc: str,
                    candidate_block: str) -> list[dict]:
    """Use LLM to grade semantic matches between a WVS construct and los_mex candidates."""

    prompt = f"""You are an expert in comparative survey methodology, specializing in cross-national
survey harmonization (WVS, ISSP, ESS, Latinobarometro, los_mex/ENCUP/ENVIPE).

## Task

Grade each los_mex construct below against this WVS construct. Assess **conceptual equivalence** —
whether they measure the same underlying attitude, belief, or behavioral disposition, even if they
use different questions, scales, or wording.

## WVS Construct

**{wvs_key}**
Description: {wvs_desc}
Items: {wvs_items_desc}

## los_mex Constructs (93 total)

{candidate_block}

## Grading Scale (0-3)

- **3 = Near-identical**: Same latent concept, directly comparable. Questions tap the same attitude
  dimension with equivalent or near-equivalent intent. Example: "confidence in parliament" (WVS)
  vs "institutional trust in Congress" (los_mex).
- **2 = Same concept, different operationalization**: Same broad psychological or sociological
  construct, but different emphasis, scope, or item composition. Expected correlation r > 0.5
  in a joint sample. Example: "social intolerance toward outgroups" (WVS, neighbor rejection)
  vs "tolerance of social diversity" (los_mex, acceptance of minorities).
- **1 = Thematic overlap**: Related topic or domain, but constructs capture different facets.
  Low expected correlation. Example: "democratic values importance" vs "perceived representativeness."
- **0 = Unrelated**: No meaningful conceptual connection.

## Critical distinctions

- **Opposite poles count as grade 2-3** (e.g., "intolerance" vs "tolerance" = same dimension,
  reversed polarity).
- **Same domain != same construct**: "fear of crime" vs "support for surveillance" are both
  "security" but measure different things.
- **Behavioral vs attitudinal**: "voting participation" (behavior) and "democratic values"
  (attitude) are grade 1 at best.
- **Read descriptions carefully** — labels can be misleading.

## For grade 2-3 matches: divergence risk analysis

Explain WHY these constructs might produce DIFFERENT gamma (SES-bridge) patterns despite measuring
related concepts. Consider:
- **Item composition**: Different breadth, response format (binary vs Likert), number of items
- **Population/fielding**: WVS Mexico 2018 (n=1741) vs los_mex specific survey (n~1200, different year)
- **Scale mechanics**: Binary pick-5 (WVS child qualities) vs ordinal Likert; aggregation method
- **Construct breadth**: One broad umbrella vs narrow facet
- **Cultural framing**: WVS questions translated/adapted for global use vs los_mex designed for Mexico
- **Temporal gap**: WVS 2018 vs los_mex survey year (2008-2019 depending on domain)

## Output

Return a JSON array containing ONLY candidates with grade >= 1:
```json
[
  {{
    "losmex_id": "DOMAIN__construct_name",
    "grade": 3,
    "rationale": "Brief explanation of conceptual match",
    "polarity": "same" or "reversed",
    "divergence_risks": ["risk 1", "risk 2", ...]
  }}
]
```

Order by grade descending, then by strength of match. If nothing reaches grade 1, return `[]`.
Be selective — most pairs are grade 0. Typical: 0-3 grade-3, 2-8 grade-2, 5-15 grade-1."""

    cached = _load_cache(wvs_key)
    if cached is not None:
        return cached

    response = _call_llm(prompt)
    try:
        result = _parse_json(response)
    except ValueError:
        print(f"  WARN: Could not parse LLM response for {wvs_key}")
        result = []

    _save_cache(wvs_key, result)
    return result


def main():
    # -- Load data ---------------------------------------------------------
    with open(KG_PATH) as f:
        kg = json.load(f)
    lm_constructs = kg["constructs"]

    with open(WVS_MANIFEST) as f:
        wvs_manifest = json.load(f)

    with open(WVS_SVS) as f:
        wvs_svs = json.load(f)

    with open(LM_SVS) as f:
        lm_svs = json.load(f)

    # Build WVS description + items lookup
    wvs_info = {}
    for dom_key, dom_data in wvs_svs["domains"].items():
        for cluster in dom_data.get("construct_clusters", []):
            key = f"{dom_key}|{cluster['name']}"
            wvs_info[key] = {
                "description": cluster.get("description", ""),
                "items": cluster.get("question_cluster", []),
                "notes": cluster.get("notes", ""),
                "construct_type": cluster.get("construct_type", ""),
                "validated_index": cluster.get("validated_index"),
            }

    # Build los_mex description lookup
    lm_descriptions = {}
    for dom_key, dom_data in lm_svs.get("domains", {}).items():
        for cluster in dom_data.get("construct_clusters", []):
            name = cluster["name"]
            lm_descriptions[f"{dom_key}|{name}"] = cluster.get("description", "")

    # Load SES fingerprints for enrichment
    ses_fp = {}
    if SES_FP.exists():
        with open(SES_FP) as f:
            fp_data = json.load(f)
        ses_fp = fp_data.get("constructs", {})

    # Enrich lm_constructs with fingerprints
    for c in lm_constructs:
        cid = c["id"]
        dom = c["domain"]
        name = cid.split("__")[1] if "__" in cid else cid
        fp_key = f"{dom}|{name}"
        if fp_key in ses_fp:
            for k in ("rho_escol", "rho_Tam_loc", "rho_sexo", "rho_edad",
                       "ses_magnitude", "dominant_dim"):
                c[k] = ses_fp[fp_key].get(k, 0)

    print(f"WVS constructs: {len(wvs_manifest)}")
    print(f"los_mex constructs: {len(lm_constructs)}")
    print(f"LLM model: {MODEL}")
    print()

    # Build candidate block once (all los_mex constructs)
    candidate_block = _build_candidate_block(lm_constructs, lm_descriptions)

    # -- Grade each WVS construct -----------------------------------------
    cross_map = []
    total_api_calls = 0

    for wvs_c in wvs_manifest:
        wvs_key = wvs_c["key"]
        wvs_col = wvs_c["column"]
        wvs_domain = wvs_key.split("|")[0]

        info = wvs_info.get(wvs_key, {})
        wvs_desc = info.get("description", "")
        wvs_notes = info.get("notes", "")
        wvs_items = info.get("items", [])
        wvs_ctype = info.get("construct_type", "")
        wvs_validated = info.get("validated_index")

        # Build items description
        items_desc = f"{len(wvs_items)} items: {', '.join(wvs_items[:8])}"
        if len(wvs_items) > 8:
            items_desc += f"... ({len(wvs_items)} total)"
        if wvs_validated:
            items_desc += f" (validated index: {wvs_validated})"
        if wvs_ctype:
            items_desc += f" [{wvs_ctype}]"
        if wvs_notes:
            items_desc += f"\nNotes: {wvs_notes[:300]}"

        # Check cache first
        cached = _load_cache(wvs_key)
        if cached is not None:
            print(f"  [cached] {wvs_key} -> {len(cached)} matches")
            matches = cached
        else:
            print(f"  [LLM] {wvs_key} ...", end="", flush=True)
            matches = grade_construct(wvs_key, wvs_desc, items_desc, candidate_block)
            total_api_calls += 1
            print(f" -> {len(matches)} matches")
            time.sleep(0.3)

        # Sort by grade
        matches = sorted(matches, key=lambda x: -x.get("grade", 0))

        # Classify
        top_grade = max((m.get("grade", 0) for m in matches), default=0)

        entry = {
            "wvs_key": wvs_key,
            "wvs_col": wvs_col,
            "wvs_domain": wvs_domain,
            "wvs_description": wvs_desc,
            "wvs_construct_type": wvs_ctype,
            "matches": matches,
            "best_match": matches[0] if matches else None,
            "match_quality": _classify_grade(top_grade),
        }
        cross_map.append(entry)

    # -- Summary -----------------------------------------------------------
    quality_counts = {}
    for e in cross_map:
        q = e["match_quality"]
        quality_counts[q] = quality_counts.get(q, 0) + 1

    print(f"\n{'='*60}")
    print(f"Match quality distribution (v2, LLM-based):")
    for q in ["near_identical", "same_concept", "thematic_only", "no_match"]:
        print(f"  {q}: {quality_counts.get(q, 0)}")

    # Collect divergence risks across all grade 2-3 matches
    all_risks = {}
    n_grade3 = 0
    n_grade2 = 0

    print(f"\nGrade-3 matches (near-identical):")
    for e in cross_map:
        for m in e.get("matches", []):
            if m.get("grade") == 3:
                n_grade3 += 1
                pol = m.get("polarity", "?")
                risks = m.get("divergence_risks", [])
                for r in risks:
                    all_risks[r] = all_risks.get(r, 0) + 1
                print(f"  {e['wvs_key']} -> {m['losmex_id']} [{pol}]")
                print(f"    {m.get('rationale', '')[:100]}")
                if risks:
                    print(f"    Risks: {'; '.join(risks[:3])}")

    print(f"\nGrade-2 matches (same concept, different operationalization):")
    for e in cross_map:
        for m in e.get("matches", []):
            if m.get("grade") == 2:
                n_grade2 += 1
                risks = m.get("divergence_risks", [])
                for r in risks:
                    all_risks[r] = all_risks.get(r, 0) + 1
                print(f"  {e['wvs_key']} -> {m['losmex_id']}")
                print(f"    {m.get('rationale', '')[:100]}")

    print(f"\nDivergence risk frequency (across {n_grade3} grade-3 + {n_grade2} grade-2 matches):")
    for risk, count in sorted(all_risks.items(), key=lambda x: -x[1])[:15]:
        print(f"  [{count}x] {risk[:100]}")

    print(f"\nAPI calls made: {total_api_calls}")

    # -- Save --------------------------------------------------------------
    output = {
        "version": "v2",
        "method": f"LLM semantic grading ({MODEL})",
        "grading_scale": {
            "3": "near-identical concept, directly comparable",
            "2": "same concept, different operationalization",
            "1": "thematic overlap only",
            "0": "unrelated",
        },
        "n_wvs_constructs": len(wvs_manifest),
        "n_losmex_constructs": len(lm_constructs),
        "quality_summary": quality_counts,
        "divergence_risk_frequency": dict(sorted(all_risks.items(), key=lambda x: -x[1])),
        "mappings": cross_map,
    }
    with open(OUTPUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {OUTPUT}")


def _classify_grade(top_grade: int) -> str:
    if top_grade >= 3:
        return "near_identical"
    if top_grade >= 2:
        return "same_concept"
    if top_grade >= 1:
        return "thematic_only"
    return "no_match"


if __name__ == "__main__":
    main()
