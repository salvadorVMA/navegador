# Propagator and Projector Methods in the Graph Traversal Engine

## A Technical Report on Dynamics and Geometry for SES-Conditioned Attitude Networks

---

## 1. Introduction and Project Context

The navegador project analyzes survey data from the World Values Survey (WVS, covering 66 countries across 7 waves from 1981 to 2018) and Mexican national surveys through networks of attitudinal constructs stratified by socioeconomic and demographic position. The core data object is the **gamma-surface**: a function $\gamma(\text{construct}_i, \text{construct}_j, \text{country}, \text{wave})$ that measures the monotonic covariation between pairs of attitudinal constructs, conditioned on four SES dimensions.

Each country-wave combination yields a **signed weighted graph** where:

- **Nodes** represent attitudinal constructs such as "gender role traditionalism," "democratic system evaluation," or "personal religiosity" (55 constructs in Wave 7).
- **Edge weights** $\gamma(A, B) \in [-1, 1]$ are Goodman-Kruskal gamma coefficients estimated via a doubly robust bridge estimator with 200 bootstrap iterations. Positive $\gamma$ indicates that higher SES position pushes both constructs in the same direction; negative $\gamma$ indicates opposite directions; $|\gamma| \approx 0$ indicates no SES-mediated monotonic relationship.
- **SES conditioning** uses four dimensions: education level (escol), urbanization (Tam\_loc), gender (sexo), and age/cohort (edad). All four are treated with equal standing --- none is a "control" subordinate to the others.

Each construct also carries a **4D SES fingerprint** $\mathbf{f}_i = (\rho_{\text{escol}}, \rho_{\text{Tam\_loc}}, \rho_{\text{sexo}}, \rho_{\text{edad}})$, where each component is the Spearman rank correlation between the construct score and the corresponding SES dimension. A key empirical result: the dot product $\mathbf{f}_i \cdot \mathbf{f}_j$ predicts $\text{sign}(\gamma_{ij})$ at 99.4% accuracy. Two constructs whose SES profiles point in the same direction in this 4D space are co-elevated by the same sociodemographic position.

The typical Wave 7 network has 23% edge density, diameter 4, average path length 1.73, and 94--100% structural balance --- meaning it is almost perfectly bipartite into a "cosmopolitan" camp (constructs elevated by education and urbanization) and a "traditional" camp (constructs elevated by older age and rural residence).

The Graph Traversal Engine (GTE) chains three analytical layers into a single query path: **Structure** (what is connected to what), **Dynamics** (how does signal propagate), and **Geometry** (how do patterns generalize across contexts). This report covers the Dynamics layer (the **Propagator**, Phase 2) and the Geometry layer (the **Projector**, Phase 3).

---

## Part I: The Propagator (Phase 2 --- Dynamics Layer)

### 2. Motivation

The Propagator addresses a fundamental question: **if construct A shifts in a society --- say, gender role traditionalism decreases --- what happens to other constructs?**

This is not a causal question. The gamma-surface captures conditional associations mediated by SES, not interventional effects. The Propagator asks what the association structure *implies* about co-movement: given that A and B are SES-coupled, a population-level shift in A's distribution is structurally accompanied by shifts elsewhere in the network. The Propagator quantifies these structural implications.

Three complementary methods are applied to the same graph, each grounded in a different physical metaphor:

| Method | Physical metaphor | What propagates | Edge signs used? | Scale control |
|--------|------------------|-----------------|-----------------|---------------|
| Belief Propagation | Statistical mechanics | Probability mass | Yes (Potts coupling) | None (equilibrium) |
| Personalized PageRank | Stochastic process | Random walkers | No ($|\gamma|$ only) | Teleport probability $\alpha$ |
| Spectral Heat Kernel | Diffusion PDE | Heat / signal | No ($|\gamma|$ only) | Continuous time $t$ |

When all three methods agree that construct B is strongly affected by a shift at A, the finding is robust to modeling assumptions. When they disagree, the disagreement itself reveals which aspect of graph structure --- sign structure, degree distribution, or spectral gap --- drives the result.

### 3. Belief Propagation on a Potts Markov Random Field

#### 3.1 Methodological motivation

Belief Propagation (BP) treats the construct network as a **Markov Random Field (MRF)**: a joint probability distribution over discrete belief states where conditional independence mirrors graph structure. Each construct is a random variable taking one of $K = 5$ ordinal states (quintile bins from the DR bridge pipeline). The MRF framework asks: if we observe that construct A is in a specific state, how does this evidence update the marginal distributions at all other constructs, propagated through the network?

This is the **information-theoretic** approach to propagation. BP computes the conditional implications of evidence --- not what *causes* what, but what *knowing* one thing tells us about another, given the joint structure encoded by the gamma weights.

#### 3.2 Mathematical formulation

The joint distribution over construct states $\mathbf{x} = (x_1, \ldots, x_n)$, $x_i \in \{1, 2, 3, 4, 5\}$, factorizes as:

$$P(\mathbf{x}) \propto \prod_{i \in V} \phi_i(x_i) \prod_{(i,j) \in E} \psi_{ij}(x_i, x_j)$$

The **node potential** $\phi_i(x_i)$ is the prior marginal of construct $i$ --- the empirical response distribution over the five quantile categories. When constructs are binned by equal-frequency quantile cuts (as in the Julia DR pipeline), the marginal is uniform by construction: $\phi_i(x) = 1/5$ for all $x$.

The **edge potential** uses a Potts model that incorporates both the magnitude and the sign of $\gamma_{ij}$:

$$\psi_{ij}(x_i, x_j) = \begin{cases} \exp(\beta \, |\gamma_{ij}|) & \text{if } (x_i = x_j \text{ and } \gamma_{ij} > 0) \text{ or } (x_i \neq x_j \text{ and } \gamma_{ij} < 0) \\ 1 & \text{otherwise} \end{cases}$$

For positive $\gamma$: agreement between states is favored (concordant SES-mediated covariation). For negative $\gamma$: disagreement is favored (discordant covariation). The inverse temperature $\beta$ controls coupling strength; $\beta = 2.0$ is used, producing noticeable but not overwhelming posterior shifts for edge weights in the observed range ($|\gamma|$ typically 0.01--0.10).

Messages are passed between neighbors iteratively. The message from node $i$ to node $j$ at iteration $t$ is:

$$m_{i \to j}^{(t+1)}(x_j) = \lambda \cdot m_{i \to j}^{(t)}(x_j) + (1 - \lambda) \cdot \sum_{x_i} \psi_{ij}(x_i, x_j) \, \phi_i(x_i) \prod_{k \in \mathcal{N}(i) \setminus j} m_{k \to i}^{(t)}(x_i)$$

where $\lambda = 0.5$ is a damping factor that prevents oscillation on loopy graphs. After convergence, the belief at node $j$ is:

$$b_j(x_j) \propto \phi_j(x_j) \prod_{k \in \mathcal{N}(j)} m_{k \to j}(x_j)$$

The **lift** --- the KL divergence from prior to posterior at node $j$ when construct $i$ is clamped to a specific state --- measures how much evidence at $i$ shifts the distribution at $j$:

$$L_{ij} = D_{\text{KL}}(b_j \| \phi_j) = \sum_{x_j} b_j(x_j) \log \frac{b_j(x_j)}{\phi_j(x_j)}$$

Running all $n$ single-evidence scenarios (clamping each construct at its top quintile) produces an $n \times n$ lift matrix $\mathbf{L}$, where $L_{ij}$ quantifies the informational coupling from $i$ to $j$.

#### 3.3 Design rationale

**Why Potts over Gaussian?** A Gaussian potential would treat ordinal categories as continuous with equal inter-category distances. This is empirically false for Likert-type items: the psychological distance between "strongly agree" and "agree" is not the same as between "agree" and "neutral." The Potts model operates on category identity rather than magnitude, avoiding this assumption. The cost is that Potts cannot model graded ordinal structure (it treats categories 1 and 5 as equally "different" from category 3). For 5-bin quantile-cut constructs, this is acceptable --- the bins are statistical partitions, not semantic anchors.

**Why BP is uniquely sign-aware.** Among the three Propagator methods, only BP uses the sign of $\gamma$ directly in its coupling structure. PPR and spectral diffusion operate on $|\gamma|$ and must recover direction post hoc. BP's Potts potentials encode whether concordance or discordance is favored at each edge, making it the only method that directly computes *directional* implications.

#### 3.4 Interpretation

- $L_{ij} > 0.1$: strong implication --- knowing construct $i$'s state substantially shifts the posterior at $j$.
- $L_{ij} \in [0.01, 0.1]$: moderate implication --- detectable but modest.
- $L_{ij} < 0.01$: negligible --- $i$ tells us almost nothing about $j$.

In this project, BP converged for 100% of the 66 Wave 7 country networks, typically within 50--100 iterations. The lift matrix reveals which constructs are most informationally coupled --- for example, clamping gender\_role\_traditionalism in Mexico most strongly lifts religious\_practice and sexual\_morality\_permissiveness, reflecting the tight SES coupling of these constructs through education and urbanization.

### 4. Personalized PageRank

#### 4.1 Methodological motivation

Personalized PageRank (PPR) models a **random walker** who starts at the anchor construct, follows edges with probability proportional to $|\gamma|$, and teleports back to the anchor with probability $\alpha$. The stationary distribution of this walk measures **structural influence**: how much of the network's traffic flows through each node when the process is seeded from a specific source.

Where BP asks "what does knowing A tell us about B?", PPR asks "how reachable is B from A, given the network's weighted connectivity?" PPR naturally handles the **fan-out problem**: influence dissipates with distance but concentrates at well-connected hubs, producing a ranked influence profile that respects the network's degree heterogeneity.

#### 4.2 Mathematical formulation

The transition matrix is constructed from absolute edge weights:

$$P = D^{-1} |W|$$

where $D = \text{diag}\left(\sum_j |\gamma_{ij}|\right)$ is the weighted degree matrix. The PPR vector seeded at node $i$ satisfies:

$$\boldsymbol{\pi}^{(i)} = \alpha \, \mathbf{e}_i + (1 - \alpha) \, P^\top \boldsymbol{\pi}^{(i)}$$

with closed-form solution $\boldsymbol{\pi}^{(i)} = \alpha (I - (1-\alpha)P^\top)^{-1} \mathbf{e}_i$. In practice, this is solved by power iteration, which converges in approximately 50 iterations for $n = 55$.

The teleport probability $\alpha = 0.2$ balances local and global exploration: the walker returns to the source one time in five, concentrating influence near the anchor while allowing multi-hop reach.

Three derived quantities characterize the network's influence architecture:

- **Hub score** of node $i$: $h_i = \sum_{j \neq i} \pi^{(i)}_j$ --- total outgoing influence when seeded from $i$.
- **Sink score** of node $j$: $s_j = \sum_{i \neq j} \pi^{(i)}_j$ --- total incoming influence from all seeds.
- **Asymmetry**: $A_{ij} = \pi^{(i)}_j - \pi^{(j)}_i$ --- directional dominance between two constructs. Even on an undirected graph, PPR produces asymmetric influence because degree heterogeneity creates directional bias: high-degree nodes influence more than they are influenced.

#### 4.3 Sign restoration

PPR uses $|\gamma|$ and produces unsigned influence values. Direction is recovered via **Dijkstra path sign accumulation**: the sign of the effect at node $j$ when the anchor $i$ shifts in a given direction is:

$$\text{direction}_j = \text{direction}_{\text{anchor}} \times \prod_{\text{edges on Dijkstra path}} \text{sign}(\gamma_{\text{edge}})$$

For direct neighbors, this reduces to $\text{sign}(\gamma_{ij})$.

#### 4.4 Interpretation

PPR differs from the TDA mediator analysis (which uses betweenness centrality on shortest paths) by accounting for **all paths**, not just the shortest. A construct with high betweenness lies on many shortest paths; a construct with high PPR receives random walkers through *any* route, weighted by connection strength.

In this project, no universal hubs exist across all 66 countries --- all hubs are zone-specific. The most consistent hub is economic\_ideology (median rank 7 across cultural zones, appearing in the top 10 in 6 or more of 8 zones). PPR and mediator scores correlate weakly ($\rho$ between $-0.15$ and $+0.10$), confirming that they measure genuinely different structural properties.

### 5. Spectral Heat Kernel Diffusion

#### 5.1 Methodological motivation

The heat equation on graphs models **continuous diffusion** of a signal placed at one node. At short times, only immediate neighbors respond; at long times, the signal equilibrates across the entire connected component. This provides a **multi-scale** view of propagation that neither BP (single equilibrium) nor PPR (single stationary distribution) can offer. Different phenomena operate at different time scales, and the spectral method reveals which constructs respond at which scale.

#### 5.2 Mathematical formulation

The normalized graph Laplacian is:

$$\mathcal{L} = I - D^{-1/2} |W| D^{-1/2}$$

Its eigendecomposition $\mathcal{L} = U \Lambda U^\top$ yields eigenvalues $0 = \lambda_0 \leq \lambda_1 \leq \cdots \leq \lambda_{n-1}$ (diffusion rates) and eigenvectors $\mathbf{u}_0, \mathbf{u}_1, \ldots, \mathbf{u}_{n-1}$ (spatial modes of variation).

The **heat kernel** is:

$$H(t) = e^{-\mathcal{L}t} = U \, \text{diag}(e^{-\lambda_0 t}, \ldots, e^{-\lambda_{n-1} t}) \, U^\top$$

The response at construct $j$ from an impulse at construct $i$ after time $t$ is:

$$H(t)_{ji} = \sum_{k=0}^{n-1} e^{-\lambda_k t} \, u_k(j) \, u_k(i)$$

Each eigenvector $\mathbf{u}_k$ represents a spatial pattern of variation across constructs. Each eigenvalue $\lambda_k$ is its decay rate. Small eigenvalues correspond to slow decay --- large-scale, persistent patterns. Large eigenvalues correspond to fast decay --- local, transient patterns.

The **characteristic time** of the network is $t^* = 1/\lambda_1$, where $\lambda_1$ is the Fiedler eigenvalue (algebraic connectivity). At $t \approx t^*$, the slowest non-trivial mode dominates, and diffusion "sees" the global bipartite structure.

The **diffusion distance** at time $t$ is:

$$D_t(i, j)^2 = \sum_{k} e^{-2\lambda_k t} \left(u_k(i) - u_k(j)\right)^2$$

This is a time-parameterized metric: at small $t$, it approximates geodesic distance; at large $t$, it collapses to global community structure.

#### 5.3 Multi-scale interpretation

Computing $H(t)_{ji}$ at multiple time points reveals the time-scale structure of propagation:

| Regime | What it captures |
|--------|-----------------|
| $t \ll t^*$ | Local neighborhood effects only; only direct neighbors respond |
| $t \approx t^*$ | Effects reach across the bipartition boundary (cosmopolitan $\leftrightarrow$ traditional camps) |
| $t \gg t^*$ | Equilibrium; uniform distribution; no remaining information |

The Fiedler eigenvalue $\lambda_1$ itself measures how tightly coupled the network is. Higher $\lambda_1$ means faster equilibration, meaning a more tightly integrated attitude structure. Across WVS Wave 7 countries, $\lambda_1$ ranges from 0.61 (Bangladesh) to 0.89 (Mongolia), with a median of 0.71. For WVS networks, the characteristic time $t^* \approx 1.4$, meaning that by $t = 5$, only the slowest modes survive and by $t = 10$ the signal is nearly uniform.

#### 5.4 Interpretation

The network's diameter of 4 and density of 23% cause diffusion to equilibrate quickly. The interesting regime is $t < t^*$, where local structure dominates. Early responders (high $H(t)_{ji}$ at small $t$) are structurally adjacent; late responders (requiring large $t$) are separated by the camp boundary. This temporal ordering of responses adds information that the static methods cannot provide.

Like PPR, the spectral method uses $|\gamma|$ and discards sign information. Sign is restored through the same Dijkstra path accumulation procedure. The spectral analysis is symmetric (the Laplacian is symmetric), so it cannot capture the directional asymmetries that PPR detects.

### 6. Consensus Scoring

After running all three methods for a given anchor, the Propagator synthesizes results through a consensus procedure:

1. For each target construct, determine whether it appears in the **top 10** by each method's ranking criterion (KL lift for BP, PPR score for PageRank, heat kernel response at $t = 1.0$ for spectral).
2. The **agreement score** is the fraction of methods (0/3 to 3/3) that include the target in the top 10.
3. The final ranking sorts by agreement score first, then by mean rank across methods as a tiebreaker.
4. Confidence labels: "high" (3/3 agreement), "medium" (2/3), "low" (1/3).

A construct ranked highly by all three is robustly predicted to co-move with the anchor regardless of the modeling metaphor. Disagreements reveal structurally informative edge cases. For instance, a construct may have high BP lift (informationally coupled) but low PPR (structurally distant, reached only through a specific narrow path) --- indicating that the relationship is real but fragile, dependent on a single mediating construct. Conversely, high PPR but low BP lift suggests the construct is well-connected (many paths) but weakly coupled (small $|\gamma|$ on each).

---

## Part II: The Projector (Phase 3 --- Geometry Layer)

### 7. Motivation

The Propagator answers: "What co-moves with A in Mexico?" The Projector extends this: **Can we predict what would happen in Germany? In 1996 versus 2018? Which SES dimensions drive the downstream effects?** The Projector operates on the *landscape of graphs* --- the collection of country-wave networks --- rather than on any single graph.

### 8. Spectral Distance Projection

#### 8.1 Motivation

Countries with similar eigenspectra of their association networks have similar "wiring" of SES-attitude relationships. Spectral distance quantifies structural similarity without requiring that the same pairs of constructs be linked --- only that the overall pattern of connectivity (density, community structure, spectral gap) be similar.

#### 8.2 Mathematical formulation

For each country $c$, compute the sorted eigenvalue vector $\boldsymbol{\lambda}^{(c)} = (\lambda_0^{(c)}, \lambda_1^{(c)}, \ldots, \lambda_{n-1}^{(c)})$ from its normalized Laplacian. The spectral distance between two countries is the $L_2$ norm:

$$d_{\text{spectral}}(c_1, c_2) = \|\boldsymbol{\lambda}^{(c_1)} - \boldsymbol{\lambda}^{(c_2)}\|_2$$

When construct sets differ across waves (24 constructs in Wave 3 vs. 55 in Wave 7), eigenvalue vectors are padded with zeros to equal length.

#### 8.3 Interpretation

Small spectral distance means similar network topology: similar density, connectivity, and community structure. It does **not** mean the same constructs are linked --- only that the *pattern* of linkage is similar. A propagation result from the source country is more likely to hold in a spectrally similar target country because the dynamics (diffusion rates, equilibration time, fan-out behavior) are governed by the spectrum.

In this project, Mexico's nearest spectral neighbor is Japan ($d = 0.073$), not Brazil or other Latin American countries. This counterintuitive finding reflects the fact that spectral distance captures network *topology*, not cultural content. Mexico and Japan share similar density and connectivity patterns despite very different attitudinal profiles.

### 9. Zone Aggregation

#### 9.1 Motivation

The Inglehart-Welzel cultural zones (English-speaking, Catholic Europe, Protestant Europe, Orthodox, Latin American, Confucian, South/Southeast Asian, African-Islamic) group countries by shared historical-cultural heritage. Testing whether propagation patterns cluster by zone reveals whether cultural background constrains SES-attitude dynamics or whether each country is structurally idiosyncratic.

#### 9.2 Method

For each zone $Z$ containing countries $\{c_1, \ldots, c_k\}$:

1. Run the Propagator on each country $c_i$ with the same anchor construct and direction.
2. Compute **sign consistency**: the fraction of countries where each top-ranked effect has the same direction (positive or negative shift).
3. Compute **mean agreement**: the average consensus score across zone members.
4. Identify **notable divergences**: countries where the propagation pattern inverts relative to the zone majority.

#### 9.3 Interpretation

High sign consistency within a zone means the SES-attitude mechanism generalizes across countries with shared cultural heritage: the same anchor shift produces the same downstream directions. Low consistency means country-specific factors (institutional context, economic structure, historical path) dominate over shared heritage.

In this project, spectral zone coherence is statistically significant ($p = 0.001$ for Wave 7, permutation test), but topological zone coherence is not (bottleneck distances $p = 0.672$). Within-zone Fiedler partition agreement (measured by Adjusted Rand Index) is 2.86 times the across-zone value. The English-speaking zone is the most internally coherent (ARI = 0.153). These results indicate that cultural zones capture *spectral* structure (connectivity patterns) but not *topological* structure (persistent loops and voids).

### 10. Temporal Trajectory

#### 10.1 Motivation

With data spanning 1996--2018 across five WVS waves, the Projector tracks how a country's attitude network evolves over time. Does the propagation pattern change? Is the network tightening (attitudes becoming more interdependent under SES conditioning) or loosening (attitudes decoupling)?

#### 10.2 Fiedler trajectory

For country $c$ across available waves $w_1, \ldots, w_T$, the sequence:

$$\lambda_1^{(c)}(w_1), \; \lambda_1^{(c)}(w_2), \; \ldots, \; \lambda_1^{(c)}(w_T)$$

is the country's **algebraic connectivity trajectory**. A linear regression slope classifies the trend:

- **Tightening** (positive slope): SES increasingly constrains attitude bundles; propagation effects grow stronger.
- **Stable** ($|\text{slope}|$ below threshold): persistent structure.
- **Loosening** (negative slope): attitudes decouple from SES-mediated co-movement; propagation effects weaken.

#### 10.3 Network autoregression forecast

A one-parameter autoregressive model forecasts how the mean construct response vector $\mathbf{x}(w)$ evolves:

$$\hat{\mathbf{x}}(w+1) = \alpha^* \cdot A^{(w)} \cdot \mathbf{x}(w) + (1 - \alpha^*) \cdot \mathbf{x}(w)$$

where $A^{(w)} = D^{-1}|W^{(w)}|$ is the row-normalized absolute weight matrix at wave $w$, and $\alpha^*$ is fitted by minimizing prediction error across all available wave transitions:

$$\alpha^* = \arg\min_\alpha \sum_{t=1}^{T-1} \|\hat{\mathbf{x}}^{(\alpha)}(w_{t+1}) - \mathbf{x}(w_{t+1})\|^2$$

The single parameter $\alpha$ blends network-driven dynamics (the adjacency structure pushes neighboring constructs toward alignment) with persistence (each construct retains its current value). A shock at the anchor modifies $\mathbf{x}(w_{\text{current}})$ by the shock magnitude and propagates forward through this equation.

Per-construct residual standard deviation across wave transitions provides uncertainty bounds: 80% prediction interval $= \hat{x}_i \pm 1.28 \, \sigma_i$.

#### 10.4 Mediator stability

The persistence of top mediator constructs across waves assesses which structural bridges are load-bearing versus transient. A mediator construct that ranks as the top betweenness-centrality node in 4 of 5 waves (such as gender\_role\_traditionalism in the majority of countries) is a fundamental feature of the SES-attitude geometry; one that appears in only a single wave is likely a statistical artifact.

#### 10.5 Key findings

Mexico's Fiedler value peaks at Wave 5 (2007, $\lambda_1 = 0.82$) and then declines, suggesting the Mexican attitude network was most tightly integrated around 2007. The global convergence pattern oscillates with no net trend (alternating between converging and diverging across adjacent waves). Education's role in SES dominance shows a structural break: escol accounts for less than 2% of SES stratification in Waves 3--6 but jumps to 35.5% in Wave 7, suggesting a global shift in how education structures attitude covariation.

The fitted autoregression parameter $\alpha$ ranges from 0.00 (Egypt --- pure persistence, no network-driven dynamics) to 0.40 (Vietnam --- substantial network influence). Mexico's $\alpha = 0.112$, meaning 89% inertia and 11% network-driven change per wave transition.

### 11. SES Geometry Characterization

#### 11.1 Motivation

The propagation results tell us *which* constructs co-move, but the SES fingerprints tell us *where in SES space* the effects land. If the anchor is driven primarily by education, do the downstream effects also concentrate on education-driven constructs, or do they "leak" into age or gender dimensions?

#### 11.2 Method

For each construct in the top-$N$ consensus ranking:

1. Retrieve its 4D SES fingerprint $\mathbf{f}_j = (\rho_{\text{escol}}, \rho_{\text{Tam\_loc}}, \rho_{\text{sexo}}, \rho_{\text{edad}})$.
2. Weight each fingerprint by the predicted effect direction ($\pm 1$).
3. Compute the **mean SES vector** of effects: $\bar{\mathbf{f}} = \frac{1}{N} \sum_{j} (\pm 1) \cdot \mathbf{f}_j$.
4. Identify the **dominant dimension**: $\arg\max_d |\bar{f}_d|$.
5. Compute **SES spread**: the standard deviation of fingerprint magnitudes across the top-$N$ effects. High spread means effects scatter across SES dimensions; low spread means they concentrate on one dimension.

#### 11.3 Interpretation

If the anchor is education-driven and all effects are also education-driven, the propagation stays "within dimension" --- pure SES-mediated co-movement along a single axis. If effects cross into age or gender dimensions, the SES mechanism is more complex: the education gradient triggers a cascade that connects to age-stratified or gender-stratified attitudes.

The network's PCA reveals that PC1 accounts for 78% of fingerprint variance (the education-vs-tradition axis), so most propagation stays within this dominant dimension. But 22% of variance is orthogonal --- effects that leak into age or urbanization dimensions. These **cross-dimension** effects are the most sociologically interesting because they reveal how SES mechanisms entangle different stratification axes. For example, a shift in constructs structured by education may propagate to constructs structured by age, indicating that education and generational experience are coupled in the underlying social structure.

### 12. Transfer Confidence

#### 12.1 Motivation

How reliable is it to extrapolate a propagation result from one country to another? The Projector produces a confidence score that integrates multiple signals about cross-context transferability.

#### 12.2 Formulation

$$\text{confidence}(\text{source}, \text{target}) = w_1 \cdot \left(1 - \frac{d_{\text{spectral}}}{d_{\max}}\right) + w_2 \cdot \mathbb{1}[\text{same zone}] + w_3 \cdot \text{fiedler\_stability}$$

with weights $w_1 = 0.5$, $w_2 = 0.3$, $w_3 = 0.2$:

- **Spectral similarity** ($w_1 = 0.5$): the dominant signal. Countries with similar eigenspectra have similar diffusion dynamics.
- **Zone membership** ($w_2 = 0.3$): shared cultural zone provides a prior for similar SES-attitude mechanisms.
- **Fiedler stability** ($w_3 = 0.2$): defined as $1 - |\Delta\lambda_1 / \bar{\lambda}_1|$ over available waves. A country with a stable Fiedler trajectory has a persistent network structure that is more predictable.

#### 12.3 Interpretation

The confidence score ranges from 0 to 1. It reflects the Projector's assessment of whether the target country's network dynamics are similar enough to the source country's that a propagation result can be meaningfully transferred.

Examples from the project illustrate the score's behavior:

- **Mexico to Japan**: moderate confidence. High spectral similarity ($d = 0.073$, the smallest in the dataset) but different cultural zone (Latin American vs. Confucian). The score reflects that the *topology* of the attitude network is shared even though the cultural context differs.
- **Mexico to Brazil**: moderate confidence. Same cultural zone (Latin American) but larger spectral distance. Similar cultural heritage provides a prior for shared mechanisms, but the network wiring differs more than Mexico-Japan.
- **Mexico to Pakistan**: low confidence. Despite high topological similarity (Jaccard index 0.86 on the edge set), the SES geometry is nearly orthogonal: sign agreement between the two countries is only 49% (essentially random). This case demonstrates that structural similarity and SES-content similarity are independent properties --- transfer requires both.

---

## 13. Interpreting Results: A Summary Framework

The Propagator and Projector together provide a structured answer to questions about attitude co-movement across societies and time:

**The Propagator tells you** what co-moves when an anchor shifts, according to three complementary lenses. BP reveals informational coupling (what knowing A tells us about B). PPR reveals structural reachability (how well-connected B is to A, through all paths). Spectral diffusion reveals multi-scale dynamics (at what time scale B responds to A). Consensus across all three methods identifies robust effects that survive different modeling assumptions.

**The Projector tells you** whether that pattern generalizes. Spectral distance identifies structurally similar countries where the propagation dynamics are likely to hold. Zone aggregation tests whether cultural heritage constrains the mechanisms. Temporal trajectories track whether the network is tightening or loosening. SES geometry characterizes which stratification dimensions carry the effects. Transfer confidence synthesizes these signals into an actionable reliability estimate.

**Neither layer is causal.** The gamma-surface captures conditional association patterns mediated by SES. The statement "if trust increases, democratic satisfaction also increases" means: "in populations where people with the same SES profile score higher on trust, they also score higher on democratic satisfaction." This is an associative pattern, not an interventional claim. Changing trust does not necessarily cause democratic satisfaction to change --- both may be independently driven by a shared sociodemographic configuration.

**The Conditional Independence Assumption (CIA).** The DR bridge estimator conditions on four SES dimensions. Under CIA, $\gamma$ captures only SES-mediated covariation. Direct $A \to B$ effects independent of SES, confounders outside the four-variable set, reverse causation, and non-monotonic SES-attitude relationships are all invisible to the system. The NMI diagnostic (which detects any statistical dependence regardless of shape) is universally low in the empirical sweeps, suggesting that non-monotonic patterns are rare, but the other limitations remain.

**Structural balance governs sign propagation.** With 94--100% of triangles sign-consistent, the network is cleanly bipartite. Propagation respects this geometry: effects within the same camp (both constructs elevated by the same SES profile) are positive; effects crossing the camp boundary are negative. The bipartition into "cosmopolitan" (education/urbanization-driven) and "traditional" (age/rural-driven) camps is the single most important structural feature of the network, and the Propagator's sign predictions inherit this structure.

---

*This document describes methods implemented in the navegador Graph Traversal Engine. For implementation details, see `docs/GRAPH_TRAVERSAL_ENGINE_PLAN.md`. For the mathematical specifications of individual message passing stages, see `docs/MESSAGE_PASSING_SPEC.md`. For empirical findings, see the analysis reports in `data/results/`.*
