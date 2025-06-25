# Docstring and Comment Indexing Gaps

**Priority**: Medium  
**Status**: Open  
**Created**: 2025-06-25  

## Issue
During QA testing, regex searches failed to find content within docstrings and comments, while semantic search succeeded. This indicates inconsistent text extraction for different search methods.

## Test Case
```python
"""
This file contains unique identifier: XYZ123_PYTHON_UNIQUE_TEST
"""

def unique_test_function_xyz123():
    """A unique test function with identifier xyz123"""
    return "test_result_xyz123"
```

**Results**:
- `search_regex("XYZ123_PYTHON_UNIQUE_TEST")` → 0 results
- `search_regex("unique_test_function_xyz123")` → 1 result  
- `search_semantic("unique test function xyz123")` → 1 result

## Impact
- Documentation content not searchable via regex
- Inconsistent search behavior between methods
- Reduced utility for finding code by comments

## Scope
Verify docstring/comment indexing for all working languages:
- Python docstrings (`"""`)
- Java Javadoc (`/** */`)
- C# XML docs (`/// <summary>`)
- TypeScript JSDoc (`/** */`)
- JavaScript JSDoc (`/** */`)
- Markdown content (already working)
- Inline comments (`//`, `#`, `/* */`)

## Expected Behavior
Both regex and semantic search should find content in:
1. File-level documentation
2. Function/method docstrings  
3. Class documentation
4. Inline comments
5. Multi-line comments

## Validation
Create test files with unique identifiers in various comment styles and verify both search methods return consistent results.