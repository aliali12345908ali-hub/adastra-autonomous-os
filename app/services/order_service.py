from datetime import datetime, timezone
from hashlib import sha256
import json
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.settings import settings
from app.models.models import AuditEvent, Order, OrderStatus

ALLOWED_TRANSITIONS={
 OrderStatus.ORDER_CREATED:{OrderStatus.PAYMENT_PENDING,OrderStatus.FAILED},
 OrderStatus.PAYMENT_PENDING:{OrderStatus.PAYMENT_VERIFIED,OrderStatus.FAILED},
 OrderStatus.PAYMENT_VERIFIED:{OrderStatus.ORDER_CONFIRMED,OrderStatus.FAILED},
}

def engine_on(): return settings.engine_switch.upper()=="ON"

def payload_hash(payload: dict) -> str:
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return sha256(raw).hexdigest()

def verify_payment_event(db:Session,*,event_id:str,session_id:str,amount_cents:int,currency:str,payment_intent_id:str|None,payload:dict):
    if not engine_on(): raise RuntimeError("Adastra Engine is OFF (fail-closed).")
    currency=currency.lower()
    if amount_cents!=settings.target_amount_cents: raise ValueError("Payment amount does not match the required amount.")
    if currency!=settings.target_currency: raise ValueError("Payment currency does not match the required currency.")
    stmt=select(Order).where(Order.stripe_session_id==session_id)
    if not settings.database_url.startswith("sqlite"):
        stmt=stmt.with_for_update()
    order=db.execute(stmt).scalar_one_or_none()
    if order is None: raise LookupError("Order matching Stripe session was not found.")
    ph=payload_hash(payload)
    existing=db.execute(select(AuditEvent).where(AuditEvent.provider=="stripe",AuditEvent.event_id==event_id)).scalar_one_or_none()
    if existing:
        if existing.payload_hash!=ph: raise RuntimeError("Idempotency conflict: same provider/event_id with different payload hash.")
        db.rollback(); return "Duplicate event detected; no duplicate processing."
    if order.status in {OrderStatus.PAYMENT_VERIFIED,OrderStatus.ORDER_CONFIRMED}:
        db.rollback(); return "Already verified; no duplicate processing."
    if order.status==OrderStatus.ORDER_CREATED: order.status=OrderStatus.PAYMENT_PENDING
    if order.status!=OrderStatus.PAYMENT_PENDING: raise ValueError(f"Unexpected order state: {order.status.value}")
    order.status=OrderStatus.PAYMENT_VERIFIED
    order.paid_at=datetime.now(timezone.utc)
    order.stripe_payment_intent_id=payment_intent_id
    db.add(AuditEvent(order_id=order.id,provider="stripe",event_type="checkout.session.completed",event_id=event_id,payload_hash=ph,result={"amount_cents":amount_cents,"currency":currency}))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return "Duplicate event detected; no duplicate processing."
    return "Payment verified and order secured."
