---
description: Stripe Python SDK API reference for version 14.x (API version 2026-01-28.clover)
alwaysApply: false
---

# Stripe Python SDK Reference

## Installation & Version

```
pip install stripe>=14.0.0
```

Current SDK version: 14.3.0
Current API version: `2026-01-28.clover`

## Client Initialization

The recommended approach is `StripeClient`:

```python
from stripe import StripeClient

client = StripeClient(
    "sk_test_xxx",
    stripe_version="2026-01-28.clover",  # optional, defaults to SDK's pinned version
)
```

Constructor parameters:
- `api_key: str` (required)
- `stripe_account: str | None` — for Connect
- `stripe_version: str | None` — override API version
- `base_addresses: BaseAddresses | None` — custom endpoints
- `max_network_retries: int | None`
- `http_client: HTTPClient | None`

Legacy global configuration (still supported):

```python
import stripe

stripe.api_key = "sk_test_xxx"
stripe.api_version = "2026-01-28.clover"
```

## Customer Operations

```python
# Create
customer = client.v1.customers.create(
    params={
        "email": "customer@example.com",
        "metadata": {"order_id": "123"},
    }
)

# Retrieve
customer = client.v1.customers.retrieve("cus_xxx")

# Update
customer = client.v1.customers.update(
    "cus_xxx",
    params={"metadata": {"order_id": "456"}},
)

# Delete
client.v1.customers.delete("cus_xxx")

# List
customers = client.v1.customers.list(params={"limit": 10})
for customer in customers.auto_paging_iter():
    print(customer.id)
```

## Subscription Operations

```python
# Create
subscription = client.v1.subscriptions.create(
    params={
        "customer": "cus_xxx",
        "items": [{"price": "price_xxx"}],
    }
)

# Retrieve
subscription = client.v1.subscriptions.retrieve("sub_xxx")

# Cancel
client.v1.subscriptions.cancel("sub_xxx")
```

## Error Handling

Exception hierarchy:

```
StripeError (base)
├── APIError
├── APIConnectionError
├── AuthenticationError
├── PermissionError
├── RateLimitError
├── SignatureVerificationError
├── IdempotencyError
├── TemporarySessionExpiredError
└── StripeErrorWithParamCode
    ├── CardError
    └── InvalidRequestError
```

`StripeError` base class properties:
- `message: str` — human-readable error message
- `user_message: str | None` — user-safe message (present on all StripeError subclasses)
- `http_status: int | None`
- `code: str | None` — e.g., `"card_declined"`, `"invalid_number"`
- `json_body: dict | None` — raw API error response
- `request_id: str | None`

`StripeErrorWithParamCode` adds:
- `param: str | None` — the parameter that caused the error

`CardError` adds:
- `decline_code: str | None` — card issuer decline reason

Usage:

```python
import stripe

try:
    customer = client.v1.customers.create(params={"email": "test@example.com"})
except stripe.InvalidRequestError as e:
    print(f"Invalid request: {e.message}, param: {e.param}")
except stripe.CardError as e:
    print(f"Card error: {e.user_message}, code: {e.code}")
except stripe.AuthenticationError:
    print("Invalid API key")
except stripe.StripeError as e:
    print(f"Stripe error: {e.message}")
```

## Webhook Verification

```python
import stripe

event = stripe.Webhook.construct_event(
    payload=request.body,        # raw request body bytes
    sig_header=request.headers["Stripe-Signature"],
    secret="whsec_xxx",
)

# Or using StripeClient:
event = client.construct_event(
    payload=request.body,
    sig_header=request.headers["Stripe-Signature"],
    secret="whsec_xxx",
)
```

## Per-Request Version Override

```python
# Using legacy API
stripe.Customer.create(
    email="customer@example.com",
    stripe_version="2026-01-28.clover",
)

# Using StripeClient — version is set at client init
# Per-request override uses options dict:
customer = client.v1.customers.create(
    params={"email": "test@example.com"},
    options={"stripe_version": "2026-01-28.clover"},
)
```

## Pagination

```python
# Manual cursor-based pagination
customers = client.v1.customers.list(params={"limit": 100})
while customers.has_more:
    customers = client.v1.customers.list(
        params={"limit": 100, "starting_after": customers.data[-1].id}
    )

# Auto-pagination (recommended)
for customer in client.v1.customers.list(params={"limit": 100}).auto_paging_iter():
    process(customer)
```

List parameters:
- `limit`: 1-100 (default 10)
- `starting_after`: cursor for forward pagination (object ID)
- `ending_before`: cursor for backward pagination (object ID)

## Expanding Objects

Retrieve related objects inline instead of making separate API calls:

```python
# Expand a single related object
payment_intent = client.v1.payment_intents.retrieve(
    "pi_xxx",
    params={"expand": ["customer"]},
)
# payment_intent.customer is now a full Customer object, not just an ID

# Nested expansion (up to 4 levels deep)
charge = client.v1.charges.retrieve(
    "ch_xxx",
    params={"expand": ["customer", "payment_intent.customer"]},
)

# Expand on list endpoints
invoices = client.v1.invoices.list(
    params={"expand": ["data.customer", "data.subscription"]},
)
```

## Idempotency Keys

Safely retry creation requests without risk of duplicates:

```python
import uuid

customer = client.v1.customers.create(
    params={"email": "customer@example.com"},
    options={"idempotency_key": str(uuid.uuid4())},
)

# Legacy API
stripe.Customer.create(
    email="customer@example.com",
    idempotency_key=str(uuid.uuid4()),
)
```

- Use for all POST requests (creation/update)
- Not needed for GET/DELETE (inherently idempotent)
- Keys expire after 24 hours
- Max 255 characters; V4 UUIDs recommended

## Metadata

Attach custom key-value data to objects:

```python
# Set metadata on creation
customer = client.v1.customers.create(
    params={
        "email": "customer@example.com",
        "metadata": {"order_id": "6735", "internal_ref": "abc123"},
    }
)

# Update metadata (merges with existing)
customer = client.v1.customers.update(
    "cus_xxx",
    params={"metadata": {"order_id": "6736"}},
)

# Delete a metadata key (set to empty string)
customer = client.v1.customers.update(
    "cus_xxx",
    params={"metadata": {"internal_ref": ""}},
)
```

Limits: 50 keys max, key names up to 40 chars, values up to 500 chars.

## Error Handling Best Practices

### Retry Logic with Exponential Backoff

```python
import time
import stripe

MAX_RETRIES = 3

def create_customer_with_retry(client, params):
    for attempt in range(MAX_RETRIES):
        try:
            return client.v1.customers.create(params=params)
        except stripe.APIConnectionError:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)  # exponential backoff
        except stripe.RateLimitError:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)
        except stripe.InvalidRequestError:
            raise  # non-retryable
        except stripe.CardError:
            raise  # non-retryable
```

### Webhook Handler Pattern

```python
from flask import Flask, request, jsonify
import stripe

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, "whsec_xxx")
    except ValueError:
        return jsonify(error="Invalid payload"), 400
    except stripe.SignatureVerificationError:
        return jsonify(error="Invalid signature"), 400

    # Handle specific event types
    if event.type == "customer.subscription.created":
        subscription = event.data.object
        handle_subscription_created(subscription)
    elif event.type == "customer.subscription.updated":
        subscription = event.data.object
        handle_subscription_updated(subscription)
    elif event.type == "customer.subscription.deleted":
        subscription = event.data.object
        handle_subscription_deleted(subscription)
    elif event.type == "payment_intent.payment_failed":
        payment_intent = event.data.object
        error = payment_intent.last_payment_error
        if error and error.type == "card_error":
            notify_customer(payment_intent.customer, error.message)

    return jsonify(success=True), 200
```

Key webhook best practices:
- Return 2xx quickly before complex processing
- Log event IDs to prevent duplicate processing
- Use async queues for heavy processing
- Events are not guaranteed in order; design handlers to be order-independent
- Stripe retries failed deliveries for up to 3 days with exponential backoff
