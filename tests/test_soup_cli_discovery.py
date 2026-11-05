"""Tests for portable Soup CLI executable discovery."""

import os
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from soup_cli_discovery import resolve_python_interpreter, resolve_soup_binary


def test_resolve_python_interpreter():
    py = resolve_python_interpreter()
    assert py
    assert Path(py).is_file()


def test_soup_bin_env_override(tmp_path, monkeypatch):
    fake_soup = tmp_path / "soup"
    fake_soup.write_text("#!/bin/sh\necho soup\n")
    fake_soup.chmod(0o755)

    monkeypatch.setenv("SOUP_BIN", str(fake_soup))
    resolved = resolve_soup_binary()
    assert resolved == fake_soup.resolve()


def test_soup_bin_env_missing_raises(monkeypatch):
    monkeypatch.setenv("SOUP_BIN", "/nonexistent/path/to/soup")
    with pytest.raises(FileNotFoundError, match="does not exist"):
        resolve_soup_binary()


def test_soup_bin_not_executable_raises(tmp_path, monkeypatch):
    fake_soup = tmp_path / "soup"
    fake_soup.write_text("#!/bin/sh\n")
    fake_soup.chmod(0o644)  # not executable

    monkeypatch.setenv("SOUP_BIN", str(fake_soup))
    with pytest.raises(PermissionError, match="not executable"):
        resolve_soup_binary()


def test_missing_soup_raises_informative_error(tmp_path, monkeypatch):
    monkeypatch.delenv("SOUP_BIN", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))  # empty PATH
    with pytest.raises(FileNotFoundError, match="Soup CLI binary .* could not be discovered"):
        resolve_soup_binary(repo_root=tmp_path / "dummy_repo")
