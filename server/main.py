import os
import httpx
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from svix.webhooks import Webhook, WebhookVerificationError

# ── Wired today: Clerk auth + Postgres orders + Resend outbound ────────
# ── NOT wired yet: AgentMail per-customer reply inbox + scoped webhook
#    See README → "What's NOT wired yet" + "Agent task".

ORDERS_DB_URL = os.environ["ORDERS_DB_URL"]
CLERK_JWT_ISSUER = os.environ["CLERK_JWT_ISSUER"]
CLERK_JWKS_URL = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
RESEND_WEBHOOK_SECRET = os.environ["RESEND_WEBHOOK_SECRET"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
bearer_scheme = HTTPBearer()
jwks_client = jwt.PyJWKClient(CLERK_JWKS_URL)


def verify_clerk_jwt(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(creds.credentials).key
        payload = jwt.decode(
            creds.credentials,
            signing_key,
            algorithms=["RS256"],
            issuer=CLERK_JWT_ISSUER,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"invalid token: {e}")
    return payload["sub"]


class OrderRequest(BaseModel):
    sku: str
    quantity: int = 1
    note: str | None = None


@app.post("/api/orders")
def create_order(
    req: OrderRequest,
    user_id: str = Depends(verify_clerk_jwt),
):
    """Create an order row in Postgres. Clerk-gated."""
    order_id = _insert_order(
        user_id=user_id, sku=req.sku, quantity=req.quantity, note=req.note,
    )
    return {"order_id": order_id, "user_id": user_id, "sku": req.sku}


@app.get("/api/orders/{order_id}")
def get_order(order_id: str, user_id: str = Depends(verify_clerk_jwt)):
    """Order detail page data. Clerk-gated; only owner can read."""
    row = _fetch_order(order_id=order_id, user_id=user_id)
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return row


@app.post("/api/resend-webhook")
async def resend_webhook(request: Request):
    """Svix-signed Resend webhook — updates delivery state on email events."""
    payload = await request.body()
    try:
        event = Webhook(RESEND_WEBHOOK_SECRET).verify(payload, dict(request.headers))
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="invalid signature")

    event_type = event.get("type")
    data = event.get("data", {})
    if event_type == "email.delivered":
        _mark_email_delivered(message_id=data.get("email_id"))
    elif event_type == "email.bounced":
        _mark_email_bounced(
            message_id=data.get("email_id"),
            reason=data.get("bounce", {}).get("reason"),
        )
    else:
        print(f"unhandled resend event: {event_type}")
    return {"received": True}


# ══════════════════════════════════════════════════════════════════════
# AGENT TASK — wire AgentMail here.
#
# Three handlers to add:
#
#   POST /api/orders/{order_id}/provision-inbox
#       → Create per-customer AgentMail inbox, stamp metadata.order_ref,
#         subscribe a webhook scoped to ONLY this inbox (inbox_ids=[id]),
#         re-read the webhook to confirm scope persisted as sent.
#
#   POST /api/agentmail-webhook
#       → Receive message.delivered events. Look up the inbox in our DB
#         (we stored inbox_id at provision-time), route the message to
#         the right order_id, and ack.
#
#   POST /api/orders/{order_id}/teardown-inbox
#       → DELETE the webhook + inbox when the order is archived. Dangling
#         webhooks fire forever and rack up retry storms.
#
# Verify the integration shape FIRST via the fetchsandbox MCP server:
#   - mcp__fetchsandbox__list_workflows  (slug: "agentmail")
#   - mcp__fetchsandbox__run_workflow    (id: "inbox_create_and_subscribe_webhook")
#   - mcp__fetchsandbox__run_workflow    (id: "webhook_lifecycle_create_read_delete")
#
# These give you the exact request/response shapes AgentMail expects,
# without burning a real API key.
# ══════════════════════════════════════════════════════════════════════


# ── DB helpers (stubs — wire to real Postgres in dev) ──────────────────

def _insert_order(*, user_id: str, sku: str, quantity: int, note: str | None) -> str:
    response = httpx.post(
        f"{ORDERS_DB_URL}/orders",
        json={"user_id": user_id, "sku": sku, "quantity": quantity, "note": note},
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()["id"]


def _fetch_order(*, order_id: str, user_id: str) -> dict | None:
    response = httpx.get(
        f"{ORDERS_DB_URL}/orders/{order_id}",
        params={"user_id": user_id},
        timeout=10.0,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def _mark_email_delivered(*, message_id: str | None) -> None:
    if not message_id:
        return
    httpx.post(
        f"{ORDERS_DB_URL}/emails/{message_id}/delivered", timeout=10.0,
    ).raise_for_status()


def _mark_email_bounced(*, message_id: str | None, reason: str | None) -> None:
    if not message_id:
        return
    httpx.post(
        f"{ORDERS_DB_URL}/emails/{message_id}/bounced",
        json={"reason": reason},
        timeout=10.0,
    ).raise_for_status()
