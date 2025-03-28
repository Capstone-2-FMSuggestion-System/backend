from app.database import engine, Base
from app.models import User, Category, Product, CartItems, Orders, OrderItems, Inventory, InventoryTransactions, Menus, MenuItems, FavoriteMenus, Reviews, Promotions, Payments

# Tạo tất cả các bảng
Base.metadata.create_all(bind=engine)
print("Migration completed successfully!")