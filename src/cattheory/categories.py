"""Tiny finite-category infrastructure.

A :class:`Category` is a thin in-memory record of:

* a set of object identifiers (strings),
* a dict from ``(src, dst)`` to a tuple of arrow identifiers,
* a composition rule ``compose(f, g)`` that returns the composite arrow id.

We restrict to thin categories where there is at most one arrow per
``(src, dst)`` pair. That makes the laws cheap to check and the constructions
on the seed cleanly verifiable. Real-world cases (e.g. multiple distinct
performances of the same song in one show) are modelled in
``cattheory/spans.py``, not here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from typing import Callable

from ..integration.reconcile import Compendium


@dataclass(frozen=True)
class Category:
    """Tiny thin category.

    Invariants enforced by :meth:`check_laws`:

    * For every object ``o``, the identity arrow is present.
    * Composition is associative.
    * Identity acts as identity under composition.
    """

    name: str
    objects: tuple[str, ...]
    arrows: dict[tuple[str, str], str]
    compose: Callable[[str, str], str]
    identity_of: Callable[[str], str]

    def hom(self, src: str, dst: str) -> str | None:
        return self.arrows.get((src, dst))

    def check_laws(self, *, sample_size: int = 1000, seed: int = 0) -> tuple[bool, list[str]]:
        """Return (ok, failing_law_descriptions).

        Small categories are checked exhaustively. Large ones (the archival
        ``Date`` poset has ~2300 objects, and an exhaustive O(n²)–O(n³) sweep is
        intractable) are checked by verifying every identity *and* sampling
        random composable triples for associativity — so a broken ``compose``
        is caught with high probability rather than the law check silently
        degrading to "identities are present" (which proves almost nothing).
        """
        if len(self.objects) > 120:
            return self._check_laws_sampled(sample_size=sample_size, seed=seed)
        return self._check_laws_exhaustive()

    def _check_laws_sampled(self, *, sample_size: int, seed: int) -> tuple[bool, list[str]]:
        """Identity check + randomized associativity sampling for large categories."""
        import random

        issues: list[str] = []
        for o in self.objects:
            if self.identity_of(o) != self.arrows.get((o, o)):
                issues.append(f"identity missing on {o!r}")
        # Deterministic sampler: associativity on random composable triples.
        rng = random.Random(seed)
        arrow_keys = list(self.arrows.keys())
        # Index arrows by source for composability lookups.
        by_src: dict[str, list[tuple[str, str]]] = {}
        for a, b in arrow_keys:
            by_src.setdefault(a, []).append((a, b))
        checked = 0
        attempts = 0
        max_attempts = sample_size * 20
        while checked < sample_size and attempts < max_attempts:
            attempts += 1
            a, b = arrow_keys[rng.randrange(len(arrow_keys))]
            cand_g = by_src.get(b)
            if not cand_g:
                continue
            _b, c = cand_g[rng.randrange(len(cand_g))]
            cand_h = by_src.get(c)
            if not cand_h:
                continue
            _c, d = cand_h[rng.randrange(len(cand_h))]
            # Closure: the composite arrow (a -> c, a -> d) must be present in
            # the arrow set. This is the data-reachable law — a corrupted/
            # incomplete arrow table fails here even when ``compose`` is pure
            # string surgery whose algebraic associativity can never break.
            if (a, c) not in self.arrows:
                issues.append(f"closure fails: composite ({a},{c}) not in arrows")
            if (a, d) not in self.arrows:
                issues.append(f"closure fails: composite ({a},{d}) not in arrows")
            f, g, h = self.arrows[(a, b)], self.arrows[(b, c)], self.arrows[(c, d)]
            try:
                left = self.compose(self.compose(f, g), h)
                right = self.compose(f, self.compose(g, h))
            except (ValueError, KeyError) as exc:
                # A composite that is not itself composable is a closure/assoc
                # failure, not a crash — record it.
                issues.append(f"associativity/closure fails on ({f},{g},{h}): {exc}")
                checked += 1
                continue
            if left != right:
                issues.append(f"associativity fails on ({f},{g},{h}): {left} ≠ {right}")
            checked += 1
        return (len(issues) == 0, issues)

    def _check_laws_exhaustive(self) -> tuple[bool, list[str]]:
        """Full associativity / closure check (fine for seed-scale categories)."""
        issues: list[str] = []
        for o in self.objects:
            id_arrow = self.identity_of(o)
            if id_arrow != self.arrows.get((o, o)):
                issues.append(f"identity missing on {o!r}")
        for (a, b), f in self.arrows.items():
            for (b2, c), g in self.arrows.items():
                if b != b2:
                    continue
                gf = self.compose(f, g)
                if (a, c) not in self.arrows:
                    issues.append(f"composition {f}{g} closure missing for {(a, c)}")
                    continue
                if gf != self.arrows[(a, c)]:
                    issues.append(f"compose({f},{g}) = {gf} ≠ {self.arrows[(a, c)]}")
        # Identity law
        for (a, b), f in self.arrows.items():
            if self.compose(self.identity_of(a), f) != f:
                issues.append(f"left identity fails on {f}")
            if self.compose(f, self.identity_of(b)) != f:
                issues.append(f"right identity fails on {f}")
        return (len(issues) == 0, issues)


def _date_arrow(src: _date, dst: _date) -> str:
    return f"{src.isoformat()}->{dst.isoformat()}"


def build_date_category(dates: tuple[_date, ...]) -> Category:
    """The poset category of distinct dates with the ≤ arrow."""
    unique = tuple(sorted(set(dates)))
    objects = tuple(d.isoformat() for d in unique)
    arrows: dict[tuple[str, str], str] = {}
    for i, a in enumerate(unique):
        for j, b in enumerate(unique):
            if i <= j:
                arrows[(a.isoformat(), b.isoformat())] = _date_arrow(a, b)

    def compose(f: str, g: str) -> str:
        # f: a->b, g: b->c -> a->c
        a, b = f.split("->")
        b2, c = g.split("->")
        if b != b2:
            raise ValueError(f"non-composable arrows: {f}, {g}")
        return f"{a}->{c}"

    def identity_of(o: str) -> str:
        return f"{o}->{o}"

    return Category(
        name="Date",
        objects=objects,
        arrows=arrows,
        compose=compose,
        identity_of=identity_of,
    )


def build_show_category(compendium: Compendium) -> Category:
    """The discrete category whose objects are the compendium's show slugs."""
    objects = tuple(sorted(s.slug for s in compendium.shows))
    arrows = {(o, o): f"id_{o}" for o in objects}

    def compose(f: str, g: str) -> str:
        if f != g:
            raise ValueError("only identities compose in a discrete category")
        return f

    def identity_of(o: str) -> str:
        return f"id_{o}"

    return Category(
        name="Show",
        objects=objects,
        arrows=arrows,
        compose=compose,
        identity_of=identity_of,
    )
