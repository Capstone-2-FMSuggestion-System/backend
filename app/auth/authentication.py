from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List
from ..user.models import User
from sqlalchemy.orm import Session
from ..core.database import get_db
import logging

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# Setup logging
logger = logging.getLogger(__name__)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Lấy thông tin người dùng hiện tại từ token JWT
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User: Đối tượng User của người dùng hiện tại
        
    Raises:
        HTTPException: Nếu token không hợp lệ hoặc người dùng không tồn tại
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Lấy user_id từ payload
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Lấy thông tin người dùng từ database
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            raise credentials_exception
            
        # Kiểm tra trạng thái người dùng
        if user.status == "inactive":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
            
        return user
    except JWTError:
        raise credentials_exception

def get_current_user_with_permissions(required_permissions: List[str] = None):
    """
    Dependency factory để kiểm tra quyền của người dùng hiện tại
    
    Args:
        required_permissions: Danh sách các quyền cần thiết
        
    Returns:
        function: Dependency function để sử dụng với FastAPI
    """
    async def _get_current_user_with_permissions(
        current_user: User = Depends(get_current_user),
    ) -> User:
        # Nếu không yêu cầu quyền gì, trả về người dùng hiện tại
        if not required_permissions:
            return current_user
            
        # Kiểm tra vai trò admin (có tất cả quyền)
        if current_user.role == "admin":
            return current_user
            
        # Kiểm tra từng quyền cần thiết
        user_permissions = get_user_permissions(current_user)
        
        for permission in required_permissions:
            if permission not in user_permissions:
                # Log thông tin hữu ích
                logger.warning(f"User {current_user.user_id} ({current_user.username}) with role {current_user.role} tried to access a resource requiring permission '{permission}'")
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have the required permission: {permission}"
                )
                
        return current_user
        
    return _get_current_user_with_permissions

def get_user_permissions(user: User) -> List[str]:
    """
    Lấy danh sách quyền của người dùng dựa trên vai trò
    
    Args:
        user: Đối tượng User
        
    Returns:
        List[str]: Danh sách các quyền
    """
    # Ánh xạ vai trò sang quyền
    role_permissions = {
        "admin": [
            "manage_users", 
            "manage_products", 
            "manage_orders",
            "manage_categories",
            "view_dashboard",
            "manage_inventory"
        ],
        "manager": [
            "manage_products",
            "manage_orders",
            "view_dashboard",
            "manage_inventory"
        ],
        "user": [
            "view_products",
            "place_orders"
        ]
    }
    
    # Trả về quyền dựa trên vai trò
    return role_permissions.get(user.role, []) 