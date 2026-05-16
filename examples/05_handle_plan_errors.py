"""Graceful handling of plan-tier errors.

If your code might run under multiple subscription tiers (e.g. a BASIC dev key
locally and an ULTRA key in prod), catch ``PlanLimitError`` to fall back nicely.
"""
import os

from cryptovol import CryptoVol, PlanLimitError, ValidationError

cv = CryptoVol(api_key=os.environ["CRYPTOVOL_API_KEY"])

try:
    # The Asia session is ULTRA-only; on BASIC/PRO this raises PlanLimitError.
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
