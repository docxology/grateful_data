# AGENTS.md — `grateful_data/data/archival`

> Docs for this subtree of the grateful_data repo (`docxology/grateful_data`).
> Repo-wide policy: see the repo root `AGENTS.md`/`README.md`.

## What this is

Committed archival tier of the grateful_data corpus: the full **gdshowsdb**
YAML-derived snapshot plus curated layers (personnel, citations, reviews,
releases, lyric pointers), written as JSON by `scripts/00_fetch_sources.py`
(`--online --archival-max`) and consumed by the `GRATEFUL_DATA_TIER=archival`
pipeline (`scripts/99_pipeline.py --tier archival`). This is the full-corpus
source of truth; `data/seed/` holds the small curated counterpart. Measured
counts live in `output/archival/build_report.json` and
`data/archival/README.md` (shows, venues, songs, performances, recordings,
releases, reviews, citations, lyric pointers) — re-derive, don't hard-code.

## Layout (verified by direct listing, 2026-08-29)

```
README.md, citations.json, lyric_pointers.json, performances.json, personnel.json, recordings.json, releases.json, reviews.json, shows.json, songs.json, venue_geo.json, venues.json
```

## Gotchas

- Contents-only docs: if the tree changed since the listing above, re-verify
  against disk.
