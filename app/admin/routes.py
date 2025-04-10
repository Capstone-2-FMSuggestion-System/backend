from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from ..core.database import get_db
from ..core.auth import get_current_user
from .models import User, Product, Category, Orders, Payments, Promotions
from .schemas import ProductCreate, UserCreate, PromotionCreate, DashboardStats, RecentOrdersResponse, RevenueOverviewResponse, RecentOrder, RevenuePeriod
from typing import List, Optional
from datetime import datetime, timedelta
import calendar
import json
import logging
from ..core.cache import get_cache, set_cache

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
        ]
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
        return json.loads(cached_data)
    
    # Đếm tổng số đơn hàng
    total_orders = db.query(Orders).count()
    
    # Tính tổng doanh thu từ các đơn hàng đã hoàn thành
    total_revenue = db.query(func.sum(Orders.total_amount)).filter(
        Orders.status == "completed"
    ).scalar() or 0
    
    # Đếm tổng số khách hàng (người dùng có vai trò "user")
    total_customers = db.query(User).filter(User.role == "user").count()
    
    # Đếm tổng số sản phẩm
    total_products = db.query(Product).count()
    
    # Tạo kết quả
    result = {
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "total_customers": total_customers,
        "total_products": total_products
    }
    
    # Lưu vào cache với thời gian hết hạn là 5 phút
    await set_cache(cache_key, json.dumps(result), 300)
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
        return json.loads(cached_data)
    
    # Lấy đơn hàng gần đây nhất
    recent_orders_query = db.query(
        Orders, User.full_name
    ).join(
        User, Orders.user_id == User.user_id
    ).order_by(
        Orders.created_at.desc()
    ).limit(limit).all()
    
    # Chuyển đổi kết quả sang định dạng mong muốn
    orders_list = []
    for order, customer_name in recent_orders_query:
        orders_list.append({
            "order_id": order.order_id,
            "user_id": order.user_id,
            "customer_name": customer_name,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "payment_method": order.payment_method,
            "created_at": order.created_at
        })
    
    result = {"orders": orders_list}
    
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
        return json.loads(cached_data)
    
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
    
    # Tạo query cơ bản để lấy doanh thu và số đơn hàng
    base_query = db.query(
        Orders.created_at,
        Orders.total_amount
    ).filter(
        Orders.status == "completed",
        Orders.created_at >= start_dt,
        Orders.created_at <= end_dt + timedelta(days=1)  # Bao gồm cả ngày end_date
    )
    
    # Khởi tạo danh sách kết quả
    result_data = []
    
    # Xử lý dựa vào time_range
    if time_range == "daily":
        # Nhóm theo ngày
        daily_revenue = {}
        daily_orders = {}
        
        for order in base_query.all():
            date_str = order.created_at.strftime("%Y-%m-%d")
            if date_str not in daily_revenue:
                daily_revenue[date_str] = 0
                daily_orders[date_str] = 0
            
            daily_revenue[date_str] += float(order.total_amount)
            daily_orders[date_str] += 1
        
        # Điền vào khoảng trống nếu có
        current_date = start_dt
        while current_date <= end_dt:
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str not in daily_revenue:
                daily_revenue[date_str] = 0
                daily_orders[date_str] = 0
            
            result_data.append({
                "period": date_str,
                "revenue": daily_revenue[date_str],
                "orders_count": daily_orders[date_str]
            })
            
            current_date += timedelta(days=1)
    
    elif time_range == "weekly":
        # Nhóm theo tuần
        weekly_revenue = {}
        weekly_orders = {}
        
        for order in base_query.all():
            # ISO week format: YYYY-WW
            year, week, _ = order.created_at.isocalendar()
            week_str = f"{year}-W{week:02d}"
            
            if week_str not in weekly_revenue:
                weekly_revenue[week_str] = 0
                weekly_orders[week_str] = 0
            
            weekly_revenue[week_str] += float(order.total_amount)
            weekly_orders[week_str] += 1
        
        # Chuyển đổi danh sách tuần thành kết quả
        for week_str in sorted(weekly_revenue.keys()):
            result_data.append({
                "period": week_str,
                "revenue": weekly_revenue[week_str],
                "orders_count": weekly_orders[week_str]
            })
    
    elif time_range == "monthly":
        # Nhóm theo tháng
        monthly_revenue = {}
        monthly_orders = {}
        
        for order in base_query.all():
            month_str = order.created_at.strftime("%Y-%m")
            
            if month_str not in monthly_revenue:
                monthly_revenue[month_str] = 0
                monthly_orders[month_str] = 0
            
            monthly_revenue[month_str] += float(order.total_amount)
            monthly_orders[month_str] += 1
        
        # Điền vào khoảng trống nếu có
        current_year = start_dt.year
        current_month = start_dt.month
        end_year = end_dt.year
        end_month = end_dt.month
        
        while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
            month_str = f"{current_year}-{current_month:02d}"
            
            if month_str not in monthly_revenue:
                monthly_revenue[month_str] = 0
                monthly_orders[month_str] = 0
            
            result_data.append({
                "period": month_str,
                "revenue": monthly_revenue[month_str],
                "orders_count": monthly_orders[month_str]
            })
            
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
    
    else:  # yearly
        # Nhóm theo năm
        yearly_revenue = {}
        yearly_orders = {}
        
        for order in base_query.all():
            year_str = order.created_at.strftime("%Y")
            
            if year_str not in yearly_revenue:
                yearly_revenue[year_str] = 0
                yearly_orders[year_str] = 0
            
            yearly_revenue[year_str] += float(order.total_amount)
            yearly_orders[year_str] += 1
        
        # Điền vào khoảng trống nếu có
        for year in range(start_dt.year, end_dt.year + 1):
            year_str = str(year)
            
            if year_str not in yearly_revenue:
                yearly_revenue[year_str] = 0
                yearly_orders[year_str] = 0
            
            result_data.append({
                "period": year_str,
                "revenue": yearly_revenue[year_str],
                "orders_count": yearly_orders[year_str]
            })
    
    result = {
        "time_range": time_range,
        "data": result_data
    }
    
    # Lưu vào cache với thời gian hết hạn 10 phút
    await set_cache(cache_key, json.dumps(result), 600)
    logger.info(f"Revenue overview cached for 10 minutes")
    
    return result 