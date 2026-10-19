"""Temporary anonymous RAG sessions and shared hourly budget."""

from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision = "0002_demo"
down_revision = "0001_sprint1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "demo_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("chunks", sa.JSON(), nullable=False),
        sa.Column("vectors", sa.JSON(), nullable=False),
        sa.Column("questions_used", sa.Integer(), nullable=False),
        sa.Column("busy", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_demo_sessions_expires_at", "demo_sessions", ["expires_at"])
    budget = op.create_table(
        "demo_budget",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uploads", sa.Integer(), nullable=False),
        sa.Column("questions", sa.Integer(), nullable=False),
    )
    op.bulk_insert(
        budget,
        [
            {
                "id": 1,
                "window_start": datetime(2000, 1, 1, tzinfo=UTC),
                "uploads": 0,
                "questions": 0,
            }
        ],
    )


def downgrade():
    op.drop_table("demo_budget")
    op.drop_index("ix_demo_sessions_expires_at", table_name="demo_sessions")
    op.drop_table("demo_sessions")
