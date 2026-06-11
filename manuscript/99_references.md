# References {#sec:references}

Bibliography lives in [`manuscript/references.bib`](references.bib) and is read by Pandoc during PDF render. Inline citations use `[@citekey]` syntax throughout introduction, methodology, related work, and limitations sections.

Validate bibliography syntax:

```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/working/entofile/manuscript/references.bib --strict
```

Research notes backing related-work claims: [`../docs/research/related_formats.md`](../docs/research/related_formats.md).
