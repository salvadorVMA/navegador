"""Diagnostic: isolate where DR estimate hangs on local Mac.

Run:
    python scripts/debug/test_dr_diagnostic.py 2>&1 | tee /tmp/dr_diag.log

Watch in another terminal:
    tail -f /tmp/dr_diag.log
"""
import sys, time, warnings, json, signal
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "debug"))


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# Timeout for any step
class StepTimeout(Exception):
    pass

def _alarm(signum, frame):
    raise StepTimeout()

signal.signal(signal.SIGALRM, _alarm)


# ── Step 1: Load data ──
log("STEP 1: Loading data...")
t0 = time.time()
signal.alarm(120)
try:
    from sweep_dr_highci import load_data, load_v1_pairs
    enc_dict, enc_nom_dict_rev = load_data()
    signal.alarm(0)
    log(f"  Data loaded in {time.time()-t0:.1f}s")
except StepTimeout:
    log("  TIMEOUT loading data (>120s)")
    sys.exit(1)

# Verify agg columns
s0 = list(enc_dict.keys())[0]
agg_count = sum(1 for c in enc_dict[s0]["dataframe"].columns if c.startswith("agg_"))
log(f"  {s0}: {agg_count} agg columns")

# ── Step 2: Pick a simple non-agg pair ──
log("STEP 2: Finding test pair...")
pairs = load_v1_pairs(0.25)
log(f"  {len(pairs)} pairs above threshold")

# Find a non-agg pair
p = None
for x in pairs:
    if not x["var_a"].startswith("agg_") and not x["var_b"].startswith("agg_"):
        p = x
        break
if not p:
    log("  No non-agg pairs found!")
    sys.exit(1)

log(f"  Pair: {p['var_a']} x {p['var_b']}")
log(f"  v1_gamma: {p['v1_gamma']:+.4f}")

# ── Step 3: Manually replicate estimate with per-step timing ──
import numpy as np
import pandas as pd
from ses_regression import (
    SurveyVarModel, SESEncoder, SES_REGRESSION_VARS,
    _drop_ses_sentinel_rows, CrossDatasetBivariateEstimator,
    goodman_kruskal_gamma,
)
import statsmodels.api as sm

col_a = p["var_a"].split("|")[0]
col_b = p["var_b"].split("|")[0]
domain_a = p["var_a"].split("|")[1]
domain_b = p["var_b"].split("|")[1]
survey_a = enc_nom_dict_rev.get(domain_a)
survey_b = enc_nom_dict_rev.get(domain_b)
df_a = enc_dict[survey_a]["dataframe"]
df_b = enc_dict[survey_b]["dataframe"]
log(f"  surveys: {survey_a}({len(df_a)}) x {survey_b}({len(df_b)})")

available = [v for v in SES_REGRESSION_VARS if v in df_a.columns and v in df_b.columns]
log(f"  SES vars ({len(available)}): {available}")

# 3a: Fit model_a
log("STEP 3a: Fitting SurveyVarModel A...")
signal.alarm(30)
try:
    t0 = time.time()
    model_a = SurveyVarModel()
    model_a.fit(df_a, col_a, available, "Pondi2", max_categories=5)
    signal.alarm(0)
    log(f"  model_a: {time.time()-t0:.2f}s, cats={model_a._categories}")
except StepTimeout:
    signal.alarm(0)
    log("  TIMEOUT fitting model_a (>30s) — THIS IS THE HANG")
    sys.exit(1)
except Exception as e:
    signal.alarm(0)
    log(f"  ERROR fitting model_a: {e}")
    sys.exit(1)

# 3b: Fit model_b
log("STEP 3b: Fitting SurveyVarModel B...")
signal.alarm(30)
try:
    t0 = time.time()
    model_b = SurveyVarModel()
    model_b.fit(df_b, col_b, available, "Pondi2", max_categories=5)
    signal.alarm(0)
    log(f"  model_b: {time.time()-t0:.2f}s, cats={model_b._categories}")
except StepTimeout:
    signal.alarm(0)
    log("  TIMEOUT fitting model_b (>30s) — THIS IS THE HANG")
    sys.exit(1)
except Exception as e:
    signal.alarm(0)
    log(f"  ERROR fitting model_b: {e}")
    sys.exit(1)

# 3c: SES encoding
log("STEP 3c: SES encoding...")
t0 = time.time()
enc = SESEncoder()
sub_a = _drop_ses_sentinel_rows(
    df_a[[col_a] + [v for v in available if v in df_a.columns]].dropna(), available
)
sub_b = _drop_ses_sentinel_rows(
    df_b[[col_b] + [v for v in available if v in df_b.columns]].dropna(), available
)
X_a = enc.fit_transform(sub_a[available]).fillna(0.0)
X_b = enc.transform(sub_b[available]).fillna(0.0)
log(f"  sub_a={len(sub_a)}, sub_b={len(sub_b)}, X cols={len(X_a.columns)} ({time.time()-t0:.2f}s)")

# 3d: Propensity model
log("STEP 3d: Propensity model...")
signal.alarm(30)
try:
    t0 = time.time()
    prop_avail = [v for v in ["sexo", "escol", "edad"] if v in df_a.columns and v in df_b.columns]
    prop_enc = SESEncoder()
    Xp_a = prop_enc.fit_transform(sub_a[prop_avail]).fillna(0.0)
    Xp_b = prop_enc.transform(sub_b[prop_avail]).fillna(0.0)
    X_pooled = pd.concat([Xp_a, Xp_b], ignore_index=True)
    delta = np.concatenate([np.ones(len(Xp_a)), np.zeros(len(Xp_b))])
    Xc = sm.add_constant(X_pooled, has_constant="add")
    prop_model = sm.Logit(delta, Xc).fit(method="bfgs", disp=False)
    signal.alarm(0)
    log(f"  Propensity fit: {time.time()-t0:.2f}s")
except StepTimeout:
    signal.alarm(0)
    log("  TIMEOUT propensity model (>30s)")
    sys.exit(1)

# 3e: Joint table
log("STEP 3e: Joint table...")
t0 = time.time()
cats_a = model_a._categories
cats_b = model_b._categories
K_a, K_b = len(cats_a), len(cats_b)
helper = CrossDatasetBivariateEstimator(n_sim=500)
ses_pop = helper._sample_ses_population(df_a, df_b, available, "Pondi2")
X_ref_a = model_a._encoder.transform(ses_pop[available]).fillna(0.0)
X_ref_b = model_b._encoder.transform(ses_pop[available]).fillna(0.0)
pa_ref = model_a.predict_proba(X_ref_a).values[:, :K_a]
pb_ref = model_b.predict_proba(X_ref_b).values[:, :K_b]
joint = (pa_ref[:, :, None] * pb_ref[:, None, :]).mean(axis=0)
joint /= joint.sum()
gamma_point = goodman_kruskal_gamma(joint)
log(f"  gamma_point={gamma_point:+.4f} ({time.time()-t0:.2f}s)")

# 3f: Bootstrap — 5 iterations with per-iteration timing
log("STEP 3f: Bootstrap (5 iterations)...")
rng = np.random.default_rng(42)
n_a, n_b = len(sub_a), len(sub_b)
for b in range(5):
    signal.alarm(30)
    try:
        bt0 = time.time()
        idx_a = rng.choice(n_a, size=n_a, replace=True)
        idx_b = rng.choice(n_b, size=n_b, replace=True)
        boot_a = sub_a.iloc[idx_a].reset_index(drop=True)
        boot_b = sub_b.iloc[idx_b].reset_index(drop=True)

        t1 = time.time()
        bm_a = SurveyVarModel()
        bm_a.fit(boot_a, col_a, available, "Pondi2")
        fit_a = time.time() - t1

        t2 = time.time()
        bm_b = SurveyVarModel()
        bm_b.fit(boot_b, col_b, available, "Pondi2")
        fit_b = time.time() - t2

        t3 = time.time()
        X_ra = bm_a._encoder.transform(ses_pop[available]).fillna(0.0)
        X_rb = bm_b._encoder.transform(ses_pop[available]).fillna(0.0)
        pa = bm_a.predict_proba(X_ra).values[:, :K_a]
        pb = bm_b.predict_proba(X_rb).values[:, :K_b]
        jt = (pa[:, :, None] * pb[:, None, :]).mean(axis=0)
        jt /= jt.sum()
        bg = goodman_kruskal_gamma(jt)
        pred = time.time() - t3
        signal.alarm(0)

        log(f"  boot[{b}] {time.time()-bt0:.2f}s (fit_a={fit_a:.2f} fit_b={fit_b:.2f} pred={pred:.3f}) gamma={bg:+.4f}")
    except StepTimeout:
        signal.alarm(0)
        log(f"  boot[{b}] TIMEOUT (>30s) — BFGS HANG DETECTED")
    except Exception as e:
        signal.alarm(0)
        log(f"  boot[{b}] ERROR: {e}")

log("DIAGNOSTIC COMPLETE")
