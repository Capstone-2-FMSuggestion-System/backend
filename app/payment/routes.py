from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.auth import get_current_user
from ..core.invalidation_helpers import invalidate_dashboard_cache
from .models import User, Orders, Payments
from ..e_commerce.models import Product
from ..e_commerce.schemas import OrderCreate
from .schemas import ZaloPayOrderResponse, ZaloPayCallback, PaymentCreate, PaymentMethod
from .crud import create_payment, update_payment_status
from ..e_commerce.crud import create_order, update_order_status
from . import zalopay
import json
import ipaddress
import random
from datetime import datetime
import logging

router = APIRouter(prefix="/api/payments", tags=["Payments"])

@router.post("/zalopay/create", response_model=ZaloPayOrderResponse)
async def create_zalopay_payment(order: OrderCreate, payment_method: PaymentMethod = PaymentMethod.ZALOPAY_APP, db: Session = Depends(get_db)):
    # Create order in database
    db_order = create_order(db, order)
    if not db_order:
        raise HTTPException(status_code=400, detail="Could not create order")

    # Prepare items for ZaloPay
    items = []
    for item in order.cart_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        if product:
            items.append({
                "id": str(product.product_id),
                "name": product.name,
                "price": float(product.price),
                "quantity": item.quantity
            })

    # Call ZaloPay to create order with specified payment method
    response = zalopay.create_zalopay_order(
        order_id=db_order.order_id,
        user_id=order.user_id,
        amount=float(db_order.total_amount),
        items=items,
        payment_method=payment_method.value
    )

    # Check ZaloPay response
    if response.get("return_code") != 1:
        raise HTTPException(status_code=400, detail=response.get("return_message", "Could not create ZaloPay order"))

    # Tạo đối tượng PaymentCreate
    payment_data = PaymentCreate(
        order_id=db_order.order_id,
        amount=float(db_order.total_amount),
        method=f"zalopay_{payment_method.value}"
    )
    
    # Gọi hàm create_payment với đối tượng PaymentCreate
    db_payment = create_payment(db=db, payment=payment_data)
    
    # Cập nhật zp_trans_id nếu có
    if response.get("zp_trans_id"):
        update_payment_status(
            db=db, 
            payment_id=db_payment.payment_id, 
            status="pending", 
            zp_trans_id=response.get("zp_trans_id")
        )

    # Lấy app_trans_id từ response hoặc tạo mới nếu không có
    app_trans_id = response.get("app_trans_id")
    
    # Nếu không có app_trans_id trong response, tạo một giá trị mặc định
    if not app_trans_id:
        # Tạo app_trans_id theo định dạng yyMMdd_xxxxxx
        trans_id = random.randrange(1000000)
        app_trans_id = "{:%y%m%d}_{}".format(datetime.now(), trans_id)
        logging.warning(f"app_trans_id not found in ZaloPay response, using generated value: {app_trans_id}")

    # Invalidate dashboard cache to reflect new order
    await invalidate_dashboard_cache()
    logging.info(f"Dashboard cache invalidated after creating order {db_order.order_id}")

    return {
        "order_url": response.get("order_url"),
        "zp_trans_id": response.get("zp_trans_id"),
        "app_trans_id": app_trans_id,
        "payment_method": payment_method
    }

@router.post("/zalopay/callback")
async def zalopay_callback(callback_data: ZaloPayCallback, request: Request, db: Session = Depends(get_db)):
    # Verify callback signature
    if not zalopay.verify_callback(callback_data.dict()):
        return {"return_code": -1, "return_message": "mac not equal"}

    try:
        # Parse callback data
        data = json.loads(callback_data.data)
        app_trans_id = data.get("app_trans_id")
        zp_trans_id = data.get("zp_trans_id")
        embed_data = json.loads(data.get("embed_data", "{}"))
        order_id = embed_data.get("order_id")

        # Update order status
        db_order = update_order_status(db, order_id=order_id, status="completed")
        if not db_order:
            return {"return_code": 0, "return_message": "Order not found"}

        # Update payment status
        db_payment = db.query(Payments).filter(Payments.order_id == order_id).first()
        if db_payment:
            update_payment_status(db, payment_id=db_payment.payment_id, status="completed", zp_trans_id=zp_trans_id)
        
        # Invalidate dashboard cache when order is completed
        await invalidate_dashboard_cache()
        logging.info(f"Dashboard cache invalidated after completing order {order_id}")

        print(f"update order's status = success where app_trans_id = {app_trans_id}")
        return {"return_code": 1, "return_message": "success"}
    except Exception as e:
        return {"return_code": 0, "return_message": str(e)}

@router.get("/zalopay/status/{app_trans_id}")
async def check_zalopay_status(app_trans_id: str):
    response = zalopay.query_order_status(app_trans_id)
    return response

@router.get("/payment-methods")
async def get_payment_methods():
    """
    Get available payment methods with descriptions
    """
    payment_methods = [
        {
            "id": PaymentMethod.COD.value,
            "name": "Cash on Delivery",
            "description": "Pay when you receive the items",
            "icon_url": "https://example.com/cod-icon.svg"
        },
        {
            "id": PaymentMethod.ZALOPAY_APP.value,
            "name": "ZaloPay App",
            "description": "Pay directly with ZaloPay app",
            "icon_url": "https://zalopay.vn/assets/images/logo.svg"
        },
        {
            "id": PaymentMethod.ATM.value,
            "name": "ATM Card",
            "description": "Pay with ATM card (domestic bank cards)",
            "icon_url": "https://zalopay.vn/assets/images/atm-icon.svg"
        },
        {
            "id": PaymentMethod.CREDIT_CARD.value,
            "name": "Credit Card",
            "description": "Pay with Visa, Mastercard, JCB",
            "icon_url": "https://zalopay.vn/assets/images/cc-icon.svg"
        },
        {
            "id": PaymentMethod.QR_CODE.value,
            "name": "QR Code",
            "description": "Scan QR code to pay",
            "icon_url": "https://zalopay.vn/assets/images/qr-icon.svg"
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

    return {
        "order_id": db_order.order_id,
        "payment_id": db_payment.payment_id,
        "amount": float(db_order.total_amount),
        "status": "pending"
    }