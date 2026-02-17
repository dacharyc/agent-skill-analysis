---
description: Stripe Go SDK API reference for stripe-go v84.x
alwaysApply: false
---

# Stripe Go SDK Reference

## Installation

```
go get github.com/stripe/stripe-go/v84
```

Current SDK version: 84.3.0

Import path: `github.com/stripe/stripe-go/v84`

**Important:** In Go (strongly-typed language), the API version is fixed by the SDK release. Do not manually set an API version — update the SDK instead.

## Authentication

```go
import "github.com/stripe/stripe-go/v84"

stripe.Key = "sk_test_xxx"
```

## Customer Operations

```go
import (
    "github.com/stripe/stripe-go/v84"
    "github.com/stripe/stripe-go/v84/customer"
)

// Create
params := &stripe.CustomerParams{
    Email: stripe.String("customer@example.com"),
}
params.AddMetadata("order_id", "123")
c, err := customer.New(params)

// Retrieve
c, err := customer.Get("cus_xxx", nil)

// Update
params := &stripe.CustomerParams{}
params.AddMetadata("order_id", "456")
c, err := customer.Update("cus_xxx", params)

// Delete
c, err := customer.Del("cus_xxx", nil)

// List
params := &stripe.CustomerListParams{}
params.Filters.AddFilter("limit", "", "10")
i := customer.List(params)
for i.Next() {
    c := i.Customer()
    fmt.Println(c.ID)
}
```

### Customer Client struct

```go
type Client struct {
    B   stripe.Backend
    Key string
}
```

Package-level functions (`customer.New`, `customer.Get`, etc.) use a default client with `stripe.Key`. Method-level variants (`client.New`, `client.Get`) allow custom backends.

## Subscription Operations

```go
import (
    "github.com/stripe/stripe-go/v84"
    "github.com/stripe/stripe-go/v84/subscription"
)

// Create
params := &stripe.SubscriptionParams{
    Customer: stripe.String("cus_xxx"),
    Items: []*stripe.SubscriptionItemsParams{
        {Price: stripe.String("price_xxx")},
    },
}
s, err := subscription.New(params)

// Retrieve
s, err := subscription.Get("sub_xxx", nil)

// Cancel
s, err := subscription.Cancel("sub_xxx", nil)
```

## Error Handling

```go
import "github.com/stripe/stripe-go/v84"

// Error type constants
stripe.ErrorTypeAPI            // "api_error"
stripe.ErrorTypeCard           // "card_error"
stripe.ErrorTypeIdempotency    // "idempotency_error"
stripe.ErrorTypeInvalidRequest // "invalid_request_error"

// Error struct fields
type Error struct {
    ChargeID       string          `json:"charge,omitempty"`
    Code           ErrorCode       `json:"code,omitempty"`
    DeclineCode    DeclineCode     `json:"decline_code,omitempty"`
    DocURL         string          `json:"doc_url,omitempty"`
    HTTPStatusCode int             `json:"status,omitempty"`
    Msg            string          `json:"message"`
    Param          string          `json:"param,omitempty"`
    PaymentIntent  *PaymentIntent  `json:"payment_intent,omitempty"`
    RequestID      string          `json:"request_id,omitempty"`
    Type           ErrorType       `json:"type"`
}

// Usage
c, err := customer.New(params)
if err != nil {
    if stripeErr, ok := err.(*stripe.Error); ok {
        switch stripeErr.Type {
        case stripe.ErrorTypeCard:
            fmt.Printf("Card error: %s\n", stripeErr.Msg)
        case stripe.ErrorTypeInvalidRequest:
            fmt.Printf("Invalid: %s, param: %s\n", stripeErr.Msg, stripeErr.Param)
        default:
            fmt.Printf("Stripe error: %s\n", stripeErr.Msg)
        }
    }
}
```

## Webhook Verification

```go
import "github.com/stripe/stripe-go/v84/webhook"

event, err := webhook.ConstructEvent(
    body,           // []byte — raw request body
    sigHeader,      // string — Stripe-Signature header
    "whsec_xxx",    // string — webhook signing secret
)
if err != nil {
    // handle signature verification failure
}

switch event.Type {
case "customer.subscription.created":
    // handle
case "customer.subscription.updated":
    // handle
}
```

## Pagination

```go
import (
    "github.com/stripe/stripe-go/v84"
    "github.com/stripe/stripe-go/v84/customer"
)

// Auto-pagination via iterator
params := &stripe.CustomerListParams{}
params.Filters.AddFilter("limit", "", "100")
i := customer.List(params)
for i.Next() {
    c := i.Customer()
    fmt.Println(c.ID)
}
if err := i.Err(); err != nil {
    log.Fatal(err)
}
```

List parameters: `Limit` (1-100, default 10), `StartingAfter`, `EndingBefore`.

## Expanding Objects

```go
params := &stripe.PaymentIntentParams{}
params.AddExpand("customer")
params.AddExpand("payment_method")

pi, err := paymentintent.Get("pi_xxx", params)
// pi.Customer is now a full *stripe.Customer, not just an ID string

// Nested expansion (up to 4 levels)
params.AddExpand("latest_charge.balance_transaction")

// Expand on list endpoints
listParams := &stripe.InvoiceListParams{}
listParams.AddExpand("data.customer")
listParams.AddExpand("data.subscription")
```

## Idempotency Keys

```go
import "github.com/google/uuid"

params := &stripe.CustomerParams{
    Email: stripe.String("customer@example.com"),
}
params.SetIdempotencyKey(uuid.New().String())
c, err := customer.New(params)
```

- Use for all creation/update calls
- Keys expire after 24 hours
- Max 255 characters

## Metadata

```go
// Set metadata on creation
params := &stripe.CustomerParams{
    Email: stripe.String("customer@example.com"),
}
params.AddMetadata("order_id", "6735")
params.AddMetadata("internal_ref", "abc123")
c, err := customer.New(params)

// Access metadata
fmt.Println(c.Metadata["order_id"])
```

Limits: 50 keys max, key names up to 40 chars, values up to 500 chars.

## Error Handling Best Practices

### Retry with Exponential Backoff

```go
func createCustomerWithRetry(params *stripe.CustomerParams, maxRetries int) (*stripe.Customer, error) {
    var lastErr error
    for attempt := 0; attempt < maxRetries; attempt++ {
        c, err := customer.New(params)
        if err == nil {
            return c, nil
        }
        lastErr = err
        if stripeErr, ok := err.(*stripe.Error); ok {
            switch stripeErr.Type {
            case stripe.ErrorTypeInvalidRequest, stripe.ErrorTypeCard:
                return nil, err // non-retryable
            }
        }
        time.Sleep(time.Duration(1<<uint(attempt)) * time.Second)
    }
    return nil, lastErr
}
```

### Complete Webhook Handler

```go
func handleWebhook(w http.ResponseWriter, r *http.Request) {
    body, err := io.ReadAll(r.Body)
    if err != nil {
        http.Error(w, "read body", http.StatusBadRequest)
        return
    }

    event, err := webhook.ConstructEvent(
        body,
        r.Header.Get("Stripe-Signature"),
        webhookSecret,
    )
    if err != nil {
        http.Error(w, "verify signature", http.StatusBadRequest)
        return
    }

    switch event.Type {
    case "customer.subscription.created":
        var sub stripe.Subscription
        if err := json.Unmarshal(event.Data.Raw, &sub); err != nil {
            log.Printf("parse subscription: %v", err)
            http.Error(w, "parse", http.StatusBadRequest)
            return
        }
        handleSubscriptionCreated(&sub)
    case "customer.subscription.updated":
        var sub stripe.Subscription
        if err := json.Unmarshal(event.Data.Raw, &sub); err != nil {
            log.Printf("parse subscription: %v", err)
            http.Error(w, "parse", http.StatusBadRequest)
            return
        }
        handleSubscriptionUpdated(&sub)
    case "customer.subscription.deleted":
        var sub stripe.Subscription
        if err := json.Unmarshal(event.Data.Raw, &sub); err != nil {
            log.Printf("parse subscription: %v", err)
            http.Error(w, "parse", http.StatusBadRequest)
            return
        }
        handleSubscriptionDeleted(&sub)
    case "payment_intent.payment_failed":
        var pi stripe.PaymentIntent
        if err := json.Unmarshal(event.Data.Raw, &pi); err != nil {
            log.Printf("parse payment intent: %v", err)
            http.Error(w, "parse", http.StatusBadRequest)
            return
        }
        if pi.LastPaymentError != nil {
            log.Printf("payment failed: %s (type: %s)",
                pi.LastPaymentError.Msg, pi.LastPaymentError.Type)
        }
    default:
        log.Printf("unhandled event type: %s", event.Type)
    }

    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]bool{"received": true})
}
```

Key webhook best practices:
- Return 200 quickly before heavy processing
- Unmarshal `event.Data.Raw` into the appropriate struct type
- Log event IDs to detect duplicates
- Events are not delivered in order; handlers must be order-independent
- Stripe retries for up to 3 days with exponential backoff
