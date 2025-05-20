from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.auth import create_access_token, get_current_user
from .models import User
from .schemas import UserCreate, Login, ForgotPassword, ResetPassword
from ..user.crud import get_user_by_username, get_user_by_email, create_user, update_user
from ..core.security import verify_password, get_password_hash
from datetime import timedelta
from ..core.cache import get_cache, set_cache, redis_client
from ..user.schemas import UserUpdate
from ..user.schemas import User as UserSchema
import json
import secrets
from datetime import datetime, timedelta
import asyncio
from typing import List, Dict, Any
import importlib

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Hàm để thực hiện cache trước các dữ liệu cần thiết sau khi đăng nhập
async def prefetch_user_data_after_login(user_id: int, db: Session, request: Request):
    """
    Hàm helper để cache trước các dữ liệu cần thiết sau khi người dùng đăng nhập
    
    Args:
        user_id: ID của người dùng đã đăng nhập
        db: Database session
        request: HTTP request object
    """
    try:
        # Truy xuất thông tin người dùng thật từ database để có đầy đủ các trường
        real_user = db.query(User).filter(User.user_id == user_id).first()
        if not real_user:
            print(f"Error: User with ID {user_id} not found in database")
            return
        
        # Import các route module để truy cập các handler function
        from ..e_commerce.routes import get_featured_products, get_categories, get_categories_tree
        from ..user.routes import get_cart_items
        from ..e_commerce.routes import get_user_orders
        from ..user.routes import get_current_user_info

        print(f"Prefetching data for user_id: {user_id} after login")
        
        # Gọi các API handlers để cache dữ liệu
        tasks = []
        
        # API không cần thông tin người dùng
        tasks.append(get_featured_products(db=db))
        tasks.append(get_categories(db=db))
        tasks.append(get_categories_tree(force_refresh=True, db=db))
        
        # API cần thông tin người dùng
        tasks.append(get_cart_items(current_user=real_user, db=db))
        tasks.append(get_user_orders(current_user=real_user, db=db))
        tasks.append(get_current_user_info(current_user=real_user))
        
        # Thực hiện tất cả các task song song
        await asyncio.gather(*tasks)
        print(f"Successfully prefetched data for user_id: {user_id}")
        
    except Exception as e:
        print(f"Error prefetching data after login: {str(e)}")
        import traceback
        traceback.print_exc()

@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registereds ")
    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    current_user = get_current_user(db=db) if "Authorization" in router.dependencies else None
    if user.role != "user" and (not current_user or current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="Only admin can assign other roles")
    new_user = create_user(db, user.dict(exclude_unset=True))
    access_token = create_access_token({"user_id": new_user.user_id, "username": new_user.username}, timedelta(minutes=30))
    return {"token": access_token, "user_id": new_user.user_id}

@router.post("/login")
async def login(
    login_data: Login, 
    background_tasks: BackgroundTasks, 
    request: Request,
    db: Session = Depends(get_db)
):
    # Kiểm tra xem đầu vào là email hay username
    if "@" in login_data.username_or_email:
        # Nếu là email
        user = get_user_by_email(db, login_data.username_or_email)
    else:
        # Nếu là username
        user = get_user_by_username(db, login_data.username_or_email)
        print("User login: ", user.password)
        print("Password login: ", login_data.password)
        print("Verify password: ", verify_password(login_data.password, user.password))
        
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Kiểm tra trạng thái người dùng
    if user.status == "blocked":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been blocked. Please contact administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(
        {"user_id": user.user_id, "username": user.username, "role": user.role},
        timedelta(minutes=30)
    )
    
    # Thêm tác vụ prefetch dữ liệu sau khi đăng nhập vào background
    background_tasks.add_task(prefetch_user_data_after_login, user.user_id, db, request)
    
    return {
        "token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "role": user.role
    }

@router.post("/logout", response_model=dict)
async def logout(current_user: User = Depends(get_current_user)):
    try:
        # Xóa cache thông tin người dùng
        cache_key = f"user_info:{current_user.user_id}"
        await redis_client.delete(cache_key)
        
        # Xóa các cache liên quan đến người dùng
        cart_cache_key = f"user_cart:{current_user.user_id}"
        location_cache_key = f"user_location:{current_user.user_id}"
        chat_history_cache_key = f"user_chat_history:{current_user.user_id}"
        
        await redis_client.delete(cart_cache_key)
        await redis_client.delete(location_cache_key)
        await redis_client.delete(chat_history_cache_key)
        
        return {"message": "Logged out successfully and cleared user cache"}
    except Exception as e:
        # Log lỗi nhưng vẫn xác nhận logout thành công
        print(f"Error clearing cache on logout: {str(e)}")
        return {"message": "Logged out successfully"}

@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Legacy endpoint cho việc lấy thông tin người dùng hiện tại.
    Giữ lại để đảm bảo tính tương thích với frontend hiện tại.
    Trong tương lai, nên dùng /api/users/me.
    """
    try:
        # Tạo cache key dựa trên user_id
        cache_key = f"user_info:{current_user.user_id}"
        
        # Kiểm tra xem thông tin đã được cache chưa
        cached_data = await get_cache(cache_key)
        if cached_data:
            return json.loads(cached_data)
        
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
        await set_cache(cache_key, json.dumps(user_data), 900)
        
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user information: {str(e)}"
        )

@router.post("/forgot-password")
async def forgot_password(request: ForgotPassword, db: Session = Depends(get_db)):
    """
    Endpoint để yêu cầu đặt lại mật khẩu
    """
    user = get_user_by_email(db, request.email)
    if not user:
        # Trả về thành công ngay cả khi email không tồn tại để tránh email enumeration
        return {"message": "If your email is registered, you will receive a password reset link"}
    
    # Tạo reset token
    reset_token = secrets.token_urlsafe(32)
    token_expiry = datetime.utcnow() + timedelta(hours=1)
    
    # Lưu token vào cache với thời gian hết hạn 1 giờ
    cache_key = f"password_reset:{reset_token}"
    await set_cache(
        cache_key,
        json.dumps({
            "user_id": user.user_id,
            "email": user.email,
            "expiry": token_expiry.isoformat()
        }),
        3600  # 1 hour in seconds
    )
    
    # Tạo reset URL
    reset_url = f"{request.reset_url_base}/reset-password/{reset_token}"
    
    # Trả về thông tin để frontend gửi email
    return {
        "message": "If your email is registered, you will receive a password reset link",
        "reset_token": reset_token,
        "reset_url": reset_url,
        "email": user.email
    }

@router.post("/reset-password")
async def reset_password(request: ResetPassword, db: Session = Depends(get_db)):
    """
    Endpoint để đặt lại mật khẩu với token
    """
    # Lấy thông tin từ cache
    cache_key = f"password_reset:{request.reset_token}"
    cached_data = await get_cache(cache_key)
    
    if not cached_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    try:
        token_data = json.loads(cached_data)
        expiry = datetime.fromisoformat(token_data["expiry"])
        
        # Kiểm tra token hết hạn
        if datetime.utcnow() > expiry:
            await redis_client.delete(cache_key)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        # Kiểm tra mật khẩu mới
        if len(request.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters"
            )
        
        # Cập nhật mật khẩu
        user = db.query(User).filter(User.user_id == token_data["user_id"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash mật khẩu mới
        hashed_password = get_password_hash(request.new_password)
        user.password = hashed_password
        db.commit()
        
        # Xóa token khỏi cache
        await redis_client.delete(cache_key)
        
        return {"message": "Password has been reset successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting password: {str(e)}"
        )

@router.get("/verify-token", response_model=UserSchema)
async def verify_token_endpoint(current_user: User = Depends(get_current_user)):
    """
    Xác minh JWT token và trả về thông tin người dùng nếu hợp lệ.
    Được sử dụng bởi các dịch vụ khác (ví dụ: base_chat) để xác thực token.
    """
    return current_user

