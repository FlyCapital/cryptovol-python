"""Reconstruct a vol smile across moneyness for one expiry — using the bulk endpoint.

Bulk is strongly preferred over a loop of single-point calls: the API loads the
SABR snapshot once and reuses it for every query in the request.
"""
import os

from cryptovol import CryptoVol

cv = CryptoVol(api_key=os.environ["CRYPTOVOL_API_KEY"])

EXPIRY = "2026-12-26"
MONEYNESS_GRID = [0.70, 0.80, 0.90, 0.95, 1.00, 1.05, 1.10, 1.20, 1.30]

resp = cv.vol_surface_bulk(
    ccy="BTC",
    session="us",
    queries=[
        {"expiry": EXPIRY, "strike_type": "moneyness", "strike_value": m}
        for m in MONEYNESS_GRID
    ],
)

print(f"Snapshot: {resp.date}  Spot: {resp.spot:,.0f}")
print(f"Expiry:   {EXPIRY}\n")
print(f"  {'K/S':>6}   {'Strike':>10}   {'IV (%)':>8}")
print("  " + "-" * 32)
for pt in resp.successful:
    print(f"  {pt.strike_value:>6.2f}   {pt.strike:>10,.0f}   {pt.vol:>8.2f}")

if resp.failed:
    print(f"\n{len(resp.failed)} queries failed:")
    for f in resp.failed:
        print(f"  {f.expiry}: {f.error}")
