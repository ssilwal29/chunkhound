# 2025-06-25 - [FEATURE] Add Path Filtering to MCP Search Tools
**Priority**: High

## Problem

ChunkHound's MCP search tools (`search_regex`, `search_semantic`) currently search across all indexed files. Users need ability to limit search scope to specific paths or directories for focused results.

## Solution

Add optional `path` parameter to both MCP search tools to filter results by relative file paths.

## Implementation

### API Changes

```python
# MCP tool parameters (add to both search_regex and search_semantic)
{
    "path": {
        "type": "string",
        "description": "Optional relative path to limit search scope (e.g., 'src/', 'tests/')", 
        "optional": true
    }
}
```

### Backend Changes

1. **DatabaseProvider Interface**: Add `path_filter: str | None = None` parameter
2. **DuckDBProvider**: Implement SQL path filtering using `LIKE` patterns
3. **SearchService**: Add path parameter and validation
4. **MCP Layer**: Update tool schemas and input validation

### Security

- Path validation to prevent directory traversal
- Normalize relative paths to safe patterns  
- Limit to indexed file paths only

## Acceptance Criteria

- [x] `search_regex` accepts optional `path` parameter
- [x] `search_semantic` accepts optional `path` parameter  
- [x] Path filtering works for files and directories
- [x] Backward compatibility maintained
- [x] Security validation prevents path traversal
- [x] Tests cover path filtering scenarios

## Examples

```bash
# Search only in src/ directory
search_regex(pattern="def\\s+\\w+", path="src/")

# Search specific file
search_semantic(query="authentication logic", path="auth/handlers.py")

# Search test files
search_regex(pattern="assert", path="tests/")
```

# History

## 2025-06-25
Implemented path filtering feature across all layers of the application:

1. **DatabaseProvider Interface** (interfaces/database_provider.py):
   - Added `path_filter: str | None = None` parameter to `search_semantic` and `search_regex` methods
   - Updated docstrings with parameter descriptions

2. **DuckDBProvider Implementation** (providers/database/duckdb_provider.py):
   - Added `_validate_and_normalize_path_filter` method for security validation:
     - Prevents directory traversal attacks (blocks `..`, `~`, etc.)
     - Normalizes path separators to forward slashes
     - Ensures relative paths only (strips leading `/`)
     - Auto-adds trailing slash for directory patterns
   - Modified SQL queries to use `LIKE` pattern matching with `%/{path}%` format
   - Applied path filtering to both main queries and count queries for pagination

3. **Database Wrapper** (chunkhound/database.py):
   - Updated `search_semantic` and `search_regex` to pass through `path_filter` parameter
   - Fixed delegation to use provider directly for regex search (was incorrectly using SearchService)

4. **SearchService** (services/search_service.py):
   - Added `path_filter` parameter to both search methods
   - Updated method signatures and docstrings
   - Passed parameter through to database provider calls

5. **MCP Server** (chunkhound/mcp_server.py):
   - Added `path` parameter extraction from tool arguments
   - Updated tool schemas to include optional `path` field with description
   - Passed `path_filter` to database search methods

6. **Tests** (tests/test_path_filtering.py):
   - Created comprehensive test suite covering:
     - Regex search with path filtering
     - Semantic search with path filtering (skipped if no embedding provider)
     - Path validation security tests
     - Path normalization tests
   - Tests verify filtering works for directories and specific files

7. **Documentation** (examples/path_filtering_demo.py):
   - Created demo script showing various path filtering use cases
   - Includes security validation examples

**Key Implementation Details:**
- Used SQL `LIKE` with pattern `%/{normalized_path}%` to match absolute paths in DB
- Path validation prevents security vulnerabilities while being user-friendly
- Maintained backward compatibility - path parameter is optional
- All tests pass successfully

**What's Left:**
- Feature is complete and ready for use
- Consider adding path filtering to CLI tools in future iteration

## 2025-06-25 - Verification Complete
Verified path filtering functionality works correctly:

1. **Semantic Search**: Successfully filters results by path
   - Tested with `providers/` directory filter
   - Tested with specific file `chunkhound/mcp_server.py`
   - Results correctly limited to specified paths

2. **Regex Search**: Path filtering working as expected
   - Found test functions in `tests/` directory
   - Found specific functions in individual files
   - Returns empty results for non-existent paths

3. **Security Validation**: Confirmed working
   - Dangerous patterns blocked (`.., ~, etc.`)
   - Path normalization working correctly
   - Only relative paths accepted

4. **Backward Compatibility**: Maintained
   - Both search tools work without path parameter
   - Optional parameter doesn't break existing usage

**Status: COMPLETE** - All acceptance criteria met and verified.