from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Tên Function: get_db
    
    1. Mô tả ngắn gọn:
    Tạo và quản lý phiên kết nối với cơ sở dữ liệu.
    
    2. Mô tả công dụng:
    Tạo một phiên làm việc mới với cơ sở dữ liệu và đảm bảo phiên
    được đóng đúng cách sau khi sử dụng, ngay cả khi xảy ra lỗi.
    Function này được sử dụng như một dependency trong FastAPI.
    
    3. Các tham số đầu vào:
    - Không có tham số đầu vào
    
    4. Giá trị trả về:
    - Generator[Session, None, None]: Đối tượng Session cho phép tương tác với database
    
    5. Ví dụ sử dụng:
    >>> @app.get("/users")
    >>> def get_users(db: Session = Depends(get_db)):
    >>>     return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()