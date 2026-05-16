# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-05-16

### Added
- Initial release.
- `CryptoVol` synchronous client with `vol_index`, `vol_surface`, `vol_surface_bulk`, `vol_history`.
- Typed Pydantic v2 response models with `.to_dataframe()` helpers (optional `[pandas]` extra).
- Exception hierarchy: `AuthenticationError`, `PlanLimitError`, `NotFoundError`, `ValidationError`, `RateLimitError`, `ServerError`, `TimeoutError`.
- Automatic retries with exponential backoff for 5xx and 429.
- Examples in `examples/` covering smile reconstruction, vol-index plotting, risk-reversals, and Greeks.
