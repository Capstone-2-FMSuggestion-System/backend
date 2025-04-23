# Đây là file models.py cho module inventory
# Trong tương lai, có thể chuyển định nghĩa các model vào đây

from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, text
from ..core.database import Base

# Import models từ các module cần thiết
from ..user.models import User
from ..e_commerce.models import Product

class Inventory(Base):
    __tablename__ = "inventory"
    inventory_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, default=0)
    unit = Column(String(20))
    last_updated = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

class InventoryTransactions(Base):
    __tablename__ = "inventory_transactions"
    transaction_id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.inventory_id"), nullable=False)
    type = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
