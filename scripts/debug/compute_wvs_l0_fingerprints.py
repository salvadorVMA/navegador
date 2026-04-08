"""
Compute WVS L0 (item-level) SES fingerprints for all individual Q-codes.

Loads the raw WVS Wave 7 CSV from the ZIP, filters to Mexico, harmonizes
SES variables, and computes Spearman rho per Q-code against each of the
4 SES dimensions (sexo, edad, escol, Tam_loc).

For items that belong to a WVS construct (from wvs_construct_manifest.json),
also computes loading_gamma = GK gamma(raw_item, bin5(parent_construct)).

Output: data/results/wvs_l0_fingerprints.json

Format compatible with OntologyQuery._lift_to_construct() — items keyed as
    "{Q-code}|W7_MEX"
with fields: rho_escol, rho_Tam_loc, rho_sexo, rho_edad, ses_magnitude,
dominant_dim, parent_construct, loading_gamma, loading_type, domain, etc.

Usage:
    python scripts/debug/compute_wvs_l0_fingerprints.py
    python scripts/debug/compute_wvs_l0_fingerprints.py --country MEX
    python scripts/debug/compute_wvs_l0_fingerprints.py --all-countries
"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import (
    DOMAIN_MAP,
    SES_VARS,
    WVS_SENTINEL_THRESHOLD,
    build_qcode_to_acode,
    load_equivalences,
)
from wvs_loader import (
    WVSLoader,
    _load_csv_from_source,
    _find_wvs_file,
    clean_sentinels,
    harmonize_ses,
    _COL_COUNTRY_ALPHA,
)

SES_COLS = ["sexo", "edad", "escol", "Tam_loc"]
_RHO_TO_GAMMA_SCALE = 1.14

# Columns to skip (administrative, weights, SES vars themselves)
_SKIP_COLS = {
    "sexo", "edad", "escol", "Tam_loc",
    "B_COUNTRY", "B_COUNTRY_ALPHA", "A_WAVE", "A_YEAR", "A_STUDY",
    "W_WEIGHT", "S_WEIGHT", "I_WEIGHT", "D_INTERVIEW",
    "version", "doi", "fw_comment",
    "N_REGION_ISO", "N_REGION_WVS",
    "O1_LONGITUDE", "O2_LATITUDE",
    "O3_INTERVIEWER_NUMBER",
    "G_TOWNSIZE",  # raw SES source col (already harmonized to Tam_loc)
    "Q260", "Q262", "Q275",  # raw SES source cols
}
_SKIP_PREFIXES = ("wvs_agg_",)

OUTPUT_PATH = ROOT / "data" / "results" / "wvs_l0_fingerprints.json"


# ─────────────────────────────────────────────────────────────
# Core primitives (mirrors compute_ses_fingerprints.py)
# ─────────────────────────────────────────────────────────────

def _is_sentinel(v: float) -> bool:
    """WVS sentinel: negative values; los_mex sentinel: >= 97 or < 0."""
    if pd.isna(v):
        return False
    return v < 0 or v >= 97


def _clean_ses_wvs(df: pd.DataFrame) -> pd.DataFrame:
    """Extract clean numeric SES columns from a harmonized WVS DataFrame."""
    out = pd.DataFrame(index=df.index)
    for col in SES_COLS:
        if col not in df.columns:
            out[col] = np.nan
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        # edad is continuous (15-100), no sentinel filtering needed
        if col == "edad":
            out[col] = s.where(s.between(15, 100))
        else:
            # Filter sentinels for discrete SES vars
            sentinel = s.apply(lambda v: _is_sentinel(v) if pd.notna(v) else False)
            out[col] = s.where(~sentinel)
    return out


def _spearman_rho(x: pd.Series, y: pd.Series) -> Optional[float]:
    """Spearman rho with pairwise NaN omission. Returns None if n < 10."""
    mask = x.notna() & y.notna()
    if mask.sum() < 10:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rho, _ = spearmanr(x[mask], y[mask])
    return float(rho) if np.isfinite(rho) else None


def _bin5(s: pd.Series) -> pd.Series:
    """Rank-normalise -> equal-frequency qcut to 5 bins (matches Julia pipeline)."""
    s = pd.to_numeric(s, errors="coerce")
    valid = s.dropna()
    if len(valid) < 20:
        return pd.Series(np.nan, index=s.index)
    ranks = valid.rank(method="average") / (len(valid) + 1)
    try:
        binned = pd.cut(ranks, bins=5, labels=[1, 2, 3, 4, 5]).astype(float)
    except ValueError:
        return pd.Series(np.nan, index=s.index)
    result = pd.Series(np.nan, index=s.index)
    result[valid.index] = binned.values
    return result


def _gk_gamma(x: pd.Series, y: pd.Series) -> Optional[float]:
    """Goodman-Kruskal gamma via joint frequency table.

    Drops NaN pairwise. Returns None if n < 10 or no non-tied pairs.
    """
    mask = x.notna() & y.notna()
    if mask.sum() < 10:
        return None
    xv = np.asarray(x[mask], dtype=float)
    yv = np.asarray(y[mask], dtype=float)

    xi = np.sort(np.unique(xv))
    yi = np.sort(np.unique(yv))
    if len(xi) < 2 or len(yi) < 2:
        return None

    xi_idx = {v: i for i, v in enumerate(xi)}
    yi_idx = {v: i for i, v in enumerate(yi)}

    table = np.zeros((len(xi), len(yi)), dtype=np.float64)
    for a, b in zip(xv, yv):
        table[xi_idx[a], yi_idx[b]] += 1.0

    C = D = 0.0
    for i in range(len(xi)):
        for j in range(len(yi)):
            if table[i, j] == 0.0:
                continue
            C += table[i, j] * table[i + 1:, j + 1:].sum()
            D += table[i, j] * table[i + 1:, :j].sum()

    if C + D == 0.0:
        return None
    return round(float((C - D) / (C + D)), 4)


def _fingerprint(series: pd.Series, ses_df: pd.DataFrame) -> Optional[Dict]:
    """Compute 4D SES fingerprint for one variable."""
    rhos = {}
    for sv in SES_COLS:
        if sv not in ses_df.columns:
            continue
        rho = _spearman_rho(series, ses_df[sv])
        if rho is not None:
            rhos[f"rho_{sv}"] = round(rho, 4)

    if not rhos:
        return None

    vals = list(rhos.values())
    magnitude = float(np.sqrt(np.mean(np.array(vals) ** 2)))
    dominant = max(rhos, key=lambda k: abs(rhos[k])).replace("rho_", "")
    return {
        **rhos,
        "ses_magnitude": round(magnitude, 4),
        "dominant_dim": dominant,
        "n_obs": int(series.dropna().shape[0]),
    }


# ─────────────────────────────────────────────────────────────
# Build Q-code → construct mapping from manifest
# ─────────────────────────────────────────────────────────────

def _build_qcode_construct_index(
    manifest_path: Path,
) -> Dict[str, Dict]:
    """Build {Q-code: {construct_key, reverse_coded}} from the WVS construct manifest.

    Returns a dict mapping individual Q-code strings to their parent construct info.
    """
    if not manifest_path.exists():
        return {}

    with open(manifest_path) as f:
        manifest = json.load(f)

    index: Dict[str, Dict] = {}
    for entry in manifest:
        key = entry.get("key", "")
        agg_col = entry.get("column", "")
        reverse_coded = set(entry.get("reverse_coded", []))
        for qcode in entry.get("items", []):
            index[qcode] = {
                "construct_key": key,
                "agg_col": agg_col,
                "reverse_coded": qcode in reverse_coded,
            }
    return index


def _build_domain_construct_index(
    construct_fps: Dict[str, Dict],
) -> Dict[str, List[tuple]]:
    """Build {domain_prefix: [(construct_key, normalized_rho_vec), ...]} for orphan matching."""
    index: Dict[str, List[tuple]] = {}
    for key, fp in construct_fps.items():
        domain = key.split("|")[0]
        vals = np.array([fp.get(f"rho_{sv}", 0.0) for sv in SES_COLS], dtype=float)
        norm = np.linalg.norm(vals)
        if norm < 1e-9:
            continue
        index.setdefault(domain, []).append((key, vals / norm))
    return index


def _best_candidate_construct(
    item_fp: Dict,
    domain_construct_index: Dict[str, List[tuple]],
    domain: str,
) -> Optional[str]:
    """Return the construct key with highest cosine similarity to item_fp in the same domain."""
    candidates = domain_construct_index.get(domain, [])
    if not candidates:
        return None
    vals = np.array([item_fp.get(f"rho_{sv}", 0.0) for sv in SES_COLS], dtype=float)
    norm = np.linalg.norm(vals)
    if norm < 1e-9:
        return None
    item_vec = vals / norm
    best_key, best_cos = None, -2.0
    for key, cvec in candidates:
        cos = float(np.dot(item_vec, cvec))
        if cos > best_cos:
            best_cos, best_key = cos, key
    return best_key


# ─────────────────────────────────────────────────────────────
# Main computation
# ─────────────────────────────────────────────────────────────

def compute_wvs_l0_fingerprints(
    country: str = "MEX",
    wave: int = 7,
    output_path: Path = OUTPUT_PATH,
    wvs_dir: Optional[Path] = None,
) -> dict:
    """Compute L0 fingerprints for all Q-codes in WVS data for a given country/wave.

    Parameters
    ----------
    country : str
        ISO alpha-3 country code (default: MEX).
    wave : int
        WVS wave number (default: 7).
    output_path : Path
        Output JSON path.

    Returns
    -------
    dict with keys: metadata, constructs, items, domains.
    """
    if wvs_dir is None:
        wvs_dir = ROOT / "data" / "wvs"

    # ── Load raw WVS data ──────────────────────────────────────
    print(f"Loading WVS Wave {wave} data for {country}...")
    loader = WVSLoader(wvs_dir=wvs_dir)
    df_raw = loader.load_slice(wave=wave, countries=[country])
    print(f"  {len(df_raw)} respondents, {len(df_raw.columns)} columns")

    # ── Build Q-code lookup tables ─────────────────────────────
    equivalences = loader.equivalences
    qcode_to_acode = build_qcode_to_acode(equivalences)
    acode_to_info = {}
    for _, row in equivalences.iterrows():
        acode_to_info[row["a_code"]] = {
            "title": row["title"],
            "domain": row["domain"],
            "prefix": row["prefix"],
        }

    short_id = f"W{wave}_{country}"

    # ── Load construct manifest for Q-code -> construct mapping ──
    manifest_path = ROOT / "data" / "results" / "wvs_construct_manifest.json"
    qcode_construct_index = _build_qcode_construct_index(manifest_path)
    print(f"  {len(qcode_construct_index)} Q-codes mapped to constructs")

    # ── Build construct aggregate columns in df_raw ────────────
    # The raw WVS DataFrame does not have wvs_agg_* columns — we build them
    # from the manifest's item lists (simple mean of items after sentinel cleaning).
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest_data = json.load(f)
        n_agg_built = 0
        for entry in manifest_data:
            agg_col = entry.get("column", "")
            item_cols = entry.get("items", [])
            if not agg_col or not item_cols:
                continue
            # Only use items present in the raw data
            present = [c for c in item_cols if c in df_raw.columns]
            if not present:
                continue
            # Build aggregate: mean of items (sentinel-cleaned, values < 0 -> NaN)
            item_df = df_raw[present].apply(pd.to_numeric, errors="coerce")
            item_df = item_df.where(item_df >= 0)
            # Reverse-code items if specified
            rc_items = set(entry.get("reverse_coded", []))
            for rc_col in rc_items:
                if rc_col in item_df.columns:
                    col_min = item_df[rc_col].min()
                    col_max = item_df[rc_col].max()
                    if pd.notna(col_min) and pd.notna(col_max):
                        item_df[rc_col] = col_max + col_min - item_df[rc_col]
            df_raw[agg_col] = item_df.mean(axis=1)
            n_agg_built += 1
        print(f"  {n_agg_built} construct aggregates built from item means")

    # ── Load existing L1 construct fingerprints ────────────────
    l1_fp_path = ROOT / "data" / "results" / "wvs_ses_fingerprints_v2.json"
    construct_fps: Dict[str, Dict] = {}
    if l1_fp_path.exists():
        with open(l1_fp_path) as f:
            l1_data = json.load(f)
        construct_fps = l1_data.get("constructs", {})
        print(f"  {len(construct_fps)} L1 construct fingerprints loaded")

    # ── Clean SES columns ──────────────────────────────────────
    ses_df = _clean_ses_wvs(df_raw)

    # ── Pre-bin construct aggregate columns for loading_gamma ──
    binned_agg: Dict[str, pd.Series] = {}
    for col in df_raw.columns:
        if col.startswith("wvs_agg_"):
            binned_agg[col] = _bin5(df_raw[col])

    # ── Compute fingerprints for each Q-code ───────────────────
    print("\nComputing L0 fingerprints...")
    items: Dict[str, Dict] = {}
    n_with_construct = 0
    n_orphan = 0
    n_skipped = 0

    for col in sorted(df_raw.columns):
        # Skip administrative, SES, aggregate, and weight columns
        if col in _SKIP_COLS:
            continue
        if any(col.startswith(pfx) for pfx in _SKIP_PREFIXES):
            continue
        if col.lower().startswith(("folio", "consec", "pond", "peso", "weight",
                                   "wt_", "id_", "d_", "o1_", "o2_", "o3_",
                                   "n_", "a_", "b_", "s_", "i_")):
            continue

        series = pd.to_numeric(df_raw[col], errors="coerce")

        # Filter sentinels from the item (negative values)
        series = series.where(series >= 0)

        n_unique = series.dropna().nunique()
        if n_unique < 2 or n_unique > 20:
            n_skipped += 1
            continue

        fp = _fingerprint(series, ses_df)
        if not fp:
            n_skipped += 1
            continue

        # ── Determine domain from equivalence table ────────────
        acode_info = None
        if col in qcode_to_acode:
            acode = qcode_to_acode[col].get(wave)
            if acode and acode in acode_to_info:
                acode_info = acode_to_info[acode]

        domain_name = acode_info["domain"] if acode_info else "Unknown"
        domain_prefix = acode_info["prefix"] if acode_info else ""
        title = acode_info["title"] if acode_info else col

        # ── Check construct membership ─────────────────────────
        construct_info = qcode_construct_index.get(col, {})
        parent_construct = construct_info.get("construct_key")
        agg_col = construct_info.get("agg_col")
        is_rc = construct_info.get("reverse_coded", False)

        # ── Compute loading_gamma if construct member ──────────
        loading_gamma = None
        loading = None
        loading_type = None

        if parent_construct and agg_col and agg_col in binned_agg:
            # Exact loading: gamma(raw_item, bin5(agg_construct))
            lg = _gk_gamma(series, binned_agg[agg_col])
            if lg is not None:
                loading_gamma = lg
                loading_type = "exact"
            # Also compute Spearman rho loading
            if agg_col in df_raw.columns:
                loading = _spearman_rho(series, df_raw[agg_col])
            n_with_construct += 1
        else:
            n_orphan += 1

        item_key = f"{col}|{short_id}"
        entry = {
            **fp,
            "domain": domain_name,
            "domain_prefix": domain_prefix,
            "title": title,
            "in_construct": parent_construct is not None,
            "parent_construct": parent_construct,
            "reverse_coded": is_rc,
            "loading": round(loading, 4) if loading is not None else None,
            "loading_gamma": loading_gamma,
            "loading_type": loading_type,
        }

        if is_rc:
            entry["interpret_warning"] = (
                "Item was reverse-coded when building its parent construct. "
                "Raw rho signs here are INVERTED relative to the construct's "
                "conceptual direction."
            )

        items[item_key] = entry

    print(f"  {len(items)} item fingerprints computed")
    print(f"  {n_with_construct} with parent construct, {n_orphan} orphans, {n_skipped} skipped")

    # ── Enrich orphans with candidate construct ────────────────
    print("\nEnriching orphans with candidate construct loadings...")
    domain_construct_index = _build_domain_construct_index(construct_fps)
    n_enriched = 0
    n_none = 0

    for item_key, item_data in items.items():
        if item_data.get("in_construct"):
            if item_data.get("loading_type") is None:
                item_data["loading_type"] = "exact"
            continue

        # Find best candidate construct in same domain
        # Use domain_prefix (single letter like "A", "B", etc.) to match
        # WVS construct keys that start with "WVS_{prefix}|"
        wvs_domain_prefix = f"WVS_{item_data.get('domain_prefix', '')}"
        candidate_key = _best_candidate_construct(
            item_data, domain_construct_index, wvs_domain_prefix,
        )

        if candidate_key is None:
            item_data["candidate_construct"] = None
            item_data["candidate_loading"] = None
            item_data["candidate_loading_gamma"] = None
            item_data["loading_type"] = "none"
            n_none += 1
            continue

        # Find the agg_col for this candidate
        candidate_agg_col = None
        for c_info in qcode_construct_index.values():
            if c_info["construct_key"] == candidate_key:
                candidate_agg_col = c_info["agg_col"]
                break
        # Fallback: derive from construct key
        if candidate_agg_col is None:
            cname = candidate_key.split("|", 1)[1] if "|" in candidate_key else ""
            candidate_agg_col = f"wvs_agg_{cname}"

        # Compute loading against candidate construct
        item_col = item_key.split("|")[0]
        if candidate_agg_col in df_raw.columns and item_col in df_raw.columns:
            item_series = pd.to_numeric(df_raw[item_col], errors="coerce")
            item_series = item_series.where(item_series >= 0)
            loading = _spearman_rho(item_series, df_raw[candidate_agg_col])
            if loading is not None:
                gamma_approx = float(np.clip(loading * _RHO_TO_GAMMA_SCALE, -1.0, 1.0))
                item_data["candidate_construct"] = candidate_key
                item_data["candidate_loading"] = round(loading, 4)
                item_data["candidate_loading_gamma"] = round(gamma_approx, 4)
                item_data["loading_type"] = "approximate"
                n_enriched += 1
            else:
                item_data["candidate_construct"] = None
                item_data["candidate_loading"] = None
                item_data["candidate_loading_gamma"] = None
                item_data["loading_type"] = "none"
                n_none += 1
        else:
            item_data["candidate_construct"] = None
            item_data["candidate_loading"] = None
            item_data["candidate_loading_gamma"] = None
            item_data["loading_type"] = "none"
            n_none += 1

    n_exact = sum(1 for v in items.values() if v.get("loading_type") == "exact")
    print(f"  exact: {n_exact}  approximate: {n_enriched}  none: {n_none}")

    # ── Build domain-level fingerprints ────────────────────────
    print("\nComputing domain-level fingerprints...")
    by_domain: Dict[str, List[Dict]] = {}
    for key, fp in items.items():
        dp = fp.get("domain_prefix", "")
        if dp:
            by_domain.setdefault(dp, []).append(fp)

    domains: Dict[str, Dict] = {}
    for domain_prefix, fps_list in by_domain.items():
        rho_keys = [f"rho_{sv}" for sv in SES_COLS]
        agg: Dict = {}
        for k in rho_keys:
            vals = [fp[k] for fp in fps_list if k in fp]
            if vals:
                agg[k] = round(float(np.mean(vals)), 4)
        if not agg:
            continue
        present = [k for k in rho_keys if k in agg]
        agg["ses_magnitude"] = round(
            float(np.sqrt(np.mean([agg[k] ** 2 for k in present]))), 4
        )
        frozen = dict(agg)
        agg["dominant_dim"] = max(
            (k.replace("rho_", "") for k in present),
            key=lambda sv, _fp=frozen: abs(_fp[f"rho_{sv}"]),
        )
        agg["n_items"] = len(fps_list)
        domain_name = DOMAIN_MAP.get(domain_prefix, domain_prefix)
        domains[f"WVS_{domain_prefix}"] = {**agg, "domain_name": domain_name}

    print(f"  {len(domains)} domain fingerprints computed")

    # ── Assemble output ────────────────────────────────────────
    result = {
        "metadata": {
            "source": f"WVS_W{wave}_{country}",
            "n": len(df_raw),
            "n_items": len(items),
            "n_items_loading_exact": n_exact,
            "n_items_loading_approximate": n_enriched,
            "n_items_loading_none": n_none,
            "ses_vars": SES_COLS,
            "rho_to_gamma_scaling_factor": _RHO_TO_GAMMA_SCALE,
            "generated": datetime.now(timezone.utc).isoformat(),
            "description": (
                "WVS L0 (item-level) SES fingerprints. Each Q-code gets a 4D "
                "fingerprint vector [rho_escol, rho_Tam_loc, rho_sexo, rho_edad]. "
                "Items with parent_construct have exact loading_gamma; orphans get "
                "approximate candidate_loading_gamma via cosine-nearest construct."
            ),
        },
        "constructs": construct_fps,  # L1 from existing file
        "items": items,               # L0 computed here
        "domains": domains,           # L2 computed from L0
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # ── Report ─────────────────────────────────────────────────
    _print_report(items, domains, construct_fps)
    print(f"\nOutput: {output_path}")
    return result


def _print_report(
    items: Dict[str, Dict],
    domains: Dict[str, Dict],
    construct_fps: Dict[str, Dict],
) -> None:
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("WVS L0 SES Fingerprint Report")
    print("=" * 60)

    # Top items by SES magnitude
    print("\nTop 15 Q-codes by SES magnitude:")
    ranked = sorted(items.items(), key=lambda x: -x[1].get("ses_magnitude", 0))
    for key, fp in ranked[:15]:
        qcode = key.split("|")[0]
        title = fp.get("title", "")[:50]
        parent = fp.get("parent_construct", "")
        parent_str = f" [{parent}]" if parent else ""
        print(f"  {qcode:8s}  mag={fp['ses_magnitude']:.3f}"
              f"  dom={fp['dominant_dim']:8s}"
              f"  {title}{parent_str}")

    # Domain summary
    print("\nDomain-level SES magnitudes:")
    for domain, fp in sorted(domains.items(), key=lambda x: -x[1].get("ses_magnitude", 0)):
        dname = fp.get("domain_name", domain)
        print(f"  {domain:6s}  mag={fp['ses_magnitude']:.3f}"
              f"  dom={fp['dominant_dim']:8s}"
              f"  n_items={fp['n_items']}")

    # Loading type distribution
    exact = sum(1 for v in items.values() if v.get("loading_type") == "exact")
    approx = sum(1 for v in items.values() if v.get("loading_type") == "approximate")
    none_ = sum(1 for v in items.values() if v.get("loading_type") == "none")
    print(f"\nLoading types: exact={exact}, approximate={approx}, none={none_}")

    # Construct coverage
    n_with_parent = sum(1 for v in items.values() if v.get("in_construct"))
    print(f"Items with parent construct: {n_with_parent}/{len(items)}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute WVS L0 (item-level) SES fingerprints"
    )
    parser.add_argument(
        "--country", default="MEX",
        help="ISO alpha-3 country code (default: MEX)",
    )
    parser.add_argument(
        "--wave", type=int, default=7,
        help="WVS wave number (default: 7)",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Output JSON path (default: data/results/wvs_l0_fingerprints.json)",
    )
    parser.add_argument(
        "--all-countries", action="store_true",
        help="Compute for all W7 countries (outputs separate files)",
    )
    parser.add_argument(
        "--wvs-dir", type=Path, default=None,
        help="Path to WVS data directory (default: data/wvs/ relative to project root)",
    )
    args = parser.parse_args()

    out = args.output or OUTPUT_PATH

    if args.all_countries:
        from wvs_metadata import CULTURAL_ZONES
        all_countries = sorted(
            c for zone_countries in CULTURAL_ZONES.values()
            for c in zone_countries
        )
        for alpha3 in all_countries:
            country_out = out.parent / f"wvs_l0_fingerprints_{alpha3}.json"
            print(f"\n{'=' * 60}")
            print(f"Processing {alpha3}...")
            try:
                compute_wvs_l0_fingerprints(
                    country=alpha3, wave=args.wave, output_path=country_out,
                    wvs_dir=args.wvs_dir,
                )
            except Exception as e:
                print(f"  ERROR: {e}")
    else:
        compute_wvs_l0_fingerprints(
            country=args.country, wave=args.wave, output_path=out,
            wvs_dir=args.wvs_dir,
        )
