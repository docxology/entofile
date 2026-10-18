# References {#sec:references}

Bibliography lives in [`docs/manuscript/references.bib`](https://github.com/docxology/entofile/blob/b88a050587603bf3d42290252d5b2c46571c8456/docs/manuscript/references.bib) and is read by Pandoc during PDF render. Inline citations use `[@citekey]` syntax throughout introduction, methodology, related work, and limitations sections.

Validate bibliography syntax:

```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/working/entofile/docs/manuscript/references.bib --strict
```

Research notes backing related-work claims: [`../docs/research/related_formats.md`](https://github.com/docxology/entofile/blob/b88a050587603bf3d42290252d5b2c46571c8456/docs/research/related_formats.md).
