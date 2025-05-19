# Import models và schemas trước
from .models import Product, Category, CartItems, Orders, OrderItems, Menus, MenuItems, FavoriteMenus, Reviews, Promotions
from .schemas import ProductCreate, ProductUpdate, ProductResponse, CartItemCreate, CartItem, OrderCreate, OrderResponse

# Export crud functions
from .crud import (
    get_products,
    get_product,
    create_product,
    update_product,
    create_order,
    update_order_status,
    get_order,
    create_cart_item,
    get_cart_item,
    get_cart_items_by_user,
    update_cart_item,
    delete_cart_item,
    create_favorite_menu,
    get_favorite_menu,
    get_favorite_menus_by_user,
    delete_favorite_menu
)

# Import router sau các import khác để tránh circular import
from .routes import router
