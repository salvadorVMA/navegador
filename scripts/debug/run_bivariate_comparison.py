"""
Bivariate-enabled architecture comparison — 10 cross-topic questions.
Runs the NEW analytical_essay pipeline (which now includes SES bivariate
demographic breakdowns) and saves results to a dedicated folder.
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, '/workspaces/navegador')

from run_analysis import run_analysis

# Same 10 test questions as compare_architectures_final.py
TEST_QUESTIONS = [
    {
        "id": "q1_religion_politics",
        "query": "¿Cómo se relacionan la religión y la política en México?",
        "query_en": "How do religion and politics relate in Mexico?",
        "topics": ["Religion", "Political Culture"],
        "variables": ["p1|REL", "p2|REL", "p1|CUL", "p3|CUL"],
    },
    {
        "id": "q2_environment_economy",
        "query": "¿Cómo equilibran los mexicanos las preocupaciones ambientales con el desarrollo económico?",
        "query_en": "How do Mexicans balance environmental concerns with economic development?",
        "topics": ["Environment", "Economy"],
        "variables": ["p1|MED", "p2|MED", "p1|ECO", "p2|ECO"],
    },
    {
        "id": "q3_education_poverty",
        "query": "¿Qué relación ven los mexicanos entre educación y pobreza?",
        "query_en": "What relationship do Mexicans see between education and poverty?",
        "topics": ["Education", "Poverty"],
        "variables": ["p1|EDU", "p2|EDU", "p1|POB", "p2|POB"],
    },
    {
        "id": "q4_gender_family",
        "query": "¿Cómo están cambiando los roles de género en la familia mexicana?",
        "query_en": "How are gender roles changing in the Mexican family?",
        "topics": ["Gender", "Family"],
        "variables": ["p1|GEN", "p2|GEN", "p1|FAM", "p2|FAM"],
    },
    {
        "id": "q5_migration_culture",
        "query": "¿Cómo afecta la migración a la identidad cultural mexicana?",
        "query_en": "How does migration affect Mexican cultural identity?",
        "topics": ["Migration", "Identity"],
        "variables": ["p1|MIG", "p2|MIG", "p5_1|IDE", "p7|IDE"],
    },
    {
        "id": "q6_health_poverty",
        "query": "¿Cómo se relaciona el acceso a la salud con la pobreza en México?",
        "query_en": "How does health access relate to poverty in Mexico?",
        "topics": ["Health", "Poverty"],
        "variables": ["p1|SAL", "p2|SAL", "p1|POB", "p3|POB"],
    },
    {
        "id": "q7_democracy_corruption",
        "query": "¿Qué piensan los mexicanos sobre la relación entre democracia y corrupción?",
        "query_en": "What do Mexicans think about the relationship between democracy and corruption?",
        "topics": ["Political Culture", "Corruption"],
        "variables": ["p1|CUL", "p3|CUL", "p2|COR", "p3|COR"],
    },
    {
        "id": "q8_indigenous_discrimination",
        "query": "¿Cómo perciben los mexicanos la discriminación hacia pueblos indígenas?",
        "query_en": "How do Mexicans perceive discrimination against indigenous peoples?",
        "topics": ["Indigenous", "Human Rights"],
        "variables": ["p1|IND", "p2|IND", "p1|DER", "p2|DER"],
    },
    {
        "id": "q9_technology_education",
        "query": "¿Cómo impacta la tecnología en la educación según los mexicanos?",
        "query_en": "How does technology impact education according to Mexicans?",
        "topics": ["Technology", "Education"],
        "variables": ["p1|SOC", "p2|SOC", "p1|EDU", "p3|EDU"],
    },
    {
        "id": "q10_security_justice",
        "query": "¿Qué relación ven los mexicanos entre seguridad pública y justicia?",
        "query_en": "What relationship do Mexicans see between public security and justice?",
        "topics": ["Security", "Justice"],
        "variables": ["p1|SEG", "p2|SEG", "p1|JUS", "p2|JUS"],
    },
]

OUTPUT_DIR = Path("/workspaces/navegador/data/results/architecture_comparison_bivariate")


def run_essay_with_bivariate(variables: List[str], query: str) -> Dict[str, Any]:
    start = time.time()
    try:
        result = run_analysis(
            analysis_type="analytical_essay",
            selected_variables=variables,
            user_query=query,
            model_name='gpt-4.1-mini-2025-04-14',
            temperature=0.4,
        )
        latency_ms = (time.time() - start) * 1000
        print(f"   {'✅ Success' if result.get('success') else '❌ Failed'} — {latency_ms:.0f}ms")
        return {"success": result.get('success', False), "result": result,
                "latency_ms": latency_ms, "error": result.get('error')}
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        print(f"   ❌ Exception — {latency_ms:.0f}ms: {e}")
        return {"success": False, "result": {}, "latency_ms": latency_ms, "error": str(e)}


def save_essay_markdown(test_q: Dict, run: Dict, output_dir: Path) -> Path:
    q_id = test_q["id"]
    out = output_dir / f"{q_id}_bivariate.md"

    wrapper = run.get("result", {})
    results = wrapper.get("results", wrapper)
    quant = results.get("quantitative_report", {})
    fault_lines = quant.get("demographic_fault_lines") or {}
    variables_analyzed = quant.get("variable_count", "N/A")
    divergence = quant.get("divergence_index", 0)
    shape_summary = quant.get("shape_summary", {})

    essay = results.get("essay", {})
    prev_len = len(essay.get("prevailing_view", ""))
    counter_len = len(essay.get("counterargument", ""))
    dialectical_ratio = counter_len / max(prev_len, 1)

    # Bivariate variables with breakdowns
    biv_vars = [
        v for v in quant.get("variables", [])
        if v.get("bivariate_stats")
    ]

    # Fault lines summary rows
    fl_rows = ""
    for dim, info in fault_lines.items():
        strength = (
            "weak" if info["mean_cramers_v"] < 0.1
            else "moderate" if info["mean_cramers_v"] < 0.3
            else "strong"
        )
        fl_rows += (
            f"| {dim} | {info['mean_cramers_v']:.3f} ({strength}) "
            f"| {info['max_cramers_v']:.3f} | {info['n_significant']} |\n"
        )

    fault_lines_table = ""
    if fl_rows:
        fault_lines_table = (
            "### Demographic Fault Lines\n\n"
            "| Dimension | Mean Cramér's V | Max Cramér's V | Variables |\n"
            "|-----------|----------------|----------------|----------|\n"
            + fl_rows
        )

    formatted = wrapper.get("formatted_report", "No output generated")

    content = f"""# Bivariate Essay: {q_id}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Architecture:** analytical_essay + SES bivariate breakdowns

## Query
**ES:** {test_q['query']}
**EN:** {test_q['query_en']}
**Topics:** {', '.join(test_q['topics'])}
**Variables Requested:** {', '.join(test_q['variables'])}

---

## Performance

| Metric | Value |
|--------|-------|
| Success | {'✅ Yes' if run['success'] else '❌ No'} |
| Latency | {run['latency_ms']:.0f} ms ({run['latency_ms']/1000:.1f}s) |
| Variables Analyzed | {variables_analyzed} |
| Divergence Index | {divergence:.1%} |
| Shape Summary | {shape_summary} |
| Essay Sections | {len([k for k in ['summary','introduction','prevailing_view','counterargument','implications'] if essay.get(k)])}/5 |
| Dialectical Ratio | {dialectical_ratio:.2f} |
| Variables with Bivariate Breakdowns | {len(biv_vars)} |
| Error | {run.get('error') or 'None'} |

---

{fault_lines_table}

---

## Full Essay Output

```
{formatted[:8000]}
```
{'*(Truncated from ' + str(len(formatted)) + ' characters)*' if len(formatted) > 8000 else ''}
"""

    out.write_text(content, encoding='utf-8')
    return out


def save_summary(all_results: List[Dict], output_dir: Path) -> Path:
    out = output_dir / "00_SUMMARY.md"

    rows = ""
    for r in all_results:
        q = r["question"]
        run = r["run"]
        wrapper = run.get("result", {})
        inner = wrapper.get("results", wrapper)
        quant = inner.get("quantitative_report", {})
        biv_count = sum(
            1 for v in quant.get("variables", []) if v.get("bivariate_stats")
        )
        fl = quant.get("demographic_fault_lines") or {}
        top_dim = next(iter(fl), "—")
        top_v = fl[top_dim]["mean_cramers_v"] if top_dim != "—" else 0

        rows += (
            f"| {q['id']} | {'✅' if run['success'] else '❌'} "
            f"| {run['latency_ms']/1000:.1f}s "
            f"| {quant.get('divergence_index', 0):.0%} "
            f"| {biv_count}/{quant.get('variable_count','?')} "
            f"| {top_dim} (V={top_v:.2f}) |\n"
        )

    success_runs = [r for r in all_results if r["run"]["success"]]
    avg_latency = (
        sum(r["run"]["latency_ms"] for r in success_runs) / len(success_runs)
        if success_runs else 0
    )
    biv_totals = [
        sum(1 for v in
            r["run"].get("result", {}).get("results",
            r["run"].get("result", {})).get("quantitative_report", {}).get("variables", [])
            if v.get("bivariate_stats"))
        for r in success_runs
    ]
    avg_biv = sum(biv_totals) / len(biv_totals) if biv_totals else 0

    content = f"""# Bivariate Architecture Comparison — Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Pipeline:** analytical_essay + Phase 2 SES bivariate analysis

---

## Results

| Question | OK | Time | Divergence | Biv. Vars | Top Fault Line |
|----------|----|------|------------|-----------|----------------|
{rows}

---

## Aggregate Stats

- **Success Rate:** {len(success_runs)}/{len(all_results)} ({len(success_runs)/len(all_results):.0%})
- **Average Latency:** {avg_latency:.0f} ms ({avg_latency/1000:.1f}s)
- **Avg Variables with Bivariate Breakdowns:** {avg_biv:.1f}

---

## Individual Reports

"""
    for r in all_results:
        q = r["question"]
        content += f"- [{q['id']}](./{q['id']}_bivariate.md) — {q['query_en']}\n"

    out.write_text(content, encoding='utf-8')
    return out


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 80)
    print("BIVARIATE ARCHITECTURE COMPARISON — 10 QUESTIONS")
    print("Pipeline: analytical_essay + SES demographic breakdowns")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 80)

    all_results = []

    for i, q in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[{i}/{len(TEST_QUESTIONS)}] {q['id']}")
        print(f"  Query: {q['query']}")
        run = run_essay_with_bivariate(q["variables"], q["query"])
        f = save_essay_markdown(q, run, OUTPUT_DIR)
        all_results.append({"question": q, "run": run, "file": str(f)})
        print(f"  Saved: {f.name}")

    summary = save_summary(all_results, OUTPUT_DIR)
    print(f"\n{'=' * 80}")
    print(f"DONE — {len(all_results)} questions")
    print(f"Summary: {summary}")
    print("=" * 80)


if __name__ == "__main__":
    main()
