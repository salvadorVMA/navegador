"""
Phase 0: Rebuild kg_ontology from v4 manifest constructs.

The original kg_ontology.json used early-pass, generic construct names
(e.g. SEG__perceived_threats, SOC__digital_access) that no longer match
the canonical v4 constructs from the DR sweep.

This script:
  1. Keeps the 24-domain structure and domain labels from the original KG.
  2. Replaces all construct nodes with the 93 v4 manifest constructs.
  3. Fuzzy-matches old relationships to new constructs using Jaccard token
     similarity; high-confidence matches are preserved, low-confidence ones
     are archived in `legacy_unresolved` for future LLM re-annotation.

Output: data/results/kg_ontology_v2.json

Usage:
    python scripts/debug/rebuild_kg_ontology.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

KG_PATH      = ROOT / "data" / "kg_ontology.json"
MANIFEST_PATH = ROOT / "data" / "results" / "construct_variable_manifest.json"
OUTPUT_PATH  = ROOT / "data" / "results" / "kg_ontology_v2.json"

# Jaccard threshold: above → keep as matched, below → archive as unresolved
MATCH_THRESHOLD = 0.20


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

_STOP = {"and", "or", "of", "the", "in", "to", "a", "an", "with", "for",
         "by", "on", "at", "from", "toward", "toward", "toward", "s"}

def _tokens(text: str) -> set:
    """Lower-case, split on underscores/spaces, drop stopwords."""
    raw = re.split(r"[_\s\-]+", text.lower())
    return {t for t in raw if t and t not in _STOP}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _best_match(
    old_id: str,
    new_constructs_by_domain: Dict[str, List[Dict]],
) -> Tuple[Optional[str], float]:
    """Find the new construct ID with highest Jaccard to old_id within same domain."""
    parts = old_id.split("__", 1)
    if len(parts) != 2:
        return None, 0.0
    domain, old_name = parts[0], parts[1]
    candidates = new_constructs_by_domain.get(domain, [])
    if not candidates:
        return None, 0.0

    old_tokens = _tokens(old_name)
    best_id, best_score = None, 0.0
    for c in candidates:
        score = _jaccard(old_tokens, _tokens(c["name"]))
        if score > best_score:
            best_score = score
            best_id = c["id"]
    return best_id, best_score


# ─────────────────────────────────────────────────────────────
# Domain label enrichment (from original KG)
# ─────────────────────────────────────────────────────────────

_DOMAIN_LABEL_OVERRIDES: Dict[str, str] = {
    "ENV": "envejecimiento (aging)",  # avoid confusion with environment
}


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def rebuild(
    kg_path: Path = KG_PATH,
    manifest_path: Path = MANIFEST_PATH,
    output_path: Path = OUTPUT_PATH,
    threshold: float = MATCH_THRESHOLD,
) -> dict:
    # ── Load inputs ──────────────────────────────────────────
    with open(kg_path) as f:
        old_kg = json.load(f)
    with open(manifest_path) as f:
        manifest = json.load(f)

    domain_labels: Dict[str, str] = {
        d["id"]: d["label"] for d in old_kg.get("domains", [])
    }

    # ── Build new construct nodes from manifest ──────────────
    new_constructs: List[Dict] = []
    new_by_domain: Dict[str, List[Dict]] = {}
    new_id_set: set = set()

    for entry in manifest:
        if not entry.get("column"):         # excluded / no_columns / etc.
            continue
        key = entry["key"]                  # e.g. "CIE|institutional_trust_in_science"
        parts = key.split("|", 1)
        if len(parts) != 2:
            continue
        domain, name = parts

        # Human-readable label: replace underscores with spaces, title-case
        label = name.replace("_", " ").title()

        new_id = f"{domain}__{name}"        # mirror old DOMAIN__name convention
        construct = {
            "id":       new_id,
            "label":    label,
            "domain":   domain,
            # v4 measurement metadata
            "manifest_key":  key,
            "column":        entry.get("column"),
            "type":          entry.get("type"),
            "alpha":         entry.get("alpha"),
            "n_items":       entry.get("n_items"),
            "n_valid":       entry.get("n_valid"),
        }
        new_constructs.append(construct)
        new_id_set.add(new_id)
        new_by_domain.setdefault(domain, []).append({"id": new_id, "name": name})

    # ── Match old relationships to new construct IDs ──────────
    old_rels = old_kg.get("relationships", [])
    matched_rels: List[Dict] = []
    unresolved: List[Dict] = []

    for rel in old_rels:
        src_old = rel.get("from", "")
        tgt_old = rel.get("to", "")

        src_new, src_score = _best_match(src_old, new_by_domain)
        tgt_new, tgt_score = _best_match(tgt_old, new_by_domain)

        min_score = min(src_score, tgt_score)
        annotation = {
            "from":         src_new or src_old,
            "to":           tgt_new or tgt_old,
            "type":         rel.get("type"),
            "evidence":     rel.get("evidence"),
            "strength":     rel.get("strength"),
            # provenance
            "_legacy_from": src_old,
            "_legacy_to":   tgt_old,
            "_match_score": round(min_score, 3),
        }

        if (src_new and tgt_new and min_score >= threshold
                and src_new != tgt_new):
            matched_rels.append(annotation)
        else:
            annotation["_reason"] = (
                "no_domain_candidates" if not src_new or not tgt_new
                else f"low_jaccard ({min_score:.2f} < {threshold})"
            )
            unresolved.append(annotation)

    # ── Assemble new KG ───────────────────────────────────────
    new_kg = {
        "version": "v2",
        "description": (
            "Ontology rebuilt from v4 manifest constructs (2026-03-17). "
            "Relationships fuzzy-matched from v1 (threshold=%.2f). "
            "Unresolved legacy relationships in legacy_unresolved." % threshold
        ),
        "domains": [
            {
                "id":    d["id"],
                "label": _DOMAIN_LABEL_OVERRIDES.get(d["id"], d["label"]),
            }
            for d in old_kg.get("domains", [])
        ],
        "constructs":          new_constructs,
        "relationships":       matched_rels,
        "legacy_unresolved":   unresolved,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(new_kg, f, indent=2, ensure_ascii=False)

    # ── Summary ───────────────────────────────────────────────
    domains_with_constructs = len(new_by_domain)
    print(f"\n═══ kg_ontology_v2 rebuild summary ═══")
    print(f"  Domains:            {len(new_kg['domains'])} total  "
          f"({domains_with_constructs} with v4 constructs)")
    print(f"  New constructs:     {len(new_constructs)}")
    print(f"  Relationships:      {len(old_rels)} old  →  "
          f"{len(matched_rels)} matched  +  {len(unresolved)} unresolved")
    print(f"\n  Per-domain constructs:")
    for domain in sorted(new_by_domain):
        label = domain_labels.get(domain, "")
        n = len(new_by_domain[domain])
        print(f"    {domain:5s} ({label[:35]:35s}): {n}")

    print(f"\n  Match score distribution (matched):")
    if matched_rels:
        scores = [r["_match_score"] for r in matched_rels]
        print(f"    min={min(scores):.2f}  median={sorted(scores)[len(scores)//2]:.2f}"
              f"  max={max(scores):.2f}")

    print(f"\n  Unresolved by reason:")
    reasons: Dict[str, int] = {}
    for r in unresolved:
        reasons[r.get("_reason", "?")] = reasons.get(r.get("_reason", "?"), 0) + 1
    for reason, n in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"    {reason}: {n}")

    print(f"\n  Output: {output_path}")
    return new_kg


if __name__ == "__main__":
    rebuild()
