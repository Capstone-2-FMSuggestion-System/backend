from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from .models import Product, Category, CartItems, Orders, OrderItems, FavoriteMenus, Menus
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
        payment_method=order.payment_method
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