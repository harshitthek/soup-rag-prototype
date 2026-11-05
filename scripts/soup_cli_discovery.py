"""Portable executable and environment discovery for Soup CLI."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def resolve_soup_binary(repo_root: Path | None = None) -> Path:
    """Discover and validate the Soup CLI executable.

    Resolution order:
    1. Explicit SOUP_BIN environment variable.
    2. PATH lookup via shutil.which("soup").
    3. Sibling development directory fallback (../Soup/.venv/bin/soup).

    Raises:
        FileNotFoundError: If no valid, executable Soup binary is found.
    """
    env_bin = os.environ.get("SOUP_BIN")
    if env_bin:
        p = Path(env_bin).resolve()
        if not p.is_file():
            raise FileNotFoundError(
                f"Configured SOUP_BIN={env_bin} does not exist or is not a file."
            )
        if not os.access(p, os.X_OK):
            raise PermissionError(
                f"Configured SOUP_BIN={env_bin} is not executable."
            )
        return p

    which_soup = shutil.which("soup")
    if which_soup:
        p = Path(which_soup).resolve()
        if os.access(p, os.X_OK):
            return p

    # Sibling dev repo fallback
    if repo_root is not None:
        sibling_soup = repo_root.parent / "Soup" / ".venv" / "bin" / "soup"
        if sibling_soup.is_file() and os.access(sibling_soup, os.X_OK):
            return sibling_soup.resolve()

    raise FileNotFoundError(
        "Soup CLI binary ('soup') could not be discovered. "
        "Please install Soup CLI in your environment or set the SOUP_BIN environment variable "
        "(e.g. export SOUP_BIN=/path/to/soup)."
    )


def resolve_python_interpreter() -> str:
    """Discover the current active Python interpreter."""
    return sys.executable
