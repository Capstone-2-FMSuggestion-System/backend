from sqlalchemy.orm import Session
from typing import Optional, List
from .models import Payments, Orders
from .schemas import PaymentCreate, PaymentUpdate

def create_payment(db: Session, payment: PaymentCreate) -> Payments:
    """
    Tên Function: create_payment
    
    1. Mô tả ngắn gọn:
    Tạo một giao dịch thanh toán mới.
    
    2. Mô tả công dụng:
    Tạo một bản ghi thanh toán mới trong cơ sở dữ liệu cho một đơn hàng.
    Ghi lại thông tin về phương thức thanh toán, số tiền và trạng thái ban đầu
    là "pending" (đang chờ).
    """
    db_payment = Payments(
        order_id=payment.order_id,
        amount=payment.amount,
        method=payment.method,
        status="pending"
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def update_payment_status(db: Session, payment_id: int, status: str, zp_trans_id: Optional[str] = None) -> Optional[Payments]:
    """
    Tên Function: update_payment_status
    
    1. Mô tả ngắn gọn:
    Cập nhật trạng thái thanh toán và mã giao dịch ZaloPay.
    
    2. Mô tả công dụng:
    Cập nhật trạng thái và mã giao dịch của một thanh toán trong cơ sở dữ liệu.
    Thường được sử dụng sau khi nhận được phản hồi từ cổng thanh toán ZaloPay
    để cập nhật trạng thái giao dịch (thành công, thất bại, etc.).
    """
    db_payment = db.query(Payments).filter(Payments.payment_id == payment_id).first()
    if not db_payment:
        return None
    
    db_payment.status = status
    if zp_trans_id:
        db_payment.zp_trans_id = zp_trans_id
    
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_payment(db: Session, payment_id: int) -> Optional[Payments]:
    """
    Tên Function: get_payment
    
    1. Mô tả ngắn gọn:
    Lấy thông tin giao dịch thanh toán theo ID.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy thông tin chi tiết của một giao dịch thanh toán
    dựa trên ID. Thường được sử dụng khi cần kiểm tra thông tin hoặc trạng thái
    của một giao dịch thanh toán cụ thể.
    """
    return db.query(Payments).filter(Payments.payment_id == payment_id).first()

def get_payment_by_order(db: Session, order_id: int) -> Optional[Payments]:
    """
    Tên Function: get_payment_by_order
    
    1. Mô tả ngắn gọn:
    Lấy thông tin thanh toán theo ID đơn hàng.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy thông tin thanh toán của một đơn hàng cụ thể.
    Thường được sử dụng khi cần kiểm tra trạng thái thanh toán của đơn hàng
    hoặc để xác nhận xem đơn hàng đã được thanh toán chưa.
    """
    return db.query(Payments).filter(Payments.order_id == order_id).first() 