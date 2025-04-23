from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.auth import create_access_token, get_current_user
from .models import User
from .schemas import UserCreate, Login
from ..user.crud import get_user_by_username, get_user_by_email, create_user
from ..core.security import verify_password
from datetime import timedelta
from ..core.cache import get_cache, set_cache, redis_client
from ..user.schemas import UserUpdate
import json

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
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
async def login(login_data: Login, db: Session = Depends(get_db)):
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

