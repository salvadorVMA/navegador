"""
Phase 4.3 — γ-Surface Visualization

1. Country map in PCA space (colored by cultural zone)
2. Heatmap: construct-pairs × countries with dendrogram
3. Temporal ribbon plots for selected pairs (1981-2022)
4. Mexico trajectory in PCA space across waves

Output:
  data/results/gamma_surface_pca.png
  data/results/gamma_surface_heatmap.png
  data/results/gamma_surface_temporal.png
  data/results/gamma_surface_mex_trajectory.png

Run:
  conda run -n nvg_py13_env python scripts/debug/visualize_gamma_surface.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SURFACE_PATH = ROOT / "data" / "results" / "gamma_surface.json"
OUTPUT_DIR   = ROOT / "data" / "results"

from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

WAVE_YEARS = {1: 1982, 2: 1992, 3: 1996, 4: 2001, 5: 2007, 6: 2012, 7: 2018}

# Zone colors
ZONE_COLORS = {
    "Latin America": "#e41a1c",
    "English-speaking": "#377eb8",
    "Protestant Europe": "#4daf4a",
    "Catholic Europe": "#984ea3",
    "Orthodox/ex-Communist": "#ff7f00",
    "Confucian": "#a65628",
    "South/Southeast Asian": "#f781bf",
    "African-Islamic": "#999999",
    "Unknown": "#cccccc",
}


def load_surface() -> dict:
    with open(SURFACE_PATH) as f:
        return json.load(f)


def build_country_pair_matrix(surface: dict):
    """Build matrix: countries × pairs (values = γ) for Wave 7 WVS data."""
    # Collect all W7 WVS entries
    by_country_pair = defaultdict(dict)
    all_pairs = set()
    all_countries = set()

    for key, entry in surface.items():
        if entry.get("dataset") != "wvs" or entry.get("wave") != 7:
            continue
        country = entry["country"]
        # Extract pair from key: wvs::W7_XXX::pair_id
        parts = key.split("::", 2)
        if len(parts) < 3:
            continue
        pid = parts[2]
        by_country_pair[country][pid] = entry["gamma"]
        all_pairs.add(pid)
        all_countries.add(country)

    countries = sorted(all_countries)
    pairs = sorted(all_pairs)

    # Build matrix (NaN where missing)
    matrix = np.full((len(countries), len(pairs)), np.nan)
    for i, c in enumerate(countries):
        for j, p in enumerate(pairs):
            if p in by_country_pair[c]:
                matrix[i, j] = by_country_pair[c][p]

    return matrix, countries, pairs


def build_temporal_series(surface: dict):
    """Build temporal series for Mexico across waves."""
    by_pair_wave = defaultdict(dict)

    for key, entry in surface.items():
        if entry.get("dataset") != "wvs" or entry.get("country") != "MEX":
            continue
        wave = entry.get("wave")
        if wave is None:
            continue
        parts = key.split("::", 2)
        if len(parts) < 3:
            continue
        pid = parts[2]
        by_pair_wave[pid][wave] = {
            "gamma": entry["gamma"],
            "ci_lo": entry.get("ci_lo", 0),
            "ci_hi": entry.get("ci_hi", 0),
        }

    return by_pair_wave


def main():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Patch
        from scipy.cluster.hierarchy import dendrogram, linkage
        from sklearn.decomposition import PCA
        from sklearn.impute import SimpleImputer
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install: pip install matplotlib scipy scikit-learn")
        sys.exit(1)

    if not SURFACE_PATH.exists():
        print(f"ERROR: {SURFACE_PATH} not found. Run build_gamma_surface.py first.")
        sys.exit(1)

    data = load_surface()
    surface = data.get("surface", {})
    print(f"Surface entries: {len(surface)}")

    # ── 1. PCA of countries in γ-space ────────────────────────────────────
    matrix, countries, pairs = build_country_pair_matrix(surface)
    print(f"Country-pair matrix: {matrix.shape} ({len(countries)} countries × {len(pairs)} pairs)")

    if matrix.shape[0] >= 3 and matrix.shape[1] >= 3:
        # Impute NaN with column mean
        imputer = SimpleImputer(strategy="mean")
        matrix_imp = imputer.fit_transform(matrix)

        pca = PCA(n_components=min(3, matrix_imp.shape[0]))
        coords = pca.fit_transform(matrix_imp)

        fig, ax = plt.subplots(figsize=(12, 9))
        for i, c in enumerate(countries):
            zone = COUNTRY_ZONE.get(c, "Unknown")
            color = ZONE_COLORS.get(zone, "#cccccc")
            ax.scatter(coords[i, 0], coords[i, 1], c=color, s=80, alpha=0.8, edgecolors="black", linewidths=0.5)
            ax.annotate(c, (coords[i, 0], coords[i, 1]), fontsize=7,
                        ha="center", va="bottom", alpha=0.8)

        # Legend
        legend_patches = [Patch(facecolor=ZONE_COLORS[z], label=z)
                          for z in ZONE_COLORS if z != "Unknown"]
        ax.legend(handles=legend_patches, loc="upper left", fontsize=8, framealpha=0.8)

        ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
        ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
        ax.set_title("Countries in γ-Structure Space (WVS Wave 7)")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / "gamma_surface_pca.png", dpi=150)
        plt.close(fig)
        print(f"  Saved: gamma_surface_pca.png")
        print(f"  PC1: {pca.explained_variance_ratio_[0]*100:.1f}%  "
              f"PC2: {pca.explained_variance_ratio_[1]*100:.1f}%")

    # ── 2. Heatmap with dendrogram ────────────────────────────────────────
    if matrix.shape[0] >= 5 and matrix.shape[1] >= 5:
        matrix_imp = SimpleImputer(strategy="mean").fit_transform(matrix)

        # Select top-variance pairs for readability
        pair_vars = np.nanvar(matrix_imp, axis=0)
        top_idx = np.argsort(pair_vars)[-50:]  # top 50 most variable pairs
        mat_sub = matrix_imp[:, top_idx]
        pair_labels = [pairs[i][:40] for i in top_idx]

        fig, ax = plt.subplots(figsize=(20, 12))
        im = ax.imshow(mat_sub, aspect="auto", cmap="RdBu_r", vmin=-0.2, vmax=0.2)

        ax.set_yticks(range(len(countries)))
        ax.set_yticklabels(countries, fontsize=6)
        ax.set_xticks(range(len(pair_labels)))
        ax.set_xticklabels(pair_labels, fontsize=5, rotation=90)
        ax.set_title("γ Heatmap: Countries × Top-50 Variable Pairs (Wave 7)")
        fig.colorbar(im, ax=ax, label="γ", shrink=0.6)
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / "gamma_surface_heatmap.png", dpi=150)
        plt.close(fig)
        print(f"  Saved: gamma_surface_heatmap.png")

    # ── 3. Temporal ribbon plots ──────────────────────────────────────────
    temporal = build_temporal_series(surface)
    # Select pairs with data in 4+ waves and largest |mean γ|
    candidates = []
    for pid, wave_data in temporal.items():
        if len(wave_data) < 4:
            continue
        mean_g = np.mean([abs(v["gamma"]) for v in wave_data.values()])
        candidates.append((pid, mean_g, wave_data))
    candidates.sort(key=lambda x: -x[1])

    if candidates:
        n_plot = min(12, len(candidates))
        fig, axes = plt.subplots(3, 4, figsize=(20, 12), sharey=False)
        axes = axes.flatten()

        for idx in range(n_plot):
            pid, _, wave_data = candidates[idx]
            ax = axes[idx]
            ws = sorted(wave_data.keys())
            years = [WAVE_YEARS[w] for w in ws]
            gammas = [wave_data[w]["gamma"] for w in ws]
            ci_lo = [wave_data[w]["ci_lo"] for w in ws]
            ci_hi = [wave_data[w]["ci_hi"] for w in ws]

            ax.fill_between(years, ci_lo, ci_hi, alpha=0.2, color="steelblue")
            ax.plot(years, gammas, "o-", color="steelblue", markersize=4)
            ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
            ax.set_title(pid[:35], fontsize=7)
            ax.set_xlim(1978, 2024)
            ax.tick_params(labelsize=6)

        # Hide unused axes
        for idx in range(n_plot, len(axes)):
            axes[idx].set_visible(False)

        fig.suptitle("γ Temporal Evolution — Mexico (WVS 1981-2022)", fontsize=12)
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / "gamma_surface_temporal.png", dpi=150)
        plt.close(fig)
        print(f"  Saved: gamma_surface_temporal.png ({n_plot} pairs)")

    # ── 4. Mexico trajectory in PCA space ─────────────────────────────────
    if matrix.shape[0] >= 3:
        # Build per-wave Mexico vectors
        mex_waves = defaultdict(dict)
        for key, entry in surface.items():
            if entry.get("dataset") != "wvs" or entry.get("country") != "MEX":
                continue
            wave = entry.get("wave")
            if wave is None:
                continue
            parts = key.split("::", 2)
            if len(parts) < 3:
                continue
            pid = parts[2]
            if pid in set(pairs):
                j = pairs.index(pid)
                mex_waves[wave][j] = entry["gamma"]

        if len(mex_waves) >= 2:
            fig, ax = plt.subplots(figsize=(10, 8))
            wave_coords = {}
            for w in sorted(mex_waves.keys()):
                vec = np.full(len(pairs), np.nan)
                for j, g in mex_waves[w].items():
                    vec[j] = g
                # Impute missing with column means from W7 matrix
                for j in range(len(vec)):
                    if np.isnan(vec[j]):
                        col_vals = matrix_imp[:, j] if matrix.shape[0] > 0 else [0]
                        vec[j] = np.mean(col_vals)
                coord = pca.transform(vec.reshape(1, -1))[0]
                wave_coords[w] = coord

            # Plot trajectory
            ws = sorted(wave_coords.keys())
            xs = [wave_coords[w][0] for w in ws]
            ys = [wave_coords[w][1] for w in ws]
            ax.plot(xs, ys, "o-", color="#e41a1c", linewidth=2, markersize=8)
            for w, x, y in zip(ws, xs, ys):
                ax.annotate(f"W{w}\n({WAVE_YEARS.get(w, '')})",
                            (x, y), fontsize=8, ha="center", va="bottom")

            # Plot W7 countries as background
            for i, c in enumerate(countries):
                zone = COUNTRY_ZONE.get(c, "Unknown")
                color = ZONE_COLORS.get(zone, "#cccccc")
                ax.scatter(coords[i, 0], coords[i, 1], c=color, s=30, alpha=0.3)
                if c in ("USA", "JPN", "DEU", "BRA", "ARG", "CHN", "IND"):
                    ax.annotate(c, (coords[i, 0], coords[i, 1]), fontsize=6, alpha=0.5)

            ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
            ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
            ax.set_title("Mexico Trajectory in γ-Structure Space (1981-2022)")
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            fig.savefig(OUTPUT_DIR / "gamma_surface_mex_trajectory.png", dpi=150)
            plt.close(fig)
            print(f"  Saved: gamma_surface_mex_trajectory.png")

    print("\nDone.")


if __name__ == "__main__":
    main()
