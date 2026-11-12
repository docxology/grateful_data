# Archival tier (`data/archival/`)

Committed snapshot of the full **gdshowsdb** YAML corpus plus curated layers
from `data/seed/` (personnel, citations, reviews, releases, lyric pointers).

## Measured extent (last build)

Regenerate `output/archival/build_report.json` after refresh; do not hard-code
counts in prose.

| Entity | Measured (2026-05-30 offline citation/context refresh, truckin gap-fill snapshot) |
| --- | --- |
| Shows | 3,341 |
| Venues | 912 |
| Songs | 645 |
| Performances | 40,757 |
| Segue markers (`segue_into`) | 16,585 |
| Personnel | 14 (curated) |
| Recordings | 7,122 (Internet Archive LMA unlimited; 100 dropped on unknown show slug, 1 on date mismatch) |
| Releases | 259 (curated seed + Wikipedia discography merge) |
| Reviews | 1,888 (1,877 maximinus + 11 curated exemplar rows) |
| Citations | 139 (26 seed + bibliography MD + `docs/manuscript/references.bib`, URL-deduped) |
| Lyric pointers | 548 (CMU index + curated overlay + dead.net gap-fill URLs; 80 with lyricist, 24 with themes) |

Coverage vs `FULL_CORPUS_SHOW_ESTIMATE` (~2,318) is reported in the build report.

## Refresh procedure

```bash
cd /path/to/grateful_data

```bash
# Clone/update vendor dump (gitignored) and write committed JSON — full pagination profile
uv run python scripts/00_fetch_sources.py --online --archival-max

# Equivalent explicit flags:
# uv run python scripts/00_fetch_sources.py --online --write-archival --ia-max-rows 0 --setlistfm-max-pages 0

# Optional: Setlist.fm gap-fill (requires SETLISTFM_API_KEY for archival-max)
export SETLISTFM_API_KEY=...

# Full analysis + export + bundle at archival scale
GRATEFUL_DATA_TIER=archival uv run python scripts/99_pipeline.py --tier archival

# Cross-source reconciliation report (also runs at end of archival pipeline)
GRATEFUL_DATA_TIER=archival uv run python scripts/17_reconcile_sources.py
```

Vendor caches (gitignored): `data/vendor/{gdshowsdb,cmu,whitegum,dead_net,wikipedia}/`.

## Files

- `shows.json` — date, venue, setlist (titles only; human-readable)
- `performances.json` — authoritative performance rows with optional `segue_into` (archival tier)
- `venues.json`, `songs.json`, `recordings.json`, … — same contract as `data/seed/`

## Provenance

- Primary bulk: [jefmsmit/gdshowsdb](https://github.com/jefmsmit/gdshowsdb) year YAML (`:segued` → `segue_into`)
- Gap-fill setlists: [Noah Gorstein truckin-through-time](https://noahgorstein.com/blog/truckin-through-time/) SQLite (~983 shows not in gdshowsdb alone)
- Curated overlays: `data/seed/` (personnel with intervals is authoritative — online dead.net/Wikipedia personnel skipped when `personnel.json` present)
- Bibliography: numbered markdown + `docs/manuscript/references.bib` merged offline (`bibliography_combined`)
- Lyric pointers: CMU `dead-lyrics.html` index (no lyric text); seed themes/lyricists overlay matching `song_slug`; dead.net song pages for catalog songs still missing a URL
- Optional online: Internet Archive LMA (unlimited with `--archival-max`), Alex Allan / whitegum index, dead.net roster, **Wikipedia** discography/members; CMU setlists (primary + Wayback mirrors — currently 404 / wrapper-only); **truckin-through-time** SQLite download; dead.net `/songs` HTML (often 403 — gap-fill uses constructed `/song/{slug}` URLs); Grateful Stats API when `GRATEFULSTATS_API_KEY` is set; Setlist.fm API when `SETLISTFM_API_KEY` is set (`setlistfm_max_pages=0` = full pagination)

## CI policy

Tests and coverage gates use **`data/seed/`** only (`GRATEFUL_DATA_TIER=seed`,
default). Archival smoke tests (`tests/test_archival_smoke.py`) run structural
checks when this directory is present; they do not pin entity counts.
