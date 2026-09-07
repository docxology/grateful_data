# Methodology

## Schema

The compendium primitive is a small frozen-dataclass schema. Every entity
validates its inputs in ``__post_init__``; every primary key is computed by a
canonical-slug function so that joins across sources reduce to dictionary
lookups. The nine entity types are ``Show``, ``Venue``, ``Person``, ``Song``,
``Performance``, ``Recording``, ``Release``, ``Citation``, and ``Lineup``;
their fields and invariants are documented in ``src/models.py``.

Two canonical-slug rules suffice for source-agnostic identity:

* a song slug is the ASCII-folded, punctuation-stripped slug of its title;
* a show slug is ``YYYY-MM-DD@<venue-slug>``.

These deterministic functions absorb the cross-source-naming variance that
would otherwise require a manual alias table.

### Data dictionary (core entities)

The field-level contract for the entities that carry the quantitative claims;
the authoritative definition with all invariants is ``src/models.py``.

| Entity | Key | Principal fields | Notes |
| --- | --- | --- | --- |
| ``Show`` | ``slug`` = ``YYYY-MM-DD@venue`` | ``date``, ``venue_slug`` | one concert; ``venue_slug`` is a foreign key into ``Venue`` |
| ``Venue`` | ``slug`` | ``name``, ``city``, ``state_or_region``, ``country`` | geo coordinates live in a ``venue_geo`` sidecar |
| ``Song`` | ``slug`` (slug of title) | ``title``, ``composers``, ``lyricists``, ``first_performed``, ``last_performed``, ``aliases`` | catalogue entry; need not have been performed |
| ``Performance`` | ``(show, song, set, position)`` | ``show_slug``, ``song_slug``, ``set_number``, ``position``, ``segue_into``, ``notes`` | the apex of the show$\leftrightarrow$song span |
| ``Person`` | ``slug`` | ``intervals`` = ``(start, end, role)`` tuples | open interval (``end=None``) means still active |
| ``Recording`` | ``slug`` | ``show_slug`` (or date), ``source_type`` | Internet Archive + curated rows |
| ``Review`` | — | ``show_slug``, ``kind``, ``sentiment`` $\in[-1,1]$, ``source_url`` | positive sentiment requires a source URL (honesty check) |
| ``Citation`` | ``key`` | ``kind``, ``url`` | bibliography + ``references.bib`` |
| ``LyricPointer`` | ``song_slug`` | ``url``, ``themes``, ``lyricist`` | URL metadata only — never lyric text |

## Source ingestion

Each cited source has its own *reference parser* at ``src/sources/<name>.py``.
Every parser exposes a single ``parse`` function whose input is a record in
the documented upstream shape (JSON payload for API sources, line-oriented
text block for HTML-derived archives, dict-of-tables for relational dumps)
and whose output is in the canonical schema. The committed snapshot in
``data/archival/`` is built from gdshowsdb YAML, truckin-through-time SQLite
gap-fill, and curated overlays. Live HTTP fetchers are implemented in
``src/ingest/`` and invoked by
``scripts/00_fetch_sources.py --online --archival-max``. We support nine
ingestion paths corresponding to the survey above:

| Source | Module | Citation |
| --- | --- | --- |
| Setlist.fm | ``sources/setlistfm.py`` | [@setlistfm_gd] |
| The SetList Program | ``sources/setlist_program.py`` | [@setlists_net_program] |
| CMU / Mark Leone | ``sources/cmu_setlists.py`` | [@cmu_leone_setlists; @noah_truckin_through_time] |
| GDsets | ``sources/gdsets.py`` | [@gdsets_com; @gdsets_dead] |
| gdshowsdb | ``sources/gdshowsdb.py`` | [@gdshowsdb] |
| Internet Archive LMA | ``sources/internet_archive.py`` | [@internet_archive_lma; @fifteen_songs_dataset] |
| Alex Allan / whitegum | ``sources/alex_allan.py`` | [@whitegum_alex_allan] |
| dead.net (official) | ``sources/dead_net.py`` | [@dead_net_official] |
| Wikipedia | ``sources/wikipedia.py`` | [@wikipedia_gd; @wikipedia_discography] |

The Internet Archive path is treated as recording *metadata* rather than as an
audio-ingestion license. The Grateful Dead collection has its own access and
upload posture, and its item metadata can include source, taper, and transfer
fields that are valuable without bundling audio files
[@internet_archive_gd_collection_policy]. Likewise, the lyric layer records
URLs, lyricist attribution, and curated theme labels only; Dodd and Trist's
annotated lyrics are cited as external interpretive context, not ingested text
[@dodd_annotated_lyrics].

### Contextual-source layer

Historical context is deliberately stored as citations and prose, not as
performance data. The enriched-bibliography pass added a fourth source class:
checked contextual anchors for formation, public honors, sound engineering,
tape-trading, Deadhead sociology, studio-era reception, bibliography, and
live-recording scholarship
[@dead_net_biography; @foundsf_weir_psychedelic_sf;
@smithsonian_institutionally_dead; @mcintosh_wall_of_sound;
@marshall_bootleg_collectors; @brackett_live_dead;
@adams_deadhead_social_science; @dodd_weiner_annotated_bibliography;
@americana_highways_workingmans_american_beauty;
@kennedy_center_honors_2024].
These sources can explain why a date matters, but they do not create or
override ``Show``, ``Performance``, ``Recording``, or ``Release`` rows. The
quality tiers are explicit:

* **Data-bearing primary sources** (gdshowsdb, Truckin, Setlist.fm, SetList
  Program, Internet Archive metadata) may create or corroborate schema rows
  through parser code.
* **Pointer-only sources** (whitegum, the CMU lyric index, dead.net song pages,
  Dodd/Trist) may supply URLs, attributions, and themes but never bundled lyric
  text.
* **Scholarly or institutional context** (UCSC, Wallace, Brackett,
  Adams/Sardiello, Lewin, NIST/Padi, Popoff/Andreatta) may support manuscript
  interpretation, methods scope, and related work.
* **Journalism or publisher context** (JSTOR Daily, Americana Highways,
  Billboard, Britannica, McIntosh) may support labelled reception, biography,
  or technical context only.
* **Community reconstruction** (Reddit threads, Grateful Seconds) may support
  explicitly labelled background, never quantitative findings.

No current-person, revenue, lyric, or audio claim from the source dossier is
allowed into the quantitative layer unless it is independently sourced and
represented in the schema. The same rule applies to citation placement:
contextual sources may explain the provenance of a figure or timeline label,
but the plotted statistics must still come from generated reports or exported
figure data.

## Integration

The integration layer at ``src/integration/reconcile.py`` performs a
deterministic merge. The merge rule is pointwise per entity type — venues
join on slug, songs join on slug with union of composer/lyricist tuples and
min/max of first/last-performed dates, people join on slug with union of
intervals, performances join on the four-tuple ``(show, song, set, pos)``.
The resulting ``Compendium`` is immutable and byte-stable across runs.

## Committed compendium (`data/archival/`)

The published dataset lives under ``data/archival/`` ({{CORPUS_SCOPE_PHRASE}}).
It merges gdshowsdb YAML, truckin-through-time gap-fill, Internet Archive LMA
metadata, bibliography citations, maximinus reviews, CMU lyric pointers, and
curated personnel/releases overlays. ``GRATEFUL_DATA_TIER=archival`` selects
this load path (see ``src/tier.py``).

## Analyses and validation

The analysis layer at ``src/analysis/`` computes descriptive statistics,
co-occurrence and Markov transitions, era and personnel timelines, geo and
tour aggregates, lyric-theme frequencies from pointers, review sentiment,
segue extraction, eigenvector centrality, stationary distributions, and
bustout (recurrence-gap) metrics — each as a pure function of the
``Compendium``.

Distributional statistics are first-class objects rather than incidental plot
annotations. ``src/analysis/distributions.py`` computes show-level
performance-row summaries, robust percentiles, and simple concentration
statistics (Gini, top-decile share, and the number of ranked items needed to
cover 50\% and 80\% of rows). The method is descriptive only: it reports
skew and concentration in the archival record without treating unequal song
frequency, venue recurrence, or setlist length as causal effects. Show-level
performance distributions include empty-setlist shows, because excluding them
would make the setlist-completeness limitation invisible.

The same module now adds fixed-seed item-level bootstrap intervals for the
song and venue concentration statistics. These intervals are reported as
exploratory uncertainty bands around descriptive metrics: the resampling unit
is the observed item count (a song's performance count or a venue's show
count), not a claim about unobserved concerts, fan preference, or musical
causation.

Exploratory repertoire modeling lives in ``src/analysis/exploratory.py``. It
constructs an era-by-song performance-count matrix with generic segment
markers excluded, applies a centered SVD to log-count profiles, and clusters
the two-dimensional coordinates with deterministic k-means-style updates and
stable tie-breaks. The output is explicitly labelled as pattern discovery: it
helps inspect era-weighted repertoire profiles, but it is not predictive,
causal, or a definitive musicological taxonomy.

The transition analysis is intentionally modest: a first-order chain over
adjacent within-show performance rows plus an explicit segue graph over
source-marked ``segue_into`` edges. MIR work on full-concert setlist
identification shows why audio-level segmentation is a separate, harder task
that would require different evidence and different artifacts
[@wang_setlist_segmentation]. The current analysis report also includes a
deterministic transition-sensitivity layer: predecessor-support thresholds are
summarized with and without generic segment markers, and era-specific
transition summaries are reported as descriptive diagnostics. These sensitivity
rows do not rerun the permutation screen and do not create predictive claims;
they show how fragile or stable the visible transition surface is under
ordinary presentation choices.

Repertoire concentration is likewise reported with sensitivity context. Beyond
the fixed-seed bootstrap intervals, the analysis report summarizes alternate
top-N cuts for performance share, within-cut Gini, top-decile concentration,
and era coverage. This keeps the manuscript from treating a single top-song
cutoff or heatmap width as if it were an intrinsic property of the archive.

### First-principles claim ledger

The methods layer now includes a claim-governance pass in
``src/analysis/first_principles.py``. This is not a statistical model; it is a
reproducibility device. The ledger deconstructs each major manuscript claim
family into five irreducible parts: the data input, the hard constraint that
must hold, the softer modeling or presentation choice, the assumption that
remains after the hard constraint is enforced, and the interpretation limit.
The current build classifies {{FIRST_PRINCIPLES_CLAIM_AREAS_N}} claim families
across {{FIRST_PRINCIPLES_CLAIM_CLASSES_N}} claim classes, naming
{{FIRST_PRINCIPLES_HARD_CONSTRAINTS_N}} hard constraints,
{{FIRST_PRINCIPLES_ASSUMPTIONS_N}} assumptions, and
{{FIRST_PRINCIPLES_VALIDATION_ARTIFACTS_N}} validation artifacts.

This layer prevents the common failure mode in computational humanities
projects: a polished visualization silently upgrades a descriptive pattern into
an explanatory claim. For example, repertoire rankings are permitted to say
what was counted after segment-marker exclusion; they are not permitted to say
what the band preferred. The transition matrix is permitted to summarize
adjacent setlist rows; it is not permitted to infer musical causality. The
historical-context timeline is permitted to orient computed show counts against
cited milestones; it is not permitted to create or modify a ``Show`` row.
``scripts/19_first_principles_review.py`` serializes the ledger as
``output/reports/first_principles_review.json`` and
``output/reports/first_principles_claims.csv``. Each row also names the
manuscript section, figure filename, report key, governing test file, and
claim status, so caveats can be routed through the ledger instead of repeated
as free-floating prose.

### Provenance, external pointers, and reviewer artifacts

Source provenance is exported as a sidecar rather than written into the frozen
entity dataclasses. ``src/provenance.py`` records the source-layer families
behind shows, songs, venues, performances, recordings, releases, citations,
lyric pointers, reviews, personnel rows, and computed segue edges. The records
are deliberately conservative: they identify ingest or computation layers, not
hidden row-level certainty that the schema does not store.

The external-media layer is pointer-only. ``src/external_manifests.py`` writes
audio and lyric URL manifests with compact metadata, hashes where available,
and explicit policy labels. It rejects bundled audio, local paths, lyric text,
transcripts, excerpts, waveforms, and derived text fields. It also writes a
small pipeline contract that names allowed inputs and outputs for future
external audio-feature and lyric-annotation workflows. This keeps future
audio- or lyric-analysis work reproducible without changing the present
copyright and data-boundary claims.

Visualization lives in ``src/viz/``: reusable panel builders
(``panels.py``), a figure registry (``figures.py``), mosaic composition
(``compose.py``), alluvial flows (``alluvial.py``), and non-blank figure
validation (``validate.py``). HTML dashboards and entity markdown pages live
in ``src/reporting/``.

The figure set is deliberately mixed: frequency and concentration views use
ranked bars or cumulative-share curves; distributions use histograms with
median and high-percentile reference lines; temporal activity uses bars/lines;
co-occurrence and transition matrices use heatmaps; geography uses a
size-encoded scatter map; and the composer/song/era view uses an alluvial
diagram. Pie charts are avoided because the same categorical comparisons are
more legible as sorted bars with counts and shares.

The contextual-source distinction also shapes the visual layer. The new
historical-context timeline overlays a small set of cited milestones on
computed show counts; it is a visual orientation aid, not an ingest product.
The figure registry therefore carries its title, screen-reader alt text,
caption hint, data source, statistic, exclusion rule, claim class, draw
function, and figure-data exporter together. The same metadata feeds the
dashboard, raw figure-data index, publication validator, and manuscript
captions, so prose claims and plotted statistics are auditable from one
registry. A plain static explorer under ``output/explorer/`` reuses exported
show, song, venue, segue, figure, provenance, and claim-evidence data for
local filtering without adding a frontend framework. The explorer supports
URL-state filters, sortable table headers, related links, and filtered CSV
download, so readers can inspect subsets without depending on a server.

Runtime probes certify manuscript claims beyond unit tests:

* ``src/audit.py::audit_completeness`` — referential integrity (tier-aware);
* ``src/export.py`` — full raw CSV/JSON export of every entity type;
* ``src/analysis/first_principles.py`` — first-principles claim/evidence
  ledger for hard constraints, assumptions, validation artifacts, and limits;
* ``src/provenance.py`` — sidecar provenance CSV/JSON for entity/source-layer
  review;
* ``src/external_manifests.py`` — pointer-only external audio/lyric manifests
  with protected-content rejection;
* ``src/viz/datasets.py`` — raw CSV/JSON export of {{FIGURE_DATASETS_N}}
  registered figure datasets;
* ``src/viz/validate.py::validate_figures`` — every expected PNG exists and
  is non-degenerate.
