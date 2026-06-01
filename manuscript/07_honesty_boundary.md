# The executable honesty boundary

The prose elsewhere in this manuscript draws a bright line between *ingested
snapshot* and *live upstream*, between *pointer metadata* and *lyric text*,
between *cited source* and *HTTP fetch*. This section promotes that boundary
from prose to a runtime contract enforced inside the compendium loader by
:class:`grateful_data.honesty.HonestyBoundary`.

## What the boundary refuses

The boundary recursively walks the raw JSON payloads and the built
``Compendium`` and raises :class:`HonestyViolation` on any of the
following shapes:

| Forbidden shape | Detection rule |
| --- | --- |
| ``lyric_text`` / ``lyrics`` / ``verse`` / ``chorus`` / ``stanza`` / ``refrain`` keys anywhere | recursive walk on lowercased key name; project bundles pointers, not text |
| ``audio_feature_*`` / ``synth_*`` keys anywhere | recursive walk on lowercased key prefix; project bundles no audio |
| ``Review`` with ``sentiment > 0`` and empty ``source_url`` | over-claim shape ("positive but unverifiable") |
| ``Citation`` with empty or non-``http(s)://`` URL | broken provenance |
| ``Recording`` with ``gd``-prefixed ``archive_id`` whose URL does not point at ``archive.org`` | identifier suggests Internet Archive but URL is elsewhere |
| ``LyricPointer`` with empty ``source_url`` | we promise a pointer; missing pointer is over-claim |

A violation aborts ``load_seed_compendium`` before any analysis runs.
``enforce_honesty=False`` is available but exists only for tests of the
boundary itself.

The same rule applies to prose-only context introduced from the supplied
source dossier. Formation stories, Wall of Sound details, public honors,
songwriter recollections, studio-era reception, and tape-trading claims must
cite checked sources and remain prose or citation metadata unless the project
has a schema field for them
[@dead_net_biography; @foundsf_weir_psychedelic_sf; @mcintosh_wall_of_sound;
@kennedy_center_honors_2024; @marshall_bootleg_collectors;
@rolling_stone_robert_hunter_interview;
@americana_highways_workingmans_american_beauty]. The dossier does not
authorize new quantitative rows, current-person claims, lyric text, audio
features, or revenue figures inside ``data/archival/``. Community
reconstructions are explicitly labelled as context when cited
[@grateful_seconds_touring_revenues].

## Why this exists

Two lessons from the prior-work memory drove it directly:

* **disclosure is not remediation** — buried hedges in research-manuscript
  prose are laundering, not honesty. A runtime check forced into every
  load is the durable form.
* **shape tests don't bind truth** — a unit test that checks the *shape*
  of a review record passes happily on a fabricated positive review. The
  honesty boundary checks the *content* shape that fabrication takes.

## Binding to tests

Each forbidden shape has a dedicated negative-control test that constructs
a synthetic violation and asserts the boundary rejects it. The positive
control is the committed archival compendium: ``test_seed_loader_passes_honesty``
asserts that the real snapshot loads with ``enforce_honesty=True``.
The whole loop is tested in ``tests/test_honesty.py`` and (with one tamper
test per failure mode flipping a real row to a known-bad shape) in
``tests/test_honesty_tamper.py``.

## Verdict

**CERTIFY-WITH-RESIDUALS for v0.1.** The honesty boundary enforces every
named failure mode at load time, the negative-control tamper tests
demonstrate it fails loud on the right shapes, and the entity-page
generators are anti-fabrication-tested in
``tests/test_entity_pages_no_fabrication.py``. Acknowledged residuals at
this version:

* schema validation catches shape violations but cross-field semantic
  validity (e.g. date ∈ band-active-window, set position ≤ setlist length)
  is not yet a gate — that is the next layer of refinement;
* the ``cattheory/`` package's load-bearing modules (categories, functors,
  spans, natural, colimits, yoneda) each carry a *negative control* — a
  broken composition, a non-monotone functor, or a too-small colimit vertex
  that the check must reject — so the constructions are tested for teeth, not
  merely exercised. The colimit now verifies the universal property (not just
  subset-of-union) and Yoneda is checked over the non-degenerate ``Date``
  poset rather than the trivial discrete case. The one remaining piece of
  honest *scaffolding* is ``enriched.py``: the audio-similarity enrichment is
  structural only — concrete weights would come from a downstream pipeline
  against the ``fifteen-songs-dataset`` [@fifteen_songs_dataset], and the
  honesty boundary forbids bundling audio features, so it is labelled a stub
  rather than presented as an empirical result.

## Licensing and provenance

The compendium integrates many community and institutional sources, and is
explicit about reuse posture. The *code and the derived compendium schema*
(the slugged entity tables and the category-theoretic constructions) are the
contribution of this project; the *underlying facts* — setlists, dates,
venues, personnel — are drawn from the cited sources, each of which carries
its own terms. Setlist and show data derive primarily from community archives
(gdshowsdb, the truckin-through-time dataset, Setlist.fm) and reference works
(Wikipedia, Britannica); recording metadata comes from the Internet Archive
Live Music Archive, whose Grateful Dead collection has its own access policy
and metadata conventions [@internet_archive_gd_collection_policy]; reviews are
a curated/maximinus subset. No lyric text and no audio-feature data are bundled
— lyric pointers are URL metadata only — both to respect copyright and as the
project's stated ethical boundary. Dodd and Trist's annotated lyrics are cited
as scholarship, not copied as data [@dodd_annotated_lyrics].

One nuance worth stating explicitly: while individual facts (a date, a venue,
a song title) are not protectable, a *curated compilation* — a particular
hand-edited setlist or segue sequence — can carry its own rights independent of
lyrics or audio, and our setlist and segue data derive from such
community-curated sources. Archive scholarship on the Dead's sound record
underscores that this is a co-created curation ecosystem, not a source-free
fact dump [@wallace_cocreation_sound_archive; @dead_net_taping_dead].
Downstream users should therefore consult each cited source for its own
licensing before redistribution; this work claims rights only over the
integration code and the structural representation, not over the source facts
or any upstream curator's compilation.

## Out of scope

The boundary is not a content-moderation system or a lyric classifier. It
is a small set of refusals encoding what the *project itself* has promised
to do and not do, written in code so a future contributor cannot quietly
drift past it.
