"""Create isolated Beta slot lease table and seed ten slots.

Revision ID: 2026_10_04_adastra_beta
Revises: 2026_10_04_adastra_base
"""
from alembic import op
import sqlalchemy as sa

revision = "2026_10_04_adastra_beta"
down_revision = "2026_10_04_adastra_base"
branch_labels = None
depends_on = None

slot_status = sa.Enum("AVAILABLE", "RESERVED", name="betaslotstatus")

def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        slot_status.create(bind, checkfirst=True)
    op.create_table(
        "beta_slots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slot_number", sa.Integer(), nullable=False, unique=True),
        sa.Column("status", slot_status, nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("idx_beta_slots_status", "beta_slots", ["status"], unique=False)
    now = sa.func.now()
    for slot in range(1, 11):
        op.execute(sa.text("INSERT INTO beta_slots (slot_number, status, created_at, version) VALUES (:slot, 'AVAILABLE', CURRENT_TIMESTAMP, 1)").bindparams(slot=slot))

def downgrade():
    op.drop_index("idx_beta_slots_status", table_name="beta_slots")
    op.drop_table("beta_slots")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        slot_status.drop(bind, checkfirst=True)
