# Đây là file schemas.py cho module inventory
# Định nghĩa trực tiếp các schema thay vì import từ schemas.py gốc

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class InventoryBase(BaseModel):
    product_id: int
    quantity: int
    unit: Optional[str] = None

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    quantity: Optional[int] = None
    unit: Optional[str] = None

class InventoryResponse(InventoryBase):
    inventory_id: int
    last_updated: datetime
    
    class Config:
        from_attributes = True

class InventoryTransactionBase(BaseModel):
    inventory_id: int
    type: str  # "in" or "out"
    quantity: int

class InventoryTransactionCreate(InventoryTransactionBase):
    pass

class InventoryTransactionResponse(InventoryTransactionBase):
    transaction_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Alias cho tương thích với code cũ
TransactionCreate = InventoryTransactionCreate
