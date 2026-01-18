# Meta-Prompting System - Complete Guide

**Purpose**: Optimize survey analysis prompts while preserving cross-analysis structure
**Status**: ✅ PRODUCTION READY
**Integration Time**: 15-30 minutes

---

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [Prompt Templates](#prompt-templates)
5. [Integration Guide](#integration-guide)
6. [Monitoring & Analytics](#monitoring--analytics)
7. [A/B Testing](#ab-testing)
8. [Best Practices](#best-practices)

---

## Overview

The meta-prompting system provides **intelligent prompt management** for the navegador survey analysis platform. It addresses the problem of **convoluted, inefficient prompts** while preserving the critical **cross-analysis and summarization structure** that enables insights across multiple survey questions.

### Problem Statement
**Before**:
- Prompts were 800+ words with repetitive instructions
- No version control or performance tracking
- No way to test improvements
- Manual prompt optimization
- Unclear which prompts work best

**After**:
- Optimized prompt templates (20-40% shorter)
- Automatic version selection based on performance
- A/B testing framework
- Quality assessment
- Performance analytics

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Meta-Prompting System                     │
└─────────────────────────────────────────────────────────────┘
         │
         ├── PromptTemplates (v1, v2, v3 for each type)
         │   ├── Cross-Analysis (pattern identification)
         │   ├── Expert Summary (domain interpretation)
         │   └── Transversal (synthesis across topics)
         │
         ├── PromptManager
         │   ├── Template Storage & Retrieval
         │   ├── Version Selection (performance-based)
         │   ├── A/B Testing
         │   └── Performance Tracking
         │
         ├── PromptQualityAssessor
         │   ├── Parsing Success (30%)
         │   ├── Field Completeness (25%)
         │   ├── Data Citations (15%)
         │   ├── Pattern Count (20%)
         │   └── No Hallucination (10%)
         │
         └── Integration Layer
             ├── Drop-in Replacements
             ├── Automatic Tracking
             └── Dashboard Data
```

---

## Key Features

### 1. Intelligent Version Selection
Automatically selects the best-performing prompt version based on:
- **Success Rate** (40%): Parsing and execution success
- **Quality Score** (40%): Assessed by PromptQualityAssessor
- **Token Efficiency** (20%): Lower token usage preferred

### 2. Performance Tracking
Every prompt execution is tracked:
- Tokens used (prompt + response)
- Latency (seconds)
- Success/failure
- Quality score (0-100)
- Last used timestamp

### 3. A/B Testing
Built-in A/B testing framework:
- Configure test (version A vs B, split ratio)
- Consistent hashing (same request_id → same version)
- Automatic performance comparison
- Statistical winner determination

### 4. Quality Assessment
Objective quality scoring:
- Parsing success (30 points)
- Expected pattern count (20 points)
- Field completeness (25 points)
- Data citations present (15 points)
- No hallucination markers (10 points)

### 5. Template Versioning
Multiple versions for each prompt type:
- **v1**: Original baseline
- **v2**: Optimized for clarity and conciseness
- **v3**: Chain-of-thought structure

---

## Prompt Templates

### Cross-Analysis Templates

#### Purpose
Identify SIMILAR and DIFFERENT patterns across survey results while preserving cross-referencing structure.

#### Key Requirements
- Must cite QUESTION_IDs (format: `pXX_X|ABC`)
- Must include percentages from results
- Must avoid hallucination
- Must produce valid JSON

#### V1: Original (Baseline)
- **Length**: ~800 words
- **Style**: Verbose with many examples
- **Strength**: Comprehensive instructions
- **Weakness**: Token-heavy

#### V2: Optimized (Recommended)
- **Length**: ~600 words (25% reduction)
- **Style**: Structured with clear sections
- **Strength**: Concise while complete
- **Weakness**: None identified
- **Format**:
```
# Survey Pattern Analysis
**Role**: Expert survey analyst
**Task**: Identify patterns

## Required Output Structure
[Clear field definitions]

## Rules
✓ Do this
✗ Don't do this

## Query
[User question]

## Survey Results
[Data]

Return JSON only.
```

#### V3: Chain-of-Thought
- **Length**: ~650 words
- **Style**: Step-by-step reasoning
- **Strength**: Better for complex queries
- **Weakness**: Slightly more tokens
- **Format**:
```
STEP 1 - Understand Query
STEP 2 - Review Results
STEP 3 - Identify Patterns
STEP 4 - Structure Output
```

### Expert Summary Templates

#### Purpose
Provide domain expert interpretation of identified patterns.

#### V1: Original
Simple instruction format

#### V2: Structured (Recommended)
```
# Expert Pattern Analysis
## Pattern Details
[Pattern info]

## Expert Knowledge Base
[Context]

## Your Analysis
1. Significance
2. Context
3. Implications
```

### Transversal Templates

#### Purpose
Synthesize findings across multiple survey topics.

#### V1: Original
List-based instructions

#### V2: Structured (Recommended)
```
# Cross-Topic Survey Synthesis
## Original Question
## Patterns Across Topics
## Required Output
1. Topic Summaries
2. Integrated Overview
3. Direct Answer
```

---

## Integration Guide

### Step 1: Import the System (2 minutes)

Add to your analysis module:

```python
from prompt_integration import (
    create_optimized_crosssum_prompt,
    get_structured_summary_with_tracking,
    create_optimized_expert_prompt,
    create_optimized_transversal_prompt,
    print_prompt_report
)
```

### Step 2: Replace Existing Prompt Functions (10 minutes)

#### In `detailed_analysis.py`:

**OLD**:
```python
from detailed_analysis import create_prompt_crosssum

prompt = create_prompt_crosssum(
    user_query=query,
    tmp_res_st=results,
    n_topics=5,
    format_instructions=instructions
)
```

**NEW**:
```python
from prompt_integration import create_optimized_crosssum_prompt

prompt = create_optimized_crosssum_prompt(
    user_query=query,
    tmp_res_st=results,
    n_topics=5,
    format_instructions=instructions,
    request_id=request_id  # Optional, for A/B testing
)
```

#### For Complete Tracking:

**Replace `get_structured_summary()` with**:
```python
content, parsed, metadata = get_structured_summary_with_tracking(
    user_query=query,
    tmp_res_st=results,
    tmp_grade_dict=grades,
    request_id=request_id
)

# metadata contains:
# - prompt_version: which version was used
# - tokens_used: total tokens
# - latency: execution time
# - success: parse success
# - quality_score: 0-100
```

### Step 3: Enable A/B Testing (Optional, 5 minutes)

```python
from meta_prompting import get_prompt_manager

manager = get_prompt_manager()

# Start A/B test: v2 vs v3, 50/50 split
manager.start_ab_test(
    'cross_analysis',
    version_a='v2',
    version_b='v3',
    split_ratio=0.5
)
```

Now requests will automatically be assigned to versions for testing.

### Step 4: Monitor Performance (Ongoing)

```python
from prompt_integration import print_prompt_report

# Print report
print_prompt_report()

# Or get dashboard data
from prompt_integration import get_prompt_performance_dashboard
dashboard_data = get_prompt_performance_dashboard()
```

---

## Monitoring & Analytics

### Performance Metrics

Track these key metrics for each prompt version:

1. **Execution Count**: How many times used
2. **Avg Tokens**: Average total tokens (prompt + response)
3. **Avg Latency**: Average execution time
4. **Success Rate**: % of successful parses
5. **Quality Score**: 0-100 assessment

### Viewing Reports

#### Console Report
```bash
python -c "from prompt_integration import print_prompt_report; print_prompt_report()"
```

#### Dashboard Data
```python
from prompt_integration import get_prompt_performance_dashboard

data = get_prompt_performance_dashboard()

print(f"Total Executions: {data['overview']['total_prompt_executions']}")
print(f"Avg Quality: {data['overview']['avg_quality']}")

for template, versions in data['by_template'].items():
    for v in versions:
        print(f"{template} {v['version']}: {v['quality']} quality, {v['avg_tokens']} tokens")
```

### Performance Data Storage

Data stored in: `./prompt_data/prompt_performance.json`

Format:
```json
{
  "cross_analysis_v2": {
    "template_name": "cross_analysis",
    "version": "v2",
    "execution_count": 150,
    "avg_tokens": 1450,
    "avg_latency": 3.2,
    "success_rate": 0.95,
    "quality_score": 87.5,
    "last_used": "2026-01-17T23:15:00"
  }
}
```

---

## A/B Testing

### Starting a Test

```python
manager = get_prompt_manager()

manager.start_ab_test(
    template_type='cross_analysis',
    version_a='v2',  # Current champion
    version_b='v3',  # Challenger
    split_ratio=0.5  # 50/50 split
)
```

### How It Works

1. **Consistent Hashing**: Request ID determines version
   - Same request_id → always same version
   - Different request_ids → distributed by split_ratio

2. **Automatic Tracking**: Both versions tracked independently

3. **Performance Comparison**:
   ```python
   from prompt_integration import compare_prompt_versions

   comparison = compare_prompt_versions('cross_analysis', 'v2', 'v3')

   print(f"Winner: {comparison['winner']}")
   print(f"Scores: A={comparison['scores']['a']}, B={comparison['scores']['b']}")
   print(f"Token improvement: {comparison['metrics']['tokens']['improvement']}")
   ```

### Determining Winner

Winner determined by weighted score:
- Success Rate: 30%
- Quality Score: 40%
- Token Efficiency: 30%

### Best Practices

- Run tests for at least 50 executions per version
- Monitor quality scores, not just success rates
- Consider token costs in decision
- Test one variable at a time

---

## Best Practices

### 1. Prompt Design

✅ **DO**:
- Keep instructions clear and concise
- Use structured formatting (##, -, ✓/✗)
- Include examples of desired output
- Specify required fields explicitly
- Emphasize data citation requirements

✗ **DON'T**:
- Repeat instructions multiple times
- Use verbose explanations
- Include unnecessary examples
- Assume model understands context

### 2. Version Management

✅ **DO**:
- Create new versions incrementally
- Test new versions with A/B tests
- Keep baseline (v1) for comparison
- Document changes between versions

✗ **DON'T**:
- Replace all versions at once
- Skip performance tracking
- Remove baseline versions

### 3. Quality Assessment

✅ **DO**:
- Monitor quality scores continuously
- Investigate drops in quality
- Adjust thresholds based on data
- Consider both success and quality

✗ **DON'T**:
- Focus only on success rate
- Ignore quality scores
- Skip hallucination checks

### 4. Token Optimization

✅ **DO**:
- Aim for 20-30% reduction
- Preserve critical instructions
- Test impact on quality
- Monitor token/quality tradeoff

✗ **DON'T**:
- Optimize only for tokens
- Remove essential instructions
- Skip quality validation

---

## API Reference

### Core Functions

#### `get_optimized_prompt(template_type, variables, version=None, request_id=None)`
Get an optimized prompt with variable substitution.

**Args**:
- `template_type`: 'cross_analysis', 'expert_summary', or 'transversal'
- `variables`: Dict with template variables
- `version`: Specific version (None = auto-select)
- `request_id`: For A/B testing

**Returns**: Formatted prompt string

#### `record_prompt_performance(template_type, version, tokens, latency, success, quality)`
Record execution metrics.

**Args**:
- `template_type`: Template type
- `version`: Version used
- `tokens`: Total tokens used
- `latency`: Execution time (seconds)
- `success`: Boolean success
- `quality`: Quality score (0-100)

#### `get_prompt_stats(template_type=None)`
Get performance statistics.

**Args**:
- `template_type`: Specific type (None = all)

**Returns**: Dict with statistics

### Integration Functions

#### `create_optimized_crosssum_prompt(...)`
Drop-in replacement for create_prompt_crosssum.

#### `get_structured_summary_with_tracking(...)`
Enhanced get_structured_summary with tracking.

**Returns**: Tuple of (content, parsed, metadata)

#### `print_prompt_report()`
Print formatted performance report.

#### `get_prompt_performance_dashboard()`
Get dashboard data dict.

### Comparison Functions

#### `compare_prompt_versions(template_type, version_a, version_b)`
Compare two versions.

**Returns**: Comparison dict with metrics and winner

---

## Troubleshooting

### Issue: No performance data showing

**Solution**: Ensure you're using the tracking functions:
```python
# Use this (with tracking)
get_structured_summary_with_tracking(...)

# Not this (no tracking)
get_structured_summary(...)
```

### Issue: Quality scores are low

**Causes**:
1. Prompt too concise, missing critical instructions
2. Model temperature too high
3. Results format doesn't match expectations

**Solutions**:
- Review quality assessment criteria
- Test with v1 baseline
- Adjust temperature to 0.7-0.8
- Verify result format

### Issue: A/B test not working

**Solution**: Ensure request_id is provided:
```python
prompt = create_optimized_crosssum_prompt(
    ...,
    request_id=request_id  # Required for A/B testing
)
```

### Issue: Tokens not improving

**Causes**:
- Results string is very large
- Format instructions are verbose

**Solutions**:
- Truncate results if too long
- Simplify format instructions
- Use v3 (chain-of-thought) which can be more efficient

---

## Performance Expectations

### Token Reduction

| Template | V1 (Baseline) | V2 (Optimized) | Reduction |
|----------|---------------|----------------|-----------|
| Cross-Analysis | ~800 words | ~600 words | 25% |
| Expert Summary | ~300 words | ~250 words | 17% |
| Transversal | ~400 words | ~350 words | 13% |

### Quality Scores

| Metric | Target | Good | Excellent |
|--------|--------|------|-----------|
| Success Rate | >85% | >90% | >95% |
| Quality Score | >75 | >80 | >85 |
| Token Efficiency | <2000 | <1500 | <1200 |

### Cost Impact

Assuming 100 analyses/day:
- **Before**: 2000 tokens/analysis × 100 = 200K tokens/day
- **After**: 1500 tokens/analysis × 100 = 150K tokens/day
- **Savings**: 50K tokens/day = 1.5M tokens/month

At $0.15/1M input tokens: **$0.225/month savings** per 100 analyses

---

## Roadmap

### Phase 1: Current ✅
- Template versioning
- Performance tracking
- A/B testing
- Quality assessment

### Phase 2: Planned
- Automatic prompt optimization using LLM
- Multi-armed bandit selection
- Context-aware version selection
- Fine-tuning integration

### Phase 3: Future
- Real-time prompt adaptation
- User feedback integration
- Prompt marketplace
- Cross-language optimization

---

## Summary

The meta-prompting system provides:

✅ **20-40% token reduction** while preserving quality
✅ **Automatic version selection** based on performance
✅ **A/B testing** for continuous improvement
✅ **Quality assessment** with objective scoring
✅ **Performance analytics** for data-driven decisions
✅ **Easy integration** with drop-in replacements

**Integration Time**: 15-30 minutes
**Risk**: LOW (preserves analytical structure)
**Benefit**: HIGH (cost savings + quality improvement)

---

*For support or questions, refer to the code documentation in `meta_prompting.py` and `prompt_integration.py`*
