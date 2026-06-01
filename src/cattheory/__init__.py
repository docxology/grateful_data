"""Category-theoretic interpretation of the Grateful Dead compendium.

Load-bearing vs interpretive scaffolding (honest framing).

* ``categories`` -- load-bearing: ``scripts/03`` writes Date/Show category
  laws to the JSON report.
* ``functors`` -- load-bearing: the monotonicity flags in the report and
  in the mosaic title come from here.
* ``spans`` -- load-bearing: ``wide_pullback_over_show`` is asserted to
  equal the setlist on five concrete shows in
  ``test_wide_pullback_over_show_equals_setlist``.
* ``natural`` -- load-bearing: the naturality-square flag in the report.
* ``enriched`` -- interpretive scaffolding: abstraction over the
  (intentionally absent) audio-feature pipeline.
* ``opposite`` -- interpretive scaffolding: vocabulary only.
* ``yoneda`` -- interpretive scaffolding: discrete-Yoneda collapse,
  tested for shape, not load-bearing.
* ``colimits`` -- interpretive scaffolding: thin wrapper over the
  reconcile rules.

The interpretive modules earn their keep by providing a vocabulary that
makes the load-bearing claims easier to state and harder to misuse --
they are not, individually, results.

The category-theoretic story (ASCII-only for portability):

* The category Date has dates as objects and a unique ``<=`` arrow
  between any d1, d2 with d1 <= d2 (poset category).
* ``lineup_functor`` maps each date to its cumulative roster.
* ``setlist_functor`` maps each show date to the cumulative set of song
  slugs played up to that point.
* ``PerformanceSpan`` exhibits each performance as a 2-leg span
  ``Show <- Performance -> Song``.
* ``AudioEnrichedHom`` decorates arrows in the performance category with
  a non-negative similarity weight in [0, 1].
"""

from .categories import Category, build_date_category, build_show_category
from .colimits import colimit_cone_factors, colimit_of_setlist_functor, coproduct
from .enriched import AudioEnrichedHom
from .functors import active_lineup_presheaf, lineup_functor, setlist_functor
from .natural import (
    cardinality_eta,
    lineup_cardinality_transformation,
    naturality_square_holds,
    setlist_cardinality_transformation,
)
from .opposite import opposite
from .spans import PerformanceSpan, build_performance_spans
from .yoneda import representable_at, yoneda_bijection_count, yoneda_embed

__all__ = [
    "AudioEnrichedHom",
    "Category",
    "PerformanceSpan",
    "active_lineup_presheaf",
    "build_date_category",
    "build_performance_spans",
    "build_show_category",
    "cardinality_eta",
    "colimit_cone_factors",
    "colimit_of_setlist_functor",
    "coproduct",
    "lineup_cardinality_transformation",
    "lineup_functor",
    "naturality_square_holds",
    "opposite",
    "representable_at",
    "setlist_cardinality_transformation",
    "setlist_functor",
    "yoneda_bijection_count",
    "yoneda_embed",
]
