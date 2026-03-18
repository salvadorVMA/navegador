"""
Phase 1: Compute SES fingerprints for all constructs and individual survey items.

A SES fingerprint is a 4-dimensional vector of Spearman ρ between a variable
and each of the 4 sociodemographic (SES) predictors:

    escol    — education level
    Tam_loc  — town size / urban-rural axis
    sexo     — gender
    edad     — age / cohort

All four are treated as SES dimensions with equal standing.  Gender and age
are not "demographic controls" separate from SES — they are dimensions of the
sociodemographic position that structures attitudes, access, and outcomes.
ses_magnitude is the RMS of the 4 ρ values: overall SES stratification
intensity regardless of which dimension drives it.  dominant_dim is the
single predictor with the largest |ρ|.

Three coverage levels are produced (bottom-up, L0 = finest grain):

  Level 0 — questions (individual survey items):  [USE WITH CAUTION]
      All raw survey question columns with 2–20 unique ordinal values.

      REVERSE-CODING CAVEAT: items coded 1=Yes/2=No (or similar inverted
      scales) will show ρ signs OPPOSITE to the construct they belong to.
      Check the `reverse_coded` flag before interpreting any L0 fingerprint:
        - reverse_coded=True  → ρ signs are inverted vs the concept direction;
                                 use parent_construct L1 fingerprint instead.
        - reverse_coded=False + in_construct=True → consistent with L1.
        - in_construct=False  → standalone item; interpret directly but note
                                 single-item reliability is lower than L1.

      FACTOR LOADINGS (`loading`, `loading_gamma`, and their `_abs` variants):
      For items that belong to a construct, two loadings are computed:

      loading = Spearman ρ(raw_item, agg_construct).
          Signed: negative for reverse-coded items (raw item anti-correlates
          with the scale). Uses the ρ estimand; NOT dimensionally consistent
          with γ bridge values (γ systematically ignores tied pairs and is
          1.05×–7× larger than ρ for the same relationship).

      loading_gamma = Goodman-Kruskal γ(raw_item, bin5(agg_construct)).
          Uses the same estimand as the Julia DR bridge:
          bin5 = rank-normalize → equal-frequency qcut to 5 bins.
          SIGNED: negative for reverse-coded items. Use the full signed product
          for prediction chains across the γ bridge:

              signal = loading_gamma_A × γ(A→B) × loading_gamma_B

          all three terms use the γ estimand, so the product is dimensionally
          consistent. Double negatives (both items RC) are correct — they
          cancel to a positive prediction.

  Level 1 — constructs (agg_* columns):  [AUTHORITATIVE]
      93 v4 manifest constructs, multi-item aggregates, sentinel-filtered,
      reverse-coded where specified in construct_v5_overrides.json.
      These fingerprints reflect the CONCEPTUAL direction of each scale
      (high score = more of the concept) and are safe to interpret directly.

      SES FINGERPRINT ALIGNMENT:
      Each construct has a 4D SES fingerprint [rho_escol, rho_Tam_loc,
      rho_sexo, rho_edad].  The sign of the bridge γ(A,B) is predicted by
      the DOT PRODUCT of the two fingerprint vectors at 99.4% accuracy.
      This is not a heuristic but the natural geometric interpretation:
      two constructs whose SES fingerprints point in the same 4D direction
      will be co-elevated by the same sociodemographic position → γ > 0.
      Opposite directions → γ < 0.  Near-orthogonal → γ ≈ 0.
      See fingerprint_dot and fingerprint_cos on bridge edges.

  Level 2 — domains:  [COARSE FALLBACK ONLY]
      Mean of construct fingerprints within each domain.  Averaging can cancel
      signals when constructs within a domain pull in opposite directions.
      Use only when no L1 or L0 match is available.

Lookup hierarchy for the agent:
  query → ChromaDB match → L1 construct fingerprint          [preferred]
                        → L0 item fingerprint, rc-checked    [if no construct]
                        → L2 domain fingerprint              [final fallback]

Output: data/results/ses_fingerprints.json

Usage:
    python scripts/debug/compute_ses_fingerprints.py
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

SES_VARS = ["sexo", "edad", "escol", "Tam_loc"]

_SKIP_PREFIXES = ("agg_",)
_SKIP_COLS = {
    "sexo", "edad", "escol", "Tam_loc", "region",
    "empleo", "est_civil", "income_quintile",
    "empleo_formality", "region_x_Tam_loc",
    "Pondi2", "folio", "consecutive", "id", "survey_id",
    "escol_orig", "Tam_loc_orig",
}

OUTPUT_PATH = ROOT / "data" / "results" / "ses_fingerprints.json"

_AGE_BIN_MAP = {
    "0-18": 1, "19-24": 2, "25-34": 3, "35-44": 4,
    "45-54": 5, "55-64": 6, "65+": 7,
}


# ─────────────────────────────────────────────────────────────
# Core fingerprint primitives
# ─────────────────────────────────────────────────────────────

def _bin5(s: pd.Series) -> pd.Series:
    """Rank-normalise → equal-frequency qcut to 5 bins.

    Mirrors the Julia bridge pipeline: midrank transform (ties get average
    rank) scaled to (0,1), then cut into 5 equal-frequency bins labelled
    1–5.  Returns NaN where input is NaN.
    """
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
    """Goodman-Kruskal γ via joint frequency table.

    Drops NaN pairwise.  Returns None if n < 10 or no non-tied pairs.
    Uses contingency-table algorithm: O(k_x × k_y) memory, fast for
    small-cardinality ordinal data (k_x ≤ 20, k_y = 5 for binned
    constructs).

    Ties are excluded from both numerator and denominator — this is the
    same estimand used by the Julia bridge, making γ(item, binned_construct)
    dimensionally consistent with γ(construct_A, construct_B).
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

def _spearman_rho(x: pd.Series, y: pd.Series) -> Optional[float]:
    """Spearman ρ, pairwise NaN omission. Returns None if n < 10."""
    mask = x.notna() & y.notna()
    if mask.sum() < 10:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rho, _ = spearmanr(x[mask], y[mask])
    return float(rho) if np.isfinite(rho) else None


def _clean_ses(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with clean numeric SES columns extracted from df.

    edad is derived from sd2 (continuous age 15–100) when absent —
    ses_analysis produces string categories, so we use the raw column
    directly (monotone with ordinal bins, Spearman-safe).
    Accepts the full survey DataFrame so sd2 is accessible.
    """
    ses_cols = [v for v in SES_VARS if v in df.columns]
    out = df[ses_cols].copy()
    for col in ses_cols:
        s = pd.to_numeric(out[col], errors="coerce")
        sentinel = s.apply(lambda v: (v >= 97 or v < 0) if pd.notna(v) else False)
        out[col] = s.where(~sentinel)

    if "edad" not in out.columns or out["edad"].dropna().empty:
        if "sd2" in df.columns:
            age_raw = pd.to_numeric(df["sd2"], errors="coerce")
            out["edad"] = age_raw.where(age_raw.between(15, 100))
        elif "edad" in out.columns:
            out["edad"] = out["edad"].map(_AGE_BIN_MAP)
    return out


def _fingerprint(series: pd.Series, ses_df: pd.DataFrame) -> Optional[Dict]:
    """Compute fingerprint dict for one variable against the 4 SES columns."""
    rhos = {}
    for sv in SES_VARS:
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
    return {**rhos, "ses_magnitude": round(magnitude, 4),
            "dominant_dim": dominant, "n_obs": int(series.dropna().shape[0])}


def _aggregate_fingerprints(per_survey: List[Dict]) -> Dict:
    """Median ρ across surveys; recompute magnitude and dominant_dim."""
    if not per_survey:
        return {}
    rho_keys = [k for k in per_survey[0] if k.startswith("rho_")]
    agg: Dict = {}
    for k in rho_keys:
        vals = [d[k] for d in per_survey if k in d]
        agg[k] = round(float(np.median(vals)), 4)

    present = [k for k in rho_keys if k in agg]
    agg["ses_magnitude"] = round(
        float(np.sqrt(np.mean([agg[k] ** 2 for k in present]))), 4
    )
    frozen = dict(agg)
    agg["dominant_dim"] = max(
        (k.replace("rho_", "") for k in present),
        key=lambda sv, _fp=frozen: abs(_fp[f"rho_{sv}"]),
    )
    agg["n_surveys"] = len(per_survey)
    agg["total_obs"] = sum(d.get("n_obs", 0) for d in per_survey)
    return agg


# ─────────────────────────────────────────────────────────────
# Level-specific collectors
# ─────────────────────────────────────────────────────────────

def _collect_construct_fps(
    enc_dict: dict,
    enc_nom_dict: dict,
    col_to_key: Dict[str, str],
) -> Dict[str, Dict]:
    """Level 2: one fingerprint per v4 construct (agg_* columns)."""
    per_construct: Dict[str, List[Dict]] = {}
    for survey_name, sd in enc_dict.items():
        df = sd.get("dataframe")
        if not isinstance(df, pd.DataFrame):
            continue
        if not enc_nom_dict.get(survey_name):
            continue
        ses_df = _clean_ses(df)
        for col in (c for c in df.columns if c.startswith("agg_")):
            key = col_to_key.get(col)
            if not key:
                continue
            fp = _fingerprint(df[col], ses_df)
            if fp:
                per_construct.setdefault(key, []).append(fp)

    return {k: agg for k, surveys in per_construct.items()
            if (agg := _aggregate_fingerprints(surveys))}


def _build_item_index(
    manifest: List[Dict],
    svs_path: Optional[Path] = None,
) -> Dict[str, Dict[str, tuple]]:
    """Build a complete index: {domain: {item_col: (construct_key, is_rc)}}.

    Covers all item sources:
      - selected_item   (tier2 single-item constructs)
      - gateway_items   (formative index constructs)
      - reverse_coded   (RC items in reflective scales)
      - question_cluster from SVS v4 (non-RC reflective scale items)
    """
    if svs_path is None:
        svs_path = ROOT / "data" / "results" / "semantic_variable_selection_v4.json"

    # Load SVS v4 for question_cluster coverage
    svs_clusters: Dict[str, Dict[str, List[str]]] = {}  # domain → {name → [items]}
    if svs_path.exists():
        with open(svs_path) as f:
            svs = json.load(f)
        for domain, dom_data in svs.get("domains", {}).items():
            svs_clusters[domain] = {}
            for c in dom_data.get("construct_clusters", []):
                items = [q.split("|")[0] for q in c.get("question_cluster", [])]
                svs_clusters[domain][c["name"]] = items

    index: Dict[str, Dict[str, tuple]] = {}  # domain → {col → (key, is_rc)}

    for entry in manifest:
        if not entry.get("column"):
            continue
        key = entry["key"]
        domain, cname = key.split("|", 1)
        d = index.setdefault(domain, {})

        reverse_list: List[str] = entry.get("reverse_coded") or []

        # tier2 selected_item
        if entry.get("selected_item"):
            col = entry["selected_item"]
            d[col] = (key, col in reverse_list)

        # formative gateway_items
        for col in (entry.get("gateway_items") or []):
            d[col] = (key, col in reverse_list)

        # RC items from manifest reverse_coded list
        for col in reverse_list:
            d[col] = (key, True)

        # Non-RC reflective items from SVS question_cluster
        for col in svs_clusters.get(domain, {}).get(cname, []):
            if col not in d:  # don't overwrite RC entries
                d[col] = (key, False)

    return index


def _find_parent_construct(
    col: str,
    domain: str,
    item_index: Dict[str, Dict[str, tuple]],
) -> tuple[Optional[str], bool]:
    """Look up (construct_key, reverse_coded) from the prebuilt item_index."""
    result = item_index.get(domain, {}).get(col)
    return result if result else (None, False)


def _item_construct_loading(
    item_series: pd.Series,
    construct_col: str,
    df: pd.DataFrame,
) -> Optional[float]:
    """Spearman r(item, construct_agg) — the factor loading of this item on its
    parent construct.  Signed: negative for reverse-coded items (raw item value
    runs opposite to the conceptual direction of the scale).

    This is the correct attenuation coefficient for the prediction chain:
        r(item_A, construct_A) × γ(A→B) × r(construct_B, item_B)
    """
    if construct_col not in df.columns:
        return None
    construct_series = df[construct_col]
    mask = item_series.notna() & construct_series.notna()
    if mask.sum() < 10:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rho, _ = spearmanr(item_series[mask], construct_series[mask])
    return round(float(rho), 4) if np.isfinite(rho) else None


def _collect_item_fps(
    enc_dict: dict,
    enc_nom_dict: dict,
    manifest: List[Dict],
    col_to_key: Dict[str, str],
    item_index: Optional[Dict] = None,
) -> Dict[str, Dict]:
    """Level 1: one fingerprint per individual ordinal survey question.

    For items that belong to a construct, computes two factor loadings:

      loading        = Spearman ρ(raw_item, agg_construct)
                       Signed (negative for RC items).  Uses the ρ estimand,
                       so is NOT dimensionally consistent with γ bridge values.

      loading_gamma  = Goodman-Kruskal γ(raw_item, bin5(agg_construct))
                       Uses the same estimand as the Julia DR bridge.
                       Dimensionally consistent for prediction chains:
                           |loading_gamma_A| × |γ(A→B)| × |loading_gamma_B|
                       The binned construct is pre-computed once per agg_col per
                       survey (rank-norm → 5 equal-frequency bins) then γ is
                       computed against the raw item.
    """
    key_to_agg: Dict[str, str] = {v: k for k, v in col_to_key.items()}
    _index = item_index or {}

    per_item: Dict[str, List[Dict]] = {}
    per_loading: Dict[str, List[float]] = {}
    per_loading_gamma: Dict[str, List[float]] = {}
    item_meta: Dict[str, Dict] = {}

    for survey_name, sd in enc_dict.items():
        df = sd.get("dataframe")
        if not isinstance(df, pd.DataFrame):
            continue
        domain = enc_nom_dict.get(survey_name)
        if not domain:
            continue
        ses_df = _clean_ses(df)

        # Pre-bin every agg_col present in this survey (once per construct per survey)
        binned_agg: Dict[str, pd.Series] = {}
        for agg_col in (c for c in df.columns if c.startswith("agg_")):
            binned_agg[agg_col] = _bin5(df[agg_col])

        question_cols = [
            c for c in df.columns
            if c not in _SKIP_COLS
            and not any(c.startswith(pfx) for pfx in _SKIP_PREFIXES)
            and not c.lower().startswith(
                ("folio", "consec", "pond", "peso", "weight", "wt_", "id_", "encuesta")
            )
        ]
        for col in question_cols:
            series = pd.to_numeric(df[col], errors="coerce")
            n_unique = series.dropna().nunique()
            if n_unique < 2 or n_unique > 20:
                continue
            item_key = f"{col}|{domain}"
            fp = _fingerprint(series, ses_df)
            if not fp:
                continue
            per_item.setdefault(item_key, []).append(fp)
            item_meta[item_key] = {"domain": domain, "survey": survey_name}

            # Factor loadings: only if parent construct agg_col is present
            parent_key, _ = _find_parent_construct(col, domain, _index)
            if parent_key:
                agg_col = key_to_agg.get(parent_key)
                if agg_col:
                    # ρ loading
                    loading = _item_construct_loading(series, agg_col, df)
                    if loading is not None:
                        per_loading.setdefault(item_key, []).append(loading)
                    # γ loading (dimensionally consistent with bridge)
                    binned = binned_agg.get(agg_col)
                    if binned is not None:
                        lg = _gk_gamma(series, binned)
                        if lg is not None:
                            per_loading_gamma.setdefault(item_key, []).append(lg)

    result: Dict[str, Dict] = {}
    for item_key, surveys in per_item.items():
        agg = _aggregate_fingerprints(surveys)
        if not agg:
            continue
        col, domain = item_key.split("|", 1) if "|" in item_key else (item_key, "")
        meta = item_meta.get(item_key, {})
        parent, is_rc = _find_parent_construct(col, domain, _index)

        # Aggregate loadings across surveys
        loading_vals = per_loading.get(item_key, [])
        loading = round(float(np.median(loading_vals)), 4) if loading_vals else None

        lg_vals = per_loading_gamma.get(item_key, [])
        loading_gamma = round(float(np.median(lg_vals)), 4) if lg_vals else None

        entry: Dict = {
            **agg,
            "domain":              meta.get("domain"),
            "survey":              meta.get("survey"),
            "in_construct":        parent is not None,
            "parent_construct":    parent,
            "reverse_coded":       is_rc,
            # ρ loading: r(raw_item, agg_construct). Signed — negative for RC items.
            # NOT dimensionally consistent with γ bridge values.
            "loading":             loading,
            "loading_abs":         round(abs(loading), 4) if loading is not None else None,
            # γ loading: γ(raw_item, bin5(agg_construct)).
            # Same estimand as Julia DR bridge — use for prediction chains:
            #   |loading_gamma_A| × |γ(A→B)| × |loading_gamma_B|
            "loading_gamma":       loading_gamma,
            "loading_gamma_abs":   round(abs(loading_gamma), 4) if loading_gamma is not None else None,
        }
        if is_rc:
            entry["interpret_warning"] = (
                "Item was reverse-coded when building its parent construct. "
                "Raw ρ signs here are INVERTED relative to the construct's "
                "conceptual direction (higher raw score = less of the concept). "
                "Use parent_construct L1 fingerprint for correct interpretation. "
                "loading is negative (raw item anti-correlates with construct scale)."
            )
        result[item_key] = entry
    return result


def _collect_domain_fps(construct_fps: Dict[str, Dict]) -> Dict[str, Dict]:
    """Level 2: mean of construct fingerprints within each domain."""
    by_domain: Dict[str, List[Dict]] = {}
    for key, fp in construct_fps.items():
        by_domain.setdefault(key.split("|")[0], []).append(fp)

    rho_keys = [f"rho_{sv}" for sv in SES_VARS]
    result: Dict[str, Dict] = {}
    for domain, fps_list in by_domain.items():
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
        agg["n_constructs"] = len(fps_list)
        result[domain] = agg
    return result


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def compute_fingerprints(output_path: Path = OUTPUT_PATH) -> dict:
    """Build L0/L1/L2 fingerprints and write ses_fingerprints.json.

    Level hierarchy (bottom-up):
      L0 — questions  (finest grain, individual survey items)
      L1 — constructs (authoritative, multi-item aggregates)
      L2 — domains    (coarsest, mean of constructs; fallback only)
    """
    from dataset_knowledge import enc_dict, enc_nom_dict  # noqa: PLC0415
    from scripts.debug.build_construct_variables import build_v4_constructs  # noqa: PLC0415

    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    print("Building v4 construct columns …")
    enc_dict, manifest = build_v4_constructs(enc_dict, enc_nom_dict_rev)

    col_to_key: Dict[str, str] = {
        entry["column"]: entry["key"]
        for entry in manifest if entry.get("column")
    }

    print("\nComputing Level 1 (construct) fingerprints …")
    construct_fps = _collect_construct_fps(enc_dict, enc_nom_dict, col_to_key)
    print(f"  {len(construct_fps)} construct fingerprints computed")

    item_index = _build_item_index(manifest)

    print("\nComputing Level 0 (question/item) fingerprints …")
    item_fps = _collect_item_fps(enc_dict, enc_nom_dict, manifest, col_to_key, item_index)
    print(f"  {len(item_fps)} item fingerprints computed")

    print("\nComputing Level 2 (domain) fingerprints …")
    domain_fps = _collect_domain_fps(construct_fps)
    print(f"  {len(domain_fps)} domain fingerprints computed")

    result = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "ses_vars": SES_VARS,
            "level_hierarchy": "L0=questions (items) → L1=constructs → L2=domains",
            "n_questions": len(item_fps),
            "n_constructs": len(construct_fps),
            "n_domains": len(domain_fps),
            "lookup_hierarchy": "L1 construct → L0 item (rc-checked) → L2 domain (fallback)",
            "description": (
                "Spearman ρ of each variable with each of 4 SES dimensions "
                "(escol, Tam_loc, sexo, edad — all treated equally as SES). "
                "ses_magnitude = RMS of the 4 rho values. "
                "dominant_dim = SES dimension with highest |rho|. "
                "The SES fingerprint is a 4D vector; two constructs whose "
                "fingerprints point in the same direction (positive dot product) "
                "will have γ > 0 on the bridge (99.4% accuracy). "
                "L0 items carry loading_gamma = γ(item, bin5(construct)): "
                "signed, γ-scale, dimensionally consistent with the DR bridge. "
                "Prediction chain: loading_gamma_A × γ(A→B) × loading_gamma_B "
                "(signed product; double negatives from RC items cancel correctly)."
            ),
        },
        "constructs": construct_fps,
        "items": item_fps,
        "domains": domain_fps,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    _print_report(construct_fps, domain_fps)
    print(f"\n  Output: {output_path}")
    return result


def _print_report(construct_fps: Dict, domain_fps: Dict) -> None:
    print("\n═══ SES Fingerprint Report ═══\n")
    print("Top 10 L1 constructs by SES magnitude:")
    ranked = sorted(construct_fps.items(), key=lambda x: -x[1].get("ses_magnitude", 0))
    for key, fp in ranked[:10]:
        dom, name = (key.split("|", 1) + [""])[:2]
        print(f"  {dom}|{name[:45]:45s}  mag={fp['ses_magnitude']:.3f}"
              f"  dom={fp['dominant_dim']:8s}"
              f"  rho_escol={fp.get('rho_escol', 0):+.3f}")

    print("\nL2 domain-level SES magnitudes:")
    for domain, fp in sorted(domain_fps.items(), key=lambda x: -x[1].get("ses_magnitude", 0)):
        print(f"  {domain:5s}  mag={fp['ses_magnitude']:.3f}"
              f"  dom={fp['dominant_dim']:8s}"
              f"  n_constructs={fp['n_constructs']}")


if __name__ == "__main__":
    compute_fingerprints()
