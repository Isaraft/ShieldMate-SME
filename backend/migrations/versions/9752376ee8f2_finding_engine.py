"""finding_engine

Revision ID: 9752376ee8f2
Revises: 1806ce4b7076
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9752376ee8f2"
down_revision: str | None = "1806ce4b7076"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "finding_evaluations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("evaluated_at", sa.Integer(), nullable=False),
        sa.Column("scan_created_at", sa.Integer(), nullable=False),
        sa.Column("applied", sa.Boolean(), nullable=False),
        sa.Column("assessment", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["domains.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(["scan_id"], ["scan_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id", "policy_version"),
    )
    with op.batch_alter_table("finding_evaluations", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_finding_evaluations_asset_id"), ["asset_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_finding_evaluations_organization_id"), ["organization_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_finding_evaluations_scan_id"), ["scan_id"], unique=False
        )

    op.create_table(
        "findings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("rule_id", sa.String(length=40), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("severity", sa.String(length=8), nullable=False),
        sa.Column("severity_rank", sa.Integer(), nullable=False),
        sa.Column("urgency", sa.Integer(), nullable=False),
        sa.Column("relevance", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("impact", sa.String(length=600), nullable=False),
        sa.Column("recommendation", sa.String(length=800), nullable=False),
        sa.Column("rationale", sa.String(length=600), nullable=False),
        sa.Column("limitation", sa.String(length=600), nullable=False),
        sa.Column("first_seen_at", sa.Integer(), nullable=False),
        sa.Column("last_seen_at", sa.Integer(), nullable=False),
        sa.Column("resolved_at", sa.Integer(), nullable=True),
        sa.Column("observed_at", sa.Integer(), nullable=False),
        sa.Column("source_scan_id", sa.String(length=36), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("last_evaluation_at", sa.Integer(), nullable=False),
        sa.Column("last_scan_created_at", sa.Integer(), nullable=False),
        sa.Column("last_scan_id", sa.String(length=36), nullable=False),
        sa.Column("recheck_status", sa.String(length=20), nullable=False),
        sa.Column("history_truncated", sa.Boolean(), nullable=False),
        sa.CheckConstraint("severity IN ('high','medium','low','info')"),
        sa.CheckConstraint("status IN ('open','resolved')"),
        sa.ForeignKeyConstraint(["asset_id"], ["domains.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "fingerprint"),
    )
    with op.batch_alter_table("findings", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_findings_asset_id"), ["asset_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_findings_category"), ["category"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_findings_organization_id"), ["organization_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_findings_severity"), ["severity"], unique=False)
        batch_op.create_index(batch_op.f("ix_findings_status"), ["status"], unique=False)

    op.create_table(
        "finding_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("finding_id", sa.String(length=36), nullable=False),
        sa.Column("source_scan_id", sa.String(length=36), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("occurred_at", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["finding_id"], ["findings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("finding_id", "source_scan_id", "policy_version"),
    )
    with op.batch_alter_table("finding_events", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_finding_events_finding_id"), ["finding_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_finding_events_source_scan_id"), ["source_scan_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("finding_events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_finding_events_source_scan_id"))
        batch_op.drop_index(batch_op.f("ix_finding_events_finding_id"))

    op.drop_table("finding_events")
    with op.batch_alter_table("findings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_findings_status"))
        batch_op.drop_index(batch_op.f("ix_findings_severity"))
        batch_op.drop_index(batch_op.f("ix_findings_organization_id"))
        batch_op.drop_index(batch_op.f("ix_findings_category"))
        batch_op.drop_index(batch_op.f("ix_findings_asset_id"))

    op.drop_table("findings")
    with op.batch_alter_table("finding_evaluations", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_finding_evaluations_scan_id"))
        batch_op.drop_index(batch_op.f("ix_finding_evaluations_organization_id"))
        batch_op.drop_index(batch_op.f("ix_finding_evaluations_asset_id"))

    op.drop_table("finding_evaluations")
