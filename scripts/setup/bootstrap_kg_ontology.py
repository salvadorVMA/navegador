"""
Bootstrap script for the Navegador Knowledge Graph ontology.

Generates data/kg_ontology.json and data/kg_review_summary.md via a two-pass
LLM-assisted process:

  Pass 1 — Per-topic annotation (parallelized):
    For each survey topic, ask the LLM to propose 3-6 constructs, map every
    question in that topic to a construct, and suggest intra-topic relationships.
    Uses mod_bajo (cheapest model) — estimated total cost < $0.10.

  Pass 2 — Cross-domain relationships (single call):
    Send a compact domain+construct summary to the LLM and ask for
    evidence-backed cross-domain relationships.

After running, review data/kg_review_summary.md before using the ontology.
The JSON file can be edited directly in VS Code.

Usage:
    python scripts/setup/bootstrap_kg_ontology.py
    python scripts/setup/bootstrap_kg_ontology.py --dry-run   # print prompts only
"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from utility_functions import get_answer, clean_llm_json_output

# LLM model — cheapest, sufficient for classification tasks
MOD = "gpt-4.1-nano-2025-04-14"
# Paths
ONTOLOGY_PATH = ROOT / "data" / "kg_ontology.json"
REVIEW_PATH = ROOT / "data" / "kg_review_summary.md"

# Confidence threshold below which a question mapping is flagged for review
CONFIDENCE_THRESHOLD = 0.70
# Max questions per topic to include in the LLM prompt (avoids token limits)
MAX_QUESTIONS_PER_TOPIC = 80


# ---------------------------------------------------------------------------
# Pass 1 — per-topic construct annotation
# ---------------------------------------------------------------------------

def _build_topic_prompt(topic_abbrev: str, topic_label: str, questions: dict) -> str:
    """
    Build a per-topic annotation prompt.

    questions: {question_id: question_text}  (question_id format: pN_M|TOPIC)
    """
    q_items = list(questions.items())[:MAX_QUESTIONS_PER_TOPIC]
    question_lines = []
    for qid, text in q_items:
        # Strip the leading "SURVEY_NAME|" prefix that appears in pregs_dict values
        clean_text = text.split("|", 1)[-1] if "|" in text else text
        # Use "QUESTION_ID:" prefix so the LLM doesn't confuse it with text content
        question_lines.append(f"  QUESTION_ID: {qid} | TEXT: {clean_text[:130]}")
    question_block = "\n".join(question_lines)

    return f"""You are an expert social scientist annotating a survey ontology.

Survey topic: "{topic_label}" (abbreviation: {topic_abbrev})

Below are {len(q_items)} survey questions. Format: QUESTION_ID: <id> | TEXT: <text>

CRITICAL RULE: In your JSON output, copy the QUESTION_ID value EXACTLY as shown, including the
pipe character and topic suffix (e.g., "p5_1|{topic_abbrev}"). Do NOT shorten, drop the "|{topic_abbrev}"
suffix, or add any brackets.

Your task:
1. Identify 3 to 6 CONSTRUCTS that these questions measure (e.g., national_identity, media_trust).
2. Map EVERY question to exactly one construct using its exact QUESTION_ID.
3. Propose RELATIONSHIPS between constructs within this topic.
4. For each mapping, provide a confidence score (0.0–1.0).

QUESTIONS:
{question_block}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "constructs": [
    {{"id": "{topic_abbrev}__<snake_case_name>", "label": "<Human Readable Label>"}}
  ],
  "question_mappings": [
    {{"question_id": "p5_1|{topic_abbrev}", "construct_id": "{topic_abbrev}__<name>", "confidence": 0.9}}
  ],
  "intra_relationships": [
    {{"from": "{topic_abbrev}__<name>", "to": "{topic_abbrev}__<name>", "type": "<relation_type>",
      "evidence": "<brief rationale>"}}
  ]
}}

Rules:
- construct id format MUST be: {topic_abbrev}__<snake_case> (e.g., {topic_abbrev}__national_identity)
- question_id MUST match exactly one of the QUESTION_ID values listed above
- Every QUESTION_ID in the list above must appear exactly once in question_mappings
- Confidence < 0.7 = question could plausibly belong to another construct
- relation_type examples: "correlates_with", "influences", "predicts", "is_part_of"
"""


def _annotate_topic(topic_abbrev: str, topic_label: str, questions: dict, dry_run: bool) -> dict:
    """Call the LLM for a single topic and return parsed result."""
    prompt = _build_topic_prompt(topic_abbrev, topic_label, questions)

    if dry_run:
        print(f"\n{'='*60}\nDRY RUN — prompt for {topic_abbrev}:\n{prompt[:400]}...\n")
        return {"constructs": [], "question_mappings": [], "intra_relationships": []}

    try:
        raw = get_answer(prompt, model=MOD, temperature=0.3)
        cleaned = clean_llm_json_output(raw)
        result = json.loads(cleaned)
        print(f"  ✓ {topic_abbrev} — {len(result.get('constructs', []))} constructs, "
              f"{len(result.get('question_mappings', []))} mappings")
        return result
    except Exception as e:
        print(f"  ✗ {topic_abbrev} — LLM/parse error: {e}")
        return {"constructs": [], "question_mappings": [], "intra_relationships": [], "error": str(e)}


# ---------------------------------------------------------------------------
# Pass 2 — cross-domain relationships
# ---------------------------------------------------------------------------

def _build_cross_domain_prompt(domain_construct_summary: str) -> str:
    return f"""You are a social scientist building a knowledge graph for a Mexican public opinion survey project
("Los Mexicanos Vistos Por Sí Mismos", UNAM 2014-2015).

Below are the survey domains and their constructs. Your task: propose CROSS-DOMAIN relationships
that are backed by established social science research. Be conservative — only include relationships
with clear empirical evidence in the literature.

DOMAIN → CONSTRUCTS:
{domain_construct_summary}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "cross_domain_relationships": [
    {{
      "from": "<construct_id>",
      "to": "<construct_id>",
      "type": "<relation_type>",
      "evidence": "<citation or brief rationale>",
      "strength": "strong|moderate|weak"
    }}
  ]
}}

Rules:
- relation_type examples: "influences", "negatively_affects", "predicts", "correlates_with", "enables"
- strength: "strong" = well-replicated finding; "moderate" = mixed evidence; "weak" = theoretical
- Omit relationships that are speculative or not grounded in research.
- Aim for 10–25 relationships total (quality over quantity).
"""


def _annotate_cross_domain(all_constructs: list, dry_run: bool) -> list:
    """Propose cross-domain relationships from the full construct list."""
    # Build a compact summary grouped by domain
    domain_map: dict = {}
    for c in all_constructs:
        parts = c["id"].split("__", 1)
        domain = parts[0] if len(parts) == 2 else c["id"]
        domain_map.setdefault(domain, []).append(c)

    summary_lines = []
    for domain, constructs in sorted(domain_map.items()):
        labels = ", ".join(c["label"] for c in constructs)
        ids = ", ".join(c["id"] for c in constructs)
        summary_lines.append(f"  {domain}: {labels}\n       IDs: {ids}")
    summary = "\n".join(summary_lines)

    prompt = _build_cross_domain_prompt(summary)

    if dry_run:
        print(f"\n{'='*60}\nDRY RUN — cross-domain prompt:\n{prompt[:400]}...\n")
        return []

    try:
        raw = get_answer(prompt, model=MOD, temperature=0.3)
        cleaned = clean_llm_json_output(raw)
        result = json.loads(cleaned)
        rels = result.get("cross_domain_relationships", [])
        print(f"  ✓ Cross-domain — {len(rels)} relationships proposed")
        return rels
    except Exception as e:
        print(f"  ✗ Cross-domain — LLM/parse error: {e}")
        return []


# ---------------------------------------------------------------------------
# Assemble the ontology JSON
# ---------------------------------------------------------------------------

def _assemble_ontology(
    rev_topic_dict: dict,
    pregs_dict: dict,
    topic_results: dict,
    cross_domain_rels: list,
) -> dict:
    """Merge per-topic results and cross-domain relationships into the final JSON schema."""

    domains = [{"id": k, "label": v} for k, v in rev_topic_dict.items()]

    # Build comprehensive lookup maps for ID resolution
    # Maps: exact_id → qid, bare_base → qid, "base|TOPIC" → qid
    all_qids = set(pregs_dict.keys())
    # Per-topic map: for each topic, map base variants to the full QID
    topic_qid_map: dict = {}  # (base, topic) → full_qid
    for qid in all_qids:
        if "|" in qid:
            base, topic = qid.rsplit("|", 1)
            topic_qid_map[(base, topic)] = qid
            # Also map shortened base (e.g. "p1" → "p1_1") — first match wins
            short_base = base.split("_")[0]
            topic_qid_map.setdefault((short_base, topic), qid)

    def _resolve_qid(raw_id: str, topic_abbrev: str) -> str:
        """Resolve a potentially malformed question ID to a valid QID."""
        # Strip brackets or whitespace the LLM may have added
        raw_id = raw_id.strip().strip("[]")

        # 1. Exact match
        if raw_id in all_qids:
            return raw_id
        # 2. LLM dropped the |TOPIC suffix — append it
        candidate = f"{raw_id}|{topic_abbrev}"
        if candidate in all_qids:
            return candidate
        # 3. LLM dropped both _N suffix and |TOPIC — use topic map
        for (base, topic), full_qid in topic_qid_map.items():
            if topic == topic_abbrev and (base == raw_id or raw_id.split("|")[0] == base):
                return full_qid
        # 4. Can't resolve — return as-is (will be flagged as invalid construct ref)
        return raw_id

    all_constructs = []
    all_questions = []
    all_intra_rels = []
    seen_qids: set = set()

    for topic_abbrev, result in topic_results.items():
        for c in result.get("constructs", []):
            if c not in all_constructs:
                all_constructs.append({"id": c["id"], "label": c["label"], "domain": topic_abbrev})

        for qm in result.get("question_mappings", []):
            resolved = _resolve_qid(qm["question_id"], topic_abbrev)
            if resolved in seen_qids:
                continue
            seen_qids.add(resolved)
            text = pregs_dict.get(resolved, "")
            # Strip leading "SURVEY_NAME|" prefix from text
            if "|" in text:
                text = text.split("|", 1)[-1]
            all_questions.append(
                {
                    "id": resolved,
                    "text": text,
                    "construct": qm["construct_id"],
                    "confidence": qm.get("confidence", 1.0),
                }
            )

        for r in result.get("intra_relationships", []):
            all_intra_rels.append(
                {
                    "from": r["from"],
                    "to": r["to"],
                    "type": r["type"],
                    "evidence": r.get("evidence", ""),
                    "strength": r.get("strength", "moderate"),
                }
            )

    # Reconcile: add any constructs referenced in question_mappings but missing from constructs array.
    # This happens when the LLM invents a construct name in mappings that it didn't list in constructs.
    existing_construct_ids = {c["id"] for c in all_constructs}
    for q in all_questions:
        cid = q["construct"]
        if cid and cid not in existing_construct_ids:
            domain = cid.split("__")[0] if "__" in cid else ""
            label = cid.split("__", 1)[-1].replace("_", " ").title() if "__" in cid else cid
            all_constructs.append({"id": cid, "label": label, "domain": domain})
            existing_construct_ids.add(cid)

    # Cross-domain relationships (remove confidence field if present, not in schema)
    all_rels = all_intra_rels + [
        {k: v for k, v in r.items() if k in ("from", "to", "type", "evidence", "strength")}
        for r in cross_domain_rels
    ]

    return {
        "domains": domains,
        "constructs": all_constructs,
        "questions": all_questions,
        "relationships": all_rels,
    }


# ---------------------------------------------------------------------------
# Review document generator
# ---------------------------------------------------------------------------

def _generate_review_doc(ontology: dict, pregs_dict: dict) -> str:
    """Generate the prioritised human-review markdown document."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# KG Ontology Review Checklist",
        f"Generated: {now}  ",
        f"Edit `data/kg_ontology.json` directly to make corrections, then reload the KG.\n",
    ]

    # ── Priority 1: Cross-domain relationships ──────────────────────────
    construct_ids = {c["id"] for c in ontology["constructs"]}
    domain_of = {c["id"]: c["domain"] for c in ontology["constructs"]}

    cross_rels = [
        r for r in ontology["relationships"]
        if domain_of.get(r["from"]) != domain_of.get(r["to"])
    ]

    lines.append(
        f"## PRIORITY 1 — Cross-Domain Relationships  \n"
        f"**Review ALL {len(cross_rels)} items.** Mark each as ✅ keep | ❌ delete | ✏️ edit.\n"
    )

    if cross_rels:
        lines.append("| From | Type | To | Evidence | Strength |")
        lines.append("|------|------|----|----------|----------|")
        for r in sorted(cross_rels, key=lambda x: x.get("strength", ""), reverse=True):
            lines.append(
                f"| `{r['from']}` | {r['type']} | `{r['to']}` "
                f"| {r.get('evidence', '—')} | {r.get('strength', '—')} |"
            )
    else:
        lines.append("_No cross-domain relationships proposed._\n")

    # ── Priority 2: Construct definitions per topic ──────────────────────
    lines.append(
        "\n## PRIORITY 2 — Construct Definitions by Topic  \n"
        "Skim each block (~3 min per topic). Check: do the construct labels make sense "
        "given the sample questions?\n"
    )

    constructs_by_domain: dict = {}
    for c in ontology["constructs"]:
        constructs_by_domain.setdefault(c["domain"], []).append(c)

    questions_by_construct: dict = {}
    for q in ontology["questions"]:
        questions_by_construct.setdefault(q["construct"], []).append(q)

    for domain_id, constructs in sorted(constructs_by_domain.items()):
        domain_label = next((d["label"] for d in ontology["domains"] if d["id"] == domain_id), domain_id)
        lines.append(f"### {domain_id} — {domain_label}\n")
        for c in constructs:
            qs = questions_by_construct.get(c["id"], [])
            lines.append(f"**`{c['id']}`** — {c['label']} ({len(qs)} questions)")
            for q in qs[:3]:
                text = q.get("text", pregs_dict.get(q["id"], ""))
                if "|" in text:
                    text = text.split("|", 1)[-1]
                lines.append(f"  - `{q['id']}`: {text[:120]}")
            if len(qs) > 3:
                lines.append(f"  - _(+{len(qs)-3} more)_")
            lines.append("")

    # ── Priority 3: Uncertain mappings ──────────────────────────────────
    uncertain = [
        q for q in ontology["questions"]
        if q.get("confidence", 1.0) < CONFIDENCE_THRESHOLD
    ]

    lines.append(
        f"## PRIORITY 3 — Uncertain Question Mappings (confidence < {CONFIDENCE_THRESHOLD})  \n"
        f"Spot-check these {len(uncertain)} items. Each could belong to an alternative construct.\n"
    )

    if uncertain:
        lines.append("| Question ID | Text | Assigned Construct | Confidence |")
        lines.append("|-------------|------|--------------------|------------|")
        for q in sorted(uncertain, key=lambda x: x.get("confidence", 1.0)):
            text = q.get("text", pregs_dict.get(q["id"], ""))
            if "|" in text:
                text = text.split("|", 1)[-1]
            lines.append(
                f"| `{q['id']}` | {text[:80]} | `{q['construct']}` | {q.get('confidence', '?'):.2f} |"
            )
    else:
        lines.append("_All mappings have high confidence._\n")

    lines.append(
        "\n---\n"
        "## How to Edit\n"
        "- **Rename construct**: change `label` in the `constructs` array of `kg_ontology.json`\n"
        "- **Reassign question**: change `construct` in a `questions` entry\n"
        "- **Delete cross-domain link**: remove the entry from `relationships`\n"
        "- **Merge constructs**: update all question `construct` fields, remove stale construct entry\n"
        "- After editing, reload with: `from survey_kg import kg; kg.load_from_json('data/kg_ontology.json')`\n"
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(dry_run: bool = False) -> None:
    print("━" * 60)
    print("Navegador — KG Ontology Bootstrap")
    print("━" * 60)

    # Load data
    print("\nLoading survey data...")
    try:
        from dataset_knowledge import rev_topic_dict, pregs_dict, DATA_AVAILABLE
        if not DATA_AVAILABLE or not rev_topic_dict or not pregs_dict:
            print("ERROR: Survey data not available. Check data/encuestas/los_mex_dict.json", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"ERROR loading dataset_knowledge: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"  Topics: {list(rev_topic_dict.keys())}")
    print(f"  Total questions: {len(pregs_dict)}")

    # Group questions by topic
    topics_questions: dict = {}
    for qid, text in pregs_dict.items():
        parts = qid.split("|")
        if len(parts) == 2:
            topic_abbrev = parts[1]
            if topic_abbrev in rev_topic_dict:
                topics_questions.setdefault(topic_abbrev, {})[qid] = text

    print(f"\nPass 1 — Annotating {len(topics_questions)} topics in parallel...")

    # Parallel per-topic annotation
    topic_results: dict = {}
    with ThreadPoolExecutor(max_workers=min(8, len(topics_questions))) as executor:
        futures = {
            executor.submit(
                _annotate_topic,
                abbrev,
                rev_topic_dict[abbrev],
                questions,
                dry_run,
            ): abbrev
            for abbrev, questions in topics_questions.items()
        }
        for future in as_completed(futures):
            abbrev = futures[future]
            try:
                topic_results[abbrev] = future.result()
            except Exception as e:
                print(f"  ✗ {abbrev} — unexpected error: {e}")
                topic_results[abbrev] = {"constructs": [], "question_mappings": [], "intra_relationships": []}

    # Collect all constructs for Pass 2
    all_constructs = []
    for result in topic_results.values():
        all_constructs.extend(result.get("constructs", []))

    print(f"\nPass 2 — Proposing cross-domain relationships ({len(all_constructs)} constructs)...")
    cross_domain_rels = _annotate_cross_domain(all_constructs, dry_run)

    # Assemble ontology
    print("\nAssembling ontology...")
    ontology = _assemble_ontology(rev_topic_dict, pregs_dict, topic_results, cross_domain_rels)

    n = {
        "domains": len(ontology["domains"]),
        "constructs": len(ontology["constructs"]),
        "questions": len(ontology["questions"]),
        "relationships": len(ontology["relationships"]),
    }
    print(f"  Domains: {n['domains']}, Constructs: {n['constructs']}, "
          f"Questions: {n['questions']}, Relationships: {n['relationships']}")

    if not dry_run:
        # Save ontology JSON
        ONTOLOGY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ONTOLOGY_PATH, "w", encoding="utf-8") as f:
            json.dump(ontology, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Ontology saved → {ONTOLOGY_PATH}")

        # Save review document
        review_md = _generate_review_doc(ontology, pregs_dict)
        with open(REVIEW_PATH, "w", encoding="utf-8") as f:
            f.write(review_md)
        print(f"✅ Review checklist saved → {REVIEW_PATH}")

        print("\n" + "━" * 60)
        print("NEXT STEPS:")
        print(f"  1. Open {REVIEW_PATH} in VS Code")
        print("  2. Review Priority 1 (cross-domain relationships) — ~10 min")
        print("  3. Skim Priority 2 (construct definitions) — ~30 min")
        print("  4. Fix any issues directly in data/kg_ontology.json")
        print("  5. The KG will auto-load next time you import survey_kg")
        print("━" * 60)
    else:
        print("\n[dry-run] No files written.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap the Navegador KG ontology")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts only, do not call LLM or write files")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
