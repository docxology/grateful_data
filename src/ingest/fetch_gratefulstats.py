"""Optional Grateful Stats REST overlay (requires Patreon API credentials)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from ..models import Citation, normalize_slug

DEFAULT_BASE = "https://www.gratefulstats.com/api"


def _api_headers() -> dict[str, str]:
    key = os.environ.get("GRATEFULSTATS_API_KEY", "").strip()
    if not key:
        return {}
    return {
        "User-Agent": "grateful_data-ingest/1.0",
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }


def fetch_gratefulstats_citation(*, online: bool) -> list[Citation]:
    """Return a citation row when the API base is reachable (smoke probe)."""
    if not online:
        return []
    base = os.environ.get("GRATEFULSTATS_API_BASE", DEFAULT_BASE).rstrip("/")
    key = os.environ.get("GRATEFULSTATS_API_KEY", "").strip()
    if not key:
        raise OSError("gratefulstats: GRATEFULSTATS_API_KEY not set")
    url = f"{base}/shows?{urllib.parse.urlencode({'year': 1977, 'limit': 1})}"
    req = urllib.request.Request(url, headers=_api_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise OSError(f"gratefulstats API HTTP {exc.code}: {exc.reason}") from exc
    except OSError as exc:
        raise OSError(f"gratefulstats API unreachable: {exc}") from exc
    return [
        Citation(
            key=normalize_slug("grateful_stats_api")[:80],
            title="Grateful Stats API (live probe)",
            url="https://www.gratefulstats.com/APIInfo.html",
            kind="api",
        ),
    ]
