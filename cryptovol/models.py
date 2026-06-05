"""Typed response models for the CryptoVol API.

All models are Pydantic v2 ``BaseModel`` subclasses, so they give you:

* IDE autocomplete on response fields
* Runtime validation of types
* ``.model_dump()`` to round-trip back to plain dicts

If you'd rather work with raw dicts, every client method accepts
``raw=True`` to skip parsing.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Shared building blocks ────────────────────────────────────────────────────


class Greeks(BaseModel):
    """Black-Scholes Greeks computed at the resolved (K, T, vol) point."""

    model_config = ConfigDict(extra="allow")

    delta: Optional[float] = None
    gamma: Optional[float] = None
    vega: Optional[float] = None
    theta: Optional[float] = None


class Analytics(BaseModel):
    """Spot, forward, rate, BS price, and Greeks (PRO and ULTRA only)."""

    model_config = ConfigDict(extra="allow")

    spot: Optional[float] = None
    forward: Optional[float] = None
    yield_rate: Optional[float] = None
    price: Optional[float] = None
    greeks: Optional[Greeks] = None


# ── /v1/vol-index ─────────────────────────────────────────────────────────────


class VolIndexPoint(BaseModel):
    """One day of the constant-maturity vol index."""

    model_config = ConfigDict(extra="allow")

    date: str
    vol: float


class VolIndexResponse(BaseModel):
    """Response from ``GET /v1/vol-index``."""

    model_config = ConfigDict(extra="allow")

    ccy: str
    tenor: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    count: int
    data: List[VolIndexPoint] = Field(default_factory=list)

    def to_dataframe(self):  # pragma: no cover — optional dep
        """Convert ``.data`` to a pandas DataFrame indexed by date.

        Requires pandas to be installed (``pip install cryptovol[pandas]``).
        """
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required for .to_dataframe(). "
                "Install with: pip install cryptovol[pandas]"
            ) from e
        df = pd.DataFrame([p.model_dump() for p in self.data])
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
        return df


# ── /v1/vol-surface (single point) ────────────────────────────────────────────


class VolSurfacePoint(BaseModel):
    """A single SABR-interpolated vol point on the surface."""

    model_config = ConfigDict(extra="allow")

    ccy: str
    session: str
    date: str
    expiry: str
    strike_type: str
    strike_value: float
    strike: float
    option_type: Optional[str] = None
    vol: float
    analytics: Optional[Analytics] = None


# ── /v1/vol-surface/bulk ──────────────────────────────────────────────────────


class BulkResultItem(BaseModel):
    """One item in a bulk response — either a resolved point or an error."""

    model_config = ConfigDict(extra="allow")

    expiry: str
    strike_type: Optional[str] = None
    strike_value: Optional[float] = None
    strike: Optional[float] = None
    option_type: Optional[str] = None
    vol: Optional[float] = None
    analytics: Optional[Analytics] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        """True if this query resolved successfully (no error field)."""
        return self.error is None


class BulkVolResponse(BaseModel):
    """Response from ``POST /v1/vol-surface/bulk``."""

    model_config = ConfigDict(extra="allow")

    ccy: str
    session: str
    date: str
    spot: Optional[float] = None
    count: int
    results: List[BulkResultItem] = Field(default_factory=list)

    @property
    def successful(self) -> List[BulkResultItem]:
        """All bulk results that resolved without error."""
        return [r for r in self.results if r.ok]

    @property
    def failed(self) -> List[BulkResultItem]:
        """All bulk results that came back with an error field."""
        return [r for r in self.results if not r.ok]


# ── /v1/vol-surface/raw ───────────────────────────────────────────────────────


class RawSurfaceExpiry(BaseModel):
    """Market-quoted vols for one listed expiry: index-aligned ``strikes``/``mkt_vol``."""

    model_config = ConfigDict(extra="allow")

    expiry: str
    tenor_days: Optional[int] = None
    forward: Optional[float] = None
    atm_strike: Optional[float] = None
    strikes: List[float] = Field(default_factory=list)
    mkt_vol: List[float] = Field(default_factory=list)


class RawVolSurface(BaseModel):
    """Response from ``GET /v1/vol-surface/raw`` — raw market-quoted surface
    (discrete strike ladders, before model fitting)."""

    model_config = ConfigDict(extra="allow")

    ccy: str
    session: str
    datetime: Optional[str] = None
    vol_date: str
    spot: Optional[float] = None
    count: int
    expiries: List[RawSurfaceExpiry] = Field(default_factory=list)


# ── /v1/vol-history ───────────────────────────────────────────────────────────


class VolHistoryPoint(BaseModel):
    """One day of constant-maturity, constant-strike historical vol."""

    model_config = ConfigDict(extra="allow")

    date: str
    vol: float


class VolHistoryResponse(BaseModel):
    """Response from ``GET /v1/vol-history``."""

    model_config = ConfigDict(extra="allow")

    ccy: str
    tenor: str
    strike_type: str
    strike_value: float
    option_type: Optional[str] = None
    session: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    count: int
    data: List[VolHistoryPoint] = Field(default_factory=list)

    def to_dataframe(self):  # pragma: no cover — optional dep
        """Convert ``.data`` to a pandas DataFrame indexed by date."""
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required for .to_dataframe(). "
                "Install with: pip install cryptovol[pandas]"
            ) from e
        df = pd.DataFrame([p.model_dump() for p in self.data])
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
        return df


# ── /v1/spot-history ──────────────────────────────────────────────────────────


class SpotHistoryPoint(BaseModel):
    """One day of spot price for the requested asset."""

    model_config = ConfigDict(extra="allow")

    date: str
    spot: float


class SpotHistoryResponse(BaseModel):
    """Response from ``GET /v1/spot-history``."""

    model_config = ConfigDict(extra="allow")

    ccy: str
    session: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    count: int
    data: List[SpotHistoryPoint] = Field(default_factory=list)

    def to_dataframe(self):  # pragma: no cover — optional dep
        """Convert ``.data`` to a pandas DataFrame indexed by date."""
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required for .to_dataframe(). "
                "Install with: pip install cryptovol[pandas]"
            ) from e
        df = pd.DataFrame([p.model_dump() for p in self.data])
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
        return df


# ── /v1/realized-vol ──────────────────────────────────────────────────────────


class RealizedVolPoint(BaseModel):
    """One day of rolling realized volatility (annualized, in percent)."""

    model_config = ConfigDict(extra="allow")

    date: str
    rv: float


class RealizedVolResponse(BaseModel):
    """Response from ``GET /v1/realized-vol``."""

    model_config = ConfigDict(extra="allow")

    ccy: str
    session: str
    window: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    count: int
    data: List[RealizedVolPoint] = Field(default_factory=list)

    def to_dataframe(self):  # pragma: no cover — optional dep
        """Convert ``.data`` to a pandas DataFrame indexed by date."""
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required for .to_dataframe(). "
                "Install with: pip install cryptovol[pandas]"
            ) from e
        df = pd.DataFrame([p.model_dump() for p in self.data])
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
        return df
