# Import từ các module tương ứng
from ..user.schemas import UserCreate
from ..e_commerce.schemas import ProductCreate, PromotionCreate
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Đây là file schemas.py cho module admin
# Trong tương lai, có thể chuyển định nghĩa các schema vào đây

# Schema cho thống kê tổng hợp dashboard
class DashboardStats(BaseModel):
    total_orders: int
    total_revenue: float
    total_customers: int
    total_products: int

# Schema cho đơn hàng gần đây
class RecentOrder(BaseModel):
    order_id: int
    user_id: int
    customer_name: str
    total_amount: float
    status: str
    payment_method: Optional[str]
    created_at: datetime

# Schema cho response danh sách đơn hàng gần đây
class RecentOrdersResponse(BaseModel):
    orders: List[RecentOrder]

# Schema cho thông tin doanh thu theo thời kỳ
class RevenuePeriod(BaseModel):
    period: str
    revenue: float
    orders_count: int

# Schema cho response tổng quan doanh thu
class RevenueOverviewResponse(BaseModel):
    time_range: str
    data: List[RevenuePeriod]
