import hmac
import hashlib
import time
import urllib.request
import urllib.parse
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os
import requests

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
        'PAYOS_CHECKSUM_KEY'
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
    
    # Prepare order data
    order = {
        "client_id": PAYOS_CLIENT_ID,
        "order_code": f"ORDER_{order_id}_{int(time.time())}",
        "amount": int(amount * 100),  # Convert to smallest currency unit
        "description": f"Payment for order #{order_id}",
        "cancel_url": f"{os.getenv('FRONTEND_URL')}/payment/cancel",
        "return_url": f"{os.getenv('FRONTEND_URL')}/payment/success",
        "items": items,
        "customer": {
            "user_id": str(user_id)
        }
    }

    # Create checksum
    data_str = json.dumps(order, sort_keys=True)
    checksum = hmac.new(
        PAYOS_CHECKSUM_KEY.encode('utf-8'),
        data_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Add checksum to headers
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': PAYOS_API_KEY,
        'x-checksum': checksum
    }

    # Send request to PayOS
    try:
        logger.info(f"Sending request to PayOS with data: {json.dumps(order, indent=2)}")
        logger.info(f"Request headers: {json.dumps(headers, indent=2)}")
        
        response = requests.post(
            "https://api-sandbox.payos.vn/v2/payment-requests",
            json=order,
            headers=headers,
            timeout=10
        )
        
        logger.info(f"PayOS response status: {response.status_code}")
        logger.info(f"PayOS response headers: {dict(response.headers)}")
        
        try:
            result = response.json()
            logger.info(f"PayOS response body: {json.dumps(result, indent=2)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse PayOS response: {response.text}")
            raise PayOSError(f"Invalid JSON response from PayOS: {str(e)}")
        
        # Log response time
        response_time = time.time() - start_time
        logger.info(f"PayOS order created successfully. Response time: {response_time:.2f}s")
        
        if result.get("status") != "success":
            error_msg = result.get("message", "Unknown error")
            logger.error(f"PayOS order creation failed: {error_msg}")
            raise PayOSError(error_msg)
            
        return result
        
    except requests.exceptions.Timeout:
        logger.error("Request to PayOS timed out")
        raise PayOSError("Request to PayOS timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while creating PayOS order: {str(e)}")
        raise PayOSError(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while creating PayOS order: {str(e)}")
        raise PayOSError(str(e))

def verify_callback(data: Dict[str, Any]) -> bool:
    """
    Verify the validity of callback data from PayOS.
    
    Args:
        data (Dict[str, Any]): Dictionary containing callback data from PayOS
        
    Returns:
        bool: True if data is valid and unchanged, False if invalid
    """
    logger.info("Verifying PayOS callback data")
    try:
        received_checksum = data.get("checksum")
        data_str = json.dumps(data.get("data", {}), sort_keys=True)
        
        if not received_checksum or not data_str:
            logger.error("Missing checksum or data in callback")
            return False
        
        # Compute checksum for verification
        computed_checksum = hmac.new(
            PAYOS_CHECKSUM_KEY.encode('utf-8'),
            data_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        is_valid = received_checksum == computed_checksum
        if not is_valid:
            logger.warning("Invalid checksum in callback")
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
        # Prepare request data
        data = {
            "client_id": PAYOS_CLIENT_ID,
            "order_code": order_code
        }
        
        data_str = json.dumps(data, sort_keys=True)
        checksum = hmac.new(
            PAYOS_CHECKSUM_KEY.encode('utf-8'),
            data_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Add checksum to headers
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': PAYOS_API_KEY,
            'x-checksum': checksum
        }

        # Send request to PayOS
        req = urllib.request.Request(
            url="https://api-sandbox.payos.vn/v2/payment-requests/status",
            data=data_str.encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        
        # Log response time
        response_time = time.time() - start_time
        logger.info(f"Order status query completed. Response time: {response_time:.2f}s")
        
        if result.get("status") != "success":
            logger.error(f"Order status query failed: {result.get('message')}")
            raise PayOSError(result.get("message"))
            
        return result
        
    except urllib.error.URLError as e:
        logger.error(f"Network error while querying order status: {str(e)}")
        raise PayOSError(f"Network error: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from PayOS: {str(e)}")
        raise PayOSError(f"Invalid response format: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while querying order status: {str(e)}")
        raise PayOSError(str(e))

# Verify environment variables on module load
if not verify_env():
    logger.error("PayOS integration is not properly configured")