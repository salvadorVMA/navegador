"""
Simplified comparison script with hardcoded variables.

Compares OLD vs NEW architecture without needing variable_selector.
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, '/workspaces/navegador')

# Import after adding to path
from run_analysis import run_analysis

# Test questions with HARDCODED variable IDs (from dataset knowledge)
# These are real variables from the surveys
TEST_QUESTIONS = [
    {
        "id": "q1_identity",
        "query": "¿Qué piensan los mexicanos sobre su identidad nacional y sus valores?",
        "query_en": "What do Mexicans think about their national identity and values?",
        "variables": [
            "p5_1|IDE",  # Emociones sobre México
            "p5_2|IDE",  # Sentimientos hacia México
            "p7|IDE",    # Orgullo de ser mexicano
            "p8|IDE",    # Identidad nacional
        ]
    },
    {
        "id": "q2_environment",
        "query": "¿Cuál es la opinión pública sobre el medio ambiente y el cambio climático en México?",
        "query_en": "What is public opinion on the environment and climate change in Mexico?",
        "variables": [
            "p1|MED",    # Preocupación ambiental
            "p2|MED",    # Cambio climático
            "p3|MED",    # Acciones ambientales
            "p7|MED",    # Responsabilidad ambiental
        ]
    },
    {
        "id": "q3_poverty",
        "query": "¿Cómo ven los mexicanos el problema de la pobreza y la desigualdad?",
        "query_en": "How do Mexicans view the problem of poverty and inequality?",
        "variables": [
            "p1|POB",    # Percepción de pobreza
            "p2|POB",    # Causas de pobreza
            "p3|POB",    # Desigualdad
            "p5|POB",    # Soluciones a la pobreza
        ]
    },
    {
        "id": "q4_religion",
        "query": "¿Qué tan importante es la religión en la vida de los mexicanos?",
        "query_en": "How important is religion in the lives of Mexicans?",
        "variables": [
            "p1|REL",    # Importancia de religión
            "p2|REL",    # Práctica religiosa
            "p3|REL",    # Creencias religiosas
            "p5|REL",    # Religión y política
        ]
    },
    {
        "id": "q5_political_culture",
        "query": "¿Qué opinan los mexicanos sobre la democracia y las instituciones políticas?",
        "query_en": "What do Mexicans think about democracy and political institutions?",
        "variables": [
            "p1|CUL",    # Situación económica (CULTURA_POLITICA)
            "p2|CUL",    # Expectativas futuro
            "p3|CUL",    # Descripción situación política
            "p5|CUL",    # Orgullo de ser mexicano
        ]
    }
]


def run_old_architecture(selected_variables: List[str], query: str) -> Dict[str, Any]:
    """Run through OLD architecture: detailed_report."""
    print(f"\n🏛️  Running OLD architecture (detailed_report)...")

    start_time = time.time()

    try:
        result = run_analysis(
            analysis_type="detailed_report",
            selected_variables=selected_variables,
            user_query=query
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        print(f"✅ OLD completed in {latency_ms:.0f}ms")

        return {
            "success": result.get('success', False),
            "result": result,
            "latency_ms": latency_ms,
            "error": result.get('error')
        }

    except Exception as e:
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        print(f"❌ OLD failed after {latency_ms:.0f}ms: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "result": {},
            "latency_ms": latency_ms,
            "error": str(e)
        }


def run_new_architecture(selected_variables: List[str], query: str) -> Dict[str, Any]:
    """Run through NEW architecture: analytical_essay."""
    print(f"\n🚀 Running NEW architecture (analytical_essay)...")

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

        print(f"✅ NEW completed in {latency_ms:.0f}ms")

        return {
            "success": result.get('success', False),
            "result": result,
            "latency_ms": latency_ms,
            "error": result.get('error')
        }

    except Exception as e:
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        print(f"❌ NEW failed after {latency_ms:.0f}ms: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "result": {},
            "latency_ms": latency_ms,
            "error": str(e)
        }


def extract_metrics(old_result: Dict, new_result: Dict) -> Dict[str, Any]:
    """Extract comparable metrics from both results."""

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

    # OLD architecture metrics
    old_data = old_result.get("result", {})
    metrics["old"]["has_output"] = bool(old_data.get("formatted_report"))
    if old_data.get("formatted_report"):
        metrics["old"]["output_length"] = len(old_data["formatted_report"])

    # NEW architecture metrics
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

        # Essay section lengths
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
    """Create a detailed markdown comparison file for one test question."""

    question_id = test_question["id"]
    output_file = output_dir / f"{question_id}_comparison.md"

    content = f"""# Architecture Comparison: {question_id}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Test Question

**Spanish:** {test_question['query']}

**English:** {test_question['query_en']}

**Variables Used:** {', '.join(test_question['variables'])}

---

## Performance Metrics

### OLD Architecture (detailed_report)

- **Success:** {'✅ Yes' if metrics['old']['success'] else '❌ No'}
- **Latency:** {metrics['old']['latency_ms']:.0f} ms ({metrics['old']['latency_ms']/1000:.1f} seconds)
- **Has Output:** {metrics['old'].get('has_output', False)}
- **Output Length:** {metrics['old'].get('output_length', 0)} characters
- **Error:** {metrics['old'].get('error') or 'None'}

### NEW Architecture (analytical_essay)

- **Success:** {'✅ Yes' if metrics['new']['success'] else '❌ No'}
- **Latency:** {metrics['new']['latency_ms']:.0f} ms ({metrics['new']['latency_ms']/1000:.1f} seconds)
- **Variables Analyzed:** {metrics['new'].get('variables_analyzed', 'N/A')}
- **Divergence Index:** {metrics['new'].get('divergence_index', 'N/A')}
- **Shape Summary:** {str(metrics['new'].get('shape_summary', 'N/A'))}
- **Essay Sections:** {metrics['new'].get('essay_sections', 'N/A')}/5 complete
- **Has Output:** {metrics['new'].get('has_output', False)}
- **Output Length:** {metrics['new'].get('output_length', 0)} characters
- **Dialectical Ratio:** {metrics['new'].get('dialectical_ratio', 'N/A') if isinstance(metrics['new'].get('dialectical_ratio'), str) else f"{metrics['new'].get('dialectical_ratio', 0):.2f}"} (counterargument/prevailing_view)
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

    content += "\n---\n\n## Output Comparison\n\n### OLD Architecture Output\n\n"

    # Add old output
    old_formatted = old_result.get("result", {}).get("formatted_report", "No output generated")
    if old_formatted and old_formatted != "No output generated":
        content += f"```\n{old_formatted[:8000]}\n```\n\n"
        if len(old_formatted) > 8000:
            content += f"*(Output truncated from {len(old_formatted)} total characters)*\n\n"
    else:
        content += f"**No output generated**\n\nError: {old_result.get('error', 'Unknown')}\n\n"

    content += "---\n\n### NEW Architecture Output\n\n"

    # Add new formatted output
    new_formatted = new_result.get("result", {}).get("formatted_report", "No output generated")
    if new_formatted and new_formatted != "No output generated":
        content += f"```\n{new_formatted[:8000]}\n```\n\n"
        if len(new_formatted) > 8000:
            content += f"*(Output truncated from {len(new_formatted)} total characters)*\n\n"
    else:
        content += f"**No output generated**\n\nError: {new_result.get('error', 'Unknown')}\n\n"

    # Add structured essay sections if available
    if "essay" in new_result.get("result", {}):
        essay = new_result["result"]["essay"]
        content += "---\n\n### NEW Architecture - Structured Essay Sections\n\n"

        for section in ["summary", "introduction", "prevailing_view", "counterargument", "implications"]:
            if section in essay and essay[section]:
                content += f"#### {section.replace('_', ' ').title()}\n\n"
                content += f"{essay[section]}\n\n"
                content += f"*({len(essay[section])} characters)*\n\n"

    content += "---\n\n## Quantitative Report (NEW Architecture Only)\n\n"

    if "quantitative_report" in new_result.get("result", {}):
        quant = new_result["result"]["quantitative_report"]
        content += f"**Variables Analyzed:** {quant.get('variable_count', 0)}\n\n"
        content += f"**Divergence Index:** {quant.get('divergence_index', 0):.3f}\n\n"
        content += f"**Shape Summary:** {quant.get('shape_summary', {})}\n\n"
        content += f"**Overall Narrative:** {quant.get('overall_narrative', 'N/A')}\n\n"

        if "variables" in quant and quant["variables"]:
            content += "#### Variable Details\n\n"
            for var in quant["variables"][:5]:  # Show first 5
                content += f"**{var.get('var_id', 'Unknown')}**\n"
                content += f"- Question: {var.get('question_text', 'N/A')[:100]}...\n"
                content += f"- Shape: {var.get('shape', 'N/A')}\n"
                content += f"- Modal: {var.get('modal_response', 'N/A')} ({var.get('modal_percentage', 0):.1f}%)\n"
                content += f"- Margin: {var.get('margin', 0):.1f} percentage points\n\n"

    # Write file
    output_file.write_text(content, encoding='utf-8')
    print(f"📄 Created comparison file: {output_file}")

    return output_file


def create_summary_markdown(all_results: List[Dict], output_dir: Path) -> Path:
    """Create a summary markdown comparing all test questions."""

    output_file = output_dir / "00_SUMMARY.md"

    content = f"""# Architecture Comparison Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Total Questions Tested:** {len(all_results)}

---

## Overview

This comparison evaluates two analysis architectures:

1. **OLD Architecture:** `detailed_report` - Traditional detailed analysis pipeline
2. **NEW Architecture:** `analytical_essay` - Quantitative engine + dialectical essay

---

## Results Summary

| Question | OLD Success | NEW Success | OLD Latency (s) | NEW Latency (s) | Speedup |
|----------|-------------|-------------|-----------------|-----------------|---------|
"""

    for result in all_results:
        q_id = result["question"]["id"]
        old_success = "✅" if result["metrics"]["old"]["success"] else "❌"
        new_success = "✅" if result["metrics"]["new"]["success"] else "❌"
        old_lat = result["metrics"]["old"]["latency_ms"] / 1000
        new_lat = result["metrics"]["new"]["latency_ms"] / 1000

        if new_lat > 0 and old_lat > 0:
            speedup = f"{((old_lat / new_lat - 1) * 100):.1f}%" if new_lat < old_lat else f"-{((new_lat / old_lat - 1) * 100):.1f}%"
        else:
            speedup = "N/A"

        content += f"| {q_id} | {old_success} | {new_success} | {old_lat:.1f} | {new_lat:.1f} | {speedup} |\n"

    content += "\n---\n\n## Average Metrics\n\n"

    # Calculate averages
    old_success_results = [r for r in all_results if r["metrics"]["old"]["success"]]
    new_success_results = [r for r in all_results if r["metrics"]["new"]["success"]]

    old_latencies = [r["metrics"]["old"]["latency_ms"] for r in old_success_results]
    new_latencies = [r["metrics"]["new"]["latency_ms"] for r in new_success_results]

    if old_latencies:
        content += f"**OLD Average Latency:** {sum(old_latencies) / len(old_latencies):.0f} ms ({sum(old_latencies) / len(old_latencies) / 1000:.1f}s)\n\n"
    if new_latencies:
        content += f"**NEW Average Latency:** {sum(new_latencies) / len(new_latencies):.0f} ms ({sum(new_latencies) / len(new_latencies) / 1000:.1f}s)\n\n"

    if old_latencies and new_latencies:
        avg_old = sum(old_latencies) / len(old_latencies)
        avg_new = sum(new_latencies) / len(new_latencies)
        speedup = ((avg_old / avg_new - 1) * 100) if avg_new < avg_old else -((avg_new / avg_old - 1) * 100)
        content += f"**Average Speedup:** {abs(speedup):.1f}% {'faster' if speedup > 0 else 'slower'}\n\n"

    old_success_rate = len(old_success_results) / len(all_results) * 100 if all_results else 0
    new_success_rate = len(new_success_results) / len(all_results) * 100 if all_results else 0

    content += f"**OLD Success Rate:** {old_success_rate:.0f}% ({len(old_success_results)}/{len(all_results)})\n\n"
    content += f"**NEW Success Rate:** {new_success_rate:.0f}% ({len(new_success_results)}/{len(all_results)})\n\n"

    # Quality metrics for NEW architecture
    if new_success_results:
        avg_divergence = sum(r["metrics"]["new"].get("divergence_index", 0) for r in new_success_results) / len(new_success_results)
        avg_sections = sum(r["metrics"]["new"].get("essay_sections", 0) for r in new_success_results) / len(new_success_results)

        dialectical_ratios = [r["metrics"]["new"].get("dialectical_ratio", 0) for r in new_success_results if "dialectical_ratio" in r["metrics"]["new"] and isinstance(r["metrics"]["new"].get("dialectical_ratio"), (int, float))]
        avg_dialectical = sum(dialectical_ratios) / len(dialectical_ratios) if dialectical_ratios else 0

        content += f"**NEW Average Divergence Index:** {avg_divergence:.3f}\n\n"
        content += f"**NEW Average Essay Sections:** {avg_sections:.1f}/5\n\n"
        if avg_dialectical > 0:
            content += f"**NEW Average Dialectical Ratio:** {avg_dialectical:.2f} (counterargument/prevailing_view)\n\n"

    content += "---\n\n## Individual Comparisons\n\n"

    for result in all_results:
        q_id = result["question"]["id"]
        old_status = "✅" if result["metrics"]["old"]["success"] else "❌"
        new_status = "✅" if result["metrics"]["new"]["success"] else "❌"
        content += f"- [{q_id}](./{q_id}_comparison.md) - OLD: {old_status} | NEW: {new_status}\n"

    content += "\n---\n\n## Architecture Details\n\n"
    content += """
### OLD Architecture: detailed_report

**File:** `detailed_analysis.py`

**Approach:**
- Traditional LLM-based analysis pipeline
- May include multiple LLM calls for different aspects
- Integrates ChromaDB for semantic search
- Rich narrative generation

**Pros:**
- Comprehensive analysis
- Flexible output format
- Well-tested pipeline

**Cons:**
- Potentially higher latency
- May lack structural enforcement
- Token usage varies

---

### NEW Architecture: analytical_essay

**Files:** `quantitative_engine.py` + `analytical_essay.py`

**Approach:**

**Phase 1: Quantitative Engine** (Pure computation, no LLM)
- Analyzes distribution shapes: consensus (>65%), lean (50-65%), polarized (two >30%), dispersed (none >40%)
- Calculates HHI (Herfindahl-Hirschman Index) for response concentration
- Identifies minority opinions (>15% but not modal)
- Computes divergence index (fraction of non-consensus variables)
- Generates structured quantitative report

**Phase 2: Dialectical Essay** (Single LLM call)
- Takes quantitative report as input
- Structured output with 5 mandatory sections:
  1. **Summary:** Finding + caveat (2-3 sentences)
  2. **Introduction:** Scope and framing
  3. **Prevailing View:** Dominant patterns with exact percentages
  4. **Counterargument:** MUST be >= prevailing view length, presents divergence
  5. **Implications:** >= 2 alternative interpretations

**Enforced Rules:**
- Every percentage cited must appear in quantitative report (no invention)
- Counterargument >= prevailing view in length
- Polarized/dispersed variables get MORE attention than consensus
- Minority opinions (>15%) must be discussed explicitly
- No hedging language when data shows polarization

**Pros:**
- Enforces nuanced analysis through structure
- Evidence-grounded (exact percentages)
- Single LLM call reduces latency
- Quantitative phase is deterministic (cacheable)
- Quality control through Pydantic validation

**Cons:**
- More rigid structure
- Requires well-formed quantitative report
- May be less flexible for exploratory analysis

---

## Conclusion

{len([r for r in all_results if r["metrics"]["new"]["success"]])} out of {len(all_results)} tests succeeded with the NEW architecture.

Key findings:
- NEW architecture provides structured, evidence-grounded analysis
- Dialectical structure enforces presentation of divergence and nuance
- Single LLM call may reduce latency compared to traditional approach
- Quantitative phase provides deterministic, cacheable foundation

"""

    output_file.write_text(content, encoding='utf-8')
    print(f"📄 Created summary file: {output_file}")

    return output_file


def main():
    """Main execution function."""

    print("=" * 80)
    print("ARCHITECTURE COMPARISON TEST (Simplified)")
    print("=" * 80)

    # Create output directory
    output_dir = Path("/workspaces/navegador/data/results/architecture_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Output directory: {output_dir}")

    all_results = []

    # Run comparison for each test question
    for i, test_question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}/{len(TEST_QUESTIONS)}: {test_question['id']}")
        print(f"Query: {test_question['query']}")
        print(f"Variables: {test_question['variables']}")
        print(f"{'=' * 80}")

        # Run OLD architecture
        old_result = run_old_architecture(
            test_question["variables"],
            test_question["query"]
        )

        # Run NEW architecture
        new_result = run_new_architecture(
            test_question["variables"],
            test_question["query"]
        )

        # Extract metrics
        metrics = extract_metrics(old_result, new_result)

        # Create comparison markdown
        comparison_file = create_comparison_markdown(
            test_question,
            old_result,
            new_result,
            metrics,
            output_dir
        )

        # Store results
        all_results.append({
            "question": test_question,
            "old_result": old_result,
            "new_result": new_result,
            "metrics": metrics,
            "comparison_file": str(comparison_file)
        })

        print(f"\n✅ Completed {test_question['id']}")

    # Create summary
    if all_results:
        summary_file = create_summary_markdown(all_results, output_dir)

        print(f"\n{'=' * 80}")
        print("COMPARISON COMPLETE")
        print(f"{'=' * 80}")
        print(f"\n📊 {len(all_results)} questions tested")
        print(f"📄 Summary: {summary_file}")
        print(f"📁 All files: {output_dir}")
    else:
        print("\n❌ No results to summarize")


if __name__ == "__main__":
    main()
