import argparse
from typing import Any, cast

from .main_parser import (
    add_common_arguments,
    add_database_argument,
    add_embedding_arguments,
    add_file_pattern_arguments,
)


def add_package_subparser(subparsers: Any) -> argparse.ArgumentParser:
    """Add package command subparser."""
    parser = subparsers.add_parser(
        "package",
        help="Index a PyPI or GitHub package",
        description=(
            "Download a package from PyPI or clone a GitHub repository "
            "and run ChunkHound indexing on it."
        ),
    )

    add_common_arguments(parser)
    add_database_argument(parser)
    add_embedding_arguments(parser)
    add_file_pattern_arguments(parser)

    parser.add_argument(
        "--pypi",
        help="PyPI package name to download",
    )
    parser.add_argument(
        "--github",
        help="GitHub repository URL to clone",
    )
    parser.add_argument(
        "--ref",
        help="Git reference (branch or tag) to checkout",
    )
    parser.add_argument(
        "--force-reindex",
        action="store_true",
        help="Force reindexing of all files",
    )
    parser.add_argument(
        "--embedding-batch-size",
        type=int,
        default=100,
        help="Number of text chunks per embedding API request (default: 100)",
    )
    parser.add_argument(
        "--db-batch-size",
        type=int,
        default=500,
        help="Number of records per database transaction (default: 500)",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Maximum concurrent embedding batches (default: 3)",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up orphaned chunks from deleted files",
    )

    return cast(argparse.ArgumentParser, parser)


__all__: list[str] = ["add_package_subparser"]
