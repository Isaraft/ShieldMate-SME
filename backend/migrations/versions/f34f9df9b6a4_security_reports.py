"""security_reports

Revision ID: f34f9df9b6a4
Revises: e53b215e4b66
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f34f9df9b6a4"
down_revision: str | None = "e53b215e4b66"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "security_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("request_key", sa.String(length=36), nullable=False),
        sa.Column("locale", sa.String(length=2), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("byte_count", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        sa.Column("pdf", sa.LargeBinary(), nullable=True),
        sa.CheckConstraint("status IN ('generating','ready','failed')"),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "request_key"),
    )
    with op.batch_alter_table("security_reports", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_security_reports_created_by"), ["created_by"], unique=False
        )
        batch_op.create_index(
            "one_report_generation_per_org",
            ["organization_id"],
            unique=True,
            sqlite_where=sa.text("status = 'generating'"),
        )
        batch_op.create_index("report_org_created", ["organization_id", "created_at"], unique=False)

    op.create_table(
        "report_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(["report_id"], ["security_reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("report_events", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_report_events_report_id"), ["report_id"], unique=False)
        batch_op.create_index(
            "report_event_org_time", ["organization_id", "created_at"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("report_events", schema=None) as batch_op:
        batch_op.drop_index("report_event_org_time")
        batch_op.drop_index(batch_op.f("ix_report_events_report_id"))

    op.drop_table("report_events")
    with op.batch_alter_table("security_reports", schema=None) as batch_op:
        batch_op.drop_index("report_org_created")
        batch_op.drop_index(
            "one_report_generation_per_org", sqlite_where=sa.text("status = 'generating'")
        )
        batch_op.drop_index(batch_op.f("ix_security_reports_created_by"))

    op.drop_table("security_reports")
