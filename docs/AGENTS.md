# docs/ — entofile Agent Hub

Operational documentation for the ENTO project. Pipeline gates do not parse these files; they prevent agent and contributor drift. The public home is `https://github.com/docxology/entofile`; this working tree remains the source of truth until local and external release evidence are recorded.

## File inventory

| File | Purpose |
| --- | --- |
| `README.md` | Navigation hub |
| `AGENTS.md` | This index |
| `agent_instructions.md` | Hard rules (read first) |
| `architecture.md` | Layer diagram and module map |
| `quickstart.md` | First-run commands |
| `syntax_guide.md` | `{{TOKEN}}` reference |
| `rendering_pipeline.md` | Manuscript → PDF |
| `output_conventions.md` | `output/` layout |
| `output_inventory.md` | Artifact graph |
| `testing_philosophy.md` | Zero mocks, coverage |
| `style_guide.md` | Code/doc conventions |
| `faq.md` | Common questions |
| `troubleshooting.md` | Failure recipes |
| `research/related_formats.md` | Related work notes |
| `research/agenda.md` | Preregistered research questions, hypotheses, metrics, and stopping rules |
| `research/agenda.yaml` | Machine-readable research backlog and preregistration contract |
| `methods.md` | Crypto and benchmark methods |
| `figure_registry.md` | Figure pipeline, registry, and visual evidence contract |
| `security.md` | Key handling, verify CLI, ZIP limits |
| `entofile-threat-model.md` | AppSec threat model (TM-001-008) |
| `nation_state_roadmap.md` | Nation-state pillar gap analysis |
| `research/reproducible_figures_crypto_vectors.md` | Figure pipeline and crypto test strategy |

## Read order

1. `agent_instructions.md`
2. `architecture.md`
3. `testing_philosophy.md`
4. `rendering_pipeline.md`
5. `../manuscript/AGENTS.md`

## Verification

```bash
uv run python scripts/run_tests.py
uv run python scripts/ento_analysis.py
uv run python scripts/z_generate_manuscript_variables.py
```

## Cross-references

- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md)
- [`../src/AGENTS.md`](../src/AGENTS.md)
- [`../../../AGENTS.md`](../../../AGENTS.md) — template root
