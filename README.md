# Hệ thống Gợi ý Thực đơn cho Gia đình

## Mô tả

Hệ thống gợi ý thực đơn cho gia đình với tích hợp chức năng thương mại điện tử cho phép người dùng mua sắm nguyên liệu. Dự án này giải quyết vấn đề lựa chọn thực đơn hàng ngày cho gia đình và tự động gợi ý các nguyên liệu cần thiết cùng khả năng đặt mua trực tuyến.

## Cài đặt

### Yêu cầu hệ thống
- Python 3.11+
- MySQL 8.0+
- Redis 6.2+
- Docker và Docker Compose (tùy chọn)

### Cài đặt thông qua Docker

1. Clone repository:
```python
import os
os.system('git clone <repository_url>')
os.system('cd family-menu-system')
```

2. Tạo file .env từ mẫu:
```bash
cp .env.example .env
```

3. Cập nhật các biến môi trường trong file .env với thông tin cấu hình thích hợp.

4. Khởi động các services:
```bash
docker-compose up -d
```

### Cài đặt thủ công

1. Cài đặt Python dependencies:
```bash
pip install -r requirements.txt
```

2. Cài đặt và cấu hình MySQL:
```python
# Thực hiện các lệnh MySQL sau
# CREATE DATABASE family_menu_db;
# CREATE USER 'family_user'@'localhost' IDENTIFIED BY 'your_password';
# GRANT ALL PRIVILEGES ON family_menu_db.* TO 'family_user'@'localhost';
# FLUSH PRIVILEGES;
```

3. Cài đặt và khởi động Redis:
```bash
redis-server
```

4. Cập nhật file .env với thông tin cấu hình:
```

## Hướng dẫn sử dụng

1. Truy cập API documentation:
```
http://localhost:8000/docs
```

5. Chạy ứng dụng:
```bash
python run.py
# Hoặc
uvicorn app.main:app --reload
```

3. Đăng nhập và nhận JWT token:
```python
import requests
import json

response = requests.post(
    'http://localhost:8000/api/auth/login',
    json={
        'username': 'user@example.com',
        'password': 'your_password'
    }
)
token = response.json()['access_token']
print(f"Token: {token}")
```

4. Sử dụng token để thực hiện các API call:
```python
import requests
import json

headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:8000/api/users/me',
    headers=headers
)
print(json.dumps(response.json(), indent=2))
```

## Các tính năng

1. **Quản lý người dùng**
   - Đăng ký, đăng nhập với JWT authentication
   - Phân quyền: user, admin, inventory_manager
   - Quản lý thông tin cá nhân và preferences

2. **Quản lý sản phẩm**
   - CRUD sản phẩm và danh mục
   - Quản lý kho hàng và theo dõi tồn kho
   - Theo dõi lịch sử giao dịch

3. **Gợi ý thực đơn**
   - Gợi ý dựa trên preferences của người dùng
   - Lưu và quản lý thực đơn yêu thích
   - Tính toán nguyên liệu cần thiết cho thực đơn

4. **Giỏ hàng và đặt hàng**
   - Thêm/xóa sản phẩm vào giỏ hàng
   - Quản lý đơn hàng và theo dõi trạng thái
   - Thanh toán qua ZaloPay

5. **Tích hợp ZaloPay**
   - Tạo đơn hàng
   - Xử lý callback
   - Kiểm tra trạng thái giao dịch

## Yêu cầu hệ thống

- Python 3.9+
- MySQL 8.0+
- Redis 6.2+
- Docker và Docker Compose (tùy chọn)
- Các thư viện phụ thuộc:
  - fastapi==0.103.2
  - uvicorn==0.23.2
  - sqlalchemy==2.0.20
  - pyjwt==2.8.0
  - aioredis==2.0.1
  - pymysql==1.1.0
  - python-dotenv==1.0.0
  - python-jose[cryptography]==3.3.0
  - httpx==0.25.0
  - requests==2.28.2

## Cấu trúc thư mục

```
app/
├── core/                  # Thư mục chứa các thành phần cốt lõi
│   ├── __init__.py
│   ├── auth.py            # Utility xác thực người dùng
│   ├── database.py        # Cấu hình database
│   ├── security.py        # Xử lý bảo mật
│   └── cache.py           # Cấu hình cache
│
├── admin/                 # Module quản trị
├── auth/                  # Module xác thực
├── user/                  # Module người dùng
├── e_commerce/            # Module thương mại điện tử
├── inventory/             # Module quản lý kho
├── payment/               # Module thanh toán
│
├── models.py              # Định nghĩa models chính
├── schemas.py             # Định nghĩa schemas chính
└── main.py                # Cấu hình và khởi tạo FastAPI app

backend/                   # Backend application
docs/                      # Documentation files
.env                       # Environment variables
requirements.txt           # Python dependencies
run.py                     # Application entry point
docker-compose.yml         # Docker configuration
Dockerfile                 # Docker build file
```

## Cách kiểm thử

Chạy unit tests:
```python
import os
os.system('pytest')
```

Kiểm tra API endpoints thông qua Swagger UI:
```
http://localhost:8000/docs
```

Kiểm tra ReDoc:
```
http://localhost:8000/redoc
```

## Cấu hình PayOS

### Đăng ký tài khoản PayOS

1. Truy cập [PayOS Developer Portal](https://developer.payos.vn/) và đăng ký tài khoản nhà phát triển
2. Tạo ứng dụng mới và lấy thông tin Client ID, API Key và Checksum Key
3. Cấu hình URL callback trong trang PayOS Developer Portal: `https://your-domain.com/payment/payos-callback`

### Cấu hình biến môi trường

Thêm các biến môi trường sau vào file `.env` hoặc `docker-compose.yml`:

```
PAYOS_CLIENT_ID=your-payos-client-id
PAYOS_API_KEY=your-payos-api-key
PAYOS_CHECKSUM_KEY=your-payos-checksum-key
FRONTEND_URL=http://localhost:3000
```

### Kiểm tra cấu hình

Sau khi cấu hình, bạn có thể kiểm tra tích hợp PayOS bằng cách thực hiện thanh toán thử nghiệm với tài khoản sandbox.