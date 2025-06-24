# Rust Language Support

**Status:** Closed  
**Priority:** Medium  
**Assigned:** N/A  
**Created:** 2025-06-24  
**Completed:** 2025-06-24  

## Summary

Add comprehensive Rust language support to ChunkHound using tree-sitter parsing. This will enable semantic code search and analysis for Rust codebases.

## Requirements

### Core Implementation
- **Rust Parser**: Create `providers/parsing/rust_parser.py` with tree-sitter-rust integration
- **Language Registry**: Add `RUST = "rust"` to `core/types/common.py` Language enum
- **File Extension Mapping**: Map `.rs` files to Rust language
- **Provider Registration**: Register RustParser in `registry/__init__.py`

### Rust-Specific Chunks
Support extraction of these Rust semantic units:
- **Functions**: `fn function_name()` 
- **Methods**: `impl` block methods and trait implementations
- **Structs**: `struct StructName` definitions
- **Enums**: `enum EnumName` with variants
- **Traits**: `trait TraitName` definitions
- **Implementations**: `impl` blocks for structs/traits
- **Modules**: `mod module_name` declarations
- **Macros**: `macro_rules!` definitions
- **Constants**: `const` and `static` declarations
- **Types**: `type` aliases

### Tree-sitter Integration
- Use official `tree-sitter-rust` grammar
- Follow existing parser patterns from `go_parser.py` and `base_parser.py`
- Support qualified naming (module::struct::method)
- Extract Rust-specific metadata (visibility, mutability, etc.)

## Technical Design

### Parser Structure
```python
class RustParser(TreeSitterParserBase):
    def __init__(self):
        super().__init__(Language.RUST)
        # Rust-specific chunk types configuration
    
    def _extract_chunks(self, tree_node, source, file_path):
        # Extract functions, structs, enums, traits, etc.
```

### Chunk Types Mapping
- Functions → `ChunkType.FUNCTION`
- Methods → `ChunkType.METHOD` 
- Structs → `ChunkType.STRUCT`
- Enums → `ChunkType.ENUM`
- Traits → `ChunkType.TRAIT`
- Implementations → `ChunkType.INTERFACE` (for trait impls)
- Modules → `ChunkType.NAMESPACE`
- Macros → `ChunkType.MACRO`
- Constants/statics → `ChunkType.VARIABLE`
- Type aliases → `ChunkType.TYPE`

### File Extensions
Add to `Language.from_file_extension()`:
```python
'.rs': cls.RUST,
```

## Implementation Steps

1. **Update Language enum** - Add RUST to `core/types/common.py`
2. **Create RustParser** - Implement `providers/parsing/rust_parser.py`
3. **Register parser** - Add to `registry/__init__.py` 
4. **Add file mapping** - Update extension detection logic
5. **Test implementation** - Verify parsing of sample Rust files

## Dependencies

- `tree-sitter-language-pack` (should include rust grammar)
- No additional dependencies required

## Testing

- Create test Rust files with various constructs
- Verify chunk extraction accuracy
- Test qualified name generation
- Validate metadata extraction

## Success Criteria

- [x] Rust files (.rs) are correctly identified
- [x] All major Rust constructs are extracted as chunks
- [x] Qualified names include module paths
- [x] Parser integrates seamlessly with existing architecture
- [x] No performance regression on existing languages

## Notes

- Follow existing parser patterns for consistency
- Rust's ownership system and lifetime annotations should be preserved in code chunks
- Consider Rust's module system for proper namespace handling
- Support both library and binary crate structures