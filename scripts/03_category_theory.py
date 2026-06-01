#!/usr/bin/env python3
"""Verify the category-theoretic laws and dump a report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.cattheory import (  # noqa: E402
    build_date_category,
    build_performance_spans,
    build_show_category,
)
from src.cattheory.colimits import colimit_cone_factors  # noqa: E402
from src.cattheory.functors import (  # noqa: E402
    active_lineup_presheaf,
    is_monotone,
    lineup_functor,
    setlist_functor,
)
from src.cattheory.spans import (  # noqa: E402
    projections_commute_with_setlist_functor,
)
from src.cattheory.yoneda import yoneda_lemma_holds_for_setlist  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402
from src.viz.panels import categorical_summary  # noqa: E402


def main() -> None:
    out_dir = ROOT / "output" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp = load_seed_compendium()

    date_cat = build_date_category(tuple(s.date for s in comp.shows))
    show_cat = build_show_category(comp)
    date_ok, date_issues = date_cat.check_laws()
    show_ok, show_issues = show_cat.check_laws()

    F_setlist = setlist_functor(comp)
    F_lineup = lineup_functor(comp)
    P_active = active_lineup_presheaf(comp)
    spans = build_performance_spans(comp)
    cat = categorical_summary(comp)
    # A mid-corpus date for the Yoneda witness (deterministic).
    mid_date = sorted(F_setlist)[len(F_setlist) // 2] if F_setlist else ""

    report = {
        "Date category laws": {
            "ok": date_ok,
            "n_objects": len(date_cat.objects),
            # Large posets use the randomized associativity sampler, not an
            # exhaustive sweep; small ones are checked exhaustively.
            "law_check": "sampled" if len(date_cat.objects) > 120 else "exhaustive",
            "issues": date_issues,
        },
        "Show category laws": {
            "ok": show_ok,
            "n_objects": len(show_cat.objects),
            "law_check": "sampled" if len(show_cat.objects) > 120 else "exhaustive",
            "issues": show_issues,
        },
        "setlist_functor monotone": cat["setlist_functor_monotone"],
        "lineup_functor monotone": cat["lineup_functor_monotone"],
        "active_lineup_presheaf expected_non_monotone": cat[
            "active_lineup_presheaf_expected_non_monotone"
        ],
        "active_lineup_presheaf monotone": is_monotone(P_active),
        "cardinality_eta naturality_holds": cat["cardinality_eta_naturality_holds"],
        "colimit_universal_property_holds": colimit_cone_factors(F_setlist),
        "span_projections_commute_with_setlist_functor": (
            projections_commute_with_setlist_functor(comp)
        ),
        "yoneda_lemma_holds_for_setlist_at_mid_date": (
            yoneda_lemma_holds_for_setlist(comp, mid_date) if mid_date else False
        ),
        "n_performance_spans": len(spans),
        "cumulative_setlist_cardinality_end": len(F_setlist[max(F_setlist)]),
        "cumulative_lineup_cardinality_end": len(F_lineup[max(F_lineup)]),
    }
    out = out_dir / "category_theory_report.json"
    with out.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(out)


if __name__ == "__main__":
    main()
