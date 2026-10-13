import os, sys, types
os.environ.update({"DATABASE_URL":"sqlite:///./test_adastra.db","ADASTRA_ENGINE_SWITCH":"ON","STRIPE_SECRET_KEY":"sk_test_x","STRIPE_WEBHOOK_SECRET":"whsec_test"})
# Minimal stripe stub so the core tests do not require network or the Stripe package.
stripe=types.ModuleType("stripe")
class SigErr(Exception): pass
class Webhook:
    @staticmethod
    def construct_event(*args,**kwargs): return {"id":"evt_test","type":"checkout.session.completed","data":{"object":{"id":"cs_test","amount_total":100000,"currency":"eur","payment_status":"paid","payment_intent":"pi_test"}}}
stripe.Webhook=Webhook; stripe.error=types.SimpleNamespace(SignatureVerificationError=SigErr)
class Checkout:
    class Session:
        @staticmethod
        def create(**kwargs): return types.SimpleNamespace(id="cs_test",url="https://checkout.test")
stripe.checkout=Checkout(); sys.modules["stripe"]=stripe
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base,engine,SessionLocal
from app.models.models import Customer,Order,AuditEvent,OrderStatus
Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
client=TestClient(app)

def test_health(): assert client.get('/health').status_code==200

def test_order_persists_and_checkout_binds():
    r=client.post('/api/v1/orders',json={"project_name":"Demo","company_name":"Acme","industry":"Ecom","automation_challenge":"Audit","technology_stack":["FastAPI"],"customer_email":"a@example.com"})
    assert r.status_code==201
    db=SessionLocal(); order=db.query(Order).first(); assert order and order.stripe_session_id=="cs_test" and order.status==OrderStatus.PAYMENT_PENDING; db.close()

def test_webhook_is_idempotent():
    r=client.post('/api/v1/webhook',headers={"stripe-signature":"test"},content=b'{}'); assert r.status_code==200
    r2=client.post('/api/v1/webhook',headers={"stripe-signature":"test"},content=b'{}'); assert r2.status_code==200
    db=SessionLocal(); assert db.query(AuditEvent).count()==1; assert db.query(Order).first().status==OrderStatus.PAYMENT_VERIFIED; db.close()
