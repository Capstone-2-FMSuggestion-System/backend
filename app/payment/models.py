# Đây là file models.py cho module payment

from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, TIMESTAMP, text, JSON
from sqlalchemy.orm import relationship
from ..core.database import Base

# Import models từ các module cần thiết
from ..user.models import User

class Payments(Base):
    __tablename__ = "payments"
    payment_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    method = Column(String(50))
    status = Column(String(20), default="pending")
    transaction_id = Column(String(100), nullable=True)
    payment_data = Column(JSON, nullable=True)  # Store PayOS payment data
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    # Relationships
    order = relationship("Orders", back_populates="payments")

# Import các model cần thiết sau khi định nghĩa model Payments
from ..e_commerce.models import Orders, Product
