# [TASK] Code Quality Cleanup

**Date**: 2025-06-23
**Priority**: High
**Status**: Open

## Scope
Fix all type errors and linting issues across the codebase to achieve production-ready code quality.

## Issues Identified
- 243 mypy type errors across 23 files
- 4,915 ruff linting errors (3,321 auto-fixable)
- 4 test failures related to assertions and file handling

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
   - BGE batch sizing assertion logic
   - Database status return consistency  
   - File modification test setup

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