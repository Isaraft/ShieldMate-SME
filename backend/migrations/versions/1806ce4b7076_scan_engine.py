"""scan_engine

Revision ID: 1806ce4b7076
Revises: 90bff5eabc24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1806ce4b7076"
down_revision: str | None = "90bff5eabc24"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scan_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("requested_by", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("hostname", sa.String(length=253), nullable=False),
        sa.Column("proof_generation", sa.Integer(), nullable=False),
        sa.Column("proof_verified_at", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.Integer(), nullable=True),
        sa.Column("finished_at", sa.Integer(), nullable=True),
        sa.Column("lease_until", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=40), nullable=True),
        sa.Column("completed_checks", sa.Integer(), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "status IN ('queued','running','completed','partial','failed','interrupted')"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("scan_runs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_scan_runs_asset_id"), ["asset_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_scan_runs_created_at"), ["created_at"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_scan_runs_organization_id"), ["organization_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_scan_runs_requested_by"), ["requested_by"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_scan_runs_status"), ["status"], unique=False)
        batch_op.create_index(
            "one_active_scan_per_asset",
            ["asset_id"],
            unique=True,
            sqlite_where=sa.text("status IN ('queued', 'running')"),
        )

    op.create_table(
        "check_observations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("check_id", sa.String(length=40), nullable=False),
        sa.Column("observed_at", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("summary", sa.String(length=240), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("explanation", sa.String(length=600), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["scan_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id", "check_id"),
    )
    with op.batch_alter_table("check_observations", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_check_observations_scan_id"), ["scan_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("check_observations", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_check_observations_scan_id"))

    op.drop_table("check_observations")
    with op.batch_alter_table("scan_runs", schema=None) as batch_op:
        batch_op.drop_index(
            "one_active_scan_per_asset", sqlite_where=sa.text("status IN ('queued', 'running')")
        )
        batch_op.drop_index(batch_op.f("ix_scan_runs_status"))
        batch_op.drop_index(batch_op.f("ix_scan_runs_requested_by"))
        batch_op.drop_index(batch_op.f("ix_scan_runs_organization_id"))
        batch_op.drop_index(batch_op.f("ix_scan_runs_created_at"))
        batch_op.drop_index(batch_op.f("ix_scan_runs_asset_id"))

    op.drop_table("scan_runs")
