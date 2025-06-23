# [BUG] Empty Chunk Content Filtering

**Date**: 2025-06-23  
**Priority**: Medium  
**Status**: Open  
**Files**: `services/indexing_coordinator.py`

## Problem

Multiple warnings about empty chunks being skipped:
```
WARNING | Skipping chunk with empty code content: header_534 at lines 534-535
WARNING | Skipping chunk with empty code content: header_536 at lines 536-537
... (multiple similar warnings) ...
WARNING | Skipping chunk with empty code content: code_block_538 at lines 538-545
```

## Root Cause

The `_store_chunks` method in `services/indexing_coordinator.py:487-520` correctly filters empty chunks but this indicates:
1. Upstream parsing is creating chunks with empty content
2. Markdown headers and code blocks are being parsed as empty
3. No validation at chunk creation time

## Solution

Improve chunk filtering at creation time:
- Add validation in chunking phase before storage
- Investigate why markdown headers/code blocks are empty
- Consider whether some "empty" chunks should be preserved (e.g., section markers)

## Acceptance Criteria

- [ ] Reduce/eliminate empty chunk warnings
- [ ] Validate chunk content during creation, not just storage
- [ ] Preserve meaningful empty chunks (if any)
- [ ] No regression in chunk quality or completeness