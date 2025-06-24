# [TASK] Code Quality Cleanup

**Date**: 2025-06-23
**Priority**: High
**Status**: Open

## Scope
Fix all type errors and linting issues across the codebase to achieve production-ready code quality.

## Issues Identified (Updated 2025-06-24)
- 265 mypy type errors across 24 files
- 5,573 ruff linting errors (3,820 auto-fixable)
- 4 test failures, 2 test errors related to:
  - BGE batch sizing assertion logic
  - Database incremental status inconsistency
  - File modification test directory creation

## Requirements
1. **Type Safety**: Fix all mypy errors
   - Add missing type annotations 
   - Resolve assignment/return type mismatches
   - Install missing type stubs (e.g., types-psutil)

2. **Code Style**: Fix all ruff linting errors
   - Remove trailing whitespace
   - Fix import organization
   - Remove unused imports
   - Update deprecated typing imports

3. **Test Stability**: Fix failing tests
   - `test_adaptive_batch_sizing_increase` assertion logic
   - Database incremental processing status consistency
   - File modification test directory setup and cleanup

## Expectations
- Zero mypy type errors
- Zero ruff linting errors
- All tests passing
- No functional changes to core logic
- Maintain existing API contracts

## Success Criteria
- `uv run mypy chunkhound/` passes clean
- `uv run ruff check .` passes clean  
- `uv run pytest tests/` passes with no failures

## Files Affected
Primary focus on:
- `chunkhound/` directory (core module)
- `providers/` parsing modules
- `tests/` test suite
- CLI modules in `chunkhound/api/`

## Notes
- Use `ruff check . --fix` for auto-fixable issues first
- Address type errors systematically by module
- Preserve all existing functionality

## Current Test Results (2025-06-24)
- **Tests**: 370 passed, 8 skipped, 4 failed, 2 errors
- **Core functionality**: Working as evidenced by passing tests
- **Issues**: Minor edge cases in incremental operations and file handling