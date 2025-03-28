# Family Menu Suggestion System

Hệ thống gợi ý thực đơn cho gia đình, kết hợp với chức năng thương mại điện tử cho phép người dùng mua sắm nguyên liệu.

## Tính năng chính

1. **Quản lý người dùng**
   - Đăng ký, đăng nhập với JWT authentication
   - Phân quyền: user, admin, inventory_manager
   - Quản lý thông tin cá nhân và preferences
   - Lưu trữ vị trí địa lý để tối ưu gợi ý

2. **Quản lý sản phẩm**
   - CRUD sản phẩm và danh mục
   - Quản lý kho hàng và theo dõi tồn kho
   - Theo dõi lịch sử giao dịch
   - Hỗ trợ phân cấp danh mục sản phẩm

3. **Gợi ý thực đơn**
   - Gợi ý dựa trên preferences của người dùng
   - Lưu và quản lý thực đơn yêu thích
   - Đánh giá và nhận xét thực đơn
   - Tính toán nguyên liệu cần thiết cho thực đơn

4. **Giỏ hàng và đặt hàng**
   - Thêm/xóa sản phẩm vào giỏ hàng
   - Quản lý đơn hàng và theo dõi trạng thái
   - Thanh toán qua ZaloPay
   - Lưu trữ lịch sử đơn hàng

5. **Tích hợp ZaloPay**
   - Tạo đơn hàng
   - Xử lý callback
   - Kiểm tra trạng thái giao dịch
   - Nhiều phương thức thanh toán:
     - Thanh toán qua ứng dụng ZaloPay
     - Thanh toán bằng thẻ ATM
     - Thanh toán bằng thẻ tín dụng (Visa, Mastercard, JCB)
     - Thanh toán bằng QR code

## Kiến trúc hệ thống

- **Backend**: FastAPI (Python)
- **Database**: MySQL 8.0
- **Cache**: Redis
- **Authentication**: JWT
- **Payment Gateway**: ZaloPay API
- **Containerization**: Docker & Docker Compose

## Yêu cầu hệ thống

- Python 3.9+
- MySQL 8.0+
- Redis 6.2+
- Docker và Docker Compose (tùy chọn)

## Cài đặt

### Phương pháp 1: Sử dụng Docker

1. Clone repository:
```bash
git clone <repository_url>
cd family-menu-system
```

2. Tạo file .env từ mẫu:
```bash
cp .env.example .env
```

3. Cập nhật các biến môi trường trong file .env:
```
DATABASE_URL=mysql+pymysql://family_user:your_password@db/family_menu_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-for-jwt
ZALOPAY_APP_ID=2553
ZALOPAY_KEY1=PcY4iZIKFCIdgZvA6ueMcMHHUbRLYjPL
ZALOPAY_KEY2=kLtgPl8HHhfvMuDHPwKfgfsY4Ydm9eIz
ZALOPAY_CREATE_ORDER_URL=https://sb-openapi.zalopay.vn/v2/create
ZALOPAY_QUERY_URL=https://sb-openapi.zalopay.vn/v2/query
ZALOPAY_CALLBACK_URL=http://your-domain/api/payments/callback
```

4. Khởi động các services:
```bash
docker-compose up -d
```

5. Truy cập API documentation tại:
```
http://localhost:8000/docs
```

### Phương pháp 2: Cài đặt thủ công

1. Cài đặt Python dependencies:
```bash
pip install -r requirements.txt
```

2. Cài đặt và cấu hình MySQL:
```sql
CREATE DATABASE family_menu_db;
CREATE USER 'family_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON family_menu_db.* TO 'family_user'@'localhost';
FLUSH PRIVILEGES;
```

3. Cài đặt và khởi động Redis:
```bash
redis-server
```

4. Cập nhật file .env với thông tin cấu hình:
```
DATABASE_URL=mysql+pymysql://family_user:your_password@localhost/family_menu_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-for-jwt
ZALOPAY_APP_ID=your_app_id
ZALOPAY_KEY1=your_key1
ZALOPAY_KEY2=your_key2
ZALOPAY_CREATE_ORDER_URL=https://sb-openapi.zalopay.vn/v2/create
ZALOPAY_QUERY_URL=https://sb-openapi.zalopay.vn/v2/query
ZALOPAY_CALLBACK_URL=http://your-domain/api/payments/callback
```

5. Chạy ứng dụng:
```bash
python run.py
# Hoặc
uvicorn app.main:app --reload
```

## Cấu trúc dự án

```
family_menu_system/
├── app/
│   ├── __init__.py                  # Khởi tạo package
│   ├── main.py                      # Điểm vào ứng dụng FastAPI
│   ├── models.py                    # Định nghĩa các mô hình (Models) ánh xạ bảng MySQL
│   ├── schemas.py                   # Định nghĩa các Pydantic models cho API
│   ├── database.py                  # Kết nối và quản lý session MySQL
│   ├── auth.py                      # Xác thực và quản lý token (JWT)
│   ├── crud.py                      # Logic xử lý dữ liệu (Create, Read, Update, Delete)
│   ├── cache.py                     # Tích hợp Redis cho caching
│   ├── zalopay.py                   # Tích hợp ZaloPay API
│   └── routes/
│       ├── __init__.py              # Khởi tạo package routes
│       ├── auth.py                  # API xác thực (register, login)
│       ├── user.py                  # API cho người dùng (tìm kiếm, giỏ hàng, v.v.)
│       ├── inventory.py             # API quản lý kho
│       ├── admin.py                 # API quản trị viên
│       ├── payment.py               # API cổng thanh toán
│       └── e_commerce.py            # API thương mại điện tử
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_zalopay.py
├── .env                             # Biến môi trường
├── requirements.txt                 # Danh sách phụ thuộc
├── Dockerfile                       # File Docker
├── docker-compose.yml               # Cấu hình Docker Compose
└── run.py                           # Script chạy ứng dụng
```

## Mô hình dữ liệu

Hệ thống sử dụng các bảng chính sau:

- **users**: Thông tin người dùng và phân quyền
- **categories**: Danh mục sản phẩm (hỗ trợ phân cấp)
- **products**: Thông tin sản phẩm
- **cart_items**: Giỏ hàng của người dùng
- **orders** & **order_items**: Đơn hàng và chi tiết đơn hàng
- **inventory** & **inventory_transactions**: Quản lý kho hàng
- **menus** & **menu_items**: Thực đơn và chi tiết thực đơn
- **favorite_menus**: Thực đơn yêu thích của người dùng
- **reviews**: Đánh giá sản phẩm
- **promotions**: Khuyến mãi
- **payments**: Thông tin thanh toán

## API Documentation

API documentation đầy đủ có sẵn tại `/docs` sau khi khởi động ứng dụng.

### Các endpoint chính:

1. **Authentication**
   - `POST /api/auth/register` - Đăng ký tài khoản mới
   - `POST /api/auth/login` - Đăng nhập và nhận JWT token

2. **User**
   - `GET /api/users/me` - Lấy thông tin người dùng hiện tại
   - `PUT /api/users/me` - Cập nhật thông tin người dùng
   - `GET /api/users/cart` - Xem giỏ hàng
   - `POST /api/users/cart` - Thêm sản phẩm vào giỏ hàng
   - `PUT /api/users/cart/{cart_item_id}` - Cập nhật số lượng sản phẩm trong giỏ hàng
   - `DELETE /api/users/cart/{cart_item_id}` - Xóa sản phẩm khỏi giỏ hàng
   - `GET /api/users/menu-suggestions` - Nhận gợi ý thực đơn

3. **E-Commerce**
   - `GET /api/e-commerce/categories` - Lấy danh sách danh mục
   - `GET /api/e-commerce/products` - Tìm kiếm sản phẩm
   - `GET /api/e-commerce/products/{product_id}` - Xem chi tiết sản phẩm
   - `POST /api/e-commerce/orders` - Tạo đơn hàng mới
   - `GET /api/e-commerce/orders` - Xem lịch sử đơn hàng
   - `GET /api/e-commerce/orders/{order_id}` - Xem chi tiết đơn hàng

4. **Admin**
   - `GET /api/admin/users` - Quản lý người dùng
   - `POST /api/admin/products` - Thêm sản phẩm mới
   - `PUT /api/admin/products/{product_id}` - Cập nhật sản phẩm
   - `DELETE /api/admin/products/{product_id}` - Xóa sản phẩm
   - `GET /api/admin/analytics/sales` - Xem báo cáo doanh số
   - `GET /api/admin/analytics/inventory` - Xem báo cáo tồn kho

5. **Inventory**
   - `GET /api/inventory/products` - Xem tồn kho sản phẩm
   - `POST /api/inventory/transactions` - Tạo giao dịch nhập/xuất kho
   - `GET /api/inventory/transactions` - Xem lịch sử giao dịch kho

6. **Payment**
   - `POST /api/payments/zalopay/create` - Tạo đơn hàng thanh toán ZaloPay
   - `POST /api/payments/zalopay/callback` - Callback URL cho ZaloPay
   - `GET /api/payments/zalopay/status/{app_trans_id}` - Kiểm tra trạng thái thanh toán
   - `GET /api/payments/zalopay/payment-methods` - Lấy danh sách phương thức thanh toán

## Phụ thuộc

```
fastapi==0.103.2
uvicorn==0.23.2
sqlalchemy==2.0.20
pyjwt==2.8.0
aioredis==2.0.1
pymysql==1.1.0
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
httpx==0.25.0
requests==2.28.2
```

## Testing

Chạy unit tests:
```bash
pytest
```

## Security

1. **Authentication & Authorization**
   - JWT authentication với expiration time
   - Role-based access control (user, admin, inventory_manager)
   - Password hashing với bcrypt

2. **Bảo mật dữ liệu**
   - Input validation với Pydantic
   - SQL injection protection với SQLAlchemy ORM
   - CORS protection

3. **Bảo mật mạng**
   - Rate limiting
   - SSL/TLS trong production
   - Secure headers

## Monitoring & Logging

1. **Logging**
   - Application logs
   - Access logs
   - Error logs

2. **Metrics**
   - Response time
   - Error rate
   - Transaction success rate

## Troubleshooting

### Vấn đề kết nối cơ sở dữ liệu
- Kiểm tra thông tin kết nối trong file .env
- Đảm bảo MySQL đang chạy và có thể truy