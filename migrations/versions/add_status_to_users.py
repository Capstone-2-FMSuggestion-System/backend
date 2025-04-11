"""Add status field to User model

Revision ID: 001
Revises: 
Create Date: 2025-04-10

"""

from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('status', sa.String(20), nullable=True))
    op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")
    op.alter_column('users', 'status', nullable=False, server_default=sa.text("'active'"))

def downgrade():
    op.drop_column('users', 'status') 