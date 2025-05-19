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
        "client_id": PAYOS_CLIENT_ID,
        "order_code": f"TEST_ORDER_{int(time.time())}",
        "amount": 10000,  # 100 VND
        "description": "Test order",
        "cancel_url": "http://localhost:3000/payment/cancel",
        "return_url": "http://localhost:3000/payment/success",
        "items": [
            {
                "name": "Test Item",
                "quantity": 1,
                "price": 10000
            }
        ],
        "customer": {
            "user_id": "test_user"
        }
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

    print("\n=== Request Details ===")
    print(f"URL: https://api-sandbox.payos.vn/v2/payment-requests")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Payload: {json.dumps(test_order, indent=2)}")

    try:
        # Send request
        print("\n=== Sending Request ===")
        response = requests.post(
            "https://api-sandbox.payos.vn/v2/payment-requests",
            json=test_order,
            headers=headers,
            timeout=30,
            verify=True
        )

        print(f"\n=== Response Details ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            result = response.json()
            print(f"Response Body: {json.dumps(result, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {response.text}")
            print(f"Error: {str(e)}")

    except requests.exceptions.Timeout:
        print("\nError: Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"\nError: Network error - {str(e)}")
    except Exception as e:
        print(f"\nError: Unexpected error - {str(e)}")

if __name__ == "__main__":
    test_payos_connection() 