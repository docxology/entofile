# Reproducibility {#sec:reproducibility}

Configuration hash: `{{CONFIG_HASH}}` (SHA-256 prefix of `docs/manuscript/config.yaml`, version {{CONFIG_VERSION}}).

Author: {{CONFIG_FIRST_AUTHOR}}. Keywords: {{CONFIG_KEYWORDS}}.

## Regenerate artifacts

```bash
uv run python scripts/ento_analysis.py
uv run python scripts/build_dashboard.py
uv run python scripts/generate_conformance_fixtures.py
uv run python scripts/verify_conformance_fixtures.py
uv run python scripts/check_figure_layout.py
uv run python scripts/generate_api_docs.py
uv run python scripts/export_sbom.py
```

These commands prepare independent evidence; they are not the complete publication
gate. Follow the [ordered rendering and certification procedure](https://github.com/docxology/entofile/blob/c4445e46c8c10b18ac61afe735da80410e9c400e/docs/rendering_pipeline.md):
render actual reader products, build the bootstrap release envelope, run
`scripts/run_tests.py`, and hydrate/render again with measured coverage. Then run
`scripts/audit_publication_readiness.py --check` in the SDK environment, snapshot
the complete inventory with `scripts/maintenance/refresh_artifact_manifests.py`,
and run `scripts/pipeline/stage_04_validate.py`. Build the outer release envelope
last, outside `output/`, and verify all checksums. If any producer changes an
input after hydration, repeat hydration/rendering, certification, and finalization;
never ship a manuscript whose `BENCHMARK_CSV_SHA256` differs from the final CSV.

Third-party containers: run `verify` before `unpack` (see [@sec:limitations]).

The reproducibility contract is deliberately operational rather than rhetorical:
scripts, fixture classes, generated reports, rendered outputs, and validation
commands are named so a reader can rerun or inspect the same evidence surface
[@sandve2013reproducible; @wilson2017goodenough]. ENTO does not claim that this
release candidate already satisfies an external artifact-review badge; it does organize
the release artifacts around the same availability/functionality/reusability
distinctions [@acm2024artifactbadging].

The project test gate requires {{TEST_COVERAGE_MIN}}% coverage on `src/` with no
mocks (measured {{MEASURED_COVERAGE_PERCENT}}% on the latest pipeline run;
no-mock scan: `{{NO_MOCK_STATUS}}`). "No mocks" means real ZIP, crypto,
filesystem, subprocess, and report execution over documented fixture,
synthetic-stress, and conformance-vector inputs; it does not mean every input
byte is a real-world observational dataset. Benchmark CSV path:
`output/data/ento_benchmark_results.csv` (SHA-256:
`{{BENCHMARK_CSV_SHA256}}`). This hash is a single-run provenance stamp, not a
reproducibility target: the CSV's timing columns (`pack_seconds`,
`unpack_seconds`, `pack_throughput_mib_s`) are re-measured on every run, so each
regeneration yields a new CSV and a new hash. The byte-exact, run-invariant
quantities are the data-derived columns — `expansion_ratio`, `manifest_bytes`,
and the tamper-detection outcomes — which follow the closed-form law of
[@eq:expansion_law] and reproduce identically across runs.

Those deterministic columns are bound by a dedicated **data fingerprint**: `{{BENCHMARK_DATA_FINGERPRINT}}`. It is the SHA-256 of only the run-invariant benchmark columns (condition, track and byte counts, expansion ratio, manifest bytes, tamper outcomes), computed row-order-independently and over canonicalized numeric values — so it depends on the *values*, not on how they happen to be spelled — by `benchmark_data_fingerprint` in `src/benchmark_stats.py`. Unlike the whole-CSV hash, this fingerprint *is* a reproducibility target — regenerating the pipeline on any host reproduces it exactly (`tests/test_data_fingerprint.py`), and a mismatch signals real corruption of the deterministic data rather than wall-clock noise. It is the honest counterpart to the closed-form expansion law: the parts of the benchmark that are determined by the format, fingerprinted; the parts that are measured, reported with their dispersion ([@sec:benchmark_interpretation]).

## Registered figures

{{FIGURE_INDEX}}

The registry lists {{FIGURE_COUNT}} figures at {{CONFIG_VIZ_DPI}} DPI. Each entry records `generated_by`, CSV provenance, and a `caption_token` mirrored in the manuscript figure-caption variables. After analysis, metadata is written to `{{FIGURE_REGISTRY_PATH}}`.

![{{FIG_CAPTION_RELEASE_EVIDENCE_MAP}}](../../output/figures/release_evidence_map.png){#fig:release_evidence_map width={{FIGURE_WIDTH}}%}

[@fig:release_evidence_map] summarizes the generated evidence surface for paper {{PAPER_VERSION}} and default format {{FORMAT_VERSION}}: benchmark CSV, registered figures, conformance vectors, SBOM, release manifest checksums, and rendered PDF/HTML outputs.

## Artifact inventory

| Category | Files |
| --- | --- |
| Figures (`output/figures/`) | {{ARTIFACT_FIGURES}} |
| Data (`output/data/`) | {{ARTIFACT_DATA_FILES}} |
| SBOM | {{SBOM_STATUS}} at `{{SBOM_PATH}}` (components: {{SBOM_COMPONENT_COUNT}}) |

Evidence reports: conformance status `{{CONFORMANCE_REPORT_STATUS}}` at
`{{CONFORMANCE_REPORT_PATH}}`; artifact manifest status
`{{ARTIFACT_MANIFEST_STATUS}}` at `{{ARTIFACT_MANIFEST_PATH}}`; release manifest
status `{{RELEASE_MANIFEST_STATUS}}` at `{{RELEASE_MANIFEST_PATH}}`. The evidence
provenance contract is maintained in
[the input and output provenance contract](https://github.com/docxology/entofile/blob/c4445e46c8c10b18ac61afe735da80410e9c400e/docs/evidence_provenance.md).

## Fixture digests

| Fixture | SHA-256 |
| --- | --- |
| `eeg.csv` | `{{FIXTURE_EEG_SHA256}}` |
| `sample.vcf` | `{{FIXTURE_VCF_SHA256}}` |
| `spectrogram.bin` | `{{FIXTURE_SPECTROGRAM_SHA256}}` |

Claim bindings are declared in `data/claim_ledger.yaml` and documented in `docs/claim_ledger.md`. Tests: `tests/test_claim_ledger.py`, `tests/test_claim_ledger_security.py` (tamper rate, container verification report, GCM backend claim). The release-candidate build uses a physical consumer clone at `projects/working/entofile` under the pinned template SDK and renders with `--project working/entofile`. Public source is `https://github.com/docxology/entofile`; a local readiness pass does not prove an uploaded, signed, or paired publication.

Generated at: {{GENERATION_TIMESTAMP}}
