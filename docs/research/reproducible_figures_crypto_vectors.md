# Reproducible figures and crypto verification (research notes)

External synthesis for ENTO default format 0.5.0 design choices and the
0.2.0-0.4.0 compatibility ladder. Complements [`related_formats.md`](related_formats.md).

## Figure pipelines (2024–2026 practice)

| Pattern | Role in ENTO |
| --- | --- |
| Declarative figure registry (label → generator → CSV source) | `src/figure_registry.py::FIGURE_SPECS` |
| Config-driven rendering (DPI, figsize from YAML) | `manuscript/config.yaml` → `experiment.viz` → `configure_viz()` |
| Machine-readable provenance JSON | `output/figures/figure_registry.json` with `generated_by`, `csv_source`, `takeaway`, `evidence`, and `caution` |
| Validation gate before PDF render | `validate_generated_outputs()` checks PNG set + registry + tamper rate |

**Recommendation applied:** keep analysis CSV as the single numerical source of truth; generators read only that file; manuscript prose references `[[FIG:...]]` labels bound to registry entries, not hand-placed PNG paths. Each figure also carries an explicit visual contract: the intended takeaway, the generated evidence that backs it, and the caution that prevents over-reading.

**FigureManager integration:** optional `register_with_infrastructure()` registers with Layer 1 `FigureManager`; `write_figure_registry()` runs last so project-specific provenance fields are not clobbered.

## Bioacoustic / multimodal containers

WAV + sidecar JSON is common for field recordings but splits integrity across files. Custom binary containers (e.g. spectrogram blobs) allow typed tracks with unified manifests. ENTO format 0.2.0 uses ZIP + per-track AEAD headers rather than WAV-in-zip alone, so tamper checks apply per track without an external sidecar.

## HKDF-SHA256 test strategy

| Approach | When to use |
| --- | --- |
| RFC 5869 / NIST known-answer vectors | Required before claiming standards interoperability |
| Pinned regression vectors from live implementation | Honest gate for stdlib-first v0.1 reference code |

ENTO format **0.5.0** uses **pinned regression vectors** (`data/test_vectors/hkdf_regression.json`, `aes256_gcm_regression.json`) plus format-specific tests to lock HKDF, GCM, manifest-context AAD, canonicalization, and PADMÉ behavior across refactors; compatibility `0.2.0`-`0.4.0` paths remain covered so older containers stay readable.

## References

See `manuscript/references.bib` for cited standards (HKDF, AES-GCM, FAIR, RO-Crate, BagIt, etc.).
