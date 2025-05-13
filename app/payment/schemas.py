from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class PaymentCreate(BaseModel):
    order_id: int
    amount: Decimal
    method: str

class PaymentResponse(BaseModel):
    payment_url: str
