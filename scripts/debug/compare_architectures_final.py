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

# 10 comprehensive test questions spanning multiple topics
TEST_QUESTIONS = [
    {
        "id": "q1_religion_politics",
        "query": "¿Cómo se relacionan la religión y la política en México?",
        "query_en": "How do religion and politics relate in Mexico?",
        "topics": ["Religion", "Political Culture"],
        "variables": [
            "p1|REL",    # Importancia religión
            "p2|REL",    # Práctica religiosa
            "p1|CUL",    # Situación económica país
            "p3|CUL",    # Situación política actual
        ]
    },
    {
        "id": "q2_environment_economy",
        "query": "¿Cómo equilibran los mexicanos las preocupaciones ambientales con el desarrollo económico?",
        "query_en": "How do Mexicans balance environmental concerns with economic development?",
        "topics": ["Environment", "Economy"],
        "variables": [
            "p1|MED",    # Preocupación ambiental
            "p2|MED",    # Cambio climático
            "p1|ECO",    # Situación económica personal
            "p2|ECO",    # Expectativas económicas
        ]
    },
    {
        "id": "q3_education_poverty",
        "query": "¿Qué relación ven los mexicanos entre educación y pobreza?",
        "query_en": "What relationship do Mexicans see between education and poverty?",
        "topics": ["Education", "Poverty"],
        "variables": [
            "p1|EDU",    # Calidad educativa
            "p2|EDU",    # Acceso educación
            "p1|POB",    # Percepción pobreza
            "p2|POB",    # Causas pobreza
        ]
    },
    {
        "id": "q4_gender_family",
        "query": "¿Cómo están cambiando los roles de género en la familia mexicana?",
        "query_en": "How are gender roles changing in the Mexican family?",
        "topics": ["Gender", "Family"],
        "variables": [
            "p1|GEN",    # Roles de género
            "p2|GEN",    # Igualdad género
            "p1|FAM",    # Estructura familiar
            "p2|FAM",    # Roles familiares
        ]
    },
    {
        "id": "q5_migration_culture",
        "query": "¿Cómo afecta la migración a la identidad cultural mexicana?",
        "query_en": "How does migration affect Mexican cultural identity?",
        "topics": ["Migration", "Identity"],
        "variables": [
            "p1|MIG",    # Opinión sobre migración
            "p2|MIG",    # Causas migración
            "p5_1|IDE",  # Emociones sobre México
            "p7|IDE",    # Orgullo ser mexicano
        ]
    },
    {
        "id": "q6_health_poverty",
        "query": "¿Cómo se relaciona el acceso a la salud con la pobreza en México?",
        "query_en": "How does health access relate to poverty in Mexico?",
        "topics": ["Health", "Poverty"],
        "variables": [
            "p1|SAL",    # Acceso servicios salud
            "p2|SAL",    # Calidad servicios salud
            "p1|POB",    # Situación laboral
            "p3|POB",    # Desigualdad
        ]
    },
    {
        "id": "q7_democracy_corruption",
        "query": "¿Qué piensan los mexicanos sobre la relación entre democracia y corrupción?",
        "query_en": "What do Mexicans think about the relationship between democracy and corruption?",
        "topics": ["Political Culture", "Corruption"],
        "variables": [
            "p1|CUL",    # Situación política
            "p3|CUL",    # Descripción situación política
            "p2|COR",    # Percepción corrupción
            "p3|COR",    # Experiencia corrupción
        ]
    },
    {
        "id": "q8_indigenous_discrimination",
        "query": "¿Cómo perciben los mexicanos la discriminación hacia pueblos indígenas?",
        "query_en": "How do Mexicans perceive discrimination against indigenous peoples?",
        "topics": ["Indigenous", "Human Rights"],
        "variables": [
            "p1|IND",    # Derechos indígenas
            "p2|IND",    # Discriminación indígena
            "p1|DER",    # Derechos humanos
            "p2|DER",    # Discriminación general
        ]
    },
    {
        "id": "q9_technology_education",
        "query": "¿Cómo impacta la tecnología en la educación según los mexicanos?",
        "query_en": "How does technology impact education according to Mexicans?",
        "topics": ["Technology", "Education"],
        "variables": [
            "p1|SOC",    # Acceso tecnología
            "p2|SOC",    # Uso internet
            "p1|EDU",    # Calidad educativa
            "p3|EDU",    # Tecnología en educación
        ]
    },
    {
        "id": "q10_security_justice",
        "query": "¿Qué relación ven los mexicanos entre seguridad pública y justicia?",
        "query_en": "What relationship do Mexicans see between public security and justice?",
        "topics": ["Security", "Justice"],
        "variables": [
            "p1|SEG",    # Percepción inseguridad
            "p2|SEG",    # Confianza policía
            "p1|JUS",    # Acceso justicia
            "p2|JUS",    # Confianza sistema judicial
        ]
    }
]


def run_old_architecture(selected_variables: List[str], query: str) -> Dict[str, Any]:
    """Run through FIXED OLD architecture."""
    print(f"\n🏛️  OLD (FIXED): detailed_report")

    start_time = time.time()

    try:
        result = run_analysis(
            analysis_type="detailed_report",
            selected_variables=selected_variables,
            user_query=query
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        print(f"   {'✅ Success' if result.get('success') else '❌ Failed'} - {latency_ms:.0f}ms")

        return {
            "success": result.get('success', False),
            "result": result,
            "latency_ms": latency_ms,
            "error": result.get('error')
        }

    except Exception as e:
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        print(f"   ❌ Exception - {latency_ms:.0f}ms: {e}")

        return {
            "success": False,
            "result": {},
            "latency_ms": latency_ms,
            "error": str(e)
        }


def run_new_architecture(selected_variables: List[str], query: str) -> Dict[str, Any]:
    """Run through ENHANCED NEW architecture."""
    print(f"\n🚀 NEW (ENHANCED): analytical_essay")

    start_time = time.time()

    try:
        result = run_analysis(
            analysis_type="analytical_essay",
            selected_variables=selected_variables,
            user_query=query,
            model_name='gpt-4.1-mini-2025-04-14',
            temperature=0.4
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        print(f"   {'✅ Success' if result.get('success') else '❌ Failed'} - {latency_ms:.0f}ms")

        return {
            "success": result.get('success', False),
            "result": result,
            "latency_ms": latency_ms,
            "error": result.get('error')
        }

    except Exception as e:
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        print(f"   ❌ Exception - {latency_ms:.0f}ms: {e}")

        return {
            "success": False,
            "result": {},
            "latency_ms": latency_ms,
            "error": str(e)
        }


def extract_metrics(old_result: Dict, new_result: Dict) -> Dict[str, Any]:
    """Extract comparable metrics."""

    metrics = {
        "old": {
            "success": old_result.get("success", False),
            "latency_ms": old_result.get("latency_ms", 0),
            "error": old_result.get("error"),
        },
        "new": {
            "success": new_result.get("success", False),
            "latency_ms": new_result.get("latency_ms", 0),
            "error": new_result.get("error"),
        }
    }

    # OLD metrics
    old_data = old_result.get("result", {})
    metrics["old"]["has_output"] = bool(old_data.get("formatted_report"))
    if old_data.get("formatted_report"):
        metrics["old"]["output_length"] = len(old_data["formatted_report"])

    # Track validation results
    metrics["old"]["valid_variables"] = old_data.get("valid_variables", [])
    metrics["old"]["invalid_variables"] = old_data.get("invalid_variables", [])

    # NEW metrics
    new_data = new_result.get("result", {})
    if "essay" in new_data:
        essay = new_data["essay"]
        metrics["new"]["essay_sections"] = len([
            k for k in ["summary", "introduction", "prevailing_view",
                       "counterargument", "implications"]
            if k in essay and essay[k]
        ])
        metrics["new"]["has_output"] = bool(new_data.get("formatted_report"))

        if new_data.get("formatted_report"):
            metrics["new"]["output_length"] = len(new_data["formatted_report"])

        if "prevailing_view" in essay and "counterargument" in essay:
            metrics["new"]["prevailing_view_length"] = len(essay["prevailing_view"])
            metrics["new"]["counterargument_length"] = len(essay["counterargument"])
            metrics["new"]["dialectical_ratio"] = len(essay["counterargument"]) / max(len(essay["prevailing_view"]), 1)

    if "quantitative_report" in new_data:
        quant = new_data["quantitative_report"]
        metrics["new"]["variables_analyzed"] = quant.get("variable_count", 0)
        metrics["new"]["divergence_index"] = quant.get("divergence_index", 0)
        metrics["new"]["shape_summary"] = quant.get("shape_summary", {})

    return metrics


def create_comparison_markdown(
    test_question: Dict,
    old_result: Dict,
    new_result: Dict,
    metrics: Dict,
    output_dir: Path
) -> Path:
    """Create comparison markdown for one question."""

    question_id = test_question["id"]
    output_file = output_dir / f"{question_id}_comparison.md"

    content = f"""# Cross-Topic Comparison: {question_id}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Test Question

**Spanish:** {test_question['query']}

**English:** {test_question['query_en']}

**Topics Covered:** {', '.join(test_question['topics'])}

**Variables Used:** {', '.join(test_question['variables'])}

---

## Performance Metrics

### OLD Architecture (FIXED detailed_report)

- **Success:** {'✅ Yes' if metrics['old']['success'] else '❌ No'}
- **Latency:** {metrics['old']['latency_ms']:.0f} ms ({metrics['old']['latency_ms']/1000:.1f}s)
- **Has Output:** {metrics['old'].get('has_output', False)}
- **Output Length:** {metrics['old'].get('output_length', 0)} characters
- **Valid Variables:** {len(metrics['old'].get('valid_variables', []))}
- **Invalid Variables:** {len(metrics['old'].get('invalid_variables', []))}
- **Error:** {metrics['old'].get('error') or 'None'}

### NEW Architecture (ENHANCED analytical_essay)

- **Success:** {'✅ Yes' if metrics['new']['success'] else '❌ No'}
- **Latency:** {metrics['new']['latency_ms']:.0f} ms ({metrics['new']['latency_ms']/1000:.1f}s)
- **Variables Analyzed:** {metrics['new'].get('variables_analyzed', 'N/A')}
- **Divergence Index:** {metrics['new'].get('divergence_index', 'N/A')}
- **Shape Summary:** {str(metrics['new'].get('shape_summary', 'N/A'))}
- **Essay Sections:** {metrics['new'].get('essay_sections', 'N/A')}/5 complete
- **Has Output:** {metrics['new'].get('has_output', False)}
- **Output Length:** {metrics['new'].get('output_length', 0)} characters
- **Dialectical Ratio:** {metrics['new'].get('dialectical_ratio', 'N/A') if isinstance(metrics['new'].get('dialectical_ratio'), str) else f"{metrics['new'].get('dialectical_ratio', 0):.2f}"}
- **Error:** {metrics['new'].get('error') or 'None'}

### Comparison

"""

    if metrics['old']['latency_ms'] > 0 and metrics['new']['latency_ms'] > 0:
        diff_ms = metrics['new']['latency_ms'] - metrics['old']['latency_ms']
        pct_diff = (metrics['new']['latency_ms'] / metrics['old']['latency_ms'] - 1) * 100
        faster_slower = 'faster ⚡' if diff_ms < 0 else 'slower 🐌'
        content += f"- **Latency Difference:** {abs(diff_ms):.0f} ms ({abs(pct_diff):.1f}% {faster_slower})\n"

    if metrics['old'].get('output_length') and metrics['new'].get('output_length'):
        content += f"- **Output Length Difference:** {metrics['new']['output_length'] - metrics['old']['output_length']} characters\n"

    content += "\n---\n\n## Analysis Outputs\n\n### OLD Architecture Output\n\n"

    old_formatted = old_result.get("result", {}).get("formatted_report", "No output generated")
    if old_formatted and old_formatted != "No output generated":
        content += f"```\n{old_formatted[:6000]}\n```\n\n"
        if len(old_formatted) > 6000:
            content += f"*(Truncated from {len(old_formatted)} characters)*\n\n"
    else:
        content += f"**No output generated**\n\nError: {old_result.get('error', 'Unknown')}\n\n"

    content += "---\n\n### NEW Architecture Output\n\n"

    new_formatted = new_result.get("result", {}).get("formatted_report", "No output generated")
    if new_formatted and new_formatted != "No output generated":
        content += f"```\n{new_formatted[:6000]}\n```\n\n"
        if len(new_formatted) > 6000:
            content += f"*(Truncated from {len(new_formatted)} characters)*\n\n"
    else:
        content += f"**No output generated**\n\nError: {new_result.get('error', 'Unknown')}\n\n"

    output_file.write_text(content, encoding='utf-8')
    return output_file


def create_summary_markdown(all_results: List[Dict], output_dir: Path) -> Path:
    """Create summary comparing all questions."""

    output_file = output_dir / "00_FINAL_SUMMARY.md"

    content = f"""# Final Architecture Comparison Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Test Questions:** {len(all_results)} cross-topic questions

**Architectures Tested:**
- OLD (FIXED): detailed_report with validation + real data
- NEW (ENHANCED): analytical_essay with auto-correction

---

## Quick Results

| Question | Topics | OLD | NEW | OLD Time (s) | NEW Time (s) |
|----------|--------|-----|-----|--------------|--------------|
"""

    for result in all_results:
        q_id = result["question"]["id"]
        topics = "/".join(result["question"]["topics"][:2])  # First 2 topics
        old_success = "✅" if result["metrics"]["old"]["success"] else "❌"
        new_success = "✅" if result["metrics"]["new"]["success"] else "❌"
        old_time = result["metrics"]["old"]["latency_ms"] / 1000
        new_time = result["metrics"]["new"]["latency_ms"] / 1000

        content += f"| {q_id} | {topics} | {old_success} | {new_success} | {old_time:.1f} | {new_time:.1f} |\n"

    content += "\n---\n\n## Overall Statistics\n\n"

    old_success_results = [r for r in all_results if r["metrics"]["old"]["success"]]
    new_success_results = [r for r in all_results if r["metrics"]["new"]["success"]]

    old_latencies = [r["metrics"]["old"]["latency_ms"] for r in old_success_results]
    new_latencies = [r["metrics"]["new"]["latency_ms"] for r in new_success_results]

    if old_latencies:
        content += f"**OLD Average Latency:** {sum(old_latencies) / len(old_latencies):.0f} ms ({sum(old_latencies) / len(old_latencies) / 1000:.1f}s)\n\n"
    if new_latencies:
        content += f"**NEW Average Latency:** {sum(new_latencies) / len(new_latencies):.0f} ms ({sum(new_latencies) / len(new_latencies) / 1000:.1f}s)\n\n"

    old_success_rate = len(old_success_results) / len(all_results) * 100 if all_results else 0
    new_success_rate = len(new_success_results) / len(all_results) * 100 if all_results else 0

    content += f"**OLD Success Rate:** {old_success_rate:.0f}% ({len(old_success_results)}/{len(all_results)})\n\n"
    content += f"**NEW Success Rate:** {new_success_rate:.0f}% ({len(new_success_results)}/{len(all_results)})\n\n"

    if new_success_results:
        avg_divergence = sum(r["metrics"]["new"].get("divergence_index", 0) for r in new_success_results) / len(new_success_results)
        avg_sections = sum(r["metrics"]["new"].get("essay_sections", 0) for r in new_success_results) / len(new_success_results)

        content += f"**NEW Average Divergence Index:** {avg_divergence:.3f}\n\n"
        content += f"**NEW Average Essay Completeness:** {avg_sections:.1f}/5 sections\n\n"

    content += "---\n\n## Individual Reports\n\n"

    for result in all_results:
        q_id = result["question"]["id"]
        query_en = result["question"]["query_en"]
        old_status = "✅" if result["metrics"]["old"]["success"] else "❌"
        new_status = "✅" if result["metrics"]["new"]["success"] else "❌"
        content += f"- [{q_id}](./{q_id}_comparison.md) - {query_en}\n"
        content += f"  - OLD: {old_status} | NEW: {new_status}\n"

    content += "\n---\n\n## Key Findings\n\n"
    content += """
### Both Architectures Now:
- ✅ Validate variables before processing
- ✅ Use real data (no mock/placeholder data)
- ✅ Provide transparent error messages
- ✅ Maintain data integrity
- ❌ No silent substitution of variables

### Differences:
- **OLD:** Strict validation → suggests corrections → user must fix
- **NEW:** Smart validation → auto-corrects typos → proceeds with warnings

### Cross-Topic Analysis:
These tests used questions spanning multiple survey topics, which is more representative
of real-world usage where users ask complex questions that require data from multiple sources.

"""

    output_file.write_text(content, encoding='utf-8')
    return output_file


def main():
    """Main execution."""

    print("=" * 80)
    print("FINAL ARCHITECTURE COMPARISON - 10 CROSS-TOPIC QUESTIONS")
    print("Testing: FIXED OLD + ENHANCED NEW")
    print("=" * 80)

    output_dir = Path("/workspaces/navegador/data/results/architecture_comparison_final")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Output: {output_dir}\n")

    all_results = []

    for i, test_question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}/{len(TEST_QUESTIONS)}: {test_question['id']}")
        print(f"Topics: {', '.join(test_question['topics'])}")
        print(f"Query: {test_question['query']}")
        print(f"{'=' * 80}")

        old_result = run_old_architecture(test_question["variables"], test_question["query"])
        new_result = run_new_architecture(test_question["variables"], test_question["query"])

        metrics = extract_metrics(old_result, new_result)

        comparison_file = create_comparison_markdown(
            test_question, old_result, new_result, metrics, output_dir
        )

        all_results.append({
            "question": test_question,
            "old_result": old_result,
            "new_result": new_result,
            "metrics": metrics,
            "comparison_file": str(comparison_file)
        })

        print(f"\n✅ Completed {test_question['id']}")

    if all_results:
        summary_file = create_summary_markdown(all_results, output_dir)

        print(f"\n{'=' * 80}")
        print("COMPARISON COMPLETE")
        print(f"{'=' * 80}")
        print(f"\n📊 {len(all_results)} questions tested")
        print(f"📄 Summary: {summary_file}")
        print(f"📁 All files: {output_dir}")


if __name__ == "__main__":
    main()
