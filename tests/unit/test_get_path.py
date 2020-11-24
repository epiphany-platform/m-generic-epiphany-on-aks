"""Unit testing of the "get_path" function."""

from os import environ
from pathlib import Path
from azepi._helpers import get_path


def test_get_path_unix_absolute_path():
    """Test returned object for UNIX absolute path."""

    assert get_path(
        "/dir/file") == Path("/dir/file"), "Should be Path('/dir/file')"


def test_get_path_resolve_dot():
    """Test dot resolving."""

    assert get_path(".") == Path.cwd()


def test_get_path_expand_tilde():
    """Test tilde expansion."""

    assert get_path("~/file") == Path(environ["HOME"]) / "file"
