"""Create durable Adastra order, customer and audit schema.

Revision ID: 2026_10_04_adastra_base
Revises: None
"""
from alembic import op
import sqlalchemy as sa

revision = "2026_10_04_adastra_base"
down_revision = None
branch_labels = None
depends_on = None

order_status = sa.Enum(
    "ORDER_CREATED", "PAYMENT_PENDING", "PAYMENT_VERIFIED", "ORDER_CONFIRMED",
    "AUDIT_QUEUED", "AUDIT_PROCESSING", "REPORT_GENERATED", "QUALITY_CHECK",
    "DELIVERY_READY", "DELIVERED", "FAILED", name="orderstatus"
)

def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        order_status.create(bind, checkfirst=True)
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("company", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_customers_email", "customers", ["email"], unique=False)
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("project_name", sa.String(200), nullable=False),
        sa.Column("industry", sa.String(200), nullable=False),
        sa.Column("automation_challenge", sa.Text(), nullable=False),
        sa.Column("technology_stack", sa.JSON(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", order_status, nullable=False),
        sa.Column("stripe_session_id", sa.String(255), unique=True),
        sa.Column("stripe_payment_intent_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_orders_stripe_session_id", "orders", ["stripe_session_id"], unique=False)
    op.create_index("ix_orders_stripe_payment_intent_id", "orders", ["stripe_payment_intent_id"], unique=False)
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id")),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result", sa.JSON()),
        sa.UniqueConstraint("provider", "event_id", name="uq_provider_event_id"),
    )

def downgrade():
    op.drop_table("audit_events")
    op.drop_index("ix_orders_stripe_payment_intent_id", table_name="orders")
    op.drop_index("ix_orders_stripe_session_id", table_name="orders")
    op.drop_table("orders")
    op.drop_index("ix_customers_email", table_name="customers")
    op.drop_table("customers")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        order_status.drop(bind, checkfirst=True)
