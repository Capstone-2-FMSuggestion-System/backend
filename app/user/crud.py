from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from .models import User
from .schemas import UserCreate, UserUpdate, UserSearchFilter
from ..core.security import hash_password
from sqlalchemy import or_, text

def get_user_by_username(db: Session, username: str) -> Optional[User]:
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
    - Optional[User]: Đối tượng User nếu tìm thấy, None nếu không tìm thấy
    """
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
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
    - Optional[User]: Đối tượng User nếu tìm thấy, None nếu không tìm thấy
    """
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user) -> User:
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
    - user (Union[dict, UserCreate]): Thông tin người dùng cần tạo,
      có thể là dictionary hoặc đối tượng Pydantic UserCreate
    
    4. Giá trị trả về:
    - User: Đối tượng User đã được tạo trong database
    """
    # Kiểm tra xem user có phải là dictionary không
    if isinstance(user, dict):
        # Mã hóa mật khẩu
        hashed_password = hash_password(user.get("password"))
        db_user = User(
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
        db_user = User(
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

def get_user(db: Session, user_id: int) -> Optional[User]:
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
    - Optional[User]: Đối tượng User nếu tìm thấy, None nếu không tìm thấy
    """
    return db.query(User).filter(User.user_id == user_id).first()

def update_user(db: Session, user_id: int, user) -> Optional[User]:
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
    - user (Union[dict, UserUpdate]): Dữ liệu cập nhật,
      có thể là dictionary hoặc đối tượng Pydantic UserUpdate
    
    4. Giá trị trả về:
    - Optional[User]: Đối tượng User đã cập nhật nếu thành công, None nếu không tìm thấy user
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
    Xóa người dùng và tất cả dữ liệu liên quan khỏi hệ thống.
    
    2. Mô tả công dụng:
    Xóa bản ghi người dùng và tất cả dữ liệu liên quan khỏi cơ sở dữ liệu dựa trên ID.
    Bao gồm xóa cart_items, favorite_menus, reviews, payments, order_items, và orders.
    Thường được sử dụng khi người dùng yêu cầu xóa tài khoản
    hoặc khi admin cần xóa tài khoản không hợp lệ.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - user_id (int): ID của người dùng cần xóa
    
    4. Giá trị trả về:
    - bool: True nếu xóa thành công, False nếu không tìm thấy người dùng
    """
    from ..e_commerce.models import CartItems, FavoriteMenus, Reviews, Orders, OrderItems
    from ..payment.models import Payments
    
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    try:
        # 1. Xóa cart_items của user
        db.query(CartItems).filter(CartItems.user_id == user_id).delete()
        
        # 2. Xóa favorite_menus của user
        db.query(FavoriteMenus).filter(FavoriteMenus.user_id == user_id).delete()
        
        # 3. Xóa reviews của user
        db.query(Reviews).filter(Reviews.user_id == user_id).delete()
        
        # 4. Lấy tất cả orders của user để xóa payments và order_items
        user_orders = db.query(Orders).filter(Orders.user_id == user_id).all()
        order_ids = [order.order_id for order in user_orders]
        
        if order_ids:
            # 5. Xóa payments liên quan đến orders của user
            db.query(Payments).filter(Payments.order_id.in_(order_ids)).delete()
            
            # 6. Xóa order_items liên quan đến orders của user
            db.query(OrderItems).filter(OrderItems.order_id.in_(order_ids)).delete()
        
        # 7. Xóa orders của user
        db.query(Orders).filter(Orders.user_id == user_id).delete()
        
        # 8. Xóa các bảng khác có thể tham chiếu đến user_id (sử dụng raw SQL)
        # Tạm thời tắt foreign key checks để xóa dữ liệu
        try:
            db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            # Xóa tất cả các bảng có thể tham chiếu đến user_id
            tables_to_clean = [
                "health_data",
                "conversations", 
                "user_sessions",
                "notifications",
                "user_preferences",
                "chat_messages",
                "user_activities",
                "user_logs"
            ]
            
            for table in tables_to_clean:
                try:
                    if table == "health_data":
                        # Xóa health_data thông qua conversations
                        db.execute(text(f"""
                            DELETE hd FROM {table} hd 
                            INNER JOIN conversations c ON hd.conversation_id = c.conversation_id 
                            WHERE c.user_id = :user_id
                        """), {"user_id": user_id})
                    else:
                        # Xóa trực tiếp theo user_id
                        db.execute(text(f"DELETE FROM {table} WHERE user_id = :user_id"), {"user_id": user_id})
                except Exception as e:
                    print(f"Warning: Could not delete from {table} table: {e}")
            
            # Bật lại foreign key checks
            db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            
        except Exception as e:
            print(f"Warning: Error in foreign key management: {e}")
            # Đảm bảo bật lại foreign key checks
            try:
                db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            except:
                pass
        
        # 9. Cuối cùng xóa user
        db.delete(db_user)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise e

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
    - List[User]: Danh sách các đối tượng User
    """
    return db.query(User).offset(skip).limit(limit).all()

def search_users(db: Session, search_params: UserSearchFilter, skip: int = 0, limit: int = 100):
    """
    Tên Function: search_users
    
    1. Mô tả ngắn gọn:
    Tìm kiếm người dùng theo tên, vai trò và trạng thái.
    
    2. Mô tả công dụng:
    Truy vấn cơ sở dữ liệu để tìm kiếm người dùng theo các điều kiện như tên, vai trò
    và trạng thái. Hỗ trợ phân trang thông qua các tham số skip và limit.
    
    3. Các tham số đầu vào:
    - db (Session): Phiên làm việc với database
    - search_params (UserSearchFilter): Các tham số tìm kiếm
    - skip (int): Số lượng bản ghi bỏ qua (mặc định: 0)
    - limit (int): Số lượng bản ghi tối đa trả về (mặc định: 100)
    
    4. Giá trị trả về:
    - Tuple[List[User], int]: Danh sách các đối tượng User thỏa mãn điều kiện và tổng số
    """
    # Bắt đầu xây dựng truy vấn
    query = db.query(User)
    
    # Lọc theo tên (tìm kiếm trong username và full_name)
    if search_params.name:
        query = query.filter(
            or_(
                User.username.ilike(f"%{search_params.name}%"),
                User.full_name.ilike(f"%{search_params.name}%")
            )
        )
    
    # Lọc theo vai trò
    if search_params.role:
        query = query.filter(User.role == search_params.role)
    
    # Lọc theo trạng thái
    if search_params.status:
        query = query.filter(User.status == search_params.status)
    
    # Đếm tổng số bản ghi
    total = query.count()
    
    # Thực hiện phân trang
    users = query.offset(skip).limit(limit).all()
    
    return users, total 