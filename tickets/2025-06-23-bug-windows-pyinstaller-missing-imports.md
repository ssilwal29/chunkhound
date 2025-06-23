# [BUG] Windows PyInstaller Missing Hidden Imports

**Priority:** High  
**Status:** Open  
**Date:** 2025-06-23  
**Platform:** Windows (x86_64)  
**Component:** CI/CD Build Pipeline, PyInstaller Configuration  

## Problem Description

The Windows build fails during the PyInstaller phase due to missing hidden imports. Several core chunkhound modules are not found, causing the build to terminate.

## Error Details

```
20184 ERROR: Hidden import 'chunkhound.core.types' not found
20200 ERROR: Hidden import 'chunkhound.core.types.common' not found  
20200 ERROR: Hidden import 'providers.embedding.openai_provider' not found
20200 ERROR: Hidden import 'providers.parser.tree_sitter_provider' not found
```

## Root Cause

The `chunkhound-optimized.spec` file contains outdated or incorrect hidden import paths that don't match the current project structure:

```python
hiddenimports = [
    # These paths are incorrect/outdated:
    'chunkhound.core.types',           # ❌ Not found
    'chunkhound.core.types.common',    # ❌ Not found  
    'providers.embedding.openai_provider',    # ❌ Wrong path
    'providers.parser.tree_sitter_provider',  # ❌ Wrong path
    # ... other imports
]
```

## Expected Behavior

Windows build should complete successfully and create a working executable like the macOS ARM64 build did.

## Analysis

Based on the project structure, the correct import paths should be:

1. **Core types module**: Located at `core/types/` not `chunkhound.core.types/`
2. **Provider modules**: Located at `providers/` with different internal structure

## Solution

Update `chunkhound-optimized.spec` to fix the hidden imports:

1. **Remove non-existent imports:**
   ```python
   # Remove these lines:
   'chunkhound.core.types',
   'chunkhound.core.types.common', 
   'providers.embedding.openai_provider',
   'providers.parser.tree_sitter_provider',
   ```

2. **Add correct import paths:**
   ```python
   # Add these instead:
   'core.types',
   'core.types.common',
   'providers.embeddings.openai_provider',  # Note: embeddings not embedding
   'providers.parsing',  # Use parsing directory structure
   ```

3. **Verify all current module paths** by checking actual project structure

## Files Affected

- `chunkhound-optimized.spec` (lines ~29-33, ~36-43)

## Investigation Needed

1. **Audit all hidden imports** in the spec file against actual project structure
2. **Test locally on Windows** to verify PyInstaller works with corrected imports  
3. **Compare with working builds** (macOS ARM64 succeeded, so imports must work there)

## Testing Strategy

1. Fix the spec file hidden imports
2. Test locally with PyInstaller on Windows if available
3. Run GitHub Actions workflow again
4. Verify Windows binary creation and basic functionality

## Related Issues

- macOS ARM64 build succeeded with same spec file (platform differences?)
- Windows UV installation and dependency resolution worked correctly
- Only PyInstaller phase failed, indicating environment is properly set up

## Priority Justification

High priority because:
- Windows is a major target platform
- Core functionality is blocked  
- Likely affects all Windows deployment scenarios
- Simple configuration fix once import paths are corrected