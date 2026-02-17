---
description: Quick reference for Stripe SDK patterns across languages
alwaysApply: false
---

# Stripe SDK Quick Reference

## Current Versions

| SDK | Version | API Version |
|-----|---------|-------------|
| stripe-python | 14.3.0 | 2026-01-28.clover |
| stripe-go | v84.3.0 | Fixed by SDK release |
| stripe-node | 17.x | 2026-01-28.clover |
| stripe-ruby | 13.x | 2026-01-28.clover |

## Client Initialization

**Python:**
```python
from stripe import StripeClient
client = StripeClient("sk_test_xxx", stripe_version="2026-01-28.clover")
```

**Go:** (version fixed by SDK — do not set manually)
```go
import "github.com/stripe/stripe-go/v84"
stripe.Key = "sk_test_xxx"
```

**Node.js:**
```javascript
const stripe = new Stripe('sk_test_xxx', { apiVersion: '2026-01-28.clover' });
```

**Ruby:**
```ruby
client = Stripe::StripeClient.new("sk_test_xxx", stripe_version: "2026-01-28.clover")
```

## Error Classes

**Python:**
```
stripe.StripeError
├── stripe.APIError
├── stripe.APIConnectionError
├── stripe.AuthenticationError
├── stripe.RateLimitError
├── stripe.SignatureVerificationError
└── stripe.StripeErrorWithParamCode
    ├── stripe.CardError
    └── stripe.InvalidRequestError
```
Properties: `e.message`, `e.user_message`, `e.http_status`, `e.code`, `e.param` (CardError/InvalidRequestError), `e.decline_code` (CardError)

**Go:**
```go
*stripe.Error  // single type, differentiate via .Type field
// stripe.ErrorTypeCard, stripe.ErrorTypeInvalidRequest, stripe.ErrorTypeAPI
```
Fields: `.Msg`, `.Type`, `.Code`, `.Param`, `.DeclineCode`, `.HTTPStatusCode`

**Node.js:** differentiate via `err.type` string:
`StripeCardError`, `StripeInvalidRequestError`, `StripeAuthenticationError`, `StripeRateLimitError`
Properties: `err.message`, `err.statusCode`, `err.code`, `err.param`

**Ruby:**
```
Stripe::StripeError → Stripe::CardError, Stripe::InvalidRequestError, Stripe::AuthenticationError, Stripe::RateLimitError, Stripe::SignatureVerificationError
```
Properties: `e.message`, `e.http_status`, `e.code`, `e.param`

## Webhook Verification

**Python:** `stripe.Webhook.construct_event(payload, sig_header, secret)`
**Go:** `webhook.ConstructEvent(body, sigHeader, secret)` — import `github.com/stripe/stripe-go/v84/webhook`
**Node.js:** `stripe.webhooks.constructEvent(payload, sigHeader, secret)`
**Ruby:** `Stripe::Webhook.construct_event(payload, sig_header, secret)`
