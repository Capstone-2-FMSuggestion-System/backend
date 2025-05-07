from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from ..core.database import get_db
from .models import Payments
from ..e_commerce.models import Orders, OrderItems, Product
from .schemas import (
    PaymentCreate, PaymentResponse, PaymentMethod,
    PayOSPaymentRequest, OrderDetailsResponse, PayOSCallbackData
)
from .crud import (
    create_payment, get_payment_by_order, update_payment_status,
    get_payment_by_transaction
)
from payos import PayOS
from payos.type import PaymentData, ItemData
import logging
from pydantic import BaseModel
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize PayOS client
payOS = PayOS(
    client_id="8beadbae-a0e7-4923-b5e9-f49fcadd3ca4",
    api_key="760cfb21-3d78-428e-b556-3a41060d8a42",
    checksum_key="43588c53ec34ac56749988368dbdac4c7fed5f512aafc1941c61da712ecef7a9"
)

router = APIRouter(prefix="/api/payments", tags=["Payments"])

class PaymentRequest(BaseModel):
    amount: Decimal
    shipping_address_id: Optional[int] = None

class OrderItemResponse(BaseModel):
    product_name: str
    quantity: int
    price: str

class OrderDetailsResponse(BaseModel):
    order_id: int
    total: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

@router.get("/payos/{user_id}/{order_id}", response_model=OrderDetailsResponse)
async def get_payos_payment_details(
    user_id: int,
    order_id: int,
    db: Session = Depends(get_db)
):
    """
    Get payment details for an order.
    """
    order = db.query(Orders).filter(
        Orders.order_id == order_id,
        Orders.user_id == user_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or not in valid status.")
    
    order_items = db.query(OrderItems).filter(OrderItems.order_id == order_id).all()
    items = []
    for item in order_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        items.append(OrderItemResponse(
            product_name=product.name if product else "Unknown",
            quantity=item.quantity,
            price=str(item.price)
        ))
    
    return OrderDetailsResponse(
        order_id=order.order_id,
        total=order.total_amount,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=items
    )

@router.post("/payos/{user_id}/{order_id}", response_model=dict)
async def create_payos_payment(
    user_id: int,
    order_id: int,
    payment_request: PayOSPaymentRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new PayOS payment for an order.
    """
    # Get order details
    order = db.query(Orders).filter(
        Orders.order_id == order_id,
        Orders.user_id == user_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or not in valid status.")

    # Check for existing payment
    existing_payment = get_payment_by_order(db=db, order_id=order_id)
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment already exists for this order.")

    # Prepare order items
    order_items = db.query(OrderItems).filter(OrderItems.order_id == order_id).all()
    items: List[ItemData] = []
    for item in order_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        items.append(ItemData(
            name=product.name if product else "Unknown",
            quantity=item.quantity,
            price=int(item.price)
        ))

    # Create payment data
    payment_data = PaymentData(
        orderCode=order.order_id,
        amount=int(payment_request.amount),
        description=f"Payment for order {order.order_id}"[:25],
        items=items,
        cancelUrl="http://localhost:8000/cancel",
        returnUrl="http://localhost:8000/return"
    )

    try:
        # Create payment link
        payment_link = payOS.createPaymentLink(paymentData=payment_data)

        # Create payment record
        payment = PaymentCreate(
            order_id=order.order_id,
            amount=float(payment_request.amount),
            method=PaymentMethod.PAYOS,
            status="pending"
        )
        db_payment = create_payment(db=db, payment=payment)

        logger.info(f"Payment created successfully for order {order.order_id}")

        return {
            "payment_url": payment_link.checkoutUrl,
            "payment_id": db_payment.payment_id
        }
    except Exception as e:
        logger.error(f"Payment processing failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment processing failed: {str(e)}")

@router.post("/payos/callback")
async def payos_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle PayOS payment callback.
    """
    try:
        callback_data = await request.json()
        logger.info(f"Received PayOS callback: {callback_data}")

        # Verify callback data
        payment_id = callback_data.get("paymentId")
        if not payment_id:
            raise HTTPException(status_code=400, detail="Invalid callback data")

        # Get payment record
        payment = get_payment_by_transaction(db=db, transaction_id=payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Update payment status
        status = "completed" if callback_data.get("status") == "PAID" else "failed"
        update_payment_status(
            db=db,
            payment_id=payment.payment_id,
            status=status,
            payment_data=callback_data
        )

        # Process payment in background
        background_tasks.add_task(process_payment_completion, payment.payment_id, status, db)

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing PayOS callback: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def process_payment_completion(payment_id: int, status: str, db: Session):
    """
    Process payment completion in background.
    """
    try:
        payment = get_payment(db=db, payment_id=payment_id)
        if not payment:
            logger.error(f"Payment {payment_id} not found")
            return

        if status == "completed":
            # Update order status
            order = db.query(Orders).filter(Orders.order_id == payment.order_id).first()
            if order:
                order.status = "paid"
                db.commit()
                logger.info(f"Updated order {order.order_id} status to paid")
    except Exception as e:
        logger.error(f"Error processing payment completion: {str(e)}")
        db.rollback()