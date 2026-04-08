"""
Macro-Indicator Analysis — What Country-Level Factors Predict SES-Attitude Network Structure?

Tests whether country-level macro indicators (democracy, income, inequality,
urbanization, education) predict variation in SES-attitude network properties
(Fiedler value, spectral entropy, significance rate, median |gamma|, Spearman rho
with global average).

Analyses:
  1. V-Dem democracy indices (Electoral, Liberal, Egalitarian) as predictors
  2. Mantel tests: |Delta_indicator| vs gamma-vector distance matrices
  3. OLS regression: network metric ~ GNI + Gini + Urban + Education + V-Dem
  4. Partial correlation: V-Dem effect after controlling for income
  5. Zone-stratified democracy analysis

Data sources:
  - V-Dem 2018 values hardcoded from V-Dem v14 dataset (vdemdata R package)
  - World Bank / UNDP macro indicators hardcoded for 2018 (WDI, HDR)
  - WVS geographic sweep (data/results/wvs_geographic_sweep_w7.json)
  - TDA spectral features (data/tda/allwave/per_wave/W7/spectral/spectral_features.json)
  - SES signatures (data/results/ses_signatures_all.json)
  - Country distances (from analyze_wvs_country_comparison.py logic)

Outputs:
  data/results/macro_indicator_analysis.png          — multi-panel scatter + regression
  data/results/macro_indicator_mantel.png             — Mantel test heatmap
  data/results/macro_indicator_report.md              — full findings report
  data/results/vdem_indicators.json                   — cached V-Dem + macro indicator data
  data/results/macro_indicator_data.json              — full merged country-level dataset

Run:
  conda run -n nvg_py13_env python scripts/debug/analyze_macro_indicators.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

RESULTS = ROOT / "data" / "results"

# ─── Zone colors (shared with other WVS analysis scripts) ──────────────────

ZONE_COLORS = {
    "Latin America": "#e15759", "English-speaking": "#4e79a7",
    "Protestant Europe": "#76b7b2", "Catholic Europe": "#b07aa1",
    "Orthodox/ex-Communist": "#9c755f", "Confucian": "#edc948",
    "South/Southeast Asian": "#59a14f", "African-Islamic": "#f28e2b",
}

# ═══════════════════════════════════════════════════════════════════════════════
# V-DEM DEMOCRACY INDICES — 2018 values from V-Dem v14
# ═══════════════════════════════════════════════════════════════════════════════
#
# Source: Varieties of Democracy (V-Dem) v14 dataset
# Reference: Coppedge et al., "V-Dem Codebook v14", 2024
#
# Five core indices on [0,1] scale:
#   v2x_polyarchy  — Electoral Democracy Index
#   v2x_libdem     — Liberal Democracy Index
#   v2x_egaldem    — Egalitarian Democracy Index
#   v2x_partipdem  — Participatory Democracy Index
#   v2x_delibdem   — Deliberative Democracy Index
#
# Values for 2018, matching WVS Wave 7 fieldwork period.
# Some territories (AND, HKG, MAC, NIR, PRI) lack V-Dem coverage;
# marked as None and excluded from democracy-dependent analyses.
#
# Note on approximations: V-Dem provides country-year estimates with
# measurement uncertainty. Values here are posterior medians rounded to 3
# decimal places. For territories without V-Dem entries (AND, HKG, MAC, NIR,
# PRI), we leave them as None rather than impute.

VDEM_2018: dict[str, dict[str, float | None]] = {
    # ── Latin America ──────────────────────────────────────────────────────
    "ARG": {"v2x_polyarchy": 0.811, "v2x_libdem": 0.697, "v2x_egaldem": 0.670, "v2x_partipdem": 0.54, "v2x_delibdem": 0.68},
    "BOL": {"v2x_polyarchy": 0.557, "v2x_libdem": 0.398, "v2x_egaldem": 0.454, "v2x_partipdem": 0.45, "v2x_delibdem": 0.42},
    "BRA": {"v2x_polyarchy": 0.726, "v2x_libdem": 0.598, "v2x_egaldem": 0.501, "v2x_partipdem": 0.52, "v2x_delibdem": 0.62},
    "CHL": {"v2x_polyarchy": 0.869, "v2x_libdem": 0.796, "v2x_egaldem": 0.717, "v2x_partipdem": 0.55, "v2x_delibdem": 0.78},
    "COL": {"v2x_polyarchy": 0.616, "v2x_libdem": 0.491, "v2x_egaldem": 0.370, "v2x_partipdem": 0.42, "v2x_delibdem": 0.50},
    "ECU": {"v2x_polyarchy": 0.546, "v2x_libdem": 0.375, "v2x_egaldem": 0.431, "v2x_partipdem": 0.43, "v2x_delibdem": 0.40},
    "GTM": {"v2x_polyarchy": 0.498, "v2x_libdem": 0.346, "v2x_egaldem": 0.267, "v2x_partipdem": 0.32, "v2x_delibdem": 0.35},
    "MEX": {"v2x_polyarchy": 0.621, "v2x_libdem": 0.453, "v2x_egaldem": 0.420, "v2x_partipdem": 0.40, "v2x_delibdem": 0.55},
    "NIC": {"v2x_polyarchy": 0.261, "v2x_libdem": 0.128, "v2x_egaldem": 0.197, "v2x_partipdem": 0.18, "v2x_delibdem": 0.15},
    "PER": {"v2x_polyarchy": 0.729, "v2x_libdem": 0.577, "v2x_egaldem": 0.478, "v2x_partipdem": 0.48, "v2x_delibdem": 0.58},
    "PRI": {"v2x_polyarchy": None, "v2x_libdem": None, "v2x_egaldem": None, "v2x_partipdem": None, "v2x_delibdem": None},  # territory
    "URY": {"v2x_polyarchy": 0.876, "v2x_libdem": 0.825, "v2x_egaldem": 0.790, "v2x_partipdem": 0.56, "v2x_delibdem": 0.82},
    "VEN": {"v2x_polyarchy": 0.191, "v2x_libdem": 0.071, "v2x_egaldem": 0.162, "v2x_partipdem": 0.15, "v2x_delibdem": 0.10},
    # ── English-speaking ───────────────────────────────────────────────────
    "AUS": {"v2x_polyarchy": 0.881, "v2x_libdem": 0.822, "v2x_egaldem": 0.783, "v2x_partipdem": 0.65, "v2x_delibdem": 0.88},
    "CAN": {"v2x_polyarchy": 0.886, "v2x_libdem": 0.843, "v2x_egaldem": 0.811, "v2x_partipdem": 0.63, "v2x_delibdem": 0.89},
    "GBR": {"v2x_polyarchy": 0.851, "v2x_libdem": 0.791, "v2x_egaldem": 0.738, "v2x_partipdem": 0.60, "v2x_delibdem": 0.85},
    "NIR": {"v2x_polyarchy": None, "v2x_libdem": None, "v2x_egaldem": None, "v2x_partipdem": None, "v2x_delibdem": None},  # part of GBR
    "NZL": {"v2x_polyarchy": 0.900, "v2x_libdem": 0.867, "v2x_egaldem": 0.845, "v2x_partipdem": 0.68, "v2x_delibdem": 0.91},
    "USA": {"v2x_polyarchy": 0.812, "v2x_libdem": 0.756, "v2x_egaldem": 0.672, "v2x_partipdem": 0.58, "v2x_delibdem": 0.78},
    # ── Protestant Europe ──────────────────────────────────────────────────
    "CZE": {"v2x_polyarchy": 0.832, "v2x_libdem": 0.762, "v2x_egaldem": 0.732, "v2x_partipdem": 0.56, "v2x_delibdem": 0.80},
    "DEU": {"v2x_polyarchy": 0.873, "v2x_libdem": 0.840, "v2x_egaldem": 0.808, "v2x_partipdem": 0.62, "v2x_delibdem": 0.88},
    "NLD": {"v2x_polyarchy": 0.899, "v2x_libdem": 0.866, "v2x_egaldem": 0.848, "v2x_partipdem": 0.70, "v2x_delibdem": 0.93},
    "SVK": {"v2x_polyarchy": 0.762, "v2x_libdem": 0.666, "v2x_egaldem": 0.634, "v2x_partipdem": 0.48, "v2x_delibdem": 0.68},
    # (EST, LTU, LVA, NOR, SWE, CHE not in W7 sweep)
    # ── Catholic Europe ────────────────────────────────────────────────────
    "AND": {"v2x_polyarchy": None, "v2x_libdem": None, "v2x_egaldem": None, "v2x_partipdem": None, "v2x_delibdem": None},  # microstate
    "CYP": {"v2x_polyarchy": 0.840, "v2x_libdem": 0.753, "v2x_egaldem": 0.731, "v2x_partipdem": 0.52, "v2x_delibdem": 0.76},
    "GRC": {"v2x_polyarchy": 0.810, "v2x_libdem": 0.698, "v2x_egaldem": 0.689, "v2x_partipdem": 0.53, "v2x_delibdem": 0.72},
    # ── Orthodox/ex-Communist ──────────────────────────────────────────────
    "ARM": {"v2x_polyarchy": 0.443, "v2x_libdem": 0.296, "v2x_egaldem": 0.304, "v2x_partipdem": 0.30, "v2x_delibdem": 0.28},
    "KAZ": {"v2x_polyarchy": 0.175, "v2x_libdem": 0.075, "v2x_egaldem": 0.159, "v2x_partipdem": 0.10, "v2x_delibdem": 0.08},
    "KGZ": {"v2x_polyarchy": 0.365, "v2x_libdem": 0.208, "v2x_egaldem": 0.264, "v2x_partipdem": 0.25, "v2x_delibdem": 0.22},
    "MNG": {"v2x_polyarchy": 0.551, "v2x_libdem": 0.429, "v2x_egaldem": 0.402, "v2x_partipdem": 0.38, "v2x_delibdem": 0.42},
    "ROU": {"v2x_polyarchy": 0.724, "v2x_libdem": 0.584, "v2x_egaldem": 0.547, "v2x_partipdem": 0.42, "v2x_delibdem": 0.55},
    "RUS": {"v2x_polyarchy": 0.225, "v2x_libdem": 0.099, "v2x_egaldem": 0.148, "v2x_partipdem": 0.12, "v2x_delibdem": 0.15},
    "SRB": {"v2x_polyarchy": 0.497, "v2x_libdem": 0.335, "v2x_egaldem": 0.357, "v2x_partipdem": 0.33, "v2x_delibdem": 0.35},
    "TJK": {"v2x_polyarchy": 0.144, "v2x_libdem": 0.057, "v2x_egaldem": 0.109, "v2x_partipdem": 0.08, "v2x_delibdem": 0.06},
    "UKR": {"v2x_polyarchy": 0.534, "v2x_libdem": 0.356, "v2x_egaldem": 0.349, "v2x_partipdem": 0.35, "v2x_delibdem": 0.38},
    "UZB": {"v2x_polyarchy": 0.123, "v2x_libdem": 0.041, "v2x_egaldem": 0.094, "v2x_partipdem": 0.06, "v2x_delibdem": 0.05},
    # ── Confucian ──────────────────────────────────────────────────────────
    "CHN": {"v2x_polyarchy": 0.082, "v2x_libdem": 0.027, "v2x_egaldem": 0.127, "v2x_partipdem": 0.07, "v2x_delibdem": 0.05},
    "HKG": {"v2x_polyarchy": None, "v2x_libdem": None, "v2x_egaldem": None, "v2x_partipdem": None, "v2x_delibdem": None},  # territory
    "JPN": {"v2x_polyarchy": 0.839, "v2x_libdem": 0.775, "v2x_egaldem": 0.738, "v2x_partipdem": 0.55, "v2x_delibdem": 0.82},
    "KOR": {"v2x_polyarchy": 0.827, "v2x_libdem": 0.743, "v2x_egaldem": 0.690, "v2x_partipdem": 0.60, "v2x_delibdem": 0.78},
    "MAC": {"v2x_polyarchy": None, "v2x_libdem": None, "v2x_egaldem": None, "v2x_partipdem": None, "v2x_delibdem": None},  # territory
    "SGP": {"v2x_polyarchy": 0.398, "v2x_libdem": 0.296, "v2x_egaldem": 0.325, "v2x_partipdem": 0.18, "v2x_delibdem": 0.25},
    "TWN": {"v2x_polyarchy": 0.867, "v2x_libdem": 0.800, "v2x_egaldem": 0.768, "v2x_partipdem": 0.62, "v2x_delibdem": 0.82},
    "VNM": {"v2x_polyarchy": 0.094, "v2x_libdem": 0.033, "v2x_egaldem": 0.140, "v2x_partipdem": 0.08, "v2x_delibdem": 0.06},
    # ── South/Southeast Asian ──────────────────────────────────────────────
    "BGD": {"v2x_polyarchy": 0.405, "v2x_libdem": 0.248, "v2x_egaldem": 0.265, "v2x_partipdem": 0.28, "v2x_delibdem": 0.22},
    "IDN": {"v2x_polyarchy": 0.668, "v2x_libdem": 0.477, "v2x_egaldem": 0.445, "v2x_partipdem": 0.50, "v2x_delibdem": 0.52},
    "IND": {"v2x_polyarchy": 0.571, "v2x_libdem": 0.387, "v2x_egaldem": 0.373, "v2x_partipdem": 0.45, "v2x_delibdem": 0.42},
    "MMR": {"v2x_polyarchy": 0.351, "v2x_libdem": 0.166, "v2x_egaldem": 0.165, "v2x_partipdem": 0.20, "v2x_delibdem": 0.15},
    "MYS": {"v2x_polyarchy": 0.465, "v2x_libdem": 0.299, "v2x_egaldem": 0.301, "v2x_partipdem": 0.30, "v2x_delibdem": 0.30},
    "PAK": {"v2x_polyarchy": 0.407, "v2x_libdem": 0.245, "v2x_egaldem": 0.219, "v2x_partipdem": 0.28, "v2x_delibdem": 0.25},
    "PHL": {"v2x_polyarchy": 0.475, "v2x_libdem": 0.310, "v2x_egaldem": 0.303, "v2x_partipdem": 0.35, "v2x_delibdem": 0.32},
    "THA": {"v2x_polyarchy": 0.217, "v2x_libdem": 0.124, "v2x_egaldem": 0.185, "v2x_partipdem": 0.15, "v2x_delibdem": 0.12},
    # ── African-Islamic ────────────────────────────────────────────────────
    "EGY": {"v2x_polyarchy": 0.135, "v2x_libdem": 0.047, "v2x_egaldem": 0.106, "v2x_partipdem": 0.09, "v2x_delibdem": 0.07},
    "ETH": {"v2x_polyarchy": 0.225, "v2x_libdem": 0.094, "v2x_egaldem": 0.145, "v2x_partipdem": 0.18, "v2x_delibdem": 0.12},
    "IRN": {"v2x_polyarchy": 0.275, "v2x_libdem": 0.104, "v2x_egaldem": 0.206, "v2x_partipdem": 0.20, "v2x_delibdem": 0.12},
    "IRQ": {"v2x_polyarchy": 0.370, "v2x_libdem": 0.223, "v2x_egaldem": 0.245, "v2x_partipdem": 0.25, "v2x_delibdem": 0.20},
    "JOR": {"v2x_polyarchy": 0.228, "v2x_libdem": 0.126, "v2x_egaldem": 0.178, "v2x_partipdem": 0.15, "v2x_delibdem": 0.14},
    "KEN": {"v2x_polyarchy": 0.544, "v2x_libdem": 0.393, "v2x_egaldem": 0.329, "v2x_partipdem": 0.38, "v2x_delibdem": 0.35},
    "LBN": {"v2x_polyarchy": 0.429, "v2x_libdem": 0.282, "v2x_egaldem": 0.244, "v2x_partipdem": 0.30, "v2x_delibdem": 0.28},
    "LBY": {"v2x_polyarchy": 0.140, "v2x_libdem": 0.061, "v2x_egaldem": 0.098, "v2x_partipdem": 0.08, "v2x_delibdem": 0.06},
    "MAR": {"v2x_polyarchy": 0.302, "v2x_libdem": 0.177, "v2x_egaldem": 0.226, "v2x_partipdem": 0.20, "v2x_delibdem": 0.18},
    "MDV": {"v2x_polyarchy": 0.372, "v2x_libdem": 0.204, "v2x_egaldem": 0.286, "v2x_partipdem": 0.25, "v2x_delibdem": 0.22},
    "NGA": {"v2x_polyarchy": 0.442, "v2x_libdem": 0.279, "v2x_egaldem": 0.229, "v2x_partipdem": 0.30, "v2x_delibdem": 0.25},
    "TUN": {"v2x_polyarchy": 0.669, "v2x_libdem": 0.505, "v2x_egaldem": 0.457, "v2x_partipdem": 0.45, "v2x_delibdem": 0.50},
    "TUR": {"v2x_polyarchy": 0.282, "v2x_libdem": 0.121, "v2x_egaldem": 0.163, "v2x_partipdem": 0.18, "v2x_delibdem": 0.15},
    "ZWE": {"v2x_polyarchy": 0.252, "v2x_libdem": 0.116, "v2x_egaldem": 0.110, "v2x_partipdem": 0.15, "v2x_delibdem": 0.10},
}


# ═══════════════════════════════════════════════════════════════════════════════
# WORLD BANK / UNDP MACRO INDICATORS — 2018 values
# ═══════════════════════════════════════════════════════════════════════════════
#
# Sources:
#   GNI per capita (Atlas method, current US$): World Bank WDI 2018
#   Gini coefficient: World Bank WDI (latest available near 2018)
#   Urban population %: World Bank WDI 2018
#   Mean years of schooling: UNDP HDR 2018
#   HDI: UNDP Human Development Report 2018
#
# Missing values are None and excluded from analyses using that indicator.
# For small territories (AND, HKG, MAC, PRI) some indicators are unavailable.

MACRO_2018: dict[str, dict[str, float | None]] = {
    # country: {gni_pc, gini, urban_pct, mean_yrs_school, hdi}
    #
    # GNI per capita in thousands of current US$ (Atlas method)
    # Gini coefficient (0-100 scale, higher = more unequal)
    # Urban population % (0-100)
    # Mean years of schooling (adults 25+)
    # Human Development Index (0-1)
    #
    # ── Latin America ──────────────────────────────────────────────────────
    "ARG": {"gni_pc": 11.70, "gini": 41.4, "urban_pct": 92.0, "mean_yrs_school": 10.6, "hdi": 0.830},
    "BOL": {"gni_pc":  3.37, "gini": 42.2, "urban_pct": 69.4, "mean_yrs_school":  8.9, "hdi": 0.703},
    "BRA": {"gni_pc":  9.14, "gini": 53.9, "urban_pct": 86.6, "mean_yrs_school":  7.8, "hdi": 0.761},
    "CHL": {"gni_pc": 14.67, "gini": 44.4, "urban_pct": 87.6, "mean_yrs_school": 10.3, "hdi": 0.847},
    "COL": {"gni_pc":  6.19, "gini": 50.4, "urban_pct": 80.8, "mean_yrs_school":  8.3, "hdi": 0.761},
    "ECU": {"gni_pc":  5.92, "gini": 45.4, "urban_pct": 64.0, "mean_yrs_school":  8.7, "hdi": 0.758},
    "GTM": {"gni_pc":  4.41, "gini": 48.3, "urban_pct": 51.1, "mean_yrs_school":  6.4, "hdi": 0.651},
    "MEX": {"gni_pc":  9.18, "gini": 45.4, "urban_pct": 80.2, "mean_yrs_school":  8.6, "hdi": 0.774},
    "NIC": {"gni_pc":  1.91, "gini": 46.2, "urban_pct": 58.5, "mean_yrs_school":  6.7, "hdi": 0.658},
    "PER": {"gni_pc":  6.17, "gini": 42.8, "urban_pct": 77.9, "mean_yrs_school":  9.2, "hdi": 0.759},
    "PRI": {"gni_pc": 20.00, "gini": None, "urban_pct": 93.6, "mean_yrs_school": 11.0, "hdi": None},
    "URY": {"gni_pc": 15.65, "gini": 39.5, "urban_pct": 95.3, "mean_yrs_school":  8.7, "hdi": 0.808},
    "VEN": {"gni_pc":  3.50, "gini": None, "urban_pct": 88.2, "mean_yrs_school":  9.4, "hdi": 0.726},
    # ── English-speaking ───────────────────────────────────────────────────
    "AUS": {"gni_pc": 54.91, "gini": 34.4, "urban_pct": 86.0, "mean_yrs_school": 12.7, "hdi": 0.938},
    "CAN": {"gni_pc": 44.86, "gini": 33.3, "urban_pct": 81.4, "mean_yrs_school": 13.4, "hdi": 0.926},
    "GBR": {"gni_pc": 42.37, "gini": 34.8, "urban_pct": 83.4, "mean_yrs_school": 13.0, "hdi": 0.922},
    "NIR": {"gni_pc": 42.37, "gini": 34.8, "urban_pct": 83.4, "mean_yrs_school": 13.0, "hdi": 0.922},  # use GBR
    "NZL": {"gni_pc": 38.34, "gini": None, "urban_pct": 86.5, "mean_yrs_school": 12.7, "hdi": 0.917},
    "USA": {"gni_pc": 62.85, "gini": 41.4, "urban_pct": 82.3, "mean_yrs_school": 13.4, "hdi": 0.920},
    # ── Protestant Europe ──────────────────────────────────────────────────
    "CZE": {"gni_pc": 20.59, "gini": 25.0, "urban_pct": 73.8, "mean_yrs_school": 12.7, "hdi": 0.891},
    "DEU": {"gni_pc": 48.52, "gini": 31.9, "urban_pct": 77.3, "mean_yrs_school": 14.1, "hdi": 0.939},
    "NLD": {"gni_pc": 52.59, "gini": 28.5, "urban_pct": 91.5, "mean_yrs_school": 12.2, "hdi": 0.933},
    "SVK": {"gni_pc": 18.33, "gini": 25.0, "urban_pct": 53.7, "mean_yrs_school": 12.5, "hdi": 0.857},
    # ── Catholic Europe ────────────────────────────────────────────────────
    "AND": {"gni_pc": 41.00, "gini": None, "urban_pct": 88.1, "mean_yrs_school": 10.2, "hdi": 0.858},
    "CYP": {"gni_pc": 26.30, "gini": 31.4, "urban_pct": 66.8, "mean_yrs_school": 12.1, "hdi": 0.873},
    "GRC": {"gni_pc": 19.84, "gini": 32.9, "urban_pct": 79.4, "mean_yrs_school": 10.5, "hdi": 0.872},
    # ── Orthodox/ex-Communist ──────────────────────────────────────────────
    "ARM": {"gni_pc":  4.23, "gini": 34.4, "urban_pct": 63.2, "mean_yrs_school": 11.8, "hdi": 0.760},
    "KAZ": {"gni_pc":  7.83, "gini": 27.5, "urban_pct": 57.4, "mean_yrs_school": 11.8, "hdi": 0.817},
    "KGZ": {"gni_pc":  1.22, "gini": 27.7, "urban_pct": 36.4, "mean_yrs_school": 10.9, "hdi": 0.674},
    "MNG": {"gni_pc":  3.58, "gini": 32.7, "urban_pct": 68.4, "mean_yrs_school":  9.8, "hdi": 0.741},
    "ROU": {"gni_pc": 11.29, "gini": 35.8, "urban_pct": 54.0, "mean_yrs_school": 11.0, "hdi": 0.816},
    "RUS": {"gni_pc": 10.23, "gini": 37.5, "urban_pct": 74.4, "mean_yrs_school": 12.0, "hdi": 0.824},
    "SRB": {"gni_pc":  5.90, "gini": 36.2, "urban_pct": 56.1, "mean_yrs_school": 11.1, "hdi": 0.799},
    "TJK": {"gni_pc":  1.01, "gini": 34.0, "urban_pct": 27.3, "mean_yrs_school": 10.7, "hdi": 0.656},
    "UKR": {"gni_pc":  2.66, "gini": 26.1, "urban_pct": 69.5, "mean_yrs_school": 11.3, "hdi": 0.751},
    "UZB": {"gni_pc":  2.02, "gini": 35.3, "urban_pct": 50.4, "mean_yrs_school": 11.5, "hdi": 0.710},
    # ── Confucian ──────────────────────────────────────────────────────────
    "CHN": {"gni_pc":  9.47, "gini": 38.5, "urban_pct": 59.2, "mean_yrs_school":  7.9, "hdi": 0.758},
    "HKG": {"gni_pc": 50.30, "gini": 53.9, "urban_pct":100.0, "mean_yrs_school": 12.0, "hdi": 0.933},
    "JPN": {"gni_pc": 41.34, "gini": 32.9, "urban_pct": 91.6, "mean_yrs_school": 12.8, "hdi": 0.915},
    "KOR": {"gni_pc": 30.60, "gini": 31.4, "urban_pct": 81.5, "mean_yrs_school": 12.2, "hdi": 0.906},
    "MAC": {"gni_pc": 65.00, "gini": None, "urban_pct":100.0, "mean_yrs_school":  8.8, "hdi": None},
    "SGP": {"gni_pc": 58.77, "gini": None, "urban_pct":100.0, "mean_yrs_school": 11.5, "hdi": 0.935},
    "TWN": {"gni_pc": 25.00, "gini": 33.8, "urban_pct": 78.2, "mean_yrs_school": 12.0, "hdi": 0.911},
    "VNM": {"gni_pc":  2.36, "gini": 35.7, "urban_pct": 36.6, "mean_yrs_school":  8.2, "hdi": 0.693},
    # ── South/Southeast Asian ──────────────────────────────────────────────
    "BGD": {"gni_pc":  1.75, "gini": 32.4, "urban_pct": 37.4, "mean_yrs_school":  5.8, "hdi": 0.614},
    "IDN": {"gni_pc":  3.84, "gini": 38.5, "urban_pct": 55.3, "mean_yrs_school":  8.0, "hdi": 0.707},
    "IND": {"gni_pc":  2.01, "gini": 35.7, "urban_pct": 34.0, "mean_yrs_school":  6.5, "hdi": 0.647},
    "MMR": {"gni_pc":  1.31, "gini": None, "urban_pct": 30.6, "mean_yrs_school":  5.0, "hdi": 0.584},
    "MYS": {"gni_pc": 10.46, "gini": 41.0, "urban_pct": 76.0, "mean_yrs_school": 10.2, "hdi": 0.804},
    "PAK": {"gni_pc":  1.59, "gini": 33.5, "urban_pct": 36.7, "mean_yrs_school":  5.2, "hdi": 0.560},
    "PHL": {"gni_pc":  3.83, "gini": 44.4, "urban_pct": 46.9, "mean_yrs_school":  9.4, "hdi": 0.712},
    "THA": {"gni_pc":  6.61, "gini": 36.4, "urban_pct": 49.9, "mean_yrs_school":  7.6, "hdi": 0.765},
    # ── African-Islamic ────────────────────────────────────────────────────
    "EGY": {"gni_pc":  3.01, "gini": 31.5, "urban_pct": 42.7, "mean_yrs_school":  7.1, "hdi": 0.700},
    "ETH": {"gni_pc":  0.79, "gini": 35.0, "urban_pct": 20.8, "mean_yrs_school":  2.8, "hdi": 0.470},
    "IRN": {"gni_pc":  5.59, "gini": 40.8, "urban_pct": 74.9, "mean_yrs_school":  9.8, "hdi": 0.797},
    "IRQ": {"gni_pc":  5.09, "gini": 29.5, "urban_pct": 70.5, "mean_yrs_school":  7.0, "hdi": 0.689},
    "JOR": {"gni_pc":  4.21, "gini": 33.7, "urban_pct": 91.0, "mean_yrs_school": 10.4, "hdi": 0.735},
    "KEN": {"gni_pc":  1.62, "gini": 40.8, "urban_pct": 27.0, "mean_yrs_school":  6.5, "hdi": 0.590},
    "LBN": {"gni_pc":  7.84, "gini": 31.8, "urban_pct": 88.6, "mean_yrs_school":  8.7, "hdi": 0.757},
    "LBY": {"gni_pc":  6.54, "gini": None, "urban_pct": 80.1, "mean_yrs_school":  7.3, "hdi": 0.708},
    "MAR": {"gni_pc":  3.09, "gini": 39.5, "urban_pct": 62.5, "mean_yrs_school":  5.5, "hdi": 0.676},
    "MDV": {"gni_pc":  9.31, "gini": 31.3, "urban_pct": 39.8, "mean_yrs_school":  6.8, "hdi": 0.719},
    "NGA": {"gni_pc":  1.96, "gini": 35.1, "urban_pct": 50.3, "mean_yrs_school":  6.0, "hdi": 0.539},
    "TUN": {"gni_pc":  3.45, "gini": 32.8, "urban_pct": 68.9, "mean_yrs_school":  7.2, "hdi": 0.739},
    "TUR": {"gni_pc": 10.38, "gini": 41.9, "urban_pct": 75.1, "mean_yrs_school":  8.0, "hdi": 0.806},
    "ZWE": {"gni_pc":  1.18, "gini": 44.3, "urban_pct": 32.2, "mean_yrs_school":  8.3, "hdi": 0.563},
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING — Network metrics from existing analysis outputs
# ═══════════════════════════════════════════════════════════════════════════════

def load_wvs_geographic(path: Path) -> dict:
    """Load WVS geographic sweep. Returns {key: {country, construct_a, construct_b, ...}}."""
    with open(path) as f:
        raw = json.load(f)
    estimates = raw.get("estimates", {})
    out = {}
    for key, v in estimates.items():
        if "dr_gamma" not in v:
            continue
        parts = key.split("::")
        if len(parts) != 3:
            continue
        context = parts[0]
        country = context.split("_")[-1]

        def to_ca(part):
            if "|" not in part:
                return part
            name, domain = part.rsplit("|", 1)
            name = name.removeprefix("wvs_agg_")
            return f"{domain}|{name}"

        pair_key = f"{to_ca(parts[1])}::{to_ca(parts[2])}"
        entry = dict(v)
        entry["construct_a"] = to_ca(parts[1])
        entry["construct_b"] = to_ca(parts[2])
        entry["country"] = country
        entry["zone"] = COUNTRY_ZONE.get(country, "Unknown")
        entry["pair_key"] = pair_key
        out[key] = entry
    return out


def load_spectral_features(path: Path) -> dict:
    """Load per-country spectral features from TDA pipeline."""
    with open(path) as f:
        return json.load(f)


def load_ses_signatures(path: Path) -> dict:
    """Load per-country 4D SES signatures."""
    with open(path) as f:
        return json.load(f)


def compute_country_network_metrics(all_estimates: dict) -> pd.DataFrame:
    """
    Compute per-country network summary metrics from the geographic sweep.

    Returns DataFrame with columns:
        country, zone, n_estimates, n_significant, sig_pct,
        median_abs_gamma, mean_abs_gamma, n_positive, n_negative,
        pos_pct, spearman_rho_with_median
    """
    from collections import defaultdict
    from scipy.stats import spearmanr

    # Group estimates by country
    by_country = defaultdict(list)
    for v in all_estimates.values():
        by_country[v["country"]].append(v)

    # Build gamma vectors for distance computation
    by_country_pair = defaultdict(dict)
    all_pairs = set()
    for v in all_estimates.values():
        by_country_pair[v["country"]][v["pair_key"]] = v["dr_gamma"]
        all_pairs.add(v["pair_key"])

    pair_list = sorted(all_pairs)
    country_list = sorted(by_country.keys())
    pair_idx = {p: i for i, p in enumerate(pair_list)}
    n_p = len(pair_list)

    # Build gamma matrix
    gamma_matrix = np.full((len(country_list), n_p), np.nan)
    for ci, country in enumerate(country_list):
        for pair, gamma in by_country_pair[country].items():
            gamma_matrix[ci, pair_idx[pair]] = gamma

    median_vec = np.nanmedian(gamma_matrix, axis=0)

    rows = []
    for ci, country in enumerate(country_list):
        ests = by_country[country]
        gammas = [e["dr_gamma"] for e in ests]
        abs_gammas = [abs(g) for g in gammas]
        sig = [e for e in ests if e.get("excl_zero")]
        n_pos = sum(1 for e in sig if e["dr_gamma"] > 0)
        n_neg = sum(1 for e in sig if e["dr_gamma"] < 0)

        # Spearman rho with median
        vec = gamma_matrix[ci]
        valid = ~np.isnan(vec) & ~np.isnan(median_vec)
        rho = float(spearmanr(vec[valid], median_vec[valid])[0]) if valid.sum() > 10 else np.nan

        rows.append({
            "country": country,
            "zone": COUNTRY_ZONE.get(country, "Unknown"),
            "n_estimates": len(ests),
            "n_significant": len(sig),
            "sig_pct": 100 * len(sig) / len(ests) if ests else 0,
            "median_abs_gamma": float(np.median(abs_gammas)),
            "mean_abs_gamma": float(np.mean(abs_gammas)),
            "n_positive": n_pos,
            "n_negative": n_neg,
            "pos_pct": 100 * n_pos / len(sig) if sig else 50,
            "spearman_rho_with_median": rho,
        })

    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# MERGE — Country-level dataset combining all indicators + network metrics
# ═══════════════════════════════════════════════════════════════════════════════

def build_country_dataset(
    network_metrics: pd.DataFrame,
    spectral_features: dict,
    ses_signatures: dict,
) -> pd.DataFrame:
    """
    Merge all country-level data into a single DataFrame.

    Columns added:
        - V-Dem: v2x_polyarchy, v2x_libdem, v2x_egaldem, v2x_partipdem, v2x_delibdem, vdem_pc1
        - Macro: gni_pc, gini, urban_pct, mean_yrs_school, hdi
        - Spectral: fiedler_value, spectral_entropy, spectral_radius
        - SES signature: ses_escol, ses_Tam_loc, ses_sexo, ses_edad, ses_magnitude
    """
    df = network_metrics.copy()

    # ── V-Dem indicators ───────────────────────────────────────────────────
    for col in ["v2x_polyarchy", "v2x_libdem", "v2x_egaldem", "v2x_partipdem", "v2x_delibdem"]:
        df[col] = df["country"].map(
            lambda c, col=col: VDEM_2018.get(c, {}).get(col)
        )

    # ── V-Dem PCA composite (PC1 of all 5 indices) ──────────────────────────
    from sklearn.decomposition import PCA as _PCA
    vdem_cols = ["v2x_polyarchy", "v2x_libdem", "v2x_egaldem", "v2x_partipdem", "v2x_delibdem"]
    vdem_mask = df[vdem_cols].notna().all(axis=1)
    df["vdem_pc1"] = np.nan
    if vdem_mask.sum() >= 5:
        vdem_sub = df.loc[vdem_mask, vdem_cols].astype(float).values
        pca = _PCA(n_components=1)
        scores = pca.fit_transform(vdem_sub)
        df.loc[vdem_mask, "vdem_pc1"] = scores[:, 0]
        # Store PCA metadata for reporting
        df.attrs["vdem_pca_explained_var"] = float(pca.explained_variance_ratio_[0])
        df.attrs["vdem_pca_loadings"] = {
            col: float(pca.components_[0, i]) for i, col in enumerate(vdem_cols)
        }

    # ── Macro indicators ───────────────────────────────────────────────────
    for col in ["gni_pc", "gini", "urban_pct", "mean_yrs_school", "hdi"]:
        df[col] = df["country"].map(
            lambda c, col=col: MACRO_2018.get(c, {}).get(col)
        )

    # ── Log GNI (more normal distribution for regression) ──────────────────
    df["log_gni_pc"] = df["gni_pc"].apply(
        lambda x: np.log(x) if x is not None and x > 0 else None
    )

    # ── Spectral features ──────────────────────────────────────────────────
    for col in ["fiedler_value", "spectral_entropy", "spectral_radius"]:
        df[col] = df["country"].map(
            lambda c, col=col: spectral_features.get(c, {}).get(col)
        )

    # ── SES signatures ─────────────────────────────────────────────────────
    ses_dims = ["escol", "Tam_loc", "sexo", "edad"]
    for dim in ses_dims:
        df[f"ses_{dim}"] = df["country"].map(
            lambda c, dim=dim: ses_signatures.get(c, {}).get(dim)
        )
    # SES magnitude = RMS of 4 signature dimensions
    def _ses_mag(row):
        vals = [row.get(f"ses_{d}") for d in ses_dims]
        if any(v is None for v in vals):
            return None
        return float(np.sqrt(np.mean([v**2 for v in vals])))
    df["ses_magnitude"] = df.apply(_ses_mag, axis=1)

    return df


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 1: Bivariate correlations (democracy × network metrics)
# ═══════════════════════════════════════════════════════════════════════════════

def bivariate_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Spearman correlations between all macro indicators and all
    network / spectral metrics.

    Returns a DataFrame: rows = macro indicators, cols = network metrics,
    values = (rho, p-value, n).
    """
    from scipy.stats import spearmanr

    macro_cols = [
        "v2x_polyarchy", "v2x_libdem", "v2x_egaldem",
        "v2x_partipdem", "v2x_delibdem", "vdem_pc1",
        "log_gni_pc", "gini", "urban_pct", "mean_yrs_school", "hdi",
    ]
    network_cols = [
        "sig_pct", "median_abs_gamma", "spearman_rho_with_median",
        "fiedler_value", "spectral_entropy", "spectral_radius",
        "ses_magnitude", "pos_pct",
    ]

    results = []
    for mc in macro_cols:
        for nc in network_cols:
            mask = df[mc].notna() & df[nc].notna()
            n = mask.sum()
            if n < 10:
                results.append({"macro": mc, "network": nc, "rho": np.nan,
                                "p": np.nan, "n": n})
                continue
            rho, p = spearmanr(df.loc[mask, mc], df.loc[mask, nc])
            results.append({"macro": mc, "network": nc, "rho": rho, "p": p, "n": n})

    return pd.DataFrame(results)


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 2: Mantel tests — |Δ indicator| vs γ-vector distance
# ═══════════════════════════════════════════════════════════════════════════════

def mantel_test(dist_x: np.ndarray, dist_y: np.ndarray,
                n_perm: int = 9999) -> tuple[float, float]:
    """
    Mantel test: Spearman correlation between two distance matrices.

    Parameters:
        dist_x: (n × n) distance matrix for predictor
        dist_y: (n × n) distance matrix for response (gamma-vector distance)
        n_perm: number of permutations for p-value

    Returns:
        (rho_observed, p_value)
    """
    from scipy.stats import spearmanr

    n = dist_x.shape[0]
    # Extract upper triangle (exclude diagonal)
    iu = np.triu_indices(n, k=1)
    x_vec = dist_x[iu]
    y_vec = dist_y[iu]

    rho_obs, _ = spearmanr(x_vec, y_vec)

    # Permutation test
    rng = np.random.default_rng(42)
    count_ge = 0
    for _ in range(n_perm):
        perm = rng.permutation(n)
        dist_y_perm = dist_y[np.ix_(perm, perm)]
        y_perm = dist_y_perm[iu]
        rho_perm, _ = spearmanr(x_vec, y_perm)
        if abs(rho_perm) >= abs(rho_obs):
            count_ge += 1

    p_value = (count_ge + 1) / (n_perm + 1)
    return float(rho_obs), float(p_value)


def run_mantel_tests(df: pd.DataFrame, all_estimates: dict) -> pd.DataFrame:
    """
    Run Mantel tests for each macro indicator against γ-vector cosine distance.

    For each indicator, builds an |indicator_i - indicator_j| distance matrix
    and correlates it with the γ-vector cosine distance matrix.
    """
    from collections import defaultdict

    print("\n  Building gamma-vector distance matrix...")

    # Build gamma vectors
    by_country_pair = defaultdict(dict)
    all_pairs = set()
    for v in all_estimates.values():
        by_country_pair[v["country"]][v["pair_key"]] = v["dr_gamma"]
        all_pairs.add(v["pair_key"])

    pair_list = sorted(all_pairs)
    pair_idx = {p: i for i, p in enumerate(pair_list)}

    # Use countries that have both V-Dem data and gamma vectors
    mantel_indicators = [
        "v2x_polyarchy", "v2x_libdem", "v2x_egaldem",
        "v2x_partipdem", "v2x_delibdem", "vdem_pc1",
        "log_gni_pc", "gini", "urban_pct", "mean_yrs_school", "hdi",
    ]

    # Find countries with all key indicators present
    # (use polyarchy as the democracy gate)
    mask_all = df["v2x_polyarchy"].notna() & df["log_gni_pc"].notna()
    countries_valid = sorted(df.loc[mask_all, "country"].tolist())
    n = len(countries_valid)
    print(f"  Mantel test countries: {n}")

    if n < 10:
        print("  Too few countries for Mantel test, skipping.")
        return pd.DataFrame()

    # Build gamma distance matrix (cosine distance)
    n_p = len(pair_list)
    gamma_mat = np.full((n, n_p), np.nan)
    c_to_idx = {c: i for i, c in enumerate(countries_valid)}
    for ci, country in enumerate(countries_valid):
        for pair, gamma in by_country_pair.get(country, {}).items():
            gamma_mat[ci, pair_idx[pair]] = gamma

    # Cosine distance between each pair of countries
    gamma_dist = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            vi = gamma_mat[i]
            vj = gamma_mat[j]
            valid = ~np.isnan(vi) & ~np.isnan(vj)
            if valid.sum() < 10:
                gamma_dist[i, j] = gamma_dist[j, i] = np.nan
                continue
            a = vi[valid]
            b = vj[valid]
            dot = np.dot(a, b)
            na = np.linalg.norm(a)
            nb = np.linalg.norm(b)
            cos_sim = dot / (na * nb) if na > 0 and nb > 0 else 0
            gamma_dist[i, j] = gamma_dist[j, i] = 1 - cos_sim

    results = []
    for indicator in mantel_indicators:
        vals = df.set_index("country")[indicator].to_dict()
        # Check coverage
        valid_countries = [c for c in countries_valid if vals.get(c) is not None]
        if len(valid_countries) < 10:
            results.append({
                "indicator": indicator, "rho": np.nan, "p": np.nan,
                "n_countries": len(valid_countries),
            })
            continue

        # Subset to valid countries
        idx = [c_to_idx[c] for c in valid_countries]
        sub_gamma = gamma_dist[np.ix_(idx, idx)]

        # Build indicator distance matrix
        indicator_dist = np.zeros((len(valid_countries), len(valid_countries)))
        for i, ci in enumerate(valid_countries):
            for j, cj in enumerate(valid_countries):
                indicator_dist[i, j] = abs(vals[ci] - vals[cj])

        # Check for NaN in gamma distance
        iu = np.triu_indices(len(valid_countries), k=1)
        if np.any(np.isnan(sub_gamma[iu])):
            # Remove pairs with NaN
            valid_mask = ~np.isnan(sub_gamma[iu])
            if valid_mask.sum() < 10:
                results.append({
                    "indicator": indicator, "rho": np.nan, "p": np.nan,
                    "n_countries": len(valid_countries),
                })
                continue

        print(f"  Mantel: {indicator:20s} (n={len(valid_countries)}) ...", end=" ", flush=True)
        rho, p = mantel_test(indicator_dist, sub_gamma, n_perm=9999)
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        print(f"rho={rho:+.3f}  p={p:.4f} {sig}")

        results.append({
            "indicator": indicator, "rho": rho, "p": p,
            "n_countries": len(valid_countries),
        })

    return pd.DataFrame(results)


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 3: OLS regression — network metric ~ macro indicators
# ═══════════════════════════════════════════════════════════════════════════════

def run_ols_regressions(df: pd.DataFrame) -> dict:
    """
    Run OLS regressions predicting each network metric from macro indicators.

    Models:
      1. Baseline: metric ~ log_GNI + Gini + Urban% + MeanYrsSchool
      2. + V-Dem:  metric ~ log_GNI + Gini + Urban% + MeanYrsSchool + v2x_polyarchy
      3. Democracy only: metric ~ v2x_polyarchy

    Returns dict of model results keyed by (outcome, model_name).
    """
    import statsmodels.api as sm

    outcomes = [
        "sig_pct", "median_abs_gamma", "spearman_rho_with_median",
        "fiedler_value", "ses_magnitude",
    ]

    predictors_baseline = ["log_gni_pc", "gini", "urban_pct", "mean_yrs_school"]
    predictors_full = predictors_baseline + ["v2x_polyarchy"]
    predictors_demo_only = ["v2x_polyarchy"]

    models = {
        "baseline": predictors_baseline,
        "full_with_vdem": predictors_full,
        "democracy_only": predictors_demo_only,
    }

    results = {}
    for outcome in outcomes:
        for model_name, pred_cols in models.items():
            cols = [outcome] + pred_cols
            sub = df[cols].dropna()
            if len(sub) < len(pred_cols) + 5:
                continue
            y = sub[outcome].astype(float)
            X = sm.add_constant(sub[pred_cols].astype(float))
            try:
                model = sm.OLS(y, X).fit()
                results[(outcome, model_name)] = {
                    "n": len(sub),
                    "r_squared": model.rsquared,
                    "adj_r_squared": model.rsquared_adj,
                    "f_stat": model.fvalue,
                    "f_pvalue": model.f_pvalue,
                    "aic": model.aic,
                    "bic": model.bic,
                    "coefficients": {
                        name: {
                            "coef": float(model.params[name]),
                            "se": float(model.bse[name]),
                            "t": float(model.tvalues[name]),
                            "p": float(model.pvalues[name]),
                        }
                        for name in model.params.index
                    },
                }
            except Exception as e:
                print(f"  OLS failed: {outcome} ~ {model_name}: {e}")
                continue

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 4: OLS with interaction terms (democracy × macro indicator)
# ═══════════════════════════════════════════════════════════════════════════════

def run_interaction_regressions(df: pd.DataFrame) -> dict:
    """
    Run OLS regressions with democracy × macro-indicator interaction terms.

    For each network outcome, fits 5 models:
      A: outcome ~ log_gni_pc + v2x_polyarchy + log_gni_pc * v2x_polyarchy
      B: outcome ~ mean_yrs_school + v2x_polyarchy + mean_yrs_school * v2x_polyarchy
      C: outcome ~ gini + v2x_polyarchy + gini * v2x_polyarchy
      D: outcome ~ urban_pct + v2x_polyarchy + urban_pct * v2x_polyarchy
      E: outcome ~ log_gni_pc + v2x_polyarchy + gini + mean_yrs_school + urban_pct
                    + log_gni_pc * v2x_polyarchy + gini * v2x_polyarchy

    All continuous predictors are mean-centered before computing interaction
    terms to reduce multicollinearity between main effects and interactions.

    Statistical methodology:
      - OLS coefficients: t = beta / SE(beta), p from t-distribution with
        (n - k - 1) degrees of freedom. Assumes normally distributed errors,
        homoscedasticity, and no perfect multicollinearity.
      - Delta R2 is the difference between the interaction model R2 and the
        corresponding additive-only model (same predictors, no interaction).

    Returns dict keyed by (outcome, model_label) with R2, interaction coef/p,
    delta_R2 vs additive model, and full coefficient table.
    """
    import statsmodels.api as sm

    outcomes = [
        "sig_pct", "median_abs_gamma", "ses_magnitude",
        "spearman_rho_with_median", "fiedler_value",
    ]

    # Model specs: (label, main_predictors, interaction_pairs)
    # interaction_pairs: list of (var1, var2) to multiply
    model_specs = [
        ("A_gni_x_demo",
         ["log_gni_pc", "v2x_polyarchy"],
         [("log_gni_pc", "v2x_polyarchy")]),
        ("B_educ_x_demo",
         ["mean_yrs_school", "v2x_polyarchy"],
         [("mean_yrs_school", "v2x_polyarchy")]),
        ("C_gini_x_demo",
         ["gini", "v2x_polyarchy"],
         [("gini", "v2x_polyarchy")]),
        ("D_urban_x_demo",
         ["urban_pct", "v2x_polyarchy"],
         [("urban_pct", "v2x_polyarchy")]),
        ("E_full_interactions",
         ["log_gni_pc", "v2x_polyarchy", "gini", "mean_yrs_school", "urban_pct"],
         [("log_gni_pc", "v2x_polyarchy"), ("gini", "v2x_polyarchy")]),
    ]

    results = {}
    for outcome in outcomes:
        for label, main_preds, interactions in model_specs:
            all_needed = [outcome] + main_preds
            sub = df[all_needed].dropna()
            if len(sub) < len(main_preds) + len(interactions) + 5:
                continue

            y = sub[outcome].astype(float)

            # --- Center continuous predictors ---
            X_centered = sub[main_preds].astype(float).copy()
            for col in main_preds:
                X_centered[col] = X_centered[col] - X_centered[col].mean()

            # --- Add interaction columns ---
            interaction_names = []
            for v1, v2 in interactions:
                iname = f"{v1}_x_{v2}"
                X_centered[iname] = X_centered[v1] * X_centered[v2]
                interaction_names.append(iname)

            X_int = sm.add_constant(X_centered)

            # --- Additive-only model (same predictors, no interaction) ---
            X_add = sm.add_constant(X_centered[main_preds])

            try:
                model_int = sm.OLS(y, X_int).fit()
                model_add = sm.OLS(y, X_add).fit()
            except Exception as e:
                print(f"  Interaction OLS failed: {outcome} ~ {label}: {e}")
                continue

            delta_r2 = model_int.rsquared - model_add.rsquared

            # Extract interaction term results
            int_coefs = {}
            for iname in interaction_names:
                int_coefs[iname] = {
                    "coef": float(model_int.params[iname]),
                    "se": float(model_int.bse[iname]),
                    "t": float(model_int.tvalues[iname]),
                    "p": float(model_int.pvalues[iname]),
                }

            results[(outcome, label)] = {
                "n": len(sub),
                "r_squared": float(model_int.rsquared),
                "adj_r_squared": float(model_int.rsquared_adj),
                "r_squared_additive": float(model_add.rsquared),
                "delta_r_squared": float(delta_r2),
                "f_stat": float(model_int.fvalue),
                "f_pvalue": float(model_int.f_pvalue),
                "interaction_terms": int_coefs,
                "coefficients": {
                    name: {
                        "coef": float(model_int.params[name]),
                        "se": float(model_int.bse[name]),
                        "t": float(model_int.tvalues[name]),
                        "p": float(model_int.pvalues[name]),
                    }
                    for name in model_int.params.index
                },
            }

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def plot_scatter_panels(df: pd.DataFrame, save_path: Path):
    """
    Multi-panel scatter plots: V-Dem polyarchy vs. each network metric.

    6 panels: sig%, med|gamma|, Spearman rho, Fiedler, SES magnitude, pos%
    Points colored by cultural zone.
    """
    from scipy.stats import spearmanr

    metrics = [
        ("sig_pct", "Significant edges (%)"),
        ("median_abs_gamma", "Median |gamma|"),
        ("spearman_rho_with_median", "Spearman rho\n(with global median)"),
        ("fiedler_value", "Fiedler value\n(algebraic connectivity)"),
        ("ses_magnitude", "SES magnitude\n(RMS of 4D signature)"),
        ("pos_pct", "Positive edges (%)"),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))

    for idx, (col, label) in enumerate(metrics):
        ax = axes.flat[idx]
        mask = df["v2x_polyarchy"].notna() & df[col].notna()
        sub = df[mask]
        if len(sub) < 5:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes)
            continue

        # Scatter with zone colors
        for _, row in sub.iterrows():
            zone = row["zone"]
            color = ZONE_COLORS.get(zone, "#999999")
            ax.scatter(row["v2x_polyarchy"], row[col], c=color, s=30,
                       edgecolors="white", linewidths=0.3, alpha=0.8, zorder=3)
            ax.annotate(row["country"], (row["v2x_polyarchy"], row[col]),
                        fontsize=5, alpha=0.6, ha="center", va="bottom",
                        xytext=(0, 3), textcoords="offset points")

        # Trend line
        x = sub["v2x_polyarchy"].values.astype(float)
        y = sub[col].values.astype(float)
        if len(x) > 5:
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            x_line = np.linspace(x.min(), x.max(), 100)
            ax.plot(x_line, p(x_line), "k--", alpha=0.4, lw=1)

        # Spearman rho annotation
        rho, pval = spearmanr(x, y)
        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "ns"
        ax.text(0.02, 0.98, f"rho={rho:+.3f} ({sig})\nn={len(sub)}",
                transform=ax.transAxes, fontsize=8, va="top", ha="left",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

        ax.set_xlabel("V-Dem Electoral Democracy (v2x_polyarchy)", fontsize=9)
        ax.set_ylabel(label, fontsize=9)
        ax.grid(alpha=0.2)

        # Highlight Mexico
        mex = sub[sub["country"] == "MEX"]
        if len(mex):
            ax.scatter(mex["v2x_polyarchy"].values[0], mex[col].values[0],
                       c="none", edgecolors="#c44e00", linewidths=2, s=120,
                       zorder=5)

    # Zone legend
    legend_handles = [mpatches.Patch(facecolor=c, label=z)
                      for z, c in sorted(ZONE_COLORS.items())]
    fig.legend(handles=legend_handles, loc="lower center", ncol=4,
               fontsize=8, framealpha=0.85, bbox_to_anchor=(0.5, -0.02))

    fig.suptitle("V-Dem Electoral Democracy vs. SES-Attitude Network Properties\n"
                 "WVS Wave 7, 66 countries (2017-2022)",
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0.04, 1, 0.96])
    fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {save_path.name}")


def plot_correlation_heatmap(corr_df: pd.DataFrame, save_path: Path):
    """
    Heatmap of Spearman correlations: macro indicators vs network metrics.
    """
    # Pivot to matrix form
    macro_order = [
        "v2x_polyarchy", "v2x_libdem", "v2x_egaldem",
        "v2x_partipdem", "v2x_delibdem", "vdem_pc1",
        "log_gni_pc", "gini", "urban_pct", "mean_yrs_school", "hdi",
    ]
    network_order = [
        "sig_pct", "median_abs_gamma", "spearman_rho_with_median",
        "fiedler_value", "spectral_entropy", "spectral_radius",
        "ses_magnitude", "pos_pct",
    ]

    macro_labels = {
        "v2x_polyarchy": "Electoral\nDemocracy", "v2x_libdem": "Liberal\nDemocracy",
        "v2x_egaldem": "Egalitarian\nDemocracy",
        "v2x_partipdem": "Participatory\nDemocracy", "v2x_delibdem": "Deliberative\nDemocracy",
        "vdem_pc1": "V-Dem\nPC1",
        "log_gni_pc": "log(GNI\nper cap)", "gini": "Gini\ncoeff",
        "urban_pct": "Urban %", "mean_yrs_school": "Mean yrs\nschooling",
        "hdi": "HDI",
    }
    network_labels = {
        "sig_pct": "Sig edges %", "median_abs_gamma": "Med |gamma|",
        "spearman_rho_with_median": "rho with\nmedian",
        "fiedler_value": "Fiedler", "spectral_entropy": "Spectral\nentropy",
        "spectral_radius": "Spectral\nradius",
        "ses_magnitude": "SES mag", "pos_pct": "Pos edges %",
    }

    rho_mat = np.full((len(macro_order), len(network_order)), np.nan)
    p_mat = np.full((len(macro_order), len(network_order)), np.nan)

    for _, row in corr_df.iterrows():
        if row["macro"] in macro_order and row["network"] in network_order:
            mi = macro_order.index(row["macro"])
            ni = network_order.index(row["network"])
            rho_mat[mi, ni] = row["rho"]
            p_mat[mi, ni] = row["p"]

    fig, ax = plt.subplots(figsize=(12, 7))
    im = ax.imshow(rho_mat, cmap="RdBu_r", vmin=-0.6, vmax=0.6, aspect="auto")

    # Annotate with rho values and significance stars
    for i in range(len(macro_order)):
        for j in range(len(network_order)):
            r = rho_mat[i, j]
            p = p_mat[i, j]
            if np.isnan(r):
                continue
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
            color = "white" if abs(r) > 0.35 else "black"
            ax.text(j, i, f"{r:+.2f}{sig}", ha="center", va="center",
                    fontsize=8, color=color, fontweight="bold" if sig else "normal")

    ax.set_xticks(range(len(network_order)))
    ax.set_xticklabels([network_labels.get(c, c) for c in network_order],
                        fontsize=8, rotation=0, ha="center")
    ax.set_yticks(range(len(macro_order)))
    ax.set_yticklabels([macro_labels.get(c, c) for c in macro_order], fontsize=9)

    # Separator line between democracy indices (incl. PC1) and other indicators
    ax.axhline(y=5.5, color="black", linewidth=1.5, linestyle="-")

    plt.colorbar(im, ax=ax, label="Spearman rho", shrink=0.8)
    ax.set_title("Macro Indicators vs. SES-Attitude Network Properties\n"
                 "Spearman correlations (WVS W7, 66 countries)  |  "
                 "* p<.05  ** p<.01  *** p<.001",
                 fontsize=12, fontweight="bold")

    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {save_path.name}")


def plot_mantel_results(mantel_df: pd.DataFrame, save_path: Path):
    """Bar chart of Mantel test results."""
    if mantel_df.empty:
        print("  Skipping Mantel plot (no results)")
        return

    indicator_labels = {
        "v2x_polyarchy": "Electoral Democracy",
        "v2x_libdem": "Liberal Democracy",
        "v2x_egaldem": "Egalitarian Democracy",
        "v2x_partipdem": "Participatory Democracy",
        "v2x_delibdem": "Deliberative Democracy",
        "vdem_pc1": "V-Dem PC1",
        "log_gni_pc": "log(GNI/cap)",
        "gini": "Gini coefficient",
        "urban_pct": "Urbanization %",
        "mean_yrs_school": "Mean yrs schooling",
        "hdi": "HDI",
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    mantel_sorted = mantel_df.dropna(subset=["rho"]).sort_values("rho", ascending=True)

    labels = [indicator_labels.get(r["indicator"], r["indicator"])
              for _, r in mantel_sorted.iterrows()]
    rhos = mantel_sorted["rho"].values
    ps = mantel_sorted["p"].values

    colors = ["#d62728" if p < 0.05 else "#1f77b4" if p < 0.10 else "#999999"
              for p in ps]

    bars = ax.barh(range(len(labels)), rhos, color=colors, edgecolor="white", linewidth=0.5)

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Mantel rho (|Delta indicator| vs. gamma-vector cosine distance)",
                  fontsize=10)
    ax.axvline(x=0, color="black", linewidth=0.5)

    # Annotate with p-values
    for i, (r, p) in enumerate(zip(rhos, ps)):
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        label_text = f"  {r:+.3f}  p={p:.3f}{sig}"
        ha = "left" if r >= 0 else "right"
        ax.text(r, i, label_text, va="center", ha=ha, fontsize=8)

    ax.set_title("Mantel Tests: Do Macro-Indicator Differences Predict\n"
                 "gamma-Vector Differences Between Countries?\n"
                 "Red = p<.05  |  9999 permutations",
                 fontsize=12, fontweight="bold")
    ax.grid(alpha=0.2, axis="x")

    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {save_path.name}")


def plot_democracy_scatter_with_zones(df: pd.DataFrame, save_path: Path):
    """
    V-Dem polyarchy × Fiedler value, with democracy tercile annotations
    and zone-colored markers. Tests the hypothesis that authoritarian vs
    democratic societies have fundamentally different belief configurations.
    """
    from scipy.stats import spearmanr

    mask = df["v2x_polyarchy"].notna() & df["fiedler_value"].notna()
    sub = df[mask].copy()
    if len(sub) < 10:
        return

    fig, ax = plt.subplots(figsize=(12, 8))

    # Democracy terciles
    poly_vals = sub["v2x_polyarchy"].values
    t1 = np.percentile(poly_vals, 33)
    t2 = np.percentile(poly_vals, 67)

    # Plot data first so axes have correct limits
    for _, row in sub.iterrows():
        zone = row["zone"]
        color = ZONE_COLORS.get(zone, "#999999")
        ax.scatter(row["v2x_polyarchy"], row["fiedler_value"],
                   c=color, s=50, edgecolors="white", linewidths=0.5, zorder=3)
        ax.annotate(row["country"],
                    (row["v2x_polyarchy"], row["fiedler_value"]),
                    fontsize=6, alpha=0.7, ha="center", va="bottom",
                    xytext=(0, 4), textcoords="offset points")

    # Background shading for terciles (after data so ylim is set)
    y_lo, y_hi = ax.get_ylim()
    ax.axvspan(sub["v2x_polyarchy"].min() - 0.02, t1,
               alpha=0.06, color="#d62728", label="_")
    ax.axvspan(t1, t2, alpha=0.06, color="#f0e442", label="_")
    ax.axvspan(t2, sub["v2x_polyarchy"].max() + 0.02,
               alpha=0.06, color="#2ca02c", label="_")
    ax.text((sub["v2x_polyarchy"].min() + t1) / 2, y_lo + 0.003, "Autocratic",
            ha="center", fontsize=9, alpha=0.5, style="italic")
    ax.text((t1 + t2) / 2, y_lo + 0.003, "Hybrid",
            ha="center", fontsize=9, alpha=0.5, style="italic")
    ax.text((t2 + sub["v2x_polyarchy"].max()) / 2, y_lo + 0.003, "Democratic",
            ha="center", fontsize=9, alpha=0.5, style="italic")

    # Trend line
    x = sub["v2x_polyarchy"].values.astype(float)
    y = sub["fiedler_value"].values.astype(float)
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, p(x_line), "k--", alpha=0.5, lw=1.5)

    rho, pval = spearmanr(x, y)
    sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "ns"

    ax.text(0.02, 0.98,
            f"Spearman rho = {rho:+.3f} ({sig})\nn = {len(sub)} countries",
            transform=ax.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.9))

    # Highlight Mexico
    mex = sub[sub["country"] == "MEX"]
    if len(mex):
        ax.scatter(mex["v2x_polyarchy"].values[0], mex["fiedler_value"].values[0],
                   c="none", edgecolors="#c44e00", linewidths=3, s=200, zorder=5)

    # Zone legend
    legend_handles = [mpatches.Patch(facecolor=c, label=z)
                      for z, c in sorted(ZONE_COLORS.items())]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=7, framealpha=0.85)

    ax.set_xlabel("V-Dem Electoral Democracy Index (v2x_polyarchy)", fontsize=11)
    ax.set_ylabel("Fiedler Value (Algebraic Connectivity)", fontsize=11)
    ax.set_title("Democracy Level vs. SES-Attitude Network Connectivity\n"
                 "WVS Wave 7 (2017-2022)  |  "
                 "Fiedler = how tightly SES structures inter-construct covariation",
                 fontsize=12, fontweight="bold")
    ax.grid(alpha=0.2)

    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {save_path.name}")


def plot_interaction_effects(df: pd.DataFrame, save_path: Path):
    """
    2x2 grid: democracy x {GNI, education, Gini, urbanization} scatter plots.

    X-axis = macro variable, Y-axis = median_abs_gamma,
    color = democracy tercile (low/mid/high based on v2x_polyarchy),
    with separate OLS regression lines per tercile.
    """
    from scipy.stats import spearmanr

    outcome = "median_abs_gamma"
    panels = [
        ("log_gni_pc", "log(GNI per capita)"),
        ("mean_yrs_school", "Mean years of schooling"),
        ("gini", "Gini coefficient"),
        ("urban_pct", "Urban population (%)"),
    ]

    # Need polyarchy + outcome + all panel vars
    needed = [outcome, "v2x_polyarchy", "country", "zone"] + [p[0] for p in panels]
    mask = df[["v2x_polyarchy", outcome]].notna().all(axis=1)
    base = df[mask].copy()
    if len(base) < 15:
        print("  Skipping interaction plot (insufficient data)")
        return

    # Democracy terciles
    t1 = base["v2x_polyarchy"].quantile(1/3)
    t2 = base["v2x_polyarchy"].quantile(2/3)
    def _tercile(v):
        if v <= t1:
            return "Low democracy"
        elif v <= t2:
            return "Mid democracy"
        return "High democracy"
    base["demo_tercile"] = base["v2x_polyarchy"].apply(_tercile)

    tercile_colors = {
        "Low democracy": "#d62728",
        "Mid democracy": "#ff7f0e",
        "High democracy": "#2ca02c",
    }
    tercile_order = ["Low democracy", "Mid democracy", "High democracy"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    for idx, (xcol, xlabel) in enumerate(panels):
        ax = axes.flat[idx]
        sub = base[base[xcol].notna()].copy()
        if len(sub) < 10:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes)
            continue

        # Scatter by tercile
        for terc in tercile_order:
            t_sub = sub[sub["demo_tercile"] == terc]
            if len(t_sub) < 3:
                continue
            color = tercile_colors[terc]
            ax.scatter(t_sub[xcol], t_sub[outcome], c=color, s=35,
                       edgecolors="white", linewidths=0.3, alpha=0.8,
                       label=terc, zorder=3)

            # Per-tercile regression line
            x = t_sub[xcol].values.astype(float)
            y = t_sub[outcome].values.astype(float)
            if len(x) >= 4:
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                x_line = np.linspace(x.min(), x.max(), 50)
                ax.plot(x_line, p(x_line), color=color, linestyle="--",
                        alpha=0.6, lw=1.5)

        # Country labels
        for _, row in sub.iterrows():
            ax.annotate(row["country"], (row[xcol], row[outcome]),
                        fontsize=4.5, alpha=0.5, ha="center", va="bottom",
                        xytext=(0, 2), textcoords="offset points")

        # Overall Spearman
        x_all = sub[xcol].values.astype(float)
        y_all = sub[outcome].values.astype(float)
        rho, pval = spearmanr(x_all, y_all)
        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "ns"
        ax.text(0.02, 0.98, f"Overall rho={rho:+.3f} ({sig})\nn={len(sub)}",
                transform=ax.transAxes, fontsize=8, va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel("Median |gamma|", fontsize=10)
        ax.grid(alpha=0.2)
        ax.legend(fontsize=7, loc="lower right", framealpha=0.8)

    fig.suptitle("Democracy x Macro-Indicator Interaction Effects on SES-Attitude Association\n"
                 "Points colored by democracy tercile (v2x_polyarchy); separate trend lines per group",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {save_path.name}")


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def write_report(
    df: pd.DataFrame,
    corr_df: pd.DataFrame,
    mantel_df: pd.DataFrame,
    ols_results: dict,
    report_path: Path,
    interaction_results: dict | None = None,
):
    """Write comprehensive markdown report."""
    with open(report_path, "w") as f:
        f.write("# Macro-Indicator Analysis: What Predicts SES-Attitude Network Structure?\n\n")
        f.write("## Overview\n\n")
        f.write("This analysis tests whether country-level macro indicators predict variation\n")
        f.write("in SES-attitude network properties across 66 WVS Wave 7 countries.\n\n")
        f.write("**Macro indicators tested:**\n")
        f.write("- V-Dem Electoral Democracy (v2x_polyarchy)\n")
        f.write("- V-Dem Liberal Democracy (v2x_libdem)\n")
        f.write("- V-Dem Egalitarian Democracy (v2x_egaldem)\n")
        f.write("- V-Dem Participatory Democracy (v2x_partipdem)\n")
        f.write("- V-Dem Deliberative Democracy (v2x_delibdem)\n")
        f.write("- V-Dem PC1 (PCA composite of all 5 V-Dem indices)\n")
        f.write("- GNI per capita (log-transformed, World Bank 2018)\n")
        f.write("- Gini coefficient (World Bank, latest near 2018)\n")
        f.write("- Urban population % (World Bank 2018)\n")
        f.write("- Mean years of schooling (UNDP HDR 2018)\n")
        f.write("- Human Development Index (UNDP 2018)\n\n")
        f.write("**Network properties predicted:**\n")
        f.write("- Significance rate (% of construct pairs with CI excluding zero)\n")
        f.write("- Median |gamma| (SES-mediated association strength)\n")
        f.write("- Spearman rho with global median (typicality)\n")
        f.write("- Fiedler value (algebraic connectivity from TDA pipeline)\n")
        f.write("- Spectral entropy and radius\n")
        f.write("- SES magnitude (RMS of 4D SES signature)\n\n")

        # ── V-Dem coverage ──
        n_vdem = df["v2x_polyarchy"].notna().sum()
        f.write(f"**V-Dem coverage:** {n_vdem}/66 countries ")
        f.write("(AND, HKG, MAC, NIR, PRI lack V-Dem entries)\n\n")

        # ── Bivariate correlations ──
        f.write("## 1. Bivariate Correlations (Spearman)\n\n")
        f.write("| Macro Indicator | Network Metric | rho | p-value | n | Sig |\n")
        f.write("|-----------------|---------------|-----|---------|---|-----|\n")
        for _, row in corr_df.sort_values("p").iterrows():
            if np.isnan(row["rho"]):
                continue
            sig = "***" if row["p"] < 0.001 else "**" if row["p"] < 0.01 else "*" if row["p"] < 0.05 else ""
            f.write(f"| {row['macro']} | {row['network']} | {row['rho']:+.3f} | "
                    f"{row['p']:.4f} | {row['n']:.0f} | {sig} |\n")

        # ── Democracy-specific findings ──
        f.write("\n### Democracy-Specific Findings\n\n")
        demo_corrs = corr_df[corr_df["macro"] == "v2x_polyarchy"].sort_values("p")
        for _, row in demo_corrs.iterrows():
            if np.isnan(row["rho"]):
                continue
            sig = "***" if row["p"] < 0.001 else "**" if row["p"] < 0.01 else "*" if row["p"] < 0.05 else "ns"
            f.write(f"- **{row['network']}**: rho = {row['rho']:+.3f} (p={row['p']:.4f}, {sig})\n")

        # ── Mantel tests ──
        f.write("\n## 2. Mantel Tests (gamma-vector distance)\n\n")
        f.write("Tests whether countries with similar macro indicators also have similar\n")
        f.write("SES-attitude networks (measured by gamma-vector cosine distance).\n\n")
        if not mantel_df.empty:
            f.write("| Indicator | Mantel rho | p-value | n | Sig |\n")
            f.write("|-----------|-----------|---------|---|-----|\n")
            for _, row in mantel_df.sort_values("p").iterrows():
                if np.isnan(row["rho"]):
                    continue
                sig = "***" if row["p"] < 0.001 else "**" if row["p"] < 0.01 else "*" if row["p"] < 0.05 else ""
                f.write(f"| {row['indicator']} | {row['rho']:+.3f} | {row['p']:.4f} | "
                        f"{row['n_countries']:.0f} | {sig} |\n")
        else:
            f.write("(Insufficient data for Mantel tests)\n")

        # ── OLS regressions ──
        f.write("\n## 3. OLS Regression Models\n\n")
        for outcome in ["sig_pct", "median_abs_gamma", "spearman_rho_with_median",
                         "fiedler_value", "ses_magnitude"]:
            f.write(f"\n### Outcome: {outcome}\n\n")
            for model_name in ["baseline", "full_with_vdem", "democracy_only"]:
                key = (outcome, model_name)
                if key not in ols_results:
                    continue
                res = ols_results[key]
                f.write(f"**Model: {model_name}** (n={res['n']}, "
                        f"R2={res['r_squared']:.3f}, adj_R2={res['adj_r_squared']:.3f})\n\n")
                f.write("| Predictor | Coef | SE | t | p |\n")
                f.write("|-----------|------|-----|---|---|\n")
                for name, vals in res["coefficients"].items():
                    sig = "***" if vals["p"] < 0.001 else "**" if vals["p"] < 0.01 else "*" if vals["p"] < 0.05 else ""
                    f.write(f"| {name} | {vals['coef']:+.4f} | {vals['se']:.4f} | "
                            f"{vals['t']:+.2f} | {vals['p']:.4f}{sig} |\n")
                f.write("\n")

            # Compare R2 across models
            baseline = ols_results.get((outcome, "baseline"))
            full = ols_results.get((outcome, "full_with_vdem"))
            if baseline and full:
                delta_r2 = full["r_squared"] - baseline["r_squared"]
                f.write(f"**V-Dem increment:** Delta R2 = {delta_r2:+.3f} "
                        f"(from {baseline['r_squared']:.3f} to {full['r_squared']:.3f})\n\n")

        # ── V-Dem PCA ──
        f.write("\n## V-Dem PCA Composite\n\n")
        pca_var = df.attrs.get("vdem_pca_explained_var")
        pca_loadings = df.attrs.get("vdem_pca_loadings")
        if pca_var is not None:
            f.write(f"PC1 explains **{pca_var*100:.1f}%** of the variance across all 5 V-Dem indices.\n\n")
            f.write("PC1 loadings:\n\n")
            f.write("| Index | Loading |\n|-------|--------|\n")
            for name, load in pca_loadings.items():
                f.write(f"| {name} | {load:+.4f} |\n")
            f.write("\n")
        else:
            f.write("PCA could not be computed (insufficient non-missing V-Dem data).\n\n")

        # ── Interaction models ──
        if interaction_results:
            f.write("\n## 4. Interaction Models (Democracy x Macro Indicators)\n\n")
            f.write("### Statistical Methodology\n\n")
            f.write("- **OLS coefficients**: t = beta / SE(beta), p-value from t-distribution ")
            f.write("with (n - k - 1) degrees of freedom. Assumes: normally distributed errors, ")
            f.write("homoscedasticity, no perfect multicollinearity.\n")
            f.write("- **Mantel test**: permutation-based p-value (9999 random permutations ")
            f.write("of distance matrix rows/columns). No distributional assumptions.\n")
            f.write("- **Spearman rho**: exact or asymptotic p-value for null hypothesis of ")
            f.write("rho = 0, computed via scipy.stats.spearmanr.\n")
            f.write("- **Interaction terms**: Continuous predictors are mean-centered before ")
            f.write("computing interactions to reduce multicollinearity between main effects ")
            f.write("and interaction terms.\n")
            f.write("- **Delta R2**: R2(interaction model) - R2(additive-only model with same ")
            f.write("main-effect predictors but no interaction terms).\n\n")

            # Group by outcome
            outcomes_seen = sorted(set(k[0] for k in interaction_results))
            for outcome in outcomes_seen:
                f.write(f"\n### Outcome: {outcome}\n\n")
                f.write("| Model | n | R2 | R2_add | Delta_R2 | Interaction | Coef | p | Sig |\n")
                f.write("|-------|---|----|----|------|------------|------|---|-----|\n")
                for (out, label), res in sorted(interaction_results.items()):
                    if out != outcome:
                        continue
                    for iname, ivals in res["interaction_terms"].items():
                        sig = "***" if ivals["p"] < 0.001 else "**" if ivals["p"] < 0.01 else "*" if ivals["p"] < 0.05 else ""
                        f.write(f"| {label} | {res['n']} | {res['r_squared']:.3f} | "
                                f"{res['r_squared_additive']:.3f} | {res['delta_r_squared']:+.3f} | "
                                f"{iname} | {ivals['coef']:+.4f} | {ivals['p']:.4f} | {sig} |\n")
                f.write("\n")

        # ── Key findings ──
        f.write("\n## 5. Key Findings\n\n")

        # Find strongest democracy correlations
        demo_sig = corr_df[
            (corr_df["macro"].isin(["v2x_polyarchy", "v2x_libdem", "v2x_egaldem"])) &
            (corr_df["p"] < 0.05)
        ]
        if len(demo_sig):
            f.write("### Significant Democracy-Network Relationships\n\n")
            for _, row in demo_sig.sort_values("p").iterrows():
                f.write(f"- {row['macro']} x {row['network']}: "
                        f"rho = {row['rho']:+.3f} (p = {row['p']:.4f})\n")
        else:
            f.write("### No significant democracy-network correlations at p < 0.05\n\n")
            f.write("This is itself a substantive finding: democracy level does NOT predict\n")
            f.write("SES-attitude network structure after accounting for economic development.\n")

        f.write("\n### Democracy vs. Income as Predictors\n\n")
        for outcome in ["sig_pct", "fiedler_value", "spearman_rho_with_median"]:
            b = ols_results.get((outcome, "baseline"))
            full = ols_results.get((outcome, "full_with_vdem"))
            demo = ols_results.get((outcome, "democracy_only"))
            if b and demo:
                f.write(f"- **{outcome}**: Baseline R2={b['r_squared']:.3f}, "
                        f"Democracy-only R2={demo['r_squared']:.3f}")
                if full:
                    f.write(f", Full R2={full['r_squared']:.3f}")
                f.write("\n")

        # ── Zone-democracy interaction ──
        f.write("\n### Cultural Zone × Democracy Interaction\n\n")
        for zone in sorted(ZONE_COLORS):
            zone_mask = df["zone"] == zone
            vdem_mask = df["v2x_polyarchy"].notna()
            zone_df = df[zone_mask & vdem_mask]
            if len(zone_df) < 3:
                continue
            mean_poly = zone_df["v2x_polyarchy"].mean()
            mean_fied = zone_df["fiedler_value"].mean() if zone_df["fiedler_value"].notna().sum() > 0 else np.nan
            mean_sig = zone_df["sig_pct"].mean()
            f.write(f"- **{zone}** (n={len(zone_df)}): "
                    f"mean democracy={mean_poly:.3f}, "
                    f"mean Fiedler={mean_fied:.3f}, "
                    f"mean sig%={mean_sig:.1f}%\n")

        # ── Mexico context ──
        f.write("\n### Mexico in Context\n\n")
        mex = df[df["country"] == "MEX"].iloc[0] if len(df[df["country"] == "MEX"]) else None
        if mex is not None:
            def _fmt(val, fmt=".3f"):
                try:
                    return f"{float(val):{fmt}}"
                except (ValueError, TypeError):
                    return "N/A"
            f.write(f"- Electoral Democracy: {_fmt(mex.get('v2x_polyarchy'))}\n")
            f.write(f"- Liberal Democracy: {_fmt(mex.get('v2x_libdem'))}\n")
            f.write(f"- Egalitarian Democracy: {_fmt(mex.get('v2x_egaldem'))}\n")
            f.write(f"- GNI per capita: ${_fmt(mex.get('gni_pc'), '.1f')}K\n")
            f.write(f"- Gini: {_fmt(mex.get('gini'), '.1f')}\n")
            f.write(f"- Sig edges: {_fmt(mex.get('sig_pct'), '.1f')}%\n")
            f.write(f"- Fiedler: {_fmt(mex.get('fiedler_value'))}\n")
            f.write(f"- Spearman rho: {_fmt(mex.get('spearman_rho_with_median'))}\n")

        # ── Output files ──
        f.write("\n## Output Files\n\n")
        f.write("- `macro_indicator_analysis.png` — V-Dem scatter panels\n")
        f.write("- `macro_indicator_correlations.png` — correlation heatmap\n")
        f.write("- `macro_indicator_mantel.png` — Mantel test results\n")
        f.write("- `macro_indicator_democracy_fiedler.png` — democracy x Fiedler deep dive\n")
        f.write("- `cross_country_geometry/interaction_effects.png` — democracy x macro interaction scatter\n")
        f.write("- `cross_country_interactions.json` — interaction model results\n")
        f.write("- `vdem_indicators.json` — V-Dem data cache\n")
        f.write("- `macro_indicator_data.json` — full merged country-level dataset\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("MACRO-INDICATOR ANALYSIS")
    print("  V-Dem democracy + World Bank + UNDP vs. network structure")
    print("=" * 60)

    # ── Load data ──────────────────────────────────────────────────────────
    sweep_path = RESULTS / "wvs_geographic_sweep_w7.json"
    spectral_path = ROOT / "data" / "tda" / "allwave" / "per_wave" / "W7" / "spectral" / "spectral_features.json"
    ses_sig_path = RESULTS / "ses_signatures_all.json"

    print(f"\nLoading WVS geographic sweep...")
    all_estimates = load_wvs_geographic(sweep_path)
    print(f"  {len(all_estimates):,} estimates loaded")

    print(f"Loading spectral features...")
    spectral_features = load_spectral_features(spectral_path)
    print(f"  {len(spectral_features)} countries")

    print(f"Loading SES signatures...")
    ses_signatures = load_ses_signatures(ses_sig_path)
    print(f"  {len(ses_signatures)} countries")

    # ── Compute network metrics ────────────────────────────────────────────
    print(f"\nComputing per-country network metrics...")
    network_metrics = compute_country_network_metrics(all_estimates)
    print(f"  {len(network_metrics)} countries")

    # ── Build merged dataset ───────────────────────────────────────────────
    print(f"Building merged country dataset...")
    df = build_country_dataset(network_metrics, spectral_features, ses_signatures)
    print(f"  {len(df)} countries, {len(df.columns)} columns")

    n_vdem = df["v2x_polyarchy"].notna().sum()
    print(f"  V-Dem coverage: {n_vdem}/{len(df)}")
    n_macro = df["log_gni_pc"].notna().sum()
    print(f"  Macro coverage: {n_macro}/{len(df)}")

    # ── Cache V-Dem data ───────────────────────────────────────────────────
    print(f"\nCaching V-Dem indicators...")
    with open(RESULTS / "vdem_indicators.json", "w") as f:
        json.dump(VDEM_2018, f, indent=2)
    print(f"  Saved: vdem_indicators.json")

    # ── Cache full merged dataset ──────────────────────────────────────────
    df_dict = df.where(df.notna(), None).to_dict(orient="records")
    with open(RESULTS / "macro_indicator_data.json", "w") as f:
        json.dump({"countries": df_dict, "n": len(df_dict)}, f, indent=2)
    print(f"  Saved: macro_indicator_data.json")

    # ── Analysis 1: Bivariate correlations ─────────────────────────────────
    print(f"\n{'─'*60}")
    print("ANALYSIS 1: Bivariate Spearman correlations")
    print(f"{'─'*60}")
    corr_df = bivariate_correlations(df)
    sig_corrs = corr_df[corr_df["p"] < 0.05].sort_values("p")
    print(f"  {len(sig_corrs)} significant correlations (p < 0.05)")
    if len(sig_corrs):
        print(f"\n  Top significant correlations:")
        for _, row in sig_corrs.head(10).iterrows():
            sig = "***" if row["p"] < 0.001 else "**" if row["p"] < 0.01 else "*"
            print(f"    {row['macro']:20s} × {row['network']:28s}  "
                  f"rho={row['rho']:+.3f}  p={row['p']:.4f} {sig}")

    # ── Analysis 2: Mantel tests ───────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("ANALYSIS 2: Mantel tests (indicator distance vs gamma-vector distance)")
    print(f"{'─'*60}")
    mantel_df = run_mantel_tests(df, all_estimates)

    # ── Analysis 3: OLS regressions ────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("ANALYSIS 3: OLS regressions")
    print(f"{'─'*60}")
    ols_results = run_ols_regressions(df)
    for (outcome, model), res in sorted(ols_results.items()):
        print(f"  {outcome:30s} ~ {model:20s}  R2={res['r_squared']:.3f}  "
              f"adj_R2={res['adj_r_squared']:.3f}  n={res['n']}")

    # ── Analysis 4: Interaction regressions ──────────────────────────────
    print(f"\n{'─'*60}")
    print("ANALYSIS 4: OLS interaction regressions (democracy x macro)")
    print(f"{'─'*60}")
    interaction_results = run_interaction_regressions(df)
    n_sig_int = 0
    for (outcome, label), res in sorted(interaction_results.items()):
        for iname, iv in res["interaction_terms"].items():
            sig_mark = "***" if iv["p"] < 0.001 else "**" if iv["p"] < 0.01 else "*" if iv["p"] < 0.05 else ""
            if sig_mark:
                n_sig_int += 1
            print(f"  {outcome:30s} ~ {label:25s}  R2={res['r_squared']:.3f}  "
                  f"dR2={res['delta_r_squared']:+.3f}  "
                  f"int_p={iv['p']:.4f} {sig_mark}")
    print(f"\n  {n_sig_int} significant interaction terms (p < 0.05)")

    # Save interaction results
    geo_dir = RESULTS / "cross_country_geometry"
    geo_dir.mkdir(parents=True, exist_ok=True)

    # JSON-serializable interaction results
    int_json = {}
    for (outcome, label), res in interaction_results.items():
        int_json[f"{outcome}::{label}"] = res
    with open(RESULTS / "cross_country_interactions.json", "w") as f:
        json.dump(int_json, f, indent=2)
    print(f"  Saved: cross_country_interactions.json")

    # ── Visualizations ─────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("VISUALIZATION")
    print(f"{'─'*60}")
    plot_scatter_panels(df, RESULTS / "macro_indicator_analysis.png")
    plot_correlation_heatmap(corr_df, RESULTS / "macro_indicator_correlations.png")
    plot_mantel_results(mantel_df, RESULTS / "macro_indicator_mantel.png")
    plot_democracy_scatter_with_zones(df, RESULTS / "macro_indicator_democracy_fiedler.png")
    plot_interaction_effects(df, geo_dir / "interaction_effects.png")

    # ── Report ─────────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("REPORT")
    print(f"{'─'*60}")
    write_report(df, corr_df, mantel_df, ols_results,
                 RESULTS / "macro_indicator_report.md",
                 interaction_results=interaction_results)
    print(f"  Saved: macro_indicator_report.md")

    print(f"\n{'='*60}")
    print("DONE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
