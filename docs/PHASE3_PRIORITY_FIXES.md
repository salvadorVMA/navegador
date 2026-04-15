# ARCHIVED -- Phase 3 Critical Reliability Fixes

> **This document is archived.** It describes dashboard reliability fixes from January 2026. These fixes have been applied and the project has moved well beyond this phase into SES bridge estimation, WVS integration, knowledge graphs, TDA, and the Graph Traversal Engine. Retained for historical reference.

---

# Phase 3: Critical Reliability Fixes - Priority Plan

**Date**: 2026-01-17
**Status**: 🚧 IN PROGRESS
**Focus**: High-impact reliability improvements

---

## Critical Issues Identified

### 1. 🔴 CRITICAL: Dashboard Race Conditions
**File**: `dashboard.py` lines 1214-1850
**Problem**:
- Two callbacks modify `session_data` simultaneously:
  - `handle_chat_interaction()` (lines 1231-1411)
  - `handle_auto_next_step()` (lines 1427-1850)
- Both use `.copy()` but shallow copy doesn't prevent nested dict modifications
- `pending_main_action` state duplicated and can be lost
- Request IDs generated but not enforced consistently

**Impact**: HIGH
- User queries can be lost or executed multiple times
- Session state corruption
- Unpredictable behavior under load

**Recommended Fix**:
```python
# Add request locking mechanism
import threading
_request_lock = threading.Lock()
_active_requests = set()

# In handle_chat_interaction:
request_id = str(uuid.uuid4())
with _request_lock:
    if request_id in _active_requests:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
    _active_requests.add(request_id)

# In handle_auto_next_step:
with _request_lock:
    if request_id not in _active_requests:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
    _active_requests.remove(request_id)
```

**Effort**: 4-6 hours
**Priority**: P0 (Must fix)

---

### 2. 🟠 HIGH: Excessive Timeouts
**Files**: `dashboard.py` lines 742, 775, 1466
**Problem**:
- 180-second timeouts cause poor UX
- No progress feedback during long waits
- Comments show history of increases: 10→30→60→180 seconds
- Thread pool created fresh each time (no reuse)

**Impact**: MEDIUM-HIGH
- Users think app is frozen
- Poor user experience
- Resource waste (new executors each time)

**Recommended Fix**:
```python
# Module-level executor pool
_executor_pool = ThreadPoolExecutor(max_workers=4)

# Reduce timeouts and add streaming progress
timeout = 30  # Reduced from 180
future = _executor_pool.submit(agent_function, args)

# Add progress callback
while not future.done():
    time.sleep(2)
    update_progress_indicator()
```

**Effort**: 2-3 hours
**Priority**: P1 (Should fix)

---

###3. 🟠 HIGH: Memory Leaks in LangGraph
**File**: `agent.py` line 134-137
**Problem**:
- `MemorySaver` checkpointer never cleaned up
- Each conversation thread stored indefinitely
- 1000+ conversations = GBs of memory

**Impact**: MEDIUM-HIGH
- Memory grows unbounded
- Application will eventually crash
- Poor performance as memory fills

**Recommended Fix**:
```python
# Implement periodic cleanup
class ManagedMemorySaver(MemorySaver):
    def __init__(self, max_age_hours=24):
        super().__init__()
        self.max_age = max_age_hours * 3600

    def cleanup_old_checkpoints(self):
        current_time = time.time()
        # Remove checkpoints older than max_age
        for thread_id, checkpoint in list(self.checkpoints.items()):
            if current_time - checkpoint['timestamp'] > self.max_age:
                del self.checkpoints[thread_id]
```

**Effort**: 2-3 hours
**Priority**: P1 (Should fix)

---

### 4. 🟡 MEDIUM: Poor Error Handling
**Files**: Multiple modules
**Problem**:
- Many try-except blocks just print and return `dash.no_update`
- Errors not logged persistently
- Users don't see meaningful error messages
- Silent failures throughout codebase

**Impact**: MEDIUM
- Difficult debugging
- Poor user experience
- Support issues

**Recommended Fix**:
```python
# Centralized error handler
class DashboardErrorHandler:
    def __init__(self, log_file='dashboard_errors.log'):
        self.logger = logging.getLogger('dashboard')
        handler = logging.FileHandler(log_file)
        self.logger.addHandler(handler)

    def handle_error(self, error, context, user_facing_message=None):
        # Log detailed error
        self.logger.error(f"{context}: {error}", exc_info=True)

        # Return user-friendly message
        if user_facing_message:
            return create_error_message(user_facing_message)
        return create_error_message("An error occurred. Please try again.")
```

**Effort**: 3-4 hours
**Priority**: P2 (Nice to have)

---

### 5. 🟡 MEDIUM: Duplicate Code in Dashboard
**File**: `dashboard.py` lines 237-281, 626-667
**Problem**:
- Three nearly identical functions for config creation
- Bug fixes need to be applied 3+ times
- ~100 lines of duplicate code

**Impact**: LOW-MEDIUM
- Maintenance burden
- Inconsistency risk
- Code bloat

**Recommended Fix**:
```python
def create_unified_config(thread_id=None, recursion_limit=None):
    """Single unified config creation function"""
    config_dict = {"configurable": {}}

    if thread_id:
        config_dict["configurable"]["thread_id"] = thread_id
    if recursion_limit:
        config_dict["recursion_limit"] = recursion_limit

    return normalize_config(config_dict)
```

**Effort**: 1-2 hours
**Priority**: P2 (Nice to have)

---

## Phase 3 Implementation Plan

### Sprint 1: Critical Fixes (6-8 hours)
**Week 1 Focus**: Race conditions and timeout improvements

1. **Fix Dashboard Race Conditions** (P0)
   - Implement request locking mechanism
   - Add request ID enforcement
   - Use deep copy for session data
   - Add duplicate request detection
   - **Deliverable**: No more concurrent modification errors

2. **Reduce Timeouts & Add Progress** (P1)
   - Reduce to 30-second default timeout
   - Implement persistent thread pool
   - Add progress streaming
   - Better timeout messages
   - **Deliverable**: Much better UX, 150s time savings per query

### Sprint 2: Memory & Error Handling (5-6 hours)
**Week 1-2 Focus**: Stability improvements

3. **Fix Memory Leaks** (P1)
   - Implement managed checkpointer
   - Add automatic cleanup (24hr retention)
   - Add memory usage monitoring
   - **Deliverable**: Stable long-term memory usage

4. **Improve Error Handling** (P2)
   - Create centralized error handler
   - Add persistent logging
   - User-friendly error messages
   - **Deliverable**: Better debugging, better UX

### Sprint 3: Code Quality (2-3 hours)
**Week 2 Focus**: Maintainability

5. **Refactor Duplicate Code** (P2)
   - Consolidate config functions
   - Remove dead code
   - **Deliverable**: Cleaner codebase

---

## Success Metrics

### Before Phase 3
- ❌ Race conditions cause data loss
- ❌ 180-second timeout frustrates users
- ❌ Memory grows unbounded
- ❌ Poor error messages

### After Phase 3
- ✅ No race conditions (request locking)
- ✅ 30-second timeout with progress feedback
- ✅ Stable memory usage (24hr cleanup)
- ✅ Clear error messages with logging

### Reliability Improvement
- **Data Loss Risk**: HIGH → NONE
- **Timeout Frustration**: HIGH → LOW
- **Memory Stability**: POOR → GOOD
- **Debuggability**: POOR → GOOD

---

## Quick Wins (Can Implement Now)

### 1. Add Request ID Validation (15 min)
```python
# At top of dashboard.py
_active_request_ids = set()
_request_lock = threading.Lock()
```

### 2. Persistent Thread Pool (10 min)
```python
# Module level
_executor_pool = ThreadPoolExecutor(max_workers=4)
```

### 3. Deep Copy Session Data (5 min)
```python
import copy
session_data = copy.deepcopy(session_data)  # Instead of .copy()
```

### 4. Add Error Logger (20 min)
```python
import logging
logging.basicConfig(filename='dashboard.log', level=logging.ERROR)
```

---

## Risks & Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**:
- Test each fix independently
- Keep old code commented for rollback
- Incremental deployment

### Risk 2: Performance Impact of Locking
**Mitigation**:
- Use fine-grained locks (not global)
- Lock only during critical sections
- Profile performance before/after

### Risk 3: Complex Dashboard Refactoring
**Mitigation**:
- Focus on high-impact fixes first
- Don't rewrite everything
- Pragmatic improvements only

---

## Next Steps

1. **Implement Quick Wins** (30 min total)
   - Add request locking infrastructure
   - Use persistent thread pool
   - Deep copy session data

2. **Test Critical Path** (1 hour)
   - Submit multiple queries rapidly
   - Verify no data loss
   - Check for race conditions

3. **Deploy & Monitor** (ongoing)
   - Watch for errors in logs
   - Monitor memory usage
   - Collect user feedback

---

## Conclusion

Phase 3 focuses on **high-impact, low-risk improvements** that significantly enhance reliability without requiring major rewrites.

**Total Estimated Effort**: 13-17 hours
**Expected Impact**: HIGH
**Risk Level**: LOW-MEDIUM

The priority order ensures critical issues are fixed first, with incremental improvements that can be tested and deployed independently.
