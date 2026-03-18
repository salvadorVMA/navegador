# SES Bridge Network — Topology & Geometry Report

*Generated from `kg_ontology_v2.json` (Julia v4 sweep, 2026-03-14)*

## What This Report Analyses

The SES bridge network is a graph where **nodes** are attitudinal constructs
(aggregated survey scales, e.g. *personal_religiosity*, *structural_housing_quality*)
and **edges** are statistically significant doubly-robust (DR) bridge estimates
between cross-domain construct pairs. An edge exists when the 95% bootstrap CI
for Goodman-Kruskal γ excludes zero — meaning the two attitudes are monotonically
co-driven by shared sociodemographic position (the 4 SES dimensions: education,
town size, gender, age).

Each edge carries a **signed weight** γ ∈ [-1, 1]:
- γ > 0: higher SES pushes both attitudes in the same direction (co-elevation)
- γ < 0: higher SES pushes them in opposite directions (counter-variation)

Each node carries a **4D SES fingerprint** `[ρ_escol, ρ_Tam_loc, ρ_sexo, ρ_edad]` —
the Spearman correlation of the construct with each SES dimension. This fingerprint
determines the node's position in a continuous sociodemographic space, and — as we
will show — almost entirely determines the network's topology.

## 1. Global Structure

| Metric | Value |
|--------|-------|
| Nodes | 93 |
| Edges | 984 |
| Density | 0.2300 (23.0%) |
| Connected components | 23 |
| Giant component | 71 nodes, 984 edges |
| Isolated nodes | 22 |
| Diameter | 4 |
| Radius | 3 |
| Avg. shortest path length | 1.728 |
| Avg. clustering coefficient | 0.5307 |
| Transitivity (global clustering) | 0.7199 |
| Degree assortativity | 0.1161 |
| Domain assortativity | -0.0632 |
| Small-world σ | 0.991 |

### 1.1 Density

**Definition.** For an undirected graph with *n* nodes and *m* edges,
density = 2m / n(n−1) — the fraction of all possible edges that actually exist.

Here: 2 × 984 / (93 × 92) = **23.0%**.

Most real-world networks (social, biological, technological) have densities below 5%.
A density of 23% means SES creates **pervasive** connectivity: a typical
connected construct bridges to roughly one-quarter of all other constructs. This is not
a sparse web of isolated links — it is a thick fabric of SES-mediated co-variation.

### 1.2 Connected Components

**Definition.** A connected component is a maximal subgraph in which every pair of
nodes is reachable via some path. Isolated nodes (degree 0) each form their own
trivial component.

The network has **23 components**: one giant component of 71 nodes
containing **all** 984 edges, plus 22 isolated singletons.

The 22 isolated constructs are those whose SES magnitude (RMS of fingerprint entries)
is too small to produce any bootstrap CI that excludes zero. They are not disconnected
from SES — they are simply below the statistical detection threshold. In fingerprint
space, they cluster near the origin.

### 1.3 Diameter & Average Path Length

**Definition.** The *diameter* is the longest shortest path between any two nodes in
the giant component — the worst-case number of hops to get from one construct to another.
The *average shortest path length* (APL) is the mean over all node pairs.

Diameter = **4**, APL = **1.728**, radius = **3**.

An APL of 1.73 means that, on average, any two connected constructs are
fewer than 2 hops apart. Combined with diameter 4, this means the network is
**ultra-compact**: no two attitudes in the giant component are more than 4 SES-mediated
steps from each other. For reference, the internet has diameter ~20, social networks ~6,
protein interaction networks ~10. A diameter of 4 in a graph of 71 nodes is characteristic
of a dense, nearly-complete subgraph, not a sparse hierarchical structure.

### 1.4 Clustering Coefficient

**Definition.** The *local clustering coefficient* C(v) of a node v measures how many
of v's neighbors are also neighbors of each other:

    C(v) = 2 × |edges among neighbors of v| / (deg(v) × (deg(v) − 1))

The *average clustering coefficient* is the mean C(v) over all nodes. *Transitivity*
(global clustering) is the ratio 3 × triangles / connected-triples across the whole graph,
which gives more weight to high-degree nodes.

Average clustering = **0.531**, transitivity = **0.720**.

For a random Erdős-Rényi graph with the same density, the expected clustering equals
the density itself: C_random = 0.230. Our observed value (0.531) is
**2.3× higher** than random expectation.

This excess clustering means neighbors tend to share neighbors — the network has
clique-like local structure. This is a natural signature of a geometric graph:
if A and B are both close to C in fingerprint space, then A and B are likely close
to each other, forming a triangle. Random graphs lack this geometric transitivity.

### 1.5 Small-World Test

**Definition.** The small-world coefficient σ = (C/C_rand) / (L/L_rand), where C and L
are the observed clustering and path length, and C_rand, L_rand are the values expected
for a random graph with the same size and density. A network is small-world when σ > 1:
high clustering (like a lattice) combined with short paths (like a random graph).

σ = **0.991**.

σ ≤ 1: the network is **not** small-world. The path lengths are not shorter
than random expectation — the high clustering comes at the cost of slightly
longer paths than a pure random graph. This is consistent with a geometric
graph: geometric proximity creates local clustering, but the same geometry
also creates longer paths between distant regions of fingerprint space.

### 1.6 Assortativity

**Definition.** *Degree assortativity* (Newman, 2002) is the Pearson correlation of
degrees at either end of an edge. Positive = hubs connect to hubs (assortative).
Negative = hubs connect to low-degree nodes (disassortative, hub-and-spoke).

*Attribute assortativity* (here: domain) measures whether edges preferentially connect
nodes with the same categorical attribute. It equals 1 if all edges are within-group,
0 if mixing is random, and negative if cross-group edges are overrepresented.

Degree assortativity = **0.116**. Weakly positive — hubs tend to
connect to other hubs. In a geometric graph, this is expected: constructs with large SES
magnitudes (far from the origin) produce many significant bridges, and they preferentially
bridge to other high-magnitude constructs (whose large fingerprints make for large dot products).

Domain assortativity = **-0.063**. Weakly negative — the SES bridge
connects *across* survey domains slightly more than within. This is partly by construction
(the sweep only estimates cross-domain pairs), but even among the 22 domains represented
in the giant component, no domain captures its edges internally. SES is a *between-domain*
connector: it links housing quality to religiosity, science attitudes to political engagement.

## 2. Degree Distribution

**Definition.** The degree k(v) of node v is the number of edges incident on v.
The degree distribution P(k) describes the probability that a randomly chosen node
has degree k. Its shape distinguishes network types:
- *Scale-free* (Barabási-Albert): P(k) ~ k^(-α), heavy tail, few mega-hubs
- *Random* (Erdős-Rényi): Poisson-like, peaked around the mean
- *Geometric* (thresholded proximity): bimodal or uniform in the connected core

| Stat | All nodes | Connected core |
|------|-----------|----------------|
| Count | 93 | 71 |
| Mean | 21.2 | 27.7 |
| Median | 21 | 35 |
| Std. dev. | 17.8 | 15.2 |
| Min | 0 | 1 |
| Max | 51 | 51 |
| CV | 0.84 | 0.55 |

![Degree Distribution](network_topology_degree.png)

**Figure: Degree Distribution.** Left: histogram showing the bimodal structure —
a spike at degree 0 (22 isolated nodes) and a broad distribution
in the connected core (degrees 1–51). Right: complementary cumulative
distribution (CCDF) on log-log axes. A power law (scale-free) would appear as a
straight line; the observed **concave** shape rules out scale-free structure.

The connected core has CV = 0.55. For comparison, scale-free networks typically
have CV > 2 (one or two nodes dominate), while random graphs have CV ≈ 1/√⟨k⟩ ≈ 0.19.
The observed value sits between these extremes — there are hubs (HAB|structural_housing_quality
at degree 51) but the distribution is far more uniform than a scale-free network.
This is the hallmark of a **thresholded geometric graph**: connectivity is determined by
proximity in a continuous space, not by preferential attachment. Nodes with larger SES
magnitudes (farther from the origin) exceed the significance threshold with more partners,
creating moderate hubs — but no node can dominate the way it would under rich-get-richer dynamics.

## 3. Centrality Analysis

Centrality measures quantify different notions of node "importance" in a graph.
We compute four complementary measures:

- **Degree centrality** C_D(v) = deg(v) / (n−1). Simply the fraction of other nodes that v
  connects to. High-degree nodes are broadly SES-entangled with many other constructs.

- **Betweenness centrality** C_B(v) = Σ_{s≠v≠t} σ_st(v) / σ_st, where σ_st is the number
  of shortest paths from s to t, and σ_st(v) is the number passing through v. Measures
  how much information flow (or SES-mediated influence chains) passes through v. A node
  with high betweenness but moderate degree acts as a *bottleneck* or *bridge* between
  otherwise separate regions of the network.

- **Eigenvector centrality** C_E(v) = (1/λ) Σ_u∈N(v) C_E(u). A node is important if it
  connects to other important nodes (recursive definition, solved as the leading eigenvector
  of the adjacency matrix). Captures prestige — being connected to the well-connected.

- **PageRank** PR(v). Google's variant of eigenvector centrality, with damping factor
  and weighted by |γ| (edge weight = abs_gamma). Accounts for both connectivity structure
  and bridge strength.

### Top 10 by Degree

| Rank | Construct | Domain | Degree | Betweenness | Eigenvector | PageRank |
|------|-----------|--------|--------|-------------|-------------|----------|
| 1 | structural_housing_quality | HAB | 51 | 0.0770 | 0.1660 | 0.0512 |
| 2 | basic_services_access | HAB | 49 | 0.0253 | 0.1722 | 0.0318 |
| 3 | political_interest_and_engagement | FED | 49 | 0.0268 | 0.1721 | 0.0261 |
| 4 | digital_and_cultural_capital | EDU | 48 | 0.0148 | 0.1767 | 0.0496 |
| 5 | perceived_opportunity_structure | MIG | 47 | 0.0187 | 0.1736 | 0.0273 |
| 6 | personal_religiosity | REL | 45 | 0.0168 | 0.1631 | 0.0243 |
| 7 | household_asset_endowment | HAB | 45 | 0.0145 | 0.1663 | 0.0412 |
| 8 | social_rights_service_quality | DER | 44 | 0.0271 | 0.1522 | 0.0146 |
| 9 | reading_engagement_and_literacy | DEP | 44 | 0.0095 | 0.1689 | 0.0329 |
| 10 | cultural_socialization_in_childhood | DEP | 43 | 0.0262 | 0.1614 | 0.0345 |

### Top 10 by Betweenness Centrality

| Rank | Construct | Domain | Betweenness | Degree |
|------|-----------|--------|-------------|--------|
| 1 | structural_housing_quality | HAB | 0.0770 | 51 |
| 2 | traditional_gender_role_attitudes | GEN | 0.0524 | 37 |
| 3 | ageism_and_negative_stereotypes | ENV | 0.0444 | 16 |
| 4 | job_search_and_employment_precarity | ECO | 0.0425 | 23 |
| 5 | economic_wellbeing_perception | ECO | 0.0356 | 37 |
| 6 | media_trust_and_quality_evaluation | SOC | 0.0282 | 28 |
| 7 | social_rights_service_quality | DER | 0.0271 | 44 |
| 8 | political_interest_and_engagement | FED | 0.0268 | 49 |
| 9 | cultural_socialization_in_childhood | DEP | 0.0262 | 43 |
| 10 | basic_services_access | HAB | 0.0253 | 49 |

![Centrality Comparison](network_topology_centrality.png)

**Figure: Centrality Comparison.** Pairwise scatter plots of degree, betweenness,
and eigenvector centrality. Points are colored by domain. If all measures agreed
perfectly, points would fall on the diagonal; divergence reveals structural roles.

### Interpretation

**Degree and eigenvector centrality are strongly correlated.** This is expected in a
dense, low-modularity network: being connected to many nodes is almost equivalent to
being connected to important nodes, because most of the network is reachable in 1-2 hops.
The eigenvector values are remarkably uniform among top nodes (0.152–0.177), confirming
that no single node dominates the spectral structure.

**Betweenness reveals structural bottlenecks.** The most interesting divergences between
degree and betweenness centrality:

- **ageism_and_negative_stereotypes** (ENV): degree 16, betweenness 0.0444. Ranked #3 in betweenness but only #53 in degree — a **structural bottleneck** connecting otherwise distant network regions. Its position in fingerprint space is unique enough that shortest paths are funneled through it.
- **job_search_and_employment_precarity** (ECO): degree 23, betweenness 0.0425. Ranked #4 in betweenness but only #46 in degree — a **structural bottleneck** connecting otherwise distant network regions. Its position in fingerprint space is unique enough that shortest paths are funneled through it.
- **tolerance_of_gender_based_violence** (GEN): degree 10, betweenness 0.0095. Ranked #23 in betweenness but only #59 in degree — a **structural bottleneck** connecting otherwise distant network regions. Its position in fingerprint space is unique enough that shortest paths are funneled through it.

**PageRank (γ-weighted)** highlights nodes with *strong* connections, not just *many*.
HAB constructs dominate PageRank because housing quality/services/assets have the largest
|γ| values — their SES entanglement is not only broad but deep.

## 4. Edge Signs & Structural Balance

### 4.1 Sign Distribution

Each edge carries a sign: γ > 0 (positive, co-elevation) or γ < 0 (negative, counter-variation).

| Metric | Value |
|--------|-------|
| Positive edges (γ > 0) | 515 (52.3%) |
| Negative edges (γ < 0) | 469 (47.7%) |

The split is remarkably close to 50/50 (52% positive / 48% negative).
This means SES does not have a uniform direction across all attitude domains — it elevates
some attitudes while suppressing others in roughly equal measure. Mexican sociodemographic
position creates a **bidirectional** structuring of opinion space.

![γ Distribution](network_topology_gamma.png)

**Figure: γ Distribution.** Left: histogram of edge γ values, split by sign. The distribution
is roughly symmetric around zero, with long tails reaching ±0.29. Right: cumulative distribution
of |γ|. The median |γ| is small, confirming that most SES-mediated co-variation is weak but
statistically detectable. The tail (|γ| > 0.1) represents the 5-10% of pairs with strong
SES entanglement.

### 4.2 Structural Balance

**Definition.** In a signed graph, a triangle (3-clique) is *balanced* if the product
of its three edge signs is positive, and *frustrated* if negative. By Cartwright-Harary
balance theory (1956), a perfectly balanced signed graph can be partitioned into exactly
two camps where all within-camp edges are positive and all cross-camp edges are negative.

The four possible triangles:
- (+, +, +) → product = +1 → **balanced** (all three agree)
- (+, −, −) → product = +1 → **balanced** (two enemies, one friend)
- (+, +, −) → product = −1 → **frustrated** (inconsistent)
- (−, −, −) → product = −1 → **frustrated** (all disagree — no coalition possible)

| Metric | Value |
|--------|-------|
| Total triangles | 8,283 |
| Balanced triangles | 7,790 (94.0%) |
| Frustrated triangles | 493 (6.0%) |

![Structural Balance](network_topology_balance.png)

**Figure: Structural Balance.** Left: pie chart showing the 94%/6% balance split.
Right: bar chart of positive/negative edge counts.

**94% balanced** is far above what random signs would produce. With a
52%/48% positive/negative split, random sign assignment predicts
50% balanced triangles. The observed 94% is a massive departure
from randomness (+44 percentage points).

This near-perfect balance means the sign structure is **almost globally consistent**:
the 71 connected constructs can be partitioned into two camps where within-camp γ is
predominantly positive and cross-camp γ is predominantly negative. This is the
mathematical signature of a bipolar SES geometry — sociodemographic position creates
two coherent blocs of attitudes that SES pushes in opposite directions.

The 6% of frustrated triangles represent triads where the SES geometry does not neatly
decompose into two camps — constructs influenced by different SES dimensions in
non-aligned ways. These are the genuinely complex nodes in the opinion landscape.

## 5. Domain Mixing

**Definition.** Domain mixing measures whether SES bridges preferentially connect
constructs within the same survey domain or across different domains. This is quantified
by the domain assortativity coefficient (Section 1.6) and by counting intra- vs inter-domain edges.

| Metric | Value |
|--------|-------|
| Intra-domain edges | 0 (0.0%) |
| Inter-domain edges | 984 (100.0%) |

> **Note:** Zero intra-domain edges is **by construction** — the DR bridge sweep only
> estimates cross-domain pairs. Intra-domain SES co-variation certainly exists but was
> not estimated. This means domain assortativity is mechanically depressed.

![Domain Heatmap](network_topology_domain_heatmap.png)

**Figure: Domain Heatmap.** Left: edge count between each pair of domains (darker = more
edges). Right: mean γ between each domain pair (red = positive, blue = negative).
The edge-count heatmap reveals the most SES-entangled domain pairs; the sign heatmap
shows whether SES co-elevates or counter-varies the two domains.

### Top 10 Domain Pairs by Edge Count

| Domains | Edges | Mean γ | Sign | Interpretation |
|---------|-------|--------|------|----------------|
| CIE × REL | 25 | -0.0187 | − | Science curiosity and religiosity are SES-opposed |
| FED × REL | 20 | +0.0003 | + | Political engagement and religiosity are SES-independent on average |
| CIE × FED | 20 | -0.0082 | − | Science and politics slightly opposed via SES |
| HAB × REL | 19 | -0.0089 | − | Housing quality and religiosity slightly SES-opposed |
| CIE × HAB | 16 | +0.0678 | + | Science and housing quality co-elevated by education |
| CIE × GLO | 15 | -0.0565 | − | Science and globalization attitudes SES-opposed |
| GLO × REL | 14 | +0.0094 | + | Globalization skepticism and religiosity slightly co-elevated |
| JUS × REL | 14 | +0.0016 | + | Justice and religiosity show weak SES co-variation |
| FED × HAB | 14 | +0.0030 | + | Political engagement and housing slightly co-elevated |
| HAB × JUS | 14 | -0.0059 | − | Housing quality and justice attitudes slightly opposed |

The most SES-entangled domain pair is **CIE × REL** (25 edges, mean γ = −0.019).
Science and religion are the domains most pervasively linked through sociodemographic
position, with SES pushing them in opposite directions — higher education is associated
with greater science engagement *and* lower religiosity.

## 6. Community Structure

**Definition.** A community is a group of nodes more densely connected to each other than
to the rest of the network. *Modularity* Q measures the quality of a partition:

    Q = (1/2m) Σ_ij [A_ij − k_i k_j / 2m] δ(c_i, c_j)

where A is the adjacency matrix, k_i is the degree of node i, m is the total edge count,
and δ(c_i, c_j) = 1 if nodes i and j are in the same community. Q ranges from −0.5 to 1:
- Q ≈ 0: partition is no better than random
- Q > 0.3: clear community structure
- Q > 0.7: strong community structure

We compare three partitions:

| Method | How it works | Communities | Modularity |
|--------|-------------|------------|------------|
| Louvain | Greedy modularity optimization with local moves and multi-level coarsening | 3 | 0.0894 |
| Greedy | Agglomerative: repeatedly merge the pair of communities that most improves Q | 3 | 0.0874 |
| Domain | Use the 22 survey domains as predefined communities | 23 | -0.0822 |

![Community vs Domain](network_topology_communities.png)

**Figure: Community Composition.** Stacked bars showing how Louvain communities
are composed by domain. Each bar is one community; colors represent domains.
The mix of colors in each bar demonstrates that communities cut across domain boundaries.

### Interpretation

Louvain modularity Q = **0.089** — effectively zero. Both algorithmic methods converge
on 3 communities, but the partition is barely better than random (Q < 0.1). The network
has **no meaningful community structure**.

Domain-based partition achieves Q = **-0.082** — *negative*, meaning the domain
partition is *worse* than random. Domains are not communities; they are administrative
categories (survey themes) that SES cuts across orthogonally. SES does not respect
thematic boundaries — it structures attitudes by sociodemographic axis, not by topic.

This is a fundamental finding: **there are no clusters in the SES bridge network**.
Low modularity is the network signature of a continuous gradient. The 4D SES space
is low-dimensional, so there are not enough degrees of freedom for sharp boundaries.
Attitudes vary smoothly along sociodemographic axes, not in discrete blocs.

### Louvain Community Composition

- **C0** (25 nodes from 15 domains): JUS(3), FED(3), HAB(2), ...
- **C1** (11 nodes from 10 domains): SEG(2), SAL(1), GEN(1), ...
- **C2** (35 nodes from 19 domains): CIE(4), NIN(3), EDU(3), ...

## 7. Fingerprint Geometry (4D SES Space)

### 7.1 PCA: Dimensionality of the Fingerprint Space

**What it is.** Each construct carries a 4D fingerprint vector `[ρ_escol, ρ_Tam_loc, ρ_sexo, ρ_edad]`
— the Spearman correlation of the construct with each SES dimension. PCA (Principal Component
Analysis) rotates these 4 coordinates to find the axes of maximum variance. The eigenvalues
(variance explained) tell us how many independent dimensions the fingerprints actually use;
the eigenvectors (loadings) tell us what each synthetic axis means in terms of the original
SES dimensions.

**How it's computed.** Center the 93 fingerprint vectors (subtract mean), compute the 4×4
covariance matrix, decompose via SVD. The resulting principal components (PCs) are ordered by
decreasing variance explained.

| PC | Variance Explained | Cumulative | Interpretation |
|----|-------------------|------------|----------------|
| PC1 | 77.7% | 77.7% | The education-vs-tradition axis (dominant) |
| PC2 | 12.0% | 89.6% | The age-vs-urbanization axis (secondary) |
| PC3 | 6.8% | 96.4% | Residual gender/location variation |
| PC4 | 3.6% | 100.0% | Remaining noise (negligible) |

![Fingerprint PCA](network_topology_pca.png)

**Figure: Fingerprint PCA.** Each dot is a construct, positioned by its PC1 and PC2
coordinates (collectively capturing 90% of variance). Node size is proportional to
SES magnitude (RMS of the fingerprint). Colors indicate survey domain. The 50 strongest
bridges are drawn as lines (orange = positive γ, blue = negative γ). The spread
of the cloud reveals the effective geometry of the SES space.

### 7.2 PCA Loadings — What the Axes Mean

| Dimension | PC1 loading | PC2 loading |
|-----------|-------------|-------------|
| Education (escol) | -0.753 | +0.090 |
| Town size (Tam_loc) | +0.450 | -0.644 |
| Gender (sexo) | +0.202 | +0.176 |
| Age/cohort (edad) | +0.435 | +0.739 |

**PC1 (77.7% of variance): The education-vs-tradition axis**

PC1 loads heavily on **escol** (-0.753) in opposition to **Tam_loc** (+0.450)
and **edad** (+0.202). This axis separates constructs that are *elevated by education*
(negative PC1 scores: high ρ_escol) from those elevated by *rural residence and older age*
(positive PC1 scores: high ρ_Tam_loc, high ρ_edad).

The opposition is not accidental — it reflects the deep structure of Mexican sociodemographic
stratification. Education and urbanization are positively correlated in the population
(cities have more schooling), yet they load on opposite sides of PC1 in the fingerprint space.
This means they structure *attitudes* in opposite directions: education elevates some attitudes
(science engagement, digital capital, cultural consumption) while town size and age elevate
others (religiosity, traditional gender roles, community attachment).

The dominance of PC1 (78% of variance) means that **most of the variation in how SES**
**structures attitudes reduces to a single continuum**: from education-driven cosmopolitan
attitudes on one end to age/locality-driven traditional attitudes on the other. This is the
*primary cleavage* in the SES fingerprint space.

**PC2 (12.0% of variance): The age-vs-urbanization axis**

PC2 loads heavily on **edad** (+0.739) in opposition to **Tam_loc** (-0.644).
Education is nearly invisible on this axis (loading +0.090). PC2 captures the
*residual variation* after the dominant education axis is removed: the independent effects
of age versus urbanization.

Constructs with high PC2 scores are those structured by age *independently of education* —
attitudes that shift across cohorts regardless of schooling level (e.g., technology adoption,
generational values). Constructs with low PC2 scores are structured by urbanization
independently of education — urban/rural differences that persist across educational levels
(e.g., access to services, community structure, local governance experience).

Together, PC1 and PC2 reveal that the 4D SES space is effectively **2-dimensional**:
a dominant education-vs-tradition axis, and a secondary age-vs-urbanization axis.
Gender (sexo) contributes weakly to both components — it structures a smaller, more
specialized set of attitudes (reproductive rights, gender role expectations) rather than
broadly structuring the entire opinion landscape.

![SES Dimension Profiles](network_topology_ses_profiles.png)

**Figure: SES Dimension Profiles.** Violin plots of Spearman ρ for each SES dimension
across the 71 connected constructs. Education (escol) has the widest spread — the most
polarizing dimension, with some constructs strongly positively correlated and others
strongly negatively correlated. Town size (Tam_loc) is the second widest, skewed negative
(rural residence tends to elevate traditional/community attitudes). Gender (sexo) is the
most concentrated around zero — consistent with PC1/PC2 loadings showing gender's weak
overall contribution to the fingerprint geometry.

### 7.3 Dominant SES Dimension per Construct

For each construct, the *dominant dimension* is the SES variable with the highest |ρ|.

| Dimension | Count | % | What it means |
|-----------|-------|---|---------------|
| escol | 37 | 40% | Education is the primary stratifier for this construct |
| Tam_loc | 23 | 25% | Urban/rural context is the primary stratifier |
| edad | 22 | 24% | Age/cohort is the primary stratifier |
| sexo | 11 | 12% | Gender is the primary stratifier |

Education dominates (40%), but **60% of constructs are primarily structured by**
**non-education SES dimensions**. This challenges the common assumption that education
is the only SES dimension that matters for attitudes. Town size (25%) and age (24%)
are nearly as important in aggregate. Gender, while less frequent as the *dominant*
dimension, is the *exclusive* stratifier for some attitudes (gender role beliefs,
reproductive health access).

### 7.4 Fingerprint Dot Product vs. Bridge γ

**The key test.** If the network is truly a geometric graph — if topology is determined by
fingerprint positions — then the dot product of two constructs' fingerprints should predict
the bridge γ between them. The dot product fp_A · fp_B = Σ_d ρ_A,d × ρ_B,d captures whether
the two constructs are pushed in the same direction (+) or opposite directions (−) by each
SES dimension simultaneously.

Pearson r = **0.685** (p = 2.2e-137), computed over all 984 significant edges.

![Dot vs Gamma](network_topology_dot_gamma.png)

**Figure: Dot Product vs. γ.** Each point is a significant bridge edge. The strong
linear relationship confirms that the 4D fingerprint geometry *predicts* both the sign and
magnitude of the DR bridge estimate. The regression line passes near the origin, confirming
that zero dot product → zero γ (orthogonal SES profiles → no SES-mediated co-variation).

The r² = 0.470, meaning **47% of the variance in γ is explained by the
fingerprint dot product alone**. This is remarkable because the dot product is computed from
simple bivariate Spearman correlations (each construct vs. each SES dimension independently),
while γ is estimated by the full doubly-robust bridge (propensity weighting, joint distribution
modeling, 200 bootstrap iterations). The fact that a simple 4-number dot product recovers
47% of the complex estimator's output confirms that the bridge network is
fundamentally **low-dimensional** and **geometrically determined**.

The remaining 53% of variance likely comes from: (a) interaction effects between
SES dimensions not captured by the dot product (e.g., education × gender interactions),
(b) bootstrap noise in γ estimates, and (c) non-linear SES effects that the fingerprint
(linear Spearman ρ) cannot capture.

## 8. Summary: What Kind of Network Is This?

### Key Properties

- **Dense (23%)**: 23% of possible edges exist. SES creates broad, pervasive connectivity — not a sparse web of isolated links.
- **Compact (diameter 4, APL 1.73)**: Any two connected constructs are fewer than 2 hops apart on average. The SES bridge is an ultra-short-range connector.
- **High clustering (0.531 vs 0.230 random)**: Neighbors share neighbors at 2.3× the random rate — geometric transitivity.
- **Structurally balanced (94%)**: 94% of triangles are sign-consistent. The network admits a near-perfect two-camp partition.
- **Near-equal sign split (52%/48%)**: SES drives co-elevation and counter-variation in equal measure — a bidirectional structuring of opinion space.
- **No community structure (Q = 0.089)**: No discrete clusters. The network is a continuous gradient, not a modular graph.
- **Geometrically determined (r = 0.685)**: The 4D fingerprint dot product explains 47% of variance in γ. Topology is a projection of SES geometry.
- **Low effective dimensionality (PC1 = 78%)**: The 4D fingerprint space is effectively ~1.5D: one dominant education-vs-tradition axis plus a secondary age-vs-urbanization axis.

### Network Archetype

This is a **signed thresholded inner-product graph** in R⁴. It is not a social network,
not scale-free, not a classical small-world, and not a modular graph. Its structure derives
from four interlocking properties:

**1. Topology from geometry.** Each construct occupies a position in 4D SES space via its
fingerprint vector. Two constructs form a significant bridge when the magnitude of their
fingerprint interaction (dot product) exceeds the statistical noise floor. The dot product
predicts γ sign at 99.4% accuracy and γ magnitude at r = 0.685. The graph is not
an independent object — it is a *projection* of a continuous geometric space onto a discrete
edge set, with significance testing acting as the threshold function.

**2. Signed edges with structural balance.** Both positive and negative edges exist in
near-equal numbers (52%/48%). The 94% structural
balance means the sign pattern is almost perfectly consistent across triangles — the network
admits a clean bipartition into two *camps* of attitudes. One camp is elevated by the
education-cosmopolitan end of PC1; the other by the tradition-locality end. This bipartition
is the discrete shadow of the continuous PC1 axis.

**3. Dense + low modularity.** High density (23%) and near-zero modularity
(Q = 0.089) are natural consequences of low dimensionality. In R⁴ — effectively R^1.5
given the PCA spectrum — there are not enough degrees of freedom to create well-separated
clusters. Every construct's fingerprint has non-trivial projection onto the dominant PC1 axis,
producing inner products (and therefore bridges) with many other constructs.

**4. Bimodal connectivity.** The 22 isolated nodes are constructs with SES
magnitudes too small to clear the significance threshold against any partner. They sit near
the origin in fingerprint space. The 71 connected nodes form a single dense
component — the *core* of SES-structured opinion. There is no middle ground: a construct is
either strongly SES-structured (and connected to many others) or barely SES-structured (and isolated).

### Theoretical Analogy

The closest model is a **random geometric graph** (RGG) in R⁴: scatter n points in a
low-dimensional space; connect pairs whose geometric interaction exceeds a threshold.
RGGs produce exactly the properties we observe: high clustering (geometric transitivity),
short paths (low dimensionality), weak community structure (no natural boundaries in
continuous space), and bimodal degree distributions (interior nodes connect broadly,
boundary nodes sparsely). The key difference is that our "distance" is a *signed*
inner product, generating the balanced sign structure that a standard RGG would lack.

### Implication for Interpretation

The SES bridge network does not reveal hidden *clusters* of attitudes. It reveals a
**gradient**. Mexican attitudes vary continuously along a low-dimensional sociodemographic
axis — primarily education (which loads in opposition to age and town size on PC1) — and
the bridge graph is the statistical shadow of this continuous structure. The network is best
understood not as a map of discrete communities, but as a *contour map* of a smooth
sociodemographic landscape, where the edges are contour lines connecting attitudes at
similar SES elevations.

---

## 9. The Full Item-Level Network

### 9.1 The Three-Layer Architecture

The construct-level network (Sections 1–8) is a compressed view. The full network has
three layers:

```
L0 Items (6,359)  ──loading_γ──▶  L1 Constructs (93)  ──bridge_γ──▶  L1 Constructs  ──loading_γ──▶  L0 Items
     (raw survey questions)            (aggregated scales)                                    (raw survey questions)
```

Each connection in this chain carries a Goodman-Kruskal γ ∈ [-1, 1]:

- **Loading γ** (item → construct): measures how strongly an individual survey question
  co-varies monotonically with its parent construct. Computed as γ(raw_item, bin5(agg_construct)).
  Items that are reverse-coded have negative loading γ; items aligned with the construct
  direction have positive loading γ.

- **Bridge γ** (construct → construct): the DR bridge estimate from the Julia sweep.
  Measures SES-mediated monotonic co-variation between two constructs in different domains.

The **signal chain** from item A to item B through the bridge is:

    signal(A → B) = loading_γ_A × bridge_γ(construct_A, construct_B) × loading_γ_B

All three terms are on the same γ scale, so the product is dimensionally consistent.
Signs propagate correctly: a reverse-coded item (negative loading) connected through a
positive bridge to a positively-loaded item produces a negative prediction — meaning
higher values on item A predict lower values on item B, mediated by SES.

### 9.2 Item-Construct Coverage

**6,359 items** across 24 survey domains, connected to constructs via three mechanisms:

| Loading Type | Count | % | Method |
|-------------|-------|---|--------|
| **Exact** | 482 | 7.6% | γ(item, bin5(parent_construct)) — directly measured |
| **Approximate** | 5,307 | 83.5% | ρ(item, candidate_construct) × 1.14 — nearest construct by fingerprint cosine similarity |
| **None** | 570 | 9.0% | No construct exists in domain (JUE, CON) |

The 1.14 scaling factor converts Spearman ρ to approximate γ, based on the empirical
relationship: for 474 construct-member items with both measurements, Pearson r(ρ, γ) = 0.977
and median |γ|/|ρ| = 1.14. The inflation arises because GK γ excludes tied pairs from its
denominator, while ρ averages tied ranks — for 5-point Likert items with ~30-50% ties,
this produces ~14% systematic inflation.

#### Items by Domain

| Domain | Items | Exact | Approx | None | Items/Construct |
|--------|-------|-------|--------|------|-----------------|
| CIE | 244 | 31 | 213 | 0 | 49 |
| CON | 239 | 0 | 0 | 239 | — |
| COR | 225 | 20 | 205 | 0 | 56 |
| CUL | 277 | 31 | 246 | 0 | 55 |
| DEP | 168 | 21 | 147 | 0 | 42 |
| DER | 166 | 21 | 145 | 0 | 33 |
| ECO | 145 | 15 | 130 | 0 | 48 |
| EDU | 213 | 20 | 193 | 0 | 53 |
| ENV | 233 | 11 | 222 | 0 | 78 |
| FAM | 436 | 26 | 410 | 0 | 87 |
| FED | 192 | 28 | 164 | 0 | 38 |
| GEN | 276 | 14 | 262 | 0 | 92 |
| GLO | 263 | 15 | 248 | 0 | 88 |
| HAB | 289 | 28 | 261 | 0 | 72 |
| IDE | 368 | 18 | 350 | 0 | 92 |
| IND | 183 | 9 | 174 | 0 | 61 |
| JUE | 331 | 0 | 0 | 331 | — |
| JUS | 217 | 20 | 197 | 0 | 54 |
| MED | 181 | 17 | 164 | 0 | 45 |
| MIG | 225 | 16 | 209 | 0 | 75 |
| NIN | 315 | 18 | 297 | 0 | 79 |
| POB | 126 | 13 | 113 | 0 | 42 |
| REL | 244 | 35 | 209 | 0 | 49 |
| SAL | 140 | 12 | 128 | 0 | 47 |
| SEG | 329 | 30 | 299 | 0 | 66 |
| SOC | 334 | 13 | 321 | 0 | 167 |

### 9.3 Loading γ Distribution

**Definition.** Loading γ measures the monotonic association between an individual item
and its anchor construct. It answers: *if I know someone's position on the construct,
how well can I predict their response to this specific item?*

| Statistic | Exact (n=474) | Approximate (n=5,307) |
|-----------|--------------|---------------------|
| Mean | 0.022 | 0.059 |
| Median | 0.129 | 0.039 |
| Std. dev. | 0.676 | 0.127 |
| Mean |loading| | 0.612 | 0.094 |
| Median |loading| | 0.670 | 0.062 |
| % negative | 44.9% | 30.5% |

![Loading Distributions](network_item_loading_dist.png)

**Figure: Loading γ Distributions.** Left: exact loadings (measured γ for construct-member items).
Center: approximate loadings (ρ × 1.14 for orphan items matched to nearest construct).
Right: comparison of absolute loading magnitudes. Exact loadings are substantially larger
(median |γ| ≈ 0.67) because these items were selected *because* they belong to the construct.
Approximate loadings are weaker (median |γ| ≈ 0.06) because orphan items are matched
to the nearest construct by fingerprint similarity — a weaker relationship than construct membership.

**Consequence for the signal chain:** The loading step is where most signal is lost.
A bridge γ of 0.10 between two constructs propagates to item-item signal of only
|0.67| × 0.10 × |0.67| ≈ 0.0449
for exact items, and |0.06| × 0.10 × |0.06| ≈ 0.0004
for approximate items — a 100× attenuation in the approximate case.

### 9.4 Signal Attenuation Through the Full Chain

**Definition.** For each pair of bridged constructs, and for each pair of items
(one from each construct), the signal is |loading_A| × |bridge_γ| × |loading_B|.
This measures how much of the SES-mediated covariation between constructs survives
down to the level of individual survey questions.

Total item-to-item signal chains computed: **3,894,963**

| Statistic | Value |
|-----------|-------|
| Mean |signal| | 0.00127 |
| Median |signal| | 0.00016 |
| Max |signal| | 0.2301 |
| P90 |signal| | 0.00244 |
| P99 |signal| | 0.0199 |
| Chains with |signal| ≥ 0.001 | 769,205 (19.7%) |
| Chains with |signal| ≥ 0.01 | 94,838 (2.4%) |
| Chains with |signal| ≥ 0.05 | 8,778 (0.2%) |

![Signal Attenuation](network_item_signal_attenuation.png)

**Figure: Signal Attenuation.** Left: histogram of log₁₀(|signal|) — the full distribution
of item-to-item signal strengths. The vertical dashed line marks the 0.001 attenuation
threshold. Center: CDF on log scale showing what fraction of chains exceed each signal
level. Right: categorical breakdown of signal strength.

**Interpretation.** The signal chain is a **triple multiplicative bottleneck**:

1. **Loading attenuation (item → construct):** Most items load at |γ| ≈ 0.05–0.70 on their
   construct, depending on loading type. This first multiplication reduces the signal by ~50-95%.

2. **Bridge attenuation (construct → construct):** Bridge γ values are typically 0.005–0.15.
   This second multiplication reduces the signal by another 85-99%.

3. **Loading attenuation (construct → item):** Same as step 1 in the target domain.
   A third multiplicative reduction.

The cumulative effect: a bridge γ of 0.10 (a strong bridge) between two constructs
propagates to a median item-item signal of ~10⁻³ to 10⁻⁴. Only the strongest bridges
between the best-loaded items produce signals above 0.01.

**2.4% of item-item chains exceed |signal| ≥ 0.01** — these are the
genuinely detectable SES-mediated associations at the raw survey question level.
The remaining 98% are real in principle but too attenuated to
be practically useful for individual item-level prediction.

### 9.5 Domain-to-Domain Signal Flow

**Definition.** For each pair of domains, aggregate all item-to-item signals across all
bridged construct pairs. The mean |signal| reveals which domain pairs have the strongest
item-level SES entanglement, accounting for both bridge strength and item loading quality.

![Domain Signal Heatmap](network_item_signal_heatmap.png)

**Figure: Domain Signal Heatmap.** Left: item-pair count between domains (log₁₀ scale),
showing the combinatorial fan-out. Right: mean |signal| between domains. Hot cells
indicate domain pairs where SES-mediated covariation penetrates all the way down to
individual survey items.

#### Top 10 Domain Pairs by Mean |signal|

| Domains | Item Pairs | Mean |signal| | Max |signal| | Mean signed | Direction |
|---------|------------|----------------|--------------|-------------|-----------|
| EDU × HAB | 33,157 | 0.00959 | 0.2301 | -0.00114 | counter-vary |
| DEP × EDU | 21,131 | 0.00858 | 0.1586 | +0.00284 | co-elevate |
| DEP × HAB | 28,137 | 0.00671 | 0.1578 | -0.00123 | counter-vary |
| CIE × DEP | 27,572 | 0.00649 | 0.1698 | -0.00248 | counter-vary |
| ECO × SAL | 1,296 | 0.00625 | 0.1530 | -0.00033 | counter-vary |
| CIE × EDU | 42,892 | 0.00597 | 0.2127 | -0.00121 | counter-vary |
| EDU × REL | 32,020 | 0.00497 | 0.1028 | +0.00151 | co-elevate |
| CIE × HAB | 61,876 | 0.00443 | 0.2032 | +0.00047 | co-elevate |
| EDU × MED | 7,590 | 0.00405 | 0.0900 | -0.00079 | counter-vary |
| DEP × REL | 27,572 | 0.00393 | 0.0783 | +0.00200 | co-elevate |

The strongest domain-level item signal is **EDU × HAB** (mean |signal| = 0.00959,
max |signal| = 0.2301). Even the strongest domain pair has mean item-level signal
of order 10⁻⁴ to 10⁻³ — consistent with the triple multiplicative bottleneck.

### 9.6 Item Reach: How Many Items Can Each Item See?

**Definition.** The *reach* of an item is the number of items in other domains it can
connect to through the construct → bridge → construct chain (regardless of signal strength).
This is the item-level analogue of degree centrality.

| Statistic | All Items | Connected Items |
|-----------|-----------|-----------------|
| Count | 6,359 | 4,544 |
| Mean reach | 1228 | 1718 |
| Median reach | 1209 | 2091 |
| Max reach | 3,119 | 3,119 |
| Zero-reach items | 1,815 (28.5%) | — |

![Item Reach by Domain](network_item_reach_by_domain.png)

**Figure: Item Reach by Domain.** Box plots showing how many items each item can reach
through the bridge chain, by domain. Domains with high-degree constructs (HAB, CIE, REL)
produce items with the widest reach.

The median connected item reaches **2091** items in other domains.
But 1,815 items (28.5%) have zero reach — either they
belong to isolated constructs (no significant bridges) or to domains without constructs (JUE, CON).

### 9.7 The Bipartite Fan-Out

**Definition.** Each bridge connects two constructs, but each construct aggregates
multiple items. A single bridge therefore creates a *fan-out* of item-to-item connections
equal to |items_A| × |items_B|. This fan-out determines the combinatorial structure of
the item-level network.

Items per construct: mean = 62.2, median = 53, range [8, 264].

984 construct-level bridges expand to **3,894,963** item-level signal chains
(average fan-out: 3958 item-pairs per bridge).

![Bipartite Structure](network_item_bipartite.png)

**Figure: Bipartite Structure.** Left: items per construct (how many items feed into
each construct node). Right: bridge fan-out (how many items in other domains are reachable
from items in each construct, through its bridges).

### 9.8 Synthesis: The Item-Level Network as a Signal Decay Hierarchy

The expanded item-level network reveals a **three-stage signal decay** hierarchy:

| Level | Connections | Typical |γ| | Signal remaining |
|-------|------------|-----------|------------------|
| L1 ↔ L1 (bridge) | 984 | 0.01–0.29 | 100% (reference) |
| L0 → L1 (exact loading) | 482 | 0.67 | ×0.67 |
| L0 → L1 (approx loading) | 5307 | 0.06 | ×0.06 |
| L0 ↔ L0 (full chain, exact) | — | 0.0014 | ×0.449 of bridge |
| L0 ↔ L0 (full chain, approx) | — | ~10⁻⁴ | ×0.0039 of bridge |

**Key insight:** The item-level network is not a *different* network from the construct-level
network — it is the *same* geometric structure, viewed through a noisy lens. The SES geometry
(fingerprint positions in R⁴) determines the construct-level bridges, and the loading structure
determines how much of that signal penetrates to individual items.

The practical consequence: **construct-level analysis is the right level of abstraction**.
Item-level signal is so attenuated that only the strongest bridges between the best-loaded
items produce detectable associations. Of 3,894,963 possible item-to-item chains,
only 94,838 (2.4%) exceed |signal| ≥ 0.01.
The construct layer acts as a *noise-reducing aggregation* that makes the SES geometry visible.

However, the item-level view is valuable for one critical purpose: **tracing predictions**
**to specific survey questions**. When a user asks "what does housing quality have to do
with religiosity?", the answer can be traced from specific housing items (e.g., *does your
home have running water?*) through the bridge to specific religiosity items (e.g., *how
often do you attend religious services?*), with explicit signal strength at each step.