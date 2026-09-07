# AGENTS: `scripts/` — Thin Orchestrator Contract

Technical specification for this project's analysis scripts. Repo-wide policy:
see the root [`AGENTS.md`](../AGENTS.md).

## Design Contract

- Scripts are orchestration only: argparse, path bootstrap
  (`_bootstrap.ensure_project_root`), logging, and a single delegated call into
  a `src/` entrypoint.
- Business/data/plot/analysis logic lives in `src/` (importable + tested);
  never inline it in a script.
- Shared bootstrap: import `ensure_project_root` from `_bootstrap`; do not
  hand-roll `sys.path.insert(0, str(ROOT))`.
- Figure filenames, dashboard links, and validation expected-sets derive from
  `src/viz/figures.py` — do not duplicate lists here.
- Reusable script behavior must be covered by tests in `tests/`; tests import
  the `src/` modules, not script internals.
- Template-repo discovery (`TEMPLATE_REPO_ROOT` env or ancestor walk) lives in
  `src.reporting.manuscript.find_template_root`; scripts must not hardcode
  machine-specific absolute paths.

## Script Inventory

| Script | Pattern | Delegates to | Output |
|--------|---------|--------------|--------|
| `00_fetch_sources.py` | Stage 0 Thin Orchestrator | `src.ingest.*` | `data/archival/`, `data/vendor/`, fetch manifest |
| `01_build_compendium.py` | Stage 1 Thin Orchestrator | `src.seed` | `output/data/` compendium CSV+JSON |
| `02_analyze.py` | Stage 2 Thin Orchestrator | `src.analysis.*` | `output/reports/analysis_report.json` |
| `03_category_theory.py` | Stage 3 Thin Orchestrator | `src.cattheory.*` | `output/reports/category_theory_report.json` |
| `04_figures.py` | Stage 8 Thin Orchestrator | `src.viz.figures.render_group` | core PNGs in `output/figures/` |
| `05_extended_figures.py` | Stage 9 Thin Orchestrator | `src.viz.figures.render_group` | extended PNGs |
| `06_mosaic.py` | Stage 10 Thin Orchestrator | `src.viz.compose.save_mosaic` | `output/figures/mosaic_total.png` |
| `07_dashboard.py` | Stage 14 Thin Orchestrator | `src.reporting.dashboard` | `output/dashboard.html` |
| `08_more_figures.py` | Stage 11 Thin Orchestrator | `src.viz.figures.render_group` | supplementary PNGs |
| `09_song_pages.py` | Optional Thin Orchestrator | `src.reporting.song_pages` | `output/pages/songs/` |
| `10_alluvial.py` | Stage 12 Thin Orchestrator | `src.viz.alluvial` | alluvial PNG |
| `11_entity_pages.py` | Optional Thin Orchestrator | `src.reporting.entity_pages` | `output/pages/` |
| `12_summary_report.py` | Optional Thin Orchestrator | `src.analysis.*`, `src.honesty` | `output/SUMMARY.md` |
| `13_audit_completeness.py` | Stage 4 Thin Orchestrator | `src.audit.audit_completeness` | `output/reports/completeness_audit.json` |
| `14_validate_figures.py` | Stage 17 Thin Orchestrator | `src.viz.validate` | figure validation report |
| `15_export_raw.py` | Stage 6 Thin Orchestrator | `src.export.export_all` | `output/data/raw/` |
| `16_archival_bundle.py` | Stage 6b Thin Orchestrator (archival) | `src.export` | manifest + SHA-256 + tarball |
| `17_reconcile_sources.py` | Stage 6c Thin Orchestrator (archival) | `src.integration.source_reconciliation` | `output/reports/source_reconciliation.json` |
| `18_export_figure_data.py` | Stage 13 Thin Orchestrator | `src.viz.datasets` | `output/data/figures/` |
| `19_first_principles_review.py` | Stage 5 Thin Orchestrator | `src.analysis.first_principles` | claim/evidence ledger JSON+CSV |
| `20_validate_publication_outputs.py` | Guardrail CLI | `src.viz.figures` + local checks | `output/reports/publication_validation.json` |
| `21_release_prep.py` | Guardrail CLI | `src.reporting.release_prep` | `output/reports/release_prep.json` |
| `22_archival_refresh_diff.py` | Guardrail CLI | local diff over `data/archival/` | refresh-diff report |
| `23_export_provenance.py` | Stage 7 Thin Orchestrator | `src.provenance` | `output/data/provenance/` |
| `24_external_manifests.py` | Stage 15 Thin Orchestrator | `src.external_manifests` | `output/data/external/` |
| `25_generate_explorer.py` | Stage 16 Thin Orchestrator | `src.reporting.explorer` | `output/explorer/` |
| `26_peer_review_dossier.py` | Stage 18 Thin Orchestrator | `src.reporting.peer_review` | dossier JSON+MD |
| `27_promotion_readiness.py` | Readiness report | local checks | `output/reports/promotion_readiness.json` |
| `99_pipeline.py` | Stage-list Orchestrator | `runpy` over numbered scripts | full analysis pipeline |
| `z_generate_manuscript_variables.py` | Stage 20 Thin Orchestrator (archival) | `src.reporting.manuscript.main` | `output/data/manuscript_variables.json`, `output/manuscript/` |
| `__init__.py` | Package marker | — | — |
| `_bootstrap.py` | Shared bootstrap helper | — | sys.path + Agg matplotlib |

## Gotchas

- Tier selection is global: `GRATEFUL_DATA_TIER=seed|archival` (default
  `seed`); `99_pipeline.py --tier` sets it per stage.
- Stage order for the default pipeline: see root `AGENTS.md` — do not
  renumber scripts casually; `99_pipeline.py` pins the order.
