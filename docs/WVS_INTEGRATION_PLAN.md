# WVS Integration Plan for Navegador

## 1. Overview

This document outlines the plan to integrate the **World Values Survey (WVS)** into Navegador alongside the existing "Los Mexicanos vistos por si mismos" (los_mex) dataset. The goal is to enable the navegador agent to query, analyze, and cross-reference both datasets, and to construct an SES bridge between WVS and los_mex similar to the existing cross-survey bridge within los_mex.

## 2. WVS Data Inventory

### 2.1 Files Copied to `data/wvs/`

| File | Description | Size |
|------|-------------|------|
| `F00011356-WVS_Cross-National_Wave_7_csv_v6_0.zip` | Wave 7 individual-level data (2017-2022), 97K respondents, 64 countries | 20MB (190MB unzipped) |
| `F00011931-WVS_Time_Series_1981-2022_csv_v5_0.zip` | Full longitudinal dataset, waves 1-7, 1981-2022 | 118MB (1.3GB unzipped) |
| `F00003844-WVS_Time_Series_List_of_Variables_and_equivalences_1981_2022_v3_1.xlsx` | Variable equivalences across waves (1048 vars) | 70KB |
| `F00012255-WVS_TimeSeries_1981_2020_CountrySpecificCodes.xlsx` | Country-specific code mappings | 229KB |
| `WVS_Countries_in_time_series_1981-2022.xlsx` | Country participation by wave | 15KB |
| `WVS7_Master_Questionnaire_2017-2020_English.pdf` | Wave 7 master questionnaire | 865KB |
| `WVS7_Questionnaire_Mexico_2018_Spanish.pdf` | Mexico-specific questionnaire (Spanish) | 193KB |
| `F00017184-WVS_Time_Series_1981_2022_Variables_Report_v5.0.pdf` | Complete variable report | 7.3MB |
| `wvs_var_forgob.xlsx` | User's custom variable selection scores | 30KB |

### 2.2 Mexico in WVS

Mexico participates in **all 7 waves** with substantial samples:

| Wave | Period | n (Mexico) |
|------|--------|-----------|
| 1 | 1981-1984 | 1,837 |
| 2 | 1990-1994 | 1,531 |
| 3 | 1995-1998 | 1,510 |
| 4 | 1999-2004 | 1,535 |
| 5 | 2005-2009 | 1,560 |
| 6 | 2010-2014 | 2,000 |
| 7 | 2017-2022 | 1,741 |
| **Total** | | **11,714** |

Wave 7 (2018 for Mexico) is the closest temporal match to los_mex (2014-2015).

## 3. WVS Data Structure

### 3.1 Variable Naming Convention

WVS uses a **dual coding system**:

- **Time-series codes** (A-prefix): Stable identifiers across waves (e.g., `A001` = "Important in life: Family")
- **Wave-specific Q-codes**: Used in the actual CSV data (e.g., `Q1` in Wave 7 = `A001` in time series)

The equivalence mapping file links these across all 7 waves.

### 3.2 Variable Domains (by prefix)

| Prefix | Domain | Total vars | In Wave 7 |
|--------|--------|-----------|-----------|
| A | Social Values, Attitudes & Stereotypes | 208 | 60 |
| B | Environment | 25 | 1 |
| C | Work/Employment | 50 | 18 |
| D | Family | 68 | 18 |
| E | Politics & Society | 296 | 134 |
| F | Religion & Morale | 127 | 36 |
| G | National Identity | 119 | 25 |
| H | Security | 30 | 28 |
| I | Science & Technology | 2 | 2 |
| X | SES/Demographics | 49 | 29 |
| Y | Derived Indices | 37 | 37 |

### 3.3 Sentinel Values

WVS uses **negative sentinel codes** (unlike los_mex which uses `>= 97`):
- `-1` = Don't know
- `-2` = No answer
- `-3` = Not applicable
- `-4` = Not asked in this country
- `-5` = Missing; not specified

### 3.4 SES Variables Available for Mexico (Wave 7)

| WVS var | Description | los_mex equivalent | n_valid (MEX) | Values |
|---------|-------------|-------------------|---------------|--------|
| Q260 | Sex | sexo | 1741 | 1=Male, 2=Female |
| Q262 | Age (continuous) | edad (binned) | 1739 | 18-90+ |
| Q275 | Education ISCED (8 levels) | escol | 1664 | 0-8 |
| Q275R | Education recoded (3 groups) | — | 1733 | 1-3 |
| Q279 | Marital status | est_civil | 1664 | 1-7 |
| Q288 | Income scale (10 levels) | income_quintile | 1719 | 1-10 |
| Q288R | Income recoded (3 groups) | — | 1719 | 1-3 |
| G_TOWNSIZE | Town size (8 levels) | Tam_loc (4 levels) | 1724 | 1-8 |
| H_URBRURAL | Urban/Rural | — | 1741 | 1-2 |
| N_REGION_WVS | Region (country-specific) | region | 1741 | 484101-484132 |

### 3.5 Wave 7 CSV Structure

- **613 columns** total in Wave 7 CSV
- Administrative columns: `version`, `doi`, `A_WAVE`, `A_YEAR`, `A_STUDY`, `B_COUNTRY`, `B_COUNTRY_ALPHA`, etc.
- Region/geography: `N_REGION_ISO`, `N_REGION_WVS`, `G_TOWNSIZE`, `H_URBRURAL`
- Substantive questions: `Q1`-`Q290` (373 Q-coded variables)
- Weights: `W_WEIGHT`, `PWGHT`

## 4. Structural Comparison: WVS vs. los_mex

| Dimension | los_mex | WVS |
|-----------|---------|-----|
| **Country** | Mexico only | 64+ countries |
| **Temporal** | Single wave (2014-2015) | 7 waves (1981-2022) |
| **Surveys** | 26 thematic surveys | 1 omnibus survey |
| **Sample per survey** | ~1,200 each | ~1,741 (MEX Wave 7) |
| **Data format** | SPSS `.sav` → JSON dict | CSV (from zip) |
| **Variable naming** | `p1_1`, `p5_2`, etc. | `Q1`, `Q260`, etc. |
| **SES vars** | sexo, edad, escol, Tam_loc | Q260, Q262, Q275, G_TOWNSIZE |
| **Sentinels** | >= 97 or < 0 | Negative codes (-1 to -5) |
| **Weights** | `Pondi2` | `W_WEIGHT`, `PWGHT` |
| **Metadata** | `variable_value_labels`, `column_names_to_labels` | Codebook PDFs + equivalence XLSX |

## 5. Integration Architecture

### 5.1 Data Layer: `wvs_loader.py`

A new module that mirrors `dataset_knowledge.py` for WVS data:

```python
# Core responsibilities:
# 1. Extract Mexico data from Wave 7 CSV (primary) and Time Series (longitudinal)
# 2. Build a wvs_dict structure parallel to los_mex_dict
# 3. Map Q-codes to human-readable labels using equivalence file
# 4. Handle WVS sentinel codes (-1 to -5)
# 5. Cache processed data as JSON (like los_mex_dict.json)

wvs_dict = {
    'enc_dict': {
        'WVS_WAVE7_MEX': {
            'dataframe': {...},  # Mexico Wave 7 data
            'metadata': {
                'variable_value_labels': {...},
                'column_names_to_labels': {...},  # Q-code -> human-readable
            }
        },
        # Optional: longitudinal slices
        'WVS_WAVE6_MEX': {...},
        'WVS_WAVE5_MEX': {...},
    },
    'enc_nom_dict': {
        'WVS_WAVE7_MEX': 'WV7',
        'WVS_WAVE6_MEX': 'WV6',
        ...
    },
    'pregs_dict': {
        'Q1|WV7': 'WVS_WAVE7_MEX|Important in life: Family',
        ...
    },
    'ses_dict': {...},
    'mkdown_tables': {...},
    'df_tables': {...},
}
```

### 5.2 Domain Mapping: WVS ↔ los_mex

Thematic overlap between WVS domains and los_mex surveys:

| WVS Domain (prefix) | los_mex Survey(s) | Bridge potential |
|---------------------|-------------------|-----------------|
| A: Social Values | IDE (Identidad y Valores) | **High** — life priorities, happiness, child qualities |
| B: Environment | MED (Medio Ambiente) | **Medium** — environment vs. economy tradeoff |
| C: Work/Employment | ECO (Economía y Empleo) | **High** — job attitudes, labor market |
| D: Family | FAM (Familia), ENV (Envejecimiento) | **High** — family trust, marriage, children |
| E: Politics | CUL (Cultura Política), FED (Federalismo), JUS (Justicia) | **Very high** — trust in institutions, democracy, political participation |
| F: Religion | REL (Religión) | **Very high** — religious practice, secularization |
| G: National Identity | IDE (Identidad), GLO (Globalización), MIG (Migración) | **High** — national pride, immigration attitudes |
| H: Security | SEG (Seguridad Pública), COR (Corrupción) | **High** — neighborhood safety, crime |
| I: Science & Tech | CIE (Ciencia y Tecnología), SOC (Sociedad de la Información) | **Medium** — science attitudes |

### 5.3 SES Bridge: `wvs_ses_bridge.py`

A new module extending the existing bridge framework to connect WVS ↔ los_mex:

```
WVS (Mexico, Wave 7, 2018)     los_mex (26 surveys, 2014-2015)
         \                           /
          \                         /
           Shared SES space
     [sex, age, education, town_size]
              |
     SES-mediated γ estimation
     (DoublyRobustBridgeEstimator)
```

**SES variable harmonization:**

| Bridge var | los_mex source | WVS source | Harmonization |
|-----------|---------------|------------|---------------|
| sexo | `sexo` (1=M, 2=F) | `Q260` (1=M, 2=F) | Direct match |
| edad | `edad` (7 bins: 0-18...65+) | `Q262` (continuous) | Bin Q262 into same 7 groups |
| escol | `escol` (1-5 ordinal) | `Q275` (0-8 ISCED) | Remap ISCED 0-8 → 5-level scale |
| Tam_loc | `Tam_loc` (1-4) | `G_TOWNSIZE` (1-8) | Collapse 8-level → 4-level |

**Key design decisions:**
- Reuse `DoublyRobustBridgeEstimator` from `ses_regression.py` — it already handles the SES bridge mechanics
- Add a `SESHarmonizer` class that maps WVS SES variables to the los_mex encoding before passing to the estimator
- The temporal gap (2014-2015 vs 2018) is a known limitation but acceptable for SES-structural relationships

### 5.4 Cross-Dataset Bridge Types

Three bridge directions become possible:

1. **WVS ↔ los_mex (cross-survey, same country)**: "Does WVS trust-in-government (E069) co-vary with los_mex political culture items, mediated by SES?" — This is the primary use case.

2. **WVS cross-country (same survey, different countries)**: "How does Mexico compare to Argentina on family values (D-prefix) controlling for SES?" — Enabled naturally by WVS multi-country structure.

3. **WVS longitudinal (same country, different waves)**: "How have Mexican attitudes toward democracy changed across waves 1-7, controlling for SES composition shifts?" — Enabled by time-series dataset.

### 5.5 Agent Integration

Extend `agent.py` / `analytical_essay.py` to recognize WVS as an available dataset:

```python
# In dataset_knowledge.py or a new wvs_knowledge.py:
# 1. Register WVS surveys alongside los_mex in enc_nom_dict
# 2. Add WVS questions to pregs_dict for semantic search
# 3. Update variable_selector.py ChromaDB embeddings to include WVS items
# 4. Add WVS domain mappings to survey_kg.py knowledge graph
```

### 5.6 Knowledge Graph Extension (`survey_kg.py`)

Add WVS domains as new nodes in the knowledge graph, with cross-links to los_mex domains:

```
WVS_Politics (E-prefix)  ←→  CUL (Cultura Política)
WVS_Religion (F-prefix)  ←→  REL (Religión)
WVS_Family (D-prefix)    ←→  FAM (Familia)
WVS_Security (H-prefix)  ←→  SEG (Seguridad Pública)
...
```

## 6. Implementation Plan

### Phase 1: Data Ingestion (Foundation)

1. **`wvs_loader.py`** — Load, filter (Mexico), clean sentinels, build `wvs_dict`
2. **`wvs_metadata.py`** — Parse equivalence XLSX → variable labels, domain tags
3. **Cache** — Save processed Mexico data as `data/wvs/wvs_mex_dict.json`
4. **Tests** — Unit tests for loader, sentinel handling, label resolution

### Phase 2: SES Bridge

5. **`SESHarmonizer`** class — Map WVS SES vars → los_mex encoding
6. **Cross-dataset sweep** — Run `DoublyRobustBridgeEstimator` on WVS×los_mex pairs
7. **Validation** — Compare intra-WVS γ estimates with known WVS cross-tab results
8. **Tests** — Unit tests for harmonizer, bridge estimation

### Phase 3: Agent Integration

9. **Update `dataset_knowledge.py`** — Register WVS alongside los_mex
10. **Update `variable_selector.py`** — Add WVS items to ChromaDB
11. **Update `survey_kg.py`** — Add WVS domain nodes and cross-links
12. **Update `analytical_essay.py`** — Handle WVS in essay generation pipeline

### Phase 4: Cross-Country & Longitudinal (Stretch)

13. **Multi-country loader** — Extend `wvs_loader.py` for non-Mexico data
14. **Cross-country bridge** — Compare Mexico vs. other Latin American countries
15. **Longitudinal analysis** — Track Mexico attitude shifts across waves 1-7

## 7. Technical Considerations

### 7.1 Data Size

- Wave 7 Mexico: 1,741 rows × 613 columns — trivially small, fits in memory
- Time Series Mexico (all waves): 11,714 rows — still small
- Full WVS Time Series: 1.3GB CSV — load on-demand, filter to Mexico immediately

### 7.2 Sentinel Handling

WVS sentinels are negative (`-1` to `-5`) while los_mex uses `>= 97`. The `_is_sentinel()` function in `ses_regression.py` currently checks `>= 97 or < 0`, which **already handles WVS negative sentinels**. However, WVS also uses 0 as a valid value in some variables (e.g., Q275 education: 0 = "Early childhood education"), so `< 0` is the correct WVS sentinel threshold.

### 7.3 Weight Variables

- los_mex: `Pondi2` (population weight)
- WVS: `W_WEIGHT` (survey weight), `PWGHT` (population size weight for cross-country)
- For Mexico-only analysis, use `W_WEIGHT`
- For cross-country, use `PWGHT`

### 7.4 Temporal Gap

los_mex was fielded 2014-2015; WVS Wave 7 Mexico was fielded 2018. This 3-4 year gap is acceptable for SES-structural bridge estimation because:
- SES composition (age/sex/education/urbanization distributions) changes slowly
- The bridge measures SES-mediated co-variation structure, not absolute levels
- WVS Wave 6 (2012 for Mexico) is closer temporally but has different variable coverage

### 7.5 `.gitignore` Updates

Add to `.gitignore`:
```
data/wvs/*.zip
data/wvs/*.csv
data/wvs/wvs_mex_dict.json
```
The zip files are large (138MB total) and the CSV data should be generated locally.

## 8. Extending the Bridge: Time, Geography, and Anchor Questions

The existing los_mex SES bridge estimates γ (Goodman-Kruskal gamma) measuring monotonic SES-mediated co-variation between attitude variables from different surveys. WVS introduces two new dimensions — **time** and **geography** — plus **anchor questions** that can validate and strengthen the bridge.

### 8.1 The Time Dimension

#### What WVS adds

los_mex is a single cross-section (2014-2015). WVS provides **7 waves spanning 1981-2022** for Mexico, with 121 variables measured identically across all waves and 218 variables across waves 5-7 (2005-2022). This enables:

**Core longitudinal variables available in all 7 Mexico waves (20 substantive):**

| Variable | Description | Domain |
|----------|-------------|--------|
| A008 | Feeling of happiness | Social Values |
| A029-A042 | Child qualities (independence, hard work, responsibility, imagination, tolerance, thrift, determination, religious faith, unselfishness, obedience) | Social Values |
| E003-E004 | Personal aims: first/second choice | Politics |
| E023 | Interest in politics | Politics |
| E025-E027 | Political action: petition, boycotts, demonstrations | Politics |
| E069_01-E069_07 | Confidence in: churches, armed forces, press, unions, police, parliament | Politics/Trust |
| F028, F034 | Religious attendance, religious person | Religion |
| G006 | National pride | Identity |

**Bridge extension: temporal γ trajectories.** For each WVS variable pair, compute γ within each wave using the same DR estimator. This yields γ(t) — a time series of SES-mediated association strength. Questions the temporal bridge can answer:

1. "Has the SES-structuring of political trust strengthened or weakened since 1981?"
2. "Is the SES gradient in religiosity steepening (secularization is SES-driven) or flattening (secularization is universal)?"
3. "Did the 2008 financial crisis change SES-mediated attitudes toward work?"

**Implementation:** No new estimator needed. Run `DoublyRobustBridgeEstimator` on (variable_A_wave_i, variable_B_wave_j) pairs within WVS Mexico data. The SES harmonization is trivial since WVS uses the same SES coding across waves (X001=sex, X003=age, X025=education, X049=settlement size).

#### What the temporal bridge cannot do

- **Causal claims about change**: γ(t₁) ≠ γ(t₂) does not mean SES-mediation changed — it could reflect sampling variation, question-context effects, or real structural change. The n ≈ 1,500 per wave yields CI widths of ~0.2 (same wall as los_mex), so only large shifts (Δγ > 0.3) are detectable.
- **Panel tracking**: WVS is repeated cross-sections, not a panel. No individual-level change.
- **High-frequency dynamics**: 5-10 year gaps between waves miss short-term fluctuations.
- **Bridging WVS time-series to los_mex time-series**: los_mex has only one wave, so the bridge is always WVS(wave_i) ↔ los_mex(2014). The temporal gap varies from 0 years (Wave 6, 2012) to 33 years (Wave 1, 1981). For distant waves, SES composition differences become non-trivial.

### 8.2 The Geographic Dimension

#### WVS Cultural Zones

WVS countries cluster into **cultural zones** on the Inglehart-Welzel cultural map, based on two dimensions:
- **Traditional vs. Secular-Rational values** (y-axis): religion, authority, nationalism
- **Survival vs. Self-Expression values** (x-axis): trust, tolerance, subjective well-being

The cultural zones are:

| Cultural Zone | Wave 7 Countries | n (Wave 7) |
|--------------|------------------|-----------|
| **Latin America** | MEX, ARG, BOL, BRA, CHL, COL, ECU, GTM, NIC, PER, PRI, URY, VEN | ~18,000 |
| **English-speaking** | AUS, CAN, GBR, NZL, USA, NIR | ~12,500 |
| **Protestant Europe** | DEU, NLD | ~3,700 |
| **Catholic Europe** | AND, CYP, GRC | ~3,200 |
| **Orthodox/ex-Communist** | ARM, CZE, KAZ, KGZ, MNG, ROU, RUS, SRB, SVK, TJK, UKR, UZB | ~15,600 |
| **Confucian** | CHN, HKG, JPN, KOR, MAC, SGP, TWN, VNM | ~14,700 |
| **South/Southeast Asian** | BGD, IDN, IND, MMR, MYS, PAK, PHL, THA | ~14,300 |
| **African-Islamic** | EGY, ETH, IRN, IRQ, JOR, KEN, LBN, LBY, MAR, MDV, NGA, TUN, TUR, ZWE | ~16,800 |

Mexico sits in the **Latin American** zone — moderate traditional values, moderate survival-to-self-expression values.

#### Bridge extension: cross-country γ comparison

For any WVS variable pair, compute γ within each country using the same DR estimator (with that country's SES distribution). This yields γ_country — a cross-national profile of SES-mediated association. Questions the geographic bridge can answer:

1. "Is the SES-structuring of trust in institutions uniquely Mexican, or does it appear across Latin America?"
2. "How does Mexico's SES gradient in religiosity compare to Brazil, Argentina, and the Catholic European average?"
3. "Are the attitudes most SES-structured in Mexico also the most SES-structured globally, or are some uniquely Mexican?"

**SES harmonization across countries:** WVS SES variables (X001, X003, X025, X049) are already harmonized by design — they use the same codes in all countries. However:
- **Education (X025/Q275)**: ISCED levels mean different things in different educational systems. Use recoded 3-group (X025R/Q275R) for cross-country comparability.
- **Income (X047/Q288)**: Country-specific scales. Use recoded 3-group (X047R/Q288R) or within-country percentile normalization.
- **Settlement size**: Harmonized 1-8 scale across countries, but absolute sizes differ (a "large city" in Bolivia ≠ in Japan).

#### What the geographic bridge cannot do

- **Direct WVS(country_A) ↔ los_mex bridge**: los_mex is Mexico-only. The cross-country bridge works entirely within WVS. It provides *context* for los_mex findings ("los_mex trust patterns are typical/atypical for Latin America") but doesn't create new WVS-los_mex variable pairs.
- **Causal country comparisons**: γ_Mexico ≠ γ_Argentina does not imply the countries differ in causal SES mechanisms — it could reflect different response distributions, scale interpretation, or genuine structural differences.
- **Small-country estimates**: Countries with n < 1,000 (AND=1,004, NIR=447) will have very wide CIs. The n ≈ 1,200 uncertainty wall applies per country.
- **Within-country regional variation**: WVS does not sample at sub-national levels large enough for regional γ estimates (Mexico has n=1,741 total, too small to split by state).

### 8.3 Anchor Questions: Bridging via Shared Content

#### The key insight

Some los_mex questions have **near-identical or semantically equivalent phrasing** to WVS questions. These are "anchor questions" — items that appear in both datasets and can be used to:

1. **Validate the SES bridge**: If anchor Q_A appears in both WVS and los_mex, the marginal distribution P(Q_A|SES) should be similar in both datasets (after temporal adjustment). Discrepancies indicate bridge calibration problems.
2. **Strengthen cross-dataset estimation**: Anchor questions provide *direct* cross-tabulation between datasets (same question, same country, similar time), avoiding the need for SES-mediated simulation.
3. **Create composite scales**: Combine an anchor question's WVS longitudinal trajectory with its los_mex cross-tabulation profile.

#### Candidate Anchor Pairs

Based on thematic analysis, the most promising anchors to find:

| WVS Variable | WVS Question | Likely los_mex Match | los_mex Survey |
|-------------|-------------|---------------------|---------------|
| G006 | "How proud of nationality" | p5\|CUL: "¿Qué tan orgulloso se siente de ser mexicano?" | CUL |
| E069_06 | "Confidence: The Police" | p15_X\|SEG / p16_X\|COR: trust in police items | SEG, COR |
| E069_07 | "Confidence: Parliament" | p16_X\|CUL: trust in congress items | CUL |
| E069_11 | "Confidence: The Government" | p16_X\|CUL: trust in government items | CUL |
| E069_12 | "Confidence: Political Parties" | p16_X\|CUL: trust in parties | CUL |
| A008 | "Feeling of happiness" | p8\|FAM: childhood happiness / p-items in IDE | FAM, IDE |
| F028 | "How often attend religious services" | p-items\|REL: religious practice frequency | REL |
| F034 | "Religious person" | p-items\|REL: self-identification | REL |
| H001 | "Secure in neighborhood" | p3\|SEG: "¿qué tan seguro se siente?" | SEG |
| D059 | "Men make better political leaders" | p-items\|GEN: gender equality in politics | GEN |
| A170 | "Satisfaction with your life" | p-items in multiple surveys | IDE, FAM |
| E023 | "Interest in politics" | p-items\|CUL: political interest | CUL |
| B008 | "Environment vs. economic growth" | p2\|MED: environment vs economy priority | MED |

#### Finding Anchors: Semantic Matching Pipeline

The existing `variable_selector.py` infrastructure is perfectly suited for anchor detection:

```
Step 1: Embed all WVS question texts (English + Spanish translation)
        into the same ChromaDB collection used for los_mex

Step 2: For each WVS question, query ChromaDB for nearest los_mex neighbors
        using cosine similarity on OpenAI embeddings

Step 3: LLM-grade the top candidates (0-3 relevance scale)
        - Grade 3: Near-identical phrasing and response scale
        - Grade 2: Same concept, different phrasing or scale
        - Grade 1: Related topic, different angle
        - Grade 0: Unrelated

Step 4: Manual review of Grade 3 and Grade 2 pairs
        Verify response scale compatibility (Likert 1-4 vs 1-5, etc.)
```

**Language consideration**: los_mex questions are in Spanish; WVS has both English master text and a Spanish Mexico questionnaire (`WVS7_Questionnaire_Mexico_2018_Spanish.pdf`). Use the Spanish WVS text for embedding-based matching against los_mex Spanish text for highest accuracy.

#### Anchor Question Usage in the Bridge

**Type 1 — Direct Validation Anchors (Grade 3):**
If WVS Q and los_mex Q are near-identical:
- Compare P(Q|SES) in WVS vs. los_mex directly. They should agree (up to the 3-year temporal gap).
- Any systematic discrepancy flags a calibration issue: sampling bias, question-order effects, or SES-encoding errors.
- These anchors can be used to compute a **calibration correction** for the SES bridge, adjusting for systematic dataset-level shifts.

**Type 2 — Thematic Anchors (Grade 2):**
If WVS Q and los_mex Q measure the same concept differently:
- Run the SES bridge normally (DR estimator).
- Compare γ_bridge with the direct cross-tab correlation available from the anchor. The discrepancy quantifies bridge estimation error for that domain.
- If γ_bridge ≈ r_anchor, the bridge is well-calibrated for that domain.

**Type 3 — Longitudinal Extension via Anchors:**
If a Grade 3 anchor exists in both WVS (across multiple waves) and los_mex:
- WVS provides the *temporal trajectory* of P(Q|SES) from 1981-2022
- los_mex provides *deeper cross-tabulation* with the 25 other los_mex surveys at a single time point (2014-2015)
- Together: "How the attitude tracked over time (WVS trajectory) and what it correlated with at one snapshot (los_mex bridge)"

#### What anchors cannot do

- **Eliminate bridge uncertainty**: Even with anchors, the SES bridge γ estimates retain the n ≈ 1,200 sampling noise floor (CI width ~0.2). Anchors help detect *bias*, not reduce *variance*.
- **Replace the bridge for non-anchor questions**: Most los_mex questions (4,493 items across 26 surveys) will NOT have WVS anchors. The bridge remains necessary for the vast majority of cross-dataset pairs.
- **Guarantee response-scale equivalence**: "How proud are you of being Mexican?" on a 1-4 scale vs. 1-5 scale produces different distributions even for identical populations. Scale harmonization is required.

### 8.4 The Traveling Bridge: γ as a Surface

#### Core idea

The bridge is not tied to a single context. The DR estimator fits P(Y|SES) and P(Z|SES) *locally* in whatever dataset it receives, then simulates a joint table over a reference SES population. Nothing about the mechanics is Mexico-specific or time-specific. The bridge can "travel" to any context where the same (or equivalent) variables and SES predictors exist.

This means γ is not a single number — it is a **surface**:

```
γ(variable_pair, country, wave, SES_reference) → [-1, +1]
```

Each point on this surface answers: "In this country, at this time, how much does shared SES drive monotonic co-variation between these two attitudes?"

#### What varies when the bridge travels

Two things change across contexts:

**1. The P(Y|SES) relationship.** Education may predict trust in institutions strongly in Mexico (high institutional inequality) but weakly in Sweden (low institutional inequality). This is *substantive* — it means SES structures attitudes differently across societies. Comparing γ_MEX vs γ_SWE for the same variable pair tells you exactly this.

**2. The SES reference population.** Mexico's SES distribution (younger, less educated, more concentrated in large cities) differs from Japan's. This matters because γ is computed over a simulated population. The choice of reference population determines what the comparison means:

| Reference population | What γ measures | Use case |
|---------------------|----------------|----------|
| **Local** (each context's own SES) | "How much does SES structure these attitudes *in this society as it is*?" | Natural comparison: each context on its own terms |
| **Standardized** (fixed across all) | "If the *same* SES population existed everywhere, how would SES structure attitudes?" | Isolates the P(Y\|SES) relationship from SES composition |
| **Pooled** (merged from multiple contexts) | Compromise — smooths composition differences | Reduces variance when comparing similar contexts |

For the temporal dimension, the same logic applies. Mexico in 1981 was younger, less educated, more rural. Using local SES per wave means γ(1981) and γ(2018) reflect both changes in P(Y|SES) *and* changes in SES composition. Using a standardized reference (e.g., Mexico 2018 SES distribution applied to all waves) isolates structural change from compositional change.

#### Concrete examples

```
γ(trust_police × religiosity, MEX, wave7, local)      = 0.35  ← "In Mexico 2018, SES strongly structures this pair"
γ(trust_police × religiosity, ARG, wave7, local)      = 0.12  ← "In Argentina 2018, SES barely structures it"
γ(trust_police × religiosity, MEX, wave3, local)      = 0.41  ← "In Mexico 1995, SES structured it even more"
γ(trust_police × religiosity, MEX, wave7, LatAm_std)  = 0.30  ← "Standardized to Latin American SES composition"
γ(trust_police × religiosity, LatAm_pooled, wave7, _) = 0.22  ← "Regional pooled average, tighter CI"
```

#### Variance management for the γ surface

With n ≈ 1,200-1,800 per wave per country, each individual γ has CI width ~0.2. This is the wall. But the surface structure offers strategies unavailable to single-point estimation:

**Pooling within zones or adjacent waves.** If γ is assumed similar across Latin American countries (a testable hypothesis), pool ARG+BRA+CHL+COL+MEX+PER into n ≈ 8,000 → CI width ~0.08. Same logic temporally: pool waves 5+6+7 (2005-2022) into n ≈ 5,300 for a "recent era" estimate vs. waves 1+2+3 (1981-1998) for an "early era" estimate. This is a bias-variance tradeoff — pooling assumes homogeneity within the pool, but that assumption is itself testable by comparing unpooled γ values within the pool.

**Hierarchical/shrinkage estimation.** Estimate γ per country independently, then shrink toward the cultural-zone mean (James-Stein style — already implemented in `MRPBridgeEstimator`). Countries with small n get pulled toward the group mean; countries with large n retain their own estimate. This is the natural Bayesian approach and yields tighter CIs without assuming full homogeneity.

**Difference-in-γ and γ-profile ranking.** Instead of interpreting absolute γ values (noisy), compare Δγ = γ_country_A - γ_country_B for the *same* variable pair. If both share similar noise structure, some variance cancels. Even better: rank variable pairs by γ within each country and compare rankings (Spearman ρ on the γ-profiles). This is robust to scale differences and answers: "Do the same variable pairs that are most SES-structured in Mexico also tend to be most SES-structured in Argentina?"

#### What the γ surface reveals

The surface enables questions that single-point estimation cannot:

- "For trust-in-police × religiosity, is the γ surface **flat** (universal SES-structuring), **tilted by region** (cultural-zone effect), **tilted by time** (modernization effect), or **both**?"
- "Which variable pairs have the **steepest temporal gradient** in γ? Those are the attitudes whose SES-structuring is changing fastest."
- "Which cultural zones show the most **within-zone heterogeneity** in γ? Those are zones where country-level factors dominate over cultural-zone membership."
- "Do the γ rankings across variable pairs **correlate** between Mexico and Argentina? High correlation means SES structures attitudes similarly in both countries, even if absolute γ levels differ."

#### Combined architecture with anchor validation

```
                        GEOGRAPHY (66 countries)
                       /
                      /  γ_surface(country_i, wave_j)
                     /   per variable pair
                    /
   los_mex ←——SES BRIDGE——→ WVS_MEX_Wave7
     (2014)    γ(SES)         (2018)
                    \
                     \  γ_surface(MEX, wave_1...7)
                      \ per variable pair
                       \
                        TIME (1981-2022)

   ANCHOR QUESTIONS validate the bridge at contact points:
   - Where same Q appears in both datasets → direct P(Q|SES) comparison
   - Calibration correction for systematic dataset-level shifts
   - Longitudinal fusion: WVS trajectory + los_mex cross-domain depth
```

The bridge at the center produces γ for a single (variable_pair, context). The extensions produce a surface over contexts. The anchors validate both.

#### What the traveling bridge still cannot do

- **Cross-context los_mex bridging**: los_mex exists only in Mexico 2014. The bridge can travel to WVS_ARG or WVS_MEX_1995, but it cannot bridge WVS_ARG ↔ los_mex — that would require simulating "what if Argentines answered Mexican survey questions," which is counterfactual rather than SES-mediated.
- **Causal attribution of Δγ**: γ_MEX(2018) > γ_MEX(1995) could mean SES-structuring genuinely strengthened, or it could be an artifact of changing SES composition, question-context evolution, or sampling. The standardized-reference approach helps isolate the first, but cannot fully separate structural change from compositional change without stronger assumptions.
- **Beating the per-cell wall**: Pooling helps overall n, but the real bottleneck is cell counts in the SES×attitude cross-tab. If a particular SES stratum (e.g., highly-educated rural women) is rare in one country, pooling across countries helps only if that stratum exists elsewhere with sufficient frequency.

### 8.5 Limitations of the Extended Bridge

| Limitation | Cause | Mitigation |
|-----------|-------|-----------|
| Sampling noise floor | n ≈ 1,200-2,000 per wave/country | Accept CI width ~0.2; pool within zones/eras; shrinkage estimation |
| γ detects monotonic only | Goodman-Kruskal definition | NMI supplement detects non-monotonic; already implemented |
| Temporal gap los_mex↔WVS | 3-year fieldwork gap | Use Wave 6 (2012) as secondary anchor; validate with Wave 7 |
| SES encoding differences | Different scales/binning | SESHarmonizer class; use recoded (coarser) variables |
| Question context effects | Different survey instruments | Anchor validation; flag anchor discrepancies |
| Cultural zone boundaries | Inglehart-Welzel zones are approximate | Treat zones as fuzzy clusters; compare individual countries |
| Missing variables in early waves | Not all questions asked in all waves | 121 vars across all waves; 218 in waves 5-7 |
| Cross-country education semantics | ISCED levels differ in practice | Use 3-group recoding (low/medium/high) for comparability |
| Compositional vs. structural Δγ | Local reference confounds both | Standardized-reference γ isolates structural change |
| γ-profile comparison validity | Ranking assumes common noise structure | Bootstrap the rankings; report rank-stability intervals |

## 9. Revised Implementation Plan

### Phase 1: Data Ingestion (Foundation)

1. **`wvs_loader.py`** — Load, filter (Mexico + multi-country), clean sentinels, build `wvs_dict`
2. **`wvs_metadata.py`** — Parse equivalence XLSX → variable labels, domain tags, wave-mapping
3. **Cultural zone registry** — Assign WVS countries to Inglehart-Welzel zones; store as config
4. **Cache** — Save processed data as `data/wvs/wvs_mex_dict.json` (Mexico) + per-zone caches
5. **Tests** — Unit tests for loader, sentinel handling, label resolution, zone assignment

### Phase 2: Anchor Question Discovery

6. **Extract WVS question texts** — From codebook + Spanish questionnaire PDF
7. **Embed WVS questions** — Into ChromaDB alongside los_mex questions
8. **Semantic matching sweep** — For each WVS Q, find nearest los_mex neighbors
9. **LLM grading** — Grade 0-3 relevance + response-scale compatibility
10. **Anchor registry** — Curated list of Grade 2-3 anchor pairs with scale harmonization notes

### Phase 3: SES Bridge & γ Surface (Core)

11. **`SESHarmonizer`** class — Map WVS SES vars → los_mex encoding; support local/standardized/pooled reference populations
12. **WVS×los_mex sweep** — Run `DoublyRobustBridgeEstimator` on cross-dataset pairs (Mexico, Wave 7)
13. **Anchor validation** — Compare bridge γ with direct anchor cross-tabs; quantify calibration error
14. **Temporal sweep** — γ(variable_pair, MEX, wave_i, local) for all 7 waves; γ(variable_pair, MEX, wave_i, standardized) with fixed reference
15. **Geographic sweep** — γ(variable_pair, country_j, wave7, local) for Latin American countries; extend to comparison zones
16. **Pooled/shrinkage estimates** — Zone-pooled γ and James-Stein shrinkage γ for tighter CIs
17. **γ-profile rankings** — Rank variable pairs by γ within each country; compute cross-country Spearman ρ on rankings
18. **Tests** — Unit tests for harmonizer, bridge estimation, anchor validation, pooling, shrinkage

### Phase 4: Surface Analysis & Interpretation

19. **Temporal gradients** — Detect variable pairs with steepest Δγ across waves; test significance via bootstrap
20. **Geographic gradients** — Identify variable pairs where γ varies most across cultural zones
21. **Compositional vs. structural decomposition** — Compare local-reference γ with standardized-reference γ; attribute Δγ to SES composition change vs. structural P(Y|SES) change
22. **Anchor longitudinal fusion** — For anchor questions: WVS trajectory of P(Q|SES) across waves + los_mex cross-domain depth at 2014

### Phase 5: Agent Integration

23. **Update `dataset_knowledge.py`** — Register WVS alongside los_mex (all waves, multi-country)
24. **Update `variable_selector.py`** — Add WVS items to ChromaDB with anchor cross-links
25. **Update `survey_kg.py`** — Add WVS domain nodes, temporal edges, geographic/zone nodes, anchor edges
26. **Update `analytical_essay.py`** — Handle γ-surface queries; anchor-informed narrative; comparative context (time, geography)

## 10. Expected Outcomes

1. **γ surface**: A queryable surface γ(variable_pair, country, wave, SES_reference) that the navegador agent can slice along any dimension
2. **Temporal trajectories**: γ(t) per variable pair showing how SES-mediated co-variation evolved in Mexico over 40 years, with compositional/structural decomposition
3. **Geographic profiles**: γ per country for key variable pairs, with zone-pooled and shrinkage estimates; γ-profile rankings comparing which attitude pairs are most SES-structured across countries
4. **Anchor-validated calibration**: Quantified bridge accuracy where WVS and los_mex share near-identical questions; calibration correction if systematic discrepancies exist
5. **Variance-managed estimation**: Pooled (n ≈ 8,000 within zones), shrinkage, and Δγ/ranking comparisons that extract signal despite the n ≈ 1,200 per-cell wall
6. **Combined narrative depth**: "Mexican trust in institutions is SES-structured (γ=0.35), has steepened since 1995 (temporal gradient), is typical for Latin America but unusually strong vs. English-speaking countries (geographic profile), and matches the los_mex political culture survey within calibration tolerance (anchor validation). Using a standardized SES reference, 60% of the temporal change is structural rather than compositional."
