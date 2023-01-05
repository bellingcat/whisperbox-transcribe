"""add_job_and_artifact_tables

Revision ID: c43a1ddae8b7
Revises: 
Create Date: 2023-01-05 12:00:58.824773

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c43a1ddae8b7"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "jobs",
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column(
            "status",
            sa.Enum("Create", "Error", "Success", name="jobstatus"),
            nullable=False,
        ),
        sa.Column(
            "type", sa.Enum("Transcript", name="jobtype"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_jobs_id"), "jobs", ["id"], unique=False)
    op.create_table(
        "artifacts",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("data", sa.JSON(none_as_null=True), nullable=True),
        sa.Column(
            "type",
            sa.Enum("RawTranscript", name="artifacttype"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_artifacts_id"), "artifacts", ["id"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_artifacts_id"), table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_index(op.f("ix_jobs_id"), table_name="jobs")
    op.drop_table("jobs")
    # ### end Alembic commands ###
