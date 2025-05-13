from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, TIMESTAMP, text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

from ..e_commerce.models import Orders, Product

class Payments(Base):
    __tablename__ = "payments"
    payment_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    method = Column(String(50))
    status = Column(String(20), default="pending")
    transaction_id = Column(String(100), nullable=True)
    payment_data = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    order = relationship("Orders", back_populates="payments")