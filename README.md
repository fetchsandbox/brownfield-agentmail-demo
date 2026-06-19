# Customer support reply hub

<a href="https://www.producthunt.com/products/fetchsandbox?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-fetchsandbox" target="_blank" rel="noopener noreferrer"><img alt="FetchSandbox - Runnable API integrations for developers and AI agents | Product Hunt" width="250" height="54" src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1175731&theme=light"></a>


Each customer in our orders app gets their own reply-address. When they
email it, our agent reads the message, looks up the order, and responds
inline. Next.js 15 (App Router) on the front, FastAPI on the back, Clerk
for auth, Postgres for orders.

## Stack

| Layer    | What |
|---|---|
| Frontend | Next.js 15 + React 19, Clerk (`@clerk/nextjs`) |
| Backend  | FastAPI, Clerk JWT verify, Postgres orders table |
| Email    | Resend for outbound (order confirmations, receipts) |
| Workspace| pnpm monorepo: `web/` + `server/` |

## What's wired

- `POST /api/orders` — Clerk-gated; creates an order row in Postgres
- `POST /api/resend-webhook` — Svix-signed; updates delivery state on
  `email.delivered` / `email.bounced`
- `GET /api/orders/[id]` — order detail page

## What's NOT wired yet

- **Per-customer reply inbox.** Every customer needs a unique address
  they can email about their order. Today they all reply to `support@`,
  hit a shared queue, and lose the order context. We want one inbox per
  `user_id`, with `metadata.order_ref` stamped on it so the inbound
  webhook can route directly back to the right order.

- **Inbound message handling.** When a customer emails their inbox,
  we need to receive the `message.delivered` event for THAT inbox
  specifically — NOT org-wide. Org-wide subscription leaks cross-tenant
  data through one endpoint, which is a non-starter for a multi-tenant
  agent deployment.

- **Webhook scope reconciliation.** After subscribe, re-read the
  webhook and confirm `inbox_ids` persisted as sent. The POST response
  echoes the request; only the GET tells us what AgentMail actually
  stored. Reconcile on every create.

## Run locally

```bash
pnpm install

# Python deps in a dedicated venv
cd server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Copy .env.example to .env and fill in your Clerk + (eventually) AgentMail keys
cp server/.env.example server/.env

pnpm dev   # web on :3000, server on :8000
```

Open http://localhost:3000, sign in via Clerk, place a test order.

## Agent task

Wire the three "NOT wired yet" items using **AgentMail** via the
fetchsandbox MCP server (`.mcp.json` is already configured — no API key
needed, no account required).

Curated AgentMail workflows are available to verify the integration
shape before you touch real code:

- `inbox_create_and_subscribe_webhook` — 4 steps, end-to-end inbox
  provisioning + scoped webhook subscribe
- `webhook_lifecycle_create_read_delete` — 4 steps, full webhook CRUD
  for teardown safety

Run them via MCP first to see the exact shape AgentMail expects, then
mirror that shape into `server/main.py` as real handlers.
