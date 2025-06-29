import importlib.util
from pathlib import Path

from chunkhound.api.cli.commands.run import _resolve_package_path


def test_resolve_existing_package():
    path = _resolve_package_path("json")
    assert path is not None
    assert Path(path).is_dir()


def test_resolve_missing_package():
    assert _resolve_package_path("nonexistent_pkg_12345") is None
