# AGENTS — grateful_data

Module-by-module orientation for contributors and agents.

## Project status

Self-contained project (`docxology/grateful_data`); every command below runs
from the repository root. No `infrastructure/` imports by design. Documentation
lives in this file and [`README.md`](README.md) (no separate `docs/` 12-file
hub).

## Architecture (two-layer, thin orchestrator)

- `src/` — pure logic: schema, source parsers, integration, analysis, category theory, visualization panels.
- `scripts/` — thin orchestrators that load data, call `src/`, write outputs.
- `tests/` — real fixtures, no mocks, 90%+ coverage on `src/`.
- `data/seed/` — CI demonstrator JSON fixtures (83 shows).
- `data/archival/` — committed full gdshowsdb snapshot + truckin gap-fill (3,341 shows; includes `performances.json`).
- `data/vendor/` — gitignored upstream caches (`gdshowsdb/`, `cmu/`, `whitegum/`, `dead_net/`, `wikipedia/`).
- `docs/manuscript/` — markdown sections + `references.bib`.

Tier selection: `GRATEFUL_DATA_TIER=seed|archival` or `scripts/99_pipeline.py --tier …`
(default `seed`). See `src/tier.py`.

Load path (single gate):

```
assert_valid (validation.py)
  → seed_bundle + source parsers
  → build_compendium
  → HonestyBoundary (raw JSON + compendium)
```

## Module map

| Module | Responsibility |
| --- | --- |
| `src/models.py` | Dataclass schema; `normalize_slug`, `canonical_song_id`, `canonical_show_id`. |
| `src/seed.py` | Bundled-seed loader orchestrator (`resolve_seed_dir()`). |
| `src/tier.py` | `GRATEFUL_DATA_TIER` → `data/seed/` vs `data/archival/`. |
| `src/ingest/` | Online fetch (`fetch_*`), gdshowsdb YAML load, merge, `write_archival_seed`. |
| `src/ingest/fetch_bibliography.py` | Parse numbered bibliography MD + inline links + DOIs + `docs/manuscript/references.bib`. |
| `src/ingest/fetch_truckin_db.py` | Download/parse truckin-through-time SQLite for setlist gap-fill. |
| `src/ingest/fetch_dead_net_songs.py` | dead.net `/songs` HTML scrape → lyric pointer URLs. |
| `src/ingest/fetch_gratefulstats.py` | Optional Grateful Stats API smoke probe (`GRATEFULSTATS_API_KEY`). |
| `src/ingest/lyric_pointer_enrich.py` | Curated theme/lyricist overlay, song-catalog propagation, dead.net gap-fill. |
| `src/integration/source_reconciliation.py` | Gap-fill ingest stats, contribution counters, ambiguity buckets, and venue-alias collision summaries. |
| `src/validation.py` | Seed JSON shape validator (`SEED_FILE_CONTRACT`, optional `performances.json`); called at load. |
| `src/honesty.py` | Runtime honesty boundary (no lyric text, pointer-only reviews, etc.). |
| `src/provenance.py` | Sidecar provenance records and CSV/JSON export; schema stays frozen. |
| `src/external_manifests.py` | Pointer-only audio/lyric manifest generation and protected-content rejection. |
| `src/cli.py` | Query CLI over a loaded compendium, including `provenance <entity_type> <key>`. |
| `src/sources/seed_bundle.py` | Parsers for bundled seed JSON records. |
| `src/sources/setlistfm.py` | Parse Setlist.fm JSON show payloads. |
| `src/sources/setlist_program.py` | Parse Setlists.net "SetList Program" records. |
| `src/sources/cmu_setlists.py` | Parse Mark Leone CMU setlist archive line format. |
| `src/sources/gdsets.py` | Parse GDsets memorabilia + setlist records. |
| `src/sources/gdshowsdb.py` | Parse the gdshowsdb relational dump. |
| `src/sources/internet_archive.py` | Parse Internet Archive Live Music Archive metadata. |
| `src/sources/alex_allan.py` | Parse Alex Allan / whitegum song-finder index. |
| `src/sources/dead_net.py` | Parse dead.net band/personnel snippets. |
| `src/sources/wikipedia.py` | Parse Wikipedia discography + member entries. |
| `src/integration/reconcile.py` | Merge across sources; build `Compendium`. |
| `src/integration/aliases.py` | Song alias canonicalization map. |
| `src/analysis/stats.py` | Top-line counts and top-song tallies. |
| `src/analysis/distributions.py` | Robust percentiles, Gini/Pareto concentration, bootstrap intervals, performance-row distributions. |
| `src/analysis/exploratory.py` | Era-by-song matrices, centered SVD embedding, deterministic exploratory clusters. |
| `src/analysis/first_principles.py` | Claim/evidence ledger: hard constraints, assumptions, validation artifacts, and interpretation limits. |
| `src/analysis/repertoire.py` | Catalog coverage, lifespans, era turnover, and top-N repertoire sensitivity. |
| `src/analysis/cooccurrence.py` | Show-by-song co-occurrence matrix. |
| `src/analysis/transitions.py` | Setlist Markov chain transitions, FDR screen, and support/segment/era sensitivity diagnostics. |
| `src/analysis/timeseries.py` | Performances over time. |
| `src/analysis/network.py` | Venue + personnel multipartite graph metrics. |
| `src/analysis/composers.py` | Composer attribution counts. |
| `src/analysis/lyrics.py` | Lyric theme frequencies from pointers. |
| `src/analysis/reviews.py` | Review sentiment aggregates. |
| `src/analysis/segues.py` | Segue edge extraction. |
| `src/analysis/eras.py` | Era labels and density heatmaps. |
| `src/analysis/geo.py` | Venue geo lookup from seed. |
| `src/analysis/venues.py` | Conservative venue identity review, alias decisions, and negative controls. |
| `src/analysis/personnel_timeline.py` | Gantt bars and lineup diversity. |
| `src/analysis/positions.py` | Set-position distribution. |
| `src/analysis/tours.py` | Tour show counts. |
| `src/analysis/centrality.py` | Co-occurrence eigenvector centrality. |
| `src/analysis/stationary.py` | Markov stationary distribution. |
| `src/analysis/bustouts.py` | Recurrence-gap ("bustout") analytics — seed-relative max gap between successive plays + rarities. |
| `src/cattheory/categories.py` | `Category` class; base categories. |
| `src/cattheory/functors.py` | `setlist_functor`, `lineup_functor`, `active_lineup_presheaf`, `is_monotone`. |
| `src/cattheory/spans.py` | Performance-as-span construction. |
| `src/cattheory/enriched.py` | Weight-enriched morphisms. |
| `src/cattheory/natural.py` | Cardinality natural transformation checks. |
| `src/cattheory/yoneda.py` | Representable presheaf embedding. |
| `src/cattheory/opposite.py` | Opposite-category helpers. |
| `src/viz/style.py` | Shared colors, DPI, figure sizes, provenance footer. |
| `src/viz/panels.py` | Reusable matplotlib panel builders (`draw_*`, `save_figure`). |
| `src/viz/figures.py` | **Figure registry SSOT** — `FIGURE_SPECS`, `EXPECTED_FILENAMES`, `DASHBOARD_FIGURES`, figure docs metadata, `render_group`, `render_one`. |
| `src/viz/datasets.py` | Registry-backed CSV/JSON datasets and documented figure-data index rows for rendered figure panels. |
| `src/viz/compose.py` | Total mosaic composition (delegates to `panels.draw_*`). |
| `src/viz/alluvial.py` | Composer → song → era alluvial diagram. |
| `src/viz/validate.py` | Figure existence + non-blank validation. |
| `src/audit.py` | Data-completeness audit (`audit_completeness`). |
| `src/export.py` | Raw CSV/JSON export of every entity. |
| `src/reporting/dashboard.py` | HTML dashboard builder (`build_dashboard_html`, `write_dashboard`). |
| `src/reporting/entity_pages.py` | Era/venue/person markdown pages. |
| `src/reporting/explorer.py` | Plain static explorer over exported show/song/venue/segue/figure/claim/provenance data with URL-state filters, sorting, related links, and CSV download. |
| `src/reporting/peer_review.py` | Reviewer dossier mapping claim families to reports, figures, tests, and citations. |
| `src/reporting/song_pages.py` | Per-song markdown pages. |
| `src/reporting/manuscript.py` | Manuscript variable derivation, template-root discovery (`find_template_root`), and `output/manuscript/` hydration. |
| `src/reporting/release_prep.py` | Release-prep gate logic: step plan (`build_steps`), subprocess runner, HTML postprocess, template-root resolution. |
| `scripts/_bootstrap.py` | Shared `sys.path` + headless matplotlib setup for scripts. |

## Category-theory report keys

`scripts/03_category_theory.py` writes `output/reports/category_theory_report.json`:

- `setlist_functor monotone` / `lineup_functor monotone` — expect `true` on seed.
- `active_lineup_presheaf expected_non_monotone` — expect `true` (Pigpen witness).
- `active_lineup_presheaf monotone` — deprecated alias; expect `false`.

## Test-coverage gate

```bash
uv run --extra dev pytest tests/ --cov=src --cov-fail-under=90
```

## Pipeline

```bash
uv run python scripts/99_pipeline.py
```

Stage order (`99_pipeline.py`):

| Stage | Script | Role |
| --- | --- | --- |
| 0 | `00_fetch_sources.py` | `--online --archival-max` → `data/archival/`; **gdshowsdb** + **truckin** gap-fill; **maximinus** reviews; **bibliography** (`*.md` + `docs/manuscript/references.bib`); **CMU dead-lyrics** pointers; **dead.net** lyric gap-fill; IA LMA; Setlist.fm / Grateful Stats when keyed |
| 1 | `01_build_compendium.py` | CSV + JSON compendium |
| 2 | `02_analyze.py` | Descriptive + transitions report |
| 3 | `03_category_theory.py` | Functor laws + spans report |
| 4 | `13_audit_completeness.py` | Completeness audit JSON (0 dangling hard refs) |
| 5 | `19_first_principles_review.py` | Claim/evidence ledger JSON + CSV |
| 6 | `15_export_raw.py` | Raw entity CSV + JSON export |
| 6b | `16_archival_bundle.py` | Archival tier only: manifest + SHA-256 + tarball |
| 6c | `17_reconcile_sources.py` | Archival tier only: `output/reports/source_reconciliation.json` (completeness + ingest stats) |
| 7 | `23_export_provenance.py` | Sidecar provenance CSV/JSON under `output/data/provenance/` |
| 8 | `04_figures.py` | Core figures via `render_group("core")` |
| 9 | `05_extended_figures.py` | Extended figures via `render_group("extended")` |
| 10 | `06_mosaic.py` | Total mosaic PNG |
| 11 | `08_more_figures.py` | Supplementary figures via `render_group("more")` |
| 12 | `10_alluvial.py` | Alluvial/set-flow figure |
| 13 | `18_export_figure_data.py` | Registry-backed figure CSV + JSON datasets plus data-source/statistic/exclusion/claim-class index rows under `output/data/figures/` |
| 14 | `07_dashboard.py` | Sectioned static HTML dashboard with raw figure-data links, registry metadata, and claim-ledger table |
| 15 | `24_external_manifests.py` | Pointer-only audio/lyric manifests under `output/data/external/` |
| 16 | `25_generate_explorer.py` | Plain static explorer under `output/explorer/` |
| 17 | `14_validate_figures.py` | Validates all figures against `EXPECTED_FILENAMES` |
| 18 | `26_peer_review_dossier.py` | Reviewer dossier JSON/Markdown under `output/reports/` |
| 19 | `27_promotion_readiness.py` | Readiness report only; does not move lifecycle folders |
| 20 | `z_generate_manuscript_variables.py` | Archival tier only: `output/data/manuscript_variables.json` |

### Optional ingest credentials

| Variable | Effect |
| --- | --- |
| `SETLISTFM_API_KEY` | Setlist.fm pagination overlay (`setlistfm_max_pages=0` = unlimited with `--archival-max`) |
| `GRATEFULSTATS_API_KEY` | Grateful Stats REST smoke citation when API reachable |
| `GRATEFULSTATS_API_BASE` | Override API base (default `https://www.gratefulstats.com/api`) |

Figure filenames, dashboard links, and validation expected-set all derive from
`src/viz/figures.py` — do not duplicate lists in scripts.

Additional scripts (not in default pipeline): `09_song_pages.py`,
`11_entity_pages.py`, `12_summary_report.py`, `20_validate_publication_outputs.py`,
`21_release_prep.py`, `22_archival_refresh_diff.py`.

Publication validator:

```bash
uv run python scripts/20_validate_publication_outputs.py --strict
```

Release-prep dry run:

```bash
uv run python scripts/21_release_prep.py --dry-run
```

Archival refresh diff is non-destructive: `scripts/22_archival_refresh_diff.py`
compares a candidate under `output/refresh/` or a provided directory against
`data/archival/` and never overwrites the committed archival snapshot.

## Manuscript PDF

`99_pipeline.py` is the **analysis** pipeline (data → figures → reports) and is
deliberately free of `infrastructure/` coupling. Manuscript → PDF rendering is
a template-level concern, run from the template root via the shared renderer:

```bash
cd /path/to/grateful_data
GRATEFUL_DATA_TIER=archival uv run python scripts/z_generate_manuscript_variables.py
cd /path/to/template
uv run python scripts/03_render_pdf.py --project grateful_data
```

This performs the multi-pass LaTeX + bibliography build and writes
`output/pdf/grateful_data_combined.pdf` (citations from `references.bib`
resolve in the rendered output) plus per-section slide PDFs under
`output/slides/`. `domain_profile.yaml` declares `manuscript_pdf` as an
expected output and `manuscript_citations_resolve` as a review gate; this is
the command that satisfies both.

## Manuscript

`docs/manuscript/` follows the template format. `references.bib` carries surveyed
sources. The manuscript distinguishes seed-data claims (audited, in-repo)
from full-corpus scaling claims. Repeated caveats should point to the
first-principles ledger rather than duplicating long limitations prose; figure
captions should state data source, statistic, exclusion rule, and claim class
when relevant.
