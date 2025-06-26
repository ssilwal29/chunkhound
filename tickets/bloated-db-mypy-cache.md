# Database Bloating Due to .mypy_cache Indexing

## Issue Summary
The MCP server's periodic indexer causes database bloating by indexing `.mypy_cache` files, and running `chunkhound index` does not clean up this bloated data.

## Root Cause Analysis

### 1. Missing .mypy_cache in Default Exclude Patterns
- Location: `services/indexing_coordinator.py:694`
- Default exclude patterns: `["*/__pycache__/*", "*/node_modules/*", "*/.git/*", "*/venv/*", "*/.venv/*"]`
- Missing: `*/.mypy_cache/*` pattern
- `.gitignore` correctly excludes `.mypy_cache/` (line 150), but this is not reflected in the indexer

### 2. Periodic Indexer in MCP Server
- The MCP server's `PeriodicIndexManager` calls `_discover_files` with `exclude_patterns=None`
- This uses the default exclude patterns, which don't include `.mypy_cache`
- Result: Thousands of `.mypy_cache` files get indexed (2784 files in the bloated example)

### 3. No Orphaned File Cleanup
- Location: `services/indexing_coordinator.py:737`
- The `_cleanup_orphaned_files` method is not implemented (returns 0)
- This means running `chunkhound index` won't remove files that shouldn't be indexed
- Even if exclude patterns were fixed, existing bloated data wouldn't be cleaned

## Impact
- Database size explosion: 3208 files vs 208 files (15x increase)
- Chunk count explosion: 514,769 chunks vs 5,583 chunks (92x increase)
- `.mypy_cache` JSON files create thousands of duplicate chunks (e.g., 2634 duplicates of ".class: TypeVarType")
- Performance degradation for search operations
- Wasted embedding generation attempts

## Fix Required
1. Add `*/.mypy_cache/*` to default exclude patterns in `IndexingCoordinator._discover_files`
2. Implement `_cleanup_orphaned_files` to remove database entries for files that no longer match current patterns
3. Consider aligning default exclude patterns with common `.gitignore` entries

## Fix Implemented (2025-06-26)

### Changes Made
1. **Centralized exclude patterns**: Added `DEFAULT_EXCLUDE_PATTERNS` in `IndexingCoordinator` including `.mypy_cache`
2. **Fixed cleanup method**: 
   - `_cleanup_orphaned_files` now accepts exclude patterns parameter
   - Matches patterns against both relative and absolute paths
   - Uses progress bar instead of individual log messages
3. **Fixed bugs**: Changed `_db_provider` to `_db` references
4. **Ensured consistency**: MCP server periodic indexer now calls cleanup on startup
5. **Reduced log noise**: Changed file deletion logs from INFO to DEBUG level

### Result
- `chunkhound index` removes `.mypy_cache` files from DB without regenerating embeddings
- Both CLI and MCP server use identical cleanup logic
- Existing valid files and their embeddings are preserved
- Progress bars maintain clean UI during cleanup