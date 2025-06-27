# 2025-06-27 - [FEATURE] Unified Configuration System
**Priority**: High  
**Status**: Complete

Fragmented configuration across multiple systems with inconsistent env vars and scattered CLI parsers. Missing project-level config and exclude patterns not properly enforced during file watching.

# History

## 2025-06-27T12:07:00+03:00
**Implemented unified configuration system**
- Created single `ChunkHoundConfig` Pydantic model for all components
- Added hierarchical config loading: CLI > env vars > project file > user file > defaults
- Removed entire `chunkhound config` command system
- Added `.chunkhound.json` project config support
- Standardized all env vars to `CHUNKHOUND_` prefix with `__` delimiter
- Maintained backward compatibility for existing workflows

## 2025-06-27T12:56:00+03:00
**Fixed critical exclude patterns bug**
- **Problem**: Exclude patterns respected during initial indexing but forgotten during file watching
- **Root Cause**: CLI watch mode and MCP server file watchers bypassed exclude pattern validation
- **Fix**: Added exclude pattern checking in both `process_cli_file_change()` and `process_file_change()` callbacks
- **Impact**: Files like `node_modules/*` no longer indexed during watch mode
- **Verification**: Pattern matching logic tested and confirmed working

**Files modified**:
- `chunkhound/api/cli/commands/run.py`: Added exclude patterns to watch mode callback
- `chunkhound/mcp_server.py`: Added exclude patterns to MCP file watcher
- `services/indexing_coordinator.py`: Removed duplicate patterns, use unified config
- `chunkhound/periodic_indexer.py`: Updated to use unified config patterns
- `chunkhound/core/config/unified_config.py`: Added `.mypy_cache` to defaults, added helper method

**Key exclude patterns now enforced everywhere**:
- `**/node_modules/**`, `**/.git/**`, `**/__pycache__/**`, `**/venv/**`, `**/.venv/**`, `**/.mypy_cache/**`