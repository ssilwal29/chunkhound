"""Package command for ChunkHound."""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from loguru import logger

from .run import run_command


async def package_command(args: argparse.Namespace) -> None:
    """Download or clone a package and index it."""
    if not args.pypi and not args.github:
        logger.error("Specify --pypi or --github")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        if args.pypi:
            logger.info(f"Downloading PyPI package: {args.pypi}")
            install_dir = tmp_path / "pkg"
            subprocess.run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--no-deps",
                    "--no-compile",
                    "--upgrade",
                    "--target",
                    str(install_dir),
                    args.pypi,
                ],
                check=True,
            )
            package_dir = install_dir
        else:
            logger.info(f"Cloning repository: {args.github}")
            repo_dir = tmp_path / "repo"
            clone_cmd = ["git", "clone", "--depth", "1", args.github, str(repo_dir)]
            if args.ref:
                clone_cmd.extend(["--branch", args.ref])
            subprocess.run(clone_cmd, check=True)
            package_dir = repo_dir

        index_args = argparse.Namespace(**vars(args))
        index_args.path = package_dir
        index_args.watch = False
        index_args.initial_scan_only = False

        await run_command(index_args)


__all__: list[str] = ["package_command"]
