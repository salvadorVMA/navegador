# WVS Ontology & Cross-Country Prediction Findings

*Generated: 2026-04-07*
*Branch: `wvs`*

---

## 1. Overview

The WVS ontology extends the los_mex construct knowledge graph to 66 countries using World Values Survey Wave 7 data. It provides per-country construct networks with signed bridge edges (Goodman-Kruskal γ), SES fingerprints, camp bipartitions, and individual-level predictions via `DRPredictionEngine`.

**Readiness score: 84/100** (construct quality 23/25, network structure 25/25, cross-study alignment 11/25, feasibility 25/25).

---

## 2. Infrastructure Built

| File | Purpose |
|------|---------|
| `scripts/debug/build_wvs_kg_ontology.py` | Builds `wvs_kg_ontology.json` + `wvs_ses_fingerprints_v2.json` from sweep data |
| `scripts/debug/diagnostic_wvs_ontology_readiness.py` | 5-section diagnostic: construct quality, network structure, cross-study capacity, feasibility, OntologyQuery E2E |
| `scripts/debug/demo_wvs_ontology.py` | Per-country KG builder + circle-layout network visualizations (canonical shared layout) |
| `scripts/debug/demo_wvs_ontology_capabilities.py` | All 10 OntologyQuery operations demonstrated across 6 countries |
| `scripts/debug/test_wvs_prediction_scenarios.py` | 5 prediction scenarios × 6 countries using DRPredictionEngine |
| `scripts/debug/test_wvs_profile_predictions.py` | 5 SES profiles × 5 scenarios × 6 countries: individual-level predictions |
| `tests/unit/test_wvs_ontology_readiness.py` | 35 unit tests covering WVS data integrity + OntologyQuery integration |
| `opinion_ontology.py` | Added `dataset` parameter + Path coercion (3-line change) |

### Data Files Generated

| File | Contents |
|------|----------|
| `data/results/wvs_kg_ontology.json` | WVS KG: 56 constructs, 395 bridges, 8 domains |
| `data/results/wvs_ses_fingerprints_v2.json` | OntologyQuery-compatible 4D fingerprints (56 constructs) |
| `data/results/wvs_ontology_readiness_report.json` | Full diagnostic report |
| `data/results/wvs_ontology_readiness_report.md` | Human-readable diagnostic |
| `data/results/wvs_ontology_network_mex.png` | Mexico circle network (domain sectors, signed edges) |
| `data/results/wvs_ontology_comparison.png` | 6-country comparison (shared canonical layout) |
| `data/results/wvs_prediction_scenarios_heatmap.png` | 5×6 γ heatmap (scenarios vs countries) |
| `data/results/wvs_prediction_scenario_circles.png` | 5 scenarios with per-country edges (color=country, solid/dashed=sign) |
| `data/results/wvs_profile_prediction_heatmaps.png` | 5 profiles × 6 countries prediction shifts |
| `data/results/wvs_profile_prediction_bars.png` | Baseline vs A-informed predictions per profile per country |

---

## 3. WVS Bridge Network Structure

### Mexico vs Los_Mex Comparison

| Metric | WVS MEX W7 | los_mex |
|--------|-----------|---------|
| Total pairs | 982 | 4,135 |
| Significant | 395 (40.2%) | 984 (23.8%) |
| Constructs | 49 | 93 |
| Connected | 43 | 71 |
| Isolated | 6 | 22 |
| Density | 43.7% | 23.0% |
| Diameter | 3 | 4 |
| Avg path length | 1.614 | 1.728 |
| Fingerprint-γ sign consistency | 100% | 99.4% |
| Structural balance | 99.6% | 94% |

The WVS network is **denser and more balanced** than los_mex, with perfect fingerprint-gamma sign consistency.

### Cross-Country Network Comparison

| Country | Edges | Density | Diameter | Cosmopolitan | Tradition | Balance |
|---------|-------|---------|----------|-------------|-----------|---------|
| MEX | 391 | 43% | 3 | 29 | 14 | 99.8% |
| USA | 659 | 54% | 2 | 26 | 24 | 93.2% |
| JPN | 419 | 44% | 3 | 26 | 18 | 98.0% |
| DEU | 622 | 55% | 3 | 24 | 24 | 95.9% |
| BRA | 389 | 38% | 3 | 30 | 16 | 98.9% |
| NGA | 316 | 31% | 4 | 26 | 20 | 100.0% |

USA and Germany have the densest networks (~55%); Nigeria is sparsest (31%). Balance ranges from 93% (USA, most contested) to 100% (Nigeria, cleanest bipartition).

---

## 4. Camp Structure: Cosmopolitan vs Tradition

### Two Levels of SES Dominance (Important Distinction)

The WVS data shows different SES dimensions dominating at different levels of analysis:

**Per-construct level** — which dim has highest |ρ| for each construct:
- sexo: 23/56, Tam_loc: 20/56, edad: 8/56, **escol: only 5/56**
- Most WVS constructs have small SES effects (median magnitude 0.059), and gender/urbanization are slightly larger than education in most individual constructs

**Bridge network level** — which dim drives construct-pair co-variation:
- escol: **48.7%** of bridge dot-product contribution
- edad: 32.6%, Tam_loc: 12.4%, sexo: 6.3%
- Education has the largest *absolute magnitudes* (mean |ρ_escol| = 0.076 vs sexo's 0.035), so it dominates the products that determine bridge sign and strength

**Why the difference**: Gender "wins" the per-construct count because it's the largest of four small numbers in 23 cases (mean |ρ_sexo| = 0.029 among those constructs). Education wins fewer constructs but has stronger effects where it does — and bridge co-variation is driven by products of magnitudes, not by which dim "wins" individually.

### What Drives Camp Assignment

The Fiedler bipartition is driven by **education at the bridge level** (Spearman ρ = +0.70, p < 0.0001) with a secondary **gender** axis (ρ = −0.42, p = 0.001). Age and urbanization are not significant drivers of the bipartition. This is consistent with education dominating the bridge dot-products even though it dominates few individual fingerprints.

- **Cosmopolitan camp** (+Fiedler): Constructs where more educated people score higher — subjective wellbeing, postmaterialist values, outgroup trust, autonomy values, online participation, democratic evaluation.
- **Tradition camp** (−Fiedler): Constructs where less educated people score higher — authoritarian governance tolerance, state surveillance acceptance, basic needs deprivation, conformity values, science skepticism, religious belief.

### The Geometry Is a Gradient, Not Two Types

The split is nearly even (MEX: 35 cosmopolitan vs 21 tradition) but Fiedler confidence is very low — maximum 0.10 for most constructs. Modularity Q = 0.089 (near-zero community structure). The "camps" are two halves of a single education-driven axis, not discrete sociological types.

### 39 of 56 Constructs Flip Camp Across Countries

This is the central cross-country finding. The reason is that the **SES geometry rotates** across national contexts:

1. **In Mexico**, education dominates the Fiedler axis (ρ = 0.70) — camp = "does education push you up or down?"
2. **In Germany/Japan**, urbanization and age contribute more — the axis captures a different dimension of social stratification
3. When the dominant axis rotates, constructs that were "cosmopolitan" in one country become "tradition" in another

**Key examples:**

| Construct | MEX | USA | JPN | DEU | BRA | NGA |
|-----------|-----|-----|-----|-----|-----|-----|
| Institutional trust | T | T | **C** | T | **C** | **C** |
| Security behaviors | C | **T** | **T** | **T** | **T** | C |
| Importance of life domains | T | T | **C** | **C** | **C** | **C** |
| Familial duty | C | **T** | C | **T** | C | **T** |
| Postmaterialist values | C | C | **T** | **T** | C | **T** |

**Institutional trust** flips because educated urbanites are *cynical* about institutions in Mexico/USA but *trusting* in Japan/Brazil/Nigeria. **Security behaviors** flip because security awareness is a modern urban trait in Mexico/Nigeria (more to protect) but a conservative anxiety in USA/Germany (fear-based).

---

## 5. Prediction Scenarios

### 5 Scenarios Tested Across 6 Countries

Each scenario fitted `DRPredictionEngine` on real respondent-level WVS data (1,237-2,596 per country). n_sim=500, n_bootstrap=20.

| # | Scenario | Key Finding |
|---|----------|-------------|
| S1 | Autonomy → Participation | Universally positive. MEX +0.030*, BRA +0.075*. No effect in DEU/JPN |
| S2 | Participation → Security | **Sign flip**: MEX/NGA positive, USA/DEU negative. γ spread = 0.21 |
| S3 | Economic Worry → Trust | Only JPN significant (−0.030*). USA weakly positive (+0.011*) |
| S4 | Morality → Change | **No significant effects anywhere** — not SES-mediated |
| S5 | Participation → Immigration | DEU +0.031* only. Most relationships not SES-mediated |

### 5 SES Profiles Tested

| Profile | sexo | edad | escol | Tam_loc |
|---------|------|------|-------|---------|
| Young urban educated woman | F | 25 | 4 | 4 (urban) |
| Older rural less-educated man | M | 60 | 2 | 1 (rural) |
| Middle-aged urban professional man | M | 40 | 4 | 3 |
| Young rural woman | F | 22 | 2 | 1 (rural) |
| Older urban educated woman | F | 55 | 4 | 4 (urban) |

### Profile Prediction Findings

1. **SES profiles set radically different baselines**: The same construct has E[B] ranging from 1.0 to 10.0 depending on the person's education, age, gender, and urbanization. The bridge shift operates on top of this.

2. **The bridge shift is modest but directionally consistent**: γ values of 0.03-0.15 translate to E[B] shifts of 0.01-0.36. The shift direction always matches the gamma sign.

3. **Urban educated profiles get larger shifts**: They sit further from floor/ceiling effects, so the lift from knowing A has more room to operate.

4. **S2 is the most profile-differentiating scenario**: In Nigeria, the young urban educated woman's prediction shifts +0.20 (participation → more security awareness) while in Germany it shifts −0.03 (participation → less security anxiety).

---

## 6. OntologyQuery: 10 Operations Across Countries

All 10 `OntologyQuery` methods work on WVS data out of the box with only a 3-line change (Path coercion + `dataset` parameter).

### Key Cross-Country Differences

**get_neighbors** — Same construct, different bridge partners:
- "Online participation" in MEX: top neighbor = religious exclusivism (+0.08)
- In USA: perceived immigration effects (−0.10)
- In JPN: precautionary security (−0.11)
- In DEU: civic dishonesty tolerance (+0.18)

**find_path** — Same endpoints, different routes:
- "Autonomy → Anti-immigration" in USA/DEU: direct 1-hop (strong bridge)
- In MEX/JPN: 2-hop via "online participation" as intermediary
- In JPN: unexpectedly *positive* expected sign (both in cosmopolitan camp)

**get_network** — Same seed, different connectivity:
- "Institutional trust" in MEX: 0 edges (completely isolated)
- In DEU: 22 edges at 1-hop, 522 at 2-hop (deeply connected)
- In NGA: 15 edges (moderate)

**get_frustrated_nodes** — Boundary constructs vary by context:
- MEX: 1 frustrated node (clean bipartition)
- USA: 26 frustrated nodes (most structurally contested)
- DEU: 13, led by "socioeconomic insecurity worry" (21% frustrated triangles)

---

## 7. Cross-Study Alignment (WVS ↔ los_mex)

**Remaining weakness** (cross_study score: 11/25):

- Median fingerprint cosine for grade-3 pairs: **0.238** (up from 0.195 pre-realignment, still low)
- 17/46 grade-3 pairs have **negative cosine** — same concept, opposite SES profiles
- Dominant dimension agreement: **13%** — WVS dominated by sexo (23/56) and Tam_loc (20/56); los_mex by escol (37/93)
- Root cause: SES fingerprints are **survey-specific, not concept-inherent**

---

## 8. Remaining Gap

| Gap | Impact | Effort |
|-----|--------|--------|
| No WVS item-level fingerprints (L0) | Cannot lift individual WVS Q-codes to constructs | ~1 hour if WVS CSVs available |

All other gaps (KG file, OntologyQuery parameterization, fingerprint reformatting) are resolved.
