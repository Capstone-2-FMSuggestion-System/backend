from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
from .models import Product, Category, CartItems, Orders, OrderItems, FavoriteMenus, Menus, Promotions
from .schemas import ProductCreate, ProductUpdate, CartItemCreate, OrderCreate
import logging

logger = logging.getLogger(__name__)

# Import the invalidation helper - this needs to be imported conditionally
# to avoid circular imports since it will be called from payment module
async def invalidate_dashboard_cache_async():
    """Wrapper function to avoid circular imports"""
    from ..core.invalidation_helpers import invalidate_dashboard_cache
    return await invalidate_dashboard_cache()

# Product CRUD operations
def get_products(db: Session, skip: int = 0, limit: int = 100, category_id: Optional[int] = None) -> List[Product]:
    """
    Lấy danh sách sản phẩm có phân trang và lọc theo danh mục.
    """
    query = db.query(Product)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    return query.offset(skip).limit(limit).all()

def get_product(db: Session, product_id: int) -> Optional[Product]:
    """
    Lấy thông tin sản phẩm theo ID.
    """
    return db.query(Product).filter(Product.product_id == product_id).first()

def create_product(db: Session, product: ProductCreate) -> Product:
    """
    Tạo sản phẩm mới trong hệ thống.
    """
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_data: dict) -> Optional[Product]:
    """
    Cập nhật thông tin sản phẩm.
    """
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    
    for field, value in product_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

# Promotion CRUD operations
def get_promotion_by_code(db: Session, code: str) -> Optional[Promotions]:
    """
    Lấy thông tin khuyến mãi theo mã code (name field trong bảng Promotions)
    Kiểm tra xem coupon có trong thời hạn sử dụng không
    """
    current_time = datetime.now()
    return db.query(Promotions).filter(
        Promotions.name == code,
        Promotions.start_date <= current_time,
        Promotions.end_date >= current_time
    ).first()

def get_promotion_by_id(db: Session, promotion_id: int) -> Optional[Promotions]:
    """
    Lấy thông tin khuyến mãi theo ID
    """
    return db.query(Promotions).filter(Promotions.promotion_id == promotion_id).first()

def get_all_active_promotions(db: Session) -> List[Promotions]:
    """
    Lấy danh sách tất cả khuyến mãi đang có hiệu lực
    """
    current_time = datetime.now()
    return db.query(Promotions).filter(
        Promotions.start_date <= current_time,
        Promotions.end_date >= current_time
    ).all()

def create_promotion(db: Session, name: str, discount: float, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, days_valid: int = 30) -> Promotions:
    """
    Tạo mã giảm giá mới
    
    Args:
        db (Session): Phiên làm việc với database
        name (str): Tên mã giảm giá (coupon code)
        discount (float): Phần trăm giảm giá (ví dụ: 10 cho 10%)
        start_date (datetime, optional): Ngày bắt đầu có hiệu lực. Mặc định là ngày hiện tại.
        end_date (datetime, optional): Ngày kết thúc hiệu lực. 
        days_valid (int, optional): Số ngày có hiệu lực nếu không cung cấp end_date. Mặc định là 30.
    
    Returns:
        Promotions: Đối tượng khuyến mãi đã được tạo
    """
    # Kiểm tra xem mã đã tồn tại chưa
    existing_promotion = get_promotion_by_code(db, name)
    if existing_promotion:
        raise ValueError(f"Mã giảm giá '{name}' đã tồn tại")
    
    # Nếu không có start_date, sử dụng thời gian hiện tại
    if not start_date:
        start_date = datetime.now()
    
    # Nếu không có end_date, tính dựa trên days_valid
    if not end_date:
        end_date = start_date + timedelta(days=days_valid)
    
    # Tạo promotion mới
    new_promotion = Promotions(
        name=name,
        discount=discount,
        start_date=start_date,
        end_date=end_date
    )
    
    db.add(new_promotion)
    db.commit()
    db.refresh(new_promotion)
    
    return new_promotion

def update_promotion(db: Session, promotion_id: int, name: Optional[str] = None, discount: Optional[float] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Optional[Promotions]:
    """
    Cập nhật thông tin khuyến mãi
    
    Args:
        db (Session): Phiên làm việc với database
        promotion_id (int): ID của khuyến mãi cần cập nhật
        name (str, optional): Tên mã giảm giá mới
        discount (float, optional): Phần trăm giảm giá mới
        start_date (datetime, optional): Ngày bắt đầu mới
        end_date (datetime, optional): Ngày kết thúc mới
    
    Returns:
        Promotions: Đối tượng khuyến mãi đã được cập nhật hoặc None nếu không tìm thấy
    """
    promotion = get_promotion_by_id(db, promotion_id)
    if not promotion:
        return None
    
    if name:
        promotion.name = name
    if discount is not None:
        promotion.discount = discount
    if start_date:
        promotion.start_date = start_date
    if end_date:
        promotion.end_date = end_date
    
    db.commit()
    db.refresh(promotion)
    
    return promotion

def delete_promotion(db: Session, promotion_id: int) -> bool:
    """
    Xóa mã giảm giá
    
    Args:
        db (Session): Phiên làm việc với database
        promotion_id (int): ID của khuyến mãi cần xóa
    
    Returns:
        bool: True nếu xóa thành công, False nếu không tìm thấy khuyến mãi
    """
    promotion = get_promotion_by_id(db, promotion_id)
    if not promotion:
        return False
    
    db.delete(promotion)
    db.commit()
    
    return True

def apply_coupon_to_order(db: Session, order_id: int, coupon_code: str) -> Optional[dict]:
    """
    Áp dụng mã giảm giá vào đơn hàng
    
    Args:
        db (Session): Phiên làm việc với cơ sở dữ liệu
        order_id (int): ID của đơn hàng cần áp dụng mã giảm giá
        coupon_code (str): Mã giảm giá
        
    Returns:
        dict: Thông tin về tổng tiền đơn hàng sau khi áp dụng mã giảm giá hoặc None nếu không thành công
    """
    # Kiểm tra đơn hàng có tồn tại không
    order = db.query(Orders).filter(Orders.order_id == order_id).first()
    if not order:
        return None
        
    # Kiểm tra mã giảm giá có hợp lệ không
    promotion = get_promotion_by_code(db, coupon_code)
    if not promotion:
        return None
    
    # Tính toán số tiền giảm giá
    original_total = order.total_amount
    discount_amount = original_total * (Decimal(promotion.discount) / 100)
    new_total = original_total - discount_amount
    
    # Cập nhật tổng tiền của đơn hàng
    order.total_amount = new_total
    db.commit()
    db.refresh(order)
    
    return {
        "order_id": order.order_id,
        "original_total": float(original_total),
        "discount_percent": float(promotion.discount),
        "discount_amount": float(discount_amount),
        "new_total": float(new_total)
    }

# Order CRUD operations
def create_order(db: Session, order: OrderCreate) -> Orders:
    """
    Tạo đơn hàng mới trong hệ thống.
    """
    total_amount = Decimal('0')
    
    # Create the order
    db_order = Orders(
        user_id=order.user_id,
        total_amount=total_amount,
        status="pending",
        payment_method=order.payment_method,
        recipient_name=order.recipient_name,
        recipient_phone=order.recipient_phone,
        shipping_address=order.shipping_address,
        shipping_city=order.shipping_city,
        shipping_province=order.shipping_province,
        shipping_postal_code=order.shipping_postal_code
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Create order items
    for item in order.items:
        # Lấy thông tin sản phẩm từ database
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        if not product:
            raise ValueError(f"Product with ID {item.product_id} not found")
        
        # Lấy giá thực tế của sản phẩm
        product_price = product.price
        
        db_order_item = OrderItems(
            order_id=db_order.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=product_price  # Sử dụng giá thực tế
        )
        db.add(db_order_item)
        total_amount += product_price * item.quantity
    
    # Update order total
    db_order.total_amount = total_amount
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order_status(db: Session, order_id: int, status: str) -> Optional[Orders]:
    """
    Cập nhật trạng thái đơn hàng.
    """
    db_order = db.query(Orders).filter(Orders.order_id == order_id).first()
    if not db_order:
        return None
    
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    
    # Schedule cache invalidation instead of awaiting directly
    # since this is a synchronous function
    import asyncio
    try:
        # Schedule the invalidation to run in the background
        loop = asyncio.get_event_loop()
        loop.create_task(invalidate_dashboard_cache_async())
        logger.info(f"Dashboard cache invalidation scheduled after updating order {order_id}")
    except Exception as e:
        logger.error(f"Failed to schedule cache invalidation: {e}")
    
    return db_order

def get_order(db: Session, order_id: int) -> Optional[Orders]:
    """
    Lấy thông tin đơn hàng theo ID.
    """
    return db.query(Orders).filter(Orders.order_id == order_id).first()

# Cart Items CRUD operations
def create_cart_item(db: Session, user_id: int, cart_item: CartItemCreate) -> CartItems:
    """
    Thêm sản phẩm vào giỏ hàng của người dùng.
    """
    db_cart_item = CartItems(
        user_id=user_id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity
    )
    db.add(db_cart_item)
    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item

def get_cart_item(db: Session, cart_item_id: int) -> Optional[CartItems]:
    """
    Lấy thông tin một mục trong giỏ hàng theo ID.
    """
    return db.query(CartItems).filter(CartItems.cart_item_id == cart_item_id).first()

def get_cart_items_by_user(db: Session, user_id: int) -> List[CartItems]:
    """
    Lấy danh sách tất cả các mục trong giỏ hàng của một người dùng.
    """
    return db.query(CartItems).filter(CartItems.user_id == user_id).all()

def update_cart_item(db: Session, cart_item_id: int, quantity: int) -> Optional[CartItems]:
    """
    Cập nhật số lượng sản phẩm trong giỏ hàng.
    """
    db_cart_item = get_cart_item(db, cart_item_id)
    if not db_cart_item:
        return None
    
    db_cart_item.quantity = quantity
    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item

def delete_cart_item(db: Session, cart_item_id: int) -> bool:
    """
    Xóa mục khỏi giỏ hàng.
    """
    db_cart_item = get_cart_item(db, cart_item_id)
    if not db_cart_item:
        return False
    
    db.delete(db_cart_item)
    db.commit()
    return True

# Favorite Menu CRUD operations
def create_favorite_menu(db: Session, user_id: int, menu_id: int) -> FavoriteMenus:
    """
    Tạo bản ghi yêu thích cho menu.
    """
    favorite = FavoriteMenus(user_id=user_id, menu_id=menu_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite

def get_favorite_menu(db: Session, favorite_menu_id: int) -> Optional[FavoriteMenus]:
    """
    Lấy thông tin menu yêu thích theo ID.
    """
    return db.query(FavoriteMenus).filter(FavoriteMenus.favorite_menu_id == favorite_menu_id).first()

def get_favorite_menus_by_user(db: Session, user_id: int) -> List[FavoriteMenus]:
    """
    Lấy danh sách menu yêu thích của người dùng.
    """
    return db.query(FavoriteMenus).filter(FavoriteMenus.user_id == user_id).all()

def delete_favorite_menu(db: Session, favorite_menu_id: int) -> bool:
    """
    Xóa menu khỏi danh sách yêu thích.
    """
    favorite = get_favorite_menu(db, favorite_menu_id)
    if not favorite:
        return False
    
    db.delete(favorite)
    db.commit()
    return True