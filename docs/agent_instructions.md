# Agent Instructions — entofile

Read this before modifying `src/`, `tests/`, or `manuscript/`.

## Hard rules

1. **No mocks** — tests use real fixtures, temp files, ZIPs, crypto, generated reports, and subprocesses where needed. Label deterministic fixtures, synthetic stress tracks, and conformance vectors honestly.
2. **Thin scripts** — business logic in `src/` only; `scripts/` orchestrate I/O.
3. **Registry tokens** — numeric manuscript claims use `{{TOKEN}}`, not literals.
4. **Fail closed** — crypto and validation paths reject tampered inputs; do not swallow errors.
5. **Fixture loader** — use `src/fixtures.py::load_fixture_tracks`; do not duplicate mappings.
6. **Observability** — internal manifest is auditable; export level filters via `observability.py`.
7. **Development source vs public mirror** — commit project changes under the `projects/working/entofile` working tree (the development source), not public `template/` unless Layer 1. The public repository is `https://github.com/docxology/entofile`; keep it in sync from the working tree.
8. **Verify hostile archives** — run `verify -i container.ento.zip` before `unpack` on third-party inputs; never skip ZIP/member/digest checks.
9. **Security module** — path policy lives in `src/security.py`; do not duplicate track-id regex elsewhere.
10. **Proof export** — call `export_proof` on the **exported** manifest view, not the internal auditable manifest.

## Current release-evidence contract

- `scripts/run_tests.py` is the canonical test gate and writes the fail-closed test-result sidecar.
- Certifying publication checks must rerun live gates; side-file metadata is diagnostic evidence, not certification.
- Regenerate analysis, conformance, figure-layout, manuscript-variable, SBOM, and release artifacts before release claims.
- Local publication readiness and external public-endpoint readiness are separate states and must be reported separately.
- `experiment_plan.yaml` and [`research/agenda.md`](research/agenda.md) are the research source of truth: every cycle has at least three competing hypotheses, a control, exact metrics, falsification criteria, and a stopping rule.

## Verification checklist

```bash
uv run python scripts/run_tests.py
grep -r "unittest.mock\|MagicMock\|@patch" tests/ || echo "Clean"
uv run python scripts/ento_analysis.py
uv run python scripts/z_generate_manuscript_variables.py
uv run python scripts/audit_publication_readiness.py --check
grep -r "{{" output/manuscript/ || echo "Tokens resolved"
```

## See also

- [`security.md`](security.md)
- [`entofile-threat-model.md`](entofile-threat-model.md)
- [`evidence_provenance.md`](evidence_provenance.md)
- [`publication_checklist.md`](publication_checklist.md)
- [`redteam_publish_0.4.md`](redteam_publish_0.4.md)
- [`testing_philosophy.md`](testing_philosophy.md)
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md)
