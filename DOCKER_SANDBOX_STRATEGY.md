# Docker Sandbox Strategy - Claude1 Testing Environment

**Purpose**: Safe, isolated environment for testing all Claude1 optimization work
**Container Name**: `Claude1`
**Risk Level**: LOW (isolated from production)
**Setup Time**: 10-15 minutes

---

## Strategy Overview

### Goals
1. **Isolation**: Test all Phase 1-3 + Meta-Prompting changes without affecting production
2. **Reproducibility**: Consistent environment for reliable testing
3. **Safety**: No access to production data or APIs unless explicitly configured
4. **Monitoring**: Built-in tools to track performance and errors

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Docker Container: Claude1               │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Python 3.13 Environment                       │    │
│  │  - All navegador dependencies                   │    │
│  │  - Testing tools and monitoring                 │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Mounted Volumes (Read-Only by default)        │    │
│  │  - Code from Claude1 branch                     │    │
│  │  - Test data (synthetic only)                   │    │
│  │  - Cache directory (persistent)                 │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Isolated Resources                             │    │
│  │  - Separate ChromaDB instance                   │    │
│  │  - Test API keys (low quota)                    │    │
│  │  - Local cache storage                          │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Exposed Ports: 8050 (Dash), 8888 (Jupyter)            │
└─────────────────────────────────────────────────────────┘
```

---

## Safety Features

### 1. Data Isolation
- **No production data**: Only synthetic test datasets
- **Separate ChromaDB**: Fresh vector database for testing
- **Read-only mounts**: Code mounted read-only by default

### 2. API Protection
- **Rate limiting**: Test API keys with low quotas
- **Cost monitoring**: Track all LLM calls
- **Fallback mode**: Can run with mock responses

### 3. Resource Limits
- **Memory**: 4GB limit (configurable)
- **CPU**: 2 cores (configurable)
- **Disk**: 10GB limit for cache/logs

### 4. Network Isolation
- **No outbound by default**: Requires explicit API key setup
- **Local-only services**: ChromaDB, cache accessible only in container

---

## Testing Phases

### Phase 1: Smoke Tests (5 minutes)
- Import all modules
- Verify config.py paths
- Test error handling
- Check cache initialization

### Phase 2: Integration Tests (10 minutes)
- Test RequestManager race condition prevention
- Verify ThreadPool management
- Test ErrorHandler logging
- Validate deep copy functionality

### Phase 3: Meta-Prompting Tests (15 minutes)
- Test all 3 prompt versions (v1/v2/v3)
- Verify quality scoring
- Test A/B framework
- Validate performance tracking

### Phase 4: End-to-End Tests (20 minutes)
- Full query processing pipeline
- Cross-analysis with synthetic data
- Expert summaries
- Transversal analysis

---

## Container Features

### Included Tools
- **Testing**: pytest, unittest
- **Monitoring**: check_cache_stats.py, performance dashboard
- **Debugging**: iPython, pdb, logging
- **Profiling**: memory_profiler, cProfile

### Pre-configured
- Conda environment with Python 3.13
- All navegador dependencies
- Git configured with Claude1 branch
- Jupyter notebook server (optional)

### Persistent Storage
```
/sandbox-data/
  ├── cache/          # LLM response cache
  ├── logs/           # Error and performance logs
  ├── chromadb/       # Vector database
  └── test-results/   # Test outputs
```

---

## Usage Patterns

### Quick Test
```bash
docker run -it --rm claude1 python test_quick_fixes.py
```

### Interactive Development
```bash
docker run -it -p 8050:8050 claude1 bash
# Inside container:
conda activate nvg_py13_env
python dashboard.py
```

### Automated Testing
```bash
docker run --rm claude1 pytest tests/
```

---

## Security Considerations

### ✅ Safe Practices
- Use test API keys with spending limits
- Mount production data as read-only
- Review logs before committing changes
- Test with synthetic data first

### ⚠️ Warnings
- Don't commit .env files with real keys
- Don't expose container ports publicly
- Don't mount production database
- Don't run as root inside container

---

## Rollback Plan

If issues are discovered in sandbox:
1. **No impact on production** (isolated environment)
2. **Git branch intact** (can revert commits)
3. **Data preserved** (persistent volumes)
4. **Quick restart** (container can be rebuilt)

---

## Performance Expectations

### Resource Usage
- **Cold start**: ~30 seconds
- **Memory baseline**: ~500MB
- **With dashboard**: ~1.5GB
- **Full analysis**: ~2.5GB

### Testing Speed
- **Unit tests**: <1 minute
- **Integration tests**: 2-3 minutes
- **Full suite**: 5-10 minutes

---

## Success Metrics

### Must Pass
- ✅ All imports successful
- ✅ Config paths resolve correctly
- ✅ Cache system functional
- ✅ No race conditions detected
- ✅ Error handling works
- ✅ Prompt optimization reduces tokens

### Should Achieve
- 🎯 70% cache hit rate (after warmup)
- 🎯 25% token reduction in prompts
- 🎯 Quality scores >80
- 🎯 Zero memory leaks
- 🎯 <3s response times

---

## Monitoring Dashboard

Access via: http://localhost:8050

**Panels**:
1. Cache statistics (hit rate, size, savings)
2. Request manager stats (active, completed)
3. Thread pool stats (tasks, reuse)
4. Error handler stats (by type, frequency)
5. Prompt performance (by version, quality)

---

## Next Steps After Sandbox Testing

1. **Review results** - Check all metrics pass
2. **Document findings** - Note any issues
3. **Adjust configurations** - Tune based on results
4. **Plan production rollout** - If tests pass
5. **Monitor closely** - Watch for issues

---

## Support Files

- **Dockerfile.claude1** - Container definition
- **docker-compose.claude1.yml** - Orchestration config
- **test_sandbox.py** - Comprehensive test suite
- **.env.sandbox** - Test environment variables
- **run_sandbox.sh** - Quick start script

---

## Conclusion

This sandbox provides a **safe, isolated, reproducible** environment for testing all Claude1 optimizations. The container can be destroyed and recreated at any time without risk to production systems.

**Status**: Ready to build and deploy
**Risk**: MINIMAL (complete isolation)
**Benefit**: HIGH (confident testing before production)
