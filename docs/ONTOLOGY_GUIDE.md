# Navegador Ontology Guide

Self-contained reference for any agent or developer querying or extending the
survey knowledge graph and SES fingerprint system.

---

## What the ontology is

A three-level knowledge graph over Mexican public opinion survey data ("los_mex"),
encoding **which attitudes co-vary because of shared sociodemographic position**.

It is **not** a general attitude correlation network. Every edge in it is a
SES-mediated association, estimated by the Doubly Robust (DR) bridge estimator
under a Conditional Independence Assumption (§ Limitations below).

---

## SES foundation — read this first

The entire system is built on 4 sociodemographic (SES) dimensions:

| Variable | What it measures |
|----------|-----------------|
| `escol` | Education level (ordinal, 5-level) |
| `Tam_loc` | Town size / urban-rural axis (ordinal, 4-level) |
| `sexo` | Gender (binary) |
| `edad` | Age / cohort (7 bins) |

**All four have equal standing.** Gender and age/cohort structure access,
attitudes, and life trajectories in ways inseparable from class in Mexican
society. Do not treat `escol` as the canonical SES dimension and the others
as controls or noise — doing so produces wrong sign predictions on ~5% of
bridge edges and misrepresents the sociodemographic geometry of the data.

The DR bridge conditions on all 4 simultaneously via ordered-logit propensity
models. γ(A,B) measures the covariation between constructs A and B that would
remain if both survey populations had the same joint distribution over these
4 SES dimensions.

---

## Critical limitations (CIA)

**γ(A,B) captures ONLY SES-mediated covariation.** Under the Conditional
Independence Assumption, once you condition on SES cell membership, A and B are
assumed independent. The bridge cannot detect:

1. Direct causal links A → B that are independent of SES
2. Confounders outside the 4-var SES set (e.g. region, religiosity as a
   background variable, media exposure)
3. Reverse causation B → A
4. Non-monotonic SES structuring (U-shaped, crossover patterns) — use NMI
   for these; γ ≈ 0 with NMI >> 0 flags a non-monotonic pattern

**Near-zero γ means SES does not co-drive A and B monotonically. It does NOT
mean A and B are unrelated.**

---

## Level hierarchy

Levels are numbered bottom-up (finest grain = L0):

| Level | Unit | Count | Status |
|-------|------|:-----:|--------|
| **L0** | Questions (raw survey items) | 6 359 | Use with caution — check `reverse_coded` |
| **L1** | Constructs (multi-item aggregates) | 93 | Authoritative |
| **L2** | Domains | 24 | Coarse fallback only |

**Lookup priority**: L1 construct → L0 item (reverse-coding checked) → L2 domain

L2 domains are means of L1 fingerprints; averaging cancels when constructs within
a domain pull in opposite directions (e.g. REL: personal_religiosity is
anti-education while religious_socialization is pro-education).

---

## SES fingerprint

Every L1 construct node carries a 4D SES fingerprint:

```json
{
  "rho_escol":    +0.344,
  "rho_Tam_loc":  -0.465,
  "rho_sexo":     -0.042,
  "rho_edad":     -0.076,
  "ses_magnitude": 0.292,
  "dominant_dim": "Tam_loc",
  "ses_sign":     1
}
```

| Field | Meaning |
|-------|---------|
| `rho_*` | Spearman ρ(construct, SES_var), median across surveys |
| `ses_magnitude` | RMS of all 4 ρ values — overall stratification intensity |
| `dominant_dim` | SES dimension with highest \|ρ\| (any of the 4) |
| `ses_sign` | sign(rho_escol) — single-axis summary only; use full vector for direction analysis |

Distribution of `dominant_dim` across 93 constructs: escol=37, Tam_loc=23,
edad=22, sexo=11. The majority are primarily structured by age, location, or
gender, not education.

---

## Bridge edges

984 of 4 135 construct pairs have a statistically significant bridge
(CI of γ excludes zero). Each edge carries:

```json
{
  "from":              "HAB|structural_housing_quality",
  "to":                "EDU|digital_and_cultural_capital",
  "gamma":             +0.2775,
  "ci_lo":             +0.236,
  "ci_hi":             +0.310,
  "ci_width":          0.074,
  "nmi":               0.009,
  "fingerprint_dot":   +0.1742,
  "fingerprint_cos":   +0.643,
  "dot_sign_consistent": true
}
```

| Field | Meaning |
|-------|---------|
| `gamma` | Goodman-Kruskal γ ∈ [−1,+1]. **Signed.** Positive = SES co-elevates both constructs |
| `ci_lo/hi` | Bootstrap 95% CI (Julia v4, n_bootstrap=200) |
| `nmi` | Normalized mutual information — detects non-monotonic SES patterns γ misses |
| `fingerprint_dot` | dot(fingerprint_A, fingerprint_B) — predicts sign(gamma) at 99.4% accuracy |
| `fingerprint_cos` | Cosine of fingerprint vectors — normalized alignment |
| `dot_sign_consistent` | False for 6 edges, all with \|γ\| < 0.02 (noise at threshold) |

**Why fingerprint_dot predicts γ sign**: Two constructs whose SES profiles point
in the same 4D direction are co-elevated by the same sociodemographic position.
The dot product captures alignment across all 4 SES dimensions simultaneously.
Using only `rho_escol` alignment works 94.9% of the time; the full dot product
works 99.4% of the time.

---

## Prediction chains

To predict item B from item A across the bridge:

```
signal = loading_gamma_A × γ(A→B) × loading_gamma_B
```

All three terms use the Goodman-Kruskal γ estimand → dimensionally consistent.

| Term | Where to find it | Sign |
|------|-----------------|------|
| `loading_gamma_A` | L0 item entry in `ses_fingerprints.json` | Negative if item A is reverse-coded |
| `γ(A→B)` | Bridge edge `gamma` in `kg_ontology_v2.json` | Positive/negative per SES alignment |
| `loading_gamma_B` | L0 item entry in `ses_fingerprints.json` | Negative if item B is reverse-coded |

**Double negatives cancel correctly**: if both items are reverse-coded, the product
is positive — the prediction direction is preserved. Use the signed product throughout;
only take absolute value when reporting magnitude.

`loading_gamma` = γ(raw_item, bin5(agg_construct)), where bin5 = rank-normalize
then equal-frequency qcut to 5 bins — mirrors the Julia bridge binning pipeline.

**The bridge γ is the dominant bottleneck**: weak bridge domains (NIN, IND, REL
overall) have γ ≈ 0.01–0.04; no item loading rescues a near-zero bridge. Always
check the bridge CI before interpreting a prediction chain.

---

## Reverse coding

Items coded 1=Yes/2=No or with other inverted scales have `reverse_coded=True`
in their L0 entry. Their raw ρ signs are INVERTED relative to the construct's
conceptual direction. `loading_gamma` is naturally negative for RC items —
this is correct, not a bug. The parent L1 construct fingerprint always reflects
the conceptual direction (high score = more of the concept).

---

## Output files

| File | Contents |
|------|----------|
| `data/results/kg_ontology_v2.json` | Master ontology: domains, 93 L1 constructs (with fingerprints), 984 bridge edges, self-documenting metadata block |
| `data/results/ses_fingerprints.json` | L0 questions (6 359), L1 constructs (93), L2 domains (24) with full fingerprint data and loading_gamma |
| `data/results/construct_dr_sweep_v5_julia_v4.json` | Raw sweep output (Julia v4): all 4 135 pairs, γ + CI + NMI |
| `data/kg_ontology.json` | **STALE** — v1 with 176 old construct names. Do not use. |

---

## Source code

| Module | Role |
|--------|------|
| `scripts/debug/rebuild_kg_ontology.py` | Builds `kg_ontology_v2.json` from v4 manifest |
| `scripts/debug/compute_ses_fingerprints.py` | Computes L0/L1/L2 fingerprints; adds `loading_gamma` to L0 items |
| `ses_regression.py` | Python DR bridge estimator (reference implementation) |
| `survey_kg.py` | Knowledge graph query interface |
| Julia `src/dr_estimator.jl` | Primary numeric engine for sweeps |

---

## Quick reference: what γ is and is not

| γ IS | γ IS NOT |
|------|----------|
| SES-mediated monotonic co-variation | Total correlation between A and B |
| Conditioned on [escol, Tam_loc, sexo, edad] | Causal effect of A on B |
| Signed: direction of SES alignment | Meaningful for non-monotonic relationships |
| Comparable across surveys (same SES reference population) | Valid if CIA assumption fails |
| The bottleneck in item→item prediction chains | Rescued by high item loadings when γ ≈ 0 |
