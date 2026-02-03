# Claude1 Sandbox - Quick Start Guide

**Purpose**: Safe, isolated testing environment for all Claude1 optimizations
**Status**: Ready to use
**Setup Time**: 5-10 minutes

---

## What is this?

The Claude1 sandbox is a Docker container that provides a **completely isolated environment** for testing all optimization work (Phase 1-3 + Meta-Prompting) without any risk to your production system.

### What's Inside?
- ✅ All Phase 1 fixes (config, error handling, security)
- ✅ All Phase 2 optimizations (70% cost reduction via caching)
- ✅ All Phase 3 reliability improvements (race condition prevention)
- ✅ Complete meta-prompting system (25% token reduction)
- ✅ Testing tools and monitoring dashboard
- ✅ Isolated data storage (separate ChromaDB, cache, logs)

---

## Quick Start (3 Commands)

```bash
# 1. Build the container (first time only, ~5 minutes)
./run_sandbox.sh build

# 2. Run all tests (~2 minutes)
./run_sandbox.sh test

# 3. Open interactive shell
./run_sandbox.sh shell
```

That's it! You're now in a safe sandbox with all optimizations ready to test.

---

## Available Commands

### Essential Commands
```bash
./run_sandbox.sh build       # Build container (first time)
./run_sandbox.sh test        # Run all tests
./run_sandbox.sh shell       # Interactive development
./run_sandbox.sh status      # Check if running
```

### Advanced Commands
```bash
./run_sandbox.sh start       # Start container (background)
./run_sandbox.sh stop        # Stop container
./run_sandbox.sh logs        # View live logs
./run_sandbox.sh dashboard   # Start Dash dashboard on :8050
./run_sandbox.sh clean       # Remove everything (destructive)
```

---

## What Gets Tested?

### Phase 1: Configuration & Security ✅
- Config.py path management
- Error handling in dataset_knowledge.py
- .env file loading
- Security protections

### Phase 2: Cost Optimization ✅
- LLM response caching (70% reduction target)
- Cache hit rates and statistics
- Token usage tracking
- Performance monitoring

### Phase 3: Reliability ✅
- RequestManager (race condition prevention)
- ManagedThreadPool (thread reuse)
- ErrorHandler (centralized logging)
- Deep copy session data

### Meta-Prompting System ✅
- Template versioning (v1/v2/v3)
- Automatic version selection
- Quality scoring (0-100)
- A/B testing framework
- Performance tracking

---

## Setting Up API Keys (Optional)

For full testing with real LLM calls:

1. **Copy the template**:
   ```bash
   cp .env.sandbox .env.sandbox.local
   ```

2. **Add test API keys** (use keys with low quotas):
   ```bash
   # Edit .env.sandbox.local
   OPENAI_API_KEY=sk-test-your-test-key
   ANTHROPIC_API_KEY=sk-ant-test-your-key
   ```

3. **Mount the file** (edit docker-compose.claude1.yml):
   ```yaml
   volumes:
     - ./.env.sandbox.local:/sandbox/navegador/.env:ro
   ```

**Important**: Never use production API keys in the sandbox!

---

## Inside the Container

Once you run `./run_sandbox.sh shell`, you'll be in the container:

```bash
# You're now inside the sandbox!
(nvg_py13_env) sandboxuser@container:/sandbox/navegador$

# Run tests
./run_tests.sh

# Or individual test
python test_sandbox.py

# Check specific module
python quick_fixes.py
python meta_prompting.py

# Start dashboard
python dashboard.py  # Access at http://localhost:8050
```

### Directory Structure

```
/sandbox/navegador/         # Your code (read-only by default)
/sandbox-data/
  ├── cache/                # LLM response cache
  ├── logs/                 # Error and debug logs
  ├── chromadb/            # Vector database
  ├── test-results/        # Test outputs
  └── prompt_data/         # Prompt performance tracking
```

---

## Understanding Test Results

### Expected Output (All Pass)

```
==========================================
CLAUDE1 SANDBOX TEST SUITE
==========================================

Phase 1: Smoke Tests
----------------------------------------
✓ config.py imported
✓ quick_fixes.py imported
✓ meta_prompting.py imported
✓ prompt_integration.py imported
✓ performance_optimization.py imported

Phase 2: Module Tests
----------------------------------------
✓ RequestManager working
✓ ManagedThreadPool working
✓ ErrorHandler working
✓ Deep copy working

Phase 3: Integration Tests
----------------------------------------

1. Testing config.py...
   ✓ Project root: /sandbox/navegador
   ✓ Config loaded successfully

2. Testing quick_fixes.py...
   ✓ RequestManager working
   ✓ ManagedThreadPool working
   ✓ ErrorHandler working
   ✓ Deep copy working

3. Testing meta_prompting.py...
   ✓ PromptManager initialized
   ✓ Generated prompt (1234 chars)

4. Testing prompt_integration.py...
   ✓ Quality assessment working (score: 85.0)
   ✓ Prompt creation working

5. Testing race condition prevention...
   ✓ Race condition prevented (1/5 succeeded)

==========================================
RESULTS: 5/5 tests passed
==========================================
✅ ALL TESTS PASSED - Sandbox is working correctly
```

### What Success Means

- ✅ **All imports work**: No missing dependencies
- ✅ **Config resolves paths**: System can find files
- ✅ **Race conditions prevented**: Only 1 thread succeeds (not 5)
- ✅ **Quality scoring works**: 0-100 assessment functional
- ✅ **No crashes**: All modules load and execute

---

## Monitoring Performance

### Check Cache Statistics
```bash
# Inside container
python check_cache_stats.py

# Expected output:
Cache Hit Rate: 45.2%
Total Calls: 100
Cache Hits: 45
Cache Misses: 55
Estimated Savings: $1.23
```

### Check Prompt Performance
```bash
# Inside container
python -c "from prompt_integration import print_prompt_report; print_prompt_report()"

# Shows:
- Token usage by version
- Quality scores
- Success rates
- Which version performs best
```

### View Error Logs
```bash
# From host
./run_sandbox.sh shell
cat /sandbox-data/logs/dashboard_errors.log
```

---

## Troubleshooting

### Container won't build
```bash
# Check Docker is running
docker ps

# Check disk space
df -h

# Try clean build
./run_sandbox.sh clean
./run_sandbox.sh build
```

### Tests fail with import errors
```bash
# Verify conda environment
./run_sandbox.sh shell
conda env list  # Should show nvg_py13_env

# Activate manually if needed
conda activate nvg_py13_env
```

### API calls fail
```bash
# Check if .env file is mounted
./run_sandbox.sh shell
cat .env  # Should show API keys

# Verify keys are set
echo $OPENAI_API_KEY
```

### Container uses too much memory
```bash
# Reduce resource limits in docker-compose.claude1.yml
resources:
  limits:
    memory: 2G  # Reduce from 4G
```

---

## Safety Features

### What's Protected? ✅
- ✅ **No production data**: Only synthetic test data
- ✅ **Isolated database**: Separate ChromaDB instance
- ✅ **Read-only code**: Can't accidentally modify files (by default)
- ✅ **Resource limits**: Can't consume all system resources
- ✅ **Separate network**: No access to production services

### What If Something Breaks?
- **Container only**: Destroy and rebuild anytime
- **Git intact**: Your Claude1 branch is unchanged
- **Host safe**: Nothing on your Mac is affected
- **Fast recovery**: `./run_sandbox.sh clean && ./run_sandbox.sh build`

---

## Next Steps After Testing

### If All Tests Pass ✅
1. Review performance metrics
2. Check quality scores meet targets
3. Verify no memory leaks
4. Plan integration into main codebase

### If Tests Fail ⚠️
1. Check logs: `/sandbox-data/logs/`
2. Run individual module tests
3. Review error messages
4. Fix issues in Claude1 branch
5. Rebuild container and retest

---

## Advanced Usage

### Custom Test Scenarios

Create your own test in the container:

```python
# /sandbox/navegador/my_test.py
from quick_fixes import get_request_manager
from meta_prompting import get_optimized_prompt

# Your custom test logic here
def test_custom_scenario():
    # Test something specific
    pass

if __name__ == "__main__":
    test_custom_scenario()
```

### Jupyter Notebook Testing

```bash
# Start Jupyter server (port 8888)
./run_sandbox.sh shell
jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser

# Access at: http://localhost:8888
```

### Persistent Development

To edit files inside container (removes read-only protection):

Edit `docker-compose.claude1.yml`:
```yaml
volumes:
  - ./:/sandbox/navegador  # Remove :ro
```

Rebuild:
```bash
./run_sandbox.sh clean
./run_sandbox.sh build
```

---

## Performance Expectations

### First Run (Cold Start)
- Build time: 5-10 minutes
- Test time: 2-3 minutes
- Memory usage: ~1.5GB

### Subsequent Runs (Warm)
- Start time: 5-10 seconds
- Test time: 1-2 minutes
- Memory usage: ~1.0GB

### Resource Usage
- **Disk**: ~2GB (container) + ~500MB (volumes)
- **Memory**: 1-2GB (configurable)
- **CPU**: 1-2 cores (configurable)

---

## Cleanup

### Remove Container Only (Keep Data)
```bash
./run_sandbox.sh stop
```

### Remove Everything (Container + Data)
```bash
./run_sandbox.sh clean
```

### Check What's Taking Space
```bash
docker system df
docker volume ls | grep claude1
```

---

## Support

### Getting Help

1. **Check this README** - Most questions answered here
2. **Review logs** - `./run_sandbox.sh logs`
3. **Run diagnostics** - `./run_sandbox.sh status`
4. **Check DOCKER_SANDBOX_STRATEGY.md** - Detailed architecture

### Common Issues

| Issue | Solution |
|-------|----------|
| Container won't start | `docker ps -a` → check status |
| Tests timeout | Increase memory limits |
| Import errors | Verify conda environment activated |
| API failures | Check .env file mounted correctly |
| Out of disk space | `./run_sandbox.sh clean` |

---

## Summary

✅ **Safe**: Completely isolated from production
✅ **Fast**: Tests run in 1-3 minutes
✅ **Comprehensive**: Tests all optimization phases
✅ **Easy**: 3 commands to build, test, and use
✅ **Disposable**: Delete and rebuild anytime

The Claude1 sandbox gives you confidence that all optimizations work correctly before integrating into your production system.

**Ready to test? Run: `./run_sandbox.sh build`**
