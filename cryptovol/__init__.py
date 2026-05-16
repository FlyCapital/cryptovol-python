"""CryptoVol — Python SDK for the CryptoVol crypto implied volatility API.

Quick start
-----------

    from cryptovol import CryptoVol

    cv = CryptoVol(api_key="YOUR_RAPIDAPI_KEY")
    idx = cv.vol_index(ccy="BTC", tenor="30D")
    print(idx.data[-1].vol)

See https://github.com/YOUR_GH_USERNAME/cryptovol-python for full docs.
"""
from .client import CryptoVol
from .exceptions import (
    AuthenticationError,
    CryptoVolError,
    NotFoundError,
    PlanLimitError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .models import (
    Analytics,
    BulkResultItem,
    BulkVolResponse,
    Greeks,
    VolHistoryPoint,
    VolHistoryResponse,
    VolIndexPoint,
    VolIndexResponse,
    VolSurfacePoint,
)

__version__ = "0.1.0"

__all__ = [
    "CryptoVol",
    # Exceptions
    "CryptoVolError",
    "AuthenticationError",
    "PlanLimitError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    # Models
    "Analytics",
    "Greeks",
    "VolIndexResponse",
    "VolIndexPoint",
    "VolSurfacePoint",
    "BulkVolResponse",
    "BulkResultItem",
    "VolHistoryResponse",
    "VolHistoryPoint",
]
