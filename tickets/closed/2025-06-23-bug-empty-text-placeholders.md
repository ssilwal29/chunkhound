# [BUG] Empty Text Placeholder Warnings

**Date**: 2025-06-23  
**Priority**: Medium  
**Status**: Closed  
**Files**: `providers/embeddings/openai_provider.py`, `services/indexing_coordinator.py`

## Problem

Multiple warnings about empty text being replaced with placeholders:
```
WARNING | Empty text at index 985, using placeholder
WARNING | Empty text at index 986, using placeholder
... (multiple similar warnings) ...
WARNING | Empty text at index 2536, using placeholder
```

## Root Cause

The `validate_texts` method in `providers/embeddings/openai_provider.py:340-358` correctly handles empty text by:
1. Detecting empty/whitespace-only strings
2. Replacing with `[EMPTY]` placeholder
3. Logging warnings for each occurrence

This indicates upstream data quality issues where chunks have empty text content.

## Solution

Improve text validation upstream:
- Filter empty text chunks before embedding generation
- Investigate why chunks have empty text (different from empty code)
- Consider batch filtering to reduce embedding API calls
- Add metrics to track empty text frequency

## Acceptance Criteria

- [x] Reduce frequency of empty text placeholders
- [x] Filter empty text chunks before embedding validation
- [x] Maintain embedding quality for valid content
- [x] Add monitoring for empty text patterns

## Resolution

Fixed by adding pre-embedding filtering in `services/indexing_coordinator.py:_generate_embeddings()`:
- Filter empty text chunks before sending to embedding provider
- Added metrics logging for empty chunk counts
- Prevents OpenAI provider from creating `[EMPTY]` placeholders
- Maintains embedding quality for valid content only