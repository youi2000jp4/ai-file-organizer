# Contributing to ai-file-organizer

First off, thank you for considering contributing! 🎉

## Quick start

```bash
# Clone and install in editable mode with dev deps
git clone https://github.com/yourusername/ai-file-organizer.git
cd ai-file-organizer
pip install -e ".[dev]"

# Run tests
pytest

# Lint & format
ruff check src tests
ruff format src tests

# Type check
mypy src
```

## How to contribute

### Reporting bugs
Open a [Bug Report](https://github.com/yourusername/ai-file-organizer/issues/new?template=bug_report.yml).  
Include: OS, Python version, `file-org --version`, and the exact command you ran.

### Requesting features
Open a [Feature Request](https://github.com/yourusername/ai-file-organizer/issues/new?template=feature_request.yml).

### Pull requests

1. Fork the repo and create a branch: `git checkout -b feat/my-feature`
2. Make your changes with tests
3. Ensure `pytest`, `ruff check`, and `mypy` all pass
4. Open a PR against `main` with a clear description

## Code style

- **Formatter**: `ruff format` (Black-compatible, 100-char lines)
- **Linter**: `ruff check` — fix issues before committing
- **Type hints**: All public functions must have complete type annotations
- **Tests**: New features need tests; bug fixes should add a regression test
- **Comments**: Only when the *why* is non-obvious

## Project structure

```
src/file_organizer/
├── cli.py        # Typer commands — keep thin, delegate to organizer
├── organizer.py  # Core logic: scan, plan, execute
├── llm.py        # LLM API calls — isolated for easy testing/mocking
├── config.py     # Pydantic settings + TOML persistence
└── models.py     # Pure data models (no side effects)
```

## Adding a new LLM provider

1. Add config fields in `config.py`
2. Update `effective_api_key`, `effective_base_url`, `effective_model` properties
3. The `LLMClient` in `llm.py` uses the OpenAI-compatible API — most providers work out of the box

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
