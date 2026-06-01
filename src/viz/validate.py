"""Figure-validation: prove every rendered figure is real and non-degenerate.

Rendering a figure to disk does not prove it is *correct*: a panel whose data
silently collapsed to empty still writes a (blank) PNG, and a green pipeline
would ship it. This module is the probe that closes that gap. For each figure
it checks:

* the file exists and exceeds a minimum byte size,
* the decoded raster meets minimum pixel dimensions,
* the pixels are **not blank** — i.e. the image has non-trivial variance, so a
  uniformly-white/empty canvas is rejected.

It reads PNGs via :mod:`matplotlib.image` (already a project dependency — no
new packages), so it works headless with the Agg backend.

SCOPE (honesty): this is a **blank-canvas tripwire**, not a correctness oracle.
A figure plotting the *wrong* data (swapped axes, stale series, sparse noise)
can still pass the variance check — pixel variance proves "not blank," never
"correct." Figure *correctness* is bound elsewhere: the data behind the figures
is computed by ``src/analysis`` and pinned by the archival ground-truth tests
(``tests/test_archival_ground_truth.py``). Do not read a green figure-validation
report as certifying that the plotted numbers are right.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import matplotlib.image as mpimg
import numpy as np

# Defaults tuned so a real ~150-dpi matplotlib panel passes comfortably while a
# blank canvas or truncated write fails.
MIN_BYTES = 1000
MIN_DIM = 100
MIN_VARIANCE = 1e-5


@dataclass(frozen=True)
class FigureValidation:
    """Per-figure validation result."""

    path: str
    exists: bool
    size_bytes: int
    width: int
    height: int
    pixel_variance: float
    ok: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "exists": self.exists,
            "size_bytes": self.size_bytes,
            "width": self.width,
            "height": self.height,
            "pixel_variance": round(self.pixel_variance, 8),
            "ok": self.ok,
            "reasons": list(self.reasons),
        }


def validate_figure(
    path: Path | str,
    *,
    min_bytes: int = MIN_BYTES,
    min_dim: int = MIN_DIM,
    min_variance: float = MIN_VARIANCE,
) -> FigureValidation:
    """Validate a single rendered figure on disk."""
    p = Path(path)
    reasons: list[str] = []

    if not p.exists():
        return FigureValidation(
            str(p), False, 0, 0, 0, 0.0, False, ("file does not exist",)
        )

    size = p.stat().st_size
    if size < min_bytes:
        reasons.append(f"file too small ({size} < {min_bytes} bytes)")

    width = height = 0
    variance = 0.0
    try:
        arr = mpimg.imread(str(p))
        if arr.ndim >= 2:
            height, width = int(arr.shape[0]), int(arr.shape[1])
        variance = float(np.var(arr))
        if width < min_dim or height < min_dim:
            reasons.append(f"dimensions too small ({width}x{height}, min {min_dim})")
        if variance < min_variance:
            reasons.append(
                f"image appears blank (pixel variance {variance:.2e} < {min_variance:.0e})"
            )
    except Exception as exc:  # pragma: no cover - exercised via negative-control test
        reasons.append(f"could not decode image: {exc}")

    ok = not reasons
    return FigureValidation(
        str(p), True, size, width, height, variance, ok, tuple(reasons)
    )


@dataclass(frozen=True)
class FigureValidationReport:
    """Aggregate validation across a directory of expected figures."""

    results: tuple[FigureValidation, ...]
    missing: tuple[str, ...]

    @property
    def all_ok(self) -> bool:
        return not self.missing and all(r.ok for r in self.results)

    @property
    def n_ok(self) -> int:
        return sum(1 for r in self.results if r.ok)

    def to_dict(self) -> dict:
        return {
            "n_figures": len(self.results),
            "n_ok": self.n_ok,
            "n_failed": len(self.results) - self.n_ok,
            "missing": list(self.missing),
            "all_ok": self.all_ok,
            "results": [r.to_dict() for r in self.results],
        }


def validate_figures(
    figures_dir: Path | str,
    expected: list[str] | tuple[str, ...] | None = None,
    **kwargs,
) -> FigureValidationReport:
    """Validate every figure in ``figures_dir``.

    If ``expected`` is given, any expected filename absent from the directory
    is reported as ``missing`` (a missing expected figure is a hard failure).
    """
    figures_dir = Path(figures_dir)
    present = (
        sorted(p.name for p in figures_dir.glob("*.png"))
        if figures_dir.exists()
        else []
    )
    names = list(expected) if expected is not None else present

    results = tuple(validate_figure(figures_dir / name, **kwargs) for name in names)
    missing = tuple(name for name in names if not (figures_dir / name).exists())
    return FigureValidationReport(results=results, missing=missing)
