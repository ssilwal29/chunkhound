import importlib.util
import importlib.metadata
from pathlib import Path

from chunkhound.api.cli.commands.run import _resolve_package_path, _get_package_version


def test_resolve_existing_package():
    path = _resolve_package_path("json")
    assert path is not None
    assert Path(path).is_dir()


def test_resolve_missing_package():
    assert _resolve_package_path("nonexistent_pkg_12345") is None


def test_get_package_version():
    v = _get_package_version("pip")
    assert v == importlib.metadata.version("pip")
