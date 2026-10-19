# References {#sec:references}

Bibliography lives in [the source bibliography](https://github.com/docxology/entofile/blob/c4445e46c8c10b18ac61afe735da80410e9c400e/docs/manuscript/references.bib) and is read by Pandoc during PDF render. Inline citations use `[@citekey]` syntax throughout introduction, methodology, related work, and limitations sections.

Validate bibliography syntax:

```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/working/entofile/docs/manuscript/references.bib --strict
```

Research notes backing related-work claims: [the related-format research notes](https://github.com/docxology/entofile/blob/c4445e46c8c10b18ac61afe735da80410e9c400e/docs/research/related_formats.md).
