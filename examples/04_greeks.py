"""Get full Greeks for a 25-delta call (PRO/ULTRA only)."""
import os

from cryptovol import CryptoVol

cv = CryptoVol(api_key=os.environ["CRYPTOVOL_API_KEY"])

pt = cv.vol_surface(
    ccy="BTC",
    expiry="2026-12-26",
    strike_type="delta",
    strike_value=0.25,
    option_type="C",
    include_analytics=True,
)

a = pt.analytics
g = a.greeks

print(f"BTC 25Δ Call — exp {pt.expiry}")
print(f"  Spot:    {a.spot:,.0f}")
print(f"  Forward: {a.forward:,.0f}")
print(f"  Strike:  {pt.strike:,.0f}")
print(f"  IV:      {pt.vol:.2f}%")
print(f"  Price:   {a.price:,.2f}")
print()
print(f"  Δ delta: {g.delta:+.4f}")
print(f"  Γ gamma: {g.gamma:.6f}")
print(f"  ν vega:  {g.vega:.4f}  (per 1 vol pt)")
print(f"  Θ theta: {g.theta:.4f}  (per day)")
