"""
Final comprehensive comparison: 10 cross-topic questions
Tests FIXED OLD + ENHANCED NEW architectures
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, '/workspaces/navegador')

from run_analysis import run_analysis
from variable_selector import _variable_selector
from dataset_knowledge import tmp_topic_st
from langchain_openai import ChatOpenAI

# 10 comprehensive test questions spanning multiple topics
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


MODEL_MINI = 'gpt-4.1-mini-2025-04-14'
MODEL_FULL = 'gpt-4.1-2025-04-14'

TEST_MODELS = {
    "mini": MODEL_MINI,
    "full": MODEL_FULL,
}


def run_architecture(
    architecture: str,
    selected_variables: List[str],
    query: str,
    model_name: str,
) -> Dict[str, Any]:
    """Run a single architecture + model combination."""
    label = f"{'OLD' if architecture == 'detailed_report' else 'NEW'} ({architecture}) + {model_name}"
    print(f"\n{'🏛️' if architecture == 'detailed_report' else '🚀'}  {label}")

    start_time = time.time()

    try:
        result = run_analysis(
            analysis_type=architecture,
            selected_variables=selected_variables,
            user_query=query,
            model_name=model_name,
            temperature=0.4,
        )

        latency_ms = (time.time() - start_time) * 1000
        print(f"   {'✅ Success' if result.get('success') else '❌ Failed'} - {latency_ms:.0f}ms")

        return {
            "success": result.get('success', False),
            "result": result,
            "latency_ms": latency_ms,
            "error": result.get('error'),
            "architecture": architecture,
            "model": model_name,
        }

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        print(f"   ❌ Exception - {latency_ms:.0f}ms: {e}")

        return {
            "success": False,
            "result": {},
            "latency_ms": latency_ms,
            "error": str(e),
            "architecture": architecture,
            "model": model_name,
        }


def extract_cell_metrics(result: Dict) -> Dict[str, Any]:
    """Extract metrics from a single architecture+model result."""
    m: Dict[str, Any] = {
        "success": result.get("success", False),
        "latency_ms": result.get("latency_ms", 0),
        "error": result.get("error"),
        "architecture": result.get("architecture"),
        "model": result.get("model"),
    }
    wrapper = result.get("result", {})
    data = wrapper.get("results", wrapper)

    m["has_output"] = bool(wrapper.get("formatted_report"))
    m["output_length"] = len(wrapper.get("formatted_report", ""))

    # OLD-specific
    m["valid_variables"] = data.get("valid_variables", [])
    m["invalid_variables"] = data.get("invalid_variables", [])

    # NEW-specific
    if "essay" in data:
        essay = data["essay"]
        sections = ["summary", "introduction", "prevailing_view", "counterargument", "implications"]
        m["essay_sections"] = len([k for k in sections if k in essay and essay[k]])
        pv = len(essay.get("prevailing_view", ""))
        ca = len(essay.get("counterargument", ""))
        m["prevailing_view_length"] = pv
        m["counterargument_length"] = ca
        m["dialectical_ratio"] = ca / max(pv, 1)
    if "quantitative_report" in data:
        quant = data["quantitative_report"]
        m["variables_analyzed"] = quant.get("variable_count", 0)
        m["divergence_index"] = quant.get("divergence_index", 0)
        m["shape_summary"] = quant.get("shape_summary", {})
    if "reasoning" in data and data["reasoning"]:
        m["has_reasoning"] = True
        m["reasoning_variables_mapped"] = len(data["reasoning"].get("variable_analyses", []))
        m["reasoning_tensions"] = len(data["reasoning"].get("key_tensions", []))
    else:
        m["has_reasoning"] = False

    return m




CELL_KEYS = [
    ("detailed_report", "mini"),
    ("detailed_report", "full"),
    ("analytical_essay", "mini"),
    ("analytical_essay", "full"),
]

CELL_LABELS = {
    ("detailed_report", "mini"): "OLD + mini",
    ("detailed_report", "full"): "OLD + full",
    ("analytical_essay", "mini"): "NEW + mini",
    ("analytical_essay", "full"): "NEW + full",
}


def create_comparison_markdown(
    test_question: Dict,
    cell_results: Dict,
    cell_metrics: Dict,
    output_dir: Path,
) -> Path:
    """Create 2x2 comparison markdown for one question."""

    question_id = test_question["id"]
    output_file = output_dir / f"{question_id}_comparison.md"

    content = f"""# 2x2 Comparison: {question_id}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Test Question

**Spanish:** {test_question['query']}

**English:** {test_question['query_en']}

**Topics Covered:** {', '.join(test_question['topics'])}

**Variables Selected (semantic search):** {', '.join(test_question.get('variables', []))}

---

## Performance Metrics

| Metric | OLD + mini | OLD + full | NEW + mini | NEW + full |
|--------|-----------|-----------|-----------|-----------|
"""

    metric_rows = [
        ("Success", lambda m: "✅" if m["success"] else "❌"),
        ("Latency (s)", lambda m: f"{m['latency_ms']/1000:.1f}"),
        ("Output length", lambda m: str(m.get("output_length", "—"))),
        ("Variables analyzed", lambda m: str(m.get("variables_analyzed", m.get("valid_variables", "—") and len(m.get("valid_variables", []))))),
        ("Essay sections", lambda m: f"{m['essay_sections']}/5" if "essay_sections" in m else "—"),
        ("Dialectical ratio", lambda m: f"{m['dialectical_ratio']:.2f}" if "dialectical_ratio" in m else "—"),
        ("Divergence index", lambda m: f"{m['divergence_index']:.2f}" if "divergence_index" in m else "—"),
        ("Has reasoning", lambda m: "✅" if m.get("has_reasoning") else "—"),
        ("Error", lambda m: m.get("error") or "None"),
    ]

    for row_label, extractor in metric_rows:
        row = f"| {row_label} |"
        for key in CELL_KEYS:
            try:
                row += f" {extractor(cell_metrics[key])} |"
            except Exception:
                row += " — |"
        content += row + "\n"

    content += "\n---\n\n## Analysis Outputs\n\n"

    for key in CELL_KEYS:
        label = CELL_LABELS[key]
        content += f"### {label}\n\n"
        formatted = cell_results[key].get("result", {}).get("formatted_report", "")
        if formatted:
            content += f"```\n{formatted[:5000]}\n```\n"
            if len(formatted) > 5000:
                content += f"*(Truncated from {len(formatted)} chars)*\n"
        else:
            content += f"**No output.** Error: {cell_results[key].get('error', 'Unknown')}\n"
        content += "\n"

    output_file.write_text(content, encoding='utf-8')
    return output_file


def create_summary_markdown(all_results: List[Dict], output_dir: Path) -> Path:
    """Create 2x2 summary across all questions."""

    output_file = output_dir / "00_FINAL_SUMMARY.md"

    content = f"""# 2x2 Architecture × Model Comparison

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Test Questions:** {len(all_results)} (semantic search selected variables)

**Models:** mini = {MODEL_MINI} | full = {MODEL_FULL}

---

## Success Rate

| Question | OLD+mini | OLD+full | NEW+mini | NEW+full |
|----------|----------|----------|----------|----------|
"""

    for r in all_results:
        q_id = r["question"]["id"]
        row = f"| {q_id} |"
        for key in CELL_KEYS:
            row += " ✅ |" if r["cell_metrics"][key]["success"] else " ❌ |"
        content += row + "\n"

    content += "\n---\n\n## Latency (seconds)\n\n"
    content += "| Question | OLD+mini | OLD+full | NEW+mini | NEW+full |\n"
    content += "|----------|----------|----------|----------|----------|\n"
    for r in all_results:
        q_id = r["question"]["id"]
        row = f"| {q_id} |"
        for key in CELL_KEYS:
            ms = r["cell_metrics"][key]["latency_ms"]
            row += f" {ms/1000:.1f} |"
        content += row + "\n"

    content += "\n---\n\n## Variables Selected per Question\n\n"
    for r in all_results:
        q_id = r["question"]["id"]
        vars_selected = r["question"].get("variables", [])
        content += f"- **{q_id}** ({len(vars_selected)}): {', '.join(vars_selected)}\n"

    content += "\n---\n\n## Individual Reports\n\n"
    for r in all_results:
        q_id = r["question"]["id"]
        content += f"- [{q_id}](./{q_id}_comparison.md) — {r['question']['query_en']}\n"

    output_file.write_text(content, encoding='utf-8')
    return output_file


def main():
    """Main execution — 2x2: architecture × model."""

    print("=" * 80)
    print("2x2 ARCHITECTURE × MODEL COMPARISON — 10 QUESTIONS")
    print(f"  Architectures: detailed_report (OLD) | analytical_essay (NEW)")
    print(f"  Models:        mini ({MODEL_MINI})")
    print(f"                 full ({MODEL_FULL})")
    print("=" * 80)

    output_dir = Path("/workspaces/navegador/data/results/architecture_comparison_2x2")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Output: {output_dir}\n")

    all_results = []

    selection_llm = ChatOpenAI(model="gpt-4o-mini")

    for i, test_question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}/{len(TEST_QUESTIONS)}: {test_question['id']}")
        print(f"Topics: {', '.join(test_question['topics'])}")
        print(f"Query: {test_question['query']}")
        print(f"{'=' * 80}")

        # Semantic search — shared across all 4 cells
        print(f"\n🔍 Semantic search...")
        topic_ids, variables_dict, grade_dict = _variable_selector(
            test_question["query"], tmp_topic_st, selection_llm, use_simultaneous_retrieval=True
        )
        sorted_vars = sorted(grade_dict.items(), key=lambda x: list(x[1].keys())[0], reverse=True)
        selected_variables = [var_id for var_id, _ in sorted_vars[:10]]
        print(f"✅ {len(selected_variables)} variables selected: {selected_variables}")
        test_question["variables"] = selected_variables

        # Run all 4 cells
        cell_results = {}
        for (architecture, model_key) in CELL_KEYS:
            model_name = TEST_MODELS[model_key]
            cell_results[(architecture, model_key)] = run_architecture(
                architecture, selected_variables, test_question["query"], model_name
            )

        cell_metrics = {key: extract_cell_metrics(cell_results[key]) for key in CELL_KEYS}

        comparison_file = create_comparison_markdown(
            test_question, cell_results, cell_metrics, output_dir
        )

        all_results.append({
            "question": test_question,
            "cell_results": cell_results,
            "cell_metrics": cell_metrics,
            "comparison_file": str(comparison_file),
        })

        print(f"\n✅ Completed {test_question['id']}")

    if all_results:
        summary_file = create_summary_markdown(all_results, output_dir)

        print(f"\n{'=' * 80}")
        print("2x2 COMPARISON COMPLETE")
        print(f"{'=' * 80}")
        print(f"\n📊 {len(all_results)} questions × 4 cells = {len(all_results) * 4} runs")
        print(f"📄 Summary: {summary_file}")
        print(f"📁 All files: {output_dir}")


if __name__ == "__main__":
    main()
