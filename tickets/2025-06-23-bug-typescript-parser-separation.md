# 2025-06-23 - [BUG] TypeScript Parser Separation
**Priority**: High
**Status**: Open

TypeScript indexing fails with "Impossible pattern at row 3, column 25" when parsing files. Root cause: unified JavaScript/TypeScript parser uses incompatible tree-sitter query patterns.

## Problem
- Error: `Failed to extract TypeScript components: Impossible pattern at row 3, column 25`
- Location: `providers/parsing/typescript_parser.py:511-523` 
- Invalid query pattern: `return_type: (type_annotation...)` doesn't exist in JavaScript grammar
- Current approach tries to use TypeScript-specific AST nodes in mixed JavaScript/TypeScript contexts

## Solution
Separate JavaScript and TypeScript parsers following industry best practices:

1. **Create base class** `TreeSitterParserBase` with shared functionality
2. **Separate parsers**: `JavaScriptParser` and `TypeScriptParser` with language-specific queries
3. **Language-specific queries**: 
   - JavaScript: Simple patterns without type annotations
   - TypeScript: Full type system support (interfaces, type aliases, generics)

## Implementation
- Extract shared methods to base class (`_initialize`, `_get_node_text`, `_create_chunk`)
- JavaScript parser: Remove TypeScript-specific query patterns
- TypeScript parser: Use proper TypeScript AST node types
- Update `ParserRegistry` for file extension routing

## Files
- `providers/parsing/base_parser.py` (NEW)
- `providers/parsing/javascript_parser.py` (refactor)
- `providers/parsing/typescript_parser.py` (refactor)
- `registry/parser_registry.py` (update)

## Benefits
- Eliminates "impossible pattern" errors
- Aligns with tree-sitter ecosystem (separate `tree-sitter-javascript` vs `tree-sitter-typescript`)
- Reduces code duplication >50%
- Enables TypeScript-specific features

# History

## 2025-06-23
Root cause identified through tree-sitter query analysis. Industry research confirms separate parsers are standard practice. Current unified approach creates grammar conflicts when TypeScript-specific nodes don't exist in JavaScript parsing contexts. Solution: implement base class architecture with language-specific parsers.