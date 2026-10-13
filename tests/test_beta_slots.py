import os, types, sys
os.environ.update({"DATABASE_URL":"sqlite:///./test_beta.db","ADASTRA_ENGINE_SWITCH":"ON","STRIPE_SECRET_KEY":"sk_test_x","STRIPE_WEBHOOK_SECRET":"whsec_test"})
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
from app.db.session import Base, engine, SessionLocal
from app.models.beta_slots import BetaSlot, BetaSlotStatus
from app.services.beta_manager import reserve_beta_slot, heartbeat_beta_slot, release_beta_slot
Base.metadata.create_all(engine)

def reset_slots(db):
    db.query(BetaSlot).delete(); db.commit()
    for i in range(1, 11): db.add(BetaSlot(slot_number=i,status=BetaSlotStatus.AVAILABLE,version=1))
    db.commit()

def test_reserve_first_available_slot():
    db=SessionLocal();
    try:
        reset_slots(db)
        slot=reserve_beta_slot(db, 123); db.commit()
        assert slot.slot_number == 1 and slot.status == BetaSlotStatus.RESERVED and slot.order_id == 123
    finally: db.close()

def test_reservation_exhaustion():
    db=SessionLocal()
    try:
        db.query(BetaSlot).delete(); db.commit()
        for i in range(1,11):
            slot=BetaSlot(slot_number=i,status=BetaSlotStatus.RESERVED,order_id=i,version=1); db.add(slot)
        db.commit()
        try: reserve_beta_slot(db, 999); assert False
        except LookupError: pass
    finally: db.close()


def test_reservation_establishes_lease_and_heartbeat():
    db=SessionLocal()
    try:
        reset_slots(db)
        slot=reserve_beta_slot(db, 321, lease_seconds=900)
        db.commit()
        assert slot.lease_until is not None
        assert slot.heartbeat_at is not None
        renewed=heartbeat_beta_slot(db, slot.id, 321, lease_seconds=900)
        db.commit()
        assert renewed.lease_until is not None
        assert renewed.heartbeat_at is not None
    finally: db.close()

def test_release_requires_owner_and_clears_lease_state():
    db=SessionLocal()
    try:
        reset_slots(db)
        slot=reserve_beta_slot(db, 456)
        db.commit()
        try:
            release_beta_slot(db, slot.id, 999)
            assert False
        except LookupError:
            db.rollback()
        released=release_beta_slot(db, slot.id, 456)
        db.commit()
        assert released.status == BetaSlotStatus.AVAILABLE
        assert released.order_id is None
        assert released.lease_until is None
        assert released.heartbeat_at is None
    finally: db.close()


def test_expired_lease_rejects_stale_heartbeat_and_release():
    from datetime import datetime, timedelta, timezone
    db = SessionLocal()
    try:
        reset_slots(db)
        slot = reserve_beta_slot(db, 789, lease_seconds=900)
        db.commit()
        slot_id = slot.id
        db.query(BetaSlot).filter(BetaSlot.id == slot_id).update({
            BetaSlot.lease_until: datetime.now(timezone.utc) - timedelta(seconds=5)
        })
        db.commit()
        try:
            heartbeat_beta_slot(db, slot_id, 789)
            assert False, "expired owner heartbeat must be rejected"
        except LookupError as exc:
            assert "expired" in str(exc).lower()
            db.rollback()
        try:
            release_beta_slot(db, slot_id, 789)
            assert False, "expired owner release must be rejected"
        except LookupError as exc:
            assert "expired" in str(exc).lower()
            db.rollback()
    finally:
        db.close()
