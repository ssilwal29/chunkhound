"""MCP command module - handles Model Context Protocol server operations."""

import argparse
import os
from pathlib import Path
from typing import Any, cast


def mcp_command(args: argparse.Namespace) -> None:
    """Execute the MCP server command.

    Args:
        args: Parsed command-line arguments containing database path
    """
    import subprocess
    import sys

    # Use the standalone MCP launcher that sets environment before any imports
    mcp_launcher_path = Path(__file__).parent.parent.parent.parent.parent / "mcp_launcher.py"
    cmd = [sys.executable, str(mcp_launcher_path), "--db", str(args.db)]

    # Inherit current environment and ensure critical variables are passed through
    env = os.environ.copy()

    # Explicitly ensure OpenAI API key is available if set in current environment
    if "OPENAI_API_KEY" in os.environ:
        env["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]

    process = subprocess.run(
        cmd,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,  # Allow stderr for MCP SDK internal error handling
        env=env  # Pass environment variables to subprocess
    )

    # Exit with the same code as the subprocess
    sys.exit(process.returncode)


def add_mcp_subparser(subparsers: Any) -> argparse.ArgumentParser:
    """Add MCP command subparser to the main parser.

    Args:
        subparsers: Subparsers object from the main argument parser

    Returns:
        The configured MCP subparser
    """
    mcp_parser = subparsers.add_parser(
        "mcp",
        help="Run Model Context Protocol server",
        description="Start the MCP server for integration with MCP-compatible clients"
    )

    mcp_parser.add_argument(
        "--db",
        type=Path,
        default=Path("chunkhound.db"),
        help="DuckDB database file path (default: chunkhound.db)",
    )

    return cast(argparse.ArgumentParser, mcp_parser)


__all__: list[str] = ["mcp_command", "add_mcp_subparser"]
