# Đây là file schemas.py cho module auth
# Định nghĩa trực tiếp hoặc import từ user.schemas thay vì từ schemas.py gốc

from ..user.schemas import Token, TokenData, User, UserInDB, UserCreate, Login
from pydantic import BaseModel, EmailStr

# Trong tương lai, có thể chuyển định nghĩa các schema vào đây

class ForgotPassword(BaseModel):
    email: EmailStr
    reset_url_base: str

class ResetPassword(BaseModel):
    reset_token: str
    new_password: str
