# Error handling

Every API failure becomes a typed Python exception. Catch the base class to handle anything, or a specific subclass to react narrowly.

## Hierarchy

```
CryptoVolError                  # base — catch this to handle anything
├── AuthenticationError         # 401, or 403 without "plan" in the body
├── PlanLimitError              # 403 — tier blocks asset/session/history/Greeks
├── NotFoundError               # 404 — no data for that date/session
├── ValidationError             # 400 / 422 — malformed params
├── RateLimitError              # 429 — quota exceeded
├── ServerError                 # 5xx — transient server-side failure
└── TimeoutError                # request exceeded `timeout`
```

Every exception carries:

- `e.message` — human-readable text from the server
- `e.status_code` — HTTP status code (when applicable)
- `e.response_body` — the parsed JSON body (or raw text) for debugging

## Patterns

### Catch-all

```python
from cryptovol import CryptoVol, CryptoVolError

try:
    pt = cv.vol_surface(ccy="BTC", expiry="2026-12-26",
                        strike_type="moneyness", strike_value=1.0)
except CryptoVolError as e:
    log.error(f"CryptoVol call failed [{e.status_code}]: {e.message}")
```

### React to plan limits

If you ship code that might run under different subscription tiers, fall back gracefully:

```python
from cryptovol import PlanLimitError

try:
    pt = cv.vol_surface(ccy="ETH", expiry="2026-12-26",
                        strike_type="moneyness", strike_value=1.0,
                        session="asia")
except PlanLimitError:
    # Asia session is ULTRA-only — fall back to US
    pt = cv.vol_surface(ccy="ETH", expiry="2026-12-26",
                        strike_type="moneyness", strike_value=1.0,
                        session="us")
```

### Distinguish auth vs plan-limit

Both come back as HTTP 403. The SDK heuristic: if the response body mentions `"plan"`, `"upgrade"`, or `"tier"`, you get `PlanLimitError`; otherwise `AuthenticationError`.

```python
from cryptovol import AuthenticationError, PlanLimitError

try:
    ...
except AuthenticationError:
    print("Check your API key.")
except PlanLimitError as e:
    print(f"Upgrade needed: {e}")
```

### Retries

The client retries transient failures (5xx and 429) automatically with exponential backoff. To customize:

```python
cv = CryptoVol(api_key="...", max_retries=5)   # default is 3
cv = CryptoVol(api_key="...", max_retries=0)   # disable retries entirely
```

`RateLimitError` honors the `Retry-After` header when the server sends one.
