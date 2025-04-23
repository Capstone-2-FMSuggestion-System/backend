"""Add new column to table

Revision ID: 592d5f23c39f
Revises: 46e89ac3295c
Create Date: 2025-04-11 04:55:09.353174

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '592d5f23c39f'
down_revision = '46e89ac3295c'
branch_labels = None
depends_on = None


def upgrade():
    # Thêm cột avatar_url vào bảng users
    try:
        op.add_column('users', sa.Column('avatar_url', sa.String(255), nullable=True))
        print("Đã thêm cột avatar_url vào bảng users")
    except Exception as e:
        print(f"Không thể thêm cột avatar_url: {e}")
    
    # Tạo bảng product_images
    try:
        op.create_table('product_images',
            sa.Column('image_id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('image_url', sa.String(255), nullable=False),
            sa.Column('is_primary', sa.Boolean(), server_default='0'),
            sa.Column('display_order', sa.Integer(), server_default='0'),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['product_id'], ['products.product_id']),
            sa.PrimaryKeyConstraint('image_id')
        )
        print("Đã tạo bảng product_images")
    except Exception as e:
        print(f"Không thể tạo bảng product_images: {e}")


def downgrade():
    # Xóa bảng product_images
    try:
        op.drop_table('product_images')
    except Exception as e:
        print(f"Không thể xóa bảng product_images: {e}")
    
    # Xóa cột avatar_url từ bảng users
    try:
        op.drop_column('users', 'avatar_url')
    except Exception as e:
        print(f"Không thể xóa cột avatar_url: {e}") 