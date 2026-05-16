"""Shared test fixtures."""
import pytest

from cryptovol import CryptoVol

TEST_BASE_URL = "https://cryptovol.p.rapidapi.com"


@pytest.fixture
def client():
    """A CryptoVol client with retries disabled for predictable test behavior."""
    cv = CryptoVol(
        api_key="test-key",
        base_url=TEST_BASE_URL,
        max_retries=0,
        timeout=5.0,
    )
    yield cv
    cv.close()
