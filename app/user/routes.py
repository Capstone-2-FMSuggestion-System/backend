from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.auth import get_current_user
from .models import User
from .schemas import UserUpdate, AvatarUpdate
from .crud import get_user_by_username, get_user, create_user, update_user, delete_user, get_users

# Import từ module e_commerce
from ..e_commerce.models import Product, CartItems, Orders, OrderItems 
from ..e_commerce.schemas import ProductResponse, CartItem, OrderCreate, OrderResponse
from ..e_commerce.crud import get_products, get_product, create_cart_item, get_cart_item, update_cart_item, delete_cart_item

# Import các module khác cần thiết
from ..core.cache import get_cache, set_cache, redis_client
from ..core.cloudinary_utils import upload_image, delete_image
from typing import List
import os
import re

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
        "avatar_url": current_user.avatar_url,
        "role": current_user.role,
        "status": current_user.status,
        "location": current_user.location,
        "preferences": current_user.preferences,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }
    
    # Lọc bỏ các giá trị None
    user_data = {k: v for k, v in user_data.items() if v is not None}
    
    # Lưu vào cache với thời gian hết hạn là 15 phút
    await set_cache(cache_key, str(user_data), 900)
    
    return user_data

@router.put("/me", response_model=dict)
async def update_user_info(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint duy nhất để cập nhật thông tin người dùng.
    Trước đây có endpoint /profile nhưng đã được gộp vào endpoint này.
    """
    try:
        # Chỉ cập nhật các trường cho phép
        update_data = user_update.dict(exclude_unset=True)
        
        # Không cho phép thay đổi role từ endpoint này
        if "role" in update_data:
            del update_data["role"]
        
        # Cập nhật từng trường
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        # Commit thay đổi vào database
        db.commit()
        
        # Xóa cache thông tin người dùng
        cache_key = f"user_info:{current_user.user_id}"
        await redis_client.delete(cache_key)
        
        # Trả về thông tin người dùng đã cập nhật
        user_data = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "avatar_url": current_user.avatar_url,
            "role": current_user.role,
            "status": current_user.status,
            "location": current_user.location,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
        
        return {"message": "User information updated successfully", "user": user_data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user information: {str(e)}"
        )

@router.post("/me/avatar", response_model=dict)
async def update_user_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Kiểm tra định dạng file
    allowed_extensions = ["jpg", "jpeg", "png", "gif", "webp"]
    file_extension = file.filename.split(".")[-1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File phải có định dạng: {', '.join(allowed_extensions)}"
        )
    
    # Xóa avatar cũ nếu có
    if current_user.avatar_url:
        # Lấy public_id từ URL
        match = re.search(r'data_fm/([^/]+)', current_user.avatar_url)
        if match:
            old_public_id = f"data_fm/{match.group(1).split('.')[0]}"
            try:
                await delete_image(old_public_id)
            except Exception as e:
                # Log lỗi nhưng vẫn tiếp tục tải lên avatar mới
                print(f"Không thể xóa avatar cũ: {e}")
    
    # Tải lên avatar mới
    try:
        upload_result = await upload_image(file, folder="data_fm")
        
        # Cập nhật URL avatar trong database
        current_user.avatar_url = upload_result["url"]
        db.commit()
        
        # Xóa cache thông tin người dùng
        cache_key = f"user_info:{current_user.user_id}"
        await redis_client.delete(cache_key)
        
        return {
            "message": "Avatar updated successfully",
            "avatar_url": upload_result["url"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}"
        )

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
    
    # Tạo cart_item với chính xác số lượng tham số theo định nghĩa hàm
    cart_item = create_cart_item(db, user_id=current_user.user_id, cart_item=item)
    
    # Xóa cache giỏ hàng khi thêm sản phẩm mới
    cache_key = f"user_cart:{current_user.user_id}"
    await redis_client.delete(cache_key)
    
    return {"message": "Item added to cart", "cart_item_id": cart_item.cart_item_id}

@router.put("/cart/{cart_item_id}", response_model=dict)
async def update_cart_item_route(
    cart_item_id: int,
    quantity: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Lấy cart_item với chính xác số lượng tham số theo định nghĩa hàm
    cart_item = get_cart_item(db, cart_item_id)
    if not cart_item or cart_item.user_id != current_user.user_id:
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
    # Lấy cart_item với chính xác số lượng tham số theo định nghĩa hàm
    cart_item = get_cart_item(db, cart_item_id)
    if not cart_item or cart_item.user_id != current_user.user_id:
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