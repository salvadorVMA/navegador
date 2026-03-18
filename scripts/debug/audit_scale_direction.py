"""
audit_scale_direction.py — Detect scale-inversion in construct member items.

A scale is INVERTED when value 1 carries the highest-intensity / most-positive
label (e.g. 1=Mucho, 1=Muy de acuerdo) but the item is NOT yet reverse-coded.
Without reversal, higher aggregate scores mean LESS of the implied concept.

Output:
  1. Console report of all flagged items grouped by construct.
  2. data/results/scale_audit_v1.json — machine-readable audit with:
       - per-item flags (inverted / already_rc / ok)
       - proposed_overrides: additions to construct_v5_overrides["reverse_coded_overrides"]
       - already_handled: constructs that are fully covered in existing RC

Usage:
    python scripts/debug/audit_scale_direction.py
    python scripts/debug/audit_scale_direction.py --apply   # writes proposed overrides
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SVS_PATH = ROOT / "data" / "results" / "semantic_variable_selection_v4.json"
V5_PATH = ROOT / "data" / "results" / "construct_v5_overrides.json"
OUTPUT_PATH = ROOT / "data" / "results" / "scale_audit_v1.json"

# ─────────────────────────────────────────────────────────────────────────────
# Keywords indicating an INVERTED scale (value 1 = most positive / most intense)
# ─────────────────────────────────────────────────────────────────────────────
_INVERTED_PATTERNS = [
    # Agreement (Likert)
    r"\bmuy de acuerdo\b",
    r"\btotalmente de acuerdo\b",
    r"\bcompletamente de acuerdo\b",
    r"\bde acuerdo\b",          # 1=De acuerdo on a 4-pt inverted scale
    # Frequency
    r"\bsiempre\b",
    # Intensity: Mucho / Bastante (when at position 1)
    r"\bmucho\b",
    r"\bmucha\b",
    r"\bmuchos\b",
    r"\bmuchas\b",
    # Quality scales
    r"\bexcelente\b",
    r"\bmuy buena\b",
    r"\bmuy bueno\b",
    r"\bmuy bien\b",
    # Satisfaction (only if positive qualifier — exclude "totalmente insatisfecho")
    r"\bmuy satisfech[oa]\b",
    r"\btotalmente satisfech[oa]\b",
    r"\bmuy confiad[oa]\b",
    # Trust (confianza alta)
    r"\bmucha confianza\b",
    # "Totalmente" as agreement/truth marker (NOT "totalmente insatisfecho/falso/pagado")
    r"\btotalmente\s+(?:de\s+acuerdo|cierto|correcto|seguro)",
]
_INVERTED_RE = re.compile("|".join(_INVERTED_PATTERNS), re.IGNORECASE)

# Labels that look positive but are NOT scale-inversion indicators
# (categorical / demographic / other)
_EXCLUDE_PATTERNS = [
    r"\bhombre\b", r"\bmujer\b",
    r"\bsí\b", r"\bno\b",
    r"\burbano\b", r"\brural\b",
    r"\bcdmx\b", r"\bnorte\b", r"\bsur\b", r"\bcentro\b",
    r"\bjubilado\b", r"\bempleado\b",
]
_EXCLUDE_RE = re.compile("|".join(_EXCLUDE_PATTERNS), re.IGNORECASE)


def _is_inverted_label(label: str) -> bool:
    """Return True if label at value '1' indicates a descending (inverted) scale."""
    if _EXCLUDE_RE.search(label):
        return False
    return bool(_INVERTED_RE.search(label))


def _load_enc_dict() -> dict:
    print("Loading survey data …", flush=True)
    from dataset_knowledge import load_los_mex_dict
    d = load_los_mex_dict()
    return d["enc_dict"]


def _value_label_for_one(enc_dict: dict, survey_name: str, col: str) -> Optional[str]:
    """Return the label for numeric code '1' of (survey, col), or None if absent.

    Handles both integer keys ('1', 1) and float keys ('1.0') as produced by
    different survey pre-processing pipelines.
    """
    meta = enc_dict.get(survey_name, {}).get("metadata", {})
    vvl = meta.get("variable_value_labels", {})
    labels = vvl.get(col, {})
    if not labels:
        # Some surveys store inside column_names_to_labels (rare)
        cnl = meta.get("column_names_to_labels", {})
        labels = cnl.get(col, {}) if isinstance(cnl.get(col), dict) else {}
    # Try various key representations for value=1
    for k in ("1", 1, "1.0", 1.0):
        v = labels.get(k)
        if v is not None:
            return v
    return None


def _load_svs() -> dict:
    with open(SVS_PATH) as f:
        return json.load(f)


def _load_v5() -> dict:
    if V5_PATH.exists():
        with open(V5_PATH) as f:
            return json.load(f)
    return {}


def _current_rc_set(v4_cluster: dict, v5_overrides: dict, key: str) -> set:
    """All items already reverse-coded for this construct (v4 + v5 combined)."""
    rc = set(v4_cluster.get("reverse_coded_items") or [])
    extra = v5_overrides.get("reverse_coded_overrides", {}).get(key, {}).get("add", [])
    rc.update(extra)
    return rc


# ─────────────────────────────────────────────────────────────────────────────
# Domain → survey name mapping (enc_nom_dict_rev equivalent, derived at runtime)
# ─────────────────────────────────────────────────────────────────────────────

def _build_dom_to_survey(enc_dict: dict, svs: dict) -> Dict[str, str]:
    """Map domain code → survey name by matching survey_title in SVS to enc_dict keys."""
    dom_to_survey: Dict[str, str] = {}
    for domain, dom_data in svs.get("domains", {}).items():
        title = dom_data.get("survey_title", "").upper()
        # Direct match
        if title in enc_dict:
            dom_to_survey[domain] = title
            continue
        # Fuzzy: look for enc_dict key that contains the title (or vice versa)
        for sname in enc_dict:
            if title in sname.upper() or sname.upper() in title:
                dom_to_survey[domain] = sname
                break
    return dom_to_survey


# ─────────────────────────────────────────────────────────────────────────────
# Main audit
# ─────────────────────────────────────────────────────────────────────────────

def run_audit(enc_dict: dict) -> dict:
    svs = _load_svs()
    v5 = _load_v5()
    excluded_keys = set(v5.get("excluded", {}).keys())
    items_to_drop = {k: set(v) for k, v in v5.get("items_to_drop", {}).items()}

    dom_to_survey = _build_dom_to_survey(enc_dict, svs)

    audit_results: Dict[str, dict] = {}   # construct_key → {...}
    proposed_overrides: Dict[str, List[str]] = {}  # construct_key → [items to add to RC]

    for domain, dom_data in svs.get("domains", {}).items():
        survey_name = dom_to_survey.get(domain)
        if not survey_name:
            print(f"  [WARN] No survey for domain {domain}")
            continue
        df = enc_dict[survey_name].get("dataframe")

        for cluster in dom_data.get("construct_clusters", []):
            cname = cluster["name"]
            key = f"{domain}|{cname}"
            if key in excluded_keys:
                continue

            # Effective item list (after drops)
            qids_raw = cluster.get("question_cluster", [])
            qids_bare = [q.split("|")[0] if "|" in q else q for q in qids_raw]
            drop_set = items_to_drop.get(key, set())
            qids_bare = [q for q in qids_bare if q not in drop_set]

            current_rc = _current_rc_set(cluster, v5, key)

            item_audit: List[dict] = []
            needs_reversal: List[str] = []

            for col in qids_bare:
                label1 = _value_label_for_one(enc_dict, survey_name, col)
                if label1 is None:
                    item_audit.append({
                        "col": col, "label_1": None, "inverted": False,
                        "already_rc": col in current_rc, "flag": "no_label"
                    })
                    continue

                inverted = _is_inverted_label(label1)
                already_rc = col in current_rc
                if inverted and not already_rc:
                    needs_reversal.append(col)
                    flag = "NEEDS_RC"
                elif inverted and already_rc:
                    flag = "inverted_already_rc"
                elif not inverted and already_rc:
                    flag = "rc_but_not_inverted"  # worth checking
                else:
                    flag = "ok"

                item_audit.append({
                    "col": col, "label_1": label1, "inverted": inverted,
                    "already_rc": already_rc, "flag": flag
                })

            audit_results[key] = {
                "survey": survey_name,
                "n_items": len(qids_bare),
                "n_inverted_unhandled": len(needs_reversal),
                "proposed_add_rc": needs_reversal,
                "items": item_audit,
            }
            if needs_reversal:
                proposed_overrides[key] = needs_reversal

    return {
        "proposed_overrides": proposed_overrides,
        "audit": audit_results,
    }


def print_report(result: dict) -> None:
    audit = result["audit"]
    proposed = result["proposed_overrides"]

    print("\n" + "=" * 70)
    print("SCALE DIRECTION AUDIT")
    print("=" * 70)

    flagged = {k: v for k, v in audit.items() if v["n_inverted_unhandled"] > 0}
    clean = {k: v for k, v in audit.items() if v["n_inverted_unhandled"] == 0}

    print(f"\n  Constructs audited : {len(audit)}")
    print(f"  Flagged (needs RC) : {len(flagged)}")
    print(f"  Clean              : {len(clean)}")

    if flagged:
        print("\n── CONSTRUCTS NEEDING REVERSE-CODING ──────────────────────────────")
        for key, info in sorted(flagged.items()):
            print(f"\n  {key}  ({info['survey']})")
            for item in info["items"]:
                if item["flag"] == "NEEDS_RC":
                    print(f"    ✗  {item['col']:15s}  label_1={item['label_1']!r}")
            print(f"    → proposed add_rc: {info['proposed_add_rc']}")

    # Also list items already RC but worth noting
    rc_not_inverted = []
    for key, info in audit.items():
        for item in info["items"]:
            if item["flag"] == "rc_but_not_inverted":
                rc_not_inverted.append((key, item["col"], item["label_1"]))
    if rc_not_inverted:
        print("\n── RC'D BUT LABEL NOT DETECTED AS INVERTED (review) ───────────────")
        for key, col, label in rc_not_inverted:
            print(f"  {key:50s}  {col:15s}  label_1={label!r}")

    print("\n" + "=" * 70)
    print(f"Proposed additions to reverse_coded_overrides:")
    for key, items in sorted(proposed.items()):
        print(f"  {key}: {items}")
    print("=" * 70 + "\n")


def apply_overrides(result: dict, v5_path: Path = V5_PATH) -> None:
    """Merge proposed_overrides into construct_v5_overrides.json."""
    v5 = _load_v5()
    rc_ov = v5.setdefault("reverse_coded_overrides", {})
    proposed = result["proposed_overrides"]
    n_new = 0
    for key, items in proposed.items():
        entry = rc_ov.setdefault(key, {"add": []})
        existing = set(entry.get("add", []))
        new_items = [i for i in items if i not in existing]
        entry["add"] = sorted(existing | set(items))
        n_new += len(new_items)
    with open(v5_path, "w") as f:
        json.dump(v5, f, indent=2, ensure_ascii=False)
    print(f"  Written {n_new} new RC entries to {v5_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="Write proposed overrides into construct_v5_overrides.json")
    args = parser.parse_args()

    enc_dict = _load_enc_dict()
    result = run_audit(enc_dict)
    print_report(result)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Full audit saved to {OUTPUT_PATH}")

    if args.apply:
        print("\nApplying proposed overrides …")
        apply_overrides(result)
        print("Done. Run build_construct_variables.py to rebuild constructs.")
