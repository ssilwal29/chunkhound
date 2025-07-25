#!/usr/bin/env python3
"""
ChunkHound MCP Server - Model Context Protocol implementation
Provides code search capabilities via stdin/stdout JSON-RPC protocol
"""

import asyncio
import json
import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions

# Disable all logging for MCP server to prevent interference with JSON-RPC
logging.disable(logging.CRITICAL)
for logger_name in ['', 'mcp', 'server', 'fastmcp']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL + 1)



# Disable loguru logger used by database module
try:
    from loguru import logger as loguru_logger
    loguru_logger.remove()
    loguru_logger.add(lambda _: None, level="CRITICAL")
except ImportError:
    pass

try:
    from .core.config import EmbeddingProviderFactory
    from .core.config.unified_config import ChunkHoundConfig
    from .database import Database
    from .embeddings import EmbeddingManager
    from .file_watcher import FileWatcherManager
    from .periodic_indexer import PeriodicIndexManager
    from .registry import configure_registry, get_registry
    from .signal_coordinator import SignalCoordinator
    from .task_coordinator import TaskCoordinator, TaskPriority
except ImportError:
    # Handle running as standalone script or PyInstaller binary
    from chunkhound.core.config import EmbeddingProviderFactory
    from chunkhound.core.config.unified_config import ChunkHoundConfig
    from chunkhound.database import Database
    from chunkhound.embeddings import EmbeddingManager
    from chunkhound.file_watcher import FileWatcherManager
    from chunkhound.periodic_indexer import PeriodicIndexManager
    from chunkhound.signal_coordinator import SignalCoordinator
    from chunkhound.task_coordinator import TaskCoordinator, TaskPriority
    from registry import configure_registry

# Global database, embedding manager, and file watcher instances
# Global state management
_database: Database | None = None
_embedding_manager: EmbeddingManager | None = None
_file_watcher: FileWatcherManager | None = None
_signal_coordinator: SignalCoordinator | None = None
_task_coordinator: TaskCoordinator | None = None
_periodic_indexer: PeriodicIndexManager | None = None

# Initialize MCP server with explicit stdio
server = Server("ChunkHound Code Search")


def _build_mcp_registry_config(config: ChunkHoundConfig, db_path: Path) -> dict[str, Any]:
    """Build registry configuration for MCP server mode.

    Args:
        config: Unified configuration
        db_path: Database path

    Returns:
        Registry configuration dictionary
    """
    registry_config = {
        'database': {
            'path': str(db_path),
            'type': 'duckdb',
            'batch_size': config.indexing.db_batch_size,
        },
        'embedding': {
            'batch_size': config.embedding.batch_size,
            'max_concurrent_batches': config.embedding.max_concurrent_batches,
            'provider': config.embedding.provider,
            'model': config.get_embedding_model(),
        }
    }

    # Add API key if available
    if config.embedding.api_key:
        registry_config['embedding']['api_key'] = config.embedding.api_key.get_secret_value()

    # Add base URL if available
    if config.embedding.base_url:
        registry_config['embedding']['base_url'] = config.embedding.base_url

    return registry_config


def setup_signal_coordination(db_path: Path, database: Database):
    """Setup signal coordination for process coordination."""
    global _signal_coordinator

    try:
        _signal_coordinator = SignalCoordinator(db_path, database)
        _signal_coordinator.setup_mcp_signal_handling()
        # Signal coordination initialized (logging disabled for MCP server)
    except Exception:
        # Failed to setup signal coordination (logging disabled for MCP server)
        raise


def log_environment_diagnostics():
    """Log environment diagnostics for API key debugging - only in non-MCP mode."""
    import os
    # Skip diagnostics in MCP mode to maintain clean JSON-RPC communication
    if os.environ.get("CHUNKHOUND_MCP_MODE"):
        return
    print("=== MCP SERVER ENVIRONMENT DIAGNOSTICS ===", file=sys.stderr)
    print(f"OPENAI_API_KEY present: {'OPENAI_API_KEY' in os.environ}", file=sys.stderr)
    if 'OPENAI_API_KEY' in os.environ:
        key = os.environ['OPENAI_API_KEY']
        print(f"OPENAI_API_KEY length: {len(key)}", file=sys.stderr)
        print(f"OPENAI_API_KEY prefix: {key[:7]}...", file=sys.stderr)
    else:
        print("OPENAI_API_KEY not found in process environment", file=sys.stderr)
    print("===============================================", file=sys.stderr)


@asynccontextmanager
async def server_lifespan(server: Server) -> AsyncIterator[dict]:
    """Manage server startup and shutdown lifecycle."""
    global _database, _embedding_manager, _file_watcher, _signal_coordinator, _task_coordinator, _periodic_indexer

    # Set MCP mode to suppress stderr output that interferes with JSON-RPC
    os.environ["CHUNKHOUND_MCP_MODE"] = "1"

    if "CHUNKHOUND_DEBUG" in os.environ:
        print("Server lifespan: Starting initialization", file=sys.stderr)

    try:
        # Log environment diagnostics for API key debugging
        log_environment_diagnostics()

        # Initialize database path
        db_path = Path(os.environ.get("CHUNKHOUND_DB_PATH", "chunkhound.db"))
        db_path.parent.mkdir(parents=True, exist_ok=True)

        if "CHUNKHOUND_DEBUG" in os.environ:
            print(f"Server lifespan: Using database at {db_path}", file=sys.stderr)

        # Initialize embedding configuration BEFORE database creation
        _embedding_manager = EmbeddingManager()
        if "CHUNKHOUND_DEBUG" in os.environ:
            print("Server lifespan: Embedding manager initialized", file=sys.stderr)

        # Setup embedding provider and registry configuration
        unified_config = None
        try:
            # Load unified configuration with environment variable support
            unified_config = ChunkHoundConfig.load_hierarchical()

            # Validate configuration for MCP
            missing_config = unified_config.get_missing_config()
            if missing_config and "CHUNKHOUND_DEBUG" in os.environ:
                print(f"Server lifespan: Missing config (will use defaults): {missing_config}", file=sys.stderr)

            # Create provider using unified factory
            provider = EmbeddingProviderFactory.create_provider(unified_config.embedding)
            _embedding_manager.register_provider(provider, set_default=True)

            if "CHUNKHOUND_DEBUG" in os.environ:
                print(f"Server lifespan: Embedding provider registered successfully: {unified_config.embedding.provider} with model {unified_config.get_embedding_model()}", file=sys.stderr)

            # CRITICAL FIX: Configure registry BEFORE database creation
            registry_config = _build_mcp_registry_config(unified_config, db_path)
            configure_registry(registry_config)

            if "CHUNKHOUND_DEBUG" in os.environ:
                print("Server lifespan: Registry configured with embedding provider", file=sys.stderr)
                print(f"Server lifespan: Registry config: {registry_config}", file=sys.stderr)

        except ValueError as e:
            # API key or configuration issue - only log in non-MCP mode
            if "CHUNKHOUND_DEBUG" in os.environ:
                print(f"Server lifespan: Embedding provider setup failed (expected): {e}", file=sys.stderr)
            if "CHUNKHOUND_DEBUG" in os.environ and not os.environ.get("CHUNKHOUND_MCP_MODE"):
                print(f"Embedding provider setup failed: {e}", file=sys.stderr)
                print("Configuration help:", file=sys.stderr)
                print("- Set CHUNKHOUND_EMBEDDING_PROVIDER (openai|openai-compatible|tei|bge-in-icl)", file=sys.stderr)
                print("- Set CHUNKHOUND_EMBEDDING_API_KEY or legacy OPENAI_API_KEY", file=sys.stderr)
                print("- Set CHUNKHOUND_EMBEDDING_MODEL (optional)", file=sys.stderr)
                print("- For OpenAI-compatible: Set CHUNKHOUND_EMBEDDING_BASE_URL", file=sys.stderr)
        except Exception as e:
            # Unexpected error - log for debugging but continue
            if "CHUNKHOUND_DEBUG" in os.environ:
                print(f"Server lifespan: Unexpected error setting up embedding provider: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)

        # Create database AFTER registry configuration
        _database = Database(db_path)
        try:
            # Initialize database with connection only - no background refresh thread
            _database.connect()
            if "CHUNKHOUND_DEBUG" in os.environ:
                print("Server lifespan: Database connected successfully", file=sys.stderr)
                # Verify IndexingCoordinator has embedding provider
                try:
                    try:
                        from .registry import get_registry
                    except ImportError:
                        from registry import get_registry
                    indexing_coordinator = get_registry().create_indexing_coordinator()
                    has_embedding_provider = indexing_coordinator._embedding_provider is not None
                    print(f"Server lifespan: IndexingCoordinator embedding provider available: {has_embedding_provider}", file=sys.stderr)
                except Exception as debug_error:
                    print(f"Server lifespan: Debug check failed: {debug_error}", file=sys.stderr)
        except Exception as db_error:
            if "CHUNKHOUND_DEBUG" in os.environ:
                print(f"Server lifespan: Database connection error: {db_error}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
            raise

        # Setup signal coordination for process coordination
        setup_signal_coordination(db_path, _database)
        if "CHUNKHOUND_DEBUG" in os.environ:
            print("Server lifespan: Signal coordination setup complete", file=sys.stderr)

        # Initialize task coordinator for priority-based operation processing
        _task_coordinator = TaskCoordinator(max_queue_size=1000)
        await _task_coordinator.start()
        if "CHUNKHOUND_DEBUG" in os.environ:
            print("Server lifespan: Task coordinator initialized", file=sys.stderr)

        # Initialize filesystem watcher with offline catch-up
        _file_watcher = FileWatcherManager()
        try:
            if "CHUNKHOUND_DEBUG" in os.environ:
                print("Server lifespan: Initializing file watcher...", file=sys.stderr)

            # Check if watchdog is available before initializing
            try:
                from .file_watcher import WATCHDOG_AVAILABLE
            except ImportError:
                from chunkhound.file_watcher import WATCHDOG_AVAILABLE

            if not WATCHDOG_AVAILABLE:
                # FAIL FAST: watchdog is required for real-time file watching
                error_msg = (
                    "FATAL: watchdog library not available - real-time file watching disabled.\n"
                    "This causes silent failures where file modifications are missed.\n"
                    "Install watchdog: pip install watchdog>=4.0.0"
                )
                print(f"❌ MCP SERVER ERROR: {error_msg}", file=sys.stderr)
                raise ImportError(error_msg)

            watcher_success = await _file_watcher.initialize(process_file_change)
            if not watcher_success:
                # FAIL FAST: file watcher initialization failed
                error_msg = (
                    "FATAL: File watcher initialization failed - real-time monitoring disabled.\n"
                    "This causes silent failures where file modifications are missed.\n"
                    "Check watch paths configuration and filesystem permissions."
                )
                print(f"❌ MCP SERVER ERROR: {error_msg}", file=sys.stderr)
                raise RuntimeError(error_msg)

            if "CHUNKHOUND_DEBUG" in os.environ:
                print("Server lifespan: File watcher initialized successfully", file=sys.stderr)
        except Exception as fw_error:
            # FAIL FAST: Any file watcher error should crash the server
            error_msg = f"FATAL: File watcher initialization failed: {fw_error}"
            print(f"❌ MCP SERVER ERROR: {error_msg}", file=sys.stderr)
            if "CHUNKHOUND_DEBUG" in os.environ:
                import traceback
                traceback.print_exc(file=sys.stderr)
            raise RuntimeError(error_msg)

        # Initialize periodic indexer for background scanning
        try:
            if "CHUNKHOUND_DEBUG" in os.environ:
                print("Server lifespan: Initializing periodic indexer...", file=sys.stderr)
            
            # Get base directory from environment or use current working directory
            base_directory = Path(os.getcwd())
            
            # Get IndexingCoordinator from registry
            try:
                from .registry import get_registry
            except ImportError:
                from registry import get_registry
            indexing_coordinator = get_registry().create_indexing_coordinator()
            
            # Create periodic indexer with environment configuration
            _periodic_indexer = PeriodicIndexManager.from_environment(
                indexing_coordinator=indexing_coordinator,
                task_coordinator=_task_coordinator,
                base_directory=base_directory
            )
            
            # Start periodic indexer (immediate startup scan + periodic scans)
            await _periodic_indexer.start()
            
            if "CHUNKHOUND_DEBUG" in os.environ:
                print("Server lifespan: Periodic indexer initialized successfully", file=sys.stderr)
        except Exception as pi_error:
            # Non-fatal error - log but continue without periodic indexing
            if "CHUNKHOUND_DEBUG" in os.environ:
                print(f"Server lifespan: Periodic indexer initialization failed (non-fatal): {pi_error}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
            _periodic_indexer = None

        if "CHUNKHOUND_DEBUG" in os.environ:
            print("Server lifespan: All components initialized successfully", file=sys.stderr)

        # Return server context to the caller
        yield {"db": _database, "embeddings": _embedding_manager, "watcher": _file_watcher, "task_coordinator": _task_coordinator, "periodic_indexer": _periodic_indexer}

    except Exception as e:
        if "CHUNKHOUND_DEBUG" in os.environ:
            print(f"Server lifespan: Initialization failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
        raise Exception(f"Failed to initialize database and embeddings: {e}")
    finally:
        if "CHUNKHOUND_DEBUG" in os.environ:
            print("Server lifespan: Entering cleanup phase", file=sys.stderr)

        # Cleanup periodic indexer
        if _periodic_indexer:
            try:
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("Server lifespan: Stopping periodic indexer...", file=sys.stderr)
                await _periodic_indexer.stop()
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("Server lifespan: Periodic indexer stopped", file=sys.stderr)
            except Exception as pi_cleanup_error:
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print(f"Server lifespan: Error stopping periodic indexer: {pi_cleanup_error}", file=sys.stderr)

        # Cleanup task coordinator
        if _task_coordinator:
            try:
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("Server lifespan: Stopping task coordinator...", file=sys.stderr)
                await _task_coordinator.stop()
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("Server lifespan: Task coordinator stopped", file=sys.stderr)
            except Exception as tc_cleanup_error:
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print(f"Server lifespan: Error stopping task coordinator: {tc_cleanup_error}", file=sys.stderr)

        # Cleanup coordination files
        if _signal_coordinator:
            try:
                _signal_coordinator.cleanup_coordination_files()
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("Server lifespan: Signal coordination files cleaned up", file=sys.stderr)
            except Exception as coord_error:
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print(f"Server lifespan: Error cleaning up coordination files: {coord_error}", file=sys.stderr)

        # Cleanup filesystem watcher
        if _file_watcher:
            try:
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("Server lifespan: Cleaning up file watcher...", file=sys.stderr)
                await _file_watcher.cleanup()
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("Server lifespan: File watcher cleaned up successfully", file=sys.stderr)
            except Exception as fw_cleanup_error:
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print(f"Server lifespan: Error cleaning up file watcher: {fw_cleanup_error}", file=sys.stderr)

        # Cleanup database
        if _database:
            try:
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("Server lifespan: Closing database connection...", file=sys.stderr)
                
                # Ensure all pending operations complete
                if _task_coordinator:
                    try:
                        await asyncio.wait_for(_task_coordinator.wait_for_completion(), timeout=10.0)
                    except asyncio.TimeoutError:
                        if "CHUNKHOUND_DEBUG" in os.environ:
                            print("Server lifespan: Task coordinator cleanup timeout", file=sys.stderr)
                
                # Force final checkpoint before closing to minimize WAL size
                try:
                    _database._maybe_checkpoint(force=True)
                    if "CHUNKHOUND_DEBUG" in os.environ:
                        print("Server lifespan: Final checkpoint completed", file=sys.stderr)
                except Exception as checkpoint_error:
                    if "CHUNKHOUND_DEBUG" in os.environ:
                        print(f"Server lifespan: Final checkpoint failed: {checkpoint_error}", file=sys.stderr)
                
                # Close database (skip built-in checkpoint as we just did it)
                _database.disconnect(skip_checkpoint=True)
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("Server lifespan: Database connection closed successfully", file=sys.stderr)
            except Exception as db_close_error:
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print(f"Server lifespan: Error closing database: {db_close_error}", file=sys.stderr)

        if "CHUNKHOUND_DEBUG" in os.environ:
            print("Server lifespan: Cleanup complete", file=sys.stderr)


async def _wait_for_file_completion(file_path: Path, max_retries: int = 3) -> bool:
    """Wait for file to be fully written (not locked by editor)"""
    for _ in range(max_retries):
        try:
            with open(file_path, 'rb') as f:
                f.read(1)  # Test read access
            return True
        except (OSError, PermissionError):
            await asyncio.sleep(0.1)  # Brief wait
    return False


async def process_file_change(file_path: Path, event_type: str):
    """
    Process a file change event by updating the database.

    This function is called by the filesystem watcher when files change.
    Uses the task coordinator to ensure file processing doesn't block search operations.
    """
    global _database, _embedding_manager, _task_coordinator

    if not _database:
        return

    async def _execute_file_processing():
        """Execute the actual file processing logic."""
        try:
            if event_type == 'deleted':
                # Remove file from database with cleanup tracking
                _database.delete_file_completely(str(file_path))
            else:
                # Process file (created, modified, moved)
                if file_path.exists() and file_path.is_file():
                    # Check if file should be excluded before processing
                    try:
                        from .core.config.unified_config import ChunkHoundConfig
                    except ImportError:
                        from chunkhound.core.config.unified_config import ChunkHoundConfig
                    
                    exclude_patterns = ChunkHoundConfig.get_default_exclude_patterns()
                    
                    from fnmatch import fnmatch
                    should_exclude = False
                    
                    # Get relative path from current working directory for pattern matching
                    base_dir = Path.cwd()
                    try:
                        rel_path = file_path.relative_to(base_dir)
                    except ValueError:
                        # File is not under base directory, use absolute path
                        rel_path = file_path
                    
                    for exclude_pattern in exclude_patterns:
                        # Check both relative and absolute paths
                        if (fnmatch(str(rel_path), exclude_pattern) or 
                            fnmatch(str(file_path), exclude_pattern)):
                            should_exclude = True
                            break
                    
                    if should_exclude:
                        if "CHUNKHOUND_DEBUG" in os.environ:
                            print(f"MCP: Skipped excluded file: {file_path}", file=sys.stderr)
                        return

                    # Phase 4: Verify file is fully written before processing
                    if not await _wait_for_file_completion(file_path):
                        return  # Skip if file not ready

                    # Use incremental processing for 10-100x performance improvement
                    await _database.process_file_incremental(file_path=file_path)

                    # Transaction already committed by IndexingCoordinator with backup/rollback safety
        except Exception as e:
            # Log the exception instead of silently handling it
            if "CHUNKHOUND_DEBUG" in os.environ:
                print(f"Exception during {event_type} processing: {e}", file=sys.stderr)
                import traceback
                print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)

    # Queue file processing as low-priority task to avoid blocking searches
    if _task_coordinator:
        try:
            # Use nowait to avoid blocking the file watcher
            future = await _task_coordinator.queue_task_nowait(
                TaskPriority.LOW,
                _execute_file_processing
            )
            # Don't await the future - let file processing happen in background
        except Exception as e:
            if "CHUNKHOUND_DEBUG" in os.environ:
                print(f"Failed to queue file processing task: {e}", file=sys.stderr)
            # Fallback to direct processing if queue is full or coordinator is down
            await _execute_file_processing()
    else:
        # Fallback to direct processing if no task coordinator
        await _execute_file_processing()


def estimate_tokens(text: str) -> int:
    """Estimate token count using simple heuristic (3 chars ≈ 1 token for safety)."""
    return len(text) // 3


def truncate_code(code: str, max_chars: int = 1000) -> tuple[str, bool]:
    """Truncate code content with smart line breaking."""
    if len(code) <= max_chars:
        return code, False

    # Try to break at line boundaries
    lines = code.split('\n')
    truncated_lines = []
    char_count = 0

    for line in lines:
        if char_count + len(line) + 1 > max_chars:
            break
        truncated_lines.append(line)
        char_count += len(line) + 1

    return '\n'.join(truncated_lines) + '\n...', True


def limit_response_size(response_data: dict[str, Any], max_tokens: int) -> dict[str, Any]:
    """Limit response size to fit within token limits by reducing results."""
    if not response_data.get("results"):
        return response_data

    # Start with full response and iteratively reduce until under limit
    limited_results = response_data["results"][:]

    while limited_results:
        # Create test response with current results
        test_response = {
            "results": limited_results,
            "pagination": response_data["pagination"]
        }

        # Estimate token count
        response_text = json.dumps(test_response, default=str)
        token_count = estimate_tokens(response_text)

        if token_count <= max_tokens:
            # Update pagination to reflect actual returned results
            actual_count = len(limited_results)
            updated_pagination = response_data["pagination"].copy()
            updated_pagination["page_size"] = actual_count
            updated_pagination["has_more"] = (
                updated_pagination.get("has_more", False) or
                actual_count < len(response_data["results"])
            )
            if actual_count < len(response_data["results"]):
                updated_pagination["next_offset"] = updated_pagination.get("offset", 0) + actual_count

            return {
                "results": limited_results,
                "pagination": updated_pagination
            }

        # Remove results from the end to reduce size
        # Remove in chunks for efficiency
        reduction_size = max(1, len(limited_results) // 4)
        limited_results = limited_results[:-reduction_size]

    # If even empty results exceed token limit, return minimal response
    return {
        "results": [],
        "pagination": {
            "offset": response_data["pagination"].get("offset", 0),
            "page_size": 0,
            "has_more": len(response_data["results"]) > 0,
            "total": response_data["pagination"].get("total", 0)
        }
    }


def convert_to_ndjson(results: list[dict[str, Any]]) -> str:
    """Convert search results to NDJSON format."""
    lines = []
    for result in results:
        lines.append(json.dumps(result, ensure_ascii=False))
    return "\n".join(lines)


@server.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls"""
    if not _database:
        if _signal_coordinator and _signal_coordinator.is_coordination_active():
            raise Exception("Database temporarily unavailable during coordination")
        else:
            raise Exception("Database not initialized")

    if name == "search_regex":
        pattern = arguments.get("pattern", "")
        page_size = max(1, min(arguments.get("page_size", 10), 100))
        offset = max(0, arguments.get("offset", 0))
        max_tokens = max(1000, min(arguments.get("max_response_tokens", 20000), 25000))
        path_filter = arguments.get("path")

        async def _execute_regex_search():
            # Check connection instead of forcing reconnection (fixes race condition)
            if _database and not _database.is_connected():
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("Database not connected, reconnecting before regex search", file=sys.stderr)
                _database.reconnect()

            results, pagination = _database.search_regex(pattern=pattern, page_size=page_size, offset=offset, path_filter=path_filter)

            # Format response with pagination metadata
            response_data = {
                "results": results,
                "pagination": pagination
            }

            # Apply response size limiting
            limited_response = limit_response_size(response_data, max_tokens)
            response_text = json.dumps(limited_response, default=str)

            # Final safety check - ensure we never exceed MCP limit
            if estimate_tokens(response_text) > 25000:
                # Emergency fallback - return minimal response
                emergency_response = {
                    "results": [],
                    "pagination": {
                        "offset": offset,
                        "page_size": 0,
                        "has_more": True,
                        "total": limited_response["pagination"].get("total", 0)
                    }
                }
                response_text = json.dumps(emergency_response, default=str)

            return [types.TextContent(type="text", text=response_text)]

        try:
            if _task_coordinator:
                return await _task_coordinator.queue_task(TaskPriority.HIGH, _execute_regex_search)
            else:
                return await _execute_regex_search()
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

    elif name == "search_semantic":
        query = arguments.get("query", "")
        page_size = max(1, min(arguments.get("page_size", 10), 100))
        offset = max(0, arguments.get("offset", 0))
        max_tokens = max(1000, min(arguments.get("max_response_tokens", 20000), 25000))
        provider = arguments.get("provider", "openai")
        model = arguments.get("model", "text-embedding-3-small")
        threshold = arguments.get("threshold")
        path_filter = arguments.get("path")

        if not _embedding_manager or not _embedding_manager.list_providers():
            raise Exception("No embedding providers available. Set OPENAI_API_KEY to enable semantic search.")

        async def _execute_semantic_search():
            # Check connection instead of forcing reconnection (fixes race condition)
            if _database and not _database.is_connected():
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("Database not connected, reconnecting before semantic search", file=sys.stderr)
                _database.reconnect()

            # Implement timeout coordination for MCP-OpenAI API latency mismatch
            # MCP client timeout is typically 5-15s, but OpenAI API can take up to 30s
            try:
                # Use asyncio.wait_for with MCP-safe timeout (12 seconds)
                # This is shorter than OpenAI's 30s timeout but allows most requests to complete
                result = await asyncio.wait_for(
                    _embedding_manager.embed_texts([query], provider),
                    timeout=12.0
                )
                query_vector = result.embeddings[0]

                results, pagination = _database.search_semantic(
                    query_vector=query_vector,
                    provider=provider,
                    model=model,
                    page_size=page_size,
                    offset=offset,
                    threshold=threshold,
                    path_filter=path_filter
                )

                # Format response with pagination metadata
                response_data = {
                    "results": results,
                    "pagination": pagination
                }

                # Apply response size limiting
                limited_response = limit_response_size(response_data, max_tokens)
                response_text = json.dumps(limited_response, default=str)

                # Final safety check - ensure we never exceed MCP limit
                if estimate_tokens(response_text) > 25000:
                    # Emergency fallback - return minimal response
                    emergency_response = {
                        "results": [],
                        "pagination": {
                            "offset": offset,
                            "page_size": 0,
                            "has_more": True,
                            "total": limited_response["pagination"].get("total", 0)
                        }
                    }
                    response_text = json.dumps(emergency_response, default=str)

                return [types.TextContent(type="text", text=response_text)]

            except asyncio.TimeoutError:
                # Handle MCP timeout gracefully with informative error
                raise Exception("Semantic search timed out. This can happen when OpenAI API is experiencing high latency. Please try again.")

        try:
            if _task_coordinator:
                return await _task_coordinator.queue_task(TaskPriority.HIGH, _execute_semantic_search)
            else:
                return await _execute_semantic_search()
        except Exception as e:
            raise Exception(f"Semantic search failed: {str(e)}")

    elif name == "get_stats":
        async def _execute_get_stats():
            stats = _database.get_stats()
            if _task_coordinator:
                # Add task coordinator stats
                stats['task_coordinator'] = _task_coordinator.get_stats()
            return [types.TextContent(type="text", text=json.dumps(stats, ensure_ascii=False))]

        try:
            if _task_coordinator:
                return await _task_coordinator.queue_task(TaskPriority.MEDIUM, _execute_get_stats)
            else:
                return await _execute_get_stats()
        except Exception as e:
            raise Exception(f"Failed to get stats: {str(e)}")

    elif name == "health_check":
        async def _execute_health_check():
            health_status = {
                "status": "healthy",
                "version": "1.1.0",
                "database_connected": _database is not None,
                "embedding_providers": _embedding_manager.list_providers() if _embedding_manager else [],
                "task_coordinator_running": _task_coordinator.get_stats()['is_running'] if _task_coordinator else False
            }
            return [types.TextContent(type="text", text=json.dumps(health_status, ensure_ascii=False))]

        try:
            if _task_coordinator:
                return await _task_coordinator.queue_task(TaskPriority.MEDIUM, _execute_health_check)
            else:
                return await _execute_health_check()
        except Exception as e:
            raise Exception(f"Failed to perform health check: {str(e)}")

    else:
        raise ValueError(f"Tool not found: {name}")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="search_regex",
            description="Search code chunks using regex patterns with pagination support.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regular expression pattern to search for"},
                    "page_size": {"type": "integer", "description": "Number of results per page (1-100)", "default": 10},
                    "offset": {"type": "integer", "description": "Starting position for pagination", "default": 0},
                    "max_response_tokens": {"type": "integer", "description": "Maximum response size in tokens (1000-25000)", "default": 20000},
                    "path": {"type": "string", "description": "Optional relative path to limit search scope (e.g., 'src/', 'tests/')"}
                },
                "required": ["pattern"]
            }
        ),
        types.Tool(
            name="search_semantic",
            description="Search code using semantic similarity with pagination support.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "page_size": {"type": "integer", "description": "Number of results per page (1-100)", "default": 10},
                    "offset": {"type": "integer", "description": "Starting position for pagination", "default": 0},
                    "max_response_tokens": {"type": "integer", "description": "Maximum response size in tokens (1000-25000)", "default": 20000},
                    "provider": {"type": "string", "description": "Embedding provider to use", "default": "openai"},
                    "model": {"type": "string", "description": "Embedding model to use", "default": "text-embedding-3-small"},
                    "threshold": {"type": "number", "description": "Distance threshold for filtering results (optional)"},
                    "path": {"type": "string", "description": "Optional relative path to limit search scope (e.g., 'src/', 'tests/')"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_stats",
            description="Get database statistics including file, chunk, and embedding counts",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="health_check",
            description="Check server health status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


def send_error_response(message_id: Any, code: int, message: str, data: dict | None = None):
    """Send a JSON-RPC error response to stdout."""
    error_response = {
        "jsonrpc": "2.0",
        "id": message_id,
        "error": {
            "code": code,
            "message": message,
            "data": data
        }
    }
    print(json.dumps(error_response, ensure_ascii=False), flush=True)


def validate_mcp_initialize_message(message_text: str) -> tuple[bool, dict | None, str | None]:
    """
    Validate MCP initialize message for common protocol issues.
    Returns (is_valid, parsed_message, error_description)
    """
    try:
        message = json.loads(message_text.strip())
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {str(e)}"

    if not isinstance(message, dict):
        return False, None, "Message must be a JSON object"

    # Check required JSON-RPC fields
    if message.get("jsonrpc") != "2.0":
        return False, message, f"Invalid jsonrpc version: '{message.get('jsonrpc')}' (must be '2.0')"

    if message.get("method") != "initialize":
        return True, message, None  # Only validate initialize messages

    # Validate initialize method specifically
    params = message.get("params", {})
    if not isinstance(params, dict):
        return False, message, "Initialize method 'params' must be an object"

    missing_fields = []
    if "protocolVersion" not in params:
        missing_fields.append("protocolVersion")
    if "capabilities" not in params:
        missing_fields.append("capabilities")
    if "clientInfo" not in params:
        missing_fields.append("clientInfo")

    if missing_fields:
        return False, message, f"Initialize method missing required fields: {', '.join(missing_fields)}"

    return True, message, None


def provide_mcp_example():
    """Provide a helpful example of correct MCP initialize message."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "your-mcp-client",
                "version": "1.0.0"
            }
        }
    }


async def handle_mcp_with_validation():
    """Handle MCP with improved error messages for protocol issues."""
    try:
        # Use the official MCP Python SDK stdio server pattern
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            # Initialize with lifespan context
            try:
                # Debug output to help diagnose initialization issues
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("MCP server: Starting server initialization", file=sys.stderr)

                async with server_lifespan(server) as server_context:
                    # Initialize the server
                    if "CHUNKHOUND_DEBUG" in os.environ:
                        print("MCP server: Server lifespan established, running server...", file=sys.stderr)

                    try:
                        await server.run(
                            read_stream,
                            write_stream,
                            InitializationOptions(
                                server_name="ChunkHound Code Search",
                                server_version="1.1.0",
                                capabilities=server.get_capabilities(
                                    notification_options=NotificationOptions(),
                                    experimental_capabilities={},
                                ),
                            ),
                        )

                        if "CHUNKHOUND_DEBUG" in os.environ:
                            print("MCP server: Server.run() completed, entering keepalive mode", file=sys.stderr)

                        # Keep the process alive until client disconnects
                        # The MCP SDK handles the connection lifecycle, so we just need to wait
                        # for the server to be terminated by the client or signal
                        try:
                            # Wait indefinitely - the MCP SDK will handle cleanup when client disconnects
                            await asyncio.Event().wait()
                        except (asyncio.CancelledError, KeyboardInterrupt):
                            if "CHUNKHOUND_DEBUG" in os.environ:
                                print("MCP server: Received shutdown signal", file=sys.stderr)
                        except Exception as e:
                            if "CHUNKHOUND_DEBUG" in os.environ:
                                print(f"MCP server unexpected error: {e}", file=sys.stderr)
                                import traceback
                                traceback.print_exc(file=sys.stderr)
                    except Exception as server_run_error:
                        if "CHUNKHOUND_DEBUG" in os.environ:
                            print(f"MCP server.run() error: {server_run_error}", file=sys.stderr)
                            import traceback
                            traceback.print_exc(file=sys.stderr)
                        raise
            except Exception as lifespan_error:
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print(f"MCP server lifespan error: {lifespan_error}", file=sys.stderr)
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                raise
    except Exception as e:
        # Analyze error for common protocol issues with recursive search
        error_details = str(e)
        if "CHUNKHOUND_DEBUG" in os.environ:
            print(f"MCP server top-level error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)

        def find_validation_error(error, depth=0):
            """Recursively search for ValidationError in exception chain."""
            if depth > 10:  # Prevent infinite recursion
                return False, ""

            error_str = str(error).lower()

            # Check for validation error indicators
            validation_keywords = [
                'protocolversion', 'field required', 'validation error',
                'validationerror', 'literal_error', 'input should be',
                'missing', 'pydantic'
            ]

            if any(keyword in error_str for keyword in validation_keywords):
                return True, str(error)

            # Check exception chain
            if hasattr(error, '__cause__') and error.__cause__:
                found, details = find_validation_error(error.__cause__, depth + 1)
                if found:
                    return found, details

            if hasattr(error, '__context__') and error.__context__:
                found, details = find_validation_error(error.__context__, depth + 1)
                if found:
                    return found, details

            # Check exception groups (anyio/asyncio task groups)
            if hasattr(error, 'exceptions') and error.exceptions:
                for exc in error.exceptions:
                    found, details = find_validation_error(exc, depth + 1)
                    if found:
                        return found, details

            return False, ""

        is_validation_error, validation_details = find_validation_error(e)
        if validation_details:
            error_details = validation_details

        if is_validation_error:
            # Send helpful protocol validation error
            send_error_response(
                1,  # Assume initialize request
                -32602,
                "Invalid MCP protocol message",
                {
                    "details": "The MCP initialization message is missing required fields or has invalid format.",
                    "common_issue": "Missing 'protocolVersion' field in initialize request parameters",
                    "required_fields": ["protocolVersion", "capabilities", "clientInfo"],
                    "correct_example": provide_mcp_example(),
                    "validation_error": error_details,
                    "help": [
                        "Ensure your MCP client includes 'protocolVersion': '2024-11-05'",
                        "Include all required fields in the initialize request",
                        "Verify your MCP client library is up to date"
                    ]
                }
            )
        else:
            # Handle other initialization or runtime errors
            send_error_response(
                None,
                -32603,
                "MCP server error",
                {
                    "details": str(e),
                    "suggestion": "Check that the database path is accessible and environment variables are correct."
                }
            )


async def main():
    """Main entry point for the MCP server with robust error handling."""
    await handle_mcp_with_validation()


if __name__ == "__main__":
    asyncio.run(main())
