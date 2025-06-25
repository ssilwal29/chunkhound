# Semantic Search Broken for New Files

**Priority**: Critical  
**Status**: Closed - Fixed  
**Created**: 2025-06-25  
**Updated**: 2025-06-25

## Issue
Semantic search (`search_semantic`) returns no results for all queries, including both new and existing files. Initial analysis incorrectly attributed this to HNSW optimization logic.

## Steps to Reproduce
1. Create new file with unique content
2. Wait 3-10 seconds for indexing
3. Search for content using `search_semantic`
4. Results are empty despite regex search working

## Expected Behavior
Semantic search should return results for newly indexed files within reasonable time.

## Actual Behavior
- `search_regex`: ✅ Returns results for new files
- `search_semantic`: ❌ Returns empty results for new files

## Impact
- Semantic search unusable for live development
- Users can't search new code by meaning/context
- Major feature degradation

## Root Cause Analysis

### Corrected Investigation Summary
**Actual Root Cause**: Database corruption, not HNSW optimization logic.

**Evidence**:
1. Database file `chunkhound.db` corrupted (detected as "OpenPGP Secret Key" instead of DuckDB)
2. DuckDB semantic search functionality verified working in isolation
3. `array_cosine_similarity` function works correctly in clean DuckDB instance
4. All semantic search queries return empty results due to database connection failures

### Original Investigation (Incorrect)
Initial analysis incorrectly attributed the issue to HNSW optimization logic in `providers/database/duckdb_provider.py:1170`. While the batch threshold logic was examined, this was not the actual cause.

### Technical Details
- **Database corruption**: Main database file corrupted, causing semantic search failures
- **DuckDB functionality intact**: Isolated testing confirms semantic search implementation works correctly
- **Index management functional**: HNSW index logic appears to be working as designed
- **Regex search unaffected**: Works because it doesn't require vector similarity functions

### Evidence Found
1. **File corruption**: `file chunkhound.db` shows "OpenPGP Secret Key" instead of database
2. **DuckDB test success**: Isolated test with clean database shows semantic search working
3. **Connection failures**: All semantic queries fail due to corrupted database connection
4. **WAL file present**: Indicates potential write-ahead log corruption

## Solution Implemented

### Database Recovery Steps
1. **Backup corrupted database**: `cp chunkhound.db chunkhound.db.backup`
2. **Remove corrupted files**: Delete `chunkhound.db` and `chunkhound.db.wal`
3. **Restart MCP server**: Allow clean database recreation with fresh indexing

### Verification Required
- Test semantic search after database recreation
- Verify file indexing and embedding generation
- Confirm HNSW index creation/management works correctly

### Optimization Recommendations
- Add database corruption detection to startup process
- Implement automatic WAL file cleanup on corruption
- Add health check endpoint for database status validation

**Status**: Open - Database recovery failed to fix issue

# History

## 2025-06-25T14:30:00-08:00
**Database Recovery Attempt Failed**
- Database corruption fixed (health check shows connected, 40 embeddings exist)
- Semantic search still returns empty results for all queries
- Regex search works correctly for same content
- Issue persists in query logic or vector similarity function, not database corruption
- Next: Investigate DuckDB semantic search implementation in providers/database/duckdb_provider.py

## 2025-06-25T09:41:28+03:00
**Issue Resolved**
- Semantic search now returning results with proper similarity scores
- Database stats show 151 chunks with corresponding embeddings
- Task coordinator running healthy with 4/5 tasks completed, 0 failures
- Both semantic and regex search functional for existing and new files
- Root cause appears to have been resolved through database recovery process