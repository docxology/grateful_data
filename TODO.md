# TODO — Improvement Roadmap

This roadmap is for upcoming work only. Keep completed work in git history,
generated reports, and manuscript prose; keep this file focused on future
minor, medium, and large improvements that would materially improve the
compendium, manuscript, figures, dashboard, or reproducibility story.

## Operating Rules

- Preserve the no-lyrics/no-audio-bundling boundary unless a future section is
  explicitly an external-pipeline pointer.
- Keep volatile counts in generated variables or reports, not hard-coded prose.
- Bind every new quantitative claim to tests, report JSON, raw CSV/JSON output,
  or a figure-data export.
- Prefer improving existing modules and manuscript sections over creating a
  sprawling docs hub.
- Re-render after manuscript or visualization changes and verify the PDF, web
  manuscript, dashboard, figure validation, and unresolved-token checks.

## Minor Improvements

- Keep a post-render visual inspection habit: after substantial figure changes,
  inspect the mosaic and newly added panels at PDF-like size for clipped labels
  or text collisions before final validation.

## Medium Improvements

- Add an optional reviewer-facing figure checklist generated from
  `output/data/figures/index.json` so external reviewers can audit data source,
  statistic, exclusion rule, and claim class without opening the dashboard.

## Large Improvements

- Full archival refresh campaign: run an online candidate through
  `scripts/22_archival_refresh_diff.py`, review the JSON/Markdown delta, and
  only then decide whether to replace the committed archival snapshot.
- External audio-feature pipeline: implement the external runner described by
  `output/data/external/pipeline_contract.json`, keeping all caches outside the
  repository and exporting only permitted metadata.
- External lyric-analysis pipeline: implement the external annotation runner
  described by `output/data/external/pipeline_contract.json`, keeping lyric
  text/excerpts/transcripts out of the repository.
- Promotion execution: if explicitly requested, move the project from
  `working/` to `active/`, run the template-wide render, and ensure it does not
  degrade sibling projects or public-template boundaries.

## Completed By Release-Prep Pass

- Added `scripts/20_validate_publication_outputs.py` for PDF/HTML/dashboard,
  token, citation, figure-validation, completeness, figure-data, raw-link,
  provenance, external-manifest, explorer, and dossier checks.
- Added `scripts/21_release_prep.py` with dry-run command ordering, archival
  pipeline/test/render/HTML-postprocess/validator orchestration, and
  `output/reports/release_prep.json`.
- Added non-destructive `scripts/22_archival_refresh_diff.py`; candidates live
  under `output/refresh/` or a provided directory and never overwrite
  `data/archival/`.
- Added sidecar provenance exports, CLI provenance lookup, expanded
  reconciliation buckets, and first-principles ledger links to manuscript
  section, figure, report key, test file, and claim status.
- Added pointer-only external manifests, static explorer generation,
  peer-review dossier generation, dashboard claim-ledger table, and
  promotion-readiness report output.

## Completed By Sensitivity/Explorer Pass

- Added transition sensitivity under `analysis_report.json` for support
  thresholds, segment-marker inclusion/exclusion, and era-specific transition
  summaries.
- Added repertoire top-N sensitivity under `analysis_report.json` for
  performance share, within-cut concentration, and era coverage across
  alternate top-N cuts.
- Added venue identity review rows under `analysis_report.json`, including
  conservative alias decisions and negative controls.
- Upgraded the static explorer with sortable table headers, URL-state filters,
  and filtered CSV download while staying plain HTML/CSS/JS.
- Added `output/data/external/pipeline_contract.json` to specify allowed
  inputs/outputs for future pointer-only audio-feature and lyric-annotation
  workflows.
- Synced README/AGENTS/reproducibility guidance and added short command-line
  examples for inspecting provenance, figure-data, validation, and sensitivity
  reports.

## Completed By Statistics/Visualization Sprint

- Added auditable figure registry fields for data source, statistic, exclusion
  rule, and claim class, and propagated them into dashboard cards and
  `output/data/figures/index.json`.
- Added publication figures and raw CSV/JSON exports for transition support
  sensitivity, repertoire top-N sensitivity, and venue identity review.
- Updated transition, stationary, association, and co-occurrence publication
  views to exclude generic segment markers, with marker-inclusive sensitivity
  shown explicitly.
- Restyled the performance distribution, repertoire embedding, release
  timeline, era heatmap, and mosaic for better PDF-scale readability.
- Upgraded the static explorer to v3 with figure rows and related
  figure/provenance links while remaining plain HTML/CSS/JS.
- Tightened results captions and manuscript limitations, normalized legacy
  BibTeX URL wrappers, and synced README/AGENTS/reproducibility guidance.

## Update Cadence

- Review this file after each substantial pipeline or manuscript pass.
- Delete items that are completed and evidenced elsewhere.
- Split vague items into testable tasks before implementation.
- Add new items only when they have a clear artifact, validation path, or
  manuscript-quality payoff.

## Workflowz review — 2026-11-10

- [ ] **WFZ-GD-001 — Make fallback venue geocoding reproducible across processes** — **P2** — `src/ingest/geo_enrich.py:106` describes a deterministic non-US/unknown-country fallback, but `src/ingest/geo_enrich.py:107` uses Python’s per-process randomized `hash()` and `src/ingest/geo_enrich.py:111` derives latitude from it. Replace process-random hashing with a stable defined digest for these fallback rows while retaining real coordinates and existing output shape. **Acceptance probe:** from the repository root, run the geo-enrichment fallback path for the same non-US/unknown-country venue in two fresh Python processes with different, fixed `PYTHONHASHSEED` values and assert that both exported rows (especially latitude/longitude) are byte-for-byte equal; assert actual US-state and non-US known-coordinate inputs remain unchanged. Add that two-process case to the geo-enrichment behavior tests. **Dependencies/constraints:** inspect the full function and existing callers before editing; do not change bundled lyric/audio boundaries or invent geographic coordinates, and keep the explicitly approximate fallback status clear in reports.
