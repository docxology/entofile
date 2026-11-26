# Quickstart

Use Python 3.15 and uv from an entofile checkout. The CLI reads and writes ENTO
wire format 0.5.0. The paper release label and the wire version have different
roles.

```sh
uv sync --locked --extra dev
uv run entofile genkey -o master.key
uv run entofile pack -k master.key -o example.ento.zip
uv run entofile verify -i example.ento.zip -k master.key
uv run entofile unpack -i example.ento.zip -k master.key -o decrypted
```

The default pack uses the bundled deterministic example tracks. Use a private
working directory for the key and keep it separate from the archive. Verify
before extracting input from a third party. See the [operator
checklist](operator_checklist.md) for input handling and sidecar restrictions,
and the [wire format profile](format_0_5_0.md) for the manifest and track
contracts.

## Reproduce benchmark data

```sh
uv run python scripts/ento_analysis.py
uv run python scripts/check_figure_layout.py
```

The default benchmark configuration lives in
[the manuscript config](manuscript/config.yaml). The CSV under
`output/data/ento_benchmark_results.csv` records raw measurements, including
wall-clock timings. The benchmark fingerprint binds the deterministic fields.
The [methods](methods.md#determinism-contract) and [output
inventory](output_inventory.md) explain which measurements are repeatable and
which files supply manuscript claims. Use [benchmark
profiles](benchmark_profiles.md) for the separate expanded run.

## Render and verify

The [rendering pipeline](rendering_pipeline.md) registers a clean entofile
checkout inside the pinned Template SDK and builds the analysis, manuscript,
and release evidence. The complete suite exercises publication metadata and
expects real generated artifacts. After the initial render and bundle, run
`uv run python scripts/run_tests.py` in the staged entofile checkout. Re-render
to incorporate the test results before taking the final artifact snapshot.

Once analysis has created the benchmark CSV and figures, check local
navigation from the entofile checkout with Lychee:

```sh
git diff --check
lychee --offline README.md AGENTS.md TODO.md CONTRIBUTING.md SECURITY.md 'docs/**/*.md'
```
