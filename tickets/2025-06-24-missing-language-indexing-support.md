# [BUG] Missing Language Indexing Support Despite Parser Availability

**Date**: 2025-06-24  
**Priority**: High  
**Status**: Open  
**Type**: Bug  

## Problem Summary

Multiple language parsers exist in `providers/parsing/` but files in those languages are not being indexed or made searchable through MCP tools. QA testing revealed that while parsers are implemented, the indexing pipeline is not processing these file types.

## Languages Affected

The following languages have parsers but **fail to index**:
- **Rust** (.rs files) - `rust_parser.py` exists
- **Go** (.go files) - `go_parser.py` exists  
- **C** (.c files) - `c_parser.py` exists
- **C++** (.cpp files) - `cpp_parser.py` exists
- **Kotlin** (.kt files) - `kotlin_parser.py` exists
- **Groovy** (.groovy files) - `groovy_parser.py` exists
- **Bash** (.sh files) - `bash_parser.py` exists
- **TOML** (.toml files) - `toml_parser.py` exists
- **MATLAB** (.m files) - `matlab_parser.py` exists
- **Makefile** - `makefile_parser.py` exists

## Languages That Work

Confirmed working languages:
- **Python** (.py files) ✅
- **Java** (.java files) ✅
- **C#** (.cs files) ✅
- **TypeScript** (.ts files) ✅
- **JavaScript** (.js files) ✅
- **Markdown** (.md files) ✅

## QA Test Evidence

### Test Method
1. Created test files for each language with unique identifiers
2. Waited 3-8 seconds for indexing
3. Performed both semantic and regex searches
4. Verified task coordinator showed active processing

### Results
- All non-working languages returned empty search results
- Working languages returned proper chunk data with file paths, line numbers, and code content
- Task coordinator stats: `{"tasks_queued": 65, "tasks_completed": 64, "is_running": true}` - showing active processing

### Sample Test Files Created
```rust
// qa_test.rs
struct QARustTest {
    qa_test_field: String,
}
impl QARustTest {
    fn new() -> Self {
        QARustTest {
            qa_test_field: "rust_qa_unique_value".to_string(),
        }
    }
}
```

**Search Result**: Empty (should have found `rust_qa_unique_value`)

## Root Cause Analysis

### Possible Issues
1. **File Extension Mapping**: Languages may not be properly associated with file extensions
2. **Parser Registration**: Parsers exist but may not be registered in the indexing pipeline
3. **Configuration Missing**: Language detection or processing configuration incomplete
4. **Tree-sitter Integration**: Grammar files or language bindings may be missing

### Investigation Areas
- Check `chunkhound/parser.py` for language registration
- Verify file extension mapping in configuration
- Validate tree-sitter language grammar availability
- Review indexing coordinator language filtering

## Expected Behavior

When a `.rs`, `.go`, `.c`, etc. file is created/modified:
1. File should be detected by file watcher
2. Appropriate parser should be selected based on extension
3. File should be parsed into chunks using tree-sitter
4. Chunks should be stored in database with embeddings
5. Content should be searchable via MCP tools

## Impact

**High Impact**: This significantly limits ChunkHound's usefulness for polyglot codebases. Many projects use multiple languages, and the missing support reduces search coverage.

## Files to Investigate

```
chunkhound/parser.py              # Main parser coordination
chunkhound/config.py              # Language configuration  
providers/parsing/__init__.py     # Parser registration
chunkhound/file_watcher.py        # File extension filtering
services/indexing_coordinator.py  # Language processing pipeline
```

## Test Commands for Validation

```bash
# Create test files
echo 'fn test() { println!("rust_test"); }' > test.rs
echo 'func test() { fmt.Println("go_test") }' > test.go

# Check if files are being processed
# Search for unique identifiers after 3-5 seconds
```

## Success Criteria

- [ ] All languages with existing parsers can be indexed
- [ ] Search operations return results for all supported file types
- [ ] File extension detection works for all parser-supported languages
- [ ] Documentation updated with complete language support list

---

**Reporter**: QA Testing  
**Discovered During**: Extended MCP tool validation testing