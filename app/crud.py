from sqlalchemy.orm import Session
from . import models, schemas
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from .security import hash_password

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """
    Tên Function: get_user_by_username
    
    1. Mô tả ngắn gọn:
    Tìm kiếm người dùng theo tên đăng nhập.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để tìm kiếm và trả về thông tin của người dùng
    dựa trên tên đăng nhập (username). Thường được sử dụng trong quá trình
    xác thực và kiểm tra tài khoản.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - username (str): Tên đăng nhập cần tìm kiếm
    
    4. Giá trị trả về:
    - Optional[models.User]: Đối tượng User nếu tìm thấy, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> user = get_user_by_username(db, "nguyen_van_a")
    >>> if user:
    >>>     print(f"Đã tìm thấy người dùng: {user.full_name}")
    """
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    Tên Function: get_user_by_email
    
    1. Mô tả ngắn gọn:
    Tìm kiếm người dùng theo địa chỉ email.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để tìm kiếm và trả về thông tin của người dùng
    dựa trên địa chỉ email. Thường được sử dụng trong quá trình đăng ký
    để kiểm tra email đã tồn tại hay chưa.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - email (str): Địa chỉ email cần tìm kiếm
    
    4. Giá trị trả về:
    - Optional[models.User]: Đối tượng User nếu tìm thấy, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> user = get_user_by_email(db, "example@email.com")
    >>> if user:
    >>>     print(f"Email này đã được đăng ký bởi: {user.username}")
    """
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user) -> models.User:
    """
    Tên Function: create_user
    
    1. Mô tả ngắn gọn:
    Tạo người dùng mới trong hệ thống.
    
    2. Mô tả công dụng:
    Tạo một bản ghi người dùng mới trong cơ sở dữ liệu với thông tin được cung cấp.
    Hỗ trợ hai định dạng dữ liệu đầu vào: dictionary hoặc đối tượng Pydantic.
    Tự động mã hóa mật khẩu trước khi lưu vào database.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - user (Union[dict, schemas.UserCreate]): Thông tin người dùng cần tạo,
      có thể là dictionary hoặc đối tượng Pydantic UserCreate
    
    4. Giá trị trả về:
    - models.User: Đối tượng User đã được tạo trong database
    
    5. Ví dụ sử dụng:
    >>> user_data = {
    >>>     "username": "nguyen_van_a",
    >>>     "email": "nguyenvana@example.com",
    >>>     "password": "mat_khau_123",
    >>>     "full_name": "Nguyễn Văn A"
    >>> }
    >>> new_user = create_user(db, user_data)
    """
    # Kiểm tra xem user có phải là dictionary không
    if isinstance(user, dict):
        # Mã hóa mật khẩu
        hashed_password = hash_password(user.get("password"))
        db_user = models.User(
            username=user.get("username"),
            email=user.get("email"),
            password=hashed_password,
            full_name=user.get("full_name"),
            location=user.get("location", None),
            role=user.get("role", "user")
        )
    else:
        # Nếu là đối tượng Pydantic
        # Mã hóa mật khẩu
        hashed_password = hash_password(user.password)
        db_user = models.User(
            username=user.username,
            email=user.email,
            password=hashed_password,
            full_name=user.full_name,
            location=getattr(user, "location", None),
            role=getattr(user, "role", "user")
        )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """
    Tên Function: get_user
    
    1. Mô tả ngắn gọn:
    Lấy thông tin người dùng theo ID.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy thông tin chi tiết của một người dùng
    dựa trên ID của họ. Thường được sử dụng khi cần xem hoặc chỉnh sửa
    thông tin người dùng.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - user_id (int): ID của người dùng cần tìm
    
    4. Giá trị trả về:
    - Optional[models.User]: Đối tượng User nếu tìm thấy, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> user = get_user(db, 123)
    >>> if user:
    >>>     print(f"Tên người dùng: {user.full_name}")
    """
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def update_user(db: Session, user_id: int, user) -> Optional[models.User]:
    """
    Tên Function: update_user
    
    1. Mô tả ngắn gọn:
    Cập nhật thông tin người dùng.
    
    2. Mô tả công dụng:
    Cập nhật thông tin của người dùng trong cơ sở dữ liệu dựa trên ID.
    Hỗ trợ cập nhật từ cả dictionary và đối tượng Pydantic.
    Tự động mã hóa mật khẩu mới nếu được cung cấp.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - user_id (int): ID của người dùng cần cập nhật
    - user (Union[dict, schemas.UserUpdate]): Dữ liệu cập nhật,
      có thể là dictionary hoặc đối tượng Pydantic UserUpdate
    
    4. Giá trị trả về:
    - Optional[models.User]: Đối tượng User đã cập nhật nếu thành công, None nếu không tìm thấy user
    
    5. Ví dụ sử dụng:
    >>> update_data = {
    >>>     "full_name": "Nguyễn Văn B",
    >>>     "password": "mat_khau_moi_123"
    >>> }
    >>> updated_user = update_user(db, user_id=123, user=update_data)
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Nếu là dictionary
    if isinstance(user, dict):
        # Nếu có cập nhật mật khẩu
        if "password" in user:
            user["password"] = hash_password(user["password"])
        
        for field, value in user.items():
            setattr(db_user, field, value)
    else:
        # Nếu là đối tượng Pydantic
        update_data = user.dict(exclude_unset=True)
        
        # Nếu có cập nhật mật khẩu
        if "password" in update_data:
            update_data["password"] = hash_password(update_data["password"])
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    """
    Tên Function: delete_user
    
    1. Mô tả ngắn gọn:
    Xóa người dùng khỏi hệ thống.
    
    2. Mô tả công dụng:
    Xóa bản ghi người dùng khỏi cơ sở dữ liệu dựa trên ID.
    Thường được sử dụng khi người dùng yêu cầu xóa tài khoản
    hoặc khi admin cần xóa tài khoản không hợp lệ.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - user_id (int): ID của người dùng cần xóa
    
    4. Giá trị trả về:
    - bool: True nếu xóa thành công, False nếu không tìm thấy người dùng
    
    5. Ví dụ sử dụng:
    >>> if delete_user(db, user_id=123):
    >>>     print("Đã xóa người dùng thành công")
    >>> else:
    >>>     print("Không tìm thấy người dùng")
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """
    Tên Function: get_users
    
    1. Mô tả ngắn gọn:
    Lấy danh sách người dùng có phân trang.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy danh sách người dùng với khả năng
    phân trang thông qua các tham số skip và limit. Hữu ích khi cần
    hiển thị danh sách người dùng trên giao diện quản trị.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - skip (int): Số lượng bản ghi bỏ qua (mặc định: 0)
    - limit (int): Số lượng bản ghi tối đa trả về (mặc định: 100)
    
    4. Giá trị trả về:
    - List[models.User]: Danh sách các đối tượng User
    
    5. Ví dụ sử dụng:
    >>> # Lấy 10 người dùng, bỏ qua 20 người dùng đầu tiên
    >>> users = get_users(db, skip=20, limit=10)
    >>> for user in users:
    >>>     print(f"User ID: {user.user_id}, Name: {user.full_name}")
    """
    return db.query(models.User).offset(skip).limit(limit).all()

# Order CRUD operations
def create_order(db: Session, order: schemas.OrderCreate) -> models.Orders:
    """
    Tên Function: create_order
    
    1. Mô tả ngắn gọn:
    Tạo đơn hàng mới trong hệ thống.
    
    2. Mô tả công dụng:
    Tạo một đơn hàng mới và các mặt hàng trong đơn hàng, tính toán tổng số tiền
    dựa trên giá thực tế của sản phẩm tại thời điểm đặt hàng. Đảm bảo tính
    chính xác của giá khi có nhiều người mua cùng lúc.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - order (schemas.OrderCreate): Thông tin đơn hàng cần tạo, bao gồm:
      + user_id: ID người dùng đặt hàng
      + cart_items: Danh sách các mặt hàng
      + payment_method: Phương thức thanh toán
    
    4. Giá trị trả về:
    - models.Orders: Đơn hàng đã được tạo trong database
    
    5. Ví dụ sử dụng:
    >>> order_data = schemas.OrderCreate(
    >>>     user_id=1,
    >>>     cart_items=[{"product_id": 1, "quantity": 2}],
    >>>     payment_method="zalopay"
    >>> )
    >>> new_order = create_order(db, order_data)
    """
    total_amount = Decimal('0')
    
    # Create the order
    db_order = models.Orders(
        user_id=order.user_id,
        total_amount=total_amount,
        status="pending",
        payment_method=order.payment_method
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Create order items
    for item in order.cart_items:
        # Lấy thông tin sản phẩm từ database
        product = db.query(models.Product).filter(models.Product.product_id == item.product_id).first()
        if not product:
            raise ValueError(f"Product with ID {item.product_id} not found")
        
        # Lấy giá thực tế của sản phẩm
        product_price = product.price
        
        db_order_item = models.OrderItems(
            order_id=db_order.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=product_price  # Sử dụng giá thực tế
        )
        db.add(db_order_item)
        total_amount += product_price * item.quantity
    
    # Update order total
    db_order.total_amount = total_amount
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order_status(db: Session, order_id: int, status: str) -> Optional[models.Orders]:
    """
    Tên Function: update_order_status
    
    1. Mô tả ngắn gọn:
    Cập nhật trạng thái đơn hàng.
    
    2. Mô tả công dụng:
    Cập nhật trạng thái của đơn hàng trong cơ sở dữ liệu.
    Thường được sử dụng khi cần thay đổi trạng thái đơn hàng
    (ví dụ: từ "pending" sang "completed" hoặc "cancelled").
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - order_id (int): ID của đơn hàng cần cập nhật
    - status (str): Trạng thái mới của đơn hàng
    
    4. Giá trị trả về:
    - Optional[models.Orders]: Đơn hàng đã cập nhật nếu thành công, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> updated_order = update_order_status(db, order_id=123, status="completed")
    >>> if updated_order:
    >>>     print(f"Đã cập nhật trạng thái đơn hàng thành: {updated_order.status}")
    """
    db_order = db.query(models.Orders).filter(models.Orders.order_id == order_id).first()
    if not db_order:
        return None
    
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    return db_order

def get_order(db: Session, order_id: int) -> Optional[models.Orders]:
    """
    Tên Function: get_order
    
    1. Mô tả ngắn gọn:
    Lấy thông tin đơn hàng theo ID.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy thông tin chi tiết của một đơn hàng
    dựa trên ID. Thường được sử dụng khi cần xem chi tiết đơn hàng
    hoặc kiểm tra trạng thái đơn hàng.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - order_id (int): ID của đơn hàng cần tìm
    
    4. Giá trị trả về:
    - Optional[models.Orders]: Đối tượng Orders nếu tìm thấy, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> order = get_order(db, order_id=123)
    >>> if order:
    >>>     print(f"Tổng tiền đơn hàng: {order.total_amount}")
    """
    return db.query(models.Orders).filter(models.Orders.order_id == order_id).first()

# Payment CRUD operations
def create_payment(db: Session, payment: schemas.PaymentCreate) -> models.Payments:
    """
    Tên Function: create_payment
    
    1. Mô tả ngắn gọn:
    Tạo một giao dịch thanh toán mới.
    
    2. Mô tả công dụng:
    Tạo một bản ghi thanh toán mới trong cơ sở dữ liệu cho một đơn hàng.
    Ghi lại thông tin về phương thức thanh toán, số tiền và trạng thái ban đầu
    là "pending" (đang chờ).
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - payment (schemas.PaymentCreate): Thông tin thanh toán cần tạo, bao gồm:
      + order_id: ID của đơn hàng
      + amount: Số tiền thanh toán
      + method: Phương thức thanh toán
    
    4. Giá trị trả về:
    - models.Payments: Đối tượng Payment đã được tạo trong database
    
    5. Ví dụ sử dụng:
    >>> payment_data = schemas.PaymentCreate(
    >>>     order_id=123,
    >>>     amount=100000,
    >>>     method="zalopay"
    >>> )
    >>> new_payment = create_payment(db, payment_data)
    """
    db_payment = models.Payments(
        order_id=payment.order_id,
        amount=payment.amount,
        method=payment.method,
        status="pending"
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def update_payment_status(db: Session, payment_id: int, status: str, zp_trans_id: Optional[str] = None) -> Optional[models.Payments]:
    """
    Tên Function: update_payment_status
    
    1. Mô tả ngắn gọn:
    Cập nhật trạng thái thanh toán và mã giao dịch ZaloPay.
    
    2. Mô tả công dụng:
    Cập nhật trạng thái và mã giao dịch của một thanh toán trong cơ sở dữ liệu.
    Thường được sử dụng sau khi nhận được phản hồi từ cổng thanh toán ZaloPay
    để cập nhật trạng thái giao dịch (thành công, thất bại, etc.).
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - payment_id (int): ID của giao dịch thanh toán cần cập nhật
    - status (str): Trạng thái mới của giao dịch
    - zp_trans_id (Optional[str]): Mã giao dịch từ ZaloPay (nếu có)
    
    4. Giá trị trả về:
    - Optional[models.Payments]: Đối tượng Payment đã cập nhật nếu thành công, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> updated_payment = update_payment_status(
    >>>     db,
    >>>     payment_id=123,
    >>>     status="success",
    >>>     zp_trans_id="230317_123456"
    >>> )
    """
    db_payment = db.query(models.Payments).filter(models.Payments.payment_id == payment_id).first()
    if not db_payment:
        return None
    
    db_payment.status = status
    if zp_trans_id:
        db_payment.zp_trans_id = zp_trans_id
    
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_payment(db: Session, payment_id: int) -> Optional[models.Payments]:
    """
    Tên Function: get_payment
    
    1. Mô tả ngắn gọn:
    Lấy thông tin giao dịch thanh toán theo ID.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy thông tin chi tiết của một giao dịch thanh toán
    dựa trên ID. Thường được sử dụng khi cần kiểm tra thông tin hoặc trạng thái
    của một giao dịch thanh toán cụ thể.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - payment_id (int): ID của giao dịch thanh toán cần tìm
    
    4. Giá trị trả về:
    - Optional[models.Payments]: Đối tượng Payment nếu tìm thấy, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> payment = get_payment(db, payment_id=123)
    >>> if payment:
    >>>     print(f"Trạng thái thanh toán: {payment.status}")
    """
    return db.query(models.Payments).filter(models.Payments.payment_id == payment_id).first()

def get_payment_by_order(db: Session, order_id: int) -> Optional[models.Payments]:
    """
    Tên Function: get_payment_by_order
    
    1. Mô tả ngắn gọn:
    Lấy thông tin thanh toán theo ID đơn hàng.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy thông tin thanh toán của một đơn hàng cụ thể.
    Thường được sử dụng khi cần kiểm tra trạng thái thanh toán của đơn hàng
    hoặc để xác nhận xem đơn hàng đã được thanh toán chưa.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - order_id (int): ID của đơn hàng cần tìm thông tin thanh toán
    
    4. Giá trị trả về:
    - Optional[models.Payments]: Đối tượng Payment nếu tìm thấy, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> payment = get_payment_by_order(db, order_id=123)
    >>> if payment:
    >>>     print(f"Phương thức thanh toán: {payment.method}")
    """
    return db.query(models.Payments).filter(models.Payments.order_id == order_id).first()

# Product CRUD operations
def get_products(db: Session, skip: int = 0, limit: int = 100, category_id: Optional[int] = None) -> List[models.Product]:
    """
    Tên Function: get_products
    
    1. Mô tả ngắn gọn:
    Lấy danh sách sản phẩm có phân trang và lọc theo danh mục.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy danh sách sản phẩm với khả năng phân trang
    và lọc theo danh mục (nếu được chỉ định). Hữu ích khi hiển thị danh sách
    sản phẩm trên giao diện người dùng hoặc trang quản trị.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - skip (int): Số lượng bản ghi bỏ qua (mặc định: 0)
    - limit (int): Số lượng bản ghi tối đa trả về (mặc định: 100)
    - category_id (Optional[int]): ID của danh mục cần lọc (nếu có)
    
    4. Giá trị trả về:
    - List[models.Product]: Danh sách các đối tượng Product
    
    5. Ví dụ sử dụng:
    >>> # Lấy 10 sản phẩm đầu tiên của danh mục có ID là 1
    >>> products = get_products(db, limit=10, category_id=1)
    >>> for product in products:
    >>>     print(f"Tên sản phẩm: {product.name}, Giá: {product.price}")
    """
    query = db.query(models.Product)
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    return query.offset(skip).limit(limit).all()

def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    """
    Tên Function: get_product
    
    1. Mô tả ngắn gọn:
    Lấy thông tin sản phẩm theo ID.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy thông tin chi tiết của một sản phẩm
    dựa trên ID. Thường được sử dụng khi cần hiển thị trang chi tiết
    sản phẩm hoặc kiểm tra thông tin sản phẩm.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - product_id (int): ID của sản phẩm cần tìm
    
    4. Giá trị trả về:
    - Optional[models.Product]: Đối tượng Product nếu tìm thấy, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> product = get_product(db, product_id=123)
    >>> if product:
    >>>     print(f"Tên sản phẩm: {product.name}, Giá: {product.price}")
    """
    return db.query(models.Product).filter(models.Product.product_id == product_id).first()

def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
    """
    Tên Function: create_product
    
    1. Mô tả ngắn gọn:
    Tạo sản phẩm mới trong hệ thống.
    
    2. Mô tả công dụng:
    Tạo một bản ghi sản phẩm mới trong cơ sở dữ liệu với thông tin được cung cấp.
    Thường được sử dụng trong trang quản trị khi thêm sản phẩm mới vào hệ thống.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - product (schemas.ProductCreate): Thông tin sản phẩm cần tạo
    
    4. Giá trị trả về:
    - models.Product: Đối tượng Product đã được tạo trong database
    
    5. Ví dụ sử dụng:
    >>> product_data = schemas.ProductCreate(
    >>>     name="Cà phê sữa",
    >>>     price=25000,
    >>>     description="Cà phê pha với sữa đặc",
    >>>     category_id=1
    >>> )
    >>> new_product = create_product(db, product_data)
    """
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_data: dict) -> Optional[models.Product]:
    """
    Tên Function: update_product
    
    1. Mô tả ngắn gọn:
    Cập nhật thông tin sản phẩm.
    
    2. Mô tả công dụng:
    Cập nhật thông tin của sản phẩm trong cơ sở dữ liệu dựa trên ID.
    Cho phép cập nhật một hoặc nhiều trường thông tin của sản phẩm.
    Thường được sử dụng trong trang quản trị để chỉnh sửa thông tin sản phẩm.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - product_id (int): ID của sản phẩm cần cập nhật
    - product_data (dict): Dictionary chứa các trường thông tin cần cập nhật
    
    4. Giá trị trả về:
    - Optional[models.Product]: Đối tượng Product đã cập nhật nếu thành công, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> update_data = {
    >>>     "name": "Cà phê đen",
    >>>     "price": 20000,
    >>>     "description": "Cà phê đen đậm đà"
    >>> }
    >>> updated_product = update_product(db, product_id=123, product_data=update_data)
    """
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    
    for field, value in product_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

# Cart Items CRUD operations
def create_cart_item(db: Session, user_id: int, cart_item: schemas.CartItem) -> models.CartItems:
    """
    Tên Function: create_cart_item
    
    1. Mô tả ngắn gọn:
    Thêm sản phẩm vào giỏ hàng của người dùng.
    
    2. Mô tả công dụng:
    Tạo một bản ghi mới trong giỏ hàng cho người dùng với thông tin sản phẩm
    và số lượng được chỉ định. Thường được sử dụng khi người dùng muốn thêm
    sản phẩm vào giỏ hàng của họ.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - user_id (int): ID của người dùng sở hữu giỏ hàng
    - cart_item (schemas.CartItem): Thông tin sản phẩm cần thêm vào giỏ hàng
    
    4. Giá trị trả về:
    - models.CartItems: Đối tượng CartItems đã được tạo trong database
    
    5. Ví dụ sử dụng:
    >>> cart_item = schemas.CartItem(
    >>>     product_id=123,
    >>>     quantity=2
    >>> )
    >>> new_cart_item = create_cart_item(db, user_id=1, cart_item=cart_item)
    """
    db_cart_item = models.CartItems(
        user_id=user_id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity
    )
    db.add(db_cart_item)
    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item

def get_cart_item(db: Session, cart_item_id: int) -> Optional[models.CartItems]:
    """
    Tên Function: get_cart_item
    
    1. Mô tả ngắn gọn:
    Lấy thông tin một mục trong giỏ hàng theo ID.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy thông tin chi tiết của một mục trong giỏ hàng
    dựa trên ID của mục đó. Thường được sử dụng khi cần kiểm tra hoặc cập nhật
    một sản phẩm cụ thể trong giỏ hàng.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - cart_item_id (int): ID của mục trong giỏ hàng cần tìm
    
    4. Giá trị trả về:
    - Optional[models.CartItems]: Đối tượng CartItems nếu tìm thấy, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> cart_item = get_cart_item(db, cart_item_id=123)
    >>> if cart_item:
    >>>     print(f"Số lượng sản phẩm: {cart_item.quantity}")
    """
    return db.query(models.CartItems).filter(models.CartItems.cart_item_id == cart_item_id).first()

def get_cart_items_by_user(db: Session, user_id: int) -> List[models.CartItems]:
    """
    Tên Function: get_cart_items_by_user
    
    1. Mô tả ngắn gọn:
    Lấy danh sách tất cả các mục trong giỏ hàng của một người dùng.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để lấy toàn bộ sản phẩm trong giỏ hàng của một người dùng
    dựa trên ID của họ. Thường được sử dụng để hiển thị giỏ hàng của người dùng
    hoặc tính toán tổng giá trị đơn hàng.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - user_id (int): ID của người dùng cần lấy giỏ hàng
    
    4. Giá trị trả về:
    - List[models.CartItems]: Danh sách các đối tượng CartItems của người dùng
    
    5. Ví dụ sử dụng:
    >>> cart_items = get_cart_items_by_user(db, user_id=1)
    >>> for item in cart_items:
    >>>     print(f"Sản phẩm: {item.product_id}, Số lượng: {item.quantity}")
    """
    return db.query(models.CartItems).filter(models.CartItems.user_id == user_id).all()

def update_cart_item(db: Session, cart_item_id: int, quantity: int) -> Optional[models.CartItems]:
    """
    Tên Function: update_cart_item
    
    1. Mô tả ngắn gọn:
    Cập nhật số lượng sản phẩm trong giỏ hàng.
    
    2. Mô tả công dụng:
    Cập nhật số lượng của một sản phẩm trong giỏ hàng. Thường được sử dụng
    khi người dùng thay đổi số lượng sản phẩm trong giỏ hàng của họ hoặc
    khi hệ thống cần điều chỉnh số lượng theo tồn kho.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - cart_item_id (int): ID của mục trong giỏ hàng cần cập nhật
    - quantity (int): Số lượng mới của sản phẩm
    
    4. Giá trị trả về:
    - Optional[models.CartItems]: Đối tượng CartItems đã cập nhật nếu thành công, None nếu không tìm thấy
    
    5. Ví dụ sử dụng:
    >>> updated_item = update_cart_item(db, cart_item_id=123, quantity=3)
    >>> if updated_item:
    >>>     print(f"Đã cập nhật số lượng thành: {updated_item.quantity}")
    """
    db_cart_item = get_cart_item(db, cart_item_id)
    if not db_cart_item:
        return None
    
    db_cart_item.quantity = quantity
    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item

def delete_cart_item(db: Session, cart_item_id: int) -> bool:
    db_cart_item = get_cart_item(db, cart_item_id)
    if not db_cart_item:
        return False
    
    db.delete(db_cart_item)
    db.commit()
    return True

# Menu CRUD operations
def create_menu(db: Session, menu_data: dict, menu_items: List[dict] = None) -> models.Menus:
    new_menu = models.Menus(**menu_data)
    db.add(new_menu)
    db.commit()
    db.refresh(new_menu)
    
    if menu_items:
        for item in menu_items:
            menu_item = models.MenuItems(menu_id=new_menu.menu_id, **item)
            db.add(menu_item)
        db.commit()
    
    return new_menu

def get_menu(db: Session, menu_id: int) -> Optional[models.Menus]:
    return db.query(models.Menus).filter(models.Menus.menu_id == menu_id).first()

def get_menus(db: Session, skip: int = 0, limit: int = 100) -> List[models.Menus]:
    return db.query(models.Menus).offset(skip).limit(limit).all()

def update_menu(db: Session, menu_id: int, menu_data: dict) -> Optional[models.Menus]:
    db_menu = get_menu(db, menu_id)
    if not db_menu:
        return None
    
    for field, value in menu_data.items():
        setattr(db_menu, field, value)
    
    db.commit()
    db.refresh(db_menu)
    return db_menu

def delete_menu(db: Session, menu_id: int) -> bool:
    db_menu = get_menu(db, menu_id)
    if not db_menu:
        return False
    
    db.delete(db_menu)
    db.commit()
    return True

# Review CRUD operations
def create_review(db: Session, review_data: dict) -> models.Reviews:
    new_review = models.Reviews(**review_data)
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

def get_review(db: Session, review_id: int) -> Optional[models.Reviews]:
    return db.query(models.Reviews).filter(models.Reviews.review_id == review_id).first()

def get_reviews_by_product(db: Session, product_id: int) -> List[models.Reviews]:
    return db.query(models.Reviews).filter(models.Reviews.product_id == product_id).all()

def update_review(db: Session, review_id: int, review_data: dict) -> Optional[models.Reviews]:
    db_review = get_review(db, review_id)
    if not db_review:
        return None
    
    for field, value in review_data.items():
        setattr(db_review, field, value)
    
    db.commit()
    db.refresh(db_review)
    return db_review

def delete_review(db: Session, review_id: int) -> bool:
    db_review = get_review(db, review_id)
    if not db_review:
        return False
    
    db.delete(db_review)
    db.commit()
    return True

# Promotion CRUD operations
def create_promotion(db: Session, promotion_data: dict) -> models.Promotions:
    new_promotion = models.Promotions(**promotion_data)
    db.add(new_promotion)
    db.commit()
    db.refresh(new_promotion)
    return new_promotion

def get_promotion(db: Session, promotion_id: int) -> Optional[models.Promotions]:
    return db.query(models.Promotions).filter(models.Promotions.promotion_id == promotion_id).first()

def get_active_promotions(db: Session) -> List[models.Promotions]:
    current_time = datetime.now()
    return db.query(models.Promotions).filter(
        models.Promotions.start_date <= current_time,
        models.Promotions.end_date >= current_time
    ).all()

def update_promotion(db: Session, promotion_id: int, promotion_data: dict) -> Optional[models.Promotions]:
    db_promotion = get_promotion(db, promotion_id)
    if not db_promotion:
        return None
    
    for field, value in promotion_data.items():
        setattr(db_promotion, field, value)
    
    db.commit()
    db.refresh(db_promotion)
    return db_promotion

def delete_promotion(db: Session, promotion_id: int) -> bool:
    db_promotion = get_promotion(db, promotion_id)
    if not db_promotion:
        return False
    
    db.delete(db_promotion)
    db.commit()
    return True

# Inventory CRUD operations
def create_inventory(db: Session, inventory_data: dict) -> models.Inventory:
    new_inventory = models.Inventory(**inventory_data)
    db.add(new_inventory)
    db.commit()
    db.refresh(new_inventory)
    return new_inventory

def get_inventory(db: Session, inventory_id: int) -> Optional[models.Inventory]:
    return db.query(models.Inventory).filter(models.Inventory.inventory_id == inventory_id).first()

def get_inventory_by_product(db: Session, product_id: int) -> Optional[models.Inventory]:
    return db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()

def update_inventory(db: Session, inventory_id: int, quantity: int) -> Optional[models.Inventory]:
    db_inventory = get_inventory(db, inventory_id)
    if not db_inventory:
        return None
    
    db_inventory.quantity = quantity
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

def delete_inventory(db: Session, inventory_id: int) -> bool:
    db_inventory = get_inventory(db, inventory_id)
    if not db_inventory:
        return False
    
    db.delete(db_inventory)
    db.commit()
    return True

# Inventory Transaction CRUD operations
def create_inventory_transaction(db: Session, transaction_data: dict) -> models.InventoryTransactions:
    new_transaction = models.InventoryTransactions(**transaction_data)
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

def get_inventory_transactions(db: Session, start_date: str = None, end_date: str = None) -> List[models.InventoryTransactions]:
    query = db.query(models.InventoryTransactions)
    if start_date:
        query = query.filter(models.InventoryTransactions.created_at >= start_date)
    if end_date:
        query = query.filter(models.InventoryTransactions.created_at <= end_date)
    return query.all()

# Favorite Menu CRUD operations
def create_favorite_menu(db: Session, user_id: int, menu_id: int) -> models.FavoriteMenus:
    favorite = models.FavoriteMenus(user_id=user_id, menu_id=menu_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite

def get_favorite_menu(db: Session, favorite_menu_id: int) -> Optional[models.FavoriteMenus]:
    return db.query(models.FavoriteMenus).filter(models.FavoriteMenus.favorite_menu_id == favorite_menu_id).first()

def get_favorite_menus_by_user(db: Session, user_id: int) -> List[models.FavoriteMenus]:
    return db.query(models.FavoriteMenus).filter(models.FavoriteMenus.user_id == user_id).all()

def delete_favorite_menu(db: Session, favorite_menu_id: int) -> bool:
    favorite = get_favorite_menu(db, favorite_menu_id)
    if not favorite:
        return False
    
    db.delete(favorite)
    db.commit()
    return True 