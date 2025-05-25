import os
import json
import hmac
import hashlib
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get PayOS credentials
PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")

def test_payos_connection():
    print("\n=== Testing PayOS Connection ===")
    print(f"Client ID: {PAYOS_CLIENT_ID}")
    print(f"API Key: {PAYOS_API_KEY[:5]}...{PAYOS_API_KEY[-5:]}")
    print(f"Checksum Key: {PAYOS_CHECKSUM_KEY[:5]}...{PAYOS_CHECKSUM_KEY[-5:]}")

    # Test data
    test_order = {
        "clientId": PAYOS_CLIENT_ID,
        "orderCode": f"TEST_ORDER_{int(time.time())}",
        "amount": 10000,  # 10.000 VND
        "description": "Test order",
        "cancelUrl": "http://localhost:3000/payment/cancel",
        "returnUrl": "http://localhost:3000/payment/success",
        "items": [
            {
                "name": "Test Item",
                "quantity": 1,
                "price": 10000
            }
        ]
    }

    # Create checksum
    data_str = json.dumps(test_order, sort_keys=True)
    checksum = hmac.new(
        PAYOS_CHECKSUM_KEY.encode('utf-8'),
        data_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Headers
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': PAYOS_API_KEY,
        'x-checksum': checksum
    }

    # Thử kết nối với API sandbox
    print("\n=== Testing SANDBOX API ===")
    test_sandbox(test_order, headers)
    
    # Thử kết nối với API production
    print("\n=== Testing PRODUCTION API ===")
    test_production(test_order, headers)

def test_sandbox(test_order, headers):
    try:
        print(f"Sending request to Sandbox URL: https://api-sandbox.payos.vn/v2/payment-requests")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Payload: {json.dumps(test_order, indent=2)}")

        response = requests.post(
            "https://api-sandbox.payos.vn/v2/payment-requests",
            json=test_order,
            headers=headers,
            timeout=30,
            verify=True
        )

        print(f"Status Code: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        except:
            print(f"Response (text): {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def test_production(test_order, headers):
    try:
        print(f"Sending request to Production URL: https://api-merchant.payos.vn/v2/payment-requests")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Payload: {json.dumps(test_order, indent=2)}")

        response = requests.post(
            "https://api-merchant.payos.vn/v2/payment-requests",
            json=test_order,
            headers=headers,
            timeout=30,
            verify=True
        )

        print(f"Status Code: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        except:
            print(f"Response (text): {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_payos_connection() 