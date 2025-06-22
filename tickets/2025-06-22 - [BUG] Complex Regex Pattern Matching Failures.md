# 2025-06-22 - [BUG] Complex Regex Pattern Matching Failures

**Priority**: Medium  
**Status**: WONTFIX

**Issue**: Complex regex patterns fail to return expected matches while simple patterns work correctly. During QA testing, patterns like `Database.*ChunkHound.*service.*layer` and `markdown_qa_unique_identifier_2025` returned no results despite content existing in indexed files.

**Evidence**:
- ✅ Simple patterns work: `ChunkHound`, `python_qa_unique_identifier_2025` 
- ❌ Complex patterns fail: `Database.*ChunkHound.*service.*layer`, `markdown_qa_unique_identifier_2025`
- File content confirmed to exist via semantic search

**Impact**: Reduces regex search utility for complex pattern matching scenarios.

**Root Cause**: Complex regex patterns fail because they expect to match across content boundaries that don't exist within individual code chunks. The chunking process splits code into logical units (functions, classes, etc.), so patterns spanning multiple concepts often don't match within a single chunk's content. Additionally, DuckDB's RE2 regex engine has different multiline matching behavior.

**Resolution**: WONTFIX - This is a fundamental architectural limitation. Complex cross-chunk patterns should use semantic search instead of regex.

# History

## 2025-06-22T11:46:00+03:00
Initial discovery during comprehensive QA testing of semantic_search and regex_search MCP tools. Simple patterns work, complex ones fail without error messages.

## 2025-06-22T20:30:00+03:00
**Root cause identified**: Complex patterns like `Database.*ChunkHound.*service.*layer` fail because:

1. **Chunking Boundaries**: Code is parsed into logical chunks (functions, classes, etc.). Multi-concept patterns span across chunk boundaries where no single chunk contains all terms in sequence.

2. **DuckDB RE2 Engine**: Uses `regexp_matches(c.code, ?)` with RE2 engine which has different multiline behavior than PCRE.

3. **Evidence**: Pattern `Database.*service` works (finds "Database connection manager - delegates to service layer"), but `Database.*ChunkHound.*service.*layer` fails because no single chunk contains all four terms.

4. **markdown_qa_unique_identifier_2025**: Confirmed this identifier doesn't exist in codebase (semantic search found no matches).

**Closing as WONTFIX**: This is fundamental to ChunkHound's architecture. For cross-chunk pattern matching, use semantic search instead of regex. Regex is designed for intra-chunk patterns only.