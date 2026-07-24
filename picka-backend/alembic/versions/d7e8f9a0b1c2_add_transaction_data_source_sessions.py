"""add transaction data source and demo sessions

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d7e8f9a0b1c2"
down_revision: str | None = "c6d7e8f9a0b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "demo_payment_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_demo_payment_sessions_user_id",
        "demo_payment_sessions",
        ["user_id"],
    )
    op.add_column(
        "transactions",
        sa.Column(
            "data_source",
            sa.String(length=20),
            nullable=False,
            server_default="SEED",
        ),
    )
    op.add_column(
        "transactions",
        sa.Column("demo_session_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_transactions_demo_session_id",
        "transactions",
        "demo_payment_sessions",
        ["demo_session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_transactions_data_source", "transactions", ["data_source"]
    )
    op.create_index(
        "ix_transactions_demo_session_id", "transactions", ["demo_session_id"]
    )

    # 기존 API 결제(PICKA-* 승인번호)는 사용자별 활성 시연 세션으로 분류합니다.
    op.execute(sa.text("""
        INSERT INTO demo_payment_sessions (user_id, status, started_at)
        SELECT user_id, 'ACTIVE', MIN(approved_at)
        FROM transactions
        WHERE approval_number LIKE 'PICKA-%'
        GROUP BY user_id
    """))
    op.execute(sa.text("""
        UPDATE transactions AS transaction
        SET data_source = 'DEMO', demo_session_id = session.id
        FROM demo_payment_sessions AS session
        WHERE transaction.user_id = session.user_id
          AND transaction.approval_number LIKE 'PICKA-%'
          AND session.status = 'ACTIVE'
    """))
    op.alter_column("transactions", "data_source", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_transactions_demo_session_id", table_name="transactions")
    op.drop_index("ix_transactions_data_source", table_name="transactions")
    op.drop_constraint(
        "fk_transactions_demo_session_id", "transactions", type_="foreignkey"
    )
    op.drop_column("transactions", "demo_session_id")
    op.drop_column("transactions", "data_source")
    op.drop_index(
        "ix_demo_payment_sessions_user_id", table_name="demo_payment_sessions"
    )
    op.drop_table("demo_payment_sessions")
