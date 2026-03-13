"""
Stream 3 — Dimensionality Review

For the 4 constructs flagged as potentially multi-dimensional, computes:
  - Spearman inter-item correlation matrix
  - 2-component PCA (via numpy SVD) with loadings and variance explained
  - Recommendation: keep-as-is / split / simplify

Target constructs:
  EDU|digital_and_cultural_capital
  FED|fiscal_and_service_federalism_preferences
  CUL|political_efficacy_and_engagement
  DEP|attitudes_toward_cultural_openness_and_foreign_influence

Output: data/results/construct_dimensionality_review.md
Run:    python scripts/debug/dimensionality_review.py
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

OUT = ROOT / "data" / "results" / "construct_dimensionality_review.md"

TARGETS = [
    "EDU|digital_and_cultural_capital",
    "FED|fiscal_and_service_federalism_preferences",
    "CUL|political_efficacy_and_engagement",
    "DEP|attitudes_toward_cultural_openness_and_foreign_influence",
]


def _is_sentinel(v: float) -> bool:
    return v >= 97 or v < 0


def _clean(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    return s.where(~s.apply(lambda v: _is_sentinel(v) if pd.notna(v) else False))


def spearman_matrix(df_items: pd.DataFrame) -> pd.DataFrame:
    cols = df_items.columns.tolist()
    n = len(cols)
    mat = np.ones((n, n))
    pmat = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            pair = df_items[[cols[i], cols[j]]].dropna()
            if len(pair) < 10:
                mat[i, j] = mat[j, i] = np.nan
                pmat[i, j] = pmat[j, i] = np.nan
            else:
                r, p = sp_stats.spearmanr(pair.iloc[:, 0], pair.iloc[:, 1])
                mat[i, j] = mat[j, i] = r
                pmat[i, j] = pmat[j, i] = p
    return pd.DataFrame(mat, index=cols, columns=cols), pd.DataFrame(pmat, index=cols, columns=cols)


def pca_2comp(df_items: pd.DataFrame) -> dict:
    """
    Run 2-component PCA using numpy SVD on complete-case rows.
    Returns dict with loadings, variance_explained, n_rows.
    """
    clean = df_items.dropna()
    n = len(clean)
    if n < 10:
        return {"error": f"Only {n} complete rows — PCA not feasible"}

    X = clean.values.astype(float)
    # Standardize
    means = X.mean(axis=0)
    stds = X.std(axis=0, ddof=1)
    stds[stds == 0] = 1.0
    Z = (X - means) / stds

    # SVD
    try:
        U, S, Vt = np.linalg.svd(Z, full_matrices=False)
    except np.linalg.LinAlgError as e:
        return {"error": str(e)}

    var_exp = (S ** 2) / (S ** 2).sum()
    n_comp = min(2, len(S))
    loadings = Vt[:n_comp]  # shape: (n_comp, n_features)

    return {
        "n_rows": n,
        "n_items": len(df_items.columns),
        "variance_explained": var_exp[:n_comp].tolist(),
        "loadings": loadings.tolist(),
        "item_names": df_items.columns.tolist(),
    }


def interpret_pca(pca_result: dict) -> str:
    """
    Produce a text recommendation based on PCA result.
    """
    if "error" in pca_result:
        return f"PCA not feasible: {pca_result['error']}"

    ve = pca_result["variance_explained"]
    ve1 = ve[0] if len(ve) > 0 else 0
    ve2 = ve[1] if len(ve) > 1 else 0
    loadings = np.array(pca_result["loadings"])
    items = pca_result["item_names"]

    # PC1 loadings
    l1 = loadings[0] if len(loadings) > 0 else []
    l2 = loadings[1] if len(loadings) > 1 else []

    lines = [
        f"PC1 explains {ve1:.1%} of variance, PC2 explains {ve2:.1%} "
        f"(cumulative: {ve1+ve2:.1%})."
    ]

    if len(l1) == len(items):
        # Items loading positively vs negatively on PC1
        pc1_pos = [items[j] for j in range(len(items)) if l1[j] > 0.2]
        pc1_neg = [items[j] for j in range(len(items)) if l1[j] < -0.2]
        if pc1_neg:
            lines.append(f"PC1: items with positive loading: {pc1_pos}")
            lines.append(f"PC1: items with negative loading (may need reversal): {pc1_neg}")
        else:
            lines.append(f"PC1: all items load positively — unidimensional signal for: {pc1_pos}")

    # Dimensionality verdict
    if ve1 > 0.5:
        verdict = "**Verdict: KEEP — predominantly unidimensional** (PC1 > 50% variance). Consider dropping lowest-loading item(s) to improve α."
    elif ve2 > 0.20:
        # Check if PC2 has a clear structure
        if len(l2) == len(items):
            p2_pos = [items[j] for j in range(len(items)) if l2[j] > 0.3]
            p2_neg = [items[j] for j in range(len(items)) if l2[j] < -0.3]
            if p2_pos and p2_neg:
                verdict = (
                    f"**Verdict: SPLIT — two distinct dimensions detected** (PC2 = {ve2:.1%} variance). "
                    f"Dimension 1 items: {p2_pos}. Dimension 2 items: {p2_neg}."
                )
            else:
                verdict = f"**Verdict: SIMPLIFY — PC2 = {ve2:.1%}, but loadings not clearly separated. Drop lowest PC1-loading items.**"
        else:
            verdict = f"**Verdict: REVIEW — PC2 = {ve2:.1%} variance. Check loadings manually.**"
    else:
        verdict = f"**Verdict: KEEP — PC1 {ve1:.1%}, PC2 {ve2:.1%}. Acceptable unidimensionality.**"

    lines.append(verdict)
    return "\n".join(lines)


def format_corr_matrix(corr: pd.DataFrame, pval: pd.DataFrame, items: list[str]) -> str:
    lines = []
    header = "| item | " + " | ".join(items) + " |"
    sep = "|------|" + "|".join(["------"] * len(items)) + "|"
    lines.append(header)
    lines.append(sep)
    for row_item in items:
        cells = []
        for col_item in items:
            if row_item == col_item:
                cells.append("—")
            else:
                r = corr.loc[row_item, col_item]
                p = pval.loc[row_item, col_item]
                if np.isnan(r):
                    cells.append("n/a")
                else:
                    sig = "*" if p < 0.05 else ""
                    sig = "**" if p < 0.01 else sig
                    cells.append(f"{r:.2f}{sig}")
        lines.append(f"| `{row_item}` | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def format_loadings(pca_result: dict) -> str:
    if "error" in pca_result:
        return f"_{pca_result['error']}_"
    items = pca_result["item_names"]
    loadings = np.array(pca_result["loadings"])
    ve = pca_result["variance_explained"]
    n_comp = len(ve)

    header = "| item | " + " | ".join(f"PC{i+1} ({ve[i]:.1%})" for i in range(n_comp)) + " |"
    sep = "|------|" + "|".join(["------"] * n_comp) + "|"
    rows = [header, sep]
    for j, item in enumerate(items):
        vals = [f"{loadings[i][j]:+.3f}" for i in range(n_comp)]
        rows.append(f"| `{item}` | " + " | ".join(vals) + " |")
    return "\n".join(rows)


def main():
    print("Loading data...")
    from dataset_knowledge import enc_dict, enc_nom_dict
    from build_construct_variables import build_v4_constructs

    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    svs_path = ROOT / "data" / "results" / "semantic_variable_selection_v4.json"
    manifest_path = ROOT / "data" / "results" / "construct_variable_manifest.json"

    with open(svs_path) as f:
        svs = json.load(f)
    with open(manifest_path) as f:
        manifest_list = json.load(f)

    manifest = {m["key"]: m for m in manifest_list if m.get("key")}

    # Build SVS item lookup
    svs_items: dict[str, list[str]] = {}
    for domain, dom_data in svs.get("domains", {}).items():
        for cluster in dom_data.get("construct_clusters", []):
            key = f"{domain}|{cluster['name']}"
            raw = cluster.get("question_cluster", [])
            svs_items[key] = [q.split("|")[0] for q in raw]

    print("Building construct variables...")
    enc_dict, _ = build_v4_constructs(enc_dict, enc_nom_dict_rev)

    out_lines: list[str] = []
    out_lines.append("# Dimensionality Review — Stream 3\n\n")
    out_lines.append(
        "Inter-item Spearman correlations and 2-component PCA for constructs flagged as "
        "potentially multi-dimensional.\n\n"
        "**Significance**: * p<0.05, ** p<0.01\n\n"
    )
    out_lines.append("---\n\n")

    for ckey in TARGETS:
        domain = ckey.split("|")[0]
        survey_name = enc_nom_dict_rev.get(domain)
        m = manifest.get(ckey, {})
        alpha = m.get("alpha")
        alpha_str = f"{alpha:.4f}" if alpha is not None else "N/A"
        items = svs_items.get(ckey, [])

        print(f"  Processing {ckey}...")
        out_lines.append(f"## {ckey}  (α={alpha_str}, {m.get('type','?')})\n\n")

        if not survey_name or survey_name not in enc_dict:
            out_lines.append(f"_Survey not found for domain {domain}_\n\n---\n\n")
            continue

        if not items:
            out_lines.append("_No items in SVS v4_\n\n---\n\n")
            continue

        df = enc_dict[survey_name].get("dataframe")
        if not isinstance(df, pd.DataFrame):
            out_lines.append("_DataFrame not available_\n\n---\n\n")
            continue

        # Build cleaned item sub-dataframe
        available = [it for it in items if it in df.columns]
        if len(available) < 2:
            out_lines.append(f"_Only {len(available)} items available in dataframe — cannot assess dimensionality_\n\n---\n\n")
            continue

        sub = pd.DataFrame()
        for col in available:
            sub[col] = _clean(df[col])

        out_lines.append(f"**Items**: {available} (n={len(available)}, n_rows={len(sub.dropna())} complete)\n\n")

        # Inter-item correlations
        out_lines.append("### Inter-Item Spearman Correlation Matrix\n\n")
        if len(available) >= 2:
            corr, pval = spearman_matrix(sub)
            out_lines.append(format_corr_matrix(corr, pval, available) + "\n\n")

            # Mean inter-item r
            mask = np.triu(np.ones_like(corr.values, dtype=bool), k=1)
            upper = corr.values[mask]
            valid_r = upper[~np.isnan(upper)]
            if len(valid_r):
                out_lines.append(
                    f"Mean inter-item r = {valid_r.mean():.3f}, "
                    f"min = {valid_r.min():.3f}, max = {valid_r.max():.3f}\n\n"
                )

        # PCA
        out_lines.append("### 2-Component PCA\n\n")
        pca_result = pca_2comp(sub)
        if "error" in pca_result:
            out_lines.append(f"_{pca_result['error']}_\n\n")
        else:
            out_lines.append(format_loadings(pca_result) + "\n\n")
            interp = interpret_pca(pca_result)
            out_lines.append(interp + "\n\n")

        out_lines.append("---\n\n")

    with open(OUT, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
    print(f"\nDone — written to {OUT}")


if __name__ == "__main__":
    main()
