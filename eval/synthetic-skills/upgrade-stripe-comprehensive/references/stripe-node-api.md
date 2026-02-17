---
description: Stripe Node.js SDK API reference for stripe v17.x
alwaysApply: false
---

# Stripe Node.js SDK Reference

## Installation

```
npm install stripe
```

## Client Initialization

```javascript
const Stripe = require('stripe');

const stripe = new Stripe('sk_test_xxx', {
  apiVersion: '2026-01-28.clover',  // recommended: pin version explicitly
});
```

Constructor options:
- `apiVersion: string` — API version to use
- `maxNetworkRetries: number` — retry count (default 2)
- `timeout: number` — request timeout in ms (default 80000)
- `httpAgent: http.Agent` — custom HTTP agent
- `stripeAccount: string` — for Connect

## Customer Operations

```javascript
// Create
const customer = await stripe.customers.create({
  email: 'customer@example.com',
  metadata: { order_id: '123' },
});

// Retrieve
const customer = await stripe.customers.retrieve('cus_xxx');

// Update
const customer = await stripe.customers.update('cus_xxx', {
  metadata: { order_id: '456' },
});

// Delete
const deleted = await stripe.customers.del('cus_xxx');

// List
const customers = await stripe.customers.list({ limit: 10 });
for await (const customer of stripe.customers.list({ limit: 10 })) {
  console.log(customer.id);
}
```

## Subscription Operations

```javascript
// Create
const subscription = await stripe.subscriptions.create({
  customer: 'cus_xxx',
  items: [{ price: 'price_xxx' }],
});

// Retrieve
const subscription = await stripe.subscriptions.retrieve('sub_xxx');

// Cancel
const canceled = await stripe.subscriptions.cancel('sub_xxx');
```

## Error Handling

```javascript
try {
  const customer = await stripe.customers.create({ email: 'test@example.com' });
} catch (err) {
  switch (err.type) {
    case 'StripeCardError':
      console.log(`Card error: ${err.message}`);
      break;
    case 'StripeInvalidRequestError':
      console.log(`Invalid request: ${err.message}`);
      break;
    case 'StripeAuthenticationError':
      console.log('Invalid API key');
      break;
    case 'StripeRateLimitError':
      console.log('Rate limited');
      break;
    default:
      console.log(`Stripe error: ${err.message}`);
  }
}
```

Error properties:
- `err.type` — error type string
- `err.message` — human-readable message
- `err.statusCode` — HTTP status code
- `err.code` — Stripe error code (e.g., `"card_declined"`)
- `err.param` — parameter that caused the error
- `err.requestId` — Stripe request ID

## Webhook Verification

```javascript
const express = require('express');
const app = express();

// IMPORTANT: Use express.raw() for the webhook endpoint, not express.json()
app.post('/webhook',
  express.raw({ type: 'application/json' }),
  (req, res) => {
    const sig = req.headers['stripe-signature'];

    let event;
    try {
      event = stripe.webhooks.constructEvent(
        req.body,       // raw body (Buffer)
        sig,            // Stripe-Signature header
        'whsec_xxx',    // webhook signing secret
      );
    } catch (err) {
      console.log(`Webhook signature verification failed: ${err.message}`);
      return res.status(400).send(`Webhook Error: ${err.message}`);
    }

    switch (event.type) {
      case 'customer.subscription.created':
        // handle
        break;
      case 'customer.subscription.updated':
        // handle
        break;
      case 'customer.subscription.deleted':
        // handle
        break;
    }

    res.json({ received: true });
  }
);
```

`constructEvent` signature:
```javascript
stripe.webhooks.constructEvent(payload, sigHeader, secret, tolerance?)
```
- `payload`: raw request body (string or Buffer)
- `sigHeader`: value of `Stripe-Signature` header
- `secret`: webhook endpoint signing secret
- `tolerance`: optional, seconds (default 300)

## Pagination

```javascript
// Manual pagination
let hasMore = true;
let startingAfter;
while (hasMore) {
  const result = await stripe.customers.list({
    limit: 100,
    ...(startingAfter && { starting_after: startingAfter }),
  });
  for (const customer of result.data) {
    process(customer);
  }
  hasMore = result.has_more;
  if (result.data.length > 0) {
    startingAfter = result.data[result.data.length - 1].id;
  }
}

// Auto-pagination (recommended)
for await (const customer of stripe.customers.list({ limit: 100 })) {
  process(customer);
}
```

List parameters: `limit` (1-100, default 10), `starting_after`, `ending_before`.

## Expanding Objects

```javascript
// Expand related objects inline
const paymentIntent = await stripe.paymentIntents.retrieve('pi_xxx', {
  expand: ['customer', 'payment_method'],
});
// paymentIntent.customer is now a full object, not just 'cus_xxx'

// Nested expansion (up to 4 levels)
const charge = await stripe.charges.retrieve('ch_xxx', {
  expand: ['customer', 'payment_intent.customer'],
});

// Expand on creation
const subscription = await stripe.subscriptions.create({
  customer: 'cus_xxx',
  items: [{ price: 'price_xxx' }],
  expand: ['latest_invoice.payment_intent'],
});

// Expand on list endpoints (prefix with data.)
const invoices = await stripe.invoices.list({
  expand: ['data.customer', 'data.subscription'],
});
```

## Idempotency Keys

```javascript
const { v4: uuidv4 } = require('uuid');

const customer = await stripe.customers.create(
  { email: 'customer@example.com' },
  { idempotencyKey: uuidv4() },
);

// Automatic retries use idempotency keys internally
const stripe = new Stripe('sk_test_xxx', {
  maxNetworkRetries: 2,  // library auto-generates idempotency keys for retries
});
```

- Use for all POST requests
- Keys expire after 24 hours
- Max 255 characters

## Metadata

```javascript
// Set metadata on creation
const customer = await stripe.customers.create({
  email: 'customer@example.com',
  metadata: { order_id: '6735', internal_ref: 'abc123' },
});

// Update metadata (merges with existing)
await stripe.customers.update('cus_xxx', {
  metadata: { order_id: '6736' },
});

// Delete a metadata key (set to null or empty string)
await stripe.customers.update('cus_xxx', {
  metadata: { internal_ref: null },
});

// Access metadata
console.log(customer.metadata.order_id);
```

Limits: 50 keys max, key names up to 40 chars, values up to 500 chars.

## Error Handling Best Practices

### Retry with Exponential Backoff

```javascript
async function createCustomerWithRetry(params, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await stripe.customers.create(params);
    } catch (err) {
      // Non-retryable errors
      if (err.type === 'StripeCardError' ||
          err.type === 'StripeInvalidRequestError' ||
          err.type === 'StripeAuthenticationError') {
        throw err;
      }
      // Retryable: connection, rate limit, API errors
      if (attempt === maxRetries - 1) throw err;
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
    }
  }
}
```

### Complete Webhook Handler with Async Processing

```javascript
const express = require('express');
const Stripe = require('stripe');

const stripe = new Stripe('sk_test_xxx', {
  apiVersion: '2026-01-28.clover',
});
const app = express();

// Track processed events to prevent duplicates
const processedEvents = new Set();

app.post('/webhook',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const sig = req.headers['stripe-signature'];

    let event;
    try {
      event = stripe.webhooks.constructEvent(req.body, sig, 'whsec_xxx');
    } catch (err) {
      console.error(`Signature verification failed: ${err.message}`);
      return res.status(400).json({ error: err.message });
    }

    // Idempotency: skip already-processed events
    if (processedEvents.has(event.id)) {
      return res.json({ received: true });
    }
    processedEvents.add(event.id);

    // Return 200 immediately, process asynchronously
    res.json({ received: true });

    // Async processing
    try {
      switch (event.type) {
        case 'customer.subscription.created':
          await handleSubscriptionCreated(event.data.object);
          break;
        case 'customer.subscription.updated':
          await handleSubscriptionUpdated(event.data.object);
          break;
        case 'customer.subscription.deleted':
          await handleSubscriptionDeleted(event.data.object);
          break;
        case 'payment_intent.payment_failed': {
          const pi = event.data.object;
          if (pi.last_payment_error?.type === 'card_error') {
            await notifyCustomer(pi.customer, pi.last_payment_error.message);
          }
          break;
        }
      }
    } catch (err) {
      console.error(`Error processing ${event.type}: ${err.message}`);
    }
  }
);
```

Key webhook best practices:
- Use `express.raw()` not `express.json()` for the webhook route
- Return 2xx immediately before processing
- Log event IDs to prevent duplicate processing
- Events are not guaranteed in order
- Stripe retries for up to 3 days with exponential backoff
