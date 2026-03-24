"""
Phase 1.2 — Build WVS ↔ los_mex construct cross-map

Maps WVS constructs to los_mex constructs via:
  (a) Name-based fuzzy matching (token overlap + semantic similarity)
  (b) SES fingerprint cosine similarity (once WVS fingerprints are computed)
  (c) Domain correspondence (WVS domains → los_mex domains)

This is a heuristic cross-map — no LLM calls needed.

Output:
  data/results/wvs_losmex_construct_map.json

Run:
  conda run -n nvg_py13_env python scripts/debug/build_wvs_losmex_construct_map.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

KG_PATH = ROOT / "data" / "results" / "kg_ontology_v2.json"
WVS_MANIFEST = ROOT / "data" / "results" / "wvs_multi_construct_manifest.json"
WVS_SVS = ROOT / "data" / "results" / "wvs_svs_v1.json"
OUTPUT = ROOT / "data" / "results" / "wvs_losmex_construct_map.json"

# Domain correspondence: WVS domain prefix → los_mex domain codes
# Based on conceptual overlap between WVS sections and los_mex survey domains
DOMAIN_MAP = {
    "WVS_A": ["IDE", "FAM", "VAL"],  # Social Values → Identity, Family, Values
    "WVS_B": ["MED"],                 # Environment → Media/Environment
    "WVS_C": ["ECO", "LAB"],          # Work → Economy, Labor
    "WVS_D": ["FAM", "GEN"],          # Family → Family, Gender
    "WVS_E": ["POL", "DEM", "FED", "PAR", "GOB"],  # Politics
    "WVS_F": ["REL", "VAL"],          # Religion → Religiosity, Values
    "WVS_G": ["IDE", "MIG"],          # National Identity → Identity, Migration
    "WVS_H": ["SEG", "VIC"],          # Security → Security, Victimization
    "WVS_I": ["CIE", "EDU"],          # Science/Tech → Science, Education
}


def _tokenize(name: str) -> set[str]:
    """Tokenize a construct name into lowercase words."""
    return set(re.findall(r'[a-z]+', name.lower()))


def _name_similarity(name_a: str, name_b: str) -> float:
    """Jaccard similarity between tokenized construct names."""
    tokens_a = _tokenize(name_a)
    tokens_b = _tokenize(name_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def main():
    # Load los_mex constructs from KG ontology
    with open(KG_PATH) as f:
        kg = json.load(f)
    lm_constructs = kg["constructs"]  # 93 constructs
    print(f"los_mex constructs: {len(lm_constructs)}")

    # Load WVS constructs from manifest
    with open(WVS_MANIFEST) as f:
        wvs_manifest = json.load(f)
    # Use WVS_W7_MEX as reference
    wvs_constructs = [m for m in wvs_manifest.get("WVS_W7_MEX", []) if m.get("column")]
    print(f"WVS constructs: {len(wvs_constructs)}")

    # Load WVS SVS for descriptions
    with open(WVS_SVS) as f:
        wvs_svs = json.load(f)
    # Build description lookup
    wvs_descriptions = {}
    for dom_key, dom_data in wvs_svs.get("domains", {}).items():
        for cluster in dom_data.get("construct_clusters", []):
            cname = cluster.get("name", "")
            domain_prefix = dom_key.replace("WVS_", "")
            key = f"WVS_{domain_prefix}|{cname}"
            wvs_descriptions[key] = cluster.get("description", "")

    # Build cross-map
    cross_map = []

    for wvs_c in wvs_constructs:
        wvs_key = wvs_c["key"]
        wvs_col = wvs_c["column"]
        wvs_domain = wvs_key.split("|")[0]  # e.g., WVS_A
        wvs_name = wvs_key.split("|")[1]    # e.g., social_intolerance_outgroups

        # Get candidate los_mex domains
        candidate_domains = DOMAIN_MAP.get(wvs_domain, [])

        # Score all los_mex constructs
        matches = []
        for lm_c in lm_constructs:
            lm_id = lm_c["id"]
            lm_domain = lm_c["domain"]
            lm_name = lm_id.split("__")[1] if "__" in lm_id else lm_id
            lm_col = lm_c["column"]

            # Name similarity
            name_sim = _name_similarity(wvs_name, lm_name)

            # Domain bonus: if los_mex domain matches expected correspondence
            domain_bonus = 0.15 if lm_domain in candidate_domains else 0.0

            # Combined score
            score = name_sim + domain_bonus

            if score > 0.1:  # minimum threshold
                matches.append({
                    "losmex_id": lm_id,
                    "losmex_col": lm_col,
                    "losmex_domain": lm_domain,
                    "name_similarity": round(name_sim, 3),
                    "domain_match": lm_domain in candidate_domains,
                    "score": round(score, 3),
                    "losmex_fingerprint": [
                        lm_c.get("rho_escol", 0),
                        lm_c.get("rho_Tam_loc", 0),
                        lm_c.get("rho_sexo", 0),
                        lm_c.get("rho_edad", 0),
                    ],
                    "losmex_ses_magnitude": lm_c.get("ses_magnitude", 0),
                })

        matches.sort(key=lambda x: -x["score"])
        top_matches = matches[:3]  # top 3 candidates

        entry = {
            "wvs_key": wvs_key,
            "wvs_col": wvs_col,
            "wvs_domain": wvs_domain,
            "wvs_description": wvs_descriptions.get(wvs_key, ""),
            "candidate_domains": candidate_domains,
            "matches": top_matches,
            "best_match": top_matches[0] if top_matches else None,
            "match_quality": _classify_match(top_matches),
        }
        cross_map.append(entry)

    # Summary
    quality_counts = {}
    for e in cross_map:
        q = e["match_quality"]
        quality_counts[q] = quality_counts.get(q, 0) + 1

    print(f"\nMatch quality distribution:")
    for q, n in sorted(quality_counts.items()):
        print(f"  {q}: {n}")

    # Show best matches
    print(f"\nTop matches (score >= 0.4):")
    for e in cross_map:
        if e["best_match"] and e["best_match"]["score"] >= 0.4:
            m = e["best_match"]
            print(f"  {e['wvs_key']} → {m['losmex_id']} (score={m['score']:.3f})")

    # Save
    output = {
        "version": "v1",
        "n_wvs_constructs": len(wvs_constructs),
        "n_losmex_constructs": len(lm_constructs),
        "quality_summary": quality_counts,
        "domain_correspondence": DOMAIN_MAP,
        "mappings": cross_map,
    }
    with open(OUTPUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {OUTPUT}")


def _classify_match(matches: list[dict]) -> str:
    """Classify match quality based on top scores."""
    if not matches:
        return "no_match"
    top = matches[0]["score"]
    if top >= 0.5:
        return "strong"
    if top >= 0.3:
        return "moderate"
    if top >= 0.15:
        return "weak"
    return "no_match"


if __name__ == "__main__":
    main()
