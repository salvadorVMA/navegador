"""
Stream 1 — Construct Diagnostics

For all 56 significant DR bridge constructs:
  1. Marginal distribution of the agg_* variable (mean, std, skew, value counts)
  2. Bivariate table: agg_* mean by each SES variable (sexo, edad, escol, Tam_loc)
  3. Alpha–gamma relationship: does higher alpha → higher |γ|?

Output: data/results/construct_diagnostics.md
Run:    python scripts/debug/construct_diagnostics.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "debug"))

OUT = ROOT / "data" / "results" / "construct_diagnostics.md"

SES_VARS = ["sexo", "edad", "escol", "Tam_loc"]
SES_LABELS = {
    "sexo":    {1: "Hombre", 2: "Mujer"},
    "edad":    {1: "18-25", 2: "26-35", 3: "36-45", 4: "46-55", 5: "56-65", 6: "66+"},
    "escol":   {1: "Ninguna", 2: "Primaria", 3: "Secundaria", 4: "Media sup.", 5: "Superior"},
    "Tam_loc": {1: "Rural (<2.5k)", 2: "Semi-urban", 3: "Urban", 4: "Metro"},
}


def _is_sentinel(v: float) -> bool:
    return v >= 97 or v < 0


def _clean(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    return s.where(~s.apply(lambda v: _is_sentinel(v) if pd.notna(v) else False))


def load_sweep(sweep_path: Path) -> list[dict]:
    """Return flat list of estimate dicts from the nested sweep JSON."""
    with open(sweep_path) as f:
        data = json.load(f)
    estimates = data.get("estimates", data)  # handle both old and new format
    if isinstance(estimates, dict):
        return list(estimates.values())
    return estimates  # already a list


def load_significant_constructs(sweep_path: Path) -> set[str]:
    pairs = load_sweep(sweep_path)
    sig = set()
    for p in pairs:
        ci = p.get("dr_gamma_ci", [p.get("ci_low"), p.get("ci_high")])
        if not ci or ci[0] is None:
            continue
        lo, hi = ci[0], ci[1]
        if lo > 0 or hi < 0:
            sig.add(p["construct_a"])
            sig.add(p["construct_b"])
    return sig


def load_manifest(path: Path) -> dict[str, dict]:
    with open(path) as f:
        items = json.load(f)
    return {m["key"]: m for m in items if m.get("key")}


def marginals(s: pd.Series) -> str:
    s = s.dropna()
    if len(s) == 0:
        return "  _no data_\n"
    lines = [
        f"  N={len(s)}, mean={s.mean():.2f}, std={s.std():.2f}, "
        f"min={s.min():.2f}, max={s.max():.2f}, "
        f"skew={s.skew():.2f}, kurt={s.kurt():.2f}",
    ]
    # Decile distribution
    deciles = s.quantile([0.1, 0.25, 0.5, 0.75, 0.9])
    lines.append(
        f"  P10={deciles[0.1]:.2f}, P25={deciles[0.25]:.2f}, "
        f"P50={deciles[0.5]:.2f}, P75={deciles[0.75]:.2f}, P90={deciles[0.9]:.2f}"
    )
    # Bucket into 5 bins
    try:
        counts = pd.cut(s, bins=5).value_counts().sort_index()
        bucket_str = "  | " + " | ".join(
            f"{iv}: {n}" for iv, n in counts.items()
        ) + " |"
        lines.append(bucket_str)
    except Exception:
        pass
    return "\n".join(lines) + "\n"


def bivariate_table(df: pd.DataFrame, agg_col: str, ses_var: str) -> str:
    if ses_var not in df.columns or agg_col not in df.columns:
        return f"  _{ses_var} not available_\n"
    sv = _clean(df[ses_var])
    av = df[agg_col]
    labels = SES_LABELS.get(ses_var, {})
    rows = []
    for code in sorted(sv.dropna().unique()):
        mask = sv == code
        grp = av[mask].dropna()
        if len(grp) == 0:
            continue
        label = labels.get(int(code), str(int(code)))
        rows.append(f"  {label} (n={len(grp)}): mean={grp.mean():.2f}, std={grp.std():.2f}")
    if not rows:
        return f"  _{ses_var}: no valid groups_\n"
    return "\n".join(rows) + "\n"


def alpha_gamma_analysis(
    sig_constructs: set[str],
    manifest: dict[str, dict],
    sweep_pairs: list[dict],
    out_lines: list[str],
) -> None:
    # For each significant construct, collect all its significant pairs' |γ|
    construct_gamma: dict[str, list[float]] = {c: [] for c in sig_constructs}
    for p in sweep_pairs:
        ci = p.get("dr_gamma_ci", [p.get("ci_low"), p.get("ci_high")])
        if not ci or ci[0] is None:
            continue
        lo, hi = ci[0], ci[1]
        if lo > 0 or hi < 0:
            g = abs(p.get("dr_gamma", p.get("gamma", 0)))
            for key in ("construct_a", "construct_b"):
                c = p.get(key)
                if c in construct_gamma:
                    construct_gamma[c].append(g)

    rows = []
    for c in sig_constructs:
        m = manifest.get(c, {})
        alpha = m.get("alpha")
        gammas = construct_gamma.get(c, [])
        if alpha is None or not gammas:
            continue
        rows.append({
            "construct": c,
            "alpha": alpha,
            "n_sig_edges": len(gammas),
            "mean_gamma": float(np.mean(gammas)),
            "max_gamma": float(np.max(gammas)),
        })

    if not rows:
        out_lines.append("_No data for alpha–gamma analysis_\n")
        return

    df = pd.DataFrame(rows).sort_values("alpha")
    alphas = df["alpha"].values
    mean_gammas = df["mean_gamma"].values
    max_gammas = df["max_gamma"].values

    r_mean, p_mean = sp_stats.spearmanr(alphas, mean_gammas)
    r_max, p_max = sp_stats.spearmanr(alphas, max_gammas)

    out_lines.append(
        f"**Spearman ρ(alpha, mean|γ|) = {r_mean:.3f}** (p={p_mean:.3f}, n={len(df)})\n\n"
        f"**Spearman ρ(alpha, max|γ|) = {r_max:.3f}** (p={p_max:.3f})\n\n"
    )
    out_lines.append(
        "Interpretation: ρ > 0 means higher-alpha constructs tend to show stronger SES-mediated "
        "co-variation with others. ρ ≈ 0 means reliability and bridge strength are orthogonal "
        "(a well-measured construct can still be SES-independent).\n\n"
    )

    # Table
    out_lines.append("| Construct | α | N sig edges | Mean \\|γ\\| | Max \\|γ\\| |\n")
    out_lines.append("|-----------|---|------------|-----------|----------|\n")
    for _, row in df.iterrows():
        out_lines.append(
            f"| {row['construct']} | {row['alpha']:.3f} | {row['n_sig_edges']} | "
            f"{row['mean_gamma']:.4f} | {row['max_gamma']:.4f} |\n"
        )
    out_lines.append("\n")


def main():
    print("Loading data...")
    from dataset_knowledge import enc_dict, enc_nom_dict
    from build_construct_variables import build_v4_constructs

    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    sweep_path = ROOT / "data" / "results" / "construct_dr_sweep.json"
    manifest_path = ROOT / "data" / "results" / "construct_variable_manifest.json"

    sweep_pairs = load_sweep(sweep_path)

    sig_constructs = load_significant_constructs(sweep_path)
    manifest = load_manifest(manifest_path)
    print(f"  {len(sig_constructs)} significant constructs found")

    print("Building construct variables...")
    enc_dict, _ = build_v4_constructs(enc_dict, enc_nom_dict_rev)

    out_lines: list[str] = []
    out_lines.append("# Construct Diagnostics — Stream 1\n\n")
    out_lines.append(
        "Frequency distributions and SES bivariate profiles for all 56 significant DR bridge constructs.\n\n"
    )
    out_lines.append(
        f"**Source**: `construct_dr_sweep.json` — {len(sweep_pairs)} pairs, "
        f"{len(sig_constructs)} constructs with at least one CI-excluding-zero edge.\n\n"
    )
    out_lines.append("---\n\n")

    # Sort by alpha descending (same order as significant_constructs.md)
    ordered = sorted(
        sig_constructs,
        key=lambda c: (manifest.get(c, {}).get("alpha") or -99),
        reverse=True,
    )

    for i, ckey in enumerate(ordered, 1):
        m = manifest.get(ckey, {})
        domain = ckey.split("|")[0]
        survey_name = enc_nom_dict_rev.get(domain)
        alpha = m.get("alpha")
        alpha_str = f"{alpha:.4f}" if alpha is not None else "N/A"
        ctype = m.get("type", "?")
        n_valid = m.get("n_valid", "?")
        agg_col = m.get("column")

        out_lines.append(f"## [{i:02d}] {ckey}  (α={alpha_str}, {ctype}, N={n_valid})\n\n")

        if not survey_name or survey_name not in enc_dict:
            out_lines.append(f"_Survey not found for domain {domain}_\n\n")
            print(f"  [{i:02d}] {ckey} — survey not found")
            continue

        df = enc_dict[survey_name].get("dataframe")
        if not isinstance(df, pd.DataFrame) or not agg_col or agg_col not in df.columns:
            out_lines.append(f"_agg column `{agg_col}` not found in dataframe_\n\n")
            print(f"  [{i:02d}] {ckey} — agg column missing")
            continue

        # ── Marginals ──
        out_lines.append("### Marginal Distribution\n\n")
        out_lines.append(marginals(df[agg_col]))
        out_lines.append("\n")

        # ── Bivariate SES ──
        out_lines.append("### Bivariate by SES Variable\n\n")
        for ses_var in SES_VARS:
            out_lines.append(f"**{ses_var}**\n\n")
            out_lines.append(bivariate_table(df, agg_col, ses_var))
            out_lines.append("\n")

        out_lines.append("---\n\n")
        print(f"  [{i:02d}] {ckey} done")

    # ── Alpha–gamma section ──
    out_lines.append("## Alpha–Gamma Relationship\n\n")
    out_lines.append(
        "Does internal consistency (α) predict bridge strength (|γ|)? "
        "Based on all significant pairs per construct.\n\n"
    )
    alpha_gamma_analysis(sig_constructs, manifest, sweep_pairs, out_lines)

    # Write output
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
    print(f"\nDone — written to {OUT}")


if __name__ == "__main__":
    main()
