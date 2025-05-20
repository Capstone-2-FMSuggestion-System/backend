import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os
import json
import time
import inspect
from payos import PayOS, ItemData, PaymentData

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
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Khởi tạo PayOS client
payos_client = PayOS(
    client_id=PAYOS_CLIENT_ID,
    api_key=PAYOS_API_KEY,
    checksum_key=PAYOS_CHECKSUM_KEY
)

class PayOSError(Exception):
    """Custom exception for PayOS related errors"""
    pass

def verify_env() -> bool:
    """
    Verify that all required environment variables for PayOS are configured.
    """
    required_vars = [
        'PAYOS_CLIENT_ID',
        'PAYOS_API_KEY',
        'PAYOS_CHECKSUM_KEY',
        'FRONTEND_URL'
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

def create_payos_order(order_id: int, user_id: int, amount: float, items: list) -> Dict[str, Any]:
    """
    Create a new payment order on PayOS.
    
    Args:
        order_id (int): ID of the order in the system
        user_id (int): ID of the user making the payment
        amount (float): Amount to be paid
        items (list): List of items in the order
        
    Returns:
        Dict[str, Any]: PayOS order information including:
            + payment_url: Payment URL
            + order_code: Order code
            + status: Status code
            + message: Status message
    """
    logger.info(f"Creating PayOS order for order_id: {order_id}, user_id: {user_id}, amount: {amount}")
    start_time = time.time()
    
    # Validate input
    if amount <= 0:
        raise PayOSError("Amount must be greater than 0")
    if not items:
        raise PayOSError("Items list cannot be empty")
    
    try:
        # Chuyển định dạng items từ input thành ItemData của PayOS
        payos_items = []
        for item in items:
            payos_items.append(
                ItemData(
                    name=item["name"],
                    price=int(item["price"]), # Ensure price is integer for PayOS
                    quantity=item["quantity"]
                )
            )
        
        # Tạo mã đơn hàng duy nhất - sử dụng số nguyên thay vì chuỗi
        # Kết hợp order_id và timestamp để tạo số nguyên duy nhất
        # Ví dụ: nếu order_id = 123 và timestamp = 1690000000, 
        # orderCode = 1231690000000
        current_timestamp = int(time.time())
        # Tạo orderCode dưới dạng số nguyên bằng cách nối order_id và timestamp
        order_code = int(f"{order_id}{current_timestamp}")
        
        # Tạo PaymentData - Lưu ý: orderCode phải là số nguyên
        payment_data = PaymentData(
            orderCode=order_code,
            amount=int(amount),
            description=f"Payment for order #{order_id}",
            items=payos_items,
            cancelUrl=f"{FRONTEND_URL}/payment/cancel",
            returnUrl=f"{FRONTEND_URL}/payment/success",
            # Thêm thông tin khách hàng
            buyerName=f"Customer {user_id}",
            buyerEmail=f"customer{user_id}@example.com",
            buyerPhone="0123456789"
        )
        
        # Gọi API tạo payment link
        logger.info(f"Sending request to PayOS with data: {payment_data.to_json()}")
        # Lấy kết quả từ PayOS API - đây là một đối tượng CreatePaymentResult, không phải dict
        payment_result = payos_client.createPaymentLink(payment_data)
        
        # In ra log chi tiết về đối tượng payment_result
        logger.info(f"Payment result type: {type(payment_result)}")
        logger.info(f"Payment result dir: {dir(payment_result)}")
        
        # Thử chuyển đổi đối tượng thành dict bằng __dict__ nếu có
        if hasattr(payment_result, '__dict__'):
            logger.info(f"Payment result __dict__: {payment_result.__dict__}")
        
        # Chuyển đổi CreatePaymentResult thành dict để có thể JSON serialize
        response_data = {}
        
        # Kiểm tra từng thuộc tính dự kiến
        if hasattr(payment_result, 'checkoutUrl'):
            response_data["checkoutUrl"] = payment_result.checkoutUrl
        
        if hasattr(payment_result, 'orderCode'):
            response_data["orderCode"] = payment_result.orderCode
        
        if hasattr(payment_result, 'description'):
            response_data["description"] = payment_result.description
        else:
            response_data["description"] = "Success"
        
        # Ghi log đầy đủ kết quả tìm được
        logger.info(f"Extracted response data: {response_data}")
        
        logger.info(f"PayOS response: {json.dumps(response_data, indent=2)}")
        
        # Log response time
        response_time = time.time() - start_time
        logger.info(f"PayOS order created successfully. Response time: {response_time:.2f}s")
        
        # Chuyển đổi kết quả để tương thích với định dạng cũ
        result = {
            "payment_url": response_data.get("checkoutUrl"),
            "order_code": response_data.get("orderCode"),
            # Assuming success if no error, actual status might be in response_data.get("status") if API provides it
            "status": "success", 
            "message": response_data.get("description", "Success") 
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating PayOS order: {str(e)}")
        logger.error(f"Error details: {e}", exc_info=True)
        # Trả về lỗi theo định dạng cũ
        return {
            "payment_url": None,
            "order_code": None,
            "status": "error",
            "message": str(e)
        }

def verify_callback(webhook_body: Dict[str, Any]) -> bool:
    """
    Verify the validity of callback data from PayOS.
    
    Args:
        webhook_body (Dict[str, Any]): Dictionary containing callback data from PayOS
        
    Returns:
        bool: True if data is valid and unchanged, False if invalid
    """
    logger.info("Verifying PayOS callback data")
    try:
        # Sử dụng phương thức của PayOS library để xác thực webhook
        # The confirmWebhook method expects the webhook body as a dictionary
        is_valid = payos_client.verifyPaymentWebhookData(webhook_body)
        
        if not is_valid:
            logger.warning("Invalid checksum in callback or invalid webhook data structure")
        else:
            logger.info("Callback verification successful")
            
        return is_valid
        
    except Exception as e:
        logger.error(f"Error verifying callback: {str(e)}")
        return False

def query_order_status(order_code: str) -> Dict[str, Any]:
    """
    Query the status of an order from PayOS.
    
    Args:
        order_code (str): Order code from PayOS
        
    Returns:
        Dict[str, Any]: Order status information
    """
    logger.info(f"Querying order status for order_code: {order_code}")
    start_time = time.time()
    
    try:
        # Sử dụng phương thức của PayOS library để kiểm tra trạng thái
        # Cũng cần chuyển đổi kết quả thành dict tương tự như với createPaymentLink
        payment_info = payos_client.getPaymentLinkInformation(order_code)
        
        # In ra thông tin về đối tượng payment_info
        logger.info(f"Payment info type: {type(payment_info)}")
        logger.info(f"Payment info dir: {dir(payment_info)}")
        
        # Chuyển đổi kết quả thành dict
        response_data = {}
        
        # Kiểm tra từng thuộc tính dự kiến
        if hasattr(payment_info, 'status'):
            response_data["status"] = payment_info.status
        else:
            response_data["status"] = ""
            
        if hasattr(payment_info, 'description'):
            response_data["description"] = payment_info.description
        else:
            response_data["description"] = ""
            
        if hasattr(payment_info, 'amount'):
            response_data["amount"] = payment_info.amount
        else:
            response_data["amount"] = 0
            
        if hasattr(payment_info, 'checkoutUrl'):
            response_data["checkoutUrl"] = payment_info.checkoutUrl
        else:
            response_data["checkoutUrl"] = ""
            
        if hasattr(payment_info, 'createdAt'):
            response_data["createdAt"] = payment_info.createdAt
        else:
            response_data["createdAt"] = ""
            
        if hasattr(payment_info, 'updatedAt'):
            response_data["updatedAt"] = payment_info.updatedAt
        else:
            response_data["updatedAt"] = ""
        
        # Log response time
        response_time = time.time() - start_time
        logger.info(f"Order status query completed. Response time: {response_time:.2f}s")
        
        # Lấy trạng thái trực tiếp từ phản hồi API
        api_status = response_data.get("status", "").upper() # Ensure uppercase for consistency
        
        result = {
            "status": "success", # Indicates the API call was successful
            "data": {
                "order_code": order_code,
                "status": api_status, # Use the direct status from PayOS API
                "description": response_data.get("description", ""),
                "amount": response_data.get("amount", 0),
                "payment_url": response_data.get("checkoutUrl", ""),
                "created_at": response_data.get("createdAt", ""), # Assuming these fields exist
                "updated_at": response_data.get("updatedAt", "")  # Assuming these fields exist
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error querying order status: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

# Verify environment variables on module load
if not verify_env():
    logger.error("PayOS integration is not properly configured")