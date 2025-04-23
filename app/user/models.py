# Đây là file models.py cho module user
# Trong tương lai, có thể chuyển định nghĩa các model vào đây

from sqlalchemy import Column, Integer, String, TIMESTAMP, JSON, text, ForeignKey, DECIMAL, Boolean
from ..core.database import Base

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100))
    avatar_url = Column(String(255))
    preferences = Column(JSON)
    location = Column(String(100))
    role = Column(String(20), default="user")
    status = Column(String(20), default="active")
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
