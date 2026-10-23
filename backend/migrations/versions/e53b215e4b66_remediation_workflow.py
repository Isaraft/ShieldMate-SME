"""remediation_workflow

Revision ID: e53b215e4b66
Revises: 9752376ee8f2
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e53b215e4b66"
down_revision: str | None = "9752376ee8f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("findings", schema=None) as batch_op:
        batch_op.create_index("finding_identity_org", ["id", "organization_id"], unique=True)
    op.create_table(
        "remediation_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("finding_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("owner_label", sa.String(length=80), nullable=False),
        sa.Column("note", sa.String(length=2000), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.Integer(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("history_truncated", sa.Boolean(), nullable=False),
        sa.CheckConstraint("status IN ('todo','in_progress','done')"),
        sa.CheckConstraint("length(owner_label) <= 80 AND length(note) <= 2000"),
        sa.CheckConstraint("version >= 1"),
        sa.ForeignKeyConstraint(
            ["finding_id", "organization_id"],
            ["findings.id", "findings.organization_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("finding_id"),
        sa.UniqueConstraint("id", "organization_id"),
    )
    with op.batch_alter_table("remediation_tasks", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_remediation_tasks_organization_id"), ["organization_id"], unique=False
        )
        batch_op.create_index(
            "task_org_status_updated", ["organization_id", "status", "updated_at"], unique=False
        )

    op.create_table(
        "task_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["task_id", "organization_id"],
            ["remediation_tasks.id", "remediation_tasks.organization_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "version"),
    )
    with op.batch_alter_table("task_events", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_task_events_task_id"), ["task_id"], unique=False)
        batch_op.create_index(
            "task_event_org_time", ["organization_id", "created_at"], unique=False
        )


def downgrade() -> None:

    with op.batch_alter_table("task_events", schema=None) as batch_op:
        batch_op.drop_index("task_event_org_time")
        batch_op.drop_index(batch_op.f("ix_task_events_task_id"))

    op.drop_table("task_events")
    with op.batch_alter_table("remediation_tasks", schema=None) as batch_op:
        batch_op.drop_index("task_org_status_updated")
        batch_op.drop_index(batch_op.f("ix_remediation_tasks_organization_id"))

    op.drop_table("remediation_tasks")
    with op.batch_alter_table("findings", schema=None) as batch_op:
        batch_op.drop_index("finding_identity_org")
