from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.beta_slots import BetaSlot, BetaSlotStatus

BETA_SLOT_COUNT = 10
DEFAULT_LEASE_SECONDS = 900  # 15 minutes; workers must renew before expiry.


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _lease_expired(lease_until: datetime | None, now: datetime) -> bool:
    if lease_until is None:
        return True
    # SQLite may return naive datetimes in local tests; interpret those as UTC.
    if lease_until.tzinfo is None:
        lease_until = lease_until.replace(tzinfo=timezone.utc)
    return lease_until <= now


def reserve_beta_slot(db: Session, order_id: int, lease_seconds: int = DEFAULT_LEASE_SECONDS) -> BetaSlot:
    """Atomically reserve one available slot and establish an explicit lease."""
    if lease_seconds <= 0:
        raise ValueError("lease_seconds must be positive")
    stmt = (
        select(BetaSlot)
        .where(BetaSlot.status == BetaSlotStatus.AVAILABLE)
        .order_by(BetaSlot.slot_number)
        .limit(1)
    )
    if db.bind and db.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)
    slot = db.execute(stmt).scalar_one_or_none()
    if slot is None:
        raise LookupError("Beta slots are fully booked")
    now = _now()
    slot.status = BetaSlotStatus.RESERVED
    slot.order_id = order_id
    slot.lease_until = now + timedelta(seconds=lease_seconds)
    slot.heartbeat_at = now
    slot.released_at = None
    slot.version = (slot.version or 0) + 1
    db.flush()
    return slot


def heartbeat_beta_slot(db: Session, slot_id: int, order_id: int, lease_seconds: int = DEFAULT_LEASE_SECONDS) -> BetaSlot:
    """Renew an owned reservation; ownership/state must be explicit."""
    if lease_seconds <= 0:
        raise ValueError("lease_seconds must be positive")
    stmt = select(BetaSlot).where(
        BetaSlot.id == slot_id,
        BetaSlot.order_id == order_id,
        BetaSlot.status == BetaSlotStatus.RESERVED,
    )
    if db.bind and db.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update()
    slot = db.execute(stmt).scalar_one_or_none()
    if slot is None:
        raise LookupError("Owned reserved Beta slot was not found")
    now = _now()
    if _lease_expired(slot.lease_until, now):
        raise LookupError("Beta slot lease has expired; stale worker rejected")
    slot.heartbeat_at = now
    slot.lease_until = now + timedelta(seconds=lease_seconds)
    slot.version = (slot.version or 0) + 1
    db.flush()
    return slot


def release_beta_slot(db: Session, slot_id: int, order_id: int) -> BetaSlot:
    """Release only when the owner and active reservation are proven."""
    stmt = select(BetaSlot).where(
        BetaSlot.id == slot_id,
        BetaSlot.order_id == order_id,
        BetaSlot.status == BetaSlotStatus.RESERVED,
    )
    if db.bind and db.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update()
    slot = db.execute(stmt).scalar_one_or_none()
    if slot is None:
        raise LookupError("Owned reserved Beta slot was not found")
    now = _now()
    if _lease_expired(slot.lease_until, now):
        raise LookupError("Beta slot lease has expired; stale worker rejected")
    slot.status = BetaSlotStatus.AVAILABLE
    slot.order_id = None
    slot.lease_until = None
    slot.heartbeat_at = None
    slot.released_at = now
    slot.version = (slot.version or 0) + 1
    db.flush()
    return slot
