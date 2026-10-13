import os, types, sys
os.environ.update({"DATABASE_URL":"sqlite:///./test_security.db","ADASTRA_ENGINE_SWITCH":"ON","STRIPE_SECRET_KEY":"sk_test_x","STRIPE_WEBHOOK_SECRET":"whsec_test"})
stripe=types.ModuleType("stripe")
class SigErr(Exception): pass
stripe.error=types.SimpleNamespace(SignatureVerificationError=SigErr)
sys.modules["stripe"]=stripe
from app.db.session import Base, engine, SessionLocal
from app.models.models import Customer, Order, OrderStatus, AuditEvent
from app.services.order_service import verify_payment_event
Base.metadata.drop_all(engine); Base.metadata.create_all(engine)

def make_order(db):
    c=Customer(name="Test",email="security@example.com",company="TestCo"); db.add(c); db.flush()
    o=Order(customer_id=c.id,project_name="P",industry="I",automation_challenge="C",technology_stack=["FastAPI"],amount_cents=100000,currency="eur",status=OrderStatus.PAYMENT_PENDING,stripe_session_id="cs_security")
    db.add(o); db.commit(); return o

def test_wrong_amount_rejected():
    db=SessionLocal();
    try:
        make_order(db)
        try: verify_payment_event(db,event_id="evt_amount",session_id="cs_security",amount_cents=99999,currency="eur",payment_intent_id="pi",payload={"amount":99999})
        except ValueError as e: assert "amount" in str(e)
        else: assert False
    finally: db.close()

def test_wrong_currency_rejected():
    db=SessionLocal();
    try:
        db.query(AuditEvent).delete(); db.query(Order).delete(); db.query(Customer).delete(); db.commit(); make_order(db)
        try: verify_payment_event(db,event_id="evt_currency",session_id="cs_security",amount_cents=100000,currency="usd",payment_intent_id="pi",payload={"currency":"usd"})
        except ValueError as e: assert "currency" in str(e)
        else: assert False
    finally: db.close()

def test_same_event_different_payload_is_conflict():
    db=SessionLocal();
    try:
        db.query(AuditEvent).delete(); db.query(Order).delete(); db.query(Customer).delete(); db.commit(); make_order(db)
        verify_payment_event(db,event_id="evt_conflict",session_id="cs_security",amount_cents=100000,currency="eur",payment_intent_id="pi",payload={"v":1})
        try: verify_payment_event(db,event_id="evt_conflict",session_id="cs_security",amount_cents=100000,currency="eur",payment_intent_id="pi",payload={"v":2})
        except RuntimeError as e: assert "Idempotency conflict" in str(e)
        else: assert False
    finally: db.close()
