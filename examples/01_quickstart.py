"""Quickstart: fetch the latest BTC 30-day implied volatility."""
import os

from cryptovol import CryptoVol

cv = CryptoVol(api_key=os.environ["CRYPTOVOL_API_KEY"])

idx = cv.vol_index(ccy="BTC", tenor="30D")

print(f"{idx.ccy} {idx.tenor} — {idx.count} daily points")
print(f"Latest: {idx.data[-1].date}  IV = {idx.data[-1].vol:.2f}%")
