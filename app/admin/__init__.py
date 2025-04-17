"""
Admin module cho các chức năng quản trị
"""

# Import các models, schemas và routes cho admin
from .models import User, Product, Category, Orders, Payments, Promotions
from .schemas import ProductCreate, UserCreate, PromotionCreate, DashboardStats, RecentOrdersResponse, RevenueOverviewResponse

# Import router từ routes
from .routes import router

# Export các thành phần quan trọng 
__all__ = [
    "router",
    "User", "Product", "Category", "Orders", "Payments", "Promotions",
    "ProductCreate", "UserCreate", "PromotionCreate", 
    "DashboardStats", "RecentOrdersResponse", "RevenueOverviewResponse"
]
