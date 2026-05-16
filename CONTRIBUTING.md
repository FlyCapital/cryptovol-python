# Contributing

Thanks for your interest in improving `cryptovol-python`! Bug reports, docs fixes, and feature PRs are all welcome.

## Set up

```bash
git clone https://github.com/FlyCapital/cryptovol-python.git
cd cryptovol-python
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,docs]"
```

## Run the test suite

```bash
pytest                # all tests
pytest --cov          # with coverage
ruff check cryptovol  # lint
```

The default test suite uses `pytest-httpx` and runs entirely offline — no API key required.

## Build the docs locally

```bash
mkdocs serve
# open http://127.0.0.1:8000
```

## Submitting a PR

1. Open an issue first for non-trivial changes so we can align on scope.
2. Add or update tests covering your change.
3. Run `ruff check cryptovol` and `pytest` before pushing.
4. Update `CHANGELOG.md` under an `## [Unreleased]` heading.

## Reporting bugs

Please include:

- A minimal repro snippet (omit your API key).
- The full traceback / error message.
- `python --version`, `cryptovol.__version__`.
