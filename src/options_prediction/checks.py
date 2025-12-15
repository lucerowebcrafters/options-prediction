from __future__ import annotations

"""Utility helpers for validating runtime prerequisites."""

import importlib.util
from typing import Iterable, List


class MissingDependencyError(RuntimeError):
    """Raised when an optional dependency is unavailable."""


def missing_packages(packages: Iterable[str]) -> List[str]:
    return [name for name in packages if importlib.util.find_spec(name) is None]


def require_packages(packages: Iterable[str]) -> None:
    missing = missing_packages(packages)
    if missing:
        raise MissingDependencyError(
            "The following packages are required but not installed: " + ", ".join(sorted(missing))
        )
