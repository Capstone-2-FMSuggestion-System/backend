from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from .models import Payments, Orders
from .schemas import PaymentCreate, PaymentUpdate, PaymentMethod
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_payment(db: Session, payment: PaymentCreate) -> Payments:
    """
    Create a new payment record.
    """
    try:
        db_payment = Payments(
            order_id=payment.order_id,
            amount=payment.amount,
            method=payment.method,
            status="pending",
            transaction_id=payment.transaction_id
        )
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        logger.info(f"Created payment record for order {payment.order_id}")
        return db_payment
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating payment: {str(e)}")
        raise

def update_payment_status(
    db: Session, 
    payment_id: int, 
    status: str, 
    transaction_id: Optional[str] = None,
    payment_data: Optional[Dict[str, Any]] = None
) -> Optional[Payments]:
    """
    Update payment status and related information.
    """
    try:
        db_payment = db.query(Payments).filter(Payments.payment_id == payment_id).first()
        if not db_payment:
            return None
        
        db_payment.status = status
        if transaction_id:
            db_payment.transaction_id = transaction_id
        if payment_data:
            db_payment.payment_data = payment_data
        db_payment.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_payment)
        logger.info(f"Updated payment {payment_id} status to {status}")
        return db_payment
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating payment status: {str(e)}")
        raise

def get_payment(db: Session, payment_id: int) -> Optional[Payments]:
    """
    Get payment by ID.
    """
    return db.query(Payments).filter(Payments.payment_id == payment_id).first()

def get_payment_by_order(db: Session, order_id: int) -> Optional[Payments]:
    """
    Get payment by order ID.
    """
    return db.query(Payments).filter(Payments.order_id == order_id).first()

def get_payment_by_transaction(db: Session, transaction_id: str) -> Optional[Payments]:
    """
    Get payment by transaction ID.
    """
    return db.query(Payments).filter(Payments.transaction_id == transaction_id).first()

def get_payments_by_status(db: Session, status: str) -> List[Payments]:
    """
    Get all payments with specific status.
    """
    return db.query(Payments).filter(Payments.status == status).all()

def get_payments_by_method(db: Session, method: str) -> List[Payments]:
    """
    Get all payments with specific payment method.
    """
    return db.query(Payments).filter(Payments.method == method).all()