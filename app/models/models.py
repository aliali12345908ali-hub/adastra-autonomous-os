import enum
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

def utcnow(): return datetime.now(timezone.utc)

class OrderStatus(str, enum.Enum):
    ORDER_CREATED="ORDER_CREATED"; PAYMENT_PENDING="PAYMENT_PENDING"; PAYMENT_VERIFIED="PAYMENT_VERIFIED"
    ORDER_CONFIRMED="ORDER_CONFIRMED"; AUDIT_QUEUED="AUDIT_QUEUED"; AUDIT_PROCESSING="AUDIT_PROCESSING"
    REPORT_GENERATED="REPORT_GENERATED"; QUALITY_CHECK="QUALITY_CHECK"; DELIVERY_READY="DELIVERY_READY"
    DELIVERED="DELIVERED"; FAILED="FAILED"

class Customer(Base):
    __tablename__="customers"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(200),nullable=False)
    email: Mapped[str]=mapped_column(String(320),unique=True,index=True,nullable=False)
    company: Mapped[str|None]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,nullable=False)
    orders: Mapped[list["Order"]]=relationship(back_populates="customer")

class Order(Base):
    __tablename__="orders"
    id: Mapped[int]=mapped_column(primary_key=True)
    customer_id: Mapped[int]=mapped_column(ForeignKey("customers.id"),nullable=False)
    project_name: Mapped[str]=mapped_column(String(200),nullable=False)
    industry: Mapped[str]=mapped_column(String(200),nullable=False)
    automation_challenge: Mapped[str]=mapped_column(Text,nullable=False)
    technology_stack: Mapped[list|dict]=mapped_column(JSON,nullable=False)
    amount_cents: Mapped[int]=mapped_column(Integer,nullable=False)
    currency: Mapped[str]=mapped_column(String(3),nullable=False)
    status: Mapped[OrderStatus]=mapped_column(Enum(OrderStatus),nullable=False,default=OrderStatus.ORDER_CREATED)
    stripe_session_id: Mapped[str|None]=mapped_column(String(255),unique=True,index=True)
    stripe_payment_intent_id: Mapped[str|None]=mapped_column(String(255),index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,nullable=False)
    paid_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    customer: Mapped["Customer"]=relationship(back_populates="orders")
    events: Mapped[list["AuditEvent"]]=relationship(back_populates="order")

class AuditEvent(Base):
    __tablename__="audit_events"
    __table_args__=(UniqueConstraint("provider","event_id",name="uq_provider_event_id"),)
    id: Mapped[int]=mapped_column(primary_key=True)
    order_id: Mapped[int|None]=mapped_column(ForeignKey("orders.id"))
    provider: Mapped[str]=mapped_column(String(50),nullable=False)
    event_type: Mapped[str]=mapped_column(String(100),nullable=False)
    event_id: Mapped[str]=mapped_column(String(255),nullable=False)
    payload_hash: Mapped[str]=mapped_column(String(64),nullable=False)
    timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,nullable=False)
    result: Mapped[dict|None]=mapped_column(JSON)
    order: Mapped["Order|None"]=relationship(back_populates="events")
