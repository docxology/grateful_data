"""Executable honesty boundary for the compendium.

The manuscript's honesty framing — "no lyric text or audio bundled; reviews
must point to a real source; no fabricated DOIs; no fabricated 'audio
feature' fields" — is here promoted from prose to a runtime contract
enforced inside :func:`assert_honesty` (called by ``src/seed.py`` at load
time and by ``scripts/`` validators). Violations raise
:class:`HonestyViolation` and the loader fails closed.

The pattern follows the BTC_Buffalo honesty-boundary precedent: the
contract walks the seed shape and refuses anything that would let the
project quietly drift from its stated scope.

Forbidden shapes
================

* ``lyric_text``, ``lyrics``, ``verse``, ``chorus`` keys anywhere — the
  project explicitly does not bundle lyric text (copyright).
* A ``Review`` with sentiment ``> 0`` and an empty or missing
  ``source_url`` — over-claim shape "we say something positive happened
  with no way to verify it".
* A ``Citation`` whose ``url`` is empty or non-http(s).
* A ``Recording`` whose ``archive_id`` claims to be from Internet Archive
  (prefix ``gd``) but whose ``url`` does not point at ``archive.org``.
* A ``LyricPointer`` whose ``source_url`` is empty — we promise it's a
  *pointer*; missing pointer is over-claim.
* Any ``audio_feature_*`` key anywhere — we do not bundle audio features;
  any such field would be silently fabricated until the
  ``fifteen-songs-dataset`` pipeline runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .integration.reconcile import Compendium


class HonestyViolation(Exception):
    """Raised when the seed or a compendium fails the honesty boundary."""

    def __init__(self, violations: tuple[str, ...]) -> None:
        super().__init__("honesty boundary violated: " + "; ".join(violations))
        self.violations = violations


FORBIDDEN_LYRIC_KEYS: frozenset[str] = frozenset(
    {"lyric_text", "lyrics", "verse", "chorus", "stanza", "refrain"}
)
FORBIDDEN_KEY_PREFIXES: tuple[str, ...] = ("audio_feature_", "synth_")


@dataclass(frozen=True)
class HonestyBoundary:
    """Stateless contract over compendium-shaped data."""

    def check_raw_seed(self, payload: Any, *, path: str = "$") -> tuple[str, ...]:
        """Walk a freshly-loaded JSON payload for forbidden shapes."""
        violations: list[str] = []
        if isinstance(payload, dict):
            for k, v in payload.items():
                lk = k.lower() if isinstance(k, str) else ""
                if lk in FORBIDDEN_LYRIC_KEYS:
                    violations.append(
                        f"{path}.{k}: forbidden lyric-text key (project bundles pointers only)"
                    )
                if any(lk.startswith(p) for p in FORBIDDEN_KEY_PREFIXES):
                    violations.append(
                        f"{path}.{k}: forbidden prefix (project bundles no audio features)"
                    )
                violations.extend(self.check_raw_seed(v, path=f"{path}.{k}"))
        elif isinstance(payload, list):
            for i, item in enumerate(payload):
                violations.extend(self.check_raw_seed(item, path=f"{path}[{i}]"))
        return tuple(violations)

    def check_compendium(self, comp: Compendium) -> tuple[str, ...]:
        """Check a fully-built ``Compendium`` for boundary violations."""
        violations: list[str] = []
        for r in comp.reviews:
            if r.sentiment > 0 and not r.source_url:
                violations.append(
                    f"review by {r.author!r} on {r.show_slug}: positive sentiment with no source_url (over-claim shape)"
                )
        for c in comp.citations:
            if not c.url or not c.url.startswith(("http://", "https://")):
                violations.append(f"citation {c.key!r}: missing or non-http(s) URL")
        for rec in comp.recordings:
            if rec.archive_id.lower().startswith("gd") and "archive.org" not in rec.url:
                violations.append(
                    f"recording {rec.archive_id!r}: identifier suggests Internet Archive "
                    "but url does not point at archive.org"
                )
        for lp in comp.lyric_pointers:
            if not lp.source_url:
                violations.append(
                    f"lyric pointer for {lp.song_slug!r}: missing source_url"
                )
        return tuple(violations)

    def check_payloads(self, payloads: Iterable[Any]) -> tuple[str, ...]:
        violations: list[str] = []
        for p in payloads:
            violations.extend(self.check_raw_seed(p))
        return tuple(violations)


def assert_honesty(comp: Compendium, raw_payloads: Iterable[Any] = ()) -> None:
    """Convenience: build the boundary, check both views, raise on violations."""
    boundary = HonestyBoundary()
    violations = boundary.check_compendium(comp)
    violations = violations + boundary.check_payloads(raw_payloads)
    if violations:
        raise HonestyViolation(violations)
