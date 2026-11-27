# Grateful Data documentation

Grateful Data reconciles setlists and related metadata into a queryable
compendium. It derives repertoire, transition, and venue summaries and binds
them to figures, source records, and claim limits. The [project README](../README.md)
provides the overview and citation.

| Guide | Use it to |
| --- | --- |
| [Published manuscript on Zenodo](https://doi.org/10.5281/zenodo.20482026) | Read the archived v1.0.0 edition |
| [Publication guide](rendering.md) | Rebuild and validate the manuscript and figures with the pinned Template |
| [Publication artifacts](artifacts.md) | Inspect the dashboard, explorer, figure tables, and provenance |
| [Canonical manuscript](manuscript/README.md) | Edit sections, configuration, and BibTeX |
| [Source bibliography](bibliography.md) | Review the Markdown bibliography consumed by the citation importer |
| [Archival input record](../data/archival/README.md) | Trace the sources, coverage, and protected-content limits of the retained data |
| [Command inventory](../scripts/README.md) | Locate the numbered analysis and reporting scripts |
| [Backlog](backlog.md) and [project history](project-history.md) | Find follow-ups and archived engineering decisions |

## Setup

Use [uv](https://docs.astral.sh/uv/) from the repository root. The package
supports Python 3.11 or newer. Use Python 3.14 or newer for the pinned
Template integration.

```bash
uv sync --locked --python 3.14 --extra dev
```

The CLI entry point is `python -m src.cli`. Pipeline stages live in
`scripts/`. The test dependencies are in the `dev` extra.

## Offline replay

Use the default seed tier for examples. Set `GRATEFUL_DATA_TIER=archival`
for a command that should read the retained archival snapshot.

```bash
uv run --locked python -m src.cli stats
GRATEFUL_DATA_TIER=archival uv run --locked python -m src.cli stats
GRATEFUL_DATA_TIER=archival uv run --locked python -m src.cli provenance songs scarlet_begonias
```

Seed rows in `data/seed/` are fixtures and curated examples. Archival rows
in `data/archival/` are compiled from the recorded providers, including
gdshowsdb and truckin-through-time gap-fill. The manuscript uses the archival
tier. Source layers have different coverage. Count corpus show records
separately from estimates of canonical concerts. Recordings and lyrics are
represented as metadata and source pointers.

Run the [publication guide](rendering.md) from a disposable worktree when
regenerating reports or figures, since the repository tracks prior output
snapshots. For the native test gate in that worktree, set
`TEMPLATE_REPO_ROOT` to the pinned Template path and run:

```bash
uv run --locked --extra dev pytest tests/ --cov=src --cov-fail-under=90
```

The publication smoke test invokes hydration and writes derived files into
the active worktree. It uses the repository's retained archival inputs and
reports.
