"""Synchronous client for the CryptoVol API.

Quick start
-----------

    from cryptovol import CryptoVol

    cv = CryptoVol(api_key="YOUR_RAPIDAPI_KEY")

    # Daily 30-day BTC vol index
    idx = cv.vol_index(ccy="BTC", tenor="30D")
    print(idx.data[-1].vol)

    # ATM vol for a specific expiry
    pt = cv.vol_surface(
        ccy="BTC", expiry="2026-12-26",
        strike_type="moneyness", strike_value=1.0,
        include_analytics=True,
    )
    print(pt.vol, pt.analytics.greeks.delta)
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Literal, Optional, Union

import httpx

from .exceptions import (
    AuthenticationError,
    CryptoVolError,
    NotFoundError,
    PlanLimitError,
    RateLimitError,
    ServerError,
    TimeoutError as CryptoVolTimeoutError,
    ValidationError,
)
from .models import (
    BulkVolResponse,
    VolHistoryResponse,
    VolIndexResponse,
    VolSurfacePoint,
)

DEFAULT_BASE_URL = "https://cryptovol.p.rapidapi.com"
DEFAULT_HOST = "cryptovol.p.rapidapi.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_USER_AGENT = "cryptovol-python/0.1.0"

StrikeType = Literal["strike", "moneyness", "delta"]
OptionType = Literal["C", "P"]
Session = Literal["asia", "london", "us"]
Tenor = Literal[
    "1D", "1W", "2W", "3W", "1M", "2M", "3M", "6M", "9M", "1Y",
    "7D", "14D", "21D", "30D", "60D", "90D", "180D", "270D", "365D",
]


class CryptoVol:
    """Synchronous client for the CryptoVol REST API.

    Parameters
    ----------
    api_key:
        Your RapidAPI key. Get one at https://www.cryptovol.io/api.
        Sent as ``X-RapidAPI-Key`` on every request.
    base_url:
        Override the API base URL. Defaults to the RapidAPI gateway.
    host:
        Value for the ``X-RapidAPI-Host`` header. You won't need to change
        this unless you're routing through a different gateway.
    timeout:
        Per-request timeout in seconds. Defaults to 30s.
    max_retries:
        How many times to retry transient failures (network errors and 5xx
        responses) with exponential backoff. Set to 0 to disable.
    user_agent:
        Custom User-Agent header. Useful if you're embedding the SDK in your
        own product and want clean attribution in server logs.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        host: str = DEFAULT_HOST,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        if not api_key:
            raise ValueError(
                "api_key is required. Get a key at https://www.cryptovol.io/api"
            )

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.host = host
        self.timeout = timeout
        self.max_retries = max_retries

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": host,
                "User-Agent": user_agent,
                "Accept": "application/json",
            },
        )

    # ── Context manager support ──────────────────────────────────────────────

    def __enter__(self) -> "CryptoVol":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client. Safe to call multiple times."""
        self._client.close()

    # ── Endpoints ────────────────────────────────────────────────────────────

    def vol_index(
        self,
        ccy: str = "BTC",
        tenor: str = "30D",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        *,
        raw: bool = False,
    ) -> Union[VolIndexResponse, Dict[str, Any]]:
        """Daily implied volatility index (CryptoVIX-style time series).

        Parameters
        ----------
        ccy:
            Asset symbol — one of ``BTC``, ``ETH``, ``SOL``, ``XRP``, ``AVAX``,
            ``TRX``. Subject to your plan tier.
        tenor:
            Constant-maturity tenor (e.g. ``7D``, ``30D``, ``1M``, ``3M``).
        start_date / end_date:
            Optional ``YYYY-MM-DD`` bounds. If omitted, defaults to roughly
            the last year (or the most that your plan allows).
        raw:
            If True, return the parsed JSON dict instead of a typed model.
        """
        params = _drop_none({
            "ccy": ccy,
            "tenor": tenor,
            "start_date": start_date,
            "end_date": end_date,
        })
        data = self._request("GET", "/v1/vol-index", params=params)
        return data if raw else VolIndexResponse.model_validate(data)

    def vol_surface(
        self,
        ccy: str,
        expiry: str,
        strike_type: StrikeType,
        strike_value: float,
        *,
        option_type: OptionType = "C",
        session: Session = "us",
        date: Optional[str] = None,
        include_analytics: bool = False,
        raw: bool = False,
    ) -> Union[VolSurfacePoint, Dict[str, Any]]:
        """Single-point SABR-interpolated implied vol query.

        Parameters
        ----------
        ccy:
            Asset symbol.
        expiry:
            Option expiry date, ``YYYY-MM-DD``. Must be in the future
            relative to the snapshot date.
        strike_type:
            How ``strike_value`` is interpreted:

            * ``"strike"`` — absolute strike price (e.g. ``100_000``)
            * ``"moneyness"`` — K/S ratio (e.g. ``1.0`` for ATM, ``0.9`` for 10% OTM put)
            * ``"delta"`` — signed/unsigned BS delta magnitude (e.g. ``0.25``)
        strike_value:
            The numeric strike, moneyness, or delta — see ``strike_type``.
        option_type:
            ``"C"`` (call, default) or ``"P"`` (put). Required when
            ``strike_type="delta"``; ignored otherwise.
        session:
            ``"asia"``, ``"london"``, or ``"us"``. Subject to your plan tier.
        date:
            Optional snapshot date (``YYYY-MM-DD``). Defaults to the latest
            available snapshot.
        include_analytics:
            If True, also return spot, forward, yield rate, BS price, and Greeks.
            Requires a PRO or ULTRA plan.
        raw:
            If True, return the parsed JSON dict instead of a typed model.
        """
        params = _drop_none({
            "ccy": ccy,
            "expiry": expiry,
            "strike_type": strike_type,
            "strike_value": strike_value,
            "option_type": option_type,
            "session": session,
            "date": date,
            "include_analytics": str(include_analytics).lower() if include_analytics else None,
        })
        data = self._request("GET", "/v1/vol-surface", params=params)
        return data if raw else VolSurfacePoint.model_validate(data)

    def vol_surface_bulk(
        self,
        ccy: str,
        queries: List[Dict[str, Any]],
        *,
        session: Session = "us",
        date: Optional[str] = None,
        raw: bool = False,
    ) -> Union[BulkVolResponse, Dict[str, Any]]:
        """Resolve many (expiry, strike) points in a single request.

        Far more efficient than looping over :meth:`vol_surface` — one
        snapshot is loaded once and reused for every query.

        Parameters
        ----------
        ccy:
            Asset symbol.
        queries:
            List of dicts, each with keys:

            * ``expiry`` (str, required) — ``YYYY-MM-DD``
            * ``strike_type`` (str, required) — ``"strike"``, ``"moneyness"``, or ``"delta"``
            * ``strike_value`` (float, required)
            * ``option_type`` (str, optional) — ``"C"`` or ``"P"`` (default ``"C"``)
            * ``include_analytics`` (bool, optional) — default False
        session:
            ``"asia"``, ``"london"``, or ``"us"``.
        date:
            Optional snapshot date.
        raw:
            If True, return the parsed JSON dict instead of a typed model.

        Example
        -------

            response = cv.vol_surface_bulk(
                ccy="BTC",
                queries=[
                    {"expiry": "2026-09-26", "strike_type": "moneyness", "strike_value": 0.9},
                    {"expiry": "2026-09-26", "strike_type": "moneyness", "strike_value": 1.0},
                    {"expiry": "2026-09-26", "strike_type": "moneyness", "strike_value": 1.1},
                    {"expiry": "2026-09-26", "strike_type": "delta",
                     "strike_value": 0.25, "option_type": "C", "include_analytics": True},
                ],
            )
            for item in response.successful:
                print(item.expiry, item.strike, item.vol)
        """
        body = _drop_none({
            "ccy": ccy,
            "session": session,
            "date": date,
            "queries": queries,
        })
        data = self._request("POST", "/v1/vol-surface/bulk", json=body)
        return data if raw else BulkVolResponse.model_validate(data)

    def vol_history(
        self,
        ccy: str = "BTC",
        tenor: str = "1M",
        strike_type: Literal["moneyness", "delta"] = "moneyness",
        strike_value: float = 1.0,
        *,
        option_type: OptionType = "C",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        raw: bool = False,
    ) -> Union[VolHistoryResponse, Dict[str, Any]]:
        """Historical time series at a constant maturity and constant strike.

        Ideal for backtesting, regression analysis, and vol regime monitoring.

        Requires a PRO or ULTRA plan (BASIC plans get 403 on this endpoint).

        Parameters
        ----------
        ccy:
            Asset symbol.
        tenor:
            Constant-maturity tenor: ``1D``, ``1W``, ``2W``, ``3W``, ``1M``,
            ``2M``, ``3M``, ``6M``, ``9M``, or ``1Y``.
        strike_type:
            ``"moneyness"`` (K/S) or ``"delta"``. Absolute strikes are not
            supported for history queries.
        strike_value:
            Must be a value on the published grid — see the API docs for the
            full list. Common moneyness points: 0.9, 0.95, 1.0, 1.05, 1.1.
            Common deltas: 0.10, 0.25.
        option_type:
            ``"C"`` or ``"P"``. Required when ``strike_type="delta"``.
        start_date / end_date:
            ``YYYY-MM-DD`` bounds. PRO plans are limited to the last year.
        raw:
            If True, return the parsed JSON dict instead of a typed model.
        """
        params = _drop_none({
            "ccy": ccy,
            "tenor": tenor,
            "strike_type": strike_type,
            "strike_value": strike_value,
            "option_type": option_type,
            "start_date": start_date,
            "end_date": end_date,
        })
        data = self._request("GET", "/v1/vol-history", params=params)
        return data if raw else VolHistoryResponse.model_validate(data)

    # ── HTTP plumbing ────────────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Send a request with retries and convert HTTP errors to typed exceptions."""
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(
                    method, path, params=params, json=json
                )
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(_backoff(attempt))
                    continue
                raise CryptoVolTimeoutError(
                    f"Request to {path} timed out after {self.timeout}s"
                ) from e
            except httpx.HTTPError as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(_backoff(attempt))
                    continue
                raise CryptoVolError(f"Network error calling {path}: {e}") from e

            # Retry 5xx
            if 500 <= response.status_code < 600 and attempt < self.max_retries:
                time.sleep(_backoff(attempt))
                continue

            # Retry 429 with backoff
            if response.status_code == 429 and attempt < self.max_retries:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else _backoff(attempt)
                time.sleep(delay)
                continue

            return _handle_response(response)

        # Should be unreachable, but just in case
        raise CryptoVolError(  # pragma: no cover
            f"Exhausted retries for {path}: {last_error}"
        )


# ── Helpers ──────────────────────────────────────────────────────────────────


def _drop_none(d: Dict[str, Any]) -> Dict[str, Any]:
    """Strip keys whose value is None so we don't send them as query params."""
    return {k: v for k, v in d.items() if v is not None}


def _backoff(attempt: int) -> float:
    """Exponential backoff: 0.5s, 1s, 2s, 4s..."""
    return 0.5 * (2 ** attempt)


def _handle_response(response: httpx.Response) -> Any:
    """Raise typed exceptions for error responses; return parsed JSON otherwise."""
    if response.is_success:
        try:
            return response.json()
        except ValueError as e:
            raise CryptoVolError(
                f"Server returned non-JSON response (status {response.status_code})",
                status_code=response.status_code,
                response_body=response.text,
            ) from e

    # Pull a human-readable message out of the body
    try:
        body = response.json()
        message = (
            body.get("detail")
            or body.get("error")
            or body.get("message")
            or str(body)
        )
    except ValueError:
        body = response.text
        message = body or response.reason_phrase

    status = response.status_code
    kwargs = {"status_code": status, "response_body": body}

    if status in (401,):
        raise AuthenticationError(message, **kwargs)
    if status == 403:
        # The API uses 403 for two distinct cases:
        #   1. Missing/invalid RapidAPI proxy secret  -> AuthenticationError
        #   2. Plan tier limit violation              -> PlanLimitError
        # The plan-limit messages all mention "plan" or "Upgrade"; auth ones don't.
        text = str(message).lower()
        if "plan" in text or "upgrade" in text or "tier" in text:
            raise PlanLimitError(message, **kwargs)
        raise AuthenticationError(message, **kwargs)
    if status == 404:
        raise NotFoundError(message, **kwargs)
    if status in (400, 422):
        raise ValidationError(message, **kwargs)
    if status == 429:
        raise RateLimitError(message, **kwargs)
    if 500 <= status < 600:
        raise ServerError(message, **kwargs)

    raise CryptoVolError(message, **kwargs)
