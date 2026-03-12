"""WVS anchor question discovery: find los_mex questions semantically equivalent to WVS questions.

Anchor questions are items that appear in both WVS and los_mex (near-identically
or thematically). They serve three purposes:
  1. Bridge validation — compare P(Q|SES) directly across datasets
  2. Calibration — quantify systematic dataset-level bias
  3. Longitudinal fusion — WVS temporal trajectory + los_mex cross-domain depth

Pipeline (§9 Phase 2 of WVS Integration Plan)
----------------------------------------------
  Step 1  Extract WVS question texts from equivalences (English titles)
  Step 2  For each WVS Wave 7 question, query los_mex ChromaDB for top-k neighbours
  Step 3  LLM grades each candidate 0–3 for relevance and scale compatibility
  Step 4  Save anchor registry to data/wvs/anchor_registry.json

Grading scale
-------------
  3  Near-identical phrasing and response scale  → direct validation anchor
  2  Same concept, different phrasing or scale   → thematic anchor
  1  Related topic, different angle              → weak anchor (informative only)
  0  Unrelated                                   → discard

Usage
-----
    from wvs_anchor_discovery import WVSAnchorDiscovery, load_anchor_registry

    # Build registry (requires OpenAI API key + ChromaDB with los_mex)
    discovery = WVSAnchorDiscovery(db_f1=db_f1, llm=llm)
    registry = discovery.build_registry(equivalences, wave=7, n_candidates=5)
    discovery.save(registry, Path('data/wvs/anchor_registry.json'))

    # Load pre-built registry
    registry = load_anchor_registry(Path('data/wvs/anchor_registry.json'))
    grade3 = {k: v for k, v in registry.items() if v.get('best_grade', 0) >= 3}
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Registry data model
# ---------------------------------------------------------------------------

class AnchorCandidate(BaseModel):
    """One los_mex candidate for a WVS question."""
    los_mex_id: str            # e.g. 'p16_3|CUL'
    los_mex_survey: str        # e.g. 'CULTURA_POLITICA'
    los_mex_text: str          # full question text
    cosine_similarity: float   # ChromaDB distance converted to similarity
    grade: int                 # 0–3
    grade_justification: str
    scale_compatible: bool     # True if response scales are directly comparable
    scale_notes: str           # e.g. 'WVS 1-4, los_mex 1-4'


class AnchorEntry(BaseModel):
    """Anchor discovery result for one WVS question."""
    wvs_qcode: str             # e.g. 'Q71'
    wvs_acode: str             # e.g. 'E069_06'
    wvs_title: str             # English title from equivalences
    wvs_domain: str            # e.g. 'Politics & Society'
    candidates: List[AnchorCandidate]
    best_grade: int            # max grade across candidates (0 if none found)
    best_candidate: Optional[AnchorCandidate]  # highest-grade candidate


# ---------------------------------------------------------------------------
# LLM grading prompt
# ---------------------------------------------------------------------------

_GRADE_SYSTEM = """You are an expert in comparative survey methodology.
You will be shown a WVS (World Values Survey) question and a candidate question
from the 'Los mexicanos vistos por sí mismos' (los_mex) survey battery.

Your task: judge how well the los_mex question matches the WVS question.

GRADING SCALE:
  3 — Near-identical: same concept, essentially same wording and response scale.
      Can be used as a direct validation anchor.
  2 — Same concept, different wording or response scale.
      Same underlying construct but with minor methodological differences.
  1 — Related topic but different angle; weak thematic overlap.
  0 — Unrelated or only superficially similar.

Also assess SCALE COMPATIBILITY: whether response scales are directly comparable
(same number of points, same direction, same anchors).

Reply ONLY with valid JSON in this exact schema:
{
  "grade": <0|1|2|3>,
  "grade_justification": "<1-2 sentence explanation>",
  "scale_compatible": <true|false>,
  "scale_notes": "<brief note on scale differences, or 'Direct match' if identical>"
}"""

_GRADE_USER = """WVS question:
  Code: {wvs_code}
  Text: {wvs_title}
  Domain: {wvs_domain}

los_mex candidate:
  ID: {los_mex_id}
  Text: {los_mex_text}
  Survey: {los_mex_survey}
  Cosine similarity: {similarity:.3f}

Grade this match."""


# ---------------------------------------------------------------------------
# Main discovery class
# ---------------------------------------------------------------------------

class WVSAnchorDiscovery:
    """Find and grade anchor questions between WVS and los_mex.

    Parameters
    ----------
    db_f1 : ChromaDB collection
        The los_mex ChromaDB collection (from utility_functions.environment_setup).
    llm : callable
        LLM callable that accepts a list of messages and returns a string.
        Compatible with LangChain ChatOpenAI / ChatAnthropic.
    embedding_fn : callable, optional
        Embedding function: list[str] → list[list[float]].
        If None, uses db_f1's built-in embedding function via ChromaDB query.
    batch_pause : float
        Seconds to pause between LLM grading batches (rate-limit protection).
    """

    _DEFAULT_OUTPUT = Path("data/wvs/anchor_registry.json")

    def __init__(
        self,
        db_f1,
        llm,
        embedding_fn=None,
        batch_pause: float = 0.5,
    ):
        self.db_f1 = db_f1
        self.llm = llm
        self.embedding_fn = embedding_fn
        self.batch_pause = batch_pause

    # ------------------------------------------------------------------
    # Step 2: Vector search
    # ------------------------------------------------------------------

    def _query_los_mex(
        self,
        query_text: str,
        n_candidates: int = 5,
    ) -> List[Dict[str, Any]]:
        """Query ChromaDB for los_mex questions nearest to query_text.

        Returns list of dicts with keys:
            id, text, survey, distance, similarity
        """
        results = self.db_f1.query(
            query_texts=[query_text],
            n_results=n_candidates,
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        if not results["ids"] or not results["ids"][0]:
            return hits

        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            # ChromaDB cosine distance ∈ [0, 2]; similarity = 1 - distance/2
            similarity = max(0.0, 1.0 - distance / 2.0)
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            text = results["documents"][0][i] if results["documents"] else ""

            hits.append({
                "id": doc_id,
                "text": text,
                "survey": metadata.get("survey", metadata.get("topic", "")),
                "distance": distance,
                "similarity": similarity,
            })

        return hits

    # ------------------------------------------------------------------
    # Step 3: LLM grading
    # ------------------------------------------------------------------

    def _grade_candidate(
        self,
        wvs_qcode: str,
        wvs_title: str,
        wvs_domain: str,
        candidate: Dict[str, Any],
    ) -> AnchorCandidate:
        """Grade one los_mex candidate against a WVS question."""
        user_content = _GRADE_USER.format(
            wvs_code=wvs_qcode,
            wvs_title=wvs_title,
            wvs_domain=wvs_domain,
            los_mex_id=candidate["id"],
            los_mex_text=candidate["text"],
            los_mex_survey=candidate["survey"],
            similarity=candidate["similarity"],
        )

        raw = self._call_llm(_GRADE_SYSTEM, user_content)
        parsed = _parse_grade_json(raw)

        return AnchorCandidate(
            los_mex_id=candidate["id"],
            los_mex_survey=candidate["survey"],
            los_mex_text=candidate["text"],
            cosine_similarity=candidate["similarity"],
            grade=parsed.get("grade", 0),
            grade_justification=parsed.get("grade_justification", ""),
            scale_compatible=parsed.get("scale_compatible", False),
            scale_notes=parsed.get("scale_notes", ""),
        )

    def _call_llm(self, system: str, user: str) -> str:
        """Invoke the LLM with system + user messages, return raw string."""
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [SystemMessage(content=system), HumanMessage(content=user)]
        response = self.llm.invoke(messages)
        return response.content if hasattr(response, "content") else str(response)

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def build_registry(
        self,
        equivalences: pd.DataFrame,
        wave: int = 7,
        n_candidates: int = 5,
        min_similarity: float = 0.6,
        qcodes: Optional[List[str]] = None,
        verbose: bool = True,
    ) -> Dict[str, AnchorEntry]:
        """Run the full anchor discovery pipeline for all Wave 7 Q-codes.

        Parameters
        ----------
        equivalences : pd.DataFrame
            From wvs_metadata.load_equivalences(). Must have columns:
            a_code, title, domain, w7 (or w{wave}).
        wave : int
            WVS wave to use (default 7). Only questions present in this wave
            (non-null Q-code) are processed.
        n_candidates : int
            Number of los_mex candidates per WVS question.
        min_similarity : float
            Minimum cosine similarity to include a candidate (skip low-quality hits).
        qcodes : list[str], optional
            Restrict to these Q-codes (for testing or partial runs).
        verbose : bool
            Print progress.

        Returns
        -------
        dict mapping wvs_qcode → AnchorEntry
        """
        wave_col = f"w{wave}"
        if wave_col not in equivalences.columns:
            raise ValueError(f"Wave column '{wave_col}' not in equivalences DataFrame.")

        # Filter to questions present in this wave
        wave_df = equivalences[equivalences[wave_col].notna()].copy()
        if qcodes:
            wave_df = wave_df[wave_df[wave_col].isin(qcodes)]

        registry: Dict[str, AnchorEntry] = {}
        total = len(wave_df)

        for i, (_, row) in enumerate(wave_df.iterrows()):
            qcode = str(row[wave_col])
            acode = str(row["a_code"])
            title = str(row["title"])
            domain = str(row["domain"])

            if verbose:
                print(f"[{i+1}/{total}] {qcode} ({acode}): {title[:60]}…")

            # Step 2: vector search
            candidates_raw = self._query_los_mex(title, n_candidates=n_candidates)
            candidates_raw = [c for c in candidates_raw if c["similarity"] >= min_similarity]

            if not candidates_raw:
                registry[qcode] = AnchorEntry(
                    wvs_qcode=qcode, wvs_acode=acode, wvs_title=title,
                    wvs_domain=domain, candidates=[], best_grade=0,
                    best_candidate=None,
                )
                continue

            # Step 3: LLM grading
            graded: List[AnchorCandidate] = []
            for cand in candidates_raw:
                try:
                    ac = self._grade_candidate(qcode, title, domain, cand)
                    graded.append(ac)
                except Exception as exc:
                    if verbose:
                        print(f"    ⚠ grading failed for {cand['id']}: {exc}")
                    # Add ungraded candidate (grade 0)
                    graded.append(AnchorCandidate(
                        los_mex_id=cand["id"], los_mex_survey=cand["survey"],
                        los_mex_text=cand["text"], cosine_similarity=cand["similarity"],
                        grade=0, grade_justification="grading failed",
                        scale_compatible=False, scale_notes="",
                    ))

            graded.sort(key=lambda c: (c.grade, c.cosine_similarity), reverse=True)
            best = graded[0] if graded else None
            best_grade = best.grade if best else 0

            if verbose and best_grade >= 2:
                print(f"    ★ Grade {best_grade}: {best.los_mex_id} — {best.grade_justification[:80]}")

            registry[qcode] = AnchorEntry(
                wvs_qcode=qcode, wvs_acode=acode, wvs_title=title,
                wvs_domain=domain, candidates=graded, best_grade=best_grade,
                best_candidate=best,
            )

            # Rate-limit pause between questions
            if i < total - 1:
                time.sleep(self.batch_pause)

        return registry

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def save(self, registry: Dict[str, AnchorEntry], path: Path) -> None:
        """Save anchor registry to JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {qcode: entry.model_dump() for qcode, entry in registry.items()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        n_grade3 = sum(1 for e in registry.values() if e.best_grade == 3)
        n_grade2 = sum(1 for e in registry.values() if e.best_grade == 2)
        print(f"Anchor registry saved: {len(registry)} WVS questions, "
              f"{n_grade3} grade-3 anchors, {n_grade2} grade-2 anchors → {path}")

    @staticmethod
    def load(path: Path) -> Dict[str, AnchorEntry]:
        """Load a previously saved anchor registry."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Anchor registry not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {qcode: AnchorEntry(**entry) for qcode, entry in raw.items()}


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

def load_anchor_registry(path: Path) -> Dict[str, AnchorEntry]:
    """Load a saved anchor registry. Alias for WVSAnchorDiscovery.load()."""
    return WVSAnchorDiscovery.load(path)


def filter_anchors(
    registry: Dict[str, AnchorEntry],
    min_grade: int = 2,
) -> Dict[str, AnchorEntry]:
    """Return only entries whose best_grade >= min_grade."""
    return {k: v for k, v in registry.items() if v.best_grade >= min_grade}


def registry_to_dataframe(registry: Dict[str, AnchorEntry]) -> pd.DataFrame:
    """Flatten anchor registry into a tidy DataFrame for analysis.

    Returns one row per (WVS question, best los_mex candidate).
    Only includes entries with at least one candidate.
    """
    rows = []
    for qcode, entry in registry.items():
        if not entry.best_candidate:
            continue
        bc = entry.best_candidate
        rows.append({
            "wvs_qcode": qcode,
            "wvs_acode": entry.wvs_acode,
            "wvs_title": entry.wvs_title,
            "wvs_domain": entry.wvs_domain,
            "los_mex_id": bc.los_mex_id,
            "los_mex_survey": bc.los_mex_survey,
            "los_mex_text": bc.los_mex_text,
            "cosine_similarity": bc.cosine_similarity,
            "grade": bc.grade,
            "grade_justification": bc.grade_justification,
            "scale_compatible": bc.scale_compatible,
            "scale_notes": bc.scale_notes,
        })
    return pd.DataFrame(rows)


def summarise_registry(registry: Dict[str, AnchorEntry]) -> pd.DataFrame:
    """One-row-per-WVS-question summary of anchor grades by domain."""
    rows = []
    for qcode, entry in registry.items():
        rows.append({
            "wvs_qcode": qcode,
            "wvs_acode": entry.wvs_acode,
            "wvs_domain": entry.wvs_domain,
            "n_candidates": len(entry.candidates),
            "best_grade": entry.best_grade,
            "best_los_mex_id": entry.best_candidate.los_mex_id if entry.best_candidate else None,
            "best_similarity": entry.best_candidate.cosine_similarity if entry.best_candidate else None,
            "scale_compatible": entry.best_candidate.scale_compatible if entry.best_candidate else None,
        })
    df = pd.DataFrame(rows)
    return df.sort_values("best_grade", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_grade_json(raw: str) -> Dict[str, Any]:
    """Extract JSON from LLM response, with fallback for malformed output."""
    import re
    raw = raw.strip()
    # Try to extract JSON block
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    # Fallback: extract grade integer directly
    grade_match = re.search(r'"grade"\s*:\s*([0-3])', raw)
    grade = int(grade_match.group(1)) if grade_match else 0
    return {
        "grade": grade,
        "grade_justification": "parse error — extracted grade only",
        "scale_compatible": False,
        "scale_notes": "",
    }
