# 2025-06-23 - [BUG] TypeScript Method Extraction Failure
**Priority**: High
**Status**: Closed

TypeScript parser fails to extract class methods and function names, with tree-sitter errors and missing function detection in parsed code.

## Problem
- Error: `Invalid node type at row 1, column 28: property_name`
- Function `getDisplayName` not found in extraction: expected in function list but missing
- Class methods not extracted: `assert len(method_chunks) > 0` fails with length 0
- Location: `providers/parsing/typescript_parser.py:481` in `_extract_class_methods`

## Root Cause
Tree-sitter node handling issues:
1. `property_name` nodes not properly handled in class method extraction
2. Arrow function detection fails to extract proper function names
3. TypeScript-specific syntax (type annotations, interfaces) interfering with extraction

## Solution
Fix TypeScript parser tree-sitter queries:

1. **Update class method extraction** to handle `property_name` nodes
2. **Improve function name detection** for arrow functions and method declarations
3. **Handle TypeScript-specific syntax** (type annotations, optional parameters)
4. **Fix tree-sitter query patterns** for modern TypeScript/ES6+ features

## Test Evidence
```typescript
// This code should extract functions but doesn't:
const getDisplayName = (): string => "name";  // Missing from function list

class TestClass {
    methodName(): void { }  // Not extracted as method
}
```

## Files Affected
- `providers/parsing/typescript_parser.py:481` (`_extract_class_methods`)
- `tests/test_typescript_parser.py:149,270` (failing tests)

# History

## 2025-06-23
Test failures show TypeScript parser has same tree-sitter node handling issues as JavaScript parser, plus TypeScript-specific syntax complications. Function and method extraction completely broken.

**FIXED**: Updated tree-sitter queries to properly handle:
1. Arrow function variable assignments using `variable_declarator` pattern
2. Class method names with wildcard matching for `property_name` nodes
3. All TypeScript parser tests now pass (12/12)