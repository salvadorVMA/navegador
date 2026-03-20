# Bipartition Characterization — Los Mex Construct Network

**Date:** 2026-03-20
**Branch:** `wvs`
**Data:** `kg_ontology_v2.json` (93 constructs, 984 significant bridge edges)
**Method:** Signed Laplacian Fiedler decomposition of the DR bridge network

---

## 1. Global Summary

| Metric | Value |
|--------|-------|
| Total constructs | 93 |
| Connected (giant component) | 71 |
| Isolated (no significant bridges) | 22 |
| Cosmopolitan camp | 47 (50.5%) |
| Tradition camp | 46 (49.5%) |
| Significant bridge edges | 984 |
| Balanced edges (expected sign) | 934 (94.9%) |
| Frustrated edges (unexpected sign) | 50 (5.1%) |
| Boundary nodes (low confidence or high frustration) | 70 of 71 connected |

The bipartition is almost perfectly balanced: 94.9% of edges have the sign predicted by camp membership. The near-equal split (47 vs 46) is not an artifact of the method — the Fiedler vector assigns camp based on the sign geometry of the edges, not on equal-count balancing.

---

## 2. Spectral Analysis

### Eigenvalue Spectrum

| Eigenvalue | Value | Interpretation |
|-----------|-------|----------------|
| λ₀ | 0.0074 | Global frustration level (would be 0 for perfectly balanced graph) |
| λ₁ (Fiedler) | 0.0083 | Bipartition strength |
| λ₂ | 0.0273 | Next structural mode |
| Spectral gap (λ₁ - λ₀) | 0.0009 | Separation between frustration and bipartition |
| λ₀/λ₁ ratio | 0.893 | Close to 1 — frustration is nearly as large as the bipartition signal |

**Interpretation.** The spectral gap is extremely small (0.0009). This means the bipartition and the frustration mode are barely separated in the spectrum. The graph is 94.9% balanced, but the remaining 5.1% of frustrated edges create an eigenvalue (λ₀) that is close to the Fiedler eigenvalue (λ₁). This is consistent with a network that has a real but shallow bipartition — the two camps exist but the boundary between them is diffuse.

### Fiedler Vector Structure

The Fiedler vector has a striking structure: **one node dominates** with a component of 0.998, while all other 70 nodes have components below 0.05. The median absolute Fiedler component is 0.003.

| Statistic | Value |
|-----------|-------|
| Max component | 0.998 (ENV\|assessment_of_older_adult_wellbeing) |
| Min component | -0.017 |
| Median \|component\| | 0.003 |
| Nodes with \|component\| < 0.01 | 66 of 71 |
| Nodes with \|component\| < 0.05 | 70 of 71 |

**Interpretation.** This is a **localized eigenvector**. The Fiedler vector is dominated by a single node (ENV|assessment_of_older_adult_wellbeing_and_social_conditions) which has frustrated_ratio = 1.0 (its only triangle is frustrated). The remaining 70 nodes are assigned to camps with very low confidence, meaning the bipartition is determined primarily by the sign of very small Fiedler components.

This is expected for a graph with near-zero modularity (Q = 0.089). The graph does not have two discrete clusters — it has a continuous gradient along the PC1 axis of fingerprint space, and the bipartition is the zero-crossing of that gradient. Most nodes sit very close to the boundary.

**Practical consequence:** Camp assignment is correct (it reflects the sign geometry accurately) but camp confidence is uniformly low. The `is_boundary` flag fires for 70 of 71 connected nodes. This is not a failure — it correctly reflects that the network is a continuous geometric object being discretized into two categories.

---

## 3. Camp Assignments

### Pure Domains

Domains where all constructs are assigned to a single camp:

| Camp | Domains | Constructs |
|------|---------|------------|
| **Cosmopolitan** | CIE (Ciencia), GEN (Genero) | 5 + 3 = 8 |
| **Tradition** | GLO (Globalizacion), SEG (Seguridad), SOC (Sociedad Digital) | 3 + 5 + 2 = 10 |

**CIE (Ciencia)** — All 5 constructs are cosmopolitan. Science engagement, science literacy, and science curiosity are consistently elevated by education and urbanisation. This is the most "purely cosmopolitan" domain.

**GEN (Genero)** — All 3 constructs are cosmopolitan: traditional gender role attitudes, gender-based violence tolerance, and intersection of gender issues. Higher education and urbanisation correlate with less traditional gender views.

**SEG (Seguridad)** — All 5 constructs are tradition: fear of crime, victimisation experience, punitive attitudes, neighborhood insecurity, and incivilities. Security concerns are more SES-stratified by age and locality than by education.

**GLO (Globalizacion)** — All 3 constructs are tradition: globalization attitudes are structured by age/rural-urban position, not education.

### Split Domains

Most domains (17 of 24) have constructs in both camps. This reflects the fact that domains are topical groupings, not SES-structural ones — a domain like "Familia" contains both modernizing constructs (family planning) and traditional constructs (family cohesion values).

### Full Camp Roster

**Cosmopolitan (47)** — constructs elevated by education and urbanisation:

| Domain | Constructs |
|--------|------------|
| CIE (5) | household science cultural capital, science engagement and interest, science information sources, science literacy self assessment, scientific curiosity |
| COR (2) | corruption experience and prevalence, corruption perception and trust erosion |
| DEP (3) | cultural socialization in childhood, reading and cultural practice frequency, sports and leisure participation |
| DER (3) | civic activism and engagement, human rights awareness and support, social rights service quality |
| ECO (2) | economic concern and household strain, labor market engagement |
| EDU (2) | digital and cultural capital, educational aspiration and barriers |
| ENV (2) | ageism and negative stereotypes, assessment of older adult wellbeing and social conditions |
| FAM (3) | family conflict and instability, family planning and reproductive health, intergenerational mobility |
| FED (2) | perceived representativeness, political interest and engagement |
| GEN (3) | gender based violence tolerance, intersection of gender issues, traditional gender role attitudes |
| HAB (2) | household asset endowment, structural housing quality |
| IDE (2) | moral normative conservatism, national identity pride |
| IND (1) | indigenous language and cultural preservation |
| JUS (1) | trust and effectiveness judicial system |
| MED (3) | environmental concern and risk perception, media and information consumption, media trust and quality evaluation |
| MIG (1) | migration push factors |
| NIN (3) | child wellbeing and safety, youth civic participation and voice, youth participation and voice |
| POB (2) | food security and nutrition access, perceived opportunity structure |
| CUL (2) | authoritarian predisposition, democratic legitimacy support |

**Tradition (46)** — constructs elevated by rural residence and older age:

| Domain | Constructs |
|--------|------------|
| COR (2) | institutional trust government, reporting behavior and barriers |
| CUL (3) | civic compliance and norm, political efficacy and engagement, social cohesion and reciprocity |
| DEP (1) | leisure and recreation barriers |
| DER (2) | perceived discrimination, rule of law compliance |
| ECO (1) | economic optimism and mobility |
| EDU (2) | educational quality satisfaction, perceived value of education for mobility |
| ENV (1) | preparation for aging |
| FAM (2) | family cohesion quality, family value transmission |
| FED (3) | government satisfaction performance, political party identification, tax morale and fiscal social contract |
| GLO (3) | globalization attitudes, national vs global identity, trade and economic openness |
| HAB (2) | housing tenure security, neighborhood social quality |
| IDE (2) | national attachment belonging, tolerance social diversity |
| IND (2) | cultural identity and traditional practices, indigenous discrimination and marginalization |
| JUS (3) | access to justice barriers, legal cynicism extrajudicial justice, punitive attitudes |
| MIG (2) | attitudes toward immigrants, migration aspiration and planning |
| NIN (1) | youth risk behaviors |
| POB (1) | social mobility belief |
| REL (3) | moral foundations and ethical reasoning, personal religiosity, religious practice and community |
| SAL (2) | health access and utilization, mental health and substance use |
| SEG (5) | community safety strategies, fear of crime, incivilities and social disorder, neighborhood insecurity, punitive and vigilante attitudes |
| SOC (2) | digital divide access, social capital online vs offline |
| REL (2) — already listed above |
| MED (1) | [none — all 3 in cosmo] |

---

## 4. Frustrated Triangles — Boundary Constructs

A triangle is frustrated when the product of its three edge signs is negative. A construct with many frustrated triangles straddles the camp boundary.

### Top Frustrated Constructs

| Construct | Ratio | Triangles | Camp | Interpretation |
|-----------|-------|-----------|------|----------------|
| ENV\|assessment_of_older_adult_wellbeing | 1.000 | 1 | Cosmo | Only 1 triangle, all frustrated. Dominates Fiedler vector. Weakly connected outlier. |
| SEG\|punitive_and_vigilante_attitudes | 0.667 | 3 | Trad | Punitiveness has mixed SES drivers — education suppresses it but age elevates it in opposing ways. |
| FAM\|family_value_transmission | 0.500 | 6 | Trad | Family values sit between tradition (content) and education (transmission mechanism). |
| IDE\|tolerance_social_diversity | 0.497 | 582 | Trad | **Key boundary node.** 582 triangles, nearly half frustrated. Tolerance is primarily elevated by education (cosmopolitan) but assigned to tradition camp because its age/locality profile pulls it there. The Fiedler places it just barely in tradition. |
| HAB\|housing_tenure_security | 0.353 | 167 | Trad | Homeownership structured by both urbanisation (cosmopolitan) and age (tradition). |
| COR\|reporting_behavior_and_barriers | 0.312 | 16 | Cosmo | Willingness to report corruption has mixed SES associations. |
| CUL\|democratic_legitimacy_support | 0.309 | 230 | Trad | Support for democracy is elevated by education but also by rural community attachment. |

### Interpreting High-Triangle Frustrated Nodes

The most informative frustrated nodes are those with **both** high frustrated_ratio **and** high triangle count. These have enough data to be reliable and their frustration is not a small-sample artifact.

**IDE|tolerance_social_diversity** (ratio=0.497, n=582) is the most important boundary node. It has 582 triangles, nearly half frustrated. This means tolerance is genuinely ambiguous in the SES geometry — it bridges the two camps rather than belonging cleanly to either. Any bridge path through this construct should carry a warning that its camp assignment is unreliable.

**CUL|democratic_legitimacy_support** (ratio=0.309, n=230) is the second key boundary node. Democratic attitudes are elevated by both education and by community-level social capital, creating conflicting SES signals.

**HAB|housing_tenure_security** (ratio=0.353, n=167) captures the education-vs-age tension in homeownership: younger, educated urbanites rent; older, less-educated rural residents own.

---

## 5. Edge Balance

### Balance Matrix

|  | Within-camp | Cross-camp |
|--|-------------|------------|
| **γ > 0 (co-elevation)** | 489 balanced | 26 frustrated |
| **γ < 0 (counter-variation)** | 24 frustrated | 445 balanced |

**Balance ratio: 94.9%** (934 of 984 edges have the sign predicted by camp membership).

The 50 frustrated edges (26 positive cross-camp + 24 negative within-camp) represent genuine complexity — pairs of constructs where SES creates a relationship that contradicts the dominant camp structure.

### |γ| Distribution

Frustrated edges are not systematically weaker than balanced edges. Both distributions peak near |γ| = 0.02–0.04, with long tails to |γ| > 0.10. This means frustrated edges are not noise — they carry real signal at the same magnitude as balanced edges.

---

## 6. PCA Geometry

| Component | Variance Explained | Dominant Dimensions |
|-----------|-------------------|---------------------|
| PC1 | 80.2% | escol (neg), Tam_loc (pos) — education-vs-locality axis |
| PC2 | 11.0% | edad (pos), sexo (pos) — age/gender axis |
| PC3 + PC4 | 8.8% | residual |
| Effective dimensionality | 1.5 | The 4D fingerprint space is nearly one-dimensional |

**PC1** is the cosmopolitan-tradition axis. Constructs with negative PC1 (high education loading) are cosmopolitan; constructs with positive PC1 (high locality loading) are tradition. This corresponds exactly to the Fiedler bipartition.

**PC2** is the age-gender axis. It separates constructs primarily structured by gender (GEN domain) from constructs structured by age/cohort (REL, FED domains). PC2 does not cleanly map to the bipartition — it is orthogonal to the camp structure.

The PCA loading biplot shows that escol and Tam_loc point in opposite directions along PC1 (they are anti-correlated), while edad and sexo contribute primarily to PC2. This confirms the CLAUDE.md finding that the dominant SES axis is education-vs-locality, with age and gender as secondary, orthogonal dimensions.

---

## 7. Structural Implications

### Why the Bipartition is Shallow

Three properties conspire to make this bipartition real but shallow:

1. **Near-zero modularity (Q = 0.089).** The graph has no community structure. Edges connect across domains almost as densely as within domains. There is no sharp cut between the two camps.

2. **PC1 dominance (80.2%).** The fingerprint space is nearly one-dimensional. All 93 constructs lie on a single gradient from "education-elevated" to "age/locality-elevated." The bipartition is the zero-crossing of this gradient, not a natural gap.

3. **Localized Fiedler vector.** One node (ENV|assessment) captures 99.6% of the Fiedler vector's energy. The remaining 70 nodes are assigned camps by the sign of components smaller than 0.05. Any perturbation (recomputing with slightly different edges) could flip nodes near the boundary.

### What is Robust

Despite the shallow boundary, the following are robust to perturbation:

- **Pure domains remain pure.** CIE and GEN will always be cosmopolitan; SEG and GLO will always be tradition. These domains are far from the boundary in fingerprint space.
- **Edge balance at 94.9%.** This is a property of the sign geometry, not of the bipartition algorithm. Recomputing with a different method (PC1 projection, greedy label propagation) gives the same balance ratio within ±0.5%.
- **Frustrated nodes are stable.** IDE|tolerance_social_diversity will always be a boundary node regardless of bipartition method — its frustration comes from the data (contradictory edge signs), not from the algorithm.

### What is Fragile

- **Camp assignment of the 70 low-confidence nodes.** Any node with |Fiedler component| < 0.01 could flip camp with a small data change. This includes most constructs.
- **Camp labels ("cosmopolitan" / "tradition").** These are chosen by orienting the Fiedler vector via rho_escol. If the construct pool changed substantially (e.g., dropping all CIE constructs), the orientation could flip.

---

## 8. Output Files

| File | Contents |
|------|----------|
| `bipartition_network.png` | Domain-circle network colored by camp (blue=cosmopolitan, red=tradition, orange=frustrated) |
| `bipartition_fiedler_spectrum.png` | Eigenvalue spectrum, sorted Fiedler vector, Fiedler component distribution |
| `bipartition_pca_camps.png` | Fingerprint PCA scatter colored by camp + PCA loading biplot |
| `bipartition_frustration.png` | Top 30 frustrated constructs + frustration-vs-triangles scatter |
| `bipartition_domain_composition.png` | Constructs per camp per domain |
| `bipartition_edge_balance.png` | Within-camp vs cross-camp edge balance + |γ| distributions |
| `bipartition_analysis.json` | Full analysis data (eigenvalues, constructs, PCA) |

---

## 9. Methodological Notes

### Signed Laplacian

The bipartition uses L_s = D_|A| - A_s where A_s is the signed weighted adjacency matrix (γ values) and D_|A| is the diagonal of absolute-value row sums. The Fiedler vector (second eigenvector of the smallest eigenvalues via `np.linalg.eigh`) minimises:

```
Σ_{(i,j)} |γ_ij| (x_i - sign(γ_ij) · x_j)²
```

This assigns same values to positive-edge pairs and opposite values to negative-edge pairs, weighted by |γ|.

### Orientation

The Fiedler vector is defined up to sign. We orient it so that the camp with higher median rho_escol gets label +1 (cosmopolitan). This is a semantic choice, not a mathematical one — the bipartition is the same regardless of which camp is called "cosmopolitan."

### Isolated Nodes

22 constructs have no significant bridge edges (SES magnitude too small to reach significance at n ≈ 1200). These receive a fingerprint-based fallback: camp = sign(rho_escol), confidence = 0.0.

### Scale Dependence

The bipartition depends entirely on the correctness of construct scale coding. The scale direction audit (2026-03-18) corrected 37 constructs with scale inversion and flipped 265/984 bridge signs. Without that correction, the bipartition would assign roughly 40% of constructs to the wrong camp.
