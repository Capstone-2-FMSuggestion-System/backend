import requests
import hashlib
import hmac
import json
import os
from app.core.config import settings 

PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")
PAYOS_API_URL = os.getenv("PAYOS_API_URL", "https://payosapi.com/transaction")

class PayOS:
    def __init__(self, client_id, api_key, checksum_key):
        self.client_id = client_id
        self.api_key = api_key
        self.checksum_key = checksum_key
        self.api_url = settings.PAYOS_API_URL

    def calculate_checksum(self, data: dict):
        sorted_data = sorted(data.items())
        query_string = '&'.join(f"{key}={value}" for key, value in sorted_data)
        query_string += f"&key={self.checksum_key}"
        return hashlib.sha256(query_string.encode()).hexdigest()

    def create_payment_link(self, payload: dict):
        checksum = self.calculate_checksum(payload)
        payload['checksum'] = checksum
        response = requests.post(self.api_url, json=payload, headers={"x-client-id": self.client_id, "x-api-key": self.api_key})
        return response.json()