---
description: Stripe Ruby SDK API reference for stripe gem v13.x
alwaysApply: false
---

# Stripe Ruby SDK Reference

## Installation

```ruby
gem 'stripe', '~> 13.0'
```

## Client Initialization

The recommended approach is `Stripe::StripeClient`:

```ruby
client = Stripe::StripeClient.new("sk_test_xxx")

# With explicit version:
client = Stripe::StripeClient.new(
  "sk_test_xxx",
  stripe_version: "2026-01-28.clover"
)
```

Constructor parameters:
- `api_key` (required)
- `stripe_account:` — for Connect
- `stripe_version:` — override API version

Legacy global configuration (still supported):

```ruby
Stripe.api_key = "sk_test_xxx"
Stripe.api_version = "2026-01-28.clover"
```

## Customer Operations

```ruby
# Create
customer = client.v1.customers.create(
  email: "customer@example.com",
  metadata: { order_id: "123" }
)

# Retrieve
customer = client.v1.customers.retrieve("cus_xxx")

# Update
customer = client.v1.customers.update(
  "cus_xxx",
  metadata: { order_id: "456" }
)

# Delete
client.v1.customers.delete("cus_xxx")

# List
customers = client.v1.customers.list(limit: 10)
customers.auto_paging_each do |customer|
  puts customer.id
end
```

## Subscription Operations

```ruby
# Create
subscription = client.v1.subscriptions.create(
  customer: "cus_xxx",
  items: [{ price: "price_xxx" }]
)

# Retrieve
subscription = client.v1.subscriptions.retrieve("sub_xxx")

# Cancel
client.v1.subscriptions.cancel("sub_xxx")
```

## Error Handling

```ruby
begin
  customer = client.v1.customers.create(email: "test@example.com")
rescue Stripe::CardError => e
  puts "Card error: #{e.message}"
  puts "Code: #{e.code}"
  puts "Param: #{e.param}"
rescue Stripe::InvalidRequestError => e
  puts "Invalid request: #{e.message}, param: #{e.param}"
rescue Stripe::AuthenticationError
  puts "Invalid API key"
rescue Stripe::RateLimitError
  puts "Rate limited"
rescue Stripe::StripeError => e
  puts "Stripe error: #{e.message}"
end
```

Exception hierarchy:

```
Stripe::StripeError (base)
├── Stripe::APIError
├── Stripe::APIConnectionError
├── Stripe::AuthenticationError
├── Stripe::PermissionError
├── Stripe::RateLimitError
├── Stripe::SignatureVerificationError
├── Stripe::IdempotencyError
├── Stripe::CardError
└── Stripe::InvalidRequestError
```

Error properties:
- `e.message` — human-readable error message
- `e.http_status` — HTTP status code
- `e.code` — Stripe error code
- `e.param` — parameter that caused the error (CardError, InvalidRequestError)
- `e.request_id` — Stripe request ID

## Webhook Verification

```ruby
# In a Rails controller or Sinatra route:
payload = request.body.read
sig_header = request.env["HTTP_STRIPE_SIGNATURE"]

begin
  event = Stripe::Webhook.construct_event(
    payload,        # raw request body string
    sig_header,     # Stripe-Signature header value
    "whsec_xxx"     # webhook signing secret
  )
rescue JSON::ParserError => e
  # Invalid payload
  status 400
  return
rescue Stripe::SignatureVerificationError => e
  # Invalid signature
  status 400
  return
end

case event.type
when "customer.subscription.created"
  # handle
when "customer.subscription.updated"
  # handle
when "customer.subscription.deleted"
  # handle
end
```

`construct_event` signature:
```ruby
Stripe::Webhook.construct_event(payload, sig_header, secret, tolerance: 300)
```
- `payload`: raw request body string
- `sig_header`: value of `Stripe-Signature` header
- `secret`: webhook endpoint signing secret
- `tolerance:`: optional, seconds (default 300)

## Pagination

```ruby
# Manual pagination
customers = client.v1.customers.list(limit: 100)
loop do
  customers.data.each { |c| process(c) }
  break unless customers.has_more
  customers = client.v1.customers.list(
    limit: 100,
    starting_after: customers.data.last.id
  )
end

# Auto-pagination (recommended)
client.v1.customers.list(limit: 100).auto_paging_each do |customer|
  process(customer)
end
```

List parameters: `limit` (1-100, default 10), `starting_after`, `ending_before`.

## Expanding Objects

```ruby
# Expand related objects inline
payment_intent = client.v1.payment_intents.retrieve(
  "pi_xxx",
  expand: ["customer", "payment_method"]
)
# payment_intent.customer is now a full Stripe::Customer object

# Nested expansion (up to 4 levels)
charge = client.v1.charges.retrieve(
  "ch_xxx",
  expand: ["customer", "payment_intent.customer"]
)

# Expand on creation
subscription = client.v1.subscriptions.create(
  customer: "cus_xxx",
  items: [{ price: "price_xxx" }],
  expand: ["latest_invoice.payment_intent"]
)

# Expand on list endpoints (prefix with data.)
invoices = client.v1.invoices.list(
  expand: ["data.customer", "data.subscription"]
)
```

## Idempotency Keys

```ruby
require "securerandom"

customer = client.v1.customers.create(
  { email: "customer@example.com" },
  { idempotency_key: SecureRandom.uuid }
)

# Legacy API
Stripe::Customer.create(
  { email: "customer@example.com" },
  { idempotency_key: SecureRandom.uuid }
)
```

- Use for all POST requests
- Keys expire after 24 hours
- Max 255 characters

## Metadata

```ruby
# Set metadata on creation
customer = client.v1.customers.create(
  email: "customer@example.com",
  metadata: { order_id: "6735", internal_ref: "abc123" }
)

# Update metadata (merges with existing)
client.v1.customers.update(
  "cus_xxx",
  metadata: { order_id: "6736" }
)

# Delete a metadata key (set to empty string)
client.v1.customers.update(
  "cus_xxx",
  metadata: { internal_ref: "" }
)

# Access metadata
puts customer.metadata["order_id"]
```

Limits: 50 keys max, key names up to 40 chars, values up to 500 chars.

## Error Handling Best Practices

### Retry with Exponential Backoff

```ruby
def create_customer_with_retry(client, params, max_retries: 3)
  max_retries.times do |attempt|
    begin
      return client.v1.customers.create(**params)
    rescue Stripe::APIConnectionError, Stripe::RateLimitError => e
      raise if attempt == max_retries - 1
      sleep(2**attempt)
    rescue Stripe::InvalidRequestError, Stripe::CardError
      raise # non-retryable
    end
  end
end
```

### Complete Rails Webhook Controller

```ruby
class WebhooksController < ApplicationController
  skip_before_action :verify_authenticity_token

  def create
    payload = request.body.read
    sig_header = request.env["HTTP_STRIPE_SIGNATURE"]

    begin
      event = Stripe::Webhook.construct_event(
        payload, sig_header, Rails.application.credentials.stripe_webhook_secret
      )
    rescue JSON::ParserError
      head :bad_request and return
    rescue Stripe::SignatureVerificationError
      head :bad_request and return
    end

    # Idempotency: skip already-processed events
    return head :ok if ProcessedEvent.exists?(stripe_event_id: event.id)
    ProcessedEvent.create!(stripe_event_id: event.id)

    case event.type
    when "customer.subscription.created"
      subscription = event.data.object
      SubscriptionService.handle_created(subscription)
    when "customer.subscription.updated"
      subscription = event.data.object
      SubscriptionService.handle_updated(subscription)
    when "customer.subscription.deleted"
      subscription = event.data.object
      SubscriptionService.handle_deleted(subscription)
    when "payment_intent.payment_failed"
      payment_intent = event.data.object
      error = payment_intent.last_payment_error
      if error&.type == "card_error"
        CustomerNotifier.payment_failed(
          payment_intent.customer,
          error.message
        ).deliver_later
      end
    else
      Rails.logger.info("Unhandled webhook event: #{event.type}")
    end

    head :ok
  end
end
```

Key webhook best practices:
- Skip CSRF verification for webhook routes
- Return 2xx quickly before heavy processing
- Log event IDs to prevent duplicate processing
- Use `deliver_later` / background jobs for async processing
- Events are not guaranteed in order
- Stripe retries for up to 3 days with exponential backoff
