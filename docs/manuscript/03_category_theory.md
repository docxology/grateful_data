# Category-theoretic interpretation

## Why category theory

Category theory gives us a vocabulary for *structure that survives change of
representation*. The four constructions below identify structure that does
not depend on which source we drew the data from or on which subset of the
corpus we are looking at: they are stable in exactly the sense category
theory was built to express.

The point is not to claim that setlists require category theory. The point is
to make the data model's relations explicit. Lewin's transformational theory
famously shifts attention from musical objects to transformations among
objects [@lewin_gmit]; NIST's music case study shows category theory used as an
ontology and integration framework for musical knowledge
[@padi_category_music_case_study]; and recent work on hidden categories in
Lewinian GIS and Klumpenhouwer networks makes the categorical connection
literal [@popoff_hidden_categories]. Those works license the *kind* of move
being made here -- a shift from objects to relations and an ontology whose
diagrams can be checked -- but they do not make the Grateful Dead corpus
categorically interesting by association. Our use is narrower: shows, songs,
dates, and performances form a small relational system whose laws can be
checked directly against the compendium.

**Scope of these claims.** $\mathbf{Date}$ is a *thin* poset category, so
associativity holds automatically and the Yoneda statement is the elementary
poset case rather than a deep theorem. We therefore present the mechanized
checks below — law sampling, the colimit universal property, the Yoneda
bijection, the span/functor commutation — as *encoding and sanity checks*: they
verify that the schema faithfully instantiates these categorical structures and
that the corresponding properties hold on the real corpus (each with a negative
control that fails on broken input), not that a non-trivial mathematical theorem
about the Grateful Dead has been proved. Their value is that the data model is
demonstrably the categorical object we claim it is — which is what licenses the
representation-independent reading — not mathematical novelty or a claim that
categorical music theory explains the band's musical choices.

## The date poset and the show category

Let $\mathbf{Date}$ be the small category whose objects are the distinct
performance dates in the compendium and whose morphisms $d_1 \to d_2$ exist
iff $d_1 \le d_2$. $\mathbf{Date}$ is a thin poset category; identities and
associativity hold by construction. Let $\mathbf{Show}$ be the discrete category
whose objects are the show slugs. Both categories' laws are checked
mechanically in ``src/cattheory/categories.py::Category.check_laws``. Small
categories are verified exhaustively; at archival scale the $\mathbf{Date}$
poset has {{N_DATE_POSET_OBJECTS}} objects, so an exhaustive associativity sweep
is intractable. The checker instead verifies every identity and samples a fixed
(seeded) set of random composable triples, checking both associativity and
**closure** (that each sampled composite arrow is present in the table). Because
the $\mathbf{Date}$ ``compose`` is order-preserving string composition, its
associativity holds by construction; the data-reachable defect is a
non-transitively-closed arrow table, which the sampled closure check catches
with high probability. This is a *regression guard* — the laws hold by
construction; the check is a sampled probe of systematic corruption, not a
proof — paired with a negative control that fails on a deliberately non-closed
table.

## The setlist functor

Define $F_{\text{setlist}} : \mathbf{Date} \to \mathbf{Set}$ by sending each
date $d$ to the set of song slugs ever performed on or before $d$, and each
arrow $d_1 \le d_2$ to the inclusion of sets. $F_{\text{setlist}}$ is a
covariant functor because the cumulative-songs set is monotone in $d$.
``cattheory/functors.py::setlist_functor`` returns the explicit
representation; ``is_monotone`` checks the functor law on the compendium.

## The lineup functor and the active-roster presheaf

Define $F_{\text{lineup}} : \mathbf{Date} \to \mathbf{Set}$ by sending each
date $d$ to the set of personnel who have been in the band on or before $d$,
and each arrow to the inclusion. $F_{\text{lineup}}$ is again a monotone
covariant functor.

The *active-roster* assignment $P_{\text{active}}(d) = \{p \mid p\ \text{is
in the band on}\ d\}$ is also natural, but it is *not* monotone: when
Pigpen leaves the band in 1972 [@ucr_lineup_changes; @dead_net_official],
the active set shrinks, so $P_{\text{active}}$ fails the covariant-functor
law. It is, however, a perfectly good presheaf: contravariantly, the
"forgetting" arrow $d_2 \to d_1$ can be sent to the restriction of the
active set. We make both views available
(``setlist_functor``, ``lineup_functor``, ``active_lineup_presheaf``) and
check that one is monotone and the other is not. The categorical content
matches the historical fact: cumulative views grow; instantaneous views
oscillate.

## Performances as spans, with fibers over shows and songs

For each performance $p = (\text{show}, \text{song}, \text{set}, \text{pos})$,
define a (2-leg) span:

$$\mathrm{Show}\ \xleftarrow{\pi_{\text{show}}}\ p\ \xrightarrow{\pi_{\text{song}}}\ \mathrm{Song}.$$

In ``cattheory/spans.py``, ``PerformanceSpan`` exposes the two projections
explicitly. The *fiber* of $\pi_{\text{show}}$ over a fixed show $s$ — the
preimage $\pi_{\text{show}}^{-1}(s)$, equivalently the wide pullback of all
spans pinned on the left to $s$ in the discrete fibration sense — recovers
the show's setlist in canonical order. Symmetrically, the fiber of
$\pi_{\text{song}}$ over a fixed song recovers the song's performance
history. We use "fiber / multi-leg span" rather than "wide pullback" in the
strict universal-property sense; the discrete-base setting collapses the
distinction. This construction shows that the performance primitive is not a
derived field of the schema; it *is* the apex linking shows and songs, and
the two projections commute by definition with the cumulative setlist
functor.

The categorical content is small but real:

* No data is lost going either direction along a span; both projections
  are total.
* The two wide-pullback constructions give the two natural "transposes" of
  the performance table — show-major and song-major — without privileging
  either.
* Composition of spans (in the bicategory of spans) corresponds exactly to
  the relational operation "show A and show B both played a song
  C" — useful for cross-show similarity measures.

## Audio enrichment

Following the precedent of the ``fifteen-songs-dataset``
[@fifteen_songs_dataset] and the broader MIR problem of identifying and
segmenting live concert songs [@wang_setlist_segmentation], pairs of
performances of the *same song* could carry a similarity weight in $[0, 1]$.
The category whose objects are performances and whose hom-objects are these
weights is enriched over the unit-interval monoid $([0, 1], \max, 0)$.
``cattheory/enriched.py::AudioEnrichedHom``
captures the abstraction: the constructor enforces the weight constraint
and the same-song precondition; identity homs at weight $1.0$ behave as
required in the enrichment.

We do not bundle audio. The enrichment is structural; concrete weights are
expected to come from a downstream pipeline against the
``fifteen-songs-dataset``.

## Coproducts and colimits

``cattheory/colimits.py`` exposes two constructions: the binary coproduct of
two ``Compendium`` fragments, which by the reconciliation rules collapses
into the disjoint-union compendium, and the colimit of the cumulative
setlist functor on the compendium, which equals the set of all songs ever
performed in the bundled data. Crucially, the colimit check verifies the
*universal property*, not merely that each $F(d)$ is a subset of the union:
``colimit_cone_factors`` confirms that a strictly larger cocone vertex admits
the unique mediating map and — as a built-in negative control — that a vertex
*strictly smaller* than $\bigcup F$ fails to receive the colimit. A check that
only asserted $F(d) \subseteq \bigcup F$ would be vacuous (true for any
family); requiring the negative control to fail is what gives it teeth. The
test ``test_coproduct_disjoint_union`` additionally asserts that splitting the
shows and re-merging via the coproduct returns the original show set — a
structural reproducibility witness for the reconciliation layer itself.

## Natural transformations

The cardinality assignment ``η_d = |F(d)|`` is a natural transformation
``F ⟹ \mathrm{Card} \circ F`` for any monotone covariant functor
``F : \mathbf{Date} \to \mathbf{Set}``. The naturality square reduces
(on this thin poset) to ``|F(d_1)| \le |F(d_2)|`` whenever
``d_1 \le d_2``. ``src/cattheory/natural.py`` exposes
``naturality_square_holds`` and the two concrete instances
``setlist_cardinality_transformation``,
``lineup_cardinality_transformation``; both pass on the compendium and both are
tested against a hand-crafted broken-cardinality functor as a negative
control. This is small but real categorical machinery — it lets us reason
about *several* functors in parallel through a single shared transformation.

## Representability (Yoneda) over the date poset

In the *discrete* show category the Yoneda embedding collapses to an equality
indicator and is a near-tautology. The non-degenerate statement lives over the
$\mathbf{Date}$ **poset**. For a fixed date $d$ the covariant representable
$\mathrm{Hom}(d, -)$ sends each date $e$ to a singleton when $d \le e$ and to
$\varnothing$ otherwise. A natural transformation
$\mathrm{Hom}(d, -) \Rightarrow F_{\text{setlist}}$ assigns the arrow $d \to e$
an element of $F_{\text{setlist}}(e)$, and naturality with the inclusion legs
forces a single element that must lie in $F_{\text{setlist}}(e)$ for *every*
$e \ge d$. Because the setlist functor is monotone, that condition holds exactly
for the elements of $F_{\text{setlist}}(d)$, giving the Yoneda bijection
$\mathrm{Nat}(\mathrm{Hom}(d, -), F_{\text{setlist}}) \cong F_{\text{setlist}}(d)$:
*the songs played by date $d$ are the natural transformations into the setlist
functor.* ``cattheory/yoneda.py::yoneda_lemma_holds_for_setlist`` checks this on
the corpus, and ``count_yoneda_naturals`` has a negative control — on a
non-monotone functor an element that later drops out is correctly rejected and
the bijection fails.

## What the construction buys

The payoff is that **the question "what songs were played when, by whom?"**
decomposes as a fibered relation in the compendium category: the span
projections commute with the cumulative setlist functor, and the fiber over a
fixed show date gives back exactly that show's setlist for exactly that lineup.
This is not asserted but *checked* —
``cattheory/spans.py::projections_commute_with_setlist_functor`` verifies, over
the whole corpus, that the union of show-fibers up to each date equals the
setlist functor's value there. The compendium primitive is the apex of the
span, not a derived join — which is what the categorical reading makes explicit,
and what allows seamless extension to any other performance corpus with the
same shape.
