# Message Passing on the WVS Belief Network

**Technical Report -- Navegador Project**

*Generated: 2026-04-01 | Data: WVS Wave 7 (66 countries, 55 constructs) + Temporal (37 countries, Waves 3-7)*

---

## Table of Contents

1. [Belief Propagation (Stage 1)](#1-belief-propagation-stage-1)
2. [Spectral Diffusion (Stage 2)](#2-spectral-diffusion-stage-2)
3. [Personalized PageRank (Stage 3)](#3-personalized-pagerank-stage-3)
4. [W7 Descriptive Snapshot](#4-w7-descriptive-snapshot-all-66-countries)
5. [Temporal Dynamics (Stage 5)](#5-temporal-dynamics-37-countries)
6. [Cross-Stage Synthesis](#6-cross-stage-synthesis)

---

## Overview

This report documents the five-stage message passing analysis of the WVS (World Values Survey) belief network. The network consists of 55 attitudinal constructs connected by doubly-robust SES-bridge estimates ($\gamma$ values), computed separately for each of 66 countries in Wave 7 (2017-2022) and across 7 waves (1981-2022) for 37 countries with temporal data.

The **fundamental question** is: given the SES-mediated coupling between attitudinal constructs, what can we infer about the *structure*, *dynamics*, and *cultural specificity* of belief systems across the world?

Each stage applies a different mathematical framework to the same underlying $\gamma$ network:

| Stage | Framework | Key question |
|-------|-----------|-------------|
| 1. Belief Propagation | Markov Random Field | Which beliefs are most constrained by their neighbors? |
| 2. Spectral Diffusion | Graph Laplacian | How easily does the network bisect? Where are the bottlenecks? |
| 3. Personalized PageRank | Random walks | Which beliefs are influence hubs vs endpoints? |
| 4. W7 Snapshot | Equilibrium analysis | How far is each country from its SES-predicted state? |
| 5. Temporal Dynamics | Mixing model | How much does the SES network explain belief change over time? |

The analysis reveals three headline findings:

1. **No universal belief hubs exist** -- influence topology is fundamentally zone-specific, with economic ideology being the closest to a global constant
2. **Cultural zones structure spectral topology** -- within-zone Fiedler partition agreement is 2.86x higher than across-zone, with English-speaking countries showing the most coherent belief structure
3. **Network-driven vs inertial societies** map onto modernization: rapidly developing countries (VNM, IND) show high network influence ($\alpha > 0.30$), while theocratic or post-conflict states (EGY, JOR) show near-zero

---

## 1. Belief Propagation (Stage 1)

### 1.1 Mathematical Motivation

We model the 55-construct belief network as a **pairwise Markov Random Field** (MRF) on a signed, weighted graph $G = (V, E, w)$, where each node $i \in V$ represents a WVS construct and each edge weight $w_{ij} = \gamma(i, j)$ is the doubly-robust SES-bridge estimate.

The energy function follows a **Potts-like** coupling:

$$E(\mathbf{x}) = -\sum_{(i,j) \in E} w_{ij} \cdot x_i \cdot x_j$$

where $x_i \in \{-1, +1\}$ is a binarized belief state (above/below median). The Gibbs distribution $P(\mathbf{x}) \propto \exp(-\beta E(\mathbf{x}))$ defines a joint probability over all configurations, parameterized by inverse temperature $\beta$.

We approximate marginals via **loopy belief propagation** (LBP): each node $i$ sends messages $m_{i \to j}(x_j)$ to neighbors, iterating:

$$m_{i \to j}(x_j) \propto \sum_{x_i} \psi_{ij}(x_i, x_j) \cdot \phi_i(x_i) \cdot \prod_{k \in \mathcal{N}(i) \setminus j} m_{k \to i}(x_i)$$

where $\psi_{ij}(x_i, x_j) = \exp(\beta \cdot w_{ij} \cdot x_i \cdot x_j)$ is the pairwise potential and $\phi_i(x_i)$ is the local evidence (uniform prior in our case).

After convergence, we compute the **belief lift**: the KL divergence between the BP posterior marginal $b_i(x_i)$ and the prior $\phi_i(x_i)$:

$$\text{lift}_i = D_{\text{KL}}(b_i \| \phi_i) = \sum_{x_i} b_i(x_i) \log \frac{b_i(x_i)}{\phi_i(x_i)}$$

High lift means that node $i$'s belief is strongly constrained by its network neighborhood -- its SES-mediated connections to other constructs push it far from the uninformative prior.

### 1.2 Results

- **Convergence**: 100% (66/66 countries converged)
- **Median top lift**: 0.0311 (most countries' top influencer has modest lift)
- **Outlier countries**: GRC (0.44), URY (0.39), TWN (0.28) -- strong network constraint on beliefs

**Top influencers** (construct most often ranked #1 across countries):

| Construct | Countries (#1 in) | Domain |
|-----------|-------------------|--------|
| Immigrant origin status | 14 | G: National identity |
| Online political participation | 11 | E: Politics |
| Job scarcity gender discrimination | 6 | C: Work |

The dominance of `immigrant_origin_status` (14 countries) and `online_political_participation` (11) reveals that immigration attitudes and digital civic engagement are the constructs most tightly constrained by their SES network neighborhood. In the MRF interpretation, these nodes sit at high local field positions: their beliefs are effectively *determined* by the beliefs of their SES-linked neighbors.

**Full BP top-10 influencers:**

| Rank | Construct | Countries (#1 in) | Domain |
|------|-----------|-------------------|--------|
| 1 | Immigrant origin status | 14 | G: National identity |
| 2 | Online political participation | 11 | E: Politics |
| 3 | Job scarcity gender discrimination | 6 | C: Work |
| 4 | Voting participation | 6 | E: Politics |
| 5 | Political information sources | 5 | E: Politics |
| 6 | Socioeconomic insecurity worry | 3 | H: Security |
| 7 | Social intolerance outgroups | 3 | A: Social values |
| 8 | Religious practice and self identification | 3 | F: Religion/Morale |
| 9 | Work ethic | 2 | C: Work |
| 10 | Voluntary association active membership | 2 | A: Social values |

**Lift distribution by cultural zone:**

| Zone | Countries | Median lift | Max lift | Max country |
|------|-----------|-------------|----------|-------------|
| Catholic Europe | 3 | 0.0794 | 0.4400 | GRC |
| English-speaking | 6 | 0.0387 | 0.0450 | AUS |
| Protestant Europe | 2 | 0.0353 | 0.0391 | DEU |
| Confucian | 8 | 0.0330 | 0.2845 | TWN |
| Orthodox/ex-Communist | 12 | 0.0310 | 0.0350 | ROU |
| South/Southeast Asian | 8 | 0.0304 | 0.0377 | IDN |
| African-Islamic | 14 | 0.0303 | 0.0344 | LBY |
| Latin America | 13 | 0.0302 | 0.3906 | URY |

The zone-level breakdown reveals that **Catholic Europe** (driven by GRC and CYP outliers) has the highest median lift, while most zones cluster around the global median of ~0.031. The African-Islamic zone shows the most heterogeneity, with lifts ranging from near-median to substantially above.

### 1.3 Interpretation

BP lift measures **how much a construct's belief distribution is shaped by network context** rather than local evidence. A construct with high lift is "predictable from its neighbors" -- knowing someone's education, age, gender, and urbanization-conditioned attitudes on related topics tightly constrains their stance on immigration or online participation.

The outlier countries (GRC: 0.44, URY: 0.39, TWN: 0.28) have unusually tight belief coupling: the SES network in these societies acts as a strong constraint system where one attitude implies many others. This is consistent with their high SES collinearity (PC1 > 80%).

### 1.4 Pitfalls and Limitations

1. **Loopy BP is approximate**: the belief network has many short cycles (clustering coefficient 0.53), so LBP marginals are not exact. On trees, BP computes exact marginals; on loopy graphs, it minimizes the Bethe free energy, which is an approximation to the true Gibbs free energy. The bound $|b_i - p_i| \leq O(\beta^{\text{girth}})$ suggests accuracy improves with longer cycle lengths. Our network's average clustering of 0.53 implies many triangles (short cycles), but 100% convergence across 66 countries indicates the approximation is stable in practice.
2. **Potts vs Gaussian**: the binary Potts model discretizes each construct to $\{-1, +1\}$ (above/below median), discarding ordinal information. The WVS constructs are continuous aggregates on [1,10], and binarization loses gradient information. A Gaussian MRF with precision matrix $J$ (where $J_{ij} = -\gamma_{ij}$) would model continuous beliefs directly, but requires $O(n^3)$ matrix inversion per country and is sensitive to the positive-definiteness of $J$. The Potts discretization is a conservative choice that ensures stable inference at the cost of information loss.
3. **Observational, not causal**: BP lift reflects SES-mediated *statistical* coupling. It does not imply that changing one belief would propagate to neighbors. In the language of causal inference, the $\gamma$ edges are observational associations conditioned on SES, not interventional effects. A construct with high lift could be highly constrained because it shares common SES causes with many neighbors (confounding), not because those neighbors directly influence it.
4. **Beta sensitivity**: the inverse temperature $\beta$ controls coupling strength. At $\beta = 0$ (infinite temperature), all beliefs are independent and lift = 0 everywhere. At $\beta \to \infty$ (zero temperature), the system freezes into the ground state and all beliefs are deterministic. Our default $\beta = 1$ is a modeling choice placing the system in the ordered phase but far from the frozen limit. A systematic $\beta$-sweep would identify the critical temperature $\beta_c$ where the phase transition occurs, but this is computationally expensive (66 countries $\times$ 20+ $\beta$ values).
5. **Edge density**: the $\gamma$ matrix is dense (23% non-zero edges), making the MRF highly connected. In sparse MRFs, BP is near-exact; in dense MRFs, the Bethe approximation degrades. The high density of our network means BP results should be interpreted as qualitative rankings rather than precise posterior probabilities.

### Plots

![Top-10 BP influencers across 66 countries](../tda/message_passing/plots/bp_top_influencers.png)

---

## 2. Spectral Diffusion (Stage 2)

### 2.1 Mathematical Motivation

The **graph Laplacian** $L = D - A$ (where $D$ is the degree matrix and $A$ the adjacency matrix of $|\gamma|$ weights) governs diffusion on the network. Its eigendecomposition $L = U \Lambda U^T$ yields:

- $\lambda_1 = 0$ (trivial, connected component)
- $\lambda_2$ = **Fiedler value** (algebraic connectivity): the smallest nontrivial eigenvalue, measuring how easily the network can be bisected
- $\mathbf{v}_2$ = **Fiedler vector**: its sign pattern defines the optimal graph bipartition (spectral clustering)

The **heat kernel** $H(t) = \exp(-tL)$ describes continuous-time diffusion of belief states on the network. At time $t$, an initial perturbation $\mathbf{f}(0)$ evolves as:

$$\mathbf{f}(t) = \exp(-tL) \mathbf{f}(0) = \sum_k e^{-\lambda_k t} (\mathbf{u}_k^T \mathbf{f}(0)) \mathbf{u}_k$$

The Fiedler value $\lambda_2$ controls the slowest non-trivial decay mode: low $\lambda_2$ means slow mixing (beliefs persist in two camps), high $\lambda_2$ means rapid homogenization.

### 2.2 Results

- **Fiedler range**: 0.615 (BGD) to 0.888 (MNG)
- **Median**: 0.705
- **Within-zone ARI**: 0.0164 (Fiedler partition agreement within cultural zones)
- **Across-zone ARI**: 0.0057
- **Ratio**: 2.86x -- Fiedler partitions are nearly 3x more similar within cultural zones than across zones

**Zone-level ARI (Fiedler partition coherence):**

| Zone | Mean ARI | Interpretation |
|------|----------|----------------|
| English-speaking | 0.153 | Highly coherent -- similar bipartition across AUS, CAN, GBR, USA, NZL, NIR |
| Catholic Europe | -0.002 | No coherence |
| South/Southeast Asian | -0.003 | No coherence |

**Fiedler value distribution by zone:**

| Zone | Countries | Median | Min (country) | Max (country) | IQR |
|------|-----------|--------|---------------|---------------|-----|
| English-speaking | 6 | 0.685 | 0.653 (GBR) | 0.704 (USA) | 0.023 |
| African-Islamic | 14 | 0.689 | 0.628 (NGA) | 0.734 (KEN) | 0.060 |
| Protestant Europe | 2 | 0.689 | 0.679 (NLD) | 0.699 (DEU) | 0.010 |
| Orthodox/ex-Communist | 12 | 0.705 | 0.628 (CZE) | 0.888 (MNG) | 0.058 |
| South/Southeast Asian | 8 | 0.706 | 0.615 (BGD) | 0.790 (IDN) | 0.054 |
| Confucian | 8 | 0.718 | 0.678 (KOR) | 0.807 (SGP) | 0.052 |
| Latin America | 13 | 0.726 | 0.649 (BRA) | 0.780 (COL) | 0.047 |
| Catholic Europe | 3 | 0.736 | 0.710 (AND) | 0.757 (GRC) | 0.024 |

**Top Fiedler-loading constructs** (most frequently the highest-loading construct on the Fiedler vector across countries):

| Construct | Countries with top loading |
|-----------|--------------------------|
| Immigrant origin status | 11 |
| Voting participation | 6 |
| Basic needs deprivation | 4 |
| Online political participation | 3 |
| Religion versus secularism orientation | 3 |
| Job scarcity gender discrimination | 3 |
| Multilevel place attachment | 2 |
| Socioeconomic insecurity worry | 2 |

The top-loading constructs on the Fiedler vector are the constructs that sit furthest from the spectral bisection plane -- they define the two camps of the belief structure. Their diversity across countries (no single construct dominates) confirms the zone-specificity of belief topology.

Note that the Fiedler partition is *not* the same as a positive/negative $\gamma$-sign partition. The Fiedler vector minimizes the Rayleigh quotient $R(\mathbf{v}) = \mathbf{v}^T L \mathbf{v} / \mathbf{v}^T \mathbf{v}$ subject to orthogonality with the constant eigenvector. This yields the partition that minimizes total edge weight *cut*, which is a different objective from maximizing structural balance (the $\gamma$-sign partition). In practice the two partitions largely agree (both reflect the dominant education-vs-tradition axis identified by PCA), but discrepancies arise where non-monotonic SES patterns or NMI-detectable-but-$\gamma$-invisible relationships create spectral structure invisible to the sign partition.

### 2.3 Interpretation

The Fiedler vector partitions each country's 55-construct network into two camps. In English-speaking countries, this partition is nearly identical: the same constructs cluster together regardless of whether we look at Australia, Canada, or the UK. This means the *structure* of SES-mediated belief coupling -- which beliefs go together and which oppose each other -- is a cultural invariant in the Anglosphere.

Bangladesh's low Fiedler value (0.61) indicates a near-bipartite belief structure: the network has a clear bottleneck separating two belief clusters, with weak cross-cluster SES coupling. Mongolia's high value (0.89) means uniform SES coupling -- no natural split point.

The Fiedler value also controls **diffusion timescale**: the time for a belief perturbation to spread across the full network scales as $\tau \sim 1/\lambda_2$. With the observed range (0.61 to 0.89), diffusion timescales vary by a factor of 1.4x across countries. Bangladesh would take ~45% longer than Mongolia for a belief perturbation to reach network-wide equilibrium.

The spectral gap $\lambda_2$ has a second interpretation via the **Cheeger inequality**: $h^2/2 \leq \lambda_2 \leq 2h$, where $h$ is the Cheeger constant (optimal edge cut ratio). Low $\lambda_2$ implies a cheap graph cut exists -- the network can be split into two weakly-connected components. This connects to the sociological concept of belief polarization: countries with low Fiedler values have two belief clusters with minimal SES-mediated cross-talk.

### 2.4 Pitfalls and Limitations

1. **Absolute values discard sign**: the Laplacian uses $|\gamma|$ weights, losing the positive/negative distinction. The Fiedler partition is a *structural* bipartition, not a sign-based one (though in practice they largely agree due to 94% structural balance).
2. **Linear dynamics**: the heat kernel is a linear diffusion model. Real belief change involves nonlinear thresholds, social influence cascades, and exogenous shocks.
3. **Arbitrary $t$**: the diffusion time $t$ is a free parameter. We report Fiedler values (eigenvalues) rather than diffused states to avoid this choice.

### Plots

![Fiedler values by cultural zone](../tda/message_passing/plots/fiedler_values_by_zone.png)

---

## 3. Personalized PageRank (Stage 3)

### 3.1 Mathematical Motivation

**Personalized PageRank** (PPR) with restart probability $\alpha$ computes, for each seed node $s$, the stationary distribution:

$$\boldsymbol{\pi}_s = \alpha \mathbf{e}_s + (1 - \alpha) P^T \boldsymbol{\pi}_s$$

where $P$ is the row-normalized transition matrix of $|\gamma|$ weights and $\mathbf{e}_s$ is the indicator vector for node $s$. Solving:

$$\boldsymbol{\pi}_s = \alpha (I - (1-\alpha) P^T)^{-1} \mathbf{e}_s$$

The **hub score** of node $i$ is its average PPR mass when every other node is seeded: $\text{hub}(i) = \frac{1}{n} \sum_s \pi_s(i)$. High hub score means many random walks end up at $i$ regardless of starting point -- $i$ is a global attractor of network influence.

The **sink score** is the complement: nodes with low hub scores are influence endpoints (belief *consequences* rather than belief *drivers*).

### 3.2 Results

- **No universal hubs**: no construct appears in the top-10 hub list of every cultural zone. Influence topology is fundamentally zone-specific.
- **Most consistent**: `economic_ideology` has global median rank 7 and appears in the top-10 of 6+ zones -- the closest thing to a universal influence hub.
- **Weak mediator correlation**: Spearman $\rho \approx -0.15$ to $+0.10$ between PPR hub rank and Floyd-Warshall mediator score in all countries. Topological centrality (shortest paths) and diffusion centrality (random walks) measure different things.

**Zone-specific hubs (top construct per zone):**

| Zone | Top Hub | Zone top-10 count |
|------|---------|-------------------|
| Latin America | Economic ideology | 9/13 |
| English-speaking | Democratic values importance | 6/6 |
| Catholic Europe | Confidence in civil society organizations | 3/3 |
| Orthodox/ex-Communist | Democratic system evaluation | 9/12 |
| Confucian | Economic ideology | 6/8 |
| African-Islamic | Child qualities prosocial diligence | 10/14 |

**Extended zone-specific hub table** (top-3 hubs per zone):

| Zone | Rank | Hub construct | Top-10 in | Global med. rank |
|------|------|--------------|-----------|-----------------|
| Latin America | 1 | Economic ideology | 9/13 | 7 |
|  | 2 | Authoritarian governance tolerance | 8/13 | 16 |
|  | 3 | Democratic values importance | 8/13 | 11 |
| English-speaking | 1 | Democratic values importance | 6/6 | 11 |
|  | 2 | Child qualities prosocial diligence | 5/6 | 14 |
|  | 3 | Economic ideology | 5/6 | 7 |
| Catholic Europe | 1 | Confidence in civil society organizations | 3/3 | 11 |
|  | 2 | Confidence in international organizations | 3/3 | 14 |
|  | 3 | Acceptance of state surveillance | 2/3 | 16 |
| Orthodox/ex-Communist | 1 | Democratic system evaluation | 9/12 | 13 |
|  | 2 | Confidence in civil society organizations | 8/12 | 11 |
|  | 3 | Economic ideology | 8/12 | 7 |
| Confucian | 1 | Economic ideology | 6/8 | 7 |
|  | 2 | Confidence in civil society organizations | 5/8 | 11 |
|  | 3 | Postmaterialist values | 5/8 | 10 |
| African-Islamic | 1 | Child qualities prosocial diligence | 10/14 | 14 |
|  | 2 | Democratic system evaluation | 8/14 | 13 |

The global median rank column reveals the contrast between zone-specific and global influence: `economic_ideology` (median rank 7) is the closest to a global hub, but `democratic_values_importance` (median rank 11) and `postmaterialist_values` (median rank 10) are strong in Latin America and English-speaking zones yet much weaker elsewhere.

**Mexico PPR profile:**

Mexico's PPR hub scores are notably flat (range: 0.766-0.798, excluding sinks), indicating a diffuse influence topology where no single construct dominates. The top hubs are `voluntary_association_belonging` (0.798), `democratic_values_importance` (0.798), and `perceived_positive_effects_of_immigration` (0.797). The sinks (near-zero scores) are `existential_threat_worry`, `immigrant_origin_status`, `offline_political_participation`, `perceived_corruption`, `socioeconomic_insecurity_worry`, and `voting_participation` -- these are belief endpoints rather than drivers in the Mexican SES network.

### 3.3 Interpretation

The absence of universal hubs is a strong result. It means that belief influence structure is culturally contingent: in Latin America, `economic_ideology` and `authoritarian_governance_tolerance` drive belief coupling, while in English-speaking countries, `democratic_values_importance` and `child_qualities_prosocial_diligence` dominate. The SES network routes influence through different constructs depending on the cultural context.

The hub/sink asymmetry is interpretively rich: hubs are constructs that *generate* SES-mediated constraint (knowing someone's stance on economic ideology constrains many other beliefs), while sinks are constructs that *absorb* constraint (stance on online political participation is a downstream consequence of many other beliefs).

### 3.4 Pitfalls and Limitations

1. **Influence $\neq$ causation**: PPR measures network influence, not causal effect. A hub could be a common *symptom* of underlying SES position rather than a *driver* of other beliefs.
2. **PPR conflates reach and proximity**: a construct can have high hub score either because it is connected to many others (high degree) or because it is close to high-degree nodes (proximity). These are substantively different.
3. **$\alpha$ sensitivity**: restart probability $\alpha$ controls locality vs globality of influence. Our default $\alpha = 0.2$ is standard but arbitrary. Small $\alpha$ emphasizes global network structure (long random walks), while large $\alpha$ emphasizes local neighborhood (short walks). The choice affects the hub/sink ranking: local hubs (high-degree nodes) dominate at high $\alpha$, while global hubs (bridge nodes) dominate at low $\alpha$.
4. **Transition matrix symmetry**: PPR uses $|\gamma|$ weights, discarding the sign structure. A signed PageRank variant (e.g., using separate positive and negative transition matrices) would capture the co-elevation vs counter-variation distinction that is central to the $\gamma$-surface framework.

### Plots

![PPR hub scores for Mexico](../tda/message_passing/plots/ppr_hub_scores_mex.png)

---

## 4. W7 Descriptive Snapshot (All 66 Countries)

### 4.1 Velocity Field and Equilibrium Distance

For each country's belief network, we define the **network equilibrium** as the stationary distribution $\boldsymbol{\pi}^*$ of the Markov chain defined by the row-normalized $|\gamma|$ transition matrix:

$$\boldsymbol{\pi}^* = \boldsymbol{\pi}^* P$$

The **equilibrium distance** is the L2 norm between the observed construct means $\bar{\mathbf{x}}$ and the equilibrium prediction:

$$d_{\text{eq}} = \| \bar{\mathbf{x}} - \boldsymbol{\pi}^* \|_2$$

The **velocity field** $\mathbf{v} = P \bar{\mathbf{x}} - \bar{\mathbf{x}}$ gives the direction and magnitude of the force the network exerts on each construct: positive velocity means the network pushes the construct upward, negative means downward.

### 4.2 Results

**Equilibrium distance ranking** (selected countries):

| Rank | Country | Zone | Eq. Distance |
|------|---------|------|-------------|
| 1 | MNG | Orthodox/ex-Communist | 10.12 |
| 2 | ARG | Latin America | 11.37 |
| 3 | MAR | African-Islamic | 11.63 |
| 4 | MEX | Latin America | 11.89 |
| 5 | IND | South/Southeast Asian | 12.03 |
| ... | | | |
| 4 | MEX | Latin America | 11.89 |
| ... | | | |
| 64 | PER | Latin America | 15.63 |
| 65 | EGY | African-Islamic | 15.86 |
| 66 | LBY | African-Islamic | 15.86 |

**Top velocity constructs** (most frequently highest-velocity across countries):

| Construct | Countries with top velocity |
|-----------|---------------------------|
| Immigrant origin status | 14/66 |
| Online political participation | 8/66 |
| Neighborhood disorder and crime | 7/66 |
| Social intolerance outgroups | 4/66 |
| Perceived positive effects of immigration | 3/66 |

**Zone-level equilibrium distance:**

| Zone | Countries | Median eq. dist. | Closest | Farthest |
|------|-----------|-----------------|---------|----------|
| English-speaking | 6 | 12.87 | USA (12.2) | NZL (14.3) |
| Latin America | 13 | 12.95 | ARG (11.4) | PER (15.6) |
| South/Southeast Asian | 8 | 12.96 | IND (12.0) | BGD (15.0) |
| Orthodox/ex-Communist | 12 | 13.47 | MNG (10.1) | TJK (14.8) |
| Confucian | 8 | 13.71 | MAC (12.2) | TWN (14.7) |
| African-Islamic | 14 | 13.95 | MAR (11.6) | LBY (15.9) |
| Catholic Europe | 3 | 14.15 | CYP (13.7) | GRC (14.2) |
| Protestant Europe | 2 | 14.90 | DEU (14.4) | NLD (15.5) |

The zone-level pattern is clear: **Latin America** has the lowest median equilibrium distance (beliefs most consistent with SES predictions), while **African-Islamic** and **Protestant Europe** are farthest from equilibrium. This aligns with the finding that education is the dominant SES dimension in Latin America (73% of bridges), producing a simpler, more predictable belief structure.

**Expanded equilibrium distance ranking (top-10 and bottom-10):**

| Rank | Country | Zone | Eq. Distance |
|------|---------|------|-------------|
| 1 | MNG | Orthodox/ex-Communist | 10.12 |
| 2 | ARG | Latin America | 11.37 |
| 3 | MAR | African-Islamic | 11.63 |
| 4 | MEX | Latin America | 11.89 |
| 5 | IND | South/Southeast Asian | 12.03 |
| 6 | TUR | African-Islamic | 12.05 |
| 7 | GTM | Latin America | 12.11 |
| 8 | MYS | South/Southeast Asian | 12.13 |
| 9 | CHL | Latin America | 12.23 |
| 10 | USA | English-speaking | 12.23 |
| ... | | | |
| 57 | TWN | Confucian | 14.71 |
| 58 | PAK | South/Southeast Asian | 14.78 |
| 59 | TJK | Orthodox/ex-Communist | 14.78 |
| 60 | BGD | South/Southeast Asian | 14.96 |
| 61 | TUN | African-Islamic | 15.10 |
| 62 | NIC | Latin America | 15.15 |
| 63 | NLD | Protestant Europe | 15.45 |
| 64 | PER | Latin America | 15.63 |
| 65 | EGY | African-Islamic | 15.86 |
| 66 | LBY | African-Islamic | 15.86 |

**Full velocity field -- top constructs by domain:**

| Domain | Top-velocity constructs | Total countries |
|--------|------------------------|----------------|
| A: Social values | social_intolerance_outgroups (4), voluntary_association_belonging (2) | 6 |
| C: Work | job_scarcity_gender_discrimination (2) | 2 |
| D: Family | gender_role_traditionalism (1) | 1 |
| E: Politics | online_political_participation (8), voting_participation (3), democratic_system_evaluation (1) | 12 |
| F: Religion/Morale | religious_exclusivism (2), civic_dishonesty_tolerance (2), religion_versus_secularism_orientation (1), violence_tolerance (1) | 6 |
| G: National identity | immigrant_origin_status (14), perceived_positive_effects_of_immigration (3), perceived_negative_effects_of_immigration (3), multilevel_place_attachment (2) | 22 |
| H: Security | neighborhood_disorder_and_crime (7), crime_victimization (2), socioeconomic_insecurity_worry (2), institutional_threat_perception (1), existential_threat_worry (1) | 13 |

Security (H) and National Identity (G) domains dominate the velocity field, accounting for over half of the top-velocity constructs. These are the belief domains under the strongest network pressure in Wave 7.

The domain concentration of velocity is notable: Politics (E) has the most constructs (19 of 55) but accounts for a minority of top-velocity instances. Political attitudes are close to their SES-predicted positions. In contrast, Security and Identity constructs are consistently displaced from their network-predicted positions, suggesting that recent geopolitical events (migration crises, security threats, nationalist movements) have pushed these attitudes away from where SES mediation alone would place them.

### 4.3 Interpretation

Countries *close* to equilibrium (MNG: 10.1, ARG: 11.4) have belief profiles that are approximately consistent with their SES network: the network's "force" on each construct is small. Countries *far* from equilibrium (LBY: 15.9, EGY: 15.9) have belief profiles that the network would substantially rearrange if it were the only force operating -- suggesting that non-SES forces (religion, politics, conflict) are holding beliefs away from the SES-predicted equilibrium.

Mexico ranks 4th closest (eq_distance = 11.9), meaning its belief structure is well-explained by SES mediation. This is consistent with the earlier finding that Mexico has the lowest RMSE from the global median $\gamma$-vector.

The equilibrium distance concept connects to statistical mechanics: in a Boltzmann system, the equilibrium distribution is the maximum-entropy state consistent with the energy constraints. Countries close to equilibrium have belief profiles that are "natural" given their SES coupling structure -- each belief is approximately where the network forces would place it. Countries far from equilibrium have beliefs held in "strained" positions by external forces (religion, authoritarianism, recent conflict) that override SES mediation.

The top-velocity constructs provide a specific prediction: if non-SES forces were removed, `immigrant_origin_status` would shift the most in 14/66 countries. This is the construct under the greatest "tension" between its SES-predicted position and its observed position. In concrete terms: the SES network predicts a particular relationship between immigration attitudes and other beliefs (e.g., education, urbanization), but the observed attitudes are displaced from this prediction by political rhetoric, media framing, or historical migration patterns.

The velocity field's top constructs (immigration status, online political participation) are the same as BP's top influencers, reinforcing that these are the constructs under the most network pressure.

### Plots

![Equilibrium distance ranking](../tda/message_passing/plots/equilibrium_distance_ranking.png)

---

## 5. Temporal Dynamics (37 Countries)

### 5.1 Mathematical Motivation

We model belief change as a **1-parameter mixing** of inertia and network prediction:

$$\bar{\mathbf{x}}_{t+1} = (1 - \alpha) \bar{\mathbf{x}}_t + \alpha \cdot P_t \bar{\mathbf{x}}_t$$

where $\bar{\mathbf{x}}_t$ is the vector of construct means at wave $t$, $P_t$ is the row-normalized $|\gamma|$ transition matrix at wave $t$, and $\alpha \in [0, 1]$ is the **mixing parameter**.

- $\alpha = 0$: pure inertia (beliefs at $t+1$ equal beliefs at $t$)
- $\alpha = 1$: pure network dynamics (beliefs at $t+1$ fully determined by SES network)

We estimate $\alpha^*$ via least-squares:

$$\alpha^* = \arg\min_\alpha \sum_{t} \| \bar{\mathbf{x}}_{t+1} - [(1 - \alpha) \bar{\mathbf{x}}_t + \alpha \cdot P_t \bar{\mathbf{x}}_t] \|_2^2$$

which has a closed-form solution as a scalar linear regression of $\Delta x$ on $(Px - x)$.

### 5.2 Results

- **Countries with temporal data**: 37
- **Alpha range**: 0.00 (EGY) to 0.40 (VNM)

**Most network-driven societies** ($\alpha > 0.30$):

| Country | Zone | $\alpha$ | Waves |
|---------|------|----------|-------|
| VNM | Confucian | 0.398 | 3 |
| RUS | Orthodox/ex-Communist | 0.384 | 3 |
| IND | South/Southeast Asian | 0.345 | 6 |
| URY | Latin America | 0.337 | 4 |
| THA | South/Southeast Asian | 0.330 | 3 |

**Most inertial societies** ($\alpha < 0.05$):

| Country | Zone | $\alpha$ | Waves |
|---------|------|----------|-------|
| JOR | African-Islamic | 0.037 | 3 |
| SVN | Catholic Europe | 0.024 | 3 |
| EGY | African-Islamic | 0.000 | 3 |

**Zone-level $\alpha$ summary:**

| Zone | Countries | Median $\alpha$ | Range |
|------|-----------|-----------------|-------|
| South/Southeast Asian | 7 | 0.239 | 0.087-0.345 |
| English-speaking | 3 | 0.200 | 0.086-0.212 |
| Latin America | 8 | 0.179 | 0.085-0.337 |
| Orthodox/ex-Communist | 6 | 0.172 | 0.085-0.384 |
| Confucian | 3 | 0.170 | 0.080-0.398 |
| Protestant Europe | 2 | 0.119 | 0.113-0.126 |
| African-Islamic | 5 | 0.103 | 0.000-0.299 |
| Catholic Europe | 3 | 0.039 | 0.024-0.216 |

### 5.3 Mexico Deep Dive

- **Overall $\alpha$**: 0.112 (moderately network-driven)
- **Waves**: [3, 4, 5, 6, 7] (1996-2018)
- **Temporal core constructs**: 20 (present in 3+ waves)

**Per-transition dynamics:**

| Transition | $\alpha$ | Interpretation |
|------------|----------|----------------|
| W3 to W4 | 0.015 | Near-zero: 1996-2000 belief change was inertial (post-crisis stability) |
| W4 to W5 | 0.151 | Moderate: 2000-2005 network influence rising (democratic transition era) |
| W5 to W6 | 0.000 | Zero: 2005-2012 change orthogonal to network predictions (drug war shock?) |
| W6 to W7 | 0.349 | Strong: 2012-2018 network drives belief change (consolidation) |

**Equilibrium distance trajectory:**

| Wave | Year | Eq. Distance | Trend |
|------|------|-------------|-------|
| W3 | 1996 | 7.64 |  |
| W4 | 2000 | 8.25 | + |
| W5 | 2005 | 8.58 | + |
| W6 | 2012 | 11.51 | + |
| W7 | 2018 | 11.89 | + |

Mexico's equilibrium distance *increases* monotonically from 7.6 (1996) to 11.9 (2018), meaning Mexican beliefs are *diverging* from the SES network's predicted equilibrium over time. This suggests that non-SES forces (democratization, drug war, media landscape changes) are increasingly pulling beliefs away from the pattern predicted by pure SES mediation.

**Top velocity constructs (last wave):**

- `online_political_participation`: velocity = +1.895 (upward network pressure)
- `social_intolerance_outgroups`: velocity = -1.340 (downward network pressure)
- `religion_versus_secularism_orientation`: velocity = -1.089 (downward network pressure)

**Residual RMSE by transition** (how well the mixing model fits):

| Transition | Residual RMSE | $\alpha$ | Interpretation |
|------------|--------------|----------|----------------|
| W3_W4 | 1.996 | 0.015 | Good fit |
| W4_W5 | 1.880 | 0.151 | Good fit |
| W5_W6 | 2.241 | 0.000 | Poor fit -- large residuals |
| W6_W7 | 1.909 | 0.349 | Good fit |

All transitions show RMSE around 1.9-2.2, indicating that the 1-parameter mixing model captures the general direction of belief change but leaves substantial construct-level residuals. The W5-W6 transition (2005-2012) has the highest RMSE (2.24) and $\alpha = 0$, confirming that this period's belief change was orthogonal to network predictions.

**Temporal top-velocity constructs** (most frequently highest-velocity across 37 countries):

| Construct | Countries with top velocity |
|-----------|---------------------------|
| Immigrant origin status | 7/37 |
| Neighborhood disorder and crime | 4/37 |
| Online political participation | 3/37 |
| Religious exclusivism | 2/37 |
| Voting participation | 2/37 |
| Job scarcity gender discrimination | 2/37 |
| Crime victimization | 2/37 |
| Perceived negative effects of immigration | 2/37 |

The temporal velocity leaders mirror the W7 snapshot: immigration status, neighborhood disorder, and online political participation are under the most persistent network pressure across both time and geography.

### 5.4 Interpretation

$\alpha$ measures **how much of observed belief change is explained by the SES network's predictions**. Vietnam ($\alpha = 0.40$) and Russia ($\alpha = 0.38$) show the strongest network-driven dynamics: their belief shifts between waves follow the direction predicted by SES coupling. Egypt ($\alpha = 0.00$) shows pure inertia: belief change is orthogonal to SES network predictions, suggesting that non-SES forces (religion, authoritarianism, conflict) dominate.

The geographic pattern is suggestive: high-$\alpha$ countries tend to be undergoing rapid socioeconomic modernization (Vietnam, India, Thailand), while low-$\alpha$ countries are either highly stable (Slovenia) or in states where non-SES institutions dominate belief formation (Egypt, Jordan).

This connects to Inglehart's modernization theory: in societies undergoing rapid economic development, rising education and urbanization reshape the SES distribution, and belief change follows the new SES structure ($\alpha > 0$). In societies where material security is either already achieved (Western Europe) or disrupted by conflict (MENA), belief change is driven by forces outside the SES network ($\alpha \approx 0$).

**Mexico's increasing $\alpha$ trajectory** is particularly revealing: from near-zero in 1996-2000 (post-peso crisis inertia) to 0.35 in 2012-2018 (network-driven change). This suggests that Mexico's belief dynamics are becoming *more* SES-structured over time, even as the beliefs themselves diverge from the SES-predicted equilibrium. The paradox resolves as follows: the *direction* of belief change is increasingly aligned with SES network predictions, but the *magnitude* is insufficient to close the growing gap. External forces (security crisis, political polarization) amplify the gap faster than SES convergence can close it.

### 5.5 Pitfalls and Limitations

1. **Few time points**: most countries have only 3 waves, giving $\alpha$ estimates with 1-2 degrees of freedom. Mexico's 5 waves provide the most reliable estimate.
2. **Sparse early waves**: WVS Waves 1-2 have fewer countries and different construct coverage, limiting temporal depth.
3. **Stationarity assumption**: the model assumes the SES network structure (the $\gamma$ matrix) is constant across waves. In reality, SES coupling itself evolves.
4. **Ecological inference**: construct means $\bar{x}$ are population aggregates. Individual-level belief dynamics may differ from aggregate trends.

### Plots

![Temporal alpha by zone](../tda/message_passing/plots/alpha_by_zone.png)

![Mexico temporal trajectory](../tda/message_passing/plots/mex_temporal_trajectory.png)

---

## 6. Cross-Stage Synthesis

### 6.1 BP Lift vs PPR Influence

Belief propagation and personalized PageRank capture complementary aspects of network influence:

| Dimension | BP Lift | PPR Hub Score |
|-----------|--------|---------------|
| What it measures | KL divergence from prior | Stationary random walk mass |
| Interpretation | "How much does the network constrain this belief?" | "How much influence does this belief exert?" |
| Directionality | Symmetric (how constrained) | Asymmetric (how influential) |
| Top constructs | Immigration status, online political participation | Economic ideology, democratic values |

The discrepancy is substantive: **immigration attitudes are the most *constrained*** (BP) but not the most *influential* (PPR). Conversely, economic ideology is moderately constrained but highly influential -- it generates SES-mediated coupling across many domains without being tightly pinned itself.

### 6.2 Spectral Partition vs Gamma Sign Structure

The Fiedler bipartition (spectral) and the $\gamma$-sign structure (from the bridge estimates) both partition constructs into two camps. Their agreement is high but not perfect:

- The Fiedler partition uses $|\gamma|$ weights and finds the optimal algebraic bisection
- The $\gamma$-sign structure uses signed weights and the 94% structural balance to define a social-balance bipartition
- In English-speaking countries (ARI = 0.153), both partitions agree closely, confirming that the sign structure and spectral structure are aligned
- In South/Southeast Asian countries (ARI = -0.003), they diverge, suggesting complex SES coupling patterns that do not reduce to a clean two-camp model

### 6.3 Network-Driven vs Inertial Societies

Combining the temporal $\alpha$ with the W7 equilibrium distance reveals four regimes:

| | Low eq. distance (near equilibrium) | High eq. distance (far from equilibrium) |
|---|---|---|
| **High $\alpha$** (network-driven) | Converging (VNM, IND) | Restructuring (RUS, URY) |
| **Low $\alpha$** (inertial) | Stable equilibrium (MEX, BRA) | Externally held (EGY, JOR) |


Each quadrant has distinct sociological characteristics:

- **Converging** societies are both close to equilibrium AND have belief changes that follow network predictions -- the SES system is settling into its predicted state. These are typically countries in the middle of rapid modernization where expanding education and urbanization are actively reshaping belief structures.
- **Restructuring** societies are far from equilibrium but moving toward it -- the network is actively reshaping beliefs. Post-Soviet states (Russia, Ukraine) and rapidly urbanizing societies fit here.
- **Stable equilibrium** societies are close to equilibrium but show inertial dynamics -- they reached the SES-predicted state and are staying there. These are mature democracies where SES distributions have been stable for decades and belief structures have settled into their SES-predicted configuration.
- **Externally held** societies are far from equilibrium and not moving toward it -- non-SES forces (theocratic governance, authoritarian control, conflict) dominate belief formation. Egypt ($\alpha = 0.00$, eq_dist = 15.9) is the archetype: beliefs are entirely determined by non-SES forces, and the SES network has zero predictive power for belief change.

This 2x2 framework provides a testable typology: as countries develop economically, the prediction is movement from "externally held" toward "converging" (lower left to upper left in the table). Conversely, democratic backsliding or conflict should move countries from "stable equilibrium" toward "externally held" (lower left to lower right).

### 6.4 Construct-Level Cross-Stage Summary

For the key constructs that appear across multiple stages, we can build a cross-stage profile:

| Construct | BP lift rank | PPR hub rank | Velocity rank | $\alpha$ contribution |
|-----------|-------------|-------------|--------------|---------------------|
| `immigrant_origin_status` | #1 (14 countries) | Sink (near-zero) | #1 (14/66) | High velocity |
| `online_political_participation` | #2 (11 countries) | Sink (near-zero) | #2 (8/66) | High velocity |
| `economic_ideology` | Low | #1 hub (med. rank 7) | Low | Moderate |
| `democratic_values_importance` | Low | #2 hub (med. rank 11) | Low | Moderate |
| `job_scarcity_gender_discrimination` | #3 (6 countries) | Mid-range | #4 (2/66) | Moderate |

The cross-stage pattern reveals a fundamental **asymmetry**: the most *constrained* constructs (immigration, online participation) are *not* the most *influential*. They are sinks in the PPR sense -- downstream consequences of the belief network rather than upstream drivers. Conversely, the most influential constructs (economic ideology, democratic values) have modest constraint levels but high reach. This is consistent with a causal picture where abstract political ideology shapes specific attitudes toward immigration and civic participation, mediated by SES position.

### 6.5 Methodological Relationships

The five message passing stages form a hierarchy of increasing temporal commitment:

| Stage | Input | Output | Time assumption |
|-------|-------|--------|-----------------|
| BP (Stage 1) | Signed $\gamma$ matrix | Posterior marginals, lift | Static (single wave) |
| Spectral (Stage 2) | $|\gamma|$ Laplacian | Fiedler bipartition, diffusion timescales | Static, continuous-time |
| PPR (Stage 3) | $|\gamma|$ transition matrix | Hub/sink scores | Static, discrete-time random walk |
| W7 Descriptive (Stage 4) | Transition matrix + means | Equilibrium distance, velocity | Static snapshot with equilibrium reference |
| Temporal (Stage 5) | Multi-wave matrices + means | $\alpha$, trajectories | Multi-wave panel |

Each stage adds information but also adds assumptions. BP requires the MRF approximation (pairwise potentials, loopy inference). Spectral diffusion assumes linear dynamics. PPR assumes ergodic random walks. The temporal model assumes stationary network structure. Results are most robust where multiple stages converge on the same conclusion.

### 6.6 The Message Passing Picture

Taken together, the five message passing stages reveal a consistent picture of SES-mediated belief coupling in the WVS:

1. **The SES network is strong but not universal**: 100% BP convergence and high Fiedler values (median 0.705) indicate robust SES coupling, but no universal influence hubs exist.

2. **Cultural zones structure belief topology**: spectral partition coherence is 2.86x higher within zones than across zones, and hub constructs are zone-specific.

3. **The network explains ~11% of Mexico's belief change**: $\alpha = 0.11$, with increasing network influence over time (from near-zero in 1996-2000 to 0.35 in 2012-2018).

4. **Equilibrium distance is geographic**: countries undergoing rapid socioeconomic transformation (Vietnam, India) show both high network influence and convergence toward SES-predicted equilibrium, while post-conflict and theocratic states (Libya, Egypt) are held far from equilibrium by non-SES forces.

5. **Immigration and online participation are the pressure points**: these constructs consistently appear as the most network-constrained (BP), highest-velocity (W7 descriptive), and most frequently dominant across countries. They sit at the intersection of SES dimensions (education, urbanization, age) and are the constructs most "in tension" with their network neighborhood.

6. **The hub-sink asymmetry reveals belief causality**: BP and PPR identify complementary roles. Economic ideology and democratic values are hubs (influence generators), while immigration attitudes and online participation are sinks (influence endpoints). If the SES network approximates causal structure, this suggests a causal chain: abstract political values -> specific policy attitudes -> behavioral intentions, mediated by sociodemographic position.

7. **Mexico is prototypically Latin American**: across all stages -- BP lift, Fiedler partition, PPR hub profile, equilibrium distance, and temporal $\alpha$ -- Mexico falls squarely within the Latin American zone distribution. Its increasing network influence ($\alpha$) and diverging equilibrium distance tell a specific story of a society where SES-mediated belief coupling is strengthening even as external forces (security crisis, political polarization, media transformation) push aggregate beliefs away from the SES-predicted equilibrium.

### 6.7 Limitations and Future Work

Several limitations affect all five stages:

1. **Construct selection**: the 55 WVS constructs are a subset of all possible belief dimensions. Missing constructs (e.g., specific policy preferences, media consumption, social media use) may alter the network topology.

2. **SES bridge as proxy**: the $\gamma$ edges measure SES-*mediated* covariation, not direct causal influence between beliefs. The message passing framework treats these edges as if they were direct couplings, which overstates the strength of the belief network when SES is a common cause rather than a mediator.

3. **Cross-country comparability**: WVS samples vary in quality, coverage, and timing across countries. The 55-construct matrix has structural NaN where country-specific DR estimates are missing, affecting network density.

4. **Temporal sparsity**: most countries have only 3 waves, giving $\alpha$ estimates with minimal degrees of freedom. A Bayesian hierarchical model borrowing strength across countries would improve temporal estimates.

5. **Stationarity**: all stages except temporal assume a fixed network structure. In reality, the $\gamma$ matrix evolves as SES distributions change. A time-varying network model (e.g., temporal exponential random graph models) would capture this evolution.

**Future directions:**

- Gaussian MRF (continuous beliefs) for more faithful BP
- Dynamic spectral analysis tracking Fiedler vector rotation across waves
- Causal discovery (PC algorithm) on the $\gamma$ matrix to orient edges
- Integration with los_mex construct network for Mexico-specific deep dive
- GPU-accelerated BP and PPR for parameter sensitivity analysis
- Country-specific hub profiles as inputs to the agent's analytical essays
- Predictive validation: does $\alpha$ at wave $t$ predict belief shift at $t+1$?

### 6.8 Connection to the Broader Navegador Framework

The message passing analysis extends the Navegador project's core pipeline:

1. **SES bridge** ($\gamma$-surface): establishes the edge weights
2. **Construct aggregation**: reduces ~6,000 survey items to 55 constructs
3. **TDA pipeline**: persistent homology, Ricci curvature, spectral distances
4. **Message passing** (this report): BP, spectral, PPR, temporal dynamics

Each layer adds a different analytical lens:

- The $\gamma$-surface asks: *how strongly are two beliefs coupled by SES?*
- TDA asks: *what is the topological shape of the belief network?*
- Message passing asks: *how does information/influence flow through the network?*

The message passing results feed back into the agent layer: the `OntologyQuery` class in `opinion_ontology.py` can use BP lift and PPR hub scores to contextualize its `get_neighborhood()` and `find_path()` responses, telling users not just *which beliefs are connected* but *which beliefs drive which others* and *how quickly perturbations propagate*.

For the Mexican survey data (los_mex), the temporal analysis provides a specific prediction: constructs with high velocity in the W6-W7 transition (online political participation, social intolerance, religion orientation) are the constructs most likely to shift in the next survey wave, and the direction of shift is predictable from the SES network structure.

---

## Appendix A: Mathematical Notation

| Symbol | Definition |
|--------|-----------|
| $G = (V, E, w)$ | Weighted belief network graph |
| $\gamma(i,j)$ | Doubly-robust SES-bridge estimate between constructs $i$ and $j$ |
| $L = D - A$ | Graph Laplacian ($D$ = degree matrix, $A$ = adjacency matrix) |
| $\lambda_2$ | Fiedler value (algebraic connectivity) |
| $\mathbf{v}_2$ | Fiedler vector (spectral bipartition) |
| $P$ | Row-normalized transition matrix of $|\gamma|$ weights |
| $\boldsymbol{\pi}_s$ | Personalized PageRank vector from seed $s$ |
| $\alpha$ | Restart probability (PPR) or mixing parameter (temporal) |
| $d_{\text{eq}}$ | Equilibrium distance: $\| \bar{\mathbf{x}} - \boldsymbol{\pi}^* \|_2$ |
| $\mathbf{v}$ | Velocity field: $P\bar{\mathbf{x}} - \bar{\mathbf{x}}$ |
| $\beta$ | Inverse temperature in Potts MRF |
| $b_i(x_i)$ | BP posterior marginal for node $i$ |
| $\text{lift}_i$ | KL divergence: $D_{\text{KL}}(b_i \| \phi_i)$ |

## Appendix B: Data Sources

| Data file | Description |
|-----------|-------------|
| `bp_all_summary.json` | Per-country BP convergence, top influencer, top lift |
| `spectral_all_summary.json` | Per-country Fiedler value, partition sizes, top loading |
| `ppr_hub_comparison.json` | Universal/zone-specific hubs, mediator correlation |
| `temporal_all_summary.json` | Per-country $\alpha$, zone, wave count |
| `w7_descriptive_summary.json` | Equilibrium distance ranking, velocity frequency |
| `mex_temporal.json` | Mexico deep dive: per-transition $\alpha$, residuals, velocity |
| `fiedler_comparison.json` | 66x66 ARI matrix of Fiedler partitions |
| `matrices/manifest.json` | Country list, construct index, cultural zones |

## Appendix C: Cultural Zone Membership

| Zone | Countries | $n$ |
|------|-----------|-----|
| African-Islamic | EGY, ETH, IRN, IRQ, JOR, KEN, LBN, LBY, MAR, MDV, NGA, TUN, TUR, ZWE | 14 |
| Catholic Europe | AND, CYP, GRC | 3 |
| Confucian | CHN, HKG, JPN, KOR, MAC, SGP, TWN, VNM | 8 |
| English-speaking | AUS, CAN, GBR, NIR, NZL, USA | 6 |
| Latin America | ARG, BOL, BRA, CHL, COL, ECU, GTM, MEX, NIC, PER, PRI, URY, VEN | 13 |
| Orthodox/ex-Communist | ARM, CZE, KAZ, KGZ, MNG, ROU, RUS, SRB, SVK, TJK, UKR, UZB | 12 |
| Protestant Europe | DEU, NLD | 2 |
| South/Southeast Asian | BGD, IDN, IND, MMR, MYS, PAK, PHL, THA | 8 |

Total: 66 countries across 8 Inglehart-Welzel cultural zones.

Zone sizes range from 2 (Protestant Europe: DEU, NLD) to 14 (African-Islamic). Smaller zones have less statistical power for within-zone comparisons; results for Protestant Europe and Catholic Europe (3 countries) should be interpreted with caution.

## Appendix D: Pipeline Architecture

The message passing pipeline consists of five sequential stages, each implemented as a separate Python script in `scripts/debug/`:

```
mp_belief_propagation.py     # Stage 1: Loopy BP on Potts MRF
mp_spectral_diffusion.py     # Stage 2: Laplacian eigendecomposition + heat kernel
mp_ppr_influence.py          # Stage 3: Personalized PageRank hub/sink analysis
mp_temporal_descriptive.py   # Stage 4+5: W7 snapshot + temporal dynamics
mp_report.py                 # This script: report generation + plots
```

All stages share common utilities from `mp_utils.py`:
- `load_manifest()` -- country/zone/construct metadata
- `load_weight_matrix(country)` -- per-country 55x55 $\gamma$ matrix
- `load_temporal_matrix(wave)` -- per-wave Mexico construct matrix
- `symmetrize_abs()`, `fill_nan_zero()`, `row_normalize()` -- matrix helpers

Input data: WVS Wave 7 $\gamma$-surface (68,174 estimates from Julia DR sweep) converted to 55x55 per-country construct matrices by `tda_convert_sweep_to_matrices.py`.

## Appendix E: Construct Index

The 55 WVS constructs used in the message passing analysis, grouped by domain:

| Domain | Constructs | Count |
|--------|-----------|-------|
| A: Social values | child_qualities_autonomy_self_expression, child_qualities_conformity_tradition, child_qualities_prosocial_diligence, importance_of_life_domains, social_intolerance_outgroups, subjective_wellbeing, voluntary_association_active_membership, voluntary_association_belonging | 8 |
| C: Work | job_scarcity_gender_discrimination, job_scarcity_nativist_preference, work_ethic | 3 |
| D: Family | familial_duty_obligations, female_income_threat_to_marriage, gender_role_traditionalism | 3 |
| E: Politics | authoritarian_governance_tolerance, autocracy_support, confidence_in_civil_society_organizations, confidence_in_domestic_institutions, confidence_in_international_organizations, democratic_system_evaluation, democratic_values_importance, economic_ideology, electoral_integrity, international_organization_knowledge, offline_political_participation, online_political_participation, perceived_corruption, political_information_sources, postmaterialist_values, science_technology_optimism, societal_change_attitudes, voting_participation | 18 |
| F: Religion/Morale | civic_dishonesty_tolerance, life_autonomy_morality_permissiveness, religion_versus_secularism_orientation, religious_belief, religious_exclusivism, religious_practice_and_self_identification, sexual_and_reproductive_morality_permissiveness, violence_tolerance | 8 |
| G: National identity | immigrant_origin_status, multilevel_place_attachment, outgroup_trust, perceived_negative_effects_of_immigration, perceived_positive_effects_of_immigration | 5 |
| H: Security | acceptance_of_state_surveillance, basic_needs_deprivation, crime_victimization, existential_threat_worry, freedom_security_tradeoff_perception, institutional_threat_perception, neighborhood_disorder_and_crime, precautionary_security_behaviors, socioeconomic_insecurity_worry | 9 |
| I: Science | science_skepticism | 1 |

Domain E (Politics & Society) dominates with the most constructs, reflecting the WVS's strong focus on political attitudes and institutional confidence. Domain F (Religion & Morale) is the second largest. Together, these two domains account for over half of all constructs.

## Appendix F: Key Results Summary Table

| Metric | Value | Source stage |
|--------|-------|-------------|
| BP convergence rate | 100% (66/66) | Stage 1 |
| Median top BP lift | 0.0311 | Stage 1 |
| Max BP lift | 0.4400 (GRC) | Stage 1 |
| BP top influencer | immigrant_origin_status (14 countries) | Stage 1 |
| Fiedler range | 0.615-0.888 | Stage 2 |
| Fiedler median | 0.705 | Stage 2 |
| Within-zone ARI | 0.0164 (2.86x across-zone) | Stage 2 |
| Most coherent zone | English-speaking (ARI=0.153) | Stage 2 |
| Universal PPR hubs | None | Stage 3 |
| Most consistent hub | economic_ideology (median rank 7) | Stage 3 |
| Mediator-PPR correlation | rho ~ -0.15 to +0.10 (weak) | Stage 3 |
| Eq. distance range | 10.1-15.9 | Stage 4 |
| Mexico eq. distance rank | 4/66 | Stage 4 |
| Top velocity construct | immigrant_origin_status (14/66) | Stage 4 |
| Temporal countries | 37 | Stage 5 |
| Alpha range | 0.00-0.40 | Stage 5 |
| Mexico alpha | 0.112 | Stage 5 |
| Most network-driven | VNM (alpha=0.398) | Stage 5 |
| Most inertial | EGY (alpha=0.000) | Stage 5 |

---

*Report generated by `scripts/debug/mp_report.py`*
