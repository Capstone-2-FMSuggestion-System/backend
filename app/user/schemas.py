# Đây là file schemas.py cho module user
# Định nghĩa trực tiếp các schema thay vì import từ file schemas.py gốc

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = "user"
    status: Optional[str] = "active"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None

class AvatarUpdate(BaseModel):
    avatar_url: str
    public_id: Optional[str] = None

class Login(BaseModel):
    username_or_email: str
    password: str

class User(UserBase):
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class UserInDB(User):
    password: str
    class Config:
        from_attributes = True

class UserSearchFilter(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
