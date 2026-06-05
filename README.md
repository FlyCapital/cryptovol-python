# cryptovol-python

[![PyPI version](https://img.shields.io/pypi/v/cryptovol.svg)](https://pypi.org/project/cryptovol/)
[![Python versions](https://img.shields.io/pypi/pyversions/cryptovol.svg)](https://pypi.org/project/cryptovol/)
[![CI](https://github.com/FlyCapital/cryptovol-python/actions/workflows/ci.yml/badge.svg)](https://github.com/FlyCapital/cryptovol-python/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/badge/docs-cryptovol.io-blue)](https://www.cryptovol.io/docs)

The official Python SDK for the **[CryptoVol API](https://www.cryptovol.io)** — institutional-grade implied volatility data for crypto options.

> SABR-calibrated surfaces · 3 sessions/day (Asia, London, US) · BTC, ETH, SOL, XRP, AVAX, TRX · Constant-maturity history for backtesting

---

## Install

```bash
pip install cryptovol
```

Optional pandas integration (for `.to_dataframe()`):

```bash
pip install "cryptovol[pandas]"
```

## Get an API key

Sign up at **[cryptovol.io/signup](https://www.cryptovol.io/signup)** — free BASIC tier, no card required. Your key (`cvk_live_...`) appears on [cryptovol.io/account](https://www.cryptovol.io/account). PRO and ULTRA tiers unlock higher quotas and more assets.

## Quick start

```python
from cryptovol import CryptoVol

cv = CryptoVol(api_key="cvk_live_...")

# Daily BTC 30-day implied vol index
idx = cv.vol_index(ccy="BTC", tenor="30D")
print(f"Latest BTC 30D IV: {idx.data[-1].vol}%")

# ATM vol for a specific expiry, with Greeks
pt = cv.vol_surface(
    ccy="BTC",
    expiry="2026-12-26",
    strike_type="moneyness",
    strike_value=1.0,
    include_analytics=True,
)
print(f"BTC ATM Dec 26: {pt.vol}%  delta={pt.analytics.greeks.delta:.3f}")
```

That's it. The client is typed end-to-end, so your IDE autocompletes every field.

---

## What you can query

| Method | Endpoint | What it returns |
|---|---|---|
| `cv.vol_index(...)` | `GET /v1/vol-index` | Daily IV index time series (CryptoVIX-style) |
| `cv.vol_surface(...)` | `GET /v1/vol-surface` | One SABR-interpolated vol point |
| `cv.vol_surface_bulk(...)` | `POST /v1/vol-surface/bulk` | Many points in one round-trip — efficient |
| `cv.vol_surface_raw(...)` | `GET /v1/vol-surface/raw` | Raw market-quoted surface (strike ladders, pre-fit) — PRO and ULTRA |
| `cv.vol_history(...)` | `GET /v1/vol-history` | Constant-maturity historical IV for backtests |
| `cv.spot_history(...)` | `GET /v1/spot-history` | Daily spot price time series per session |
| `cv.realized_vol(...)` | `GET /v1/realized-vol` | Rolling annualized RV (√365) from spot log-returns |

### Strike conventions

`vol_surface` and `vol_surface_bulk` accept three strike types:

- **`"moneyness"`** — `strike_value` is the K/S ratio. `1.0` = ATM, `0.9` = 10% OTM put strike.
- **`"delta"`** — `strike_value` is the BS delta magnitude. `0.25` with `option_type="C"` gives the 25-delta call strike.
- **`"strike"`** — `strike_value` is the absolute strike (e.g. `100_000`).

For `"delta"`, the SDK solves K via SABR-interpolated Newton iteration on the surface — same calibration the API serves.

---

## Common recipes

### Plot the BTC 30-day vol index

```python
import matplotlib.pyplot as plt
from cryptovol import CryptoVol

cv = CryptoVol(api_key="...")
df = cv.vol_index(ccy="BTC", tenor="30D",
                  start_date="2025-01-01", end_date="2026-05-01").to_dataframe()

df["vol"].plot(title="BTC 30D Implied Vol")
plt.ylabel("IV (%)"); plt.show()
```

### Reconstruct a vol smile for one expiry

```python
expiry = "2026-09-26"
moneyness_grid = [0.7, 0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2, 1.3]

resp = cv.vol_surface_bulk(
    ccy="BTC",
    queries=[
        {"expiry": expiry, "strike_type": "moneyness", "strike_value": m}
        for m in moneyness_grid
    ],
)

for pt in resp.successful:
    print(f"{pt.strike_value:.2f}x  K={pt.strike:>10,.0f}  vol={pt.vol:.2f}%")
```

### Build a 25-delta risk-reversal time series

```python
import pandas as pd

call = cv.vol_history(ccy="BTC", tenor="1M",
                      strike_type="delta", strike_value=0.25, option_type="C").to_dataframe()
put  = cv.vol_history(ccy="BTC", tenor="1M",
                      strike_type="delta", strike_value=0.25, option_type="P").to_dataframe()

rr = call["vol"] - put["vol"]
rr.plot(title="BTC 1M 25Δ Risk-Reversal")
```

### Greeks on a 25-delta call

```python
pt = cv.vol_surface(
    ccy="BTC", expiry="2026-12-26",
    strike_type="delta", strike_value=0.25, option_type="C",
    include_analytics=True,
)
g = pt.analytics.greeks
print(f"K={pt.strike:.0f}  vol={pt.vol:.2f}%  Δ={g.delta:.3f}  Γ={g.gamma:.6f}  V={g.vega:.2f}  Θ={g.theta:.2f}")
```

---

## Error handling

Every API error becomes a typed exception you can catch precisely:

```python
from cryptovol import CryptoVol, PlanLimitError, ValidationError, RateLimitError

cv = CryptoVol(api_key="...")

try:
    cv.vol_history(ccy="ETH", tenor="1M",
                   strike_type="moneyness", strike_value=1.0)
except PlanLimitError as e:
    print(f"Plan limit hit — upgrade needed: {e}")
except ValidationError as e:
    print(f"Bad params: {e}")
except RateLimitError as e:
    print(f"Slow down: {e}")
```

Hierarchy:

```
CryptoVolError                 # base — catch this to handle anything
├── AuthenticationError        # 401, or 403 without "plan" in the body
├── PlanLimitError             # 403 — tier blocks asset/session/history/Greeks
├── NotFoundError              # 404 — no data for that date/session
├── ValidationError            # 400 / 422 — malformed params
├── RateLimitError             # 429 — quota exceeded
├── ServerError                # 5xx
└── TimeoutError               # request exceeded `timeout`
```

---

## Configuration

```python
from cryptovol import CryptoVol

cv = CryptoVol(
    api_key="...",
    timeout=30.0,          # per-request timeout (seconds)
    max_retries=3,         # retries 5xx and 429 with exponential backoff
    user_agent="my-app/1.2.3",
)

# Or as a context manager — closes the HTTP client on exit
with CryptoVol(api_key="...") as cv:
    idx = cv.vol_index()
```

### Raw JSON

Every method accepts `raw=True` if you'd rather skip the typed models and work with plain dicts:

```python
data = cv.vol_index(ccy="BTC", tenor="30D", raw=True)
# data is just the parsed JSON
```

---

## Plan tiers (at a glance)

All six methods are available on every plan. Tiers differ in the breadth of the data window (assets, sessions, history depth) and Greeks access.

| | BASIC | PRO | ULTRA |
|---|---|---|---|
| Assets | BTC | + ETH, SOL | + XRP, AVAX, TRX |
| Sessions | US | US | Asia, London, US |
| History window | 30 days | 1 year | Full archive |
| Greeks / analytics | — | ✓ | ✓ |
| Quota | 500/month | 100k/day | 100k/day |

The history window applies to `vol_history`, `spot_history`, `realized_vol`, and any date range passed to `vol_index`. Hitting a limit raises `PlanLimitError` — the message tells you which tier unlocks it. Full details at **[cryptovol.io/api](https://www.cryptovol.io/api)**.

---

## Development

```bash
git clone https://github.com/FlyCapital/cryptovol-python.git
cd cryptovol-python
pip install -e ".[dev]"
pytest
```

---

## Links

- **API docs:** https://www.cryptovol.io/docs
- **Methodology:** https://www.cryptovol.io/methodology
- **Research / blog:** https://www.cryptovol.io/blog
- **Get an API key:** https://www.cryptovol.io/signup

## License

MIT — see [LICENSE](./LICENSE).
