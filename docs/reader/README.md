# Grateful Data HTML reader

Download the [reader ZIP](grateful-data-reader.zip), extract it, and open
`web/index.html`. Keep the `web/` and `figures/` directories together.
The HTML, figures, favicon, and text fonts are included. Typeset mathematics
uses MathJax 4.0.0 from jsDelivr and requires network access. External
bibliography links also open their source sites.

This HTML reader uses the manuscript source and archived analysis inputs
bound by the [render and package receipt](receipt.json). The receipt records
the authored source and Template revisions, the Stage 04 result, and the
SHA-256 of the ZIP and its entries. The [published v1.0.0 edition](https://doi.org/10.5281/zenodo.20482026)
remains available separately.

## Check or reproduce the archive

From the repository root, check the downloaded ZIP against the
`archive.sha256` value in the receipt.

```sh
sha256sum docs/reader/grateful-data-reader.zip
```

To recreate the same ZIP, use matching rendered files from the
[publication workflow](../rendering.md). Run this from the repository root
and provide the rendered Grateful Data worktree and an unused ZIP destination.

```sh
python - /path/to/rendered/grateful_data /path/to/new-reader.zip <<'PY'
from hashlib import sha256
import json
from pathlib import Path
import sys
from zipfile import ZIP_STORED, ZipFile, ZipInfo

rendered, destination = map(Path, sys.argv[1:])
archive = json.loads(Path("docs/reader/receipt.json").read_text())["archive"]
with ZipFile(destination, "x") as bundle:
    for name, expected in sorted(archive["entries"].items()):
        source = Path("LICENSE") if name == "LICENSE" else rendered / "output" / name
        payload = source.read_bytes()
        if sha256(payload).hexdigest() != expected["sha256"]:
            raise SystemExit(f"Render bytes differ for {name}")
        entry = ZipInfo(name, (1980, 1, 1, 0, 0, 0))
        entry.create_system = 3
        entry.external_attr = 0o100644 << 16
        bundle.writestr(entry, payload, compress_type=ZIP_STORED)

if sha256(destination.read_bytes()).hexdigest() != archive["sha256"]:
    raise SystemExit("Archive digest differs")
PY
```
