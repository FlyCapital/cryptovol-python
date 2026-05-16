# cryptovol-python

The official Python SDK for the **[CryptoVol API](https://www.cryptovol.io)** — institutional-grade implied volatility data for crypto options.

!!! tip "What's included"
    - **SABR-calibrated** vol surfaces — arbitrage-free interpolation
    - **3 sessions/day** — Asia, London, US closes
    - **6 assets** — BTC, ETH, SOL, XRP, AVAX, TRX
    - **Constant-maturity history** for clean backtesting
    - **Greeks** computed at any (K, T) point

## Install

```bash
pip install cryptovol
```

For pandas integration:

```bash
pip install "cryptovol[pandas]"
```

## A 30-second tour

```python
from cryptovol import CryptoVol

cv = CryptoVol(api_key="YOUR_RAPIDAPI_KEY")

# Daily IV index
idx = cv.vol_index(ccy="BTC", tenor="30D")

# Single vol point with Greeks
pt = cv.vol_surface(
    ccy="BTC", expiry="2026-12-26",
    strike_type="delta", strike_value=0.25, option_type="C",
    include_analytics=True,
)
print(pt.vol, pt.analytics.greeks.delta)

# Many points at once
resp = cv.vol_surface_bulk(
    ccy="BTC",
    queries=[
        {"expiry": "2026-09-26", "strike_type": "moneyness", "strike_value": m}
        for m in [0.9, 1.0, 1.1]
    ],
)

# Constant-maturity history
hist = cv.vol_history(ccy="BTC", tenor="1M",
                      strike_type="moneyness", strike_value=1.0)
```

## Next steps

- [Quick start](quickstart.md) — full walkthrough of every endpoint
- [Recipes](recipes.md) — common analytics patterns
- [Error handling](errors.md) — exception hierarchy and retry behavior
- [API reference](reference.md) — every method, parameter, and return type

## Get a key

Sign up at **[cryptovol.io/api](https://www.cryptovol.io/api)** — BASIC, PRO, and ULTRA tiers available.
