# Documentation — entofile

Navigation hub for the ENTO format **0.4.0** reference implementation (0.4 paper
release). The public repository is
[github.com/docxology/entofile](https://github.com/docxology/entofile); the
maintainer's build and render path remains `projects/working/entofile`.

## Start here

| Audience | Document |
| --- | --- |
| First run | [`quickstart.md`](quickstart.md) |
| Operators | [`operator_checklist.md`](operator_checklist.md) |
| AI agents | [`agent_instructions.md`](agent_instructions.md) |
| Architecture | [`architecture.md`](architecture.md) |
| Manuscript tokens | [`syntax_guide.md`](syntax_guide.md) + [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) |
| Glossary | [`glossary.md`](glossary.md) |

## Pipeline and outputs

| Document | Topic |
| --- | --- |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Analysis → PDF |
| [`output_conventions.md`](output_conventions.md) | `output/` layout |
| [`output_inventory.md`](output_inventory.md) | Producer/consumer graph |
| [`evidence_provenance.md`](evidence_provenance.md) | Input/output provenance and no-mock evidence boundary |
| [`benchmark_profiles.md`](benchmark_profiles.md) | Release and expanded benchmark profiles |

## Quality

| Document | Topic |
| --- | --- |
| [`testing_philosophy.md`](testing_philosophy.md) | Zero mocks, coverage |
| [`style_guide.md`](style_guide.md) | Code and doc rules |
| [`troubleshooting.md`](troubleshooting.md) | Common failures |
| [`faq.md`](faq.md) | Quick answers |

## Research and methods

| Document | Topic |
| --- | --- |
| [`research/related_formats.md`](research/related_formats.md) | Related formats and security norms |
| [`research/reproducible_figures_crypto_vectors.md`](research/reproducible_figures_crypto_vectors.md) | Figure pipeline and crypto test strategy |
| [`redteam_publish_0.4.md`](redteam_publish_0.4.md) | RedTeam findings for release 0.4 RC |
| [`redteam_claim_scholarship_audit_0.4.md`](redteam_claim_scholarship_audit_0.4.md) | Repo-wide claim and scholarship RedTeam audit for release 0.4 RC |
| [`redteam_repo_visual_audit_0.4.md`](redteam_repo_visual_audit_0.4.md) | Repo-wide RedTeam and visualization confirmation for release 0.4 RC |
| [`redteam_publish_1.0.md`](redteam_publish_1.0.md) | Historical RedTeam findings for the previous release line |
| [`publication_checklist.md`](publication_checklist.md) | Pre-deposit gate commands |
| [`public_release_checklist.md`](public_release_checklist.md) | Public repository release gate |
| [`public_ci_dry_run.md`](public_ci_dry_run.md) | Non-publishing GitHub Actions dry-run map |
| [`release_notes_template.md`](release_notes_template.md) | Future release-note scaffold |
| [`nation_state_roadmap.md`](nation_state_roadmap.md) | Nation-state pillar gap analysis |
| [`methods.md`](methods.md) | Crypto, benchmarks, validation |
| [`security.md`](security.md) | Key handling, verify CLI, ZIP limits |
| [`entofile-threat-model.md`](entofile-threat-model.md) | AppSec threat model |
| [`format_migration.md`](format_migration.md) | Choosing default `0.4.0` or compatibility formats |
| [`provenance_signing.md`](provenance_signing.md) | Signing and SLSA-compatible release provenance |
| [`kms_hsm_profile.md`](kms_hsm_profile.md) | External key custody profile |
| [`pq_transition_note.md`](pq_transition_note.md) | Post-quantum integration note |
| [`streaming_design.md`](streaming_design.md) | Deferred streaming pack/unpack constraints |
| [`manifest_extension_policy.md`](manifest_extension_policy.md) | Future manifest field policy |
| [`figure_registry.md`](figure_registry.md) | Code-derived figure pipeline and visual evidence contract |

## Project root

- [`../AGENTS.md`](../AGENTS.md) — project API overview
- [`../README.md`](../README.md) — project summary
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution and verification guide
- [`../SECURITY.md`](../SECURITY.md) — coordinated vulnerability reporting
- [`../CITATION.cff`](../CITATION.cff) — citation metadata for public promotion
- [`../LICENSE`](../LICENSE) — MIT license text
