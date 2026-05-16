"""Exception hierarchy for the CryptoVol SDK.

Catch `CryptoVolError` to handle any API-related failure. Catch a more specific
subclass when you want to react to a particular condition (e.g. retry on
rate limits, prompt the user to upgrade on plan-limit errors).
"""
from __future__ import annotations

from typing import Any, Optional


class CryptoVolError(Exception):
    """Base exception for all errors raised by the CryptoVol SDK."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_body: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:  # pragma: no cover — trivial
        if self.status_code is not None:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(CryptoVolError):
    """Raised on 401 / 403 — invalid or missing API key, or non-allowed origin."""


class PlanLimitError(CryptoVolError):
    """Raised on 403 when the request hits a plan-tier limit.

    Examples: querying ETH on a BASIC plan, requesting Greeks without PRO,
    querying dates older than your plan's history window.

    The server's error message typically tells you which tier unlocks the feature.
    """


class NotFoundError(CryptoVolError):
    """Raised on 404 — no data available for the requested asset/date/session."""


class ValidationError(CryptoVolError):
    """Raised on 400 / 422 — malformed parameters (bad ccy, bad date format, etc.)."""


class RateLimitError(CryptoVolError):
    """Raised on 429 — daily/monthly quota exceeded."""


class ServerError(CryptoVolError):
    """Raised on 5xx — transient server-side failure."""


class TimeoutError(CryptoVolError):
    """Raised when a request exceeds the configured timeout."""
