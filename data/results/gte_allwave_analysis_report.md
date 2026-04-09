# GTE Cross-Wave Analysis Report

Waves analyzed: W3 (1996), W4 (2000), W5 (2007), W6 (2012), W7 (2018)

## 1. Per-Wave Summary

| Wave | Year | Countries | Constructs | Med Fiedler | Med Balance | Med |SES| | Top BP Hub |
|------|------|-----------|-----------|------------|------------|---------|------------|
| W3 | 1996 | 38 | 24 | 0.0 | 0.7557 | 0.0792 | job_scarcity_gender_discr (7) |
| W4 | 2000 | 27 | 25 | 0.0 | 0.7342 | 0.0746 | gender_role_traditionalis (7) |
| W5 | 2007 | 43 | 31 | 0.0 | 0.7262 | 0.0705 | immigrant_origin_status (11) |
| W6 | 2012 | 47 | 44 | 0.0 | 0.7106 | 0.0694 | immigrant_origin_status (9) |
| W7 | 2018 | 66 | 55 | 0.1315 | 0.7188 | 0.0772 | immigrant_origin_status (14) |

### SES Dimension Dominance

| Wave | escol | Tam_loc | sexo | edad |
|------|-------|---------|------|------|
| W3 | 1.7% | 28.6% | 25.7% | 44.0% |
| W4 | 1.7% | 32.7% | 29.8% | 35.8% |
| W5 | 1.3% | 33.5% | 25.4% | 39.8% |
| W6 | 0.9% | 35.6% | 26.4% | 37.1% |
| W7 | 35.5% | 22.2% | 14.2% | 28.2% |

## 2. Cross-Wave Evolution

Countries with 2+ waves: **68**

### Camp Stability

Total camp flips across all countries and transitions: **1447**

Most volatile constructs:

- religious_belief: 58 flips
- democratic_system_evaluation: 52 flips
- confidence_in_international_organizations: 52 flips
- economic_ideology: 51 flips
- postmaterialist_values: 50 flips
- confidence_in_civil_society_organizations: 50 flips
- job_scarcity_nativist_preference: 49 flips
- societal_change_attitudes: 48 flips
- child_qualities_conformity_tradition: 48 flips
- autocracy_support: 47 flips

### Fingerprint Drift

| Transition | Countries | Median cosine | Mean cosine | Min | Max |
|-----------|-----------|--------------|------------|-----|-----|
| W3→W4 | 16 | 0.706 | 0.692 | 0.382 | 0.931 |
| W3→W5 | 12 | 0.839 | 0.759 | 0.343 | 0.918 |
| W3→W6 | 5 | 0.726 | 0.705 | 0.520 | 0.907 |
| W3→W7 | 1 | 0.547 | 0.547 | 0.547 | 0.547 |
| W4→W5 | 12 | 0.640 | 0.626 | 0.109 | 0.968 |
| W4→W6 | 5 | 0.530 | 0.539 | 0.437 | 0.657 |
| W4→W7 | 4 | 0.490 | 0.401 | -0.114 | 0.740 |
| W5→W6 | 21 | 0.705 | 0.678 | 0.207 | 0.962 |
| W5→W7 | 12 | 0.384 | 0.376 | 0.058 | 0.576 |
| W6→W7 | 33 | 0.505 | 0.464 | -0.033 | 0.853 |

## 3. Mexico Deep Dive

### Fingerprint Drift

**W3→W4** (23 shared constructs): median cosine = 0.8368
  - Gaining importance: Tam_loc (+0.0330)
  - Losing importance: sexo (+0.0004)
**W4→W5** (24 shared constructs): median cosine = 0.9029
  - Gaining importance: escol (+0.0153)
  - Losing importance: Tam_loc (-0.0029)
**W5→W6** (30 shared constructs): median cosine = 0.8342
  - Gaining importance: edad (+0.0101)
  - Losing importance: Tam_loc (-0.0477)
**W6→W7** (43 shared constructs): median cosine = 0.8532
  - Gaining importance: edad (-0.0085)
  - Losing importance: escol (-0.0178)

### Connectivity (Fiedler)

- W3 (1996): 0.673
- W4 (2000): 0.7801
- W5 (2007): 0.8188
- W6 (2012): 0.7051
- W7 (2018): 0.7256

## 4. Figures

![balance_trajectory](gte_allwave_plots/balance_trajectory.png)
![camp_volatility](gte_allwave_plots/camp_volatility.png)
![fiedler_heatmap](gte_allwave_plots/fiedler_heatmap.png)
![fingerprint_drift_scatter](gte_allwave_plots/fingerprint_drift_scatter.png)
![hub_rank_ribbon](gte_allwave_plots/hub_rank_ribbon.png)
![ses_dominance_stacked](gte_allwave_plots/ses_dominance_stacked.png)
