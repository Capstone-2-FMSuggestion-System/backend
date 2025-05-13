# Đây là file models.py cho module payment

from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, TIMESTAMP, text
from ..core.database import Base
from sqlalchemy.orm import relationship
# Import models từ các module cần thiết
from ..user.models import User

class Payments(Base):
    __tablename__ = "payments"
    payment_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    method = Column(String(50))
    status = Column(String(20), default="pending")
    zp_trans_id = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    
# Import các model cần thiết sau khi định nghĩa model Payments
from ..e_commerce.models import Orders, Product