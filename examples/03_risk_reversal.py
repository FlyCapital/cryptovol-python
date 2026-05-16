"""Build a 25-delta risk-reversal historical series (PRO/ULTRA only).

The 25Δ RR is a standard skew measure: 25Δ-call IV minus 25Δ-put IV.
Positive RR = call skew; negative RR = put skew (typical for risk-off regimes).
"""
import os

from cryptovol import CryptoVol

cv = CryptoVol(api_key=os.environ["CRYPTOVOL_API_KEY"])

call = cv.vol_history(
    ccy="BTC", tenor="1M",
    strike_type="delta", strike_value=0.25, option_type="C",
).to_dataframe()

put = cv.vol_history(
    ccy="BTC", tenor="1M",
    strike_type="delta", strike_value=0.25, option_type="P",
).to_dataframe()

rr = (call["vol"] - put["vol"]).rename("rr_25d")
print(rr.tail(10))
print(f"\nMean 25Δ RR: {rr.mean():.3f}%   Std: {rr.std():.3f}%")
