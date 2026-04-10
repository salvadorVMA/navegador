"""
NarrativeSynthesizer -- Phase 4 narrative layer for the Graph Traversal Engine.

Converts structured GTE outputs (propagation + projection) into human-readable
analytical narratives. The synthesizer adds ZERO information -- it only
reformats what the engine already computed.

Two modes:
  1. With LLM: sends a structured prompt to an LLM for polished narrative
  2. Without LLM: returns the structured prompt as a template (for testing
     or programmatic consumption)

Caveats are auto-generated from data quality signals: low Fiedler connectivity,
low method agreement, signal attenuation, sparse construct sets, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from graph_traversal_engine.context import WAVE_YEARS
from graph_traversal_engine.propagator import PropagationResult
from graph_traversal_engine.projector import ProjectionResult


# -- Result containers ---------------------------------------------------------

@dataclass
class NarrativeRequest:
    """All structured inputs needed for narrative generation."""
    anchor: str
    anchor_label: str           # Human-readable construct name
    direction: str              # "increasing" / "decreasing"
    context: str                # "Mexico, Wave 7 (2019)"
    zone: str                   # "Latin America"
    network_stats: dict         # fiedler, n_constructs, n_edges
    top_effects: list[dict]     # From consensus ranking
    ses_geometry: dict          # From SES projection
    cross_country: dict         # From spectral neighbors + zone patterns
    temporal: dict              # From temporal trajectory
    caveats: list[str]          # Automatically generated warnings


@dataclass
class GTEOutput:
    """Complete GTE output: structured data + narrative."""
    query_context: dict
    propagation: PropagationResult
    projection: ProjectionResult
    narrative: str
    caveats: list[str]
    metadata: dict


# -- Synthesizer ---------------------------------------------------------------

def _humanize_construct(key: str) -> str:
    """Convert 'gender_role_traditionalism|WVS_D' -> 'Gender Role Traditionalism'."""
    name = key.split("|")[0] if "|" in key else key
    return name.replace("_", " ").title()


class NarrativeSynthesizer:
    """
    Generate narrative text from structured GTE outputs.

    Args:
        llm_callable: Optional async/sync function(prompt: str) -> str.
            If None, returns the structured prompt for testing.
    """

    def __init__(self, llm_callable: Optional[Callable] = None) -> None:
        self._llm = llm_callable

    def synthesize(
        self,
        propagation: PropagationResult,
        projection: ProjectionResult,
        country: str,
        wave: int,
        zone: str = "",
    ) -> tuple[str, list[str]]:
        """
        Generate narrative and caveats from structured GTE outputs.

        Returns: (narrative_text, caveats_list)
        """
        request = self._build_request(propagation, projection, country, wave, zone)
        prompt = self._build_prompt(request)

        if self._llm is not None:
            narrative = self._llm(prompt)
        else:
            narrative = prompt

        return narrative, request.caveats

    def _build_request(
        self,
        propagation: PropagationResult,
        projection: ProjectionResult,
        country: str,
        wave: int,
        zone: str,
    ) -> NarrativeRequest:
        """Assemble all data into a NarrativeRequest."""
        anchor = propagation.anchor
        direction = "decreasing" if propagation.anchor_direction < 0 else "increasing"
        year = WAVE_YEARS.get(wave, wave)
        context_str = f"{country}, Wave {wave} ({year})"

        # Network stats
        fiedler = 0.0
        if projection.temporal and wave in projection.temporal.fiedler_trajectory:
            fiedler = projection.temporal.fiedler_trajectory[wave]

        network_stats = {
            "fiedler_value": fiedler,
            "n_present_constructs": propagation.n_present,
            "method_agreement": propagation.method_agreement,
        }

        # Top effects
        top_effects = []
        for eff in propagation.consensus[:10]:
            top_effects.append({
                "construct": eff.construct,
                "label": _humanize_construct(eff.construct),
                "direction": "+" if eff.direction > 0 else "-",
                "agreement": f"{eff.agreement_score:.0%}",
                "confidence": eff.confidence,
                "bp_rank": eff.bp_rank,
                "ppr_rank": eff.ppr_rank,
                "spectral_rank": eff.spectral_rank,
            })

        # SES geometry
        ses_geometry = {}
        if projection.ses_projection:
            sp = projection.ses_projection
            ses_geometry = {
                "mean_ses_vector": sp.mean_ses_vector,
                "dominant_dimension": sp.dominant_dimension,
                "dominant_direction": sp.dominant_direction,
                "within_dimension_pct": f"{sp.within_dimension:.0%}",
                "cross_dimension_effects": [
                    _humanize_construct(c) for c in sp.cross_dimension_effects
                ],
            }

        # Cross-country
        cross_country = {
            "spectral_neighbors": [
                {"country": c, "distance": round(d, 4),
                 "confidence": projection.transfer_confidence.get(c, 0)}
                for c, d in projection.spectral_neighbors[:5]
            ],
            "n_zones": len(projection.zone_patterns),
            "source_zone": zone,
        }

        # Temporal
        temporal = {}
        if projection.temporal:
            t = projection.temporal
            temporal = {
                "waves": t.waves_available,
                "fiedler_trend": t.fiedler_trend,
                "fiedler_slope": t.fiedler_slope,
                "mediator_stability": t.mediator_stability,
            }

        # Auto-generate caveats
        caveats = self._generate_caveats(
            propagation, projection, fiedler, country, wave
        )

        return NarrativeRequest(
            anchor=anchor,
            anchor_label=_humanize_construct(anchor),
            direction=direction,
            context=context_str,
            zone=zone,
            network_stats=network_stats,
            top_effects=top_effects,
            ses_geometry=ses_geometry,
            cross_country=cross_country,
            temporal=temporal,
            caveats=caveats,
        )

    def _generate_caveats(
        self,
        propagation: PropagationResult,
        projection: ProjectionResult,
        fiedler: float,
        country: str,
        wave: int,
    ) -> list[str]:
        """Auto-generate caveats based on data quality signals."""
        caveats = []

        # Fundamental caveat (always present)
        caveats.append(
            "These are associative patterns conditioned on SES, not causal claims. "
            "gamma measures monotonic covariation mediated by education, urbanization, "
            "gender, and age -- not direct influence between attitudes."
        )

        # Low connectivity
        if fiedler < 0.5:
            caveats.append(
                f"Low network connectivity (Fiedler = {fiedler:.2f}). "
                "Propagation results are less reliable in loosely connected networks."
            )

        # Low method agreement
        agreement = propagation.method_agreement
        if agreement:
            min_agree = min(agreement.values())
            if min_agree < 0.5:
                caveats.append(
                    f"Low cross-method agreement ({min(agreement, key=agreement.get)}: "
                    f"r = {min_agree:.2f}). Methods disagree on propagation rankings."
                )

        # Small construct set (early waves)
        if propagation.n_present < 30:
            caveats.append(
                f"Only {propagation.n_present} constructs available in this context "
                f"(Wave {wave}). Earlier waves have fewer survey items; results may "
                "not capture the full attitude network."
            )

        # No BP data
        if not propagation.bp_effects:
            caveats.append(
                "Belief propagation data not available for this context. "
                "Consensus is based on PPR and spectral methods only."
            )

        # Temporal instability
        if projection.temporal and projection.temporal.fiedler_trend == "loosening":
            caveats.append(
                f"{country}'s network connectivity is loosening over time "
                f"(slope = {projection.temporal.fiedler_slope:.4f}). "
                "Current patterns may be less stable than in tightening networks."
            )

        return caveats

    def _build_prompt(self, req: NarrativeRequest) -> str:
        """Construct the LLM prompt from structured data."""
        lines = []
        lines.append("# Graph Traversal Engine Analysis")
        lines.append("")
        lines.append(f"## Context: {req.context}")
        lines.append(f"**Query**: What happens when **{req.anchor_label}** is {req.direction}?")
        lines.append(f"**Cultural zone**: {req.zone or 'unknown'}")
        lines.append("")

        # Network stats
        lines.append("## Network Structure")
        stats = req.network_stats
        lines.append(f"- Fiedler connectivity: {stats['fiedler_value']:.3f}")
        lines.append(f"- Constructs: {stats['n_present_constructs']}")
        if stats.get("method_agreement"):
            for pair, corr in stats["method_agreement"].items():
                lines.append(f"- Method agreement ({pair}): r = {corr}")
        lines.append("")

        # Top effects
        lines.append("## Predicted Co-Movement (Top 10)")
        lines.append("")
        lines.append("| Rank | Construct | Dir | Agreement | Confidence | BP | PPR | Spectral |")
        lines.append("|------|-----------|-----|-----------|------------|----|----|----------|")
        for i, eff in enumerate(req.top_effects, 1):
            lines.append(
                f"| {i} | {eff['label']} | {eff['direction']} | "
                f"{eff['agreement']} | {eff['confidence']} | "
                f"{eff.get('bp_rank', '-')} | {eff.get('ppr_rank', '-')} | "
                f"{eff.get('spectral_rank', '-')} |"
            )
        lines.append("")

        # SES geometry
        if req.ses_geometry:
            lines.append("## SES Geometry of Effects")
            sg = req.ses_geometry
            lines.append(f"- Dominant SES dimension: **{sg['dominant_dimension']}** ({sg['dominant_direction']})")
            lines.append(f"- Within-dimension effects: {sg['within_dimension_pct']}")
            if sg.get("cross_dimension_effects"):
                lines.append(f"- Cross-dimension effects: {', '.join(sg['cross_dimension_effects'][:3])}")
            lines.append("")

        # Cross-country
        if req.cross_country.get("spectral_neighbors"):
            lines.append("## Cross-Country Context")
            lines.append("")
            lines.append("| Country | Spectral Distance | Transfer Confidence |")
            lines.append("|---------|-------------------|---------------------|")
            for nbr in req.cross_country["spectral_neighbors"]:
                lines.append(
                    f"| {nbr['country']} | {nbr['distance']:.4f} | {nbr['confidence']:.3f} |"
                )
            lines.append("")

        # Temporal
        if req.temporal:
            lines.append("## Temporal Context")
            t = req.temporal
            lines.append(f"- Waves available: {t['waves']}")
            lines.append(f"- Fiedler trend: **{t['fiedler_trend']}** (slope = {t['fiedler_slope']})")
            lines.append(f"- Mediator stability: {t['mediator_stability']}")
            lines.append("")

        # Caveats
        if req.caveats:
            lines.append("## Caveats")
            for caveat in req.caveats:
                lines.append(f"- {caveat}")
            lines.append("")

        return "\n".join(lines)
