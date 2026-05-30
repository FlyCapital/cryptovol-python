"""Endpoint tests using pytest-httpx — fully offline, no real API needed."""
import pytest

from cryptovol import (
    AuthenticationError,
    CryptoVol,
    NotFoundError,
    PlanLimitError,
    RateLimitError,
    ServerError,
    ValidationError,
)

BASE = "https://cryptovol-api-nbakzshi6q-uc.a.run.app"


# ── vol_index ────────────────────────────────────────────────────────────────


def test_vol_index_parses_response(client, httpx_mock):
    payload = {
        "ccy": "BTC", "tenor": "30D",
        "start_date": "2026-04-01", "end_date": "2026-05-01",
        "count": 2,
        "data": [
            {"date": "2026-04-30", "vol": 42.15},
            {"date": "2026-05-01", "vol": 41.80},
        ],
    }
    httpx_mock.add_response(url=f"{BASE}/v1/vol-index?ccy=BTC&tenor=30D", json=payload)

    resp = client.vol_index(ccy="BTC", tenor="30D")

    assert resp.ccy == "BTC"
    assert resp.tenor == "30D"
    assert resp.count == 2
    assert resp.data[-1].vol == 41.80


def test_vol_index_raw_returns_dict(client, httpx_mock):
    payload = {"ccy": "BTC", "tenor": "30D", "count": 0, "data": []}
    httpx_mock.add_response(url=f"{BASE}/v1/vol-index?ccy=BTC&tenor=30D", json=payload)

    resp = client.vol_index(ccy="BTC", tenor="30D", raw=True)

    assert isinstance(resp, dict)
    assert resp["ccy"] == "BTC"


def test_vol_index_passes_date_range(client, httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE}/v1/vol-index?ccy=ETH&tenor=1M&start_date=2026-01-01&end_date=2026-02-01",
        json={"ccy": "ETH", "tenor": "1M", "count": 0, "data": []},
    )
    client.vol_index(
        ccy="ETH", tenor="1M",
        start_date="2026-01-01", end_date="2026-02-01",
    )


# ── vol_surface (single point) ───────────────────────────────────────────────


def test_vol_surface_with_analytics(client, httpx_mock):
    payload = {
        "ccy": "BTC", "session": "us", "date": "2026-05-10",
        "expiry": "2026-12-26",
        "strike_type": "delta", "strike_value": 0.25, "strike": 110_000.0,
        "option_type": "C", "vol": 52.34,
        "analytics": {
            "spot": 95000.0, "forward": 96000.0, "yield_rate": 0.012,
            "price": 4200.50,
            "greeks": {"delta": 0.2501, "gamma": 0.000023, "vega": 145.6, "theta": -32.1},
        },
    }
    httpx_mock.add_response(
        url=f"{BASE}/v1/vol-surface?ccy=BTC&expiry=2026-12-26&strike_type=delta&strike_value=0.25&option_type=C&session=us&include_analytics=true",
        json=payload,
    )

    pt = client.vol_surface(
        ccy="BTC", expiry="2026-12-26",
        strike_type="delta", strike_value=0.25, option_type="C",
        include_analytics=True,
    )

    assert pt.vol == 52.34
    assert pt.strike == 110_000.0
    assert pt.analytics.greeks.delta == 0.2501
    assert pt.analytics.spot == 95000.0


def test_vol_surface_no_analytics_omits_param(client, httpx_mock):
    # include_analytics=False must NOT appear in the query string
    httpx_mock.add_response(
        url=f"{BASE}/v1/vol-surface?ccy=BTC&expiry=2026-12-26&strike_type=moneyness&strike_value=1.0&option_type=C&session=us",
        json={
            "ccy": "BTC", "session": "us", "date": "2026-05-10",
            "expiry": "2026-12-26", "strike_type": "moneyness",
            "strike_value": 1.0, "strike": 95000.0, "vol": 48.0,
        },
    )
    pt = client.vol_surface(
        ccy="BTC", expiry="2026-12-26",
        strike_type="moneyness", strike_value=1.0,
    )
    assert pt.vol == 48.0


# ── vol_surface_bulk ─────────────────────────────────────────────────────────


def test_vol_surface_bulk(client, httpx_mock):
    payload = {
        "ccy": "BTC", "session": "us", "date": "2026-05-10",
        "spot": 95000.0,
        "count": 3,
        "results": [
            {"expiry": "2026-09-26", "strike_type": "moneyness",
             "strike_value": 0.9, "strike": 85500.0, "vol": 54.1},
            {"expiry": "2026-09-26", "strike_type": "moneyness",
             "strike_value": 1.0, "strike": 95000.0, "vol": 48.0},
            {"expiry": "2025-01-01", "error": "expiry in the past"},
        ],
    }
    httpx_mock.add_response(url=f"{BASE}/v1/vol-surface/bulk", json=payload)

    resp = client.vol_surface_bulk(
        ccy="BTC",
        queries=[
            {"expiry": "2026-09-26", "strike_type": "moneyness", "strike_value": 0.9},
            {"expiry": "2026-09-26", "strike_type": "moneyness", "strike_value": 1.0},
            {"expiry": "2025-01-01", "strike_type": "moneyness", "strike_value": 1.0},
        ],
    )

    assert resp.count == 3
    assert len(resp.successful) == 2
    assert len(resp.failed) == 1
    assert resp.failed[0].error == "expiry in the past"
    assert resp.successful[0].ok is True
    assert resp.failed[0].ok is False


# ── vol_history ──────────────────────────────────────────────────────────────


def test_vol_history(client, httpx_mock):
    payload = {
        "ccy": "BTC", "tenor": "1M",
        "strike_type": "delta", "strike_value": 0.25, "option_type": "C",
        "start_date": "2026-04-01", "end_date": "2026-05-01",
        "count": 2,
        "data": [
            {"date": "2026-04-30", "vol": 52.1},
            {"date": "2026-05-01", "vol": 51.8},
        ],
    }
    httpx_mock.add_response(
        url=(
            f"{BASE}/v1/vol-history?ccy=BTC&tenor=1M"
            f"&strike_type=delta&strike_value=0.25&option_type=C&session=us"
        ),
        json=payload,
    )

    resp = client.vol_history(
        ccy="BTC", tenor="1M",
        strike_type="delta", strike_value=0.25, option_type="C",
    )

    assert resp.count == 2
    assert resp.option_type == "C"
    assert resp.data[0].vol == 52.1


# ── Error mapping ────────────────────────────────────────────────────────────


def test_plan_limit_error_on_403_with_plan_message(client, httpx_mock):
    httpx_mock.add_response(
        status_code=403,
        json={"detail": "Asset ETH is not available on the BASIC plan. Upgrade to PRO."},
    )
    with pytest.raises(PlanLimitError) as exc:
        client.vol_index(ccy="ETH", tenor="30D")
    assert exc.value.status_code == 403
    assert "BASIC" in str(exc.value)


def test_authentication_error_on_403_without_plan_message(client, httpx_mock):
    httpx_mock.add_response(status_code=403, json={"error": "Forbidden"})
    with pytest.raises(AuthenticationError):
        client.vol_index(ccy="BTC", tenor="30D")


def test_not_found_error_on_404(client, httpx_mock):
    httpx_mock.add_response(
        status_code=404,
        json={"detail": "No surface data found for BTC on 'us' session"},
    )
    with pytest.raises(NotFoundError):
        client.vol_surface(
            ccy="BTC", expiry="2026-12-26",
            strike_type="moneyness", strike_value=1.0,
        )


def test_validation_error_on_400(client, httpx_mock):
    httpx_mock.add_response(status_code=400, json={"detail": "Invalid ccy 'DOGE'."})
    with pytest.raises(ValidationError):
        client.vol_index(ccy="DOGE", tenor="30D")


def test_rate_limit_on_429(client, httpx_mock):
    httpx_mock.add_response(status_code=429, json={"message": "quota exceeded"})
    with pytest.raises(RateLimitError):
        client.vol_index(ccy="BTC", tenor="30D")


def test_server_error_on_500(client, httpx_mock):
    httpx_mock.add_response(status_code=500, text="internal error")
    with pytest.raises(ServerError):
        client.vol_index(ccy="BTC", tenor="30D")


# ── Client setup ─────────────────────────────────────────────────────────────


def test_missing_api_key_raises():
    with pytest.raises(ValueError, match="api_key"):
        CryptoVol(api_key="")


def test_sends_cryptovol_key_header(client, httpx_mock):
    httpx_mock.add_response(json={"ccy": "BTC", "tenor": "30D", "count": 0, "data": []})

    client.vol_index(ccy="BTC", tenor="30D")

    request = httpx_mock.get_request()
    assert request.headers["X-CryptoVol-Key"] == "test-key"
    # The legacy RapidAPI headers must not leak through.
    assert "X-RapidAPI-Key"  not in request.headers
    assert "X-RapidAPI-Host" not in request.headers


def test_context_manager_closes(httpx_mock):
    with CryptoVol(api_key="test-key", max_retries=0) as cv:
        httpx_mock.add_response(
            json={"ccy": "BTC", "tenor": "30D", "count": 0, "data": []}
        )
        cv.vol_index(ccy="BTC", tenor="30D")
    # client should now be closed; no easy way to assert directly, but no errors
