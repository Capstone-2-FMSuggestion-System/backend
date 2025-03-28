from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 404  # Root path not defined

def test_register_user():
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 200
    assert "token" in response.json()
    assert "user_id" in response.json()

def test_login():
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    assert "token" in response.json()
    assert "user_id" in response.json()
    assert "role" in response.json()

def test_create_zalopay_order():
    # First login to get token
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    token = login_response.json()["token"]
    
    # Create order
    response = client.post(
        "/api/payments/zalopay/create",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": 1,
            "cart_items": [
                {
                    "product_id": 1,
                    "quantity": 2
                }
            ],
            "payment_method": "zalopay"
        }
    )
    assert response.status_code == 200
    assert "order_url" in response.json()
    assert "app_trans_id" in response.json()

def test_check_zalopay_status():
    response = client.get("/api/payments/zalopay/status/230314_123456")
    assert response.status_code == 200
    assert "return_code" in response.json() 