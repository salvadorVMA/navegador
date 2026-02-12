# Agentic Tools Implementation Plan

**Version:** 1.0
**Date:** 2026-02-11
**Status:** Ready for Implementation

## Overview

This document outlines the implementation of agentic tools to enhance Navegador's survey analysis capabilities. The implementation follows a **hybrid approach**: LLM reasoning augmented with deterministic tools for accuracy.

### Key Principles

1. **Backward Compatibility**: Original analysis pipeline remains intact
2. **Opt-In Architecture**: Tool-enhanced analysis is optional via flags
3. **A/B Testing Ready**: Easy comparison between standard and enhanced approaches
4. **Progressive Enhancement**: Tools augment, not replace, LLM capabilities

---

## Architecture

### Current Architecture (Preserved)

```
User Query
    ↓
Intent Detection (LLM)
    ↓
Variable Selection (ChromaDB + LLM)
    ↓
Analysis Pipeline (LLM-only)
    ├── Pattern Identification
    ├── Expert Summaries
    └── Transversal Analysis
    ↓
Formatted Report
```

### Enhanced Architecture (New, Opt-In)

```
User Query
    ↓
Intent Detection (LLM)
    ↓
Variable Selection (ChromaDB + LLM)
    ↓
Analysis Pipeline (Hybrid: LLM + Tools)
    ├── Pattern Identification
    │   ├── LLM identifies patterns
    │   └── Tools verify claims ←── NEW
    ├── Fact-Checking Layer ←── NEW
    │   └── Validate all numerical claims
    ├── Expert Summaries
    └── Transversal Analysis
    ↓
Enhanced Report + Accuracy Metrics
```

---

## Implementation Components

### 1. Survey Analysis Tools (`survey_analysis_tools.py`) ✅ CREATED

**Location:** `/workspaces/navegador/survey_analysis_tools.py`

**Features:**
- 8 LangChain-compatible tools using `@tool` decorator
- Deterministic statistical calculations
- Metadata fetching without hallucination
- Claim validation against actual data
- Built-in execution monitoring

**Key Tools:**

| Tool | Purpose | Example Use Case |
|------|---------|------------------|
| `get_variable_metadata` | Fetch precise variable info | Get question text without hallucination |
| `calculate_percentage_from_data` | Exact percentage calculation | Verify "85% agree" claim |
| `validate_percentage_claim` | Fact-check LLM claims | Auto-validate pattern descriptions |
| `analyze_variable_summary` | Comprehensive variable stats | Ground-truth summaries |
| `cross_reference_variables` | Find actual relationships | Verify cross-variable patterns |
| `calculate_pattern_strength` | Statistical pattern metrics | Quantify pattern significance |

**Monitoring:**
- Tracks all tool executions
- Success rates, latency, usage patterns
- Integrates with existing LangSmith monitoring

### 2. Tool-Enhanced Analysis Integration (`tool_enhanced_analysis.py`) ✅ CREATED

**Location:** `/workspaces/navegador/tool_enhanced_analysis.py`

**Features:**
- Wraps existing analysis functions
- Adds tool-calling at pattern identification
- Post-analysis fact-checking
- Backward-compatible interface

**Key Functions:**

```python
# Drop-in replacement for run_detailed_analysis
run_hybrid_detailed_analysis(
    selected_variables,
    user_query,
    enable_tools=True,        # Toggle tool enhancement
    enable_fact_checking=True # Toggle validation
)

# Fact-check existing patterns
fact_check_all_patterns(patterns_dict)

# Enhanced reporting
format_hybrid_analysis_report(results)
```

### 3. Integration with `run_analysis.py` (To Be Done)

**Modification Required:** Add new analysis type

```python
# In run_analysis.py, add:

def run_analysis(analysis_type: str, selected_variables: list,
                 user_query: str, **kwargs) -> dict:

    # ... existing code ...

    elif analysis_type == "detailed_report_with_tools":  # NEW
        return _run_hybrid_detailed_report(selected_variables, user_query, **kwargs)

    elif analysis_type == "fact_check_only":  # NEW
        return _run_fact_check_analysis(selected_variables, user_query, **kwargs)
```

**Implementation:**

```python
def _run_hybrid_detailed_report(selected_variables: list, user_query: str, **kwargs) -> dict:
    """Run detailed report with tool enhancement and fact-checking"""
    from tool_enhanced_analysis import run_hybrid_detailed_analysis, format_hybrid_analysis_report

    try:
        # Run hybrid analysis
        analysis_results = run_hybrid_detailed_analysis(
            selected_variables=selected_variables,
            user_query=user_query,
            analysis_params=kwargs.get('analysis_params'),
            enable_tools=kwargs.get('enable_tools', True),
            enable_fact_checking=kwargs.get('enable_fact_checking', True)
        )

        # Format report
        formatted_report = format_hybrid_analysis_report(analysis_results)

        return {
            'success': analysis_results.get('success', False),
            'analysis_type': 'detailed_report_with_tools',
            'results': analysis_results,
            'formatted_report': formatted_report,
            'tool_enhanced': True,
            'accuracy_rate': analysis_results.get('accuracy_rate', 0),
            'error': analysis_results.get('error') if not analysis_results.get('success') else None
        }

    except Exception as e:
        print(f"Error in hybrid analysis: {e}")
        return {
            'success': False,
            'error': str(e),
            'analysis_type': 'detailed_report_with_tools',
            'results': {},
            'formatted_report': f'Error in tool-enhanced analysis: {str(e)}'
        }
```

### 4. Agent Integration (Optional for Advanced Users)

**For `agent.py` - Add intent:**

```python
# In intent_dict (intent_classifier.py)
intent_dict = {
    # ... existing intents ...
    "select_analysis_mode": "If user wants to choose between standard or tool-enhanced analysis",
}

# In agent.py workflow
def select_analysis_mode(state: AgentState) -> AgentState:
    """Let user choose analysis mode"""
    response = """
    Choose analysis mode:
    1. **Standard** - Fast, LLM-only analysis
    2. **Tool-Enhanced** - Slower, fact-checked with accuracy metrics
    3. **Comparison** - Run both and compare results

    Which would you like?
    """
    state["messages"].append(AIMessage(content=response))
    return state
```

---

## Testing Strategy

### Phase 1: Tool Validation ✅ (Ready)

**Goal:** Ensure tools work correctly

```bash
# Test tools directly
python survey_analysis_tools.py

# Expected output:
# - Tool execution demo
# - Successful metadata retrieval
# - Monitoring statistics
```

### Phase 2: Integration Testing (Next)

**Create test file:** `tests/integration/test_tool_enhanced_analysis.py`

```python
def test_hybrid_analysis_vs_standard():
    """Compare tool-enhanced vs standard analysis"""

    # Same inputs for both
    selected_vars = ['p1|MEX', 'p2|MEX']
    query = "What do Mexicans think about education?"

    # Run standard
    standard_results = run_analysis(
        'detailed_report',
        selected_vars,
        query
    )

    # Run tool-enhanced
    enhanced_results = run_analysis(
        'detailed_report_with_tools',
        selected_vars,
        query,
        enable_tools=True,
        enable_fact_checking=True
    )

    # Compare
    print(f"Standard success: {standard_results['success']}")
    print(f"Enhanced success: {enhanced_results['success']}")
    print(f"Accuracy rate: {enhanced_results.get('accuracy_rate', 'N/A')}")
    print(f"Tool calls: {enhanced_results.get('tool_statistics', {}).get('total_executions', 0)}")
```

### Phase 3: A/B Testing in Production

**Dashboard Integration:**

```python
# In dashboard.py, add analysis mode selector
dcc.RadioItems(
    id='analysis-mode',
    options=[
        {'label': 'Standard (Fast)', 'value': 'detailed_report'},
        {'label': 'Tool-Enhanced (Accurate)', 'value': 'detailed_report_with_tools'},
        {'label': 'Compare Both', 'value': 'comparison'}
    ],
    value='detailed_report'  # Default to standard
)
```

---

## Performance Expectations

### Standard Analysis (Current)

- **Speed:** ~15-30 seconds for detailed report
- **Token Usage:** ~8,000-12,000 tokens
- **Accuracy:** Unknown (no validation)
- **Cost:** ~$0.10-0.15 per analysis

### Tool-Enhanced Analysis (New)

- **Speed:** ~20-40 seconds (33% slower)
- **Token Usage:** ~10,000-15,000 tokens (25% more)
- **Accuracy:** 85-95% (validated)
- **Cost:** ~$0.12-0.18 per analysis
- **Benefit:** Quantified accuracy + fact-checking

### When to Use Each

| Scenario | Recommended Mode |
|----------|------------------|
| Quick exploration | Standard |
| Public-facing results | Tool-Enhanced |
| Academic publication | Tool-Enhanced + manual review |
| Rapid prototyping | Standard |
| High-stakes decisions | Tool-Enhanced |

---

## Rollout Plan

### Week 1: Foundation ✅ DONE
- [x] Create `survey_analysis_tools.py`
- [x] Create `tool_enhanced_analysis.py`
- [x] Add monitoring infrastructure

### Week 2: Integration
- [ ] Modify `run_analysis.py` to add new analysis types
- [ ] Update `agent.py` to support analysis mode selection
- [ ] Create integration tests

### Week 3: Testing & Tuning
- [ ] Run A/B tests with sample queries
- [ ] Tune tool selection logic
- [ ] Optimize performance bottlenecks
- [ ] Document accuracy improvements

### Week 4: Production Deployment
- [ ] Add dashboard UI controls
- [ ] Update user documentation
- [ ] Enable by default for specific use cases
- [ ] Monitor and iterate

---

## Migration Path

### For Developers

**Before (Standard):**
```python
results = run_analysis(
    'detailed_report',
    selected_variables,
    user_query
)
```

**After (Tool-Enhanced):**
```python
# Option 1: Full enhancement
results = run_analysis(
    'detailed_report_with_tools',
    selected_variables,
    user_query,
    enable_tools=True,
    enable_fact_checking=True
)

# Option 2: Tools only, no fact-checking
results = run_analysis(
    'detailed_report_with_tools',
    selected_variables,
    user_query,
    enable_tools=True,
    enable_fact_checking=False
)

# Option 3: Keep standard (no change needed)
results = run_analysis(
    'detailed_report',  # Still works!
    selected_variables,
    user_query
)
```

### For End Users (Dashboard)

1. **No change required** - Standard analysis still default
2. **Opt-in UI** - Radio button to enable tools
3. **Comparison mode** - See both side-by-side

---

## Monitoring & Metrics

### Tool Execution Metrics

```python
from survey_analysis_tools import get_tool_stats

stats = get_tool_stats()
# Returns:
# {
#   'total_executions': 42,
#   'success_rate': 0.95,
#   'avg_execution_time': 0.123,
#   'executions_by_tool': {
#     'calculate_percentage_from_data': 15,
#     'validate_percentage_claim': 12,
#     ...
#   }
# }
```

### Accuracy Metrics

```python
# After analysis
print(f"Accuracy Rate: {results['accuracy_rate']}%")
print(f"Patterns Fact-Checked: {results['fact_check']['patterns_checked']}")
print(f"Corrections Needed: {results['fact_check']['patterns_needing_correction']}")
```

### Integration with LangSmith

```python
# Tools automatically log to LangSmith when available
# View in LangSmith dashboard:
# - Tool call traces
# - Token usage per tool
# - Success/failure rates
```

---

## Configuration

### Environment Variables

```bash
# .env additions
ENABLE_ANALYSIS_TOOLS=true          # Global toggle
ENABLE_FACT_CHECKING=true           # Global fact-checking
TOOL_ACCURACY_TOLERANCE=5.0         # Percentage point tolerance
TOOL_CACHE_ENABLED=true             # Cache tool results
```

### Analysis Parameters

```python
analysis_params = {
    'enable_tools': True,
    'enable_fact_checking': True,
    'tool_timeout': 10.0,  # seconds
    'validation_tolerance': 5.0,  # percentage points
    'require_tool_verification': False,  # Fail if tools fail
}

results = run_analysis(
    'detailed_report_with_tools',
    selected_variables,
    user_query,
    analysis_params=analysis_params
)
```

---

## Future Enhancements

### Phase 2: MCP Integration

- Connect to live survey platforms (Qualtrics, SurveyMonkey)
- Real-time data updates
- External knowledge bases

### Phase 3: Advanced Agentic Features

- Self-correcting analysis loops
- Multi-step reasoning with tool orchestration
- Automated report generation with citations

### Phase 4: Skills System

- Domain-specific analysis skills (political science, sociology)
- Custom statistical test suites
- Specialized visualization tools

---

## Code Examples

### Example 1: Simple Tool Usage

```python
from survey_analysis_tools import calculate_percentage_from_data

# Verify a claim
result = calculate_percentage_from_data.invoke({
    'variable_id': 'p1_1|MEX',
    'response_category': 'Strongly agree'
})

print(f"Actual percentage: {result['percentage']}%")
print(f"Sample size: {result['total_responses']}")
```

### Example 2: Fact-Check Existing Analysis

```python
from tool_enhanced_analysis import fact_check_all_patterns

# Load existing analysis results
with open('results/analysis_123.json', 'r') as f:
    analysis = json.load(f)

# Fact-check patterns
fact_check = fact_check_all_patterns(analysis['patterns'])

print(f"Accuracy: {fact_check['accuracy_rate']:.1f}%")
print(f"Patterns needing correction: {fact_check['patterns_needing_correction']}")
```

### Example 3: A/B Test

```python
from run_analysis import run_analysis
import time

# Benchmark
queries = [
    "What do Mexicans think about democracy?",
    "How do people view education policy?",
]

for query in queries:
    vars = ['p1|MEX', 'p2|MEX', 'p3|MEX']

    # Standard
    start = time.time()
    standard = run_analysis('detailed_report', vars, query)
    standard_time = time.time() - start

    # Enhanced
    start = time.time()
    enhanced = run_analysis('detailed_report_with_tools', vars, query)
    enhanced_time = time.time() - start

    print(f"\nQuery: {query}")
    print(f"Standard: {standard_time:.1f}s")
    print(f"Enhanced: {enhanced_time:.1f}s (Accuracy: {enhanced.get('accuracy_rate', 'N/A')}%)")
```

---

## FAQ

### Q: Will this break existing code?

**A:** No. All existing analysis types continue to work. The tool-enhanced mode is opt-in via new analysis types.

### Q: What if tools fail?

**A:** Graceful degradation. If tools fail, system falls back to standard LLM-only analysis with a warning.

### Q: How much slower is tool-enhanced analysis?

**A:** Approximately 20-40% slower, but with quantified accuracy improvements.

### Q: Can I use tools without fact-checking?

**A:** Yes. Set `enable_fact_checking=False` in analysis parameters.

### Q: How do I monitor tool usage?

**A:** Call `get_tool_stats()` or check LangSmith dashboard for detailed traces.

### Q: Can I add custom tools?

**A:** Yes! Use the `@tool` decorator and add to `AVAILABLE_TOOLS` list in `survey_analysis_tools.py`.

---

## Support & Contribution

### Getting Help

- **Documentation:** `docs/AGENTIC_TOOLS_IMPLEMENTATION_PLAN.md` (this file)
- **Code Reference:** See inline comments in `survey_analysis_tools.py`
- **Examples:** Run `python survey_analysis_tools.py` for demos

### Contributing New Tools

1. Add tool function with `@tool` decorator
2. Include docstring with args/returns
3. Add error handling and monitoring
4. Update `AVAILABLE_TOOLS` list
5. Add tests in `tests/unit/test_survey_tools.py`
6. Update this documentation

---

## Success Metrics

### Target Metrics (After 4 Weeks)

- [ ] **Accuracy Rate:** >85% of claims validated
- [ ] **Tool Success Rate:** >95% of tool calls succeed
- [ ] **Performance:** <2x slowdown vs standard
- [ ] **Adoption:** 30% of analyses use tools
- [ ] **User Satisfaction:** Positive feedback on accuracy

### Measurement

```python
# Weekly report
from survey_analysis_tools import get_tool_stats
from meta_prompting import get_prompt_stats

tool_stats = get_tool_stats()
prompt_stats = get_prompt_stats()

report = {
    'tool_calls': tool_stats['total_executions'],
    'tool_success_rate': tool_stats['success_rate'],
    'avg_accuracy': prompt_stats.get('avg_quality_score', 0),
    'adoption_rate': tool_stats['total_executions'] / prompt_stats['total_executions']
}
```

---

## Conclusion

This implementation provides a **pragmatic, incremental path** to enhanced agentic capabilities:

✅ **Preserves existing functionality**
✅ **Enables A/B testing**
✅ **Quantifies accuracy improvements**
✅ **Maintains demo-to-production path**
✅ **Aligns with project goals**

The hybrid approach balances **speed** (LLM reasoning) with **accuracy** (deterministic tools), providing the best of both worlds while maintaining the flexibility to choose based on use case.

---

**Next Steps:**
1. Review this plan
2. Run tool demos: `python survey_analysis_tools.py`
3. Implement integration in `run_analysis.py`
4. Create integration tests
5. Deploy to staging for A/B testing
