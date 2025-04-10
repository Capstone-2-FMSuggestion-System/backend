from passlib.context import CryptContext

# Tạo context cho việc mã hóa mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Tên Function: hash_password
    
    1. Mô tả ngắn gọn:
    Mã hóa mật khẩu sử dụng thuật toán bcrypt.
    
    2. Mô tả công dụng:
    Chuyển đổi mật khẩu dạng văn bản thông thường thành chuỗi mã hóa an toàn.
    Sử dụng thuật toán bcrypt để tạo ra một chuỗi hash không thể giải mã ngược.
    
    3. Các tham số đầu vào:
    - password (str): Chuỗi mật khẩu cần mã hóa
    
    4. Giá trị trả về:
    - str: Chuỗi mật khẩu đã được mã hóa bằng bcrypt
    
    5. Ví dụ sử dụng:
    >>> hashed = hash_password("mat_khau_123")
    >>> # Kết quả: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LedYQNB8UHUYzxUe.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Tên Function: verify_password
    
    1. Mô tả ngắn gọn:
    Xác thực mật khẩu bằng cách so sánh với phiên bản đã mã hóa.
    
    2. Mô tả công dụng:
    Kiểm tra tính hợp lệ của mật khẩu bằng cách so sánh mật khẩu người dùng nhập vào
    với phiên bản đã được mã hóa lưu trong cơ sở dữ liệu.
    
    3. Các tham số đầu vào:
    - plain_password (str): Mật khẩu gốc cần kiểm tra
    - hashed_password (str): Chuỗi mật khẩu đã được mã hóa để so sánh
    
    4. Giá trị trả về:
    - bool: True nếu mật khẩu khớp, False nếu không khớp
    
    5. Ví dụ sử dụng:
    >>> hashed = hash_password("mat_khau_123")
    >>> is_valid = verify_password("mat_khau_123", hashed)
    >>> # is_valid sẽ là True
    """
    return pwd_context.verify(plain_password, hashed_password) 