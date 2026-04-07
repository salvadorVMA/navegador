#!/usr/bin/env python3
"""
Phase 0c: Build WVS construct description corpus for semantic search.

Extracts construct metadata from wvs_losmex_construct_map_v2.json and
enriches with domain labels from wvs_metadata.py.

Output: data/gte/construct_descriptions.json
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import DOMAIN_MAP  # noqa: E402

MAP_PATH = ROOT / "data" / "results" / "wvs_losmex_construct_map_v2.json"
OUT_PATH = ROOT / "data" / "gte" / "construct_descriptions.json"


def main():
    with open(MAP_PATH) as f:
        data = json.load(f)

    corpus = {}
    for entry in data["mappings"]:
        # Parse key: "WVS_A|importance_of_life_domains" → domain + name
        wvs_key = entry["wvs_key"]
        parts = wvs_key.split("|", 1)
        domain_code = parts[0] if len(parts) == 2 else entry.get("wvs_domain", "")
        construct_name = parts[1] if len(parts) == 2 else wvs_key

        # Canonical key matches manifest format: "name|domain"
        # Manifest uses: "gender_role_traditionalism|WVS_D"
        canonical_key = f"{construct_name}|{domain_code}"

        domain_label = DOMAIN_MAP.get(domain_code.replace("WVS_", ""), domain_code)

        # Human-readable label from snake_case
        label = construct_name.replace("_", " ").title()

        corpus[canonical_key] = {
            "key": canonical_key,
            "name": construct_name,
            "label": label,
            "description": entry.get("wvs_description", ""),
            "domain_code": domain_code,
            "domain_label": domain_label,
            "construct_type": entry.get("wvs_construct_type", ""),
            "agg_column": entry.get("wvs_col", f"wvs_agg_{construct_name}"),
        }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump({
            "n_constructs": len(corpus),
            "constructs": corpus,
        }, f, indent=2)

    print(f"Built corpus: {len(corpus)} constructs → {OUT_PATH}")

    # Print domain distribution
    from collections import Counter
    domains = Counter(c["domain_code"] for c in corpus.values())
    for d, n in sorted(domains.items()):
        print(f"  {d}: {n} constructs ({DOMAIN_MAP.get(d.replace('WVS_', ''), d)})")


if __name__ == "__main__":
    main()
