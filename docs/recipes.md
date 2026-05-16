# Recipes

Concrete patterns for the analyses people actually run against the CryptoVol API.

## Plot the 30-day BTC IV index

```python
import matplotlib.pyplot as plt
from cryptovol import CryptoVol

cv = CryptoVol(api_key="...")
df = cv.vol_index(ccy="BTC", tenor="30D",
                  start_date="2025-01-01").to_dataframe()

df["vol"].plot(figsize=(10, 4), title="BTC 30D Implied Volatility")
plt.ylabel("IV (%)")
plt.tight_layout()
plt.show()
```

## Reconstruct a vol smile

```python
EXPIRY = "2026-12-26"
GRID = [0.7, 0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2, 1.3]

resp = cv.vol_surface_bulk(
    ccy="BTC",
    queries=[
        {"expiry": EXPIRY, "strike_type": "moneyness", "strike_value": m}
        for m in GRID
    ],
)

import matplotlib.pyplot as plt
xs = [p.strike_value for p in resp.successful]
ys = [p.vol           for p in resp.successful]
plt.plot(xs, ys, marker="o")
plt.xlabel("Moneyness (K/S)"); plt.ylabel("IV (%)")
plt.title(f"BTC smile — {EXPIRY}")
plt.show()
```

## Term structure of ATM vol

```python
EXPIRIES = ["2026-06-26", "2026-09-26", "2026-12-26", "2027-03-26"]

resp = cv.vol_surface_bulk(
    ccy="BTC",
    queries=[
        {"expiry": e, "strike_type": "moneyness", "strike_value": 1.0}
        for e in EXPIRIES
    ],
)

for pt in resp.successful:
    print(f"{pt.expiry}: ATM IV = {pt.vol:.2f}%")
```

## 25-delta risk-reversal time series

The 25-delta risk reversal (25Δ call IV minus 25Δ put IV) is a standard skew measure. Positive = call-skewed, negative = put-skewed.

```python
call = cv.vol_history(
    ccy="BTC", tenor="1M",
    strike_type="delta", strike_value=0.25, option_type="C",
).to_dataframe()

put = cv.vol_history(
    ccy="BTC", tenor="1M",
    strike_type="delta", strike_value=0.25, option_type="P",
).to_dataframe()

rr = (call["vol"] - put["vol"]).rename("rr_25d_1m")
rr.plot(title="BTC 1M 25Δ Risk Reversal")
```

## Butterfly term structure

A standard fly is `(call_iv + put_iv) / 2 - atm_iv`.

```python
call_25 = cv.vol_history(ccy="BTC", tenor="1M", strike_type="delta",
                         strike_value=0.25, option_type="C").to_dataframe()
put_25  = cv.vol_history(ccy="BTC", tenor="1M", strike_type="delta",
                         strike_value=0.25, option_type="P").to_dataframe()
atm     = cv.vol_history(ccy="BTC", tenor="1M", strike_type="moneyness",
                         strike_value=1.0).to_dataframe()

fly = ((call_25["vol"] + put_25["vol"]) / 2 - atm["vol"]).rename("fly_25d_1m")
```

## Bulk Greeks for portfolio risk

```python
positions = [
    {"expiry": "2026-09-26", "strike_value": 0.9, "option_type": "P"},
    {"expiry": "2026-09-26", "strike_value": 1.0, "option_type": "C"},
    {"expiry": "2026-12-26", "strike_value": 1.1, "option_type": "C"},
]

resp = cv.vol_surface_bulk(
    ccy="BTC",
    queries=[
        {
            "expiry": p["expiry"],
            "strike_type": "moneyness",
            "strike_value": p["strike_value"],
            "option_type": p["option_type"],
            "include_analytics": True,
        }
        for p in positions
    ],
)

portfolio_delta = sum(r.analytics.greeks.delta for r in resp.successful)
portfolio_vega  = sum(r.analytics.greeks.vega  for r in resp.successful)
print(f"Δ={portfolio_delta:+.3f}  ν={portfolio_vega:+.1f}")
```
