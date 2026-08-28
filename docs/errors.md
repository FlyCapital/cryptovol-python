# Error handling

Every API failure becomes a typed Python exception. Catch the base class to handle anything, or a specific subclass to react narrowly.

## Hierarchy

```
CryptoVolError                  # base — catch this to handle anything
├── AuthenticationError         # 401, or 403 without "plan" in the body
├── PlanLimitError              # 403 — reserved; every plan currently has full
│                                #   access (all assets/sessions/history/Greeks),
│                                #   pay-as-you-go at $0.001/call, so this
│                                #   shouldn't fire in practice today
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

Every plan currently has full access — all assets, all sessions, full history, Greeks, and raw quotes — so `PlanLimitError` shouldn't fire under normal use today. It's kept in the hierarchy for forward compatibility; catch it if you want to be defensive against future plan changes:

```python
from cryptovol import PlanLimitError

try:
    pt = cv.vol_surface(ccy="ETH", expiry="2026-12-26",
                        strike_type="moneyness", strike_value=1.0,
                        session="asia")
except PlanLimitError:
    # Defensive fallback — shouldn't trigger under the current flat-access model
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
