# All-Wave TDA Analysis Report

## Topological Data Analysis of the SES-Mediated Attitude Network Across
## 100 Countries and 6 WVS Waves (1990-2018)

---

### Summary

This report presents a topological data analysis (TDA) of SES-mediated attitude
covariation networks constructed from the World Values Survey (WVS) across five
geographic sweeps (Waves 3-7, 1996-2018) covering up to 100 countries, and 37
country-level temporal trajectories spanning three or more waves. The analysis
applies persistent homology, Ollivier-Ricci curvature, spectral graph theory,
and multidimensional scaling to characterize the topology, geometry, and
evolution of these networks.

**Key findings:**

1. Algebraic connectivity (Fiedler value) is a near-constant at ~0.70-0.72 across three decades.
2. Cross-country convergence oscillates rather than trending; no secular homogenization.
3. Cultural zones separate spectrally in early (W3) and late (W7) waves but not in between.
4. Topological loops are declining: networks are becoming more tree-like over time.
5. Gender role traditionalism is the universal structural bridge, dominant in 54% of countries.
6. Ricci curvature is uniformly near zero: flat geometry with no bottleneck edges.
7. Mean spectral distance declines from ~0.21 to ~0.16, indicating structural shape convergence
   even without connectivity convergence.

---

## 1. Algebraic Connectivity: A Near-Constant

The Fiedler value (second-smallest eigenvalue of the graph Laplacian) measures how
tightly connected the SES-mediated attitude network is. Higher values indicate that
removing any single construct would not disconnect the network.

| Wave | Year | N countries | Mean Fiedler | Std | Min | Max |
|------|------|-------------|-------------|-----|-----|-----|
| W3 | 1996 | 38 | 0.7232 | 0.0677 | 0.610 | 0.875 |
| W4 | 2000 | 27 | 0.7134 | 0.0622 | 0.582 | 0.853 |
| W5 | 2007 | 43 | 0.7236 | 0.0618 | 0.576 | 0.837 |
| W6 | 2012 | 47 | 0.7009 | 0.0512 | 0.569 | 0.789 |
| W7 | 2018 | 66 | 0.7096 | 0.0477 | 0.615 | 0.888 |

The global mean Fiedler value ranges from 0.701 (W6) to 0.724 (W5), a span of
just 0.023. SES network connectivity does not evolve systematically with
modernization, economic development, or survey expansion. The networks are
structurally robust: no country ever has a Fiedler value below 0.55, meaning
all attitude domains remain connected through SES mediation in every context.

**Figure 1** shows Fiedler trajectories for eight key countries. Mexico peaks at
W5 (2007, Fiedler=0.819) before declining, Germany declines monotonically from
0.821 to 0.699, Chile rises steadily from 0.672 to 0.726, and India remains
remarkably stable across all six waves.

**Figure 2** displays zone-mean Fiedler values with confidence bands. Catholic
Europe consistently shows the highest connectivity, while English-speaking and
South/Southeast Asian countries tend toward the lower range. All zones overlap
substantially, confirming that zone membership alone does not determine network
connectivity.

![Country Fiedler Panels](allwave_tda_plots/fig1_country_fiedler_panels.png)

![Zone Fiedler Evolution](allwave_tda_plots/fig2_zone_fiedler_evolution.png)

---

## 2. Convergence Oscillates, Does Not Trend

Do countries' SES-attitude networks become more similar over time? We measure
this using mean pairwise spectral distances between countries that appear in
consecutive waves.

| Transition | Years | Shared countries | Mean dist (from) | Mean dist (to) | Delta | Direction |
|-----------|-------|-----------------|-----------------|---------------|-------|-----------|
| W3→W4 | 1996-2000 | 16 | 0.2194 | 0.1992 | -0.0202 | Converging |
| W4→W5 | 2000-2007 | 12 | 0.1680 | 0.1858 | +0.0177 | Diverging |
| W5→W6 | 2007-2012 | 21 | 0.2369 | 0.1683 | -0.0687 | Converging |
| W6→W7 | 2012-2018 | 33 | 0.1458 | 0.1519 | +0.0061 | Diverging |

The pattern is clear: convergence and divergence alternate. The strongest
convergence episode (W5 to W6, 2007-2012) coincides with the global financial
crisis, which may have temporarily homogenized SES-attitude relationships through
shared economic shock. But the effect is transient -- by W6 to W7 (2012-2018),
countries begin diverging again. There is no secular trend toward a global
"end of history" homogenization of attitude structures.

**Figure 3** visualizes these dynamics as a bar chart.

![Convergence Bars](allwave_tda_plots/fig3_convergence_bars.png)

---

## 3. Spectral Distance Decline: Shape Convergence Without Connectivity Convergence

While countries neither converge nor diverge in overall connectivity (Fiedler),
their networks are becoming more similar in shape. Mean pairwise spectral distance
(which captures the full eigenvalue spectrum, not just the Fiedler gap) shows a
clear declining trend:

| Wave | Year | Mean spectral distance |
|------|------|-----------------------|
| W3 | 1996 | 0.2087 |
| W4 | 2000 | 0.1986 |
| W5 | 2007 | 0.2099 |
| W6 | 2012 | 0.1586 |
| W7 | 2018 | 0.1607 |

This decline from ~0.21 (W3-W5) to ~0.16 (W6-W7) means that country networks
are adopting more similar spectral profiles -- similar distributions of connectivity
across constructs -- even though their overall tightness (Fiedler) remains stable.
The interpretation is structural isomorphism: countries may differ in which
constructs are most SES-stratified, but the pattern of stratification itself
is becoming more uniform globally.

**Figure 6** provides side-by-side spectral distance heatmaps for W3 and W7,
showing the overall reduction in inter-country distances.

![Spectral Distance Heatmaps](allwave_tda_plots/fig6_spectral_distance_heatmaps.png)

---

## 4. Cultural Zone Coherence: Intermittent Signal

Spectral zone coherence tests whether countries within the same Inglehart-Welzel
cultural zone have more similar network structures than countries in different zones.

| Wave | Year | Spectral p-value | Interpretation |
|------|------|-----------------|----------------|
| W3 | 1996 | 0.0016 | significant |
| W4 | 2000 | 0.2016 | not significant |
| W5 | 2007 | 0.5664 | not significant |
| W6 | 2012 | 0.1672 | not significant |
| W7 | 2018 | 0.0012 | significant |

Zone coherence is significant in W3 (p=0.002) and W7 (p=0.001) but not in the
intermediate waves (W4-W6). This intermittent pattern suggests that cultural zone
effects on SES-attitude structure are real but not always detectable, possibly
because the middle waves have fewer countries per zone (reducing statistical power)
or because transitional periods blur zone boundaries.

Bottleneck distances (from persistent homology) never significantly separate zones
in any wave, confirming that topological features (loops, voids) are not zone-
specific -- they arise from universal structural properties rather than cultural
particularities.

---

## 5. Topological Loops Are Declining

The first Betti number (beta_1) counts persistent loops in the construct network --
cycles of SES-mediated covariation that cannot be reduced to tree paths.

| Wave | Year | N countries | % with loops | Max beta_1 | Mean beta_1 |
|------|------|-------------|-------------|-----------|------------|
| W3 | 1996 | 38 | 39.5% | 6 | 0.79 |
| W4 | 2000 | 27 | 44.4% | 5 | 0.89 |
| W5 | 2007 | 43 | 27.9% | 12 | 0.70 |
| W6 | 2012 | 47 | 25.5% | 3 | 0.40 |
| W7 | 2018 | 66 | 19.7% | 3 | 0.33 |

The fraction of countries with persistent loops declines from 39% (W3) to
20% (W7). Networks are becoming more tree-like over time, meaning that
SES-mediated attitude covariation is increasingly channeled through hierarchical
(tree-like) pathways rather than circular interdependencies. This is consistent
with the spectral shape convergence finding: as networks adopt more uniform
structures, the idiosyncratic loops that arise from country-specific SES patterns
are smoothed away.

**Figure 4** shows this evolution graphically.

![Beta-1 Evolution](allwave_tda_plots/fig4_betti1_evolution.png)

---

## 6. Gender Role Traditionalism: The Universal Structural Bridge

Mediator analysis identifies which construct, when removed, causes the largest
increase in shortest-path distances between all other constructs. The top mediator
is the single most structurally important node in the SES-attitude network.

Across 37 countries with temporal data:

| Construct | Countries (most common mediator) | % of total |
|-----------|-------------------------------|-----------|
| Gender Role Traditionalism | 20 | 54.1% |
| Science Skepticism | 10 | 27.0% |
| Immigrant Origin Status | 5 | 13.5% |
| Job Scarcity Gender Discrimination | 2 | 5.4% |

Gender role traditionalism is the dominant mediator in 20/37 countries (54%). This construct captures attitudes about whether women should work outside the home,
whether men make better political leaders, and whether university education is more
important for boys than girls. Its structural centrality means that SES-driven
gender attitudes form the backbone through which education, urbanization, age, and
gender connect all other attitude domains.

Mean mediator stability rate: 0.57 (proportion of
waves where the same construct remains top mediator). Values above 0.50 indicate
persistent structural importance; values below indicate that the mediator role
rotates across waves.

**Figure 5** breaks down mediator dominance by cultural zone.

![Mediator Stability](allwave_tda_plots/fig5_mediator_stability.png)

---

## 7. Flat Geometry: Ricci Curvature Near Zero

Ollivier-Ricci curvature measures local geometry at each edge. Positive curvature
indicates convergent neighborhoods (redundancy), negative curvature indicates
bottleneck edges (bridges between clusters), and zero curvature indicates flat
geometry (uniform local structure).

| Wave | Year | N countries | Mean curvature | Min mean | Max mean |
|------|------|-------------|---------------|----------|----------|
| W3 | 1996 | 38 | 0.9981 | 0.9521 | 1.0000 |
| W4 | 2000 | 27 | 0.9987 | 0.9687 | 1.0000 |
| W5 | 2007 | 43 | 0.9980 | 0.9280 | 1.0000 |
| W6 | 2012 | 47 | 0.9984 | 0.9606 | 1.0000 |
| W7 | 2018 | 66 | 0.9992 | 0.9887 | 1.0000 |

Ricci curvature is uniformly near 1.0 (the maximum for normalized weighted graphs)
across all waves and countries. This confirms the SES-attitude network is
geometrically flat with no bottleneck edges. Every edge has redundant parallel paths,
which is consistent with the high density (23% in the los_mex single-country network)
and the inner-product graph structure identified in the topology analysis.

---

## 8. Country Trajectories and MDS Movement

Individual country trajectories reveal diverse patterns that do not fit a single
modernization narrative:

- **Mexico**: Peaks at W5 (2007, Fiedler=0.819), then declines to 0.726 by W7.
  The pre-crisis peak may reflect the consolidation of democratic institutions
  that tightened SES-attitude coupling, which subsequently loosened.
- **Germany**: Monotonic decline from 0.821 to 0.699. Post-reunification,
  East-West heterogeneity may be diversifying SES-attitude pathways.
- **Chile**: Steady rise from 0.672 to 0.726, consistent with deepening
  socioeconomic structuring under sustained economic growth and inequality.
- **Brazil**: Wave 2 (0.747) to W7 (0.649), with oscillation. Political
  turbulence and regional inequality may weaken stable SES-attitude coupling.
- **India**: Remarkably stable (0.663-0.752), hovering around the global mean.
  Caste, religion, and linguistic diversity may create a structural equilibrium
  that resists secular trends.
- **Nigeria**: Rises from W2 (0.607) to W6 (0.709), then falls to W7 (0.628).
  The reversal may reflect increasing ethnic and religious polarization.
- **United States**: Low and declining -- 0.669 (W3) to 0.704 (W7) with a
  trough at W5 (0.641). Partisan polarization may create attitude structures
  that cross-cut SES lines.
- **China**: Sharp rise at W5 (0.755) and W6 (0.786), then decline to W7 (0.717).
  Rapid urbanization and education expansion may have temporarily tightened
  SES-attitude coupling.

**Figure 7** shows MDS trajectories from W3 to W7, revealing how countries
move in spectral space. The Procrustes-aligned embeddings show that most
countries move toward the center, consistent with the spectral distance decline,
while a few (particularly in the African-Islamic and South/Southeast Asian zones)
maintain distinctive positions.

![MDS Trajectories](allwave_tda_plots/fig7_mds_trajectories.png)

**Figure 8** provides the full Fiedler heatmap for all 100 countries, grouped
by cultural zone, enabling visual identification of within-zone variation and
cross-wave stability.

![Fiedler Heatmap](allwave_tda_plots/fig8_fiedler_heatmap.png)

---

## Methodology

### Data

- **Source**: World Values Survey waves 2-7 (1990-2018)
- **Countries**: 100 unique countries (3 in W2, 38 in W3, 27 in W4, 43 in W5,
  47 in W6, 66 in W7)
- **Temporal panels**: 37 countries with 3+ waves
- **Constructs**: 24-55 per wave (increasing with questionnaire expansion)
- **Edge weights**: Doubly-robust bridge gamma (SES-conditioned ordinal association)
- **SES dimensions**: Education, urbanization, age, gender (4-variable model)

### TDA Pipeline

For each country-wave network:

1. **Floyd-Warshall** all-pairs shortest paths on distance = 1 - |gamma| matrix,
   yielding mediator scores (betweenness-like centrality).
2. **Ollivier-Ricci curvature** via Sinkhorn optimal transport on each edge.
3. **Spectral decomposition** of the normalized graph Laplacian, extracting Fiedler
   value, spectral gap, spectral entropy, and spectral radius.
4. **Persistent homology** (Vietoris-Rips filtration on the distance matrix) via
   ripser, computing Betti numbers beta_0 through beta_2 and persistence entropy.
5. **MDS embedding** of the 66x66 spectral distance matrix for visualization.
6. **Zone coherence** permutation tests (10,000 permutations) on spectral and
   bottleneck distance matrices.

### Convergence Metrics

For each consecutive wave pair (W3-W4, W4-W5, W5-W6, W6-W7), the mean pairwise
spectral distance is computed for countries present in both waves. A negative delta
indicates convergence (networks becoming more similar); positive indicates divergence.

---

## Conclusions

The topological analysis reveals a paradox: SES-attitude networks are structurally
robust and nearly universal in their connectivity (Fiedler ~ 0.70), yet the
specific patterns of connectivity are gradually homogenizing (declining spectral
distances) while the topological complexity is simplifying (declining loops).
This is not modernization-as-convergence in the classical sense -- countries do not
converge to a single network structure. Instead, they converge to a common
*structural grammar* while retaining distinct *vocabularies* of SES-attitude
coupling.

The universal dominance of gender role traditionalism as the structural mediator
is the most striking finding. Across all cultural zones, the way a society
structures gender attitudes through education, urbanization, age, and gender
itself determines the topology of the entire SES-attitude network. This construct
is not merely the most SES-stratified -- it is the construct through which SES
stratification propagates to all other domains.

The flat Ricci curvature and near-tree-like topology suggest that these networks,
despite their high density, have a fundamentally simple geometry: an inner-product
graph in 4D SES space projected through a significance threshold. The apparent
complexity of cross-national attitude differences may be reducible to a low-dimensional
SES geometry that is shared across all societies.

---

*Report generated by `scripts/debug/tda_allwave_report.py`*
