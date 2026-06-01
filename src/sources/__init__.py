"""Source-specific ingestion modules.

Every module exposes:

* a ``parse(payload)`` function that converts a source-shaped record into one
  or more ``models.*`` instances, and
* a ``CITATION_KEY`` string that points into ``manuscript/references.bib``.

This protocol lets ``integration.reconcile`` treat each source uniformly while
keeping source-specific parsing logic isolated and independently testable.
"""

from . import (
    alex_allan,
    cmu_setlists,
    dead_net,
    gdsets,
    gdshowsdb,
    internet_archive,
    seed_bundle,
    setlist_program,
    setlistfm,
    wikipedia,
)

__all__ = [
    "alex_allan",
    "cmu_setlists",
    "dead_net",
    "gdsets",
    "gdshowsdb",
    "internet_archive",
    "seed_bundle",
    "setlist_program",
    "setlistfm",
    "wikipedia",
]


SOURCES = (
    setlistfm,
    setlist_program,
    cmu_setlists,
    gdsets,
    gdshowsdb,
    internet_archive,
    alex_allan,
    dead_net,
    wikipedia,
    seed_bundle,
)
"""All registered source modules, in canonical ordering."""
