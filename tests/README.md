# tests/

Run from the project root:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

No test doubles: `unittest.mock`, `MagicMock`, `patch`, and pytest `monkeypatch` are
prohibited. Use real temporary ZIPs, explicit environment restoration with
`try`/`finally`, real subprocesses, and explicit timeout parameters.
