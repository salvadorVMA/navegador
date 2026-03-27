# Post-SES-Realignment Analysis — Los Mex

## Realignment Changes

1. **Tam_loc**: reversed to 1=rural → 4=urban (matching WVS)
2. **Escol**: WVS ISCED boundaries realigned to Mexican levels
3. **Edad**: continuous numeric age (no 7-bin discretization)

## Network Descriptives

| Metric | Value |
|--------|-------|
| Significant edges | 879 |
| Sign split | 444 pos / 435 neg (51%/49%) |
| Med \|γ\| | 0.0300 |
| Mean \|γ\| | 0.0423 |
| Max \|γ\| | 0.2886 |
| Constructs connected | 67 |

## Bipartite Structure

| Metric | Value |
|--------|-------|
| Triangles | 7376 |
| Balanced | 7376 (100.0%) |
| Frustrated | 0 (0.0%) |

## SES Dominance per Bridge

| SES Dimension | Count | % | Med \|γ\| |
|--------------|-------|---|----------|
| Education (escol) | 643 | 73.2% | 0.0330 |
| Urbanization (Tam_loc) | 186 | 21.2% | 0.0175 |
| Gender (sexo) | 29 | 3.3% | 0.0443 |
| Age/Cohort (edad) | 21 | 2.4% | 0.0291 |

## Top 10 Bridges by |γ|

| γ | Dominant SES | Construct A | Construct B |
|---|------------|-------------|-------------|
| +0.2886 | escol | CIE|household_science_cultural_capital | EDU|digital_and_cultural_capital |
| +0.2775 | escol | EDU|digital_and_cultural_capital | HAB|structural_housing_quality |
| +0.2675 | escol | EDU|digital_and_cultural_capital | HAB|household_asset_endowment |
| +0.2535 | escol | CIE|household_science_cultural_capital | HAB|household_asset_endowment |
| +0.2327 | escol | CIE|household_science_cultural_capital | HAB|structural_housing_quality |
| +0.2179 | escol | CIE|household_science_cultural_capital | DEP|cultural_socialization_in_childhood |
| +0.2108 | escol | CIE|science_technology_interest_engagement | EDU|digital_and_cultural_capital |
| +0.2008 | escol | CIE|household_science_cultural_capital | DEP|reading_engagement_and_literacy |
| +0.1994 | escol | DEP|cultural_socialization_in_childhood | EDU|digital_and_cultural_capital |
| +0.1959 | escol | DEP|reading_engagement_and_literacy | EDU|digital_and_cultural_capital |

## Output Files

- `domain_circle_network_post_realignment.png` — standard network (sign-colored)
- `domain_circle_network_ses_colored.png` — network colored by dominant SES
- `post_realignment_report.md` — this report
