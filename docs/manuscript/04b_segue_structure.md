# Segue and transition structure

\label{sec:segue-structure}

The Grateful Dead's setlists are not a bag of songs but a *sequenced* object:
certain songs flow into certain others, often without pause, and those flows are
as much a part of the band's identity as the songs themselves. The compendium
captures this at two distinct levels of evidence, and keeping them separate is
the point of this section. That separation also aligns with MIR work on
full-concert setlist segmentation: audio-level identification must contend with
banter, applause, covers, transitions, and live-version variation
[@wang_setlist_segmentation], while this compendium starts from curated setlist
rows and explicit editorial segue markers.

## Two notions of "what follows what"

A **transition** is positional: song $B$ immediately follows song $A$ within a
set, whether or not the band marked a musical link. These are what the
first-order Markov model in Section \ref{sec:results} counts, and the
permutation-null screen retains {{N_SIGNIFICANT_TRANSITIONS}} of them as
significant under false-discovery-rate control (out of {{N_TRANSITION_CANDIDATES}}
eligible ordered pairs).

A **segue** is explicit: the source data marks a "->" / ">" link
between two performances, encoded in the compendium as a `segue_into` edge.
There are {{ARCHIVAL_SEGUE_MARKERS}} such markers spanning {{N_SEGUE_EDGES}}
distinct directed song pairs. A segue is therefore a *curated subset* of the
transitions — the ones a setlist editor judged to be a genuine musical
continuation — and carries stronger evidentiary weight than mere adjacency.

The two notions agree where it matters and diverge informatively. The
FDR-significant transitions and the top segues share their podium in this
archival build —
"China Cat Sunflower" -> "I Know You Rider" and "Scarlet Begonias" ->
"Fire on the Mountain" top both lists — which is reassuring: the explicit
editorial judgement and the blind statistical screen converge on the same
canonical pairings. Where they diverge, the transition view sees adjacencies
that were never marked as segues (e.g. an encore break that the Markov model
cannot distinguish from a continuation), which is exactly why the segue markers
are the higher-confidence signal.

## The most frequent segues

Figure \ref{fig:segue} ranks the segues directly. The single most frequent is
"{{TOP_SEGUE_SRC}}" -> "{{TOP_SEGUE_DST}}" with {{TOP_SEGUE_COUNT}}
occurrences — the canonical "Drums" -> "Space" passage that anchors the
second-set improvisational core for most of the band's career. That this
structural segment, rather than any song, is the corpus's most frequent segue is
not an artefact: it reflects a real feature of the music, and it is reported
honestly here precisely because the segment markers are *kept* in the
transition/segue analyses (they are excluded only from the repertoire ranking of
Section \ref{sec:results}, where they are not compositions). Below the segment core,
the ranking is a tour of the band's signature pairings — the
"China Cat" -> "Rider" fusion, the "Scarlet" -> "Fire" suite, the
"Estimated Prophet" -> "Eyes of the World" flow — recovered from the
markers alone, with no title-based inference.

## Segue hubs

Out-degree in the segue graph identifies *launch points* — songs that most often
flow into something else. The highest is ``{{TOP_SEGUE_OUT_SONG}}''
({{TOP_SEGUE_OUT_COUNT}} outgoing segues), consistent with the structural role
of the "Drums"/"Space" core as a hinge between composed material: the band
exits the improvisational segment into a wide variety of songs, so it
accumulates a large, fan-shaped out-degree rather than a single dominant
successor. Composed songs, by contrast, tend to have concentrated out-degree —
a song like "Scarlet Begonias" overwhelmingly segues into one partner — which
is the graph-theoretic signature of a fixed suite versus an improvisational
junction.

## What this does and does not establish

These are descriptive structures over the ingested setlists, not causal or
exhaustive claims. The segue markers are only as complete as the source
editors' annotations; an unmarked continuation is invisible to the segue view
and appears only as a (weaker) transition. The Markov model is first-order by
construction, so longer signature chains — "Help on the Way" -> "Slipknot!" ->
"Franklin's Tower" — are visible only as their pairwise
links, not as a single third-order object. The taping and trading literature is
a useful guardrail here: recordings and setlists are co-curated cultural
records [@dead_net_taping_dead; @wallace_cocreation_sound_archive], so this
section reports what the encoded record says rather than what the band
"really" intended in every performance. Both limitations are inherent to the
representation and are revisited in the limitations of Section \ref{sec:results}.
