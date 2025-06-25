# Add Indexing Health Check Endpoint

**Priority**: Medium  
**Status**: Open  
**Created**: 2025-06-25  

## Issue
No way to verify if file indexing is working properly. QA testing revealed silent failures in language parsing and semantic indexing.

## Proposed Solution
Add health check endpoint/command that reports:
- Files discovered vs. files indexed
- Language breakdown (files per language)
- Embedding status (chunks with/without embeddings)
- Recent indexing activity
- Parser failures/errors

## Example Output
```json
{
  "status": "degraded",
  "files_discovered": 1247,
  "files_indexed": 892,
  "languages": {
    "python": {"files": 234, "chunks": 1456, "embedded": 1456},
    "markdown": {"files": 45, "chunks": 0, "embedded": 0},
    "go": {"files": 78, "chunks": 0, "embedded": 0}
  },
  "errors": [
    "markdown parser failed: tree-sitter binding missing",
    "go parser failed: unknown error"
  ]
}
```

## Benefits
- Easier debugging of indexing issues
- Proactive detection of parser failures
- Better user experience (know when indexing complete)
- Monitoring/alerting capability

## Implementation
- Add to MCP server as new tool
- Include in CLI as `chunkhound status` command
- Consider periodic health reporting