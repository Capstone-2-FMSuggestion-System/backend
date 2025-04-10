from app.core.database import engine, Base
from app.user.models import User
from app.e_commerce.models import Category, Product, CartItems, Orders, OrderItems, Menus, MenuItems, FavoriteMenus, Reviews, Promotions
from app.inventory.models import Inventory, InventoryTransactions
from app.payment.models import Payments

# Tạo tất cả các bảng
Base.metadata.create_all(bind=engine)
print("Migration completed successfully!")