# 2025-06-22 - [BUG] Complex Regex Pattern Matching Failures

**Priority**: Medium  
**Status**: Open

**Issue**: Complex regex patterns fail to return expected matches while simple patterns work correctly. During QA testing, patterns like `Database.*ChunkHound.*service.*layer` and `markdown_qa_unique_identifier_2025` returned no results despite content existing in indexed files.

**Evidence**:
- ✅ Simple patterns work: `ChunkHound`, `python_qa_unique_identifier_2025` 
- ❌ Complex patterns fail: `Database.*ChunkHound.*service.*layer`, `markdown_qa_unique_identifier_2025`
- File content confirmed to exist via semantic search

**Impact**: Reduces regex search utility for complex pattern matching scenarios.

**Root Cause**: Unknown - possible regex engine limitations or pattern processing issues in search implementation.

**Suggested Fix**: Investigate regex pattern handling in search service implementation.

# History

## 2025-06-22T11:46:00+03:00
Initial discovery during comprehensive QA testing of semantic_search and regex_search MCP tools. Simple patterns work, complex ones fail without error messages.