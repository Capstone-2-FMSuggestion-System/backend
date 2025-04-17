# Import từ các module tương ứng
from ..user.schemas import UserCreate
from ..e_commerce.schemas import ProductCreate, PromotionCreate
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Đây là file schemas.py cho module admin
# Trong tương lai, có thể chuyển định nghĩa các schema vào đây

# Schema cho thống kê tổng hợp dashboard
class DashboardStats(BaseModel):
    total_users: int
    total_orders: int
    total_products: int
    total_revenue: float
    new_users_today: int
    new_orders_today: int
    new_products_today: int
    revenue_today: float

# Schema cho đơn hàng gần đây
class RecentOrder(BaseModel):
    order_id: int
    user_name: str
    total_amount: float
    status: str
    created_at: datetime

# Schema cho response danh sách đơn hàng gần đây
class RecentOrdersResponse(BaseModel):
    orders: List[RecentOrder]
    total: int

# Schema cho thông tin doanh thu theo thời kỳ
class RevenuePeriod(BaseModel):
    label: str
    value: float

# Schema cho response tổng quan doanh thu
class RevenueOverviewResponse(BaseModel):
    data: List[RevenuePeriod]
    total_revenue: float
    time_range: str

# Thêm schema cho Order Management API
class OrderShippingInfo(BaseModel):
    shipping_method: str
    shipping_address: str
    tracking_number: Optional[str] = None

class OrderItemDetail(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float

class OrderDetail(BaseModel):
    order_id: int
    user_id: int
    customer_name: str
    phone_number: str
    email: Optional[str] = None
    address: str
    total_amount: float
    shipping_method: str
    is_prepaid: bool
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: Optional[List[OrderItemDetail]] = None

class OrderResponse(BaseModel):
    orders: List[OrderDetail]
    total: int
    skip: int
    limit: int

class OrderFilterOptions(BaseModel):
    status_options: List[Dict[str, Any]]
    payment_options: List[Dict[str, Any]]
    shipping_options: List[Dict[str, Any]]

class OrderUpdateRequest(BaseModel):
    status: Optional[str] = None
    shipping_method: Optional[str] = None
    is_prepaid: Optional[bool] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
