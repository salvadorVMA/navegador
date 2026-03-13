"""
Stream 2 — Recode Audit

For all constructs (not just flagged ones), print side-by-side:
  - Each item's answer codes and labels from the survey dictionary
  - Current reverse-coded status from SVS v4
  - Auto-flags: scale mismatch, potential direction reversal needed, n-categories mismatch

Output: data/results/construct_code_audit.md
Run:    python scripts/debug/audit_construct_codes.py

Flags:
  [DIR?]    Scale direction may need reversal relative to construct name
            (e.g., "1=strongly disagree" on a positive-framing construct)
  [SCALE?]  Item has different number of valid categories than other items in construct
  [NOMINAL] Item appears to have nominal (non-ordinal) codes
  [SPARSE]  Item has >30% missing after sentinel removal
  [R]       Currently flagged as reverse-coded in SVS v4
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "results" / "construct_code_audit.md"

# Keywords suggesting positive direction (higher code = more of construct)
_POSITIVE_KW = re.compile(
    r"(muy de acuerdo|totalmente|siempre|mucho|completamente|muy bueno|excelente"
    r"|totalmente de acuerdo|bastante|casi siempre|frecuentemente|muy frecuente"
    r"|confía mucho|muy confiado|muy seguro|muy satisfecho|muy importante)",
    re.IGNORECASE,
)
# Keywords suggesting negative direction (higher code = LESS of construct)
_NEGATIVE_KW = re.compile(
    r"(muy en desacuerdo|nunca|nada|muy malo|muy insatisfecho|para nada"
    r"|muy poco|casi nunca|nada de acuerdo|desacuerdo|no confía|muy inseguro)",
    re.IGNORECASE,
)


def _is_sentinel(v: float) -> bool:
    return v >= 97 or v < 0


def _parse_codes(raw: dict) -> dict[float, str]:
    """Convert {str_code: label} to {float_code: label}, excluding sentinels."""
    result = {}
    for k, v in raw.items():
        try:
            code = float(k)
            if not _is_sentinel(code):
                result[code] = str(v).strip()
        except (ValueError, TypeError):
            pass
    return result


def _infer_direction(codes: dict[float, str]) -> Optional[str]:
    """
    Guess if the scale's highest numeric code = positive or negative meaning.
    Returns 'positive', 'negative', or None (ambiguous/nominal).
    """
    if not codes:
        return None
    sorted_codes = sorted(codes.keys())
    if len(sorted_codes) < 2:
        return None
    lowest_label = codes[sorted_codes[0]].lower()
    highest_label = codes[sorted_codes[-1]].lower()

    # Check highest code label
    if _POSITIVE_KW.search(highest_label):
        return "positive"
    if _NEGATIVE_KW.search(highest_label):
        return "negative"
    # Check lowest code label (reverse inference)
    if _POSITIVE_KW.search(lowest_label):
        return "negative"   # lowest=positive → highest=negative
    if _NEGATIVE_KW.search(lowest_label):
        return "positive"
    return None


def _is_ordinal(codes: dict[float, str]) -> bool:
    """Heuristic: if codes are sequential integers, likely ordinal."""
    if not codes:
        return False
    sorted_keys = sorted(codes.keys())
    if len(sorted_keys) <= 1:
        return True
    gaps = [sorted_keys[i+1] - sorted_keys[i] for i in range(len(sorted_keys)-1)]
    return all(g == 1 for g in gaps)


def format_codes(codes: dict[float, str]) -> str:
    if not codes:
        return "_(no codes found)_"
    parts = [f"{int(k) if k == int(k) else k}={v}" for k, v in sorted(codes.items())]
    return " | ".join(parts)


def load_svs_reverse(svs: dict) -> dict[str, list[str]]:
    """Return {domain|construct: [reverse_coded_items]} from SVS v4."""
    result: dict[str, list[str]] = {}
    for domain, dom_data in svs.get("domains", {}).items():
        for cluster in dom_data.get("construct_clusters", []):
            key = f"{domain}|{cluster['name']}"
            rev = cluster.get("reverse_coded_items", []) or []
            result[key] = [r.split("|")[0] for r in rev]
    return result


def load_svs_items(svs: dict) -> dict[str, list[str]]:
    """Return {domain|construct: [item_codes_without_domain_suffix]}."""
    result: dict[str, list[str]] = {}
    for domain, dom_data in svs.get("domains", {}).items():
        for cluster in dom_data.get("construct_clusters", []):
            key = f"{domain}|{cluster['name']}"
            raw = cluster.get("question_cluster", [])
            gateway = cluster.get("gateway_items", []) or []
            all_items = raw + [g for g in gateway if g not in raw]
            result[key] = [q.split("|")[0] for q in all_items]
    return result


def load_svs_construct_type(svs: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for domain, dom_data in svs.get("domains", {}).items():
        for cluster in dom_data.get("construct_clusters", []):
            key = f"{domain}|{cluster['name']}"
            result[key] = cluster.get("construct_type", "reflective_scale")
    return result


def main():
    print("Loading survey dictionary (this takes ~10-15s)...")
    from dataset_knowledge import enc_dict, enc_nom_dict

    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    svs_path = ROOT / "data" / "results" / "semantic_variable_selection_v4.json"
    manifest_path = ROOT / "data" / "results" / "construct_variable_manifest.json"

    with open(svs_path) as f:
        svs = json.load(f)
    with open(manifest_path) as f:
        manifest_list = json.load(f)

    manifest = {m["key"]: m for m in manifest_list if m.get("key")}
    svs_items = load_svs_items(svs)
    svs_reverse = load_svs_reverse(svs)
    svs_ctype = load_svs_construct_type(svs)

    print(f"  {len(manifest)} constructs in manifest")

    out_lines: list[str] = []
    out_lines.append("# Construct Code Audit — Stream 2\n\n")
    out_lines.append(
        "Side-by-side comparison of answer codes for every item in every construct. "
        "Flags: **[DIR?]** direction reversal may be needed, **[SCALE?]** n-categories mismatch, "
        "**[NOMINAL]** non-ordinal codes, **[SPARSE]** >30% missing, **[R]** currently reverse-coded in SVS v4.\n\n"
    )
    out_lines.append("---\n\n")

    # Process all constructs in manifest order, sorted by alpha descending
    sorted_keys = sorted(
        manifest.keys(),
        key=lambda k: (manifest[k].get("alpha") or -99),
        reverse=True,
    )

    for i, ckey in enumerate(sorted_keys, 1):
        m = manifest[ckey]
        domain = ckey.split("|")[0]
        survey_name = enc_nom_dict_rev.get(domain)
        alpha = m.get("alpha")
        alpha_str = f"{alpha:.4f}" if alpha is not None else "N/A"
        ctype = m.get("type", "?")
        construct_type = svs_ctype.get(ckey, "reflective_scale")
        items = svs_items.get(ckey, [])
        reverse_list = svs_reverse.get(ckey, [])

        out_lines.append(f"## [{i:02d}] {ckey}  (α={alpha_str}, {ctype})\n\n")

        if not survey_name or survey_name not in enc_dict:
            out_lines.append(f"_Survey `{survey_name}` not found for domain {domain}_\n\n---\n\n")
            print(f"  [{i:02d}] {ckey} — survey not found")
            continue

        if not items:
            out_lines.append("_No items found in SVS v4_\n\n---\n\n")
            print(f"  [{i:02d}] {ckey} — no items in SVS")
            continue

        metadata = enc_dict[survey_name].get("metadata", {})
        vvl = metadata.get("variable_value_labels", {})
        df = enc_dict[survey_name].get("dataframe")
        n_rows = len(df) if isinstance(df, pd.DataFrame) else None

        construct_flags: list[str] = []
        item_reports: list[str] = []
        n_cats_per_item: list[int] = []
        directions: list[Optional[str]] = []

        for item in items:
            item_flags: list[str] = []
            raw_codes = vvl.get(item, {})
            codes = _parse_codes(raw_codes)
            n_cats = len(codes)
            n_cats_per_item.append(n_cats)

            is_rev = item in reverse_list
            direction = _infer_direction(codes)
            directions.append(direction)
            is_ord = _is_ordinal(codes) if codes else None

            if is_rev:
                item_flags.append("[R]")

            # Sparsity check
            if isinstance(df, pd.DataFrame) and item in df.columns and n_rows:
                s = pd.to_numeric(df[item], errors="coerce")
                s = s.where(~s.apply(lambda v: _is_sentinel(v) if pd.notna(v) else False))
                pct_miss = s.isna().sum() / n_rows
                if pct_miss > 0.30:
                    item_flags.append(f"[SPARSE {pct_miss:.0%}]")

            if is_ord is False:
                item_flags.append("[NOMINAL]")

            flag_str = "  " + " ".join(item_flags) if item_flags else ""
            code_str = format_codes(codes)
            dir_str = f" → direction: **{direction}**" if direction else " → direction: _ambiguous_"
            item_reports.append(
                f"- `{item}`{flag_str}\n"
                f"  {code_str}{dir_str}\n"
            )

        # Cross-item flags
        if len(set(n_cats_per_item)) > 1 and len(n_cats_per_item) > 1:
            construct_flags.append(f"**[SCALE?]** Items have different n-categories: {n_cats_per_item}")

        # Direction consistency
        valid_dirs = [d for d in directions if d is not None]
        if len(valid_dirs) >= 2:
            if len(set(valid_dirs)) > 1:
                construct_flags.append(
                    "**[DIR?]** Items have inconsistent inferred directions: "
                    + str(list(zip(items, directions)))
                )

        if construct_flags:
            for flag in construct_flags:
                out_lines.append(f"> {flag}\n\n")
        else:
            out_lines.append("> ✓ No automatic flags\n\n")

        out_lines.append(f"Construct type: `{construct_type}` | Reverse-coded items in SVS v4: "
                         f"`{reverse_list if reverse_list else 'none'}`\n\n")
        out_lines.extend(item_reports)
        out_lines.append("\n---\n\n")
        print(f"  [{i:02d}] {ckey} done  flags={construct_flags[:1] or 'none'}")

    with open(OUT, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
    print(f"\nDone — written to {OUT}")


if __name__ == "__main__":
    main()
