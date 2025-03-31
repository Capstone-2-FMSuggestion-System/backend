from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
from ..models import User, Product, CartItems, Orders, OrderItems, Menus, MenuItems, FavoriteMenus, Reviews
from ..schemas import ProductResponse, CartItem, OrderCreate, OrderResponse, ReviewCreate, ReviewResponse, UserUpdate
from ..crud import get_products, get_product, create_cart_item, get_cart_item, update_cart_item, delete_cart_item
from ..cache import get_cache, set_cache, redis_client
from typing import List

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    # Tạo cache key dựa trên user_id
    cache_key = f"user_info:{current_user.user_id}"
    
    # Kiểm tra xem thông tin đã được cache chưa
    cached_data = await get_cache(cache_key)
    if cached_data:
        return eval(cached_data)
    
    # Nếu chưa có trong cache, lấy thông tin từ database
    user_data = {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role
    }
    
    # Lưu vào cache với thời gian hết hạn là 15 phút
    await set_cache(cache_key, str(user_data), 900)
    
    return user_data

@router.put("/me", response_model=dict)
async def update_user_info(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    
    # Xóa cache thông tin người dùng khi cập nhật thông tin
    cache_key = f"user_info:{current_user.user_id}"
    await redis_client.delete(cache_key)
    
    return {"message": "User information updated successfully"}

@router.get("/cart", response_model=List[dict])
async def get_cart_items(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Tạo cache key dựa trên user_id
    cache_key = f"user_cart:{current_user.user_id}"
    
    # Kiểm tra xem giỏ hàng đã được cache chưa
    cached_data = await get_cache(cache_key)
    if cached_data:
        return eval(cached_data)
    
    # Nếu chưa có trong cache, lấy thông tin từ database
    cart_items = db.query(CartItems).filter(CartItems.user_id == current_user.user_id).all()
    result = []
    for item in cart_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        result.append({
            "cart_item_id": item.cart_item_id,
            "product_id": item.product_id,
            "product_name": product.name,
            "quantity": item.quantity,
            "price": float(product.price),
            "total": float(product.price * item.quantity)
        })
    
    # Lưu vào cache với thời gian hết hạn là 5 phút
    await set_cache(cache_key, str(result), 300)
    
    return result

@router.post("/cart", response_model=dict)
async def add_to_cart(
    item: CartItem,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = get_product(db, item.product_id)
    if not product or item.quantity <= 0 or item.quantity > product.stock_quantity:
        raise HTTPException(status_code=400, detail="Invalid quantity or product")
    
    cart_item = create_cart_item(db, current_user.user_id, item.product_id, item.quantity)
    
    # Xóa cache giỏ hàng khi thêm sản phẩm mới
    cache_key = f"user_cart:{current_user.user_id}"
    await redis_client.delete(cache_key)
    
    return {"message": "Item added to cart", "cart_item_id": cart_item.cart_item_id}

@router.put("/cart/{cart_item_id}", response_model=dict)
async def update_cart_item(
    cart_item_id: int,
    quantity: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = get_cart_item(db, cart_item_id, current_user.user_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    product = get_product(db, cart_item.product_id)
    if not product or quantity <= 0 or quantity > product.stock_quantity:
        raise HTTPException(status_code=400, detail="Invalid quantity")
    
    update_cart_item(db, cart_item_id, quantity)
    
    # Xóa cache giỏ hàng khi cập nhật số lượng sản phẩm
    cache_key = f"user_cart:{current_user.user_id}"
    await redis_client.delete(cache_key)
    
    return {"message": "Cart item updated successfully"}

@router.delete("/cart/{cart_item_id}", response_model=dict)
async def remove_from_cart(
    cart_item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = get_cart_item(db, cart_item_id, current_user.user_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    delete_cart_item(db, cart_item_id)
    
    # Xóa cache giỏ hàng khi xóa sản phẩm
    cache_key = f"user_cart:{current_user.user_id}"
    await redis_client.delete(cache_key)
    
    return {"message": "Item removed from cart"}

@router.get("/chat-history", response_model=List[dict])
async def get_user_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Tạo cache key dựa trên user_id
    cache_key = f"user_chat_history:{current_user.user_id}"
    
    # Kiểm tra xem lịch sử chat đã được cache chưa
    cached_data = await get_cache(cache_key)
    if cached_data:
        return eval(cached_data)
    
    # Nếu chưa có trong cache, lấy thông tin từ database
    # Get all chat sessions for the user
    chat_sessions = db.execute(
        """
        SELECT cs.session_id, cs.created_at, 
               COUNT(cm.id) as message_count
        FROM chat_sessions cs
        LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
        WHERE cs.user_id = :user_id
        GROUP BY cs.session_id, cs.created_at
        ORDER BY cs.created_at DESC
        """,
        {"user_id": current_user.user_id}
    ).fetchall()

    result = [
        {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "message_count": session.message_count
        }
        for session in chat_sessions
    ]
    
    # Lưu vào cache với thời gian hết hạn là 5 phút
    await set_cache(cache_key, str(result), 300)
    
    return result

@router.get("/chat-history/{session_id}", response_model=List[dict])
async def get_chat_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Tạo cache key dựa trên session_id và user_id
    cache_key = f"chat_session:{session_id}:{current_user.user_id}"
    
    # Kiểm tra xem tin nhắn chat đã được cache chưa
    cached_data = await get_cache(cache_key)
    if cached_data:
        return eval(cached_data)
    
    # Nếu chưa có trong cache, lấy thông tin từ database
    # Verify session belongs to user
    session = db.execute(
        "SELECT user_id FROM chat_sessions WHERE session_id = :session_id",
        {"session_id": session_id}
    ).fetchone()
    
    if not session or session.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this chat session"
        )

    # Get all messages in the session
    messages = db.execute(
        """
        SELECT question, answer, timestamp
        FROM chat_messages
        WHERE session_id = :session_id
        ORDER BY timestamp ASC
        """,
        {"session_id": session_id}
    ).fetchall()

    result = [
        {
            "question": msg.question,
            "answer": msg.answer,
            "timestamp": msg.timestamp
        }
        for msg in messages
    ]
    
    # Lưu vào cache với thời gian hết hạn là 5 phút
    await set_cache(cache_key, str(result), 300)
    
    return result