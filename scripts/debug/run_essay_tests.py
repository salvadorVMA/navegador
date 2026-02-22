"""
Save analytical essay outputs for the 10 cross-topic test questions.

Runs the analytical_essay pipeline for each question and writes one
clean markdown file per question to data/results/essay_tests/.

Output: data/results/essay_tests/
  00_SUMMARY.md          — run metadata and pass/fail table
  q{N}_{topic}.md        — essay for each question
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, '/workspaces/navegador')

from run_analysis import run_analysis

# ---------------------------------------------------------------------------
# Test questions (same 10 used in the dual-pipeline comparison)
# ---------------------------------------------------------------------------

TEST_QUESTIONS = [
    {
        "id": "q1_religion_politics",
        "query": "¿Cómo se relacionan la religión y la política en México?",
        "query_en": "How do religion and politics relate in Mexico?",
        "variables": ["p2|REL", "p3|REL", "p4|REL", "p5|REL",
                      "p1|CUL", "p2|CUL", "p3|CUL", "p4|CUL", "p5|CUL"],
    },
    {
        "id": "q2_environment_economy",
        "query": "¿Cómo equilibran los mexicanos las preocupaciones ambientales con el desarrollo económico?",
        "query_en": "How do Mexicans balance environmental concerns with economic development?",
        "variables": ["p2|MED", "p4|MED", "p5|MED", "p6|MED",
                      "p1|ECO", "p2|ECO", "p3|ECO", "p4|ECO", "p5|ECO"],
    },
    {
        "id": "q3_education_poverty",
        "query": "¿Qué relación ven los mexicanos entre educación y pobreza?",
        "query_en": "What relationship do Mexicans see between education and poverty?",
        "variables": ["p2|EDU", "p3|EDU", "p4|EDU", "p5|EDU", "p6|EDU",
                      "p1|POB", "p2|POB", "p3|POB", "p4|POB"],
    },
    {
        "id": "q4_gender_family",
        "query": "¿Cómo están cambiando los roles de género en la familia mexicana?",
        "query_en": "How are gender roles changing in the Mexican family?",
        "variables": ["p1|GEN", "p2|GEN", "p5|GEN", "p6|GEN",
                      "p1|FAM", "p2|FAM", "p3|FAM", "p4|FAM", "p5|FAM"],
    },
    {
        "id": "q5_migration_culture",
        "query": "¿Cómo afecta la migración a la identidad cultural mexicana?",
        "query_en": "How does migration affect Mexican cultural identity?",
        "variables": ["p1|MIG", "p2|MIG", "p9|MIG", "p13|MIG",
                      "p4|IDE", "p6|IDE", "p7|IDE", "p8|IDE", "p9|IDE"],
    },
    {
        "id": "q6_health_poverty",
        "query": "¿Cómo se relaciona el acceso a la salud con la pobreza en México?",
        "query_en": "How does health access relate to poverty in Mexico?",
        "variables": ["p1|SAL", "p2|SAL", "p3|SAL", "p4|SAL", "p5|SAL",
                      "p1|POB", "p2|POB", "p3|POB", "p4|POB"],
    },
    {
        "id": "q7_democracy_corruption",
        "query": "¿Qué piensan los mexicanos sobre la relación entre democracia y corrupción?",
        "query_en": "What do Mexicans think about the relationship between democracy and corruption?",
        "variables": ["p1|CUL", "p2|CUL", "p3|CUL", "p4|CUL", "p5|CUL",
                      "p2|COR", "p3|COR", "p5|COR", "p8|COR"],
    },
    {
        "id": "q8_indigenous_discrimination",
        "query": "¿Cómo perciben los mexicanos la discriminación hacia pueblos indígenas?",
        "query_en": "How do Mexicans perceive discrimination against indigenous peoples?",
        "variables": ["p1|IND", "p2|IND", "p3|IND", "p4|IND", "p5|IND",
                      "p2|DER", "p3|DER", "p4|DER", "p5|DER"],
    },
    {
        "id": "q9_technology_education",
        "query": "¿Cómo impacta la tecnología en la educación según los mexicanos?",
        "query_en": "How does technology impact education according to Mexicans?",
        "variables": ["p2|SOC", "p4|SOC", "p6|SOC", "p7|SOC",
                      "p2|EDU", "p3|EDU", "p4|EDU", "p5|EDU", "p6|EDU"],
    },
    {
        "id": "q10_security_justice",
        "query": "¿Qué relación ven los mexicanos entre seguridad pública y justicia?",
        "query_en": "What relationship do Mexicans see between public security and justice?",
        "variables": ["p3|SEG", "p4|SEG", "p5|SEG", "p6|SEG", "p7|SEG",
                      "p1|JUS", "p2|JUS", "p4|JUS", "p7|JUS"],
    },
]

OUTPUT_DIR = Path("/workspaces/navegador/data/results/essay_tests")
MODEL = "gpt-4.1-mini-2025-04-14"


def run_essay(q: dict) -> Dict[str, Any]:
    start = time.time()
    result = run_analysis(
        analysis_type='analytical_essay',
        selected_variables=q['variables'],
        user_query=q['query'],
        model_name=MODEL,
    )
    elapsed = time.time() - start
    return {**result, '_elapsed_ms': int(elapsed * 1000)}


def save_essay_markdown(q: dict, result: Dict[str, Any], output_dir: Path) -> Path:
    out = output_dir / f"{q['id']}.md"
    success = result.get('success', False)
    elapsed = result.get('_elapsed_ms', 0)

    if success:
        report = result.get('formatted_report', '*(no formatted_report)*')
    else:
        error = result.get('error', 'unknown error')
        report = f"**FAILED:** {error}"

    # Extract cross-dataset pair count from results
    quant = result.get('results', {}).get('quantitative_report')
    cross_biv = None
    if quant is not None:
        if isinstance(quant, dict):
            cross_biv = quant.get('cross_dataset_bivariate')
        else:
            cross_biv = getattr(quant, 'cross_dataset_bivariate', None)
    cross_pairs = len(cross_biv) if cross_biv else 0

    content = f"""# {q['id']}

**Query (ES):** {q['query']}
**Query (EN):** {q['query_en']}
**Variables:** {', '.join(q['variables'])}
**Status:** {'✅ success' if success else '❌ failed'}
**Time:** {elapsed}ms | **Cross-dataset pairs:** {cross_pairs}

---

{report}
"""
    out.write_text(content, encoding='utf-8')
    return out


def save_summary(results: List[Dict], output_dir: Path) -> Path:
    out = output_dir / "00_SUMMARY.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    passed = sum(1 for r in results if r['result'].get('success'))
    total = len(results)

    rows = []
    for r in results:
        q = r['question']
        res = r['result']
        success = res.get('success', False)
        elapsed = res.get('_elapsed_ms', 0)
        quant = res.get('results', {}).get('quantitative_report')
        cross_biv = None
        if quant is not None:
            cross_biv = (quant.get('cross_dataset_bivariate') if isinstance(quant, dict)
                         else getattr(quant, 'cross_dataset_bivariate', None))
        cross_pairs = len(cross_biv) if cross_biv else 0
        status = '✅' if success else '❌'
        rows.append(
            f"| [{q['id']}]({q['id']}.md) | {q['query_en'][:50]}… "
            f"| {status} | {elapsed}ms | {cross_pairs} |"
        )

    table = "\n".join(rows)
    content = f"""# Analytical Essay Test Run

**Date:** {now}
**Model:** {MODEL}
**Questions:** {total}
**Passed:** {passed}/{total}

| Question | Query | Status | Time | Cross-pairs |
|----------|-------|--------|------|-------------|
{table}
"""
    out.write_text(content, encoding='utf-8')
    return out


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output: {OUTPUT_DIR}")
    print(f"Model:  {MODEL}")
    print(f"Questions: {len(TEST_QUESTIONS)}\n")

    all_results = []
    passed = 0

    for i, q in enumerate(TEST_QUESTIONS, 1):
        print(f"[{i}/{len(TEST_QUESTIONS)}] {q['id']}")
        print(f"   {q['query_en']}")
        print(f"   Variables: {q['variables']}")

        result = run_essay(q)
        success = result.get('success', False)
        elapsed = result.get('_elapsed_ms', 0)

        quant = result.get('results', {}).get('quantitative_report')
        cross_biv = None
        if quant is not None:
            cross_biv = (quant.get('cross_dataset_bivariate') if isinstance(quant, dict)
                         else getattr(quant, 'cross_dataset_bivariate', None))
        cross_pairs = len(cross_biv) if cross_biv else 0

        status = '✅' if success else '❌'
        print(f"   {status} analytical_essay — {elapsed}ms | cross-dataset pairs: {cross_pairs}")

        if not success:
            print(f"   ERROR: {result.get('error', 'unknown')}")

        save_essay_markdown(q, result, OUTPUT_DIR)
        all_results.append({'question': q, 'result': result})
        if success:
            passed += 1

    summary_path = save_summary(all_results, OUTPUT_DIR)
    print(f"\nSummary: {summary_path}")
    print(f"Essays: {passed}/{len(TEST_QUESTIONS)} ✅")


if __name__ == "__main__":
    main()
