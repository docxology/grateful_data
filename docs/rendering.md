# Replay and render the manuscript

Read the [published v1.0.0 manuscript](https://doi.org/10.5281/zenodo.20482026)
for the archived edition. The HTML tracked in Git under `output/web/`
is from an earlier run and retains that run’s browser title and reference
format. The steps below generate a current local reader.

Use a clean disposable Grateful Data worktree. Analysis and rendering
overwrite paths under `output/`, which also contains the repository's
historical snapshots. The editable paper is
[`docs/manuscript/`](manuscript/README.md) and the hydrated copy is
`output/manuscript/`.

Set up a separate checkout of [Template at the pinned revision](https://github.com/docxology/template/tree/56611eeb1074ea606a46d0b7c65d46c597bb1bac)
following the [pinned runtime guide](https://github.com/docxology/template/blob/56611eeb1074ea606a46d0b7c65d46c597bb1bac/docs/RUN_GUIDE.md).
The local render uses Python 3.14, Pandoc 3.14 with its matching pandoc-crossref
0.3.26 build, and a LaTeX distribution.

From the Template checkout root, select the pinned revision before preparing
the Grateful Data worktree. The archival pipeline uses Template to hydrate the
manuscript on its final step.

```bash
git switch --detach 56611eeb1074ea606a46d0b7c65d46c597bb1bac
```

## Rebuild from the archival snapshot

From the Grateful Data worktree root:

```bash
uv sync --locked --python 3.14 --extra dev
export TEMPLATE_REPO_ROOT=/absolute/path/to/template
uv run --locked --extra dev python scripts/99_pipeline.py --tier archival
```

The archival pipeline reads the checked-in inputs with no fetch flags. It
recomputes the compendium, report JSON, figure images and plotted rows,
provenance and pointer-only manifests, the figure registry for Template, and
manuscript variables. The shared
hydrator writes the derived sections from those variables and their source
configuration. Run the [native test gate](README.md#offline-replay) after
the replay and before final parent validation.

Start a source rebuild from the checked-in archival inputs. The tracked
`output/` snapshots record earlier runs. Some of their generated files
differ from the outputs of the current archival pipeline. The retained
figure-reference render check reused a prepared set of current archival
outputs. It verifies how Template renders those inputs. The archival
pipeline and the project validator below cover input reconstruction and
project output checks, respectively.

## Render and verify

From the Template checkout root, register the same Grateful Data worktree and
use the project-local environment prepared above for its hydration hook.
A worktree directly under `projects/working/grateful_data` already satisfies
the registration.

```bash
mkdir -p projects/working
ln -s /absolute/path/to/grateful_data projects/working/grateful_data
uv run --locked python scripts/pipeline/stage_03_render.py --project working/grateful_data
```

Inspect the newly generated combined PDF `output/pdf/grateful_data_combined.pdf`
and HTML `output/web/index.html` in the disposable Grateful Data worktree. Check the
ordered sections, resolved citations, and figure images against the
[figure-data and provenance paths](artifacts.md).

Run the project's publication validator from the Grateful Data root.

```bash
uv run --locked python scripts/20_validate_publication_outputs.py --strict
```

After output writing is finished, run the final Template validation from
the Template root.

```bash
uv run --locked python scripts/pipeline/stage_04_validate.py --project working/grateful_data
```

The project validator writes `output/reports/publication_validation.json`.
The final parent stage writes `output/reports/validation_report.json` and
`output/reports/rendered_provenance.json`.

The [legacy stage receipts](../output/reports/snapshots/legacy-template/)
retain the earlier Template run's metadata. Stage 04 reads current receipts
from `output/.pipeline/artifacts/`.
