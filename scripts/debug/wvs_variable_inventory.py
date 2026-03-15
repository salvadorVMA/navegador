"""
Phase 1 — WVS Variable Inventory

Produces a structured inventory of all substantive Wave 7 Q-columns for Mexico:
  - Spanish question text (from questionnaire PDF via pdfminer)
  - English title (from equivalences XLSX, fallback)
  - A-series code (stable time-series identifier)
  - Domain prefix (A=Social, C=Work, D=Family, E=Politics, F=Religion, G=Identity, H=Security, I=Science)
  - Wave coverage (which of 7 waves have this item, from equivalences)
  - N_valid (non-sentinel, non-missing in Mexico Wave 7)
  - Validated index membership (pre-coded from WVS_VALIDATED_INDICES.md)

Output:
  data/results/wvs_variable_inventory.json
  data/results/wvs_variable_inventory.md

Run:
  conda run -n nvg_py13_env python scripts/debug/wvs_variable_inventory.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_loader import WVSLoader

WVS_DIR = ROOT / "data" / "wvs"
PDF_PATH = WVS_DIR / "WVS7_Questionnaire_Mexico_2018_Spanish.pdf"
OUT_JSON = ROOT / "data" / "results" / "wvs_variable_inventory.json"
OUT_MD   = ROOT / "data" / "results" / "wvs_variable_inventory.md"

# ---------------------------------------------------------------------------
# Domain label map (by A-code prefix → survey-like label)
# ---------------------------------------------------------------------------
DOMAIN_LABELS: dict[str, str] = {
    "A": "Social Values, Attitudes & Stereotypes",
    "B": "Environment",
    "C": "Work & Employment",
    "D": "Family",
    "E": "Politics & Society",
    "F": "Religion & Morale",
    "G": "National Identity",
    "H": "Security",
    "I": "Science & Technology",
}

# ---------------------------------------------------------------------------
# Validated index membership (from WVS_VALIDATED_INDICES.md)
# Time-series A-codes mapped to index names.
# ---------------------------------------------------------------------------
_VALIDATED_INDEX_MEMBERSHIP: dict[str, list[str]] = {
    # Traditional/Secular-Rational
    "F034": ["Traditional/Secular-Rational", "Religiosity (Norris & Inglehart)"],
    "A006": ["Traditional/Secular-Rational", "Religiosity (Norris & Inglehart)"],
    "F120": ["Traditional/Secular-Rational"],
    "E018": ["Traditional/Secular-Rational", "RWA (proxy)"],
    "A042": ["Traditional/Secular-Rational", "RWA (proxy)"],
    "G006": ["Traditional/Secular-Rational"],
    "F198": ["Traditional/Secular-Rational"],
    # Survival/Self-Expression
    "A165": ["Survival/Self-Expression", "Social Capital", "Political Trust (Zmerli)"],
    "E025": ["Survival/Self-Expression", "EVI Voice", "Social Capital"],
    "F118": ["Survival/Self-Expression", "EVI Choice"],
    "A001": ["Survival/Self-Expression"],
    "H010": ["Survival/Self-Expression"],
    # Post-Materialist
    "E001": ["Post-Materialist"],
    "E002": ["Post-Materialist"],
    "E003": ["Post-Materialist"],
    "E004": ["Post-Materialist"],
    # EVI — Autonomy (Y003)
    "A029": ["EVI Autonomy"],
    "A038": ["EVI Autonomy"],
    "A040": ["EVI Autonomy"],
    # EVI — Equality
    "C001": ["EVI Equality", "Gender Egalitarianism"],
    "D059": ["EVI Equality", "Gender Egalitarianism", "RWA (proxy)"],
    "D060": ["EVI Equality", "Gender Egalitarianism"],
    # EVI — Choice
    "F121": ["EVI Choice"],
    # EVI — Voice
    "E026": ["EVI Voice", "Social Capital"],
    "E027": ["EVI Voice", "Social Capital"],
    # Religiosity
    "F028": ["Religiosity (Norris & Inglehart)", "CRS (approx)"],
    "F029": ["Religiosity (Norris & Inglehart)", "CRS (approx)"],
    "F024": ["Religiosity (Norris & Inglehart)", "CRS (approx)"],
    "F025": ["Religiosity (Norris & Inglehart)", "CRS (approx)"],
    # Institutional trust
    "E069_01": ["Confidence in Institutions"],
    "E069_02": ["Confidence in Institutions"],
    "E069_03": ["Confidence in Institutions"],
    "E069_04": ["Confidence in Institutions"],
    "E069_05": ["Confidence in Institutions", "Political Trust (Zmerli)"],
    "E069_06": ["Confidence in Institutions", "Political Trust (Zmerli)"],
    "E069_07": ["Confidence in Institutions"],
    "E069_08": ["Confidence in Institutions"],
    "E069_11": ["Confidence in Institutions"],
    "E069_12": ["Confidence in Institutions"],
    "E069_13": ["Confidence in Institutions"],
    "E069_14": ["Confidence in Institutions"],
    "E069_17": ["Confidence in Institutions", "Political Trust (Zmerli)"],
    "E069_18": ["Confidence in Institutions"],
    "E069_61": ["Confidence in Institutions"],
    "E069_62": ["Confidence in Institutions"],
    "E069_63": ["Confidence in Institutions"],
    # Autocracy support
    "E114": ["Autocracy Support (Foa & Mounk)"],
    "E115": ["Autocracy Support (Foa & Mounk)"],
    "E116": ["Autocracy Support (Foa & Mounk)"],
    "E117": ["Autocracy Support (Foa & Mounk)"],
    "E123": ["Autocracy Support (Foa & Mounk)"],
    "E226": ["Autocracy Support (Foa & Mounk)"],
    "E227": ["Autocracy Support (Foa & Mounk)"],
    # Gender egalitarianism
    "D061": ["Gender Egalitarianism"],
    "D078": ["Gender Egalitarianism"],
    # Social capital
    "A098": ["Social Capital"],
    "A099": ["Social Capital"],
    "A100": ["Social Capital"],
    "A101": ["Social Capital"],
    "A102": ["Social Capital"],
    "A103": ["Social Capital"],
    "A104": ["Social Capital"],
    "A105": ["Social Capital"],
    "A106": ["Social Capital"],
    # Subjective Well-Being
    "A008": ["Subjective Well-Being"],
    "A170": ["Subjective Well-Being"],
    # Environmental
    "B001": ["Environmental Concern"],
    "B002": ["Environmental Concern"],
    "B003": ["Environmental Concern"],
    "B004": ["Environmental Concern"],
}

# Columns to exclude from substantive inventory
_EXCLUDE_PREFIXES = ("A_", "B_", "C_", "D_", "N_", "G_TOWN", "H_URB",
                     "W_", "PWGHT", "version", "doi")
_EXCLUDE_EXACT = {"Q_MODE", "Q260", "Q262", "Q275",
                  "sexo", "edad", "escol", "Tam_loc", "G_TOWNSIZE"}

# ---------------------------------------------------------------------------
# PDF text extractor
# ---------------------------------------------------------------------------

def _extract_pdf_text(pdf_path: Path) -> str:
    try:
        from pdfminer.high_level import extract_text
        return extract_text(str(pdf_path))
    except Exception as e:
        print(f"  WARNING: pdfminer failed ({e}). Spanish text unavailable.")
        return ""


def _parse_pdf_items(text: str) -> dict[int, dict[str, str]]:
    """
    Parse numbered items from WVS Mexico Spanish questionnaire PDF text.

    Returns {item_number: {"text": str, "scale": str}}
    Item numbers correspond to Q-codes (item 1 → Q1, item 64 → Q64, etc.).
    """
    if not text:
        return {}

    lines = [l.rstrip() for l in text.split("\n")]
    items: dict[int, dict[str, str]] = {}
    current_scale = ""
    current_instruction = ""
    i = 0
    # Pattern: line starts with 1–3 digits followed by space + content
    item_re = re.compile(r"^(\d{1,3})\s{1,5}(.{3,})")
    # Pattern: scale definition like [1=Algo; 2=...]
    scale_re = re.compile(r"\[1=.{3,}", re.IGNORECASE)
    # TARJETA / instruction headers
    instr_re = re.compile(r"^\(TARJETA|^\(MOSTRAR|^INSTRUCCIÓN|^Introducción", re.IGNORECASE)

    n = len(lines)
    seen_nums: set[int] = set()

    while i < n:
        line = lines[i].strip()

        # Track scale context
        if scale_re.search(line):
            current_scale = line.strip("[]").strip()

        if instr_re.match(line):
            current_instruction = line

        m = item_re.match(line)
        if m:
            num = int(m.group(1))
            content = m.group(2).strip()

            # Valid Q range and not seen before and reasonable monotonicity
            if 1 <= num <= 293 and num not in seen_nums:
                # Try to collect continuation lines (next non-numbered, non-blank lines)
                continuation_lines = []
                j = i + 1
                while j < n and j < i + 5:
                    nxt = lines[j].strip()
                    # Stop if next line starts a new item number or is blank
                    if not nxt:
                        break
                    if item_re.match(nxt):
                        break
                    if scale_re.search(nxt):
                        break
                    if instr_re.match(nxt):
                        break
                    # Stop if it looks like a scale code line (short or starts with digit-parenth)
                    if len(nxt) < 3 or re.match(r"^\d\)", nxt):
                        break
                    continuation_lines.append(nxt)
                    j += 1

                full_text = content
                if continuation_lines:
                    full_text = content + " " + " ".join(continuation_lines)
                # Clean up extra whitespace
                full_text = re.sub(r"\s{2,}", " ", full_text).strip()

                items[num] = {
                    "text_es": full_text,
                    "scale": current_scale,
                    "instruction": current_instruction,
                }
                seen_nums.add(num)

        i += 1

    return items


# ---------------------------------------------------------------------------
# Main inventory builder
# ---------------------------------------------------------------------------

def build_inventory() -> dict[str, Any]:
    print("Loading WVS Wave 7 Mexico data...")
    loader = WVSLoader()
    wvs_dict = loader.build_wvs_dict(waves=[7], countries=["MEX"])
    df = wvs_dict["enc_dict"]["WVS_W7_MEX"]["dataframe"]
    meta = wvs_dict["enc_dict"]["WVS_W7_MEX"]["metadata"]
    col_labels = meta["column_names_to_labels"]
    equivalences = loader.equivalences

    # Build A-code lookups
    qcode_to_acode: dict[str, str] = {}
    acode_to_waves: dict[str, list[int]] = {}
    for _, row in equivalences.iterrows():
        acode = str(row["a_code"]).strip()
        for wave in range(1, 8):
            q = row[f"w{wave}"]
            if q:
                q = str(q).strip()
                qcode_to_acode[q] = acode
                acode_to_waves.setdefault(acode, []).append(wave)

    print(f"  {len(df)} respondents, {len(df.columns)} columns")

    # Parse Spanish PDF
    print("Parsing Spanish questionnaire PDF...")
    if PDF_PATH.exists():
        pdf_text = _extract_pdf_text(PDF_PATH)
        pdf_items = _parse_pdf_items(pdf_text)
        print(f"  {len(pdf_items)} items parsed from PDF")
    else:
        pdf_items = {}
        print("  PDF not found — using English titles only")

    # Determine substantive Q-columns to include
    def _is_substantive(col: str) -> bool:
        if col in _EXCLUDE_EXACT:
            return False
        for pfx in _EXCLUDE_PREFIXES:
            if col.startswith(pfx):
                return False
        if col.startswith("Y"):
            return False  # pre-built indices — handle separately
        # Keep Q-codes and other substantive cols
        return True

    subst_cols = [c for c in df.columns if _is_substantive(c)]
    print(f"  {len(subst_cols)} substantive columns")

    # Build per-column inventory
    domain_buckets: dict[str, list[dict]] = {}
    skipped = []

    for col in subst_cols:
        # Resolve A-code
        acode = qcode_to_acode.get(col, "")
        if not acode:
            # Try stripping the column (some might have minor variants)
            skipped.append(col)
            continue

        # Domain prefix
        domain_prefix = acode[0] if acode else "?"
        if domain_prefix not in DOMAIN_LABELS:
            skipped.append(col)
            continue

        # Q-number for PDF lookup (Q1 → 1, Q64 → 64; non-numeric → no lookup)
        q_num_str = col[1:] if col.startswith("Q") else ""
        pdf_entry = {}
        if q_num_str.isdigit():
            pdf_entry = pdf_items.get(int(q_num_str), {})

        title_es = pdf_entry.get("text_es", "")
        scale_text = pdf_entry.get("scale", "")
        title_en = col_labels.get(col, acode)

        # N_valid: non-negative values (WVS sentinels are < 0)
        col_data = pd.to_numeric(df[col], errors="coerce")
        n_valid = int((col_data >= 0).sum())

        # Wave coverage
        waves = sorted(acode_to_waves.get(acode, []))

        # Validated index membership
        validated = _VALIDATED_INDEX_MEMBERSHIP.get(acode, [])

        entry = {
            "qcode": col,
            "acode": acode,
            "domain_prefix": domain_prefix,
            "title_en": title_en,
            "title_es": title_es,
            "scale_text": scale_text,
            "n_valid": n_valid,
            "n_pct_valid": round(n_valid / len(df) * 100, 1),
            "wave_coverage": waves,
            "n_waves": len(waves),
            "validated_indices": validated,
        }
        domain_buckets.setdefault(domain_prefix, []).append(entry)

    # Sort within domains by Q-code numerically
    for prefix in domain_buckets:
        domain_buckets[prefix].sort(
            key=lambda x: int(x["qcode"][1:]) if x["qcode"][1:].isdigit() else 9999
        )

    if skipped:
        print(f"  Skipped {len(skipped)} cols (no A-code or non-substantive): {skipped[:10]}...")

    # Y-index summary
    y_summary = []
    for y in ["Y001", "Y002", "Y003"]:
        if y in df.columns:
            col_data = pd.to_numeric(df[y], errors="coerce")
            n_valid = int((col_data >= 0).sum())
            y_summary.append({"ycode": y, "n_valid": n_valid, "title": col_labels.get(y, y)})

    inventory = {
        "source": "WVS Wave 7 — Mexico (2018)",
        "n_respondents": len(df),
        "n_substantive_cols": sum(len(v) for v in domain_buckets.values()),
        "domains": {
            prefix: {
                "label": DOMAIN_LABELS.get(prefix, prefix),
                "items": items,
            }
            for prefix, items in sorted(domain_buckets.items())
        },
        "y_indices_available": y_summary,
    }

    return inventory, df


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def _render_markdown(inventory: dict[str, Any], out_path: Path) -> None:
    lines = [
        "# WVS Variable Inventory — Mexico Wave 7 (2018)",
        "",
        f"Source: {inventory['source']}",
        f"N respondents: {inventory['n_respondents']}",
        f"Substantive variables: {inventory['n_substantive_cols']}",
        "",
        "## Pre-computed Y-indices available in data",
        "",
        "| Code | N_valid | Title |",
        "|------|---------|-------|",
    ]
    for y in inventory.get("y_indices_available", []):
        lines.append(f"| {y['ycode']} | {y['n_valid']} | {y['title']} |")

    lines += ["", "## Variable Inventory by Domain", ""]

    for prefix, dom in inventory["domains"].items():
        items = dom["items"]
        label = dom["label"]
        n_items = len(items)
        n_validated = sum(1 for x in items if x["validated_indices"])
        n_low = sum(1 for x in items if x["n_pct_valid"] < 30)

        lines += [
            f"### {prefix}: {label} ({n_items} variables, {n_validated} in validated indices, {n_low} low-N)",
            "",
            "| Q-code | A-code | N_valid | %valid | Waves | Validated index(es) | Title (EN) |",
            "|--------|--------|---------|--------|-------|---------------------|------------|",
        ]
        for item in items:
            waves_str = ",".join(str(w) for w in item["wave_coverage"])
            val_str = "; ".join(item["validated_indices"]) if item["validated_indices"] else "—"
            title_en = item["title_en"][:60] + ("…" if len(item["title_en"]) > 60 else "")
            low_flag = " ⚠" if item["n_pct_valid"] < 30 else ""
            lines.append(
                f"| {item['qcode']} | {item['acode']} | {item['n_valid']} | "
                f"{item['n_pct_valid']}%{low_flag} | {waves_str} | {val_str} | {title_en} |"
            )
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown: {out_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    inventory, df = build_inventory()

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)
    print(f"JSON: {OUT_JSON}")

    _render_markdown(inventory, OUT_MD)

    # Print domain summary
    print("\nDomain summary:")
    for prefix, dom in inventory["domains"].items():
        items = dom["items"]
        n_val = sum(1 for x in items if x["validated_indices"])
        n_low = sum(1 for x in items if x["n_pct_valid"] < 30)
        n_all7 = sum(1 for x in items if x["n_waves"] == 7)
        print(f"  {prefix} ({dom['label'][:30]}): {len(items)} items, "
              f"{n_val} validated, {n_all7} in all 7 waves, {n_low} low-N")


if __name__ == "__main__":
    main()
