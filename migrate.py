"""
Script chạy migration với Alembic.
Script này vẫn được giữ lại cho tương thích ngược, 
nhưng khuyến khích sử dụng alembic_migration.py để có nhiều tùy chọn hơn.
"""

import os
import sys
import logging
import subprocess

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate():
    """Chạy migration với Alembic"""
    try:
        # Đảm bảo tất cả model được import để Alembic có thể phát hiện thay đổi
        from app.core.database import Base
        from app.user.models import User
        from app.e_commerce.models import Category, Product, CartItems, Orders, OrderItems, Menus, MenuItems, FavoriteMenus, Reviews, Promotions, CategoryPromotion, ProductImages
        from app.inventory.models import Inventory, InventoryTransactions
        from app.payment.models import Payments
        
        # Tạo migration mới
        logger.info("Tạo migration mới...")
        subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", "update_schema"], 
            check=True
        )
        
        # Áp dụng migration
        logger.info("Áp dụng migration...")
        subprocess.run(
            ["alembic", "upgrade", "head"], 
            check=True
        )
        
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()