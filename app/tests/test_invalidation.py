import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from ..main import app
from ..core.invalidation_helpers import invalidate_dashboard_cache, invalidate_specific_cache
from ..core.cache import redis_client, set_cache
import json
import asyncio

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_invalidate_dashboard_cache():
    """Test the invalidate_dashboard_cache function"""
    # Set up some test keys in cache
    await set_cache("dashboard:stats", json.dumps({"test": "data"}), 300)
    await set_cache("dashboard:recent_orders:10", json.dumps({"orders": []}), 300)
    await set_cache("dashboard:revenue:monthly:none:none", json.dumps({"data": []}), 300)
    
    # Verify the keys exist
    assert await redis_client.get("dashboard:stats") is not None
    assert await redis_client.get("dashboard:recent_orders:10") is not None
    assert await redis_client.get("dashboard:revenue:monthly:none:none") is not None
    
    # Call the invalidation function
    success = await invalidate_dashboard_cache()
    assert success is True
    
    # Verify the keys no longer exist
    assert await redis_client.get("dashboard:stats") is None
    assert await redis_client.get("dashboard:recent_orders:10") is None
    assert await redis_client.get("dashboard:revenue:monthly:none:none") is None

@pytest.mark.asyncio
async def test_invalidate_specific_cache():
    """Test the invalidate_specific_cache function"""
    # Set up some test keys in cache
    await set_cache("test:key1", "value1", 300)
    await set_cache("test:key2", "value2", 300)
    await set_cache("test:key3", "value3", 300)
    
    # Verify the keys exist
    assert await redis_client.get("test:key1") is not None
    assert await redis_client.get("test:key2") is not None
    assert await redis_client.get("test:key3") is not None
    
    # Call the invalidation function for specific keys
    success = await invalidate_specific_cache(["test:key1", "test:key2"])
    assert success is True
    
    # Verify only the specified keys were removed
    assert await redis_client.get("test:key1") is None
    assert await redis_client.get("test:key2") is None
    assert await redis_client.get("test:key3") is not None
    
    # Clean up the remaining test key
    await redis_client.delete("test:key3")

@pytest.mark.asyncio
async def test_manual_cache_invalidation_endpoint():
    """Test the manual cache invalidation endpoint"""
    # Create an async client for testing
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Set up a test key in cache
        await set_cache("dashboard:stats", json.dumps({"test": "data"}), 300)
        assert await redis_client.get("dashboard:stats") is not None
        
        # Login as admin
        login_response = await client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin_password"
        })
        assert login_response.status_code == 200
        token = login_response.json().get("token")
        
        # Call the manual invalidation endpoint
        response = await client.post(
            "/api/admin/dashboard/invalidate-cache",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "Dashboard cache invalidated successfully" in response.json().get("message", "")
        
        # Verify the key no longer exists
        assert await redis_client.get("dashboard:stats") is None

@pytest.mark.asyncio
async def test_order_creation_invalidates_cache():
    """Test that creating an order invalidates the dashboard cache"""
    # Create an async client for testing
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Set up a test key in cache
        await set_cache("dashboard:stats", json.dumps({"test": "data"}), 300)
        assert await redis_client.get("dashboard:stats") is not None
        
        # Login as regular user
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpassword"
        })
        assert login_response.status_code == 200
        token = login_response.json().get("token")
        
        # Create a new order via ZaloPay endpoint
        order_data = {
            "user_id": 1,
            "total_amount": 100.0,
            "cart_items": [
                {
                    "product_id": 1,
                    "quantity": 1,
                    "price": 100.0
                }
            ]
        }
        
        response = await client.post(
            "/api/payments/zalopay/create",
            json=order_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Verify the cache key no longer exists
        assert await redis_client.get("dashboard:stats") is None