# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] — 2026-05-30

### Changed (breaking)
- **Auth header changed**: the SDK now sends `X-CryptoVol-Key` instead of
  `X-RapidAPI-Key`. Pass your `cvk_live_...` key (from
  [cryptovol.io/account](https://www.cryptovol.io/account)) as `api_key=` —
  the SDK handles the rest.
- **Default `base_url`** moved from the RapidAPI gateway to the
  self-hosted CryptoVol API at `https://cryptovol-api-nbakzshi6q-uc.a.run.app`.
  If you have an existing RapidAPI subscription, override
  `base_url="https://cryptovol.p.rapidapi.com"` and continue to use the
  legacy `X-RapidAPI-Key` workflow by passing the key normally — the
  header name changed, so you may need to stay on `cryptovol < 0.3.0` to
  use RapidAPI.
- Removed the `host` parameter on `CryptoVol(...)` (it was only used to set
  the now-deprecated `X-RapidAPI-Host` header).

### Migration
```python
# Old (cryptovol < 0.3.0, via RapidAPI)
cv = CryptoVol(api_key="<RapidAPI key>")

# New (cryptovol >= 0.3.0, via the self-hosted hub)
cv = CryptoVol(api_key="cvk_live_...")
```

## [0.2.0] — 2026-05-29

### Added
- `cv.spot_history(...)` — daily spot price time series per session snapshot.
- `cv.realized_vol(...)` — rolling annualized realized volatility (√365) from spot log-returns.
- `session` parameter on `vol_history` (`"asia"`, `"london"`, `"us"`; defaults to `"us"`).
- Response models: `SpotHistoryResponse`, `SpotHistoryPoint`, `RealizedVolResponse`, `RealizedVolPoint` (each with `.to_dataframe()`).

### Changed
- **API policy:** `vol_history` is now available on every plan (previously PRO+ only).
  The 30-day BASIC / 1-year PRO / unlimited ULTRA history window applies as a date cap
  on `start_date`/`end_date` rather than blocking the endpoint outright.
- Plan-limits table in README/docs updated: history window now scales by tier across
  all history-bearing endpoints (`vol_history`, `spot_history`, `realized_vol`, `vol_index`).

## [0.1.0] — 2026-05-16

### Added
- Initial release.
- `CryptoVol` synchronous client with `vol_index`, `vol_surface`, `vol_surface_bulk`, `vol_history`.
- Typed Pydantic v2 response models with `.to_dataframe()` helpers (optional `[pandas]` extra).
- Exception hierarchy: `AuthenticationError`, `PlanLimitError`, `NotFoundError`, `ValidationError`, `RateLimitError`, `ServerError`, `TimeoutError`.
- Automatic retries with exponential backoff for 5xx and 429.
- Examples in `examples/` covering smile reconstruction, vol-index plotting, risk-reversals, and Greeks.
