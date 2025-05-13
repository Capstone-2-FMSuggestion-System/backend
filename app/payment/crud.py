from sqlalchemy.orm import Session
from . import models, schemas

def create_payment(db: Session, payment: schemas.PaymentCreate) -> models.Payments:
    db_payment = models.Payments(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_payment_by_order(db: Session, order_id: int):
    return db.query(models.Payments).filter(models.Payments.order_id == order_id).first()

def update_payment_status(db: Session, order_id: int, status: str, transaction_id: str = None):
    payment = db.query(models.Payments).filter(models.Payments.order_id == order_id).first()
    if payment:
        payment.status = status
        if transaction_id:
            payment.transaction_id = transaction_id
        db.commit()
        db.refresh(payment)
        return payment
    return None
