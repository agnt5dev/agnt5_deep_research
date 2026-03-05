"""Pytest fixtures and configuration for the SDK Python benchmark blueprint."""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    if src.exists():
        path = str(src)
        if path not in sys.path:
            sys.path.insert(0, path)


_ensure_src_on_path()

