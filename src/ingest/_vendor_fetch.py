"""Shared vendor-cache helpers for online ingest adapters."""

from __future__ import annotations

import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VENDOR_ROOT = PROJECT_ROOT / "data" / "vendor"


def vendor_path(source: str, filename: str) -> Path:
    return VENDOR_ROOT / source / filename


def fetch_or_read_cache(
    *,
    source: str,
    filename: str,
    url: str,
    online: bool,
    timeout: int = 120,
) -> str:
    """Return cached text or fetch and persist under ``data/vendor/<source>/``."""
    text, _url = fetch_or_read_cache_with_fallbacks(
        source=source,
        filename=filename,
        urls=(url,),
        online=online,
        timeout=timeout,
    )
    return text


def fetch_or_read_cache_with_fallbacks(
    *,
    source: str,
    filename: str,
    urls: tuple[str, ...],
    online: bool,
    timeout: int = 120,
    min_bytes: int = 200,
) -> tuple[str, str]:
    """Return ``(text, url_used)`` from cache or the first successful fetch URL."""
    path = vendor_path(source, filename)
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="replace"), f"cache:{path}"
    if not online:
        raise FileNotFoundError(f"vendor cache missing: {path} (run with --online)")
    errors: list[str] = []
    for url in urls:
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "grateful_data-ingest/1.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            if len(text.encode("utf-8")) < min_bytes:
                errors.append(f"{url}: response too small ({len(text)} chars)")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            return text, url
        except OSError as exc:
            errors.append(f"{url}: {exc}")
    raise OSError(f"all fetch URLs failed for {source}/{filename}: {'; '.join(errors)}")
