"""Integration layer: reconcile across source-specific parsers."""

from .aliases import SONG_ALIAS_MAP, canonicalize_alias
from .reconcile import Compendium, build_compendium

__all__ = [
    "Compendium",
    "SONG_ALIAS_MAP",
    "build_compendium",
    "canonicalize_alias",
]
