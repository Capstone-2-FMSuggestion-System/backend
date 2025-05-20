# Đây là file schemas.py cho module payment
# Định nghĩa trực tiếp các schema thay vì import từ schemas.py gốc

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal

class PaymentBase(BaseModel):
    order_id: int
    amount: float
    method: str
    status: str = "pending"
    zp_trans_id: Optional[str] = None  # Giữ lại tên trường này để tương thích ngược mặc dù đã chuyển sang PayOS

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    zp_trans_id: Optional[str] = None  # Giữ lại tên trường này để tương thích ngược mặc dù đã chuyển sang PayOS

class PaymentResponse(PaymentBase):
    payment_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaymentMethod(str, Enum):
    COD = "COD"
    PAYOS = "payos"

class PayOSItemData(BaseModel):
    name: str
    price: float
    quantity: int

class PayOSPaymentData(BaseModel):
    order_code: str
    amount: int
    description: str
    items: List[PayOSItemData]
    cancel_url: str
    return_url: str

class PayOSPaymentResponse(BaseModel):
    status: int
    orderCode: str
    description: str
    amount: int
    checkoutUrl: str
    qrCode: Optional[str] = None
    deeplinkApp: Optional[str] = None
    deeplinkMobile: Optional[str] = None
    baseUrl: Optional[str] = None
    expiredAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class PayOSWebhookData(BaseModel):
    orderCode: str
    amount: int
    description: str
    accountNumber: Optional[str] = None
    reference: Optional[str] = None
    transactionDateTime: Optional[str] = None
    paymentLinkId: Optional[str] = None
    status: str  # Có thể là "PAID", "CANCELLED", "EXPIRED", "PROCESSING"

class PayOSWebhook(BaseModel):
    id: str
    data: PayOSWebhookData
    code: int
    description: str
    checksum: str