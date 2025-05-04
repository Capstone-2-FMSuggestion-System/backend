from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Path, Body, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from ..core.database import get_db
from ..core.auth import get_current_user
from ..core.invalidation_helpers import invalidate_dashboard_cache
from .models import User, Product, Category, Orders, Payments, Promotions
from ..e_commerce.models import OrderItems
from .schemas import ProductCreate, UserCreate, PromotionCreate, DashboardStats, RecentOrdersResponse, RevenueOverviewResponse, RecentOrder, RevenuePeriod, OrderUpdateRequest
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import calendar
import json
import logging
from ..core.cache import get_cache, set_cache, redis_client
from ..user.models import User
from ..user.schemas import UserCreate, UserUpdate, UserSearchFilter
from ..user.crud import get_user, create_user, update_user, delete_user, search_users
from ..core.security import hash_password
import re
from ..core.cloudinary_utils import upload_image, delete_image, upload_multiple_images, extract_public_id_from_url
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from ..e_commerce.models import ProductImages
from .. import admin
from ..auth import authentication

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Cấu hình logging
logger = logging.getLogger(__name__)

def check_admin(user: User):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access this endpoint"
        )

@router.get("/users", response_model=List[dict])
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    users = db.query(User).all()
    return [
        {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at
        }
        for user in users
    ]

@router.post("/users", response_model=dict)
async def create_admin_user(
    user: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Invalidate dashboard cache when a new user is created
    await invalidate_dashboard_cache()
    logger.info(f"Dashboard cache invalidated after creating user {new_user.user_id}")
    
    return {"message": "User created successfully", "user_id": new_user.user_id}

@router.get("/products", response_model=List[dict])
async def get_all_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    products = db.query(Product).all()
    return [
        {
            "product_id": product.product_id,
            "name": product.name,
            "category_id": product.category_id,
            "price": float(product.price),
            "stock_quantity": product.stock_quantity,
            "is_featured": product.is_featured
        }
        for product in products
    ]

@router.post("/products", response_model=dict)
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    category = db.query(Category).filter(Category.category_id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    # Invalidate dashboard cache when a new product is created
    await invalidate_dashboard_cache()
    logger.info(f"Dashboard cache invalidated after creating product {new_product.product_id}")
    
    return {"message": "Product created successfully", "product_id": new_product.product_id}

@router.get("/orders", response_model=List[dict])
async def get_all_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    orders = db.query(Orders).all()
    return [
        {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "payment_method": order.payment_method,
            "created_at": order.created_at
        }
        for order in orders
    ]

@router.get("/payments", response_model=List[dict])
async def get_all_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    payments = db.query(Payments).all()
    return [
        {
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "amount": float(payment.amount),
            "method": payment.method,
            "status": payment.status,
            "created_at": payment.created_at
        }
        for payment in payments
    ]

@router.post("/promotions", response_model=dict)
async def create_promotion(
    promotion: PromotionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    new_promotion = Promotions(**promotion.dict())
    db.add(new_promotion)
    db.commit()
    db.refresh(new_promotion)
    
    # Invalidate dashboard cache when a new promotion is created
    await invalidate_dashboard_cache()
    logger.info(f"Dashboard cache invalidated after creating promotion {new_promotion.promotion_id}")
    
    return {"message": "Promotion created successfully", "promotion_id": new_promotion.promotion_id}

# API dashboard cũ (giữ lại để tương thích ngược)
@router.get("/dashboard", response_model=dict)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    total_users = db.query(User).count()
    total_orders = db.query(Orders).count()
    total_products = db.query(Product).count()
    total_revenue = db.query(Orders).filter(Orders.status == "completed").with_entities(
        func.sum(Orders.total_amount)
    ).scalar() or 0
    
    recent_orders = db.query(Orders).order_by(Orders.created_at.desc()).limit(5).all()
    
    return {
        "stats": {
            "total_users": total_users,
            "total_orders": total_orders,
            "total_products": total_products,
            "total_revenue": float(total_revenue)
        },
        "recent_orders": [
            {
                "order_id": order.order_id,
                "user_id": order.user_id,
                "total_amount": float(order.total_amount),
                "status": order.status,
                "created_at": order.created_at
            }
            for order in recent_orders
        ],
        "refreshed_at": datetime.now().isoformat()  # Thêm timestamp
    }

# API mới cho dashboard stats
@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy các thống kê tổng hợp của hệ thống (Total Order, Total Revenue, Total Customer, Total Product).
    Chỉ admin mới có quyền truy cập API này.
    
    Returns:
        DashboardStats: Các số liệu thống kê tổng hợp
    """
    logger.info(f"User {current_user.username} requested dashboard stats")
    check_admin(current_user)
    
    # Tạo cache key
    cache_key = "dashboard:stats"
    
    # Kiểm tra nếu đã có trong cache
    cached_data = await get_cache(cache_key)
    if cached_data:
        logger.info("Returning dashboard stats from cache")
        cached_dict = json.loads(cached_data)
        
        # Xác nhận cache có đầy đủ trường cần thiết theo model DashboardStats
        if not all(field in cached_dict for field in ["total_users", "new_users_today", "new_orders_today", "new_products_today", "revenue_today"]):
            logger.info("Cache không phù hợp với model DashboardStats, cần tạo lại cache")
            # Xóa cache hiện tại để tạo lại
            await redis_client.delete(cache_key)
            cached_data = None
        else:
            return cached_dict
    
    # Nếu không có cache hoặc cache không hợp lệ, tính toán lại
    
    # Tính ngày bắt đầu của ngày hôm nay
    today_start = datetime.combine(datetime.now().date(), datetime.min.time())
    
    # Đếm tổng số đơn hàng
    total_orders = db.query(Orders).count()
    
    # Đếm số đơn hàng mới trong ngày
    new_orders_today = db.query(Orders).filter(Orders.created_at >= today_start).count()
    
    # Tính tổng doanh thu từ các đơn hàng đã hoàn thành
    total_revenue = db.query(func.sum(Orders.total_amount)).filter(
        Orders.status == "completed"
    ).scalar() or 0
    
    # Tính doanh thu trong ngày
    revenue_today = db.query(func.sum(Orders.total_amount)).filter(
        Orders.created_at >= today_start
    ).scalar() or 0
    
    # Đếm tổng số người dùng
    total_users = db.query(User).count()
    
    # Đếm số người dùng mới trong ngày
    new_users_today = db.query(User).filter(User.created_at >= today_start).count()
    
    # Đếm tổng số sản phẩm
    total_products = db.query(Product).count()
    
    # Đếm số sản phẩm mới trong ngày
    new_products_today = db.query(Product).filter(Product.created_at >= today_start).count()
    
    # Tạo kết quả
    result = {
        "total_users": total_users,
        "total_orders": total_orders,
        "total_products": total_products,
        "total_revenue": float(total_revenue),
        "new_users_today": new_users_today,
        "new_orders_today": new_orders_today,
        "new_products_today": new_products_today,
        "revenue_today": float(revenue_today)
    }
    
    # Lưu vào cache với thời gian hết hạn là 5 phút
    await set_cache(cache_key, json.dumps(result, default=str), 300)
    logger.info("Dashboard stats cached for 5 minutes")
    
    return result

# API để lấy đơn hàng gần đây
@router.get("/dashboard/recent-orders", response_model=RecentOrdersResponse)
async def get_recent_orders(
    limit: int = Query(10, description="Số lượng đơn hàng gần đây muốn lấy"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách đơn hàng gần đây nhất.
    Chỉ admin mới có quyền truy cập API này.
    
    Args:
        limit (int, optional): Số lượng đơn hàng muốn lấy. Mặc định: 10.
        
    Returns:
        RecentOrdersResponse: Danh sách đơn hàng gần đây
    """
    logger.info(f"User {current_user.username} requested recent orders with limit {limit}")
    check_admin(current_user)
    
    # Tạo cache key có bao gồm limit
    cache_key = f"dashboard:recent_orders:{limit}"
    
    # Kiểm tra nếu đã có trong cache
    cached_data = await get_cache(cache_key)
    if cached_data:
        logger.info(f"Returning recent orders (limit={limit}) from cache")
        cached_dict = json.loads(cached_data)
        
        # Kiểm tra cấu trúc response có đúng không
        if "orders" not in cached_dict or "total" not in cached_dict:
            logger.info("Cache không phù hợp với model RecentOrdersResponse, cần tạo lại cache")
            await redis_client.delete(cache_key)
            cached_data = None
        else:
            return cached_dict
    
    # Lấy đơn hàng gần đây nhất
    recent_orders_query = db.query(
        Orders, User.full_name
    ).join(
        User, Orders.user_id == User.user_id
    ).order_by(
        Orders.created_at.desc()
    ).limit(limit).all()
    
    # Đếm tổng số đơn hàng
    total_orders = db.query(Orders).count()
    
    # Chuyển đổi kết quả sang định dạng mong muốn
    orders_list = []
    for order, user_name in recent_orders_query:
        orders_list.append({
            "order_id": order.order_id,
            "user_name": user_name,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "created_at": order.created_at
        })
    
    result = {
        "orders": orders_list,
        "total": total_orders
    }
    
    # Lưu vào cache với thời gian hết hạn là 2 phút
    await set_cache(cache_key, json.dumps(result, default=str), 120)
    logger.info(f"Recent orders (limit={limit}) cached for 2 minutes")
    
    return result

# API để lấy tổng quan doanh thu theo thời gian
@router.get("/dashboard/revenue-overview", response_model=RevenueOverviewResponse)
async def get_revenue_overview(
    time_range: str = Query("monthly", description="Khoảng thời gian (daily, weekly, monthly, yearly)"),
    start_date: Optional[str] = Query(None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Ngày kết thúc (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy thống kê doanh thu theo thời gian.
    Chỉ admin mới có quyền truy cập API này.
    
    Args:
        time_range (str, optional): Khoảng thời gian. Các giá trị: "daily", "weekly", "monthly", "yearly". Mặc định: "monthly".
        start_date (str, optional): Ngày bắt đầu khoảng thời gian (YYYY-MM-DD). Nếu không cung cấp, sẽ dựa vào time_range.
        end_date (str, optional): Ngày kết thúc khoảng thời gian (YYYY-MM-DD). Nếu không cung cấp, sẽ lấy đến ngày hiện tại.
        
    Returns:
        RevenueOverviewResponse: Thống kê doanh thu theo thời gian
    """
    logger.info(f"User {current_user.username} requested revenue overview with time_range={time_range}, start_date={start_date}, end_date={end_date}")
    check_admin(current_user)
    
    # Tạo cache key bao gồm tham số
    cache_key = f"dashboard:revenue:{time_range}:{start_date or 'none'}:{end_date or 'none'}"
    
    # Kiểm tra nếu đã có trong cache
    cached_data = await get_cache(cache_key)
    if cached_data:
        logger.info(f"Returning revenue overview from cache")
        cached_dict = json.loads(cached_data)
        
        # Kiểm tra cấu trúc response có đúng không
        if not all(field in cached_dict for field in ["data", "total_revenue", "time_range"]):
            logger.info("Cache không phù hợp với model RevenueOverviewResponse, cần tạo lại cache")
            await redis_client.delete(cache_key)
            cached_data = None
        else:
            return cached_dict
    
    # Chuyển đổi start_date và end_date sang đối tượng datetime
    today = datetime.now().date()
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_dt = today
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        # Mặc định lấy 30 ngày, 12 tuần, 12 tháng hoặc 5 năm dựa vào time_range
        if time_range == "daily":
            start_dt = end_dt - timedelta(days=30)
        elif time_range == "weekly":
            start_dt = end_dt - timedelta(weeks=12)
        elif time_range == "monthly":
            start_dt = datetime(end_dt.year - 1, end_dt.month, 1).date()
        else:  # yearly
            start_dt = datetime(end_dt.year - 5, 1, 1).date()
    
    # Tạo query cơ bản để lấy doanh thu
    base_query = db.query(
        Orders.created_at,
        Orders.total_amount
    ).filter(
        Orders.status == "completed",
        Orders.created_at >= start_dt,
        Orders.created_at <= end_dt + timedelta(days=1)  # Bao gồm cả ngày end_date
    )
    
    # Khởi tạo danh sách kết quả và tính tổng doanh thu
    total_revenue = db.query(func.sum(Orders.total_amount)).filter(
        Orders.status == "completed",
        Orders.created_at >= start_dt,
        Orders.created_at <= end_dt + timedelta(days=1)
    ).scalar() or 0
    
    # Định dạng dữ liệu theo time_range
    revenue_data = []
    
    if time_range == "daily":
        # Nhóm theo ngày
        for i in range((end_dt - start_dt).days + 1):
            current_date = start_dt + timedelta(days=i)
            next_date = current_date + timedelta(days=1)
            
            daily_revenue = db.query(func.sum(Orders.total_amount)).filter(
                Orders.status == "completed",
                Orders.created_at >= current_date,
                Orders.created_at < next_date
            ).scalar() or 0
            
            revenue_data.append({
                "label": current_date.strftime("%d/%m"),
                "value": float(daily_revenue)
            })
    
    elif time_range == "weekly":
        # Nhóm theo tuần
        for i in range(12):  # 12 tuần
            week_start = end_dt - timedelta(weeks=11-i)
            week_end = week_start + timedelta(days=6)
            
            if week_start < start_dt:
                continue
                
            weekly_revenue = db.query(func.sum(Orders.total_amount)).filter(
                Orders.status == "completed",
                Orders.created_at >= week_start,
                Orders.created_at <= week_end
            ).scalar() or 0
            
            revenue_data.append({
                "label": f"W{i+1}",
                "value": float(weekly_revenue)
            })
    
    elif time_range == "monthly":
        # Nhóm theo tháng
        current_date = start_dt.replace(day=1)
        while current_date <= end_dt:
            next_month = current_date.month + 1 if current_date.month < 12 else 1
            next_year = current_date.year if current_date.month < 12 else current_date.year + 1
            next_date = datetime(next_year, next_month, 1).date()
            
            monthly_revenue = db.query(func.sum(Orders.total_amount)).filter(
                Orders.status == "completed",
                Orders.created_at >= current_date,
                Orders.created_at < next_date
            ).scalar() or 0
            
            revenue_data.append({
                "label": current_date.strftime("%m/%Y"),
                "value": float(monthly_revenue)
            })
            
            current_date = next_date
    
    else:  # yearly
        # Nhóm theo năm
        for year in range(start_dt.year, end_dt.year + 1):
            year_start = datetime(year, 1, 1).date()
            year_end = datetime(year, 12, 31).date()
            
            yearly_revenue = db.query(func.sum(Orders.total_amount)).filter(
                Orders.status == "completed",
                Orders.created_at >= year_start,
                Orders.created_at <= year_end
            ).scalar() or 0
            
            revenue_data.append({
                "label": str(year),
                "value": float(yearly_revenue)
            })
    
    # Tạo kết quả theo định dạng của model
    result = {
        "data": revenue_data,
        "total_revenue": float(total_revenue),
        "time_range": time_range
    }
    
    # Lưu vào cache với thời gian hết hạn là 5 phút
    await set_cache(cache_key, json.dumps(result, default=str), 300)
    logger.info(f"Revenue overview cached for 5 minutes")
    
    return result

# API quản lý người dùng
@router.get("/manage/users", response_model=Dict[str, Any])
async def get_all_users_admin(
    skip: int = Query(0, description="Số bản ghi bỏ qua"),
    limit: int = Query(10, description="Số bản ghi tối đa trả về"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách tất cả người dùng trong hệ thống với phân trang.
    Chỉ admin mới có quyền truy cập API này.
    
    Args:
        skip (int): Số bản ghi bỏ qua
        limit (int): Số bản ghi tối đa trả về
        current_user (User): Người dùng hiện tại
        db (Session): Phiên làm việc với database
    
    Returns:
        Dict[str, Any]: Danh sách người dùng và thông tin phân trang
    """
    check_admin(current_user)
    
    # Tạo cache key
    cache_key = f"admin:users:{skip}:{limit}"
    
    # Kiểm tra cache
    cached_data = await get_cache(cache_key)
    if (cached_data):
        return json.loads(cached_data)
    
    # Lấy người dùng từ database
    users_query = db.query(User)
    total = users_query.count()
    users = users_query.offset(skip).limit(limit).all()
    
    result = {
        "items": [
            {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "role": user.role,
                "status": user.status,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }
    
    # Lưu vào cache với thời gian hết hạn là 5 phút
    await set_cache(cache_key, json.dumps(result, default=str), 300)
    
    return result

@router.get("/manage/users/{user_id}", response_model=Dict[str, Any])
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin chi tiết của một người dùng theo ID.
    Chỉ admin mới có quyền truy cập API này.
    
    Args:
        user_id (int): ID của người dùng cần lấy thông tin
        current_user (User): Người dùng hiện tại
        db (Session): Phiên làm việc với database
    
    Returns:
        Dict[str, Any]: Thông tin chi tiết của người dùng
    """
    check_admin(current_user)
    
    # Tạo cache key
    cache_key = f"admin:user:{user_id}"
    
    # Kiểm tra cache
    cached_data = await get_cache(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Lấy người dùng từ database
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    
    result = {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "role": user.role,
        "status": user.status,
        "location": user.location,
        "preferences": user.preferences,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    
    # Lưu vào cache với thời gian hết hạn là 5 phút
    await set_cache(cache_key, json.dumps(result, default=str), 300)
    
    return result

@router.post("/manage/users/search", response_model=Dict[str, Any])
async def search_users_admin(
    search_params: UserSearchFilter,
    skip: int = Query(0, description="Số bản ghi bỏ qua"),
    limit: int = Query(10, description="Số bản ghi tối đa trả về"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tìm kiếm người dùng theo tên, vai trò và trạng thái.
    Chỉ admin mới có quyền truy cập API này.
    
    Args:
        search_params (UserSearchFilter): Các tham số tìm kiếm
        skip (int): Số bản ghi bỏ qua
        limit (int): Số bản ghi tối đa trả về
        current_user (User): Người dùng hiện tại
        db (Session): Phiên làm việc với database
    
    Returns:
        Dict[str, Any]: Danh sách người dùng và thông tin phân trang
    """
    check_admin(current_user)
    
    # Tạo cache key dựa trên các tham số tìm kiếm
    cache_key = f"admin:users:search:{search_params.name or 'none'}:{search_params.role or 'none'}:{search_params.status or 'none'}:{skip}:{limit}"
    
    # Kiểm tra cache
    cached_data = await get_cache(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Tìm kiếm người dùng
    users, total = search_users(db, search_params, skip, limit)
    
    result = {
        "items": [
            {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "role": user.role,
                "status": user.status,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }
    
    # Lưu vào cache với thời gian hết hạn là 5 phút
    await set_cache(cache_key, json.dumps(result, default=str), 300)
    
    return result

@router.post("/manage/users", response_model=Dict[str, Any])
async def add_user_admin(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Thêm người dùng mới vào hệ thống.
    Chỉ admin mới có quyền truy cập API này.
    
    Args:
        user_data (UserCreate): Dữ liệu người dùng cần tạo
        current_user (User): Người dùng hiện tại
        db (Session): Phiên làm việc với database
    
    Returns:
        Dict[str, Any]: Thông báo và ID của người dùng mới
    """
    check_admin(current_user)
    
    # Kiểm tra trùng lặp username và email
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username đã tồn tại")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email đã tồn tại")
    
    # Tạo người dùng mới
    hashed_password = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        status=user_data.status
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Chuẩn bị dữ liệu chi tiết cho cache
    user_cache_data = {
        "user_id": new_user.user_id,
        "username": new_user.username,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "avatar_url": new_user.avatar_url,
        "role": new_user.role,
        "status": new_user.status,
        "location": new_user.location,
        "preferences": new_user.preferences,
        "created_at": new_user.created_at.isoformat() if new_user.created_at else None
    }
    
    # Cập nhật cache cho chi tiết người dùng mới
    await set_cache(f"admin:user:{new_user.user_id}", json.dumps(user_cache_data, default=str), 300)
    
    # Xóa cache danh sách người dùng để đảm bảo lần truy vấn tiếp theo sẽ lấy dữ liệu mới 
    # Sử dụng pattern để xóa tất cả các key liên quan
    pattern = "admin:users:*"
    cursor = 0
    
    # Tìm và xóa tất cả các key theo pattern
    while True:
        cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            await redis_client.delete(*keys)
        if cursor == 0:
            break
    
    # Ghi log
    logger.info(f"New user {new_user.user_id} created by admin {current_user.user_id}, cache updated")
    
    return {
        "message": "Người dùng đã được tạo thành công",
        "user_id": new_user.user_id
    }

@router.put("/manage/users/{user_id}", response_model=Dict[str, Any])
async def update_user_admin(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cập nhật thông tin người dùng.
    Chỉ admin mới có quyền truy cập API này.
    
    Args:
        user_id (int): ID của người dùng cần cập nhật
        user_data (UserUpdate): Dữ liệu cập nhật
        current_user (User): Người dùng hiện tại
        db (Session): Phiên làm việc với database
    
    Returns:
        Dict[str, Any]: Thông báo và thông tin người dùng đã cập nhật
    """
    check_admin(current_user)
    
    # Lấy thông tin người dùng cần cập nhật
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    
    # Kiểm tra trùng lặp username và email
    update_data = user_data.dict(exclude_unset=True)
    if "username" in update_data and update_data["username"] != user.username:
        if db.query(User).filter(User.username == update_data["username"]).first():
            raise HTTPException(status_code=400, detail="Username đã tồn tại")
    
    if "email" in update_data and update_data["email"] != user.email:
        if db.query(User).filter(User.email == update_data["email"]).first():
            raise HTTPException(status_code=400, detail="Email đã tồn tại")
    
    # Mã hóa mật khẩu nếu được cung cấp
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
    
    # Cập nhật thông tin trong database
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # Chuẩn bị dữ liệu phản hồi
    user_response = {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "role": user.role,
        "status": user.status
    }
    
    # Chuẩn bị dữ liệu chi tiết cho cache
    user_cache_data = {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "role": user.role,
        "status": user.status,
        "location": user.location,
        "preferences": user.preferences,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    
    # Cập nhật cache cho chi tiết người dùng
    await set_cache(f"admin:user:{user_id}", json.dumps(user_cache_data, default=str), 300)
    
    # Xóa cache danh sách người dùng để đảm bảo lần truy vấn tiếp theo sẽ lấy dữ liệu mới
    # Sử dụng pattern để xóa tất cả các key liên quan
    pattern = "admin:users:*"
    cursor = 0
    
    # Tìm và xóa tất cả các key theo pattern
    while True:
        cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            await redis_client.delete(*keys)
        if cursor == 0:
            break
    
    # Ghi log
    logger.info(f"User {user_id} updated by admin {current_user.user_id}, cache updated")
    
    return {
        "message": "Thông tin người dùng đã được cập nhật",
        "user": user_response
    }

@router.delete("/manage/users/{user_id}", response_model=Dict[str, Any])
async def delete_user_admin(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa người dùng khỏi hệ thống.
    Chỉ admin mới có quyền truy cập API này.
    
    Args:
        user_id (int): ID của người dùng cần xóa
        current_user (User): Người dùng hiện tại
        db (Session): Phiên làm việc với database
    
    Returns:
        Dict[str, Any]: Thông báo kết quả
    """
    check_admin(current_user)
    
    # Không cho phép admin xóa chính mình
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Không thể xóa tài khoản đang sử dụng")
    
    # Xóa người dùng
    result = delete_user(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    
    # Xóa cache người dùng cụ thể
    await redis_client.delete(f"admin:user:{user_id}")
    
    # Xóa cache danh sách người dùng để đảm bảo lần truy vấn tiếp theo sẽ lấy dữ liệu mới
    # Sử dụng pattern để xóa tất cả các key liên quan
    pattern = "admin:users:*"
    cursor = 0
    
    # Tìm và xóa tất cả các key theo pattern
    while True:
        cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            await redis_client.delete(*keys)
        if cursor == 0:
            break
    
    # Ghi log
    logger.info(f"User {user_id} deleted by admin {current_user.user_id}, cache updated")
    
    return {"message": "Người dùng đã được xóa thành công"}

@router.post("/dashboard/invalidate-cache", response_model=dict)
async def manual_invalidate_dashboard_cache(
    current_user: User = Depends(get_current_user),
):
    """
    API này cho phép admin xóa cache của dashboard thủ công.
    Hữu ích trong trường hợp cần tải lại dữ liệu mới ngay lập tức.
    """
    logger.info(f"User {current_user.username} requested manual cache invalidation")
    check_admin(current_user)
    
    success = await invalidate_dashboard_cache()
    
    if (success):
        return {"message": "Dashboard cache invalidated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate dashboard cache"
        )

# API quản lý danh mục (Categories)
@router.get("/manage/categories", response_model=Dict[str, Any])
async def get_all_categories_admin(
    skip: int = Query(0, description="Số bản ghi bỏ qua"),
    limit: int = Query(50, description="Số bản ghi tối đa trả về"),
    parent_only: bool = Query(False, description="Chỉ lấy các danh mục cấp cao nhất (parent_id = null)"),
    subcategories_only: bool = Query(False, description="Chỉ lấy các danh mục con (parent_id != null)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    # Kiểm tra cache
    cache_key = f"admin:categories:{skip}:{limit}:{parent_only}:{subcategories_only}"
    cached_result = await get_cache(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    # Lấy tất cả danh mục
    query = db.query(Category)
    
    # Lọc theo parent_id nếu có yêu cầu
    if parent_only:
        query = query.filter(Category.parent_id.is_(None))
    elif subcategories_only:
        query = query.filter(Category.parent_id.isnot(None))
    
    # Lấy tổng số danh mục theo bộ lọc
    total = query.count()
    
    # Phân trang
    categories = query.offset(skip).limit(limit).all()
    
    # Tạo map để lưu tất cả ID của danh mục và subcategories
    category_subcategories_map = {}
    
    # Hàm đệ quy để lấy tất cả ID của subcategories
    def get_all_subcategory_ids(cat_id, subcategory_ids=None):
        if subcategory_ids is None:
            subcategory_ids = []
        
        # Lấy các subcategory trực tiếp
        direct_subcategories = db.query(Category.category_id).filter(Category.parent_id == cat_id).all()
        
        # Thêm vào danh sách
        for subcategory in direct_subcategories:
            sub_id = subcategory[0]
            subcategory_ids.append(sub_id)
            # Đệ quy để lấy các subcategory của subcategory này
            get_all_subcategory_ids(sub_id, subcategory_ids)
        
        return subcategory_ids
    
    # Lấy số lượng sản phẩm cho mỗi danh mục
    result = []
    for category in categories:
        # Lấy tất cả ID của subcategories (bao gồm cả các subcategory lồng nhau)
        subcategory_ids = get_all_subcategory_ids(category.category_id)
        category_subcategories_map[category.category_id] = subcategory_ids
        
        # Đếm số lượng sản phẩm trực tiếp trong category này
        direct_product_count = db.query(Product).filter(Product.category_id == category.category_id).count()
        
        # Đếm số lượng sản phẩm trong tất cả subcategories
        subcategories_product_count = 0
        if subcategory_ids:
            subcategories_product_count = db.query(Product).filter(Product.category_id.in_(subcategory_ids)).count()
        
        # Tổng số lượng sản phẩm
        total_product_count = direct_product_count + subcategories_product_count
        
        # Đếm số danh mục con trực tiếp
        subcategories_count = db.query(Category).filter(Category.parent_id == category.category_id).count()
        
        # Lấy tên danh mục cha (nếu có)
        parent_name = None
        if category.parent_id:
            parent = db.query(Category).filter(Category.category_id == category.parent_id).first()
            if parent:
                parent_name = parent.name
        
        result.append({
            "category_id": category.category_id,
            "name": category.name,
            "description": category.description,
            "level": category.level,
            "parent_id": category.parent_id,
            "parent_name": parent_name,  # Thêm tên danh mục cha
            "product_count": total_product_count,
            "subcategories_count": subcategories_count,
            "created_at": category.created_at.isoformat() if hasattr(category, 'created_at') and category.created_at else None
        })
    
    response = {
        "total": total,
        "categories": result,
        "skip": skip,
        "limit": limit
    }
    
    # Lưu vào cache
    await set_cache(cache_key, json.dumps(response), expire=300)
    
    return response

@router.get("/manage/categories/{category_id}", response_model=Dict[str, Any])
async def get_category_by_id(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    # Kiểm tra cache
    cache_key = f"admin:category:{category_id}"
    cached_result = await get_cache(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    # Lấy thông tin danh mục
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Danh mục với ID {category_id} không tồn tại"
        )
    
    # Lấy danh mục cha (nếu có)
    parent = None
    if category.parent_id:
        parent = db.query(Category).filter(Category.category_id == category.parent_id).first()
    
    # Lấy các danh mục con
    subcategories = db.query(Category).filter(Category.parent_id == category_id).all()
    
    # Hàm đệ quy để lấy tất cả ID của subcategories
    def get_all_subcategory_ids(cat_id, subcategory_ids=None):
        if subcategory_ids is None:
            subcategory_ids = []
        
        # Lấy các subcategory trực tiếp
        direct_subcategories = db.query(Category.category_id).filter(Category.parent_id == cat_id).all()
        
        # Thêm vào danh sách
        for subcategory in direct_subcategories:
            sub_id = subcategory[0]
            subcategory_ids.append(sub_id)
            # Đệ quy để lấy các subcategory của subcategory này
            get_all_subcategory_ids(sub_id, subcategory_ids)
        
        return subcategory_ids
    
    # Lấy tất cả ID của subcategories
    subcategory_ids = get_all_subcategory_ids(category_id)
    
    # Đếm số lượng sản phẩm trực tiếp trong category này
    direct_product_count = db.query(Product).filter(Product.category_id == category_id).count()
    
    # Đếm số lượng sản phẩm trong tất cả subcategories
    subcategories_product_count = 0
    if subcategory_ids:
        subcategories_product_count = db.query(Product).filter(Product.category_id.in_(subcategory_ids)).count()
    
    # Tổng số lượng sản phẩm
    total_product_count = direct_product_count + subcategories_product_count
    
    # Thêm thông tin product_count cho mỗi subcategory
    subcategories_with_product_count = []
    for subcategory in subcategories:
        # Lấy tất cả ID của subcategories của subcategory này
        sub_subcategory_ids = get_all_subcategory_ids(subcategory.category_id)
        
        # Đếm số lượng sản phẩm trực tiếp trong subcategory này
        sub_direct_product_count = db.query(Product).filter(Product.category_id == subcategory.category_id).count()
        
        # Đếm số lượng sản phẩm trong tất cả subcategories của subcategory này
        sub_subcategories_product_count = 0
        if sub_subcategory_ids:
            sub_subcategories_product_count = db.query(Product).filter(Product.category_id.in_(sub_subcategory_ids)).count()
        
        # Tổng số lượng sản phẩm của subcategory
        sub_total_product_count = sub_direct_product_count + sub_subcategories_product_count
        
        subcategories_with_product_count.append({
            "category_id": subcategory.category_id,
            "name": subcategory.name,
            "description": subcategory.description,
            "level": subcategory.level,
            "product_count": sub_total_product_count
        })
    
    response = {
        "category": {
            "category_id": category.category_id,
            "name": category.name,
            "description": category.description,
            "level": category.level,
            "parent_id": category.parent_id,
            "created_at": category.created_at.isoformat() if hasattr(category, 'created_at') else None
        },
        "parent": {
            "category_id": parent.category_id,
            "name": parent.name
        } if parent else None,
        "subcategories": subcategories_with_product_count,
        "product_count": total_product_count
    }
    
    # Lưu vào cache
    await set_cache(cache_key, json.dumps(response), expire=300)
    
    return response

@router.post("/manage/categories", response_model=Dict[str, Any])
async def create_category_admin(
    category_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    # Kiểm tra tên danh mục đã tồn tại chưa
    if db.query(Category).filter(Category.name == category_data["name"]).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên danh mục đã tồn tại"
        )
    
    # Xác định level
    level = 1  # Mặc định là danh mục cấp 1
    if category_data.get("parent_id"):
        parent = db.query(Category).filter(Category.category_id == category_data["parent_id"]).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Danh mục cha với ID {category_data['parent_id']} không tồn tại"
            )
        level = parent.level + 1
    
    # Tạo danh mục mới
    new_category = Category(
        name=category_data["name"],
        description=category_data.get("description", ""),
        parent_id=category_data.get("parent_id"),
        level=level
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    # Invalidate dashboard cache khi tạo danh mục mới
    await invalidate_dashboard_cache()
    
    return {
        "message": "Đã tạo danh mục thành công",
        "category": {
            "category_id": new_category.category_id,
            "name": new_category.name,
            "description": new_category.description,
            "level": new_category.level,
            "parent_id": new_category.parent_id
        }
    }

@router.put("/manage/categories/{category_id}", response_model=Dict[str, Any])
async def update_category_admin(
    category_id: int,
    category_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    # Lấy thông tin danh mục
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Danh mục với ID {category_id} không tồn tại"
        )
    
    # Kiểm tra tên danh mục đã tồn tại chưa (nếu thay đổi tên)
    if category_data.get("name") and category_data["name"] != category.name:
        if db.query(Category).filter(Category.name == category_data["name"]).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên danh mục đã tồn tại"
            )
    
    # Cập nhật thông tin
    if category_data.get("name"):
        category.name = category_data["name"]
    
    if "description" in category_data:
        category.description = category_data["description"]
    
    # Cập nhật parent_id (nếu có)
    if "parent_id" in category_data and category_data["parent_id"] != category.parent_id:
        if category_data["parent_id"] is not None:
            # Kiểm tra danh mục cha tồn tại
            parent = db.query(Category).filter(Category.category_id == category_data["parent_id"]).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Danh mục cha với ID {category_data['parent_id']} không tồn tại"
                )
            
            # Kiểm tra không được chọn chính nó làm cha
            if category_data["parent_id"] == category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Không thể chọn chính danh mục này làm danh mục cha"
                )
                
            # Kiểm tra danh mục không được chọn con của nó làm cha
            if parent.parent_id == category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Không thể chọn danh mục con làm danh mục cha"
                )
            
            category.parent_id = category_data["parent_id"]
            category.level = parent.level + 1
            
            # Cập nhật level cho tất cả danh mục con
            update_subcategories_level(db, category_id, category.level)
        else:
            category.parent_id = None
            category.level = 1
            
            # Cập nhật level cho tất cả danh mục con
            update_subcategories_level(db, category_id, category.level)
    
    db.commit()
    db.refresh(category)
    
    # Invalidate dashboard cache
    await invalidate_dashboard_cache()
    
    return {
        "message": "Đã cập nhật danh mục thành công",
        "category": {
            "category_id": category.category_id,
            "name": category.name,
            "description": category.description,
            "level": category.level,
            "parent_id": category.parent_id
        }
    }

@router.delete("/manage/categories/{category_id}", response_model=Dict[str, Any])
async def delete_category_admin(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    # Lấy thông tin danh mục
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Danh mục với ID {category_id} không tồn tại"
        )
    
    # Kiểm tra xem có danh mục con không
    subcategories = db.query(Category).filter(Category.parent_id == category_id).all()
    if subcategories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa danh mục này vì có chứa danh mục con"
        )
    
    # Kiểm tra xem có sản phẩm nào thuộc danh mục này không
    products = db.query(Product).filter(Product.category_id == category_id).all()
    if products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa danh mục này vì có chứa sản phẩm"
        )
    
    # Xóa danh mục
    db.delete(category)
    db.commit()
    
    # Invalidate dashboard cache
    await invalidate_dashboard_cache()
    
    return {
        "message": "Đã xóa danh mục thành công"
    }

# Hàm cập nhật level cho tất cả danh mục con
def update_subcategories_level(db: Session, parent_id: int, parent_level: int):
    # Lấy tất cả danh mục con trực tiếp
    subcategories = db.query(Category).filter(Category.parent_id == parent_id).all()
    
    for subcategory in subcategories:
        # Cập nhật level
        subcategory.level = parent_level + 1
        db.commit()
        
        # Đệ quy cập nhật các danh mục con
        update_subcategories_level(db, subcategory.category_id, subcategory.level)

# Route quản lý sản phẩm cho admin
# Định nghĩa các schema và router cho quản lý sản phẩm

# Pydantic models cho quản lý sản phẩm
class ProductImageBase(BaseModel):
    image_url: str
    is_primary: bool = False
    display_order: int = 0

class ProductImageCreate(ProductImageBase):
    pass

class ProductImageResponse(ProductImageBase):
    image_id: int
    product_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class AdminProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    original_price: float = Field(..., gt=0)
    unit: Optional[str] = None
    stock_quantity: int = Field(0, ge=0)
    is_featured: bool = False
    category_id: int

class AdminProductCreate(AdminProductBase):
    images: Optional[List[ProductImageCreate]] = None

class AdminProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    is_featured: Optional[bool] = None
    category_id: Optional[int] = None

class AdminProductResponse(AdminProductBase):
    product_id: int
    created_at: datetime
    images: Optional[List[ProductImageResponse]] = []
    image_urls: Optional[List[str]] = []
    category_name: Optional[str] = "N/A"
    
    class Config:
        orm_mode = True

class PaginatedProductResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    skip: int
    limit: int

# API endpoint cho quản lý sản phẩm

@router.get("/manage/products", response_model=PaginatedProductResponse)
async def get_all_admin_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    stock_status: Optional[str] = None,  # Thêm tham số lọc theo trạng thái tồn kho (available/unavailable)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách tất cả sản phẩm (chỉ admin)"""
    check_admin(current_user)
    
    # Truy vấn sản phẩm và join với bảng Category để lấy tên danh mục
    query = db.query(
        Product, 
        Category.name.label("category_name")
    ).outerjoin(
        Category, 
        Product.category_id == Category.category_id
    )
    
    # Lọc theo danh mục
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # Tìm kiếm theo tên sản phẩm
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    # Lọc theo trạng thái tồn kho
    if stock_status:
        if stock_status.lower() == 'available':
            query = query.filter(Product.stock_quantity > 0)
        elif stock_status.lower() == 'unavailable':
            query = query.filter(Product.stock_quantity <= 0)
    
    # Đếm tổng số sản phẩm
    total = query.count()
    
    # Phân trang
    results = query.offset(skip).limit(limit).all()
    
    # Chuyển đổi dữ liệu để trả về định dạng mới
    product_list = []
    for product, category_name in results:
        # Lấy danh sách image_urls thay vì toàn bộ đối tượng image
        image_urls = [img.image_url for img in product.images] if product.images else []
        
        # Tạo đối tượng sản phẩm với định dạng mới
        product_dict = {
            "product_id": product.product_id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "original_price": float(product.original_price),
            "unit": product.unit,
            "stock_quantity": product.stock_quantity,
            "is_featured": product.is_featured,
            "category_id": product.category_id,
            "category_name": category_name or "N/A",  # Thêm tên danh mục
            "created_at": product.created_at,
            "image_urls": image_urls  # Thay thế trường images bằng image_urls
        }
        product_list.append(product_dict)
    
    return {
        "items": product_list,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.post("/manage/products", response_model=AdminProductResponse, status_code=201)
async def create_admin_product(
    files: List[UploadFile] = File(None),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    original_price: float = Form(...),
    unit: Optional[str] = Form(None),
    stock_quantity: int = Form(0),
    is_featured: bool = Form(False),
    category_id: int = Form(...),
    is_primary: List[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tạo sản phẩm mới với nhiều hình ảnh (chỉ admin)"""
    try:
        # Kiểm tra quyền admin
        check_admin(current_user)
        
        # Kiểm tra category_id có tồn tại không
        category = db.query(Category).filter(Category.category_id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Tạo sản phẩm mới
        db_product = Product(
            name=name,
            description=description,
            price=price,
            original_price=original_price,
            unit=unit,
            stock_quantity=stock_quantity,
            is_featured=is_featured,
            category_id=category_id
        )
        
        # Thêm sản phẩm vào database
        db.add(db_product)
        db.flush()  # Lấy ID sản phẩm sau khi thêm vào DB
        
        # Xử lý upload nhiều ảnh nếu có
        image_urls = []
        if files:
            try:
                # Upload nhiều ảnh lên Cloudinary
                results = await upload_multiple_images(files)
                
                # Thêm từng ảnh vào database
                for i, result in enumerate(results):
                    # Lấy URL từ kết quả trả về
                    image_url = result.get('url') if isinstance(result, dict) else result
                    
                    # Kiểm tra xem ảnh này có phải là ảnh chính không
                    is_primary_image = is_primary and i < len(is_primary) and is_primary[i].lower() == 'true'
                    
                    # Thêm ảnh vào database
                    db_image = ProductImages(
                        product_id=db_product.product_id,
                        image_url=image_url,
                        is_primary=is_primary_image,
                        display_order=i + 1
                    )
                    db.add(db_image)
                    image_urls.append(image_url)
            except Exception as e:
                db.rollback()
                logger.error(f"Error uploading images: {str(e)}")
                raise HTTPException(status_code=500, detail="Error uploading images")
        
        try:
            # Commit tất cả thay đổi
            db.commit()
            db.refresh(db_product)
            
            # Lấy danh sách ảnh sau khi commit
            images = db.query(ProductImages).filter(ProductImages.product_id == db_product.product_id).all()
            
            # Tạo response
            response = {
                "product_id": db_product.product_id,
                "name": db_product.name,
                "description": db_product.description,
                "price": float(db_product.price),
                "original_price": float(db_product.original_price),
                "unit": db_product.unit,
                "stock_quantity": db_product.stock_quantity,
                "is_featured": db_product.is_featured,
                "category_id": db_product.category_id,
                "category_name": category.name,
                "created_at": db_product.created_at,
                "images": images,
                "image_urls": [img.image_url for img in images]
            }
            
            # Invalidate dashboard cache
            await invalidate_dashboard_cache()
            logger.info(f"Dashboard cache invalidated after creating product {db_product.product_id}")
            
            return response
            
        except Exception as commit_error:
            db.rollback()
            logger.error(f"Error committing product to database: {str(commit_error)}")
            raise HTTPException(status_code=500, detail="Error saving product to database")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/manage/products/{product_id}", response_model=AdminProductResponse)
async def get_admin_product(
    product_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy thông tin chi tiết sản phẩm (chỉ admin)"""
    check_admin(current_user)
    
    # Query sản phẩm và join với Category để lấy tên danh mục
    result = db.query(
        Product, 
        Category.name.label("category_name")
    ).outerjoin(
        Category, 
        Product.category_id == Category.category_id
    ).filter(
        Product.product_id == product_id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product, category_name = result
    
    # Lấy danh sách image_urls
    image_urls = [img.image_url for img in product.images] if product.images else []
    
    # Tạo đối tượng sản phẩm với định dạng mới
    response = {
        "product_id": product.product_id,
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "original_price": float(product.original_price),
        "unit": product.unit,
        "stock_quantity": product.stock_quantity,
        "is_featured": product.is_featured,
        "category_id": product.category_id,
        "category_name": category_name or "N/A",  # Thêm tên danh mục
        "created_at": product.created_at,
        "image_urls": image_urls,  # Thêm mảng image_urls
        "images": product.images  # Giữ lại trường images để tương thích ngược
    }
    
    return response

@router.put("/manage/products/{product_id}", response_model=AdminProductResponse)
async def update_admin_product(
    product_id: int = Path(..., gt=0),
    files: List[UploadFile] = File(None),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    original_price: Optional[float] = Form(None),
    unit: Optional[str] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    is_featured: Optional[bool] = Form(None),
    category_id: Optional[int] = Form(None),
    is_primary: List[str] = Form(None),
    delete_images: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Lấy sản phẩm từ database
        product = db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

        # Cập nhật thông tin sản phẩm
        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if price is not None:
            product.price = price
        if original_price is not None:
            product.original_price = original_price
        if unit is not None:
            product.unit = unit
        if stock_quantity is not None:
            product.stock_quantity = stock_quantity
        if is_featured is not None:
            product.is_featured = is_featured
        if category_id is not None:
            product.category_id = category_id

        # Xử lý xóa ảnh
        if delete_images:
            try:
                # Parse JSON string thành list
                images_to_delete = json.loads(delete_images)
                if isinstance(images_to_delete, list):
                    # Xóa ảnh từ Cloudinary và database
                    for image_url in images_to_delete:
                        # Xóa từ Cloudinary
                        public_id = extract_public_id_from_url(image_url)
                        if public_id:
                            await delete_image(public_id)
                        
                        # Xóa từ database
                        image = db.query(ProductImages).filter(
                            ProductImages.product_id == product_id,
                            ProductImages.image_url == image_url
                        ).first()
                        if image:
                            db.delete(image)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid delete_images format")

        # Xử lý thêm ảnh mới
        if files:
            # Upload ảnh mới lên Cloudinary
            uploaded_images = await upload_multiple_images(files, "fm_products")
            
            # Thêm ảnh mới vào database
            for i, image_data in enumerate(uploaded_images):
                # Lấy URL từ dữ liệu Cloudinary
                image_url = image_data.get('url') if isinstance(image_data, dict) else image_data
                is_primary_image = is_primary and str(i) in is_primary
                
                new_image = ProductImages(
                    product_id=product_id,
                    image_url=image_url,
                    is_primary=is_primary_image,
                    display_order=i + 1
                )
                db.add(new_image)

        # Commit thay đổi
        db.commit()
        db.refresh(product)

        # Lấy lại thông tin sản phẩm đã cập nhật
        updated_product = db.query(Product).filter(Product.product_id == product_id).first()
        return updated_product

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/manage/products/{product_id}", status_code=204)
async def delete_admin_product(
    product_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Xóa sản phẩm (chỉ admin)"""
    check_admin(current_user)
    try:
        # Kiểm tra sản phẩm tồn tại không
        db_product = db.query(Product).filter(Product.product_id == product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Xóa ảnh sản phẩm trước
        db.query(ProductImages).filter(ProductImages.product_id == product_id).delete()
        
        # Xóa sản phẩm
        db.delete(db_product)
        db.commit()
        
        # Invalidate dashboard cache when a product is deleted
        await invalidate_dashboard_cache()
        logger.info(f"Dashboard cache invalidated after deleting product {product_id}")
        
        return None
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")

@router.post("/manage/products/{product_id}/images", response_model=ProductImageResponse)
async def add_admin_product_image(
    product_id: int = Path(..., gt=0),
    image: ProductImageCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Thêm ảnh cho sản phẩm (chỉ admin)"""
    check_admin(current_user)
    try:
        # Kiểm tra sản phẩm tồn tại không
        product = db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Tạo ảnh mới cho sản phẩm
        db_image = ProductImages(
            product_id=product_id,
            image_url=image.image_url,
            is_primary=image.is_primary,
            display_order=image.display_order
        )
        
        # Nếu là ảnh chính, đặt tất cả ảnh khác thành không chính
        if image.is_primary:
            db.query(ProductImages).filter(
                ProductImages.product_id == product_id
            ).update({"is_primary": False})
        
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return db_image
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding product image: {str(e)}")

@router.delete("/manage/products/{product_id}/images/{image_id}", status_code=204)
async def delete_admin_product_image(
    product_id: int = Path(..., gt=0),
    image_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Xóa ảnh sản phẩm (chỉ admin)"""
    check_admin(current_user)
    try:
        # Kiểm tra ảnh có tồn tại không
        db_image = db.query(ProductImages).filter(
            ProductImages.product_id == product_id,
            ProductImages.image_id == image_id
        ).first()
        
        if not db_image:
            raise HTTPException(status_code=404, detail="Product image not found")
        
        # Xóa ảnh
        db.delete(db_image)
        db.commit()
        return None
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting product image: {str(e)}")

# Route để upload một hình ảnh lên Cloudinary
@router.post("/cloudinary/upload", status_code=status.HTTP_201_CREATED)
async def upload_image_to_cloudinary(
    file: UploadFile = File(...),
    folder: Optional[str] = Form(None),
    current_user = Depends(authentication.get_current_user_with_permissions(required_permissions=["manage_products"]))
):
    """
    Upload một hình ảnh lên Cloudinary.
    
    Args:
        file: File hình ảnh cần upload
        folder: Tên thư mục trên Cloudinary (tùy chọn)
        
    Returns:
        Dict: Kết quả từ Cloudinary
    """
    try:
        # Kiểm tra kiểu file
        content_type = file.content_type
        if not content_type or not content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vui lòng tải lên file hình ảnh hợp lệ (JPEG, PNG, etc.)"
            )
        
        # Upload lên Cloudinary
        result = await upload_image(file, folder=folder if folder else None)
        
        return result
    except HTTPException as e:
        # Re-throw HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Lỗi khi upload ảnh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xử lý upload ảnh: {str(e)}"
        )

# Route để upload nhiều hình ảnh lên Cloudinary
@router.post("/cloudinary/upload-multiple", status_code=status.HTTP_201_CREATED)
async def upload_multiple_images_to_cloudinary(
    files: List[UploadFile] = File(...),
    folder: Optional[str] = Form(None),
    current_user = Depends(authentication.get_current_user_with_permissions(required_permissions=["manage_products"]))
):
    """
    Upload nhiều hình ảnh lên Cloudinary.
    
    Args:
        files: Danh sách các file hình ảnh cần upload
        folder: Tên thư mục trên Cloudinary (tùy chọn)
        
    Returns:
        List[Dict]: Danh sách kết quả từ Cloudinary
    """
    try:
        # Kiểm tra kiểu file
        for file in files:
            content_type = file.content_type
            if not content_type or not content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} không phải là hình ảnh"
                )
        
        # Upload lên Cloudinary
        results = await upload_multiple_images(files, folder=folder if folder else None)
        
        return results
    except HTTPException as e:
        # Re-throw HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Lỗi khi upload nhiều ảnh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xử lý upload nhiều ảnh: {str(e)}"
        )

# Route để xóa một hình ảnh từ Cloudinary
@router.post("/cloudinary/delete", status_code=status.HTTP_200_OK)
async def delete_cloudinary_image(
    public_id: str = Form(...),
    current_user = Depends(authentication.get_current_user_with_permissions(required_permissions=["manage_products"]))
):
    """
    Xóa một hình ảnh từ Cloudinary.
    
    Args:
        public_id: public_id của hình ảnh cần xóa
        
    Returns:
        Dict: Kết quả từ Cloudinary
    """
    try:
        result = await delete_image(public_id)
        
        if result.get("status") == "success":
            return {"message": "Xóa ảnh thành công", "public_id": public_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể xóa ảnh: {result.get('result')}"
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Lỗi khi xóa ảnh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xóa ảnh: {str(e)}"
        )

# Route để xóa một hình ảnh từ URL
@router.post("/cloudinary/delete-by-url", status_code=status.HTTP_200_OK)
async def delete_cloudinary_image_by_url(
    image_url: str = Form(...),
    current_user = Depends(authentication.get_current_user_with_permissions(required_permissions=["manage_products"]))
):
    """
    Xóa một hình ảnh từ Cloudinary bằng URL.
    
    Args:
        image_url: URL của hình ảnh cần xóa
        
    Returns:
        Dict: Kết quả từ Cloudinary
    """
    try:
        public_id = extract_public_id_from_url(image_url)
        
        if not public_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể trích xuất public_id từ URL hình ảnh"
            )
        
        result = await delete_image(public_id)
        
        if result.get("status") == "success":
            return {"message": "Xóa ảnh thành công", "public_id": public_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể xóa ảnh: {result.get('result')}"
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Lỗi khi xóa ảnh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xóa ảnh: {str(e)}"
        )

# Thêm endpoint API quản lý đơn hàng với các tính năng lọc và sắp xếp
@router.get("/manage/orders", response_model=Dict[str, Any])
async def get_admin_orders(
    skip: int = Query(0, description="Số bản ghi bỏ qua"),
    limit: int = Query(10, description="Số bản ghi tối đa trả về"),
    filter: Optional[str] = Query(None, description="Lọc theo trạng thái đơn hàng (pending, delivered, cancelled, etc.)"),
    sort: Optional[str] = Query("newest", description="Sắp xếp theo (newest, oldest, amount_high, amount_low)"),
    month: Optional[str] = Query(None, description="Lọc theo tháng (YYYY-MM)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    try:
        # Bắt đầu truy vấn cơ bản
        query = db.query(
            Orders,
            User.full_name.label("customer_name"),
            User.phone_number,
            User.email
        ).join(User, Orders.user_id == User.user_id)
        
        # Áp dụng bộ lọc theo trạng thái
        if filter:
            query = query.filter(Orders.status == filter)
            
        # Áp dụng bộ lọc theo tháng
        if month:
            try:
                year, month_num = month.split('-')
                query = query.filter(
                    extract('year', Orders.created_at) == int(year),
                    extract('month', Orders.created_at) == int(month_num)
                )
            except ValueError:
                # Bỏ qua nếu định dạng không đúng
                pass
        
        # Đếm tổng số bản ghi (trước khi phân trang)
        total_count = query.count()
        
        # Áp dụng sắp xếp
        if sort == "newest":
            query = query.order_by(Orders.created_at.desc())
        elif sort == "oldest":
            query = query.order_by(Orders.created_at.asc())
        elif sort == "amount_high":
            query = query.order_by(Orders.total_amount.desc())
        elif sort == "amount_low":
            query = query.order_by(Orders.total_amount.asc())
        else:
            # Mặc định sắp xếp theo thời gian tạo đơn giảm dần
            query = query.order_by(Orders.created_at.desc())
        
        # Áp dụng phân trang
        query = query.offset(skip).limit(limit)
        
        # Lấy kết quả
        results = query.all()
        
        # Xử lý dữ liệu trả về
        orders_list = []
        for order, customer_name, phone_number, email in results:
            # Lấy thông tin sản phẩm của đơn hàng này
            product_info = db.query(
                OrderItems.order_item_id,
                Product.name.label("product_name"),
                OrderItems.quantity,
                OrderItems.price
            ).join(
                Product, OrderItems.product_id == Product.product_id
            ).filter(
                OrderItems.order_id == order.order_id
            ).all()
            
            # Tạo chuỗi tên sản phẩm
            product_names = ", ".join([p.product_name for p in product_info])
            
            # Thêm vào danh sách
            orders_list.append({
                "id": order.order_id,
                "product_name": product_names,
                "customer_name": customer_name,
                "phone_number": phone_number,
                "email": email,
                "address": "100 Main St, NYC, NY, USA",  # Giả định - cần thêm cột địa chỉ vào bảng đơn hàng
                "total_amount": float(order.total_amount),
                "shipping_method": "Nhanh" if order.order_id % 2 == 0 else "Tiêu chuẩn",  # Giả định - cần thêm cột shipping_method vào bảng
                "is_prepaid": order.payment_method == "Prepaid",  # Giả định dựa trên payment_method
                "created_at": order.created_at,
                "status": order.status
            })
        
        return {
            "orders": orders_list,
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error in get_admin_orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Có lỗi xảy ra khi lấy danh sách đơn hàng: {str(e)}"
        )

@router.get("/manage/orders/filter-options", response_model=Dict[str, Any])
async def get_order_filter_options(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    try:
        # Lấy danh sách các trạng thái đơn hàng có trong hệ thống
        status_options = db.query(Orders.status).distinct().all()
        status_options = [
            {"value": status[0], "label": status[0].capitalize()} 
            for status in status_options
        ]
        
        # Các phương thức thanh toán
        payment_options = [
            {"value": "all", "label": "Tất cả"},
            {"value": "prepaid", "label": "Đã thanh toán trước"},
            {"value": "unpaid", "label": "Chưa thanh toán"}
        ]
        
        # Các phương thức vận chuyển
        shipping_options = [
            {"value": "all", "label": "Tất cả"},
            {"value": "Nhanh", "label": "Nhanh"},
            {"value": "Tiêu chuẩn", "label": "Tiêu chuẩn"}
        ]
        
        # Danh sách các tháng để lọc
        month_options = []
        current_date = datetime.now()
        for i in range(12):
            date = current_date.replace(month=((current_date.month - i - 1) % 12) + 1)
            if i > 0 and date.month == 12:
                date = date.replace(year=date.year - 1)
            month_options.append({
                "value": date.strftime("%Y-%m"),
                "label": date.strftime("%B %Y")
            })
        
        return {
            "status_options": status_options,
            "payment_options": payment_options,
            "shipping_options": shipping_options,
            "month_options": month_options
        }
        
    except Exception as e:
        logger.error(f"Error in get_order_filter_options: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Có lỗi xảy ra khi lấy tùy chọn lọc đơn hàng: {str(e)}"
        )

@router.get("/manage/orders/{order_id}", response_model=Dict[str, Any])
async def get_order_by_id(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    try:
        # Tìm đơn hàng theo ID
        order = db.query(Orders).filter(Orders.order_id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng với ID {order_id}"
            )
            
        # Lấy thông tin người dùng
        user = db.query(User).filter(User.user_id == order.user_id).first()
        
        # Lấy chi tiết các mặt hàng trong đơn hàng
        order_items = db.query(
            OrderItems,
            Product
        ).join(
            Product, OrderItems.product_id == Product.product_id
        ).filter(
            OrderItems.order_id == order_id
        ).all()
        
        items_list = [
            {
                "order_item_id": item.OrderItems.order_item_id,
                "product_id": item.OrderItems.product_id,
                "product_name": item.Product.name,
                "quantity": item.OrderItems.quantity,
                "price": float(item.OrderItems.price),
                "subtotal": float(item.OrderItems.price * item.OrderItems.quantity)
            }
            for item in order_items
        ]
        
        # Trả về thông tin chi tiết đơn hàng
        return {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "customer_name": user.full_name if user else "Unknown",
            "email": user.email if user else None,
            "phone_number": user.phone_number if user else None,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "payment_method": order.payment_method,
            "shipping_method": "Nhanh" if order.order_id % 2 == 0 else "Tiêu chuẩn",  # Giả định
            "is_prepaid": order.payment_method == "Prepaid",  # Giả định
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": items_list,
            "address": "100 Main St, NYC, NY, USA"  # Giả định
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_order_by_id: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Có lỗi xảy ra khi lấy thông tin đơn hàng: {str(e)}"
        )

@router.put("/manage/orders/{order_id}", response_model=Dict[str, Any])
async def update_order(
    order_id: int,
    order_data: OrderUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    try:
        # Tìm đơn hàng theo ID
        order = db.query(Orders).filter(Orders.order_id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng với ID {order_id}"
            )
        
        # Cập nhật trạng thái đơn hàng nếu có
        if order_data.status is not None:
            order.status = order_data.status
        
        # Các trường khác sẽ được cập nhật trong bảng mở rộng của đơn hàng hoặc thông tin người dùng
        
        # Lưu thay đổi
        db.commit()
        db.refresh(order)
        
        return {"message": "Cập nhật đơn hàng thành công", "order_id": order_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Có lỗi xảy ra khi cập nhật đơn hàng: {str(e)}"
        )