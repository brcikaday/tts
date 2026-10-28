"""Persist documents and audit events; optionally associate conversion history.

Revision ID: b7c2d9e4a610
Revises: 00ab090b8bdc
"""
from alembic import op
import sqlalchemy as sa

revision = "b7c2d9e4a610"
down_revision = "00ab090b8bdc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("file_url", sa.String(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("source_type IN ('upload', 'url')", name="ck_documents_source_type"),
    )
    op.create_index("ix_documents_id", "documents", ["id"])
    op.create_index("ix_documents_user_id", "documents", ["user_id"])
    op.create_table(
        "system_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_system_logs_id", "system_logs", ["id"])
    op.create_index("ix_system_logs_user_id", "system_logs", ["user_id"])
    op.create_index("ix_system_logs_created_at", "system_logs", ["created_at"])
    op.add_column("conversion_history", sa.Column("document_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_conversion_history_document_id", "conversion_history", "documents",
                          ["document_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_conversion_history_document_id", "conversion_history", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_conversion_history_document_id", table_name="conversion_history")
    op.drop_constraint("fk_conversion_history_document_id", "conversion_history", type_="foreignkey")
    op.drop_column("conversion_history", "document_id")
    op.drop_index("ix_system_logs_created_at", table_name="system_logs")
    op.drop_index("ix_system_logs_user_id", table_name="system_logs")
    op.drop_index("ix_system_logs_id", table_name="system_logs")
    op.drop_table("system_logs")
    op.drop_index("ix_documents_user_id", table_name="documents")
    op.drop_index("ix_documents_id", table_name="documents")
    op.drop_table("documents")
