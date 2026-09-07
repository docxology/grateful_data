# scripts/

Thin orchestrator scripts (ingest, analysis runs, figure/web/PDF generation).
Each script does argparse, path bootstrap (`_bootstrap.ensure_project_root`),
and a single delegated call into a `src/` entrypoint; all business, data, plot,
and analysis logic lives in `src/` and is tested under `tests/`.

## Inventory

| Script | Purpose | Delegates to | Command |
|---|---|---|---|
| `00_fetch_sources.py` | Optional online/vendor fetch + archival snapshot build | `src.ingest.*` (`fetch_*`, `merge_sources`, `write_archival_seed`) | `uv run python scripts/00_fetch_sources.py --online --archival-max` |
| `01_build_compendium.py` | Reconciled compendium dump | `src.seed.load_seed_compendium` | `uv run python scripts/01_build_compendium.py` |
| `02_analyze.py` | Descriptive + transitions report | `src.analysis.*` | `uv run python scripts/02_analyze.py` |
| `03_category_theory.py` | Functor laws + spans report | `src.cattheory.*` | `uv run python scripts/03_category_theory.py` |
| `04_figures.py` | Core figures | `src.viz.figures.render_group("core")` | `uv run python scripts/04_figures.py` |
| `05_extended_figures.py` | Extended figures | `src.viz.figures.render_group("extended")` | `uv run python scripts/05_extended_figures.py` |
| `06_mosaic.py` | Total mosaic PNG | `src.viz.compose.save_mosaic` | `uv run python scripts/06_mosaic.py` |
| `07_dashboard.py` | Static HTML dashboard | `src.reporting.dashboard.write_dashboard` | `uv run python scripts/07_dashboard.py` |
| `08_more_figures.py` | Supplementary figures | `src.viz.figures.render_group("more")` | `uv run python scripts/08_more_figures.py` |
| `09_song_pages.py` | Per-song markdown pages | `src.reporting.song_pages.write_song_pages` | `uv run python scripts/09_song_pages.py` |
| `10_alluvial.py` | Composer → song → era alluvial | `src.viz.alluvial.save_alluvial` | `uv run python scripts/10_alluvial.py` |
| `11_entity_pages.py` | Era/venue/person pages | `src.reporting.entity_pages.write_entity_pages` | `uv run python scripts/11_entity_pages.py` |
| `12_summary_report.py` | One-page extent report | `src.analysis.*`, `src.honesty.HonestyBoundary` | `uv run python scripts/12_summary_report.py` |
| `13_audit_completeness.py` | Completeness audit (0 dangling refs) | `src.audit.audit_completeness` | `uv run python scripts/13_audit_completeness.py` |
| `14_validate_figures.py` | Figure existence + non-blank validation | `src.viz.validate.validate_figures` | `uv run python scripts/14_validate_figures.py` |
| `15_export_raw.py` | Raw entity CSV + JSON export | `src.export.export_all` | `uv run python scripts/15_export_raw.py` |
| `16_archival_bundle.py` | Archival manifest + SHA-256 + tarball | `src.export.export_all` | `uv run python scripts/16_archival_bundle.py` |
| `17_reconcile_sources.py` | Cross-source reconciliation report | `src.integration.source_reconciliation` | `uv run python scripts/17_reconcile_sources.py` |
| `18_export_figure_data.py` | Figure CSV/JSON datasets | `src.viz.datasets.export_figure_datasets` | `uv run python scripts/18_export_figure_data.py` |
| `19_first_principles_review.py` | Claim/evidence ledger | `src.analysis.first_principles.write_review` | `uv run python scripts/19_first_principles_review.py` |
| `20_validate_publication_outputs.py` | Publication guardrails | `src.viz.figures` registry + local checks | `uv run python scripts/20_validate_publication_outputs.py --strict` |
| `21_release_prep.py` | Release-prep gate (run/dry-run) | `src.reporting.release_prep` (`build_steps`, `run_step`, `postprocess_html`, `resolve_template_root`) | `uv run python scripts/21_release_prep.py --dry-run` |
| `22_archival_refresh_diff.py` | Non-destructive archival diff | local diff logic over `data/archival/` | `uv run python scripts/22_archival_refresh_diff.py` |
| `23_export_provenance.py` | Sidecar provenance export | `src.provenance.write_provenance` | `uv run python scripts/23_export_provenance.py` |
| `24_external_manifests.py` | Pointer-only external manifests | `src.external_manifests.write_external_manifests` | `uv run python scripts/24_external_manifests.py` |
| `25_generate_explorer.py` | Static explorer site | `src.reporting.explorer.write_explorer` | `uv run python scripts/25_generate_explorer.py` |
| `26_peer_review_dossier.py` | Reviewer dossier | `src.reporting.peer_review.write_peer_review_dossier` | `uv run python scripts/26_peer_review_dossier.py` |
| `27_promotion_readiness.py` | Readiness report (no promotion) | local checks over repo layout | `uv run python scripts/27_promotion_readiness.py` |
| `99_pipeline.py` | Full stage-list pipeline | `runpy` over the numbered scripts above | `uv run python scripts/99_pipeline.py --tier archival` |
| `z_generate_manuscript_variables.py` | Manuscript variables + template hydration | `src.reporting.manuscript.main` | `GRATEFUL_DATA_TIER=archival uv run python scripts/z_generate_manuscript_variables.py` |
| `__init__.py` | Package marker | — | — |
| `_bootstrap.py` | Shared sys.path + headless matplotlib bootstrap | — | imported by every script |

See `AGENTS.md` for the thin-orchestrator contract. Stage order and pipeline
details live in the repo-root `AGENTS.md`.
