"""
Full dual-pipeline bivariate comparison — 10 cross-topic questions.

Runs BOTH architectures for each question and saves side-by-side results:
  - OLD: detailed_report  (detailed_analysis.py — no bivariate)
  - NEW: analytical_essay (quantitative_engine.py — Phase 4 SES + Phase 5 cross-dataset)

Output: data/results/architecture_comparison_full_bivariate/
  00_SUMMARY.md          — aggregate comparison table
  q{N}_{topic}.md        — per-question side-by-side output
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, '/workspaces/navegador')

from run_analysis import run_analysis

# ---------------------------------------------------------------------------
# Test questions (same 10 as compare_architectures_final.py)
# ---------------------------------------------------------------------------

TEST_QUESTIONS = [
    {
        "id": "q1_religion_politics",
        "query": "¿Cómo se relacionan la religión y la política en México?",
        "query_en": "How do religion and politics relate in Mexico?",
        "topics": ["Religion", "Political Culture"],
        "variables": ["p2|REL", "p3|REL", "p4|REL", "p5|REL",
                      "p1|CUL", "p2|CUL", "p3|CUL", "p4|CUL", "p5|CUL"],
    },
    {
        "id": "q2_environment_economy",
        "query": "¿Cómo equilibran los mexicanos las preocupaciones ambientales con el desarrollo económico?",
        "query_en": "How do Mexicans balance environmental concerns with economic development?",
        "topics": ["Environment", "Economy"],
        "variables": ["p2|MED", "p4|MED", "p5|MED", "p6|MED",
                      "p1|ECO", "p2|ECO", "p3|ECO", "p4|ECO", "p5|ECO"],
    },
    {
        "id": "q3_education_poverty",
        "query": "¿Qué relación ven los mexicanos entre educación y pobreza?",
        "query_en": "What relationship do Mexicans see between education and poverty?",
        "topics": ["Education", "Poverty"],
        "variables": ["p2|EDU", "p3|EDU", "p4|EDU", "p5|EDU", "p6|EDU",
                      "p1|POB", "p2|POB", "p3|POB", "p4|POB"],
    },
    {
        "id": "q4_gender_family",
        "query": "¿Cómo están cambiando los roles de género en la familia mexicana?",
        "query_en": "How are gender roles changing in the Mexican family?",
        "topics": ["Gender", "Family"],
        "variables": ["p1|GEN", "p2|GEN", "p5|GEN", "p6|GEN",
                      "p1|FAM", "p2|FAM", "p3|FAM", "p4|FAM", "p5|FAM"],
    },
    {
        "id": "q5_migration_culture",
        "query": "¿Cómo afecta la migración a la identidad cultural mexicana?",
        "query_en": "How does migration affect Mexican cultural identity?",
        "topics": ["Migration", "Identity"],
        "variables": ["p1|MIG", "p2|MIG", "p9|MIG", "p13|MIG",
                      "p4|IDE", "p6|IDE", "p7|IDE", "p8|IDE", "p9|IDE"],
    },
    {
        "id": "q6_health_poverty",
        "query": "¿Cómo se relaciona el acceso a la salud con la pobreza en México?",
        "query_en": "How does health access relate to poverty in Mexico?",
        "topics": ["Health", "Poverty"],
        "variables": ["p1|SAL", "p2|SAL", "p3|SAL", "p4|SAL", "p5|SAL",
                      "p1|POB", "p2|POB", "p3|POB", "p4|POB"],
    },
    {
        "id": "q7_democracy_corruption",
        "query": "¿Qué piensan los mexicanos sobre la relación entre democracia y corrupción?",
        "query_en": "What do Mexicans think about the relationship between democracy and corruption?",
        "topics": ["Political Culture", "Corruption"],
        "variables": ["p1|CUL", "p2|CUL", "p3|CUL", "p4|CUL", "p5|CUL",
                      "p2|COR", "p3|COR", "p5|COR", "p8|COR"],
    },
    {
        "id": "q8_indigenous_discrimination",
        "query": "¿Cómo perciben los mexicanos la discriminación hacia pueblos indígenas?",
        "query_en": "How do Mexicans perceive discrimination against indigenous peoples?",
        "topics": ["Indigenous", "Human Rights"],
        "variables": ["p1|IND", "p2|IND", "p3|IND", "p4|IND", "p5|IND",
                      "p2|DER", "p3|DER", "p4|DER", "p5|DER"],
    },
    {
        "id": "q9_technology_education",
        "query": "¿Cómo impacta la tecnología en la educación según los mexicanos?",
        "query_en": "How does technology impact education according to Mexicans?",
        "topics": ["Technology", "Education"],
        "variables": ["p2|SOC", "p4|SOC", "p6|SOC", "p7|SOC",
                      "p2|EDU", "p3|EDU", "p4|EDU", "p5|EDU", "p6|EDU"],
    },
    {
        "id": "q10_security_justice",
        "query": "¿Qué relación ven los mexicanos entre seguridad pública y justicia?",
        "query_en": "What relationship do Mexicans see between public security and justice?",
        "topics": ["Security", "Justice"],
        "variables": ["p3|SEG", "p4|SEG", "p5|SEG", "p6|SEG", "p7|SEG",
                      "p1|JUS", "p2|JUS", "p4|JUS", "p7|JUS"],
    },
]

OUTPUT_DIR = Path("/workspaces/navegador/data/results/architecture_comparison_full_bivariate")
MODEL = "gpt-4.1-mini-2025-04-14"


# ---------------------------------------------------------------------------
# Runners
# ---------------------------------------------------------------------------

def run_one(analysis_type: str, variables: List[str], query: str) -> Dict[str, Any]:
    start = time.time()
    try:
        result = run_analysis(
            analysis_type=analysis_type,
            selected_variables=variables,
            user_query=query,
            model_name=MODEL,
            temperature=0.4,
        )
        latency_ms = (time.time() - start) * 1000
        ok = result.get('success', False)
        print(f"      {'✅' if ok else '❌'} {analysis_type} — {latency_ms:.0f}ms")
        return {"success": ok, "result": result, "latency_ms": latency_ms,
                "error": result.get('error')}
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        print(f"      ❌ {analysis_type} exception — {latency_ms:.0f}ms: {e}")
        return {"success": False, "result": {}, "latency_ms": latency_ms, "error": str(e)}


# ---------------------------------------------------------------------------
# Helpers to extract structured data from result dicts
# ---------------------------------------------------------------------------

def _quant(run: Dict) -> Dict:
    """Return the quantitative_report sub-dict from a run result."""
    wrapper = run.get("result", {})
    inner = wrapper.get("results", wrapper)
    q = inner.get("quantitative_report", {})
    if hasattr(q, 'model_dump'):
        return q.model_dump()
    return q if isinstance(q, dict) else {}


def _cross_biv(run: Dict) -> Optional[Dict]:
    """Return cross_dataset_bivariate dict, or None."""
    q = _quant(run)
    return q.get("cross_dataset_bivariate")


def _fault_lines(run: Dict) -> Dict:
    return _quant(run).get("demographic_fault_lines") or {}


def _cramers_strength(v: float) -> str:
    if v < 0.1:
        return "weak"
    if v < 0.3:
        return "moderate"
    return "strong"


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _render_fault_lines_table(fl: Dict) -> str:
    if not fl:
        return "*No significant SES fault lines detected.*\n"
    rows = "\n".join(
        f"| {dim} | {info['mean_cramers_v']:.3f} ({_cramers_strength(info['mean_cramers_v'])}) "
        f"| {info['max_cramers_v']:.3f} | {info['n_significant']} |"
        for dim, info in fl.items()
    )
    return (
        "| Dimension | Mean Cramér's V | Max Cramér's V | Variables |\n"
        "|-----------|----------------|----------------|----------|\n"
        + rows + "\n"
    )


def _render_cross_dataset_table(cb: Optional[Dict]) -> str:
    if not cb:
        return "*No cross-dataset pairs estimated (variables may share a survey).*\n"
    has_patterns = any(est.get('top_contrasts') for est in cb.values())
    lines = []
    for est in cb.values():
        tc = est.get('top_contrasts')
        pattern = "—"
        if has_patterns and tc:
            top_cat = next(iter(tc))
            info = tc[top_cat]
            pattern = (
                f"\"{top_cat}\": {info['min_pct']*100:.0f}% "
                f"(\"{info['min_when']}\") → {info['max_pct']*100:.0f}% "
                f"(\"{info['max_when']}\")"
            )
        if has_patterns:
            lines.append(
                f"| {est['var_a']} × {est['var_b']} "
                f"| {est['cramers_v']:.3f} ({_cramers_strength(est['cramers_v'])}) "
                f"| {est['p_value']:.3f} | {pattern} | {est['n_simulated']} |"
            )
        else:
            lines.append(
                f"| {est['var_a']} × {est['var_b']} "
                f"| {est['cramers_v']:.3f} ({_cramers_strength(est['cramers_v'])}) "
                f"| {est['p_value']:.3f} | {est['n_simulated']} |"
            )
    rows = "\n".join(lines)
    if has_patterns:
        header = (
            "| Variable Pair | Cramér's V | p-value | Key Pattern | n sim |\n"
            "|---------------|------------|---------|-------------|-------|\n"
        )
    else:
        header = (
            "| Variable Pair | Cramér's V | p-value | n sim |\n"
            "|---------------|------------|---------|-------|\n"
        )
    return header + rows + "\n\n*Estimates via SES-bridge simulation (OrderedModel / MNLogit).*\n"


def save_question_markdown(
    test_q: Dict,
    old_run: Dict,
    new_run: Dict,
    output_dir: Path,
) -> Path:
    q_id = test_q["id"]
    out = output_dir / f"{q_id}.md"

    old_q = _quant(old_run)
    new_q = _quant(new_run)
    fl = _fault_lines(new_run)
    cb = _cross_biv(new_run)

    new_biv_vars = sum(1 for v in new_q.get("variables", []) if v.get("bivariate_stats"))
    cross_pairs = len(cb) if cb else 0

    old_fmt = old_run.get("result", {}).get("formatted_report", "*No output*")
    new_fmt = new_run.get("result", {}).get("formatted_report", "*No output*")

    content = f"""# {q_id}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Query
**ES:** {test_q['query']}
**EN:** {test_q['query_en']}
**Topics:** {', '.join(test_q['topics'])}
**Variables:** {', '.join(test_q['variables'])}

---

## Performance Comparison

| Metric | OLD (detailed_report) | NEW (analytical_essay) |
|--------|----------------------|------------------------|
| Success | {'✅' if old_run['success'] else '❌'} | {'✅' if new_run['success'] else '❌'} |
| Latency | {old_run['latency_ms']:.0f} ms | {new_run['latency_ms']:.0f} ms |
| Variables Analyzed | {old_q.get('variable_count', '—')} | {new_q.get('variable_count', '—')} |
| Divergence Index | — | {new_q.get('divergence_index', 0):.0%} |
| SES Bivariate Vars | — | {new_biv_vars}/{new_q.get('variable_count', '?')} |
| Cross-Dataset Pairs | — | {cross_pairs} |

---

## NEW: Phase 4 — SES Demographic Fault Lines

{_render_fault_lines_table(fl)}

---

## NEW: Phase 5 — Cross-Dataset Bivariate Estimates

{_render_cross_dataset_table(cb)}

---

## OLD Architecture Output (detailed_report)

```
{old_fmt[:5000]}
```
{'*(Truncated from ' + str(len(old_fmt)) + ' chars)*' if len(old_fmt) > 5000 else ''}

---

## NEW Architecture Output (analytical_essay)

```
{new_fmt[:5000]}
```
{'*(Truncated from ' + str(len(new_fmt)) + ' chars)*' if len(new_fmt) > 5000 else ''}
"""

    out.write_text(content, encoding='utf-8')
    return out


def save_summary(all_results: List[Dict], output_dir: Path) -> Path:
    out = output_dir / "00_SUMMARY.md"

    rows = []
    for r in all_results:
        q = r["question"]
        old = r["old_run"]
        new = r["new_run"]
        new_q = _quant(new)
        fl = _fault_lines(new)
        cb = _cross_biv(new)
        top_dim = next(iter(fl), "—")
        top_v = fl[top_dim]["mean_cramers_v"] if top_dim != "—" else 0.0
        biv_vars = sum(1 for v in new_q.get("variables", []) if v.get("bivariate_stats"))
        cross_pairs = len(cb) if cb else 0

        rows.append(
            f"| [{q['id']}](./{q['id']}.md) "
            f"| {'✅' if old['success'] else '❌'} {old['latency_ms']/1000:.1f}s "
            f"| {'✅' if new['success'] else '❌'} {new['latency_ms']/1000:.1f}s "
            f"| {new_q.get('divergence_index', 0):.0%} "
            f"| {biv_vars}/{new_q.get('variable_count', '?')} "
            f"| {cross_pairs} "
            f"| {top_dim} (V={top_v:.2f}) |"
        )

    ok_old = [r for r in all_results if r["old_run"]["success"]]
    ok_new = [r for r in all_results if r["new_run"]["success"]]
    avg_old = sum(r["old_run"]["latency_ms"] for r in ok_old) / max(len(ok_old), 1)
    avg_new = sum(r["new_run"]["latency_ms"] for r in ok_new) / max(len(ok_new), 1)
    avg_biv = (
        sum(sum(1 for v in _quant(r["new_run"]).get("variables", []) if v.get("bivariate_stats"))
            for r in ok_new) / max(len(ok_new), 1)
    )
    avg_cross = (
        sum(len(_cross_biv(r["new_run"]) or {}) for r in ok_new) / max(len(ok_new), 1)
    )

    content = f"""# Full Bivariate Comparison — Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Model:** {MODEL}

---

## Results

| Question | OLD ✓/time | NEW ✓/time | Divergence | SES Biv Vars | Cross Pairs | Top Fault Line |
|----------|-----------|-----------|------------|--------------|-------------|----------------|
{chr(10).join(rows)}

---

## Aggregate Stats

| Metric | OLD (detailed_report) | NEW (analytical_essay) |
|--------|----------------------|------------------------|
| Success Rate | {len(ok_old)}/{len(all_results)} | {len(ok_new)}/{len(all_results)} |
| Avg Latency | {avg_old:.0f} ms ({avg_old/1000:.1f}s) | {avg_new:.0f} ms ({avg_new/1000:.1f}s) |
| Avg SES Bivariate Vars | — | {avg_biv:.1f} |
| Avg Cross-Dataset Pairs | — | {avg_cross:.1f} |

---

## Individual Reports

{chr(10).join(f'- [{r["question"]["id"]}](./{r["question"]["id"]}.md) — {r["question"]["query_en"]}' for r in all_results)}
"""

    out.write_text(content, encoding='utf-8')
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output: {OUTPUT_DIR}")
    print(f"Model:  {MODEL}")
    print(f"Questions: {len(TEST_QUESTIONS)}\n")

    all_results = []

    for i, test_q in enumerate(TEST_QUESTIONS, 1):
        print(f"[{i}/{len(TEST_QUESTIONS)}] {test_q['id']}")
        print(f"   {test_q['query_en']}")

        old_run = run_one("detailed_report", test_q["variables"], test_q["query"])
        new_run = run_one("analytical_essay", test_q["variables"], test_q["query"])

        cb = _cross_biv(new_run)
        print(f"   Cross-dataset pairs: {len(cb) if cb else 0}")

        save_question_markdown(test_q, old_run, new_run, OUTPUT_DIR)
        all_results.append({"question": test_q, "old_run": old_run, "new_run": new_run})

    summary_path = save_summary(all_results, OUTPUT_DIR)
    print(f"\nSummary: {summary_path}")

    ok_new = sum(1 for r in all_results if r["new_run"]["success"])
    ok_old = sum(1 for r in all_results if r["old_run"]["success"])
    print(f"OLD: {ok_old}/{len(all_results)} ✅")
    print(f"NEW: {ok_new}/{len(all_results)} ✅")


if __name__ == "__main__":
    main()
