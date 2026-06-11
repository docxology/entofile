# RedTeam — entofile publish 1.0 (2026-05-25)

Workflow: **VectorSpecialists** with PHASE 1A verifier attack. Target: `projects/active/entofile` pre-release 1.0.

## PHASE 1A — Oracle attack

| Oracle | Verdict | Finding |
| --- | --- | --- |
| `validate_generated_outputs()` | **INCOMPLETE → fixed** | Verified first sorted `*.ento.zip`, which was `bad.ento.zip` (tamper fixture). Gate falsely failed on clean pipelines. |
| Evidence registry (Stage 6) | **INCOMPLETE → fixed** | Flagged `90%` figure widths and literal `32` key sizes not in claim ledger. Blocked publication validation. |
| `inspect_container()` | **INCOMPLETE → fixed** | Did not enforce ZIP size limits or member-set equality before returning manifest. |

## Concrete findings (file:line)

### RT-001 — Tamper fixture poisoned analysis gate

- **File:** `src/analysis.py` `_verify_benchmark_containers`
- **Issue:** Alphabetical first sample could be `bad.ento.zip` from tamper benchmarks.
- **Fix:** Exclude `bad.ento.zip`; prefer `medium_3.ento.zip`; delete fixture after tamper test in `src/benchmarks.py`.
- **Negative control:** Run pipeline twice; `containers_ok` stays true.

### RT-002 — Evidence registry false positives

- **Files:** `manuscript/03_results.md`, `02_methodology.md`, `06_reproducibility.md`, `08_limitations_and_threat_model.md`
- **Issue:** Hard-coded `90%`, `32` without claim ledger bindings.
- **Fix:** Claim ledger entries + tokens `{{TEST_COVERAGE_MIN}}`, `{{MASTER_KEY_BYTES}}`, `{{FIGURE_WIDTH}}`, `{{MEASURED_COVERAGE_PERCENT}}`.

### RT-003 — `inspect` weaker than `verify`

- **File:** `src/container.py` `inspect_container`
- **Issue:** Read manifest without ZIP limits or member-set check.
- **Fix:** Call `validate_zip_archive` and `assert_zip_members_match_manifest` before return.
- **Test:** `tests/test_container_security.py::test_inspect_rejects_oversize_zip`

### RT-004 — Residual (documented, not fixed in v1.0)

- **File:** `src/crypto.py` — custom AES/HKDF (TM-005). Nation-state track: audited backend v0.2.
- **File:** `manuscript/config.yaml` — empty DOI. Operator action before cite-ready deposit.
- **File:** `src/security.py` — no Sigstore/SBOM (TM-006). See `docs/nation_state_roadmap.md`.

### RT-005 — Benchmark report overwritten by Stage 6

- **File:** `output/reports/validation_report.json` (shared name)
- **Issue:** Pipeline Stage 6 validation overwrote benchmark tamper report; `validate_generated_outputs` read `tamper_detection_rate: 0.0`.
- **Fix:** Benchmark gate now writes `benchmark_validation.json`; Stage 6 keeps `validation_report.json`.


- `src/publication.py::check_publication_readiness`
- `scripts/audit_publication_readiness.py --check`

## Quality check

- Entry points covered: CLI pack/unpack/verify/inspect, analysis pipeline, publication audit.
- Trust boundaries reflected in `docs/entofile-threat-model.md`.
- Runtime vs CI separated in threat model §Quality check.
