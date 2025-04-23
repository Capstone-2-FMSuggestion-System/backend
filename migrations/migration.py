from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users', sa.Column('status', sa.String(20), nullable=True))
    op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")
    op.alter_column('users', 'status', nullable=False, server_default='active')

def downgrade():
    op.drop_column('users', 'status') 