"""
Architecture comparison v2: OLD vs NEW (v1) vs V2 (thematic), mini model only.

Test strategy:
- Same 10 questions, same semantic variable search as the 2x2 test
- 3 architectures × 10 questions = 30 runs
- Mini model only (full model not necessary based on 2x2 results)
- Results saved to data/results/architecture_comparison_v2/
- Per-question markdown + aggregate summary

What we're evaluating:
  OLD  — detailed_report: pattern → expert → transversal synthesis
  NEW  — analytical_essay v1: divergence-framed dialectical essay
  V2   — thematic_essay: thematic synthesis → content-organized essay

Key qualitative questions:
  1. Does V2 produce argument-organized essays (like OLD) rather than distribution reports (like NEW)?
  2. Does V2 mention divergence only when substantively meaningful?
  3. Does V2 match OLD's natural narrative flow while keeping NEW's data precision?
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, '/workspaces/navegador')

from run_analysis import run_analysis
from variable_selector import _variable_selector
from dataset_knowledge import tmp_topic_st
from langchain_openai import ChatOpenAI

# ── Test questions (same as 2x2 test) ────────────────────────────────────────

TEST_QUESTIONS = [
    {
        "id": "q1_religion_politics",
        "query": "¿Cómo se relacionan la religión y la política en México?",
        "query_en": "How do religion and politics relate in Mexico?",
        "topics": ["Religion", "Political Culture"],
    },
    {
        "id": "q2_environment_economy",
        "query": "¿Cómo equilibran los mexicanos las preocupaciones ambientales con el desarrollo económico?",
        "query_en": "How do Mexicans balance environmental concerns with economic development?",
        "topics": ["Environment", "Economy"],
    },
    {
        "id": "q3_education_poverty",
        "query": "¿Qué relación ven los mexicanos entre educación y pobreza?",
        "query_en": "What relationship do Mexicans see between education and poverty?",
        "topics": ["Education", "Poverty"],
    },
    {
        "id": "q4_gender_family",
        "query": "¿Cómo están cambiando los roles de género en la familia mexicana?",
        "query_en": "How are gender roles changing in the Mexican family?",
        "topics": ["Gender", "Family"],
    },
    {
        "id": "q5_migration_culture",
        "query": "¿Cómo afecta la migración a la identidad cultural mexicana?",
        "query_en": "How does migration affect Mexican cultural identity?",
        "topics": ["Migration", "Identity"],
    },
    {
        "id": "q6_health_poverty",
        "query": "¿Cómo se relaciona el acceso a la salud con la pobreza en México?",
        "query_en": "How does health access relate to poverty in Mexico?",
        "topics": ["Health", "Poverty"],
    },
    {
        "id": "q7_democracy_corruption",
        "query": "¿Qué piensan los mexicanos sobre la relación entre democracia y corrupción?",
        "query_en": "What do Mexicans think about the relationship between democracy and corruption?",
        "topics": ["Political Culture", "Corruption"],
    },
    {
        "id": "q8_indigenous_discrimination",
        "query": "¿Cómo perciben los mexicanos la discriminación hacia pueblos indígenas?",
        "query_en": "How do Mexicans perceive discrimination against indigenous peoples?",
        "topics": ["Indigenous", "Human Rights"],
    },
    {
        "id": "q9_technology_education",
        "query": "¿Cómo impacta la tecnología en la educación según los mexicanos?",
        "query_en": "How does technology impact education according to Mexicans?",
        "topics": ["Technology", "Education"],
    },
    {
        "id": "q10_security_justice",
        "query": "¿Qué relación ven los mexicanos entre seguridad pública y justicia?",
        "query_en": "What relationship do Mexicans see between public security and justice?",
        "topics": ["Security", "Justice"],
    },
]

MODEL = 'gpt-4.1-mini-2025-04-14'

ARCHITECTURES = [
    ("detailed_report",  "OLD"),
    ("analytical_essay", "NEW"),
    ("thematic_essay",   "V2"),
]


# ── Single run ────────────────────────────────────────────────────────────────

def run_arch(arch_key: str, label: str, variables: List[str], query: str) -> Dict[str, Any]:
    icons = {"OLD": "🏛️ ", "NEW": "🚀 ", "V2": "✨ "}
    print(f"\n{icons.get(label, '  ')}{label} ({arch_key})")

    start = time.time()
    try:
        result = run_analysis(
            analysis_type=arch_key,
            selected_variables=variables,
            user_query=query,
            model_name=MODEL,
            temperature=0.4,
        )
        latency_ms = (time.time() - start) * 1000
        ok = result.get('success', False)
        print(f"   {'✅' if ok else '❌'} {latency_ms:.0f}ms")
        return {"success": ok, "result": result, "latency_ms": latency_ms,
                "error": result.get('error'), "arch": arch_key, "label": label}
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        print(f"   ❌ Exception {latency_ms:.0f}ms: {e}")
        return {"success": False, "result": {}, "latency_ms": latency_ms,
                "error": str(e), "arch": arch_key, "label": label}


# ── Metrics ───────────────────────────────────────────────────────────────────

def extract_metrics(run: Dict) -> Dict:
    m = {
        "success": run["success"],
        "latency_s": run["latency_ms"] / 1000,
        "error": run["error"],
        "label": run["label"],
    }
    r = run["result"]
    m["output_length"] = len(r.get("formatted_report", ""))

    data = r.get("results", r)

    # Variables
    if "valid_variables" in data:
        m["vars_analyzed"] = len(data["valid_variables"])
    elif "quantitative_report" in data:
        m["vars_analyzed"] = data["quantitative_report"].get("variable_count", 0)
    else:
        m["vars_analyzed"] = 0

    # NEW (v1) specific
    if "essay" in data and "prevailing_view" in data.get("essay", {}):
        essay = data["essay"]
        pv = len(essay.get("prevailing_view", ""))
        ca = len(essay.get("counterargument", ""))
        m["dialectical_ratio"] = round(ca / max(pv, 1), 2)
        m["essay_sections"] = sum(1 for k in ["summary","introduction","prevailing_view","counterargument","implications"] if essay.get(k))

    # V2 specific
    if "essay" in data and "theme_sections" in data.get("essay", {}):
        essay = data["essay"]
        m["n_themes"] = len(essay.get("theme_sections", []))
        m["flagged_vars"] = len(data.get("synthesis", {}).get("variables_to_flag", []))

    # Quant report
    if "quantitative_report" in data:
        q = data["quantitative_report"]
        m["divergence_index"] = round(q.get("divergence_index", 0), 2)

    return m


# ── Per-question markdown ─────────────────────────────────────────────────────

def write_question_md(question: Dict, runs: Dict[str, Dict], output_dir: Path) -> Path:
    q_id = question["id"]
    out = output_dir / f"{q_id}_comparison.md"

    lines = [
        f"# Comparison: {q_id}",
        f"",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"**Query (ES):** {question['query']}",
        f"**Query (EN):** {question['query_en']}",
        f"**Topics:** {', '.join(question['topics'])}",
        f"**Variables:** {', '.join(question.get('variables', []))}",
        f"",
        f"---",
        f"",
        f"## Performance Metrics",
        f"",
        f"| Metric | OLD | NEW (v1) | V2 (thematic) |",
        f"|--------|-----|----------|---------------|",
    ]

    metrics_def = [
        ("Success",          lambda m: "✅" if m["success"] else "❌"),
        ("Latency (s)",      lambda m: f"{m['latency_s']:.1f}"),
        ("Output (chars)",   lambda m: str(m.get("output_length", "—"))),
        ("Vars analyzed",    lambda m: str(m.get("vars_analyzed", "—"))),
        ("Divergence idx",   lambda m: str(m.get("divergence_index", "—"))),
        ("Essay sections",   lambda m: str(m.get("essay_sections", "—"))),
        ("Dialectical ratio",lambda m: str(m.get("dialectical_ratio", "—"))),
        ("Themes (V2)",      lambda m: str(m.get("n_themes", "—"))),
        ("Flagged vars (V2)",lambda m: str(m.get("flagged_vars", "—"))),
        ("Error",            lambda m: m.get("error") or "None"),
    ]

    for label_row, fn in metrics_def:
        row = f"| {label_row} |"
        for _, arch_label in ARCHITECTURES:
            try:
                row += f" {fn(extract_metrics(runs[arch_label]))} |"
            except Exception:
                row += " — |"
        lines.append(row)

    lines += ["", "---", "", "## Analysis Outputs", ""]

    for _, arch_label in ARCHITECTURES:
        run = runs[arch_label]
        lines.append(f"### {arch_label}")
        lines.append("")
        formatted = run["result"].get("formatted_report", "")
        if formatted:
            # Show more for side-by-side reading
            lines.append("```")
            lines.append(formatted[:6000])
            lines.append("```")
            if len(formatted) > 6000:
                lines.append(f"*(Truncated from {len(formatted)} chars)*")
        else:
            lines.append(f"**No output.** Error: {run.get('error', 'Unknown')}")
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# ── Summary markdown ──────────────────────────────────────────────────────────

def write_summary_md(all_results: List[Dict], output_dir: Path) -> Path:
    out = output_dir / "00_FINAL_SUMMARY.md"

    lines = [
        "# Architecture Comparison v2: OLD vs NEW vs V2",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Model:** {MODEL}  (mini only)",
        f"**Questions:** {len(all_results)}",
        "",
        "**Architectures:**",
        "- **OLD** — `detailed_report`: pattern identification → expert voice → transversal synthesis",
        "- **NEW** — `analytical_essay` v1: distribution-framed dialectical essay",
        "- **V2**  — `thematic_essay`: thematic synthesis (content-organized) → thematic essay",
        "",
        "---",
        "",
        "## Success Rate",
        "",
        "| Question | OLD | NEW | V2 |",
        "|----------|-----|-----|----|",
    ]

    for r in all_results:
        row = f"| {r['question']['id']} |"
        for _, label in ARCHITECTURES:
            ok = r["runs"][label]["success"]
            row += " ✅ |" if ok else " ❌ |"
        lines.append(row)

    lines += ["", "---", "", "## Latency (seconds)", "",
              "| Question | OLD | NEW | V2 |", "|----------|-----|-----|----|"]

    for r in all_results:
        row = f"| {r['question']['id']} |"
        for _, label in ARCHITECTURES:
            ms = r["runs"][label]["latency_ms"]
            row += f" {ms/1000:.1f} |"
        lines.append(row)

    # Averages
    def avg_latency(label):
        vals = [r["runs"][label]["latency_ms"] / 1000 for r in all_results if r["runs"][label]["success"]]
        return f"{sum(vals)/len(vals):.1f}" if vals else "—"

    lines.append(f"| **Average** | {avg_latency('OLD')} | {avg_latency('NEW')} | {avg_latency('V2')} |")

    lines += ["", "---", "", "## Variables Selected per Question", ""]
    for r in all_results:
        q = r["question"]
        vs = q.get("variables", [])
        lines.append(f"- **{q['id']}** ({len(vs)}): {', '.join(vs)}")

    lines += ["", "---", "", "## Individual Reports", ""]
    for r in all_results:
        q = r["question"]
        lines.append(f"- [{q['id']}](./{q['id']}_comparison.md) — {q['query_en']}")

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("ARCHITECTURE COMPARISON v2: OLD | NEW | V2 (thematic)")
    print(f"  Model: {MODEL}")
    print(f"  Questions: {len(TEST_QUESTIONS)}")
    print(f"  Total runs: {len(TEST_QUESTIONS) * len(ARCHITECTURES)}")
    print("=" * 80)

    output_dir = Path("/workspaces/navegador/data/results/architecture_comparison_v2")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Output: {output_dir}\n")

    selection_llm = ChatOpenAI(model="gpt-4o-mini")
    all_results = []

    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}/{len(TEST_QUESTIONS)}: {question['id']}")
        print(f"Query: {question['query']}")
        print(f"{'=' * 80}")

        # Semantic search — shared across all 3 architectures
        print("\n🔍 Semantic search...")
        topic_ids, variables_dict, grade_dict, *_ = _variable_selector(
            question["query"], tmp_topic_st, selection_llm, use_simultaneous_retrieval=True
        )
        sorted_vars = sorted(grade_dict.items(), key=lambda x: list(x[1].keys())[0], reverse=True)
        selected = [var_id for var_id, _ in sorted_vars[:10]]
        print(f"✅ {len(selected)} variables: {selected}")
        question["variables"] = selected

        if not selected:
            print("⚠️  No variables selected — skipping this question")
            continue

        # Run all 3 architectures
        runs = {}
        for arch_key, arch_label in ARCHITECTURES:
            runs[arch_label] = run_arch(arch_key, arch_label, selected, question["query"])

        # Save per-question markdown
        write_question_md(question, runs, output_dir)

        all_results.append({"question": question, "runs": runs})
        print(f"\n✅ {question['id']} complete")

    if all_results:
        summary_file = write_summary_md(all_results, output_dir)
        print(f"\n{'=' * 80}")
        print("COMPARISON COMPLETE")
        print(f"  {len(all_results)} questions × 3 architectures = {len(all_results) * 3} runs")
        print(f"  Summary: {summary_file}")
        print(f"  Output:  {output_dir}")


if __name__ == "__main__":
    main()
