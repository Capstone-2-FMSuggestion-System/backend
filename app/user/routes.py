from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.auth import get_current_user
from .models import User
from .schemas import UserUpdate, AvatarUpdate
from ..e_commerce.schemas import CartItemCreate, CartItem, ProductResponse, ProductImageResponse
from .crud import get_user_by_username, get_user, create_user, update_user, delete_user, get_users

# Import từ module e_commerce
from ..e_commerce.models import Product, CartItems, Orders, OrderItems, ProductImages
from ..e_commerce.crud import get_products, get_product, create_cart_item, get_cart_item, update_cart_item, delete_cart_item

# Import các module khác cần thiết
from ..core.cache import get_cache, set_cache, redis_client
from ..core.cloudinary_utils import upload_image, delete_image
from typing import List
import os
import re
import logging
import json
from datetime import datetime

# Cấu hình logging
logger = logging.getLogger(__name__)

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
    logger.info(f"Avatar upload request for user: {current_user.username} (ID: {current_user.user_id})")
    
    # Kiểm tra định dạng file
    allowed_extensions = ["jpg", "jpeg", "png", "gif", "webp"]
    file_extension = file.filename.split(".")[-1].lower()
    
    if file_extension not in allowed_extensions:
        logger.warning(f"Invalid file extension: {file_extension} (Allowed: {allowed_extensions})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File phải có định dạng: {', '.join(allowed_extensions)}"
        )
    
    # Kiểm tra kích thước file (max 2MB)
    file_size = 0
    file_content = await file.read()
    file_size = len(file_content)
    # Đặt lại vị trí của file để đọc lại sau này
    await file.seek(0)
    
    max_size = 2 * 1024 * 1024  # 2MB
    if file_size > max_size:
        logger.warning(f"File too large: {file_size} bytes (Max: {max_size} bytes)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Kích thước file quá lớn. Tối đa 2MB."
        )
    
    # Xóa avatar cũ nếu có
    if current_user.avatar_url:
        logger.info(f"Existing avatar found: {current_user.avatar_url}")
        # Lấy public_id từ URL
        match = re.search(r'data_fm/([^/]+)', current_user.avatar_url)
        if match:
            old_public_id = f"data_fm/{match.group(1).split('.')[0]}"
            try:
                logger.info(f"Attempting to delete old avatar: {old_public_id}")
                await delete_image(old_public_id)
                logger.info(f"Successfully deleted old avatar")
            except Exception as e:
                # Log lỗi nhưng vẫn tiếp tục tải lên avatar mới
                logger.error(f"Failed to delete old avatar: {str(e)}")
                print(f"Không thể xóa avatar cũ: {str(e)}")
    
    # Tải lên avatar mới
    try:
        logger.info(f"Uploading new avatar: {file.filename} ({file_size} bytes)")
        # Đảm bảo upload vào đúng folder data_fm trên Cloudinary
        upload_result = await upload_image(file, folder="data_fm")
        
        # Log kết quả cho dễ debug
        logger.info(f"Avatar uploaded successfully: {upload_result.get('url')}")
        
        # Cập nhật URL avatar trong database
        current_user.avatar_url = upload_result["url"]
        db.commit()
        logger.info(f"Avatar updated in database: {upload_result['url']}")
        
        # Xóa cache thông tin người dùng
        cache_key = f"user_info:{current_user.user_id}"
        await redis_client.delete(cache_key)
        logger.info(f"User cache cleared: {cache_key}")
        
        return {
            "message": "Avatar updated successfully",
            "avatar_url": upload_result["url"]
        }
    except ValueError as e:
        # Bắt lỗi từ hàm upload_image
        logger.error(f"Validation error in avatar upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in avatar upload: {str(e)}")
        print(f"Lỗi không xác định khi cập nhật avatar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}"
        )

@router.get("/cart", response_model=List[CartItem])
async def get_cart_items(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Tạo cache key dựa trên user_id
    cache_key = f"user_cart:{current_user.user_id}"
    
    # Kiểm tra xem giỏ hàng đã được cache chưa
    cached_data = await get_cache(cache_key)
    if cached_data:
        try:
            # Sử dụng json.loads thay vì eval để an toàn hơn
            return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error parsing cached cart data: {str(e)}")
            # Nếu có lỗi khi parse cache, tiếp tục lấy dữ liệu mới
    
    # Nếu chưa có trong cache, lấy thông tin từ database
    cart_items = db.query(CartItems).filter(CartItems.user_id == current_user.user_id).all()
    result = []
    for item in cart_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        if not product:
            continue
            
        # Lấy tất cả ảnh của sản phẩm
        product_images = db.query(ProductImages).filter(
            ProductImages.product_id == item.product_id
        ).all()
        
        # Tạo danh sách ảnh với đầy đủ thông tin
        images = []
        for img in product_images:
            image_data = {
                "image_id": img.image_id,
                "product_id": img.product_id,
                "image_url": img.image_url,
                "is_primary": img.is_primary,
                "created_at": img.created_at.isoformat() if img.created_at else None
            }
            images.append(image_data)
        
        # Tạo đối tượng cart_item với cấu trúc đúng
        cart_item = {
            "cart_item_id": item.cart_item_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "user_id": item.user_id,
            "added_at": item.added_at.isoformat() if item.added_at else None,
            "product": {
                "product_id": product.product_id,
                "name": product.name,
                "description": product.description,
                "price": float(product.price),
                "original_price": float(product.original_price) if product.original_price else None,
                "stock_quantity": product.stock_quantity,
                "category_id": product.category_id,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "images": images
            }
        }
        result.append(cart_item)
    
    # Lưu vào cache với thời gian hết hạn là 5 phút
    try:
        # Sử dụng json.dumps thay vì str để serialize dữ liệu
        await set_cache(cache_key, json.dumps(result), 300)
    except Exception as e:
        logger.error(f"Error caching cart data: {str(e)}")
    
    return result

@router.post("/cart", response_model=dict)
async def add_to_cart(
    item: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = get_product(db, item.product_id)
    if not product or item.quantity <= 0 or item.quantity > product.stock_quantity:
        raise HTTPException(status_code=400, detail="Invalid quantity or product")
    
    # Tạo cart_item với chính xác số lượng tham số theo định dạng hàm
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