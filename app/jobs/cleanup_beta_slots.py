"""Isolated beta-slot cleanup job.

This job is intentionally outside the request path. It only releases slots whose
lease has expired. Long-running workers must renew heartbeat/lease before expiry.
"""
from datetime import datetime, timezone
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.beta_slots import BetaSlot, BetaSlotStatus

def cleanup_expired_slots() -> int:
    now = datetime.now(timezone.utc)
    released = 0
    with SessionLocal() as db:
        rows = db.execute(
            select(BetaSlot).where(
                BetaSlot.status == BetaSlotStatus.RESERVED,
                BetaSlot.lease_until.is_not(None),
                BetaSlot.lease_until < now,
            ).with_for_update(skip_locked=True)
        ).scalars().all()
        for slot in rows:
            slot.status = BetaSlotStatus.AVAILABLE
            slot.order_id = None
            slot.released_at = now
            slot.lease_until = None
            released += 1
        db.commit()
    return released
