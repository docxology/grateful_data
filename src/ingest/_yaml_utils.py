"""Helpers for gdshowsdb Ruby-style YAML (symbol keys as ``:name``)."""

from __future__ import annotations

from typing import Any


def sym(key: str) -> str:
    """Normalize a Ruby-style symbol key to a plain string."""
    if isinstance(key, str) and key.startswith(":"):
        return key[1:]
    return str(key)


def get(obj: dict[str, Any] | None, name: str, default: Any = None) -> Any:
    if not obj:
        return default
    if name in obj:
        return obj[name]
    colon = f":{name}"
    if colon in obj:
        return obj[colon]
    return default
