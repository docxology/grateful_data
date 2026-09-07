---
project: grateful_data
task: Confirm full real data on all shows; make all figures work, improve, validate; export raw data
effort: E5
phase: complete
progress: 20/20
mode: algorithm
started: 2026-05-28
updated: 2026-05-30
iteration: 9
---

# ISA — Grateful Data Compendium ("The Music Never Stopped")

> Project ISA: the long-lived system of record for this compendium. Iteration 2
> (2026-05-28) re-scoped to the live ask after the repo's convergent automation
> closed iteration-1's lint/mypy/coverage debt. Prior history lives in git +
> the manuscript + the iteration-1 changelog entry below.

## Problem

Iteration 1's quality debt is **already closed** (verified this session: 163
tests / 98.15% coverage / `ruff` clean / `mypy` clean / honesty green — the
27 ruff + 43 mypy + 3 coverage soft-spots no longer exist). The live ask is
different and unmet:

- **Data completeness is asserted but not *proven by a probe*.** Nothing emits
  a machine-readable report confirming every show carries full, real,
  internally-consistent data (venue resolves, every performed song resolves,
  every show has a setlist, geo/review/recording cross-refs resolve).
- **Figures render but do not *validate*.** 24 PNGs are produced; no step
  checks each one exists, is non-trivial (non-blank, adequate dimensions), and
  matches the expected manifest. A silently-blank figure would ship green.
- **Figures are functional but plain** — inconsistent provenance labelling, no
  uniform "seed n=83" footer, no shared styling pass.
- **Raw-data export is partial** — only `shows/performances/songs` CSV + a
  counts-only `compendium.json`. Venues, personnel, recordings, releases,
  citations, reviews, lyric-pointers, geo, segues are not exported as raw data.

## Vision

A reviewer runs one command and sees: a completeness report that *proves* all
83 shows hold full real data with zero dangling references; a figure-validation
report that confirms every expected figure rendered and is non-degenerate; a
`raw/` export directory with every entity as both CSV and JSON; and improved,
uniformly-labelled figures — all over the real audited seed, honesty boundary
intact, no fabricated record anywhere. The corpus scope (83 curated real shows
vs. the ~2,318-show full archive) is stated honestly, never blurred.

## Out of Scope

- No new fabricated data: no lyric text, audio features, invented shows,
  citations, or reviews. Every export/audit computes over the existing seed.
- No online fetching turned on by default in CI (`00_fetch_sources.py` is opt-in via `--online`).
- No claim that 83 shows == the complete Grateful Dead corpus; coverage scope
  is reported honestly.
- No restructuring of the manuscript or the category-theory thesis.
- Not publishing/releasing the repo (local-only rotating project).

## Principles

- **Honesty boundary is non-negotiable** — `assert_honesty` stays green; the
  completeness report states curated-corpus scope explicitly.
- **A claim ships only with a probe** — "data is complete", "figures work",
  "figures validate" each become a runtime check emitting an artifact.
- **Thin orchestrator** — audit/validation/export logic lives in `src/`,
  scripts only coordinate I/O.
- **Determinism** — fixed inputs produce byte-stable outputs; figures headless.
- **No mocks** — tests use real seed fixtures and real computation.

## Constraints

- Python ≥3.10; deps numpy/matplotlib/pyyaml only.
- Coverage gate: `src/` ≥90% (currently 98.15%, must not regress).
- New modules carry ≥90% coverage from new tests.
- Pinned seed cardinalities (must not drift): shows 83, songs 88, personnel 14,
  venues 25, recordings 6, reviews 12, citations 26, releases 30,
  lyric_pointers 25, venue_geo 25, performances 341.
- Category-theory invariants pinned: `setlist_functor monotone`=true,
  `lineup_functor monotone`=true, `active_lineup_presheaf` non-monotone (Pigpen
  witness)=true.
- All tests + pipeline run network-free on the bundled seed.

## Goal

Add and wire (a) a **data-completeness audit** that proves every show holds full
real, internally-consistent data and emits a report; (b) a **figure-validation**
module + report that confirms every expected figure rendered and is
non-degenerate; (c) a **shared figure-improvement** pass (uniform provenance
footer + styling); (d) a **complete raw-data export** of every entity to CSV +
JSON — all over the real seed, honesty intact, with the full gate (163+ tests
≥90% cov, ruff 0, mypy 0, pipeline exit 0, honesty green) re-run + artifact-
backed, plus an advisor call and a cross-vendor Forge audit before completion.

## Criteria

- [ ] ISC-1: `src/audit.py` provides `audit_completeness(comp)` returning a structured report (dataclass) over the compendium.
- [ ] ISC-2: Audit confirms every show's `venue_slug` resolves to a venue record (0 dangling) — probe asserts.
- [ ] ISC-3: Audit confirms every performed song resolves to a song record (0 dangling).
- [ ] ISC-4: Audit confirms every show has ≥1 performance (no empty setlist) — 83/83.
- [ ] ISC-5: Audit confirms every venue has geo coverage (25/25) and reports the percentage.
- [ ] ISC-6: Audit confirms every review/recording references a resolvable entity (0 dangling).
- [ ] ISC-7: Audit report states corpus scope honestly (curated n=83 vs full ~2,318) — no over-claim of "all shows ever".
- [ ] ISC-8: Script `13_audit_completeness.py` writes `output/reports/completeness_report.json` and exits 0.
- [ ] ISC-9: `src/audit.py` has ≥90% coverage from new tests in `tests/test_audit.py`.
- [ ] ISC-10: `src/viz/validate.py` provides `validate_figure(path)` checking existence, non-zero size, min dimensions, and non-blank pixel variance.
- [ ] ISC-11: `validate_figures(dir, expected)` returns per-figure pass/fail and flags any missing expected figure.
- [ ] ISC-12: Script `14_validate_figures.py` validates all rendered figures, writes `output/reports/figure_validation.json`, exits 0, and FAILS (non-zero) if any figure is missing/degenerate.
- [ ] ISC-13: Figure validation actually catches a degenerate figure — proven by a negative-control test feeding a blank/empty image.
- [ ] ISC-14: `src/viz/validate.py` has ≥90% coverage from new tests.
- [ ] ISC-15: Shared figure-improvement helper adds a uniform provenance footer ("seed compendium · n=83 shows · <date range>") applied across core figures.
- [ ] ISC-16: Improved figures still render deterministically and pass figure validation.
- [ ] ISC-17: Raw-data export writes every entity (shows, performances, songs, venues, personnel, recordings, releases, citations, reviews, lyric_pointers, venue_geo, segues) to `output/data/raw/<entity>.csv`.
- [ ] ISC-18: Raw-data export also writes a complete `output/data/raw/compendium_full.json` containing all records (not just counts).
- [ ] ISC-19: Export logic lives in `src/export.py` (thin orchestrator script `15_export_raw.py` calls it); `src/export.py` has ≥90% coverage.
- [ ] ISC-20: Exported CSV row counts equal the pinned seed cardinalities (round-trip integrity probe).
- [ ] ISC-21: New stages (13, 14, 15) are wired into `99_pipeline.py` and the full pipeline exits 0 end-to-end.
- [ ] ISC-22: Full test suite passes (163+ tests, count does not drop) at ≥90% (≥95% target) coverage.
- [ ] ISC-23: `assert_honesty` still passes; honesty grep finds no forbidden lyric/audio-feature keys in any new code or export.
- [ ] ISC-24: Pinned seed cardinalities + 3 category-theory invariants unchanged after all changes.
- [ ] ISC-25: Anti: no fabricated record, lyric text, audio-feature field, or "all 2,318 shows" over-claim introduced anywhere; no status-report-in-place-of-artifacts (every claim has a probe).
- [ ] ISC-26: Advisor consulted before complete (HARD E4) + cross-vendor Forge read-only audit run against the final artifact set; criticals addressed or surfaced.

## Test Strategy

| isc | type | check | threshold | tool |
| --- | --- | --- | --- | --- |
| ISC-1..7 | audit | report fields + 0 dangling | as stated | `pytest tests/test_audit.py` |
| ISC-8 | artifact | report JSON exists + exit 0 | exists | `python 13_…` / `Read` |
| ISC-9/14/19 | coverage | per-module % | ≥90% | `pytest --cov` |
| ISC-10..13 | validation | figure checks + negative control | catches blank | `pytest tests/test_figure_validation.py` |
| ISC-12 | artifact | validation JSON + non-zero on bad | exists/fails | `python 14_…` |
| ISC-15/16 | figure | footer present + deterministic + validates | pass | pipeline + validation |
| ISC-17/18/20 | export | files exist + row counts == cardinalities | exact | `python 15_…` + `pytest` |
| ISC-21 | pipeline | end-to-end exit code | 0 | `python 99_pipeline.py` |
| ISC-22/23/24 | gate | tests/cov/ruff/mypy/honesty/invariants | unchanged/green | full gate |
| ISC-26 | review | advisor + Forge verdict | no unaddressed critical | Inference advisor + Agent(Forge) |

## Features

| name | satisfies | depends_on | parallelizable |
| --- | --- | --- | --- |
| completeness-audit | ISC-1..9 | — | yes |
| figure-validation | ISC-10..14 | — | yes |
| figure-improve | ISC-15,16 | figure-validation | partial |
| raw-export | ISC-17..20 | — | yes |
| pipeline-wire | ISC-21 | all above | no |
| full-gate-rerun | ISC-22,23,24,25 | pipeline-wire | no |
| review | ISC-26 | full-gate-rerun | no |

## Decisions

- 2026-05-28 (iter-2): Task DIVERGED from iter-1 (lint/mypy/coverage/PDF) to the live ask (confirm data completeness + figures work/improve/validate + export raw). Re-scoped ISCs fresh; iter-1 debt verified already-closed by the repo's convergent automation, so re-grinding it would be wasted work (R15).
- 2026-05-28: "all real full data on all shows" resolved (FirstPrinciples) to *referential completeness over the curated 83-show corpus* — NOT fabricating the full ~2,318-show archive. The honesty boundary + Out-of-Scope forbid invented shows; the full-corpus path stays the documented opt-in `00_fetch_sources.py` stub. Corpus scope reported honestly in the audit.
- 2026-05-28: Primary authors all edits (template repo blocks subagent Edit/Write — memory `subagent-write-denied-use-bash-python`); Forge used read-only in VERIFY (E4 mandatory).
- 2026-05-28: Caught a false-pass — bare `.venv/bin/python -m pytest` reports "No module named pytest" yet a naive bg wrapper called it exit 0 (memory `audit-verify-collection-not-just-exit`, `gotcha-premature-bash-background-notifications`). Authoritative invocation is `uv run --project .`.

## Changelog

- conjecture (2026-05-28, iter-2): the live ask is data-confirmation + figure-validation + figure-improvement + raw-export, each backed by a runtime probe and a report; refuted_by: n/a (in progress); learned: iter-1's debt was already auto-closed so the ISA had to be re-scoped to avoid a status-report-instead-of-work failure (today's dominant failure fingerprint); criterion_now: ISC-1..26.

## Verification

_(populated during EXECUTE/VERIFY)_

---

# Iteration 3 — Archival tier (committed gdshowsdb snapshot)

## Goal

Ship a **committed** full-corpus tier under `data/archival/` (~2,318 shows from
gdshowsdb YAML) while keeping `data/seed/` as the fast CI demonstrator (83
shows, pinned test counts unchanged).

## Criteria (archival-specific)

- [x] `src/ingest/` fetches/normalizes gdshowsdb + curated layers; `00_fetch_sources.py --online --write-archival` writes `data/archival/*.json` (including `performances.json` with `segue_into`).
- [x] `GRATEFUL_DATA_TIER=archival` (or `--tier archival`) loads `data/archival/`; seed tests remain on default tier.
- [x] Archival audit: `dangling_total == 0` on hard relations; setlist-empty gdshowsdb shows reported but not counted as dangling.
- [x] `99_pipeline.py --tier archival` exits 0; figure validation 24/24; `16_archival_bundle.py` writes manifest + tarball.
- [x] Manuscript uses `{{ARCHIVAL_*}}` tokens via `scripts/z_generate_manuscript_variables.py` before PDF render.
- [x] `tests/test_archival_smoke.py` structural probes when `data/archival/` present (no pinned full-corpus counts in CI).

## Verification (2026-05-29)

| Gate | Result |
| --- | --- |
| Seed CI | 222 tests, 90.76% `src/` coverage; pinned 83-show counts unchanged |
| Archival reload | 2,358 shows; 39,774 performances; 16,569 segue markers; 3,894 recordings |
| Audit | `dangling_total=0`, geo 100% (`output/reports/completeness_report.json`) |
| Figures | 24/24 (`output/reports/figure_validation.json`) |
| Fetch manifest | `output/data/fetch_manifest.json` — gdshowsdb, curated_seed, whitegum, dead.net, IA LMA; CMU 404 skipped; Setlist.fm skipped without API key |
| PDF | `output/grateful_data/pdf/grateful_data_combined.pdf` — validation 0 issues |
| Bundle | `output/archival/grateful_data_archival.tar.gz` + `manifest.json` |

## Decisions

- 2026-05-29: gdshowsdb date keys may include `/0` `/1` same-day disambiguators → `canonical_show_id(..., show_index=N)`.
- 2026-05-29: Category law checks use identity-only mode when `len(objects) > 120` (Date poset at archival scale).
- 2026-05-29: Curated review/recording slugs remapped onto gdshowsdb venue slugs by date + token overlap.
- 2026-05-29: Archival snapshot writes `performances.json` (authoritative performance table with `segue_into`) plus human-readable `shows.json` setlists; `show_index` preserved for same-day disambiguators.
- 2026-05-29: Secondary online adapters: whitegum, dead.net, Wikipedia (discography + members), Internet Archive LMA (`--ia-max-rows`, default 5000); CMU gap-fill when upstream HTML is reachable; Setlist.fm when `SETLISTFM_API_KEY` set.

## Changelog

- conjecture (2026-05-29, iter-3): dual-tier architecture separates CI determinism from full-corpus scholarship; refuted_by: n/a; learned: exhaustive Date-category `check_laws` is O(n⁴) at ~2k dates; criterion_now: archival pipeline + honest audit semantics.

---

# Iteration 4 — Archival-max ingest + tier-accurate figures/manuscript

## Goal

One documented **`--archival-max`** ingest profile (unlimited IA rows, full Setlist.fm
pagination when keyed), CMU mirror fallbacks, tier-aware figure titles/footers, and
registry-backed manuscript tokens so archival PDFs never say "curated seed".

## Criteria

- [x] `--archival-max` sets `ia-max-rows=0`, `setlistfm-max-pages=0`, `write-archival`, `online`.
- [x] CMU fetch tries primary + Internet Archive mirrors; skipped sources recorded in `build_report.json`.
- [x] `src/viz/style.py`: `resolve_tier()`, `tier_phrase()`, `overlay_phrase()`; panels/compose use tier labels.
- [x] `02_analyze.py` + `z_generate_manuscript_variables.py`: `TOP_SONG*`, `TIER_LABEL`, `CURATED_*_N`.
- [x] `docs/manuscript/04_results.md`: no hardcoded seed prose at archival render.
- [x] Tests: `test_viz_tier_labels.py`, `test_manuscript_variables.py`, fetch adapter pagination/CMU cache.

## Verification (2026-05-29, archival-max)

| Gate | Result |
| --- | --- |
| Seed CI | 232 tests, 90.83% `src/` coverage; pinned 83-show counts unchanged |
| Archival ingest | `--online --archival-max` → 2,358 shows; 39,774 performances; **7,215** recordings (IA unlimited); 259 releases (Wikipedia merge) |
| Audit | `dangling_total=0`, geo 100% |
| Figures | 24/24; archival panel titles use "archival" not "seed" |
| Manuscript vars | `TIER_LABEL=archival compendium`; `TOP_SONG=drums` (n=1777) |
| Fetch manifest | CMU all mirrors 404 skipped; Setlist.fm skipped without `SETLISTFM_API_KEY` |
| PDF | `grateful_data_combined.pdf` — validation 0 issues; no "curated seed" in `04_results.md` source |

## Decisions

- 2026-05-29: Reviews (12), citations (26), lyric pointers (25) remain curated overlays at archival tier — figures label via `overlay_phrase()`.
- 2026-05-29: `provenance_text(tier=None)` resolves from `GRATEFUL_DATA_TIER` / comp path (not hardcoded seed).

---

# Iteration 5 — "All the way through full real data" (2026-05-30)

## Goal

Run the **archival tier on the full real corpus** end-to-end (not the 83-show
seed), apply manuscript claim-verification + deep-research source verification,
and close every gate green.

## Work + Verification (2026-05-30)

| Gate / artifact | Result |
| --- | --- |
| Full archival pipeline `99_pipeline.py --tier archival` | exit 0; 3341 shows / 40757 performances / 7122 recordings / 912 venues / 645 songs |
| Completeness audit | `dangling_total=0`, geo 100%, `is_complete=true`; 282 setlist-empty early shows reported honestly (not dangling) |
| Figure validation | 24/24 non-degenerate (`figure_validation.json`) |
| Category-theory report | setlist/lineup functors monotone=true; presheaf non-monotone; Date+Show laws pass; cumulative setlist=449, lineup=14 |
| Raw export | 12 entities to `output/data/raw/*.csv` + `compendium_full.json` (13.6 MB); row counts == archival cardinalities (citations=114 confirmed via csv parse) |
| Manuscript PDF | re-rendered from archival vars; `infrastructure.validation.cli pdf` 0 issues; markdown + prerender clean |
| Test suite | 266 passed, **90.33%** src coverage (≥90 gate) |
| ruff / mypy | ruff clean; mypy Success (84 files) |
| Cross-vendor Forge audit (ISC-26) | **CERTIFY**, no CRITICAL/HIGH |

## Claim defect FOUND + FIXED (manuscript-claim-verification)

- `04_results.md` hardcoded "cumulative setlist cardinality **74** at the
  terminal date" — a STALE seed-tier value. Archival report says **449**.
  Fixed via the generated-variable mechanism: literal 74/14 → tokens
  `{{CUMULATIVE_SETLIST_CARD_END}}` / `{{CUMULATIVE_LINEUP_CARD_END}}`, sourced
  from `category_theory_report.json` in `z_generate_manuscript_variables.py`.
  Verified gone in the re-rendered PDF ("cardinality 449", zero "74").

## Gate regressions repaired

- `hypothesis` and `pytest-httpserver` were imported by tests but undeclared in
  `pyproject.toml` dev deps → `uv run --project .` dropped them, errored 4 tests,
  and pushed coverage below 90%. Declared both; 4 tests restored; coverage 90.33%.
- Re-ran ruff/mypy gate (had silently regressed in iter-3/4 ingest/archival code):
  fixed F821 `date` import (`internet_archive.py`), dict→Mapping invariance,
  `Any|None`→str notes coercion, `row`/`perf_row` redefinition, `Figure|None`→`Figure`,
  and matplotlib date-arg `Any`-binding. ruff 0 / mypy 0.

## Deep-research source verification

- Verified the one externally-cited numeric claim flagged by the evidence gate:
  "2617 SBD recordings of 15 songs" against the cited source README
  (`github.com/grateful-dead-live/fifteen-songs-dataset` — "2617 versions in
  total" across the 15 listed songs). ACCURATE / source-backed.
- Other evidence-gate flags (`0.72`, `-1`) confirmed as heuristic false
  positives: LaTeX `\textwidth` dimension and category-theory inverse-image
  exponent `\pi^{-1}` — not data claims. NOT fabricated into the registry.

## Decisions

- 2026-05-30: "full real data" = run the committed archival corpus (3341 shows)
  end-to-end. Did NOT re-fetch online (`--archival-max`); the on-disk snapshot
  was already the full real fetch from 2026-05-29. The online refresh remains the
  documented opt-in path.
- 2026-05-30: Stale-literal manuscript numbers are fixed via tokens, never
  hand-edited to a new literal — the token wiring fails closed (raises on
  unresolved `{{...}}`), so a future tier change can't silently ship a stale value.

## Changelog

- conjecture (2026-05-30, iter-5): the live ask was an end-to-end archival run
  + claim verification, not new features; refuted_by: n/a; learned: a hardcoded
  category-theory number (74) survived 4 iterations because no token bound it to
  the report — claim-verification at archival scale surfaced it; the lint/dep
  gate had silently regressed because `working/` projects are outside the
  template's public-scope CI; criterion_now: ISC-1..26 all green + Forge CERTIFY.
</content>
</invoke>

---

# Iteration 6 — Comprehensive review-and-improve (2026-05-30)

## Goal

Deeply review the whole project and add/improve methods, tests, docs,
visualization, manuscript, and refactors "as most intelligent" — without
breaking the honesty boundary, determinism, or the gate.

## Method

Two cross-vendor read-only review agents (Forge GPT-5.4 on science/cattheory;
Engineer Claude on viz/docs/refactor/manuscript) proposed ranked improvements;
all contestable claims were VERIFIED before acting (rejected the "manuscript
says 24 figures but registry=17" claim — registry is genuinely 24/now 25).

## Work landed

**Science correctness + honesty:** segment-marker module (drums/space/jam/
tuning/feedback) — excluded from the repertoire ranking (archival top song
corrected drums→`playing_in_the_band`), counts surfaced separately, markers
RETAINED in structural co-occurrence/transition/centrality analyses (drums→space
is real adjacency); `opener_frequency` min(position) fix (was order-dependent);
Markov per-row support + seeded within-show permutation null (2300 significant
at archival); centrality switched to Jaccard-association (raw counts just
re-derived frequency); new `repertoire.py` (catalog_coverage 69.6%/196 never
performed, era turnover, song lifespans); per-kind sentiment dispersion;
composer super-additivity documented.

**Category theory de-vacuumed (each with a negative control):** colimit now
checks the universal property (too-small-apex must fail), not subset-of-union;
large-category `check_laws` uses a seeded randomized associativity sampler at
2312 objects (was identity-only); faithful Yoneda over the Date poset
(`Nat(Hom(d,-),F)≅F(d)` with non-monotone negative control); span/setlist-functor
commutation as a checked property. Framed honestly (per advisor) as
encoding/sanity checks over a thin category, not deep theorems.

**Viz:** new `song_lifespans` figure (25th); centrality figure → association;
top-songs annotates excluded segments; geo/releases label caps for archival
scale.

**Manuscript/docs:** segment-marker honesty + Limitations + Data dictionary +
Licensing/provenance (incl. compilation-rights nuance per advisor); de-vacuumed
cattheory results written up; renamed leaked "Euphoric surprise" heading;
figure count tokenized (`{{N_FIGURES}}`); README 3341-ingested-vs-~2318-estimate
fixed; new report fields wired into analysis/cattheory JSON + manuscript tokens.

## Verification (2026-05-30)

| Gate | Result |
| --- | --- |
| Tests | **293 passed** (+27 new), **90.60%** src coverage |
| ruff / mypy | clean / Success (86 source files) |
| Archival pipeline | exit 0; 3341 shows / 40757 perfs; dangling=0; geo 100%; **25/25 figures** |
| Category report | colimit-UP, span-commutation, Yoneda all true; Date law_check=**sampled** ok |
| PDF | renders; markdown + prerender + PDF validation all 0 issues; no unresolved tokens |
| Cross-vendor Forge audit | **CERTIFY-WITH-RESIDUALS** → its one HIGH (marker-exclusion over-claim in Limitations/docstring) FIXED + re-verified |
| Advisor (E5) | flagged thin-poset over-claim + compilation-rights → both addressed in manuscript |

## Decisions

- 2026-05-30: Segment markers excluded only from *repertoire* rankings; kept in
  *structural* analyses (transitions/co-occurrence/centrality) because drums→space
  is genuine setlist adjacency. Forge caught the initial over-claim that all four
  excluded them; text now matches the code.
- 2026-05-30: Category-theory checks are honestly framed as encoding/sanity
  checks over a thin poset (advisor), not novel theorems; each carries a
  negative control so it is non-vacuous.

## Deferred (honestly noted, not done)

- panels.py `_ranked_barh`/`_labeled_heatmap` extraction + merge_sources split
  (refactors; byte-identity verification not yet run).
- Colorblind palette + pies→bars (deliberate pixel changes; needs review).
- Venue-alias canonicalization (Forge P0.1: Oakland complex split 6 ways) —
  high value but judgment-laden; left as a flagged limitation in §4.
- Related-work paragraph.

## Changelog

- conjecture (2026-05-30, iter-6): a mature green project still has high-value
  honest improvements — the headline "most-performed song" was a segment marker,
  several cattheory checks were tautologies, and centrality re-derived frequency;
  refuted_by: n/a; learned: red-team the honesty NARRATIVE too (the over-claim
  hid in the Limitations section I wrote to improve honesty); criterion_now: all
  gates green + Forge HIGH fixed + advisor points addressed.

---

# Iteration 7 — Venue data-quality: detect honestly, don't merge blindly (2026-05-30)

## Goal

Continue the comprehensive improvement pass; tackle the venue-duplication defect
deferred from iter-6 (Oakland Coliseum Arena split across 5 slugs / 132 shows),
plus the remaining deferred manuscript item (related work).

## The decision that mattered

Built a conservative, hand-verified `VENUE_ALIAS_MAP` (20 entries; canonical =
seed slug so the seed stays a no-op at 25 venues; negative controls keep
Fillmore W/E/Auditorium, Arena vs Stadium, MSG vs Felt Forum, Oakland Auditorium
vs Kaiser distinct). First wired it into `build_compendium` to actually merge —
it worked and passed negative controls, but collapsed **3341→3070 shows** and
40757→40612 performances. Checked the colliding same-date records: **setlist
Jaccard ≈ 0.05** (near-disjoint), NOT ≈1.0. So they are NOT clean duplicates —
and (advisor) the Dead routinely played **early/late shows same date**, so
near-disjoint same-date pairs are *equally consistent with two legitimate shows*
as with a split duplicate. The evidence cannot decide.

**REVERTED the mutation entirely** (reconcile.py + geo.py back to original) and
instead ship `src/analysis/venues.py::venue_duplication_report` — a NON-MUTATING
measurement: 912→892 collapsible slugs (20), **311 ambiguous same-date
collisions** (mean Jaccard 0.047), wired into `analysis_report.json` +
manuscript Limitations with exact tokens. Reframed from "probable duplicates"
(over-claim toward duplication) to "ambiguous" per advisor; noted the alias map
is precision-oriented (recall non-exhaustive → lower bound).

## Also landed

- Related-work section in `01_introduction.md` (existing citekeys only):
  integration-first + structure-first contribution vs prior single-source efforts.

## Verification (2026-05-30)

| Gate | Result |
| --- | --- |
| Tests | **299 passed** (+6 venue tests w/ negative controls), **90.66%** coverage |
| ruff / mypy | clean / Success (87 files) |
| Archival pipeline | exit 0; dangling=0; geo 100%; 25/25 figures; corpus UNMUTATED (3341/912/40757) |
| PDF / markdown / prerender | all 0 issues; no unresolved tokens |
| Forge cross-vendor audit | **CERTIFY-WITH-RESIDUALS** — revert confirmed correct + corpus self-consistent + no laundering; 2 prose miscounts ("six"→five slugs, "121"→132 shows) FIXED + re-derived from data |
| Advisor (E5) | confirmed detect-and-report was the right honesty call; caught the early/late-show over-claim → reframed to "ambiguous" + added recall caveat |

## Decisions

- 2026-05-30: Do NOT merge venues/shows. Near-disjoint same-date setlists are
  undecidable (split-duplicate vs legitimate early/late double-show); merging
  would launder an unprovable judgment into the corpus. Detect + report instead.
- 2026-05-30: Venue alias map is conservative/precision-oriented; reported
  collapse count is an explicit lower bound (recall non-exhaustive).

## Changelog

- conjecture (2026-05-30, iter-7): the venue duplication is real but entangled
  with show-level ambiguity; refuted_by: setlist-Jaccard 0.05 on collisions
  (refuted the "clean duplicate" hypothesis); learned: the honest deliverable was
  a measurement + a declined merge, and the advisor caught that even my
  measurement's NAME ("probable duplicate") over-claimed — same-day early/late
  shows are the innocent alternative; criterion_now: all gates green + corpus
  unmutated + Forge CERTIFY + advisor points addressed.

---

# Iteration 8 — /RedTeam the green gates (2026-05-30)

## Method

User invoked /RedTeam on the "green" iter-7 state (313→ tests, all oracles
passing, 2 Forge CERTIFY audits). Ran the VectorSpecialists workflow, DEEP-tier:
1 verifier-specialist (attack the oracle first) + 4 vector-specialists in
parallel, each given file paths + verbatim oracle output + the literal mission
"find a way the oracle certifies the file as correct while it is actually
wrong." Verifier verdict: **ORACLE-INCOMPLETE** → re-scope: fix oracles first.
Every finding independently reproduced before fixing.

## Confirmed defects the green gates hid (all fixed + regime-correct controls)

**Category-theory checks were STILL vacuous (my own iter-6 "de-vacuuming" was fooled — the negative-control tests fired in a different regime than the corpus-scale check inspects):**
- colimit_cone_factors recomputed `union(F)` then tested subset-against-itself → tautology; never tested the apex `colimit_of_setlist_functor` actually returns. FIX: assert returned apex `F[max]` == `⋃F` (fails on non-monotone). 
- Date-law sampler checked string-concat associativity (always true) + never checked closure. FIX: sampled closure check (composite ∈ arrows); negative control = non-transitively-closed table.
- Yoneda lemma only inspected dates ≥ query → non-monotone-before-query passed. FIX: require `is_monotone` over the whole poset.

**Oracle gaps (no truth-binding):**
- NO archival ground-truth test existed — a corrupted `top_song_count: 99999` shipped green (every archival test was a `>=` threshold). FIX: `tests/test_archival_ground_truth.py` pins actual values (top_song 752, cardinalities, 282, 449/14, venue-dup, FDR 1533, date-objs 2312) + a null-data FDR control.
- `is_complete=True` hid 282 empty-setlist shows via env-var tier branch; docstring claimed "every show has a setlist"; `dangling`/`corpus_scope` defaulted to DIFFERENT tiers. FIX: `tier` is now a report field (one source of truth), docstring corrected, `n_shows_without_performances` surfaced + tokenized ({{SHOWS_WITHOUT_PERFORMANCES_N}}=282) + bound by test.

**Over-claimed / inconsistent numbers:**
- Markov "2300 significant" had NO multiple-comparison correction (~5% false positives; null-data control flagged 990). FIX: Benjamini–Hochberg FDR → **1533** significant (q=0.05), uncorrected 2284 disclosed, null-data control = 0. Manuscript reframed.
- catalog_coverage folded segment markers into the numerator, contradicting the exclusion contract. FIX: exclude markers consistently (coverage 69.42%).
- Hardcoded "roughly 2,300 objects" (actual 2312; conflated with 2300 transitions / 2318 estimate). FIX: tokenized {{N_DATE_POSET_OBJECTS}}.
- venues.py jaccard was first-vs-rest, mislabeled "pairwise" (latent — all groups size 2). FIX: true pairwise `combinations`.
- eigenvector_centrality silently returned non-converged/disconnected garbage. FIX: `eigenvector_centrality_converged` + `strict` flag.
- export round-trip value-checked ONLY song titles. FIX: full field-by-field round-trip test (venues/performances/citations/recordings).
- figure "non-degenerate" = pixel variance only (wrong-data passes). FIX: reframed as blank-canvas tripwire in docstring + manuscript; correctness bound by ground-truth tests. Recording non-`gd` date-check + venue-merge order-dependence documented as limitations.

## Verification (2026-05-30)

| Gate | Result |
| --- | --- |
| Tests | **313 passed** (+17: regime-correct cattheory controls, archival ground-truth, FDR null control, export value round-trip), **90.67%** coverage |
| ruff / mypy | clean / Success (87 files) |
| Both pipelines | seed + archival exit 0; 25/25 figures; archival complete, dangling=0, geo 100% |
| PDF / markdown / prerender | 0 issues; tokens resolve (1533/2284/2312/282); "roughly 2,300" gone |
| RedTeam | 5 specialists; verifier ORACLE-INCOMPLETE → oracle fixed first |

## Changelog

- conjecture (2026-05-30, iter-8): a doubly-CERTIFIED green project still hid a
  coherent defect class — *negative-control tests that fire in a different
  regime than the corpus-scale oracle inspects* (the exact trap I fell into in
  iter-6 de-vacuuming), plus uncorrected/over-claimed numbers; refuted_by: n/a;
  learned: RedTeam the VERIFIER first — the green tests were green because each
  control hand-crafted a defect in the one regime its check happened to look at,
  while the reported corpus-scale passes exercised none of those regimes; the
  fix is regime-correct controls + ground-truth value binding + FDR; criterion_now:
  oracles bind truth, not shape.

---

# Iteration 9 — Figure clarity + modular manuscript expansion (2026-05-30)

## Trigger

User: the segue digraph was "a crazy gray blob, unclear what it means"; improve
figures + captions; "greatly add and improve the manuscript modularly."

## Root cause (reproduced visually)

`draw_segue_graph` used a circular node-link layout with edge line width
`0.5 + 0.5*count`. At archival scale the top edge (drums→space, count 1197)
produced a ~600pt line that covered the whole panel — a literal gray blob. Read
the PNG to confirm before changing.

## Work

- **Segue figure REDESIGNED** → ranked horizontal bar chart of the top-15
  segues ("A → B", bar = count, value labels, title-cased labels via new
  `_pretty`). Now legible: recovers the canonical segues from data alone
  (Drums→Space 1197, China Cat→I Know You Rider 544, Scarlet→Fire 238).
- **Two pie charts → ranked bars** (`citation_kinds`, `recording_sources`) via a
  shared `_draw_labeled_category_bars` helper (count + share labels, single
  colorblind-safe hue). The recording-sources bar honestly surfaced that
  7,110/7,122 (100%) archival recordings are source-type UNKNOWN (the pie hid
  it) — disclosed in the caption.
- **Captions rewritten** for segue/citations/recordings (describe encoding +
  the honest UNKNOWN fact + the canonical-segue recovery).
- **NEW modular manuscript section `04b_segue_structure.md`** (`\label{sec:segue-structure}`):
  distinguishes *transitions* (positional, Markov, FDR-controlled) from *segues*
  (explicit markers, higher-confidence subset), interprets the top segues, and
  analyses segue *hubs* via out-degree (Drums = fan-shaped launch point vs
  composed songs' concentrated out-degree). All numbers token-backed
  (TOP_SEGUE_*, N_SEGUE_EDGES, N_SIGNIFICANT_TRANSITIONS) — no stale literals
  (iter-5/8 lesson). Added `\label{sec:results}` for the cross-ref.
- Report + tokens: `02_analyze` emits `segue_summary`; z_generate adds 6 segue
  tokens.

## Verification (2026-05-30)

| Gate | Result |
| --- | --- |
| Segue figure | re-rendered + viewed: clear ranked bars, blob gone |
| citation_kinds / recording_sources | re-rendered + viewed: clean bars |
| Tests | **316 passed** (+3 viz: _pretty, segue-bar, category-bars), **90.69%** coverage |
| ruff / mypy | clean / Success (87 files) |
| Archival pipeline | exit 0; 25/25 figures; complete; dangling=0 |
| PDF / markdown / prerender | 0 issues; new §segue-structure + tokens resolve; no unresolved {{}} |

## Changelog

- conjecture (2026-05-30, iter-9): the segue "blob" was a weight-scaling bug
  (linear lw on counts in the thousands), not a layout-taste issue; refuted_by:
  visual reproduction of the PNG; learned: for weighted graphs at scale a ranked
  bar chart beats a node-link blob for clarity, and a clearer encoding can
  surface honest data-quality facts the old chart hid (recordings UNKNOWN=100%);
  criterion_now: figures legible + captions honest + new modular segue section.
