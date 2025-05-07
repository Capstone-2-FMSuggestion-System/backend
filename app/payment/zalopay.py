import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os
from payos import PayOS
from payos.type import PaymentData, ItemData

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Load config from .env
PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")
PAYOS_CALLBACK_URL = os.getenv("PAYOS_CALLBACK_URL")

# Verify environment variables
def verify_env() -> bool:
    """
    Kiểm tra các biến môi trường cần thiết cho PayOS.
    
    Returns:
        bool: True nếu tất cả biến môi trường tồn tại, False nếu thiếu bất kỳ biến nào
    """
    required_vars = [
        'PAYOS_CLIENT_ID',
        'PAYOS_API_KEY',
        'PAYOS_CHECKSUM_KEY',
        'PAYOS_CALLBACK_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("Environment variables verified successfully")
    return True

class PayOSError(Exception):
    """Custom exception for PayOS related errors"""
    pass

def create_payos_order(order_id: int, user_id: int, amount: float, items: list) -> Dict[str, Any]:
    """
    Tạo đơn hàng thanh toán mới trên PayOS.
    
    Args:
        order_id (int): ID của đơn hàng trong hệ thống
        user_id (int): ID của người dùng thực hiện thanh toán
        amount (float): Số tiền cần thanh toán
        items (list): Danh sách các mặt hàng trong đơn hàng
    
    Returns:
        Dict[str, Any]: Thông tin đơn hàng PayOS bao gồm:
            - checkoutUrl: URL thanh toán
            - paymentId: Mã giao dịch PayOS
            - qrCode: Mã QR (nếu có)
    
    Raises:
        PayOSError: Nếu có lỗi trong quá trình tạo đơn hàng
    """
    logger.info(f"Creating PayOS order for order_id: {order_id}, user_id: {user_id}, amount: {amount}")
    start_time = time.time()
    
    try:
        # Validate input
        if amount <= 0:
            raise PayOSError("Amount must be greater than 0")
        if not items:
            raise PayOSError("Items list cannot be empty")
        
        # Initialize PayOS client
        payos = PayOS(
            client_id=PAYOS_CLIENT_ID,
            api_key=PAYOS_API_KEY,
            checksum_key=PAYOS_CHECKSUM_KEY
        )
        
        # Prepare items for PayOS
        payos_items = [
            ItemData(
                name=item.get("name", "Unknown"),
                quantity=item.get("quantity", 1),
                price=int(item.get("price", 0))
            )
            for item in items
        ]
        
        # Create payment data
        payment_data = PaymentData(
            orderCode=order_id,
            amount=int(amount),
            description=f"Payment for order {order_id}"[:25],
            items=payos_items,
            cancelUrl=f"{PAYOS_CALLBACK_URL}/cancel",
            returnUrl=f"{PAYOS_CALLBACK_URL}/return"
        )
        
        # Create payment link
        payment_link = payos.createPaymentLink(paymentData=payment_data)
        
        # Log response time
        response_time = time.time() - start_time
        logger.info(f"PayOS order created successfully. Response time: {response_time:.2f}s")
        
        return {
            "checkoutUrl": payment_link.checkoutUrl,
            "paymentId": payment_link.paymentId,
            "qrCode": payment_link.qrCode
        }
        
    except Exception as e:
        logger.error(f"Error creating PayOS order: {str(e)}")
        raise PayOSError(str(e))

def verify_callback(data: Dict[str, Any]) -> bool:
    """
    Xác thực tính hợp lệ của dữ liệu callback từ PayOS.
    
    Args:
        data (Dict[str, Any]): Dictionary chứa dữ liệu callback từ PayOS
    
    Returns:
        bool: True nếu dữ liệu hợp lệ, False nếu không hợp lệ
    """
    logger.info("Verifying PayOS callback data")
    try:
        # Verify required fields
        required_fields = ["paymentId", "orderCode", "amount", "status"]
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Verify payment status
        if data["status"] not in ["PAID", "CANCELLED", "FAILED"]:
            logger.error(f"Invalid payment status: {data['status']}")
            return False
        
        logger.info("Callback verification successful")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying callback: {str(e)}")
        return False

def query_payment_status(payment_id: str) -> Dict[str, Any]:
    """
    Truy vấn trạng thái đơn hàng từ PayOS.
    
    Args:
        payment_id (str): Mã giao dịch PayOS
    
    Returns:
        Dict[str, Any]: Thông tin trạng thái đơn hàng
    
    Raises:
        PayOSError: Nếu có lỗi trong quá trình truy vấn
    """
    logger.info(f"Querying payment status for payment_id: {payment_id}")
    start_time = time.time()
    
    try:
        # Initialize PayOS client
        payos = PayOS(
            client_id=PAYOS_CLIENT_ID,
            api_key=PAYOS_API_KEY,
            checksum_key=PAYOS_CHECKSUM_KEY
        )
        
        # Query payment status
        payment_info = payos.getPaymentInfo(payment_id)
        
        # Log response time
        response_time = time.time() - start_time
        logger.info(f"Payment status query completed. Response time: {response_time:.2f}s")
        
        return {
            "paymentId": payment_info.paymentId,
            "orderCode": payment_info.orderCode,
            "amount": payment_info.amount,
            "status": payment_info.status,
            "createdAt": payment_info.createdAt,
            "updatedAt": payment_info.updatedAt
        }
        
    except Exception as e:
        logger.error(f"Error querying payment status: {str(e)}")
        raise PayOSError(str(e))

# Verify environment variables on module load
if not verify_env():
    logger.error("PayOS integration is not properly configured") 