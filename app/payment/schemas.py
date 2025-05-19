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
    zp_trans_id: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    zp_trans_id: Optional[str] = None

class PaymentResponse(PaymentBase):
    payment_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaymentMethod(str, Enum):
    COD = "COD"
    ZALOPAY_APP = "zalopayapp"
    ATM = "ATM"
    CREDIT_CARD = "CC"
    QR_CODE = "QR"

class ZaloPayOrderBase(BaseModel):
    app_id: Optional[int] = None
    app_trans_id: Optional[str] = None
    app_user: Optional[str] = None
    app_time: Optional[int] = None
    item: Optional[str] = None
    embed_data: Optional[Dict[str, Any]] = None
    amount: Optional[int] = None
    description: Optional[str] = None
    bank_code: Optional[str] = None

class ZaloPayOrderResponse(BaseModel):
    return_code: int
    return_message: str
    sub_return_code: Optional[int] = None
    sub_return_message: Optional[str] = None
    order_url: Optional[str] = None
    zp_trans_token: Optional[str] = None
    order_token: Optional[str] = None
    qr_code: Optional[str] = None

class ZaloPayCallback(BaseModel):
    app_id: int
    app_trans_id: str
    app_time: int
    app_user: str
    amount: int
    embed_data: Dict[str, Any]
    item: str
    zp_trans_id: Optional[str] = None
    server_time: Optional[int] = None
    channel: Optional[int] = None
    merchant_user_id: Optional[str] = None
    user_fee_amount: Optional[int] = None
    discount_amount: Optional[int] = None