# tests/

Run from the project root:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

No mocks policy — temp ZIP fixtures and subprocess CLI only.
