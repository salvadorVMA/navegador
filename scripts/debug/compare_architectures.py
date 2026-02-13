"""
Comparison script for evaluating old vs. new analysis architecture.

This script compares:
- OLD: detailed_report (traditional detailed_analysis.py)
- NEW: analytical_essay (quantitative_engine.py + analytical_essay.py)

For each test question:
1. Selects relevant variables using _variable_selector
2. Runs through OLD architecture
3. Runs through NEW architecture
4. Collects metrics: latency, tokens, quality indicators
5. Generates comparison markdown files
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, '/workspaces/navegador')

from variable_selector import _variable_selector, tmp_topic_st
from run_analysis import run_analysis
from utility_functions import get_answer

# Test questions designed to pull data from available datasets
TEST_QUESTIONS = [
    {
        "id": "q1_identity",
        "query": "¿Qué piensan los mexicanos sobre su identidad nacional y sus valores?",
        "query_en": "What do Mexicans think about their national identity and values?",
        "expected_topics": ["IDENTIDAD_Y_VALORES"]
    },
    {
        "id": "q2_environment",
        "query": "¿Cuál es la opinión pública sobre el medio ambiente y el cambio climático en México?",
        "query_en": "What is public opinion on the environment and climate change in Mexico?",
        "expected_topics": ["MEDIO_AMBIENTE"]
    },
    {
        "id": "q3_poverty",
        "query": "¿Cómo ven los mexicanos el problema de la pobreza y la desigualdad?",
        "query_en": "How do Mexicans view the problem of poverty and inequality?",
        "expected_topics": ["POBREZA"]
    },
    {
        "id": "q4_religion",
        "query": "¿Qué tan importante es la religión en la vida de los mexicanos?",
        "query_en": "How important is religion in the lives of Mexicans?",
        "expected_topics": ["RELIGION_SECULARIZACION_Y_LAICIDAD"]
    },
    {
        "id": "q5_political_culture",
        "query": "¿Qué opinan los mexicanos sobre la democracia y las instituciones políticas?",
        "query_en": "What do Mexicans think about democracy and political institutions?",
        "expected_topics": ["CULTURA_POLITICA"]
    }
]


def select_variables_for_query(query: str) -> Dict[str, Any]:
    """
    Select variables for a query using the standard variable selector.

    Returns:
        dict with keys: topic_ids, variables_dict, grade_dict, selected_variables
    """
    print(f"\n📊 Selecting variables for: {query}")

    try:
        topic_ids, variables_dict, grade_dict = _variable_selector(
            query,
            tmp_topic_st,
            'gpt-4.1-mini-2025-04-14',
            top_vals=20,  # Reduced for faster testing
            use_simultaneous_retrieval=True
        )

        # Get top-graded variables (grade >= 2.0)
        selected_variables = [
            var_id for var_id, grade in grade_dict.items()
            if grade >= 2.0
        ][:10]  # Limit to top 10 for consistent comparison

        print(f"✅ Selected {len(selected_variables)} variables from topics: {topic_ids}")

        return {
            "topic_ids": topic_ids,
            "variables_dict": variables_dict,
            "grade_dict": grade_dict,
            "selected_variables": selected_variables
        }

    except Exception as e:
        print(f"❌ Error selecting variables: {e}")
        import traceback
        traceback.print_exc()
        return {
            "topic_ids": [],
            "variables_dict": {},
            "grade_dict": {},
            "selected_variables": []
        }


def run_old_architecture(selected_variables: List[str], query: str) -> Dict[str, Any]:
    """
    Run through OLD architecture: detailed_report.

    Returns:
        dict with keys: success, result, latency_ms, error
    """
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

        return {
            "success": False,
            "result": {},
            "latency_ms": latency_ms,
            "error": str(e)
        }


def run_new_architecture(selected_variables: List[str], query: str) -> Dict[str, Any]:
    """
    Run through NEW architecture: analytical_essay (quantitative + dialectical essay).

    Returns:
        dict with keys: success, result, latency_ms, error
    """
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

    # Try to extract token counts if available
    # OLD architecture might have tokens in results
    old_data = old_result.get("result", {})
    if "results" in old_data:
        old_results = old_data["results"]
        # Look for token usage in various possible locations
        metrics["old"]["has_output"] = bool(old_data.get("formatted_report"))

    # NEW architecture has quantitative_report and essay
    new_data = new_result.get("result", {})
    if "essay" in new_data:
        essay = new_data["essay"]
        metrics["new"]["essay_sections"] = len([
            k for k in ["summary", "introduction", "prevailing_view",
                       "counterargument", "implications"]
            if k in essay
        ])
        metrics["new"]["has_output"] = bool(new_data.get("formatted_report"))

    if "quantitative_report" in new_data:
        quant = new_data["quantitative_report"]
        metrics["new"]["variables_analyzed"] = quant.get("variable_count", 0)
        metrics["new"]["divergence_index"] = quant.get("divergence_index", 0)

    return metrics


def create_comparison_markdown(
    test_question: Dict,
    variable_selection: Dict,
    old_result: Dict,
    new_result: Dict,
    metrics: Dict,
    output_dir: Path
) -> Path:
    """
    Create a detailed markdown comparison file for one test question.
    """

    question_id = test_question["id"]
    output_file = output_dir / f"{question_id}_comparison.md"

    content = f"""# Architecture Comparison: {question_id}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Test Question

**Spanish:** {test_question['query']}

**English:** {test_question['query_en']}

**Expected Topics:** {', '.join(test_question['expected_topics'])}

---

## Variable Selection

**Topics Found:** {', '.join(variable_selection.get('topic_ids', []))}

**Variables Selected:** {len(variable_selection.get('selected_variables', []))}

**Variable IDs:** {', '.join(variable_selection.get('selected_variables', [])[:10])}

---

## Performance Metrics

### OLD Architecture (detailed_report)

- **Success:** {metrics['old']['success']}
- **Latency:** {metrics['old']['latency_ms']:.0f} ms
- **Has Output:** {metrics['old'].get('has_output', 'Unknown')}
- **Error:** {metrics['old'].get('error', 'None')}

### NEW Architecture (analytical_essay)

- **Success:** {metrics['new']['success']}
- **Latency:** {metrics['new']['latency_ms']:.0f} ms
- **Variables Analyzed:** {metrics['new'].get('variables_analyzed', 'N/A')}
- **Divergence Index:** {metrics['new'].get('divergence_index', 'N/A')}
- **Essay Sections:** {metrics['new'].get('essay_sections', 'N/A')}/5
- **Has Output:** {metrics['new'].get('has_output', 'Unknown')}
- **Error:** {metrics['new'].get('error', 'None')}

### Comparison

- **Latency Difference:** {metrics['new']['latency_ms'] - metrics['old']['latency_ms']:.0f} ms
  ({((metrics['new']['latency_ms'] / metrics['old']['latency_ms'] - 1) * 100) if metrics['old']['latency_ms'] > 0 else 0:.1f}% {'faster' if metrics['new']['latency_ms'] < metrics['old']['latency_ms'] else 'slower'})

---

## Output Comparison

### OLD Architecture Output

"""

    # Add old output
    old_formatted = old_result.get("result", {}).get("formatted_report", "No output generated")
    content += f"```\n{old_formatted[:5000]}\n```\n\n"  # Truncate to 5000 chars
    if len(old_formatted) > 5000:
        content += f"*(Output truncated: {len(old_formatted)} total characters)*\n\n"

    content += "### NEW Architecture Output\n\n"

    # Add new output
    new_formatted = new_result.get("result", {}).get("formatted_report", "No output generated")
    content += f"```\n{new_formatted[:5000]}\n```\n\n"
    if len(new_formatted) > 5000:
        content += f"*(Output truncated: {len(new_formatted)} total characters)*\n\n"

    # Add structured essay sections if available
    if "essay" in new_result.get("result", {}):
        essay = new_result["result"]["essay"]
        content += "### NEW Architecture - Structured Essay Sections\n\n"

        for section in ["summary", "introduction", "prevailing_view", "counterargument", "implications"]:
            if section in essay:
                content += f"#### {section.replace('_', ' ').title()}\n\n"
                content += f"{essay[section]}\n\n"

    content += "---\n\n## Quantitative Report (NEW Architecture Only)\n\n"

    if "quantitative_report" in new_result.get("result", {}):
        quant = new_result["result"]["quantitative_report"]
        content += f"**Variables:** {quant.get('variable_count', 0)}\n\n"
        content += f"**Divergence Index:** {quant.get('divergence_index', 0):.2f}\n\n"
        content += f"**Shape Summary:** {quant.get('shape_summary', {})}\n\n"
        content += f"**Overall Narrative:** {quant.get('overall_narrative', 'N/A')}\n\n"

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

| Question | OLD Success | NEW Success | OLD Latency (ms) | NEW Latency (ms) | Speedup |
|----------|-------------|-------------|------------------|------------------|---------|
"""

    for result in all_results:
        q_id = result["question"]["id"]
        old_success = "✅" if result["metrics"]["old"]["success"] else "❌"
        new_success = "✅" if result["metrics"]["new"]["success"] else "❌"
        old_lat = result["metrics"]["old"]["latency_ms"]
        new_lat = result["metrics"]["new"]["latency_ms"]
        speedup = f"{((old_lat / new_lat - 1) * 100):.1f}%" if new_lat > 0 and old_lat > 0 else "N/A"

        content += f"| {q_id} | {old_success} | {new_success} | {old_lat:.0f} | {new_lat:.0f} | {speedup} |\n"

    content += "\n---\n\n## Average Metrics\n\n"

    # Calculate averages
    old_latencies = [r["metrics"]["old"]["latency_ms"] for r in all_results if r["metrics"]["old"]["success"]]
    new_latencies = [r["metrics"]["new"]["latency_ms"] for r in all_results if r["metrics"]["new"]["success"]]

    if old_latencies:
        content += f"**OLD Average Latency:** {sum(old_latencies) / len(old_latencies):.0f} ms\n\n"
    if new_latencies:
        content += f"**NEW Average Latency:** {sum(new_latencies) / len(new_latencies):.0f} ms\n\n"

    old_success_rate = sum(1 for r in all_results if r["metrics"]["old"]["success"]) / len(all_results) * 100
    new_success_rate = sum(1 for r in all_results if r["metrics"]["new"]["success"]) / len(all_results) * 100

    content += f"**OLD Success Rate:** {old_success_rate:.0f}%\n\n"
    content += f"**NEW Success Rate:** {new_success_rate:.0f}%\n\n"

    content += "---\n\n## Individual Comparisons\n\n"

    for result in all_results:
        q_id = result["question"]["id"]
        content += f"- [{q_id}](./{q_id}_comparison.md)\n"

    content += "\n---\n\n## Architecture Details\n\n"
    content += """
### OLD Architecture: detailed_report

- Uses `detailed_analysis.py`
- Traditional LLM-based analysis pipeline
- May include multiple LLM calls for different aspects
- Integrates ChromaDB for semantic search

### NEW Architecture: analytical_essay

- **Phase 1:** Pure computational quantitative engine (no LLM)
  - Analyzes distribution shapes (consensus/lean/polarized/dispersed)
  - Calculates HHI (concentration index)
  - Identifies minority opinions
  - Computes divergence index

- **Phase 2:** Single LLM call for dialectical essay
  - Structured output: summary, introduction, prevailing view, counterargument, implications
  - Enforces nuance through counterargument >= prevailing view
  - Evidence-grounded with exact percentages from quantitative report

"""

    output_file.write_text(content, encoding='utf-8')
    print(f"📄 Created summary file: {output_file}")

    return output_file


def main():
    """Main execution function."""

    print("=" * 80)
    print("ARCHITECTURE COMPARISON TEST")
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
        print(f"{'=' * 80}")

        # Step 1: Select variables
        variable_selection = select_variables_for_query(test_question["query"])

        if not variable_selection["selected_variables"]:
            print(f"⚠️  No variables selected, skipping this question")
            continue

        # Step 2: Run OLD architecture
        old_result = run_old_architecture(
            variable_selection["selected_variables"],
            test_question["query"]
        )

        # Step 3: Run NEW architecture
        new_result = run_new_architecture(
            variable_selection["selected_variables"],
            test_question["query"]
        )

        # Step 4: Extract metrics
        metrics = extract_metrics(old_result, new_result)

        # Step 5: Create comparison markdown
        comparison_file = create_comparison_markdown(
            test_question,
            variable_selection,
            old_result,
            new_result,
            metrics,
            output_dir
        )

        # Store results
        all_results.append({
            "question": test_question,
            "variable_selection": variable_selection,
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
