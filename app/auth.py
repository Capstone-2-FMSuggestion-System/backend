from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from .database import get_db
from .models import User
from .crud import get_user_by_username
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Tên Function: create_access_token
    
    1. Mô tả ngắn gọn:
    Tạo JWT access token cho việc xác thực người dùng.
    
    2. Mô tả công dụng:
    Tạo một JWT (JSON Web Token) bằng cách mã hóa dữ liệu người dùng với thời gian hết hạn.
    Token được ký bằng khóa bí mật và có thể được sử dụng cho các yêu cầu xác thực.
    
    3. Các tham số đầu vào:
    - data (dict): Dictionary chứa dữ liệu cần mã hóa trong token (thường là thông tin người dùng)
    - expires_delta (timedelta, optional): Thời gian hết hạn tùy chỉnh cho token.
                                         Nếu không được cung cấp, mặc định là ACCESS_TOKEN_EXPIRE_MINUTES
    
    4. Giá trị trả về:
    - str: Token JWT đã được mã hóa
    
    5. Ví dụ sử dụng:
    >>> user_data = {"user_id": 1, "username": "nguyen_van_a"}
    >>> token = create_access_token(user_data)
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Tên Function: get_current_user
    
    1. Mô tả ngắn gọn:
    Lấy thông tin người dùng hiện tại từ JWT token.
    
    2. Mô tả công dụng:
    Giải mã JWT token để xác thực và truy xuất thông tin người dùng từ cơ sở dữ liệu.
    Function này được sử dụng như một dependency trong FastAPI để bảo vệ các endpoint yêu cầu xác thực.
    
    3. Các tham số đầu vào:
    - token (str): JWT token từ header Authorization (được inject bởi oauth2_scheme)
    - db (Session): Phiên làm việc với database (được inject bởi get_db)
    
    4. Giá trị trả về:
    - User: Đối tượng User nếu xác thực thành công
    - HTTPException: Nếu xác thực thất bại hoặc token không hợp lệ
    
    5. Ví dụ sử dụng:
    >>> @app.get("/users/me")
    >>> def read_user_me(current_user: User = Depends(get_current_user)):
    >>>     return current_user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, payload.get("username"))
    if not user:
        raise credentials_exception
    return user 