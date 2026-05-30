# Quick start

## Get an API key

Sign up at [cryptovol.io/api](https://www.cryptovol.io/api). You'll get a RapidAPI key — use it as the `api_key` parameter when constructing the client.

```python
from cryptovol import CryptoVol

cv = CryptoVol(api_key="YOUR_RAPIDAPI_KEY")
```

!!! warning "Keep your key out of source control"
    Load it from an environment variable instead:

    ```python
    import os
    cv = CryptoVol(api_key=os.environ["CRYPTOVOL_API_KEY"])
    ```

## 1. Vol index — the simplest call

`vol_index` returns a daily constant-maturity IV time series. Think VIX, but for crypto.

```python
idx = cv.vol_index(ccy="BTC", tenor="30D")

print(f"{idx.count} daily observations")
for pt in idx.data[-5:]:
    print(f"  {pt.date}: {pt.vol:.2f}%")
```

With pandas (`pip install "cryptovol[pandas]"`):

```python
df = cv.vol_index(ccy="BTC", tenor="30D",
                  start_date="2025-01-01").to_dataframe()
df["vol"].plot()
```

## 2. Vol surface — single point

`vol_surface` returns one SABR-interpolated point. Pick a strike convention that fits your workflow:

=== "Moneyness"
    ```python
    pt = cv.vol_surface(
        ccy="BTC", expiry="2026-12-26",
        strike_type="moneyness", strike_value=1.0,  # ATM
    )
    print(pt.vol)
    ```

=== "Delta"
    ```python
    pt = cv.vol_surface(
        ccy="BTC", expiry="2026-12-26",
        strike_type="delta", strike_value=0.25, option_type="C",
    )
    # SDK has used SABR-iterative inversion to find K such that BS-delta = 0.25
    print(pt.strike, pt.vol)
    ```

=== "Absolute"
    ```python
    pt = cv.vol_surface(
        ccy="BTC", expiry="2026-12-26",
        strike_type="strike", strike_value=100_000,
    )
    ```

### Adding Greeks

Set `include_analytics=True` (PRO/ULTRA plans only):

```python
pt = cv.vol_surface(
    ccy="BTC", expiry="2026-12-26",
    strike_type="delta", strike_value=0.25, option_type="C",
    include_analytics=True,
)

g = pt.analytics.greeks
print(f"Δ={g.delta:.4f}  Γ={g.gamma:.6f}  V={g.vega:.2f}  Θ={g.theta:.2f}")
```

## 3. Vol surface (bulk) — many points at once

When you need a smile, a term structure, or a grid, **use the bulk endpoint** instead of looping over `vol_surface`. The API loads the snapshot once and reuses it for every query.

```python
resp = cv.vol_surface_bulk(
    ccy="BTC",
    queries=[
        {"expiry": "2026-09-26", "strike_type": "moneyness", "strike_value": m}
        for m in [0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2]
    ],
)

for pt in resp.successful:
    print(f"{pt.strike_value:.2f}x  IV={pt.vol:.2f}%")
```

Individual failures don't fail the request — check `.successful` and `.failed`:

```python
if resp.failed:
    for f in resp.failed:
        print(f"  {f.expiry}: {f.error}")
```

## 4. Vol history — historical constant-maturity series

`vol_history` is purpose-built for backtests: a clean daily series at a fixed maturity and fixed strike. Available on every plan — the history window scales by tier (BASIC = 30 days, PRO = 1 year, ULTRA = full archive).

```python
hist = cv.vol_history(
    ccy="BTC", tenor="1M",
    strike_type="moneyness", strike_value=1.0,  # ATM
    start_date="2025-01-01",
)
print(f"{hist.count} daily ATM IV observations")
```

For delta strikes, supply `option_type`:

```python
hist_25c = cv.vol_history(
    ccy="BTC", tenor="1M",
    strike_type="delta", strike_value=0.25, option_type="C",
)
```

## Next: [recipes →](recipes.md)
