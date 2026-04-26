"""Add role column to users

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-04-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd2e3f4a5b6c7'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False, server_default='coach'))
    # Promote existing superusers to admin role
    op.execute("UPDATE users SET role = 'admin' WHERE is_superuser = TRUE")


def downgrade() -> None:
    op.drop_column('users', 'role')
