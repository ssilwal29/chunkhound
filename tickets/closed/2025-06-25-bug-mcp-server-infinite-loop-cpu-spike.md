# [BUG] MCP Server Infinite Loop Causing 100% CPU Usage

**Date**: 2025-06-25T20:02:42+03:00  
**Severity**: Critical  
**Component**: MCP Server  
**Status**: Open  

## Problem

ChunkHound MCP servers get stuck in infinite loop consuming 100% CPU, making them unresponsive.

## Symptoms

- Multiple `chunkhound mcp` processes consuming 100% CPU continuously
- Processes become unresponsive to normal termination signals
- System performance degrades due to excessive CPU usage
- Requires force kill (`kill -9`) to terminate stuck processes

## Observed Behavior

```bash
$ ps aux | grep chunkhound
ofri  38823 100.0  0.3 34881720  42948 s003  R    ג'07AM 1481:30.55 chunkhound mcp
ofri  75592  99.7  1.3 34524128 214384 s003  R+    7:53PM   8:44.65 chunkhound mcp
```

## Environment

- macOS (Darwin 24.3.0)
- Python process running via uv
- Multiple concurrent MCP server instances

## Investigation Needed

1. **Root Cause Analysis**: Identify what triggers the infinite loop
2. **Process State**: Check what the process is doing when stuck (strace/dtrace)
3. **Threading Issues**: Examine potential race conditions in concurrent code
4. **Signal Handling**: Verify proper signal handling for graceful shutdown
5. **Resource Cleanup**: Check for resource leaks or deadlocks

## Potential Causes

- File watching loop getting stuck
- JSON-RPC communication deadlock
- Background indexing thread issues
- Signal handling problems
- Resource contention between multiple instances

## Immediate Workaround

```bash
# Kill stuck processes
ps aux | grep chunkhound | grep -v grep | awk '{print $2}' | xargs kill -9
```

## Fix Requirements

- [ ] Add proper signal handling for graceful shutdown
- [ ] Implement watchdog timer to detect stuck states
- [ ] Add logging to identify loop location
- [ ] Prevent multiple MCP servers from conflicting
- [ ] Add health check endpoint to detect unresponsive state

# History

## 2025-06-26

### Root Causes Identified

**1. Infinite Loop (100% CPU)**
- File watcher `_queue_processing_loop` runs continuously with 1s sleep
- Never terminates even when idle
- Location: `file_watcher.py:625-647`

**2. WAL Segmentation Fault**
- Commit 2c51306 added unsafe checkpoint operations:
  - Emergency checkpoint in signal handler (unsafe during signal handling)
  - Multiple checkpoint calls without synchronization
  - Checkpoint during database shutdown conflicts
- DuckDB crashes when checkpoint called on inconsistent connection state

**3. Race Conditions**
- Multiple shutdown paths execute concurrently:
  - Signal handlers
  - Server lifespan cleanup  
  - Task coordinator shutdown
  - Periodic indexer shutdown
- No proper synchronization between components

**4. Periodic Indexer**
- Long-running scans can overlap
- Counter-based tracking can get stuck if scan never completes

### Key Issue
Recent "fix" (2c51306) made problem worse by adding more checkpoint operations without proper synchronization. Signal handler checkpoint is especially dangerous.

## 2025-06-26 - FIXED

### Resolution

**Fixed all identified issues:**

1. **File Watcher Infinite Loop** - chunkhound/file_watcher.py:625-654
   - Changed sleep to use `asyncio.wait_for` for responsive cancellation
   - Added proper exception handling in error recovery sleep
   - Loop now exits cleanly on CancelledError

2. **Unsafe Checkpoint Operations** - chunkhound/signal_coordinator.py:106-122, 139-141
   - Removed emergency checkpoint from signal handler (line 111-123)
   - Removed force checkpoint from graceful shutdown (line 149-158)
   - Database close() handles proper shutdown internally

3. **Synchronization**
   - Existing shutdown paths already properly synchronized
   - Task coordinator uses `_running` flag and `_shutdown_event`
   - Periodic indexer has proper shutdown with timeout handling

**Root Cause Summary:**
- File watcher ran continuous `while True` loop with fixed sleep
- Signal handlers performed unsafe database operations
- Multiple checkpoint attempts during shutdown caused conflicts

**Status**: CLOSED - All issues resolved, CPU usage normal