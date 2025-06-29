"""Run command module - handles directory indexing and file watching operations."""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Optional
import importlib.util

from loguru import logger

from chunkhound import __version__
from chunkhound.embeddings import (
    EmbeddingManager,
    create_openai_compatible_provider,
    create_openai_provider,
    create_tei_provider,
)
from chunkhound.signal_coordinator import CLICoordinator
from registry import configure_registry, create_indexing_coordinator

from ..parsers.run_parser import process_batch_arguments
from ..utils.config_helpers import (
    args_to_config,
    create_legacy_registry_config,
    validate_config_for_command,
)
from ..utils.output import OutputFormatter, format_stats
from ..utils.validation import (
    ensure_database_directory,
    validate_file_patterns,
    validate_numeric_args,
    validate_path,
    validate_provider_args,
)


def _resolve_package_path(package: str) -> Optional[Path]:
    """Resolve the filesystem path for an installed package."""
    spec = importlib.util.find_spec(package)
    if spec is None:
        return None

    if spec.submodule_search_locations:
        # Package directory
        return Path(list(spec.submodule_search_locations)[0])

    if spec.origin:
        # Single file module
        return Path(spec.origin).parent

    return None


async def run_command(args: argparse.Namespace) -> None:
    """Execute the run command using the service layer.

    Args:
        args: Parsed command-line arguments
    """
    # Initialize output formatter
    formatter = OutputFormatter(verbose=args.verbose)

    if getattr(args, "package", None):
        pkg_path = _resolve_package_path(args.package)
        if not pkg_path:
            formatter.error(f"Package not found: {args.package}")
            sys.exit(1)
        args.path = pkg_path
        formatter.info(f"Resolved package '{args.package}' to {pkg_path}")

    # Display startup information
    formatter.info(f"Starting ChunkHound v{__version__}")
    formatter.info(f"Processing directory: {args.path}")
    formatter.info(f"Database: {args.db}")

    # Process and validate batch arguments (includes deprecation warnings)
    process_batch_arguments(args)

    # Validate arguments
    if not _validate_run_arguments(args, formatter):
        sys.exit(1)

    # Initialize CLI coordinator for database access coordination
    cli_coordinator = CLICoordinator(Path(args.db))

    try:
        # Check for running MCP server and coordinate if needed
        await _handle_mcp_coordination(cli_coordinator, formatter)

        # Configure the provider registry
        config = _build_registry_config(args)
        configure_registry(config)

        # Set up file patterns using unified config
        project_dir = Path(args.path) if hasattr(args, 'path') else Path.cwd()
        unified_config = args_to_config(args, project_dir)
        include_patterns, exclude_patterns = _setup_file_patterns_from_config(unified_config, args)
        formatter.info(f"Include patterns: {include_patterns}")
        formatter.verbose_info(f"Exclude patterns: {exclude_patterns}")

        # Initialize services
        indexing_coordinator = create_indexing_coordinator()

        formatter.success(f"Service layer initialized: {args.db}")

        # Get initial stats
        initial_stats = await indexing_coordinator.get_stats()
        formatter.info(f"Initial stats: {format_stats(initial_stats)}")

        # Perform directory processing
        await _process_directory(
            indexing_coordinator, args, formatter,
            include_patterns, exclude_patterns
        )

        # Generate missing embeddings if enabled
        if not args.no_embeddings:
            await _generate_missing_embeddings(indexing_coordinator, formatter, exclude_patterns)

        # Start watch mode if enabled
        if args.watch:
            formatter.info("Initial indexing complete. Starting watch mode...")
            await _start_watch_mode(args, indexing_coordinator, formatter, exclude_patterns)
        formatter.success("Run command completed successfully")

    except KeyboardInterrupt:
        formatter.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        formatter.error(f"Run command failed: {e}")
        logger.exception("Run command error details")
        sys.exit(1)
    finally:
        # Restore database access to MCP server if coordination was active
        cli_coordinator.release_database_access()


def _validate_run_arguments(args: argparse.Namespace, formatter: OutputFormatter) -> bool:
    """Validate run command arguments.

    Args:
        args: Parsed arguments
        formatter: Output formatter

    Returns:
        True if valid, False otherwise
    """
    # Validate path
    if not validate_path(args.path, must_exist=True, must_be_dir=True):
        return False

    # Ensure database directory exists
    if not ensure_database_directory(args.db):
        return False

    # Validate provider arguments
    if not args.no_embeddings:
        if not validate_provider_args(args.provider, args.api_key, args.base_url, args.model):
            return False

    # Validate file patterns
    if not validate_file_patterns(args.include, args.exclude):
        return False

    # Validate numeric arguments (batch validation now handled in process_batch_arguments)
    if not validate_numeric_args(args.debounce_ms, getattr(args, 'embedding_batch_size', 100)):
        return False

    return True


async def _handle_mcp_coordination(cli_coordinator: CLICoordinator, formatter: OutputFormatter) -> None:
    """Handle MCP server coordination for database access.

    Args:
        cli_coordinator: CLI coordinator instance
        formatter: Output formatter
    """
    if cli_coordinator.signal_coordinator.is_mcp_server_running():
        mcp_pid = cli_coordinator.signal_coordinator.process_detector.get_server_pid()
        formatter.info(f"🔍 Detected running MCP server (PID {mcp_pid})")

        if not cli_coordinator.request_database_access():
            formatter.error("❌ Failed to coordinate database access. Please stop the MCP server or use a different database file.")
            sys.exit(1)


def _build_registry_config(args: argparse.Namespace) -> dict[str, Any]:
    """Build configuration for the provider registry.

    Args:
        args: Parsed arguments

    Returns:
        Configuration dictionary
    """
    # Convert CLI args to unified configuration
    project_dir = Path(args.path) if hasattr(args, 'path') else Path.cwd()
    unified_config = args_to_config(args, project_dir)
    
    # Validate configuration for the index command
    validation_errors = validate_config_for_command(unified_config, 'index')
    if validation_errors:
        for error in validation_errors:
            logger.error(f"Configuration error: {error}")
        raise ValueError("Invalid configuration")
    
    # Convert to legacy registry format
    return create_legacy_registry_config(
        unified_config, 
        no_embeddings=getattr(args, 'no_embeddings', False)
    )


def _setup_file_patterns_from_config(config: Any, args: argparse.Namespace) -> tuple[list[str], list[str]]:
    """Set up file inclusion and exclusion patterns from unified config.

    Args:
        config: Unified configuration object
        args: Parsed arguments (for fallback)

    Returns:
        Tuple of (include_patterns, exclude_patterns)
    """
    # Use configuration include patterns, fallback to CLI args, then defaults
    if config.indexing.include_patterns:
        include_patterns = config.indexing.include_patterns
    elif hasattr(args, 'include') and args.include:
        include_patterns = args.include
    else:
        # Get patterns from Language enum and convert to simple glob patterns
        from core.types.common import Language
        patterns = []
        for ext in Language.get_all_extensions():
            patterns.append(f"*{ext}")
        # Add special filenames
        patterns.extend(["Makefile", "makefile", "GNUmakefile", "gnumakefile"])
        include_patterns = patterns

    # Use configuration exclude patterns, fallback to CLI args, then defaults
    exclude_patterns = list(config.indexing.exclude_patterns)
    if hasattr(args, 'exclude') and args.exclude:
        exclude_patterns.extend(args.exclude)

    return include_patterns, exclude_patterns


async def _setup_embedding_manager(args: argparse.Namespace, formatter: OutputFormatter) -> EmbeddingManager | None:
    """Set up embedding manager based on provider configuration.

    Args:
        args: Parsed arguments
        formatter: Output formatter

    Returns:
        Configured EmbeddingManager or None if embeddings disabled
    """
    if args.no_embeddings:
        formatter.info("Embeddings disabled")
        return None

    try:
        embedding_manager = EmbeddingManager()

        if args.provider == "openai":
            model = args.model or "text-embedding-3-small"
            provider = create_openai_provider(
                api_key=args.api_key,
                base_url=args.base_url,
                model=model,
            )
            embedding_manager.register_provider(provider, set_default=True)
            formatter.success(f"Embedding provider: {args.provider}/{model}")

        elif args.provider == "openai-compatible":
            model = args.model or "auto-detected"
            provider = create_openai_compatible_provider(
                base_url=args.base_url,
                model=model,
                api_key=args.api_key,
            )
            embedding_manager.register_provider(provider, set_default=True)
            formatter.success(f"Embedding provider: {args.provider}/{model} at {args.base_url}")

        elif args.provider == "tei":
            provider = create_tei_provider(
                base_url=args.base_url,
                model=args.model,
            )
            embedding_manager.register_provider(provider, set_default=True)
            formatter.success(f"Embedding provider: {args.provider} at {args.base_url}")

        elif args.provider == "bge-in-icl":
            # BGE-IN-ICL provider setup would go here
            formatter.warning("BGE-IN-ICL provider not yet implemented in service layer")
            return None

        else:
            formatter.warning(f"Unknown embedding provider: {args.provider}")
            return None

        return embedding_manager

    except Exception as e:
        formatter.warning(f"Failed to initialize embedding provider: {e}")
        formatter.info("Continuing without embeddings...")
        return None


async def _process_directory(
    indexing_coordinator,
    args: argparse.Namespace,
    formatter: OutputFormatter,
    include_patterns: list[str],
    exclude_patterns: list[str]
) -> None:
    """Process directory for indexing.

    Args:
        indexing_coordinator: Indexing coordinator service
        args: Parsed arguments
        formatter: Output formatter
        include_patterns: File inclusion patterns
        exclude_patterns: File exclusion patterns
    """
    formatter.info("Starting file processing...")

    # Convert patterns to service layer format
    processed_patterns = [f"**/{pattern}" for pattern in include_patterns]

    # Process directory using indexing coordinator
    result = await indexing_coordinator.process_directory(
        args.path,
        patterns=processed_patterns,
        exclude_patterns=exclude_patterns
    )

    if result["status"] in ["complete", "success"]:
        formatter.success("Processing complete:")
        formatter.info(f"   • Processed: {result.get('files_processed', result.get('processed', 0))} files")
        formatter.info(f"   • Skipped: {result.get('skipped', 0)} files")
        formatter.info(f"   • Errors: {result.get('errors', 0)} files")
        formatter.info(f"   • Total chunks: {result.get('total_chunks', 0)}")

        # Report cleanup statistics
        cleanup = result.get('cleanup', {})
        if cleanup.get('deleted_files', 0) > 0 or cleanup.get('deleted_chunks', 0) > 0:
            formatter.info("🧹 Cleanup summary:")
            formatter.info(f"   • Deleted files: {cleanup.get('deleted_files', 0)}")
            formatter.info(f"   • Removed chunks: {cleanup.get('deleted_chunks', 0)}")

        # Show updated stats
        final_stats = await indexing_coordinator.get_stats()
        formatter.info(f"Final stats: {format_stats(final_stats)}")

    else:
        formatter.error(f"Processing failed: {result}")
        raise RuntimeError(f"Directory processing failed: {result}")


async def _generate_missing_embeddings(indexing_coordinator, formatter: OutputFormatter, exclude_patterns: list[str]) -> None:
    """Generate missing embeddings for chunks.

    Args:
        indexing_coordinator: Indexing coordinator service
        formatter: Output formatter
        exclude_patterns: File patterns to exclude from embedding generation
    """
    formatter.info("Checking for missing embeddings...")

    embed_result = await indexing_coordinator.generate_missing_embeddings(exclude_patterns=exclude_patterns)

    if embed_result["status"] == "success":
        formatter.success(f"Generated {embed_result['generated']} missing embeddings")
    elif embed_result["status"] in ["up_to_date", "complete"]:
        if embed_result.get("message"):
            formatter.success(embed_result["message"])
        else:
            formatter.info("All embeddings up to date")
    else:
        formatter.warning(f"Embedding generation failed: {embed_result}")


async def _start_watch_mode(args: argparse.Namespace, indexing_coordinator, formatter: OutputFormatter, exclude_patterns: list[str]) -> None:
    """Start file watching mode.

    Args:
        args: Parsed arguments
        indexing_coordinator: Indexing coordinator service
        formatter: Output formatter
        exclude_patterns: File patterns to exclude from processing
    """
    formatter.info("🔍 Starting file watching mode...")

    try:
        # Import file watcher components
        from chunkhound.file_watcher import WATCHDOG_AVAILABLE, FileWatcherManager

        if not WATCHDOG_AVAILABLE:
            formatter.error("❌ File watching requires the 'watchdog' package. Install with: pip install watchdog")
            return

        # Initialize file watcher
        file_watcher_manager = FileWatcherManager()

        # Create callback for file changes
        async def process_cli_file_change(file_path: Path, event_type: str):
            """Process file changes in CLI mode."""
            try:
                if event_type == 'deleted':
                    removed_chunks = await indexing_coordinator.remove_file(str(file_path))
                    if removed_chunks > 0:
                        formatter.info(f"🗑️  Removed {removed_chunks} chunks from deleted file: {file_path}")
                else:
                    # Process file (created, modified, moved)
                    if file_path.exists() and file_path.is_file():
                        # Check if file should be excluded before processing
                        from fnmatch import fnmatch
                        should_exclude = False
                        
                        # Get relative path from watch directory for pattern matching
                        watch_dir = Path(args.path) if hasattr(args, 'path') else Path.cwd()
                        try:
                            rel_path = file_path.relative_to(watch_dir)
                        except ValueError:
                            # File is not under watch directory, use absolute path
                            rel_path = file_path
                        
                        for exclude_pattern in exclude_patterns:
                            # Check both relative and absolute paths
                            if (fnmatch(str(rel_path), exclude_pattern) or 
                                fnmatch(str(file_path), exclude_pattern)):
                                should_exclude = True
                                break
                        
                        if should_exclude:
                            formatter.verbose_info(f"🚫 Skipped excluded file: {file_path}")
                            return
                        
                        result = await indexing_coordinator.process_file(file_path)
                        if result["status"] == "success":
                            formatter.info(f"📝 Processed {event_type} file: {file_path} ({result['chunks']} chunks)")
                        elif result["status"] not in ["skipped", "no_content", "no_chunks"]:
                            formatter.warning(f"⚠️  Failed to process {event_type} file: {file_path} - {result.get('error', 'unknown error')}")
            except Exception as e:
                formatter.error(f"❌ Error processing {event_type} for {file_path}: {e}")

        # Initialize file watcher with callback
        watch_paths = [args.path] if args.path.is_dir() else [args.path.parent]
        watcher_success = await file_watcher_manager.initialize(
            process_cli_file_change,
            watch_paths=watch_paths
        )

        if not watcher_success:
            formatter.error("❌ Failed to initialize file watcher")
            return

        formatter.success("✅ File watching started. Press Ctrl+C to stop.")

        # Keep watching until interrupted
        try:
            while True:
                await asyncio.sleep(1.0)
        except KeyboardInterrupt:
            formatter.info("🛑 File watching stopped by user")
        finally:
            await file_watcher_manager.cleanup()

    except ImportError as e:
        formatter.error(f"❌ Failed to import file watching components: {e}")
    except Exception as e:
        formatter.error(f"❌ File watching failed: {e}")


__all__ = ["run_command", "_resolve_package_path"]
