from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .schemas import PaymentCreate, PaymentResponse
from .crud import create_payment, get_payment_by_order
from .models import Orders
from app.core.database import get_db
from .payos import PayOS
from app.core.config import settings

router = APIRouter()

payos = PayOS(
    client_id=settings.PAYOS_CLIENT_ID,
    api_key=settings.PAYOS_API_KEY,
    checksum_key=settings.PAYOS_CHECKSUM_KEY
)

@router.post("/payments", response_model=PaymentResponse)
def create_payment_link(payment_data: PaymentCreate, db: Session = Depends(get_db)):
    order = db.query(Orders).filter(Orders.order_id == payment_data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    existing = get_payment_by_order(db, payment_data.order_id)
    if existing:
        raise HTTPException(status_code=400, detail="Payment already exists")

    payload = {
        "orderCode": payment_data.order_id,
        "amount": int(payment_data.amount),
        "description": f"Thanh toan don hang {payment_data.order_id}",
        "cancelUrl": "http://localhost:8000/cancel",
        "returnUrl": "http://localhost:8000/return"
    }
    result = payos.create_payment_link(payload)
    
    create_payment(db, payment=payment_data)
    return {"payment_url": result.get("checkoutUrl")}