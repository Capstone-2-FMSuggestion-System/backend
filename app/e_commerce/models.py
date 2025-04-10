# Đây là file models.py cho module e_commerce

from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, TIMESTAMP, Boolean, text
from sqlalchemy.orm import relationship
from ..core.database import Base

# Import User model từ module user để sử dụng cho ForeignKey
from ..user.models import User

class Category(Base):
    __tablename__ = "categories"
    category_id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.category_id"))
    name = Column(String(50), nullable=False)
    description = Column(String(500))
    level = Column(Integer, nullable=False)

class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(1000))
    price = Column(DECIMAL(10, 2), nullable=False)
    image_url = Column(String(255))
    unit = Column(String(20))
    stock_quantity = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

class CartItems(Base):
    __tablename__ = "cart_items"
    cart_item_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    added_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

class Orders(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(20), default="pending")
    payment_method = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

class OrderItems(Base):
    __tablename__ = "order_items"
    order_item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)

class Menus(Base):
    __tablename__ = "menus"
    menu_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

class MenuItems(Base):
    __tablename__ = "menu_items"
    menu_item_id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.menu_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)

class FavoriteMenus(Base):
    __tablename__ = "favorite_menus"
    favorite_menu_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("menus.menu_id"), nullable=False)

class Reviews(Base):
    __tablename__ = "reviews"
    review_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    rating = Column(Integer)
    comment = Column(String(1000))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

class Promotions(Base):
    __tablename__ = "promotions"
    promotion_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    discount = Column(DECIMAL(5, 2), nullable=False)
    start_date = Column(TIMESTAMP)
    end_date = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
