import enum
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class BetaSlotStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"

def utcnow(): return datetime.now(timezone.utc)

class BetaSlot(Base):
    __tablename__ = "beta_slots"
    id: Mapped[int] = mapped_column(primary_key=True)
    slot_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    status: Mapped[BetaSlotStatus] = mapped_column(Enum(BetaSlotStatus), nullable=False)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
