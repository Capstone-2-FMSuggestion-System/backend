import pytest
from unittest.mock import patch, MagicMock
from app.zalopay import (
    create_zalopay_order,
    verify_callback,
    query_order_status,
    verify_env,
    ZaloPayError
)

def test_verify_env_success():
    with patch.dict('os.environ', {
        'ZALOPAY_APP_ID': '2553',
        'ZALOPAY_KEY1': 'test_key1',
        'ZALOPAY_KEY2': 'test_key2',
        'ZALOPAY_CREATE_ORDER_URL': 'http://test.url/create',
        'ZALOPAY_QUERY_URL': 'http://test.url/query',
        'ZALOPAY_CALLBACK_URL': 'http://test.url/callback'
    }):
        assert verify_env() is True

def test_verify_env_failure():
    with patch.dict('os.environ', {}, clear=True):
        assert verify_env() is False

def test_create_zalopay_order_success():
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"return_code": 1, "return_message": "success"}'
    
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = create_zalopay_order(
            order_id=1,
            user_id=1,
            amount=100000,
            items=[{"name": "Test Item", "quantity": 1, "price": 100000}]
        )
        
        assert result["return_code"] == 1
        assert result["return_message"] == "success"

def test_create_zalopay_order_invalid_amount():
    with pytest.raises(ZaloPayError, match="Amount must be greater than 0"):
        create_zalopay_order(
            order_id=1,
            user_id=1,
            amount=0,
            items=[{"name": "Test Item", "quantity": 1, "price": 100000}]
        )

def test_create_zalopay_order_empty_items():
    with pytest.raises(ZaloPayError, match="Items list cannot be empty"):
        create_zalopay_order(
            order_id=1,
            user_id=1,
            amount=100000,
            items=[]
        )

def test_create_zalopay_order_network_error():
    with patch('urllib.request.urlopen', side_effect=Exception("Network error")):
        with pytest.raises(ZaloPayError, match="Network error"):
            create_zalopay_order(
                order_id=1,
                user_id=1,
                amount=100000,
                items=[{"name": "Test Item", "quantity": 1, "price": 100000}]
            )

def test_verify_callback_success():
    mock_data = {
        "data": "test_data",
        "mac": "valid_mac"
    }
    
    with patch('hmac.new') as mock_hmac:
        mock_hmac.return_value.hexdigest.return_value = "valid_mac"
        assert verify_callback(mock_data) is True

def test_verify_callback_invalid_mac():
    mock_data = {
        "data": "test_data",
        "mac": "invalid_mac"
    }
    
    with patch('hmac.new') as mock_hmac:
        mock_hmac.return_value.hexdigest.return_value = "valid_mac"
        assert verify_callback(mock_data) is False

def test_verify_callback_missing_data():
    assert verify_callback({}) is False
    assert verify_callback({"data": "test_data"}) is False
    assert verify_callback({"mac": "test_mac"}) is False

def test_query_order_status_success():
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"return_code": 1, "return_message": "success"}'
    
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = query_order_status("test_trans_id")
        assert result["return_code"] == 1
        assert result["return_message"] == "success"

def test_query_order_status_network_error():
    with patch('urllib.request.urlopen', side_effect=Exception("Network error")):
        with pytest.raises(ZaloPayError, match="Network error"):
            query_order_status("test_trans_id") 