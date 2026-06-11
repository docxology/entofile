# Reproducibility {#sec:reproducibility}

Configuration hash: `{{CONFIG_HASH}}` (SHA-256 prefix of `manuscript/config.yaml`, version {{CONFIG_VERSION}}).

Author: {{CONFIG_FIRST_AUTHOR}}. Keywords: {{CONFIG_KEYWORDS}}.

## Regenerate artifacts

```bash
uv run python scripts/ento_analysis.py
uv run python scripts/build_dashboard.py
uv run python scripts/audit_publication_readiness.py --check
uv run python scripts/z_generate_manuscript_variables.py   # run last: re-binds manuscript variables to the final CSV
```

The variable-injection step is run **last** on purpose: live readiness checks exercise the real project tree and may refresh benchmark-derived artifacts with newly measured wall-clock timings. Regenerating the manuscript variables afterward keeps the injected statistics and the recorded `BENCHMARK_CSV_SHA256` bound to the same CSV that ships, without treating the whole CSV hash as a cross-run reproducibility target.

Third-party containers: run `verify` before `unpack` (see [@sec:limitations]).

The reproducibility contract is deliberately operational rather than rhetorical:
scripts, fixture classes, generated reports, rendered outputs, and validation
commands are named so a reader can rerun or inspect the same evidence surface
[@sandve2013reproducible; @wilson2017goodenough]. ENTO does not claim that this
private RC already satisfies an external artifact-review badge; it does organize
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

![{{FIG_CAPTION_RELEASE_EVIDENCE_MAP}}](../output/figures/release_evidence_map.png){#fig:release_evidence_map width={{FIGURE_WIDTH}}%}

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
[`docs/evidence_provenance.md`](../docs/evidence_provenance.md).

## Fixture digests

| Fixture | SHA-256 |
| --- | --- |
| `eeg.csv` | `{{FIXTURE_EEG_SHA256}}` |
| `sample.vcf` | `{{FIXTURE_VCF_SHA256}}` |
| `spectrogram.bin` | `{{FIXTURE_SPECTROGRAM_SHA256}}` |

Claim bindings are declared in `data/claim_ledger.yaml` and documented in `docs/claim_ledger.md`. Tests: `tests/test_claim_ledger.py`, `tests/test_claim_ledger_security.py` (tamper rate, container verification report, GCM backend claim). The current release-candidate build path is the private `projects/working/entofile` tree rendered through the template with `--project working/entofile`; the planned public home is `https://github.com/docxology/entofile` after release readiness, not a separate source of truth for these artifacts.

Generated at: {{GENERATION_TIMESTAMP}}
