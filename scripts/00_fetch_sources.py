#!/usr/bin/env python3
"""Optional online fetch from the cited sources.

By default this writes a fetch manifest only. With ``--online`` it performs
real network/vendor operations. With ``--write-archival`` it builds the
committed ``data/archival/`` snapshot from gdshowsdb YAML + curated seed
layers (+ optional Internet Archive / Setlist.fm when configured).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

PLAN: list[dict] = [
    {
        "source": "gdshowsdb",
        "endpoint": "https://github.com/jefmsmit/gdshowsdb",
        "auth": "none (git clone)",
        "rate_limit": "n/a",
    },
    {
        "source": "setlistfm_gd",
        "endpoint": "https://api.setlist.fm/rest/1.0/artist/bd6ad4a/setlists",
        "auth": "Setlist.fm API key (SETLISTFM_API_KEY)",
        "rate_limit": "2 req/s",
    },
    {
        "source": "internet_archive_lma",
        "endpoint": "https://archive.org/advancedsearch.php?q=collection:GratefulDead",
        "auth": "none",
        "rate_limit": "10 req/s",
    },
    {
        "source": "curated_seed",
        "endpoint": "data/seed/",
        "auth": "bundled",
        "rate_limit": "n/a",
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--online", action="store_true", help="clone gdshowsdb and run network fetches"
    )
    parser.add_argument(
        "--write-archival",
        action="store_true",
        help="write data/archival/*.json from merged ingest",
    )
    parser.add_argument(
        "--archival-max",
        action="store_true",
        help="shorthand: --online --write-archival --ia-max-rows 0 --setlistfm-max-pages 0 (full pagination)",
    )
    parser.add_argument(
        "--ia-max-rows",
        type=int,
        default=None,
        help="max Internet Archive rows (0 = unlimited; default 0 with --write-archival, else 5000)",
    )
    parser.add_argument(
        "--setlistfm-max-pages",
        type=int,
        default=None,
        help="Setlist.fm pagination cap (0 = unlimited; default 0 with --write-archival, else 5)",
    )
    parser.add_argument("--skip-cmu", action="store_true", help="skip CMU/Leone fetch")
    parser.add_argument(
        "--skip-whitegum", action="store_true", help="skip whitegum/alex_allan fetch"
    )
    parser.add_argument(
        "--skip-dead-net", action="store_true", help="skip dead.net fetch"
    )
    parser.add_argument(
        "--skip-wikipedia", action="store_true", help="skip Wikipedia fetch"
    )
    args = parser.parse_args()

    if args.archival_max:
        args.online = True
        args.write_archival = True
        args.ia_max_rows = 0
        args.setlistfm_max_pages = 0
    elif args.write_archival:
        if args.ia_max_rows is None:
            args.ia_max_rows = 0
        if args.setlistfm_max_pages is None:
            args.setlistfm_max_pages = 0
    else:
        if args.ia_max_rows is None:
            args.ia_max_rows = 5000
        if args.setlistfm_max_pages is None:
            args.setlistfm_max_pages = 5

    out_dir = ROOT / "output" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "fetch_manifest.json"

    payload: dict = {
        "ran_online": args.online,
        "write_archival": args.write_archival,
        "archival_max": args.archival_max,
        "ia_max_rows": args.ia_max_rows,
        "setlistfm_max_pages": args.setlistfm_max_pages,
        "plan": PLAN,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if args.write_archival:
        from src.ingest.build import build_archival_compendium, write_archival_snapshot

        comp, report = build_archival_compendium(
            online=args.online,
            ia_max_rows=args.ia_max_rows,
            setlistfm_max_pages=args.setlistfm_max_pages,
            skip_cmu=args.skip_cmu,
            skip_whitegum=args.skip_whitegum,
            skip_dead_net=args.skip_dead_net,
            skip_wikipedia=args.skip_wikipedia,
        )
        archival_dir = write_archival_snapshot(comp, report)
        payload["archival_dir"] = str(archival_dir)
        payload["entity_counts"] = report.entity_counts
        payload["corpus_scope"] = report.corpus_scope
        payload["sources_used"] = report.sources_used
        payload["skipped"] = report.skipped
        print(archival_dir)

    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    print(manifest_path)


if __name__ == "__main__":
    main()
