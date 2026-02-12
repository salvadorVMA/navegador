# Survey Analysis Tools - Quick Reference

**Version:** 1.0
**Last Updated:** 2026-02-11

## TL;DR

```python
# Old way (still works)
results = run_analysis('detailed_report', variables, query)

# New way (opt-in, more accurate)
results = run_analysis('detailed_report_with_tools', variables, query,
                      enable_tools=True, enable_fact_checking=True)

# Check accuracy
print(f"Accuracy: {results.get('accuracy_rate', 'N/A')}%")
```

---

## Available Tools

### Metadata Tools

#### `get_variable_metadata(variable_id: str)`
Get exact variable information without LLM hallucination.

```python
result = get_variable_metadata.invoke({'variable_id': 'p1_1|MEX'})
# Returns: {'question_text': '...', 'response_categories': [...], ...}
```

#### `validate_variable_id_format(variable_id: str)`
Check if variable ID follows correct format.

```python
result = validate_variable_id_format.invoke({'variable_id': 'p1|ABC'})
# Returns: {'valid': True, 'pattern': 'pXX_YY|ABC'}
```

---

### Statistical Tools

#### `calculate_percentage_from_data(variable_id: str, response_category: str)`
Get exact percentage from actual data.

```python
result = calculate_percentage_from_data.invoke({
    'variable_id': 'p1_1|MEX',
    'response_category': 'Strongly agree'
})
# Returns: {'percentage': 45.2, 'count': 234, 'total': 518}
```

#### `calculate_pattern_strength(variable_ids: List[str], pattern_type: str)`
Quantify statistical strength of a pattern.

```python
result = calculate_pattern_strength.invoke({
    'variable_ids': ['p1|MEX', 'p2|MEX'],
    'pattern_type': 'similar'
})
# Returns: {'strength': 0.85, 'confidence': 'high', ...}
```

---

### Validation Tools

#### `validate_percentage_claim(claim: str, variable_id: str, tolerance: float)`
Fact-check an LLM's percentage claim.

```python
result = validate_percentage_claim.invoke({
    'claim': '85% of people agree',
    'variable_id': 'p1|MEX',
    'tolerance': 5.0
})
# Returns: {'valid': True, 'claimed': 85, 'actual': 83.2, 'difference': 1.8}
```

#### `cross_reference_variables(variable_ids: List[str])`
Find actual relationships between variables.

```python
result = cross_reference_variables.invoke({
    'variable_ids': ['p1|MEX', 'p2|MEX']
})
# Returns: {'relationships': [...], 'common_patterns': [...]}
```

---

### Analysis Tools

#### `analyze_variable_summary(variable_id: str)`
Get comprehensive variable statistics.

```python
result = analyze_variable_summary.invoke({'variable_id': 'p1|MEX'})
# Returns: {
#   'question': '...',
#   'top_response': '...',
#   'percentages': {...},
#   'total_responses': 500
# }
```

---

## Usage Patterns

### Pattern 1: Verify LLM Claims

```python
# LLM says: "85% of respondents agree (p1|MEX)"

# Verify it
verification = validate_percentage_claim.invoke({
    'claim': '85% agree',
    'variable_id': 'p1|MEX',
    'tolerance': 5.0
})

if verification['valid']:
    print(f"✓ Claim is accurate (actual: {verification['actual_percentage']}%)")
else:
    print(f"✗ Claim is inaccurate by {verification['difference']} percentage points")
```

### Pattern 2: Get Ground Truth

```python
# Instead of asking LLM "What percentage agreed?"
# Get it directly from data

result = calculate_percentage_from_data.invoke({
    'variable_id': 'p1_1|MEX',
    'response_category': 'Agree'
})

print(f"Ground truth: {result['percentage']}% agreed ({result['count']}/{result['total_responses']})")
```

### Pattern 3: Fact-Check Entire Analysis

```python
from tool_enhanced_analysis import fact_check_all_patterns

# After running analysis
patterns = analysis_results['patterns']

# Fact-check everything
fact_check = fact_check_all_patterns(patterns)

print(f"Accuracy: {fact_check['accuracy_rate']:.1f}%")
print(f"Patterns needing correction: {fact_check['patterns_needing_correction']}")
```

---

## Integration Examples

### Example 1: Add Tools to Existing Code

**Before:**
```python
from run_analysis import run_analysis

results = run_analysis(
    'detailed_report',
    selected_variables=['p1|MEX', 'p2|MEX'],
    user_query="What do people think about education?"
)
```

**After (with tools):**
```python
from run_analysis import run_analysis

results = run_analysis(
    'detailed_report_with_tools',  # New analysis type
    selected_variables=['p1|MEX', 'p2|MEX'],
    user_query="What do people think about education?",
    enable_tools=True,              # Enable tool calling
    enable_fact_checking=True       # Enable validation
)

# New metrics available
print(f"Analysis accuracy: {results['accuracy_rate']:.1f}%")
print(f"Tools used: {results['tool_statistics']['total_executions']}")
```

### Example 2: Gradual Adoption

```python
# Start with fact-checking only (no tool-calling during analysis)
results = run_analysis(
    'detailed_report_with_tools',
    selected_variables=vars,
    user_query=query,
    enable_tools=False,              # No tools during analysis
    enable_fact_checking=True        # But validate results after
)

# Later, enable full tool enhancement
results = run_analysis(
    'detailed_report_with_tools',
    selected_variables=vars,
    user_query=query,
    enable_tools=True,               # Tools during analysis
    enable_fact_checking=True        # And validation after
)
```

### Example 3: Comparison Mode

```python
import time

# Run both modes
start = time.time()
standard = run_analysis('detailed_report', vars, query)
standard_time = time.time() - start

start = time.time()
enhanced = run_analysis('detailed_report_with_tools', vars, query,
                       enable_tools=True, enable_fact_checking=True)
enhanced_time = time.time() - start

# Compare
print(f"Standard: {standard_time:.1f}s")
print(f"Enhanced: {enhanced_time:.1f}s (Accuracy: {enhanced.get('accuracy_rate')}%)")
print(f"Slowdown: {(enhanced_time/standard_time - 1) * 100:.1f}%")
```

---

## Monitoring

### Get Tool Statistics

```python
from survey_analysis_tools import get_tool_stats

stats = get_tool_stats()

print(f"Total tool calls: {stats['total_executions']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Avg execution time: {stats['avg_execution_time']:.3f}s")

print("\nMost used tools:")
for tool, count in sorted(stats['executions_by_tool'].items(),
                          key=lambda x: x[1], reverse=True):
    print(f"  {tool}: {count} calls")
```

### Integration with LangSmith

Tools automatically log to LangSmith when available:

```bash
# Set environment variable
export LANGSMITH_API_KEY="your-key"
export LANGSMITH_PROJECT="navegador-tools"

# Run analysis - tool traces appear in LangSmith dashboard
results = run_analysis('detailed_report_with_tools', vars, query)
```

---

## Troubleshooting

### Issue: Tools not being called

**Solution:** Check that you're using `'detailed_report_with_tools'` analysis type:

```python
# ✗ Wrong - uses standard analysis
run_analysis('detailed_report', vars, query)

# ✓ Correct - uses tool-enhanced analysis
run_analysis('detailed_report_with_tools', vars, query, enable_tools=True)
```

### Issue: Tools failing silently

**Solution:** Check tool statistics for failures:

```python
stats = get_tool_stats()
if 'failed_tools' in stats and stats['failed_tools']:
    print("Tools that failed:")
    for tool, count in stats['failed_tools'].items():
        print(f"  {tool}: {count} failures")
```

### Issue: Analysis slower than expected

**Solution:** Disable tools or fact-checking selectively:

```python
# Faster: Tools but no fact-checking
results = run_analysis('detailed_report_with_tools', vars, query,
                      enable_tools=True, enable_fact_checking=False)

# Fastest: Just fact-check results, no tools during analysis
results = run_analysis('detailed_report_with_tools', vars, query,
                      enable_tools=False, enable_fact_checking=True)
```

### Issue: FileNotFoundError when loading data

**Solution:** Ensure survey data file exists:

```python
from pathlib import Path

data_path = Path('/workspaces/navegador/data/encuestas/los_mex_dict.json')
if not data_path.exists():
    print(f"Data file not found at: {data_path}")
    # Check alternative paths or download data
```

---

## Performance Tips

### 1. Use Tools Selectively

```python
# For quick exploration - skip tools
results = run_analysis('detailed_report', vars, query)

# For public-facing results - use tools
results = run_analysis('detailed_report_with_tools', vars, query,
                      enable_tools=True, enable_fact_checking=True)
```

### 2. Cache Tool Results

Tools automatically cache data loading, but you can clear cache:

```python
from survey_analysis_tools import get_survey_data

# Clear cache to reload data
import survey_analysis_tools
survey_analysis_tools._survey_data_cache = None
```

### 3. Adjust Validation Tolerance

```python
# Strict validation (±2%)
results = run_analysis('detailed_report_with_tools', vars, query,
                      analysis_params={'validation_tolerance': 2.0})

# Lenient validation (±10%)
results = run_analysis('detailed_report_with_tools', vars, query,
                      analysis_params={'validation_tolerance': 10.0})
```

---

## Best Practices

### ✓ Do

- Use tools for public-facing or high-stakes analyses
- Check `accuracy_rate` in results
- Review `fact_check` details for patterns flagged as inaccurate
- Monitor tool statistics regularly
- Fall back to standard analysis if tools fail

### ✗ Don't

- Don't use tools for every quick exploration (overkill)
- Don't ignore tool failure warnings
- Don't set tolerance too high (defeats purpose of validation)
- Don't assume tools are always faster (they're more accurate)

---

## Code Templates

### Template: Custom Tool

```python
from langchain.tools import tool

@tool
def my_custom_analysis_tool(variable_id: str, param: str) -> dict:
    """
    Custom analysis tool description.

    Args:
        variable_id: Variable to analyze
        param: Custom parameter

    Returns:
        Dictionary with analysis results
    """
    import time
    start_time = time.time()

    try:
        # Your logic here
        result = {'variable_id': variable_id, 'result': 'success'}

        # Log execution
        from survey_analysis_tools import _tool_monitor
        _tool_monitor.log_execution(
            'my_custom_analysis_tool',
            {'variable_id': variable_id, 'param': param},
            result,
            time.time() - start_time,
            success=True
        )

        return result

    except Exception as e:
        _tool_monitor.log_execution(
            'my_custom_analysis_tool',
            {'variable_id': variable_id, 'param': param},
            None,
            time.time() - start_time,
            success=False,
            error=str(e)
        )
        return {'error': str(e)}

# Add to available tools
from survey_analysis_tools import AVAILABLE_TOOLS
AVAILABLE_TOOLS.append(my_custom_analysis_tool)
```

### Template: Manual Fact-Check

```python
from tool_enhanced_analysis import fact_check_pattern

# Your pattern from LLM
pattern = {
    'TITLE_SUMMARY': 'High agreement on education',
    'VARIABLE_STRING': 'p1|MEX,p2|MEX',
    'DESCRIPTION': '85% support increased funding (p1|MEX), 78% value quality (p2|MEX)'
}

# Fact-check it
check = fact_check_pattern(pattern)

print(f"Confidence: {check['confidence_score']:.0f}%")
print(f"Accurate: {check['is_accurate']}")

if check['corrections_needed']:
    print("Corrections needed:")
    for correction in check['corrections_needed']:
        print(f"  Variable {correction['variable']}: "
              f"Claimed {correction['claimed']}%, "
              f"Actual {correction['actual']}%")
```

---

## FAQ

**Q: Do tools slow down analysis significantly?**
A: About 20-40% slower, but with quantified accuracy improvements.

**Q: Can I use some tools but not others?**
A: Not directly, but you can create a custom analysis type that uses specific tools.

**Q: What happens if survey data is missing?**
A: Tools gracefully return error messages. Analysis falls back to standard mode.

**Q: Can tools work offline?**
A: Yes, once survey data is loaded. No external API calls needed.

**Q: How accurate is fact-checking?**
A: Depends on tolerance setting. Default ±5% catches most significant errors.

---

## Next Steps

1. **Try it:** Run `python survey_analysis_tools.py` to see demo
2. **Test it:** Run `pytest tests/integration/test_tool_enhanced_analysis.py -v`
3. **Use it:** Replace `'detailed_report'` with `'detailed_report_with_tools'`
4. **Monitor it:** Check `get_tool_stats()` regularly
5. **Extend it:** Add custom tools following the template above

---

**See also:**
- Full implementation plan: `docs/AGENTIC_TOOLS_IMPLEMENTATION_PLAN.md`
- Code reference: `survey_analysis_tools.py`
- Integration code: `tool_enhanced_analysis.py`
- Tests: `tests/integration/test_tool_enhanced_analysis.py`
