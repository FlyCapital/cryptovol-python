"""Graceful handling of plan-tier errors.

Every plan currently has full access (all assets, sessions, history, Greeks),
so ``PlanLimitError`` shouldn't fire under normal use today — it's kept for
forward compatibility. This shows the defensive pattern in case that changes.
"""
import os

from cryptovol import CryptoVol, PlanLimitError, ValidationError

cv = CryptoVol(api_key=os.environ["CRYPTOVOL_API_KEY"])

try:
    pt = cv.vol_surface(
        ccy="BTC", expiry="2026-12-26",
        strike_type="moneyness", strike_value=1.0,
        session="asia",
    )
    print(f"Asia close BTC ATM vol: {pt.vol:.2f}%")

except PlanLimitError as e:
    print(f"Falling back to US session — {e}")
    pt = cv.vol_surface(
        ccy="BTC", expiry="2026-12-26",
        strike_type="moneyness", strike_value=1.0,
        session="us",
    )
    print(f"US close BTC ATM vol: {pt.vol:.2f}%")

except ValidationError as e:
    print(f"Bad params: {e}")
