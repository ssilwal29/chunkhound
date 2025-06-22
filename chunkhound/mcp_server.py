#!/usr/bin/env python3
"""
ChunkHound MCP Server - Model Context Protocol implementation
Provides code search capabilities via stdin/stdout JSON-RPC protocol
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
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
    from .database import Database
    from .embeddings import EmbeddingManager
    from .signal_coordinator import SignalCoordinator
    from .file_watcher import FileWatcherManager
    from .core.config import EmbeddingConfig, EmbeddingProviderFactory
    from .registry import configure_registry, get_registry
except ImportError:
    # Handle running as standalone script or PyInstaller binary
    from chunkhound.database import Database
    from chunkhound.embeddings import EmbeddingManager
    from chunkhound.signal_coordinator import SignalCoordinator
    from chunkhound.file_watcher import FileWatcherManager
    from chunkhound.core.config import EmbeddingConfig, EmbeddingProviderFactory
    from registry import configure_registry, get_registry

# Global database, embedding manager, and file watcher instances
# Global state management
_database: Optional[Database] = None
_embedding_manager: Optional[EmbeddingManager] = None
_file_watcher: Optional[FileWatcherManager] = None
_signal_coordinator: Optional[SignalCoordinator] = None

# Initialize MCP server with explicit stdio
server = Server("ChunkHound Code Search")


def _build_mcp_registry_config(config: EmbeddingConfig, db_path: Path) -> Dict[str, Any]:
    """Build registry configuration for MCP server mode.

    Args:
        config: Embedding configuration
        db_path: Database path

    Returns:
        Registry configuration dictionary
    """
    registry_config = {
        'database': {
            'path': str(db_path),
            'type': 'duckdb',
            'batch_size': 500,  # Default batch size
        },
        'embedding': {
            'batch_size': 100,  # Default embedding batch size
            'max_concurrent_batches': 3,
            'provider': config.provider,
            'model': config.model,
        }
    }

    # Add API key if available
    if config.api_key:
        registry_config['embedding']['api_key'] = config.api_key.get_secret_value()

    # Add base URL if available
    if config.base_url:
        registry_config['embedding']['base_url'] = config.base_url

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
    global _database, _embedding_manager, _file_watcher, _signal_coordinator

    # Set MCP mode to suppress stderr output that interferes with JSON-RPC
    os.environ["CHUNKHOUND_MCP_MODE"] = "1"

    if "CHUNKHOUND_DEBUG" in os.environ:
        print("Server lifespan: Starting initialization", file=sys.stderr)

    try:
        # Log environment diagnostics for API key debugging
        log_environment_diagnostics()

        # Initialize database path
        db_path = Path(os.environ.get("CHUNKHOUND_DB_PATH", Path.home() / ".cache" / "chunkhound" / "chunks.duckdb"))
        db_path.parent.mkdir(parents=True, exist_ok=True)

        if "CHUNKHOUND_DEBUG" in os.environ:
            print(f"Server lifespan: Using database at {db_path}", file=sys.stderr)

        # Initialize embedding configuration BEFORE database creation
        _embedding_manager = EmbeddingManager()
        if "CHUNKHOUND_DEBUG" in os.environ:
            print("Server lifespan: Embedding manager initialized", file=sys.stderr)

        # Setup embedding provider and registry configuration
        embedding_config = None
        try:
            # Load configuration with environment variable support
            embedding_config = EmbeddingConfig()

            # Maintain backward compatibility with legacy OPENAI_API_KEY
            legacy_api_key = os.environ.get('OPENAI_API_KEY')
            if not embedding_config.api_key and legacy_api_key:
                from pydantic import SecretStr
                embedding_config.api_key = SecretStr(legacy_api_key)
                if embedding_config.provider == 'openai' and "CHUNKHOUND_DEBUG" in os.environ:
                    print("Server lifespan: Using legacy OPENAI_API_KEY for backward compatibility", file=sys.stderr)

            # Create provider using unified factory
            provider = EmbeddingProviderFactory.create_provider(embedding_config)
            _embedding_manager.register_provider(provider, set_default=True)

            if "CHUNKHOUND_DEBUG" in os.environ:
                print(f"Server lifespan: Embedding provider registered successfully: {embedding_config.provider} with model {embedding_config.model}", file=sys.stderr)

            # CRITICAL FIX: Configure registry BEFORE database creation
            registry_config = _build_mcp_registry_config(embedding_config, db_path)
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

        if "CHUNKHOUND_DEBUG" in os.environ:
            print("Server lifespan: All components initialized successfully", file=sys.stderr)

        # Return server context to the caller
        yield {"db": _database, "embeddings": _embedding_manager, "watcher": _file_watcher}

    except Exception as e:
        if "CHUNKHOUND_DEBUG" in os.environ:
            print(f"Server lifespan: Initialization failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
        raise Exception(f"Failed to initialize database and embeddings: {e}")
    finally:
        if "CHUNKHOUND_DEBUG" in os.environ:
            print("Server lifespan: Entering cleanup phase", file=sys.stderr)

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
                _database.close()
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
        except (IOError, PermissionError):
            await asyncio.sleep(0.1)  # Brief wait
    return False


async def process_file_change(file_path: Path, event_type: str):
    """
    Process a file change event by updating the database.

    This function is called by the filesystem watcher when files change.
    It runs in the main thread to ensure single-threaded database access.
    """
    global _database, _embedding_manager

    if not _database:
        return

    try:
        if event_type == 'deleted':
            # Remove file from database with cleanup tracking
            _database.delete_file_completely(str(file_path))
        else:
            # Process file (created, modified, moved)
            if file_path.exists() and file_path.is_file():
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


def estimate_tokens(text: str) -> int:
    """Estimate token count using simple heuristic (4 chars ≈ 1 token)."""
    return len(text) // 4


def truncate_code(code: str, max_chars: int = 1000) -> Tuple[str, bool]:
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


def optimize_search_results(results: List[Dict[str, Any]], max_tokens: int = 20000) -> Tuple[List[Dict[str, Any]], bool]:
    """Optimize search results to fit within token limits."""
    if not results:
        return results, False
    
    # First pass: create optimized results with previews
    optimized_results = []
    total_tokens = 0
    truncated = False
    
    for result in results:
        # Create optimized result copy
        opt_result = {
            'chunk_id': result.get('chunk_id'),
            'name': result.get('name', result.get('symbol', '')),
            'chunk_type': result.get('chunk_type'),
            'start_line': result.get('start_line'),
            'end_line': result.get('end_line'),
            'file_path': result.get('file_path'),
            'language': result.get('language'),
            'line_count': result.get('line_count')
        }
        
        # Handle code content with truncation
        original_code = result.get('content', result.get('code', ''))
        if original_code:
            code_preview, is_code_truncated = truncate_code(original_code)
            opt_result['code'] = code_preview
            if is_code_truncated:
                opt_result['is_truncated'] = True
                truncated = True
        
        # Estimate tokens for this result
        result_json = json.dumps(opt_result, ensure_ascii=False)
        result_tokens = estimate_tokens(result_json)
        
        # Check if adding this result would exceed limit
        if total_tokens + result_tokens > max_tokens:
            # If this is the first result and it's too big, include it anyway
            if not optimized_results:
                optimized_results.append(opt_result)
                truncated = True
            break
        
        optimized_results.append(opt_result)
        total_tokens += result_tokens
    
    return optimized_results, truncated


def convert_to_ndjson(results: List[Dict[str, Any]]) -> str:
    """Convert search results to NDJSON format."""
    lines = []
    for result in results:
        lines.append(json.dumps(result, ensure_ascii=False))
    return "\n".join(lines)


@server.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> List[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
    """Handle tool calls"""
    if not _database:
        if _signal_coordinator and _signal_coordinator.is_coordination_active():
            raise Exception("Database temporarily unavailable during coordination")
        else:
            raise Exception("Database not initialized")

    if name == "search_regex":
        pattern = arguments.get("pattern", "")
        limit = max(1, min(arguments.get("limit", 10), 100))
        max_tokens = max(1000, min(arguments.get("max_response_tokens", 20000), 25000))

        try:
            # Check connection instead of forcing reconnection (fixes race condition)
            if _database and not _database.is_connected():
                if "CHUNKHOUND_DEBUG" in os.environ:
                    print("Database not connected, reconnecting before regex search", file=sys.stderr)
                _database.reconnect()

            results = _database.search_regex(pattern=pattern, limit=limit)
            optimized_results, was_truncated = optimize_search_results(results, max_tokens)
            
            # Add metadata about truncation
            if was_truncated:
                response_text = f"# TRUNCATED: Results optimized to fit {max_tokens} token limit\n"
                response_text += f"# Original results: {len(results)}, Returned: {len(optimized_results)}\n"
                response_text += convert_to_ndjson(optimized_results)
            else:
                response_text = convert_to_ndjson(optimized_results)
            
            return [types.TextContent(type="text", text=response_text)]
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

    elif name == "search_semantic":
        query = arguments.get("query", "")
        limit = max(1, min(arguments.get("limit", 10), 100))
        max_tokens = max(1000, min(arguments.get("max_response_tokens", 20000), 25000))
        provider = arguments.get("provider", "openai")
        model = arguments.get("model", "text-embedding-3-small")
        threshold = arguments.get("threshold")

        if not _embedding_manager or not _embedding_manager.list_providers():
            raise Exception("No embedding providers available. Set OPENAI_API_KEY to enable semantic search.")

        try:
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

                results = _database.search_semantic(
                    query_vector=query_vector,
                    provider=provider,
                    model=model,
                    limit=limit,
                    threshold=threshold
                )

                optimized_results, was_truncated = optimize_search_results(results, max_tokens)
                
                # Add metadata about truncation
                if was_truncated:
                    response_text = f"# TRUNCATED: Results optimized to fit {max_tokens} token limit\n"
                    response_text += f"# Original results: {len(results)}, Returned: {len(optimized_results)}\n"
                    response_text += convert_to_ndjson(optimized_results)
                else:
                    response_text = convert_to_ndjson(optimized_results)

                return [types.TextContent(type="text", text=response_text)]

            except asyncio.TimeoutError:
                # Handle MCP timeout gracefully with informative error
                raise Exception("Semantic search timed out. This can happen when OpenAI API is experiencing high latency. Please try again.")

        except Exception as e:
            raise Exception(f"Semantic search failed: {str(e)}")

    elif name == "get_stats":
        try:
            stats = _database.get_stats()
            return [types.TextContent(type="text", text=json.dumps(stats, ensure_ascii=False))]
        except Exception as e:
            raise Exception(f"Failed to get stats: {str(e)}")

    elif name == "health_check":
        health_status = {
            "status": "healthy",
            "version": "1.1.0",
            "database_connected": _database is not None,
            "embedding_providers": _embedding_manager.list_providers() if _embedding_manager else []
        }
        return [types.TextContent(type="text", text=json.dumps(health_status, ensure_ascii=False))]

    else:
        raise ValueError(f"Tool not found: {name}")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="search_regex",
            description="Search code using regular expression patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regular expression pattern to search for"},
                    "limit": {"type": "integer", "description": "Maximum number of results to return (1-100)", "default": 10},
                    "max_response_tokens": {"type": "integer", "description": "Maximum response size in tokens (1000-25000)", "default": 20000}
                },
                "required": ["pattern"]
            }
        ),
        types.Tool(
            name="search_semantic",
            description="Search code using semantic similarity (vector search)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "limit": {"type": "integer", "description": "Maximum number of results to return (1-100)", "default": 10},
                    "max_response_tokens": {"type": "integer", "description": "Maximum response size in tokens (1000-25000)", "default": 20000},
                    "provider": {"type": "string", "description": "Embedding provider to use", "default": "openai"},
                    "model": {"type": "string", "description": "Embedding model to use", "default": "text-embedding-3-small"},
                    "threshold": {"type": "number", "description": "Distance threshold for filtering results (optional)"}
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


def send_error_response(message_id: Any, code: int, message: str, data: Optional[dict] = None):
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


def validate_mcp_initialize_message(message_text: str) -> Tuple[bool, Optional[dict], Optional[str]]:
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
