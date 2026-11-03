import os
import sqlite3

import stripe
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.session import get_db as get_sqlalchemy_db
from app.models.models import Customer, Order, OrderStatus
from app.services.order_service import engine_on, verify_payment_event

app = FastAPI(title="Adastra Autonomous OS")


class OrderRequest(BaseModel):
    project_name: str = Field(min_length=1, max_length=200)
    company_name: str = Field(min_length=1, max_length=200)
    industry: str = Field(min_length=1, max_length=200)
    automation_challenge: str = Field(min_length=1)
    technology_stack: list[str] = Field(min_length=1)
    customer_email: str = Field(min_length=5, max_length=320)


def read_value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


@app.get("/")
def root():
    return {"service": "Adastra Autonomous OS", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/orders", status_code=201)
def create_order(
    payload: OrderRequest,
    db: Session = Depends(get_sqlalchemy_db),
):
    if not engine_on():
        raise HTTPException(503, "Adastra Engine is OFF.")

    if not settings.stripe_secret_key:
        raise HTTPException(503, "Stripe secret key is not configured.")

    stripe.api_key = settings.stripe_secret_key

    try:
        customer = db.execute(
            select(Customer).where(Customer.email == payload.customer_email)
        ).scalar_one_or_none()

        if customer is None:
            customer = Customer(
                name=payload.company_name,
                email=payload.customer_email,
                company=payload.company_name,
            )
            db.add(customer)
            db.flush()

        order = Order(
            customer_id=customer.id,
            project_name=payload.project_name,
            industry=payload.industry,
            automation_challenge=payload.automation_challenge,
            technology_stack=payload.technology_stack,
            amount_cents=settings.target_amount_cents,
            currency=settings.target_currency,
            status=OrderStatus.ORDER_CREATED,
        )
        db.add(order)
        db.flush()

        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": settings.target_currency,
                    "unit_amount": settings.target_amount_cents,
                    "product_data": {
                        "name": payload.project_name,
                    },
                },
                "quantity": 1,
            }],
            client_reference_id=str(order.id),
            metadata={
                "order_id": str(order.id),
                "customer_email": payload.customer_email,
            },
            success_url=settings.success_url,
            cancel_url=settings.cancel_url,
        )

        session_id = read_value(session, "id")
        checkout_url = read_value(session, "url")

        if not session_id or not checkout_url:
            raise RuntimeError("Stripe returned an incomplete checkout session.")

        order.stripe_session_id = session_id
        order.status = OrderStatus.PAYMENT_PENDING
        db.commit()

        return {
            "order_id": order.id,
            "status": order.status.value,
            "checkout_url": checkout_url,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(502, "Order or Stripe checkout creation failed.")


@app.post("/api/v1/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(
        default=None,
        alias="stripe-signature",
    ),
    db: Session = Depends(get_sqlalchemy_db),
):
    if not engine_on():
        raise HTTPException(503, "Adastra Engine is OFF.")

    if not settings.stripe_webhook_secret:
        raise HTTPException(503, "Stripe webhook secret is not configured.")

    if not stripe_signature:
        raise HTTPException(400, "Missing Stripe signature.")

    raw_body = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            raw_body,
            stripe_signature,
            settings.stripe_webhook_secret,
        )
    except Exception:
        raise HTTPException(400, "Invalid Stripe webhook signature or payload.")

    event_type = read_value(event, "type")
    event_id = read_value(event, "id")

    if event_type != "checkout.session.completed":
        return {"status": "ignored", "reason": "Unsupported event type."}

    data = read_value(event, "data", {})
    checkout = read_value(data, "object", {})

    if read_value(checkout, "payment_status") != "paid":
        return {"status": "received", "reason": "Payment is not confirmed."}

    session_id = read_value(checkout, "id")
    amount = read_value(checkout, "amount_total")
    currency = read_value(checkout, "currency")
    payment_intent = read_value(checkout, "payment_intent")

    if isinstance(payment_intent, dict):
        payment_intent = payment_intent.get("id")
    metadata = read_value(checkout, "metadata", {})
    metadata_order_id = read_value(metadata, "order_id")

    if not event_id or not session_id or amount is None or not currency or not metadata_order_id:
        raise HTTPException(400, "Incomplete Stripe event data.")

    if hasattr(event, "to_dict_recursive"):
        event_payload = event.to_dict_recursive()
    elif isinstance(event, dict):
        event_payload = event
    else:
        event_payload = dict(event)

    try:
        result = verify_payment_event(
            db,
            event_id=event_id,
            session_id=session_id,
            metadata_order_id=str(metadata_order_id),
            amount_cents=int(amount),
            currency=str(currency),
            payment_intent_id=payment_intent,
            payload=event_payload,
        )
        return {"status": "processed", "result": result}

    except LookupError:
        db.rollback()
        raise HTTPException(404, "Matching order was not found.")
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc))
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(409, str(exc))
    except Exception:
        db.rollback()
        raise HTTPException(500, "Webhook processing failed.")


# Legacy SQLite protection endpoint retained for compatibility.
def get_db():
    db_path = os.getenv("DATABASE_PATH", "adastra_os.db")
    return sqlite3.connect(db_path)


def check_user_payment_status(email: str):
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT status FROM transactions "
            "WHERE customer_email=? AND status='paid'",
            (email,),
        )
        return cur.fetchone() is not None
    except Exception:
        return False
    finally:
        if conn:
            conn.close()


@app.get("/api/get-protected-info")
def protected(customer_email: str):
    if not check_user_payment_status(customer_email):
        raise HTTPException(403, "Payment required")
    return {
        "status": "success",
        "autonomous_system_status": "Operational",
    }
