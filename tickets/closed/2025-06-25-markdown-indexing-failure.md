# Markdown Indexing Complete Failure

**Priority**: Critical  
**Status**: Open  
**Created**: 2025-06-25  

## Issue
Markdown files are not being indexed at all. Created test markdown file with headers and content - zero results from both regex and semantic search.

## Test Case
```markdown
# Test Markdown Header

This is a test markdown file for QA testing.

## Secondary Header

Testing markdown_qa_test_identifier
```

## Results
- `search_regex("markdown_qa_test_identifier")`: 0 results
- `search_semantic("markdown")`: 0 results

## Impact
- Documentation not searchable
- README files invisible to search
- Major workflow disruption for docs-heavy projects

## Context
- Markdown parser exists: `providers/parsing/markdown_parser.py`
- Other languages working (Python, Java, etc.)
- Suggests parser registration or tree-sitter issue

## Urgency
Critical - documentation search is core functionality for most projects.

## Investigation
- Check markdown parser registration
- Verify tree-sitter-markdown binding
- Test with various .md file extensions
- Review error logs during indexing