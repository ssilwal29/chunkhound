# 2025-06-26 - [BUG] Bash and Makefile Files Not Being Indexed

## Priority
**High** - Core language support functionality broken

## Issue Description
During comprehensive QA testing, discovered that Bash (.sh) and Makefile (no extension) files are not being indexed by ChunkHound, despite having dedicated parsers implemented.

## Impact
- Bash scripts and Makefiles in codebases are not searchable
- Reduced language coverage (14/16 vs 16/16 expected)
- Incomplete codebase indexing for projects using these file types

## Test Case
Created test files with unique markers:

### Bash Test File (`qa_test_bash.sh`)
```bash
#!/bin/bash

# QA_BASH_UNIQUE_MARKER_12345
qa_bash_test_function() {
    # QA_BASH_FUNCTION_MARKER_67890
    echo "Bash test"
}

QA_BASH_VAR="QA_BASH_VARIABLE_MARKER_99999"
```

### Makefile Test File (`qa_test_makefile`)
```makefile
# QA_MAKEFILE_UNIQUE_MARKER_12345

qa_test_target:
	# QA_MAKEFILE_TARGET_MARKER_67890
	@echo "Makefile test"

QA_MAKEFILE_VAR = QA_MAKEFILE_VARIABLE_MARKER_99999
```

## Test Results
- **Regex Search**: `QA_BASH_UNIQUE_MARKER_12345` → 0 results
- **Regex Search**: `QA_MAKEFILE_UNIQUE_MARKER_12345` → 0 results
- **Content Search**: `Bash test` → 0 results
- **Content Search**: `Makefile test` → 0 results

## Investigation Required

### File Extension Mapping
Check if file extensions are properly mapped:
- `.sh` → BashParser
- `Makefile`, `makefile`, no extension → MakefileParser

### Parser Registration
Verify parsers are registered in the language registry:
- `providers/parsing/bash_parser.py` → Registry integration
- `providers/parsing/makefile_parser.py` → Registry integration

### File Watcher Configuration
Investigate if file watcher is configured to detect:
- `.sh` files
- Files without extensions (Makefile pattern)

### Parser Availability
Check if parsers report as available:
- `BashParser.is_available`
- `MakefileParser.is_available`

## Expected Behavior
1. Bash and Makefile files should be automatically detected and indexed
2. All chunk types (functions, variables, targets) should be extracted
3. Content should be searchable via both regex and semantic search
4. File changes should trigger re-indexing

## Debugging Steps
1. Check file extension mappings in language detection logic
2. Verify parser registration in `registry/` module
3. Test parser availability and functionality in isolation
4. Examine file watcher patterns and inclusion rules
5. Review indexing coordinator language support list

## Success Criteria
- [ ] `.sh` files are automatically indexed
- [ ] Makefile files (with and without extension) are indexed
- [ ] Bash functions, variables, and comments are extractable
- [ ] Makefile targets, variables, and rules are extractable
- [ ] Content is searchable via MCP search tools
- [ ] File modifications trigger proper re-indexing
- [ ] QA test markers return expected results

## Files to Investigate
- `chunkhound/file_watcher.py` - File detection patterns
- `services/indexing_coordinator.py` - Language parser mapping
- `providers/parsing/bash_parser.py` - Parser implementation
- `providers/parsing/makefile_parser.py` - Parser implementation
- `registry/__init__.py` - Parser registration
- `core/types/common.py` - Language enum definitions

## Related Components
- File discovery and watching system
- Language parser registry
- Indexing coordinator
- MCP search tools

## Discovered During
Comprehensive QA testing of semantic_search and regex_search MCP tools (2025-06-26)

## Reporter
QA Testing System

## Root Cause
Missing dependency: `tree-sitter-bash` was not listed in `pyproject.toml` dependencies. The BashParser crashes during initialization when the dependency is not available, preventing parser registration.

## Fix Applied
Added `tree-sitter-bash>=0.21.0` to the dependencies in `pyproject.toml`. This allows the BashParser to initialize successfully using the direct tree-sitter-bash package.

## Verification
- Bash parser now initializes successfully (using language pack fallback)
- Makefile parser continues to work correctly
- Test files with unique markers are properly indexed
- Both file types are searchable via regex and semantic search

## Status
**RESOLVED** - Both Bash and Makefile files are now being indexed correctly.