from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.auth import get_current_user
from ..core.invalidation_helpers import invalidate_dashboard_cache
from .models import User, Orders, Payments
from ..e_commerce.models import Product
from ..e_commerce.schemas import OrderCreate
from .schemas import PaymentCreate, PaymentMethod
from .crud import create_payment, update_payment_status
from ..e_commerce.crud import create_order, update_order_status
from . import payos
import json
import ipaddress
import random
from datetime import datetime
import logging

router = APIRouter(prefix="/api/payments", tags=["Payments"])

@router.post("/payos/create")
async def create_payos_payment(order: OrderCreate, db: Session = Depends(get_db)):
    # Create order in database
    db_order = create_order(db, order)
    if not db_order:
        raise HTTPException(status_code=400, detail="Could not create order")

    # Chỉ lấy items, không dùng cart_items
    items = []
    for item in order.items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        if product:
            items.append({
                "id": str(product.product_id),
                "name": product.name,
                "price": float(product.price),
                "quantity": item.quantity
            })

    # Validate tổng tiền
    item_total = sum(float(i["price"]) * int(i["quantity"]) for i in items)
    if int(order.total_amount) != int(item_total):
        raise HTTPException(status_code=400, detail=f"Tổng tiền không khớp: {order.total_amount} vs {item_total}")

    # Call PayOS to create order
    response = payos.create_payos_order(
        order_id=db_order.order_id,
        user_id=order.user_id,
        amount=float(db_order.total_amount),
        items=items
    )

    # Check PayOS response
    if response.get("status") != "success":
        raise HTTPException(status_code=400, detail=response.get("message", "Could not create PayOS order"))

    # Create payment record
    payment_data = PaymentCreate(
        order_id=db_order.order_id,
        amount=float(db_order.total_amount),
        method="payos"
    )
    db_payment = create_payment(db=db, payment=payment_data)

    # Update order code if exists
    if response.get("order_code"):
        update_payment_status(
            db=db, 
            payment_id=db_payment.payment_id, 
            status="pending", 
            zp_trans_id=response.get("order_code")
        )

    # Invalidate dashboard cache to reflect new order
    await invalidate_dashboard_cache()
    logging.info(f"Dashboard cache invalidated after creating order {db_order.order_id}")

    return {
        "payment_url": response.get("payment_url"),
        "order_code": response.get("order_code"),
        "status": response.get("status"),
        "message": response.get("message")
    }

@router.post("/payos/callback")
async def payos_callback(request: Request, db: Session = Depends(get_db)):
    # Get the raw request body
    body = await request.json()
    
    # Verify callback signature
    if not payos.verify_callback(body):
        return {"status": "error", "message": "Invalid signature"}

    try:
        # Parse callback data
        data = body.get("data", {})
        order_code = data.get("order_code")
        status = data.get("status")
        
        # Find payment by order_code (saved in zp_trans_id field)
        db_payment = db.query(Payments).filter(Payments.zp_trans_id == order_code).first()
        if not db_payment:
            return {"status": "error", "message": "Payment not found"}
            
        # Get order
        db_order = db.query(Orders).filter(Orders.order_id == db_payment.order_id).first()
        if not db_order:
            return {"status": "error", "message": "Order not found"}

        # Update order status
        db_order = update_order_status(db, order_id=db_order.order_id, status="completed")
        
        # Update payment status
        update_payment_status(db, payment_id=db_payment.payment_id, status="completed", zp_trans_id=order_code)
        
        # Invalidate dashboard cache when order is completed
        await invalidate_dashboard_cache()
        logging.info(f"Dashboard cache invalidated after completing order {db_order.order_id}")

        return {"status": "success", "message": "Callback processed successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/payos/status/{order_code}")
async def check_payos_status(order_code: str):
    response = payos.query_order_status(order_code)
    return response

@router.get("/payment-methods")
async def get_payment_methods():
    """
    Get available payment methods with descriptions
    """
    payment_methods = [
        {
            "id": PaymentMethod.COD.value,
            "name": "Thanh toán khi nhận hàng",
            "description": "Thanh toán tiền mặt khi nhận hàng",
            "icon_url": "https://example.com/cod-icon.svg"
        },
        {
            "id": "payos",
            "name": "PayOS",
            "description": "Thanh toán trực tuyến qua PayOS",
            "icon_url": "https://payos.vn/assets/images/logo.svg"
        }
    ]
    
    return {"payment_methods": payment_methods}

@router.post("/cod/create")
async def create_cod_payment(order: OrderCreate, db: Session = Depends(get_db)):
    # Create order in database
    db_order = create_order(db, order)
    if not db_order:
        raise HTTPException(status_code=400, detail="Could not create order")

    # Create payment record for COD
    payment_data = PaymentCreate(
        order_id=db_order.order_id,
        amount=float(db_order.total_amount),
        method="COD",
        status="pending"
    )
    
    db_payment = create_payment(db=db, payment=payment_data)
    
    # Invalidate dashboard cache to reflect new order
    await invalidate_dashboard_cache()
    logging.info(f"Dashboard cache invalidated after creating COD order {db_order.order_id}")

    # Trả về toàn bộ thông tin đơn hàng vừa tạo
    return {
        "order_id": db_order.order_id,
        "user_id": db_order.user_id,
        "total_amount": float(db_order.total_amount),
        "status": db_order.status,
        "payment_method": db_order.payment_method,
        "created_at": db_order.created_at,
        "updated_at": db_order.updated_at,
        "recipient_name": db_order.recipient_name,
        "recipient_phone": db_order.recipient_phone,
        "shipping_address": db_order.shipping_address,
        "shipping_city": db_order.shipping_city,
        "shipping_province": db_order.shipping_province,
        "shipping_postal_code": db_order.shipping_postal_code,
        "payment_id": db_payment.payment_id
    }